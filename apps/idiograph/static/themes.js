/* Idiograph, the PETs screen: the IPA step after the statements. Every experiential statement
   of a case is a card on a canvas, and he groups them into personal experiential themes under
   labels he names. Membership is stored, never read off where a card sits, and a card leaves its
   theme only when he takes it out. Nothing on the canvas overlaps anything else.

   The first half of this file is the model: plain functions over one board of the canvas, with
   no DOM in them, which is what lets the suite run them in node. The second half draws the canvas,
   the boards and their history, the sidebar with the Inspector and its player, the AI's help, and
   answers the pointer and the keys. It leans on
   app.js for $, api, say, esc, show, MOD, the clock and the glyphs of the turn screen's player and
   the restart line, and app.js opens it through openThemes. */

'use strict';

/* ─────────────────────────────────────────────────────────── the model ── */

/* A board is { cards: { key: card }, groups: [{ id, label, note, members, x, y }], discarded: [key],
   picks: { group: [quote key] } }. A group's members are card keys or the ids of other groups, so a
   label over labels is the same object one layer up. A card or a group belongs to one group at
   most. A group's note is his own words on why the theme exists, and a group with none has none.
   A quote key is the row's sheet and row and the quote's place among its quotes,
   `Initial:12:0`, the shape of a card key.
   A board from a server with the sticky notes also has `stickies`, [{ id, text, colour, x, y, in }],
   his notes to himself on the canvas, the file's `notes`. A note is never a statement and never a
   member: `in` names the group it sits in, a note in no group has none, and nothing that counts or
   lists a group's statements meets one. A board from a server before them has `stickies` of null.
   A board from a server with the stacks also has `stacks`, { top: [key] }: the statements stacked under
   a better one, the top, which stands for them (see thStackOnto). A stacked statement is in no group,
   not in the bin and not on the canvas: it goes where its top goes. */

const TH_GAP = 8;        // between a label and the top of what it holds
const TH_HUES = 8;       // the tints top-level themes take in turn, each its own, then grey
/* The margin every card and every label always keeps clear round it, a twentieth of a card's
   width, 10px on a 200px card: nothing comes to rest inside another's. One measure everywhere, the
   first pile, a drop, a nudge, a card put back, a new card, the AI's layout and an arrange, and
   themes.py's MARGIN is the same number. */
const TH_MARGIN = 10;
const TH_ROW = 40;       // reading a theme row by row: tops within half a card's height share a row
const TH_FRAME_X = 14;   // a theme's frame, round its label and its members
const TH_FRAME_Y = 12;
/* A label with no title. The file keeps the English word, "Untitled", as it keeps the workbook's headings, so a
   board saved in one language reads as untitled in every other (i18nleft, 1 November 2026): what is kept goes
   through thLabelKept, what is shown through thLabelShown, in the page's language, and thUntitled asks either. */
const TH_UNTITLED_SAVED = 'Untitled';
const TH_UNTITLED = t('themes.untitled');
const thUntitled = (label) => { const s = String(label || '').trim(); return !s || s === TH_UNTITLED_SAVED || s === TH_UNTITLED; };
const thLabelKept = (text) => (thUntitled(text) ? TH_UNTITLED_SAVED : text);
const thLabelShown = (label) => (label === TH_UNTITLED_SAVED ? TH_UNTITLED : label);
/* A sticky note's four papers, yellow the one a new note takes, and its size before it is measured:
   the widest a note runs and one line's height. A note fits its words, 64px wide at the least and
   160px at the most, wrapping there and growing down, and every measure of the spacing takes the
   size the page measures on it, never this one. */
const TH_STICKY_COLOURS = ['yellow', 'pink', 'green', 'blue'];
const TH_STICKY = { w: 160, h: 47 };

function thGroup(v, id) { return v.groups.find((g) => g.id === id) || null; }
const thIsGroup = (v, item) => v.groups.some((g) => g.id === item);
const thOnCanvas = (v, key) => !!v.cards[key] && !v.discarded.includes(key) && !thTopOf(v, key) && !thWaiting(v, key);

/* ── the board's sidebar (Adam, 20 October, way A of the drawings): no bin ──
   On the PETs board a statement in no PET waits in the sidebar's Not placed, off the canvas, marked
   `wait`, until he puts it on the board, where it lies loose, placed but in no PET yet. What the bin held,
   `discarded`, is Set aside, in the sidebar too. A board marked `waits` has the sidebar, the PETs board
   alone: on the GETs board a card in no GET stands on the canvas as before. A card in a PET is never
   waiting, whatever it carries, so `wait` is read only for a card in none. */
const thWaits = (v) => !!(v && v.waits);
function thWaiting(v, key) {
  const c = v && v.cards[key];
  if (!c || !c.wait || !thWaits(v) || v.discarded.includes(key) || thTopOf(v, key)) return false;
  return !v.groups.some((g) => g.members.includes(key));
}
/* the statements waiting in Not placed in interview order, sheet by sheet as the workbook has them, then
   row and line, one missing from the workbook last */
function thWaitingKeys(v, sheets = []) {
  return Object.keys(v.cards).filter((key) => thWaiting(v, key)).sort((a, b) => thInterviewCmp(v, a, b, sheets));
}
function thInterviewCmp(v, a, b, sheets = []) {
  const ca = v.cards[a];
  const cb = v.cards[b];
  if (!!ca.missing !== !!cb.missing) return ca.missing ? 1 : -1;
  const sa = sheets.indexOf(ca.sheet);
  const sb = sheets.indexOf(cb.sheet);
  if (sa !== sb) return (sa < 0 ? 1e6 : sa) - (sb < 0 ? 1e6 : sb);
  return (Number(ca.row) || 0) - (Number(cb.row) || 0) || (Number(ca.line) || 0) - (Number(cb.line) || 0)
    || String(a).localeCompare(String(b));
}
/* `wait` as the board came: a card in no PET, not set aside and not stacked waits in Not placed unless the file
   has it `loose`, on the canvas */
function thWaitsRead(v) {
  if (!v) return;
  const parents = thParents(v);
  for (const [key, c] of Object.entries(v.cards)) {
    c.wait = !!(v.waits && !c.loose && parents[key] === undefined && !v.discarded.includes(key) && !thTopOf(v, key));
  }
}
/* statements sent to wait in Not placed, out of whatever PET held them, as Take out of PET and Backspace
   do. The keys sent. */
function thSendWaiting(v, keys) {
  if (thLocked(v) || !thWaits(v)) return [];
  const out = [];
  for (const key of keys) {
    const c = v.cards[key];
    if (!c || thTopOf(v, key)) continue;
    thDetach(v, key);
    v.discarded = v.discarded.filter((k) => k !== key);
    c.wait = true;
    out.push(key);
  }
  return out;
}
/* a statement from the sidebar put on the board at (x, y), its top-left corner, loose until a drop puts it in
   a PET: out of Set aside when it was there. True when it moved. */
function thPutOn(v, key, x, y) {
  const c = v.cards[key];
  if (thLocked(v) || !c || thTopOf(v, key)) return false;
  v.discarded = v.discarded.filter((k) => k !== key);
  if (thWaits(v)) c.wait = false;
  Object.assign(c, { x: Math.round(x), y: Math.round(y) });
  return true;
}
const thExists = (v, item) => thIsGroup(v, item) || thOnCanvas(v, item);

/* ── stacks: statements stacked under a better one (Adam, 19 October) ── */

/* One point said several ways close together in the transcript: the others go under the statement
   that says it best, the top, which stands for them in the PETs table and the exports, and they stay
   one click away for the audit trail. A stack is one level deep, the top over all the rest. */
const thStacks = (v) => (v && v.stacks && typeof v.stacks === 'object' ? v.stacks : {});
const thStackOf = (v, key) => thStacks(v)[key] || [];
function thTopOf(v, key) {
  const stacks = thStacks(v);
  for (const top in stacks) if (stacks[top].includes(key)) return top;
  return null;
}
function thStacksTidy(v) {
  for (const top of Object.keys(thStacks(v))) if (!v.stacks[top].length) delete v.stacks[top];
}

/* `items` stacked under `top`, as a drop on its middle or S does: each leaves its label, the bin or
   another stack, and one that was a top brings its own stack, after it. `top` keeps its place, and a
   statement stacked under another is never a top. The ones stacked. */
function thStackOnto(v, items, top) {
  if (thLocked(v) || !v.cards[top] || thTopOf(v, top)) return [];
  if (!v.stacks) v.stacks = {};
  let held = thStackOf(v, top).slice();
  const done = [];
  for (const key of items) {
    if (key === top || !v.cards[key]) continue;
    const brought = thStackOf(v, key).slice();
    delete v.stacks[key];
    for (const t of Object.keys(v.stacks)) v.stacks[t] = v.stacks[t].filter((k) => k !== key);
    thDetach(v, key);
    v.discarded = v.discarded.filter((k) => k !== key);
    held = held.filter((k) => k !== key && !brought.includes(k)).concat([key], brought.filter((k) => k !== top));
    done.push(key);
  }
  v.stacks[top] = held;
  thStacksTidy(v);
  return done;
}

/* One taken out of its stack: into its top's label, after the top, or Not placed when the top is in
   none or in the bin, at `at` when given. Its top, or null when it was in no stack. */
function thTakeOut(v, key, at) {
  const top = thTopOf(v, key);
  if (thLocked(v) || !top) return null;
  // one taken out of a stack waiting in Not placed waits there too, beside its top
  if (v.cards[key] && thWaits(v)) v.cards[key].wait = thWaiting(v, top);
  v.stacks[top] = v.stacks[top].filter((k) => k !== key);
  thStacksTidy(v);
  const owner = v.discarded.includes(top) ? undefined : thParents(v)[top];
  const g = owner !== undefined ? thGroup(v, owner) : null;
  if (g) g.members.splice(g.members.indexOf(top) + 1, 0, key);
  if (at) Object.assign(v.cards[key], { x: Math.round(at.x), y: Math.round(at.y) });
  return top;
}

/* One put on top of the stack it is in, in its top's place, its label, its spot or the bin, the old
   top first under it. The old top, or null. */
function thMakeTop(v, key) {
  const top = thTopOf(v, key);
  if (thLocked(v) || !top) return null;
  const rest = [top].concat(v.stacks[top].filter((k) => k !== key));
  delete v.stacks[top];
  v.stacks[key] = rest;
  for (const g of v.groups) g.members = g.members.map((m) => (m === top ? key : m));
  v.discarded = v.discarded.map((k) => (k === top ? key : k));
  Object.assign(v.cards[key], { x: v.cards[top].x, y: v.cards[top].y });
  return top;
}

/* ── sticky notes: his own words to himself on the canvas, never a statement and never a member ── */

const thStickies = (v) => (v && Array.isArray(v.stickies) ? v.stickies : []);
const thSticky = (v, id) => thStickies(v).find((n) => n.id === id) || null;
const thIsSticky = (v, id) => thStickies(v).some((n) => n.id === id);
/* what stands on the canvas: a card not discarded, a label, or a sticky note */
const thHere = (v, item) => thExists(v, item) || thIsSticky(v, item);
/* a colour's name, for the menu and the Inspector's dots */
const thColourName = (c) => ({ yellow: t('themes.sticky.yellow'), pink: t('themes.sticky.pink'), green: t('themes.sticky.green'), blue: t('themes.sticky.blue') })[c] || c;
/* a note's words, its ends stripped and its lines kept */
const thStickyClean = (text) => String(text || '').replace(/\r\n?/g, '\n').trim();

/* A revision of the board on view is read-only, marked `readonly`. Every act below that changes
   a board leaves one so marked as it is, and the screen offers only what changes nothing:
   selecting, the lasso, the panel and its player, the pile's list, the view, and copying a theme
   to a board. */
const thLocked = (v) => !!(v && v.readonly);
const TH_VIEW_ACTS = ['select', 'lasso', 'panel', 'play', 'pan', 'zoom', 'pile', 'copy', 'menu'];
const thMayAct = (v, act) => !thLocked(v) || TH_VIEW_ACTS.includes(act);

function thParents(v) {
  const out = {};
  for (const g of v.groups) for (const m of g.members) out[m] = g.id;
  // a sticky note sits in the group its `in` names, which is never a membership
  for (const n of thStickies(v)) if (n.in && thIsGroup(v, n.in)) out[n.id] = n.in;
  return out;
}

function thAncestors(v, item, parents = thParents(v)) {
  const out = [];
  let at = parents[item];
  while (at !== undefined && !out.includes(at)) { out.push(at); at = parents[at]; }
  return out;
}

function thDescendants(v, id, out = []) {
  const g = thGroup(v, id);
  if (!g) return out;
  for (const m of g.members) {
    if (out.includes(m)) continue;
    out.push(m);
    thDescendants(v, m, out);
  }
  return out;
}

/* every card a group holds, however deep, for the count beside its title */
const thCardsUnder = (v, id) => thDescendants(v, id).filter((m) => thOnCanvas(v, m));

/* What a label says after its title, and in its tooltip: `3 statements`, on a PET over sub-themes
   `2 sub-themes · 7 statements`, and on a sub-theme or a group over groups `2 groups · 7
   statements`, the labels it holds itself and the statements at any depth. */
function thCountText(v, id) {
  const g = thGroup(v, id);
  if (!g) return '';
  const n = thCardsUnder(v, id).length;
  const subs = g.members.filter((m) => thIsGroup(v, m)).length;
  const said = t('themes.count.statements', { n });
  const inner = thAncestors(v, id).length ? 'themes.count.groups_then' : 'themes.count.subs_then';
  return subs ? t(inner, { n: subs, said }) : said;
}

/* The number in a PET's badge on its frame's bottom-left corner: its statements at any depth, 0
   when it holds none. The label carries its title alone, and its tooltip and the Inspector keep the
   whole of `thCountText`. */
const thBadgeText = (v, id) => String(thCardsUnder(v, id).length);

/* What the screen calls a label, in IPA's own words: a PET at the top of the canvas, a sub-theme
   inside a PET, and a group inside a sub-theme, and a group inside a group, as deep as he likes. */
function thUnit(v, id, parents = thParents(v)) {
  const depth = thAncestors(v, id, parents).length;
  if (!depth) return typeof TH !== 'undefined' && TH.mode === 'gets' ? thGetWord() : t('themes.unit.pet');
  return depth === 1 ? t('themes.unit.sub') : t('themes.unit.group');
}

/* the same name at the head of a line, "Sub-theme", "Group", and a PET or a GET as it is */
const thUnitHead = (unit) => unit.charAt(0).toUpperCase() + unit.slice(1);

function thNextId(v) {
  // on the GETs screen a label is a GET, G1, G2, apart from the PETs' ids its cards carry
  const big = typeof TH !== 'undefined' && TH.mode === 'gets';
  let n = 0;
  for (const g of v.groups) {
    const m = (big ? /^G(\d+)$/ : /^g(\d+)$/).exec(g.id);
    if (m) n = Math.max(n, Number(m[1]));
  }
  return `${big ? 'G' : 'g'}${n + 1}`;
}

/* The tints never repeat. Top-level themes take the eight in turn, each its own: a theme keeps the
   one its number gives it, g1 the first, while no theme before it holds that one, and takes the
   next free one when one does. Past the eight a theme is grey, never a tint already in use. A
   sub-theme takes its theme's tint a step lighter, and a sub-theme of that a step lighter again.
   Each group's answer is its tint, a number or 'grey', and its step. */
function thTints(v) {
  const parents = thParents(v);
  const out = {};
  const used = new Set();
  for (const g of v.groups) {
    if (parents[g.id] !== undefined) continue;
    const m = /(\d+)$/.exec(String(g.id));
    const want = m ? (Number(m[1]) + TH_HUES - 1) % TH_HUES : 0;
    let hue = 'grey';
    for (let i = 0; i < TH_HUES; i += 1) {
      if (!used.has((want + i) % TH_HUES)) { hue = (want + i) % TH_HUES; break; }
    }
    if (hue !== 'grey') used.add(hue);
    out[g.id] = { hue, step: 0 };
  }
  const walk = (id, hue, step, seen) => {
    for (const m of thGroup(v, id).members) {
      if (!thIsGroup(v, m) || seen.has(m)) continue;
      out[m] = { hue, step: Math.min(step, 2) };
      walk(m, hue, step + 1, new Set([...seen, m]));
    }
  };
  for (const id of Object.keys(out)) walk(id, out[id].hue, 1, new Set([id]));
  // a group in no tree, which normalise never lets through, still draws
  for (const g of v.groups) if (!out[g.id]) out[g.id] = { hue: 'grey', step: 0 };
  return out;
}

/* the classes a tint is drawn with */
const thTintClass = (t) => (t ? `hue-${t.hue}${t.step ? ` step-${t.step}` : ''}` : '');

/* the items of a selection that no other item of it holds: a label and one of its own cards
   selected together are the label */
function thTop(v, items) {
  const set = new Set(items);
  const parents = thParents(v);
  return [...set].filter((it) => !thAncestors(v, it, parents).some((a) => set.has(a)));
}

function thDetach(v, item) {
  if (thLocked(v)) return;
  for (const g of v.groups) {
    const at = g.members.indexOf(item);
    if (at >= 0) g.members.splice(at, 1);
  }
}

/* `g`: a new label over the selection, which then belongs to it. Items that all sat in one group
   make a group inside that group, in their place, so a sub-theme drawn out of a theme stays in
   it. Anything else leaves the group it was in. Returns the new group's id. */
function thMakeGroup(v, items, label) {
  if (thLocked(v)) return null;
  const top = thTop(v, items.filter((it) => thExists(v, it)));
  if (!top.length) return null;
  const parents = thParents(v);
  const shared = parents[top[0]];
  const common = shared !== undefined && top.every((it) => parents[it] === shared) ? thGroup(v, shared) : null;
  const at = common ? Math.min(...top.map((it) => common.members.indexOf(it))) : -1;
  top.forEach((it) => thDetach(v, it));
  const id = thNextId(v);
  v.groups.push({ id, label: thLabelKept(String(label || '').trim()), members: top, x: 0, y: 0 });
  if (common) common.members.splice(Math.min(at, common.members.length), 0, id);
  return id;
}

/* An empty label at (x, y), inside the label `inside` names, at the end of what it holds, or at the top
   of the board with none: G with nothing selected, and New group inside (20 October). Its id, or null on
   a revision on view or when `inside` is no label. */
function thMakeEmpty(v, inside, x, y) {
  if (thLocked(v) || (inside && !thIsGroup(v, inside))) return null;
  const id = thNextId(v);
  v.groups.push({ id, label: TH_UNTITLED_SAVED, members: [], x: Math.round(x), y: Math.round(y) });
  if (inside) thGroup(v, inside).members.push(id);
  return id;
}

/* a drop on a cluster: each item joins the group, unless it is the group, or holds it */
function thJoin(v, items, gid) {
  if (thLocked(v)) return [];
  const target = thGroup(v, gid);
  if (!target) return [];
  const joined = [];
  for (const it of items) {
    if (it === gid || !(thExists(v, it) || thWaiting(v, it))) continue;
    if (v.cards[it] && thWaits(v)) v.cards[it].wait = false;
    const parents = thParents(v);
    if (parents[it] === gid) continue;
    if (thIsGroup(v, it) && thAncestors(v, gid, parents).includes(it)) continue;
    thDetach(v, it);
    target.members.push(it);
    joined.push(it);
  }
  return joined;
}

function thLeave(v, item) {
  if (thLocked(v)) return undefined;
  const was = thParents(v)[item];
  const note = thSticky(v, item);
  if (note) delete note.in; else thDetach(v, item);
  return was;
}

/* Deleting a label frees what it held and loses nothing else: its members take its place in the
   group above it, or stand free when there is none. */
function thDelete(v, gid) {
  if (thLocked(v)) return false;
  const g = thGroup(v, gid);
  if (!g) return false;
  const parent = thGroup(v, thParents(v)[gid]);
  if (parent) parent.members.splice(parent.members.indexOf(gid), 1, ...g.members);
  // its sticky notes go where its members go: into the label above it, or standing free
  for (const n of thStickies(v)) {
    if (n.in !== gid) continue;
    if (parent) n.in = parent.id; else delete n.in;
  }
  v.groups = v.groups.filter((x) => x.id !== gid);
  return true;
}

/* A new sticky note at (x, y), yellow and empty, inside the group `gid` names when there is one.
   Its id, or null on a revision on view or a board from a server before the notes. */
function thStickyMake(v, x, y, gid) {
  if (thLocked(v) || !Array.isArray(v.stickies)) return null;
  let top = 0;
  for (const n of v.stickies) {
    const m = /^n(\d+)$/.exec(n.id);
    if (m) top = Math.max(top, Number(m[1]));
  }
  const id = `n${top + 1}`;
  const note = { id, text: '', colour: TH_STICKY_COLOURS[0], x: Math.round(x), y: Math.round(y) };
  if (gid && thIsGroup(v, gid)) note.in = gid;
  v.stickies.push(note);
  return id;
}

/* a note taken off the board, which only undo brings back. True when it was there. */
function thStickyRemove(v, id) {
  if (thLocked(v)) return false;
  const at = thStickies(v).findIndex((n) => n.id === id);
  if (at < 0) return false;
  v.stickies.splice(at, 1);
  return true;
}

/* A note's words, or its colour, changed. True when they changed. */
function thStickyText(v, id, text) {
  const n = thLocked(v) ? null : thSticky(v, id);
  const now = thStickyClean(text);
  if (!n || n.text === now) return false;
  n.text = now;
  return true;
}

function thStickyColour(v, id, colour) {
  const n = thLocked(v) ? null : thSticky(v, id);
  if (!n || !TH_STICKY_COLOURS.includes(colour) || n.colour === colour) return false;
  n.colour = colour;
  return true;
}

/* Sticky notes that come inside a group: each note named that is not in it already. */
function thStickiesJoin(v, ids, gid) {
  if (thLocked(v) || !thIsGroup(v, gid)) return [];
  const joined = [];
  for (const id of ids) {
    const n = thSticky(v, id);
    if (!n || n.in === gid) continue;
    n.in = gid;
    joined.push(id);
  }
  return joined;
}

/* A card set aside leaves the canvas and every group, into the sidebar's Set aside (until 20 October the
   bin). Put back, it waits in Not placed, or on the GETs board stands in no GET. */
function thDiscard(v, keys) {
  if (thLocked(v)) return [];
  const out = [];
  for (const key of keys) {
    if (!v.cards[key] || v.discarded.includes(key)) continue;
    thDetach(v, key);
    v.discarded.push(key);
    if (thWaits(v)) v.cards[key].wait = false;
    out.push(key);
  }
  return out;
}

function thRestore(v, key, x, y) {
  if (thLocked(v)) return false;
  const at = v.discarded.indexOf(key);
  if (at < 0) return false;
  v.discarded.splice(at, 1);
  if (v.cards[key]) Object.assign(v.cards[key], { x: Math.round(x), y: Math.round(y) });
  // on the PETs board it goes back to wait in Not placed
  if (v.cards[key] && thWaits(v)) v.cards[key].wait = true;
  return true;
}

function thCounts(v) {
  const parents = thParents(v);
  // a statement in no PET counts as not placed, waiting in the sidebar or loose on the canvas alike
  const out = { placed: 0, unplaced: 0, discarded: 0, missing: 0 };
  for (const [key, card] of Object.entries(v.cards)) {
    if (card.missing) out.missing += 1;
    else if (thTopOf(v, key)) continue; // a stacked statement, which its top stands for
    else if (v.discarded.includes(key)) out.discarded += 1;
    else if (parents[key] !== undefined) out.placed += 1;
    else out.unplaced += 1;
  }
  return out;
}

/* ── a theme's note: his own words on why it exists, what it holds, what it answers ── */

const thNoteOf = (g) => String((g && g.note) || '').trim();

/* A theme's note set, stripped, and gone when it is blank. True when it changed. */
function thSetNote(v, gid, text) {
  if (thLocked(v)) return false;
  const g = thGroup(v, gid);
  if (!g) return false;
  const now = String(text || '').trim();
  if (now === thNoteOf(g)) return false;
  if (now) g.note = now; else delete g.note;
  return true;
}

/* A label's description (Adam, 21 October): the longer line under its short title, a secondary heading on the
   board, in the Table view and on the printouts, so the ladder of abstraction shows. His own field, apart from
   the note: one line however it is typed, no limit on its length, "" for none, and a label with none carries
   none, so a board without descriptions reads and saves as it did. */
const thDescOf = (g) => String((g && g.description) || '').replace(/\s+/g, ' ').trim();

/* A label's description set, on one line, and gone when it is blank. True when it changed. */
function thSetDesc(v, gid, text) {
  if (thLocked(v)) return false;
  const g = thGroup(v, gid);
  if (!g) return false;
  const now = String(text || '').replace(/\s+/g, ' ').trim();
  if (now === thDescOf(g)) return false;
  if (now) g.description = now; else delete g.description;
  return true;
}

/* the words of an act on a description, as its step of undo names it */
const thDescStep = (g) => (thDescOf(g) ? t('themes.step.desc_written') : t('themes.step.desc_removed'));

/* ── picks: the quotes ticked to carry a theme ── */

/* the row a card or a quote sits on: `Initial:12:0` is on `Initial:12` */
function thRowOf(key) {
  const parts = String(key).split(':');
  parts.pop();
  return parts.join(':');
}

/* the rows a group's cards sit on, at any depth, once each */
const thRowsUnder = (v, gid) => [...new Set(thCardsUnder(v, gid).map(thRowOf))];

/* A group's picks keep only quotes of a row with a card under it, once each, so a card that leaves
   takes its row's picks with it and a label that goes takes its own. Undo puts them back. */
function thPrunePicks(v) {
  if (thLocked(v)) return v.picks || {};
  const out = {};
  for (const [gid, keys] of Object.entries(v.picks || {})) {
    if (!thIsGroup(v, gid)) continue;
    const rows = new Set(thRowsUnder(v, gid));
    const kept = [...new Set(keys)].filter((k) => rows.has(thRowOf(k)));
    if (kept.length) out[gid] = kept;
  }
  v.picks = out;
  return out;
}

/* a tick on, or off. True when it is now on. */
function thTogglePick(v, gid, qkey) {
  if (thLocked(v)) return false;
  if (!v.picks) v.picks = {};
  const list = (v.picks[gid] || []).slice();
  const at = list.indexOf(qkey);
  if (at >= 0) list.splice(at, 1); else list.push(qkey);
  if (list.length) v.picks[gid] = list; else delete v.picks[gid];
  return at < 0;
}

/* What the panel lists for a card or a label: the rows its cards sit on, in transcript order, each
   with the cards on it in line order, the row's timecode and the quotes of those cards, each
   statement's own, a quote's key being its statement's (item 198). A label keeps its picks there
   too, so a quote picked before its statement went to another PET stays in sight. `quotes` is the
   server's map of rows that have any, `sheets` the sheets in workbook order. A label lists every
   card under it at any depth, so a label over labels has the quotes of all of them. */
function thPanelRows(v, item, quotes, sheets) {
  const keys = item.kind === 'card' ? (v.cards[item.id] ? [item.id] : []) : thCardsUnder(v, item.id);
  const picked = new Set(item.kind === 'card' ? [] : ((v.picks || {})[item.id] || []));
  const rows = {};
  for (const key of keys) {
    const c = v.cards[key];
    const at = thRowOf(key);
    if (!rows[at]) rows[at] = { row: at, sheet: c.sheet, n: c.row, cards: [], seconds: c.seconds, time: c.time };
    rows[at].cards.push(key);
  }
  const place = (s) => { const i = (sheets || []).indexOf(s); return i < 0 ? (sheets || []).length : i; };
  return Object.values(rows)
    .sort((a, b) => place(a.sheet) - place(b.sheet) || (a.n || 0) - (b.n || 0))
    .map((r) => {
      const held = (quotes || {})[r.row];
      r.cards.sort((a, b) => (v.cards[a].line || 0) - (v.cards[b].line || 0));
      if (held) Object.assign(r, { seconds: held.seconds, time: held.time });
      r.quotes = held ? held.quotes.filter((q) => r.cards.includes(q.key) || picked.has(q.key)) : [];
      return r;
    });
}

/* ── the AI's help: what a name suggestion is asked about ── */

/* What n names: a label alone, a PET or a sub-theme, never a card. One label selected is that
   label, and so is the label the Inspector shows when it is among the selection or nothing is
   selected. Cards selected with no label are `cards`, which says to group them first, and anything
   else is null. */
const TH_GROUP_FIRST = t('themes.names.group_first');

function thNamesTarget(v, sel, panel) {
  const picked = thTop(v, [...sel.groups].filter((id) => thIsGroup(v, id))
    .concat([...sel.cards].filter((key) => thOnCanvas(v, key))));
  const labels = picked.filter((it) => thIsGroup(v, it));
  if (picked.length === 1 && labels.length === 1) return { kind: 'group', id: labels[0] };
  if (panel && panel.kind === 'group' && thIsGroup(v, panel.id) && (!picked.length || picked.includes(panel.id))) {
    return { kind: 'group', id: panel.id };
  }
  if (labels.length === 1) return { kind: 'group', id: labels[0] };
  if (picked.length && !labels.length) return { kind: 'cards' };
  return null;
}

/* a target's own key, and the panel's, so the names asked for one show only beside it */
const thNamesKey = (t) => `g:${t.id}`;
const thPanelKey = (item) => (item.kind === 'group' ? `g:${item.id}` : item.kind === 'sticky' ? `n:${item.id}` : `s:${item.id}`);

/* What a name suggestion sends: the label by its id and the board it is on, and the server reads
   the board and the workbook for the rest. The statements under it, its title, its note and every
   other label once go too, the shape a server from before this reads, so the titles still come
   back from one that has not been restarted. */
function thNamesBody(v, target) {
  const own = thGroup(v, target.id);
  const others = [];
  for (const g of v.groups) {
    if (g.id === own.id) continue;
    if (g.label && !thUntitled(g.label) && !others.includes(g.label)) others.push(g.label);
  }
  const body = { version: TH.meta ? TH.meta.id : null, group: own.id,
    statements: thCardsUnder(v, own.id).filter((key) => v.cards[key]).map((key) => v.cards[key].text),
    label: !thUntitled(own.label) ? own.label : '', others };
  // a label's note goes with it when it has one, for a server from before this
  if (thNoteOf(own)) body.note = thNoteOf(own);
  return body;
}

/* ── geometry, in the canvas's own units ── */

function thUnion(boxes) {
  const x = Math.min(...boxes.map((b) => b.x));
  const y = Math.min(...boxes.map((b) => b.y));
  const r = Math.max(...boxes.map((b) => b.x + b.w));
  const b = Math.max(...boxes.map((q) => q.y + q.h));
  return { x, y, w: r - x, h: b - y };
}

const thMeets = (a, b, margin = 0) => a.x < b.x + b.w + margin && b.x < a.x + a.w + margin
  && a.y < b.y + b.h + margin && b.y < a.y + a.h + margin;

const thPad = (b) => ({ x: b.x - TH_FRAME_X, y: b.y - TH_FRAME_Y, w: b.w + 2 * TH_FRAME_X, h: b.h + 2 * TH_FRAME_Y });

const thCentreIn = (box, rect) => {
  const cx = box.x + box.w / 2;
  const cy = box.y + box.h / 2;
  return cx >= rect.x && cx <= rect.x + rect.w && cy >= rect.y && cy <= rect.y + rect.h;
};

/* Where every label sits: above what it holds, its left edge on theirs, worked out from the
   members up, so a label over labels sits above the frames of the labels it holds. A label with
   nothing in it stays where it was put. `size(item)` is the measured size of a card or a label.
   `apart` is what a group leaves out of its body for now: what a drag moves, for telling where a
   drop lands, or what Alt takes out of its theme while the drag lasts. A group that keeps members
   behind keeps its label and its frame with them, and with `strict` a group left with none has no
   body at all. Each group's answer is its label, its body (the members, a sub-theme by its frame),
   the two together, and its frame round them. `pins`, while a drag lasts, holds a label by its id where
   it stood as the drag began, its frame still running round what it holds (see thDragLayout). */
function thLayout(v, size, apart, strict = false, pins = null) {
  const out = {};
  const busy = new Set();
  const visit = (id) => {
    if (out[id]) return out[id];
    if (busy.has(id)) return null;
    busy.add(id);
    const g = thGroup(v, id);
    // its sticky notes are part of what it holds, so its frame runs round them too
    const present = g.members.filter((m) => thExists(v, m))
      .concat(thStickies(v).filter((n) => n.in === id).map((n) => n.id));
    let use = apart ? present.filter((m) => !apart.has(m)) : present;
    if (!use.length && !strict) use = present;
    const boxes = [];
    for (const m of use) {
      if (thIsGroup(v, m)) {
        const inner = visit(m);
        if (inner) boxes.push(inner.frame);
      } else {
        const c = v.cards[m] || thSticky(v, m);
        const s = size(m);
        boxes.push({ x: c.x, y: c.y, w: s.w, h: s.h });
      }
    }
    const s = size(id);
    const body = boxes.length ? thUnion(boxes) : null;
    const pin = pins && pins[id];
    if (pin) { g.x = pin.x; g.y = pin.y; } else if (body) { g.x = Math.round(body.x); g.y = Math.round(body.y - TH_GAP - s.h); }
    const label = { x: g.x, y: g.y, w: s.w, h: s.h };
    const all = body ? thUnion([label, body]) : label;
    out[id] = { label, body, all, frame: thPad(all) };
    busy.delete(id);
    return out[id];
  };
  for (const g of v.groups) visit(g.id);
  return out;
}

/* What moves when the selection is dragged: the cards and sticky notes selected, the labels
   selected and all they hold, and any group every member of which is moving, so its label goes
   with them. A group that moves takes its sticky notes with it. */
function thMoving(v, cards, groups, stickies = []) {
  const set = new Set();
  for (const key of cards) if (thOnCanvas(v, key)) set.add(key);
  for (const id of stickies) if (thIsSticky(v, id)) set.add(id);
  for (const id of groups) {
    if (!thIsGroup(v, id)) continue;
    set.add(id);
    for (const d of thDescendants(v, id)) if (thExists(v, d)) set.add(d);
  }
  let grew = true;
  while (grew) {
    grew = false;
    for (const g of v.groups) {
      if (set.has(g.id)) continue;
      const present = g.members.filter((m) => thExists(v, m));
      if (present.length && present.every((m) => set.has(m))) { set.add(g.id); grew = true; }
    }
  }
  for (const n of thStickies(v)) if (n.in && set.has(n.in)) set.add(n.id);
  return set;
}

/* What Alt takes out of its theme while a drag lasts: each item dragged whose theme is not dragged
   with it. */
function thLeavers(v, moving) {
  const parents = thParents(v);
  return new Set([...moving].filter((it) => parents[it] !== undefined && !moving.has(parents[it])));
}

/* The frames as a drag draws them. Every theme reaches out to what is dragged, live, so a member
   taken far shows its frame following it there, and a sub-theme dragged inside its theme stretches
   that theme's frame the same way. With Alt held, what leaves is left out of the frame it is
   leaving, so the leaving shows before the drop. With `from`, where each label stood as the drag began
   (a drag's `from.groups`), every label not dragged stays there while the drag lasts (31 October, design
   A: no PET or sub-PET moves out of the way, so a title never runs from the pointer), its frame
   stretching round what it holds, and the drop lays it out again. */
function thDragLayout(v, size, moving, alt, from = null) {
  const pins = from ? Object.fromEntries(Object.entries(from).filter(([id]) => !moving.has(id))) : null;
  return alt ? thLayout(v, size, thLeavers(v, moving), true, pins) : thLayout(v, size, null, false, pins);
}

/* The bodies a drop takes what is dragged into, by their frames as the drag begins (31 October, design A:
   let go inside a PET or sub-PET and it goes in, keeping its level). Statements and sticky notes go into the
   innermost PET, sub-PET or group the pointer is in. A PET, a sub-PET or a group goes into the frames one level
   above its own, a sub-PET into a PET and a group into a sub-PET, and a PET into none. With labels of two
   levels dragged together the higher one says. Null with nothing dragged. */
function thBodiesFor(v, moving, layout) {
  const parents = thParents(v);
  const top = [...moving].filter((it) => !moving.has(parents[it]));
  const labels = top.filter((it) => thIsGroup(v, it));
  const all = thFrames(layout);
  if (!labels.length) return top.length ? all : null;
  const level = (id) => thAncestors(v, id, parents).length;
  const want = Math.min(...labels.map(level)) - 1;
  if (want < 0) return null;
  return Object.fromEntries(Object.entries(all).filter(([id]) => thIsGroup(v, id) && level(id) === want));
}

/* The innermost frame a point falls in, leaving out what moves: the theme a drop there joins. */
function thFrameAt(v, layout, pt, moving) {
  let best = null;
  let area = Infinity;
  for (const g of v.groups) {
    if (moving && moving.has(g.id)) continue;
    const f = layout[g.id] && layout[g.id].frame;
    if (!f || pt.x < f.x || pt.x > f.x + f.w || pt.y < f.y || pt.y > f.y + f.h) continue;
    if (f.w * f.h < area) { best = g.id; area = f.w * f.h; }
  }
  return best;
}

/* Where each PET's badge sits along the foot of its frame, from the frame's left edge: a corner's
   radius in, and stepped right past the badge of a sub-theme whose frame comes down to the same
   corner, so two badges never lie over each other. `widths` are the badges' measured widths. */
const TH_BADGE_X = 12;
const TH_BADGE_H = 14;
function thBadgeSpots(v, layout, widths = {}) {
  const parents = thParents(v);
  const depth = (id) => thAncestors(v, id, parents).length;
  const spots = {};
  const order = v.groups.map((g) => g.id).filter((id) => layout[id] && layout[id].frame)
    .sort((a, b) => depth(b) - depth(a));
  for (const id of order) {
    const f = layout[id].frame;
    const spot = { x: f.x + TH_BADGE_X, y: f.y + f.h - TH_BADGE_H / 2, w: widths[id] || 20, h: TH_BADGE_H };
    const inner = thGroup(v, id).members.filter((m) => spots[m]).map((m) => spots[m]).sort((a, b) => a.x - b.x);
    for (const o of inner) if (thMeets(spot, o, 4)) spot.x = o.x + o.w + 4;
    spots[id] = spot;
  }
  const out = {};
  for (const id of order) out[id] = Math.round(spots[id].x - layout[id].frame.x);
  return out;
}

/* What a drop does to membership. Leaving a theme is an act of its own, so a member dropped
   anywhere stays a member. `target` is the group the pointer let go over, through its label or one
   of its cards, and failing that `frame` is the innermost frame it let go in: what moved joins that
   group, a card as a member and a label as a sub-theme, which takes it out of the one it was in.
   A label never joins a group it holds. With `leave`, Alt held at the drop, what moved and is in a
   theme leaves it where it lands, unless it lands in another theme, which it joins as before. */
function thDrop(v, moving, target, frame, leave = false) {
  if (thLocked(v)) return { joined: [], left: [], dest: null };
  const parents = thParents(v);
  const top = [...moving].filter((it) => !moving.has(parents[it]));
  const ok = (g) => g && !moving.has(g) && thIsGroup(v, g);
  const dest = ok(target) ? target : ok(frame) ? frame : null;
  // a sticky note comes inside the group as a card joins it, though it never becomes a member
  const notes = top.filter((it) => thIsSticky(v, it));
  const joined = dest ? thJoin(v, top.filter((it) => !notes.includes(it) && !(leave && parents[it] === dest)), dest)
    .concat(thStickiesJoin(v, notes, dest)) : [];
  const left = [];
  if (leave) {
    for (const it of top) {
      if (joined.includes(it) || parents[it] === undefined || (dest && parents[it] !== dest)) continue;
      thLeave(v, it);
      left.push(it);
    }
  }
  return { joined, left, dest };
}

/* ── nothing overlaps ── */

/* The passes a push runs for: a neighbour pushed into a third pushes that one too, eight times
   over at most, and then it stops. */
const TH_PASSES = 8;

/* What a card or a theme takes up among its neighbours: a card its own box, a theme its frame, and
   a label with nothing in it the label alone. */
function thSolid(v, size, layout, id) {
  if (thIsGroup(v, id)) {
    const l = layout[id];
    return l ? (l.body ? l.frame : l.label) : null;
  }
  const c = v.cards[id] || thSticky(v, id);
  const s = size(id);
  return { x: c.x, y: c.y, w: s.w, h: s.h };
}

/* Who stands beside whom, by where they stand: the canvas, '', holds every card in no theme and
   every theme at the top, each by its frame, and a theme holds its own cards and its sub-themes,
   each sub-theme by its frame. Neighbours keep the margin clear between them, and what stands in
   different places never counts against each other, since a frame keeps what it holds inside it. */
function thNeighbours(v, parents = thParents(v)) {
  const out = new Map([['', []]]);
  for (const g of v.groups) out.set(g.id, []);
  const add = (id) => {
    const at = parents[id] === undefined || !out.has(parents[id]) ? '' : parents[id];
    out.get(at).push(id);
  };
  for (const g of v.groups) add(g.id);
  for (const key of Object.keys(v.cards)) if (thOnCanvas(v, key)) add(key);
  // a sticky note keeps the margin like a card, on the canvas or inside the theme it sits in
  for (const n of thStickies(v)) add(n.id);
  return out;
}

/* Every pair of neighbours nearer than the margin, the way the page weighs them: what a layout
   that needs no shift has none of. */
function thClashes(v, size) {
  const layout = thLayout(v, size, null);
  const out = [];
  for (const ids of thNeighbours(v).values()) {
    const boxes = ids.map((id) => [id, thSolid(v, size, layout, id)]);
    for (let i = 0; i < boxes.length; i += 1) {
      for (let j = i + 1; j < boxes.length; j += 1) {
        if (thMeets(boxes[i][1], boxes[j][1], TH_MARGIN)) out.push([boxes[i][0], boxes[j][0]]);
      }
    }
  }
  return out;
}

/* the smallest first, for the search below */
function thHeapPush(heap, item) {
  heap.push(item);
  let i = heap.length - 1;
  while (i > 0) {
    const up = (i - 1) >> 1;
    if (heap[up][0] <= heap[i][0]) break;
    [heap[up], heap[i]] = [heap[i], heap[up]];
    i = up;
  }
}

function thHeapPop(heap) {
  const top = heap[0];
  const last = heap.pop();
  if (heap.length) {
    heap[0] = last;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1;
      const r = l + 1;
      let m = i;
      if (l < heap.length && heap[l][0] < heap[m][0]) m = l;
      if (r < heap.length && heap[r][0] < heap[m][0]) m = r;
      if (m === i) break;
      [heap[m], heap[i]] = [heap[i], heap[m]];
      i = m;
    }
  }
  return top;
}

/* The shortest shift that leaves every box of `block` at least `gap` clear of every box of
   `others`, the block keeping its own arrangement, and { dx: 0, dy: 0 } when it is clear already.
   Best first from where it landed: a shift that still meets something offers the four ways past
   the first box it meets, and the nearest of those is tried next. `apart(a, b)` names the pairs
   that never count. Past `limit` tries the block goes beside everything, to the right. */
function thFreeOffset(block, others, gap, apart = () => false, limit = 3000) {
  if (!block.length || !others.length) return { dx: 0, dy: 0 };
  const first = (dx, dy) => {
    for (const b of block) {
      const at = { x: b.box.x + dx, y: b.box.y + dy, w: b.box.w, h: b.box.h };
      for (const o of others) if (!apart(b, o) && thMeets(at, o.box, gap)) return [at, o.box];
    }
    return null;
  };
  const heap = [[0, 0, 0]];
  const seen = new Set(['0,0']);
  while (heap.length && limit > 0) {
    limit -= 1;
    const [, dx, dy] = thHeapPop(heap);
    const hit = first(dx, dy);
    if (!hit) return { dx, dy };
    const [b, o] = hit;
    for (const [nx, ny] of [[dx + o.x + o.w + gap - b.x, dy], [dx + o.x - gap - b.w - b.x, dy],
      [dx, dy + o.y + o.h + gap - b.y], [dx, dy + o.y - gap - b.h - b.y]]) {
      const sx = nx > dx ? Math.ceil(nx) : Math.floor(nx);
      const sy = ny > dy ? Math.ceil(ny) : Math.floor(ny);
      if (seen.has(`${sx},${sy}`)) continue;
      seen.add(`${sx},${sy}`);
      thHeapPush(heap, [sx * sx + sy * sy, sx, sy]);
    }
  }
  const right = Math.max(...others.map((o) => o.box.x + o.box.w));
  return { dx: Math.ceil(right + gap - Math.min(...block.map((b) => b.box.x))), dy: 0 };
}

/* what moves as one: the items named and everything a label among them holds, its sticky notes
   included */
function thBlock(v, ids) {
  const out = new Set();
  for (const id of ids) {
    if (!thHere(v, id)) continue;
    out.add(id);
    if (thIsGroup(v, id)) for (const d of thDescendants(v, id)) if (thExists(v, d)) out.add(d);
  }
  for (const n of thStickies(v)) if (n.in && out.has(n.in)) out.add(n.id);
  return out;
}

function thShift(v, ids, dx, dy) {
  if (thLocked(v)) return;
  for (const id of ids) {
    const at = thIsGroup(v, id) ? thGroup(v, id) : (v.cards[id] || thSticky(v, id));
    if (at) { at.x = Math.round(at.x + dx); at.y = Math.round(at.y + dy); }
  }
}

/* ── the order a theme reads in, and arrange ── */

/* Ids in the order the canvas reads them: top to bottom, and left to right along a row, ids whose
   tops sit within half a card's height of the first in a row sharing it. Each spot is { id, x, y }.
   Inside a theme this is the order of how well each statement carries it, the best first. */
function thReadOrder(spots) {
  const rest = spots.slice().sort((a, b) => a.y - b.y || a.x - b.x);
  const out = [];
  while (rest.length) {
    const top = rest[0].y;
    const row = rest.filter((s) => s.y - top < TH_ROW).sort((a, b) => a.x - b.x || a.y - b.y);
    for (const s of row) { out.push(s.id); rest.splice(rest.indexOf(s), 1); }
  }
  return out;
}

/* A theme's own members as the canvas reads them, a card by its top-left corner and a sub-theme by
   its frame's, so a sub-theme takes its place among the cards where its frame's top sits. */
function thThemeOrder(v, gid, layout) {
  const g = thGroup(v, gid);
  if (!g) return [];
  return thReadOrder(g.members.filter((m) => thExists(v, m)).map((m) => {
    const f = thIsGroup(v, m) && layout[m] ? layout[m].frame : null;
    const at = f || (thIsGroup(v, m) ? thGroup(v, m) : v.cards[m]);
    return { id: m, x: at.x, y: at.y };
  }));
}

/* Auto-arrange: a theme's cards tidied under its label in a compact block, in the order they read
   now, top to bottom with ties broken left to right, the margin between them. Each sub-theme is
   arranged inside its own frame first and then set in the block as one piece where it read. The
   block keeps its top-left corner, so the label stays where it stands. Rows run as wide as about
   the square root of the pieces, the way a grid of cards is laid. A theme's own sticky notes come
   at the end of its block, in the order they read. False when there is nothing to arrange.
   `way` is one of Auto-arrange's ways (21 October): `grid`, that, `column`, one above another in the
   order they read down the PET, each sub-theme a block in its place arranged the same way, or `row`,
   all side by side. themes.py's arrange is the same. */
function thArrange(v, gid, size, way = 'grid') {
  if (thLocked(v)) return false;
  const layout = thLayout(v, size, null);
  const body = layout[gid] && layout[gid].body;
  if (!thGroup(v, gid) || !body) return false;
  const spots = [];        // where each card goes, and an empty sub-theme's label, from the body's corner
  const block = (id, seen) => {
    const notes = thReadOrder(thStickies(v).filter((n) => n.in === id).map((n) => ({ id: n.id, x: n.x, y: n.y })));
    const units = thThemeOrder(v, id, layout).concat(notes).filter((m) => !seen.has(m)).map((m) => {
      if (!thIsGroup(v, m)) return { id: m, w: size(m).w, h: size(m).h, card: true, note: thIsSticky(v, m) };
      const inner = block(m, new Set([...seen, m]));
      const label = size(m);
      return { id: m, w: Math.max(inner.w, label.w) + 2 * TH_FRAME_X, h: label.h + TH_GAP + inner.h + 2 * TH_FRAME_Y,
        inner, dx: TH_FRAME_X, dy: TH_FRAME_Y + label.h + TH_GAP };
    });
    if (!units.length) return { w: 0, h: 0, places: [] };
    const cols = way === 'column' ? 1 : way === 'row' ? units.length : Math.ceil(Math.sqrt(units.length));
    const card = (units.find((u) => u.card && !u.note) || { w: 200 }).w;
    const width = way === 'row' ? Infinity : Math.max(...units.map((u) => u.w), cols * card + (cols - 1) * TH_MARGIN);
    const places = [];
    let x = 0;
    let y = 0;
    let tall = 0;
    let w = 0;
    for (const u of units) {
      if (x > 0 && x + u.w > width) { y += tall + TH_MARGIN; x = 0; tall = 0; }
      if (u.card) places.push({ id: u.id, x, y });
      else if (u.inner.places.length) for (const p of u.inner.places) places.push({ id: p.id, x: x + u.dx + p.x, y: y + u.dy + p.y, label: p.label });
      else places.push({ id: u.id, x: x + u.dx, y: y + u.dy - TH_GAP - size(u.id).h, label: true });
      w = Math.max(w, x + u.w);
      tall = Math.max(tall, u.h);
      x += u.w + TH_MARGIN;
    }
    return { w, h: y + tall, places };
  };
  for (const p of block(gid, new Set([gid])).places) {
    const at = p.label ? thGroup(v, p.id) : (v.cards[p.id] || thSticky(v, p.id));
    if (at) { at.x = Math.round(body.x + p.x); at.y = Math.round(body.y + p.y); }
  }
  return true;
}

/* The labels and frames of a layout, to tell afterwards which themes an act made or grew: each
   label's box, with what its theme takes up among its neighbours as `solid`. */
const thLabelBoxes = (layout) => Object.fromEntries(Object.entries(layout || {}).map(([id, l]) =>
  [id, Object.assign({}, l.label, { solid: l.body ? l.frame : l.label })]));

/* A theme the act made, or whose frame now reaches past where it stood before the act on any side,
   `was` being the labels and frames before it. */
function thGrew(was, id, box) {
  const w = (was || {})[id];
  const at = w && (w.solid || w);
  return !at || box.x < at.x - 0.5 || box.y < at.y - 0.5
    || box.x + box.w > at.x + at.w + 0.5 || box.y + box.h > at.y + at.h + 0.5;
}

/* How firmly each thing stands while the canvas settles: what the act moved and that yields, then a
   sub-theme the act moved inside its theme, then a theme that grew, then what a push moved, the
   earlier the firmer. What stands firmer stays, and what stands less firmly gives way to it. */
const TH_FIRM = { yields: 4000, leads: 3000, grew: 2000, pushed: 1000 };

/* Nothing overlaps, and nothing comes to rest inside another's margin. Neighbours, as thNeighbours
   names them, keep the margin clear between them: on the canvas every card in no theme and every
   theme's frame, and inside a theme its own cards and its sub-themes' frames. A label and what it
   holds never count, since a frame holds them both.
   After an act, what it moved, `acted`, is a block. A card in it, and a theme at the top of the
   canvas, yield: when any of it meets a neighbour, or comes inside its margin, the block shifts as
   one to the nearest spot the margin clear of them all, keeping its own arrangement, so a card or a
   theme moved into a margin settles clear exactly as one dropped on top does. A sub-theme moved
   inside its theme stays where it is put, and so does a theme the act made, renamed or arranged,
   `labels`, or whose frame grew, `was` being the labels and frames before the act. A neighbour
   that comes inside its margin shifts clear of it by the least distance, a card alone and a theme
   as a block with all it holds, and a neighbour so pushed into a third pushes that one in the next
   pass, for TH_PASSES passes, and then it stops. The inside of a theme goes first, so its frame has
   followed whatever moved there before it is weighed against its own neighbours. A card in no
   theme left at rest inside a frame, which only a push that ran out of passes can leave, joins
   that theme, as a drop there does. With `stay`, a drag's drop, what the act moved lands where it
   was let go and none of it yields: all of it leads, its neighbours having made way already (see
   thMakeWay). True when anything moved. */
function thSettle(v, size, acted, was, labels, rounds = TH_PASSES, stay = false) {
  if (thLocked(v)) return false;
  const block = thBlock(v, acted || []);
  const extra = new Set(labels || []);
  const parents = thParents(v);
  const kids = thNeighbours(v, parents);
  const home = (id) => (parents[id] === undefined ? '' : parents[id]);
  // the top of the block: a card yields wherever it is, and so does a theme at the top of the
  // canvas, while a sub-theme moved inside its theme leads
  const top = [...block].filter((id) => !block.has(parents[id]));
  const yields = top.filter((id) => !thIsGroup(v, id) || parents[id] === undefined);
  if (stay) yields.splice(0);
  const leads = new Set(top.filter((id) => !yields.includes(id)));
  const depth = (h) => (h === '' ? 0 : thAncestors(v, h, parents).length + 1);
  const places = [...kids.keys()].sort((a, b) => depth(b) - depth(a));
  const pushed = new Map();
  let moved = false;
  for (let pass = 0; pass < rounds; pass += 1) {
    let layout = thLayout(v, size, null);
    const solid = (id) => thSolid(v, size, layout, id);
    const mine = yields.map((id) => ({ id, home: home(id), box: solid(id) }));
    const rest = [];
    for (const h of new Set(mine.map((b) => b.home))) {
      for (const id of kids.get(h)) if (!block.has(id)) rest.push({ id, home: h, box: solid(id) });
    }
    const apart = (a, b) => a.home !== b.home;
    if (mine.some((b) => rest.some((o) => !apart(b, o) && thMeets(b.box, o.box, TH_MARGIN)))) {
      const { dx, dy } = thFreeOffset(mine, rest, TH_MARGIN, apart);
      if (dx || dy) { thShift(v, block, dx, dy); moved = true; continue; }
    }
    let shifted = false;
    let stale = false;
    for (const h of places) {
      // a frame follows what a push inside it moved
      if (stale) { layout = thLayout(v, size, null); stale = false; }
      const items = kids.get(h).map((id, i) => {
        const box = solid(id);
        let firm = -1;
        if (yields.includes(id)) firm = TH_FIRM.yields;
        else if (leads.has(id)) firm = TH_FIRM.leads;
        else if (pushed.has(id)) firm = TH_FIRM.pushed - pushed.get(id);
        else if (!block.has(id) && thIsGroup(v, id) && (extra.has(id) || thGrew(was, id, box))) firm = TH_FIRM.grew;
        return { id, i, box, firm };
      });
      // what stands as the pass finds it pushes, and what that pushes waits for the next pass
      const standing = items.filter((l) => l.firm >= 0);
      const over = (o, n) => o !== n && o.firm >= 0 && !(block.has(o.id) && block.has(n.id))
        && (o.firm > n.firm || (o.firm === n.firm && o.i < n.i));
      for (const n of items.slice().sort((a, b) => a.firm - b.firm || a.i - b.i)) {
        if (!standing.some((l) => over(l, n) && thMeets(l.box, n.box, TH_MARGIN))) continue;
        const { dx, dy } = thFreeOffset([n], items.filter((o) => over(o, n)), TH_MARGIN);
        if (!dx && !dy) continue;
        thShift(v, thBlock(v, [n.id]), dx, dy);
        n.box = { x: n.box.x + dx, y: n.box.y + dy, w: n.box.w, h: n.box.h };
        n.firm = TH_FIRM.pushed - pass;
        pushed.set(n.id, pass);
        moved = true;
        shifted = true;
        stale = true;
      }
    }
    if (!shifted) break;
  }
  if (moved) {
    const layout = thLayout(v, size, null);
    const now = thParents(v);
    for (const key of new Set([...yields, ...pushed.keys()])) {
      const note = thIsSticky(v, key);
      if (thIsGroup(v, key) || (!note && !thOnCanvas(v, key)) || now[key] !== undefined) continue;
      const b = thSolid(v, size, layout, key);
      const at = thFrameAt(v, layout, { x: b.x + b.w / 2, y: b.y + b.h / 2 }, null);
      if (at && layout[at].body) {
        if (note) thStickiesJoin(v, [key], at); else thJoin(v, [key], at);
      }
    }
  }
  return moved;
}

/* Room made once the page has measured a board (17 October, later). The page's own acts leave nothing
   nearer than the margin, but a board laid out where its words or its type stood another size can: a
   line re-read on open, or a PET retitled in its case and taken in on GETs, that now takes a line more,
   a board from another computer's type, an agent's or a hand's. Each pair of neighbours nearer than the
   margin, as thClashes finds them, one of them a theme by its frame, its title among it, makes room by
   the one that gives way, a card or a note before a theme and the second of two themes, settling clear
   as a drop there does, so a theme's title never stands over a card. Two cards or notes make room as a
   drag lets one go there (agentoverlap, 31 October, Adam: a card an agent reworded stood over the card under
   it, in a sub-PET with the quotes shown in full, until he dragged it): the one that reads first stays where
   it is and leads, and the other is pushed clear of it by the least distance, pushing on what it then meets,
   a frame that grew so pushing its own neighbours, up to the canvas. Since 20 October the old scattered pile
   waits in Not placed, off the canvas, so no pair is left as it lies. One pair at a time, each tried once,
   and nothing is written until the next act. True when anything moved.
   The room keeps the order everything reads in (agentorder, 10 November 2026: on a board an agent changed,
   the room the page made, its type taller than the server's sizes, sent a statement in a PET past its
   neighbour, and his next act saved that order into the PETs table and the PDF). When the room made reads
   any PET, sub-PET or the PETs themselves otherwise, it is made again with every pair led by the one that
   reads first, the other pushed clear of it, and when that too reads otherwise the board stays as it was. */
function thMakeRoom(v, size) {
  if (!v || thLocked(v)) return false;
  const held = thBoardHeld(v);
  const order = thOrders(v, size);
  if (!thRoomPairs(v, size, false)) return false;
  if (thOrders(v, size) === order) return true;
  thBoardBack(v, held);
  if (thRoomPairs(v, size, true) && thOrders(v, size) === order) return true;
  thBoardBack(v, held);
  return false;
}

/* Each pair of neighbours nearer than the margin made room for, as thMakeRoom says, with `inOrder` every
   pair, a PET or a sub-PET among them, led by the one that reads first. True when anything moved. */
function thRoomPairs(v, size, inOrder) {
  let moved = false;
  const tried = new Set();
  const theme = (id) => (thIsGroup(v, id) ? 1 : 0);
  for (let pass = 0; pass < 64; pass += 1) {
    const pair = thClashes(v, size).find(([a, b]) => !tried.has(`${a} ${b}`));
    if (!pair) break;
    const [a, b] = pair;
    tried.add(`${a} ${b}`);
    const layout = thLayout(v, size, null);
    const was = thLabelBoxes(layout);
    if (inOrder) {
      const at = (id) => thSolid(v, size, layout, id) || { x: 0, y: 0 };
      const first = thReadOrder([{ id: a, x: at(a).x, y: at(a).y }, { id: b, x: at(b).x, y: at(b).y }])[0];
      if (thSettle(v, size, [first], was, [], TH_PASSES, true)) moved = true;
    } else if (theme(a) || theme(b)) {
      const gives = theme(a) < theme(b) ? a : b;
      if (thSettle(v, size, [gives], was, [])) moved = true;
    } else if (thSettle(v, size, [thReadsFirst(v, a, b)], was, [], TH_PASSES, true)) moved = true;
  }
  return moved;
}

/* The order every place on a board reads in, the PETs and inside each label, as one string to compare. */
function thOrders(v, size) {
  const layout = thLayout(v, size, null);
  const parents = thParents(v);
  const out = [gtCanvasOrder(v.groups.filter((g) => parents[g.id] === undefined)).join(' ')];
  for (const g of v.groups) out.push(`${g.id}: ${thThemeOrder(v, g.id, layout).join(' ')}`);
  return out.join('\n');
}

/* A board's cards, labels and sticky notes as they stand, to put back with thBoardBack. */
const thBoardHeld = (v) => JSON.stringify({ cards: v.cards, groups: v.groups, stickies: thStickies(v) });

function thBoardBack(v, held) {
  const h = JSON.parse(held);
  const back = (o, was) => { for (const f of Object.keys(o)) delete o[f]; Object.assign(o, was); };
  for (const [k, c] of Object.entries(v.cards)) if (h.cards[k]) back(c, h.cards[k]);
  v.groups.forEach((g, i) => { if (h.groups[i]) back(g, h.groups[i]); });
  thStickies(v).forEach((n, i) => { if (h.stickies[i]) back(n, h.stickies[i]); });
}

/* Of two cards or notes, the one the canvas reads first: the higher, or along a row the one on the left. */
function thReadsFirst(v, a, b) {
  const at = (id) => v.cards[id] || thSticky(v, id) || { x: 0, y: 0 };
  return thReadOrder([{ id: a, x: at(a).x, y: at(a).y }, { id: b, x: at(b).x, y: at(b).y }])[0];
}

/* Where every card and label stands now, to ease from once an act has moved them. */
function thSpots(v) {
  const out = { cards: {}, groups: {}, stickies: {} };
  for (const [key, c] of Object.entries(v.cards)) out.cards[key] = { x: c.x, y: c.y };
  for (const g of v.groups) out.groups[g.id] = { x: g.x, y: g.y };
  for (const n of thStickies(v)) out.stickies[n.id] = { x: n.x, y: n.y };
  return out;
}

/* ── making way: the neighbours move aside while anything is dragged ── */

/* The place whose neighbours make way for a drag: where what is dragged comes to rest if let go
   now, worked out from `hit`, what thTargetAt finds, so the drag and the drop agree. Over a theme's
   title strip that is the theme it joins, and in a body that theme (19 October for statements, 31 October,
   design A, for a PET's sub-PET or a sub-PET's group, by the level it keeps). Anywhere else a drop only
   moves (18 October), so it is the
   PET or sub-PET what is dragged stands in now, whose own members make way and whose order it takes
   its place in, or the canvas, '', for what stands in none or in more than one. A card, a note, a PET
   or a sub-theme alike, `nest` no longer counting. Alt means out: with it held nothing under the pointer
   takes the drop (31 October) and what is dragged lands on the canvas. Null over the bin and on a card's
   middle, where nothing lands. */
function thWayHome(v, moving, nest, hit, alt) {
  if (hit && (hit.discard || hit.stack)) return null;
  const parents = thParents(v);
  const top = [...moving].filter((id) => !moving.has(parents[id]));
  if (hit && hit.group) {
    if (alt && top.every((id) => parents[id] === hit.group)) return '';
    return hit.group;
  }
  if (alt || !top.length) return '';
  const shared = parents[top[0]];
  return shared !== undefined && top.every((id) => parents[id] === shared) ? shared : '';
}

/* What is dragged always has a space under it. The neighbours in `home`, as thNeighbours names them,
   that come inside the margin of what is dragged, a card or a note by its box, a selection by each
   member's and a PET or a sub-theme by its frame, slide clear by the least distance, a PET or a
   sub-theme as one block with all it holds, and a neighbour pushed into a third pushes that one in
   the next pass, for TH_PASSES passes, and then it stops, the push thSettle has. What is dragged
   never moves, and nor does a frame that holds it and reaches out to it, unless Alt takes it out.
   A member let go on the open canvas, or in its own theme, stays a member without Alt, and every
   frame that holds it reaches out to it, so in the place round each such frame, up to the canvas,
   the neighbours make way for that frame as it stretches, the innermost first, and the drop has
   nothing more to send clear. Nothing outside those places moves. Returns everything that moved.
   A drag passes `pins`, where each label stood as it began (31 October, design A, see thPreview): then
   only the statements and notes in `home` make room, a PET, a sub-PET or a group in it holding still and
   its title too, each of those a place they are sent clear of without ever pushing, no frame that reaches
   out to what is dragged sends anything clear, and on the open canvas, `home` '', nothing moves. */
function thMakeWay(v, size, moving, home, alt = false, rounds = TH_PASSES, pins = null) {
  const moved = new Set();
  if (thLocked(v) || home === null || home === undefined || (pins && home === '')) return moved;
  const parents = thParents(v);
  const top = [...moving].filter((id) => !moving.has(parents[id]));
  const holders = new Set(alt ? [] : top.flatMap((id) => thAncestors(v, id, parents)));
  // each place that makes way, with what stands in it for the drag
  const places = new Map([[home, new Set(top)]]);
  for (const id of alt || pins ? [] : top) {
    if (home !== '' && home !== parents[id]) continue;
    for (const g of thAncestors(v, id, parents)) {
      const at = parents[g] === undefined ? '' : parents[g];
      if (!places.has(at)) places.set(at, new Set());
      places.get(at).add(g);
    }
  }
  const depth = (h) => (h === '' ? 0 : thAncestors(v, h, parents).length + 1);
  const neighbours = thNeighbours(v, parents);
  const pushed = new Map();
  for (const place of [...places.keys()].sort((a, b) => depth(b) - depth(a))) {
    const near = (neighbours.get(place) || []).filter((id) => !moving.has(id) && !holders.has(id));
    // with `pins` a label in the place holds still, and only what it holds besides makes room
    const kids = pins ? near.filter((id) => !thIsGroup(v, id)) : near;
    if (!kids.length) continue;
    const stands = [...places.get(place)];
    for (let pass = 0; pass < rounds; pass += 1) {
      const layout = thDragLayout(v, size, moving, alt, pins);
      const held = stands.map((id) => ({ id, i: -1, box: thSolid(v, size, layout, id), firm: Infinity })).filter((b) => b.box);
      // what holds still, each sub-PET's frame and the place's own title short of the gap under it, is kept
      // clear of and never pushes
      const title = pins && layout[place] ? layout[place].label : null;
      const still = !pins ? [] : near.filter((id) => thIsGroup(v, id)).map((id) => ({ id, i: -1, box: thSolid(v, size, layout, id), firm: Infinity, still: true }))
        .concat(title ? [{ id: place, i: -1, box: { x: title.x, y: title.y, w: title.w, h: Math.max(0, title.h - (TH_MARGIN - TH_GAP)) }, firm: Infinity, still: true }] : [])
        .filter((b) => b.box);
      const items = kids.map((id, i) => ({ id, i, box: thSolid(v, size, layout, id),
        firm: pushed.has(id) ? TH_FIRM.pushed - pushed.get(id) : -1 })).filter((n) => n.box);
      const all = held.concat(still, items);
      // what stands as the pass finds it pushes, and what that pushes waits for the next pass
      const standing = all.filter((l) => l.firm >= 0 && !l.still);
      const over = (o, n) => o !== n && o.firm >= 0 && (o.firm > n.firm || (o.firm === n.firm && o.i < n.i));
      let shifted = false;
      for (const n of items.slice().sort((a, b) => a.firm - b.firm || a.i - b.i)) {
        if (!standing.some((l) => over(l, n) && thMeets(l.box, n.box, TH_MARGIN))) continue;
        const { dx, dy } = thFreeOffset([n], all.filter((o) => over(o, n)), TH_MARGIN);
        if (!dx && !dy) continue;
        const block = [...thBlock(v, [n.id])].filter((id) => !moving.has(id));
        thShift(v, block, dx, dy);
        for (const id of block) moved.add(id);
        n.box = { x: n.box.x + dx, y: n.box.y + dy, w: n.box.w, h: n.box.h };
        n.firm = TH_FIRM.pushed - pass;
        pushed.set(n.id, pass);
        shifted = true;
      }
      if (!shifted) break;
    }
  }
  return moved;
}

/* The board as it stood when the drag began, `d.from`, a copy, each label a copy too, with what is
   dragged at `at` when given, a map of id to place. */
function thAtStart(v, d, at = null) {
  const from = d.from || { cards: {}, groups: {}, stickies: {} };
  return thSeen(v, Object.assign({}, from.cards, from.groups, from.stickies || {}, at || {}));
}

/* A PET, a sub-PET or a group dragged near its neighbours in its own place comes to rest a margin from
   them, and none of them moves (26 October, Adam: the last sub-PET of a PET would not go any closer to
   the ones above it, since each that came inside its margin was sent up out of its way, and the gap
   stayed as it was). While what is dragged meets them only by a little, the shortest shift that clears
   it of them all is TH_NEAR or less, it stops at that shift, the margin between, and is drawn there, and
   the drop lands it there. Pulled further in, the statements among them make room and a PET or sub-PET
   holds still until the drop settles it (31 October, design A). Weighed against where
   they stood as the drag began, so a neighbour that made way never counts. The drag's `dx` and `dy`
   become the pointer's with the shift, from `d.free`, the pointer's own. Statements and notes alone, Alt
   held, a drop into another theme and a drop on a strip have no shift. */
const TH_NEAR = 3 * TH_MARGIN;
function thNearRest(d, home) {
  const v = TH.v;
  const free = d.free || { dx: d.dx, dy: d.dy };
  d.dx = free.dx;
  d.dy = free.dy;
  if (!d.nest || d.alt || d.out || home === null || home === undefined) return;
  const parents = thParents(v);
  const top = [...d.moving].filter((id) => !d.moving.has(parents[id]));
  if (!top.length || !top.every((id) => (parents[id] === undefined ? '' : parents[id]) === home)) return;
  const at = {};
  for (const id of d.moving) if (d.starts[id]) at[id] = { x: Math.round(d.starts[id].x + free.dx), y: Math.round(d.starts[id].y + free.dy) };
  const seen = thAtStart(v, d, at);
  const layout = thLayout(seen, thSize, null);
  const kids = (thNeighbours(seen).get(home) || []).filter((id) => !d.moving.has(id));
  const held = top.map((id) => ({ box: thSolid(seen, thSize, layout, id) })).filter((b) => b.box);
  const others = kids.map((id) => ({ box: thSolid(seen, thSize, layout, id) })).filter((b) => b.box);
  if (!held.length || !others.length || !held.some((b) => others.some((o) => thMeets(b.box, o.box, TH_MARGIN)))) return;
  const { dx, dy } = thFreeOffset(held, others, TH_MARGIN);
  if (Math.hypot(dx, dy) > TH_NEAR) return;
  d.dx = free.dx + dx;
  d.dy = free.dy + dy;
}

/* Whether a drop in `home` changes anything the insertion line would show: what is dragged coming into it
   from elsewhere, or taking another place among its members than it had as the drag began (26 October,
   Adam: the line under the sub-PET above showed from the first move, though the drop changed nothing). */
function thInsertMoves(v, d, home) {
  const parents = thParents(v);
  const top = [...d.moving].filter((id) => !d.moving.has(parents[id]));
  if (top.some((id) => parents[id] !== home)) return true;
  if (!d.orders) d.orders = {};
  const seq = (order) => {
    const first = order.findIndex((id) => d.moving.has(id));
    return order.filter((id, i) => !d.moving.has(id) || i === first).map((id) => (d.moving.has(id) ? '*' : id)).join('\n');
  };
  if (d.orders[home] === undefined) {
    const was = thAtStart(v, d);
    d.orders[home] = seq(thThemeOrder(was, home, thLayout(was, thSize, null)));
  }
  return seq(thThemeOrder(v, home, d.layout)) !== d.orders[home];
}

/* The canvas as it makes way for a drag, worked out afresh from where everything stood when the
   drag began, `drag.from` as thSpots took it, never from the last preview, so a neighbour the drag
   has moved away from is back on its own spot. What is dragged stands at its start moved by the
   drag, and the neighbours in `home` are sent clear of it (see thMakeWay). With `home` null, over
   the bin or on Esc, everything that stays is back where it was. Returns what made way.
   Design A (Adam, 31 October, after the drag audit): no PET or sub-PET moves out of the way. Only the
   statements and notes inside the PET or sub-PET whose body is under the pointer, `drag.hitNow`, make room,
   and only when a drop there lands in it. Over a title nothing moves, the strip saying Merge into. Every
   label not dragged stays where it stood, so a title never runs from the pointer, and the frame of a PET a
   member is dragged out of stretches after it and pushes nothing. The drop settles the rest (see thDone). */
function thPreview(v, size, drag, home) {
  const { moving, starts, from, dx, dy } = drag;
  // what is dragged going into another theme's body shows its leaving as Alt does (see thWay)
  const alt = !!(drag.alt || drag.out);
  const back = (o, at) => { if (o && at) { o.x = at.x; o.y = at.y; } };
  for (const [key, c] of Object.entries(v.cards)) if (!moving.has(key)) back(c, from.cards[key]);
  for (const g of v.groups) if (!moving.has(g.id)) back(g, from.groups[g.id]);
  for (const n of thStickies(v)) if (!moving.has(n.id)) back(n, (from.stickies || {})[n.id]);
  for (const id of moving) {
    const at = thIsGroup(v, id) ? thGroup(v, id) : (v.cards[id] || thSticky(v, id));
    if (at && starts[id]) { at.x = Math.round(starts[id].x + dx); at.y = Math.round(starts[id].y + dy); }
  }
  const under = drag.hitNow && drag.hitNow.body && drag.hitNow.group;
  const moved = thMakeWay(v, size, moving, under && under === home ? home : null, alt, TH_PASSES, from.groups);
  // the board's layout as the drop would leave it, which the insertion line reads
  drag.layout = thDragLayout(v, size, moving, alt, from.groups);
  return moved;
}

/* The board as it shows while what makes way slides there: each id in `shown` at the place given,
   and every label a copy, since a layout writes where each label sits. */
function thSeen(v, shown) {
  const at = (o, id) => (shown[id] ? Object.assign({}, o, shown[id]) : o);
  return Object.assign({}, v, {
    cards: Object.fromEntries(Object.entries(v.cards).map(([key, c]) => [key, at(c, key)])),
    groups: v.groups.map((g) => Object.assign({}, g, shown[g.id] || {})),
    stickies: Array.isArray(v.stickies) ? v.stickies.map((n) => at(n, n.id)) : v.stickies,
  });
}

/* A neighbour making way slides from where it showed to where it goes over about 160 ms, eased
   out, and with reduced motion it is there at once. Where a slide has got to at `now`. */
const TH_WAY_MS = 160;
function thWayAt(s, now, calm = false) {
  const k = calm ? 1 : Math.max(0, Math.min(1, (now - s.t0) / TH_WAY_MS));
  const e = 1 - (1 - k) ** 3;
  return { x: s.from.x + (s.to.x - s.from.x) * e, y: s.from.y + (s.to.y - s.from.y) * e, done: k >= 1 };
}

/* ── undo: the board before and after each act ── */

function thSnap(v, removed) {
  // where everything stands with every stack shut, since an open one is a view and never a change
  const base = thUnshifted(v);
  return {
    cards: base.cards,
    groups: base.groups,
    discarded: v.discarded.slice(),
    picks: JSON.parse(JSON.stringify(v.picks || {})),
    stacks: JSON.parse(JSON.stringify(thStacks(v))),
    // the close pairs marked Not the same
    not_same: JSON.parse(JSON.stringify(thNotSame(v))),
    // the sticky notes, or null on a board from a server before them
    stickies: Array.isArray(v.stickies) ? base.stickies : null,
    // the GET table's rows on the GETs screen, a quote ticked and a note for a row each a step
    rows: v.rows ? JSON.parse(JSON.stringify(v.rows)) : null,
    removed: [...(removed || [])],
  };
}

/* Puts a snapshot back over the board. A card read since keeps the line as it reads now and takes
   its place and its stored text from the snapshot, and a card the snapshot never knew stays. */
function thPut(v, snap) {
  if (thLocked(v)) return new Set();
  const cards = {};
  for (const [key, was] of Object.entries(snap.cards)) {
    const now = v.cards[key];
    cards[key] = now
      ? Object.assign({}, now, { x: was.x, y: was.y, stored: was.stored, changed: was.changed }, 'wait' in was ? { wait: was.wait } : {})
      : Object.assign({}, was);
  }
  for (const [key, card] of Object.entries(v.cards)) {
    if (!(key in cards) && !snap.removed.includes(key)) cards[key] = card;
  }
  v.cards = cards;
  v.groups = JSON.parse(JSON.stringify(snap.groups));
  v.discarded = snap.discarded.filter((key) => key in cards);
  v.picks = JSON.parse(JSON.stringify(snap.picks || {}));
  if (snap.stacks) v.stacks = JSON.parse(JSON.stringify(snap.stacks));
  if (Array.isArray(snap.not_same)) v.not_same = JSON.parse(JSON.stringify(snap.not_same));
  if (Array.isArray(snap.stickies)) v.stickies = JSON.parse(JSON.stringify(snap.stickies));
  if (snap.rows) v.rows = JSON.parse(JSON.stringify(snap.rows));
  return new Set(snap.removed);
}

/* A label as a save sends it: the whole label as the page holds it, so a field the page never edits
   goes back as it came, its note when it has one, and its description always, "" for none, so the
   server can tell a description taken off from a page that knows none (22 October: a save had sent a
   hand-picked few of a label's fields and every description on the board went with it). */
function thLabelOut(g) {
  const out = Object.assign({}, g, { members: g.members.slice(), x: Math.round(g.x), y: Math.round(g.y) });
  delete out.note;
  if (thNoteOf(g)) out.note = thNoteOf(g);
  out.description = thDescOf(g);
  return out;
}

/* The board as the themes file holds it. A card whose line has changed since the board was
   made keeps the text it was made with, with the line as it reads now beside it. */
function thBody(v, meta) {
  const cards = {};
  // where everything stands with every stack shut, which is what the file keeps
  const base = thUnshifted(v);
  for (const [key, c0] of Object.entries(v.cards)) {
    const c = Object.assign({}, c0, base.cards[key] ? { x: base.cards[key].x, y: base.cards[key].y } : {});
    const card = { x: Math.round(c.x), y: Math.round(c.y), text: c.changed ? c.stored : c.text };
    if (c.changed) card.live = c.text;
    // a card he put on the canvas in no PET yet, which the file keeps as `loose` (20 October)
    if (thWaits(v) && !c.wait) card.loose = true;
    cards[key] = card;
  }
  const out = {
    id: meta.id, name: meta.name, note: meta.note || '', created: meta.created, updated: meta.updated,
    // the board's version as this page last read it, so a save over a change made since is refused
    v: meta.v || null,
    cards,
    groups: base.groups.map(thLabelOut),
    discarded: v.discarded.slice(),
    picks: JSON.parse(JSON.stringify(v.picks || {})),
  };
  // the stacks, even none, so a stack taken apart goes from the file too. A server from before them
  // keeps none, and the page sends none to it
  if (TH.stackable && TH.mode !== 'gets') out.stacks = JSON.parse(JSON.stringify(thStacks(v)));
  // and the close pairs marked Not the same, even none, so one shown again goes from the file too
  if (TH.pairable && TH.mode !== 'gets') out.not_same = JSON.parse(JSON.stringify(thNotSame(v)));
  // his sticky notes go as the file's `notes`, even none, so a note deleted goes from the file too.
  // A board from a server before them has none to send, and that server keeps none
  if (Array.isArray(v.stickies)) {
    out.notes = base.stickies.map((n) => Object.assign({ id: n.id, text: thStickyClean(n.text), colour: n.colour,
      x: Math.round(n.x), y: Math.round(n.y) }, n.in && thIsGroup(v, n.in) ? { in: n.in } : {}));
  }
  // why a statement was left out goes back as it came, for the pile
  if (v.ai && v.ai.discarded && Object.keys(v.ai.discarded).length) out.ai = JSON.parse(JSON.stringify(v.ai));
  // on the GETs screen, the GET table's rows go with the board, even none
  if (TH.mode === 'gets' && v.rows) out.rows = gtRowsKept(v);
  return out;
}

/* Why a card was left out, when an agent said, or a New AI board before 11 November 2026. The reasons
   keep the name they had when an AI board put such a card in the bin, `discarded`. */
const thWhy = (v, key) => (v.ai && v.ai.discarded && v.ai.discarded[key]) || '';

/* A card left out of every PET or GET with a reason stands in Not placed with it under its words,
   in the small type the bin's pile gives a reason, two lines at most, the whole of it in the card's
   tooltip and the Inspector. Put in a PET or a GET, it shows none (item 182). */
function thWhyHtml(v, key, owner) {
  if (owner !== undefined || v.discarded.includes(key) || !thWhy(v, key)) return '';
  return `<p class="th-pile-why th-card-why">${esc(thWhy(v, key))}</p>`;
}

/* After the name of a board an AI made, in the board menu and the case switcher, a small faint
   "with AI", its tooltip naming the model and the source, and once he has changed the board since,
   "edited by you since" in both. A board of his own, a duplicate among them, carries nothing. */
function thWithAi(made) {
  if (!made || !made.said) return '';
  const tip = made.edited ? t('themes.withai.tip_edited', { said: made.said }) : made.said;
  return `<span class="th-withai" title="${escAttr(tip)}">${esc(made.edited ? t('themes.withai.made_edited') : t('themes.withai.made'))}</span>`;
}

/* ── the history: when a revision was made, and the days the tab lists them under ── */

/* a day as the history says it, 1 October, and with its year, 1 October 2025, through Intl (i18n.js's tDate) */
const TH_DAY = { day: 'numeric', month: 'long' };
const TH_DAY_YEAR = { day: 'numeric', month: 'long', year: 'numeric' };
/* An automatic revision every fifteen minutes while the board is worked on, through the save. */
const TH_REVISION_EVERY = 15 * 60 * 1000;
const thRevisionDue = (now, last, worked) => !!worked && now - last >= TH_REVISION_EVERY;

const thSameDay = (a, b) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
  && a.getDate() === b.getDate();
// a time of day by the times format through i18n.js's tTime (fmtsweep, 28 October 2026): 14:05 or 2:05 pm
const thClockOf = (d) => tTime(d);

/* A revision's time the way the History tab, the banner and the server's names say it: 12:04
   today, 1 October 12:04 on another day this year, and the year after the month in another. */
function thWhen(at, now = new Date()) {
  const d = new Date(at);
  if (Number.isNaN(d.getTime())) return String(at || '');
  if (thSameDay(d, now)) return thClockOf(d);
  const year = d.getFullYear() !== now.getFullYear();
  return t('themes.history.when', { day: tDate(d, year ? TH_DAY_YEAR : TH_DAY), time: thClockOf(d) });
}

/* The day a revision is listed under: Today, Yesterday, or the date. */
function thDayOf(d, now = new Date()) {
  const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  if (thSameDay(d, now)) return t('themes.history.today');
  if (thSameDay(d, yesterday)) return t('themes.history.yesterday');
  return tDate(d, TH_DAY_YEAR);
}

/* The revisions as the History tab lists them, newest first as the server sends them, grouped by
   the day they were made, each with its time. */
function thHistoryDays(history, now = new Date()) {
  const out = [];
  for (const r of history || []) {
    const t = new Date(r.at);
    const ok = !Number.isNaN(t.getTime());
    const day = ok ? thDayOf(t, now) : '';
    if (!out.length || out[out.length - 1].day !== day) out.push({ day, items: [] });
    out[out.length - 1].items.push(Object.assign({}, r, { time: ok ? thClockOf(t) : '' }));
  }
  return out;
}

/* Where Copy to board sends a theme: every other board of the case, and while a revision is on
   view, the board it is a revision of, first. */
function thCopyTargets(boards, current, viewing) {
  const out = [];
  const here = (boards || []).find((b) => b.id === current);
  if (viewing && here) out.push({ id: here.id, name: here.name, here: true });
  for (const b of boards || []) if (b.id !== current) out.push({ id: b.id, name: b.name, here: false });
  return out;
}

/* ────────────────────────────────────────────────────────── the screen ── */

const TH_ZOOM_MIN = 0.15;
const TH_ZOOM_MAX = 2.5;
const TH_UNDO_DEPTH = 80;
const TH_CARD = { w: 200, h: 80 };
const TH_LABEL = { w: 140, h: 30 };

const TH = {
  path: null,         // the workbook, as the case list and the turn screen name it
  label: '',          // the case as the opener named it, for a server that cannot
  back: null,         // the way back to where the screen was opened from
  to: 'cases',        // where it goes, statements, pets, gets or the case list, which its tooltip names
  live: false,        // a case is loaded and the canvas answers
  ask: 0,             // the open in flight, so a slow answer never lands on a newer one
  v: null,            // the board being worked on, or the revision of it on view
  meta: null,         // its id, name, note and times
  boards: [],         // every board in the file, by id, name, note and times
  sheets: [],
  quotes: {},         // the quotes of every row that has any, by sheet and row
  hasQuotes: false,   // the server sent them, which one from before the panel does not
  busy: false,        // a board op is on its way, and the canvas waits for it
  removed: new Set(), // missing cards taken out of the board
  sel: { cards: new Set(), groups: new Set(), stickies: new Set() },
  els: { cards: {}, labels: {}, frames: {}, stickies: {} },
  z: [],              // the cards in the order they are drawn, the one moved last on top
  sizes: {},
  layout: {},
  view: { x: 0, y: 0, z: 1 },
  undo: [],
  redo: [],
  undoPath: null,     // the case the stack belongs to
  stacksPath: null,   // the case the stacks below belong to
  stacks: {},         // the undo and redo of each board of that case, by id
  views: {},          // and the view each board of it was left in, by id, which a switch back finds (thLand)
  undoBoard: null,    // the board the stack in use belongs to
  press: null,        // a press on a card or a label, before it is a click or a drag
  drag: null,
  lasso: null,
  pan: null,
  space: false,
  hand: false,        // the hand: a plain drag pans, until H, V or Esc gives the pointer back
  menu: null,         // the right-click menu, and the card or label it is for
  hoverAt: null,      // during a drag, the theme whose title strip is lit for a drop there
  stackAt: null,      // during a drag, the card a drop would stack under
  lifting: null,      // the card thStackLift takes out of an open stack, while it draws the board
  stackable: false,   // the server keeps stacks, which one from before them does not
  opened: new Set(),  // the tops whose stacks are shown open, in place
  shifts: [],         // what a stack shown open moved down to make room, which the file never keeps
  baseH: {},          // each such top's own height, without its stack
  qfull: {},          // each card showing its quote, its height with it (Quotes on cards, 19 October)
  qextra: {},         // and how much of that the quote takes, which the board makes room for as a view
  unfolded: new Set(), // on GETs, the PET and sub-theme cards unfolded in place, kept with the board's view (21 October)
  roomShown: null,    // where everything showed once the room was last made, to tell what an act moved since
  kqpop: null,        // the card whose quote shows whole beside it
  qmenu: false,       // the quotes' menu of Off, Short and Full is open (30 October)
  pairs: [],          // the board's close pairs as the canvas last drew them (20 October)
  pairAt: null,       // the pair the status bar's stepping is on, by its two keys
  linkHot: null,      // the card under the pointer, whose close pairs' lines are lit
  pmenu: null,        // the menu a click on a close pair's line opens, and its pair
  cpmenu: false,      // the close pairs' gap menu is open
  pairable: false,    // the server keeps pairs marked Not the same, which one from before them does not
  usizes: {},         // the sizes of a stack's cards shown open, and of its Stack again
  config: null,       // the settings, which Settings opens with over this screen
  project: null,      // the project, its research question in the band over the canvas
  editing: null,      // the label whose title is open
  cardEdit: null,     // the card whose statement is open for editing in place
  writing: false,     // a statement edited in place is on its way to the workbook
  canEdit: false,     // the server has the route that writes it, which one from before it does not
  canCopies: false,   // and carries it to the GETs' copies, which a GETs board's edit needs (30 October)
  stickable: false,   // the server keeps sticky notes, which one from before them would drop
  stickyEdit: null,   // the sticky note whose words are open on the canvas
  stickyBox: null,    // the sticky note whose words are open in the Inspector, { id, value }
  lastEmpty: null,    // the last click on empty canvas, where and when, for a double-click there
  lastClick: null,    // the card or label clicked last and when, for a double-click
  saveTimer: null,
  chain: null,        // the saves in flight, one after another
  again: false,
  dirty: false,
  pileOpen: false,
  panel: null,        // the card or the label the Inspector shows, { kind, id }, or null for nothing
  sideOpen: false,    // the sidebar is open, which its button, `i` and Inspect do and a click never does
  panelOpen: false,   // the sidebar is open on the Inspector
  lastPick: null,     // the card or the label clicked last, which the Inspector shows with several selected
  boardOpen: false,   // the sidebar is open on a tab about the board
  tab: 'inspector',   // the sidebar's tab, open or closed: inspector, guidance or history
  guidance: null,     // the Guidance tab's headings and lines, and null from a server before them
  history: null,      // the board's revisions, newest first, and null from a server before them
  viewing: null,      // a revision on view: { rev, live, z, removed }, the board itself kept aside
  revBoard: null,     // the board the automatic revisions below are timed for
  revAt: 0,           // when the timer last asked for an automatic revision
  revDue: false,      // the next save asks for one
  worked: false,      // an act since then
  vmenu: false,       // the board menu is open
  chosen: null,       // the Current board's id, the one he is going with, never the board on the canvas
  choosable: false,   // the server keeps the Current board, which one from before it does not
  done: null,         // the PETs marked complete, { at, board, name }, `board` the one it was marked on
  doneable: false,    // the server keeps that mark, which one from before it does not
  vedit: null,        // 'name', 'note' or 'revision' of the current board, open in the menu
  doomed: null,       // the board the delete card stands in front of
  audioSheet: null,   // the sheet the panel's player is loaded for
  seekKey: null,      // the quote whose play button cued it, for the toggle
  cueAt: 0,
  ai: null,           // the switch in Settings and the model, as the server sent them
  platform: '',       // the server's, so Show in Finder is offered on a Mac alone
  exported: null,     // the files the last export wrote, as the screen names them
  names: null,        // the names asked for, { key, target, busy, names, error }
  namesAsk: 0,        // the names in flight, so a slow answer never lands on a newer one
  printable: false,   // the server has the print view, which one from before it does not
  notable: false,     // the server keeps a theme's note, which one from before the notes drops
  noting: null,       // the note open in the panel, { id, value }, until it is kept or let go
  noteRedraw: false,  // the panel is drawn afresh under the note, which is not a click away
  xmenu: false,       // the export menu is open
  casemenu: false,    // the case switcher's menu is open
  cases: [],          // the cases it lists, as the server sent them
  casesAsk: 0,        // the list in flight, so a slow answer never lands on a newer one
  mode: 'pets',       // 'gets' while the canvas is the GETs screen, the PETs canvas one layer up
  gets: null,         // the GETs screen's cases, study and minimum, as the server sent them
  casesOpen: false,   // the GETs screen's Cases panel is open, or on PETs the statements' sidebar
  ssel: new Set(),    // the sidebar's rows selected, in the section `ssec`, Not placed `wait` or Set aside `aside`
  ssec: null,
  sfold: null,        // the sidebar's sections folded open or shut, kept in the browser
  spull: null,        // rows dragged from the sidebar
  sideLast: false,    // a row of the sidebar was pressed last, so Cmd + A selects its section
  cfind: '',          // the Cases panel's search
  codeList: null,     // a thematic analysis project's code list as /api/codes gives it, for its Themes board
  ptab: 'codes',      // the panel's tab on that board, Codes or Participants
  cfold: new Set(),   // its rows folded open, a case by name, a PET or a sub-theme by `<case>/<id>`, kept by project
  cflip: new Set(),   // the rows a chevron turned the other way during a search, until the search changes
  foldRoot: null,     // the project whose folds TH.cfold holds
  rowClick: null,     // the last click on a statement's row, for a second one soon after, { key, at }
  pull: null,         // a row of the Cases panel on its way onto the canvas
  pnBox: null,        // the participant note whose words are open in the Inspector, { key, value }
  rowEdit: null,      // the GET table's row whose note is open, { gid, kase, value, focus }
  trail: null,        // the GET whose audit trail is open, { gid }
  trailAsk: 0,        // the trail in flight, so a slow answer never lands on a newer one
  trailAudio: null,   // the trail's own player
  printing: null,     // the print card's choices, { what, detail, gid }
  root: '',           // the GETs' project folder, and the print view's address, as the server sent them
  getsPrint: '',
  beside: null,       // the board open beside this one, read-only, with its own view
  besideAsk: 0,       // the board beside in flight, so a slow answer never lands on a newer one
  sids: {},           // each statement's short id by its key, S1 on, which the Inspector shows
  known: {},          // each board's `updated` as this page last saw it, to notice a change made outside
  wbAt: null,         // the case's workbook's time as the stamp last gave it, and its path, for two windows in step
  wbPath: null,
  stampLast: 0,       // when the stamp was last asked for on GETs, every thirty seconds there
  outside: null,      // a change made outside the app, { board, updated, changed, cases, line }, until Update or its cross
  taking: false,      // a case's changes coming into the GETs, which the stamp waits for (see gtTakeAll)
  farLeft: null,      // the cases whose change from outside he put away with the notice's cross
  stale: null,        // a save refused since the board changed under the page, { board, v }, until Reload or Overwrite
  staleKept: null,    // after Reload, the revision his canvas went into, { board, revision }, for Put my canvas back
  stampAsk: 0,       // the stamp in flight, so a slow answer never lands on a newer screen
  map: null,          // the minimap's fit, its scale and its place in its area, null while it is not drawn
  mapBoard: null,     // the board's own fit, which the view's box is weighed against (see thMapAround)
  mapItems: null,     // what the map draws, as thMapItems last listed it
  mapDrawn: null,     // the fit its marks were last drawn at
  mapBox: null,       // the view's box on it as last drawn, in its own pixels
  mapStale: true,     // what it draws has moved since it was drawn
  mapDrag: null,      // a press on the minimap under way, where the view was taken and whether it has moved
  mapOver: false,     // the pointer on the minimap, which keeps it from fading under his hand
  mapAwake: false,    // in Auto, a pan or a zoom has shown it and its two seconds have not run out
  mapHand: '',        // 'show' or 'hide', his own from its button or M, until the screen is opened again
  mapMode: '',        // the minimap's setting it was last drawn for, Auto, On or Off
  mapMarks: [],       // each mark drawn, its id, its classes, its style and its element, which a drag moves in place
  mapViewAt: '',      // the view the box was last drawn for, which a drag leaves as it is
  face: 'canvas',     // the board's view, 'canvas' or 'table', kept for each board in the browser
  tedit: null,        // a title open in the Table view, { id, value }
  tdrag: null,        // a row of the Table view on its way by its grip
  tfocus: null,       // the row the Table view gives the focus back to once drawn again
  tableSoon: 0,       // the Table view's next frame, when one is asked
};

const thStage = () => $('th-stage');
const TH_OPS_ROUTE = '/api/themes-versions';
const TH_BOARDS_ROUTE = '/api/themes-boards';
const TH_READ_ONLY = t('themes.read_only');

/* the board itself, kept aside while a revision is on view */
const thLiveV = () => (TH.viewing ? TH.viewing.live : TH.v);
const thLiveRemoved = () => (TH.viewing ? TH.viewing.removed : TH.removed);

/* An act a revision on view does not allow says so, and is not done. */
function thRefuse(act) {
  if (thMayAct(TH.v, act)) return false;
  say(TH_READ_ONLY, 4000);
  return true;
}

/* ── opening ── */

/* `opts.back` goes back to where it was opened from, `opts.to` names it, `statements`, `pets`, `gets` or
   the case list, and `opts.label` names the case in the bar until the server answers, and stays there when
   it cannot. `opts.gone`, from a page coming back from a restart, is run in place of the screen
   when the case cannot be opened or the file no longer holds `opts.board`. */
async function themesOpen(path, opts = {}) {
  // the GETs screen is this canvas one layer up, opened through getsOpen
  TH.mode = opts.gets ? 'gets' : 'pets';
  // and a participant's LPETs the same canvas over their timepoints' PETs, and in a project of two or more
  // timepoints the PETs canvas is the timepoint's (21 October): the calls name it (thScopeFor), and each
  // keeps its own undo, since two canvases of one workbook can hold boards of one id
  TH.lpets = !!(opts.gets && opts.lpets);
  // and in such a project the project's board is its LGETs, made from the LPETs, which the answer says
  TH.lgets = !!(opts.gets && !opts.lpets && opts.lgets);
  TH.tp = !opts.gets && Number(opts.timepoint) > 1 ? Number(opts.timepoint) : null;
  TH.tps = null;
  TH.scope = TH.lpets ? { lpets: true } : (TH.tp ? { timepoint: TH.tp } : null);
  const canvas = `${path}${TH.lpets ? '|lpets' : TH.tp ? `|t${TH.tp}` : ''}`;
  if (TH.undoPath !== canvas) { TH.undo = []; TH.redo = []; TH.undoPath = canvas; }
  if (TH.stacksPath !== canvas) { TH.stacks = {}; TH.views = {}; TH.undoBoard = null; TH.stacksPath = canvas; thAudioReset(); }
  const ask = ++TH.ask;
  TH.path = path;
  TH.back = opts.back || null;
  TH.label = opts.label || '';
  TH.live = false;
  TH.v = null;
  TH.viewing = null;
  TH.history = null;
  TH.revBoard = null;
  TH.removed = new Set();
  TH.busy = false;
  TH.noting = null;
  thClearSel();
  thPile(false);
  thVmenu(false);
  thXmenu(false);
  thCasemenu(false);
  thSideShut(false);
  thMenuClose();
  thHand(false);
  thViewDraw();
  // the minimap starts again with the screen: nothing of his button or M kept, asleep, drawn afresh
  TH.map = null;
  TH.mapStale = true;
  TH.mapHand = '';
  TH.mapAwake = false;
  TH.mapMode = '';
  TH.mapMarks = [];
  TH.mapViewAt = '';
  $('themes').hidden = false;
  // the band stays out of the way until the project comes with the case
  $('th-band').hidden = true;
  thBandMeasure();
  thWhoDraw(TH.label);
  TH.to = TH_STEPS.includes(opts.to) ? opts.to : 'cases';
  gtScreen(TH.mode === 'gets');
  $('th-demo').hidden = true;
  $('th-board').hidden = true;
  $('th-faces').hidden = true;
  TH.tedit = null;
  TH.tdrag = null;
  $('th-board-name').textContent = '';
  $('th-board-sep').hidden = true;
  $('th-status-counts').textContent = '';
  thSaveLine('', '');
  thExported(null);
  TH.names = null;
  thOutside(null);
  TH.sids = {};
  TH.known = {};
  $('th-world').innerHTML = '';
  thNote('');
  thStage().classList.add('off');
  let data;
  try {
    // the case switcher opens another case on its Current board, or else the board last open, and a
    // restart the board the page was on, which the server shows without writing
    const asked = Object.assign(opts.board ? { workbook: path, board: opts.board } : { workbook: path }, TH.scope || {});
    data = TH.mode === 'gets' ? await api('/api/gets', asked) : await api('/api/themes', asked);
  } catch (err) {
    if (ask !== TH.ask) return;
    if (opts.gone) { $('themes').hidden = true; opts.gone(); return; }
    // a server from before this screen has no such endpoint, and the screen says so and no more
    thNote(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));
    return;
  }
  if (ask !== TH.ask || $('themes').hidden) return;
  // the board a restart came back to, gone from the file, sends the page home
  if (opts.gone && opts.board && String((data.version || {}).id) !== String(opts.board)) {
    $('themes').hidden = true;
    opts.gone();
    return;
  }
  TH.live = true;
  // a server from before the AI's help sends no `ai`, and the page's own copy of the settings
  // stands in, so the controls show and a press says to restart
  TH.config = data.config || (typeof S !== 'undefined' && ((S.data && S.data.config) || S.libConfig)) || null;
  TH.ai = data.ai || { on: aiOn(TH.config), model_name: '' };
  aiPage(TH.config);
  // the AI's help is the GETs' and the PETs', and none of it is on a participant's LPETs yet (21 October)
  TH.lgets = !!(thGets() && !TH.lpets && data.lgets);
  if (TH.lpets || TH.lgets) TH.ai = Object.assign({}, TH.ai, { on: false });
  TH.platform = data.platform || '';
  // a server from before the print view sends no `print`, and the entry then says to restart
  TH.printable = !!data.print;
  // a server from before the Word document sends no `word`, and would write the draft and the CSV
  // in its place, so the entry says to restart
  TH.wordable = !!data.word;
  // a server from before the notes sends no `notes`, and would drop one on the save, so the panel
  // says to restart in the place of the box
  TH.notable = !!data.notes;
  // the Guidance tab's lines, read from themes_guidance.md on every open, and a server from before
  // them sends none, so the tab says to restart
  TH.guidance = Array.isArray(data.guidance) ? data.guidance : null;
  // and a thematic analysis project's lines are its own, ta_themes_guidance.md's, from a server since tarail
  TH.guidanceTa = !!data.guidance_ta;
  TH.project = data.project || null;
  // the project's method, whose words the board takes (tadraw)
  tMethod(TH.project && TH.project.method);
  // and the AI's controls again in that method, a thematic analysis project's all away, its prompts being IPA's: the
  // page's method was the last screen's when they were first drawn above (tarail, taai's finding)
  aiPage(TH.config);
  // the participant's timepoints, which the bar's switch lists on PETs, and the one this canvas is at
  TH.tps = Array.isArray(data.timepoints) && data.timepoints.length >= 2 ? data.timepoints : null;
  if (TH.tps && !thGets()) {
    TH.tp = Number(data.timepoint) || 1;
    TH.scope = { timepoint: TH.tp };
  }
  // the project's name in the path, and the tabs, three or the longitudinal set (dsTabsDraw)
  pathProjectDraw('th-project', TH.project);
  thStepsDraw();
  thBandDraw();
  thAiDraw();
  thWhoDraw(data.case || TH.label, data.person || null);
  TH.demo = !!data.demo;
  $('th-demo').hidden = !data.demo;
  thStage().classList.remove('off');
  thCorners();
  thMapPlace();
  thLoad(data, { fit: true });
  // the sidebar as it was left on this screen, open or closed on its tab, kept in the browser
  thSideRestore();
  // the Cases panel, open unless he closed it
  if (gtCasesStored()) gtCasesOpen(false); else gtDoorDraw();
  thFit();
  // a case's PETs changed since they came in: a window of this app's change comes in by itself, and one
  // from outside it raises Changes made elsewhere (see thStampTick)
  if (TH.mode === 'gets' && ((TH.gets && TH.gets.cases) || []).some((c) => c.status === 'changed')) thStampTick(true);
  // back from a statement's passage, the place on the canvas and the selection it had (16 October)
  if (opts.restore) thBackFromPassage(opts.restore);
  // the serif settles the cards' heights once it has loaded, so they are measured again then
  if (document.fonts && document.fonts.ready) {
    // and the quotes' room and each open stack's made again at the heights the type now gives, as every
    // measure makes it (see thMeasure), before the board makes room where its words now need it
    document.fonts.ready.then(() => {
      if (!TH.live || ask !== TH.ask || TH.drag) return;
      thMeasure();
      thInFile(() => thMakeRoom(TH.v, thSize));
      thPlace();
    });
  }
}

/* One board onto the canvas, from an open or from a board op: its cards, labels, discards and
   picks, the boards beside it, its history and the quotes, with the undo and redo it had when
   it was last on screen. A new board is fitted, and another board, from a switch or a delete, comes
   on where its cards are (thLand), the view of the board left kept for a switch back to it. */
function thLoad(data, opts = {}) {
  // another board coming on than the one on the canvas, and the view of that one kept while it is still a board
  const left = TH.v && TH.meta ? TH.meta.id : null;
  const another = !TH.meta || TH.meta.id !== (data.version || {}).id;
  if (left && another && (data.versions || []).some((x) => x.id === left)) TH.views[left] = { x: TH.view.x, y: TH.view.y, z: TH.view.z };
  // whatever comes in ends a revision on view: the board kept aside is what it replaces
  thViewDrop();
  // and a refused save's card, since the board it spoke of is no longer the one on the canvas as it was
  thStaleHide();
  const cards = {};
  for (const c of data.cards) cards[c.key] = Object.assign({}, c);
  TH.v = {
    cards,
    groups: data.groups.map((g) => Object.assign({}, g, { members: g.members.slice() })),
    discarded: data.discarded.slice(),
    picks: JSON.parse(JSON.stringify(data.picks || {})),
    // why a statement was left out, which the pile shows and a save sends back as `ai`
    ai: { discarded: Object.assign({}, data.discard_reasons || {}) },
    // his sticky notes, and null from a server before them, which would drop one on the save
    stickies: Array.isArray(data.stickies) ? data.stickies.map((n) => Object.assign({}, n)) : null,
    // the statements stacked under each top, and none from a server before the stacks
    stacks: data.stacks && typeof data.stacks === 'object' ? JSON.parse(JSON.stringify(data.stacks)) : {},
    // the close pairs marked Not the same, and none from a server before them
    not_same: Array.isArray(data.not_same) ? JSON.parse(JSON.stringify(data.not_same)) : [],
    // the sidebar's Not placed, on the PETs board alone (20 October)
    waits: TH.mode !== 'gets',
  };
  thWaitsRead(TH.v);
  TH.stickable = Array.isArray(data.stickies);
  // a server from before the close pairs keeps no Not the same, and the page marks none on it
  TH.pairable = Array.isArray(data.not_same);
  TH.pairAt = null;
  // a server from before the stacks sends none, and the page stacks nothing on it
  TH.stackable = Object.prototype.hasOwnProperty.call(data, 'stacks');
  // a stack shown open stays open while the same board is on the canvas
  if (!TH.meta || TH.meta.id !== (data.version || {}).id) TH.opened = new Set();
  TH.shifts = [];
  TH.meta = Object.assign({}, data.version);
  TH.boards = (data.versions || [data.version]).map((x) => Object.assign({}, x));
  // the boards as the file holds them now, which a change made outside is told from, and the short
  // ids, which a server from before them does not send
  thKnow(TH.boards);
  if (data.sids) TH.sids = Object.assign({}, data.sids);
  // the Current board, the one he is going with, and a server from before it sends none
  TH.chosen = data.chosen || null;
  TH.choosable = Object.prototype.hasOwnProperty.call(data, 'chosen');
  // the PETs marked complete, and a server from before the mark sends none
  TH.done = data.complete || null;
  TH.doneable = Object.prototype.hasOwnProperty.call(data, 'complete');
  TH.sheets = data.sheets || [];
  TH.quotes = data.quotes || {};
  TH.hasQuotes = data.quotes !== undefined;
  // a server from before the history sends none, and the History tab says to restart
  TH.history = Array.isArray(data.history) ? data.history.slice() : null;
  TH.z = Object.keys(cards);
  TH.removed = new Set();
  TH.names = null;
  TH.namesAsk += 1;
  TH.noting = null;
  thUseStacks(TH.meta.id);
  // the PET cards he left unfolded on this board, as the browser keeps them with its view
  if (TH.mode === 'gets') gtUnfoldRead(cards);
  // A board newly on the canvas starts its automatic revisions: the first save after an act keeps
  // the board as it stood when it came on, and the timer takes it from there
  if (TH.revBoard !== TH.meta.id) {
    TH.revBoard = TH.meta.id;
    TH.revAt = Date.now();
    TH.revDue = true;
    TH.worked = false;
  }
  thClearSel();
  TH.lastPick = null;
  thPanelDrop();
  thViewDraw();
  thDrawBoard();
  thNote(Object.keys(cards).length ? '' : t('themes.empty.statements'));
  if (TH.mode === 'gets') {
    gtLoad(data);
    // a thematic analysis project's code list, which the status bar and the Codes panel count from (themesbuild)
    if (thTa()) gtCodeListRead(); else TH.codeList = null;
    thNote(Object.keys(cards).length ? '' : (TH.lpets ? t('themes.empty.pets_participant')
      : TH.lgets ? t('themes.empty.lpets_project') : t('themes.empty.pets_project')));
  }
  thRender();
  // anything resting nearer than the margin, a card on a theme's title among it, makes room once measured, as
  // it would with the quotes off (see thInFile)
  if (thInFile(() => thMakeRoom(TH.v, thSize))) thPlace();
  // the board shows in the view it was left in, Canvas or Table
  thFaceRestore();
  if (opts.fit) thFit();
  else if (another) thLand();
  // what is on the canvas is what the file holds, or what an open lays out the same way each time
  if (!TH.dirty && !TH.chain) thSaveLine('done', TH_SAVED);
  // a board a teammate sent, taken in, and its line drawn (team_board.js)
  if (typeof tmbAfterLoad === 'function') tmbAfterLoad();
}

/* Each board keeps its own undo and redo while the case is open here, so a switch back finds
   them where they were. Another case starts with none. */
function thUseStacks(id) {
  if (TH.undoBoard === id) return;
  if (TH.undoBoard) TH.stacks[TH.undoBoard] = { undo: TH.undo, redo: TH.redo };
  const held = TH.stacks[id] || { undo: [], redo: [] };
  TH.undo = held.undo;
  TH.redo = held.redo;
  TH.undoBoard = id;
}

/* The bar's way back, Esc and a step that goes where it goes: Back, where the screen has its entry in the
   browser's history (navGo in app.js), which then takes the way back here, else the way back at once. */
async function themesBack() {
  if (typeof navBackNow === 'function' && navBackNow()) return;
  await themesLeave();
}

/* the way back, true once the screen is left for where it was opened from */
async function themesLeave() {
  thTitleDone(true);
  thNoteDone(true);
  // a name or a note open in the board menu is kept, the way a click away keeps it
  thVmenu(false);
  // a revision on view goes, and the board itself is what is saved
  thViewEnd();
  await thFlush();
  // a save that failed keeps the canvas open, with the line saying why, rather than losing it
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return false; }
  TH.live = false;
  TH.ask += 1;
  thPile(false);
  thXmenu(false);
  thCasemenu(false);
  thSideShut(false);
  thExported(null);
  thMenuClose();
  $('themes').hidden = true;
  if (TH.back) await TH.back();
  return true;
}

/* the canvas's one line, one that says the board could not be read in the one warning tint as every failure
   line is, where it stood in the soft ink (17 October, later) */
function thNote(text, failed = false) {
  $('th-note').textContent = text;
  $('th-note').hidden = !text;
  $('th-note').classList.toggle('said-failed', !!(failed && text));
}

/* ── drawing ── */

function thSize(item) {
  return TH.sizes[item] || (TH.v && TH.v.cards[item] ? TH_CARD : TH.v && thIsSticky(TH.v, item) ? TH_STICKY : TH_LABEL);
}

function thCardTitle(c) {
  if (c.missing) return t('themes.card.missing_tip', { text: c.text });
  if (c.changed) return t('themes.card.changed_tip', { text: c.text, stored: c.stored });
  return c.text;
}

const TH_PICK_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M9.4 6.5H5.6v4h3.8v1.2c0 2-1.1 3.3-3.2 4M18.4 6.5h-3.8v4h3.8v1.2c0 2-1.1 3.3-3.2 4"/></svg>';
const TH_TICK_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M5 12.6 9.8 17.4 19 7.2"/></svg>';
const TH_SPARK_ICON = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 3.2c.95 4.2 2.65 5.9 6.85 6.85-4.2.95-5.9 2.65-6.85 6.85-.95-4.2-2.65-5.9-6.85-6.85C9.35 9.1 11.05 7.4 12 3.2Z"/><path d="M18.4 14.6c.42 1.85 1.17 2.6 3.02 3.02-1.85.42-2.6 1.17-3.02 3.02-.42-1.85-1.17-2.6-3.02-3.02 1.85-.42 2.6-1.17 3.02-3.02Z"/></svg>';
const TH_DEL_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6L6 18"/></svg>';
const TH_NOTE_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M6 8h12M6 12h12M6 16h7"/></svg>';
/* the Current board's mark, a small ribbon, after its name in the board menu and in the switcher */
const TH_CHOSEN_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M7 4.5h10v15.2l-5-3.7-5 3.7z"/></svg>';
const TH_ARR_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="4.5" y="4.5" width="6" height="6" rx="1"/><rect x="13.5" y="4.5" width="6" height="6" rx="1"/><rect x="4.5" y="13.5" width="6" height="6" rx="1"/><rect x="13.5" y="13.5" width="6" height="6" rx="1"/></svg>';

/* the "⋯" a selected card carries on its corner, and a label beside its cross, which opens what a
   right-click on it offers, so nothing is reached by the right-click alone (16 October) */
// its word escaped here, since the constant is made as the script loads, before the shell's escAttr may be there
const TH_MORE_WORD = String(t('themes.more')).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const TH_MORE = `<button type="button" class="th-more" tabindex="-1" title="${TH_MORE_WORD}" aria-label="${TH_MORE_WORD}">&#8943;</button>`;

/* The paper edges under a shut stack's top, the count of cards under it: a stack of two shows one,
   of five four, and past five four with a small plus beside them (Adam, 19 October). */
const TH_EDGES_MAX = 4;
function thStackEdges(held) {
  return { edges: Math.min(TH_EDGES_MAX, held), more: held > TH_EDGES_MAX };
}

/* Every card and label is drawn afresh after an act, which is a hundred elements at most, and a
   drag moves them without drawing anything. */
function thRender() {
  if (!TH.v) return;
  const v = TH.v;
  const world = $('th-world');
  world.innerHTML = '<div class="th-frames"></div><div class="th-cards"></div><div class="th-labels"></div>';
  const [frames, cardBox, labelBox] = world.children;
  TH.els = { cards: {}, labels: {}, frames: {}, stickies: {} };
  // the close pairs' lines lie over the frames and under the cards, so they never cross a card's words
  if (TH.mode !== 'gets' && document.createElementNS) {
    const links = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    links.setAttribute('class', 'th-links');
    links.setAttribute('id', 'th-links');
    links.setAttribute('aria-hidden', 'true');
    world.insertBefore(links, cardBox);
    // and the dot at each end lies over the cards, on their edges
    const ends = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    ends.setAttribute('class', 'th-links th-linkends');
    ends.setAttribute('id', 'th-linkends');
    ends.setAttribute('aria-hidden', 'true');
    world.insertBefore(ends, cardBox.nextSibling);
  }
  // the sticky notes lie over the cards and under the labels
  const stickyBox = document.createElement('div');
  stickyBox.className = 'th-stickies';
  world.insertBefore(stickyBox, labelBox);
  const parents = thParents(v);
  const tints = thTints(v);
  const first = TH.sheets[0];
  const order = TH.z.filter((key) => key in v.cards);
  for (const key of Object.keys(v.cards)) if (!order.includes(key)) order.push(key);
  TH.z = order;
  for (const key of order) {
    const c = v.cards[key];
    if (!thOnCanvas(v, key)) continue;
    const el = document.createElement('div');
    const owner = parents[key];
    // a top carries paper edges under it, one for each statement stacked under it up to four and a
    // small plus beside them past that, and its count on its foot, "3 stacked", and shown open it has
    // none, its stack laid out under it
    const held = TH.mode === 'gets' ? 0 : thStackOf(v, key).length;
    const open = held && TH.opened && TH.opened.has(key);
    const edges = held && !open ? thStackEdges(held) : null;
    el.className = 'th-card'
      + (owner !== undefined ? ` in ${thTintClass(tints[owner])}` : '')
      + (c.missing ? ' missing' : '') + (c.changed ? ' changed' : '')
      + (held ? ` stacked${open ? ' opened' : ` edges-${edges.edges}${edges.more ? ' edges-more' : ''}`}` : '');
    el.dataset.key = key;
    el.title = thCardTitle(c) + (owner === undefined && thWhy(v, key) ? t('themes.card.left_out_tip', { why: thWhy(v, key) }) : '');
    const sheet = c.sheet && c.sheet !== first ? `<span class="th-sheet">${esc(c.sheet)}</span>` : '';
    const mark = c.missing ? `<span class="th-mark">${esc(t('themes.card.missing'))}</span>` : c.changed ? `<span class="th-mark">${esc(t('themes.card.changed'))}</span>` : '';
    const count = held ? `<button type="button" class="th-stackn" tabindex="-1" data-stackn="${escAttr(key)}" title="${escAttr(open ? t('themes.stack.again_tip') : t('themes.stack.show_tip'))}">${esc(t('themes.stack.count', { n: held }))}</button>` : '';
    el.innerHTML = `<p class="th-text">${esc(c.text)}</p>${TH.mode === 'gets' ? '' : thKqHtml(v, key)}`
      + `<div class="th-foot"><span class="th-time">${esc(c.time || '')}</span>${sheet}${mark}${count}</div>`
      + thWhyHtml(v, key, owner) + TH_MORE;
    if (edges && edges.more) el.insertAdjacentHTML('beforeend', '<span class="th-edgemore" aria-hidden="true">+</span>');
    cardBox.appendChild(el);
    TH.els.cards[key] = el;
  }
  thUnderDraw(v, cardBox, parents, tints, first);
  // a sticky note: his words in the handwriting face on its own paper, and a small cross that a
  // selected one carries
  for (const n of thStickies(v)) {
    const el = document.createElement('div');
    el.className = `th-sticky sticky-${TH_STICKY_COLOURS.includes(n.colour) ? n.colour : TH_STICKY_COLOURS[0]}`;
    el.dataset.sticky = n.id;
    el.title = t('themes.sticky.tip');
    el.innerHTML = `<p class="th-sticky-text">${esc(n.text)}</p>`
      + `<button type="button" class="th-sticky-del" tabindex="-1" title="${escAttr(t('themes.sticky.delete_tip'))}" aria-label="${escAttr(t('themes.sticky.delete_label'))}">${TH_DEL_ICON}</button>`
      + (thLocked(v) ? '' : thStripHtml(n));
    stickyBox.appendChild(el);
    TH.els.stickies[n.id] = el;
  }
  for (const g of v.groups) {
    const el = document.createElement('div');
    const upper = g.members.some((m) => thIsGroup(v, m));
    const tint = thTintClass(tints[g.id]);
    el.className = `th-label ${tint}${upper ? ' upper' : ''}`;
    el.dataset.group = g.id;
    const count = thCountText(v, g.id);
    const unit = thUnit(v, g.id, parents);
    // a theme's note follows the count in the tooltip, and a small mark of lines says it has one
    const noted = thNoteOf(g);
    el.title = noted ? t('themes.label.tip_noted', { count, note: noted, unit }) : t('themes.label.tip', { count, unit });
    // its description under its title, two lines at most, the whole of it first in the tooltip (21 October)
    const desc = thDescOf(g);
    if (desc) { el.title = `${thLabelShown(g.label)}\n${desc}\n\n${el.title}`; el.classList.add('described'); }
    const picked = ((v.picks || {})[g.id] || []).length;
    el.innerHTML = `<span class="th-swatch" aria-hidden="true"></span>`
      + `<span class="th-words"><span class="th-title">${esc(thLabelShown(g.label))}</span>${desc ? `<span class="th-desc">${esc(desc)}</span>` : ''}</span>`
      + (noted ? `<span class="th-noted" role="img" aria-label="${escAttr(t('themes.label.has_note'))}">${TH_NOTE_ICON}</span>` : '')
      + (picked ? `<span class="th-picked" title="${escAttr(t('themes.label.picked', { n: picked }))}">${TH_PICK_ICON}</span>` : '')
      + `<button type="button" class="th-arr" tabindex="-1" title="${escAttr(t('themes.label.arrange_tip'))}" aria-label="${escAttr(t('themes.label.arrange_label'))}">${TH_ARR_ICON}</button>`
      + `<button type="button" class="th-del" tabindex="-1" title="${escAttr(t('themes.label.delete_tip'))}" aria-label="${escAttr(t('themes.label.delete_label'))}">${TH_DEL_ICON}</button>`
      + TH_MORE;
    labelBox.appendChild(el);
    TH.els.labels[g.id] = el;
    // every theme draws its frame, round its label and its members, in its own tint
    const frame = document.createElement('div');
    frame.className = `th-frame ${tint}`;
    frame.dataset.frame = g.id;
    // its count, the statements at any depth, in a small badge on the frame's bottom-left corner
    frame.innerHTML = `<span class="th-badge" aria-hidden="true">${thBadgeText(v, g.id)}</span>`;
    frames.appendChild(frame);
    TH.els.frames[g.id] = frame;
  }
  // "Merge into" and the title, over the title strip a drag would merge into, and the line that shows
  // where a drop in a theme's body comes in its order (18 October)
  const merge = document.createElement('div');
  merge.className = 'th-merge';
  merge.id = 'th-merge';
  merge.hidden = true;
  merge.setAttribute('aria-hidden', 'true');
  merge.innerHTML = `<span class="th-merge-word">${esc(t('themes.merge_into'))}</span><span class="th-merge-line"></span>`;
  world.appendChild(merge);
  const insert = document.createElement('div');
  insert.className = 'th-insert';
  insert.id = 'th-insert';
  insert.hidden = true;
  insert.setAttribute('aria-hidden', 'true');
  world.appendChild(insert);
  TH.hoverAt = null;
  TH.stackAt = null;
  if (TH.mode === 'gets') gtDress(v);
  // measured, the room for the quotes and the open stacks made with it (see thMeasure)
  thMeasure();
  thDrawSel();
  thPlace();
  thDrawCounts();
  if (TH.panelOpen) thPanelDraw();
  if (TH.boardOpen) thBoardDraw();
}

/* A selected note's colours in one click: the four papers in a small strip under its bottom edge,
   its own ringed. It shows for one note selected alone, never while it is dragged or its words are
   open, and it zooms with the canvas. */
function thStripHtml(n) {
  return `<span class="th-strip">${TH_STICKY_COLOURS.map((c) => `<button type="button" class="th-strip-dot sticky-${c}${n.colour === c ? ' on' : ''}" `
    + `tabindex="-1" data-colour="${c}" aria-pressed="${n.colour === c}" aria-label="${thColourName(c)}" title="${thColourName(c)}"></button>`).join('')}</span>`;
}

/* ── quotes on cards (Adam, 19 October, way A of the drawings) ── */

/* Quotes on cards, from its button among the status bar's view tools (Adam, about 20:55: "something you
   would want to be able to toggle on and off quickly"): each statement card on the PETs and GETs boards
   shows its own quote under its statement, inside the card, three lines at most, the whole in its
   tooltip and a click away. A card with no quote shows nothing more. Off on a new install and kept in
   the settings. A view, so the board keeps where everything stood and nothing is a step of undo: the room
   the taller cards take is made as a stack shown open makes it (see thRoomMake). */
const thQuotesOn = () => !!(TH.config && TH.config.card_quotes === true);

/* Since 30 October (Adam: "the quotes button maybe has three states: no quotes, two line quotes and then full
   quotes ... full quotes on each card without having to click anything additional") the quotes show in one of
   three ways: Off, Short, three lines at most as before, and Full, each quote whole on its card. Full is kept as
   `card_quotes_full` beside `card_quotes`, so a settings file from before reads as Off or Short, and an app from
   before reads a file kept at Full as Short. Off on a new install. */
const TH_QUOTES_WAYS = ['off', 'short', 'full'];
const thQuotesWay = () => (!thQuotesOn() ? 'off' : TH.config.card_quotes_full === true ? 'full' : 'short');

/* How the button sets the way, two ways drawn for Adam (30 October): 'cycle' (A), each click the next of Off,
   Short and Full, and 'menu' (B), a click opening a menu of the three, the one in use ticked. In both a right
   click on it, or a press held, opens the menu, as Close pairs' does its gap. */
const TH_QUOTES_CONTROL = 'cycle';

/* the button's tooltip for each way, and each way's row in the menu */
const TH_QUOTES_TIPS = { off: 'themes.quotes_way.off', short: 'themes.quotes_way.short', full: 'themes.quotes_way.full' };
const TH_QUOTES_ROWS = { off: 'themes.quotes_way.off_row', short: 'themes.quotes_way.short_row', full: 'themes.quotes_way.full_row' };

/* Notes on cards (Adam, 20 October, from a tester's feedback: "if you're gonna be able to turn on and off the quote
   ... you should also be able to turn on and off where the exploratory notes show"): on the GETs board each
   statement card shows its passage's exploratory notes under its quote, three lines at most, the whole in its
   tooltip, from its button beside Quotes. Off on a new install and kept in the settings, a view as the quotes
   are, the room it takes made the same way. */
const thNotesOn = () => !!(TH.config && TH.config.card_notes === true);

function thEnHtml(v, key) {
  if (!thNotesOn() || TH.mode !== 'gets') return '';
  const c = v && v.cards[key];
  if (!c || c.kind !== 'es') return '';
  const k = gtSplit(key);
  const entry = gtCase(k.kase);
  const line = entry && (entry.lines || {})[k.ident];
  const notes = ((line && line.notes) || []).map((n) => String(n || '').trim()).filter(Boolean);
  if (!notes.length) return '';
  const text = notes.join(' · ');
  return `<p class="th-kq th-en" title="${escAttr(notes.join('\n'))}">${esc(text)}</p>`;
}

function thNotesToggle() {
  if (!TH.live || TH.drag) return;
  thStatusSave('card_notes', !thNotesOn());
}

/* a quote's words without the inverted commas the workbook keeps round it, "(no quote)" as none */
function thBareQuote(said) {
  let text = String(said || '').trim();
  if (text.toLowerCase() === '(no quote)') return '';
  const marks = ['"“”', "'‘’"];
  while (text.length >= 2 && marks.some((m) => m.includes(text[0]) && m.includes(text[text.length - 1]))) text = text.slice(1, -1).trim();
  return text;
}

/* A statement card's own quote, `{ text, time, sheet, seconds, key }`, or null for none: on PETs its
   statement's, from the server's quotes by row, and on GETs a statement card's, from its case's copy.
   A quote in pieces keeps them in order, joined by the ellipsis it was saved with. */
function thCardQuote(v, key) {
  const c = v && v.cards[key];
  if (!c) return null;
  if (TH.mode === 'gets') {
    if (c.kind !== 'es') return null;
    const k = gtSplit(key);
    const entry = gtCase(k.kase);
    const line = entry && (entry.lines || {})[k.ident];
    const q = line ? gtLineQuotes(line, k.ident)[0] : null;
    const text = q ? thBareQuote(q.text) : '';
    return text ? { text, time: q.time || c.time || '', sheet: q.sheet, seconds: q.seconds, key: q.key } : null;
  }
  const held = (TH.quotes || {})[thRowOf(key)];
  const q = held && (held.quotes || []).find((x) => x.key === key);
  const text = thBareQuote(q && q.text);
  // a quote that takes in the passages next to its own carries its range, "25:51–26:50" (quotespan)
  return text ? { text, time: q.time || (held && held.time) || c.time || '', sheet: c.sheet, seconds: held ? held.seconds : c.seconds, key } : null;
}

const thQuoted = (text) => `‘${text}’`;

/* The quote under a card's statement while the quotes show. Short, three lines at most, its whole in its
   tooltip and a click away (see thKqOpen). Full, the whole of it, every piece, with no tooltip and nothing to
   click: a click on it is a click on the card, selecting it, and a double-click edits its statement as one on
   its words does, the passage still in the card's menu and the play button in its Inspector. */
function thKqHtml(v, key) {
  const way = thQuotesWay();
  if (way === 'off') return '';
  const q = thCardQuote(v, key);
  if (!q) return '';
  if (way === 'full') return `<p class="th-kq th-kq-full">${esc(thQuoted(q.text))}</p>`;
  return `<p class="th-kq" data-kq="1" title="${escAttr(thQuoted(q.text))}">${esc(thQuoted(q.text))}</p>`;
}

/* The button: in A each click the next way, Off to Short to Full and back to Off, and in B the menu of the
   three (see TH_QUOTES_CONTROL) */
function thQuotesToggle() {
  if (!TH.live || TH.drag) return;
  if (TH_QUOTES_CONTROL === 'menu') { thQuotesMenu(!TH.qmenu); return; }
  thQuotesSet(TH_QUOTES_WAYS[(TH_QUOTES_WAYS.indexOf(thQuotesWay()) + 1) % TH_QUOTES_WAYS.length]);
}

/* a way chosen, kept in the settings at once in one write, the quote shown whole beside a card put away */
function thQuotesSet(way) {
  if (!TH_QUOTES_WAYS.includes(way) || !TH.live || TH.drag) return;
  thKqClose();
  thStatusSave('card_quotes_full', way === 'full', { card_quotes: way !== 'off' });
}

/* The button as the way stands: pressed in for Short and Full, its mark of two lines for Short and four for
   Full, its tooltip saying which, "Quotes: full". In B it opens its menu, so it says so to a screen reader. */
function thQuotesButton() {
  const btn = $('th-quotes-btn');
  if (!btn) return;
  const way = thQuotesWay();
  const said = t(TH_QUOTES_TIPS[way]);
  btn.dataset.quotes = way;
  btn.setAttribute('aria-pressed', String(way !== 'off'));
  btn.title = said;
  btn.setAttribute('aria-label', said);
  if (TH_QUOTES_CONTROL === 'menu') {
    btn.setAttribute('aria-haspopup', 'menu');
    btn.setAttribute('aria-expanded', String(!!TH.qmenu));
  }
}

/* The menu of the three, from a click on the button in B, and in both from a right click on it or a press
   held: Quotes on cards over Off, Short and Full, the one in use ticked, a choice kept at once, the menu left
   open as Close pairs' gap menu and the bar's counts menu stay. Esc or a click elsewhere puts it away. It
   stands over the button, its foot TH_QMENU_GAP over the bar, and with the status bar off over the tools. */
const TH_QMENU_GAP = 10;
function thQuotesMenu(open, x) {
  const menu = $('th-qmenu');
  if (!menu) return;
  TH.qmenu = !!open;
  menu.hidden = !open;
  thQuotesButton();
  if (!open) return;
  thQuotesMenuDraw();
  const btn = $('th-quotes-btn');
  const b = btn.getBoundingClientRect();
  const bar = $('th-status');
  const top = bar && bar.getBoundingClientRect ? Math.min(bar.getBoundingClientRect().top, b.top) : b.top;
  const at = thStatusMenuSpot(x === undefined ? b.left : x, top - (TH_QMENU_GAP - TH_SMENU_GAP), menu.offsetWidth, menu.offsetHeight, window.innerWidth);
  menu.style.left = `${at.left}px`;
  menu.style.top = `${at.top}px`;
}

function thQuotesMenuDraw() {
  const menu = $('th-qmenu');
  if (!menu) return;
  const way = thQuotesWay();
  menu.innerHTML = `<p class="th-cpmenu-head">${esc(t('themes.quotes_way.head'))}</p>`
    + TH_QUOTES_WAYS.map((w) => `<button type="button" class="ghost small th-qway${w === way ? ' on' : ''}" role="menuitemradio" `
      + `aria-checked="${w === way}" tabindex="-1" data-qway="${w}"><span class="th-cp-tick" aria-hidden="true">${w === way ? TH_TICK_ICON : ''}</span>`
      + `${esc(t(TH_QUOTES_ROWS[w]))}</button>`).join('');
}

/* the cards drawn again with their quotes or without, short or whole, what makes room for them easing there */
function thQuotesDraw() {
  thQuotesButton();
  if (TH.qmenu) thQuotesMenuDraw();
  const notes = $('th-notes-btn');
  if (notes) notes.setAttribute('aria-pressed', String(thNotesOn()));
  thCompactButton();
  if (!TH.v || TH.drag || !$('th-world')) return;
  const from = thSpots(TH.v);
  thRender();
  thEase(from);
}

/* A click on a card's quote shows it whole beside the card: QUOTE, the row's timecode and, on the PETs
   board with a recording, its play button, then the quote, then Show in passage, which does what the card's
   double-click does, and Esc. Esc, a press anywhere else or the wheel puts it away. */
function thKqOpen(key) {
  const v = TH.v;
  const q = thCardQuote(v, key);
  const el = (TH.els.under || {})[key] || TH.els.cards[key];
  const pop = $('th-kqpop');
  if (!q || !el || !pop) return;
  TH.kqpop = key;
  const timed = TH.mode !== 'gets' && q.seconds !== null && q.seconds !== undefined && q.seconds !== '';
  const play = timed
    ? `<button type="button" class="th-play" tabindex="-1" data-play="${escAttr(q.key)}" data-sheet="${escAttr(q.sheet || '')}" data-at="${Number(q.seconds) || 0}" aria-label="${escAttr(t('themes.play.label', { time: q.time }))}" title="${escAttr(t('themes.play.tip', { time: q.time }))}">${PLAY_GLYPH}</button>`
    : '';
  pop.innerHTML = `<p class="th-kqpop-head"><span class="th-kqpop-kicker">${esc(t('themes.quote'))}</span><span class="th-time">${esc(q.time || '')}</span>${play}</p>`
    + `<p class="th-kqpop-text">${esc(thQuoted(q.text))}</p>`
    + `<div class="th-kqpop-foot"><button type="button" class="th-kqpop-go" tabindex="-1" data-kqgo="1">${esc(t('themes.quote_pop.show'))}</button>`
    + `<span class="th-kqpop-esc" aria-hidden="true">${esc(t('themes.key.esc'))}</span></div>`;
  pop.hidden = false;
  // inside the canvas, clear of the title bar over it and the status bar along its foot
  const stage = $('th-stage');
  const s = stage && stage.getBoundingClientRect ? stage.getBoundingClientRect() : null;
  const foot = stage && stage.classList && stage.classList.contains('th-status-on') ? parseFloat(stage.style.getPropertyValue('--th-status-h')) || 0 : 0;
  const area = s && s.width ? { left: s.left, top: s.top, right: s.right, bottom: s.bottom - foot }
    : { left: 0, top: 0, right: window.innerWidth, bottom: window.innerHeight };
  const at = thKqSpot(el.getBoundingClientRect(), pop.offsetWidth, pop.offsetHeight, area, thKqOthers(el, area));
  pop.style.left = `${at.left}px`;
  pop.style.top = `${at.top}px`;
  thPlayerDraw();
}

/* Where the quote shown whole stands, held inside the canvas (`area`): beside the card, its top level with the
   card's, or under it or over it, wherever it covers least of the cards and labels around (`others`, their
   boxes on screen), and between places that cover as much, on the side with more room. It may sit over a
   neighbour as any pop-up does, but never over its own card where another place keeps clear of it. */
function thKqSpot(r, w, h, area, others = []) {
  const gap = 12;
  const pad = 8;
  const hold = (left, top) => ({ left: Math.max(area.left + pad, Math.min(left, area.right - w - pad)),
    top: Math.max(area.top + pad, Math.min(top, area.bottom - h - pad)) });
  const places = [
    { at: hold(r.right + gap, r.top), room: area.right - r.right },
    { at: hold(r.left - gap - w, r.top), room: r.left - area.left },
    { at: hold(r.left, r.bottom + gap), room: area.bottom - r.bottom },
    { at: hold(r.left, r.top - gap - h), room: r.top - area.top },
  ];
  const over = (a, b) => Math.max(0, Math.min(a.left + w, b.right) - Math.max(a.left, b.left))
    * Math.max(0, Math.min(a.top + h, b.bottom) - Math.max(a.top, b.top));
  for (const p of places) {
    p.own = over(p.at, r);
    p.covers = others.reduce((n, b) => n + over(p.at, b), 0);
  }
  places.sort((a, b) => a.own - b.own || a.covers - b.covers || b.room - a.room);
  const { left, top } = places[0].at;
  return { left: Math.round(left), top: Math.round(top) };
}

/* the boxes on screen of the cards, labels and notes the quote shown whole might cover, its own card left out */
function thKqOthers(own, area) {
  const els = [...Object.values(TH.els.cards || {}), ...Object.values(TH.els.under || {}), ...Object.values(TH.els.labels || {}),
    ...Object.values(TH.els.stickies || {})];
  return els.filter((el) => el && el !== own && el.getBoundingClientRect).map((el) => el.getBoundingClientRect())
    .filter((b) => b.width > 0 && b.bottom > area.top && b.top < area.bottom && b.right > area.left && b.left < area.right);
}

function thKqClose() {
  TH.kqpop = null;
  const pop = $('th-kqpop');
  if (pop) pop.hidden = true;
}

/* Show in passage: the quote put away and the card's passage opened, as Go to the passage in its menu opens it */
function thKqGo() {
  const key = TH.kqpop;
  thKqClose();
  if (key) thToPassage(key);
}

/* ── a stack shown open, in place (Adam, 19 October, drawing B) ── */

const TH_UNDER_IN = 14;   // how far in a stack's cards sit under their top
const TH_UNDER_GAP = 8;   // between one card of a stack and the next

/* whether a statement is in a stack shown open, so it is drawn and can be picked */
const thUnderShown = (v, key) => { const top = thTopOf(v, key); return !!(top && TH.opened && TH.opened.has(top) && thOnCanvas(v, top)); };

/* The cards of each stack shown open, each a card as any is, its words, its timecode and its More,
   in its top's tint, a rule down their left from the top, and Stack again under the last. */
function thUnderDraw(v, cardBox, parents, tints, first) {
  TH.els.under = {};
  TH.els.rails = {};
  if (!TH.opened || TH.mode === 'gets') return;
  for (const top of [...TH.opened]) {
    const keys = thStackOf(v, top).filter((k) => v.cards[k]);
    if (!keys.length || !thOnCanvas(v, top)) { TH.opened.delete(top); continue; }
    const owner = parents[top];
    for (const key of keys) {
      const c = v.cards[key];
      const el = document.createElement('div');
      el.className = `th-card th-under${owner !== undefined ? ` in ${thTintClass(tints[owner])}` : ''}`
        + (c.missing ? ' missing' : '') + (c.changed ? ' changed' : '');
      el.dataset.key = key;
      el.dataset.under = top;
      el.title = thCardTitle(c);
      const sheet = c.sheet && c.sheet !== first ? `<span class="th-sheet">${esc(c.sheet)}</span>` : '';
      const mark = c.missing ? `<span class="th-mark">${esc(t('themes.card.missing'))}</span>` : c.changed ? `<span class="th-mark">${esc(t('themes.card.changed'))}</span>` : '';
      el.innerHTML = `<p class="th-text">${esc(c.text)}</p>${thKqHtml(v, key)}`
        + `<div class="th-foot"><span class="th-time">${esc(c.time || '')}</span>${sheet}${mark}</div>` + TH_MORE;
      cardBox.appendChild(el);
      TH.els.under[key] = el;
    }
    const rail = document.createElement('div');
    rail.className = `th-stackrail${owner !== undefined ? ` ${thTintClass(tints[owner])}` : ''}`;
    rail.setAttribute('aria-hidden', 'true');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'th-restack';
    btn.tabIndex = -1;
    btn.dataset.restack = top;
    btn.title = t('themes.stack.restack_tip');
    btn.textContent = t('themes.stack.again');
    cardBox.appendChild(rail);
    cardBox.appendChild(btn);
    TH.els.rails[top] = { rail, btn };
  }
}

/* how much taller a top stands with its stack shown open under it */
function thUnderHeight(v, top) {
  let h = 0;
  for (const key of thStackOf(v, top)) if (TH.usizes[key]) h += TH_UNDER_GAP + TH.usizes[key].h;
  const again = TH.usizes[`again:${top}`];
  return h + TH_UNDER_GAP + (again ? again.h : 22);
}

/* Where everything stands with every stack shut: the cards, labels and notes as copies, each that a
   stack shown open moved down back where it stood, unless something has moved it since. */
function thUnshifted(v) {
  const cards = JSON.parse(JSON.stringify(v.cards));
  const groups = JSON.parse(JSON.stringify(v.groups));
  const stickies = Array.isArray(v.stickies) ? JSON.parse(JSON.stringify(v.stickies)) : [];
  thShiftBack({ cards, groups, stickies }, TH.shifts || []);
  return { cards, groups, stickies };
}

function thShiftObject(v, s) {
  if (s.kind === 'card') return v.cards[s.id] || null;
  if (s.kind === 'group') return v.groups.find((g) => g.id === s.id) || null;
  return (Array.isArray(v.stickies) ? v.stickies : []).find((n) => n.id === s.id) || null;
}

/* each move a stack shown open made, taken back in turn, the last first, where the thing still stands
   where the move left it */
function thShiftBack(v, shifts) {
  for (let i = shifts.length - 1; i >= 0; i -= 1) {
    const s = shifts[i];
    const o = thShiftObject(v, s);
    if (o && Math.round(o.x) === s.at.x && Math.round(o.y) === s.at.y) o.y -= s.dy;
  }
}

/* Room for each stack shown open, in place: the top stands as tall as its stack under it, and what
   stands below it in its column moves down as far, and so on up through every label round it, each
   that grew moving down what stands below it. The moves are a view: the file keeps where everything
   stood (see thUnshifted), and a stack shut again puts back whatever has not moved since. */
function thStacksRoom() {
  const v = TH.v;
  if (!v) return;
  // what an act moved since the room was last made stands where it showed, so it takes its share of the
  // room back off where the file keeps it, or the room would push it down again past where it was let go
  const moved = thRoomMoved(v);
  thShiftBack(v, TH.shifts || []);
  // each top stands at its own height again, as thMeasure leaves it, when the room is made again without a
  // fresh measure (see thRoomFollow)
  for (const [top, h] of Object.entries(TH.baseH || {})) if (TH.sizes[top]) TH.sizes[top] = { w: TH.sizes[top].w, h };
  TH.baseH = {};
  for (let round = 0; round < 4; round += 1) {
    // a second round starts again from each top's own height
    for (const [top, h] of Object.entries(TH.baseH)) if (TH.sizes[top]) TH.sizes[top] = { w: TH.sizes[top].w, h };
    TH.shifts = [];
    TH.baseH = {};
    thRoomMake(v);
    // each that the room took off where it was let go stands that much higher in the file, and the room is made again
    const fix = [];
    for (const [id, at] of moved) {
      const [kind, key] = [id.slice(0, id.indexOf(':')), id.slice(id.indexOf(':') + 1)];
      const o = thShiftObject(v, { kind, id: key });
      if (!o || Math.round(o.y) === Math.round(at.y)) continue;
      const dy = TH.shifts.filter((s) => s.kind === kind && s.id === key).reduce((n, s) => n + s.dy, 0);
      fix.push([o, at.y - dy]);
    }
    // the last round keeps its room, so the board never shows without it
    if (!fix.length || round === 3) break;
    thShiftBack(v, TH.shifts);
    for (const [o, y] of fix) o.y = y;
  }
  TH.roomShown = { cards: v.cards, spots: thSpots(v), room: thRoomSign() };
}

/* What the room is made for, the stacks shown open, so a move since the last time is weighed against the
   same room: one made when a stack opened or shut was made in a room that no longer stands, and its places
   are taken as the file's. The quotes' shares are not in it (23 October, Curt: cards jumped with the quotes
   shown). They were, in the order the cards were drawn, and a card picked up is drawn last, so every first
   drag after an open, and every drop of a card that brings its quote onto the canvas, took the place it was
   let go at, room and all, as the file's: it showed its quote's room lower, and the drop's settle pushed its
   neighbours down the board for good. A move is always weighed in the room it was made in, since the room
   is made again after every move (see thRoomFollow), so the shares need no sign. */
const thRoomSign = () => JSON.stringify([...(TH.opened || [])].sort());

/* The room made again for what moved since it was last made, without drawing the board again: a drop's or a
   new card's settle, the room made on an open or once the type has loaded, a note growing as he types. Each
   so moved stays where it shows and the file keeps it with its share of the room taken off, as an act's
   own move is weighed (see thStacksRoom), so what the page saves is where it stands with the quotes off,
   never where the quotes' room showed it (23 October). Nothing moved, nothing done. */
function thRoomFollow() {
  if (!TH.v || !TH.roomShown || !thRoomMoved(TH.v).size) return;
  thStacksRoom();
}

/* whether the view makes room for anything, a quote shown on a card or a stack shown open */
const thRoomOn = () => !!((TH.shifts && TH.shifts.length) || Object.keys(TH.qextra || {}).length || Object.keys(TH.baseH || {}).length);

/* A card's, a label's or a note's size as the file knows it: a card showing its quote at its height without
   it, a top shown open at its own height, anything else as measured. */
function thBaseSize(item) {
  const s = thSize(item);
  if (TH.qextra && TH.qextra[item] && TH.qfull && TH.qfull[item]) return { w: s.w, h: TH.qfull[item] - TH.qextra[item] };
  if (TH.baseH && TH.baseH[item]) return { w: s.w, h: TH.baseH[item] };
  return s;
}

/* The labels and frames as the file has them, `board` a snapshot (thSnap) or the board on the canvas, to
   weigh a settle in the file against (see thInFile). With no room in the view, the layout as it shows. */
function thFileBoxes(board) {
  const v = TH.v;
  if (!thRoomOn()) return thLabelBoxes(TH.layout);
  const base = board && board.cards ? board : thUnshifted(v);
  const at = Object.assign({}, v, { cards: base.cards, groups: base.groups },
    Array.isArray(base.discarded) ? { discarded: base.discarded } : {}, base.stacks ? { stacks: base.stacks } : {},
    Array.isArray(base.stickies) ? { stickies: base.stickies } : {});
  return thLabelBoxes(thLayout(at, thBaseSize, null));
}

/* Runs `fn` with the board where the file keeps it, every card at its height without its quote and every
   stack shut, and then makes the room again, so what `fn` moves (a settle, the room made on an open) is
   weighed as it is with the quotes off, and only what the act truly reached moves (23 October, Curt: with the
   quotes shown a settle weighed the room's own moves as frames that grew, and pushed whole PETs about the
   board). What it returns comes back. With no room in the view it runs as it is. */
function thInFile(fn) {
  const v = TH.v;
  if (!v || !thRoomOn()) return fn();
  thRoomFollow();
  thShiftBack(v, TH.shifts || []);
  TH.shifts = [];
  for (const k of Object.keys(TH.qextra || {})) {
    if (TH.sizes[k] && TH.qfull[k]) TH.sizes[k] = { w: TH.sizes[k].w, h: TH.qfull[k] - TH.qextra[k] };
  }
  for (const [top, h] of Object.entries(TH.baseH || {})) if (TH.sizes[top]) TH.sizes[top] = { w: TH.sizes[top].w, h };
  // where everything now stands is the file's, so the room is made from there
  TH.roomShown = null;
  try {
    return fn();
  } finally {
    thStacksRoom();
  }
}

/* The cards, labels and notes an act moved since the room was last made, each as `card:<key>`,
   `group:<id>` or `sticky:<id>` to where the act left it: what no longer stands where it showed. None on
   a board put back from a snapshot or read afresh, whose places are the file's (a new `cards`). */
function thRoomMoved(v) {
  const was = TH.roomShown;
  const out = new Map();
  if (!was || was.cards !== v.cards || was.room !== thRoomSign()) return out;
  const now = thSpots(v);
  for (const kind of ['cards', 'groups', 'stickies']) {
    for (const [id, at] of Object.entries(now[kind])) {
      const then = was.spots[kind][id];
      if (then && (then.x !== at.x || then.y !== at.y)) out.set(`${kind === 'cards' ? 'card' : kind === 'groups' ? 'group' : 'sticky'}:${id}`, at);
    }
  }
  return out;
}

/* The room the view makes: first for each card showing its quote, row by row down the board, then
   for each stack shown open. Each card stands at its height without its quote, and then a row at a time
   grows to its whole height, what stands below each card in its column moving down by as much as the
   tallest quote above it, and each label that grew moving down what stands below it, up to the canvas,
   so nothing overlaps and the quotes off again put everything back where it stood. What stands below two
   or more that grew, a sub-PET under two side by side, moves as far as the one that asks most, never their
   sum (30 October, see thRoomTrack). */
function thRoomMake(v) {
  const quoted = Object.keys(TH.qextra || {}).filter((k) => TH.sizes[k] && TH.qfull[k] && v.cards[k] && thOnCanvas(v, k));
  for (const k of quoted) TH.sizes[k] = { w: TH.sizes[k].w, h: TH.qfull[k] - TH.qextra[k] };
  const track = thRoomTrack(v);
  const left = quoted.sort((a, b) => v.cards[a].y - v.cards[b].y || v.cards[a].x - v.cards[b].x);
  while (left.length) {
    const parents = thParents(v);
    const home = (k) => (parents[k] === undefined ? '' : parents[k]);
    const first = left[0];
    const y0 = v.cards[first].y;
    const row = left.filter((k) => home(k) === home(first) && v.cards[k].y - y0 < TH_ROW);
    for (const k of row) left.splice(left.indexOf(k), 1);
    const before = thLayout(v, thSize, null);
    const rooms = row.map((k) => {
      const c = v.cards[k];
      const base = TH.sizes[k].h;
      TH.sizes[k] = { w: TH.sizes[k].w, h: TH.qfull[k] };
      return { x: c.x, y: c.y + base, w: TH.sizes[k].w, d: TH.qextra[k], id: `card:${k}` };
    });
    TH.shifts.push(...thStackRoom(v, thSize, first, rooms, 0, before, track));
    left.sort((a, b) => v.cards[a].y - v.cards[b].y || v.cards[a].x - v.cards[b].x);
  }
  if (!TH.opened || !TH.opened.size) return;
  const tops = [...TH.opened].filter((t) => TH.els.rails[t] && TH.sizes[t])
    .sort((a, b) => v.cards[a].y - v.cards[b].y || v.cards[a].x - v.cards[b].x);
  for (const top of tops) {
    const s = TH.sizes[top];
    TH.baseH[top] = s.h;
    const extra = thUnderHeight(v, top);
    const before = thLayout(v, thSize, null);
    TH.sizes[top] = { w: s.w, h: s.h + extra };
    const c = v.cards[top];
    TH.shifts.push(...thStackRoom(v, thSize, top, { x: c.x, y: c.y + s.h, w: s.w, id: `card:${top}` }, extra, before, track));
  }
}

/* What the room made so far has done, for thStackRoom: where the foot of every card on the canvas and of
   every label's frame stood before any room was made, `feet`, by `card:<key>` and `group:<id>`, and how far
   each card, label and note has moved down since, `moved`, by `card:`, `group:` or `sticky:` and its id.
   (30 October, Adam: a sub-PET under two side by side, the quotes shown in both, stood their two quotes'
   room below them, and every drag up to them pushed them up the board by the same, so the gap stayed.) */
function thRoomTrack(v) {
  const feet = {};
  for (const [key, c] of Object.entries(v.cards)) if (thOnCanvas(v, key)) feet[`card:${key}`] = c.y + thSize(key).h;
  for (const [id, l] of Object.entries(thLayout(v, thSize, null))) if (l && l.frame) feet[`group:${id}`] = l.frame.y + l.frame.h;
  return { feet, moved: new Map() };
}

/* How far `b`, standing below `room`, moves for it: as far as the room's owner, the card or the label that
   grew, has come down since the room began, less what `b` has moved down already, so it keeps the gap it had
   under that owner and no more, and never less than keeps its top below the owner's foot. `has` is how far
   `b` has moved down already. With no `track`, the room's own depth, as before. */
function thRoomBy(room, b, has) {
  if (room.need === undefined) return room.d;
  return Math.max(room.need - has, room.d - Math.max(0, b.y - room.y));
}

/* What stands below `region` in the place `unit` stands in moves down by `d`, a card, a note or a
   label with all it holds as one, and when the label round `unit` grew, what stands below it in its
   own place moves down by as much, up to the canvas. `region` may be a list of regions, each with its
   own `d`, the cards of one row, and what stands below several moves by the most of them. With `track`
   (see thRoomTrack) what stands below two or more that grew in turn, in rows or stacks of their own, moves
   as far as the one that asks most, not by the sum of them (see thRoomBy). The moves made, each as
   thShiftBack takes it. */
function thStackRoom(v, size, unit, region, d, before, track = null) {
  const out = [];
  const moveOne = (kind, o, id, dy) => {
    // a card being lifted out of the stack stays under the pointer (see thStackLift)
    if (kind === 'card' && id === TH.lifting) return;
    o.y += dy;
    out.push({ kind, id, dy, at: { x: Math.round(o.x), y: Math.round(o.y) } });
    if (track) track.moved.set(`${kind}:${id}`, (track.moved.get(`${kind}:${id}`) || 0) + dy);
  };
  // how far each room's owner has come down since the room began, its foot's move
  const need = (room) => (track && room.id && track.feet[room.id] !== undefined
    ? Object.assign(room, { need: room.y + room.d - track.feet[room.id] }) : room);
  const kindOf = (id) => (thIsGroup(v, id) ? 'group' : v.cards[id] ? 'card' : 'sticky');
  const shift = (id, dy) => {
    if (thIsGroup(v, id)) {
      const inside = [id].concat(thDescendants(v, id));
      for (const m of inside) {
        if (thIsGroup(v, m)) moveOne('group', thGroup(v, m), m, dy);
        else if (thOnCanvas(v, m)) moveOne('card', v.cards[m], m, dy);
      }
      for (const n of thStickies(v)) if (n.in && inside.includes(n.in)) moveOne('sticky', n, n.id, dy);
    } else if (v.cards[id]) moveOne('card', v.cards[id], id, dy);
    else if (thSticky(v, id)) moveOne('sticky', thSticky(v, id), id, dy);
  };
  let at = unit;
  let rooms = (Array.isArray(region) ? region : [Object.assign({ d }, region)]).filter((r) => r.d > 0).map(need);
  for (let level = 0; level < 12 && rooms.length; level += 1) {
    const parents = thParents(v);
    const place = parents[at] === undefined || !thIsGroup(v, parents[at]) ? '' : parents[at];
    const kids = (thNeighbours(v, parents).get(place) || []).filter((id) => id !== at);
    for (const id of kids) {
      const b = thSolid(v, size, before, id);
      if (!b) continue;
      const has = track ? track.moved.get(`${kindOf(id)}:${id}`) || 0 : 0;
      const by = rooms.reduce((most, room) => (b.y >= room.y - 1 && b.x < room.x + room.w + TH_MARGIN
        && b.x + b.w > room.x - TH_MARGIN ? Math.max(most, thRoomBy(room, b, has)) : most), 0);
      if (by > 0) shift(id, by);
    }
    if (place === '') break;
    const was = before[place] && before[place].frame;
    const now = thLayout(v, size, null)[place];
    if (!was || !now || !now.frame) break;
    const by = now.frame.y + now.frame.h - (was.y + was.h);
    rooms = by > 0 ? [need({ x: was.x, y: was.y + was.h, w: was.w, d: by, id: `group:${place}` })] : [];
    at = place;
  }
  return out;
}

/* the cards of each stack shown open, under their top wherever it is drawn, and its rule and Stack again */
function thUnderPlace() {
  for (const [top, r] of Object.entries(TH.els.rails || {})) {
    const el = TH.els.cards[top];
    if (!el) continue;
    const x = parseFloat(el.style.left) || 0;
    let y = (parseFloat(el.style.top) || 0) + (TH.baseH[top] || el.offsetHeight);
    const top0 = y;
    const ride = el.style.translate || '';
    for (const key of thStackOf(TH.v, top)) {
      const u = TH.els.under[key];
      if (!u) continue;
      y += TH_UNDER_GAP;
      u.style.left = `${x + TH_UNDER_IN}px`;
      u.style.top = `${y}px`;
      u.style.translate = ride;
      y += (TH.usizes[key] || { h: 80 }).h;
    }
    r.rail.style.left = `${x + 5}px`;
    r.rail.style.top = `${top0}px`;
    r.rail.style.height = `${Math.max(0, y - top0)}px`;
    r.rail.style.translate = ride;
    r.btn.style.left = `${x + TH_UNDER_IN}px`;
    r.btn.style.top = `${y + TH_UNDER_GAP}px`;
    r.btn.style.translate = ride;
  }
}

/* The card under the pointer whose middle a drop would stack what is dragged under (Adam, 19 October,
   drawing B): a statement's card on the canvas, not dragged, and the pointer in its middle, a fifth in
   from each side and a quarter from its top and foot, read where the card stood as the drag began, so
   a card that made way never runs from the pointer. Only statements dragged on their own stack, never
   a label or a note, and only on PETs. */
function thStackHit(clientX, clientY) {
  const d = TH.drag;
  const v = TH.v;
  if (!d || TH.mode === 'gets' || !TH.stackable || thLocked(v)) return null;
  if (TH.sel.groups.size || TH.sel.stickies.size || ![...TH.sel.cards].some((k) => d.moving.has(k))) return null;
  const pt = thToWorld(clientX, clientY);
  for (const [key, at] of Object.entries(d.from.cards || {})) {
    if (d.moving.has(key) || !thOnCanvas(v, key)) continue;
    const s = thSize(key);
    const h = TH.baseH && TH.baseH[key] ? TH.baseH[key] : s.h;
    if (pt.x > at.x + s.w * 0.2 && pt.x < at.x + s.w * 0.8 && pt.y > at.y + h * 0.25 && pt.y < at.y + h * 0.75) return key;
  }
  return null;
}

/* A top's stack shown open in place, or stacked again, `top` null stacking every one shown again. The
   cards below move down to make room, and back as it is stacked again. A view, so no step of undo and
   nothing saved. */
function thStackShow(top) {
  if (!TH.v || TH.drag) return;
  if (!TH.opened) TH.opened = new Set();
  const from = thSpots(TH.v);
  if (top === null) TH.opened.clear();
  else if (TH.opened.has(top)) TH.opened.delete(top);
  else if (thStackOf(TH.v, top).length) TH.opened.add(top);
  else return;
  const opening = top !== null && TH.opened.has(top);
  thPruneSel();
  thRender();
  thEase(from);
  // the table shows a stack under its top in place, so only the canvas glides it clear of the corners
  if (opening && TH.face !== 'table') thStackClear(top);
}

/* A stack opened near the foot of the canvas glides up until its last card stands clear of the bin
   and the zoom in the corners, so no card's words or timecode sit under them, its top never taken
   above the canvas. */
function thStackClear(top) {
  const c = TH.v && TH.v.cards[top];
  const s = TH.sizes && TH.sizes[top];
  const stage = thStage();
  if (!c || !s) return;
  const z = TH.view.z;
  const foot = stage.getBoundingClientRect().top + stage.clientHeight;
  const band = [...stage.querySelectorAll('.th-discard, .th-zoomer')]
    .reduce((m, el) => Math.max(m, foot - el.getBoundingClientRect().top + 12), 0);
  const over = TH.view.y + (c.y + s.h) * z - (stage.clientHeight - band);
  const room = TH.view.y + c.y * z - 56;
  const up = Math.min(over, room);
  if (up <= 0) return;
  thMapGlide(-TH.view.x / z, (up - TH.view.y) / z);
}

/* the menu's entries for a stack on a card: Show stack or Stack again on a top, and with others
   selected, Stack the selected statement (or the 3 selected) under this one */
function thStackItems(v, key) {
  if (!TH.stackable || thLocked(v)) return [];
  const out = [];
  if (thStackOf(v, key).length) out.push({ label: TH.opened && TH.opened.has(key) ? t('themes.stack.again') : t('themes.stack.show'), act: 'stackshow' });
  const others = [...TH.sel.cards].filter((k) => k !== key && thOnCanvas(v, k));
  if (TH.sel.cards.has(key) && others.length) {
    out.push({ label: t('themes.stack.here', { n: others.length }),
      act: 'stackhere', items: others });
  }
  return out;
}

/* S: two statements or more selected stack under the highest of them, the one top left, since higher
   reads as better on the canvas, and one top selected shows its stack or stacks it again. */
function thStackKey() {
  if (thRefuse('stack')) return;
  if (!TH.stackable) { say(RESTART_LINE, 6000); return; }
  const v = TH.v;
  const cards = [...TH.sel.cards].filter((k) => thOnCanvas(v, k));
  if (cards.length === 1 && !TH.sel.groups.size && thStackOf(v, cards[0]).length) { thStackShow(cards[0]); return; }
  if (cards.length < 2) { say(t('themes.stack.select_two')); return; }
  const top = cards.slice().sort((a, b) => v.cards[a].y - v.cards[b].y || v.cards[a].x - v.cards[b].x)[0];
  thStackDo(cards.filter((k) => k !== top), top);
}

/* `items` stacked under `top`, one step of undo, the top selected after */
function thStackDo(items, top) {
  if (thRefuse('stack') || !TH.stackable) return;
  const v = TH.v;
  const before = thSnap(v, TH.removed);
  const done = thStackOnto(v, items, top);
  if (!done.length) return;
  thAck(done);
  for (const k of done) TH.opened.delete(k);
  TH.sel.cards = new Set([top]);
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  thDone(before, t('themes.step.stacked', { n: done.length }));
}

/* Take out of the stack, in the menu: the card just below its stack, in its top's label, clear of what
   is there, and selected. One step of undo. */
function thTakeOutDo(key) {
  if (thRefuse('stack')) return;
  const v = TH.v;
  const top = thTopOf(v, key);
  if (!top) return;
  const before = thSnap(v, TH.removed);
  thTakeOut(v, key, thBelowStack(v, key, top));
  if (!thStackOf(v, top).length) TH.opened.delete(top);
  TH.sel.cards = new Set([key]);
  thDone(before, t('themes.step.unstacked'), { settle: new Set([key]) });
}

/* Where a card taken out of its stack goes: under the stack, at its top's left edge a margin below it,
   or below the stack shown open, and further down past anything it would meet there, never up and
   never aside (19 October), clear of every card, label, note and frame but the ones holding the top. */
function thBelowStack(v, key, top) {
  const parents = thParents(v);
  const holding = new Set(thAncestors(v, top, parents));
  const layout = thLayout(v, thSize, null);
  const s = TH.usizes && TH.usizes[key] ? { w: TH_CARD.w, h: TH.usizes[key].h } : thSize(key);
  const t = thSolid(v, thSize, layout, top);
  const others = [];
  for (const k of Object.keys(v.cards)) if (k !== key && k !== top && thOnCanvas(v, k)) others.push(thSolid(v, thSize, layout, k));
  for (const g of v.groups) {
    const l = layout[g.id];
    if (!l) continue;
    others.push(l.label);
    if (l.body && !holding.has(g.id)) others.push(l.frame);
  }
  for (const n of thStickies(v)) others.push(Object.assign({ x: n.x, y: n.y }, thSize(n.id)));
  const at = { x: t.x, y: t.y + t.h + TH_MARGIN };
  for (let i = 0; i < 400; i += 1) {
    const hit = others.find((o) => o && thMeets({ x: at.x, y: at.y, w: s.w, h: s.h }, o, TH_MARGIN));
    if (!hit) break;
    at.y = hit.y + hit.h + TH_MARGIN;
  }
  return at;
}

/* Make this the top, in the menu: the card on top of its stack in its top's place, the stack kept open
   when it was. One step of undo. */
function thMakeTopDo(key) {
  if (thRefuse('stack')) return;
  const v = TH.v;
  const before = thSnap(v, TH.removed);
  const was = thMakeTop(v, key);
  if (!was) return;
  if (TH.opened.delete(was)) TH.opened.add(key);
  TH.sel.cards = new Set([key]);
  thDone(before, t('themes.step.on_top'));
}

/* A card dragged out of a stack shown open: out of it where it stands, as a card of its top's label,
   the board before it for the drag's one step of undo, or null when it cannot come out. */
function thStackLift(key) {
  const v = TH.v;
  const el = TH.els.under && TH.els.under[key];
  if (!el || !thMayAct(v, 'drag')) return null;
  const before = thSnap(v, TH.removed);
  const at = { x: parseFloat(el.style.left) || 0, y: parseFloat(el.style.top) || 0 };
  const top = thTakeOut(v, key, at);
  if (!top) return null;
  if (!thStackOf(v, top).length) TH.opened.delete(top);
  TH.sel.cards = new Set([key]);
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  // the room the stack still open makes moves nothing it lifts, or the card jumps down from the pointer
  // and lands that far below where it is let go (19 October, the shots)
  TH.lifting = key;
  try { thRender(); } finally { TH.lifting = null; }
  return before;
}

function thMeasure() {
  TH.sizes = {};
  // every top measured at its own height, with no room for its stack in it yet
  TH.baseH = {};
  for (const [key, el] of Object.entries(TH.els.cards)) TH.sizes[key] = { w: el.offsetWidth, h: el.offsetHeight };
  // a card showing its quote, its whole height and the quote's share of it, its margin above it included,
  // which the board makes room for as a view (see thRoomMake)
  TH.qfull = {};
  TH.qextra = {};
  // and on GETs its exploratory notes under it, measured with it (20 October)
  for (const [key, el] of Object.entries(TH.els.cards)) {
    const shown = el.querySelectorAll ? [...el.querySelectorAll('.th-kq, .gt-unfolded')].filter((q) => q.offsetHeight) : [];
    if (!shown.length) continue;
    let extra = 0;
    for (const kq of shown) {
      const css = typeof getComputedStyle === 'function' ? getComputedStyle(kq) : null;
      extra += kq.offsetHeight + (css ? parseFloat(css.marginTop) || 0 : 0);
    }
    TH.qfull[key] = TH.sizes[key].h;
    TH.qextra[key] = Math.min(TH.sizes[key].h, extra);
  }
  // the cards of a stack shown open, and its Stack again under them, measured apart from the board's
  TH.usizes = {};
  for (const [key, el] of Object.entries(TH.els.under || {})) TH.usizes[key] = { w: el.offsetWidth, h: el.offsetHeight };
  for (const [top, r] of Object.entries(TH.els.rails || {})) TH.usizes[`again:${top}`] = { w: r.btn.offsetWidth, h: r.btn.offsetHeight };
  for (const [id, el] of Object.entries(TH.els.stickies || {})) TH.sizes[id] = { w: el.offsetWidth, h: el.offsetHeight };
  thLabelsWiden(TH.v, TH.els.labels, TH.sizes, thSize);
  TH.badges = {};
  for (const [id, el] of Object.entries(TH.els.frames || {})) {
    const badge = el.firstElementChild;
    if (badge) TH.badges[id] = badge.offsetWidth;
  }
  // and the room made again at the heights just measured, the quotes' and each open stack's, so every
  // measure leaves the board as a render does (26 October, stacktop: a measure alone, from the Table view
  // back to the canvas, the open's view restored or a title or note typed, left an open stack's top at its
  // own height, and its label's frame ended above the stack until the next render)
  thStacksRoom();
}

/* A label with a description runs as wide as what it holds, so the description shows whole where its frame
   has the room (Adam, 31 October: "I'd rather have it wider than deeper"). Each label is measured at its usual
   widest, TH_LABEL_W, then one with a description whose body is wider is let run to the body's width and
   measured again, so it never makes its frame wider: a PET's runs to its frame's inside, a sub-PET's to its own.
   One with nothing under it, or a body narrower than TH_LABEL_W, keeps TH_LABEL_W. Its title wraps at the
   same width, and past it the description takes six lines at most (.th-desc), the whole in its tooltip. A
   label's widest leaves every frame's width as it was, so the bodies are known from the first measure. A label
   with no description is as before. `size` reads `sizes`, as the layout takes it. */
const TH_LABEL_W = 340;
function thLabelsWiden(v, els, sizes, size) {
  if (!v) return;
  for (const el of Object.values(els)) el.style.maxWidth = '';
  for (const [id, el] of Object.entries(els)) sizes[id] = { w: el.offsetWidth, h: el.offsetHeight };
  const said = Object.entries(els).filter(([, el]) => el.classList.contains('described'));
  if (!said.length) return;
  // the layout sets each label's place from its body, which the place drawn next sets again: kept as it was
  const at = v.groups.map((g) => [g, g.x, g.y]);
  const layout = thLayout(v, size, null);
  for (const [g, x, y] of at) { g.x = x; g.y = y; }
  const wider = [];
  for (const [id, el] of said) {
    const body = layout[id] && layout[id].body;
    if (body && body.w > TH_LABEL_W) { el.style.maxWidth = `${Math.floor(body.w)}px`; wider.push([id, el]); }
  }
  for (const [id, el] of wider) sizes[id] = { w: el.offsetWidth, h: el.offsetHeight };
}

/* Puts every element where the board says, the labels worked out from what they hold. With a
   drag under way, what moves keeps its place in the page and rides on a translate from where it
   was picked up, which the cards that come along with a label take a moment later, so the group
   moves as a body. The frames reach out to what is dragged, live, and with Alt held what leaves
   its theme shows it: out of its frame and without its tint. What makes way for the drag rests at
   its new place and rides on a translate from there while it slides, `drag.seen` being the board
   as it shows, and the frames are drawn round it as it shows, every label not dragged where it stood as
   the drag began (31 October, see thDragLayout). A drop is told by the title or the body under the pointer
   (see thTargetAt). */
function thPlace(drag) {
  const live = TH.v;
  if (!live) return;
  // what moved since the room was made takes its room before it is drawn
  if (!drag) thRoomFollow();
  const v = drag && drag.seen ? drag.seen : live;
  const moving = drag ? drag.moving : null;
  const out = !!(drag && (drag.alt || drag.out));
  TH.layout = drag ? thDragLayout(v, thSize, moving, out, drag.from && drag.from.groups) : thLayout(v, thSize, null);
  const leaving = out ? thLeavers(v, moving) : new Set();
  const put = (el, id, at, shown = at) => {
    const carried = !!(drag && moving.has(id));
    const from = carried ? drag.starts[id] : at;
    el.style.left = `${from.x}px`;
    el.style.top = `${from.y}px`;
    const off = !carried && (shown.x !== at.x || shown.y !== at.y) ? `${shown.x - at.x}px ${shown.y - at.y}px` : '';
    // a slide driven frame by frame takes no ease of its own from an act before the drag
    if (off) el.classList.remove('ease-from', 'easing', 'nudging', 'landing', 'sent');
    // what came along with a label trails it, eased frame by frame (see thTrail)
    const trails = carried && drag.trail && !drag.grabbed.has(id);
    el.style.translate = trails ? `${drag.trail.x}px ${drag.trail.y}px` : carried ? `${drag.dx}px ${drag.dy}px` : off;
    el.classList.toggle('leaving', leaving.has(id));
  };
  for (const [key, el] of Object.entries(TH.els.cards)) put(el, key, live.cards[key], v.cards[key]);
  for (const [id, el] of Object.entries(TH.els.stickies || {})) {
    const n = thSticky(live, id);
    if (n) put(el, id, n, thSticky(v, id) || n);
  }
  const spots = thBadgeSpots(v, TH.layout, TH.badges || {});
  for (const g of v.groups) {
    const el = TH.els.labels[g.id];
    if (el) put(el, g.id, thGroup(live, g.id), g);
    const frame = TH.els.frames[g.id];
    const box = TH.layout[g.id] && TH.layout[g.id].body && TH.layout[g.id].frame;
    if (frame) {
      frame.hidden = !box;
      frame.classList.toggle('leaving', leaving.has(g.id));
      if (box) {
        frame.style.left = `${box.x}px`;
        frame.style.top = `${box.y}px`;
        frame.style.width = `${box.w}px`;
        frame.style.height = `${box.h}px`;
        if (frame.firstElementChild && spots[g.id] !== undefined) frame.firstElementChild.style.left = `${spots[g.id]}px`;
      }
    }
  }
  thUnderPlace();
  // the close pairs' lines where the cards now stand, and none while a drag is under way
  thLinksDraw(drag);
  // and the minimap draws the board again on its next frame, as it now stands
  thMapMoved();
  // and the Table view, when it shows, once the drag is down
  if (!drag) thTableSoon();
}

function thDrawSel() {
  for (const [key, el] of Object.entries(TH.els.cards)) el.classList.toggle('sel', TH.sel.cards.has(key));
  for (const [key, el] of Object.entries(TH.els.under || {})) el.classList.toggle('sel', TH.sel.cards.has(key));
  for (const [id, el] of Object.entries(TH.els.labels)) el.classList.toggle('sel', TH.sel.groups.has(id));
  // a note selected alone carries the strip of its colours
  const alone = TH.sel.stickies.size === 1 && !TH.sel.cards.size && !TH.sel.groups.size;
  for (const [id, el] of Object.entries(TH.els.stickies || {})) {
    el.classList.toggle('sel', TH.sel.stickies.has(id));
    el.classList.toggle('alone', alone && TH.sel.stickies.has(id));
  }
  // the same selection on the table's rows, and its count on the status bar
  thTableMarks();
  thLinksLit();
  thStatusDraw();
  // and Align and Spread on the toolbar, faint until enough are selected
  thPaletteState();
}

function thDrawCounts() {
  if (TH.mode === 'gets') { gtDrawCounts(); return; }
  const n = thCounts(TH.v);
  // the counts on the status bar, "not placed" for a statement on no PET wherever the app says so, the bar,
  // the panels and the manual (17 October, where the bar said "unplaced" and the rest "not placed")
  thStatusDraw();
  // the sidebar's Not placed and Set aside, and the count on its button, in place of the bin (20 October)
  void n;
  thListDraw();
}

/* ── close pairs (Adam, 20 October, way B and way 1 of the drawings) ── */

/* His rule since supervision on 20 October: statements from the same passage of the same sheet stack under
   the best one unless they say radically different things. Two statements directly in one group, or in one
   PET with no groups, from one sheet within the gap of each other by their passages' times, or by rows on a
   sheet with no times, a row standing for half a minute, are a close pair, as `themes.close_pairs` finds
   them for `board show`. A thin line links the two on the canvas, quiet at rest and strong while either
   card is hovered or selected, drawn under the cards so it never crosses a card's words, and a click on it
   offers Stack under, Not the same and Inspect both. Its button among the status bar's view tools turns it
   on and off, off on a new install and kept in the settings, a right click on it sets the gap, a minute by
   default, and the bar counts the pairs and steps through them. A view, so nothing here is a step of undo
   but what the menu does. Never on the GETs board. */
const TH_CLOSE_GAPS = [15, 30, 60, 120, 300];
const TH_CLOSE_GAP = 60;
const TH_ROW_SECONDS = 30;
const thCloseOn = () => TH.mode !== 'gets' && !!(TH.config && TH.config.close_pairs === true);
function thCloseGap() {
  const n = Number(TH.config && TH.config.close_gap);
  return TH_CLOSE_GAPS.includes(n) ? n : TH_CLOSE_GAP;
}
const thNotSame = (v) => (v && Array.isArray(v.not_same) ? v.not_same : []);

/* a key's sheet, row and line, and two keys in transcript order, as the file keeps a pair */
function thKeyParts(key) {
  const s = String(key);
  const b = s.lastIndexOf(':');
  const a = s.lastIndexOf(':', b - 1);
  return { sheet: s.slice(0, a), row: Number(s.slice(a + 1, b)), line: Number(s.slice(b + 1)) };
}
function thKeyBefore(x, y) {
  const a = thKeyParts(x);
  const b = thKeyParts(y);
  if (a.sheet !== b.sheet) return a.sheet < b.sheet ? -1 : 1;
  return a.row - b.row || a.line - b.line;
}
const thPairOf = (a, b) => [a, b].sort(thKeyBefore);
const thPairId = (p) => `${p.a}\n${p.b}`;

/* The board's close pairs, those marked Not the same left out, each `{ a, b, gap, unit, same, group }`: the
   two keys in transcript order, how far apart in seconds or in rows (`unit` 'rows'), `same` for two of one
   row, and the group both stand in, in the board's group order, then transcript order. */
function thClosePairs(v, gap = thCloseGap()) {
  if (!v || TH.mode === 'gets') return [];
  const apart = new Set(thNotSame(v).map((p) => `${p[0]}\n${p[1]}`));
  const rows = Math.max(1, Math.floor(gap / TH_ROW_SECONDS));
  const out = [];
  for (const g of v.groups) {
    const own = g.members.filter((m) => v.cards[m] && !v.cards[m].missing && thOnCanvas(v, m)).sort(thKeyBefore);
    for (let i = 0; i < own.length; i += 1) {
      for (let j = i + 1; j < own.length; j += 1) {
        const a = own[i];
        const b = own[j];
        const ca = v.cards[a];
        const cb = v.cards[b];
        if (String(ca.sheet) !== String(cb.sheet) || apart.has(`${a}\n${b}`)) continue;
        const ra = ca.row ?? thKeyParts(a).row;
        const rb = cb.row ?? thKeyParts(b).row;
        const timed = ca.seconds !== null && ca.seconds !== undefined && ca.seconds !== ''
          && cb.seconds !== null && cb.seconds !== undefined && cb.seconds !== '';
        const d = timed ? Math.abs(Number(ca.seconds) - Number(cb.seconds)) : Math.abs(ra - rb);
        if (d <= (timed ? gap : rows)) out.push({ a, b, gap: d, unit: timed ? 's' : 'rows', same: ra === rb, group: g.id });
      }
    }
  }
  return out;
}

/* how far apart, "12 s apart", "2 rows apart" on a sheet with no times, "Same passage" for one row */
function thPairWords(p) {
  if (p.same) return t('themes.pair.same');
  if (p.unit === 'rows') return t('themes.pair.rows', { n: p.gap });
  return t('themes.pair.seconds', { gap: p.gap });
}

/* a gap of the menu in words, "15 seconds", "1 minute", "2 minutes" */
const thGapWords = (n) => (n % 60 ? t('themes.pair.gap_seconds', { n }) : t('themes.pair.gap_minutes', { n: n / 60 }));

/* a statement of a pair as the menu names it: its time, or its first words where the two share a time or
   have none */
function thPairName(v, key, other) {
  const c = v.cards[key];
  const o = v.cards[other];
  if (c && c.time && (!o || o.time !== c.time)) return c.time;
  const words = String((c && c.text) || '').split(/\s+/).filter(Boolean);
  return `‘${words.slice(0, 4).join(' ')}${words.length > 4 ? '…' : ''}’`;
}

/* The pairs on the board as the canvas draws them, worked out afresh on each draw, and the one the status
   bar's stepping is on, kept by its two keys so it holds as the board changes. */
function thPairsNow() {
  TH.pairs = thCloseOn() && TH.v && !TH.viewing ? thClosePairs(TH.v) : [];
  if (TH.pairAt && !TH.pairs.some((p) => thPairId(p) === TH.pairAt)) TH.pairAt = null;
  return TH.pairs;
}

/* The "⋯" a selected card carries stands over its top right corner, half out over the gaps beside and above it
   (themes.css, .th-card .th-more, 20px across from 9px outside the corner), so a line keeps this far from the
   middle of that corner, and where it cannot it stops short of it. */
const TH_MORE_CLEAR = 16;
const thMoreAt = (c) => [c.x + c.w + 1, c.y + 1];

/* Where the line between a pair runs, in the board's own units. One card over the other, sharing a stretch of
   their width clear of the lower one's corner, a short straight line from the upper card's foot down into the
   lower card's top, when no other card stands between. Two of one row, out of each card's foot, along the gap
   under the row and into the other's foot. Otherwise out of the upper card's foot, along the gap under it,
   down the gap beside the lower card and into its side. So it keeps to the gaps between cards, and it is drawn
   under the cards all the same, so it never crosses a card's words. A small dot on each card's edge where it
   meets it, over the card and clear of its corner, says which two it links. `d` the line, `ends` the two
   dots. `others` the other cards' boxes. */
function thLinkPath(A, B, others = []) {
  const m = TH_MARGIN / 2;
  const ca = A.x + A.w / 2;
  const cb = B.x + B.w / 2;
  const [U, L] = A.y < B.y ? [A, B] : [B, A];
  if (U.y + U.h <= L.y) {
    const lo = Math.max(U.x, L.x) + 14;
    const hi = Math.min(U.x + U.w - 14, L.x + L.w - TH_MORE_CLEAR - 8);
    if (hi >= lo) {
      const x = Math.round(Math.min(hi, Math.max(lo, (U.x + U.w / 2 + L.x + L.w / 2) / 2)));
      const [y0, y1] = [U.y + U.h, L.y];
      const between = others.some((o) => o.x < x && x < o.x + o.w && o.y < y1 && o.y + o.h > y0);
      if (!between) return { d: `M${x} ${y0}V${y1}`, ends: [[x, y0], [x, y1]] };
    }
  }
  if (Math.abs(A.y - B.y) < TH_CARD.h / 2) {
    const y = Math.max(A.y + A.h, B.y + B.h) + m;
    return { d: `M${ca} ${A.y + A.h}V${y}H${cb}V${B.y + B.h}`, ends: [[ca, A.y + A.h], [cb, B.y + B.h]] };
  }
  const cu = U.x + U.w / 2;
  const right = L.x + L.w / 2 >= cu;
  const x = right ? L.x - m : L.x + L.w + m;
  const y = L.y + Math.min(L.h / 2, 28);
  const edge = right ? L.x : L.x + L.w;
  return { d: `M${cu} ${U.y + U.h}V${U.y + U.h + m}H${x}V${y}H${edge}`, ends: [[cu, U.y + U.h], [edge, y]] };
}

/* The lines drawn afresh where the cards stand, after every place of the board, and none while a drag is
   under way, when they come back at the drop. Each is its pair's group of a quiet line, a wide clear line
   that takes the click, and its gap in the tooltip. Both layers sit inside one clip, the whole board less a
   ring round the corner of each selected card, so no line or dot ever meets a "⋯". */
function thLinksDraw(drag) {
  const svg = $('th-links');
  if (!svg) return;
  const v = TH.v;
  const pairs = drag ? [] : thPairsNow();
  const box = (k) => ({ x: v.cards[k].x, y: v.cards[k].y, w: thSize(k).w, h: thSize(k).h });
  const boxes = {};
  if (pairs.length) for (const k of Object.keys(v.cards)) if (TH.els.cards[k]) boxes[k] = box(k);
  const drawn = pairs.map((p) => thLinkPath(box(p.a), box(p.b),
    Object.entries(boxes).filter(([k]) => k !== p.a && k !== p.b).map(([, b]) => b)));
  const head = (p, i) => `<g class="th-pair" data-pair="${i}" data-a="${escAttr(p.a)}" data-b="${escAttr(p.b)}"><title>${esc(thPairWords(p))}</title>`;
  const clip = `<defs><clipPath id="th-more-clip" clipPathUnits="userSpaceOnUse"><path class="th-more-holes" clip-rule="evenodd" d="${TH_MORE_ALL}"/></clipPath></defs>`;
  svg.innerHTML = `${clip}<g clip-path="url(#th-more-clip)">${pairs.map((p, i) => `${head(p, i)}<path class="th-link" d="${drawn[i].d}"/><path class="th-link-hit" d="${drawn[i].d}"/></g>`).join('')}</g>`;
  const ends = $('th-linkends');
  if (ends) {
    ends.innerHTML = `<g clip-path="url(#th-more-clip)">${pairs.map((p, i) => `${head(p, i)}${drawn[i].ends.map(([x, y]) => `<circle class="th-link-end" cx="${x}" cy="${y}" r="3.5"/>`
      + `<circle class="th-link-hit" cx="${x}" cy="${y}" r="7"/>`).join('')}</g>`).join('')}</g>`;
  }
  thLinksLit();
}

/* the clip's holes, a ring round the corner of each selected card, where its "⋯" shows, cut from the whole
   board by the even-odd rule */
const TH_MORE_ALL = 'M-50000 -50000H50000V50000H-50000Z';
function thMoreHoles() {
  const holes = document.querySelector && document.querySelector('#th-links .th-more-holes');
  if (!holes || !TH.v || !holes.setAttribute) return;
  const r = TH_MORE_CLEAR;
  holes.setAttribute('d', TH_MORE_ALL + [...TH.sel.cards].filter((k) => TH.v.cards[k] && TH.els.cards[k]).map((k) => {
    const c = TH.v.cards[k];
    const [x, y] = thMoreAt({ x: c.x, y: c.y, w: thSize(k).w, h: thSize(k).h });
    return `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`;
  }).join(''));
}

/* each line strong while either of its cards is hovered or selected, or its pair is the one stepped to */
function thLinksLit() {
  const svg = $('th-world');
  if (!svg || !svg.querySelectorAll) return;
  thMoreHoles();
  for (const g of svg.querySelectorAll('.th-pair')) {
    const { a, b } = g.dataset;
    g.classList.toggle('hot', TH.linkHot === a || TH.linkHot === b);
    g.classList.toggle('on', TH.sel.cards.has(a) || TH.sel.cards.has(b));
    g.classList.toggle('cur', TH.pairAt === `${a}\n${b}`);
  }
}

/* the pointer over a card lights its lines */
function thLinksHover(e) {
  if (!TH.pairs || !TH.pairs.length) return;
  const card = e.target.closest ? e.target.closest('.th-card') : null;
  const key = card ? card.dataset.key : null;
  if (key === TH.linkHot) return;
  TH.linkHot = key;
  thLinksLit();
}

/* The button pressed in, or not, and the lines on or off at once, kept in the settings. Off puts away the
   stepping and the menus. */
function thCloseToggle() {
  if (!TH.live || TH.drag || TH.mode === 'gets') return;
  thPairMenuClose();
  TH.pairAt = null;
  thStatusSave('close_pairs', !thCloseOn());
}

/* the lines, the button and the count drawn again after the switch or the gap changed */
function thCloseDraw() {
  const btn = $('th-close-btn');
  if (btn) btn.setAttribute('aria-pressed', String(thCloseOn()));
  if (!TH.v || !$('th-links')) { thStatusDraw(); return; }
  thLinksDraw();
  thStatusDraw();
  thTableSoon();
}

/* The gap's menu, from a right click on the button or a press held on it: the five gaps, the one in use
   ticked, and under a rule the pairs marked Not the same, each with Show again. */
function thCloseMenu(open, x, y) {
  const menu = $('th-cpmenu');
  if (!menu) return;
  TH.cpmenu = !!open;
  menu.hidden = !open;
  if (!open) return;
  thCloseMenuDraw();
  const bar = $('th-status').getBoundingClientRect();
  const at = thStatusMenuSpot(x, bar.top, menu.offsetWidth, menu.offsetHeight, window.innerWidth);
  menu.style.left = `${at.left}px`;
  menu.style.top = `${at.top}px`;
}

function thCloseMenuDraw() {
  const menu = $('th-cpmenu');
  if (!menu) return;
  const gap = thCloseGap();
  const v = TH.v;
  const apart = v ? thNotSame(v).filter((p) => v.cards[p[0]] && v.cards[p[1]]) : [];
  let html = `<p class="th-cpmenu-head">${esc(t('themes.pair.menu_head'))}</p>`
    + TH_CLOSE_GAPS.map((n) => `<button type="button" class="ghost small th-cpgap${n === gap ? ' on' : ''}" role="menuitemradio" `
      + `aria-checked="${n === gap}" tabindex="-1" data-cgap="${n}"><span class="th-cp-tick" aria-hidden="true">${n === gap ? TH_TICK_ICON : ''}</span>${esc(thGapWords(n))}</button>`).join('');
  if (apart.length) {
    html += '<div class="row-menu-rule" role="separator"></div>'
      + `<p class="th-cpmenu-head">${esc(t('themes.pair.apart_count', { n: apart.length }))}</p>`
      + apart.map((p, i) => `<div class="th-cpapart"><span class="th-cpapart-words" title="${escAttr(`${v.cards[p[0]].text}\n\n${v.cards[p[1]].text}`)}">`
        + `${esc(thPairName(v, p[0], p[1]))} and ${esc(thPairName(v, p[1], p[0]))}</span>`
        + `<button type="button" class="ghost small" tabindex="-1" data-cagain="${i}"${thLocked(v) ? ' disabled' : ''}>${esc(t('themes.pair.show_again'))}</button></div>`).join('');
  }
  menu.innerHTML = html;
}

/* a gap picked: kept at once, the menu left open as the status bar's own menu stays */
function thCloseGapPick(n) {
  if (!TH_CLOSE_GAPS.includes(n)) return;
  TH.pairAt = null;
  thStatusSave('close_gap', n);
}

/* The count on the status bar, "3 close pairs", and while stepping "2 of 3 close pairs", with ‹ and ›,
   "3 close" where the bar runs short. Nothing while the lines are off. */
function thCloseStatHtml() {
  if (!thCloseOn() || !TH.v) return '';
  const pairs = TH.pairs || [];
  const n = pairs.length;
  const at = TH.pairAt ? pairs.findIndex((p) => thPairId(p) === TH.pairAt) : -1;
  const num = at >= 0 ? t('themes.pair.at_of', { at: at + 1, n }) : String(n);
  const steps = n ? `<button type="button" class="th-cpstep" tabindex="-1" data-cstep="-1" title="${escAttr(t('themes.pair.before'))}" aria-label="${escAttr(t('themes.pair.before'))}">&#8249;</button>`
    + `<button type="button" class="th-cpstep" tabindex="-1" data-cstep="1" title="${escAttr(t('themes.pair.next'))}" aria-label="${escAttr(t('themes.pair.next'))}">&#8250;</button>` : '';
  return `<span class="th-stat th-stat-close" data-stat="close"><span class="th-stat-n">${esc(num)}</span>`
    + `<span class="th-cp-long">${esc(t('themes.pair.close_long', { n: at < 0 ? n : 0 }))}</span><span class="th-cp-short">${esc(t('themes.pair.close_short'))}</span>${steps}</span>`;
}

/* ‹ or ›: the pair before or the next, both its cards selected and the canvas glided to show them both */
function thPairStep(dir) {
  const pairs = thPairsNow();
  if (!pairs.length) return;
  const at = TH.pairAt ? pairs.findIndex((p) => thPairId(p) === TH.pairAt) : -1;
  const next = at < 0 ? (dir > 0 ? 0 : pairs.length - 1) : (at + dir + pairs.length) % pairs.length;
  const p = pairs[next];
  TH.pairAt = thPairId(p);
  TH.sel.cards = new Set([p.a, p.b]);
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  TH.lastPick = { kind: 'card', id: p.a };
  thDrawSel();
  thPanelFollow();
  thPairShow(p);
  if (TH.face === 'table') thTableShow(p.a);
}

/* the canvas glided so the pair stands in its middle, at the zoom it has, or zoomed out to hold both */
function thPairShow(p) {
  const v = TH.v;
  const stage = thStage();
  if (!v || !stage || !v.cards[p.a] || !v.cards[p.b]) return;
  const u = thUnion([p.a, p.b].map((k) => ({ x: v.cards[k].x, y: v.cards[k].y, w: thSize(k).w, h: thSize(k).h })));
  const room = thFitRoom();
  const z = TH.view.z;
  if (u.w * z > room.w || u.h * z > room.h) { thFitTo(u); return; }
  thMapGlide(u.x + u.w / 2 - (room.x + room.w / 2) / z, u.y + u.h / 2 - (room.y + room.h / 2) / z);
}

/* The menu a click on a line opens, or on a row's mark in the Table view, `from` that row's statement:
   the gap at its head, then Stack under each of the two, which stacks the other under it, Not the same,
   which takes the line off the pair for good, and Inspect both. Esc, a click elsewhere or a choice puts it
   away. */
function thPairMenuOpen(p, clientX, clientY, from = null) {
  thPairMenuClose();
  thMenuClose();
  const v = TH.v;
  if (!v || !p || !v.cards[p.a] || !v.cards[p.b]) return;
  const locked = thLocked(v);
  const other = from === p.a ? p.b : p.a;
  const stacks = from
    ? [[from, t('themes.pair.stack_here', { name: thPairName(v, other, from) })], [other, t('themes.pair.stack_this_under', { name: thPairName(v, other, from) })]]
    : [[p.a, t('themes.pair.stack_under', { name: thPairName(v, p.a, p.b) })], [p.b, t('themes.pair.stack_under', { name: thPairName(v, p.b, p.a) })]];
  const pop = document.createElement('div');
  pop.className = 'row-menu th-cmenu th-pmenu';
  pop.setAttribute('role', 'menu');
  pop.innerHTML = `<p class="th-pmenu-head">${esc(thPairWords(p))}</p>`
    + stacks.map(([top, words]) => `<button type="button" class="ghost small" role="menuitem" tabindex="-1" data-pstack="${escAttr(top)}"${locked ? ' disabled' : ''}><span>${esc(words)}</span></button>`).join('')
    + '<div class="row-menu-rule" role="separator"></div>'
    + `<button type="button" class="ghost small th-pmenu-two" role="menuitem" tabindex="-1" data-papart="1"${locked ? ' disabled' : ''}><span>${esc(t('themes.pair.not_same'))}</span>`
    + `<span class="th-pmenu-sub">${esc(t('themes.pair.not_same_sub'))}</span></button>`
    + `<button type="button" class="ghost small" role="menuitem" tabindex="-1" data-pinspect="1"><span>${esc(t('themes.pair.inspect_both'))}</span></button>`;
  document.body.appendChild(pop);
  const w = pop.offsetWidth;
  const h = pop.offsetHeight;
  pop.style.left = `${Math.max(8, Math.min(clientX + 2, window.innerWidth - w - 8))}px`;
  pop.style.top = `${clientY + 4 + h > window.innerHeight - 8 ? Math.max(8, clientY - 4 - h) : clientY + 4}px`;
  pop.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); });
  // the card a Stack under would keep on top lit while the pointer is on its entry
  pop.addEventListener('pointerover', (e) => {
    const b = e.target.closest('[data-pstack]');
    for (const k of [p.a, p.b]) {
      const el = TH.els.cards[k];
      if (el) el.classList.toggle('th-pair-top', !!b && b.dataset.pstack === k);
    }
  });
  pop.addEventListener('click', (e) => {
    const stack = e.target.closest('[data-pstack]');
    if (stack && !stack.disabled) { const top = stack.dataset.pstack; thPairMenuClose(); thPairStack(p, top); return; }
    const apart = e.target.closest('[data-papart]');
    if (apart && !apart.disabled) { thPairMenuClose(); thPairApart(p); return; }
    if (e.target.closest('[data-pinspect]')) { thPairMenuClose(); thPairInspect(p); }
  });
  TH.pmenu = { el: pop, pair: p };
  TH.linkHot = p.a;
  thLinksLit();
}

function thPairMenuClose() {
  if (!TH.pmenu) return;
  TH.pmenu.el.remove();
  for (const k of [TH.pmenu.pair.a, TH.pmenu.pair.b]) {
    const el = TH.els && TH.els.cards[k];
    if (el) el.classList.remove('th-pair-top');
  }
  TH.pmenu = null;
  TH.linkHot = null;
  thLinksLit();
}

/* Stack under this one: the other of the pair stacked under `top`, as a drop on its middle stacks it, one
   step of undo */
function thPairStack(p, top) {
  if (!TH.stackable) { say(RESTART_LINE, 6000); return; }
  thStackDo([top === p.a ? p.b : p.a], top);
}

/* Not the same: the pair kept with the board as two statements that say different things, its line gone
   for good, listed in the gap's menu to be shown again, one step of undo */
function thPairApart(p) {
  if (thRefuse('stack')) return;
  if (!TH.pairable) { say(RESTART_LINE, 6000); return; }
  const v = TH.v;
  const before = thSnap(v, TH.removed);
  v.not_same = thNotSame(v).concat([thPairOf(p.a, p.b)]);
  if (TH.pairAt === thPairId(p)) TH.pairAt = null;
  thDone(before, t('themes.step.not_same'));
}

/* Show again, in the gap's menu: the mark taken off, the line back while the two stay close, one step of
   undo */
function thPairAgain(i) {
  if (thRefuse('stack') || !TH.pairable) return;
  const v = TH.v;
  const held = thNotSame(v)[i];
  if (!held) return;
  const before = thSnap(v, TH.removed);
  v.not_same = thNotSame(v).filter((x, j) => j !== i);
  thDone(before, t('themes.step.pair_again'));
  thCloseMenuDraw();
}

/* Inspect both: the two selected, in view, and the Inspector open on them, one under the other */
function thPairInspect(p) {
  TH.sel.cards = new Set([p.a, p.b]);
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  TH.lastPick = { kind: 'card', id: p.a };
  thDrawSel();
  thInspectorOpen({ kind: 'card', id: p.a });
  // once the sidebar has made the canvas narrower
  requestAnimationFrame(() => thPairShow(p));
}

/* the close pair the selection is, when it is two cards and no more and they are one */
function thPairSelected(v) {
  if (TH.sel.cards.size !== 2 || TH.sel.groups.size || TH.sel.stickies.size || TH.mode === 'gets') return null;
  const [x, y] = [...TH.sel.cards];
  return thClosePairs(v).find((p) => (p.a === x && p.b === y) || (p.a === y && p.b === x)) || null;
}

/* The Inspector on both of a close pair: "Close pair, 12 s apart", each statement in transcript order with
   its time and its quote, and under them Stack the later under the earlier and Not the same. */
function thPairPanelHtml(v, p) {
  const one = (k) => {
    const c = v.cards[k];
    const q = thCardQuote(v, k);
    const timed = q && q.seconds !== null && q.seconds !== undefined && q.seconds !== '';
    const play = timed
      ? `<button type="button" class="th-play" tabindex="-1" data-play="${escAttr(q.key)}" data-sheet="${escAttr(q.sheet || '')}" data-at="${Number(q.seconds) || 0}" aria-label="${escAttr(t('themes.play.label', { time: q.time }))}" title="${escAttr(t('themes.play.tip', { time: q.time }))}">${PLAY_GLYPH}</button>`
      : '<span class="th-play-none"></span>';
    return `<section class="th-pairone"><p class="th-pair-text">${esc(c.text)}</p>`
      + `<p class="th-panel-meta"><span class="th-time">${esc(c.time || '')}</span>${thSheetTag(c.sheet)}${thSidHtml(k)}</p>`
      + `<h3 class="section-label">${esc(t('themes.quote'))}</h3>`
      + (q ? `<ul class="th-qlist"><li class="th-q">${play}<div class="th-qbody"><p class="th-qtext">${esc(thQuoted(q.text))}</p></div></li></ul>`
        : `<p class="th-qnone">${esc(t('themes.inspector.no_quote'))}</p>`)
      + '</section>';
  };
  const locked = thLocked(v);
  return `<p class="th-panel-meta">${esc(thPairWords(p))}</p>${one(p.a)}${one(p.b)}`
    + (locked ? '' : `<div class="th-leave-row th-pair-acts"><button type="button" class="ghost small" tabindex="-1" data-ipstack="${escAttr(p.a)}">`
      + `${esc(t('themes.pair.stack_a_under_b', { a: thPairName(v, p.b, p.a), b: thPairName(v, p.a, p.b) }))}</button>`
      + `<button type="button" class="ghost small" tabindex="-1" data-ipapart="1">${esc(t('themes.pair.not_same'))}</button></div>`);
}

/* ── the status bar: the board's counts at its left (Adam, 19 October, A of the drawings) ── */

/* The counts the status bar can show, in its order, each with its words: the PETs or GETs on the board,
   the statements in them, those not placed, those in the bin and those stacked under a top, the GETs
   board holding no stacks. Each is said whole, the number first, "0 binned" too, so a count picked by a
   right click stays where it was as the numbers change, as Excel's status bar keeps its own. */
// `binned` keeps its name in the settings, and says Set aside since 20 October. `loose` is the statements on the
// PETs canvas in no PET yet, said only when there are any
const TH_STATUS_COUNTS = ['pets', 'placed', 'stacked', 'binned', 'unplaced', 'loose'];
const TH_STATUS_NAMES = {
  pets: (u, us) => us, placed: (u, us) => t('themes.status.name_placed', { units: us }), unplaced: () => t('themes.status.name_unplaced'), loose: (u) => t('themes.status.name_loose', { unit: u }), binned: () => t('themes.status.name_binned'), stacked: () => t('themes.status.name_stacked'),
};
const thStatusOn = () => !(TH.config && TH.config.status_bar === false);
function thStatusPicked() {
  const held = TH.config && Array.isArray(TH.config.status_counts) ? TH.config.status_counts : TH_STATUS_COUNTS;
  // a choice kept from before `loose` came keeps it shown
  const wanted = held.includes('loose') || !held.includes('unplaced') ? held : held.concat(['loose']);
  return TH_STATUS_COUNTS.filter((name) => wanted.includes(name) && ((name !== 'stacked' && name !== 'loose') || TH.mode !== 'gets'));
}

/* The board's numbers for the status bar: the PETs or GETs, the top themes, in no other, the statements
   placed in them, not placed and binned as the bin's count has them, and those stacked under a top, which
   their top stands for in the other three. On GETs a participant note is never a card counted. */
function thStatusNumbers(v, gets) {
  // a thematic analysis project's board counts its codes, from the code list (themesbuild)
  const coded = gets && thTa() ? gtCodeNumbers(v) : null;
  if (coded) return coded;
  const parents = thParents(v);
  const out = { pets: 0, placed: 0, unplaced: 0, loose: 0, binned: 0, stacked: 0 };
  for (const g of v.groups) if (parents[g.id] === undefined) out.pets += 1;
  for (const [key, card] of Object.entries(v.cards)) {
    if (card.missing || (gets && card.kind === 'pn')) continue;
    if (!gets && thTopOf(v, key)) out.stacked += 1;
    else if (v.discarded.includes(key)) out.binned += 1;
    else if (parents[key] !== undefined) out.placed += 1;
    // on PETs Not placed is what waits in the sidebar, and a card loose on the canvas is in no PET yet
    else if (thWaits(v) && !card.wait) out.loose += 1;
    else out.unplaced += 1;
  }
  return out;
}

/* each count picked as its words, "9 PETs", "1 PET", "89 in PETs", "37 not placed", "4 binned", "6 stacked" */
function thStatusWords(n, gets, picked = TH_STATUS_COUNTS) {
  const unit = gets ? thGetWord() : t('themes.unit.pet'); const units = gets ? thGetWord(true) : t('themes.unit.pets');
  const said = {
    pets: n.subs ? t('codes.board.themes_subs', { themes: t('themes.status.pets', { n: n.pets, unit, units }), subs: t('codes.board.n_subthemes', { n: n.subs }) })
      : t('themes.status.pets', { n: n.pets, unit, units }), placed: t('themes.status.placed', { n: n.placed, units }), unplaced: t('themes.status.unplaced', { n: n.unplaced }),
    loose: t('themes.status.loose', { n: n.loose, unit }), binned: t('themes.status.binned', { n: n.binned }), stacked: t('themes.status.stacked', { n: n.stacked }),
  };
  return picked.filter((name) => name in said && (name !== 'stacked' || !gets) && (name !== 'loose' || (!gets && n.loose > 0)))
    .map((name) => [name, said[name]]);
}

/* The counts as Adam chose them on 26 October, wording C, total first, in his later order (26 October): "46 ES:
   25 in PETs, 5 stacked, 2 set aside, 14 not placed", then "3 PETs", on GETs, LGETs and LPETs "11 cards: 7 in
   GETs, 1 set aside, 3 not placed", a card there being a PET or a sub-PET, stacked after the in-count wherever
   a board has stacks. The parts are the statements or cards in their places,
   a stack's top once and the statements under it apart, so they add to the total. The total shows only
   where every place holding one is shown, and where the bar runs short it goes with the parts after Not
   placed, so no total ever stands over parts that do not reach it. */
const TH_STATUS_PARTS = ['placed', 'stacked', 'binned', 'unplaced', 'loose'];
function thStatusSum(n, gets, picked = TH_STATUS_COUNTS) {
  const words = thStatusWords(n, gets, picked);
  const parts = words.filter(([name]) => TH_STATUS_PARTS.includes(name));
  const pets = words.find(([name]) => name === 'pets') || null;
  const every = TH_STATUS_PARTS.every((name) => !n[name] || parts.some(([shown]) => shown === name));
  const all = TH_STATUS_PARTS.reduce((sum, name) => sum + (n[name] || 0), 0);
  const total = every ? all : null;
  const unit = gets ? (total === 1 ? t('themes.status.card') : total === null ? t('themes.status.cards_head') : t('themes.status.cards')) : t('themes.status.es');
  return { total, unit, parts, pets };
}

/* the sum as the bar says it, for its tooltip and the checks */
function thStatusSumText(sum) {
  const head = sum.parts.length ? t(sum.total === null ? 'themes.status.sum_head' : 'themes.status.sum', { total: sum.total, unit: sum.unit, parts: sum.parts.map((p) => p[1]).join(', ') }) : '';
  return [head, sum.pets ? sum.pets[1] : ''].filter(Boolean);
}

/* how many are selected, "1 ES selected", "2 cards selected", and plainly "3 selected" when PETs, GETs or
   notes are among them */
function thStatusSelected(sel, gets) {
  const k = sel.cards.size + sel.groups.size + sel.stickies.size;
  if (!k) return '';
  if (sel.groups.size || sel.stickies.size) return t('themes.status.selected', { n: k });
  return t(gets ? 'themes.status.selected_cards' : 'themes.status.selected_es', { n: k });
}

/* The counts drawn at the bar's left, each number in the mono face, so they hold still as the numbers
   change, and the bar on or off as the settings say. Off, the canvas keeps the floating zoom bar of before.
   Run on every change of the board and of the settings. */
function thStatusDraw() {
  const stage = $('th-stage');
  const box = $('th-status-counts');
  if (!stage || !box) return;
  const on = thStatusOn();
  const was = stage.classList.contains('th-status-on');
  stage.classList.toggle('th-status-on', on);
  const gets = TH.mode === 'gets';
  const sum = TH.v && on ? thStatusSum(thStatusNumbers(TH.v, gets), gets, thStatusPicked()) : null;
  // how many are selected, after the PETs, on the canvas and in the table alike (20 October, 26 October)
  const chosen = TH.v && on && TH.sel ? thStatusSelected(TH.sel, gets) : '';
  const num = (text) => {
    const at = text.indexOf(' ');
    return `<span class="th-stat-n">${esc(text.slice(0, at))}</span>${esc(text.slice(at))}`;
  };
  let html = '';
  if (sum && sum.parts.length) {
    html += '<span class="th-stat th-stat-sum" data-stat="sum">'
      + (sum.total === null ? '' : `<span class="th-stat-total"><span class="th-stat-n">${sum.total}</span> </span>`)
      + `<span class="th-stat-unit">${esc(sum.unit)}</span>: `
      + sum.parts.map(([name, text], i) => {
        // Not placed and Set aside open the sidebar on their section (20 October)
        const go = (name === 'unplaced' && !gets) || name === 'binned';
        return `<span class="th-part${go ? ' th-stat-go' : ''}" data-stat="${name}"${go ? ` role="button" title="${escAttr(name === 'binned' ? t('themes.status.show_binned') : t('themes.status.show_unplaced'))}"` : ''}>`
          + `${i ? '<span class="th-sep">, </span>' : ''}${num(text)}</span>`;
      }).join('') + '</span>';
  }
  if (sum && sum.pets) html += `<span class="th-stat" data-stat="pets">${num(sum.pets[1])}</span>`;
  if (chosen) html += `<span class="th-stat" data-stat="selected">${num(chosen)}</span>`;
  html += on ? thCloseStatHtml() : '';
  const said = sum ? thStatusSumText(sum).concat(chosen ? [chosen] : []) : [];
  const changed = box.innerHTML !== html;
  if (changed) box.innerHTML = html;
  box.title = said.length ? t('themes.status.tip', { said: said.join('. ') }) : '';
  // Quotes on cards, among the view tools, pressed in while the quotes show, its mark saying short or full
  thQuotesButton();
  // and Close pairs beside it, on the PETs board alone
  const close = $('th-close-btn');
  if (close) { close.setAttribute('aria-pressed', String(thCloseOn())); close.hidden = TH.mode === 'gets'; }
  // and Notes on cards, on the GETs board alone
  const notes = $('th-notes-btn');
  if (notes) { notes.setAttribute('aria-pressed', String(thNotesOn())); notes.hidden = TH.mode !== 'gets'; }
  // and Compact, on a thematic analysis project's board alone (themesbuild)
  thCompactButton();
  // a count grown longer, "9 not placed" to "10 not placed", may need the bar to give way again
  if (was !== on) { thCorners(); thMapPlace(); } else if (on && changed) thCorners();
}

/* the bar on or off, from View's Status Bar in Idiograph's own window, kept in the settings at once, every
   other key kept, as Settings' View keeps it on Save */
function thStatusToggle() {
  if (!TH.config) TH.config = {};
  thStatusSave('status_bar', !thStatusOn());
}

async function thStatusSave(key, value, more = {}) {
  if (!TH.config) TH.config = {};
  // `more`, other settings kept in the same write, as the toolbar's place and whether it is docked are
  // (21 October), since two writes at once race for the settings file
  const all = Object.assign({ [key]: value }, more);
  Object.assign(TH.config, all);
  if (typeof S !== 'undefined') {
    if (S.data && S.data.config) Object.assign(S.data.config, all);
    if (S.libConfig) Object.assign(S.libConfig, all);
  }
  if (key === 'palette_place' || key === 'palette_docked') thPalettePlace(); else if (key === 'arrange_way') thPaletteState();
  else if (key === 'card_quotes' || key === 'card_quotes_full' || key === 'card_notes' || key === 'card_compact') thQuotesDraw();
  else if (key === 'close_pairs' || key === 'close_gap') thCloseDraw(); else thStatusDraw();
  if (TH.smenu) thStatusMenuDraw();
  if (TH.cpmenu) thCloseMenuDraw();
  try {
    const data = await api('/api/settings', all);
    if (!data.config || data.config[key] === undefined) say(RESTART_LINE, 6000);
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  }
}

/* The right-click menu on the bar: a tick for each count, PETs, In PETs, Not placed, Binned and Stacked,
   on GETs GETs, In GETs, Not placed and Binned, each kept at once, the menu staying open as the export's
   ticks do. Esc and a click elsewhere close it. */
function thStatusMenu(open, x, y) {
  const menu = $('th-smenu');
  TH.smenu = !!open;
  menu.hidden = !open;
  if (!open) return;
  thStatusMenuDraw();
  const bar = $('th-status').getBoundingClientRect();
  const at = thStatusMenuSpot(x, bar.top, menu.offsetWidth, menu.offsetHeight, window.innerWidth);
  menu.style.left = `${at.left}px`;
  menu.style.top = `${at.top}px`;
}

/* Where the counts menu stands: its left at the pointer, held inside the window, and its foot 6 pixels above
   the bar's top whatever height on the bar the right click was, so it never covers the bar, where until
   19 October its foot stood at the pointer and a click in the bar's middle put it about 14 pixels over it. */
const TH_SMENU_GAP = 6;
function thStatusMenuSpot(x, barTop, w, h, width) {
  return { left: Math.max(8, Math.min(x, width - w - 8)), top: Math.max(8, barTop - TH_SMENU_GAP - h) };
}

function thStatusMenuDraw() {
  const picked = thStatusPicked();
  const unit = TH.mode === 'gets' ? thGetWord() : t('themes.unit.pet'); const units = TH.mode === 'gets' ? thGetWord(true) : t('themes.unit.pets');
  $('th-smenu').innerHTML = TH_STATUS_COUNTS.filter((name) => name !== 'stacked' || TH.mode !== 'gets')
    .map((name) => `<label class="view-row"><input type="checkbox" data-stat="${name}"${picked.includes(name) ? ' checked' : ''}> ${esc(TH_STATUS_NAMES[name](unit, units))}</label>`)
    .join('');
}

/* a tick changed: the counts as the menu now holds them, those the GETs board has no place for kept as
   they were, so a stacked count picked on PETs stays picked */
function thStatusPick(name, on) {
  const held = TH.config && Array.isArray(TH.config.status_counts) ? TH.config.status_counts : TH_STATUS_COUNTS;
  const next = TH_STATUS_COUNTS.filter((n) => (n === name ? on : held.includes(n)));
  thStatusSave('status_counts', next);
}

/* ── the toolbar: docked under the research question, or floating at the canvas's side ── */

/* The toolbars that dock under a screen's band or float on it by their grip, each named by a spec: the boards' since
   21 October, and since barsD (6 November 2026) the statements screen's, which distil.js names (ES_TOOLS) and every
   function here moves, fits and keeps by the same code. A spec holds its parts' ids, the toolbar `pal`, its row under
   the band `dock`, the room it floats in `stage` and the dashed `slot` where it docks again, the settings that keep it,
   `docked` and `place`, read from `config()`, the room kept clear at the stage's foot, `foot(stage)`, what is measured
   again once it moves, `measure()`, how a change is kept, `save(key, value, more)`, and `alone`, a dock that holds the
   toolbar alone and goes while it floats. The boards' own is the default everywhere. */
const TH_TOOLS = {
  pal: 'th-palette', dock: 'th-dock', stage: 'th-stage', slot: 'th-dock-slot', docked: 'palette_docked', place: 'palette_place',
  alone: false,
  config: () => { if (!TH.config) TH.config = {}; return TH.config; },
  // the status bar, or the zoom bar standing in its place, at the canvas's foot
  foot: (stage) => { const bar = stage.querySelector('.th-zoomer'); return stage.classList.contains('th-status-on') && bar ? bar.offsetHeight : 0; },
  measure: () => thBandMeasure(),
  save: (key, value, more) => thStatusSave(key, value, more),
};

/* Docked under the research question by default (Adam, 21 October, the toolbar drawings), and floating
   while he has pulled it off by its grip, both kept in the settings, on this computer, for every board. */
const thDocked = (spec = TH_TOOLS) => !(spec.config() && spec.config()[spec.docked] === false);

/* Its floating place as the settings hold it: against the left or the right edge of the canvas, its top a
   share of the room the canvas has for it, so it keeps its place as the window or a sidebar changes the
   canvas, and at the left a little above the middle with nothing kept. */
const TH_PALETTE_HOME = { edge: 'left', y: 0.38 };
function thPaletteHeld(spec = TH_TOOLS) {
  const p = spec.config() && spec.config()[spec.place];
  return p && (p.edge === 'left' || p.edge === 'right') && typeof p.y === 'number' ? p : TH_PALETTE_HOME;
}

/* the room it moves in, between the canvas's top and the status bar or the zoom bar, the gutter kept */
function thPaletteRoom(stage, pal, spec = TH_TOOLS) {
  const gutter = 16;
  const foot = spec.foot(stage);
  return { gutter, top: gutter, span: Math.max(0, stage.clientHeight - foot - pal.offsetHeight - 2 * gutter) };
}

/* The toolbar where the settings put it: in the dock under the question, or on the canvas at its place,
   the band's height measured again, and its words giving way to the room it has (see thPaletteFit). */
function thPalettePlace(place, spec = TH_TOOLS) {
  const stage = $(spec.stage);
  const pal = $(spec.pal);
  if (!stage || !pal) return;
  const at = place || thPaletteHeld(spec);
  const dock = $(spec.dock);
  const docked = thDocked(spec) && !!dock;
  pal.classList.toggle('docked', docked);
  pal.setAttribute('aria-orientation', docked ? 'horizontal' : 'vertical');
  // a dock that holds the toolbar alone, the statements screen's, stands only while the toolbar is in it
  if (spec.alone && dock) dock.hidden = !docked;
  if (docked) {
    // between the board at the dock's left and the Inspector's button at its right (option C of the bars)
    const end = dock.querySelector ? dock.querySelector('.th-dock-end') : null;
    if (pal.parentElement !== dock || (end && pal.nextElementSibling !== end)) {
      if (end && dock.insertBefore) dock.insertBefore(pal, end);
      else if (dock.appendChild) dock.appendChild(pal);
    }
    pal.classList.remove('right');
    pal.style.left = '';
    pal.style.right = '';
    pal.style.top = '';
    spec.measure();
    thPaletteFit(spec);
    return;
  }
  if (pal.parentElement !== stage && stage.appendChild) stage.appendChild(pal);
  spec.measure();
  thPaletteFit(spec);
  if (!stage.clientWidth) return;
  const room = thPaletteRoom(stage, pal, spec);
  pal.classList.toggle('right', at.edge === 'right');
  pal.style.left = at.edge === 'right' ? '' : `${room.gutter}px`;
  pal.style.right = at.edge === 'right' ? `${room.gutter}px` : '';
  pal.style.top = `${Math.round(room.top + Math.min(1, Math.max(0, at.y)) * room.span)}px`;
  stage.style.setProperty('--th-pal-w', `${pal.offsetWidth}px`);
}

/* The words give way to the room (drawing 09). Docked, Align and Spread stand under the dots (option B,
   Adam, 26 October 2026), so at 1280 Sticky note, Group, Auto-arrange, Undo and Redo keep their words, and
   where the bar runs out of room Select all loses its word first, then every word goes. Floating, where the
   canvas is too short for the column, Align and Spread go under the dots, and then the words. */
const TH_PAL_STEPS = ['snug', 'terse', 'bare', 'fold'];
const TH_DOCK_STEPS = ['snug', 'bare'];
function thPaletteFit(spec = TH_TOOLS) {
  const pal = $(spec.pal);
  if (!pal || !pal.classList) return;
  pal.classList.remove(...TH_PAL_STEPS);
  if (!pal.getClientRects || !pal.getClientRects().length) return;
  if (pal.classList.contains('docked')) {
    const over = () => pal.scrollWidth > pal.clientWidth + 1;
    pal.classList.add('fold');
    for (const step of TH_DOCK_STEPS) {
      if (!over()) break;
      pal.classList.add(step);
    }
    return;
  }
  const stage = $(spec.stage);
  const room = stage.clientHeight - spec.foot(stage) - 32;
  if (pal.offsetHeight > room) pal.classList.add('fold');
  if (pal.offsetHeight > room) pal.classList.add('bare');
}

/* Where a drag of its grip lets go: the nearer side edge, by the palette's middle, and its top as a share of
   the room, which thPalettePlace draws and the settings keep. A pure function, so the suite can hold it. */
function thPaletteDrop(left, top, width, stageWidth, room) {
  const edge = left + width / 2 > stageWidth / 2 ? 'right' : 'left';
  const y = room.span > 0 ? (top - room.top) / room.span : 0;
  return { edge, y: Math.round(Math.min(1, Math.max(0, y)) * 10000) / 10000 };
}

/* Whether a drag of the floating toolbar lets go where it docks: the pointer over the slot across the top
   of the canvas, or above the canvas, under the question. A pure function, so the suite can hold it. */
const TH_DOCK_REACH = 56;
function thPaletteDocks(pointerY, stageTop) {
  return pointerY - stageTop < TH_DOCK_REACH;
}

/* A drag on the grip moves it where the pointer takes it. Docked, the first few pixels of the drag pull it
   off the dock to float under the pointer. While it moves, a dashed slot across the top of the canvas shows
   where it docks, and letting go there docks it, and anywhere else settles it against the nearer side edge
   and keeps its place. Esc during the drag puts it back where it was. */
function thPaletteGrab(e, spec = TH_TOOLS) {
  if (e.button !== 0) return;
  e.preventDefault();
  e.stopPropagation();
  const stage = $(spec.stage);
  const pal = $(spec.pal);
  const slot = $(spec.slot);
  const was = thDocked(spec);
  const startX = e.clientX;
  const startY = e.clientY;
  let off = was ? null : (() => { const at = pal.getBoundingClientRect(); return { dx: e.clientX - at.left, dy: e.clientY - at.top }; })();
  let near = false;
  pal.classList.add('moving');
  const move = (ev) => {
    if (!off) {
      if (Math.hypot(ev.clientX - startX, ev.clientY - startY) < 5) return;
      // pulled off the dock: it floats with its grip under the pointer
      spec.config()[spec.docked] = false;
      thPalettePlace(undefined, spec);
      off = { dx: pal.offsetWidth / 2, dy: 8 };
    }
    const box = stage.getBoundingClientRect();
    const left = Math.min(Math.max(0, ev.clientX - box.left - off.dx), stage.clientWidth - pal.offsetWidth);
    const top = Math.min(Math.max(0, ev.clientY - box.top - off.dy), stage.clientHeight - pal.offsetHeight);
    pal.style.right = '';
    pal.style.left = `${left}px`;
    pal.style.top = `${top}px`;
    near = thPaletteDocks(ev.clientY, box.top);
    if (slot) { slot.hidden = false; slot.classList.toggle('near', near); }
  };
  const done = (keep) => {
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
    window.removeEventListener('keydown', esc, true);
    pal.classList.remove('moving');
    if (slot) { slot.hidden = true; slot.classList.remove('near'); }
    // a press on the grip of the docked toolbar that never moved leaves it docked
    if (!off) return;
    if (!keep) { spec.config()[spec.docked] = !was ? false : true; thPalettePlace(undefined, spec); return; }
    if (near) { spec.save(spec.docked, true); return; }
    const room = thPaletteRoom(stage, pal, spec);
    const place = thPaletteDrop(pal.offsetLeft, pal.offsetTop, pal.offsetWidth, stage.clientWidth, room);
    spec.save(spec.place, place, was ? { [spec.docked]: false } : {});
  };
  const up = () => done(true);
  const esc = (ev) => { if (ev.key === 'Escape') { ev.preventDefault(); ev.stopPropagation(); done(false); } };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
  window.addEventListener('keydown', esc, true);
}

/* ── the toolbar's tools: Auto-arrange's ways, Align and Spread (21 October) ── */

/* Auto-arrange's three ways, each with its icon, and the one its button repeats, the last he chose,
   kept in the settings: the grid it has always been, Column, one card above another in the order they
   read down the PET, which carries its hierarchy, and Row. */
const TH_ARRANGE_WAYS = ['grid', 'column', 'row'];
const TH_WAY_NAMES = { grid: t('themes.arrange.grid'), column: t('themes.arrange.column'), row: t('themes.arrange.row') };
const TH_TB_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">';
const TH_WAY_ICONS = {
  grid: `${TH_TB_SVG}<rect x="4.5" y="4.5" width="6" height="6" rx="1"/><rect x="13.5" y="4.5" width="6" height="6" rx="1"/><rect x="4.5" y="13.5" width="6" height="6" rx="1"/><rect x="13.5" y="13.5" width="6" height="6" rx="1"/></svg>`,
  column: `${TH_TB_SVG}<rect x="7" y="3.5" width="10" height="4.5" rx="1"/><rect x="7" y="9.75" width="10" height="4.5" rx="1"/><rect x="7" y="16" width="10" height="4.5" rx="1"/></svg>`,
  row: `${TH_TB_SVG}<rect x="3.5" y="7" width="4.5" height="10" rx="1"/><rect x="9.75" y="7" width="4.5" height="10" rx="1"/><rect x="16" y="7" width="4.5" height="10" rx="1"/></svg>`,
};
const thArrangeWay = () => (TH.config && TH_ARRANGE_WAYS.includes(TH.config.arrange_way) ? TH.config.arrange_way : 'grid');

/* Align's six and Spread's two, in the toolbar's order, each named as the right-click menu names it */
const TH_ALIGN_WAYS = ['left', 'centre', 'right', 'top', 'middle', 'bottom'];
const TH_SPREAD_WAYS = ['across', 'down'];
const TH_ALIGN_NAMES = { left: t('themes.align.left_name'), centre: t('themes.align.centre_name'), right: t('themes.align.right_name'), top: t('themes.align.top_name'), middle: t('themes.align.middle_name'),
  bottom: t('themes.align.bottom_name'), across: t('themes.align.across_name'), down: t('themes.align.down_name') };

/* What Align and Spread move: the cards, sticky notes and labels selected on the canvas, a label with all
   it holds, and nothing inside a label that is selected itself, which moves with it. */
function thAlignIds(v = TH.v) {
  if (!v) return [];
  const ids = [...TH.sel.cards].filter((k) => thOnCanvas(v, k))
    .concat([...TH.sel.stickies].filter((id) => thIsSticky(v, id)), [...TH.sel.groups].filter((id) => thIsGroup(v, id)));
  const parents = thParents(v);
  const set = new Set(ids);
  return ids.filter((id) => !thAncestors(v, id, parents).some((a) => set.has(a)));
}

/* Where each box goes for Align and Spread, its top-left corner by its id, from `boxes`, each { id, x, y,
   w, h }. Align moves each to the edge or the centre of the outermost of them, the others along the line
   keeping their order and moving along it only as far as keeps `gap` clear between them, so nothing comes
   to overlap. Spread keeps the first and the last where they stand, across by their left edges and down by
   their tops, and sets those between at even gaps, never under `gap`. themes.py's align_plan is the same.
   A pure function, so the suite can hold it. */
function thAlignPlan(boxes, how, gap = TH_MARGIN) {
  const at = {};
  for (const b of boxes) at[b.id] = { x: b.x, y: b.y, w: b.w, h: b.h };
  const ids = boxes.map((b) => b.id);
  if (ids.length < 2) return at;
  const min = (f) => Math.min(...ids.map(f));
  const max = (f) => Math.max(...ids.map(f));
  const meets = (a, b) => a.x < b.x + b.w + gap && b.x < a.x + a.w + gap && a.y < b.y + b.h + gap && b.y < a.y + a.h + gap;
  if (TH_ALIGN_WAYS.includes(how)) {
    const flat = ['left', 'centre', 'right'].includes(how);
    if (how === 'left') { const e = min((i) => at[i].x); for (const i of ids) at[i].x = e; }
    if (how === 'right') { const e = max((i) => at[i].x + at[i].w); for (const i of ids) at[i].x = e - at[i].w; }
    if (how === 'centre') { const m = (min((i) => at[i].x) + max((i) => at[i].x + at[i].w)) / 2; for (const i of ids) at[i].x = m - at[i].w / 2; }
    if (how === 'top') { const e = min((i) => at[i].y); for (const i of ids) at[i].y = e; }
    if (how === 'bottom') { const e = max((i) => at[i].y + at[i].h); for (const i of ids) at[i].y = e - at[i].h; }
    if (how === 'middle') { const m = (min((i) => at[i].y) + max((i) => at[i].y + at[i].h)) / 2; for (const i of ids) at[i].y = m - at[i].h / 2; }
    // along the line in the order they stood, each moved on past any before it it would now meet
    const axis = flat ? 'y' : 'x';
    const size = flat ? 'h' : 'w';
    const was = Object.fromEntries(boxes.map((b) => [b.id, b]));
    const order = ids.slice().sort((a, b) => (flat ? was[a].y - was[b].y || was[a].x - was[b].x : was[a].x - was[b].x || was[a].y - was[b].y));
    const placed = [];
    for (const i of order) {
      for (let n = 0; n < ids.length; n += 1) {
        const hit = placed.filter((p) => meets(at[i], at[p]));
        if (!hit.length) break;
        at[i][axis] = Math.max(...hit.map((p) => at[p][axis] + at[p][size])) + gap;
      }
      placed.push(i);
    }
  } else if (TH_SPREAD_WAYS.includes(how)) {
    const axis = how === 'across' ? 'x' : 'y';
    const other = axis === 'x' ? 'y' : 'x';
    const size = axis === 'x' ? 'w' : 'h';
    const order = ids.slice().sort((a, b) => at[a][axis] - at[b][axis] || at[a][other] - at[b][other]);
    const first = at[order[0]];
    const last = at[order[order.length - 1]];
    const span = last[axis] + last[size] - first[axis];
    const room = (span - order.reduce((n, i) => n + at[i][size], 0)) / (order.length - 1);
    const step = Math.max(gap, room);
    let pos = first[axis];
    for (const i of order) { at[i][axis] = pos; pos += at[i][size] + step; }
  }
  for (const i of ids) { at[i].x = Math.round(at[i].x); at[i].y = Math.round(at[i].y); }
  return at;
}

/* Align or Spread on the selection, from the toolbar, the dots or the right-click menu: each card, sticky
   note and label moved to its place, a label with all it holds, and what was moved then settles clear of
   what stands beside it as one, its own arrangement kept, so the cards not selected stay where they were.
   One step of undo. Align takes two or more, Spread three or more. */
/* each way's undo step, "Aligned 3 to the centre", "Spread 4 across" */
const TH_ALIGN_STEP = {
  left: (n) => t('themes.step.aligned_left', { n }), centre: (n) => t('themes.step.aligned_centre', { n }),
  right: (n) => t('themes.step.aligned_right', { n }), top: (n) => t('themes.step.aligned_top', { n }),
  middle: (n) => t('themes.step.aligned_middle', { n }), bottom: (n) => t('themes.step.aligned_bottom', { n }),
  across: (n) => t('themes.step.spread_across', { n }), down: (n) => t('themes.step.spread_down', { n }),
};
function thAlignDo(how) {
  if (!TH.live || TH.busy || TH.face === 'table' || thRefuse('align')) return;
  const v = TH.v;
  const ids = thAlignIds(v);
  const spread = TH_SPREAD_WAYS.includes(how);
  if (ids.length < (spread ? 3 : 2)) return;
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  const from = thSpots(v);
  const boxes = ids.map((id) => Object.assign({ id }, thSolid(v, thSize, TH.layout, id))).filter((b) => b.w !== undefined);
  const plan = thAlignPlan(boxes, how);
  let moved = 0;
  for (const b of boxes) {
    const dx = plan[b.id].x - b.x;
    const dy = plan[b.id].y - b.y;
    if (!dx && !dy) continue;
    thShift(v, thBlock(v, [b.id]), dx, dy);
    moved += 1;
  }
  if (!moved) return;
  const what = TH_ALIGN_STEP[how] ? TH_ALIGN_STEP[how](ids.length) : '';
  thDone(before, what, { settle: ids, was, from });
}

/* Auto-arrange from the toolbar: each label selected, or the label a selected card or note is in, else
   every PET on the board, arranged the way named, or the last way, each sub-theme inside its own, as the
   control on a label does. One step of undo. Choosing a way from its menu keeps it for the button. */
function thArrangeTool(way = thArrangeWay()) {
  if (!TH.live || TH.busy || TH.face === 'table' || thRefuse('arrange')) return;
  const v = TH.v;
  const parents = thParents(v);
  let targets = [...TH.sel.groups].filter((id) => thIsGroup(v, id));
  for (const id of [...TH.sel.cards, ...TH.sel.stickies]) if (parents[id] !== undefined) targets.push(parents[id]);
  if (!targets.length && !TH.sel.cards.size && !TH.sel.stickies.size) targets = v.groups.map((g) => g.id).filter((id) => parents[id] === undefined);
  targets = [...new Set(targets)];
  const set = new Set(targets);
  targets = targets.filter((id) => !thAncestors(v, id, parents).some((a) => set.has(a)));
  if (!targets.length) { say(t('themes.arrange.none_in_pet'), 4000); return; }
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  const from = thSpots(v);
  const done = targets.filter((gid) => thArrange(v, gid, thSize, way));
  if (!done.length) { say(t('themes.arrange.nothing_under')); return; }
  for (const gid of done) thAck(thCardsUnder(v, gid));
  const what = done.length === 1 ? t('themes.step.arranged', { label: thGroup(v, done[0]).label }) : t('themes.step.arranged_n', { n: done.length });
  thDone(before, what, { settle: [], was, from, labels: done });
}

/* The toolbar's state: Align faint until two or more are selected, Spread until three, the lot faint on a
   revision on view, and Auto-arrange's button showing the way it repeats. */
function thPaletteState() {
  const pal = $('th-palette');
  if (!pal || !pal.querySelectorAll || !TH.v) return;
  const n = thLocked(TH.v) ? 0 : thAlignIds().length;
  for (const b of pal.querySelectorAll('[data-align]')) b.disabled = n < 2;
  for (const b of pal.querySelectorAll('[data-spread]')) b.disabled = n < 3;
  const way = thArrangeWay();
  const arr = $('th-arrange');
  if (arr && arr.dataset.way !== way) {
    arr.dataset.way = way;
    arr.innerHTML = `${TH_WAY_ICONS[way]}<span class="th-pal-word">${esc(t('themes.label.arrange_label'))}</span>`;
    arr.title = t('themes.arrange.way_tip', { way: TH_WAY_NAMES[way] });
  }
}

/* A menu under one of the toolbar's buttons, its rows each an icon and a word, the row ticked when `on`,
   a row faint when `off`. Esc, a click elsewhere or a choice puts it away. */
function thToolMenu(button, head, rows, pick) {
  thMenuClose();
  const pop = document.createElement('div');
  pop.className = 'row-menu th-cmenu th-tbmenu';
  pop.setAttribute('role', 'menu');
  const tick = `<span class="th-dot-on" aria-hidden="true">${TH_TICK_ICON}</span>`;
  pop.innerHTML = (head ? `<p class="th-cmenu-head">${esc(head)}</p>` : '')
    + rows.map((r, i) => `${r.rule && i ? '<div class="row-menu-rule" role="separator"></div>' : ''}`
      + `${r.head ? `<p class="th-cmenu-head">${esc(r.head)}</p>` : ''}`
      + `<button type="button" class="ghost small" role="${r.on === undefined ? 'menuitem' : 'menuitemradio'}"${r.on === undefined ? '' : ` aria-checked="${r.on}"`} tabindex="-1" data-tbpick="${i}"${r.off ? ' disabled' : ''}>`
      + `<span class="th-tbicon">${r.icon}</span><span>${esc(r.label)}</span>${r.on ? tick : ''}</button>`).join('');
  document.body.appendChild(pop);
  const at = button.getBoundingClientRect();
  pop.style.left = `${Math.max(8, Math.min(at.left, window.innerWidth - pop.offsetWidth - 8))}px`;
  pop.style.top = `${at.bottom + 4 + pop.offsetHeight > window.innerHeight - 8 ? Math.max(8, at.top - 4 - pop.offsetHeight) : at.bottom + 4}px`;
  button.setAttribute('aria-expanded', 'true');
  pop.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); });
  pop.addEventListener('click', (e) => {
    const chosen = e.target.closest('[data-tbpick]');
    if (!chosen || chosen.disabled) return;
    thMenuClose();
    pick(rows[Number(chosen.dataset.tbpick)]);
  });
  TH.menu = { el: pop, item: { kind: 'toolbar' }, targets: [], button };
}

/* Auto-arrange's small arrow: Grid, Column and Row, the one the button repeats ticked. A way chosen is
   kept for the button and runs at once. */
function thArrangeMenu() {
  const way = thArrangeWay();
  thToolMenu($('th-arrange-way'), '', TH_ARRANGE_WAYS.map((w) => ({ way: w, label: TH_WAY_NAMES[w], icon: TH_WAY_ICONS[w], on: w === way })), (r) => {
    if (r.way !== thArrangeWay()) thStatusSave('arrange_way', r.way);
    thArrangeTool(r.way);
  });
}

/* the eight of Align and Spread as menu rows, each faint while the selection is too small for it, or on a
   revision on view, as the toolbar's buttons were */
function thAlignRows() {
  const n = thLocked(TH.v) ? 0 : thAlignIds().length;
  const pal = $('th-palette');
  const icon = (way) => {
    const b = pal && pal.querySelector(`[data-align="${way}"], [data-spread="${way}"]`);
    const svg = b && b.querySelector('svg');
    return svg ? svg.outerHTML : '';
  };
  return TH_ALIGN_WAYS.concat(TH_SPREAD_WAYS).map((w, i) => ({ way: w, label: TH_ALIGN_NAMES[w], icon: icon(w),
    off: n < (TH_SPREAD_WAYS.includes(w) ? 3 : 2), rule: i === 3 || i === 6 }));
}

/* The dots: Align and Spread as two sections of a menu under them (option B, Adam, 26 October 2026), each way
   with its icon and its word as its button had, Left, Centre and Right, Top, Middle and Bottom under Align,
   Across and Down under Spread, each acting on the selection as the button did. */
const TH_ALIGN_WORDS = { left: t('themes.align.left'), centre: t('themes.align.centre'), right: t('themes.align.right'), top: t('themes.align.top'), middle: t('themes.align.middle'), bottom: t('themes.align.bottom'),
  across: t('themes.align.across'), down: t('themes.align.down') };
function thAlignMoreRows() {
  return thAlignRows().map((r, i) => Object.assign(r, { label: TH_ALIGN_WORDS[r.way], head: i === 0 ? t('themes.align.head') : i === 6 ? t('themes.align.spread_head') : '' }));
}
function thAlignMore() {
  thToolMenu($('th-pal-more'), '', thAlignMoreRows(), (r) => thAlignDo(r.way));
}

/* The title bar's words give way to its room (barFit in shell.js, option C of the bars, 26 October 2026): with
   the board, Canvas and Table and the sidebars' buttons gone from it, at 1280 every tool keeps its word, and
   where it runs short the tools lose theirs first, then Experiential statements stands as ES. The name of
   thCountFit stays, run wherever the bar's parts change. */
function thCountFit() {
  const screen = $('themes');
  if (!screen || !screen.querySelector || typeof barFit !== 'function') return;
  barFit(screen.querySelector('.rail'));
}

/* ── the view ── */

function thView() {
  const { x, y, z } = TH.view;
  const world = $('th-world');
  world.style.transform = `translate(${x}px, ${y}px) scale(${z})`;
  // a case's badge on a GETs card keeps its letter legible as the canvas zooms out (see gtBadgeUp)
  const badge = gtBadgeUp(z);
  world.style.setProperty('--gt-up', badge.up.toFixed(3));
  world.classList.toggle('gt-far', badge.far);
  const stage = thStage();
  stage.style.backgroundSize = `${22 * z}px ${22 * z}px`;
  stage.style.backgroundPosition = `${x}px ${y}px`;
  $('th-zoom-level').textContent = `${Math.round(z * 100)}%`;
  // the minimap's box follows the view, and in Auto a pan or a zoom shows the map
  thMapViewed();
}

function thToWorld(clientX, clientY) {
  const r = thStage().getBoundingClientRect();
  return { x: (clientX - r.left - TH.view.x) / TH.view.z, y: (clientY - r.top - TH.view.y) / TH.view.z };
}

function thZoomAt(z, clientX, clientY) {
  const r = thStage().getBoundingClientRect();
  const sx = clientX === undefined ? r.width / 2 : clientX - r.left;
  const sy = clientY === undefined ? r.height / 2 : clientY - r.top;
  const next = Math.min(TH_ZOOM_MAX, Math.max(TH_ZOOM_MIN, z));
  TH.view.x = sx - (sx - TH.view.x) * (next / TH.view.z);
  TH.view.y = sy - (sy - TH.view.y) * (next / TH.view.z);
  TH.view.z = next;
  thView();
}

/* What the board holds on the canvas, each as a box on the board: its cards drawn there, its labels'
   titles and its notes. Fit all fits them, and a board coming on is weighed by them (see thLand). */
function thUsedBoxes() {
  const boxes = [];
  if (!TH.v) return boxes;
  for (const key of Object.keys(TH.els.cards)) {
    const c = TH.v.cards[key];
    if (c) boxes.push({ x: c.x, y: c.y, w: thSize(key).w, h: thSize(key).h });
  }
  for (const g of TH.v.groups) boxes.push(TH.layout[g.id] ? TH.layout[g.id].label : { x: g.x, y: g.y, w: 1, h: 1 });
  for (const n of thStickies(TH.v)) boxes.push({ x: n.x, y: n.y, w: thSize(n.id).w, h: thSize(n.id).h });
  return boxes;
}

/* Everything on the canvas in view, never closer than its own size, and on a board too big for that
   even at the least zoom, its top left (boardview, 30 October 2026), where its middle could be blank.
   An empty board shows the origin in the middle of the canvas. */
function thFit() {
  const stage = thStage();
  const boxes = thUsedBoxes();
  if (!boxes.length) { TH.view = { x: stage.clientWidth / 2, y: stage.clientHeight / 2, z: 1 }; thView(); return; }
  thFitTo(thUnion(boxes), true);
}

/* The part of the canvas a fit fills (20 October, closepairs2): the stage less its margin and less the
   palette and the Bin, which float over it, so Fit all and a step to a close pair never leave a card or a
   frame under either. Each takes the side of the stage it costs least to give up, so the palette at the
   left edge takes a strip down the left, and at 360 wide the Bin in the bottom left corner a strip off the
   foot. In the stage's own pixels. */
function thFitRoom() {
  const stage = thStage();
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  const pad = 56;
  const keep = { l: 0, r: 0, t: 0, b: 0 };
  const at = stage.getBoundingClientRect ? stage.getBoundingClientRect() : null;
  for (const id of ['th-palette', 'th-discard']) {
    const el = $(id);
    if (!at || !el || el.hidden || !el.getBoundingClientRect) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const box = { l: r.left - at.left, r: r.right - at.left, t: r.top - at.top, b: r.bottom - at.top };
    if (box.r <= 0 || box.l >= w || box.b <= 0 || box.t >= h) continue;
    const costs = [['l', box.r / w], ['r', (w - box.l) / w], ['t', box.b / h], ['b', (h - box.t) / h]];
    const [side] = costs.sort((a, b) => a[1] - b[1])[0];
    const need = { l: box.r, r: w - box.l, t: box.b, b: h - box.t }[side] + 12;
    keep[side] = Math.max(keep[side], need);
  }
  const x0 = Math.max(pad, keep.l);
  const y0 = Math.max(pad, keep.t);
  const x1 = Math.max(x0 + 1, w - Math.max(pad, keep.r));
  const y1 = Math.max(y0 + 1, h - Math.max(pad, keep.b));
  return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
}

/* One box in view in the middle of the canvas, the way Fit all brings everything, never closer
   than its own size: a theme's frame, a card, a close pair, or for Fit all the whole board. With
   `corner`, a box wider or taller than the room even at the least zoom starts at the room's left or
   top edge, so its top left is what shows. */
function thFitTo(box, corner = false) {
  if (!box || !box.w || !box.h) return;
  const room = thFitRoom();
  const z = Math.min(1, Math.max(TH_ZOOM_MIN, Math.min(room.w / box.w, room.h / box.h)));
  const x = corner && box.w * z > room.w ? room.x - box.x * z : room.x + room.w / 2 - (box.x + box.w / 2) * z;
  const y = corner && box.h * z > room.h ? room.y - box.y * z : room.y + room.h / 2 - (box.y + box.h / 2) * z;
  TH.view = { x, y, z };
  thView();
}

/* Where another board comes onto the canvas, from the board menu's switch or a board deleted
   (boardview, 30 October 2026, Adam: "it opens up in blank space and then I have to navigate to where
   the cards are"). Since 2 October a switch kept the view of the board left, which showed the next
   board's cards only where the two stood in one place, as a duplicate does. The view still stays when
   it shows any of this board's cards, so two boards laid out alike are compared in one place, and a
   duplicate opens where its original was. Else the view this board was left in, earlier while the
   participant has been open here, when that shows any of its cards. Else the board as an open shows
   it, fitted (thFit): its used canvas in view, or the origin on an empty board. */
function thLand() {
  const kept = TH.meta ? TH.views[TH.meta.id] : null;
  if (!thShows(TH.view) && kept && thShows(kept)) TH.view = { x: kept.x, y: kept.y, z: kept.z };
  if (thShows(TH.view)) { thView(); return; }
  thFit();
}

/* Whether the canvas at `view` shows any of the board's cards, its labels' titles or its notes: the
   middle of one inside the part of the stage a fit fills (thFitRoom). */
function thShows(view) {
  if (!view || !Number.isFinite(view.z) || !view.z) return false;
  const room = thFitRoom();
  return thUsedBoxes().some((b) => {
    const x = view.x + (b.x + b.w / 2) * view.z;
    const y = view.y + (b.y + b.h / 2) * view.z;
    return x >= room.x && x <= room.x + room.w && y >= room.y && y <= room.y + room.h;
  });
}

/* ── the minimap ── */

/* The board's minimap (18 October, Adam's yes of 17 October), Miro's and tldraw's way: a card above the
   zoom bar at the canvas's bottom right, the bar's width and TH_MAP.height high, on the card's paper,
   edge, corners and lift, as the transcript's minimap stands. It draws the board fitted to every card on
   it, a discarded one left out as the canvas leaves it: each card a small rectangle in the tint of the PET
   it stands in, the theme's own however deep it sits, and on GETs in its participant's colour wherever it
   stands, a card in no PET in the faint ink, each sticky note on its own paper, and every PET's, GET's and
   sub-theme's frame an outline in its tint. The part of the canvas in view is a box clear inside a solid
   line of the ink with the rest of the map dimmed, as the transcript's card draws it, and a view holding
   the whole map, as after Fit all, is drawn whole inside it with the board in its place (see thMapAround).
   A click glides the view there, a drag on the box pans it, a press off the box and a drag carry on from
   the place pressed, and the wheel over the card reaches the canvas under it, zooming about the pointer as
   it does anywhere on the canvas. It is drawn at most once a frame: its box on every pan and zoom, and the
   rest on a move, a drag, an open and a change of the card's size, and as the view holding the whole map
   moves. The minimap's Auto, On and Off rule it, the one setting the transcript's card follows: in Auto it
   shows on a pan or a zoom and fades MINIMAP_AWAKE after the last, never while the pointer is on it or a
   drag on it lasts, On keeps it there and Off leaves no map and no button. Its button at the end of the
   zoom bar, "Minimap (M)", and M show it until pressed again or hide it, until the screen is opened
   again. At TH_MAP.narrow pixels of window and below, the map and its button go.
   TH_MAP holds the card's height, the room round the board inside it, the least a mark's side is drawn
   at, the least the box's side is drawn at, the glide's time and the window's width at and below which
   it goes. */
const TH_MAP = { height: 160, pad: 6, least: 2, box: 6, glide: 240, narrow: 767 };
const thMapMode = () => minimapMode(TH.config);
const thMapNarrow = () => !!(window.matchMedia && window.matchMedia(`(max-width: ${TH_MAP.narrow}px)`).matches);

/* What the map draws, in the canvas's own units, each box with the classes it is drawn in: the frames
   from the layout, the sticky notes and the cards on the canvas. `look(card)` is a GETs card's
   participant's colour, and null on PETs. */
function thMapItems(v, layout, size, look) {
  const parents = thParents(v);
  const tints = thTints(v);
  const frames = [];
  for (const g of v.groups) {
    const box = layout[g.id] && layout[g.id].body && layout[g.id].frame;
    if (box) frames.push({ id: `frame:${g.id}`, x: box.x, y: box.y, w: box.w, h: box.h, cls: `tm-frame ${thTintClass(tints[g.id])}` });
  }
  const stickies = thStickies(v).map((n) => {
    const s = size(n.id);
    const paper = TH_STICKY_COLOURS.includes(n.colour) ? n.colour : TH_STICKY_COLOURS[0];
    return { id: n.id, x: n.x, y: n.y, w: s.w, h: s.h, cls: `tm-sticky sticky-${paper}` };
  });
  const cards = [];
  for (const [key, c] of Object.entries(v.cards)) {
    if (!thOnCanvas(v, key)) continue;
    const s = size(key);
    const owner = parents[key];
    const tint = owner !== undefined && tints[owner] ? ` in hue-${tints[owner].hue}` : '';
    const cls = look ? ` tm-case case-${look(c)}` : tint;
    cards.push({ id: key, x: c.x, y: c.y, w: s.w, h: s.h, cls: `tm-card${cls}${c.missing ? ' missing' : ''}` });
  }
  return { frames, stickies, cards, all: frames.concat(stickies, cards) };
}

/* The board fitted into the map's area, `w` by `h` pixels, TH_MAP.pad clear of its edges and centred,
   a small board as large as a big one, across the map's width or its height, whichever it meets first
   (18 October, where until then it was drawn at a fifth of its size at most and a board of a few cards
   sat small in the middle), or null with nothing to draw. A place on the board and a place on the map
   are read one as the other. */
function thMapFit(boxes, w, h) {
  if (!boxes.length || !(w > 2 * TH_MAP.pad) || !(h > 2 * TH_MAP.pad)) return null;
  const u = thUnion(boxes);
  const k = Math.min((w - 2 * TH_MAP.pad) / Math.max(1, u.w), (h - 2 * TH_MAP.pad) / Math.max(1, u.h));
  return { k, ux: u.x, uy: u.y, ox: (w - u.w * k) / 2, oy: (h - u.h * k) / 2, w, h };
}
const thMapToMap = (fit, x, y) => ({ x: fit.ox + (x - fit.ux) * fit.k, y: fit.oy + (y - fit.uy) * fit.k });
const thMapToBoard = (fit, x, y) => ({ x: fit.ux + (x - fit.ox) / fit.k, y: fit.uy + (y - fit.oy) / fit.k });

/* a mark's place and size on the map, never under TH_MAP.least a side */
function thMapStyle(fit, b) {
  const p = thMapToMap(fit, b.x, b.y);
  return `left:${mmPx(p.x)};top:${mmPx(p.y)};width:${mmPx(Math.max(TH_MAP.least, b.w * fit.k))};`
    + `height:${mmPx(Math.max(TH_MAP.least, b.h * fit.k))}`;
}

/* the map's marks, the frames first, then the sticky notes and the cards over them */
function thMapHtml(items, fit) {
  return items.all.map((b) => `<i class="${b.cls}" style="${thMapStyle(fit, b)}"></i>`).join('');
}

/* A drag's frame on the map (18 October, the Mac window's judder, where every frame of a drag wrote
   the whole map again, a mark for every card on the board): the marks as they were drawn stay, the fit
   kept as the drag found it, and only a mark whose place or size has changed is moved, what is dragged,
   what makes way and the frames that reach out to it. False, so the map is drawn whole, when the marks
   are not the ones drawn, a mark come or gone or its tint changed. */
function thMapPatch(items) {
  const marks = TH.mapMarks || [];
  const fit = TH.mapDrawn;
  if (!fit || marks.length !== items.all.length) return false;
  for (let i = 0; i < marks.length; i += 1) {
    const b = items.all[i];
    if (marks[i].id !== b.id || marks[i].cls !== b.cls || !marks[i].el) return false;
  }
  for (let i = 0; i < marks.length; i += 1) {
    const style = thMapStyle(fit, items.all[i]);
    if (marks[i].style === style) continue;
    marks[i].style = style;
    marks[i].el.style.cssText = style;
  }
  return true;
}

/* the part of the board in view, in its own units, from the view and the canvas's width and height */
const thMapSeen = (view, w, h) => ({ x: -view.x / view.z, y: -view.y / view.z, w: w / view.z, h: h / view.z });

/* The view's box on the map: never under TH_MAP.box a side, a small one centred on its place, its whole
   size where the view reaches past the map, the map's edge cutting it as the canvas's edge cuts a card
   (18 October, where until then it was held inside the map and shrank there as though the view had),
   and null where it lies wholly off the map. */
function thMapBox(fit, seen) {
  const a = thMapToMap(fit, seen.x, seen.y);
  let w = seen.w * fit.k;
  let h = seen.h * fit.k;
  let { x, y } = a;
  if (w < TH_MAP.box) { x -= (TH_MAP.box - w) / 2; w = TH_MAP.box; }
  if (h < TH_MAP.box) { y -= (TH_MAP.box - h) / 2; h = TH_MAP.box; }
  if (Math.min(fit.w, x + w) - Math.max(0, x) < 1 || Math.min(fit.h, y + h) - Math.max(0, y) < 1) return null;
  return { x, y, w, h };
}

/* The fit the map is drawn at: the board's own, `board`, or, where the view's box would run past the map
   on every side, as after Fit all, the board and the view together, so the box stands whole inside the map
   with its edge on all four sides and the board inside it as the canvas shows it (18 October, where the
   whole map was washed with no edge to tell where the view was). Anywhere else the board keeps its fit and
   the map's edge cuts the box. `boxes` are what the map draws, `seen` the part of the board in view. */
function thMapAround(board, boxes, seen) {
  if (!board) return null;
  const box = thMapBox(board, seen);
  const over = !!box && box.x <= 0 && box.y <= 0 && box.x + box.w >= board.w && box.y + box.h >= board.h;
  return over ? thMapFit(boxes.concat([seen]), board.w, board.h) : board;
}

/* whether two fits draw the marks in the same places */
const thMapSame = (a, b) => !!a && !!b && ['k', 'ux', 'uy', 'ox', 'oy', 'w', 'h'].every((p) => a[p] === b[p]);

/* Whether the map shows: never before a board is on the canvas, with Off or at TH_MAP.narrow and
   below, as his own button or M says while it has said, and otherwise with On, or in Auto while a pan
   or a zoom keeps it awake. */
function thMapWanted() {
  const mode = thMapMode();
  if (!TH.live || $('themes').hidden || mode === 'off' || thMapNarrow()) return false;
  if (TH.mapHand) return TH.mapHand === 'show';
  return mode === 'on' || !!TH.mapAwake;
}

/* Below about 900px a sidebar lies over the canvas and stops above the bin and the zoom bar, so the
   map, which stands over the bar, gives way while the Inspector's sidebar or the Cases panel is open
   over it, where its foot showed in a strip under the sidebar's (18 October, the shots). The map's place
   is read only while a sidebar is open, so a frame with none reads no layout (18 October, later). */
function thMapCovered() {
  const open = ['th-side', 'th-cpanel'].map((id) => $(id)).filter((el) => el && !el.hidden);
  if (!open.length) return false;
  const map = $('th-map').getBoundingClientRect();
  return open.some((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.left < map.right && r.right > map.left && r.top < map.bottom && r.bottom > map.top;
  });
}

/* whether the map shows: wanted, not given way to a sidebar, and with something to draw once drawn */
const thMapShown = () => thMapWanted() && !thMapCovered();

let thMapFrame = 0;
function thMapSchedule() {
  if (thMapFrame) return;
  thMapFrame = requestAnimationFrame(() => { thMapFrame = 0; thMapDraw(); });
}

/* A pan or a zoom, from thView: the box follows on the next frame, and in Auto the map wakes. A page
   without the map, a test's stand-in among them, has nothing to draw. */
function thMapViewed() {
  if (!$('th-map')) return;
  if (TH.live) thMapWake();
  thMapSchedule();
}

/* a move on the board, from thPlace: the marks are drawn again on the next frame */
function thMapMoved() {
  if (!$('th-map')) return;
  TH.mapStale = true;
  thMapSchedule();
}

/* A new choice of Auto, On or Off, from Settings: what his button or M said goes with it, a new Auto
   shows the map at once so he sees it and then lets it sleep, as the transcript's does, and the zoom bar
   is measured again where its button comes or goes. */
function thMapChosen() {
  const mode = thMapMode();
  const stage = thStage();
  const off = mode === 'off';
  const was = TH.mapMode;
  TH.mapMode = mode;
  if (was && was !== mode) {
    TH.mapHand = '';
    TH.mapAwake = mode === 'auto';
    thMapRest();
  }
  if (stage.classList.contains('th-map-off') !== off) {
    stage.classList.toggle('th-map-off', off);
    thCorners();
    thMapPlace();
  }
}

/* The map drawn as it stands, once a frame at most: shown or faded, what it draws listed and fitted
   again when the board has moved or the card has changed its size, and its box. While it does not show
   nothing is read. While a drag runs it reads no layout, its size, its fit and the view's box kept as the
   drag found them, and moves only the marks that moved (see thMapPatch), and after the drop it is listed
   and fitted again and drawn whole. */
function thMapDraw() {
  const map = $('th-map');
  if (!map) return;
  if (TH.live) thMapChosen();
  let shown = thMapShown();
  if (shown) {
    const area = $('th-map-area');
    const held = !!(TH.drag && TH.mapBoard && TH.mapDrawn);
    const w = held ? TH.mapBoard.w : area.clientWidth;
    const h = held ? TH.mapBoard.h : area.clientHeight;
    if (TH.mapStale || !TH.mapBoard || TH.mapBoard.w !== w || TH.mapBoard.h !== h) {
      const v = (TH.drag && TH.drag.seen) || TH.v;
      const items = thMapItems(v, TH.layout, thSize, TH.mode === 'gets' ? (c) => gtLook(c.case).colour : null);
      TH.mapItems = items;
      if (!(held && thMapPatch(items))) {
        TH.mapBoard = thMapFit(items.all, w, h);
        TH.mapDrawn = null;
        TH.mapViewAt = '';
      }
      TH.mapStale = false;
      if (!TH.mapBoard) { TH.map = null; TH.mapMarks = []; $('th-map-items').innerHTML = ''; }
    }
    shown = !!TH.mapBoard;
  } else {
    TH.map = null;
    TH.mapBoard = null;
    TH.mapDrawn = null;
    TH.mapStale = true;
    TH.mapMarks = [];
  }
  map.classList.toggle('shut', !shown);
  $('th-map-btn').setAttribute('aria-pressed', String(shown));
  if (shown) thMapViewDraw();
}

/* The view's box on the map, set again on every pan and zoom, with the fit thMapAround gives, the marks
   drawn again only when that fit has changed: a pan alone leaves them, and while the view holds the
   whole map they follow it. A drag on the map keeps the fit it started at, so the place under the
   pointer stays under it, and the fit comes back as it ends. While a card is dragged the box is left as
   it is, since that drag moves no view, and nothing is read. */
function thMapViewDraw() {
  const el = $('th-map-view');
  const at = `${TH.view.x},${TH.view.y},${TH.view.z}`;
  if (TH.drag && TH.mapDrawn && TH.mapViewAt === at) return;
  TH.mapViewAt = at;
  const stage = thStage();
  const seen = thMapSeen(TH.view, stage.clientWidth, stage.clientHeight);
  const fit = TH.mapDrag && TH.map ? TH.map : thMapAround(TH.mapBoard, TH.mapItems ? TH.mapItems.all : [], seen);
  if (fit && !thMapSame(fit, TH.mapDrawn)) {
    const holder = $('th-map-items');
    holder.innerHTML = thMapHtml(TH.mapItems, fit);
    const els = holder.children || [];
    TH.mapMarks = TH.mapItems.all.map((b, i) => ({ id: b.id, cls: b.cls, style: thMapStyle(fit, b), el: els[i] || null }));
    TH.mapDrawn = fit;
  }
  TH.map = fit;
  const box = fit ? thMapBox(fit, seen) : null;
  TH.mapBox = box;
  el.hidden = !box;
  if (!box) return;
  el.style.left = mmPx(box.x);
  el.style.top = mmPx(box.y);
  el.style.width = mmPx(box.w);
  el.style.height = mmPx(box.h);
}

/* The map's width, the zoom bar's, set on the canvas whenever the bar may have changed its width: as
   the canvas narrows or widens, and as the bar gains or loses the map's button. Its height above the bar
   is the bar's own, which thCorners measures. With the status bar along the foot, the width of its tools,
   from the pointer to Shortcuts, so the map stands over them as it stood over the zoom bar. */
function thMapPlace() {
  const stage = thStage();
  const bar = stage && stage.querySelector('.th-zoomer');
  if (!bar || !$('th-map') || !stage.clientWidth) return;
  const first = $('th-mode-pointer');
  const tools = stage.classList.contains('th-status-on') && first && first.offsetParent
    ? Math.round(bar.getBoundingClientRect().right - first.getBoundingClientRect().left) - 12 : bar.offsetWidth;
  stage.style.setProperty('--th-map-w', `${Math.max(200, tools)}px`);
  thMapSchedule();
}

/* In Auto the map wakes on a pan or a zoom and sleeps MINIMAP_AWAKE after the last of them, the time
   starting again once the pointer leaves it or a drag on it ends, so it never goes from under his hand.
   With On or Off there is nothing to wake. */
let thMapSleep = 0;
function thMapWake() {
  if (thMapMode() !== 'auto') return;
  const was = !!TH.mapAwake;
  TH.mapAwake = true;
  thMapRest();
  if (!was) thMapSchedule();
}

function thMapRest() {
  clearTimeout(thMapSleep);
  if (!TH.mapAwake || TH.mapOver || TH.mapDrag) return;
  thMapSleep = setTimeout(() => {
    if (TH.mapOver || TH.mapDrag) return;
    TH.mapAwake = false;
    thMapSchedule();
  }, MINIMAP_AWAKE);
}

function thMapLeave() {
  TH.mapOver = false;
  thMapRest();
}

/* The button and M: while the map shows, they hide it, in Auto until the next pan or zoom and with On
   until pressed again, and while it does not, they show it until pressed again. With Off, at
   TH_MAP.narrow and below, and before a board is on the canvas they do nothing. */
function thMapToggle() {
  const mode = thMapMode();
  if (!TH.live || mode === 'off' || thMapNarrow()) return;
  if (thMapShown()) {
    TH.mapHand = mode === 'on' ? 'hide' : '';
    TH.mapAwake = false;
    clearTimeout(thMapSleep);
  } else {
    TH.mapHand = mode === 'on' ? '' : 'show';
  }
  thMapSchedule();
}

/* The view glides so the top left of what it shows is `x`, `y` on the board, its zoom kept, over
   TH_MAP.glide, at once under reduced motion, and any other move of the view on the way, a pan, a
   zoom or a drag on the map, ends the glide where it stands. */
let thMapGlideFrame = 0;
function thMapGlide(x, y) {
  cancelAnimationFrame(thMapGlideFrame);
  thMapGlideFrame = 0;
  const to = { x: -x * TH.view.z, y: -y * TH.view.z };
  if (thCalm()) { TH.view.x = to.x; TH.view.y = to.y; thView(); return; }
  const from = { x: TH.view.x, y: TH.view.y };
  let last = { x: from.x, y: from.y };
  let t0 = 0;
  const step = (now) => {
    thMapGlideFrame = 0;
    if (TH.view.x !== last.x || TH.view.y !== last.y) return;
    if (!t0) t0 = now;
    const t = Math.min(1, (now - t0) / TH_MAP.glide);
    const e = 1 - (1 - t) ** 3;
    TH.view.x = from.x + (to.x - from.x) * e;
    TH.view.y = from.y + (to.y - from.y) * e;
    last = { x: TH.view.x, y: TH.view.y };
    thView();
    if (t < 1) thMapGlideFrame = requestAnimationFrame(step);
  };
  thMapGlideFrame = requestAnimationFrame(step);
}

/* a pointer as a place in the map's area */
function thMapPoint(e) {
  const r = $('th-map-area').getBoundingClientRect();
  return { x: e.clientX - r.left, y: e.clientY - r.top };
}

/* A press on the map: on the view's box it takes the box where the pointer goes, from the first move,
   and anywhere else the view glides so the place pressed comes to the middle of the canvas, a drag
   carrying on from there. A press a pixel or two off its place is still a click. */
function thMapDown(e) {
  const fit = TH.map;
  if (e.button !== 0 || !fit || !TH.live) return;
  e.preventDefault();
  const p = thMapPoint(e);
  const stage = thStage();
  const seen = thMapSeen(TH.view, stage.clientWidth, stage.clientHeight);
  const at = thMapToBoard(fit, p.x, p.y);
  const box = TH.mapBox;
  const onBox = !!box && p.x >= box.x - 1 && p.x <= box.x + box.w + 1 && p.y >= box.y - 1 && p.y <= box.y + box.h + 1;
  const grab = onBox ? { x: at.x - seen.x, y: at.y - seen.y } : { x: seen.w / 2, y: seen.h / 2 };
  TH.mapDrag = { grab, x: e.clientX, y: e.clientY, moved: onBox };
  clearTimeout(thMapSleep);
  if (!onBox) thMapGlide(at.x - grab.x, at.y - grab.y);
  const area = $('th-map-area');
  try { area.setPointerCapture(e.pointerId); } catch { /* a nicety */ }
  area.classList.add('dragging');
}

function thMapMove(e) {
  const d = TH.mapDrag;
  if (!d || !TH.map) return;
  if (!d.moved && Math.abs(e.clientX - d.x) < 4 && Math.abs(e.clientY - d.y) < 4) return;
  d.moved = true;
  cancelAnimationFrame(thMapGlideFrame);
  thMapGlideFrame = 0;
  const p = thMapPoint(e);
  const at = thMapToBoard(TH.map, p.x, p.y);
  TH.view.x = -(at.x - d.grab.x) * TH.view.z;
  TH.view.y = -(at.y - d.grab.y) * TH.view.z;
  thView();
}

function thMapUp(e) {
  if (!TH.mapDrag) return;
  TH.mapDrag = null;
  const area = $('th-map-area');
  try { area.releasePointerCapture(e.pointerId); } catch { /* already gone */ }
  area.classList.remove('dragging');
  thMapRest();
  // the fit the drag held comes back to the board's, or the board's and the view's
  thMapSchedule();
}

/* ── selection ── */

function thClearSel() {
  TH.sel.cards.clear();
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  if (TH.v) thDrawSel();
}

const thItemOf = (el) => (el.dataset.key !== undefined ? { kind: 'card', id: el.dataset.key }
  : el.dataset.sticky !== undefined ? { kind: 'sticky', id: el.dataset.sticky } : { kind: 'group', id: el.dataset.group });
const thSetOf = (item) => (item.kind === 'card' ? TH.sel.cards : item.kind === 'sticky' ? TH.sel.stickies : TH.sel.groups);
const thSelected = (item) => thSetOf(item).has(item.id);

function thSelectOnly(item) {
  TH.sel.cards.clear();
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  thSetOf(item).add(item.id);
  thDrawSel();
}

function thToggle(item) {
  const set = thSetOf(item);
  if (set.has(item.id)) set.delete(item.id); else set.add(item.id);
  thDrawSel();
}

/* drops anything the board no longer has, after an undo or a delete */
function thPruneSel() {
  // a statement in a stack shown open stays selected, as any card does
  for (const key of [...TH.sel.cards]) if (!thOnCanvas(TH.v, key) && !thUnderShown(TH.v, key)) TH.sel.cards.delete(key);
  for (const id of [...TH.sel.groups]) if (!thIsGroup(TH.v, id)) TH.sel.groups.delete(id);
  for (const id of [...TH.sel.stickies]) if (!thIsSticky(TH.v, id)) TH.sel.stickies.delete(id);
}

/* ── acts, undo and saving ── */

/* a card he moves or acts on takes the line as it reads now, and its changed mark goes */
function thAck(keys) {
  for (const key of keys) {
    const c = TH.v.cards[key];
    if (c && c.changed && !c.missing) { c.changed = false; delete c.stored; }
  }
}

/* One act done: drawn, settled so nothing overlaps, then one step of undo holding where everything
   ended up, so undo puts back where it all was before. `opts.settle` is what the act moved, the
   block that shifts clear when it lands on something, `opts.was` the labels and frames before the
   act when the canvas has drawn since, and `opts.labels` a theme made, renamed or arranged, which
   stays where it is and sends clear what its frame reaches (see thSettle). Whatever the act moved
   eases from where it stood, `opts.from` when the act has moved things already, and what was
   lifted, `opts.lifted`, settles back to its own size and stands up from the lean it was let go
   with, `opts.lean`. A drag's drop passes `opts.stay`: what it moved lands where it was let go and
   leads. The save goes at once all the same. */
function thDone(before, what, opts = {}) {
  if (thLocked(TH.v)) return;
  const was = opts.was || thLabelBoxes(TH.layout);
  const from = opts.from || thSpots(TH.v);
  thPrunePicks(TH.v);
  thPruneSel();
  thRender();
  // with room in the view the settle is weighed where the file keeps the board, against the labels before the act
  if (opts.settle && (thRoomOn()
    ? thInFile(() => thSettle(TH.v, thBaseSize, opts.settle, thFileBoxes(before), opts.labels, TH_PASSES, !!opts.stay))
    : thSettle(TH.v, thSize, opts.settle, was, opts.labels, TH_PASSES, !!opts.stay))) thPlace();
  thEase(from, opts.lifted, opts.lean);
  thStep(before, what, opts.note);
  thSoon();
  thMomentum(before);
}

/* The statements left (item 160). An act that takes statements out of Unplaced, into a PET or a
   sub-theme or onto the pile, raises the count of those left over the middle of the canvas, "4
   left", the turn screen's count in the same face and the same 850ms. The act that places the last
   one fires the third level of confetti, the case's, with one line in the count's place, "Every
   statement placed.". It compares Unplaced before the act and after it, so an act that leaves it
   as it was raises nothing, and undo and redo never come through here, so a statement brought back
   raises nothing either. Nothing is written. It takes no pointer and no focus, the Celebrations
   switch silences it, and under reduced motion the count does not show. */
function thMomentum(before) {
  if (!before || !TH.v) return;
  // on the GETs screen what is left is the PETs and sub-themes under no GET
  const unplaced = TH.mode === 'gets' ? gtLeft : (v) => thCounts(v).unplaced;
  const was = unplaced(before);
  const left = unplaced(TH.v);
  if (!(left < was)) return;
  // on GETs a PET binned is not a PET placed, so an act that only bins raises nothing (20 October)
  if (TH.mode === 'gets' && !(gtTally(TH.v).placed > gtTally(before).placed)) return;
  thFlash(left);
  if (left === 0) confetti(3);
}

function thFlash(left) {
  if (!cheerOn() || thCalm()) return;
  const flash = $('th-flash');
  const last = left === 0;
  flash.innerHTML = last ? (TH.mode === 'gets' ? t('themes.flash.every_pet') : t('themes.flash.every_statement')) : t('themes.flash.left_html', { n: left });
  flash.classList.toggle('line', last);
  // taken off and put back, so a count still showing starts again from the top
  flash.classList.remove('on');
  void flash.offsetWidth;
  flash.classList.add('on');
}

/* One step on the undo stack, holding the board before an act and after it, and for a theme's note
   the label it is on, whose panel shows it when the step is undone or done again. */
function thStep(before, what, note) {
  TH.undo.push(Object.assign({ before, after: thSnap(TH.v, TH.removed), what }, note ? { note } : {}));
  if (TH.undo.length > TH_UNDO_DEPTH) TH.undo.shift();
  TH.redo.length = 0;
  TH.worked = true;
}

function thUndo(backwards) {
  if (!TH.live || TH.editing || TH.cardEdit || TH.writing || TH.drag || TH.busy) return;
  if (thRefuse('undo')) return;
  const stack = backwards ? TH.undo : TH.redo;
  if (!stack.length) { say(backwards ? t('themes.undo.nothing') : t('themes.undo.nothing_redo'), 2000); return; }
  // a statement edited in place goes back through the workbook, not the board
  if (stack[stack.length - 1].edit) { thStatementStep(stack[stack.length - 1], backwards); return; }
  const entry = stack.pop();
  const from = thSpots(TH.v);
  TH.removed = thPut(TH.v, backwards ? entry.before : entry.after);
  (backwards ? TH.redo : TH.undo).push(entry);
  TH.worked = true;
  thPruneSel();
  // a note undone or done again shows in the Inspector, open on its label, the text it now has in
  // the box
  const noted = entry.note && thIsGroup(TH.v, entry.note) ? entry.note : null;
  if (noted) { thSelectOnly({ kind: 'group', id: noted }); TH.lastPick = { kind: 'group', id: noted }; }
  thRender();
  thEase(from);
  if (noted) thInspectorOpen({ kind: 'group', id: noted });
  thSoon();
}

/* ── motion ── */

/* Weight, in the register of the Finder and the iOS home screen, clearly there and never bouncy or
   slow, and all of it off when the system asks for reduced motion. Everything goes through CSS
   transforms: nothing here reads the layout between writes, and nothing waits on it, a save least
   of all. What is picked up lifts by TH_LIFT, and leans up to TH_LEAN degrees at full speed. */
const TH_LIFT = 1.04;
const TH_LEAN = 6;
const thCalm = () => !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

/* What an act moved eases from where it stood to where it rests with a visible overshoot. What was
   dropped lands over about 220 ms, coming down to its own size and standing up from the lean it
   was let go with, and what moved without being held, a card nudged clear by the margin, the cards
   an Auto-arrange gathers, a step undone, slides there over about 240 ms, and so does what was
   dropped and then sent clear, a card or a PET, while it lands. Either way it has settled inside
   250 ms. */
function thEase(from, lifted, lean = 0) {
  if (!from || !TH.v || thCalm()) return;
  const moves = [];
  const add = (el, was, now, id) => {
    if (!el || !was || !now) return;
    const dx = was.x - now.x;
    const dy = was.y - now.y;
    const lift = !!(lifted && lifted.has(id));
    const still = Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5;
    if (still && !lift) return;
    moves.push({ el, dx, dy, lift, sent: lift && !still });
  };
  for (const [key, el] of Object.entries(TH.els.cards)) add(el, from.cards[key], TH.v.cards[key], key);
  for (const g of TH.v.groups) add(TH.els.labels[g.id], from.groups[g.id], g, g.id);
  for (const n of thStickies(TH.v)) add((TH.els.stickies || {})[n.id], (from.stickies || {})[n.id], n, n.id);
  if (!moves.length) return;
  const tilt = Math.abs(lean) > 0.05 ? `${lean.toFixed(2)}deg` : '';
  for (const m of moves) {
    m.el.classList.add('ease-from');
    m.el.style.translate = `${m.dx}px ${m.dy}px`;
    if (m.lift) {
      m.el.classList.add('landing');
      m.el.style.scale = String(TH_LIFT);
      m.el.style.rotate = tilt;
    }
  }
  // two frames, so the starting place is drawn before the move to the resting one begins. A drag
  // picked up in between owns the translate and the lean from then on, so it is left alone
  requestAnimationFrame(() => requestAnimationFrame(() => {
    for (const m of moves) {
      m.el.classList.remove('ease-from', 'landing');
      m.el.style.scale = '';
      if (m.el.classList.contains('dragging')) continue;
      m.el.classList.add(m.lift ? 'easing' : 'nudging');
      if (m.sent) m.el.classList.add('sent');
      m.el.style.translate = '';
      m.el.style.rotate = '';
    }
    setTimeout(() => { for (const m of moves) m.el.classList.remove('easing', 'nudging', 'sent'); }, 300);
  }));
}

/* While a drag runs, everything that moves leans into the way it travels, up to TH_LEAN degrees at
   full speed, a step each frame, and stands upright again once the pointer stops, over the 160 ms of
   `.standing`, which the next move takes away. A card on its way out of a sidebar, `TH.spull` or
   `TH.pull` with its cards in `els`, leans the same way (Adam, 21 October). */
function thLean(e, d = TH.drag) {
  if (!d || thCalm()) return;
  const vx = e.clientX - d.lastX;
  d.lastX = e.clientX;
  d.lean = Math.max(-TH_LEAN, Math.min(TH_LEAN, d.lean * 0.5 + vx * 0.5));
  if (d.standing) thStand(d, false);
  thTilt(d, d.lean);
  clearTimeout(d.still);
  d.still = setTimeout(() => {
    if (TH.drag === d || TH.spull === d || TH.pull === d) { d.lean = 0; thStand(d, true); thTilt(d, 0); }
  }, 90);
}

/* what moves eases as it stands up, and leans again with no ease of its own */
function thStand(d, on) {
  d.standing = on;
  if (d.els) { for (const el of d.els) el.classList.toggle('standing', on); return; }
  for (const it of d.moving) {
    const el = TH.els.cards[it] || TH.els.labels[it] || TH.els.stickies[it];
    if (el) el.classList.toggle('standing', on);
  }
}

/* The same lean on everything that moves: the card or the label picked up, and every card and
   label it carries, each one leaning the same way about its own middle, so a theme dragged by its
   label or its frame tilts as one body. */
function thTilt(d, deg) {
  const turn = Math.abs(deg) > 0.05 ? `${deg.toFixed(2)}deg` : '';
  if (d.els) { for (const el of d.els) el.style.rotate = turn; return; }
  for (const it of d.moving) {
    const el = TH.els.cards[it] || TH.els.labels[it] || TH.els.stickies[it];
    if (el) el.style.rotate = turn;
  }
}

/* A card dragged out of a sidebar (Adam, 21 October: "The sidebar should match the canvas"). Where the
   i-th of n cards carried lies against the pointer, in the canvas's units: the one picked up a little
   below and to the right of the pointer's tip, and several in the rows a drop lays them out in. */
const TH_PULL = { x: 20, y: 14 };
function thPullSpot(i, n) {
  const cols = Math.max(1, Math.ceil(Math.sqrt(n)));
  return { x: -TH_PULL.x + (i % cols) * (TH_CARD.w + TH_MARGIN), y: -TH_PULL.y + Math.floor(i / cols) * (TH_CARD.h + TH_MARGIN) };
}

/* The cards on their way, drawn as canvas cards at the canvas's zoom in a layer of their own over
   the sidebar and the canvas alike, that follows the pointer. They lift as a card picked up on the
   canvas does, a frame after they show, and lean with `thLean`. `p` is the pull, which keeps them. */
function thPullLift(p, cards, e) {
  const layer = document.createElement('div');
  layer.className = 'th-pull';
  cards.forEach((el, i) => {
    const at = thPullSpot(i, cards.length);
    el.style.left = `${at.x}px`;
    el.style.top = `${at.y}px`;
    // the one picked up drawn over the rest, so its count shows whole
    layer.prepend(el);
  });
  document.body.appendChild(layer);
  Object.assign(p, { ghost: layer, els: cards, lean: 0, lastX: e.clientX, still: null, standing: false });
  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (p.ghost === layer) for (const el of cards) el.classList.add('dragging');
  }));
}

function thPullFollow(p, e) {
  p.ghost.style.transform = `translate(${e.clientX}px, ${e.clientY}px) scale(${TH.view.z})`;
  thLean(e, p);
}

/* the cards on their way gone, at the drop or with Esc */
function thPullGone(p) {
  clearTimeout(p.still);
  p.ghost.remove();
  p.ghost = null;
}

/* The tip that follows a member dragged, a card in a theme or a sub-theme: what Alt, Option on a
   Mac, does at the drop, and with it held what letting go does, naming what holds it, a PET or a
   sub-theme, the way Take out of PET and Take out of sub-theme do. */
const thTipText = (alt, mac, unit = t('themes.unit.pet')) => (alt ? t('themes.drag.release', { unit })
  : t('themes.drag.hold', { key: mac ? '⌥' : t('themes.key.alt'), unit }));

/* What holds what the tip is about: the card or the sub-theme picked up when Alt takes it out, or
   else the first of what Alt takes out, a PET or a sub-theme. */
function thTipUnit(v, moving, picked) {
  const leavers = [...thLeavers(v, moving)];
  if (!leavers.length) return 'PET';
  const parents = thParents(v);
  const it = picked && leavers.includes(picked) ? picked : leavers[0];
  return thUnit(v, parents[it], parents);
}

/* Drawn a little below and to the right of the pointer, and only while Alt at the drop takes
   something dragged out of its theme, so never for a card in no theme, a theme dragged by its own
   label or a drag over a card's middle, where the drop stacks. It is the page's alone: nothing about
   it is saved. */
function thTip(e) {
  const tip = $('th-tip');
  if (!tip) return;
  const d = TH.drag;
  if (d && e) { d.tipX = e.clientX; d.tipY = e.clientY; }
  // over a card's middle a drop stacks, with no key, so the tip about Alt goes while it is there
  if (!d || !d.tip || TH.stackAt) { tip.hidden = true; return; }
  const text = thTipText(d.alt, MAC, d.tipUnit);
  if (tip.textContent !== text || tip.hidden) {
    tip.textContent = text;
    tip.classList.toggle('alt', !!d.alt);
    tip.hidden = false;
    d.tipW = tip.offsetWidth;
  }
  tip.style.left = `${Math.max(8, Math.min(d.tipX + 16, window.innerWidth - (d.tipW || 0) - 8))}px`;
  tip.style.top = `${Math.min(d.tipY + 20, window.innerHeight - 30)}px`;
}

const TH_SAVED = t('themes.save.saved');

/* Beside the board's name: Auto-saved whenever the canvas is what the file holds, Saving while a
   save runs, and a line saying why when one fails. The class is `done`, not `saved`, which the turn
   screen's own save mark uses and keeps out of sight until it fades in. */
function thSaveLine(kind, text) {
  const el = $('th-save');
  el.className = `th-save${kind ? ` ${kind}` : ''}`;
  el.textContent = text;
  el.hidden = !text;
  // a narrow bar shows the mark alone, so the words are in the tooltip too
  el.title = kind === 'failed' ? text : kind ? t('themes.save.tip', { said: text.replace(/^✓ /, '') }) : '';
  // the line's width is the bar's, so the counts fit again (see thCountFit)
  thCountFit();
}

/* Every act writes the whole board, about 300 ms after the last one, one save at a time. A save
   the revision timer has asked for carries `revision: 'auto'`, and the server keeps the board as
   the file held it in its history on the way, when it differs from the last revision. */
function thSoon() {
  TH.dirty = true;
  clearTimeout(TH.saveTimer);
  TH.saveTimer = setTimeout(() => { TH.saveTimer = null; thSave(); }, 300);
}

async function thSaveOnce() {
  const v = thLiveV();
  if (!v || !TH.path) return;
  // a drag under way holds a preview of the canvas, never the board, so its save waits for the drop
  if (TH.drag) { TH.dirty = true; return; }
  // a save refused since the board changed under the page waits for Reload or Overwrite
  if (TH.stale) { TH.dirty = true; return; }
  const path = TH.path;
  const body = { workbook: path, version: thBody(v, TH.meta) };
  const due = TH.revDue;
  if (due) body.revision = 'auto';
  TH.dirty = false;
  thSaveLine('saving', t('themes.save.saving'));
  try {
    const data = TH.mode === 'gets' ? await api('/api/gets-save', body) : await api('/api/themes-save', body);
    if (due && TH.path === path) TH.revDue = false;
    // a reviewer's first board of a participant someone else works on comes back with an id of his own
    // (ownboards), which the page takes at once so the next save names it
    if (TH.mode !== 'gets' && data.version && data.version.id && TH.meta && TH.path === path
      && TH.meta.id === body.version.id && data.version.id !== TH.meta.id) thTakeOwnId(TH.meta.id, data.version.id);
    if (data.updated && TH.meta && TH.path === path) TH.meta.updated = data.updated;
    // and the version it wrote, which the next save carries
    if (data.version && data.version.v && TH.meta && TH.path === path && data.version.id === TH.meta.id) TH.meta.v = data.version.v;
    // its own save is never a change made outside
    if (data.updated && TH.meta && TH.path === path) TH.known[TH.meta.id] = data.updated;
    // an agent's board he has now changed says so in the board menu at once
    if (data.version && TH.path === path) {
      const listed = TH.boards.find((b) => b.id === data.version.id);
      if (listed && data.version.with_ai) listed.with_ai = data.version.with_ai;
    }
    // an automatic revision made on the way comes back with the history, for the tab
    if (Array.isArray(data.history) && TH.path === path && data.version && data.version.id === TH.meta.id) {
      TH.history = data.history;
      if (TH.boardOpen && TH.tab === 'history') thBoardDraw();
    }
    if (TH.path === path && !TH.dirty) thSaveLine('done', TH_SAVED);
    // a save that goes through after Reload puts the card away, his canvas still in History
    if (TH.staleKept && TH.path === path) thStaleHide();
  } catch (err) {
    TH.dirty = true;
    // the board changed since the page read it, in another window or by an agent: nothing was saved,
    // and the card in the corner offers Reload and Overwrite
    if (err.data && err.data.stale && TH.path === path && TH.meta && err.data.stale.board === TH.meta.id) {
      thSaveLine('failed', t('themes.save.not_saved'));
      thStaleShow(err.data.stale);
      return;
    }
    thSaveLine('failed', t('themes.save.not_saved_why', { why: needsRestart(err) ? RESTART_LINE : err.message }));
    // a board changed in a conversation since the page last saw it: the corner says so at once
    if (refusedAs(err, 'board_changed_outside')) thStampTick(true);
  }
}

/* the board on the canvas renamed `was` to `now` by the server, everywhere the page holds its id: his own board
   (ownboards, themes.write_own) */
function thTakeOwnId(was, now) {
  TH.meta.id = now;
  TH.meta.own = true;
  for (const b of TH.boards || []) if (b.id === was) Object.assign(b, { id: now, own: true });
  if (was in TH.known) { TH.known[now] = TH.known[was]; delete TH.known[was]; }
  if (TH.done && TH.done.board === was) TH.done.board = now;
}

/* one save at a time: an act made while one is on its way is written by the next */
function thSave() {
  if (TH.chain) { TH.again = true; return TH.chain; }
  TH.chain = (async () => {
    do {
      TH.again = false;
      await thSaveOnce();
    } while (TH.again);
  })().finally(() => { TH.chain = null; });
  return TH.chain;
}

/* The revision timer, once a minute: fifteen minutes after the last automatic revision, with an
   act since, the next save asks for another, and with no act waiting a save goes now, so a pause
   in the work still keeps it. A revision on view pauses it. */
function thRevisionTick() {
  if (!TH.live || TH.viewing || !TH.v || $('themes').hidden) return;
  if (!thRevisionDue(Date.now(), TH.revAt, TH.worked)) return;
  TH.revAt = Date.now();
  TH.worked = false;
  TH.revDue = true;
  if (!TH.saveTimer && !TH.chain) { TH.dirty = true; thSave(); }
}

/* the way out waits for whatever is still to be written, and tries once more what failed */
async function thFlush() {
  if (TH.saveTimer) { clearTimeout(TH.saveTimer); TH.saveTimer = null; }
  if (TH.chain) await TH.chain;
  if (TH.dirty) await thSave();
}

/* ── the keys' acts ── */

function thGroupKey() {
  if (thRefuse('group')) return;
  const v = TH.v;
  const items = [...TH.sel.groups].filter((id) => thIsGroup(v, id))
    .concat([...TH.sel.cards].filter((key) => thOnCanvas(v, key)));
  // with nothing selected, a new empty PET, or GET, to fill (Adam, 20 October): at the end of the table,
  // or on the canvas in the middle of what is in view
  if (!items.length && !TH.sel.cards.size && !TH.sel.groups.size && !TH.sel.stickies.size) { thNewEmpty(null); return; }
  if (!items.length) { say(t('themes.group.select_first')); return; }
  // the sticky notes selected come along inside the new PET, all but those a label selected holds
  const parents = thParents(v);
  const notes = [...TH.sel.stickies].filter((n) => thIsSticky(v, n)
    && !thAncestors(v, n, parents).some((a) => items.includes(a)));
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  thAck([...TH.sel.cards]);
  const id = thMakeGroup(v, items, '');
  if (!id) return;
  thStickiesJoin(v, notes, id);
  TH.sel.cards.clear();
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  TH.sel.groups.add(id);
  // an open Inspector goes over to the new label
  TH.lastPick = { kind: 'group', id };
  if (TH.panelOpen) TH.panel = { kind: 'group', id };
  thRender();
  thTitleOpen(id, { before, fresh: true, was });
}

/* Where a new empty label goes. Inside a label it goes under what that label holds, so it reads last
   there. At the top with the table showing it goes below everything on the board, so it is the last PET,
   and on the canvas in the middle of what is in view. */
function thEmptyAt(v, inside) {
  const layout = TH.layout || {};
  if (inside) {
    const l = layout[inside];
    if (l && l.body) return { x: l.body.x, y: l.body.y + l.body.h + TH_MARGIN };
    if (l) return { x: l.label.x + TH_FRAME_X, y: l.label.y + l.label.h + TH_GAP };
    return { x: 0, y: 0 };
  }
  if (TH.face !== 'table' && thStage()) {
    const r = thStage().getBoundingClientRect();
    if (r.width) return thToWorld(r.left + r.width / 2, r.top + r.height / 3);
  }
  const parents = thParents(v);
  let foot = 0;
  let left = Infinity;
  for (const g of v.groups) {
    const l = layout[g.id];
    if (!l) continue;
    foot = Math.max(foot, l.frame.y + l.frame.h);
    if (parents[g.id] === undefined) left = Math.min(left, l.frame.x);
  }
  for (const key of Object.keys(v.cards)) {
    if (!thOnCanvas(v, key)) continue;
    const s = (TH.sizes || {})[key] || TH_CARD;
    foot = Math.max(foot, v.cards[key].y + s.h);
  }
  for (const n of thStickies(v)) foot = Math.max(foot, n.y + ((TH.sizes || {})[n.id] || TH_CARD).h);
  return { x: Number.isFinite(left) ? left : 0, y: foot + 4 * TH_MARGIN };
}

/* G with nothing selected, a new empty PET, or GET, and New group inside on a label's menu, a sub-theme
   inside a PET or a group inside a sub-theme: the label made empty, selected, and its title box open, its
   making and its title one step of undo, Made a theme, as G over a selection is. Statements are then
   dragged into it. */
function thNewEmpty(inside) {
  if (!TH.live || TH.busy || !TH.v || thRefuse('group')) return null;
  const v = TH.v;
  if (inside && !thIsGroup(v, inside)) return null;
  const before = thSnap(v, TH.removed);
  const was = thFileBoxes();
  const at = thEmptyAt(v, inside);
  const id = thMakeEmpty(v, inside, at.x, at.y);
  if (!id) return null;
  TH.sel.cards.clear();
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  TH.sel.groups.add(id);
  TH.lastPick = { kind: 'group', id };
  if (TH.panelOpen) TH.panel = { kind: 'group', id };
  thRender();
  if (thInFile(() => thSettle(v, thSize, [], was, [id], TH_PASSES, false))) thPlace();
  thTitleOpen(id, { before, fresh: true, was });
  return id;
}

function thDiscardKey() {
  if (thRefuse('discard')) return;
  const keys = [...TH.sel.cards].filter((key) => thOnCanvas(TH.v, key));
  if (!keys.length) { say(t('themes.aside.select_first')); return; }
  const before = thSnap(TH.v, TH.removed);
  thAck(keys);
  thDiscard(TH.v, keys);
  thDone(before, t('themes.step.set_aside', { n: keys.length }));
  thSideFlash(keys, 'aside');
}

function thDeleteLabels(ids) {
  if (thRefuse('delete')) return;
  const live = ids.filter((id) => thIsGroup(TH.v, id));
  if (!live.length) return;
  const before = thSnap(TH.v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  for (const id of live) thDelete(TH.v, id);
  thDone(before, t('themes.step.deleted_labels', { n: live.length }), { settle: [], was });
}

/* Auto-arrange, from the control on a label, its menu or the panel: the theme's cards tidied under
   its label in the order they read now. One step of undo. The theme stays where its label is, and a
   neighbour its new frame reaches shifts clear of it, as a theme that grows sends one clear. */
function thArrangeGroup(gid, way = thArrangeWay()) {
  if (!TH.live || TH.busy || !thIsGroup(TH.v, gid) || thRefuse('arrange')) return;
  const v = TH.v;
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  const from = thSpots(v);
  if (!thArrange(v, gid, thSize, way)) { say(t('themes.arrange.nothing_under')); return; }
  thAck(thCardsUnder(v, gid));
  thDone(before, t('themes.step.arranged', { label: thGroup(v, gid).label }), { settle: [], was, from, labels: [gid] });
}

/* A card thrown away from its menu, as x does for the selection. */
function thDiscardOne(key) {
  if (!TH.live || TH.busy || !thOnCanvas(TH.v, key) || thRefuse('discard')) return;
  const before = thSnap(TH.v, TH.removed);
  thAck([key]);
  thDiscard(TH.v, [key]);
  TH.sel.cards.delete(key);
  thDone(before, t('themes.step.set_aside', { n: 1 }));
  thSideFlash([key], 'aside');
}

/* Taking cards out of their theme, and a sub-theme out of the theme it sits in, is an act of its own:
   what leaves stays where it stands and loses the tint. One step of undo. */
function thLeaveThemes(ids) {
  if (thRefuse('leave')) return false;
  const v = TH.v;
  const parents = thParents(v);
  const live = ids.filter((id) => thHere(v, id) && parents[id] !== undefined);
  if (!live.length) return false;
  // on the PETs board a statement taken out goes back to Not placed in the sidebar (20 October)
  if (thWaits(v) && live.every((id) => !!v.cards[id])) return thWaitDo(live);
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  thAck(live.filter((id) => !thIsGroup(v, id)));
  for (const id of live) thLeave(v, id);
  // a statement among a label or a note taken out with it waits in Not placed all the same
  if (thWaits(v)) for (const id of thSendWaiting(v, live.filter((id) => !!v.cards[id]))) TH.sel.cards.delete(id);
  const cards = live.filter((id) => !thIsGroup(v, id)).length;
  const what = live.length > 1 ? t('themes.step.took_out_n', { n: live.length })
    : thIsSticky(v, live[0]) ? t('themes.step.took_note_out')
      : cards ? t('themes.step.took_card_out') : t('themes.step.took_sub_out');
  thDone(before, what, { settle: live, was });
  return true;
}

/* Backspace or Delete: a card selected leaves its theme and stays where it is, a label selected is
   deleted and what it held stays on the canvas. Both at once are one step of undo. */
function thDeleteKey() {
  if (thRefuse('delete')) return;
  const v = TH.v;
  // a sticky note selected leaves its PET as a card does, and stays on the board
  const top = thTop(v, [...TH.sel.groups].filter((id) => thIsGroup(v, id))
    .concat([...TH.sel.cards].filter((key) => thOnCanvas(v, key)))
    .concat([...TH.sel.stickies].filter((id) => thIsSticky(v, id))));
  const parents = thParents(v);
  const labels = top.filter((it) => thIsGroup(v, it));
  // on the PETs board a card loose on the canvas goes back to Not placed too (20 October)
  const cards = top.filter((it) => !thIsGroup(v, it) && (parents[it] !== undefined || (thWaits(v) && !!v.cards[it])));
  if (!labels.length && !cards.length) {
    if (top.length && top.every((it) => thIsSticky(v, it))) say(TH_STICKY_FREE);
    else if (top.length) say(t('themes.aside.in_no_get'));
    return;
  }
  if (!labels.length) {
    if (thWaits(v)) thWaitDo(cards); else thLeaveThemes(cards);
    return;
  }
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  thAck(cards);
  for (const key of cards) thLeave(v, key);
  if (thWaits(v)) for (const key of thSendWaiting(v, cards)) TH.sel.cards.delete(key);
  for (const id of labels) thDelete(v, id);
  thDone(before, cards.length ? t('themes.step.took_out_deleted')
    : t('themes.step.deleted_labels', { n: labels.length }), { settle: cards, was });
}

/* ── a label's title ── */

const TH_TITLE_INSET = 7; // the box's border and left padding, .th-title-edit's 1px and 6px
const TH_TITLE_RIGHT = 3; // and its right, 1px and 2px (.th-title-boxes), so it ends short of the label's icons

/* The box stands where the title stood. Enter keeps what is typed, a blank one as Untitled, and
   Esc leaves the title as it was. A new label's box opens empty and its making and its first
   title are one step of undo. */
function thTitleOpen(id, opts = {}) {
  // with the table showing, the title opens in its row there, G and Rename doing there what they do here
  if (TH.face === 'table') { thTableTitleOpen(id, opts); return; }
  if (thRefuse('rename')) return;
  // a note open in the panel is kept first, since keeping it draws the labels afresh
  thNoteDone(true);
  const el = TH.els.labels[id];
  const g = thGroup(TH.v, id);
  if (!el || !g) return;
  thTitleDone(true);
  // the box keeps the title's own width and wraps as the title wraps, as tall as its words, so a
  // long title is read and edited whole, never squeezed onto one line (186). Its words stand where the
  // title's stood: the box's padding and border lie outside the title's column (.th-title-boxes), so its
  // inside is the column's width, a label run wider for its description included (see thLabelsWiden), and a
  // pixel more, since offsetWidth rounds a column of 187.4px down and the last word would wrap
  const title = el.querySelector('.th-title');
  const column = el.querySelector('.th-words');
  const wide = Math.max(180, column.offsetWidth + 1 + TH_TITLE_INSET + TH_TITLE_RIGHT);
  const input = document.createElement('textarea');
  input.className = 'th-title-edit th-title-box';
  input.rows = 1;
  input.style.width = `${wide}px`;
  input.value = opts.value !== undefined ? opts.value : (opts.fresh ? '' : thLabelShown(g.label));
  input.placeholder = t('themes.table.title_label', { unit: thUnitHead(thUnit(TH.v, id)) });
  input.spellcheck = true;
  input.setAttribute('aria-label', input.placeholder);
  const fit = () => { input.style.height = 'auto'; input.style.height = `${input.scrollHeight + 2}px`; };
  // and its description in a second box under it, "Description" in grey while empty, an empty one no
  // description at all (Adam, 21 October). Enter keeps both and ends the edit in one press, from either box,
  // Tab or Shift + Enter goes from the title to the description, Shift + Tab back (22 October: Enter had gone
  // to the description, so a PET's name was kept only on a second Enter)
  const desc = document.createElement('textarea');
  desc.className = 'th-title-edit th-title-box th-desc-box';
  desc.rows = 1;
  desc.style.width = `${wide}px`;
  desc.value = thDescOf(g);
  desc.placeholder = t('themes.label.description');
  desc.spellcheck = true;
  desc.setAttribute('aria-label', t('themes.label.description'));
  const shown = el.querySelector('.th-desc');
  const fitDesc = () => { desc.style.height = 'auto'; desc.style.height = `${desc.scrollHeight + 2}px`; };
  // The boxes lie over the label and what is under it, and the title and its description keep their room
  // unseen, so the label stays the size it was and nothing on the board moves while they are open or when
  // they close (subpetjump, 10 November: a label sits on what it holds, its foot fixed, so the boxes taller
  // than the title had lifted it, a sub-PET's over the sub-PET above it, until the edit ended)
  const over = document.createElement('div');
  over.className = 'th-title-boxes';
  over.appendChild(input);
  over.appendChild(desc);
  title.style.visibility = 'hidden';
  if (shown) shown.style.visibility = 'hidden';
  el.classList.add('editing');
  column.appendChild(over);
  fit();
  fitDesc();
  TH.editing = { id, input, desc, before: opts.before || thSnap(TH.v, TH.removed), fresh: !!opts.fresh, was: g.label,
    boxes: opts.was || thLabelBoxes(TH.layout) };
  // a title and a description are each one line that wraps: a line break typed or pasted becomes a space
  const oneLine = (box, sized) => () => {
    if (/[\r\n]/.test(box.value)) {
      const at = box.selectionStart;
      box.value = box.value.replace(/[\r\n]+/g, ' ');
      box.setSelectionRange(at, at);
    }
    sized(); thMeasure(); thPlace();
  };
  input.addEventListener('input', oneLine(input, fit));
  desc.addEventListener('input', oneLine(desc, fitDesc));
  const keys = (box) => (e) => {
    // the boxes keep their own keys: nothing on this screen or the turn screen hears them
    e.stopPropagation();
    if (e.isComposing) return;
    const plain = !e.altKey && !e.metaKey && !e.ctrlKey;
    const toDesc = box === input && plain && ((e.key === 'Tab' && !e.shiftKey) || (e.key === 'Enter' && e.shiftKey));
    if (toDesc) { e.preventDefault(); desc.focus(); desc.setSelectionRange(desc.value.length, desc.value.length); }
    else if (box === desc && e.key === 'Tab' && e.shiftKey) { e.preventDefault(); input.focus(); }
    else if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); thTitleDone(true); }
    else if (e.key === 'Escape') { e.preventDefault(); thTitleDone(false); }
  };
  input.addEventListener('keydown', keys(input));
  desc.addEventListener('keydown', keys(desc));
  // a click away keeps both, and going from one box to the other is no click away
  const away = (other) => (e) => { if (e.relatedTarget !== other) thTitleDone(true); };
  input.addEventListener('blur', away(desc));
  desc.addEventListener('blur', away(input));
  input.addEventListener('pointerdown', (e) => e.stopPropagation());
  desc.addEventListener('pointerdown', (e) => e.stopPropagation());
  thMeasure();
  thPlace();
  if (opts.desc) { desc.focus(); desc.setSelectionRange(desc.value.length, desc.value.length); return; }
  input.focus();
  input.select();
}

/* Add description or Edit description, in a label's right-click menu: the title's boxes open on the canvas with
   the description's taken, or with the table showing the Inspector open on the label with its box taken. */
function thDescOpen(id) {
  if (!TH.live || TH.busy || !thIsGroup(TH.v, id) || thRefuse('rename')) return;
  if (TH.face !== 'table') { thTitleOpen(id, { desc: true }); return; }
  thSelectOnly({ kind: 'group', id });
  TH.lastPick = { kind: 'group', id };
  thInspectorOpen({ kind: 'group', id });
  const box = $('th-gdesc');
  if (!box) return;
  box.focus();
  box.setSelectionRange(box.value.length, box.value.length);
}

/* Remove description, in its menu: taken off in one step, which Undo puts back. */
function thDescRemove(id) {
  if (!TH.live || TH.busy || !thIsGroup(TH.v, id) || thRefuse('rename')) return;
  const before = thSnap(TH.v, TH.removed);
  if (thSetDesc(TH.v, id, '')) thDone(before, t('themes.step.desc_removed'), { settle: [], labels: [id] });
}

function thTitleDone(keep) {
  // a statement open on a card goes the way a title does, wherever the canvas closes the box, and
  // so do a sticky note's words
  thCardEditDone(keep);
  thStickyEditDone(keep);
  const ed = TH.editing;
  if (!ed) return;
  TH.editing = null;
  const g = thGroup(TH.v, ed.id);
  if (g && keep) g.label = thLabelKept(ed.input.value.trim());
  const described = !!(g && keep && ed.desc && thSetDesc(TH.v, ed.id, ed.desc.value));
  // a new label, or a longer title, that comes to sit on a card sends the card clear
  const settle = { settle: [], was: ed.boxes, labels: [ed.id] };
  if (ed.fresh) thDone(ed.before, t('themes.step.made_theme'), settle);
  else if (g && g.label !== ed.was) thDone(ed.before, described ? t('themes.step.renamed_described') : t('themes.step.renamed'), settle);
  else if (described) thDone(ed.before, thDescStep(g), settle);
  else thRender();
}

/* ── a statement's passage ── */

/* From a statement to its place in the transcript and back, the hermeneutic circle's part to whole
   (16 October, a tester's ask, Adam's word): Go to the passage in a statement card's menu, on the PETs
   canvas and on the GETs canvas (a double-click on the card edits the statement on both since 30
   October), or a double-click on a statement's row in the GETs screen's Cases panel, its card on the
   board or not, saves the canvas, then
   opens Experiential statements at the passage the statement belongs to, its quote's marks lit,
   and the way back there returns to this board as it stood, the same board, the same place on the
   canvas and the same selection, its undo kept. A statement whose passage is no longer in the
   transcript says one line, the server's, and nothing changes. */
const TH_NO_PASSAGE = t('themes.card.no_passage');

/* whether a card is a statement: every card on the PETs canvas, and a statement's card on GETs */
function thIsStatement(v, key) {
  const c = v && v.cards[key];
  if (!c) return false;
  return TH.mode === 'gets' ? c.kind === 'es' : true;
}

/* a statement's sheet, row and line from its key, `Initial:12:0`, the sheet split off from the right
   since Excel never lets a sheet name carry a colon */
function thLineOf(ident) {
  const parts = String(ident || '').split(':');
  if (parts.length < 3) return null;
  const line = Number(parts.pop());
  const row = Number(parts.pop());
  const sheet = parts.join(':');
  return sheet && Number.isInteger(row) && Number.isInteger(line) ? { sheet, row, line } : null;
}

async function thToPassage(key) {
  if (!TH.live || TH.busy || !TH.v) return;
  const gets = TH.mode === 'gets';
  // on GETs a statement's row in the Cases panel goes too, its card on the board or not (16 October)
  const split = gets ? gtSplit(key) : null;
  if (gets ? split.kind !== 'es' : !thIsStatement(TH.v, key)) return;
  const at = thLineOf(gets ? split.ident : key);
  const book = gets ? (gtCase(split.kase) || {}).path : TH.path;
  if (!at || !book) { say(TH_NO_PASSAGE, 6000); return; }
  thTitleDone(true);
  thNoteDone(true);
  thVmenu(false);
  // a revision on view goes, and the board itself is what is saved and what the way back finds
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  if (!TH.live || !TH.v) return;
  const kept = {
    mode: TH.mode, path: TH.path, label: TH.label, back: TH.back, board: TH.meta ? TH.meta.id : null,
    // where its own way back goes, as it went
    to: TH.to,
    view: { x: TH.view.x, y: TH.view.y, z: TH.view.z }, pick: TH.lastPick ? { ...TH.lastPick } : null,
    sel: { cards: [...TH.sel.cards], groups: [...TH.sel.groups], stickies: [...TH.sel.stickies] },
    // the card the passage is opened from, which the way back keeps in view
    from: key,
    // and where the table was scrolled to, when it showed
    tscroll: TH.face === 'table' && $('th-table') ? $('th-table').scrollTop : null,
  };
  // the canvas it came from, a timepoint's PETs or the LPETs, which the way back reopens
  const where = TH.lpets ? { lpets: true } : TH.tp && !gets ? { timepoint: TH.tp } : {};
  const again = () => (kept.mode === 'gets' ? getsOpen : themesOpen)(kept.path,
    Object.assign({ back: kept.back, label: kept.label, to: kept.to, board: kept.board, restore: kept }, where));
  // the screen put away as the way back puts it away, its board left as it was saved
  const leave = () => {
    TH.live = false;
    TH.ask += 1;
    thPile(false);
    thXmenu(false);
    thCasemenu(false);
    thSideShut(false);
    thExported(null);
    thMenuClose();
    $('themes').hidden = true;
  };
  // a way in with its entry in the browser's history, taken again from this card by Forward. The way back is
  // named by the step's key, LGETs as lgets and a timepoint's PETs with their timepoint, so the statements
  // bar's step for the board he left is the way back to it, as from the Experiential statements step (1 November)
  await navGo(() => thToPassage(key), () => openPassage(book, at, { leave, back: again,
    to: TH.lpets ? 'lpets' : gets ? (TH.lgets ? 'lgets' : 'gets') : 'pets', timepoint: TH.tp || null }));
}

/* The board as the way back from a statement's passage finds it: the place on the canvas and the
   selection it had, each card, label and note that is still there, and the Inspector following it.
   A window that changed size while the passage was open can leave that place with the card he came
   from outside the canvas, a phone turned or a window narrowed, so then the canvas moves at the same
   zoom until that card stands in the middle of it (16 October, after the screenshot check at 360). */
function thBackFromPassage(r) {
  if (!TH.live || !TH.v || !r) return;
  if (r.view && Number.isFinite(r.view.z)) {
    TH.view = { x: r.view.x, y: r.view.y, z: r.view.z };
    thView();
  }
  const c = r.from ? TH.v.cards[r.from] : null;
  const stage = c ? thStage() : null;
  if (c && stage && stage.clientWidth && stage.clientHeight) {
    const s = thSize(r.from);
    const { x, y, z } = TH.view;
    const cx = x + (c.x + s.w / 2) * z;
    const cy = y + (c.y + s.h / 2) * z;
    if (cx < 0 || cx > stage.clientWidth || cy < 0 || cy > stage.clientHeight) {
      TH.view = { x: stage.clientWidth / 2 - (c.x + s.w / 2) * z, y: stage.clientHeight / 2 - (c.y + s.h / 2) * z, z };
      thView();
    }
  }
  const sel = r.sel || {};
  TH.sel.cards = new Set((sel.cards || []).filter((k) => TH.v.cards[k]));
  TH.sel.groups = new Set((sel.groups || []).filter((id) => thIsGroup(TH.v, id)));
  TH.sel.stickies = new Set((sel.stickies || []).filter((id) => thIsSticky(TH.v, id)));
  TH.lastPick = r.pick && thSelected(r.pick) ? r.pick : null;
  thDrawSel();
  thPanelFollow();
  // the table, when it shows, comes back where it was scrolled to, its rows selected as they were
  if (TH.face === 'table') {
    thTableDraw();
    if (Number.isFinite(r.tscroll)) $('th-table').scrollTop = r.tscroll;
  }
}

/* ── a statement edited in place ── */

/* The one act on this screen that writes the workbook: a statement's line in its row's experiential
   statements cell, every other line of the cell kept. A server from before the route says so. */
const TH_EDIT_ROUTE = '/api/edit-statement';
const TH_EDIT_EMPTY = t('themes.edit.empty');
const TH_EDIT_MISSING = t('themes.edit.missing');
const thOneLine = (text) => String(text || '').replace(/\s+/g, ' ').trim();

/* a statement's card as drawn, on the canvas or in a stack shown open */
const thCardEl = (key) => TH.els.cards[key] || (TH.els.under || {})[key] || null;

/* Double-click on a card (until 16 October, and again since 30 October, Adam: "for consistency"): a
   box over it in the serif with the statement, the way a double-click on a label opens its title.
   Enter keeps it, Esc leaves it as it was, and the text stays one line. The box takes the place of
   the card's words, over its quote when the quotes show, and holds the whole statement, as tall as
   its words, a long one no longer stopped at four lines. A card of a stack shown open opens the same
   way. A card marked missing has no line to write, and a server from before the route changes nothing.
   With `opts.panel` the box opens in the Inspector, over the statement there, by the same path:
   the same keys, the same route, the same step of undo. On the GETs, LGETs and LPETs boards a
   statement's card opens the same box (Adam, 30 October: "Edit there too"), its line written in its
   participant's own workbook (see thLineAt), a card no longer in its participant's copy refused as a
   missing one, and a server from before that carries the words to the GETs' copies changes nothing.
   Any other card there opens the Inspector, as it always has. */
async function thCardEditOpen(key, opts = {}) {
  if (TH.mode === 'gets' && !thIsStatement(TH.v, key)) { gtCardOpen(key); return; }
  if (!TH.live || TH.busy || TH.writing || thRefuse('edit')) return;
  const v = TH.v;
  const c = v.cards[key];
  if (!c || !thCardEl(key)) return;
  if (c.missing || c.gone || !thLineAt(key, c)) { say(TH_EDIT_MISSING); return; }
  thTitleDone(true);
  thNoteDone(true);
  const gets = TH.mode === 'gets';
  if (!TH.canEdit || (gets && !TH.canCopies)) {
    try {
      const ready = await api(TH_EDIT_ROUTE, { workbook: TH.path, check: true });
      // the GETs' copy of a participant takes an edit's words in the same request since 30 October, and a
      // server from before would leave it behind
      if (gets && !(ready && ready.copies)) { say(RESTART_LINE, 6000); return; }
      TH.canEdit = true;
      if (ready && ready.copies) TH.canCopies = true;
    } catch (err) {
      say(needsRestart(err) ? RESTART_LINE : err.message, 6000);
      return;
    }
    if (!TH.live || TH.v !== v || TH.cardEdit || TH.editing) return;
  }
  const el = thCardEl(key);
  if (!el || !v.cards[key]) return;
  // the Inspector's statement, while the Inspector still shows this card
  const words = opts.panel && TH.panelOpen && TH.panel && TH.panel.kind === 'card' && TH.panel.id === key
    ? $('th-panel-body').querySelector('.th-panel-title[data-edit]') : null;
  if (opts.panel && !words) return;
  const box = document.createElement('textarea');
  box.className = 'th-title-edit th-card-edit';
  if (words) box.classList.add('th-panel-edit');
  box.value = c.text;
  box.rows = 1;
  box.spellcheck = true;
  box.setAttribute('aria-label', t('themes.statement'));
  const fit = () => { box.style.height = 'auto'; box.style.height = `${box.scrollHeight + 2}px`; };
  if (words) {
    words.hidden = true;
    words.parentNode.insertBefore(box, words);
  } else {
    // in the words' own place, so with the quotes shown the quote stays under it
    const text = el.querySelector('.th-text');
    text.hidden = true;
    el.classList.add('editing');
    text.after(box);
  }
  TH.cardEdit = { key, box, was: c.text, panel: !!words };
  box.addEventListener('input', () => {
    // one line only: a line break typed or pasted becomes a space
    if (/[\r\n]/.test(box.value)) {
      const at = box.selectionStart;
      box.value = box.value.replace(/[\r\n]+/g, ' ');
      box.setSelectionRange(at, at);
    }
    fit();
  });
  box.addEventListener('keydown', (e) => {
    // the box keeps its own keys: nothing on this screen or the turn screen hears them
    e.stopPropagation();
    if (e.isComposing) return;
    if (e.key === 'Enter') {
      e.preventDefault();
      if (!thOneLine(box.value)) { say(TH_EDIT_EMPTY); return; }
      thCardEditDone(true);
    } else if (e.key === 'Escape') { e.preventDefault(); thCardEditDone(false); }
  });
  box.addEventListener('blur', () => thCardEditDone(true));
  box.addEventListener('pointerdown', (e) => e.stopPropagation());
  fit();
  box.focus();
  box.select();
}

/* Kept with Enter or a click away, or let go with Esc. A text that changed goes to the workbook, and
   an empty one is refused with a line, the card as it was. */
function thCardEditDone(keep) {
  const ed = TH.cardEdit;
  if (!ed) return;
  TH.cardEdit = null;
  const text = thOneLine(ed.box.value);
  const c = TH.v && TH.v.cards[ed.key];
  thRender();
  if (!keep || !c || text === thOneLine(ed.was)) return;
  if (!text) { say(TH_EDIT_EMPTY); return; }
  thStatementWrite(ed.key, ed.was, text, true);
}

/* Where a statement card's line is written: on PETs the board's own workbook and the card's sheet,
   row and line, and on GETs, LGETs and LPETs its participant's workbook, or the participant's at a
   timepoint on LPETs, as the Participants panel holds it, and the line its key names, `Juno/es/Initial:12:0`.
   Null for a card whose participant or line cannot be found. */
function thLineAt(key, c) {
  if (TH.mode !== 'gets') return { workbook: TH.path, sheet: c.sheet, row: c.row, line: c.line };
  const split = gtSplit(key);
  const at = split.kind === 'es' ? thLineOf(split.ident) : null;
  const book = (gtCase(split.kase) || {}).path;
  return at && book ? Object.assign({ workbook: book }, at) : null;
}

/* One line of the workbook written, `from` what it read and `to` what it reads now. On success the
   card and the board's stored text take the new words, so nothing shows as changed, and the save
   goes as usual. `step` makes it one step of undo. A failed write is one line, and the card keeps
   its text. On a GETs, LGETs or LPETs board the server carries the words to that file's copy of the
   participant in the same request, and the Participants panel's copy takes them here too. */
async function thStatementWrite(key, from, to, step) {
  const c = TH.v && TH.v.cards[key];
  const at = c ? thLineAt(key, c) : null;
  if (!c || !at || TH.writing) return false;
  TH.writing = true;
  let data;
  try {
    data = await api(TH_EDIT_ROUTE, Object.assign({}, at, { text: to, old: from }));
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 6000);
    return false;
  } finally {
    TH.writing = false;
  }
  const card = TH.live && TH.v && TH.v.cards[key];
  if (card) {
    card.text = data.text;
    card.changed = false;
    delete card.stored;
  }
  if (TH.live && TH.mode === 'gets') gtLineTook(key, data.text);
  // the edit carried the words to the board on the canvas too, so its next save carries the version
  // the edit wrote, on GETs the version from the copy the edit reached
  const copy = TH.mode === 'gets' ? ((data.copies || {})[TH.lpets ? 'lpets' : TH.lgets ? 'lgets' : 'gets'] || {}) : null;
  const mine = TH.live && TH.meta && ((copy ? copy.versions : data.versions) || []).find((b) => b.id === TH.meta.id);
  if (mine && mine.v) TH.meta.v = mine.v;
  // the edit's line in the board's History (histreplace, 30 October), for the tab when it shows
  const lines = TH.live && TH.meta && ((copy ? copy.histories : data.histories) || {})[TH.meta.id];
  if (Array.isArray(lines)) {
    TH.history = lines;
    if (TH.boardOpen && TH.tab === 'history') thBoardDraw();
  }
  if (step) {
    TH.undo.push({ edit: { key, from: data.old, to: data.text }, what: t('themes.step.statement_edited') });
    if (TH.undo.length > TH_UNDO_DEPTH) TH.undo.shift();
    TH.redo.length = 0;
  }
  TH.worked = true;
  if (!TH.live) return true;
  // a card whose words now take a line more settles clear of what it comes to rest on, and a frame it grows
  // sends its neighbours clear, as a sticky note's edit does (17 October, later)
  const was = thFileBoxes();
  thRender();
  if (thInFile(() => thSettle(TH.v, thSize, [key], was, []))) thPlace();
  if (TH.panelOpen) thPanelDraw();
  thSoon();
  return true;
}

/* Undo and redo of a statement edited in place: the old words written back through the same route,
   or the new ones again. The step moves across only once the workbook holds them. */
async function thStatementStep(entry, backwards) {
  const from = backwards ? TH.undo : TH.redo;
  const onto = backwards ? TH.redo : TH.undo;
  const { key, from: was, to: now } = entry.edit;
  if (!await thStatementWrite(key, backwards ? now : was, backwards ? was : now, false)) return;
  const at = from.lastIndexOf(entry);
  if (at >= 0) from.splice(at, 1);
  onto.push(entry);
}

/* ── sticky notes ── */

const TH_STICKY_FREE = t('themes.sticky.free');

/* A second click on empty canvas soon after the first, and near it: a double-click there. */
function thEmptyTwice(e) {
  const now = Date.now();
  const last = TH.lastEmpty;
  const twice = !!last && now - last.at < 450 && Math.hypot(e.clientX - last.x, e.clientY - last.y) < 6;
  TH.lastEmpty = twice ? null : { at: now, x: e.clientX, y: e.clientY };
  return twice;
}

/* The room a new sticky note settles into while its words are open (18 October, the find of the row of
   steps' build, where a note made beside a card grew over it as he typed): the widest a note runs and
   TH_STICKY_ROOM lines more than it has, so it lands clear of every card, note and frame beside it with
   room to grow, and should his words outgrow that room it moves clear again, itself alone, and nothing
   else moves while he types. A note there already whose words grow over a card moves clear the same way
   as he types (18 October, where it moved only once its words closed). TH_STICKY_LINE is a line of a
   note's words, 16 pixels at 1.3. */
const TH_STICKY_ROOM = 3;
const TH_STICKY_LINE = 21;
const thStickyRoom = (id) => (item) => {
  const s = thSize(item);
  return item === id ? { w: Math.max(s.w, TH_STICKY.w), h: s.h + TH_STICKY_ROOM * TH_STICKY_LINE } : s;
};

/* whether a note lies over anything beside it, a card, a note or a frame, as it now measures */
function thStickyOver(v, id) {
  if (!thIsSticky(v, id)) return false;
  const parents = thParents(v);
  const home = parents[id] === undefined ? '' : parents[id];
  const layout = thLayout(v, thSize, null);
  const mine = thSolid(v, thSize, layout, id);
  return (thNeighbours(v, parents).get(home) || []).some((other) => {
    if (other === id) return false;
    const box = thSolid(v, thSize, layout, other);
    return !!box && thMeets(mine, box);
  });
}

/* A new sticky note where the pointer is, from a double-click on empty canvas or New sticky note in
   its menu: yellow, its words open with the caret in them. Inside a PET's frame it is that PET's,
   unless `opts.free`, New sticky note on the bar, which makes it the canvas's own wherever it lands.
   It keeps the margin like a card, settling clear of everything beside it with the room its words will
   take (see thStickyRoom), and its making and its first words are one step of undo. A server from
   before the notes would drop it, so the page says to restart and makes none. */
function thStickyNew(clientX, clientY, opts = {}) {
  if (!TH.live || TH.busy || !TH.v || thRefuse('sticky')) return;
  if (!TH.stickable) { say(RESTART_LINE, 6000); return; }
  thTitleDone(true);
  thNoteDone(true);
  const v = TH.v;
  const at = thToWorld(clientX, clientY);
  const before = thSnap(v, TH.removed);
  const was = thFileBoxes();
  const gid = opts.free ? null : thFrameAt(v, TH.layout, at, null);
  const id = thStickyMake(v, at.x - TH_STICKY.w / 2, at.y - 20, gid);
  if (!id) return;
  TH.sel.cards.clear();
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  TH.sel.stickies.add(id);
  TH.lastPick = { kind: 'sticky', id };
  thRender();
  // it settles with the room its words will take, so it never comes to lie over a card as he types
  if (thInFile(() => thSettle(v, thStickyRoom(id), [id], was, []))) thPlace();
  thPanelFollow();
  thStickyEditOpen(id, { before, fresh: true, was });
}

/* A note's words open on the canvas, from a double-click on it or as it is made: a box in its own
   face on its own paper, growing with the words. Enter, Esc or a click away keeps them and leaves
   the box, Shift + Enter starts a new line, and Esc on a note with no words takes the note away. */
function thStickyEditOpen(id, opts = {}) {
  if (!TH.live || TH.busy || thRefuse('sticky')) return;
  const v = TH.v;
  const n = thSticky(v, id);
  const el = TH.els.stickies[id];
  if (!n || !el) return;
  if (!opts.fresh) { thTitleDone(true); thNoteDone(true); }
  const box = document.createElement('textarea');
  box.className = 'th-title-edit th-sticky-edit';
  box.value = n.text;
  box.rows = 1;
  box.spellcheck = true;
  box.placeholder = t('themes.sticky.placeholder');
  box.setAttribute('aria-label', t('themes.sticky.note'));
  // the note fits his words as he types: they are set, unseen, in the note's own text, which the
  // note sizes to, and the box lies over them, the placeholder's words standing in for none
  const words = el.querySelector('.th-sticky-text');
  const fit = () => { words.textContent = `${box.value || box.placeholder}\u200b`; };
  el.classList.add('editing');
  el.insertBefore(box, el.firstChild);
  TH.stickyEdit = { id, box, before: opts.before || thSnap(v, TH.removed), fresh: !!opts.fresh,
    boxes: opts.was || thFileBoxes() };
  box.addEventListener('input', () => {
    fit();
    thMeasure();
    // a note whose words outgrow its room moves clear as he types, itself alone with room to grow, a new
    // note and one there already alike (18 October, where one there already moved only as its words closed)
    const ed = TH.stickyEdit;
    if (ed && thStickyOver(v, id) && thInFile(() => thSettle(v, thStickyRoom(id), [id], ed.boxes, []))) ed.moved = true;
    thPlace();
  });
  box.addEventListener('keydown', (e) => {
    // the box keeps its own keys: nothing on this screen or the turn screen hears them
    e.stopPropagation();
    if (e.isComposing) return;
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); thStickyEditDone(true); }
    else if (e.key === 'Escape') { e.preventDefault(); thStickyEditDone(false); }
  });
  box.addEventListener('blur', () => thStickyEditDone(true));
  box.addEventListener('pointerdown', (e) => e.stopPropagation());
  fit();
  thMeasure();
  thPlace();
  box.focus();
  box.setSelectionRange(box.value.length, box.value.length);
}

/* The box closed. `keep` is Enter or a click away, and false is Esc, which keeps the words too but
   takes away a note left with none. A new note's making and its first words are one step of undo,
   and words changed on a note there already are one step, its move as they grew with them. A note
   that grew moves clear of what it comes to sit on, and comes inside a frame it is left in, as a
   card does. */
function thStickyEditDone(keep) {
  const ed = TH.stickyEdit;
  if (!ed) return;
  TH.stickyEdit = null;
  const v = TH.v;
  const n = v && thSticky(v, ed.id);
  if (!n) { thRender(); return; }
  const text = thStickyClean(ed.box.value);
  if (!keep && !text) {
    // a new note let go with Esc leaves the board as it was before it, with no step of undo
    if (ed.fresh) { TH.removed = thPut(v, ed.before); thRender(); thPanelFollow(); return; }
    thStickyRemove(v, ed.id);
    thDone(ed.before, t('themes.step.deleted_stickies', { n: 1 }));
    thPanelFollow();
    return;
  }
  const changed = n.text !== text;
  n.text = text;
  if (ed.fresh) { thDone(ed.before, t('themes.step.made_sticky'), { settle: [ed.id], was: ed.boxes }); return; }
  // words that moved the note as they grew are kept with its place, though they come back to what they were
  if (changed || ed.moved) { thDone(ed.before, t('themes.step.edited_sticky'), { settle: [ed.id], was: ed.boxes }); return; }
  thRender();
}

/* Delete note, in a note's menu, or the small cross a selected note carries: off the board, and
   one step of undo brings it back where it was, in the PET it was in. A note never goes to the bin,
   which is for statements alone. */
function thStickyDelete(ids) {
  if (!TH.live || TH.busy || thRefuse('delete')) return;
  thTitleDone(true);
  thNoteDone(true);
  const v = TH.v;
  const live = ids.filter((id) => thIsSticky(v, id));
  if (!live.length) return;
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  for (const id of live) { thStickyRemove(v, id); TH.sel.stickies.delete(id); }
  thDone(before, t('themes.step.deleted_stickies', { n: live.length }), { settle: [], was });
  thPanelFollow();
}

/* A note's colour, from its menu or the Inspector's dots: one step of undo. */
function thStickyRecolour(id, colour) {
  if (!TH.live || TH.busy || thRefuse('colour')) return;
  const before = thSnap(TH.v, TH.removed);
  if (!thStickyColour(TH.v, id, colour)) return;
  thDone(before, t('themes.step.recoloured_sticky'));
}

/* The Inspector for a sticky note: its words in a box to edit, the four colours as dots with the
   one it has marked, and Take out of PET when it is in one. On a revision on view the words show
   read-only and the dots do nothing. */
function thStickyHtml(v, n, owner) {
  const locked = thLocked(v);
  const text = TH.stickyBox && TH.stickyBox.id === n.id ? TH.stickyBox.value : n.text;
  const box = locked
    ? `<p class="th-gnote-read th-sticky-read" title="${escAttr(TH_READ_ONLY)}">${esc(n.text)}</p>`
    : `<textarea class="th-vedit th-sticky-box" id="th-sticky-box" data-sticky-box="${escAttr(n.id)}" rows="4" spellcheck="true" `
      + `placeholder="${escAttr(t('themes.sticky.placeholder'))}" aria-label="${escAttr(t('themes.sticky.note'))}">${esc(text)}</textarea>`;
  const dots = TH_STICKY_COLOURS.map((c) => `<button type="button" class="th-dot sticky-${c}${n.colour === c ? ' on' : ''}" tabindex="-1" `
    + `data-colour="${c}" aria-pressed="${n.colour === c}" aria-label="${thColourName(c)}" title="${thColourName(c)}"${locked ? ' disabled' : ''}></button>`).join('');
  return `${box}<div class="th-dots" role="group" aria-label="${escAttr(t('themes.sticky.colour'))}">${dots}</div>${thLeaveHtml(v, n.id, owner)}`;
}

function thStickyPanelDraw(v, id, owner) {
  const box = $('th-sticky-box');
  const held = TH.stickyBox && box && document.activeElement === box
    ? { start: box.selectionStart, end: box.selectionEnd, top: box.scrollTop } : null;
  const n = thSticky(v, id);
  TH.noteRedraw = true;
  // the box is on the note's own paper
  $('th-panel-body').className = `th-panel-body th-sticky-panel sticky-${TH_STICKY_COLOURS.includes(n.colour) ? n.colour : TH_STICKY_COLOURS[0]}`;
  $('th-panel-body').innerHTML = thStickyHtml(v, n, owner);
  TH.noteRedraw = false;
  const again = held ? $('th-sticky-box') : null;
  if (again) { again.focus(); again.setSelectionRange(held.start, held.end); again.scrollTop = held.top; }
  thPlayerDraw();
}

/* The Inspector's box taken: the words are open until they are kept or let go. */
function thStickyBoxStart(box) {
  const id = box.dataset.stickyBox;
  if (TH.stickyBox && TH.stickyBox.id === id) return;
  thStickyBoxDone(true);
  if (!TH.live || !thIsSticky(TH.v, id) || thLocked(TH.v)) return;
  TH.stickyBox = { id, value: box.value };
}

/* Kept, with Enter or a click away, or let go with Esc, which leaves the words as they were. Words
   that changed are one step of undo. */
function thStickyBoxDone(keep) {
  const ed = TH.stickyBox;
  if (!ed) return;
  TH.stickyBox = null;
  const v = TH.v;
  const box = $('th-sticky-box');
  const text = box && box.dataset.stickyBox === ed.id ? box.value : ed.value;
  if (keep && v && thIsSticky(v, ed.id)) {
    const before = thSnap(v, TH.removed);
    const was = thLabelBoxes(TH.layout);
    if (thStickyText(v, ed.id, text)) { thDone(before, t('themes.step.edited_sticky'), { settle: [ed.id], was }); return; }
  }
  if (TH.panelOpen) thPanelDraw();
}

/* ── the band, and Settings over this screen ── */

/* The research question, in the band under the bar the turn screen carries, from the project the
   case belongs to. Its height goes into --band, which the canvas takes off its own. A server from
   before this sends no project, and the band says there is no question yet, as the turn screen's
   does. */
function thBandDraw() {
  const p = TH.project;
  const question = p ? String(p.research_question || '').trim() : '';
  const el = $('th-band-question');
  el.classList.toggle('band-none', !question);
  if (question) el.textContent = question;
  else el.innerHTML = t('themes.band.set_it_html', { none: NO_QUESTION });
  $('th-band').hidden = false;
  thBandMeasure();
}

function thBandMeasure() {
  const screen = $('themes');
  if (!screen) return;
  const band = $('th-band');
  // the toolbar's dock under the question (21 October) shows with the band, docked or floating since option C of
  // the bars (26 October 2026), as it holds the sidebars' buttons and the board, and its height comes off the
  // canvas with the band's, the title bar's two rows on a phone taken by --rail-h
  const dock = $('th-dock');
  if (dock) dock.hidden = screen.hidden || band.hidden;
  // each measured to the fraction its lines give it, where offsetHeight rounded the band's 55.25px down and the
  // screen stood a quarter pixel taller than the window, the status bar's foot under its edge (loose31, 31 October)
  const high = (el) => { const r = el.getBoundingClientRect(); return r.bottom - r.top; };
  // and the reviewer's tray, the row under the dock while it stands on this screen (review.js, trayfix)
  const tray = $('wt-tray');
  const review = tray && !tray.hidden && tray.parentElement === screen ? high(tray) : 0;
  const tall = high(band) + (dock && !dock.hidden ? high(dock) : 0) + review;
  screen.style.setProperty('--band', `${screen.hidden || band.hidden ? 0 : tall}px`);
}

/* The status bar's steps as it runs short, in the order Adam set on 26 October 2026: the tools' words first, then
   any count he ticked beyond the total and its parts, the spacing, the tools, and only then the counts, the PETs
   before the total and its parts, so at 1280 the whole sentence always shows beside Canvas and Table */
const TH_STATUS_STEPS = ['th-status-short', 'th-status-opt', 'th-status-shortest', 'th-status-shorter', 'th-status-tiny',
  'th-status-lean', 'th-status-trim', 'th-status-least', 'th-status-bare'];

/* The zoom bar keeps clear of the bin at every width of the canvas, which narrows as the sidebars
   open beside it, to about 240px with the Cases panel and the sidebar both open on the GETs screen
   just above the 900px step. While the two fit side by side on one row they stand so. Where they do not, the words Fit all go, and where they still do
   not, the bar stands over the bin, on a second row where one will not hold it, and the pile opens
   over the bar. Run whenever the canvas changes its width.
   With the status bar along the foot (19 October) the bin, the map and the pile stand above it, and where
   the bar runs short it gives way in the order Adam set on 26 October 2026, the counts last: the tools' words,
   then any count beyond the total and its parts, then the spacing, then the tools, the counts after them, so
   no count or button is ever cut (themes.css, th-status-opt). */
function thCorners() {
  const stage = $('th-stage');
  const bar = stage && stage.querySelector('.th-zoomer');
  const bin = $('th-discard');
  if (!bar || !bin || !stage.clientWidth) return;
  stage.classList.remove('th-tight', 'th-tighter', ...TH_STATUS_STEPS);
  const status = stage.classList.contains('th-status-on');
  stage.style.setProperty('--th-status-h', `${status ? bar.offsetHeight : 0}px`);
  if (status) {
    // the counts never shrink, so a bar too short for them overflows and gives way a step at a time,
    // never cutting a word
    const over = () => bar.scrollWidth > bar.clientWidth + 1;
    for (const step of TH_STATUS_STEPS) {
      if (!over()) break;
      stage.classList.add(step);
    }
  } else {
    const gutter = parseFloat(getComputedStyle(bar).right) || 0;
    const room = stage.clientWidth - bin.offsetWidth - 3 * gutter;
    const wide = () => {
      bar.style.width = 'max-content';
      const w = bar.offsetWidth;
      bar.style.width = '';
      return w;
    };
    if (wide() > room) stage.classList.add('th-tight');
    if (stage.classList.contains('th-tight') && wide() > room) stage.classList.add('th-tighter');
  }
  thPalettePlace();
  stage.style.setProperty('--th-bin-up', `${bin.offsetHeight + 8}px`);
  stage.style.setProperty('--th-zoom-up', `${bar.offsetHeight + 8}px`);
  // below 900px the sidebars lie over the canvas and stop this far above its foot, clear of the bin
  // and the zoom bar with its ?, so both stay in reach with either sidebar open
  const body = stage.parentElement;
  if (body && body.getBoundingClientRect) {
    // only what shows: the table hides the bin, whose top of 0 left the sidebar 0 tall over the table at a
    // phone's width (20 October)
    const tops = [bar, bin].filter((el) => el.getClientRects().length).map((el) => el.getBoundingClientRect().top);
    const top = tops.length ? Math.min(...tops) : body.getBoundingClientRect().bottom;
    body.style.setProperty('--th-corners-up', `${Math.max(0, Math.round(body.getBoundingClientRect().bottom - top + 8))}px`);
  }
}

/* A save from Settings over this screen: the settings it now has, the switch, the model and the
   limit on the bar at once, and a question changed under Projects in the band. A server from before
   the bar's state came back with a save leaves the model's name as it was. */
function thSettingsSaved(data, project) {
  if (!TH.live || $('themes').hidden) return;
  if (data && data.config) TH.config = data.config;
  if (data && data.ai) TH.ai = data.ai;
  else if (data && data.config) TH.ai = Object.assign({}, TH.ai || {}, { on: aiFor(data.config, TH.mode === 'gets' ? 'gets' : 'pets') });
  if (project && TH.project && !TH.project.demo) { TH.project = project; thBandDraw(); }
  thAiDraw();
  // the minimap's Auto, On or Off, under Experiential statements' View, rule the board's map too
  thMapSchedule();
  // and the status bar, under View in the PETs category, at once
  thStatusDraw();
}

/* ── the pile ── */

function thPile(open) {
  TH.pileOpen = !!open;
  $('th-pile').hidden = !open;
  $('th-discard').setAttribute('aria-expanded', String(!!open));
  if (open) thPileList();
}

function thPileList() {
  const v = TH.v;
  if (!v) return;
  const why = (key, act) => (act === 'restore' && thWhy(v, key) ? `<div class="th-pile-why">${esc(thWhy(v, key))}</div>` : '');
  const row = (key, c, act, label) => `<li><div class="th-pile-text">${esc(c.text)}</div>${why(key, act)}`
    + `<div class="th-pile-foot"><span class="th-time">${esc(c.time || '')}</span>`
    + `${c.sheet && c.sheet !== TH.sheets[0] ? `<span class="th-sheet">${esc(c.sheet)}</span>` : ''}`
    + `${thLocked(v) ? '' : `<button type="button" class="ghost small${act === 'remove' ? ' btn-remove' : ''}" tabindex="-1" data-${act}="${escAttr(key)}">${esc(label)}</button>`}</div></li>`;
  const thrown = v.discarded.filter((key) => v.cards[key] && !v.cards[key].missing);
  const gone = Object.keys(v.cards).filter((key) => v.cards[key].missing);
  // the heading carries its count, "Set aside (3)", as the exports head their lists
  let html = `<h3 class="section-label">${esc(t('themes.pile.binned', { n: thrown.length }))}</h3>`;
  html += thrown.length
    ? `<ul class="th-pile-list">${thrown.map((key) => row(key, v.cards[key], 'restore', t('themes.pile.put_back'))).join('')}</ul>`
    : `<p class="th-pile-empty">${esc(t('themes.pile.nothing'))}</p>`;
  if (gone.length) {
    html += `<h3 class="section-label spaced">${esc(t('themes.pile.missing'))}</h3>`
      + `<ul class="th-pile-list">${gone.map((key) => row(key, v.cards[key], 'remove', t('themes.pile.remove'))).join('')}</ul>`;
  }
  $('th-pile-body').innerHTML = html;
}

/* a card put back stands unplaced in the nearest free spot to the middle of what is in view */
function thPutBack(key) {
  if (thRefuse('restore')) return;
  const stage = thStage();
  const r = stage ? stage.getBoundingClientRect() : null;
  const mid = r ? thToWorld(r.left + r.width / 2, r.top + r.height / 2) : { x: TH_CARD.w / 2, y: TH_CARD.h / 2 };
  const before = thSnap(TH.v, TH.removed);
  thAck([key]);
  if (!thRestore(TH.v, key, mid.x - TH_CARD.w / 2, mid.y - TH_CARD.h / 2)) return;
  TH.z = TH.z.filter((k) => k !== key).concat([key]);
  thDone(before, t('themes.step.put_back'), { settle: [key] });
}

/* a missing card goes from the board altogether, which undo puts back */
function thRemove(key) {
  if (!TH.v.cards[key] || thRefuse('remove')) return;
  const before = thSnap(TH.v, TH.removed);
  thDetach(TH.v, key);
  TH.v.discarded = TH.v.discarded.filter((k) => k !== key);
  delete TH.v.cards[key];
  TH.removed.add(key);
  thDone(before, t('themes.step.removed_missing'));
}

/* ── the sidebar: the Inspector, and the tabs about the board ── */

/* What the Inspector shows for the selection: one card or label selected is that one, several the
   one clicked last, or failing that what it shows already, and nothing selected is nothing. */
function thPanelPick() {
  const n = TH.sel.cards.size + TH.sel.groups.size + TH.sel.stickies.size;
  if (!n || !TH.v) return null;
  if (n === 1) {
    if (TH.sel.stickies.size) return { kind: 'sticky', id: [...TH.sel.stickies][0] };
    return TH.sel.cards.size ? { kind: 'card', id: [...TH.sel.cards][0] } : { kind: 'group', id: [...TH.sel.groups][0] };
  }
  const held = (item) => !!item && thSelected(item);
  if (held(TH.lastPick)) return { kind: TH.lastPick.kind, id: TH.lastPick.id };
  if (held(TH.panel)) return TH.panel;
  if (TH.sel.groups.size) return { kind: 'group', id: [...TH.sel.groups][0] };
  return TH.sel.cards.size ? { kind: 'card', id: [...TH.sel.cards][0] } : { kind: 'sticky', id: [...TH.sel.stickies][0] };
}

/* The Inspector follows the selection while it shows, and the sidebar stays as it is otherwise: a
   click on the canvas selects and never opens or switches it, and nor does a drag or a lasso. */
function thPanelFollow() {
  if (!TH.panelOpen) return;
  thPanelShow(thPanelPick());
}

/* The Inspector on a card or a label, or on nothing, when it reads "Select a statement or a PET."
   Not showing, it only notes what it is to show when it does. */
function thPanelShow(item) {
  thNoteDone(true);
  const was = TH.panel;
  TH.panel = item || null;
  if (!TH.panelOpen) return;
  if (!item) $('th-player').pause();
  thPanelDraw();
  if (!was || !item || thPanelKey(was) !== thPanelKey(item)) $('th-panel-body').scrollTop = 0;
}

/* Nothing selected any more: an open Inspector says so, and stays open. */
function thPanelDrop() {
  thPanelShow(null);
}

/* The sidebar's tabs in order, one showing at a time: the Inspector, about the selection, then
   Guidance, the lines of themes_guidance.md to hand, and History, the board's revisions. The GETs
   screen has every one of them, its Guidance the GETs sections of pet_guidance.md. Its Table tab went
   on 19 October, the Canvas and Table switch on the bar doing its job (Adam), and Review and Revise,
   the AI's, on 11 November 2026 (aiout). */
const TH_TABS = ['inspector', 'guidance', 'history'];
const GT_TABS = ['inspector', 'guidance', 'history'];
// a thematic analysis project's board has its own Guidance, ta_themes_guidance.md's (tarail, 3 November 2026), which
// a server from before it does not send, and the tab then stands hidden there, the GETs lines being IPA's (themesbuild)
const thTabsOf = (mode) => (mode === 'gets' ? GT_TABS : TH_TABS)
  .filter((t) => !(t === 'guidance' && mode === 'gets' && thTa() && !TH.guidanceTa));

/* a tab of the screen's own, or its first, the Inspector */
const thTabOf = (tab, mode = TH.mode) => (thTabsOf(mode).includes(tab) ? tab : thTabsOf(mode)[0]);

/* Whether the sidebar is open and on which tab, kept in the browser for each screen the way the
   rail's put-away state is, so a reload, and the next open of the screen, bring it back as it was.
   The PETs screen keeps the key the Board panel kept, the same shape, so a tab left showing there
   carries over. Nothing of it reaches the themes file, the GETs file or the settings. */
const TH_SIDE_KEYS = { pets: 'idiograph-themes-board', gets: 'idiograph-gets-board' };
const thSideKey = (mode) => TH_SIDE_KEYS[mode === 'gets' ? 'gets' : 'pets'];

function thSideStored(mode = TH.mode) {
  const tabs = thTabsOf(mode);
  try {
    const saved = JSON.parse(localStorage.getItem(thSideKey(mode)) || 'null');
    if (saved && typeof saved === 'object' && tabs.includes(saved.tab)) return { open: saved.open === true, tab: saved.tab };
  } catch { /* private window, or a value that is not ours */ }
  return { open: false, tab: tabs[0] };
}

function thSideKeep() {
  try {
    localStorage.setItem(thSideKey(TH.mode), JSON.stringify({ open: !!TH.sideOpen, tab: TH.tab }));
  } catch { /* private window */ }
}

/* On an open of the screen, once the board is on the canvas: the sidebar open on the tab it was
   left on, or closed on it, so the next press of its button finds it there. */
function thSideRestore() {
  thSideTableGone();
  const kept = thSideStored();
  TH.tab = kept.tab;
  if (kept.open) thSideOpen(kept.tab, undefined, false);
  else thSideDraw();
}

/* A GETs sidebar left open on its Table tab, which went on 19 October: the board opens on its Table
   view, and the sidebar is kept shut on the Inspector. */
function thSideTableGone() {
  if (TH.mode !== 'gets') return;
  try {
    const saved = JSON.parse(localStorage.getItem(thSideKey('gets')) || 'null');
    if (!saved || saved.tab !== 'table') return;
    localStorage.setItem(thSideKey('gets'), JSON.stringify({ open: false, tab: 'inspector' }));
    if (saved.open) thFace('table');
  } catch { /* private window, or a value that is not ours */ }
}

/* The sidebar button in the bar: the sidebar open on the tab left showing, and closed again. */
function thSideDoor() {
  if (!TH.live) return;
  if (TH.sideOpen) thSideShut();
  else thSideOpen(TH.tab);
}

/* The sidebar open on a tab, from its button, its tabs, `i`, Inspect, Note and `n`: on the Inspector,
   on `item` when one is given, or else on what is selected. */
function thSideOpen(tab, item, keep = true) {
  if (!TH.live) return;
  const to = thTabOf(tab);
  const was = TH.sideOpen ? TH.tab : null;
  if (was === 'inspector' && to !== 'inspector') thInspectorLeave();
  TH.tab = to;
  TH.sideOpen = true;
  TH.panelOpen = to === 'inspector';
  TH.boardOpen = !TH.panelOpen;
  thSideDraw();
  if (TH.panelOpen) thPanelShow(item === undefined ? thPanelPick() : item);
  else {
    thBoardDraw();
    // a tab opens at its top
    if (was !== to) $('th-bpanel-body').scrollTop = 0;
  }
  if (keep) thSideKeep();
}

/* The Inspector open: the sidebar on its first tab, from `i`, Inspect, `n`, Note on a label, a note
   undone or done again, a double-click on a GETs card and a participant note added. */
function thInspectorOpen(item, keep = true) {
  thSideOpen('inspector', item, keep);
}

/* `i`: the sidebar open on the Inspector, and closed again while it shows the Inspector. */
function thInspectorKey() {
  if (!TH.live) return;
  if (TH.panelOpen) thSideShut();
  else thInspectorOpen();
}

/* The Inspector left for another tab, or with the sidebar closed: a note or a sticky note's words
   open there are kept, as a click away keeps them, and its player pauses. */
function thInspectorLeave() {
  thNoteDone(true);
  $('th-player').pause();
}

/* The sidebar closed, from its button or `i`, and on leaving the screen or opening a case, which
   close it with `keep` false so the browser goes on holding it as he left it. Esc and a click on
   empty canvas never close it. */
function thSideShut(keep = true) {
  if (TH.panelOpen) thInspectorLeave();
  TH.sideOpen = false;
  TH.panelOpen = false;
  TH.boardOpen = false;
  thSideDraw();
  if (keep) thSideKeep();
}

/* The sidebar button pressed in while the sidebar is open, with the tooltip that closes it, and the
   sidebar showing its one tab. */
function thSideDraw() {
  const b = $('th-open-side');
  if (b) {
    b.classList.toggle('on', !!TH.sideOpen);
    b.setAttribute('aria-pressed', String(!!TH.sideOpen));
    b.title = TH.sideOpen ? t('themes.inspector.hide_tip') : t('themes.inspector.show_tip');
  }
  if (!$('th-side')) return;
  $('th-side').hidden = !TH.sideOpen;
  $('th-panel').hidden = !TH.panelOpen;
  $('th-bpanel').hidden = !TH.boardOpen;
  thTabsDraw();
}

function thTabsDraw() {
  for (const b of document.querySelectorAll('#th-tabs [data-tab]')) {
    // a tab the screen does not have stands hidden: Guidance where its lines are not there (tarail)
    if (b.dataset.tab !== 'inspector' && b.dataset.tab !== 'history') b.hidden = !thTabsOf(TH.mode).includes(b.dataset.tab);
    const on = b.dataset.tab === TH.tab;
    b.classList.toggle('on', on);
    b.setAttribute('aria-selected', String(on));
  }
}

/* The head of the tabs about the board: the board's name, and its note under it in the small type
   when it has one, read-only here, since Note in the board menu is the way to edit it. */
function thBoardHead() {
  const name = (TH.meta && TH.meta.name) || '';
  const note = (TH.meta && TH.meta.note) || '';
  $('th-bpanel-name').textContent = name;
  $('th-bpanel-name').title = name;
  $('th-bpanel-note').textContent = note;
  $('th-bpanel-note').title = note;
  $('th-bpanel-note').hidden = !note;
}

/* A tab about the board drawn afresh, for the board on the canvas. */
function thBoardDraw() {
  if (!TH.boardOpen) return;
  thBoardHead();
  if (TH.tab === 'guidance') thGuidanceDraw(); else thHistoryDraw();
}

/* The Guidance tab: each heading of themes_guidance.md in the label face, and the lines under it in
   the serif, each with a small mark, as the turn screen's rail shows guidance.md. The file is read
   on every open of the screen, so an edit shows on the next reload. The foot says where it lives,
   and with AI features on that the AI reads its own file. */
const TH_GUIDANCE_FROM = t('themes.guidance.from');

function thGuidanceDraw() {
  const body = $('th-bpanel-body');
  if (TH.guidance === null) {
    body.innerHTML = `<p class="fineprint th-restart">${esc(RESTART_LINE)}</p>`;
    return;
  }
  let html = TH.guidance.map((s) => `<section class="th-guide-group"><h3 class="section-label">${esc(s.heading)}</h3>`
    + `<ul class="th-guide-lines">${s.lines.map((line) => `<li>${esc(line)}</li>`).join('')}</ul></section>`).join('');
  if (!TH.guidance.length) html = `<p class="th-qnone">${esc(t('themes.guidance.none'))}</p>`;
  body.innerHTML = `${html}<p class="th-guide-from">${esc(TH_GUIDANCE_FROM)}</p>`;
  // asked as it draws, so a thematic analysis project's foot names its own file (tarail)
  if (TH.mode === 'gets') body.lastElementChild.textContent = t('themes.gets.guidance_from');
  // with AI features off the foot names the file and stops there
  if (!thAiOn()) body.lastElementChild.textContent = TH.mode === 'gets' ? t('themes.gets.guidance_file') : t('themes.guidance.file');
}

const thSheetTag = (sheet) => (sheet && sheet !== TH.sheets[0] ? `<span class="th-sheet">${esc(sheet)}</span>` : '');

/* The Inspector's head names what it shows: a theme by its title, in its tint, with the whole of it
   in the tooltip, and a statement or a sticky note by its kind, Statement or Sticky note, in the
   kicker's style, so the statement shows once, whole, in the body under it, and the head keeps the
   card's own tooltip. With nothing to show it goes, since the tab above already says Inspector, and
   the body's line sits under the tabs. */
function thPanelHead(v, item) {
  const head = $('th-panel-head');
  const name = $('th-panel-name');
  if (!item) {
    head.className = 'th-phead th-phead-empty';
    name.textContent = '';
    name.title = '';
    return;
  }
  if (item.kind === 'group') {
    const g = thGroup(v, item.id);
    head.className = `th-phead ${thTintClass(thTints(v)[item.id])}`;
    name.innerHTML = `<span class="th-panel-label">${esc(thLabelShown(g.label))}</span>`;
    name.title = thLabelShown(g.label);
    return;
  }
  head.className = 'th-phead th-phead-kind';
  if (item.kind === 'sticky') {
    name.textContent = t('themes.sticky.note');
    name.title = (thSticky(v, item.id) || {}).text || '';
    return;
  }
  if (TH.mode === 'gets') {
    const card = v.cards[item.id];
    // a thematic analysis project's code, "Code · 5 extracts", as its card says (themesbuild)
    const it = thTa() && card.kind === 'es' ? gtCodes().get(gtCodeOf(item.id)) : null;
    name.textContent = it ? t('codes.card_kicker', { extracts: t('codes.n.extracts', { n: it.n }) }) : gtKicker(card);
    name.title = card.text || '';
    return;
  }
  name.textContent = t('themes.statement');
  name.title = thCardTitle(v.cards[item.id]);
}

/* The Inspector: a card shows its statement and its own quote, with the row's timecode and a
   play button. A label shows its note and the quotes of every card under it, row by row in
   transcript order under the statements of that row, with a tick on each to pick the one or two
   that carry the theme. With nothing selected it says so in the small type. */
const TH_INSPECT_NONE = t('themes.inspector.none');

function thPanelDraw() {
  // a description open in the panel is kept when the panel goes off its label, as a note is
  const describing = TH.describing;
  if (describing && !(TH.panelOpen && TH.panel && TH.panel.kind === 'group' && TH.panel.id === describing.id)) {
    thDescDone(true);
    return;
  }
  // a note open in the panel is kept when the panel goes off its label, the way a click away keeps it
  const noting = TH.noting;
  if (noting && !(TH.panelOpen && TH.panel && TH.panel.kind === 'group' && TH.panel.id === noting.id)) {
    thNoteDone(true);
    return;
  }
  // and a sticky note's words open in the panel the same way
  const sticking = TH.stickyBox;
  if (sticking && !(TH.panelOpen && TH.panel && TH.panel.kind === 'sticky' && TH.panel.id === sticking.id)) {
    thStickyBoxDone(true);
    return;
  }
  const item = TH.panel;
  const v = TH.v;
  if (!item || !v) {
    thPanelHead(v, null);
    $('th-panel-body').className = 'th-panel-body th-inspect-empty';
    $('th-panel-body').innerHTML = `<p class="th-qnone th-inspect-none">${esc(TH_INSPECT_NONE)}</p>`;
    if (TH.mode === 'gets') $('th-panel-body').firstElementChild.textContent = t('themes.inspector.none_gets');
    thPlayerDraw();
    return;
  }
  const there = item.kind === 'card' ? thOnCanvas(v, item.id) : item.kind === 'sticky' ? thIsSticky(v, item.id) : thIsGroup(v, item.id);
  if (!there) { thPanelDrop(); return; }
  thPanelHead(v, item);
  let html;
  let picks = null;
  const owner = thParents(v)[item.id];
  // a sticky note has its words, its colours and Take out of PET, and no quotes
  if (item.kind === 'sticky') { thStickyPanelDraw(v, item.id, owner); return; }
  if (TH.mode === 'gets') { gtPanelDraw(v, item, owner); return; }
  // the two of a close pair selected together, from Inspect both or the stepping, read one under the other
  const pair = item.kind === 'card' ? thPairSelected(v) : null;
  TH.panelPair = pair;
  if (pair) {
    $('th-panel-name').textContent = t('themes.pair.close_pair');
    $('th-panel-name').title = '';
    $('th-panel-body').className = 'th-panel-body th-pair-panel';
    $('th-panel-body').innerHTML = thPairPanelHtml(v, pair);
    thPlayerDraw();
    return;
  }
  if (item.kind === 'card') {
    const c = v.cards[item.id];
    // the head says Statement, so the statement shows here once, whole, and a double-click on it
    // opens it for editing in place, as one on its card does
    html = `<p class="th-panel-title" data-edit="${escAttr(item.id)}" title="${escAttr(t('themes.inspector.edit_tip'))}">${esc(c.text)}</p>`
      + `<p class="th-panel-meta"><span class="th-time">${esc(c.time || '')}</span>${thSheetTag(c.sheet)}${thSidHtml(item.id)}</p>`
      + thLeftOutHtml(v, item.id, owner)
      + thLeaveHtml(v, item.id, owner);
  } else {
    // the head carries the title, so the body starts with what kind of theme it is and its count
    const g = thGroup(v, item.id);
    picks = new Set((v.picks || {})[g.id] || []);
    const picked = picks.size ? ` · ${esc(t('themes.inspector.picked', { n: picks.size }))}` : '';
    html = thDescHtml(v, g) + `<p class="kicker">${thUnitHead(thUnit(v, g.id))}</p>`
      + `<p class="th-panel-meta">${esc(thCountText(v, g.id))}${picked}</p>`
      + thPickedHtml(v, item, picks)
      + thArrangeHtml(g.id)
      + thLeaveHtml(v, g.id, owner)
      + thNoteHtml(v, g);
  }
  html += thNamesHtml(item);
  html += `<h3 class="section-label">${esc(item.kind === 'card' ? t('themes.quote') : t('themes.quotes'))}</h3>`;
  if (!TH.hasQuotes) {
    html += `<p class="fineprint th-restart">${esc(RESTART_LINE)}</p>`;
  } else {
    const rows = thPanelRows(v, item, TH.quotes, TH.sheets);
    for (const r of rows) {
      html += '<section class="th-qrow">';
      if (picks) html += `<ul class="th-qcards">${r.cards.map((k) => `<li>${esc(v.cards[k].text)}</li>`).join('')}</ul>`;
      if (!r.quotes.length) {
        html += `<p class="th-qnone">${esc(r.cards.length > 1 ? t('themes.inspector.no_quotes') : t('themes.inspector.no_quote'))}</p></section>`;
        continue;
      }
      const timed = r.seconds !== null && r.seconds !== undefined;
      html += `<ul class="th-qlist">${r.quotes.map((q) => {
        const on = !!(picks && picks.has(q.key));
        const play = timed
          ? `<button type="button" class="th-play" tabindex="-1" data-play="${escAttr(q.key)}" data-sheet="${escAttr(r.sheet)}" data-at="${r.seconds}" aria-label="${escAttr(t('themes.play.label', { time: r.time }))}" title="${escAttr(t('themes.play.tip', { time: r.time }))}">${PLAY_GLYPH}</button>`
          : '<span class="th-play-none"></span>';
        const tick = picks
          ? `<button type="button" class="th-tick${on ? ' on' : ''}" tabindex="-1" data-pick="${escAttr(q.key)}" aria-pressed="${on}"${thLocked(v) ? ' disabled' : ''} title="${escAttr(t(on ? 'themes.pick.picked_tip' : 'themes.pick.pick_tip', { unit: thUnit(v, item.id) }))}">${TH_TICK_ICON}</button>`
          : '';
        return `<li class="th-q${on ? ' on' : ''}">${play}<div class="th-qbody"><p class="th-qtext">${esc(q.text)}</p>`
          + `<span class="th-time">${esc(q.time || r.time || '')}</span>${thSheetTag(r.sheet)}</div>${tick}</li>`;
      }).join('')}</ul></section>`;
    }
    if (!rows.length) html += `<p class="th-qnone">${esc(t('themes.inspector.no_statements'))}</p>`;
  }
  // a note being written keeps its place, its words and the caret while the panel is drawn afresh
  const box = $('th-gnote');
  const held = noting && box && document.activeElement === box
    ? { start: box.selectionStart, end: box.selectionEnd, top: box.scrollTop } : null;
  const descHeld = thDescHeld();
  TH.noteRedraw = true;
  $('th-panel-body').className = `th-panel-body${item.kind === 'group' ? ` ${thTintClass(thTints(v)[item.id])}` : ''}`;
  $('th-panel-body').innerHTML = html;
  TH.noteRedraw = false;
  const again = held ? $('th-gnote') : null;
  if (again) { again.focus(); again.setSelectionRange(held.start, held.end); again.scrollTop = held.top; }
  thDescRefocus(descHeld);
  thPlayerDraw();
}

/* the description's box as it stands while the panel is drawn afresh, and taken again after, its caret kept */
function thDescHeld() {
  const box = $('th-gdesc');
  return TH.describing && box && document.activeElement === box ? { start: box.selectionStart, end: box.selectionEnd } : null;
}
function thDescRefocus(held) {
  const box = held ? $('th-gdesc') : null;
  if (box) { box.focus(); box.setSelectionRange(held.start, held.end); }
}

/* A theme's picked quotes at the head of its panel, in the order they were picked, so the quotes
   that carry it are read first. They stay with their statements below too, where the ticks are. */
function thPickedHtml(v, item, picks) {
  if (!picks || !picks.size || !TH.hasQuotes) return '';
  const found = new Map();
  for (const r of thPanelRows(v, item, TH.quotes, TH.sheets)) {
    for (const q of r.quotes) if (picks.has(q.key)) found.set(q.key, { q, r });
  }
  const items = [...picks].filter((k) => found.has(k)).map((k) => {
    const { q, r } = found.get(k);
    return `<li class="th-q on"><div class="th-qbody"><p class="th-qtext">${esc(q.text)}</p>`
      + `<span class="th-time">${esc(r.time || '')}</span>${thSheetTag(r.sheet)}</div></li>`;
  });
  return items.length ? `<h3 class="section-label">${esc(t('themes.inspector.picked_quotes'))}</h3><ul class="th-qlist th-picked">${items.join('')}</ul>` : '';
}

/* Auto-arrange, in a label's panel: the same as the small control on the label. `more` is a button that rides on
   its row, a GET's Audit trail, which stays when a revision on view takes the arranging away. */
function thArrangeHtml(id, more = '') {
  const arrange = thLocked(TH.v) ? '' : '<button type="button" class="ghost small th-arrange" tabindex="-1" '
    + `data-arrange="${escAttr(id)}" title="${escAttr(t('themes.arrange.panel_tip'))}">${esc(t('themes.label.arrange_label'))}</button>`;
  return arrange || more ? `<div class="th-leave-row${more ? ' gt-acts' : ''}">${arrange}${more}</div>` : '';
}

/* A theme's note, in its panel under the count and above the quotes: a box of a few lines in the
   board note's style. Cmd + Enter or a click away keeps it, Esc leaves it as it was, and a note kept
   is one step of undo, like a rename. On a revision on view the note shows read-only, and in front
   of a server from before the notes the box is the line saying to restart. */
function thNoteHtml(v, g) {
  const note = thNoteOf(g);
  if (thLocked(v)) return note ? `<p class="th-gnote-read" title="${escAttr(TH_READ_ONLY)}">${esc(note)}</p>` : '';
  if (!TH.notable) return `<p class="fineprint th-restart th-gnote-old">${esc(RESTART_LINE)}</p>`;
  const text = TH.noting && TH.noting.id === g.id ? TH.noting.value : note;
  const unit = thUnit(v, g.id);
  return `<textarea class="th-vedit th-gnote" id="th-gnote" data-note="${escAttr(g.id)}" rows="3" spellcheck="true" `
    + `placeholder="${escAttr(t('themes.note.placeholder', { unit }))}" aria-label="${escAttr(t('themes.note.label', { unit: thUnitHead(unit) }))}">${esc(text)}</textarea>`;
}

/* A label's description in its Inspector, under its title in the head and above the rest, the same words as
   under its title on the board, edited in either place (Adam, 21 October). Enter or a click away keeps it, Esc
   leaves it as it was, and one kept is one step of undo. On a revision on view it shows read-only. */
function thDescHtml(v, g) {
  const desc = thDescOf(g);
  if (thLocked(v)) return desc ? `<p class="th-gdesc-read" title="${escAttr(TH_READ_ONLY)}">${esc(desc)}</p>` : '';
  const text = TH.describing && TH.describing.id === g.id ? TH.describing.value : desc;
  return `<textarea class="th-vedit th-gdesc" id="th-gdesc" data-desc="${escAttr(g.id)}" rows="2" spellcheck="true" `
    + `placeholder="${escAttr(t('themes.label.description'))}" aria-label="${escAttr(t('themes.label.description'))}">${esc(text)}</textarea>`;
}

function thDescStart(box) {
  const id = box.dataset.desc;
  if (TH.describing && TH.describing.id === id) return;
  thDescDone(true);
  if (!TH.live || !thIsGroup(TH.v, id) || thLocked(TH.v)) return;
  TH.describing = { id, value: box.value };
}

function thDescDone(keep) {
  const ed = TH.describing;
  if (!ed) return;
  TH.describing = null;
  const v = TH.v;
  const box = $('th-gdesc');
  const text = box && box.dataset.desc === ed.id ? box.value : ed.value;
  if (keep && v && thIsGroup(v, ed.id)) {
    const before = thSnap(v, TH.removed);
    if (thSetDesc(v, ed.id, text)) {
      thDone(before, thDescStep(thGroup(v, ed.id)), { settle: [], labels: [ed.id] });
      return;
    }
  }
  if (TH.panelOpen) thPanelDraw();
}

/* The box taken: the note is open until it is kept or let go. */
function thNoteStart(box) {
  const id = box.dataset.note;
  if (TH.noting && TH.noting.id === id) return;
  thNoteDone(true);
  if (!TH.live || !thIsGroup(TH.v, id) || thLocked(TH.v)) return;
  TH.noting = { id, value: box.value };
}

/* Kept, with Cmd + Enter or a click away, or let go with Esc. A note that changed is one step of
   undo, and the label then carries its mark. */
function thNoteDone(keep) {
  thStickyBoxDone(keep);
  gtPnDone(keep);
  thDescDone(keep);
  const ed = TH.noting;
  if (!ed) return;
  TH.noting = null;
  const v = TH.v;
  const box = $('th-gnote');
  const text = box && box.dataset.note === ed.id ? box.value : ed.value;
  if (keep && v && thIsGroup(v, ed.id)) {
    const before = thSnap(v, TH.removed);
    if (thSetNote(v, ed.id, text)) {
      // a label that now carries the mark and comes to sit on a card sends the card clear
      thDone(before, thNoteOf(thGroup(v, ed.id)) ? t('themes.step.note_written') : t('themes.step.note_cleared'),
        { settle: [], labels: [ed.id], note: ed.id });
      return;
    }
  }
  if (TH.panelOpen) thPanelDraw();
}

/* Note, in a label's right-click menu: the Inspector open on that label, with the box taken. */
function thNoteOpen(id) {
  if (!TH.live || TH.busy || !thIsGroup(TH.v, id) || thRefuse('note')) return;
  thSelectOnly({ kind: 'group', id });
  TH.lastPick = { kind: 'group', id };
  thInspectorOpen({ kind: 'group', id });
  const box = $('th-gnote');
  if (!box) return;
  box.focus();
  box.setSelectionRange(box.value.length, box.value.length);
}

/* Take out of PET, or of sub-theme when that is what holds it, for a card in one or a sub-theme (Adam,
   20 October, from a tester's feedback): a move, never a bin, so it carries the arrow out and none of the red,
   and the card goes back among those not placed, beside where it stood. */
const thLeaveLabel = (v, owner, parents) => t('themes.leave.label', { unit: thUnit(v, owner, parents) });
function thLeaveHtml(v, id, owner) {
  if (owner === undefined || !thIsGroup(v, owner) || thLocked(v)) return '';
  return '<div class="th-leave-row"><button type="button" class="ghost small btn-out th-leave" tabindex="-1" '
    + `data-leave="${escAttr(id)}" title="${escAttr(t('themes.leave.tip', { name: thLabelShown(thGroup(v, owner).label) }))}">`
    + `${esc(thLeaveLabel(v, owner))}</button>`
    + `<span class="th-leave-from">${esc(thLabelShown(thGroup(v, owner).label))}</span></div>`;
}

/* a tick is an act like any other: one step of undo, and saved with the board */
function thPick(gid, qkey) {
  if (!TH.live || TH.busy || !thIsGroup(TH.v, gid) || thRefuse('pick')) return;
  const before = thSnap(TH.v, TH.removed);
  const on = thTogglePick(TH.v, gid, qkey);
  // a label that now carries the quote's mark may take a line more and grow up onto a card, which goes
  // clear, as a note's mark sends it (17 October, later)
  thDone(before, on ? t('themes.step.picked') : t('themes.step.unpicked'), { settle: [], labels: [gid] });
}

/* ── the panel's player ── */

/* A player of the panel's own, built from the same parts as the turn screen's: the audio element
   as the engine, a play button, the two times and a scrub bar. A quote's play button cues the
   recording of its sheet at its row's timecode and plays, the same button again pauses, and a
   press after that carries on from where it stopped. Another quote jumps there and plays. */
function thAudioReset() {
  const player = $('th-player');
  if (!player) return;
  player.pause();
  player.removeAttribute('src');
  TH.audioSheet = null;
  TH.seekKey = null;
  TH.cueAt = 0;
  $('th-pwrap').hidden = true;
}

function thPlayerDraw() {
  const player = $('th-player');
  const duration = Number.isFinite(player.duration) && player.duration > 0 ? player.duration : 0;
  const at = player.readyState >= 1 ? (player.currentTime || 0) : (TH.cueAt || 0);
  const share = duration ? Math.max(0, Math.min(1, at / duration)) : 0;
  $('th-pelapsed').textContent = timecode(at, timecodesOf(TH.project));
  $('th-ptotal').textContent = duration ? timecode(duration, timecodesOf(TH.project)) : '--:--';
  $('th-pfill').style.width = `${share * 100}%`;
  $('th-pknob').style.left = `${share * 100}%`;
  const playing = !player.paused && !player.ended;
  $('th-pplay').textContent = playing ? PAUSE_GLYPH : PLAY_GLYPH;
  $('th-pplay').setAttribute('aria-label', playing ? t('themes.player.pause') : t('themes.player.play'));
  $('th-pbar').classList.toggle('playing', playing);
  for (const b of document.querySelectorAll('#th-panel-body [data-play], #th-kqpop [data-play]')) {
    const on = playing && b.dataset.play === TH.seekKey;
    b.textContent = on ? PAUSE_GLYPH : PLAY_GLYPH;
    b.classList.toggle('playing', on);
  }
}

/* the recording of a sheet, through the same endpoint the turn screen's player asks. True once it
   is in the player. */
async function thAudioFor(sheet) {
  const player = $('th-player');
  if (TH.audioSheet === sheet && player.getAttribute('src')) return true;
  TH.audioSheet = sheet;
  TH.seekKey = null;
  player.pause();
  player.removeAttribute('src');
  $('th-pwrap').hidden = false;
  $('th-pbar').hidden = true;
  $('th-pnote').textContent = t('themes.player.looking');
  try {
    const data = await api(`/api/audio?${new URLSearchParams({ path: TH.path, sheet })}`);
    if (TH.audioSheet !== sheet) return false;
    if (data.found) {
      player.src = data.url;
      // the recording's offset, which playback adds to every time code (20 October)
      TH.audioOffset = Number(data.offset) || 0;
      $('th-pbar').hidden = false;
      $('th-pnote').textContent = data.name;
      return true;
    }
    $('th-pnote').textContent = data.note || (data.building ? t('themes.player.building') : t('themes.player.none'));
  } catch {
    if (TH.audioSheet === sheet) $('th-pnote').textContent = t('themes.player.none');
  }
  // asked again on the next press, which is when a recording still being built may be there
  TH.audioSheet = null;
  return false;
}

function thPlayToggle() {
  const player = $('th-player');
  if (!player.getAttribute('src')) return;
  if (player.paused || player.ended) {
    const played = player.play();
    if (played && played.catch) played.catch(() => say(t('themes.player.failed')));
  } else {
    player.pause();
  }
}

async function thPlayQuote(key, sheet, seconds) {
  const player = $('th-player');
  if (TH.seekKey === key && TH.audioSheet === sheet && player.getAttribute('src')) { thPlayToggle(); return; }
  if (!(await thAudioFor(sheet))) return;
  const at = Math.max(0, (Number(seconds) || 0) + (TH.audioOffset || 0));
  TH.seekKey = key;
  TH.cueAt = at;
  thPlayerDraw();
  const go = () => {
    if (TH.seekKey !== key) return;  // another quote has asked since
    try { player.currentTime = at; } catch { /* the file is still arriving */ }
    const played = player.play();
    if (played && played.catch) played.catch(() => say(t('themes.player.failed')));
  };
  if (player.readyState >= 1) go();
  else player.addEventListener('loadedmetadata', go, { once: true });
}

function thScrubTo(clientX) {
  const player = $('th-player');
  const box = $('th-pscrub').getBoundingClientRect();
  if (!box.width || !Number.isFinite(player.duration) || !player.duration) return;
  TH.cueAt = Math.max(0, Math.min(1, (clientX - box.left) / box.width)) * player.duration;
  TH.seekKey = null;
  try { player.currentTime = TH.cueAt; } catch { /* the file is still arriving */ }
  thPlayerDraw();
}

/* ── boards ── */

/* The switcher in the bar: the board's name, and the Current board's mark beside it when the board
   on the canvas is the one marked so. */
function thDrawBoard() {
  const name = (TH.meta && TH.meta.name) || '';
  const chosen = !!name && TH.chosen === TH.meta.id;
  $('th-board-name').textContent = name;
  $('th-board-chosen').hidden = !chosen;
  $('th-board').hidden = !name;
  $('th-board-sep').hidden = !name;
  $('th-board').title = chosen ? t('themes.board.tip_current', { name }) : t('themes.board.tip', { name });
  thCountFit();
  // a rename or a note kept shows at the head of the tabs about the board at once
  if (TH.boardOpen) thBoardHead();
}

function thVmenu(open) {
  if (!open && TH.vedit) thVCommit();
  if (open && TH.casemenu) thCasemenu(false);
  TH.vmenu = !!open;
  TH.vedit = null;
  $('th-vmenu').hidden = !open;
  $('th-board').setAttribute('aria-expanded', String(!!open));
  if (open) { thVmenuDraw(); thVmenuPlace(); }
}

function thVmenuPlace() {
  const menu = $('th-vmenu');
  const anchor = $('th-board').hidden ? $('th-case') : $('th-board');
  const box = anchor.getBoundingClientRect();
  menu.style.left = `${Math.max(8, Math.min(box.left - 6, window.innerWidth - menu.offsetWidth - 8))}px`;
  menu.style.top = `${box.bottom + 8}px`;
}

/* Every board by name, the one on the canvas ticked, the Current board with its mark and the word
   Current after its name, each with its note under it. Then, under the name of the board on the
   canvas, what it can do: Rename, Add a note or Edit the note, Duplicate, Mark as current or Unmark
   current, Save a revision and Delete this board. Then, after a hairline and under New, New board.
   Rename and the note open a box in the place of the name or the
   note, and Save a revision a box for its name in its place. */
function thVmenuDraw(said = '') {
  const cur = TH.meta ? TH.meta.id : null;
  const one = TH.boards.length < 2;
  let html = `<p class="section-label th-vhead">${esc(t('themes.board.boards'))}</p>`;
  for (const ver of TH.boards) {
    const on = ver.id === cur;
    const mark = ver.id === TH.chosen
      ? `<span class="th-vchosen" title="${escAttr(t('themes.board.current_tip'))}">${TH_CHOSEN_ICON}<span class="th-vchosen-word">${esc(t('themes.board.current'))}</span></span>` : '';
    const name = on && TH.vedit === 'name'
      ? `<input type="text" class="th-vedit" id="th-vedit-name" value="${escAttr(ver.name)}" spellcheck="false" aria-label="${escAttr(t('themes.board.name_label'))}">`
      : `<span class="th-vline"><span class="th-vlabel">${esc(ver.name)}</span>${thWithAi(ver.with_ai)}${ver.own && typeof tmbOwnMark === 'function' ? tmbOwnMark() : ''}${mark}</span>`;
    const note = on && TH.vedit === 'note'
      ? `<textarea class="th-vedit" id="th-vedit-note" rows="3" spellcheck="true" placeholder="${escAttr(t('themes.board.note_placeholder'))}" aria-label="${escAttr(t('themes.board.note_label'))}">${esc(ver.note || '')}</textarea>`
      : (ver.note ? `<span class="th-vnote" title="${escAttr(ver.note)}">${esc(ver.note)}</span>` : '');
    // the PETs marked complete, with a small tick and the date, on the board it was marked on
    const done = TH.done && ver.id === TH.done.board
      ? `<span class="th-vdone">${TH_TICK_ICON}${esc(t('themes.board.complete', { units: TH.mode === 'gets' ? thGetWord(true) : t('themes.unit.pets') }))}<span class="th-vdone-date">${esc(dayOf(TH.done.at))}</span></span>` : '';
    html += on
      ? `<div class="th-vitem on"><span class="th-vcheck">${TH_TICK_ICON}</span><span class="th-vtext">${name}${done}${note}</span></div>`
      : `<button type="button" class="ghost th-vitem" tabindex="-1" data-switch="${escAttr(ver.id)}"><span class="th-vcheck"></span><span class="th-vtext">${name}${done}${note}</span></button>`;
  }
  const hasNote = !!(TH.meta && TH.meta.note);
  const named = (TH.meta && TH.meta.name) || t('themes.board.this');
  const marked = !!TH.meta && TH.chosen === TH.meta.id;
  // on a board someone else works on, what would change it is greyed out (ownboards: the one writer refuses it)
  const theirs = TH.mode !== 'gets' && typeof tmbTheirsTip === 'function' ? tmbTheirsTip() : '';
  const off = theirs ? ` disabled title="${escAttr(theirs)}"` : '';
  // what the board on the canvas can do, under its own name in the BOARDS heading's style, then a
  // hairline and what makes a new one, under NEW
  html += '<div class="row-menu-rule"></div>'
    + `<p class="section-label th-vhead th-vscope" title="${escAttr(named)}">${esc(named)}</p>`
    // the board in a window of its own, for a second screen (20 October)
    + `<button type="button" class="ghost" tabindex="-1" data-vop="window" title="${escAttr(t('themes.board.window_tip', { name: named }))}">${esc(t('themes.board.window'))}</button>`
    + `<button type="button" class="ghost" tabindex="-1" data-vop="rename"${off}>${esc(t('themes.board.rename'))}</button>`
    + `<button type="button" class="ghost" tabindex="-1" data-vop="note"${off}>${esc(hasNote ? t('themes.board.edit_note') : t('themes.board.add_note'))}</button>`
    + `<button type="button" class="ghost" tabindex="-1" data-vop="duplicate" title="${escAttr(t('themes.board.duplicate_tip', { name: named }))}">${esc(t('themes.board.duplicate'))}</button>`
    + `<button type="button" class="ghost" tabindex="-1" data-vop="choose"${off || ` title="${escAttr(marked
      ? t('themes.board.unmark_tip') : t('themes.board.mark_tip'))}"`}>${esc(marked ? t('themes.board.unmark') : t('themes.board.mark'))}</button>`
    + (TH.vedit === 'revision'
      ? `<div class="th-vrev"><input type="text" class="th-vedit" id="th-vedit-rev" placeholder="${escAttr(t('themes.revision.name_placeholder'))}" spellcheck="true" aria-label="${escAttr(t('themes.revision.name_label'))}">`
        + `<button type="button" class="ghost small" tabindex="-1" data-vop="revision-go">${esc(t('themes.revision.save'))}</button></div>`
      : `<button type="button" class="ghost" tabindex="-1" data-vop="revision"${off || ` title="${escAttr(t('themes.revision.keep_tip'))}"`}>${esc(t('themes.revision.keep'))}</button>`)
    // Send board, to whoever works on this participant, with Working together on (team_board.js)
    + (TH.mode !== 'gets' && typeof tmbMenuItem === 'function' ? tmbMenuItem() : '')
    // on the GETs screen, a card for each sub-theme of the study this board has none of (item 193)
    + (TH.mode === 'gets' && !thTa() ? `<button type="button" class="ghost" tabindex="-1" data-vop="subs" title="${escAttr(t('themes.board.subs_tip'))}">${esc(t('themes.board.subs'))}</button>` : '')
    // and every case's PETs in no GET set out in a row for each participant (19 October, way 2)
    + (TH.mode === 'gets' && !thTa() ? `<button type="button" class="ghost" tabindex="-1" data-vop="bypart" title="${escAttr(GT_BY_TIP)}">${esc(t('themes.board.by_participant'))}</button>` : '')
    + `<button type="button" class="ghost btn-remove" tabindex="-1" data-vop="delete"${off || (one ? ` disabled title="${escAttr(t('themes.board.last_tip'))}"` : '')}>${esc(t('themes.board.delete'))}</button>`
    + '<div class="row-menu-rule"></div>'
    + `<p class="section-label th-vhead">${esc(t('themes.board.new_head'))}</p>`
    // on PETs a new board offers both starts (Adam, 20 October): every statement waiting in the sidebar, or
    // every statement on the canvas as a pile in the middle
    + (TH.mode === 'gets'
      ? `<button type="button" class="ghost" tabindex="-1" data-vop="new" title="${escAttr(t('themes.board.new_tip'))}">${esc(t('themes.board.new'))}</button>`
      : `<button type="button" class="ghost" tabindex="-1" data-vop="new" title="${escAttr(t('themes.board.new_empty_tip'))}">${esc(t('themes.board.new_empty'))}</button>`
        + `<button type="button" class="ghost" tabindex="-1" data-vop="new-canvas" title="${escAttr(t('themes.board.new_canvas_tip'))}">${esc(t('themes.board.new_canvas'))}</button>`);
  // the PETs phase, the case's and no one board's, last after a hairline: Mark PETs complete on the
  // Current board, there only while one is marked, and Reopen PETs once it is marked
  const chosenBoard = TH.boards.find((x) => x.id === TH.chosen);
  const at = TH.done ? whenOf(TH.done.at) : null;
  // the PETs mark is the participant's, so on one someone else works on it is greyed out on every board
  const theirsAll = TH.mode !== 'gets' && typeof tmbTheirsTip === 'function' ? tmbTheirsTip(true) : '';
  const offAll = theirsAll ? ` disabled title="${escAttr(theirsAll)}"` : '';
  if (TH.mode === 'gets') html += gtMenuFoot();
  else html += '<div class="row-menu-rule"></div>' + (TH.done
    ? `<button type="button" class="ghost" tabindex="-1" data-vop="pets-reopen"${offAll || ` title="${escAttr(t(at.time ? (TH.done.name ? 'themes.board.done_tip_time_name' : 'themes.board.done_tip_time') : (TH.done.name ? 'themes.board.done_tip_name' : 'themes.board.done_tip'), { day: at.day, time: at.time, name: TH.done.name }))}"`}>${esc(t('themes.board.reopen'))}</button>`
    : `<button type="button" class="ghost" tabindex="-1" data-vop="pets-done"${offAll || (chosenBoard
      ? ` title="${escAttr(t('themes.board.done_mark_tip', { name: chosenBoard.name }))}"` : ` disabled title="${escAttr(t('themes.board.done_first'))}"`)}>${esc(t('themes.board.done_mark'))}</button>`);
  if (said) html += `<p class="th-vsaid">${esc(said)}</p>`;
  // on GETs the mark of a board marked complete names the GETs, where it is drawn above
  $('th-vmenu').innerHTML = html;
  if (typeof menuRoles === 'function') menuRoles($('th-vmenu'));
  const revBox = $('th-vedit-rev');
  if (revBox) {
    // Enter keeps the revision, under the name typed or none, and Esc leaves the history alone
    revBox.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter') { e.preventDefault(); thVmenu(false); thSaveRevision(revBox.value); }
      else if (e.key === 'Escape') { e.preventDefault(); TH.vedit = null; thVmenuDraw(); }
    });
  }
  const nameBox = $('th-vedit-name');
  if (nameBox) {
    nameBox.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter') { e.preventDefault(); thVSave('name', nameBox.value); }
      else if (e.key === 'Escape') { e.preventDefault(); TH.vedit = null; thVmenuDraw(); }
    });
    nameBox.addEventListener('blur', () => thVSave('name', nameBox.value));
  }
  const noteBox = $('th-vedit-note');
  if (noteBox) {
    noteBox.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter' && MOD(e)) { e.preventDefault(); thVSave('note', noteBox.value); }
      else if (e.key === 'Escape') { e.preventDefault(); TH.vedit = null; thVmenuDraw(); }
    });
    noteBox.addEventListener('blur', () => thVSave('note', noteBox.value));
  }
}

function thVsaid(line) {
  if (TH.vmenu) thVmenuDraw(line); else say(line, 6000);
}

function thVEdit(kind) {
  TH.vedit = kind;
  thVmenuDraw();
  const box = $(kind === 'name' ? 'th-vedit-name' : kind === 'revision' ? 'th-vedit-rev' : 'th-vedit-note');
  if (!box) return;
  box.focus();
  if (kind === 'name') box.select();
  else box.setSelectionRange(box.value.length, box.value.length);
}

/* a box left open when the menu closes keeps what was typed in it, all but a revision's name,
   which only Enter or Save keeps */
function thVCommit() {
  if (TH.vedit === 'revision') return;
  const box = $(TH.vedit === 'name' ? 'th-vedit-name' : 'th-vedit-note');
  if (box) thVSave(TH.vedit, box.value);
}

/* Every op waits for the canvas to be saved first, so the file holds what is on the screen, and
   the canvas takes no act while it is on its way. The board ops go to the route they had before
   there were boards, and a copy and the history to `/api/themes-boards`. A board op ends a
   revision on view first. A server from before either has no such endpoint, and the menu or the
   line says so and does nothing else. */
async function thBoardOp(op, extra = {}, route = TH_OPS_ROUTE) {
  if (!TH.live || TH.busy) return null;
  thTitleDone(true);
  thNoteDone(true);
  if (route === TH_OPS_ROUTE) thViewEnd();
  TH.busy = true;
  try {
    await thFlush();
    if (TH.dirty) { thVsaid(t('themes.unsaved.boards')); return null; }
    return await api(TH.mode === 'gets' ? gtRoute(route) : route, Object.assign({ workbook: TH.path, op }, extra));
  } catch (err) {
    thVsaid(needsRestart(err) ? RESTART_LINE : err.message);
    return null;
  } finally {
    TH.busy = false;
  }
}

/* the names, the notes and the Current board from an op's answer, with the canvas left as it is */
function thTakeBoards(data) {
  TH.boards = (data.versions || []).map((x) => Object.assign({}, x));
  if (Object.prototype.hasOwnProperty.call(data, 'chosen')) TH.chosen = data.chosen || null;
  if (Object.prototype.hasOwnProperty.call(data, 'complete')) TH.done = data.complete || null;
  const mine = TH.boards.find((x) => x.id === TH.meta.id);
  if (mine) Object.assign(TH.meta, { name: mine.name, note: mine.note, updated: mine.updated }, mine.v ? { v: mine.v } : {});
  thDrawBoard();
}

async function thVSave(kind, value) {
  if (TH.vedit !== kind || !TH.meta) return;
  TH.vedit = null;
  const was = kind === 'name' ? TH.meta.name : (TH.meta.note || '');
  const now = kind === 'name' ? String(value).trim().replace(/\s+/g, ' ') : String(value).trim();
  if (now === was || (kind === 'name' && !now)) { if (TH.vmenu) thVmenuDraw(); return; }
  const data = await thBoardOp(kind === 'name' ? 'rename' : 'note',
    kind === 'name' ? { id: TH.meta.id, name: now } : { id: TH.meta.id, note: now });
  if (!data) return;
  thTakeBoards(data);
  if (TH.vmenu) thVmenuDraw();
}

/* a switch writes only which board is current: the one he leaves was saved as he went */
async function thSwitch(id) {
  if (!TH.meta || id === TH.meta.id) { thVmenu(false); return; }
  const data = await thBoardOp('switch', { id });
  if (!data) return;
  thVmenu(false);
  thLoad(data);
}

/* New is every card back in the pile, Duplicate a copy of this one to try another grouping. Both
   go on the canvas at once, with the name open in the menu to be typed over. */
async function thMakeBoard(op) {
  const canvas = op === 'new-canvas';
  if (canvas) op = 'new';
  const data = await thBoardOp(op, op === 'duplicate' ? { id: TH.meta.id } : canvas ? { start: 'canvas' } : {});
  if (!data) return;
  thLoad(data, { fit: op === 'new' });
  if (TH.vmenu) thVEdit('name');
}

/* Mark as current, or Unmark current, in the board menu: the board on the canvas marked as the one
   he is going with, the one to send a supervisor, or the mark taken off. The file keeps it as
   `chosen`, beside `current`, which stays the board on the canvas. Nothing on the canvas changes,
   and a server from before it says to restart. */
async function thChoose() {
  if (!TH.live || !TH.meta) return;
  if (!TH.choosable) { thVsaid(RESTART_LINE); return; }
  const data = await thBoardOp('choose', { id: TH.chosen === TH.meta.id ? null : TH.meta.id });
  if (!data) return;
  thTakeBoards(data);
  if (TH.vmenu) thVmenuDraw();
}

/* Mark PETs complete, or Reopen PETs, at the foot of the board menu: the PETs phase marked complete
   on the Current board, `complete` at the top of the themes file through the board op and never
   the autosave, or the mark taken off. Marking fires the third level of confetti once, the one the
   case-complete card fires, through the app's own. Nothing is locked by it, and a server from
   before it says to restart. */
async function thPetsDone(mark) {
  if (TH.mode === 'gets') { await gtDone(mark); return; }
  if (!TH.live || !TH.meta) return;
  if (!TH.doneable) { thVsaid(RESTART_LINE); return; }
  if (mark && !TH.chosen) return;
  const was = !!TH.done;
  const data = await thBoardOp(mark ? 'complete' : 'reopen');
  if (!data) return;
  thTakeBoards(data);
  if (TH.vmenu) thVmenuDraw();
  if (mark && TH.done && !was) { confetti(3); say(t('themes.board.marked_complete'), 2400); }
  else if (!mark && was) say(t('themes.board.reopened'), 2400);
}

function thAskDelete() {
  if (TH.boards.length < 2) { thVsaid(t('themes.board.last')); return; }
  const v = thLiveV();
  const parents = thParents(v);
  const themes = v.groups.filter((g) => parents[g.id] === undefined).length;
  const placed = thCounts(v).placed;
  const name = TH.meta.name;
  TH.doomed = TH.meta.id;
  $('th-confirm-line').textContent = themes
    ? t('themes.delete.with', { name, held: t('themes.delete.n_pets', { n: themes }), placed: t('themes.delete.n_statements', { n: placed }) })
    : t('themes.delete.empty', { name });
  if (TH.mode === 'gets') {
    $('th-confirm-line').textContent = themes
      ? t('themes.delete.with', { name, held: t('themes.delete.n_gets', { n: themes }), placed: t('themes.delete.n_cards', { n: placed }) })
      : t('themes.delete.empty', { name });
  }
  thVmenu(false);
  show('th-confirm');
  $('th-confirm-go').focus();
}

async function thDeleteGo() {
  const id = TH.doomed;
  TH.doomed = null;
  hide('th-confirm');
  if (!id) return;
  const data = await thBoardOp('delete', { id });
  if (!data) return;
  delete TH.stacks[id];
  if (TH.undoBoard === id) { TH.undoBoard = null; TH.undo = []; TH.redo = []; }
  thLoad(data);
}

/* ── the history ── */

/* A revision's name as the History says it. One the app named carries its kind and slots (themes.revision_mark), so
   it reads in the page's language, whatever language the file was written in. Any other, named by hand or by an
   agent, shows the name it was given. */
const TH_REVISION_SAID = {
  canvas_kept: (s) => t('themes.revision.named.canvas_kept', s),
  reload_kept: (s) => t('themes.revision.named.reload_kept', s),
  before_restoring: (s) => t('themes.revision.named.before_restoring', s),
  before_copy: (s) => t('themes.revision.named.before_copy', s),
  before_copy_revision: (s) => t('themes.revision.named.before_copy_revision', s),
  before_changes: (s) => t('themes.revision.named.before_changes', s),
  statement_edited: (s) => t('themes.revision.named.statement_edited', s),
  statement_edited_bare: (s) => t('themes.revision.named.statement_edited_bare', s),
  brought_in: (s) => t('themes.revision.named.brought_in', s),
  team_board: (s) => t('themes.revision.named.team_board', s),
};
function thRevisionSaid(r) {
  const said = r && r.kind && Object.prototype.hasOwnProperty.call(TH_REVISION_SAID, r.kind) ? TH_REVISION_SAID[r.kind] : null;
  if (!said) return String((r && r.name) || '');
  const slots = Object.assign({}, r.slots || {});
  // a time the name gives (`when_at`, i18nleft3) said in the page's language and formats, as it read when the
  // revision was made, where a revision from before keeps its words
  if (slots.when_at) {
    const made = new Date(r.at);
    slots.when = thWhen(slots.when_at, Number.isNaN(made.getTime()) ? new Date() : made);
  }
  return said(slots);
}

/* Save a revision, from the board menu or the History tab: the board as the file holds it, the
   canvas saved first, under the name typed or none. Nothing on the canvas changes. */
async function thSaveRevision(name) {
  const data = await thBoardOp('revision', { id: TH.meta.id, name: String(name || '').trim() }, TH_BOARDS_ROUTE);
  if (!data) return;
  thTakeBoards(data);
  if (Array.isArray(data.history)) TH.history = data.history;
  const r = data.revision || {};
  say(r.name ? t('themes.revision.saved_named', { board: TH.meta.name, name: thRevisionSaid(r) }) : t('themes.revision.saved_at', { board: TH.meta.name, when: thWhen(r.at) }), 5000);
  if (TH.boardOpen && TH.tab === 'history') {
    const box = $('th-rev-name');
    if (box) box.value = '';
    thBoardDraw();
  }
}

/* The History tab of the sidebar, under the board's name: the board's revisions newest first,
   by day, each with its time, its name or Automatic, and Restore. A click on one shows it on the
   canvas. Save a revision sits at the top, with a box for its name. A name being typed survives the
   list being drawn again. */
function thHistoryDraw() {
  const body = $('th-bpanel-body');
  const typed = $('th-rev-name');
  const keep = typed ? { value: typed.value, focus: document.activeElement === typed } : null;
  let html = '';
  if (TH.history === null) {
    html += `<p class="fineprint th-restart">${esc(RESTART_LINE)}</p>`;
  } else {
    html += `<div class="th-rev-save"><input type="text" class="th-vedit th-rev-name" id="th-rev-name" placeholder="${escAttr(t('themes.revision.name_placeholder'))}" spellcheck="true" aria-label="${escAttr(t('themes.revision.name_label'))}">`
      + `<button type="button" class="ghost small" tabindex="-1" data-rev-save="1">${esc(t('themes.revision.keep'))}</button></div>`;
    if (!TH.history.length) {
      html += `<p class="th-qnone">${esc(t('themes.revision.none'))}</p>`;
    }
    const seen = TH.viewing ? TH.viewing.rev.id : null;
    for (const day of thHistoryDays(TH.history)) {
      html += `<h3 class="section-label th-rev-day">${esc(day.day)}</h3><ul class="th-revs">`;
      for (const r of day.items) {
        const said = thRevisionSaid(r) || (r.auto ? t('themes.revision.automatic') : '');
        html += `<li class="th-rev${r.id === seen ? ' on' : ''}${r.auto ? ' auto' : ''}">`
          + `<button type="button" class="th-rev-view" tabindex="-1" data-rev-view="${escAttr(r.id)}" title="${escAttr(t('themes.revision.show_tip'))}">`
          + `<span class="th-time">${esc(r.time)}</span><span class="th-rev-said">${esc(said)}</span></button>`
          + `<button type="button" class="ghost small" tabindex="-1" data-rev-restore="${escAttr(r.id)}" title="${escAttr(t('themes.revision.restore_tip'))}">${esc(t('themes.revision.restore'))}</button></li>`;
      }
      html += '</ul>';
    }
  }
  body.className = 'th-panel-body th-history';
  body.innerHTML = html;
  const box = $('th-rev-name');
  if (box && keep) {
    box.value = keep.value;
    if (keep.focus) box.focus();
  }
}

/* A revision on view: the canvas shows it dimmed and read-only, the board itself kept aside, with
   the banner over it. The autosave and the revision timer wait, since nothing on it changes. */
async function thViewRevision(rid) {
  if (!TH.live || TH.busy || !TH.meta) return;
  if (TH.viewing && TH.viewing.rev.id === rid) return;
  thTitleDone(true);
  thNoteDone(true);
  thMenuClose();
  const data = await thBoardOp('view', { id: TH.meta.id, revision: rid }, TH_BOARDS_ROUTE);
  if (!data || !TH.live || $('themes').hidden) return;
  const kept = TH.viewing || { live: TH.v, z: TH.z, removed: TH.removed };
  const cards = {};
  for (const c of data.cards) cards[c.key] = Object.assign({}, c);
  TH.v = {
    cards,
    groups: data.groups.map((g) => Object.assign({}, g, { members: g.members.slice() })),
    discarded: data.discarded.slice(),
    picks: JSON.parse(JSON.stringify(data.picks || {})),
    ai: { discarded: Object.assign({}, data.discard_reasons || {}) },
    stickies: Array.isArray(data.stickies) ? data.stickies.map((n) => Object.assign({}, n)) : null,
    stacks: data.stacks && typeof data.stacks === 'object' ? JSON.parse(JSON.stringify(data.stacks)) : {},
    not_same: Array.isArray(data.not_same) ? JSON.parse(JSON.stringify(data.not_same)) : [],
    waits: TH.mode !== 'gets',
    readonly: true,
  };
  thWaitsRead(TH.v);
  TH.viewing = Object.assign(kept, { rev: data.revision });
  TH.z = Object.keys(cards);
  TH.removed = new Set();
  TH.names = null;
  thClearSel();
  thPanelDrop();
  thRender();
  thViewDraw();
}

/* the board itself back on the canvas, with nothing drawn */
function thViewDrop() {
  if (!TH.viewing) return false;
  const was = TH.viewing;
  TH.viewing = null;
  TH.v = was.live;
  TH.z = was.z;
  TH.removed = was.removed;
  return true;
}

/* Back: the board itself on the canvas again, as it was left. */
function thViewEnd() {
  if (!thViewDrop()) return;
  thClearSel();
  thMenuClose();
  thPanelDrop();
  thRender();
  thViewDraw();
}

/* The banner over a revision on view, "Viewing the revision of 12:04", with Restore and Back, and
   the canvas dimmed under it. */
function thViewDraw() {
  const on = !!TH.viewing;
  const stage = thStage();
  if (stage) stage.classList.toggle('th-viewing', on);
  const banner = $('th-viewing');
  if (!banner) return;
  banner.hidden = !on;
  if (!on) { if (TH.boardOpen && TH.tab === 'history') thBoardDraw(); return; }
  const rev = TH.viewing.rev;
  $('th-viewing-line').textContent = t('themes.revision.viewing', { when: thWhen(rev.at) });
  banner.title = thRevisionSaid(rev) || (rev.auto ? t('themes.revision.auto_tip') : t('themes.revision.hand_tip'));
  if (TH.boardOpen && TH.tab === 'history') thBoardDraw();
}

/* Restore: the board as it stands goes into its history first, "Before restoring 12:04", then the
   revision's state is the board. One step of undo puts the board back as it stood. */
async function thRestoreRevision(rid) {
  if (!TH.live || TH.busy || !TH.meta) return;
  const rev = (TH.history || []).find((r) => r.id === rid) || (TH.viewing && TH.viewing.rev) || { at: '' };
  const data = await thBoardOp('restore', { id: TH.meta.id, revision: rid }, TH_BOARDS_ROUTE);
  if (!data || !TH.live || $('themes').hidden) return;
  const before = thSnap(thLiveV(), thLiveRemoved());
  thLoad(data);
  thStep(before, t('themes.step.restored', { when: thWhen(rev.at) }));
  const kept = data.revision && data.revision.name ? thRevisionSaid(data.revision) : '';
  say(kept ? t('themes.revision.restored_kept', { when: thWhen(rev.at), name: kept }) : t('themes.revision.restored', { when: thWhen(rev.at) }), 8000);
}

/* ── copy to board ── */

/* A theme copied to another board, or from a revision on view to the board it belongs to. The
   server does it, so the file stays one piece: the target keeps a revision first, "Before Mornings
   copied from Board 1", and the copy's cards leave their groups there. Onto the board on screen it
   is one step of undo, and the canvas shows it. Onto another, one line says so. */
async function thCopyTo(gid, to) {
  if (!TH.live || TH.busy || !TH.meta) return;
  const g = thGroup(TH.v, gid);
  if (!g) return;
  const extra = { id: TH.meta.id, group: gid, to };
  if (TH.viewing) extra.revision = TH.viewing.rev.id;
  const data = await thBoardOp('copy', extra, TH_BOARDS_ROUTE);
  if (!data || !TH.live || $('themes').hidden) return;
  const copied = data.copied || {};
  const label = copied.label || g.label;
  const target = copied.to_name || ((TH.boards.find((b) => b.id === to) || {}).name) || t('themes.copy.the_board');
  if (to === TH.meta.id) {
    const before = thSnap(thLiveV(), thLiveRemoved());
    thLoad(data);
    thStep(before, t('themes.step.copied_in', { label }));
    say(t('themes.copy.here', { label, target, key: MAC ? t('themes.key.cmd') : t('themes.key.ctrl') }), 8000);
    return;
  }
  thTakeBoards(data);
  say(t('themes.copy.there', { label, target }), 6000);
}

/* ── export ── */

/* The board on the canvas, as a markdown PET draft and as the Proposed PET column of the
   statements CSV, both written beside the progress file. The workbook is only read. A line on the
   canvas then names both files the way the case holds them, Working/<file>, with Show in Finder on
   a Mac. With `word`, the board as a Word document, the IPA book's table of PETs, written
   at the case's root beside the workbook and never over a file there, the line naming it the same
   way. */
async function thExport(word = false) {
  if (!TH.live || TH.busy) return;
  if (word && !TH.wordable) { say(RESTART_LINE, 6000); return; }
  thTitleDone(true);
  thNoteDone(true);
  await thFlush();
  if (TH.dirty) { say(t('themes.unsaved.exported'), 6000); return; }
  try {
    const body = { workbook: TH.path, version: TH.meta.id };
    if (word) Object.assign(body, { op: 'word' }, thIncludesSent(false));
    // Include interviewer notes, under Markdown and CSV (settingsplit, from Settings' Export): the notes in a file
    // of their own beside the CSV, written by the statements' own export first, whose CSV the board's then takes
    // the place of, so the CSV is the board's as it always was
    const notes = !word && $('export-notes') && $('export-notes').checked
      ? await api('/api/export', { path: TH.path, notes: true }) : null;
    const data = await api('/api/themes-export', body);
    // a server from before the case-relative names sends the paths alone, and has no reveal
    const shown = data.shown || (data.paths || []).map((p) => `Working/${fileOf(p)}`);
    if (notes && notes.notes_path) shown.push(`Working/${fileOf(notes.notes_path)}`);
    if (notes && !notes.notes_path) say(t('themes.no_notes'), 6000);
    thExported({ shown, name: (data.version && data.version.name) || TH.meta.name, reveal: !!data.shown,
      word: word && TH.mode === 'pets' });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  }
}

/* the line an export leaves: what was written and where, and Show in Finder on a Mac */
function thExported(info) {
  TH.exported = info || null;
  const box = $('th-exported');
  if (!box) return;
  // the one-time line goes with the note it came in, and never comes with a later one
  if ($('th-once')) $('th-once').remove();
  box.hidden = !info;
  if (!info) return;
  $('th-exported-head').textContent = t('themes.exported', { name: info.name });
  $('th-exported-files').innerHTML = info.shown.map((f) => `<li class="mono">${esc(f)}</li>`).join('');
  $('th-reveal').hidden = !(info.reveal && TH.platform === 'darwin');
  if (info.word) thSupportOnce(info);
}

/* The one-time line (supportcard, 28 October 2026, Adam's moment A and wording 1): after the first Word export of
   PETs ever, the note gets one line under a thin rule, "Idiograph is free. If it helps your work, there are ways
   to support it.", its link opening the Support card. The settings hold the day it first showed, `support_asked`,
   written alone through /api/settings as it shows, so it never shows again, after a restart or in another window,
   and an agent reads it there too. The settings are read afresh each time, and a note closed or replaced before
   they answer gets nothing */
async function thSupportOnce(info) {
  let held = null;
  try { held = await api('/api/settings', { op: 'read' }); } catch { return; }
  if (!held || !held.config || held.config.support_asked || TH.exported !== info || $('th-once')) return;
  const line = document.createElement('p');
  line.className = 'th-once';
  line.id = 'th-once';
  line.innerHTML = t('themes.support.once_html');
  $('th-exported').appendChild(line);
  const now = new Date();
  const day = [now.getFullYear(), now.getMonth() + 1, now.getDate()].map((n, i) => String(n).padStart(i ? 2 : 4, '0')).join('-');
  try { await api('/api/settings', { support_asked: day }); } catch { /* a server from before it keeps nothing */ }
}

async function thReveal() {
  if (!TH.exported || !TH.exported.shown.length) return;
  try {
    await api('/api/themes-export', { workbook: TH.path, op: 'reveal', version: TH.meta.id, file: TH.exported.shown[0] });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  }
}

/* The export control opens a small menu under it, in the row menu's paper, the part for the view
   shown (1 November 2026, exportA): in Table view The table, Print, Save as PDF, Microsoft Word and
   Markdown and CSV, the ticks and PET labels, and on the canvas The canvas, Print, the canvas on one
   landscape page in a tab of its own, Save as PDF and Save as an image (thCanvasOut). Esc closes it,
   and so does a click anywhere else. */
function thXmenu(open) {
  TH.xmenu = !!open && TH.live;
  const menu = $('th-xmenu');
  if (!menu) return;
  menu.hidden = !TH.xmenu;
  $('th-export').setAttribute('aria-expanded', String(TH.xmenu));
  if (!TH.xmenu) return;
  // the view's own outputs alone: the table's with its ticks in Table view, the canvas's on the canvas (exportA)
  const table = TH.face === 'table';
  for (const part of menu.querySelectorAll('[data-xpart]')) part.hidden = (part.dataset.xpart === 'table') !== table;
  thLabelsDraw();
  thIncludesDraw();
  const box = $('th-export').getBoundingClientRect();
  menu.style.left = `${Math.max(8, Math.min(box.right - menu.offsetWidth, window.innerWidth - menu.offsetWidth - 8))}px`;
  menu.style.top = `${box.bottom + 8}px`;
}

/* PET labels, at the foot of the export menu: the book's letters, A, A1, A1.1, or numbers, PET 1,
   PET 1a, 1a.1, the way the Word document, the print view and the PET draft label the PETs of every
   case of this case's project. A press saves `pet_labels` in the project file at once, every other
   key kept, and the menu stays open on the choice. The demo's are fixed, the letters. A server from
   before it sends no `pet_labels`, and a press says to restart. */
const thLabelsOf = (p) => (p && p.pet_labels === 'numbers' ? 'numbers' : 'letters');

function thLabelsDraw() {
  const box = $('th-xlabels');
  if (!box) return;
  const p = TH.project;
  box.querySelectorAll('[data-labels]').forEach((b) => {
    const on = b.dataset.labels === thLabelsOf(p);
    b.classList.toggle('on', on);
    b.setAttribute('aria-checked', String(on));
    b.disabled = !p || !!p.demo;
  });
}

async function thLabels(value) {
  const p = TH.project;
  if (!TH.live || !p || p.demo || thLabelsOf(p) === value) return;
  try {
    const data = await api('/api/project', { path: TH.path, pet_labels: value });
    if (!data.project || !data.project.pet_labels) { say(RESTART_LINE, 6000); return; }
    TH.project = Object.assign({}, p, { pet_labels: data.project.pet_labels });
    // the Table view's letters follow at once
    thTableDraw();
    if (typeof S !== 'undefined' && S.data && S.data.project && (S.data.project.id || '') === (p.id || '')) {
      S.data.project.pet_labels = data.project.pet_labels;
    }
    thLabelsDraw();
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  }
}

/* Include not placed and Include statements set aside, in the export menu: whether the
   table of PETs, Table and Word, puts Not placed and the bin at its end (Adam, 18 October). Both off
   on a new install. A tick saves at once in the settings, every other key kept, and the menu stays
   open. The print view carries the same ticks and saves to the same keys. Include stacked
   statements, the third, puts the statements stacked under a top beneath it (19 October). For
   sending, the fourth, names the PDF and the Word document by the case alone and leaves the board's
   name off the page (Adam, 19 October), and the GETs print card carries it too, on the same key. */
const TH_INCLUDES = { export_not_placed: 'unplaced', export_binned: 'binned', export_stacked: 'stacked',
  export_for_sending: 'sending', export_descriptions: 'descriptions' };
// Descriptions, the one tick on on a new install (Adam, 21 October)
const TH_INCLUDES_ON = ['export_descriptions'];
const thIncluded = (key) => (TH_INCLUDES_ON.includes(key) ? !(TH.config && TH.config[key] === false) : !!(TH.config && TH.config[key]));

/* the two ticks as the settings hold them, and the same two as the print view's query or the Word
   export's body sends them, so an export just after a tick never waits on its save */
function thIncludesDraw() {
  document.querySelectorAll('#th-xmenu [data-include], #gt-print [data-include]').forEach((box) => { box.checked = thIncluded(box.dataset.include); });
  // the GETs hold no stacks, so Include stacked statements is the PETs screen's alone
  const stacked = $('th-inc-stacked');
  if (stacked) stacked.closest('label').hidden = TH.mode === 'gets';
}
function thIncludesSent(asQuery) {
  const out = {};
  for (const [key, name] of Object.entries(TH_INCLUDES)) out[name] = asQuery ? (thIncluded(key) ? '1' : '0') : thIncluded(key);
  return out;
}

async function thInclude(key, value) {
  if (!TH.config) TH.config = {};
  TH.config[key] = value;
  if (typeof S !== 'undefined') {
    if (S.data && S.data.config) S.data.config[key] = value;
    if (S.libConfig) S.libConfig[key] = value;
  }
  try {
    const data = await api('/api/settings', { [key]: value });
    if (!data.config || data.config[key] === undefined) say(RESTART_LINE, 6000);
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  }
}

/* The print view of the board on the canvas: a page the server renders from the board as the file
   holds it, in a tab of its own, which opens the print dialog itself, so Save as PDF is one step.
   A save still to go is written first. A server from before it says to restart. */
async function thPrint() {
  thXmenu(false);
  if (!TH.live || !TH.meta || TH.busy) return;
  if (!TH.printable) { say(RESTART_LINE, 6000); return; }
  thTitleDone(true);
  thNoteDone(true);
  // the table is the board's Table view since 19 October, so this prints it, the dialog opening at once
  const url = `/themes/print?${new URLSearchParams({ workbook: TH.path, board: TH.meta.id, auto: '1', ...thIncludesSent(true), ...thWhere() })}`;
  const blocked = t('themes.print.blocked');
  // the tab opens on the press, which is what the browser allows, and the page goes in once saved
  const tab = window.open(TH.dirty || TH.chain || TH.saveTimer ? 'about:blank' : url, '_blank');
  if (!tab) { say(blocked, 8000); return; }
  if (!TH.dirty && !TH.chain && !TH.saveTimer) return;
  await thFlush();
  if (TH.dirty) { tab.close(); say(t('themes.unsaved.printed'), 6000); return; }
  tab.location.href = url;
}

/* Export as PDF (31 October 2026, pdfexport, Adam: Export should offer PDF, not Print and Save as PDF): the table
   of PETs as a PDF beside the workbook, where the Word document goes and named as the print view names it. Since 9
   November 2026 (typst5, Adam: Typst for every PDF, no fallback) the server makes it with Typst and writes it
   (`/api/themes-export`'s `pdf`), the same in the window on every computer and in a browser's tab, and the line
   after names it as Word's does, with Show in Finder on a Mac. When it cannot be made the line says why, in the
   catalogue's plain words, and nothing is written. A save still to go is written first. */
async function thPdf() {
  if (!TH.live || !TH.meta || TH.busy) return;
  if (!TH.printable) { say(RESTART_LINE, 6000); return; }
  thTitleDone(true);
  thNoteDone(true);
  await thFlush();
  if (TH.dirty) { say(t('themes.unsaved.exported'), 6000); return; }
  let made = null;
  try {
    made = await api('/api/themes-export', { workbook: TH.path, version: TH.meta.id, op: 'pdf', ...thIncludesSent(false), ...thWhere() });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : (err.message || t('themes.pdf.failed')), 9000);
    return;
  }
  // a server from before it names no file
  if (!made || !made.path) { say(RESTART_LINE, 6000); return; }
  thExported({ shown: made.shown, name: (made.version && made.version.name) || TH.meta.name, reveal: true, word: false });
}

/* ── Canvas and Table: two views of one board (19 October) ── */

/* Adam's choice of 18 October, from a drawing: the PETs and the GETs boards each have Canvas and Table
   on their bar, two views of one board, always in step. The table is the book's table of PETs (Box
   5.6), PETs, sub-PETs and each statement with its own quote, or on GETs the GET table, drawn from
   the board on the page whenever the canvas draws, so it is never out of date. Under it the canvas
   stays laid out, unseen, so every measure the canvas takes holds while the table shows, and a change
   made in either is the other's at once.
   Order is read from where things stand on the canvas, as the exports and an agent's `order` read it:
   the PETs top to bottom and left to right, labels whose tops sit within a card's height of the first
   in a row sharing it, and inside a label its statements and its labels the same way, within half a
   card's height, a label by its frame's corner. Each level is lettered in that order, A, A1, A1.1, or
   PET 1, PET 1a, 1a.1 in a project set to numbers, so a letter follows its place. A reorder in the
   table goes through the server's `themes.reorder`, the one `board apply` runs for an agent's `order`,
   which sets the order by moving each item into the place of the one that read there before, so the
   canvas moves its cards to match. A rename and a move between labels are the canvas's own acts. Each
   is one step of the board's undo and saved as the canvas saves. The statements' words are read-only
   here: they are written on the statements screen. Which view a board shows is kept in the browser,
   by its screen, its case or project and its id, across a restart. */
const TH_FACE_KEY = 'idiograph-board-face';
const TH_TABLE_GRIP = '<svg viewBox="0 0 12 16" fill="currentColor" aria-hidden="true" focusable="false"><circle cx="3.5" cy="3" r="1.3"/><circle cx="8.5" cy="3" r="1.3"/><circle cx="3.5" cy="8" r="1.3"/><circle cx="8.5" cy="8" r="1.3"/><circle cx="3.5" cy="13" r="1.3"/><circle cx="8.5" cy="13" r="1.3"/></svg>';
const TH_TABLE_TIP = t('themes.table.grip_tip');

/* the place a board's view is kept under: the screen, the case's workbook or the GETs' project, and the board */
const thFaceKey = (mode, path, board) => `${mode}|${path}|${board}`;

function thFaceStored(mode, path, board) {
  try {
    const held = JSON.parse(localStorage.getItem(TH_FACE_KEY) || '{}') || {};
    return held[thFaceKey(mode, path, board)] === 'table' ? 'table' : 'canvas';
  } catch { return 'canvas'; }
}

function thFaceKeep(mode, path, board, face) {
  try {
    const held = JSON.parse(localStorage.getItem(TH_FACE_KEY) || '{}') || {};
    const key = thFaceKey(mode, path, board);
    if (face === 'table') held[key] = 'table'; else delete held[key];
    localStorage.setItem(TH_FACE_KEY, JSON.stringify(held));
  } catch { /* a private window keeps it for the page alone */ }
}

/* A board on the page, from an open or a switch: the view it was left in. */
function thFaceRestore() {
  if (!TH.meta) return;
  thFace(thFaceStored(TH.mode, TH.path, TH.meta.id), false);
}

/* Canvas or Table, from the switch or T: the switch drawn, the canvas's own tools put away while the
   table shows, the table drawn, and the choice kept for this board. A title open in either goes first. */
function thFace(face, keep = true) {
  const table = face === 'table';
  if (table !== (TH.face === 'table')) { thTitleDone(true); thTableTitleDone(true); thMenuClose(); }
  TH.face = table ? 'table' : 'canvas';
  const sw = $('th-faces');
  let turned = false;
  if (sw) {
    turned = sw.hidden === TH.live;
    sw.hidden = !TH.live;
    for (const b of sw.querySelectorAll('[data-face]')) {
      const on = b.dataset.face === TH.face;
      b.classList.toggle('on', on);
      b.setAttribute('aria-checked', String(on));
    }
  }
  $('themes').classList.toggle('table-face', table);
  $('th-table').hidden = !table;
  // the toolbar holds the switch after Auto-saved (26 October 2026), so its tools give way again when it comes or
  // goes, and the table keeps the palette (20 October) and the status bar's counts
  thCountFit();
  if (turned) thPaletteFit();
  thCorners();
  if (table) thTableDraw();
  // the map measured again on the way back, since a board opened in the table measured it with its tools hidden
  else if (TH.v) { thMeasure(); thPlace(); thMapPlace(); }
  if (keep && TH.meta) thFaceKeep(TH.mode, TH.path, TH.meta.id, TH.face);
}

/* the table drawn on the next frame after the canvas has, once however often it draws in that frame */
function thTableSoon() {
  if (TH.face !== 'table' || TH.tableSoon) return;
  TH.tableSoon = requestAnimationFrame(() => { TH.tableSoon = 0; thTableDraw(); });
}

/* A letter for a count, a for the first, z for the twenty-sixth, then aa, as the server's sub_letter. */
function thSubLetter(n) {
  let out = '';
  while (n > 0) {
    const r = (n - 1) % 26;
    out = String.fromCharCode(97 + r) + out;
    n = Math.floor((n - 1) / 26);
  }
  return out;
}

/* The label of the `i`th item, from 1, at `depth`, under `stem`, as the server's pet_numbers gives it:
   `mark` shown, and `inner` what its own items are numbered under. */
function thTableCode(depth, i, stem, letters) {
  if (letters) {
    const mark = depth === 0 ? thSubLetter(i).toUpperCase() : depth === 1 ? `${stem}${i}` : `${stem}.${i}`;
    return { mark, inner: mark };
  }
  if (depth === 0) return { mark: `PET ${i}`, inner: String(i) };
  if (depth === 1) return { mark: `PET ${stem}${thSubLetter(i)}`, inner: `${stem}${thSubLetter(i)}` };
  return { mark: `${stem}.${i}`, inner: `${stem}.${i}` };
}

/* a heading's label and title, a full stop after a PET's label and a sub-theme's and none after a
   group's, which carries one already, as the server's numbered */
const thTableHead = (code) => (code.includes('.') ? code : `${code}.`);

/* The board as the table sets it out, no DOM in it: each PET in canvas order with its code, its title,
   its note and what it holds in the order it reads, a statement by its key and a label as a node of
   its own, at any depth, and `loose`, the statements in no PET in transcript order. `layout` is the
   canvas's, for where a sub-theme's frame sits among the cards. */
function thTableTree(v, layout, letters = true, sheets = []) {
  const parents = thParents(v);
  const tops = gtCanvasOrder(v.groups.filter((g) => parents[g.id] === undefined));
  const walk = (gid, depth, i, stem, seen) => {
    const code = thTableCode(depth, i, stem, letters);
    const g = thGroup(v, gid);
    const items = [];
    let n = 0;
    for (const m of thThemeOrder(v, gid, layout)) {
      if (thIsGroup(v, m)) {
        if (seen.has(m)) continue;
        n += 1;
        items.push({ kind: 'label', node: walk(m, depth + 1, n, code.inner, new Set([...seen, m])) });
      } else if (thOnCanvas(v, m)) items.push({ kind: 'statement', key: m });
    }
    return { id: gid, code: code.mark, title: thLabelShown(g.label), note: thNoteOf(g), depth, items };
  };
  const place = (s) => { const at = (sheets || []).indexOf(s); return at < 0 ? (sheets || []).length : at; };
  const loose = Object.keys(v.cards).filter((k) => (thOnCanvas(v, k) || thWaiting(v, k)) && parents[k] === undefined)
    .sort((a, b) => place(v.cards[a].sheet) - place(v.cards[b].sheet) || (v.cards[a].row || 0) - (v.cards[b].row || 0)
      || (v.cards[a].line || 0) - (v.cards[b].line || 0));
  return { pets: tops.map((gid, i) => walk(gid, 0, i + 1, '', new Set([gid]))), loose };
}

/* What reads directly under a label, or with none the labels at the top, in the order the table sets
   them out: what a reorder there is counted among. */
function thTableSiblings(v, layout, under) {
  if (!under) {
    const parents = thParents(v);
    return gtCanvasOrder(v.groups.filter((g) => parents[g.id] === undefined));
  }
  return thThemeOrder(v, under, layout).filter((m) => thIsGroup(v, m) || thOnCanvas(v, m));
}

/* `items` with `id` taken out and set back in at `at`, the place among the others */
function thTableMoved(items, id, at) {
  const rest = items.filter((m) => m !== id);
  const i = Math.max(0, Math.min(rest.length, at));
  return rest.slice(0, i).concat([id], rest.slice(i));
}

/* The places a reorder came back with, laid on the board: each card, label and sticky note it names.
   False on a revision on view. */
function thOrderLand(v, data) {
  if (!v || !data || thLocked(v)) return false;
  for (const [key, at] of Object.entries(data.cards || {})) {
    if (v.cards[key] && at) { v.cards[key].x = Math.round(at.x); v.cards[key].y = Math.round(at.y); }
  }
  for (const g of v.groups) {
    const at = (data.groups || {})[g.id];
    if (at) { g.x = Math.round(at.x); g.y = Math.round(at.y); }
  }
  for (const n of thStickies(v)) {
    const at = (data.notes || {})[n.id];
    if (at) { n.x = Math.round(at.x); n.y = Math.round(at.y); }
  }
  return true;
}

/* A statement, or on GETs a card, moved from the table into the label `to`, as a drop on its title
   strip on the canvas moves it: it joins `to`, comes in under what `to` holds, and the canvas settles
   so nothing overlaps. False when it cannot join. */
function thTableJoin(v, keys, to) {
  keys = (Array.isArray(keys) ? keys : [keys]).filter((k) => thOnCanvas(v, k));
  if (thLocked(v) || !thIsGroup(v, to) || !keys.length) return false;
  const was = thFileBoxes();
  const at = TH.layout && TH.layout[to];
  const joined = thJoin(v, keys, to);
  if (!joined.length) return false;
  // several come in one under another, in the order they read in the table
  let y = at && at.body ? at.body.y + at.body.h + TH_MARGIN : at && at.label ? at.label.y + at.label.h + TH_GAP : null;
  const x = at && at.body ? at.body.x : at && at.label ? at.label.x : null;
  for (const key of joined) {
    const c = v.cards[key];
    if (y === null) continue;
    c.x = Math.round(x);
    c.y = Math.round(y);
    y += ((TH.sizes || {})[key] || TH_CARD).h + TH_MARGIN;
  }
  thRender();
  if (thInFile(() => thSettle(v, thSize, joined, was, [], TH_PASSES, false))) thPlace();
  return true;
}

/* An order set from the table, `items` under the label `under` or under none the PETs (the GETs on the
   GETs board), with `move` first when statements go into another label, { keys, to } (or one, { key, to }),
   the rows dragged together coming in together: the board as
   the page holds it goes to the server's reorder, the places that come back land on the canvas, and
   the whole of it is one step of undo, saved as the canvas saves. A failure puts back what moved and
   says one line. */
async function thTableOrder(under, items, move = null) {
  if (!TH.live || TH.busy || !TH.v || !TH.meta || thRefuse('move')) return false;
  const v = TH.v;
  const path = TH.path;
  const board = TH.meta.id;
  const before = thSnap(v, TH.removed);
  const from = thSpots(v);
  const moving = move ? (move.keys || [move.key]) : [];
  if (move && !thTableJoin(v, moving, move.to)) return false;
  const heights = {};
  for (const [key, s] of Object.entries(TH.sizes || {})) if (v.cards[key] && s && s.h > 0) heights[key] = Math.round(s.h);
  TH.busy = true;
  let data = null;
  let said = '';
  try {
    data = await api('/api/board-order', { workbook: path, gets: thGets(), version: thBody(v, TH.meta),
      under: under || null, items, heights });
  } catch (err) {
    said = needsRestart(err) ? RESTART_LINE : err.message;
  } finally {
    TH.busy = false;
  }
  if (TH.path !== path || !TH.meta || TH.meta.id !== board || TH.v !== v) return false;
  if (said || !data) {
    if (move) { TH.removed = thPut(v, before); thRender(); }
    say(said || RESTART_LINE, 6000);
    return false;
  }
  thOrderLand(v, data);
  if (move) thAck(moving);
  thRender();
  thEase(from);
  thStep(before, move ? t('themes.step.moved_in_table') : t('themes.step.reordered_in_table'));
  thSoon();
  if (move) thMomentum(before);
  return true;
}

/* ── the table drawn ── */

/* a statement's own quote, the one at its place among its row's, without the marks the workbook
   keeps round it, as the print view takes it */
function thOwnQuote(key) {
  const held = (TH.quotes || {})[thRowOf(key)];
  const q = held && (held.quotes || []).find((x) => x.key === key);
  let text = String((q && q.text) || '').trim();
  const marks = ['"“”', "'‘’"];
  while (text.length >= 2 && marks.some((m) => m.includes(text[0]) && m.includes(text[text.length - 1]))) text = text.slice(1, -1).trim();
  return text;
}

const thTableGrip = (what) => `<button type="button" class="tb-grip" data-tgrip="1" title="${escAttr(TH_TABLE_TIP)}" aria-label="${escAttr(t('themes.table.move', { what }))}">${TH_TABLE_GRIP}</button>`;

/* a row's ⋯, which opens the row's menu, the one a right click opens, as the canvas card's own does */
const thTableMore = () => `<button type="button" class="tb-more" data-tmore="1" tabindex="-1" title="${escAttr(t('themes.more'))}" aria-label="${escAttr(t('themes.more'))}">&#8943;</button>`;

/* `tb-sel` on a row the board's selection holds, the canvas's selection and the table's one and the same */
const thTableSelCls = (kind, id) => ((kind === 'label' ? TH.sel.groups : TH.sel.cards).has(id) ? ' tb-sel' : '');

/* One statement as a row: its grip, its words and where it is, and its own quote. A stack's top
   stands for it, with how many are stacked under it, a button that shows the stack under it as S does
   on the canvas, and shown, each statement under it a row of its own with no grip, `under`. */
function thTableStatement(v, key, parent, under = false) {
  const c = v.cards[key];
  const where = [c.sheet, c.time].filter(Boolean).join(', ');
  const quote = thOwnQuote(key);
  const stacked = !under && typeof thStackOf === 'function' ? thStackOf(v, key) : [];
  const open = stacked.length && TH.opened && TH.opened.has(key);
  let html = `<div class="tb-st${under ? ' tb-under' : ''}${thTableSelCls('statement', key)}" data-trow="${escAttr(key)}" data-tkind="${under ? 'under' : 'statement'}" data-tparent="${escAttr(parent || '')}">`
    + (under ? '<span class="tb-grip tb-nogrip" aria-hidden="true"></span>' : thTableGrip(t('themes.table.this_statement')))
    + `<div class="tb-cols"><p class="tb-text">${esc(c.text)}${where ? ` <span class="tb-ref">(${esc(where)})</span>` : ''}`
    + `${stacked.length ? ` <button type="button" class="tb-stacked" data-tstack="${escAttr(key)}" aria-expanded="${open ? 'true' : 'false'}" title="${escAttr(open ? t('themes.stack.again') : t('themes.stack.show'))}">${esc(t('themes.stack.count', { n: stacked.length }))}</button>` : ''}`
    + `${c.missing ? ` <span class="tb-gone">${esc(t('themes.table.gone'))}</span>` : ''}${under ? '' : thTablePairHtml(v, key)}</p>`
    + `<p class="tb-quote">${quote ? esc(`‘${quote}’`) : ''}</p></div>${thTableMore()}</div>`;
  if (open) html += stacked.filter((k) => v.cards[k]).map((k) => thTableStatement(v, k, parent, true)).join('');
  return html;
}

/* A statement's close pairs in the Table view, as the canvas's lines link them: a link mark for each, with
   how far apart, which a click opens the pair's menu from, and the pointer on it lights the other row. */
const TH_LINK_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="2.5" y="8" width="7" height="8" rx="2"/><rect x="14.5" y="8" width="7" height="8" rx="2"/><path d="M9.5 12h5"/></svg>';
function thTablePairHtml(v, key) {
  if (!thCloseOn() || TH.mode === 'gets') return '';
  const pairs = (TH.pairs || []).map((p, i) => [p, i]).filter(([p]) => p.a === key || p.b === key);
  return pairs.map(([p, i]) => {
    const other = p.a === key ? p.b : p.a;
    return ` <button type="button" class="tb-pair${TH.pairAt === thPairId(p) ? ' cur' : ''}" tabindex="-1" data-tpair="${i}" data-tother="${escAttr(other)}" `
      + `title="${escAttr(t('themes.table.close_to', { name: thPairName(v, other, key), apart: thPairWords(p).toLowerCase() }))}">${TH_LINK_ICON}<span>${esc(thPairWords(p))}</span></button>`;
  }).join('');
}

/* a label's heading, its title a button that opens it in a box in place */
function thTableHeadHtml(v, node, extra = '') {
  const ed = TH.tedit && TH.tedit.id === node.id;
  const unit = thUnit(v, node.id);
  const named = t('themes.table.title_label', { unit: thUnitHead(unit) });
  const title = ed
    ? `<input type="text" class="th-title-edit tb-title-box" id="tb-title-box" value="${escAttr(TH.tedit.value)}" spellcheck="true" `
      + `placeholder="${escAttr(named)}" aria-label="${escAttr(named)}" autocomplete="off" data-gramm="false">`
    : `<button type="button" class="tb-title" data-ttitle="${escAttr(node.id)}" title="${escAttr(t('themes.table.rename_tip'))}">${esc(node.title)}</button>`;
  // its description under its title, inside the heading's band, whole (21 October)
  const desc = thDescOf(thGroup(v, node.id));
  return `<div class="tb-head${desc ? ' tb-described' : ''}">${thTableGrip(t('themes.table.the_unit', { unit, title: node.title }))}`
    + (node.code ? `<span class="tb-code">${esc(thTableHead(node.code))}</span>` : '')
    + `${title}${extra}${ed ? '' : thTableMore()}</div>${desc ? `<p class="tb-desc">${esc(desc)}</p>` : ''}`;
}

function thTableNode(v, node, tints, parent) {
  const cls = node.depth === 0 ? 'tb-pet' : `tb-label${node.depth > 1 ? ' deep' : ''}`;
  let html = `<section class="${cls} ${thTintClass(tints[node.id])}${thTableSelCls('label', node.id)}" data-trow="${escAttr(node.id)}" data-tkind="label" data-tparent="${escAttr(parent || '')}">`
    + thTableHeadHtml(v, node, `<span class="tb-count">${esc(thCountText(v, node.id))}</span>`)
    + (node.note ? `<p class="tb-note">${esc(node.note)}</p>` : '')
    + `<div class="tb-body" data-tbody="${escAttr(node.id)}">`;
  for (const it of node.items) html += it.kind === 'label' ? thTableNode(v, it.node, tints, node.id) : thTableStatement(v, it.key, node.id);
  return `${html}</div></section>`;
}

/* The Table view drawn afresh from the board on the page, its scroll and a title open in it kept. Print
   and Word at its top right do what Export does, the print view and the Word document from the board
   as saved, so the export's ticks rule them as they rule Export. */
function thTableDraw() {
  const box = $('th-table');
  if (!box || TH.face !== 'table') return;
  // a row on its way, or a title open, is never drawn from under him: the next draw after it does
  if (TH.tdrag && TH.tdrag.moved) return;
  if (TH.tedit && $('tb-title-box')) return;
  const v = TH.v;
  const note = $('gt-rnote-box');
  const noting = note && document.activeElement === note ? { start: note.selectionStart, end: note.selectionEnd } : null;
  const typing = $('tb-title-box');
  if (typing && TH.tedit) TH.tedit.value = typing.value;
  const caret = typing && document.activeElement === typing ? { start: typing.selectionStart, end: typing.selectionEnd } : null;
  const focused = document.activeElement && box.contains(document.activeElement) && document.activeElement.closest('[data-trow]');
  const keepFocus = TH.tfocus || (focused && !typing ? { id: focused.dataset.trow, grip: !!document.activeElement.closest('.tb-grip') } : null);
  TH.tfocus = null;
  const top = box.scrollTop;
  box.classList.toggle('tb-locked', !v || thLocked(v));
  if (!v || !TH.meta) { box.innerHTML = ''; return; }
  const name = TH.meta.name || '';
  // a thematic analysis project's table of themes goes to Word too, as a table of PETs does (taword)
  const acts = thGets()
    ? `<button type="button" class="ghost small" data-tact="gprint" title="${escAttr(t('themes.gets.export_tip'))}">${esc(t('themes.table.print'))}</button>`
      + (thTa() && !TH.lpets ? `<button type="button" class="ghost small" data-tact="gword" title="${escAttr(t('themes.gets.word_tip'))}">${esc(t('themes.table.word'))}</button>` : '')
    : `<button type="button" class="ghost small" data-tact="print" title="${escAttr(t('themes.table.print_tip'))}">${esc(t('themes.table.print'))}</button>`
      + `<button type="button" class="ghost small" data-tact="word" title="${escAttr(t('themes.table.word_tip'))}">${esc(t('themes.table.word'))}</button>`;
  // on a PETs board the participant heads the table, the table's name smaller under it, as the print and Word do (Adam, 20 October)
  const who = thGets() ? '' : thCanvasTitle(thCaseLabel());
  const titles = who
    ? `<div class="tb-titles"><h2 class="tb-heading tb-who-head">${esc(who)}</h2><p class="tb-table-name">${esc(t('themes.table.name'))}</p></div>`
    : `<h2 class="tb-heading">${esc(thGets() ? t('themes.table.get_name', { unit: thGetWord() }) : t('themes.table.name'))}</h2>`;
  let html = `<div class="tb-page"><div class="tb-top">${titles}`
    + `<span class="tb-sub">${esc(name)}</span><span class="rail-grow"></span><span class="tb-acts">${acts}</span></div>`;
  html += thGets() ? (thTa() && !TH.lpets && !TH.lgets ? gtTableTa(v) : gtTableFace(v)) : thTablePets(v);
  box.innerHTML = `${html}<div class="tb-line" id="tb-line" hidden></div></div>`;
  box.scrollTop = top;
  const again = $('tb-title-box');
  const noteAgain = $('gt-rnote-box');
  if (again) {
    again.focus();
    const at = caret || { start: 0, end: again.value.length };
    again.setSelectionRange(at.start, at.end);
  } else if (noteAgain && (noting || (TH.rowEdit && TH.rowEdit.focus))) {
    noteAgain.focus();
    const at = noting || { start: noteAgain.value.length, end: noteAgain.value.length };
    noteAgain.setSelectionRange(at.start, at.end);
    TH.rowEdit.focus = false;
  } else if (keepFocus) {
    const row = [...box.querySelectorAll('[data-trow]')].find((el) => el.dataset.trow === keepFocus.id);
    const el = row && (keepFocus.grip ? row.querySelector('.tb-grip') : row.querySelector('.tb-title, .tb-grip'));
    if (el) el.focus({ preventScroll: false });
  }
}

function thTablePets(v) {
  const tree = thTableTree(v, TH.layout || {}, thLabelsOf(TH.project) === 'letters', TH.sheets);
  const tints = thTints(v);
  let html = '<div class="tb-pets" data-tbody="">';
  if (!tree.pets.length) html += `<p class="tb-none">${esc(t('themes.table.no_pets'))}</p>`;
  for (const node of tree.pets) html += thTableNode(v, node, tints, '');
  html += '</div>';
  // Not placed stands whenever the board has PETs, so a row can be dragged back to it, empty or not
  if (tree.loose.length || tree.pets.length) {
    html += `<div class="tb-rest"><p class="tb-rest-head">${esc(t('themes.table.not_placed', { n: tree.loose.length }))}</p><div class="tb-loose" data-tbody="${TH_TABLE_LOOSE}">`
      + tree.loose.map((k) => thTableStatement(v, k, '')).join('') + '</div></div>';
  }
  return html + thTableBin(v);
}

/* the body a row dropped in goes to Not placed, which has no order of its own, the transcript's ruling it */
const TH_TABLE_LOOSE = '~loose';

/* The bin at the table's foot, as the canvas's bin lists it: Binned, each with Put back, then those
   missing from the workbook, each with Remove. Nothing when both are empty. */
function thTableBin(v) {
  const thrown = v.discarded.filter((key) => v.cards[key] && !v.cards[key].missing);
  const gone = Object.keys(v.cards).filter((key) => v.cards[key].missing);
  if (!thrown.length && !gone.length) return '';
  const locked = thLocked(v);
  const row = (key, act, label) => {
    const c = v.cards[key];
    const it = thGets() ? gtItemOf(v, key) : null;
    const words = it ? (it.kind === 'pet' || it.kind === 'sub' ? it.title : it.text) : c.text;
    const where = it ? (c.who || it.kase || '') : [c.sheet, c.time].filter(Boolean).join(', ');
    return `<div class="tb-st tb-binned" data-tbin="${escAttr(key)}"><span class="tb-grip tb-nogrip" aria-hidden="true"></span>`
      + `<p class="tb-text">${esc(words || '')}${where ? ` <span class="tb-ref">(${esc(where)})</span>` : ''}</p>`
      + (locked ? '' : `<button type="button" class="ghost small${act === 'remove' ? ' btn-remove' : ''}" data-t${act}="${escAttr(key)}">${esc(label)}</button>`)
      + '</div>';
  };
  let html = '';
  if (thrown.length) {
    html += `<div class="tb-rest tb-bin"><p class="tb-rest-head">${esc(t('themes.table.set_aside', { n: thrown.length }))}</p>`
      + thrown.map((k) => row(k, 'restore', t('themes.pile.put_back'))).join('') + '</div>';
  }
  if (gone.length) {
    html += `<div class="tb-rest tb-bin"><p class="tb-rest-head">${esc(t('themes.pile.missing'))}</p>`
      + gone.map((k) => row(k, 'remove', t('themes.pile.remove'))).join('') + '</div>';
  }
  return html;
}

/* The GETs board's table: each GET in canvas order with its count, then a row for every case of the
   study, what of it sits under that GET, each card with its grip to go under another GET, the row's
   quote and his note for the row, and the cards under none at the end. Each GET has its Audit
   trail under its title. The sidebar's own Table tab, which held the rows' notes, went on 19 October. */
function gtTableFace(v) {
  if (!TH.gets) return '';
  const tints = thTints(v);
  const { minimum, total } = TH.gets;
  const model = gtTable(v);
  let html = '<div class="tb-pets" data-tbody="">';
  if (!model.length) html += `<p class="tb-none">${esc(t('themes.table.no_gets'))}</p>`;
  const item = (it, parent) => `<li class="tb-item${thTableSelCls('statement', it.key)}" data-trow="${escAttr(it.key)}" data-tkind="statement" data-tparent="${escAttr(parent)}">`
    + `${thTableGrip(t('themes.table.this_card'))}<span class="tb-kind">${esc(it.kind === 'pn' ? t('themes.kind.note') : it.kind === 'es' ? t('themes.statement') : it.kind === 'sub' ? t('themes.kind.sub') : t('themes.unit.pet'))}</span>`
    + `<span class="tb-said">${esc(it.kind === 'pet' || it.kind === 'sub' ? it.title : it.text)}`
    + `${it.within && it.within.length ? ` <span class="tb-in">${esc(t('themes.table.within', { names: it.within.join(', ') }))}</span>` : ''}</span>${thTableMore()}</li>`;
  for (const g of model) {
    const under = g.count < minimum;
    const node = { id: g.id, code: '', title: thLabelShown(g.label), depth: 0 };
    const subs = gtTableSubs(v, g.id);
    html += `<section class="tb-pet tb-get ${thTintClass(tints[g.id])}${thTableSelCls('label', g.id)}" data-trow="${escAttr(g.id)}" data-tkind="label" data-tparent="">`
      + thTableHeadHtml(v, node, `<span class="tb-badge${under ? ' under' : ''}" title="${escAttr(under ? t('themes.gets.under_min', { min: minimum }) : gtCountText(g.count, total))}">${esc(t('themes.gets.of', { count: g.count, total }))}</span>`)
      + (g.note ? `<p class="tb-note">${esc(g.note)}</p>` : '')
      + `<button type="button" class="ghost small tb-trail" data-gtrail="${escAttr(g.id)}">${esc(t('themes.gets.trail'))}</button>`
      + `<div class="tb-body" data-tbody="${escAttr(g.id)}">`
      + (subs.length ? `<div class="tb-subs">${subs.map((sid) => gtTableSubHtml(v, sid, g.id, 1, tints)).join('')}</div>` : '');
    for (const row of g.rows) {
      const bare = !row.counted && row.none;
      const marks = gtCaseMarks(row).filter((m) => !(bare && m === gtNoPets()))
        .map((m) => `<span class="gt-mark">${esc(m)}</span>`).join('');
      const kq = row.counted && row.quote
        ? `<p class="gt-tkey"><span class="gt-tlabel">${esc(t('themes.quote'))}</span><span class="gt-tq">${esc(row.quote.text)}</span>`
          + `<span class="th-time">${esc(row.quote.time)}</span><span class="th-sheet">${esc(row.quote.sheet)}</span></p>` : '';
      html += `<div class="tb-case"><p class="tb-who" data-tcase="${escAttr(row.kase)}" data-tget="${escAttr(g.id)}">${gtBadgeHtml(row.kase)}${esc(row.who)}${marks}</p><div class="tb-said-of">`
        + (row.items.length ? `<ul class="tb-items">${row.items.map((it) => item(it, g.id)).join('')}</ul>`
          : `<p class="tb-nothing">${esc(bare ? GT_NOTHING_NO_PETS : GT_NOTHING)}</p>`)
        + kq + gtRowNoteHtml(g.id, row) + '</div></div>';
    }
    html += '</div></section>';
  }
  html += '</div>';
  const parents = thParents(v);
  const loose = Object.keys(v.cards).filter((k) => (thOnCanvas(v, k) || thWaiting(v, k)) && parents[k] === undefined);
  if (loose.length) {
    html += `<div class="tb-rest"><p class="tb-rest-head">${esc(t('themes.table.not_placed', { n: loose.length }))}</p><ul class="tb-items tb-loose" data-tbody="${TH_TABLE_LOOSE}">`
      + loose.map((k) => item(gtItemOf(v, k), '')).join('') + '</ul></div>';
  }
  return html + thTableBin(v);
}

/* The sub-themes directly inside a GET or a GET sub-theme, in the order its frame reads them */
const gtTableSubs = (v, gid) => thThemeOrder(v, gid, TH.layout || {}).filter((m) => thIsGroup(v, m) && m !== gid);

/* A GET's sub-theme as a row of its own, as its frame sits inside the GET's on the canvas (20 October): its
   grip, its title, how many participants it holds, its menu, and the groups inside it under it. Its cards
   stay in the GET's rows by case, each saying "in" it, so a card is one row of the table however deep it
   sits. A drop on its title strip puts the cards dropped there inside it. */
function gtTableSubHtml(v, sid, parent, depth, tints) {
  const g = thGroup(v, sid);
  const n = gtCount(v, sid);
  const total = TH.gets ? TH.gets.total : 0;
  const inner = depth < 8 ? gtTableSubs(v, sid) : [];
  return `<section class="tb-label tb-getsub${depth > 1 ? ' deep' : ''} ${thTintClass(tints[sid])}${thTableSelCls('label', sid)}" data-trow="${escAttr(sid)}" data-tkind="label" data-tparent="${escAttr(parent)}">`
    + thTableHeadHtml(v, { id: sid, code: '', title: thLabelShown(g.label), depth }, `<span class="tb-badge" title="${escAttr(gtCountText(n, total))}">${esc(t('themes.gets.of', { count: n, total }))}</span>`)
    + (thNoteOf(g) ? `<p class="tb-note">${esc(thNoteOf(g))}</p>` : '')
    + (inner.length ? `<div class="tb-body" data-tbody="${escAttr(sid)}">${inner.map((i) => gtTableSubHtml(v, i, sid, depth + 1, tints)).join('')}</div>` : '')
    + '</section>';
}

/* ── selecting rows (20 October, way 1) ── */

/* Every row of the table in the order it reads, each { id, kind }: a label, a statement, or on GETs a
   card, and a statement under a top whose stack shows. Labels and statements of PETs come in the tree's
   order, then Not placed; the GETs in theirs, each one's cards case by case, then Not placed. */
function thTableFlat(v) {
  const out = [];
  if (!v) return out;
  if (thGets()) {
    if (!TH.gets) return out;
    if (thTa() && !TH.lpets && !TH.lgets) return gtTableTaFlat(v);
    const subs = (gid, depth) => {
      if (depth > 8) return;
      for (const sid of gtTableSubs(v, gid)) { out.push({ id: sid, kind: 'label' }); subs(sid, depth + 1); }
    };
    for (const g of gtTable(v)) {
      out.push({ id: g.id, kind: 'label' });
      subs(g.id, 1);
      for (const row of g.rows) for (const it of row.items) out.push({ id: it.key, kind: 'statement' });
    }
    const parents = thParents(v);
    for (const k of Object.keys(v.cards)) if (thOnCanvas(v, k) && parents[k] === undefined) out.push({ id: k, kind: 'statement' });
    return out;
  }
  const tree = thTableTree(v, TH.layout || {}, true, TH.sheets);
  const statement = (key) => {
    out.push({ id: key, kind: 'statement' });
    if (TH.opened && TH.opened.has(key)) for (const k of thStackOf(v, key)) out.push({ id: k, kind: 'under' });
  };
  const walk = (node) => {
    out.push({ id: node.id, kind: 'label' });
    for (const it of node.items) if (it.kind === 'label') walk(it.node); else statement(it.key);
  };
  tree.pets.forEach(walk);
  tree.loose.forEach(statement);
  return out;
}

const thTableItem = (id, kind) => (kind === 'label' ? { kind: 'group', id } : { kind: 'card', id });

/* A click on a row selects it as a click on its card or its label does on the canvas: alone, or with Cmd
   added or taken away, and with Shift the run of rows of its kind between the last row clicked and this
   one, Cmd and Shift together adding the run. The selection is the board's, so the canvas shows the same
   cards selected, and an Inspector showing follows it. */
function thTableSelect(id, kind, mods = {}) {
  if (!TH.v) return;
  const item = thTableItem(id, kind);
  const anchor = TH.tanchor;
  const same = (k) => (k === 'label') === (kind === 'label');
  if (mods.shift && anchor && same(anchor.kind)) {
    const flat = thTableFlat(TH.v).filter((r) => same(r.kind));
    const a = flat.findIndex((r) => r.id === anchor.id);
    const b = flat.findIndex((r) => r.id === id);
    if (a >= 0 && b >= 0) {
      if (!mods.mod) { TH.sel.cards.clear(); TH.sel.groups.clear(); TH.sel.stickies.clear(); }
      for (const r of flat.slice(Math.min(a, b), Math.max(a, b) + 1)) thSetOf(thTableItem(r.id, r.kind)).add(r.id);
      TH.lastPick = item;
      thDrawSel();
      thPanelFollow();
      return;
    }
  }
  if (mods.mod || mods.shift) {
    thToggle(item);
    TH.lastPick = thSelected(item) ? item : null;
  } else {
    thSelectOnly(item);
    TH.lastPick = item;
  }
  TH.tanchor = { id, kind };
  thPanelFollow();
}

/* the rows the selection holds marked in the table as it stands, without drawing it afresh */
function thTableMarks() {
  const box = $('th-table');
  if (!box || TH.face !== 'table' || !box.querySelectorAll) return;
  for (const row of box.querySelectorAll('[data-trow]')) {
    row.classList.toggle('tb-sel', (row.dataset.tkind === 'label' ? TH.sel.groups : TH.sel.cards).has(row.dataset.trow));
  }
}

/* S in the table: the statements selected stack under the one that reads first in the table, as on the
   canvas they stack under the highest, and one top selected shows its stack or stacks it again. */
function thTableStackKey() {
  if (thRefuse('stack')) return;
  const v = TH.v;
  const cards = [...TH.sel.cards].filter((k) => thOnCanvas(v, k));
  if (cards.length < 2) { thStackKey(); return; }
  const order = thTableFlat(v).map((r) => r.id);
  const top = cards.slice().sort((a, b) => order.indexOf(a) - order.indexOf(b))[0];
  thStackDo(cards.filter((k) => k !== top), top);
}

/* ── a title in the table ── */

/* A title opened in its box in place, from a double-click, Rename in its menu, or a label just made by
   G or New group inside, `opts.fresh`, whose box opens empty and whose making and first title are one
   step of undo, `opts.before` the board before it was made, as on the canvas (see thTitleOpen). */
function thTableTitleOpen(id, opts = {}) {
  if (!TH.live || !TH.v || !thIsGroup(TH.v, id) || thRefuse('rename')) return;
  thTableTitleDone(true);
  TH.tedit = { id, value: opts.fresh ? '' : thLabelShown(thGroup(TH.v, id).label), fresh: !!opts.fresh, before: opts.before || null,
    was: opts.was || null };
  thTableDraw();
  const row = [...$('th-table').querySelectorAll('[data-trow]')].find((el) => el.dataset.trow === id);
  if (row && row.scrollIntoView) { row.scrollIntoView({ block: 'nearest' }); thTableStageStill(); }
}

/* Enter or a click away keeps what is typed, a blank one as Untitled, and Esc leaves the title as it
   was. A change is the canvas's Renamed a label, one step of undo, and a label just made the canvas's
   Made a theme, its title whatever Enter or Esc leaves it. */
function thTableTitleDone(keep) {
  const ed = TH.tedit;
  if (!ed) return;
  const box = $('tb-title-box');
  const text = thLabelKept(String(box ? box.value : ed.value).replace(/\s+/g, ' ').trim());
  TH.tedit = null;
  TH.tfocus = { id: ed.id, grip: false };
  const v = TH.v;
  const g = v && thGroup(v, ed.id);
  if (ed.fresh && g && ed.before && !thLocked(v)) {
    if (keep) g.label = text;
    thDone(ed.before, t('themes.step.made_theme'), { settle: [], was: ed.was || undefined, labels: [ed.id] });
    return;
  }
  if (keep && g && !thLocked(v) && text !== g.label) {
    const before = thSnap(v, TH.removed);
    const was = thLabelBoxes(TH.layout);
    g.label = text;
    thDone(before, t('themes.step.renamed'), { settle: [], was, labels: [ed.id] });
    return;
  }
  thTableDraw();
}

/* ── a row dragged by its grip, and Alt with an arrow ── */

/* Where rows let go at (x, y) come. Over the title strip of another label, a drop merges into it, as on the
   canvas, `merge` its id: statements join it, and a label goes inside it. Otherwise a label lands among
   what sits in its own label, or the PETs, and statements in the innermost label's body the pointer is in,
   in Not placed, `under` TH_TABLE_LOOSE, or else their own, at the place among that body's rows the pointer
   is above. `under` is the label's id, '' for the PETs, and `line` where the line shows, in the table's own
   pixels. Null when they land nowhere. */
function thTableDropAt(d, x, y) {
  const box = $('th-table');
  const lifted = d.rows;
  const inLifted = (el) => lifted.some((r) => r === el || r.contains(el));
  const outer = box.querySelector('.tb-page').getBoundingClientRect();
  // a title strip, as the canvas's, takes what is dropped on it into its label
  for (const head of box.querySelectorAll('.tb-head')) {
    const hr = head.getBoundingClientRect();
    if (y < hr.top || y > hr.bottom || x < hr.left || x > hr.right) continue;
    const sec = head.closest('[data-trow]');
    if (!sec || inLifted(sec)) break;
    if (!thMergeInto(TH.v, new Set(d.keys), sec.dataset.trow)) break;
    return { merge: sec.dataset.trow, head, hue: getComputedStyle(sec).getPropertyValue('--hue') };
  }
  const bodies = [...box.querySelectorAll('[data-tbody]')].filter((b) => !inLifted(b));
  let body = null;
  if (d.kind === 'label') body = bodies.find((b) => b.dataset.tbody === d.from) || null;
  else {
    let best = null;
    // a statement goes into a label or Not placed, never among the PETs themselves
    for (const b of bodies) {
      if (b.dataset.tbody === '') continue;
      const r = b.getBoundingClientRect();
      if (y < r.top || y > r.bottom || x < r.left || x > r.right) continue;
      if (!best || best.contains(b)) best = b;
    }
    body = best || bodies.find((b) => b.dataset.tbody === d.from && d.from !== '') || null;
  }
  if (!body) return null;
  const br = body.getBoundingClientRect();
  if (body.dataset.tbody === TH_TABLE_LOOSE) return { under: TH_TABLE_LOOSE, at: 0, body, hue: '', line: null };
  const rows = [...body.querySelectorAll('[data-trow]')]
    .filter((r) => !lifted.includes(r) && !r.classList.contains('tb-under') && r.closest('[data-tbody]') === body);
  let at = 0;
  for (const r of rows) {
    const b = r.getBoundingClientRect();
    if (y > b.top + b.height / 2) at += 1;
  }
  let lineY;
  if (!rows.length) lineY = br.top + 4;
  else if (at < rows.length) lineY = rows[at].getBoundingClientRect().top;
  else lineY = rows[rows.length - 1].getBoundingClientRect().bottom;
  const hold = body.closest('[data-trow]');
  return { under: body.dataset.tbody, at, body, hue: hold ? getComputedStyle(hold).getPropertyValue('--hue') : '',
    line: { x: br.left - outer.left, y: lineY - outer.top, w: br.width } };
}

/* A press on a grip. A selected statement's grip takes every statement selected along with it, in the
   order they read, and an unselected row's grip its row alone, which the drag then selects. */
function thTableDown(e) {
  const grip = e.target.closest('.tb-grip');
  if (!grip || e.button !== 0 || !TH.live || TH.busy || !TH.v) return;
  e.preventDefault();
  if (thRefuse('move')) return;
  thTableTitleDone(true);
  const row = grip.closest('[data-trow]');
  if (!row || row.dataset.tkind === 'under') return;
  const id = row.dataset.trow;
  const kind = row.dataset.tkind;
  let keys = [id];
  if (kind === 'statement' && TH.sel.cards.has(id)) {
    const chosen = thTableFlat(TH.v).filter((r) => r.kind === 'statement' && TH.sel.cards.has(r.id) && thOnCanvas(TH.v, r.id)).map((r) => r.id);
    if (chosen.length > 1) keys = chosen;
  }
  const all = [...$('th-table').querySelectorAll('[data-trow]')];
  const rows = keys.map((k) => all.find((el) => el.dataset.trow === k && el.dataset.tkind !== 'under')).filter(Boolean);
  TH.tdrag = { id, kind, keys, from: row.dataset.tparent || '', row, rows, x0: e.clientX, y0: e.clientY,
    moved: false, drop: null, grip };
  try { grip.setPointerCapture(e.pointerId); } catch { /* a nicety */ }
}

/* the title strip a drop would merge into lit, "Merge into" laid over it as on the canvas, and the last
   one lit put out */
function thTableMergeShow(head) {
  const box = $('th-table');
  const was = box.querySelector('.tb-merge');
  if (was && was !== head) {
    was.classList.remove('tb-merge');
    const word = was.querySelector('.tb-merge-word');
    if (word) word.remove();
  }
  if (!head || head === was) return;
  head.classList.add('tb-merge');
  head.insertAdjacentHTML('beforeend', `<span class="tb-merge-word">${esc(t('themes.merge_into'))}</span>`);
}

function thTableMove(e) {
  const d = TH.tdrag;
  if (!d) return;
  if (!d.moved) {
    if (Math.abs(e.clientY - d.y0) < 4 && Math.abs(e.clientX - d.x0) < 4) return;
    d.moved = true;
    // a row picked up that was not selected is the selection from then on, as a card dragged is
    if (!(d.kind === 'label' ? TH.sel.groups : TH.sel.cards).has(d.id)) thTableSelect(d.id, d.kind);
    for (const r of d.rows) r.classList.add('tb-lifted');
    $('th-table').classList.add('tb-dragging');
  }
  d.drop = thTableDropAt(d, e.clientX, e.clientY);
  const line = $('tb-line');
  const into = $('th-table').querySelector('.tb-into');
  if (into && (!d.drop || into !== d.drop.body)) into.classList.remove('tb-into');
  thTableMergeShow(d.drop && d.drop.merge ? d.drop.head : null);
  if (!line) return;
  if (!d.drop || !d.drop.line) {
    line.hidden = true;
    if (d.drop && d.drop.under === TH_TABLE_LOOSE && d.from !== '') d.drop.body.classList.add('tb-into');
  } else {
    line.hidden = false;
    line.style.left = `${d.drop.line.x}px`;
    line.style.top = `${d.drop.line.y}px`;
    line.style.width = `${d.drop.line.w}px`;
    line.style.setProperty('--hue', d.drop.hue || '');
    if (d.drop.under !== d.from) d.drop.body.classList.add('tb-into');
  }
  // the table scrolls under a drag held near its top or its foot
  const box = $('th-table');
  const r = box.getBoundingClientRect();
  if (e.clientY < r.top + 40) box.scrollTop -= 12;
  else if (e.clientY > r.bottom - 40) box.scrollTop += 12;
}

function thTableUp() {
  const d = TH.tdrag;
  if (!d) return;
  TH.tdrag = null;
  $('th-table').classList.remove('tb-dragging');
  for (const r of d.rows) r.classList.remove('tb-lifted');
  const into = $('th-table').querySelector('.tb-into');
  if (into) into.classList.remove('tb-into');
  thTableMergeShow(null);
  const line = $('tb-line');
  if (line) line.hidden = true;
  if (!d.moved || !d.drop) return;
  TH.tfocus = { id: d.id, grip: true };
  if (d.drop.merge) { thTableMerge(d.keys, d.kind, d.drop.merge); return; }
  if (d.drop.under === TH_TABLE_LOOSE) {
    if (!thLeaveThemes(d.keys)) thTableDraw();
    return;
  }
  thTablePut(d.kind === 'label' ? d.id : d.keys, d.kind, d.from, d.drop.under, d.drop.at);
}

/* `items` with `ids` taken out and set back in together at `at`, the place among the others, in the
   order `ids` gives them */
function thTableMovedAll(items, ids, at) {
  const rest = items.filter((m) => !ids.includes(m));
  const i = Math.max(0, Math.min(rest.length, at));
  return rest.slice(0, i).concat(ids, rest.slice(i));
}

/* What a drop or a key does: in its own label a reorder, and statements into another label a move to
   their place there, several dragged together coming in together. Nothing when they come back where
   they were. `ids` is one id or a list. */
function thTablePut(ids, kind, from, to, at) {
  const v = TH.v;
  if (!v) return;
  ids = Array.isArray(ids) ? ids : [ids];
  const layout = TH.layout || {};
  const parents = thParents(v);
  // on the GETs board a case's card goes under another GET, its rows set out by case, not in order
  if (thGets() && kind === 'statement') {
    const coming = ids.filter((k) => parents[k] !== to);
    if (to && coming.length) thTableOrder(to, [], { keys: coming, to }); else thTableDraw();
    return;
  }
  if (kind !== 'statement') {
    // a GET's sub-theme has no order among its GET's cards, which read by case: a drop on a title strip moves it
    if (to !== from || (thGets() && from)) { thTableDraw(); return; }
    const now = thTableSiblings(v, layout, from || null);
    const order = thTableMoved(now, ids[0], at);
    if (order.join('\n') === now.join('\n')) { thTableDraw(); return; }
    thTableOrder(from || null, order);
    return;
  }
  if (!to) { thTableDraw(); return; }
  const there = thTableSiblings(v, layout, to);
  const coming = ids.filter((k) => !there.includes(k));
  const order = thTableMovedAll(there.concat(coming), ids, at);
  if (!coming.length) {
    if (order.join('\n') === there.join('\n')) { thTableDraw(); return; }
    thTableOrder(to, order);
    return;
  }
  thTableOrder(to, order, { keys: coming, to });
}

/* Rows dropped on a label's title strip, Merge into as on the canvas: statements, or GETs cards, join it
   under what it holds, and a label goes inside it with all it holds, under what it holds. One step of
   undo. */
function thTableMerge(ids, kind, target) {
  const v = TH.v;
  if (!v || !thIsGroup(v, target) || thRefuse('join')) return;
  if (kind !== 'label') {
    const there = thGets() ? [] : thTableSiblings(v, TH.layout || {}, target);
    const parents = thParents(v);
    const coming = ids.filter((k) => !there.includes(k) && parents[k] !== target);
    if (!coming.length) { thTableDraw(); return; }
    thTableOrder(target, thGets() ? [] : there.concat(coming), { keys: coming, to: target });
    return;
  }
  const gid = ids[0];
  if (!thMergeInto(v, new Set([gid]), target)) { thTableDraw(); return; }
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  const from = thSpots(v);
  const layout = TH.layout || {};
  const box = layout[gid] && (layout[gid].frame || layout[gid].label);
  const at = layout[target];
  const dest = at && at.body ? { x: at.body.x, y: at.body.y + at.body.h + TH_MARGIN }
    : at && at.label ? { x: at.label.x + TH_FRAME_X, y: at.label.y + at.label.h + TH_GAP } : null;
  const moving = thMoving(v, [], [gid]);
  if (box && dest) {
    const dx = Math.round(dest.x - box.x);
    const dy = Math.round(dest.y - box.y);
    for (const it of moving) {
      const thing = v.cards[it] || thGroup(v, it) || thSticky(v, it);
      if (thing) { thing.x += dx; thing.y += dy; }
    }
  }
  if (!thJoin(v, [gid], target).length) { TH.removed = thPut(v, before); thTableDraw(); return; }
  thAck([...moving].filter((it) => v.cards[it]));
  thDone(before, t('themes.step.joined', { label: thGroup(v, target).label }), { settle: [...moving], was, from });
}

/* Alt with an arrow up or down on a row's grip or its title: one place up or down among what sits in
   its own label. True when the key was the table's. */
function thTableKey(e) {
  if (TH.face !== 'table' || !e.altKey || MOD(e) || (e.key !== 'ArrowUp' && e.key !== 'ArrowDown')) return false;
  const row = e.target && e.target.closest && e.target.closest('#th-table [data-trow]');
  if (!row) return false;
  e.preventDefault();
  if (!TH.live || TH.busy || !TH.v || thRefuse('move')) return true;
  const from = row.dataset.tparent || '';
  const now = thTableSiblings(TH.v, TH.layout || {}, from || null);
  const i = now.indexOf(row.dataset.trow);
  const j = i + (e.key === 'ArrowUp' ? -1 : 1);
  if (i < 0 || j < 0 || j >= now.length) return true;
  TH.tfocus = { id: row.dataset.trow, grip: !!e.target.closest('.tb-grip') };
  thTableOrder(from || null, thTableMoved(now, row.dataset.trow, j));
  return true;
}

/* A row brought into view scrolls the table alone: near the table's end the browser scrolls the canvas under it
   too, which hides nothing but shifts the palette and the status bar up, so the canvas is put back. */
function thTableStageStill() {
  const st = thStage();
  if (st && st.scrollTop) st.scrollTop = 0;
  if (st && st.scrollLeft) st.scrollLeft = 0;
}

/* A search's result on the board while the table shows: its row drawn and brought to the middle of the
   view, its title or grip given the focus. */
function thTableShow(id) {
  if (TH.face !== 'table') return;
  thTableDraw();
  const row = [...$('th-table').querySelectorAll('[data-trow]')].find((el) => el.dataset.trow === String(id));
  if (!row) return;
  if (row.scrollIntoView) { row.scrollIntoView({ block: 'center' }); thTableStageStill(); }
  const el = row.querySelector('.tb-title, .tb-grip');
  if (el) el.focus({ preventScroll: true });
}

/* The row a click, a double-click or a right click is on: a statement's or a card's anywhere on it, and a
   label's only on its title strip, since the rest of a label's section is the rows it holds. */
function thTableRowAt(el) {
  const row = el && el.closest ? el.closest('#th-table [data-trow]') : null;
  if (!row) return null;
  if (row.dataset.tkind === 'label' && !el.closest('.tb-head')) return null;
  return row;
}

function thTableBoot() {
  const box = $('th-table');
  if (!box) return;
  // the canvas under it hears nothing the table does
  for (const kind of ['pointerdown', 'pointermove', 'pointerup', 'pointercancel', 'wheel', 'contextmenu', 'auxclick', 'dblclick']) {
    box.addEventListener(kind, (e) => {
      // a row of the Cases panel on its way over the GET table goes on moving and lands here (20 October)
      if (TH.pull && kind === 'pointermove') gtPullMove(e);
      else if (TH.pull && kind === 'pointerup') gtPullUp(e);
      e.stopPropagation();
    });
  }
  box.addEventListener('pointerdown', (e) => {
    // Shift or Cmd with a click picks rows, and never runs a selection of the words over them
    if ((e.shiftKey || MOD(e)) && e.target.closest('[data-trow]') && !e.target.closest('input, textarea')) e.preventDefault();
    thTableDown(e);
  });
  // and the mouse's own press, where the browser starts a selection of words: a row picked with Shift or
  // Cmd, a right click (which on a Mac selects the word under it) and a double-click select no words, as
  // a card on the canvas never does (20 October)
  box.addEventListener('mousedown', (e) => {
    if (!e.target.closest('[data-trow]') || e.target.closest('input, textarea')) return;
    if (e.shiftKey || MOD(e) || e.button === 2 || e.ctrlKey || e.detail > 1) e.preventDefault();
  });
  box.addEventListener('pointermove', thTableMove);
  box.addEventListener('pointerup', thTableUp);
  box.addEventListener('pointercancel', thTableUp);
  box.addEventListener('click', (e) => {
    const trail = e.target.closest('[data-gtrail]');
    if (trail && thGets()) { gtTrailOpen(trail.dataset.gtrail); return; }
    const note = e.target.closest('[data-gnote]');
    if (note && thGets()) { gtRowNoteOpen(note.dataset.gnote, note.dataset.gcase); return; }
    const act = e.target.closest('[data-tact]');
    if (act) {
      if (act.dataset.tact === 'print') thPrint();
      else if (act.dataset.tact === 'word') thExport(true);
      else if (act.dataset.tact === 'gprint') gtPrintOpen('table');
      else if (act.dataset.tact === 'gword') gtWordGo({ what: 'table', detail: 'full', gid: null }, false);
      return;
    }
    if (!TH.live || TH.busy || !TH.v) return;
    const stack = e.target.closest('[data-tstack]');
    if (stack) { thStackShow(stack.dataset.tstack); return; }
    // a row's link mark opens its close pair's menu, the row's statement "this one"
    const mark = e.target.closest('[data-tpair]');
    if (mark) {
      const p = (TH.pairs || [])[Number(mark.dataset.tpair)];
      const at = mark.closest('[data-trow]');
      const r = mark.getBoundingClientRect();
      if (p && at) thPairMenuOpen(p, r.left, r.bottom, at.dataset.trow);
      return;
    }
    const back = e.target.closest('[data-trestore]');
    if (back) { thPutBack(back.dataset.trestore); return; }
    const gone = e.target.closest('[data-tremove]');
    if (gone) { thRemove(gone.dataset.tremove); return; }
    const more = e.target.closest('[data-tmore]');
    const row = thTableRowAt(e.target);
    if (more && row) {
      const r = more.getBoundingClientRect();
      thMenuOpen(thTableItem(row.dataset.trow, row.dataset.tkind), r.left, r.bottom);
      return;
    }
    if (e.target.closest('input, textarea, select, .tb-binned, .tb-acts')) return;
    if (!row) {
      // a click on the table's empty space clears the selection, as on empty canvas
      if (!e.shiftKey && !MOD(e) && (TH.sel.cards.size || TH.sel.groups.size || TH.sel.stickies.size)) { thClearSel(); thPanelFollow(); }
      return;
    }
    const id = row.dataset.trow;
    const kind = row.dataset.tkind;
    // a second click on the title of the one label selected opens it, as in the Finder
    const title = e.target.closest('[data-ttitle]');
    if (title && !e.shiftKey && !MOD(e) && TH.sel.groups.size === 1 && TH.sel.groups.has(id) && !TH.sel.cards.size && e.detail < 2) {
      thTableTitleOpen(id);
      return;
    }
    thTableSelect(id, kind, { shift: e.shiftKey, mod: MOD(e) });
  });
  // a double-click on a statement goes to its passage, as Go to the passage in its menu does, and on a title opens it
  box.addEventListener('dblclick', (e) => {
    if (!TH.live || TH.busy || !TH.v || e.target.closest('input, textarea, button:not(.tb-title)')) return;
    const row = thTableRowAt(e.target);
    if (!row || e.shiftKey || MOD(e)) return;
    const id = row.dataset.trow;
    if (row.dataset.tkind === 'label') { if (!(TH.tedit && TH.tedit.id === id)) thTableTitleOpen(id); return; }
    if (thIsStatement(TH.v, id)) thToPassage(id);
    else { TH.lastPick = { kind: 'card', id }; thInspectorOpen({ kind: 'card', id }); }
  });
  // a right click on a row opens its card's or its label's menu, and on a case's name in a GET its own
  box.addEventListener('contextmenu', (e) => {
    if (!TH.live || TH.busy || !TH.v || e.target.closest('input, textarea')) return;
    const kase = e.target.closest('[data-tcase]');
    if (kase && thGets()) {
      e.preventDefault();
      const i = ((TH.gets && TH.gets.cases) || []).findIndex((c) => c.case === kase.dataset.tcase);
      if (i >= 0) gtCaseMenu(i, e.clientX, e.clientY, kase.dataset.tget);
      return;
    }
    const row = thTableRowAt(e.target);
    if (!row) return;
    e.preventDefault();
    thTableTitleDone(true);
    thMenuOpen(thTableItem(row.dataset.trow, row.dataset.tkind), e.clientX, e.clientY);
  });
  box.addEventListener('keydown', (e) => {
    if (e.target.id === 'gt-rnote-box') {
      e.stopPropagation();
      if (e.isComposing) return;
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); gtRowNoteDone(true); }
      else if (e.key === 'Escape') { e.preventDefault(); gtRowNoteDone(false); }
      return;
    }
    if (!e.target.closest('#tb-title-box')) return;
    e.stopPropagation();
    if (e.isComposing) return;
    if (e.key === 'Enter') { e.preventDefault(); thTableTitleDone(true); }
    else if (e.key === 'Escape') { e.preventDefault(); thTableTitleDone(false); }
  });
  box.addEventListener('focusout', (e) => {
    if (e.target.id === 'tb-title-box' && TH.tedit) thTableTitleDone(true);
    if (e.target.id === 'gt-rnote-box' && TH.rowEdit && !TH.rowEdit.focus) setTimeout(() => {
      if (TH.rowEdit && document.activeElement !== $('gt-rnote-box')) gtRowNoteDone(true);
    }, 0);
  });
  box.addEventListener('input', (e) => { if (e.target.id === 'gt-rnote-box' && TH.rowEdit) TH.rowEdit.value = e.target.value; });
  const sw = $('th-faces');
  sw.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  sw.addEventListener('click', (e) => {
    const b = e.target.closest('[data-face]');
    if (b && TH.live) thFace(b.dataset.face);
  });
}

/* ── the canvas in print ── */

/* The canvas itself on paper, Canvas under Export and Canvas in the GETs print card (210): every
   frame, label, card and sticky note copied from the canvas on screen, so the page never drifts
   from it, in their tints, the text wrapping as it wraps there. None of the screen's chrome comes
   with them. On paper every statement is whole. A card on screen stops at four lines, so the copy
   is laid out again by the canvas's own layout with each card at its whole height: what it comes
   to sit on makes way, the frames round it grow, and the columns, the nesting and the order stay
   the screen's. The canvas on screen is only read. The page is cropped to what is on the copy with
   a small margin and scaled to fit one landscape page of the paper the print dialog picks, never
   past its own size, whatever the pan and zoom, under a title naming the case by its pseudonym, on
   GETs the project, and the board. It is set in the light theme's colours on white paper, and the
   text stays text in a PDF. */
const TH_CANVAS_MARGIN = 24;
// what the screen draws for the hand at work and paper never shows: a label's controls, a note's
// cross and colours, a box open for editing, and the Merge a drag shows
const TH_CANVAS_CHROME = '.th-merge, .th-del, .th-arr, .th-more, .th-sticky-del, .th-strip, .th-title-edit, button, textarea, input';
// the marks an act leaves on what is drawn: selection, editing, a drag, its landing and a drop target
const TH_CANVAS_STATES = ['sel', 'alone', 'editing', 'dragging', 'landing', 'trailing', 'ease-from', 'easing', 'nudging',
  'sent', 'leaving', 'target'];
const TH_CANVAS_EMPTY = t('themes.print.empty');

/* the box round everything drawn, in the canvas's own units, with the margin all round, or null
   for a canvas with nothing on it */
function thCanvasBox(boxes, margin = TH_CANVAS_MARGIN) {
  const shown = boxes.filter((b) => b && b.w > 0 && b.h > 0);
  if (!shown.length) return null;
  const u = thUnion(shown);
  const x = Math.floor(u.x - margin);
  const y = Math.floor(u.y - margin);
  return { x, y, w: Math.ceil(u.x + u.w + margin) - x, h: Math.ceil(u.y + u.h + margin) - y };
}

/* The case by its pseudonym as the print view names it, "P9 Wren" for `P9 - Wren`, and on GETs the
   project's name, with the board's name after it. */
function thCanvasTitle(name, board) {
  const who = String(name || '').split(/\s+/).join(' ').trim().replace(/^(P\d+)\s*-\s*/, '$1 ');
  return [who, String(board || '').trim()].filter(Boolean).join(' · ');
}

/* The canvas on screen, copied: what is drawn, without the chrome or the marks an act leaves, a
   participant note left out unless `notes`, every statement whole and laid out round its whole
   height, and the box round what is left. The board is copied as undo copies it, so the layout
   writes to the copy alone, and the canvas itself, its board, its sizes and its layout, is only
   read. */
function thCanvasCopy(notes) {
  // the print is unchanged by a PET card unfolded on GETs: the board is drawn folded for the copy, and then as it was
  if (TH.mode === 'gets' && TH.unfolded && TH.unfolded.size) {
    const held = TH.unfolded;
    TH.unfolded = new Set();
    try { thRender(); return thCanvasCopy(notes); } finally { TH.unfolded = held; thRender(); }
  }
  const copy = $('th-world').cloneNode(true);
  copy.removeAttribute('id');
  // a PET's count prints as its words, without the chevron that unfolds it on screen
  copy.querySelectorAll('.gt-unfold').forEach((el) => {
    const n = document.createElement('span');
    n.className = 'gt-n';
    n.textContent = el.textContent;
    el.replaceWith(n);
  });
  copy.querySelectorAll(TH_CANVAS_CHROME).forEach((el) => el.remove());
  if (!notes) copy.querySelectorAll('.gt-pn').forEach((el) => el.remove());
  for (const el of copy.querySelectorAll('*')) {
    el.classList.remove(...TH_CANVAS_STATES);
    el.removeAttribute('title');
    el.removeAttribute('id');
    for (const p of ['translate', 'rotate', 'scale']) el.style.removeProperty(p);
    if (el.matches('.th-text, .th-title')) el.hidden = false;
  }
  const board = thSnap(TH.v);
  const laid = thCanvasWhole(board, thCanvasMeasure(copy), thSize);
  thCanvasPut(copy, board, laid.layout);
  const boxes = [...copy.querySelectorAll('.th-frame, .th-card, .th-label, .th-sticky')].filter((el) => !el.hidden).map((el) => {
    const at = { x: parseFloat(el.style.left) || 0, y: parseFloat(el.style.top) || 0 };
    if (el.classList.contains('th-frame')) return Object.assign(at, { w: parseFloat(el.style.width) || 0, h: parseFloat(el.style.height) || 0 });
    return Object.assign(at, laid.size(el.dataset.key || el.dataset.group || el.dataset.sticky));
  });
  return { html: copy.innerHTML, box: thCanvasBox(boxes) };
}

/* Each card of the copy at its whole height, the clamp lifted: the copy is set off screen and out
   of sight under `th-whole`, measured, and taken away in the same moment, before anything is drawn,
   so nothing on screen moves or flickers. */
const TH_CANVAS_AWAY = 'position: fixed; left: -100000px; top: 0; visibility: hidden; pointer-events: none;';
function thCanvasMeasure(copy) {
  const host = document.createElement('div');
  host.className = 'th-whole';
  host.setAttribute('aria-hidden', 'true');
  host.style.cssText = TH_CANVAS_AWAY;
  host.appendChild(copy);
  document.body.appendChild(host);
  const out = {};
  for (const el of copy.querySelectorAll('.th-card')) {
    if (el.dataset.key) out[el.dataset.key] = { w: el.offsetWidth, h: el.offsetHeight };
  }
  host.remove();
  return out;
}

/* The canvas's own layout run on a copy of the board, `v`, with the cards at their whole sizes,
   `whole`, `size` being the sizes measured on screen. Each card taller than on screen takes its
   whole height in the order the canvas reads, top to bottom, and stands where it is as a card let
   go does, while what it comes to sit on makes way and the frames round it grow and send clear
   what they reach (see thSettle). The sizes it came to and the layout come back. */
function thCanvasWhole(v, whole, size) {
  const sizes = {};
  const at = (item) => sizes[item] || size(item);
  const taller = Object.keys(whole).filter((key) => thOnCanvas(v, key) && whole[key].h > size(key).h);
  for (const key of thReadOrder(taller.map((k) => ({ id: k, x: v.cards[k].x, y: v.cards[k].y })))) {
    const was = thLabelBoxes(thLayout(v, at, null));
    sizes[key] = whole[key];
    thSettle(v, at, [key], was, [], TH_PASSES, true);
  }
  return { size: at, layout: thLayout(v, at, null) };
}

/* The copy's cards, notes, labels and frames put where the copy of the board says, as thPlace puts
   the canvas's at rest, each frame's badge along its foot. */
function thCanvasPut(copy, v, layout) {
  const put = (el, p) => {
    if (!p) return;
    el.style.left = `${p.x}px`;
    el.style.top = `${p.y}px`;
  };
  for (const el of copy.querySelectorAll('.th-card')) put(el, v.cards[el.dataset.key]);
  for (const el of copy.querySelectorAll('.th-sticky')) put(el, thSticky(v, el.dataset.sticky));
  for (const el of copy.querySelectorAll('.th-label')) put(el, thGroup(v, el.dataset.group));
  const spots = thBadgeSpots(v, layout, TH.badges || {});
  for (const el of copy.querySelectorAll('.th-frame')) {
    const id = el.dataset.frame;
    const box = layout[id] && layout[id].body && layout[id].frame;
    el.hidden = !box;
    if (!box) continue;
    el.style.left = `${box.x}px`;
    el.style.top = `${box.y}px`;
    el.style.width = `${box.w}px`;
    el.style.height = `${box.h}px`;
    if (el.firstElementChild && spots[id] !== undefined) el.firstElementChild.style.left = `${spots[id]}px`;
  }
}

/* the page's rules, every rule of the app's own sheets, as the canvas on screen is drawn with */
function thCanvasRules() {
  let out = '';
  for (const sheet of document.styleSheets) {
    let rules = [];
    try { rules = sheet.cssRules; } catch (err) { rules = []; }
    for (const r of rules) out += `${r.cssText}\n`;
  }
  return out;
}

/* The page in its tab: Print at the top right, then a landscape page holding the title and the
   canvas. The title is the print view's heading, the serif at 22pt over a rule, and keeps its own
   size. On screen the page is a white sheet on the app's sunk paper. On paper it is the page itself, its margin
   10mm, and the canvas alone scales to the room left under the title, its width and height over
   the copy's, through container units. A browser without typed arithmetic in calc() is given the
   scale by the page's script, the window's room on screen and A4's room on paper. Esc closes the
   tab, and the canvas it came from is left as it was. An empty box at the head and the foot of the page's margin keeps
   the browser's own date, title, address and page count off paper (17 October). The script grows each case's badge by the
   scale the canvas is drawn at, as the canvas does by its zoom (see gtBadgeUp), and a GETs canvas
   draws its GETs' titles as the GETs board does. */
function thCanvasPage(o) {
  const { w, h } = o.box;
  const style = `
:root { --paper: #FFFFFF; color-scheme: light; }
@page { size: landscape; margin: 10mm; @top-right { content: ""; } @bottom-right { content: ""; } }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { background: var(--paper-sunk); }
body.cp { margin: 0; padding: 16px; font-family: var(--sans); color: var(--ink); }
.cp-controls { display: flex; justify-content: flex-end; margin: 0 0 12px; }
.cp-controls button { font: inherit; font-size: 12px; padding: 6px 16px; cursor: pointer; color: var(--ink);
  background: #FFFDF8; border: 1px solid var(--rule-firm); border-radius: 3px; }
.cp-controls button:hover { border-color: var(--ink-faint); }
.cp-page { display: flex; flex-direction: column; box-sizing: border-box; margin: 0 auto; padding: 24px;
  width: min(100%, calc((100vh - 78px) * 297 / 210)); aspect-ratio: 297 / 210;
  background: var(--paper); box-shadow: 0 1px 3px rgba(31,27,22,.12), 0 8px 28px rgba(31,27,22,.10); }
.cp-title { flex: none; margin: 0 0 12pt; padding: 0 0 8pt; border-bottom: 1px solid var(--rule-firm);
  font-family: var(--serif); font-weight: normal; font-size: 22pt; line-height: 1.15; color: var(--ink); }
.cp-fit { flex: 1 1 auto; min-height: 0; container-type: size; overflow: hidden; }
.cp-box { --s: min(1, calc(100cqw / ${w}px), calc(100cqh / ${h}px)); width: calc(${w}px * var(--s));
  height: calc(${h}px * var(--s)); margin: 0 auto; }
.cp-canvas { position: relative; width: ${w}px; height: ${h}px; transform-origin: 0 0; transform: scale(var(--s));
  pointer-events: none; }
@media print {
  html, body { height: 100%; background: var(--paper); }
  body.cp { padding: 0; overflow: hidden; }
  .cp-controls { display: none; }
  .cp-page { width: auto; height: 100%; aspect-ratio: auto; padding: 0; box-shadow: none; break-inside: avoid; }
}`;
  // in a function of its own, so its constants keep to themselves
  const script = `(() => {
document.getElementById('cp-print').onclick = () => window.print();
addEventListener('keydown', (e) => { if (e.key === 'Escape') window.close(); });
if (!(window.CSS && CSS.supports('scale', 'calc(1px / 1px)'))) {
  const box = document.querySelector('.cp-box');
  const fit = (room, tall) => box.style.setProperty('--s', String(Math.min(1, room / ${w}, tall / ${h})));
  const screen = () => { const f = document.querySelector('.cp-fit'); fit(f.clientWidth, f.clientHeight); };
  screen();
  addEventListener('resize', screen);
  addEventListener('beforeprint', () => fit(1047, 655));
  addEventListener('afterprint', screen);
}
const gtBadgeUp = (z) => { const need = ${GT_BADGE_FLOOR} / (${GT_BADGE_LETTER} * z);
  return { up: Math.min(${GT_BADGE_MOST}, Math.max(1, need)), far: need > ${GT_BADGE_MOST} + 1e-9 }; };
const canvas = document.querySelector('.cp-canvas');
const badges = (s) => { const b = gtBadgeUp(s); canvas.style.setProperty('--gt-up', b.up.toFixed(3)); canvas.classList.toggle('gt-far', b.far); };
const shown = () => badges(document.querySelector('.cp-box').getBoundingClientRect().width / ${w});
shown();
addEventListener('resize', shown);
addEventListener('beforeprint', () => badges(Math.min(1, 1047 / ${w}, 655 / ${h})));
addEventListener('afterprint', shown);
})();`;
  return ['<!doctype html>', `<html lang="${I18N_DATA.locale || 'en-GB'}" data-theme="light">`, '<head>', '<meta charset="utf-8">',
    `<title>${esc(o.title)}</title>`, `<style>${o.rules}</style>`, `<style>${style}</style>`, '</head>',
    '<body class="cp">', `<div class="cp-controls"><button type="button" id="cp-print">${esc(t('themes.table.print'))}</button></div>`,
    '<div class="cp-page">', `<h1 class="cp-title">${esc(o.heading)}</h1>`,
    `<div class="cp-fit"><div class="cp-box"><div class="cp-canvas${o.gets ? ' gets-mode' : ''}">`,
    `<div class="th-world th-whole" style="left: ${-o.box.x}px; top: ${-o.box.y}px">${o.html}</div>`,
    '</div></div></div>', '</div>', `<script>${script}</script>`, '</body>', '</html>', ''].join('\n');
}

/* Canvas, under Export: the tab opens on the press, which is what the browser allows, a save
   still to go is written first, and the page goes in once saved. A canvas with nothing on it says
   so and opens nothing. On GETs a participant note comes only with Include participant notes. */
async function thCanvasPrint(opts = {}) {
  thXmenu(false);
  if (!TH.live || !TH.meta || TH.busy) return;
  thTitleDone(true);
  thNoteDone(true);
  if (thGets()) gtRowNoteDone(true);
  const notes = !thGets() || !!opts.notes;
  if (!thCanvasCopy(notes).box) { say(TH_CANVAS_EMPTY, 6000); return; }
  const tab = window.open('about:blank', '_blank');
  if (!tab) { say(t('themes.print.blocked'), 8000); return; }
  if (TH.dirty || TH.chain || TH.saveTimer) {
    await thFlush();
    if (TH.dirty) { tab.close(); say(t('themes.unsaved.printed'), 6000); return; }
  }
  const page = thCanvasMade(notes);
  if (!page) { tab.close(); say(TH_CANVAS_EMPTY, 6000); return; }
  tab.document.open();
  tab.document.write(page);
  tab.document.close();
}

/* The canvas's page as Print shows it, or null when
   nothing is on the canvas. The board is only read. */
function thCanvasMade(notes) {
  const made = thCanvasCopy(notes);
  if (!made.box || !TH.live || !TH.meta) return null;
  // the bar's name, the case's pseudonym on PETs and the project's on GETs
  const heading = thCanvasTitle(thCaseLabel(), TH.meta.name);
  return thCanvasPage({ html: made.html, box: made.box, rules: thCanvasRules(), heading, gets: thGets(),
    title: t('themes.canvas.page_title', { name: heading.split(' · ').join(' - '), unit: thGets() ? thGetWord(true) : t('themes.unit.pets') }) });
}

/* Save as PDF and Save as an image on the canvas (1 November 2026, exportA, Adam: "Canvas should give both a PDF
   and an image"). Since 9 November 2026 (typst5, Adam: Typst for every PDF and picture, no fallback) the server
   draws the board from its file with Typst, laid out by the canvas's own rule, and writes the file where the
   table's PDF goes, beside the workbook, or for the GETs at the project's root, a participant's LPETs beside their
   workbook (`/api/themes-export` or `/api/gets-boards` with `op` `canvas`), the same in the window on every
   computer and in a browser's tab. Quotes on cards goes as the canvas shows it, and on GETs a participant note only
   with Include participant notes. The line after names the file, with Show in Finder on a Mac, or says why it could
   not be made, and nothing is written. A save still to go is written first, and nothing on the board changes. */
async function thCanvasOut(kind, opts = {}) {
  thXmenu(false);
  if (!TH.live || !TH.meta || TH.busy) return;
  thTitleDone(true);
  thNoteDone(true);
  if (thGets()) gtRowNoteDone(true);
  const notes = !thGets() || !!opts.notes;
  if (!thCanvasCopy(notes).box) { say(TH_CANVAS_EMPTY, 6000); return; }
  await thFlush();
  if (TH.dirty) { say(t('themes.unsaved.exported'), 6000); return; }
  const body = { op: 'canvas', kind, board: TH.meta.id, quotes: thQuotesWay() };
  let made = null;
  try {
    made = thGets()
      ? await api('/api/gets-boards', Object.assign(body, { root: TH.root || '', notes },
        TH.lpets ? { workbook: TH.path, lpets: '1' } : {}))
      : await api('/api/themes-export', Object.assign(body, { workbook: TH.path, version: TH.meta.id }, thWhere()));
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : (err.message || t(kind === 'png' ? 'themes.canvas.png_failed' : 'themes.pdf.failed')), 9000);
    return;
  }
  // a server from before it names no file
  if (!made || !made.path) { say(RESTART_LINE, 6000); return; }
  const name = (made.version && made.version.name) || TH.meta.name;
  thExported({ shown: made.shown, name, reveal: !thGets() || !!TH.lpets, word: false });
}

/* ── the cases ── */

/* The case switcher, the case's name in the bar with its chevron: every case of the project with a
   themes file, by its pseudonym, this one ticked, each with the board it opens on under its name,
   its Current board when it has one and else the board last open, and Open as table at its right.
   The list is asked for each time the menu opens, and nothing is written. A server from before it
   says to restart in the menu. */
async function thCasemenu(open) {
  if (TH.mode === 'gets' && !TH.lpets) open = false;
  TH.casemenu = !!open && TH.live;
  const menu = $('th-casemenu');
  if (!menu) return;
  menu.hidden = !TH.casemenu;
  $('th-cases').setAttribute('aria-expanded', String(TH.casemenu));
  const ask = ++TH.casesAsk;
  if (!TH.casemenu) return;
  thVmenu(false);
  thXmenu(false);
  thCasemenuDraw([]);
  let data;
  try {
    data = await api('/api/themes-cases', { workbook: TH.path });
  } catch (err) {
    if (ask === TH.casesAsk && TH.casemenu) thCasemenuDraw([], needsRestart(err) ? RESTART_LINE : err.message);
    return;
  }
  if (ask === TH.casesAsk && TH.casemenu) thCasemenuDraw(data.cases || []);
}

function thCasemenuDraw(cases, said = '') {
  TH.cases = cases;
  const menu0 = (on) => { const m = $('th-casemenu'); if (m && m.classList) m.classList.toggle('pp-menu', on); };
  const mark = `<span class="th-vchosen">${TH_CHOSEN_ICON}<span class="th-vchosen-word">${esc(t('themes.board.current'))}</span></span>`;
  let html = `<p class="section-label th-vhead">${esc(t('themes.cases.head'))}</p>`;
  // each participant with their picture, label and the pen portrait's first two lines (pbiobuild, layout A)
  const people = cases.some((c) => c.person);
  menu0(people);
  cases.forEach((c, i) => {
    const p = c.person || {};
    const pic = people ? personPic(c.person, 32) : '';
    const text = `<span class="th-vtext"><span class="th-vline"><span class="th-vlabel">${esc(people ? caseShown(c.case) : c.case)}</span></span>`
      + (p.label ? `<span class="pp-label">${esc(p.label)}</span>` : '')
      + `<span class="th-vnote">${esc(c.board_name)}${thWithAi(c.with_ai)}${c.chosen ? mark : ''}</span>`
      + (p.portrait ? `<span class="pp-bio">${esc(p.portrait)}</span>` : '') + '</span>';
    const item = c.current
      ? `<div class="th-vitem on"${p.portrait ? ` title="${escAttr(p.portrait)}"` : ''}><span class="th-vcheck">${TH_TICK_ICON}</span>${pic}${text}</div>`
      : `<button type="button" class="ghost th-vitem" tabindex="-1" data-case="${i}" title="${escAttr(t('themes.cases.on_board', { name: c.case, board: c.board_name }))}"><span class="th-vcheck"></span>${pic}${text}</button>`;
    // another case also opens beside this one, read-only, the canvas split in two
    const beside = c.current || TH.lpets ? '' : `<button type="button" class="ghost small th-ctable" tabindex="-1" data-beside="${i}"`
      + ` title="${escAttr(t('themes.cases.beside_tip', { board: c.board_name, name: c.case }))}">${esc(t('themes.cases.beside'))}</button>`;
    // and every participant, this one too, in a window of its own on its statements (20 October)
    const win = `<button type="button" class="ghost small th-ctable" tabindex="-1" data-window="${i}"`
      + ` title="${escAttr(t('themes.cases.window_tip', { name: c.case }))}">${esc(t('themes.board.window'))}</button>`;
    const table = TH.lpets ? '' : `<button type="button" class="ghost small th-ctable" tabindex="-1" data-table="${i}"`
      + ` title="${escAttr(t('themes.cases.table_tip', { board: c.board_name, name: c.case }))}">${esc(t('themes.cases.table'))}</button>`;
    html += `<div class="th-crow">${item}<span class="th-cacts">${win}${beside}${table}</span></div>`;
  });
  if (said) html += `<p class="th-vsaid">${esc(said)}</p>`;
  const menu = $('th-casemenu');
  menu.innerHTML = html;
  if (typeof menuRoles === 'function') menuRoles(menu);
  const box = $('th-cases').getBoundingClientRect();
  // with the participants' pictures and portraits hung clear of the band's foot (pbiobuild, as drawn)
  const foot = people && $('th-band') && !$('th-band').hidden ? $('th-band').getBoundingClientRect().bottom + 10 : 0;
  menu.style.left = `${Math.max(8, Math.min(box.left - 6, window.innerWidth - menu.offsetWidth - 8))}px`;
  menu.style.top = `${Math.max(box.bottom + 8, foot)}px`;
}

/* Another case's PETs from the switcher: this canvas saved first, then that case opens on its
   Current board, or else the board last open, with the way back to the case list. Opening it writes
   nothing there. */
async function thCaseGo(c) {
  thCasemenu(false);
  if (!c || !TH.live || TH.busy) return;
  thTitleDone(true);
  thNoteDone(true);
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  // on LPETs that participant's LPETs, and at a timepoint that participant's PETs at the same timepoint
  themesOpen(c.path, Object.assign({ back: () => { loadLibrary().catch((err) => say(err.message, 9000)); },
    label: c.case, to: 'cases' }, TH.lpets ? { gets: true, lpets: true } : { board: c.board }, TH.lpets ? {} : thWhere()));
}

/* Open in a new window, from the switcher: that participant's statements in a window of its own, so a
   transcript can stand on one screen and a board on another (20 October). Nothing is written. */
function thCaseWindow(c) {
  thCasemenu(false);
  if (c && c.path) openInWindow({ screen: 'work', path: c.path });
}

/* Open in a new window, from the board menu: the board on the canvas in a window of its own, saved first so
   the new window opens on it as it stands. The two keep each other up to date (see thStampTick). */
async function thWindow() {
  thVmenu(false);
  if (!TH.live || !TH.path || !TH.meta) return;
  const id = TH.meta.id;
  const spot = Object.assign(TH.mode === 'gets' ? { screen: 'gets', path: TH.path, board: id }
    : { screen: 'pets', path: TH.path, board: id, label: TH.label || '' }, thWhere());
  if (TH.dirty || TH.chain || TH.saveTimer) {
    await thFlush();
    if (TH.dirty) { say(t('themes.unsaved.window'), 6000); return; }
  }
  openInWindow(spot);
}

/* Open as table: that case's board, the one it opens on, in the print view in a tab of its own with
   the print dialog shut, read-only, so two tables or more sit side by side in separate tabs. This
   case's own entry writes a save still to go first. Nothing else is written. */
async function thTable(c) {
  thCasemenu(false);
  if (!c || !c.table) return;
  const waiting = !!c.current && !!(TH.dirty || TH.chain || TH.saveTimer);
  const tab = window.open(waiting ? 'about:blank' : c.table, '_blank');
  if (!tab) { say(t('themes.print.table_blocked'), 8000); return; }
  if (!waiting) return;
  await thFlush();
  if (TH.dirty) { tab.close(); say(t('themes.unsaved.table'), 6000); return; }
  tab.location.href = c.table;
}

/* ── the AI's help ── */

/* With the switch in Settings on: AI suggest for titles in the Inspector, a PET's on the PETs screen
   and a GET's on the GETs screen, which moves nothing on the canvas by itself: a title goes on only
   when it is picked. It asks the PETs model set in Settings under PETs, the Experiential statements
   one unless another is chosen. `TH.ai.on` is the switch, AI features, as aiOn in app.js reads it from
   the settings, or as the server read it from the same file. New AI board, AI review and AI revise
   went on 11 November 2026 (aiout, Adam: his own agent through MCP does that work). */
// IPA's, never in a thematic analysis project (tadraw)
const thAiOn = () => !!(TH.ai && TH.ai.on) && !thTa();

/* The route the titles ask: the PETs screen's, or on the GETs screen its own. */
const thAiPath = () => (TH.mode === 'gets' ? '/api/gets-ai' : '/api/themes-ai');

/* The switch or the model changed: the Inspector's titles and the Guidance tab's foot drawn afresh. */
function thAiDraw() {
  if (TH.panelOpen) thPanelDraw();
  if (TH.boardOpen) thBoardDraw();
}

/* The names block in the panel, for a label alone, a PET or a sub-theme, and never for a card: the
   control, and the three names once they are back, each a pick, with Edit beside it and a cross
   for the lot, and the server's line when the quotes of some statements went for room. The names
   show beside the label they were asked for and nowhere else. */
function thNamesHtml(item, gets = null) {
  if (!thAiOn() || !item || item.kind !== 'group') return '';
  if (thLocked(TH.v)) return '';
  const nm = TH.names && TH.names.key === thPanelKey(item) ? TH.names : null;
  const busy = !!(nm && nm.busy);
  let html = '<div class="th-names"><div class="th-names-head">'
    + `<button type="button" class="ghost small th-names-go${busy ? ' busy' : ''}" tabindex="-1" data-names="go"${busy ? ' disabled' : ''} title="${escAttr(t('themes.names.tip', { unit: gets ? gets.unit : thUnit(TH.v, item.id) }))}">`
    + `${TH_SPARK_ICON}${esc(busy ? t('themes.ai.asking') : (gets ? t('themes.names.gets') : t('themes.names.pets')))}</button>`;
  if (nm && !busy && (nm.names.length || nm.error)) {
    html += `<button type="button" class="th-names-close" tabindex="-1" data-names="close" aria-label="${escAttr(t('themes.names.ignore'))}" title="${escAttr(t('themes.names.ignore'))}">${TH_DEL_ICON}</button>`;
  }
  html += '</div>';
  if (nm && nm.error) html += `<p class="th-names-note failed">${esc(nm.error)}</p>`;
  else if (nm && nm.names.length) {
    html += `<ul class="th-names-list">${nm.names.map((name, i) => `<li><button type="button" class="th-name-pick" tabindex="-1" data-name-pick="${i}" title="${escAttr(t('themes.names.rename_tip'))}">${esc(name)}</button>`
      + `<button type="button" class="ghost small th-name-edit" tabindex="-1" data-name-edit="${i}">${esc(t('themes.names.edit'))}</button></li>`).join('')}</ul>`;
    if (nm.said) html += `<p class="th-names-note">${esc(nm.said)}</p>`;
  }
  return `${html}</div>`;
}

/* `n`, or AI suggest PET titles in the Inspector, on a label: the canvas is saved, then the label
   goes by its id and the server builds the prompt from the board and the workbook, and three
   titles come back to the Inspector beside it, which `n` opens when it is closed, since that is
   where they land. Cards selected with no label are grouped first. A second press asks again. */
async function thNamesAsk() {
  if (!TH.live || TH.busy || !thAiOn() || thRefuse('names')) return;
  thTitleDone(true);
  thNoteDone(true);
  // what the Inspector shows stands in for nothing selected only while it is open
  const target = thNamesTarget(TH.v, TH.sel, TH.panelOpen ? TH.panel : null);
  if (target && target.kind === 'cards') { say(TH_GROUP_FIRST); return; }
  if (!target) { say(t('themes.names.select')); return; }
  const body = thNamesBody(TH.v, target);
  if (!body.statements.length) { say(t('themes.names.empty')); return; }
  const key = thNamesKey(target);
  const item = { kind: 'group', id: target.id };
  const ask = ++TH.namesAsk;
  TH.names = { key, target, busy: true, names: [], error: '', said: '' };
  thInspectorOpen(item);
  let next;
  try {
    // the server reads the board as the file holds it, so what is on the canvas is written first
    await thFlush();
    const data = await api(thAiPath(), Object.assign({ workbook: TH.path, op: 'names' }, body));
    next = { key, target, busy: false, names: data.names || [], error: (data.names || []).length ? '' : t('themes.names.none'),
      said: data.said || '' };
  } catch (err) {
    next = { key, target, busy: false, names: [], error: needsRestart(err) ? RESTART_LINE : err.message, said: '' };
  }
  if (ask !== TH.namesAsk || !TH.live) return;
  TH.names = next;
  if (TH.panelOpen) thPanelDraw();
}

/* A name picked is one step of undo, like a rename: it becomes the label's title. Edit opens the
   label's box with the name in it to be typed over. */
function thNameApply(i, edit) {
  const t = TH.names;
  if (!TH.live || TH.busy || !t || t.busy || !t.names[i] || thRefuse('names')) return;
  const name = t.names[i];
  const v = TH.v;
  const g = thGroup(v, t.target.id);
  if (!g) { TH.names = null; thPanelDraw(); return; }
  TH.names = null;
  if (edit) { thRender(); thTitleOpen(g.id, { value: name }); return; }
  if (g.label === name) { thRender(); return; }
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  g.label = name;
  thDone(before, t('themes.step.renamed'), { settle: [], was, labels: [g.id] });
}

/* ── work done outside the page, by an AI agent in a conversation ── */

/* A statement's short id, S1 on, small and faint after its timecode in the Inspector, so he and an
   agent can name it in a conversation, and so only with AI features on. The command line counts
   them the same way, sheet by sheet down the transcript, and a server from before them sends none. */
function thSidHtml(key) {
  const sid = TH.mode === 'pets' && thAiOn() ? (TH.sids || {})[key] : '';
  return sid ? `<span class="th-sid" title="${escAttr(t('themes.sid_tip'))}">${esc(sid)}</span>` : '';
}

/* A statement an agent left out of every PET carries why, kept in the board's `ai` as an AI
   board's discards keep theirs. In no PET it shows under the statement in the Inspector, in the
   pile's words, and in the bin the pile shows it as it shows every reason. */
function thLeftOutHtml(v, key, owner) {
  if (owner !== undefined || v.discarded.includes(key) || !thWhy(v, key)) return '';
  return `<div class="th-pile-why th-left-why">${esc(t('themes.card.left_out', { why: thWhy(v, key) }))}</div>`;
}

/* The boards as the page last saw them, by their `updated`, from an open, a board op or its own
   save. A board the file holds that is not here was added outside, and the board on the canvas
   with another `updated` was changed outside. */
function thKnow(boards) {
  TH.known = {};
  for (const b of boards || []) if (b && b.id) TH.known[b.id] = b.updated || '';
  // a stamp asked before this load answers about the boards before it, so it lands nowhere
  TH.stampAsk += 1;
}

/* The line in the top right of the canvas, one at a time in that corner, or none. */
function thOutside(info) {
  TH.outside = info || null;
  const box = $('th-outside');
  if (!box) return;
  box.hidden = !info;
  if (!info) return;
  thExported(null);
  $('th-outside-line').textContent = info.line;
  box.title = info.said || '';
  $('th-outside-show').textContent = info.added ? t('themes.outside.show') : t('themes.outside.update');
}

/* What the line says of a board, a conversation when an agent made or changed it and another
   window when not. A change made outside the app says Changes made elsewhere (20 October, Adam's
   call from a tester's feedback), and these words go in its tooltip. */
const TH_ELSEWHERE = t('themes.outside.elsewhere');
function thOutsideLine(b, added) {
  const chat = !!(b.made || b.changed);
  return added ? t(chat ? 'themes.outside.added_chat' : 'themes.outside.added_out', { name: b.name }) : t(chat ? 'themes.outside.changed_chat' : 'themes.outside.changed_out');
}

/* On a focus of the window and every thirty seconds: the stamp, which reads and writes nothing,
   and the line when a board was added or the one on the canvas changed. Never while the page has
   a save of its own on the way, an act under way or a revision on view, and `now` asks even so. */
async function thStampTick(now) {
  if (!TH.live || !TH.path || $('themes').hidden || (typeof document !== 'undefined' && document.hidden)) return;
  // a refused save's card holds the corner until Reload or Overwrite, and a change being taken in is answered
  // by what it brings
  if (TH.stale || TH.taking) return;
  if (now !== true &&(TH.busy || TH.chain || TH.saveTimer || TH.dirty || TH.drag || TH.viewing)) return;
  const ask = ++TH.stampAsk;
  const path = TH.path;
  const mode = TH.mode;
  let data;
  try {
    data = await api('/api/stamp', { workbook: path, gets: mode === 'gets' });
  } catch { return; }
  if (ask !== TH.stampAsk || path !== TH.path || mode !== TH.mode || !TH.live) return;
  const seen = thStampSeen(data, TH.known, TH.meta ? TH.meta.id : null);
  // on GETs, the cases whose PETs changed since they came in, each made in a window of this app or outside it
  const cases = mode === 'gets' && Array.isArray(data.cases) ? data.cases : [];
  const own = cases.filter((c) => c.outside === false).map((c) => c.case);
  const far = cases.filter((c) => c.outside !== false && !(TH.farLeft || new Set()).has(c.case)).map((c) => c.case);
  // A change from another window of this Idiograph is his own (Adam, 20 October: two-screen working), and
  // comes onto the board by itself. A server from before says nothing of where, and the notice shows.
  const outside = data.outside !== false;
  // and a passage's statement reworded in the workbook by another window of this app, on Experiential
  // statements or another board, comes onto this board by itself as well (20 October, two windows in step)
  const wb = data.workbook && data.workbook.at ? data.workbook : null;
  const wbSeen = !!wb && TH.wbAt !== undefined && TH.wbAt !== null && TH.wbPath === path && wb.at !== TH.wbAt;
  if (wb && (TH.wbPath !== path || TH.wbAt === undefined || TH.wbAt === null || !wb.here)) { TH.wbPath = path; TH.wbAt = wb.at; }
  if (seen && !outside) {
    await thOwnLoad(seen);
  } else if (wbSeen && wb.here && !(seen && outside)) {
    TH.wbAt = wb.at;
    await thOwnLoad({ changed: false });
  }
  if (own.length && TH.live && TH.path === path && TH.mode === mode) await gtTakeAll(own);
  const board = seen && outside ? seen : null;
  if (!board && !far.length) return;
  if (!TH.live || TH.path !== path || TH.mode !== mode || TH.stale) return;
  const info = board ? Object.assign({}, board) : { board: null, changed: false };
  info.cases = far;
  info.added = !!board && !board.changed && !far.length;
  info.said = board ? board.line : t('themes.outside.cases', { names: far.map((n) => (gtCase(n) || { who: n }).who).join(', ') });
  info.line = info.added ? board.line : TH_ELSEWHERE;
  thOutside(info);
}

/* A change from another window of this app, taken onto the canvas by itself: the canvas's own work saved
   first, then the board as the file holds it, where he had the view and the selection gone. Its undo
   starts afresh, since the steps before it no longer lead to what is there. */
async function thOwnLoad(seen) {
  if (!TH.live || TH.busy || TH.viewing || TH.drag || TH.editing || TH.cardEdit || TH.writing) return;
  const id = TH.meta ? TH.meta.id : null;
  await thFlush();
  if (TH.dirty || !TH.meta || TH.meta.id !== id) return;
  let data;
  try {
    data = TH.mode === 'gets' ? await api('/api/gets', { workbook: TH.path, board: id })
      : await api('/api/themes', { workbook: TH.path, board: id });
  } catch { return; }
  if (!TH.live || !TH.meta || TH.meta.id !== id || TH.dirty || TH.drag) return;
  if (seen.changed) {
    delete TH.stacks[id];
    if (TH.undoBoard === id) { TH.undoBoard = null; TH.undo = []; TH.redo = []; }
  }
  thLoad(data, { fit: false });
}

/* What a stamp shows the page has not seen: the board on the canvas changed outside first, else
   the newest board added, or null. */
function thStampSeen(data, known, on) {
  const boards = Array.isArray(data && data.boards) ? data.boards : [];
  const here = boards.find((b) => b.id === on);
  if (here && known[here.id] !== undefined && here.updated && here.updated !== known[here.id]) {
    return { board: here.id, updated: here.updated, changed: true, line: thOutsideLine(here, false) };
  }
  const added = boards.filter((b) => !(b.id in known));
  if (!added.length) return null;
  const b = added[added.length - 1];
  return { board: b.id, updated: b.updated, changed: false, line: thOutsideLine(b, true) };
}

/* Show it: the canvas's own work saved first through the autosave, then the board loaded, the one
   added fitted to the view and the one changed where he had it. A board changed under him starts
   its undo afresh, since the steps before it no longer lead to what is there. A save of his refused
   because of the change is kept in the board's History by the server, so nothing of his is lost. */
async function thOutsideShow() {
  const o = TH.outside;
  if (!o || !TH.live || TH.busy) return;
  TH.taking = true;
  try { await thOutsideTake(o); } finally { TH.taking = false; }
}

async function thOutsideTake(o) {
  thOutside(null);
  thViewEnd();
  await thFlush();
  TH.dirty = false;
  if (o.cases && o.cases.length) (TH.farLeft || new Set()).clear();
  // only the cases' PETs changed: their changes taken, the board as it is
  if (!o.board) { await gtTakeAll(o.cases || []); return; }
  let data;
  try {
    data = TH.mode === 'gets' ? await api('/api/gets', { workbook: TH.path, board: o.board })
      : await api('/api/themes', { workbook: TH.path, board: o.board });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 6000); return; }
  if (o.changed) {
    delete TH.stacks[o.board];
    if (TH.undoBoard === o.board) { TH.undoBoard = null; TH.undo = []; TH.redo = []; }
  }
  thLoad(data, { fit: !o.changed });
  // a line the refused save of his asked for on the way is answered by what is now on the canvas
  thOutside(null);
  if (o.cases && o.cases.length) await gtTakeAll(o.cases);
}

/* Its cross: the change is left for later, and the line does not come back for it. */
function thOutsideClose() {
  const o = TH.outside;
  if (o && o.board) TH.known[o.board] = o.updated || TH.known[o.board] || '';
  if (o && o.cases) { TH.farLeft = TH.farLeft || new Set(); for (const n of o.cases) TH.farLeft.add(n); }
  thOutside(null);
}

/* A save refused because the board changed since the page read it, in another window or by an agent
   (19 October): nothing was saved, the canvas stays as he left it, and the card in the corner says so
   with Reload first and Overwrite, the canvas saved over the board as it now stands. The autosave
   waits until he picks one. */
const TH_STALE_LINE = t('themes.stale.line');
const TH_STALE_RELOADED = t('themes.stale.reloaded');

function thStaleShow(info) {
  TH.stale = { board: String(info.board || ''), v: String(info.v || '') };
  TH.staleKept = null;
  thExported(null);
  thOutside(null);
  thStaleDraw();
}

function thStaleDraw() {
  const box = $('th-stale');
  if (!box) return;
  box.hidden = !TH.stale && !TH.staleKept;
  $('th-stale-line').textContent = TH.staleKept ? TH_STALE_RELOADED : TH_STALE_LINE;
  $('th-stale-acts').hidden = !!TH.staleKept;
  $('th-stale-back').hidden = !TH.staleKept;
}

function thStaleHide() {
  TH.stale = null;
  TH.staleKept = null;
  const box = $('th-stale');
  if (box) box.hidden = true;
}

/* Reload: the canvas kept first in the board's History, "The canvas before Reload", then the board as
   the file holds it now on the canvas, where he had the view, its undo started afresh since the steps
   before it no longer lead to what is there. The card stays, saying where his canvas is, with Put my
   canvas back, which restores it as the History tab's Restore does, until his next save goes through. */
async function thStaleReload() {
  const s = TH.stale;
  if (!s || !TH.live || TH.busy || !TH.meta || s.board !== TH.meta.id) return;
  TH.busy = true;
  let kept = null;
  let data;
  try {
    const route = TH.mode === 'gets' ? '/api/gets-save' : '/api/themes-save';
    kept = (await api(route, { workbook: TH.path, version: thBody(thLiveV(), TH.meta), keep: true })).kept || null;
    data = TH.mode === 'gets' ? await api('/api/gets', { workbook: TH.path, board: s.board })
      : await api('/api/themes', { workbook: TH.path, board: s.board });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 6000);
    return;
  } finally {
    TH.busy = false;
  }
  clearTimeout(TH.saveTimer);
  TH.saveTimer = null;
  TH.dirty = false;
  thViewEnd();
  delete TH.stacks[s.board];
  if (TH.undoBoard === s.board) { TH.undoBoard = null; TH.undo = []; TH.redo = []; }
  thLoad(data, { fit: false });
  thOutside(null);
  thSaveLine('done', TH_SAVED);
  if (kept && kept.id) {
    TH.staleKept = { board: s.board, revision: kept.id };
    thStaleDraw();
  }
}

/* Put my canvas back: the canvas kept before Reload restored onto the board, the board as it stood
   kept in History first, as Restore does. */
async function thStaleBack() {
  const k = TH.staleKept;
  thStaleHide();
  if (!k || !TH.meta || k.board !== TH.meta.id) return;
  await thRestoreRevision(k.revision);
}

/* Overwrite: the canvas saved over the board as it now stands, the version the refusal named sent
   with it, so a change made after that one is refused in turn. */
function thStaleOverwrite() {
  const s = TH.stale;
  thStaleHide();
  if (!s || !TH.live || !TH.meta || s.board !== TH.meta.id) return;
  TH.meta.v = s.v;
  thOutside(null);
  TH.dirty = true;
  thSave();
}

function thOutsideBoot() {
  $('th-stale').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-stale-reload').onclick = () => thStaleReload();
  $('th-stale-over').onclick = () => thStaleOverwrite();
  $('th-stale-back').onclick = () => thStaleBack();
  window.addEventListener('focus', () => thStampTick());
  // every few seconds on PETs, so a statement reworded in another window shows here a moment later, and on
  // GETs every thirty, whose look surveys every case (20 October)
  setInterval(() => {
    if (TH.mode === 'gets' && Date.now() - (TH.stampLast || 0) < 30 * 1000) return;
    TH.stampLast = Date.now();
    thStampTick();
  }, 4 * 1000);
  $('th-outside').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-outside-show').onclick = () => thOutsideShow();
  $('th-outside-close').onclick = () => thOutsideClose();
}

/* ── the pointer ── */

/* What the pointer is over: the bin, or the title strip of a theme, its label, leaving out what moves.
   Only a title strip takes in what is let go on it (18 October, Adam's choice from a drawing, where with
   three levels of grouping every frame and card under the pointer offered a merge while he only meant to
   move or reorder inside a sub-PET): anywhere else, in a theme's body or on the open canvas, a drop only
   moves, at every level of nesting, on PETs and on GETs. The theme a drop on a strip joins is `group`.
   Statements alone are the one exception (19 October, Adam on the shots): let go in a theme's body they
   move into the innermost PET, sub-PET or group the pointer is in, at the line shown, `body` and
   `frame` set, by the frames as they stood when the drag began, `drag.frames`. A row pulled in from the
   Cases panel takes the same.
   Design A (Adam, 31 October, after the drag audit): a PET's sub-PET, or a sub-PET's group, let go in
   another PET's or sub-PET's body goes in too, keeping its level, by the frames one level above its own
   (see thBodiesFor), and a PET goes into no body. On a title anything goes one level under it, a PET onto
   another's title becoming its sub-PET. No PET or sub-PET moves out of the way while a drag lasts, so the
   hot spot kept where a title strip stood before it made way (19 October) is gone. Alt joins nothing: with
   it held nothing on the canvas takes the drop, a title, a body or a card's middle. */
function thTargetAt(clientX, clientY) {
  const el = document.elementFromPoint(clientX, clientY);
  // the sidebar in place of the bin (20 October): a card let go on Set aside is set aside, and on the PETs
  // board one let go anywhere else on the sidebar goes back to Not placed
  if (el && TH.drag && el.closest('#th-aside')) return { discard: true };
  if (el && TH.drag && TH.mode !== 'gets' && el.closest('#th-cpanel')) return { wait: true };
  if (!el || !thStage().contains(el)) return null;
  if (el.closest('.th-ui')) return null;
  if (TH.drag && TH.drag.alt) return null;
  const moving = TH.drag ? TH.drag.moving : new Set();
  const label = el.closest('.th-label');
  if (label && !moving.has(label.dataset.group)) return { group: label.dataset.group, onLabel: true };
  // the middle of a statement's card stacks what is dragged under it (19 October)
  const under = thStackHit(clientX, clientY);
  if (under) return { stack: under };
  const pt = thToWorld(clientX, clientY);
  const bodies = TH.drag ? TH.drag.frames : thFrames(TH.layout);
  const body = bodies ? thInnermost(bodies, pt, moving) : null;
  return body ? { group: body, frame: true, body: true } : null;
}

/* the smallest of `boxes`, by theme id, that holds the point, leaving out what moves */
function thInnermost(boxes, pt, moving) {
  let best = null;
  let area = Infinity;
  for (const [id, b] of Object.entries(boxes)) {
    if (moving.has(id) || !thIsGroup(TH.v, id) || !b || !(b.w > 0) || !(b.h > 0)) continue;
    if (pt.x < b.x || pt.x > b.x + b.w || pt.y < b.y || pt.y > b.y + b.h) continue;
    if (b.w * b.h < area) { best = id; area = b.w * b.h; }
  }
  return best;
}

/* each theme's frame in `layout`, by id, copied, for a theme with a body */
function thFrames(layout) {
  const out = {};
  for (const [id, l] of Object.entries(layout || {})) {
    if (l && l.body && l.frame) out[id] = { x: l.frame.x, y: l.frame.y, w: l.frame.w, h: l.frame.h };
  }
  return out;
}

/* Whether a drop on the title strip of `target` merges: what is dragged comes into that theme, any of
   it not in it already. With Alt held, what is in it already leaves it there instead. */
function thMergeInto(v, moving, target) {
  if (!thIsGroup(v, target) || moving.has(target)) return false;
  const parents = thParents(v);
  const top = [...moving].filter((it) => !moving.has(parents[it]));
  return top.some((it) => parents[it] !== target);
}

/* The theme a drop there joins lights its title strip and its frame, unless what moves is in it
   already, by its title or, since 31 October (design A), by its body, the frame of the PET or sub-PET under
   the pointer outlined in its tint and its title tinted. Only the strip it was lit on and the one it lights
   now are touched, so a drag that stays over one place changes nothing a frame. */
function thHover(hit) {
  thSideArm(!!TH.drag, hit);
  // the card a drop would stack under shows an outline
  const on = hit && hit.stack ? hit.stack : null;
  if (TH.stackAt !== on) {
    if (TH.stackAt && TH.els.cards[TH.stackAt]) TH.els.cards[TH.stackAt].classList.remove('stack-on');
    if (on && TH.els.cards[on]) TH.els.cards[on].classList.add('stack-on');
    TH.stackAt = on;
    // and what is dragged lets it show through while it is over that card's middle
    for (const it of TH.drag ? TH.drag.moving : []) {
      if (TH.els.cards[it]) TH.els.cards[it].classList.toggle('over-stack', !!on);
    }
  }
  const want = hit && (hit.onLabel || hit.body) && TH.drag && thMergeInto(TH.v, TH.drag.moving, hit.group) ? hit.group : null;
  if (TH.hoverAt === want) return;
  for (const id of [TH.hoverAt, want]) {
    if (!id) continue;
    if (TH.els.labels[id]) TH.els.labels[id].classList.toggle('target', id === want);
    if (TH.els.frames[id]) TH.els.frames[id].classList.toggle('target', id === want);
  }
  TH.hoverAt = want;
}

/* The title strip a drop would merge into, while the drag is over it (18 October, Adam's choice from a
   drawing): it lights in its theme's tint and reads "Merge into" and its title, laid over the strip at
   its own size and type, so nothing under it moves. Only where the drop merges (see thMergeInto), and
   it goes the moment the pointer leaves the strip, and at the drop. */
function thMergeShow(hit) {
  const el = $('th-merge');
  if (!el) return;
  const d = TH.drag;
  const target = d && hit && hit.onLabel && thMergeInto(TH.v, d.moving, hit.group) ? hit.group : null;
  const box = target && TH.layout[target] && TH.layout[target].label;
  if (!box) { el.hidden = true; return; }
  const label = TH.els.labels[target];
  el.className = `th-merge ${thTintClass(thTints(TH.v)[target])}${label && label.classList.contains('upper') ? ' upper' : ''}`;
  el.style.left = `${box.x}px`;
  el.style.top = `${box.y}px`;
  el.style.minWidth = `${box.w}px`;
  el.style.minHeight = `${box.h}px`;
  el.lastElementChild.textContent = thLabelShown(thGroup(TH.v, target).label) || TH_UNTITLED;
  el.hidden = false;
}

/* Where what is dragged comes to read among the members of the PET or sub-PET it moves in, `home`, in
   the order the canvas reads a theme (see thThemeOrder), the first of what is dragged at its place:
   a line in the gap before the member it now reads before, standing up beside it on its row, or after
   the one it reads after, or lying across the gap between rows when it stands on a row of its own.
   Null on the open canvas, over a strip, and with no other member to read among. In the canvas's units,
   `thick` across. Statements coming in from elsewhere read among its members as if in it already, and
   since 31 October (design A) a sub-PET or a group coming in too, by its frame. */
function thInsertAt(v, layout, moving, home, thick) {
  if (!home || !thIsGroup(v, home)) return null;
  const parents = thParents(v);
  const coming = [...moving].filter((id) => !moving.has(parents[id]) && parents[id] !== home && (v.cards[id] || thIsGroup(v, id)));
  const order = coming.length
    ? thReadOrder(thThemeOrder(v, home, layout).concat(coming).map((m) => {
      const f = thIsGroup(v, m) && layout[m] ? layout[m].frame : null;
      const at = f || (thIsGroup(v, m) ? thGroup(v, m) : (v.cards[m] || thSticky(v, m)));
      return { id: m, x: at.x, y: at.y };
    }))
    : thThemeOrder(v, home, layout);
  const i = order.findIndex((id) => moving.has(id));
  if (i < 0 || !order.some((id) => !moving.has(id))) return null;
  const box = (id) => thSolid(v, thSize, layout, id);
  const lead = box(order[i]);
  const next = order.slice(i + 1).find((id) => !moving.has(id));
  const prev = order.slice(0, i).reverse().find((id) => !moving.has(id));
  const a = next !== undefined ? box(next) : null;
  const b = prev !== undefined ? box(prev) : null;
  const row = (o) => !!o && !!lead && Math.abs(o.y - lead.y) < TH_ROW;
  const gap = TH_MARGIN / 2;
  if (row(a)) return { x: a.x - gap - thick / 2, y: a.y, w: thick, h: a.h, along: false };
  if (row(b)) return { x: b.x + b.w + gap - thick / 2, y: b.y, w: thick, h: b.h, along: false };
  if (a) return { x: a.x, y: a.y - gap - thick / 2, w: a.w, h: thick, along: true };
  if (b) return { x: b.x, y: b.y + b.h + gap - thick / 2, w: b.w, h: thick, along: true };
  return null;
}

/* The insertion line drawn where a drop in a theme's body puts what is dragged in its order, 3 pixels
   across at any zoom, in the theme's tint, while the pointer is not over a title strip (18 October), and only
   when the drop changes the order or brings something in (26 October, see thInsertMoves). */
function thInsertShow(d) {
  const el = $('th-insert');
  if (!el) return;
  const home = d && !d.alt && !(d.hitNow && (d.hitNow.onLabel || d.hitNow.discard)) ? d.home : null;
  const at = home && d.layout && thInsertMoves(TH.v, d, home) ? thInsertAt(TH.v, d.layout, d.moving, home, 3 / TH.view.z) : null;
  if (!at) { el.hidden = true; return; }
  el.className = `th-insert ${thTintClass(thTints(TH.v)[home])}${at.along ? ' along' : ''}`;
  el.style.left = `${at.x}px`;
  el.style.top = `${at.y}px`;
  el.style.width = `${at.w}px`;
  el.style.height = `${at.h}px`;
  el.hidden = false;
}

function thDragStart() {
  const p = TH.press;
  thMenuClose();
  // a card dragged out of a stack shown open comes out of it as the drag starts, where it stood, and
  // the drag is one step of undo with it
  const lifted = p.item.kind === 'card' && thTopOf(TH.v, p.item.id) ? thStackLift(p.item.id) : null;
  if (lifted) p.add = false;
  if (!thSelected(p.item)) {
    if (!p.add) { TH.sel.cards.clear(); TH.sel.groups.clear(); }
    if (!p.add) TH.sel.stickies.clear();
    thSetOf(p.item).add(p.item.id);
    thDrawSel();
    // an open Inspector follows what is picked up, and a closed one stays closed
    TH.lastPick = p.item;
    thPanelFollow();
  }
  const v = TH.v;
  const moving = thMoving(v, TH.sel.cards, TH.sel.groups, TH.sel.stickies);
  const starts = {};
  for (const it of moving) {
    const at = thIsGroup(v, it) ? thGroup(v, it) : (v.cards[it] || thSticky(v, it));
    starts[it] = { x: at.x, y: at.y };
  }
  // everything that moves leans as it goes, and what came along with a label trails it
  const grabbed = new Set([...TH.sel.cards, ...TH.sel.groups, ...TH.sel.stickies].filter((it) => moving.has(it)));
  for (const it of moving) {
    const el = TH.els.cards[it] || TH.els.labels[it] || TH.els.stickies[it];
    if (!el) continue;
    // an ease still running from the last act gives way to the drag
    el.classList.remove('ease-from', 'easing', 'nudging', 'landing', 'sent', 'standing');
    el.style.scale = '';
    el.style.rotate = '';
    el.classList.add('dragging');
    if (!grabbed.has(it)) el.classList.add('trailing');
    // what moves is drawn over what stays, and stays on top once it is down
    el.parentNode.appendChild(el);
  }
  TH.z = TH.z.filter((key) => !moving.has(key)).concat(TH.z.filter((key) => moving.has(key)));
  // the tip about Alt follows what Alt takes out of its theme, and nothing else
  // a drag that carries a PET or a sub-theme of its own
  const parents = thParents(v);
  const nest = [...moving].some((it) => thIsGroup(v, it) && !moving.has(parents[it]));
  const cards = moving.size > 0 && [...moving].every((it) => !!v.cards[it]);
  // what it goes into when let go in a body, by the frames as they stand now, keeping its level (see thBodiesFor)
  // `home` is the place it makes way in and `layout` the board's as the drop would leave it, each move's
  TH.drag = { moving, grabbed, starts, nest, cards, frames: thBodiesFor(v, moving, TH.layout),
    before: lifted || thSnap(v, TH.removed), lifted: !!lifted, was: thLabelBoxes(TH.layout),
    from: thSpots(v), x0: p.x0, y0: p.y0, dx: 0, dy: 0, alt: !!p.alt, lean: 0, lastX: p.x0, still: null,
    tip: thLeavers(v, moving).size > 0, tipUnit: thTipUnit(v, moving, p.item.id), tipX: p.x0, tipY: p.y0,
    slides: new Map(), seen: null, raf: 0, hitNow: null, next: null, step: 0, home: null, layout: null,
    trail: grabbed.size < moving.size ? { x: 0, y: 0, t: 0, raf: 0 } : null };
  TH.hoverAt = null;
  thSideArm(true);
}

/* The neighbours make way while anything is dragged, in the place `hit` says it lands, worked out
   from where everything stood when the drag began (see thPreview), and what makes way slides
   there. */
function thWay(d, hit) {
  d.hitNow = hit;
  d.home = thWayHome(TH.v, d.moving, d.nest, hit, d.alt);
  // statements over another theme's body leave their own for it, which shows as they go (19 October), and
  // a sub-PET or a group the same since 31 October
  d.out = !!(hit && hit.body) && thMergeInto(TH.v, d.moving, hit.group);
  thNearRest(d, d.home);
  thPreview(TH.v, thSize, d, d.home);
  thWayShow(d);
}

/* What makes way slides over about 160 ms from where it shows to where the preview puts it, and a
   slide turned partway starts again from where it has got to, so nothing jumps. One back on its
   own spot is done with. With reduced motion each is there at once. Sets `d.seen`, the board as it
   shows, and asks for the next animation frame while anything is still sliding. */
function thWayShow(d, now = performance.now()) {
  const v = TH.v;
  const calm = thCalm();
  const shown = {};
  let busy = false;
  const slide = (id, at, start) => {
    if (d.moving.has(id) || !at || !start) return;
    let s = d.slides.get(id);
    const last = s ? s.to : start;
    if (at.x !== last.x || at.y !== last.y) {
      const was = s ? thWayAt(s, now, calm) : start;
      s = { from: { x: was.x, y: was.y }, to: { x: at.x, y: at.y }, t0: now };
      d.slides.set(id, s);
    }
    if (!s) return;
    const p = thWayAt(s, now, calm);
    if (!p.done) { shown[id] = { x: p.x, y: p.y }; busy = true; }
    else if (s.to.x === start.x && s.to.y === start.y) d.slides.delete(id);
  };
  for (const [key, c] of Object.entries(v.cards)) slide(key, c, d.from.cards[key]);
  for (const n of thStickies(v)) slide(n.id, n, (d.from.stickies || {})[n.id]);
  // a label with nothing in it moves by its own place, and any other follows what it holds
  for (const g of v.groups) {
    if (!g.members.some((m) => thExists(v, m)) && !thStickies(v).some((n) => n.in === g.id)) slide(g.id, g, d.from.groups[g.id]);
  }
  d.seen = busy ? thSeen(v, shown) : null;
  if (busy && !d.raf) d.raf = requestAnimationFrame(thWayTick);
  return busy;
}

/* one animation frame of the slides, the Merge following its frame back to its own spot */
function thWayTick() {
  const d = TH.drag;
  if (!d) return;
  d.raf = 0;
  thWayShow(d);
  thPlace(d);
  thMergeShow(d.hitNow);
}

function thDragMove(e) {
  const d = TH.drag;
  const v = TH.v;
  d.dx = (e.clientX - d.x0) / TH.view.z;
  d.dy = (e.clientY - d.y0) / TH.view.z;
  // the pointer's own move, which a rest a margin from the neighbours may shift (see thNearRest)
  d.free = { dx: d.dx, dy: d.dy };
  d.alt = e.altKey;
  d.px = e.clientX;
  d.py = e.clientY;
  for (const it of d.moving) {
    const at = thIsGroup(v, it) ? thGroup(v, it) : (v.cards[it] || thSticky(v, it));
    at.x = Math.round(d.starts[it].x + d.dx);
    at.y = Math.round(d.starts[it].y + d.dy);
  }
  if (d.trail && !d.trail.raf) d.trail.raf = requestAnimationFrame(thTrailTick);
  const hit = thTargetAt(e.clientX, e.clientY);
  thWay(d, hit);
  thPlace(d);
  thHover(hit);
  thMergeShow(hit);
  thInsertShow(d);
  thLean(e);
  thTip(e);
}

/* One step of a drag a frame (18 October, the Mac window's judder). Chromium hands the page one pointer
   move a frame, and WebKit, which the Mac window runs, every move as it comes, two or more a frame, and
   each move did the whole step: where it lands, the neighbours making way, every card placed. The latest
   move waits for the next frame and runs alone there, and a drop, Alt and Esc take it first. */
function thDragQueue(e) {
  const d = TH.drag;
  if (!d) return;
  d.next = e;
  if (!d.step) d.step = requestAnimationFrame(() => thDragStep(d));
}

/* the move waiting for its frame, run now, once */
function thDragStep(d) {
  if (!d) return;
  if (d.step) cancelAnimationFrame(d.step);
  d.step = 0;
  const e = d.next;
  d.next = null;
  if (e && TH.drag === d) thDragMove(e);
}

/* What came along with a label trails it by about TH_TRAIL_MS, eased out, as the .trailing transition did
   until 18 October, eased each frame here instead, since WebKit began that transition afresh on every move
   of every card that came along. At once with reduced motion. True while it has not caught up. */
const TH_TRAIL_MS = 140;
function thTrail(d, now = performance.now()) {
  if (!d.trail) return false;
  const dt = d.trail.t ? Math.max(0, Math.min(64, now - d.trail.t)) : 16;
  d.trail.t = now;
  const k = thCalm() ? 1 : 1 - Math.exp(-dt / (TH_TRAIL_MS / 3));
  d.trail.x += (d.dx - d.trail.x) * k;
  d.trail.y += (d.dy - d.trail.y) * k;
  const done = Math.abs(d.dx - d.trail.x) < 0.5 && Math.abs(d.dy - d.trail.y) < 0.5;
  if (done) { d.trail.x = d.dx; d.trail.y = d.dy; }
  return !done;
}

/* one frame of the trail, on what trails alone, and the next while it has not caught up */
function thTrailTick(now) {
  const d = TH.drag;
  if (!d || !d.trail) return;
  d.trail.raf = 0;
  const busy = thTrail(d, now);
  for (const it of d.moving) {
    if (d.grabbed.has(it)) continue;
    const el = TH.els.cards[it] || TH.els.labels[it] || TH.els.stickies[it];
    if (el) el.style.translate = `${d.trail.x}px ${d.trail.y}px`;
  }
  if (busy) d.trail.raf = requestAnimationFrame(thTrailTick);
}

/* Alt pressed or let go in the middle of a drag shows the leaving at once, with no move needed,
   and the tip says what letting go now does. */
function thDragAlt(on) {
  const d = TH.drag;
  if (d && d.next) thDragStep(d);
  if (!d || d.alt === on) return;
  d.alt = on;
  // Alt held takes the Merge away, and let go brings it back where the pointer is
  const hit = thTargetAt(d.px === undefined ? d.x0 : d.px, d.py === undefined ? d.y0 : d.py);
  thWay(d, hit);
  thPlace(d);
  thHover(hit);
  thMergeShow(hit);
  thInsertShow(d);
  thTip();
}

/* Esc in the middle of a drag puts everything back where it stood when the drag began, what was
   dragged and everything that made way, and leaves no step of undo, since nothing changed. */
function thDragCancel() {
  const d = TH.drag;
  if (!d) return;
  const v = TH.v;
  const shown = thSpots(d.seen || v);
  thPreview(v, thSize, Object.assign({}, d, { dx: 0, dy: 0 }), null);
  clearTimeout(d.still);
  cancelAnimationFrame(d.raf);
  cancelAnimationFrame(d.step);
  if (d.trail) cancelAnimationFrame(d.trail.raf);
  TH.drag = null;
  TH.press = null;
  thTip();
  thMergeShow(null);
  thInsertShow(null);
  thHover(null);
  thSideArm(false);
  // one dragged out of a stack goes back into it
  if (d.lifted) TH.removed = thPut(v, d.before);
  thRender();
  thEase(shown, d.moving, d.lean);
  // a save put off while the drag ran goes now
  if (TH.dirty) thSoon();
}

function thDragEnd(e) {
  const d = TH.drag;
  const v = TH.v;
  // Alt held at the drop counts as Alt held through it, so it joins nothing
  d.alt = !!(e.altKey || d.alt);
  const hit = thTargetAt(e.clientX, e.clientY);
  // where everything shows this moment, partway through making way, which the drop eases on from,
  // and the neighbours where they made way for the spot it is let go on, Alt at the drop counted
  const shown = thSpots(d.seen || v);
  d.hitNow = hit;
  d.out = !!(hit && hit.body) && thMergeInto(v, d.moving, hit.group);
  thNearRest(d, thWayHome(v, d.moving, d.nest, hit, d.alt));
  thPreview(v, thSize, d, thWayHome(v, d.moving, d.nest, hit, d.alt));
  const alt = d.alt;
  clearTimeout(d.still);
  cancelAnimationFrame(d.raf);
  cancelAnimationFrame(d.step);
  if (d.trail) cancelAnimationFrame(d.trail.raf);
  TH.drag = null;
  if (TH.dirty) thSoon();
  thTip();
  thMergeShow(null);
  thInsertShow(null);
  thSideArm(false);
  for (const el of Object.values(TH.els.labels)) el.classList.remove('target');
  for (const el of Object.values(TH.els.frames)) el.classList.remove('target');
  TH.hoverAt = null;
  // what he picked up himself, rather than what came along with a label he picked up
  const handled = [...TH.sel.cards].filter((key) => d.moving.has(key));
  const lifted = d.moving;
  if (hit && (hit.discard || hit.wait)) {
    // the selected cards go into the sidebar, Set aside or Not placed, and whatever came with a label goes back where it was, a
    // sticky note too, since the sidebar is for statements alone, and nothing made way
    const from = shown;
    for (const it of d.moving) {
      const at = thIsGroup(v, it) ? thGroup(v, it) : (v.cards[it] || thSticky(v, it));
      Object.assign(at, d.starts[it]);
    }
    const keys = handled.filter((key) => thOnCanvas(v, key));
    if (!keys.length) { thRender(); thEase(from, lifted); return; }
    thAck(keys);
    if (hit.discard) thDiscard(v, keys); else thSendWaiting(v, keys);
    TH.sel.cards.clear();
    thDone(d.before, hit.discard ? t('themes.step.set_aside', { n: keys.length })
      : t('themes.step.back_to_unplaced', { n: keys.length }), { from, lifted });
    thSideFlash(keys, hit.discard ? 'aside' : 'wait');
    return;
  }
  if (hit && hit.stack) {
    // what he picked up goes under the card it was let go on, and nothing else moves
    const from = shown;
    for (const it of d.moving) {
      const at = thIsGroup(v, it) ? thGroup(v, it) : (v.cards[it] || thSticky(v, it));
      Object.assign(at, d.starts[it]);
    }
    const keys = handled.filter((key) => thOnCanvas(v, key) && key !== hit.stack);
    const done = keys.length ? thStackOnto(v, keys, hit.stack) : [];
    if (!done.length) { thRender(); thEase(from, lifted); return; }
    thAck(done);
    for (const k of done) TH.opened.delete(k);
    TH.sel.cards = new Set([hit.stack]);
    thDone(d.before, t('themes.step.stacked', { n: done.length }), { from, lifted });
    return;
  }
  // A member dropped anywhere stays a member: only a title strip takes it, or the body of a theme,
  // `hit.frame`, at its level (31 October). With Alt held nothing takes it and it leaves its theme where
  // it lands
  const { joined, left, dest } = thDrop(v, d.moving, hit && !hit.frame ? hit.group : null,
    hit && hit.frame ? hit.group : null, alt);
  const moved = Math.abs(d.dx) > 0 || Math.abs(d.dy) > 0;
  if (!moved && !joined.length && !left.length) { thRender(); thEase(shown, lifted); return; }
  thAck(handled.concat(left.filter((it) => !thIsGroup(v, it))));
  const n = d.moving.size;
  let what = t('themes.step.moved', { n });
  if (joined.length) what = t('themes.step.joined', { label: thGroup(v, dest).label });
  else if (left.length > 1) what = t('themes.step.took_out_n', { n: left.length });
  else if (left.length) what = thIsGroup(v, left[0]) ? t('themes.step.took_sub_out') : t('themes.step.took_card_out');
  if (!joined.length && left.length === 1 && thIsSticky(v, left[0])) what = t('themes.step.took_note_out');
  if (d.lifted) what = t('themes.step.unstacked');
  // what was dragged lands where it was let go and the neighbours stay where they made way, a frame
  // that grew sends its own neighbours clear, and the one step records where it all ended up
  thDone(d.before, what, { settle: d.moving, stay: true, was: d.was, from: shown, lifted, lean: d.lean });
}

function thLassoMove(e) {
  const l = TH.lasso;
  if (!l.moved && Math.hypot(e.clientX - l.x0, e.clientY - l.y0) < 4) return;
  l.moved = true;
  const r = thStage().getBoundingClientRect();
  const x = Math.min(e.clientX, l.x0);
  const y = Math.min(e.clientY, l.y0);
  const w = Math.abs(e.clientX - l.x0);
  const h = Math.abs(e.clientY - l.y0);
  const box = $('th-lasso');
  box.hidden = false;
  box.style.left = `${x - r.left}px`;
  box.style.top = `${y - r.top}px`;
  box.style.width = `${w}px`;
  box.style.height = `${h}px`;
  const a = thToWorld(x, y);
  const rect = { x: a.x, y: a.y, w: w / TH.view.z, h: h / TH.view.z };
  // Shift or Cmd held at the start keeps what was selected, so a second lasso adds to the first
  TH.sel.cards = new Set(l.cards);
  TH.sel.groups = new Set(l.groups);
  TH.sel.stickies = new Set(l.stickies || []);
  for (const key of Object.keys(TH.els.cards)) {
    const c = TH.v.cards[key];
    if (thCentreIn({ x: c.x, y: c.y, w: thSize(key).w, h: thSize(key).h }, rect)) TH.sel.cards.add(key);
  }
  for (const n of thStickies(TH.v)) {
    if (thCentreIn({ x: n.x, y: n.y, w: thSize(n.id).w, h: thSize(n.id).h }, rect)) TH.sel.stickies.add(n.id);
  }
  for (const g of TH.v.groups) {
    if (TH.layout[g.id] && thCentreIn(TH.layout[g.id].label, rect)) TH.sel.groups.add(g.id);
  }
  thDrawSel();
}

/* Miro's model. A plain drag on empty canvas draws a lasso, and Space with a drag, the middle
   button or the hand (H) pans. Shift or Cmd (Ctrl on Windows and Linux) adds: a click adds a card
   or a label to the selection or takes it away, and a drag draws another lasso over what is
   selected already, inside a theme's frame too. A plain drag that starts on the empty space inside
   a frame takes the whole theme, as its title does, and a click there selects the theme. */
function thPointerDown(e) {
  if (!TH.live || TH.busy) return;
  // the corners keep their own clicks: the pile, the discard, the zoom
  if (e.target.closest('.th-ui')) return;
  if (e.target.closest('.th-title-edit')) return;
  thMenuClose();
  thTitleDone(true);
  thNoteDone(true);
  if (TH.pileOpen) thPile(false);
  // a right press, and Ctrl with a click on a Mac, is the menu's, which contextmenu opens
  if (e.button === 2 || (e.button === 0 && e.ctrlKey && MAC)) return;
  const stage = thStage();
  if (e.button === 1 || (e.button === 0 && (TH.space || TH.hand))) {
    e.preventDefault();
    TH.pan = { x0: e.clientX, y0: e.clientY, x: TH.view.x, y: TH.view.y };
    stage.classList.add('th-panning');
    try { stage.setPointerCapture(e.pointerId); } catch { /* a nicety */ }
    return;
  }
  if (e.button !== 0) return;
  if (e.target.closest('.th-del, .th-arr, .th-more, .th-sticky-del, .th-strip, .th-stackn, .th-restack, .gt-unfold')) return;
  // a click on a close pair's line opens what to do with the pair
  const link = e.target.closest('.th-pair');
  if (link && !e.shiftKey && !MOD(e)) {
    e.preventDefault();
    const p = (TH.pairs || [])[Number(link.dataset.pair)];
    if (p) thPairMenuOpen(p, e.clientX, e.clientY);
    return;
  }
  const add = e.shiftKey || MOD(e);
  const hit = e.target.closest('.th-card, .th-label, .th-sticky');
  try { stage.setPointerCapture(e.pointerId); } catch { /* a nicety */ }
  if (hit) {
    e.preventDefault();
    // a press on a card's quote that never becomes a drag shows the quote whole (see thKqOpen)
    TH.press = { item: thItemOf(hit), x0: e.clientX, y0: e.clientY, add, alt: e.altKey, kq: !!e.target.closest('[data-kq]') };
    return;
  }
  e.preventDefault();
  const frame = add ? null : thFrameAt(TH.v, TH.layout, thToWorld(e.clientX, e.clientY), null);
  if (frame) {
    TH.press = { item: { kind: 'group', id: frame }, x0: e.clientX, y0: e.clientY, add: false, alt: e.altKey, frame: true };
    return;
  }
  TH.lasso = { x0: e.clientX, y0: e.clientY, moved: false, add,
    cards: add ? [...TH.sel.cards] : [], groups: add ? [...TH.sel.groups] : [], stickies: add ? [...TH.sel.stickies] : [] };
}

function thPointerMove(e) {
  if (TH.pan) {
    TH.view.x = TH.pan.x + (e.clientX - TH.pan.x0);
    TH.view.y = TH.pan.y + (e.clientY - TH.pan.y0);
    thView();
    return;
  }
  if (TH.press && !TH.drag) {
    if (Math.hypot(e.clientX - TH.press.x0, e.clientY - TH.press.y0) < 4) return;
    // a revision on view moves nothing: a press that turns into a drag lets go instead
    if (!thMayAct(TH.v, 'drag')) { TH.press = null; return; }
    thDragStart();
  }
  // a drag takes one step a frame, the latest move (see thDragQueue)
  if (TH.drag) { thDragQueue(e); return; }
  if (TH.lasso) thLassoMove(e);
}

function thPointerUp(e) {
  const stage = thStage();
  try { stage.releasePointerCapture(e.pointerId); } catch { /* already gone */ }
  if (TH.pan) { TH.pan = null; stage.classList.remove('th-panning'); return; }
  // the move still waiting for its frame goes first, so the drop lands where the pointer let go
  if (TH.drag) { thDragStep(TH.drag); thDragEnd(e); TH.press = null; return; }
  if (TH.press) {
    const { item, add, frame, kq } = TH.press;
    TH.press = null;
    // a click selects and never opens the Inspector, which follows the selection when it is open
    if (add) { thToggle(item); TH.lastPick = thSelected(item) ? item : null; thPanelFollow(); return; }
    thSelectOnly(item);
    TH.lastPick = item;
    thPanelFollow();
    // a click on a card's quote selects the card and shows the quote whole beside it
    if (kq && item.kind === 'card') { TH.lastClick = null; thKqOpen(item.id); return; }
    // a second click on the empty space inside a frame makes a sticky note there, in that PET
    if (frame) {
      TH.lastClick = null;
      if (thEmptyTwice(e)) thStickyNew(e.clientX, e.clientY);
      return;
    }
    TH.lastEmpty = null;
    // a second click on the same label soon after the first opens its title, a second click on the
    // same statement card its words for editing on the card, as a title opens (Adam, 30 October: from
    // 16 October to then it opened the passage, which Go to the passage in its menu still does), on the
    // GETs, LGETs and LPETs boards too (Adam, 30 October, later: "Edit there too"), on another card there
    // its Inspector, and on the same sticky note its words, and a click in the frame selects the theme
    // and no more
    const now = Date.now();
    const last = TH.lastClick;
    const named = item.kind === 'card' || item.kind === 'sticky' || (item.kind === 'group' && !frame);
    TH.lastClick = named ? { kind: item.kind, id: item.id, at: now } : null;
    if (named && last && last.kind === item.kind && last.id === item.id && now - last.at < 450) {
      TH.lastClick = null;
      if (item.kind === 'sticky') thStickyEditOpen(item.id);
      else if (item.kind === 'group') thTitleOpen(item.id);
      else thCardEditOpen(item.id);
    }
    return;
  }
  if (TH.lasso) {
    const l = TH.lasso;
    TH.lasso = null;
    $('th-lasso').hidden = true;
    if (!l.moved && !l.add) { thClearSel(); thPanelFollow(); } else if (l.moved) thPanelFollow();
    // a second click on empty canvas soon after the first makes a sticky note there
    if (!l.moved && !l.add && thEmptyTwice(e)) thStickyNew(e.clientX, e.clientY);
  }
}

/* ── the hand, and the right-click menu ── */

/* H: the hand, in which a plain drag pans the canvas, and H again, V or Esc gives back the pointer.
   The two small controls by the zoom say which is on and switch between them. */
function thHand(on) {
  TH.hand = !!on;
  const stage = thStage();
  if (stage) stage.classList.toggle('th-hand', TH.hand);
  for (const [id, mine] of [['th-mode-pointer', !TH.hand], ['th-mode-hand', TH.hand]]) {
    const b = $(id);
    if (b) { b.classList.toggle('on', mine); b.setAttribute('aria-pressed', String(mine)); }
  }
}

/* A right-click on a card or a label opens a small menu in the style of the turn screen's row menu,
   for that one item: Inspect, Go to the passage on a statement's card (16 October), Take out of PET
   when it is in one, or from sub-theme, then on a label
   Auto-arrange, Rename and Note, then Bin on a card and Delete this label on a label. A
   right-click inside a frame is its label's. Esc, a click anywhere else or a choice puts it away. */
function thMenuItems(v, item, copyable = true) {
  // the empty canvas has one entry, New sticky note, and a sticky note its four colours, the one it
  // has marked, Take out of PET when it is in one, and Delete note
  // and on GETs Arrange by participant beside it (19 October, way 2)
  if (item.kind === 'canvas') {
    if (thLocked(v)) return [];
    return [{ label: t('themes.menu.new_sticky'), act: 'sticky' }].concat(TH.mode === 'gets' && !thTa() ? [{ label: t('themes.board.by_participant'), act: 'bypart' }] : []);
  }
  if (item.kind === 'sticky') {
    if (thLocked(v)) return [];
    const note = thSticky(v, item.id) || {};
    const owner = thParents(v)[item.id];
    const out = TH_STICKY_COLOURS.map((c) => ({ label: thColourName(c), act: 'colour', colour: c, on: note.colour === c }));
    if (thSelected(item) && thAlignIds(v).length >= 2) out.push({ label: t('themes.align.head'), act: 'alignsub', sub: true, rule: true });
    if (owner !== undefined) out.push({ label: thLeaveLabel(v, owner), act: 'leave', rule: true });
    out.push({ label: t('themes.sticky.delete_label'), act: 'unstick', rule: true });
    return out;
  }
  // Copy to board, on a label: the boards it can go to follow in the same menu, and with none to
  // go to the entry is there and does nothing
  const copy = { label: t('themes.menu.copy_to'), act: 'copyto', rule: true, off: !copyable };
  // Inspect, first on a card and a label: the sidebar open on the Inspector, on that one
  const inspect = { label: t('themes.menu.inspect'), act: 'inspect' };
  // Go to the passage after it on a statement's card, what a double-click on it does (16 October),
  // which changes nothing on the board
  const passage = item.kind === 'card' && thIsStatement(v, item.id) ? [{ label: t('themes.menu.passage'), act: 'passage' }] : [];
  // a revision on view keeps Inspect, the passage and the copy alone, since everything else changes the board
  if (thLocked(v)) return item.kind === 'group' ? [inspect, copy] : [inspect, ...passage];
  // a statement in a stack shown open: on top of it, or out of it, below its stack
  if (item.kind === 'card' && thTopOf(v, item.id)) {
    return [inspect, ...passage, { label: t('themes.menu.stack_top'), act: 'stacktop', rule: true },
      { label: t('themes.menu.unstack'), act: 'unstack' }];
  }
  const parents = thParents(v);
  const holder = parents[item.id];
  const items = [inspect, ...passage];
  // Group, and Ungroup when what is selected is the whole of one group, on a card (20 October)
  if (item.kind === 'card') items.push(...thGroupItems(v, item, parents));
  // Align, with the toolbar's eight beside it, on a selection of two or more (21 October), the canvas's alone
  if (TH.face !== 'table' && thSelected(item) && thAlignIds(v).length >= 2) items.push({ label: t('themes.align.head'), act: 'alignsub', sub: true, rule: item.kind !== 'card' });
  if (item.kind === 'card' && TH.mode !== 'gets') items.push(...thStackItems(v, item.id));
  // New group inside on a PET's or a sub-theme's menu, empty and its title open (20 October), and on a
  // GET's or a GET sub-theme's the same
  if (item.kind === 'group') items.push({ label: t('themes.menu.inside'), act: 'inside', rule: true });
  if (holder !== undefined) items.push({ label: thLeaveLabel(v, holder, parents), act: 'leave', key: thWaits(v) && item.kind === 'card' ? t('themes.key.backspace') : '' });
  // a card loose on the canvas, in no PET yet, goes back to the sidebar's Not placed (20 October)
  else if (item.kind === 'card' && thWaits(v)) items.push({ label: t('themes.menu.back_unplaced'), act: 'wait', key: t('themes.key.backspace') });
  // Auto-arrange lays out the canvas, so the table, always in order, leaves it out
  if (item.kind === 'group') items.push(...(TH.face === 'table' ? [] : [{ label: t('themes.label.arrange_label'), act: 'arrange' }]),
    { label: t('themes.board.rename'), act: 'rename' },
    // the description under its title (21 October): Add description, or Edit and Remove once it has one
    ...(String((v.groups.find((g) => g.id === item.id) || {}).description || '').trim()
      ? [{ label: t('themes.menu.desc_edit'), act: 'desc' }, { label: t('themes.menu.desc_remove'), act: 'undesc' }]
      : [{ label: t('themes.menu.desc_add'), act: 'desc' }]),
    { label: t('themes.board.note_label'), act: 'note' }, copy);
  // Working together: a reviewer's Comment on a PET or a GET (review.js)
  if (typeof rvwLabelItems === 'function') items.push(...rvwLabelItems(v, item));
  items.push(item.kind === 'card' ? { label: t('themes.status.name_binned'), act: 'discard', rule: true, key: 'X' }
    : { label: t('themes.menu.delete_label'), act: 'delete', rule: true });
  return items;
}

/* Group and Ungroup on a card's menu (Adam, 20 October, from a tester's feedback, Freeform's and Miro's way): Group
   does what G does with the selection, the card right-clicked alone when it was not selected, and Ungroup,
   when the cards selected are the whole of one PET, GET, sub-theme or group and nothing else, deletes its
   label and keeps the cards where they stand, as Delete this label does. */
function thGroupItems(v, item, parents) {
  const ids = thSelected(item)
    ? [...TH.sel.cards].filter((k) => thOnCanvas(v, k)).concat([...TH.sel.groups].filter((id) => thIsGroup(v, id)))
    : [item.id];
  const out = [{ label: t('themes.menu.group'), act: 'groupsel', rule: true }];
  const gid = thUngroupOf(v, ids, parents);
  if (gid) out.push({ label: t('themes.menu.ungroup'), act: 'ungroup', gid });
  return out;
}

/* the group whose label Ungroup deletes: the one holding every item selected, each of its cards and labels
   among them, or null */
function thUngroupOf(v, ids, parents = thParents(v)) {
  if (!ids.length) return null;
  const gid = parents[ids[0]];
  if (gid === undefined || !ids.every((id) => parents[id] === gid)) return null;
  const g = thGroup(v, gid);
  if (!g) return null;
  return g.members.filter((m) => thOnCanvas(v, m) || thIsGroup(v, m)).every((m) => ids.includes(m)) ? gid : null;
}

/* the entries that take something away, red with a bin as every Remove and Delete is (16 October), and Take
   out of PET, a move, with the arrow out in the ink (20 October) */
const TH_TAKES = ['delete', 'unstick'];
const TH_OUTS = ['leave'];

function thMenuOpen(item, clientX, clientY) {
  thMenuClose();
  const v = TH.v;
  const there = item.kind === 'canvas' || (item.kind === 'card' ? thOnCanvas(v, item.id) || thUnderShown(v, item.id)
    : item.kind === 'sticky' ? thIsSticky(v, item.id) : thIsGroup(v, item.id));
  if (!v || !there) return;
  const targets = thCopyTargets(TH.boards, TH.meta && TH.meta.id, !!TH.viewing);
  const items = TH.mode === 'gets' ? gtMenuItems(v, item, thMenuItems(v, item, false)) : thMenuItems(v, item, targets.length > 0);
  if (!items.length) return;
  if (item.kind !== 'canvas' && !thSelected(item)) { thSelectOnly(item); TH.lastPick = item; thPanelFollow(); }
  const pop = document.createElement('div');
  pop.className = 'row-menu th-cmenu';
  pop.setAttribute('role', 'menu');
  pop.innerHTML = items.map((it, i) => `${it.rule && i ? '<div class="row-menu-rule" role="separator"></div>' : ''}`
    + `<button type="button" class="ghost small${TH_TAKES.includes(it.act) ? ' btn-remove' : TH_OUTS.includes(it.act) ? ' btn-out' : ''}" role="menuitem" tabindex="-1" data-cmenu="${i}"${it.off ? ` disabled title="${escAttr(t('themes.menu.no_other_board'))}"` : ''}>`
    + `${it.colour ? `<span class="th-dot sticky-${it.colour}${it.on ? ' on' : ''}" aria-hidden="true"></span>` : ''}<span>${esc(it.label)}</span>`
    + `${it.key ? `<span class="th-mkey" aria-hidden="true">${esc(it.key)}</span>` : ''}`
    + `${it.sub ? '<span class="th-mkey th-msub" aria-hidden="true">&#8250;</span>' : ''}`
    + `${it.on ? `<span class="th-dot-on" aria-label="${escAttr(t('themes.menu.its_colour'))}">${TH_TICK_ICON}</span>` : ''}</button>`).join('');
  document.body.appendChild(pop);
  const w = pop.offsetWidth;
  const h = pop.offsetHeight;
  pop.style.left = `${Math.max(8, Math.min(clientX + 2, window.innerWidth - w - 8))}px`;
  pop.style.top = `${clientY + 4 + h > window.innerHeight - 8 ? Math.max(8, clientY - 4 - h) : clientY + 4}px`;
  pop.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); });
  pop.addEventListener('click', (e) => {
    const board = e.target.closest('[data-copy]');
    if (board) { const to = board.dataset.copy; thMenuClose(); thCopyTo(item.id, to); return; }
    const also = e.target.closest('[data-also]');
    if (also) { const to = also.dataset.also; thMenuClose(); gtPlaceAlso(item.id, to); return; }
    const chosen = e.target.closest('[data-cmenu]');
    if (chosen && !chosen.disabled) thMenuDo(items[Number(chosen.dataset.cmenu)], chosen);
  });
  // Align opens its eight beside it as the pointer comes to it, as a Mac menu's submenu does
  pop.addEventListener('pointerover', (e) => {
    const row = e.target.closest('[data-cmenu]');
    if (!row) return;
    const it = items[Number(row.dataset.cmenu)];
    if (it && it.act === 'alignsub') thAlignSub(row);
    else thAlignSub(null);
  });
  TH.menu = { el: pop, item, targets };
}

/* Align's eight beside the right-click menu, at the right of its row, or at its left where the window has no
   room, as a Mac menu's submenu opens. It stands on the page beside the menu and closes with it. Null takes
   it away. */
function thAlignSub(row) {
  const open = TH.menu;
  if (!open) return;
  if (!row) {
    if (open.sub) { open.sub.remove(); open.sub = null; }
    open.el.querySelectorAll('.th-msubon').forEach((r) => r.classList.remove('th-msubon'));
    return;
  }
  if (open.sub) return;
  row.classList.add('th-msubon');
  const sub = document.createElement('div');
  sub.className = 'row-menu th-cmenu th-tbmenu th-subpop';
  sub.setAttribute('role', 'menu');
  sub.setAttribute('aria-label', t('themes.align.head'));
  const rows = thAlignRows();
  sub.innerHTML = rows.map((r, i) => `${r.rule ? '<div class="row-menu-rule" role="separator"></div>' : ''}`
    + `<button type="button" class="ghost small" role="menuitem" tabindex="-1" data-tbpick="${i}"${r.off ? ' disabled' : ''}>`
    + `<span class="th-tbicon">${r.icon}</span><span>${esc(r.label)}</span></button>`).join('');
  document.body.appendChild(sub);
  open.sub = sub;
  const at = row.getBoundingClientRect();
  const menu = open.el.getBoundingClientRect();
  const right = menu.right + 12 + sub.offsetWidth <= window.innerWidth - 8;
  sub.style.left = `${right ? menu.right + 12 : Math.max(8, menu.left - 12 - sub.offsetWidth)}px`;
  sub.style.top = `${Math.max(8, Math.min(at.top - 5, window.innerHeight - sub.offsetHeight - 8))}px`;
  sub.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); });
  sub.addEventListener('click', (e) => {
    const way = e.target.closest('[data-tbpick]');
    if (!way || way.disabled) return;
    thMenuClose();
    thAlignDo(rows[Number(way.dataset.tbpick)].way);
  });
}

/* Copy to board, chosen: the same menu lists where the theme can go, each board by its name, and
   while a revision is on view the board it belongs to first, "Copy to Board 1". */
function thMenuBoards() {
  const open = TH.menu;
  if (!open) return;
  const g = thGroup(TH.v, open.item.id);
  if (!g) { thMenuClose(); return; }
  const pop = open.el;
  pop.innerHTML = `<p class="th-cmenu-head">${esc(t('themes.copy.head', { label: thLabelShown(g.label) }))}</p>`
    + open.targets.map((b) => `<button type="button" class="ghost small" role="menuitem" tabindex="-1" data-copy="${escAttr(b.id)}"><span>${esc(b.here ? t('themes.copy.to', { name: b.name }) : b.name)}</span></button>`).join('');
  const box = pop.getBoundingClientRect();
  if (box.bottom > window.innerHeight - 8) pop.style.top = `${Math.max(8, window.innerHeight - 8 - box.height)}px`;
  if (box.right > window.innerWidth - 8) pop.style.left = `${Math.max(8, window.innerWidth - 8 - box.width)}px`;
}

function thMenuClose() {
  if (!TH.menu) return;
  TH.menu.el.remove();
  if (TH.menu.sub) TH.menu.sub.remove();
  // a toolbar button whose menu it was says it is shut
  if (TH.menu.button) TH.menu.button.setAttribute('aria-expanded', 'false');
  TH.menu = null;
}

function thMenuDo(choice, row) {
  const open = TH.menu;
  if (choice && choice.act === 'copyto') { if (!choice.off) thMenuBoards(); return; }
  if (choice && choice.act === 'alignsub') { if (row) thAlignSub(row); return; }
  if (choice && choice.act === 'also') { gtAlsoList(); return; }
  thMenuClose();
  if (!open || !choice || !TH.live || TH.busy) return;
  const { item } = open;
  if (choice.act === 'inspect') { TH.lastPick = { kind: item.kind, id: item.id }; thInspectorOpen({ kind: item.kind, id: item.id }); }
  else if (choice.act === 'passage') thToPassage(item.id);
  else if (choice.act === 'wtcomment') rvwLabelComment(item.id);
  else if (choice.act === 'wtsuggest') rvwLabelSuggest(item.id);
  else if (choice.act === 'leave') thLeaveThemes([item.id]);
  else if (choice.act === 'wait') thWaitDo(TH.sel.cards.has(item.id) ? [...TH.sel.cards] : [item.id]);
  else if (choice.act === 'groupsel') thGroupKey();
  else if (choice.act === 'ungroup') thDeleteLabels([choice.gid]);
  else if (choice.act === 'arrange') thArrangeGroup(item.id);
  else if (choice.act === 'inside') thNewEmpty(item.id);
  else if (choice.act === 'rename') thTitleOpen(item.id);
  else if (choice.act === 'note') thNoteOpen(item.id);
  else if (choice.act === 'desc') thDescOpen(item.id);
  else if (choice.act === 'undesc') thDescRemove(item.id);
  else if (choice.act === 'discard') thDiscardOne(item.id);
  else if (choice.act === 'delete') thDeleteLabels([item.id]);
  else if (choice.act === 'sticky') thStickyNew(item.x, item.y);
  else if (choice.act === 'bypart') gtArrangeByParticipant();
  else if (choice.act === 'colour') thStickyRecolour(item.id, choice.colour);
  else if (choice.act === 'unstick') thStickyDelete([item.id]);
  else if (choice.act === 'stackshow') thStackShow(item.id);
  else if (choice.act === 'unfold') gtUnfold(item.id);
  else if (choice.act === 'stackhere') thStackDo(choice.items, item.id);
  else if (choice.act === 'stacktop') thMakeTopDo(item.id);
  else if (choice.act === 'unstack') thTakeOutDo(item.id);
}

function thContextMenu(e) {
  if (!TH.live || TH.busy || e.target.closest('.th-ui, .th-title-edit')) return;
  const hit = e.target.closest('.th-card, .th-label, .th-sticky');
  const frame = hit ? null : thFrameAt(TH.v, TH.layout, thToWorld(e.clientX, e.clientY), null);
  e.preventDefault();
  thTitleDone(true);
  thNoteDone(true);
  // the empty canvas has a menu of its own, with New sticky note where the pointer is
  if (!hit && !frame) { thMenuOpen({ kind: 'canvas', x: e.clientX, y: e.clientY }, e.clientX, e.clientY); return; }
  thMenuOpen(hit ? thItemOf(hit) : { kind: 'group', id: frame }, e.clientX, e.clientY);
}

/* Miro's mouse: the wheel zooms about the pointer, and a pinch, which arrives as the wheel with
   Ctrl held, zooms too. A sideways wheel, a mouse's thumb wheel or a trackpad's sideways swipe,
   pans left and right, and so does the wheel with Shift held, and the wheel with Alt held pans up
   and down (188). Panning is also Space held with a drag, a drag with the middle button, or the
   hand. */
function thWheel(e) {
  if (!TH.live || e.target.closest('.th-pile, .th-panel, .th-exported')) return;
  e.preventDefault();
  const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? thStage().clientHeight : 1;
  const dx = e.deltaX * unit;
  const dy = e.deltaY * unit;
  if (!e.ctrlKey && (e.altKey || e.shiftKey || Math.abs(dx) > Math.abs(dy))) {
    // the canvas moves the way a page scrolls: Alt up and down, anything else sideways
    if (e.altKey) TH.view.y -= dy || dx;
    else TH.view.x -= dx || dy;
    thView();
    return;
  }
  const step = Math.max(-60, Math.min(60, dy));
  thZoomAt(TH.view.z * Math.exp(-step * (e.ctrlKey ? 0.005 : 0.004)), e.clientX, e.clientY);
}

/* ── the keys ── */

/* Taken before app.js hears them, so nothing the turn screen does with a key reaches a case it
   is not showing. The title box and the cards of the overlays keep their own. */
// the Table view's keys, from thKeyDown: Cmd + Z there is the board's undo, T goes back to the canvas and V opens the boards, and the
// canvas's own keys work on the rows selected, each meaning what it means on the canvas (20 October, way 1):
// G, X, S, Backspace, I and N, and Esc clearing the selection. A row's own button keeps Enter and Space.
function thTableBoardKey(e) {
  if (e.key === 'Escape') {
    e.preventDefault();
    if (TH.vmenu) thVmenu(false);
    else if (TH.casemenu) thCasemenu(false);
    else if (TH.xmenu) thXmenu(false);
    else if (TH.exported) thExported(null);
    else if (TH.viewing) thViewEnd();
    else if (TH.opened && TH.opened.size && !(TH.sel.cards.size || TH.sel.groups.size || TH.sel.stickies.size)) thStackShow(null);
    else if (TH.sel.cards.size || TH.sel.groups.size || TH.sel.stickies.size) { thClearSel(); thPanelFollow(); }
    return;
  }
  if (e.key === 't' || e.key === 'T') { e.preventDefault(); thFace('canvas'); return; }
  if (e.key === 'v' || e.key === 'V') { e.preventDefault(); thVmenu(!TH.vmenu); return; }
  // a key typed in a field of the table, a row's note, is the field's
  if (e.target && e.target.closest && e.target.closest('input, textarea, select, [contenteditable="true"]')) return;
  if (TH.busy) return;
  if (e.key === 'g' || e.key === 'G') { e.preventDefault(); thGroupKey(); }
  else if (e.key === 'x' || e.key === 'X') { e.preventDefault(); thDiscardKey(); }
  else if ((e.key === 's' || e.key === 'S') && TH.mode !== 'gets') { e.preventDefault(); thTableStackKey(); }
  else if (e.key === 'Backspace' || e.key === 'Delete') { e.preventDefault(); thDeleteKey(); }
  else if ((e.key === 'n' || e.key === 'N') && thAiOn()) { e.preventDefault(); thNamesAsk(); }
  else if (e.key === 'i' || e.key === 'I') { e.preventDefault(); thInspectorKey(); }
}

/* The bar's three menus from the keyboard (a11yfix, 8 November 2026): the boards, the participants and Export. Opened
   by Enter or Space on their button, the first item takes the focus, the arrows, Home and End walk them, Enter and
   Space press an item, Esc shuts the menu back to its button and Tab shuts it and goes on from there. The canvas
   hears none of those keys while the focus is in a menu, and a box for typing in it keeps its own. */
const TH_MENUS = {
  'th-vmenu': () => { thVmenu(false); ($('th-board').hidden ? $('th-cases') : $('th-board')).focus(); },
  'th-casemenu': () => { thCasemenu(false); $('th-cases').focus(); },
  'th-xmenu': () => { thXmenu(false); $('th-export').focus(); },
};

function thMenuKeys(e) {
  const menu = e.target && e.target.closest && e.target.closest('#th-vmenu, #th-casemenu, #th-xmenu');
  if (!menu || e.target.closest('textarea, select, input:not([type="checkbox"]):not([type="radio"])')) return false;
  e.stopPropagation();
  if (menuKeys(e, menu, TH_MENUS[menu.id])) return true;
  if (e.key === 'Tab') TH_MENUS[menu.id]();
  return true;
}

function thKeyDown(e) {
  if ($('themes').hidden) { if (TH.kqpop) thKqClose(); return; }
  if (thMenuKeys(e)) return;
  // a quote shown whole goes on Esc, and the canvas hears nothing more of it
  if (TH.kqpop && e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); thKqClose(); return; }
  // the delete card goes on Enter, the way the trim card does, and Esc leaves the board alone
  if (!$('th-confirm').hidden) {
    if (e.key === 'Enter' && !MOD(e)) { e.preventDefault(); e.stopPropagation(); thDeleteGo(); }
    else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); TH.doomed = null; hide('th-confirm'); }
    return;
  }
  // the GETs screen's print card and its audit trail keep their own keys, and the canvas hears none
  if (gtKeys(e)) return;
  if (anyOverlayOpen()) return;
  // Alt in the middle of a drag shows at once what a drop then takes out of its theme
  if (e.key === 'Alt' && TH.drag) { e.preventDefault(); thDragAlt(true); return; }
  // Esc in the middle of a drag puts back everything it moved, and does nothing else
  if (e.key === 'Escape' && TH.drag) { e.preventDefault(); e.stopPropagation(); thDragCancel(); return; }
  // and a row dragged from the sidebar goes back to it
  if (e.key === 'Escape' && TH.spull) { e.preventDefault(); e.stopPropagation(); thSPullEnd(e, true); return; }
  // the Search card over the canvas keeps its own keys, its field typing what it types (search.js)
  if (e.target && e.target.closest && e.target.closest('.search-card')) return;
  if (e.target && e.target.closest && e.target.closest('.th-title-edit, .th-vedit')) return;
  e.stopPropagation();
  // the right-click menu goes first: Esc puts it away, and any other key does too
  if (TH.menu) { if (e.key === 'Escape') { e.preventDefault(); thMenuClose(); return; } thMenuClose(); }
  // and a close pair's menu the same way
  if (TH.pmenu) { if (e.key === 'Escape') { e.preventDefault(); thPairMenuClose(); return; } thPairMenuClose(); }
  // and the status bar's menus, the quotes' three ways, Close pairs' gap and the counts: Esc puts them away here, as
  // the line above stops every key before the document's own Esc for them hears it (30 October)
  if (e.key === 'Escape' && (TH.qmenu || TH.cpmenu || TH.smenu)) {
    e.preventDefault();
    if (TH.qmenu) thQuotesMenu(false);
    if (TH.cpmenu) thCloseMenu(false);
    if (TH.smenu) thStatusMenu(false);
    return;
  }
  if (e.key === '?' || (e.shiftKey && e.key === '/')) { e.preventDefault(); openHelp(); return; }
  if (!TH.live) return;
  // the Table view (19 October): Alt with an arrow moves a row, and Space is a button's own there
  if (TH.face === 'table' && (thTableKey(e) || e.key === ' ')) return;
  if (e.key === ' ') {
    e.preventDefault();
    if (!TH.space) { TH.space = true; thStage().classList.add('th-grab'); }
    return;
  }
  if ((MOD(e) && (e.key === 'z' || e.key === 'Z')) || REDO_Y(e)) { e.preventDefault(); thUndo(!e.shiftKey && !REDO_Y(e)); return; }
  // Cmd + A selects all: the sidebar's section when a row there was pressed last, else the canvas or the table
  if (MOD(e) && !e.altKey && (e.key === 'a' || e.key === 'A')) { e.preventDefault(); thSelectAll(); return; }
  if (MOD(e) || e.altKey || e.ctrlKey) return;
  if (TH.face === 'table') { thTableBoardKey(e); return; }
  if (e.key === 'Escape') {
    e.preventDefault();
    if (TH.vmenu) thVmenu(false);
    else if (TH.casemenu) thCasemenu(false);
    else if (TH.xmenu) thXmenu(false);
    else if (TH.pileOpen) thPile(false);
    else if (TH.exported) thExported(null);
    else if (TH.viewing) thViewEnd();
    else if (TH.hand) thHand(false);
    // a stack shown open is stacked again, and with the selection the selection goes first
    else if (TH.opened && TH.opened.size && !(TH.sel.cards.size || TH.sel.groups.size || TH.sel.stickies.size)) thStackShow(null);
    // the selection goes, and the sidebar stays as it is: an Inspector showing says so
    else if (TH.sel.cards.size || TH.sel.groups.size || TH.sel.stickies.size) { thClearSel(); thPanelFollow(); }
    return;
  }
  if (e.key === 'h' || e.key === 'H') { e.preventDefault(); thHand(!TH.hand); return; }
  // M shows or hides the minimap, as its button at the end of the zoom bar does (18 October)
  if (e.key === 'm' || e.key === 'M') { e.preventDefault(); thMapToggle(); return; }
  // T shows the board as its table, as Table on the bar does (19 October)
  if (e.key === 't' || e.key === 'T') { e.preventDefault(); thFace('table'); return; }
  // V is the pointer when the hand is on, as in Miro, and otherwise the boards
  if ((e.key === 'v' || e.key === 'V') && TH.hand) { e.preventDefault(); thHand(false); return; }
  if (TH.busy) return;
  if (e.key === 'g' || e.key === 'G') { e.preventDefault(); thGroupKey(); }
  else if (e.key === 'x' || e.key === 'X') { e.preventDefault(); thDiscardKey(); }
  // S stacks the selection under the highest of it, or shows a top's stack and stacks it again
  else if ((e.key === 's' || e.key === 'S') && TH.mode !== 'gets') { e.preventDefault(); thStackKey(); }
  else if (e.key === 'Backspace' || e.key === 'Delete') { e.preventDefault(); thDeleteKey(); }
  else if (e.key === 'v' || e.key === 'V') { e.preventDefault(); thVmenu(!TH.vmenu); }
  else if ((e.key === 'n' || e.key === 'N') && thAiOn()) { e.preventDefault(); thNamesAsk(); }
  else if (e.key === 'i' || e.key === 'I') { e.preventDefault(); thInspectorKey(); }
}

function thKeyUp(e) {
  if ($('themes').hidden) return;
  if (e.key === 'Alt' && TH.drag) { thDragAlt(false); return; }
  if (e.key !== ' ') return;
  if (e.target && e.target.closest && e.target.closest('.th-title-edit')) return;
  e.preventDefault();
  e.stopPropagation();
  TH.space = false;
  thStage().classList.remove('th-grab');
}

/* ─────────────────────────────────────────── timepoints, part 2 ── */

/* A project of two or more timepoints (21 October, Adam's longitudinal model after Farr and Nizza 2019):
   each timepoint of a participant has its own PETs canvas, its statements those of that timepoint's sheets,
   and the participant's LPETs are made from those PETs as GETs are made from every participant's. Every
   call this screen makes about its canvas names the timepoint, or the LPETs, through thScopeFor, which
   `api` in app.js asks, so each route reads and writes that canvas's own file. A project of one, and a
   server from before, send no `timepoints`, and the bar and the calls are what they always were. */
const TH_SCOPED = new Set(['/api/themes', '/api/themes-save', '/api/themes-versions', '/api/themes-boards',
  '/api/themes-cases', '/api/themes-export', '/api/themes-ai', '/api/edit-statement', '/api/stamp', '/api/gets',
  '/api/gets-save', '/api/gets-ops', '/api/gets-boards', '/api/gets-cases', '/api/gets-trail', '/api/gets-ai']);

function thScopeFor(route, body) {
  if (typeof TH === 'undefined' || !TH.scope || !TH.live || $('themes').hidden) return body;
  if (!body || typeof body !== 'object' || body.workbook !== TH.path || !TH_SCOPED.has(route)) return body;
  // the GETs' own calls take the LPETs, and the PETs' the timepoint, never the other's
  if (TH.scope.lpets && !route.startsWith('/api/gets') && route !== '/api/stamp') return body;
  if (TH.scope.timepoint && route.startsWith('/api/gets')) return body;
  return Object.assign({}, TH.scope, body);
}

/* the switch beside PETs: the timepoint's label large and its description smaller, as the statements bar has it */
function thTpDraw() {
  const pick = $('th-tp-pick');
  if (!pick) return;
  const tp = !thGets() && TH.tps ? (TH.tps.find((x) => x.n === TH.tp) || TH.tps[0]) : null;
  pick.hidden = !tp;
  if (!tp) { thTpMenu(false); return; }
  $('th-tp-label').textContent = tp.label;
  $('th-tp-desc').textContent = tp.description || '';
  $('th-tp-now').setAttribute('aria-label', t('themes.tp.now_label', { tp: [tp.label, tp.description].filter(Boolean).join(' ') }));
}

function thTpMenu(open) {
  const menu = $('th-tp-menu');
  if (!menu) return;
  if (!open || !TH.tps || thGets()) {
    menu.hidden = true;
    $('th-tp-now').setAttribute('aria-expanded', 'false');
    return;
  }
  thCasemenu(false);
  const who = String(TH.label || thCaseLabel() || '').replace(/^P\d+\s*-?\s*/, '').trim();
  let html = `<p class="tp-menu-head">${esc(who ? t('themes.tp.head_who', { who }) : t('themes.tp.head'))}</p>`;
  for (const tp of TH.tps) {
    const on = tp.n === TH.tp;
    const state = tp.state === 'none' ? t('themes.tp.none') : tp.state === 'complete' ? t('themes.tp.complete') : t('themes.tp.progress');
    html += `<button type="button" class="ghost" role="menuitemradio" aria-checked="${on}" data-tp="${tp.n}"${tp.state === 'none' ? ' disabled' : ''}>`
      + `<span class="tp-tick" aria-hidden="true">${on ? '&#10003;' : ''}</span><span>${esc(tp.label)}</span>`
      + `<span class="tp-item-desc">${esc(tp.description || '')}</span><span class="tp-item-state">${esc(state)}</span></button>`;
  }
  menu.innerHTML = html;
  menu.hidden = false;
  $('th-tp-now').setAttribute('aria-expanded', 'true');
  const first = menu.querySelector('[aria-checked="true"]') || menu.querySelector('button:not(:disabled)');
  if (first) first.focus();
}

/* another timepoint's PETs canvas for this participant, this one saved first, the way back as it was */
async function thTpGo(n) {
  thTpMenu(false);
  if (!TH.live || TH.busy || !TH.tps || n === TH.tp) return;
  thTitleDone(true);
  thNoteDone(true);
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  themesOpen(TH.path, { back: TH.back, label: TH.label, to: TH.to, timepoint: n });
}

function thTpWire() {
  $('th-tp-now').onclick = (e) => { e.stopPropagation(); thTpMenu($('th-tp-menu').hidden); };
  $('th-tp-menu').onclick = (e) => {
    e.stopPropagation();
    const b = e.target.closest('button');
    if (!b || b.disabled) return;
    thTpGo(Number(b.dataset.tp));
  };
  $('th-tp-menu').onkeydown = (e) => {
    const items = [...$('th-tp-menu').querySelectorAll('button:not(:disabled)')];
    const at = items.indexOf(document.activeElement);
    if (e.key === 'Escape') { e.stopPropagation(); thTpMenu(false); $('th-tp-now').focus(); }
    else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const next = items[(at + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length];
      if (next) next.focus();
    }
  };
  document.addEventListener('click', (e) => {
    if (!$('th-tp-menu').hidden && !e.target.closest('#th-tp-pick')) thTpMenu(false);
  });
}

/* ──────────────────────────────────────────────────────────── GETs ── */

/* The GETs screen: the PETs canvas one layer up, this same code run in a GETs mode. A card is one
   case's PET, sub-theme or statement, or a participant note, his words on what he knows of a
   participant beyond the transcript, its kind and pseudonym over its words, "PET · Juno". A label
   over cards is a GET, a label over labels a sub-theme, and boards, the Current board, history,
   undo, the bin, sticky notes and the Inspector stand as they do for PETs, through the GETs routes.
   A statement edited on its card is the one write here to a workbook, through the PETs board's route,
   which carries it to the case's boards and to this file's copy (30 October, Adam: "Edit there too"),
   and nothing else here writes a workbook or a themes file. Each case
   comes in as a copy of its PETs, which the Cases panel at the left lists, and every row of it drags
   onto the canvas as a card. A GET's badge reads "6 of 8", the cases with a PET, a sub-theme or a
   statement of theirs anywhere under it over the cases in the study, and one under the minimum
   keeps its place and its cards with a dashed outline. */

const GT_ROUTES = { '/api/themes-versions': '/api/gets-ops', '/api/themes-boards': '/api/gets-boards' };
// read as each is asked, so a card's kind follows the method in front (tadraw)
const GT_KINDS = { get pet() { return t('themes.unit.pet'); }, get sub() { return t('themes.kind.sub'); }, get es() { return t('themes.statement'); }, get pn() { return t('themes.kind.pn'); } };
const GT_CASES_KEY = 'idiograph-gets-cases';
const GT_NOT_COMPLETE = t('themes.gets.not_complete');
const gtNotComplete = () => (TH.lgets ? t('themes.gets.not_complete_l') : GT_NOT_COMPLETE);
const GT_CHANGED = t('themes.gets.changed');
const GT_NO_PETS = t('themes.gets.no_pets');
const gtNoPets = () => (TH.lgets ? t('themes.gets.no_lpets') : GT_NO_PETS);
// a timepoint the participant was not interviewed at, on LPETs (21 October)
const GT_NOT_INTERVIEWED = t('themes.gets.not_interviewed');
const thGets = () => TH.mode === 'gets';
// a thematic analysis project, whose codes come onto its themes board with no PETs (tadraw)
const thTa = () => !!(TH.project && TH.project.method === 'ta');
// what a label over cards is called one layer up: a GET on GETs, an LPET on a participant's LPETs
const thGetWord = (many) => (TH.lpets ? (many ? t('themes.unit.lpets') : t('themes.unit.lpet')) : TH.lgets ? (many ? t('themes.unit.lgets') : t('themes.unit.lget')) : many ? t('themes.unit.gets') : t('themes.unit.get'));
const gtRoute = (route) => GT_ROUTES[route] || route;
// on LGETs each card is a participant's LPET (21 October)
const gtKicker = (c) => `${TH.lgets && c.kind === 'pet' ? t('themes.unit.lpet') : GT_KINDS[c.kind] || t('themes.unit.pet')} · ${c.who || ''}`;

/* what a card's key names, as the server's split_key reads it: its case, `group`, `es` or `pn`, the
   group id, line or note number, and for a second card of a PET the number after it */
function gtSplit(key) {
  const text = String(key);
  const at = text.indexOf('/');
  const kase = at < 0 ? text : text.slice(0, at);
  const rest = at < 0 ? '' : text.slice(at + 1);
  const cut = rest.indexOf('/');
  const head = cut < 0 ? rest : rest.slice(0, cut);
  const tail = cut < 0 ? '' : rest.slice(cut + 1);
  if (head === 'es' || head === 'pn') return { kase, kind: head, ident: tail, copy: null };
  return { kase, kind: 'group', ident: head, copy: tail || null };
}

/* the key of a PET's or a sub-theme's first card, which a second one under another GET extends */
const gtBase = (key) => { const k = gtSplit(key); return k.kind === 'group' ? `${k.kase}/${k.ident}` : key; };

/* the GETs screen, opened from the head of All cases, from under the Demo card, or from the PETs
   bar, on the GETs of the project the workbook belongs to */
function getsOpen(path, opts = {}) {
  return themesOpen(path, Object.assign({}, opts, { gets: true }));
}

/* The bar and the panels for the mode the screen opens in: the GETs bar mirrors the PETs bar, the
   project's name in place of the case, GETs the step marked in place of PETs, no Export and no case
   switcher, and the Cases panel's button before the sidebar's. */
function gtScreen(on) {
  $('themes').classList.toggle('gets-mode', on);
  // a participant's LPETs keep the participant picker in their tab, the GETs none (21 October)
  $('themes').classList.toggle('lpets-mode', on && !!TH.lpets);
  // the left panel's button on both screens since 20 October: Cases on GETs, Statements on PETs
  $('th-open-cases').hidden = false;
  $('th-export').hidden = on;
  // Settings on PETs over both boards, GETs' rules being the project's, in Project settings since settingsplit
  $('th-settings').onclick = () => openSettings('pets');
  TH.gets = null;
  // the step in front marked, the cases the others open named once they come (gtLoad)
  thStepsDraw();
  if (!on) { gtCasesShut(false); TH.ssel = new Set(); TH.ssec = null; }
  // every open puts the canvas back whole, and closes the trail, the print card and a note's box
  gtBesideShut();
  gtTrailShut();
  gtPrintShut();
  TH.rowEdit = null;
}

/* GETs from the PETs bar: the canvas saved first, then the GETs of this case's project, with the
   way back to this case's PETs on the board it was on */
async function gtFromPets() {
  if (TH.lpets) { thStageGo(gtFromPets, { gets: true }); return; }
  if (!TH.live || TH.busy || thGets()) return;
  thTitleDone(true);
  thNoteDone(true);
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  const path = TH.path;
  const label = TH.label;
  const board = TH.meta ? TH.meta.id : null;
  const back = TH.back;
  const to = TH.to;
  await navGo(gtFromPets, () => getsOpen(path, { to: 'pets', label: '',
    back: () => themesOpen(path, { back, label, to, board }) }));
}

/* ── the steps (18 October) ── */

/* Distil's three screens as one row on each of its bars, Experiential statements, PETs and GETs, the book's
   steps 2 to 5, 6 and 7 (Smith, Flowers and Larkin, 2022, ch. 5), whose "to-ing and fro-ing" goes both ways,
   so every screen shows the others (Adam, Topic A of 17 October). A step goes to its screen for this case, the
   case of the workbook the screen was opened through, and on a project's GETs or LGETs opened from Home's card
   the participant opened last in the project, at the timepoint opened last (gtStepCase). Where the way back goes there already, the step is the way back, so the screen comes back as he
   left it, and otherwise it opens that screen afresh, its own way back returning to the one he left, as GETs
   from PETs has since 5 October. */
/* the steps of the bars by key, which a way back names the screen it returns to by (TH.to, S.backTo.to, TJ.to),
   never by its words (31 October 2026, the steps' English names until then) */
const TH_STEPS = ['statements', 'pets', 'lpets', 'gets', 'lgets', 'trajectories'];
// the stage in front of him, and where the canvas is, its timepoint or the LPETs, which a way back reopens
const thStageNow = () => (TH.lpets ? 'lpets' : thGets() ? (TH.lgets ? 'lgets' : 'gets') : 'pets');
const thWhere = () => (TH.lpets ? { lpets: true } : TH.tp && !thGets() ? { timepoint: TH.tp } : {});

/* The participant in the path's chooser (option C of the bars, 26 October 2026): the name alone, Wren where the
   case's label is P1 - Wren, as the statements screen shows it, the whole label in its tooltip and kept for what
   names the case in full, an export's heading and the window's title (thCaseLabel). LPETs showed the label
   until then where PETs showed the name. */
function thWhoDraw(label, person = null) {
  const el = $('th-case');
  const full = String(label || '');
  // its number and pseudonym, P2 Mabel, as the rows and the picker say it (pbiobuild, layout A as drawn)
  el.textContent = caseShown(full);
  el.dataset.label = full;
  el.title = full;
  // their picture before the name and their label after it (pbiobuild, layout A)
  if (typeof ppBarDraw === 'function') ppBarDraw($('th-pic'), $('th-label'), person);
}

const thCaseLabel = () => {
  const el = $('th-case');
  return el ? String((el.dataset && el.dataset.label) || el.textContent || '') : '';
};

/* the step in front of him marked, and each other step's tooltip naming the case it opens */
function thStepsDraw() {
  const here = thStageNow();
  const look = thGets() && !TH.lpets ? gtStepCase() : null;
  const who = look ? (look.who || look.case) : '';
  dsTabsDraw('th-steps', TH.project, here);
  // the participant's chooser in the path on PETs and LPETs, and the timepoint's after it on a timepoint's PETs
  thPickerPlace();
  thTpDraw();
  $('th-step-es').title = who ? t('themes.steps.es_who', { who }) : t('themes.steps.es');
  $('th-step-pets').title = here === 'pets' ? t('themes.steps.pets') : (who ? t('themes.steps.pets_who', { who }) : t('themes.steps.pets'));
}

/* The case of the project's GETs that the steps open: the one whose workbook the screen came through, and on
   the GETs or LGETs opened from Home's card the participant opened last in this project, from the recent list
   (`last_opened`, Adam's option B, 26 October), at the timepoint whose PETs were opened last in a project of
   two or more, and the first in case order where none of them has been opened yet. Its `path` is the workbook
   the steps open and `timepoint` theirs, null for none. */
function gtStepCase() {
  const cases = (TH.gets && TH.gets.cases) || [];
  const last = TH.to === 'cases' && TH.gets ? TH.gets.last : null;
  const hit = last && cases.find((c) => c.case === last.case);
  if (hit) return Object.assign({}, hit, { path: last.path, timepoint: Number(last.timepoint) || null });
  const own = cases.find((c) => c.path === TH.path);
  return own ? Object.assign({}, own, { timepoint: null }) : null;
}

/* the workbook and the timepoint the steps open from here: the GETs' step case, else the canvas's own */
const thStepAt = () => {
  const look = thGets() && !TH.lpets ? gtStepCase() : null;
  return look ? { path: look.path || TH.path, timepoint: look.timepoint } : { path: TH.path, timepoint: null };
};

/* the participant's chooser in the path on PETs and a participant's LPETs, and none on the project's GETs and
   LGETs (option C of the bars, 26 October 2026, where it stood in the tab in front) */
function thPickerPlace() {
  const here = thStageNow();
  $('th-cases').hidden = here !== 'pets' && here !== 'lpets';
}

function thStepTo(step) {
  if (step === thStageNow()) return;
  if (step === TH.to) { themesBack(); return; }
  // the LGETs are the project's board in the GETs' place, opened the same way (21 October)
  if (step === 'gets' || step === 'lgets') gtFromPets();
  else if (step === 'pets') gtToPets();
  else if (step === 'lpets') thToLpets();
  else if (step === 'trajectories') thToTraj();
  else if (step === 'codes') thToCodes();
  else thToStatements();
}

/* The Trajectories board from the PETs, LPETs or LGETs bar: the canvas saved and put away, its way back this
   canvas as he left it, as Experiential statements from here does (see thToStatements) */
async function thToTraj() {
  if (!TH.live || TH.busy) return;
  thTitleDone(true);
  thNoteDone(true);
  thVmenu(false);
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  const kept = { gets: thGets(), path: TH.path, label: TH.label, back: TH.back, board: TH.meta ? TH.meta.id : null, to: TH.to };
  const where = thWhere();
  const again = () => themesOpen(kept.path, Object.assign({ back: kept.back, label: kept.label, to: kept.to, board: kept.board,
    gets: kept.gets }, where));
  const leave = () => {
    TH.live = false;
    TH.ask += 1;
    thPile(false);
    thXmenu(false);
    thCasemenu(false);
    thSideShut(false);
    thMenuClose();
    $('themes').hidden = true;
  };
  await navGo(thToTraj, () => trajOpen(kept.path, { leave, back: again, to: thStageNow() }));
}

/* The code list from the Themes bar of a thematic analysis project (codes): the canvas saved and put away, its
   way back this canvas as he left it, as Trajectories from here does */
async function thToCodes(how = {}) {
  if (!TH.live || TH.busy) return;
  thTitleDone(true);
  thNoteDone(true);
  thVmenu(false);
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  const kept = { gets: thGets(), path: TH.path, label: TH.label, back: TH.back, board: TH.meta ? TH.meta.id : null, to: TH.to };
  const where = thWhere();
  const again = () => themesOpen(kept.path, Object.assign({ back: kept.back, label: kept.label, to: kept.to, board: kept.board,
    gets: kept.gets }, where));
  const leave = () => {
    TH.live = false;
    TH.ask += 1;
    thPile(false);
    thXmenu(false);
    thCasemenu(false);
    thSideShut(false);
    thMenuClose();
    $('themes').hidden = true;
  };
  // Open in Code list, from the Inspector on a code, opens it on that code (themesbuild)
  await navGo(thToCodes, () => codesOpen(kept.path, Object.assign({ leave, back: again, to: thStageNow() }, how.open ? { open: how.open } : {})));
}

/* One stage of this participant from another on the PETs and GETs bar (21 October, for the LPETs): the
   canvas saved first, then the stage `opts` names, its way back returning to this canvas as he left it */
async function thStageGo(fn, opts) {
  if (!TH.live || TH.busy) return;
  thTitleDone(true);
  thNoteDone(true);
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  const path = TH.path;
  const label = TH.label;
  const board = TH.meta ? TH.meta.id : null;
  const back = TH.back;
  const to = TH.to;
  const was = Object.assign({ gets: thGets() }, thWhere());
  await navGo(fn, () => themesOpen(path, Object.assign({ to: thStageNow(), label: '',
    back: () => themesOpen(path, Object.assign({ back, label, to, board }, was)) }, opts)));
}

/* the participant's LPETs, from the PETs or GETs bar */
function thToLpets() {
  if (TH.lpets) return Promise.resolve();
  return thStageGo(thToLpets, { gets: true, lpets: true });
}

/* PETs from the GETs bar: the canvas saved first, then the PETs of the case the steps name, with the way
   back to the GETs on the board they were on */
async function gtToPets() {
  if (TH.lpets) { thStageGo(gtToPets, {}); return; }
  if (!TH.live || TH.busy || !thGets()) return;
  thTitleDone(true);
  thNoteDone(true);
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  const path = TH.path;
  const at = thStepAt();
  const board = TH.meta ? TH.meta.id : null;
  const back = TH.back;
  const to = TH.to;
  await navGo(gtToPets, () => themesOpen(at.path, Object.assign({ to: thStageNow(), label: '',
    back: () => getsOpen(path, { back, label: '', to, board }) }, at.timepoint ? { timepoint: at.timepoint } : {})));
}

/* Experiential statements from the PETs or GETs bar where the way back goes elsewhere: the canvas saved and
   put away as a statement's passage puts it away (see thToPassage), the case opened at the passage it was on
   when the statements screen still holds it, and its way back returning to this board as he left it */
async function thToStatements() {
  if (!TH.live || TH.busy) return;
  thTitleDone(true);
  thNoteDone(true);
  thVmenu(false);
  thViewEnd();
  await thFlush();
  if (TH.live && TH.dirty) { say(t('themes.unsaved.stays_open'), 6000); return; }
  if (!TH.live || !TH.v) return;
  const gets = thGets();
  const kept = {
    mode: TH.mode, path: TH.path, label: TH.label, back: TH.back, board: TH.meta ? TH.meta.id : null, to: TH.to,
    view: { x: TH.view.x, y: TH.view.y, z: TH.view.z }, pick: TH.lastPick ? { ...TH.lastPick } : null,
    sel: { cards: [...TH.sel.cards], groups: [...TH.sel.groups], stickies: [...TH.sel.stickies] },
  };
  const where = thWhere();
  const at = thStepAt();
  const again = () => (kept.mode === 'gets' ? getsOpen : themesOpen)(kept.path,
    Object.assign({ back: kept.back, label: kept.label, to: kept.to, board: kept.board, restore: kept }, where));
  const leave = () => {
    TH.live = false;
    TH.ask += 1;
    thPile(false);
    thXmenu(false);
    thCasemenu(false);
    thSideShut(false);
    thExported(null);
    thMenuClose();
    $('themes').hidden = true;
  };
  await navGo(thToStatements, () => openStatements(at.path, { leave, back: again, to: thStageNow(),
    timepoint: gets ? at.timepoint : TH.tp }));
}

/* New sticky note from the bar (18 October): a note of the canvas's own, in no PET, made in the middle
   of the canvas in view, clear of a sidebar lying over it, which settles to the nearest place clear of
   every PET and card as a card dropped there does, its words open as a double-click on empty canvas
   opens them */
function thStickyBar() {
  if (!TH.live || TH.busy) return;
  const r = thStage().getBoundingClientRect();
  let left = r.left;
  let right = r.right;
  for (const id of ['th-side', 'th-cpanel']) {
    const el = $(id);
    if (!el || el.hidden || !el.offsetWidth) continue;
    const b = el.getBoundingClientRect();
    if (b.left >= r.left + r.width / 2 && b.left < right) right = b.left;
    else if (b.right <= r.left + r.width / 2 && b.right > left) left = b.right;
  }
  thStickyNew((left + right) / 2, r.top + r.height / 2, { free: true });
}

/* the cases, the study and the minimum from an answer that carries them */
function gtLoad(data) {
  if (!Array.isArray(data.cases)) return;
  // `last`, the participant opened last in the project, which the steps open from Home's card (gtStepCase)
  const last = data.last_opened !== undefined ? data.last_opened : (TH.gets ? TH.gets.last : null);
  TH.gets = { cases: data.cases, study: data.study || {}, settings: data.settings || {},
    minimum: thTa() ? 0 : Number(data.minimum) || 0, band: !!data.band, total: Number(data.total) || 0, smith: data.smith, last };
  // the GET table's rows of the board on the canvas, and where the print view is, which a server
  // from before them sends none of
  if (data.rows && TH.v && !TH.viewing && (!data.version || !TH.meta || data.version.id === TH.meta.id)) {
    TH.v.rows = JSON.parse(JSON.stringify(data.rows));
  }
  if (data.root !== undefined) TH.root = data.root;
  if (data.gets_print !== undefined) TH.getsPrint = data.gets_print;
  // the Cases panel's folds as he left them in this project
  if (TH.foldRoot !== TH.root) gtFoldsRead();
  gtCasesDraw();
  // the steps' tooltips name the case they open
  thStepsDraw();
}

const gtCase = (name) => ((TH.gets && TH.gets.cases) || []).find((c) => c.case === name) || null;

/* ── a thematic analysis project's codes on its Themes board (codes, 2 November 2026, shot 12) ── */

/* A code is one card: the server folds a code's row cards into its lead (codes.fold), and the page draws the lead
   as the code, Code · 9 extracts, its name, and each participant's letter with how many of its extracts are
   theirs, from the participants' copies. A row of the Participants panel whose code is on the board is placed,
   and dragged it moves the code's card. A code is its name, compared in its words, any case. */
const gtCodeNorm = (s) => String(s || '').split(/\s+/).filter(Boolean).join(' ').toLowerCase();

function gtCodes() {
  const cases = (TH.gets && TH.gets.cases) || [];
  if (TH.codesFrom === cases && TH.codesSeen) return TH.codesSeen;
  const out = new Map();
  for (const c of cases) {
    if (c.in === false) continue;
    for (const [ident, line] of Object.entries(c.lines || {})) {
      const code = gtCodeNorm(line && line.text);
      if (!code) continue;
      if (!out.has(code)) out.set(code, { name: String(line.text).split(/\s+/).filter(Boolean).join(' '), n: 0, by: new Map(), rows: [] });
      const it = out.get(code);
      it.n += 1;
      it.by.set(c.case, (it.by.get(c.case) || 0) + 1);
      // each row of the code, `<case>/es/<line>`, which the Codes panel drags and the Inspector lists (themesbuild)
      it.rows.push(`${c.case}/es/${ident}`);
    }
  }
  TH.codesFrom = cases;
  TH.codesSeen = out;
  return out;
}

/* the code a statement's card or row stands for, by its key, `<case>/es/<line>`, or '' */
function gtCodeOf(key) {
  const k = gtSplit(key);
  if (k.kind !== 'es') return '';
  const entry = gtCase(k.kase);
  const line = entry && entry.lines ? entry.lines[k.ident] : null;
  return gtCodeNorm(line && line.text);
}

/* the card on the board that stands for a code, or null */
function gtCodeCard(v, code) {
  if (!v || !code) return null;
  return Object.keys(v.cards).find((k) => gtCodeOf(k) === code) || null;
}

/* a code's card: Code · 9 extracts, its name, each participant's letter and count, in case order */
function gtCodeCardHtml(v, key, c, parents) {
  const code = gtCodes().get(gtCodeOf(key));
  const n = code ? code.n : 1;
  const whos = code ? [...code.by.entries()].map(([cs, k]) => `${gtBadgeHtml(cs)}<span class="gt-wn">${k}</span>`).join('') : '';
  // Compact on the status bar: the code's name alone (themesbuild, option B of the drawings)
  if (thCompactOn()) {
    const marks = gtMarks(c);
    return `<p class="th-text">${esc(code ? code.name : c.text || '')}</p>`
      + (marks.length ? `<div class="th-foot gt-whos">${marks.map((m) => `<span class="gt-mark">${esc(m)}</span>`).join('')}</div>` : '')
      + thWhyHtml(v, key, parents[key]) + TH_MORE;
  }
  return `<p class="gt-kicker"><span class="gt-ktext">${esc(t('codes.card_kicker', { extracts: t('codes.n.extracts', { n }) }))}</span></p>`
    + `<p class="th-text">${esc(code ? code.name : c.text || '')}</p>`
    + `<div class="th-foot gt-whos">${whos}${gtMarks(c).map((m) => `<span class="gt-mark">${esc(m)}</span>`).join('')}</div>`
    + thWhyHtml(v, key, parents[key]) + TH_MORE;
}

/* ── a thematic analysis project's Themes board as its thematic map (themesbuild, 2 November 2026) ── */

/* Adam's choices of the drawings, 2 November about 20:00: the codes waiting, option A, the panel listing the project's
   codes once, Not placed first then In themes, Participants a tab beside it, and the status bar counting codes from
   the code list, so a code that never reached the board counts as not placed; the Inspector on a code, option A; the
   Inspector on a theme as drawn, its description named Definition; and Compact, option B, a switch on the status bar.
   An IPA project's board is unchanged. */

/* The project's code list as the Code list screen reads it (`/api/codes`), read as the board opens and again after
   a description is kept here. None on an IPA project's board, a participant's LPETs or the LGETs. */
async function gtCodeListRead() {
  TH.codeAsk = (TH.codeAsk || 0) + 1;
  const ask = TH.codeAsk;
  if (!thTa() || !thGets() || TH.lpets || TH.lgets || !TH.path) { TH.codeList = null; return; }
  let data;
  try {
    data = await api('/api/codes', { workbook: TH.path });
  } catch {
    // a server from before the code list, or a list that cannot be read: the board counts its cards as before
    return;
  }
  if (ask !== TH.codeAsk || !TH.live || !thTa() || !thGets()) return;
  gtCodeListTook(data);
}

function gtCodeListTook(data) {
  TH.codeList = data && Array.isArray(data.codes) ? data : null;
  gtCasesDraw();
  thStatusDraw();
  if (TH.panelOpen) thPanelDraw();
  thTableDraw();
}

/* a code of the list by its name as compared, or null */
const gtListed = (code) => ((TH.codeList && TH.codeList.codes) || []).find((c) => gtCodeNorm(c.name) === code) || null;

/* each code's card on the board, by its code as compared */
function gtCodeCards(v) {
  const out = new Map();
  for (const k of Object.keys((v && v.cards) || {})) {
    const code = gtCodeOf(k);
    if (code && !out.has(code)) out.set(code, k);
  }
  return out;
}

/* Where a code stands on the board: `placed` under a theme, `binned` set aside, or `unplaced`, with no card on the
   board or a card in no theme, as a card on the GETs board is counted. */
function gtCodePlace(v, code, cards = gtCodeCards(v), parents = thParents(v)) {
  const key = cards.get(code);
  if (!key) return 'unplaced';
  if (v.discarded.includes(key)) return 'binned';
  return parents[key] !== undefined ? 'placed' : 'unplaced';
}

/* The status bar's numbers on a thematic analysis project's board, counted from the code list: "11 codes: 9 in
   themes, 0 set aside, 2 not placed", and the themes. Null until the list has come, when the cards are counted. */
function gtCodeNumbers(v) {
  if (!TH.codeList || !v) return null;
  const parents = thParents(v);
  const cards = gtCodeCards(v);
  const out = { pets: 0, placed: 0, unplaced: 0, loose: 0, binned: 0, stacked: 0 };
  for (const g of v.groups) if (parents[g.id] === undefined) out.pets += 1;
  // and the subthemes, "3 themes, 1 subtheme", as drawn
  out.subs = v.groups.length - out.pets;
  for (const c of TH.codeList.codes) out[gtCodePlace(v, gtCodeNorm(c.name), cards, parents)] += 1;
  return out;
}

/* each participant's letter and count, for a code as the participants' copies hold it */
const gtWhosHtml = (it) => (it ? [...it.by.entries()].map(([cs, k]) => `${gtBadgeHtml(cs)}<span class="gt-wn">${k}</span>`).join('') : '');

/* The panel's tabs on a thematic analysis project's board, Codes and Participants, in place of its head, and the
   search's words for the tab in front. */
const GT_PTAB_KEY = 'idiograph-gets-ptab';
const gtPtabsOn = () => thTa() && thGets() && !TH.lpets && !TH.lgets;
function gtPtabsDraw() {
  const tabs = $('gt-ptabs');
  if (!tabs) return;
  const on = gtPtabsOn();
  tabs.hidden = !on;
  const head = $('th-cpanel') && $('th-cpanel').querySelector('.th-phead');
  if (head) head.hidden = on;
  for (const b of tabs.querySelectorAll('[data-ptab]')) {
    const front = b.dataset.ptab === TH.ptab;
    b.classList.toggle('on', front);
    b.setAttribute('aria-selected', String(front));
  }
  const find = $('gt-find');
  if (find && on && TH.ptab === 'codes') {
    find.placeholder = t('codes.search');
    find.setAttribute('aria-label', t('codes.search'));
  }
}

function gtPtabSet(tab) {
  if (tab !== 'codes' && tab !== 'participants') return;
  TH.ptab = tab;
  try { localStorage.setItem(GT_PTAB_KEY, tab); } catch { /* a private window keeps it for the page alone */ }
  // the search's words go back to the participants' when that tab comes to the front
  thDoorCount();
  gtCasesDraw();
}

function gtPtabRead() {
  try { TH.ptab = localStorage.getItem(GT_PTAB_KEY) === 'participants' ? 'participants' : 'codes'; } catch { TH.ptab = 'codes'; }
}

/* The Codes tab: every code of the project once, by name, Not placed first and then In themes, each with its
   extracts and each participant's count, a code set aside under Set aside at the panel's foot as a card is. A row
   drags onto the board as the code's card, or moves its card when it is there. A code whose extracts are all
   another's left out of the study has no row to drag. The search finds a code by its name or its description. */
function gtCodesPanelDraw(list) {
  const v = TH.v;
  const find = TH.cfind.trim().toLowerCase();
  const seen = gtCodes();
  const all = TH.codeList
    ? TH.codeList.codes.map((c) => ({ code: gtCodeNorm(c.name), name: c.name, description: c.description || '' }))
    : [...seen.entries()].map(([code, it]) => ({ code, name: it.name, description: '' }));
  const cards = gtCodeCards(v);
  const parents = v ? thParents(v) : {};
  const place = (code) => (v ? gtCodePlace(v, code, cards, parents) : 'unplaced');
  const shown = all.filter((c) => place(c.code) !== 'binned' && gtHit(find, c.name, c.description))
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' }));
  const cases = (TH.gets && TH.gets.cases) || [];
  const row = (c) => {
    const it = seen.get(c.code);
    const first = it && it.rows.length ? gtSplit(it.rows[0]) : null;
    const i = first ? cases.findIndex((x) => x.case === first.kase) : -1;
    const n = it ? it.n : 0;
    const drag = i >= 0 ? ` data-gi="${i}" data-gkind="es" data-gid="${escAttr(first.ident)}"` : '';
    return `<li class="gt-row gt-coderow${place(c.code) === 'placed' ? ' on' : ''}${drag ? '' : ' gt-nodrag'}"${drag}${c.description ? ` title="${escAttr(c.description)}"` : ''}>`
      + `<span class="gt-rtext">${esc(c.name)}</span><span class="gt-rfoot gt-whos"><span class="gt-xn">${esc(n ? t('codes.n.extracts', { n }) : t('codes.no_extracts'))}</span>`
      + `${gtWhosHtml(it)}</span></li>`;
  };
  // each section open until its chevron shuts it, kept with the panel's folds, and open while a search runs
  const sec = (id, name, rows) => {
    const shut = !find && TH.cfold.has(id);
    return `<section class="gt-csec"><button type="button" class="gt-none gt-csec-head${shut ? '' : ' open'}" tabindex="-1" data-gtw="${escAttr(id)}" aria-expanded="${!shut}">`
      + `${GT_CHEV}<span class="gt-rtext">${esc(name)}</span><span class="gt-rn">${rows.length}</span></button>`
      + (shut || !rows.length ? '' : `<ul class="gt-crows">${rows.map(row).join('')}</ul>`) + '</section>';
  };
  let html;
  if (!all.length) html = `<p class="th-qnone">${esc(t('codes.empty'))}</p>`;
  else if (find && !shown.length) html = `<p class="th-qnone">${esc(t('codes.none_found'))}</p>`;
  else {
    html = sec(':codes/out', t('themes.status.name_unplaced'), shown.filter((c) => place(c.code) !== 'placed'))
      + sec(':codes/in', t('codes.board.in_themes'), shown.filter((c) => place(c.code) === 'placed'));
  }
  const top = list.scrollTop;
  list.innerHTML = html;
  list.scrollTop = top;
}

/* a code's extracts as the participants' copies hold them, in case order and then by time: each with its
   participant, its quote, its time and sheet, and its row's key, `<case>/es/<line>`, which Go to the passage opens */
function gtCodeExtracts(it) {
  const cases = (TH.gets && TH.gets.cases) || [];
  const at = (kase) => { const i = cases.findIndex((c) => c.case === kase); return i < 0 ? cases.length : i; };
  const out = [];
  for (const key of (it && it.rows) || []) {
    const k = gtSplit(key);
    const entry = gtCase(k.kase);
    const line = entry && entry.lines ? entry.lines[k.ident] : null;
    if (!line) continue;
    const q = gtLineQuotes(line, k.ident)[0];
    out.push({ key, kase: k.kase, who: entry.who || k.kase, text: q ? thBareQuote(q.text) : '', qkey: q ? q.key : '', time: line.time || '',
      sheet: line.sheet || '', seconds: Number.isFinite(Number(line.seconds)) && line.seconds !== null && line.seconds !== '' ? Number(line.seconds) : 1e12, row: Number(line.row) || 0 });
  }
  return out.sort((a, b) => at(a.kase) - at(b.kase) || a.seconds - b.seconds || String(a.sheet).localeCompare(String(b.sheet)) || a.row - b.row);
}

/* The Inspector on a code's card (option A of the drawings): its name and each participant's count, its
   description, the same field as on the Code list, the theme it sits in, Take out of theme and Open in Code list,
   then every extract by participant, each with Go to the passage. */
function gtCodePanelHtml(v, key, owner) {
  const c = v.cards[key];
  const code = gtCodeOf(key);
  const it = gtCodes().get(code);
  const listed = gtListed(code);
  const name = listed ? listed.name : it ? it.name : c.text || '';
  const marks = gtMarks(c).map((m) => `<span class="gt-mark">${esc(m)}</span>`).join('');
  const parents = thParents(v);
  const holder = owner !== undefined && thIsGroup(v, owner) ? thGroup(v, owner) : null;
  const where = holder ? thLabelShown(holder.label) : v.discarded.includes(key) ? t('themes.status.name_binned') : t('themes.status.name_unplaced');
  const kind = holder && parents[owner] !== undefined ? t('themes.kind.sub') : t('codes.board.theme');
  const locked = thLocked(v);
  const leave = holder && !locked ? `<button type="button" class="ghost small btn-out th-leave" tabindex="-1" data-leave="${escAttr(key)}" `
    + `title="${escAttr(t('themes.leave.tip', { name: thLabelShown(holder.label) }))}">${esc(thLeaveLabel(v, owner))}</button>` : '';
  const open = listed ? `<button type="button" class="ghost small" tabindex="-1" data-codeopen="${escAttr(listed.id)}">${esc(t('codes.board.open'))}</button>` : '';
  let desc = '';
  if (listed) {
    const typed = TH.codeDesc && TH.codeDesc.id === listed.id ? TH.codeDesc.value : listed.description || '';
    desc = `<label class="section-label gt-clabel" for="gt-cdesc">${esc(t('codes.description'))}</label>`
      + (locked ? `<p class="gt-read">${esc(listed.description || '')}</p>`
        : `<textarea class="th-vedit gt-cdesc" id="gt-cdesc" data-code="${escAttr(listed.id)}" rows="2" maxlength="2000" spellcheck="true">${esc(typed)}</textarea>`);
  }
  let html = `<p class="th-panel-title">${esc(name)}</p><p class="th-panel-meta gt-whos">${gtWhosHtml(it)}${marks}</p>`
    + thLeftOutHtml(v, key, owner) + desc
    + `<p class="gt-cin"><span class="section-label">${esc(kind)}</span><span class="gt-cin-name">${esc(where)}</span></p>`
    + (leave || open ? `<div class="th-leave-row gt-cacts">${leave}${open}</div>` : '')
    + `<h3 class="section-label">${esc(t('codes.col.extracts'))}</h3>`;
  const xs = gtCodeExtracts(it);
  if (!xs.length) return `${html}<p class="th-qnone">${esc(t('codes.none_yet'))}</p>`;
  // under a theme each extract carries a tick, its participant's key extract for the theme, the row's quote the
  // GETs file keeps for IPA's board too (gtTick), the first in the theme's order ticked faint until he picks one
  const get = gtTopOf(v, key, parents);
  const keyOf = new Map();
  if (get) for (const x of xs) if (!keyOf.has(x.kase)) keyOf.set(x.kase, gtTaKeyExtract(v, get.id, x.kase));
  const tick = (x) => {
    const kq = get && x.qkey ? keyOf.get(x.kase) : null;
    if (!kq) return '';
    const on = kq.key === x.qkey;
    return `<button type="button" class="th-tick${on ? ' on' : ''}${on && !kq.chosen ? ' gt-auto' : ''}" tabindex="-1" data-gtick="${escAttr(x.qkey)}" `
      + `data-gget="${escAttr(get.id)}" data-gcase="${escAttr(x.kase)}"${locked ? ' disabled' : ''} aria-pressed="${on}" `
      + `title="${escAttr(on ? (kq.chosen ? t('themes.gets.tick_chosen') : t('themes.gets.tick_auto')) : t('themes.gets.tick_other', { who: x.who, label: thLabelShown(get.label) }))}">${TH_TICK_ICON}</button>`;
  };
  let last = null;
  for (const x of xs) {
    if (x.kase !== last) {
      last = x.kase;
      const n = xs.filter((y) => y.kase === x.kase).length;
      html += `<p class="gt-cwho">${gtBadgeHtml(x.kase)}<span>${esc(x.who)}</span><span class="gt-cwho-n">${esc(t('codes.n.extracts', { n }))}</span></p>`;
    }
    const ticked = tick(x);
    html += `<div class="gt-cx${ticked ? ' gt-cxt' : ''}">${ticked}<div><p class="gt-quote gt-cxq">${esc(x.text ? thQuoted(x.text) : t('themes.inspector.no_quote'))}</p>`
      + `<p class="gt-cxfoot"><span class="th-time">${esc(x.time)}</span>${thSheetTag(x.sheet)}`
      + `<button type="button" class="ghost small gt-cgo" tabindex="-1" data-gopass="${escAttr(x.key)}">${esc(t('codes.go'))}</button></p></div></div>`;
  }
  return html;
}

/* A participant's key extract under a theme of a thematic analysis project: the one he ticked, kept as the theme's row
   for that participant (`rows`, as on IPA's board), else the first of theirs in the order the theme reads its codes,
   `{ key, chosen }`, or null when the theme holds none of theirs. */
function gtTaKeyExtract(v, gid, kase) {
  const stored = ((gtRows(v)[gid] || {})[kase] || {}).quote || '';
  const codes = gtCodes();
  let first = null;
  for (const { key } of gtItems(v, gid)) {
    const c = v.cards[key];
    if (!c || c.kind !== 'es' || v.discarded.includes(key)) continue;
    for (const x of gtCodeExtracts(codes.get(gtCodeOf(key)))) {
      if (x.kase !== kase || !x.qkey) continue;
      if (x.qkey === stored) return { key: stored, chosen: true };
      if (!first) first = x.qkey;
    }
  }
  return first ? { key: first, chosen: false } : null;
}

/* A code's description kept from the Inspector as it loses the focus, through the code list's own operation, as
   the Code list keeps it: one change of the list, which its Undo takes back. Esc leaves it as it was. */
function gtCodeDescStart(box) {
  if (TH.codeDesc && TH.codeDesc.id === box.dataset.code) return;
  TH.codeDesc = { id: box.dataset.code, value: box.value };
}

async function gtCodeDescDone(keep) {
  const ed = TH.codeDesc;
  if (!ed) return;
  TH.codeDesc = null;
  const box = $('gt-cdesc');
  const text = (box && box.dataset.code === ed.id ? box.value : ed.value).replace(/[\r\n]+/g, ' ').trim();
  const c = ((TH.codeList && TH.codeList.codes) || []).find((x) => x.id === ed.id);
  if (!keep || !c || text === (c.description || '') || !TH.live) { if (TH.panelOpen) thPanelDraw(); return; }
  try {
    const data = await api('/api/codes-ops', { workbook: TH.path, ops: [{ op: 'describe', code: c.id, description: text }], v: TH.codeList.v });
    gtCodeListTook(data);
    if ((data.changes || []).length) say(data.changes.join(' '), 4000);
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    // a list changed since the board read it is read again, as the Code list does
    gtCodeListRead();
  }
}

/* Open in Code list, from the Inspector on a code: the board saved and put away, the Code list open on that code */
function gtCodeOpen(id) {
  if (!TH.live || TH.busy) return;
  thToCodes({ open: id });
}

/* The Inspector on a theme or a subtheme of a thematic analysis project (as drawn): its description under the name
   Definition, how many codes, extracts and participants it holds, Auto-arrange and Audit trail on one row, its codes
   and subthemes in the order its frame reads them, each participant's extracts counted from every code under it,
   and its note. */
function gtThemePanelHtml(v, g, owner) {
  const codes = gtCodes();
  const inside = gtInside();
  const under = new Set(thCardsUnder(v, g.id).filter((k) => v.cards[k] && v.cards[k].kind === 'es' && !v.discarded.includes(k)).map(gtCodeOf).filter(Boolean));
  let extracts = 0;
  const per = new Map();
  for (const code of under) {
    const it = codes.get(code);
    if (!it) continue;
    for (const [cs, k] of it.by) {
      if (!inside.has(cs)) continue;
      extracts += k;
      per.set(cs, (per.get(cs) || 0) + k);
    }
  }
  const total = TH.gets ? TH.gets.total : 0;
  const counts = t('codes.board.theme_counts', { codes: t('codes.n.codes', { n: under.size }), extracts: t('codes.n.extracts', { n: extracts }),
    participants: gtCountText(gtCount(v, g.id), total) });
  const trail = owner === undefined
    ? `<button type="button" class="ghost small gt-trail-go" tabindex="-1" data-gtrail="${escAttr(g.id)}">${esc(t('themes.gets.trail'))}</button>` : '';
  const arrange = thLocked(v) ? '' : `<button type="button" class="ghost small th-arrange" tabindex="-1" data-arrange="${escAttr(g.id)}" `
    + `title="${escAttr(t('themes.arrange.panel_tip'))}">${esc(t('themes.label.arrange_label'))}</button>`;
  const rows = [];
  for (const m of thThemeOrder(v, g.id, TH.layout || {})) {
    if (thIsGroup(v, m)) {
      if (m !== g.id) rows.push(`<li class="gt-tsub"><span>${esc(thLabelShown(thGroup(v, m).label))}</span><span class="gt-tn">${esc(t('themes.unit.sub'))}</span></li>`);
      continue;
    }
    const c = v.cards[m];
    if (!c || c.kind !== 'es' || v.discarded.includes(m)) continue;
    const it = codes.get(gtCodeOf(m));
    rows.push(`<li><span>${esc(it ? it.name : c.text || '')}</span><span class="gt-tn">${it ? it.n : ''}</span></li>`);
  }
  const people = ((TH.gets && TH.gets.cases) || []).filter((c) => inside.has(c.case))
    .map((c) => `<li class="${per.has(c.case) ? '' : 'gt-none'}">${gtBadgeHtml(c.case)}<span>${esc(c.who)}</span>`
      + `<span class="gt-tn">${esc(per.has(c.case) ? t('codes.n.extracts', { n: per.get(c.case) }) : t('themes.gets.nothing_under'))}</span></li>`);
  return `<label class="section-label gt-clabel" for="th-gdesc">${esc(t('codes.board.definition'))}</label>` + thDescHtml(v, g)
    + `<p class="kicker">${esc(owner !== undefined ? t('themes.kind.sub') : t('codes.board.theme'))}</p>`
    + `<p class="th-panel-meta"><span>${esc(counts)}</span></p>`
    + (arrange || trail ? `<div class="th-leave-row gt-acts">${arrange}${trail}</div>` : '')
    + thLeaveHtml(v, g.id, owner)
    + `<h3 class="section-label">${esc(t('codes.codes'))}</h3>`
    + (rows.length ? `<ul class="gt-tcodes">${rows.join('')}</ul>` : `<p class="th-qnone">${esc(t('themes.inspector.no_statements'))}</p>`)
    + `<h3 class="section-label">${esc(t('themes.cases.head'))}</h3>`
    + (people.length ? `<ul class="gt-tpeople">${people.join('')}</ul>` : `<p class="th-qnone">${esc(t('themes.gets.no_participant'))}</p>`)
    + `<h3 class="section-label">${esc(t('themes.kind.note'))}</h3>` + thNoteHtml(v, g);
}

/* Compact, on the status bar of a thematic analysis project's board (option B of the drawings): each code's card its
   name alone, so one screen holds more of the board, the cards staying where he put them. Off on a new install and
   kept in the settings, as Extracts on cards is. */
const thCompactOn = () => thTa() && thGets() && !!(TH.config && TH.config.card_compact === true);

function thCompactToggle() {
  if (!TH.live || TH.drag || !thTa()) return;
  thStatusSave('card_compact', !(TH.config && TH.config.card_compact === true));
}

function thCompactButton() {
  const btn = $('th-compact-btn');
  if (!btn) return;
  btn.hidden = !(thTa() && thGets());
  btn.setAttribute('aria-pressed', String(thCompactOn()));
}

/* A thematic analysis project's table of themes (themesbuild: it listed each theme by participant and said "No PETs,
   so nothing under this GET"): each theme in canvas order with its definition and note, its codes in the order its
   frame reads them, each with its extracts by participant, its subthemes inside it the same way, then the codes in no
   theme, those with a card first, and those set aside. */
function gtTableTa(v) {
  const tints = thTints(v);
  const parents = thParents(v);
  const total = TH.gets ? TH.gets.total : 0;
  const codes = gtCodes();
  const xsHtml = (it) => {
    const xs = gtCodeExtracts(it);
    return xs.length ? `<ul class="gt-txs">${xs.map((x) => `<li>${gtBadgeHtml(x.kase)}<span class="gt-txwho">${esc(x.who)}</span>`
      + `<span class="th-time">${esc(x.time)}</span>${thSheetTag(x.sheet)}<span class="gt-txq">${esc(x.text ? thQuoted(x.text) : '')}</span></li>`).join('')}</ul>` : '';
  };
  const item = (key, parent) => {
    const c = v.cards[key] || {};
    if (c.kind === 'pn') {
      return `<li class="tb-item${thTableSelCls('statement', key)}" data-trow="${escAttr(key)}" data-tkind="statement" data-tparent="${escAttr(parent)}">`
        + `${thTableGrip(t('themes.table.this_card'))}<span class="tb-kind">${esc(t('themes.kind.note'))}</span><span class="tb-said">${esc(c.text || '')}</span>${thTableMore()}</li>`;
    }
    const it = codes.get(gtCodeOf(key));
    const n = it ? it.n : 0;
    return `<li class="tb-item gt-tcode${thTableSelCls('statement', key)}" data-trow="${escAttr(key)}" data-tkind="statement" data-tparent="${escAttr(parent)}">`
      + `${thTableGrip(t('themes.table.this_card'))}<span class="tb-kind">${esc(t('themes.statement'))}</span>`
      + `<span class="tb-said">${esc(it ? it.name : c.text || '')} <span class="tb-in">${esc(t('codes.n.extracts', { n }))}</span></span>${thTableMore()}`
      + `${xsHtml(it)}</li>`;
  };
  const theme = (gid, parent, depth) => {
    const g = thGroup(v, gid);
    const n = gtCount(v, gid);
    const order = thThemeOrder(v, gid, TH.layout || {});
    const own = order.filter((m) => !thIsGroup(v, m) && thOnCanvas(v, m) && v.cards[m]);
    const subs = depth < 8 ? order.filter((m) => thIsGroup(v, m) && m !== gid) : [];
    const cls = depth ? `tb-label tb-getsub${depth > 1 ? ' deep' : ''}` : 'tb-pet tb-get';
    return `<section class="${cls} ${thTintClass(tints[gid])}${thTableSelCls('label', gid)}" data-trow="${escAttr(gid)}" data-tkind="label" data-tparent="${escAttr(parent)}">`
      + thTableHeadHtml(v, { id: gid, code: '', title: thLabelShown(g.label), depth }, `<span class="tb-badge" title="${escAttr(gtCountText(n, total))}">${esc(t('themes.gets.of', { count: n, total }))}</span>`)
      + (thNoteOf(g) ? `<p class="tb-note">${esc(thNoteOf(g))}</p>` : '')
      + (depth ? '' : `<button type="button" class="ghost small tb-trail" data-gtrail="${escAttr(gid)}">${esc(t('themes.gets.trail'))}</button>`)
      + `<div class="tb-body" data-tbody="${escAttr(gid)}">`
      + (own.length ? `<ul class="tb-items">${own.map((k) => item(k, gid)).join('')}</ul>` : '')
      + (subs.length ? `<div class="tb-subs">${subs.map((s) => theme(s, gid, depth + 1)).join('')}</div>` : '')
      + '</div></section>';
  };
  const tops = gtCanvasOrder(v.groups.filter((g) => parents[g.id] === undefined));
  let html = '<div class="tb-pets" data-tbody="">';
  if (!tops.length) html += `<p class="tb-none">${esc(t('themes.table.no_gets'))}</p>`;
  html += tops.map((gid) => theme(gid, '', 0)).join('') + '</div>';
  // in no theme: each code's card loose on the canvas, a row to drag, then each code that never reached the board
  const loose = Object.keys(v.cards).filter((k) => (thOnCanvas(v, k) || thWaiting(v, k)) && parents[k] === undefined);
  const cards = gtCodeCards(v);
  const away = ((TH.codeList && TH.codeList.codes) || []).filter((c) => !cards.has(gtCodeNorm(c.name)));
  if (loose.length || away.length) {
    html += `<div class="tb-rest"><p class="tb-rest-head">${esc(t('themes.table.not_placed', { n: loose.length + away.length }))}</p><ul class="tb-items tb-loose" data-tbody="${TH_TABLE_LOOSE}">`
      + loose.map((k) => item(k, '')).join('')
      + away.map((c) => {
        const it = codes.get(gtCodeNorm(c.name));
        const n = it ? it.n : 0;
        return `<li class="tb-item gt-tcode gt-taway"><span class="tb-grip tb-nogrip" aria-hidden="true"></span><span class="tb-kind">${esc(t('themes.statement'))}</span>`
          + `<span class="tb-said">${esc(c.name)} <span class="tb-in">${esc(n ? t('codes.n.extracts', { n }) : t('codes.no_extracts'))}</span></span>${xsHtml(it)}</li>`;
      }).join('') + '</ul></div>';
  }
  return html + thTableBin(v);
}

/* the table's rows in the order they read, for a thematic analysis project's table (see thTableFlat) */
function gtTableTaFlat(v) {
  const out = [];
  const parents = thParents(v);
  const walk = (gid, depth) => {
    out.push({ id: gid, kind: 'label' });
    const order = thThemeOrder(v, gid, TH.layout || {});
    for (const m of order) if (!thIsGroup(v, m) && thOnCanvas(v, m) && v.cards[m]) out.push({ id: m, kind: 'statement' });
    if (depth < 8) for (const m of order) if (thIsGroup(v, m) && m !== gid) walk(m, depth + 1);
  };
  for (const gid of gtCanvasOrder(v.groups.filter((g) => parents[g.id] === undefined))) walk(gid, 0);
  for (const k of Object.keys(v.cards)) if (thOnCanvas(v, k) && parents[k] === undefined) out.push({ id: k, kind: 'statement' });
  return out;
}

/* ── each case's colour and badge (16 October) ── */

/* On the GETs board each case keeps a colour of its own, so whose PET a card is, and which PETs,
   sub-themes and statements belong together, shows at a glance, the cases staying visible inside
   the GETs (Smith, Flowers and Larkin, 2022, ch. 5). The cases' palette is themes.css's
   `--th-case0` to `--th-case24`, named here in its order, the eight of 16 October first and More
   colours' seventeen after them (21 October), a case taking its place in case order, or the next
   colour free after it, until he chooses another from the swatch on its row in the Cases panel. Every card of a
   case carries its colour along its top edge and a badge of the participant's initial in its
   kicker, two letters where two cases share one, as the server works them out. A server from before
   the colours sends none, and the page then works them out the same way. */
const GT_COLOURS = [t('themes.colour.blue'), t('themes.colour.olive'), t('themes.colour.plum'), t('themes.colour.brown'), t('themes.colour.indigo'), t('themes.colour.teal'), t('themes.colour.purple'), t('themes.colour.slate'),
  t('themes.colour.moss'), t('themes.colour.spruce'), t('themes.colour.violet'), t('themes.colour.aubergine'), t('themes.colour.pine'), t('themes.colour.denim'), t('themes.colour.khaki'), t('themes.colour.mulberry'), t('themes.colour.fern'), t('themes.colour.periwinkle'), t('themes.colour.umber'),
  t('themes.colour.grape'), t('themes.colour.ocean'), t('themes.colour.amethyst'), t('themes.colour.jade'), t('themes.colour.navy'), t('themes.colour.fig')];
// the eight the picker shows first, the rest under More colours
const GT_FIRST_COLOURS = 8;
const GT_MORE_COLUMNS = 5;

function gtLook(name) {
  const cases = (TH.gets && TH.gets.cases) || [];
  const at = cases.findIndex((c) => c.case === name);
  const c = at < 0 ? null : cases[at];
  const place = (n, or) => (Number.isInteger(n) && n >= 0 && n < GT_COLOURS.length ? n : or);
  const fallback = Math.max(0, at) % GT_COLOURS.length;
  const plain = (c && c.who) || String(name || '').replace(/^P\d+\s*-\s*/, '');
  const initial = String(plain).replace(/[^\p{L}\p{N}]/gu, '').slice(0, 1).toUpperCase() || '?';
  return { colour: place(c && c.colour, fallback), default: place(c && c.default, fallback), chosen: !!(c && c.chosen),
    badge: (c && c.badge) || initial };
}

/* a case's badge, its initial in a dot of its colour, beside its name, which says it for a screen reader */
const gtBadgeHtml = (name) => {
  const look = gtLook(name);
  return `<span class="gt-badge case-${look.colour}" aria-hidden="true">${esc(look.badge)}</span>`;
};

/* The badge on a card keeps its letter legible as the canvas zooms out (16 October, later): its
   letter is 10px at 100% and never drawn under 9px on the screen, so below 90% the badge grows by
   `up`, upward from the kicker's foot, the card keeping its height, until it stands as tall as the
   card's head, its top at the card's top edge. Past that, `far`, the letter could no longer be read
   and the badge keeps its disc of the case's colour without it. The canvas's print page does the same
   by the scale it prints at. */
const GT_BADGE_LETTER = 10;
const GT_BADGE_FLOOR = 9;
const GT_BADGE_MOST = 25 / 15;
function gtBadgeUp(z) {
  const need = GT_BADGE_FLOOR / (GT_BADGE_LETTER * (Number(z) || 1));
  return { up: Math.min(GT_BADGE_MOST, Math.max(1, need)), far: need > GT_BADGE_MOST + 1e-9 };
}

/* the cases of the study: those Settings has not taken out */
function gtInside() {
  return new Set(((TH.gets && TH.gets.cases) || []).filter((c) => c.in).map((c) => c.case));
}

/* The cases with a PET, a sub-theme or a statement of theirs anywhere under a GET, sub-themes
   included, of the cases in the study. A participant note never counts. */
function gtCount(v, gid) {
  const inside = gtInside();
  const found = new Set();
  for (const key of thCardsUnder(v, gid)) {
    const c = v.cards[key];
    if (!c || c.kind === 'pn' || !inside.has(c.case)) continue;
    found.add(c.case);
    // a thematic analysis project's code card stands for every participant whose extracts it holds (codes)
    if (thTa() && c.kind === 'es') {
      const code = gtCodes().get(gtCodeOf(key));
      for (const cs of code ? code.by.keys() : []) if (inside.has(cs)) found.add(cs);
    }
  }
  return found.size;
}

/* The PETs and sub-themes of the study under no GET, for the count of those left (20 October: "Every PET
   placed" showed when it was not so): each one of a case in the study, whether it has a card on the board or
   not, under no GET unless a card of it is, and one whose every card is in the bin is not left. `placed`
   counts those under a GET. When no case carries its PETs, as from a server before them, the cards on the
   board stand in. */
function gtTally(v) {
  const parents = thParents(v);
  const cases = ((TH.gets && TH.gets.cases) || []).filter((c) => c.in);
  const units = new Set();
  for (const c of cases) {
    const byId = Object.fromEntries((c.pets || []).map((p) => [p.id, p]));
    for (const p of c.pets || []) {
      const up = p.parent ? byId[p.parent] : null;
      if (!p.parent || (up && !up.parent)) units.add(`${c.case}/${p.id}`);
    }
  }
  if (!cases.some((c) => Array.isArray(c.pets))) {
    for (const [key, c] of Object.entries(v.cards)) if (c.kind === 'pet' || c.kind === 'sub') units.add(gtBase(key));
  }
  const under = new Set();
  const kept = new Set();
  for (const [key, c] of Object.entries(v.cards)) {
    if (c.kind !== 'pet' && c.kind !== 'sub') continue;
    const base = gtBase(key);
    if (v.discarded.includes(key)) continue;
    kept.add(base);
    if (parents[key] !== undefined) under.add(base);
  }
  const binned = (u) => !kept.has(u) && Object.keys(v.cards).some((k) => gtBase(k) === u && v.discarded.includes(k));
  let left = 0;
  let placed = 0;
  for (const u of units) {
    if (under.has(u)) placed += 1;
    else if (!binned(u)) left += 1;
  }
  return { left, placed };
}
const gtLeft = (v) => gtTally(v).left;

/* the GET a card sits in, the label at the top of what holds it, or null */
function gtTopOf(v, key, parents = thParents(v)) {
  const up = thAncestors(v, key, parents);
  return up.length ? thGroup(v, up[up.length - 1]) : null;
}

/* What a card names under its words. A statement names its PET and that PET's GET, and a second
   card of a PET under another GET names the other one, as the first one does. */
function gtFrom(v, key, c, parents) {
  // a thematic analysis project's codes are in no PET, which its cards never say (tadraw)
  if (c.kind === 'es' && thTa()) return '';
  if (c.kind === 'es') {
    const entry = gtCase(c.case);
    const pet = entry && c.pet ? (entry.pets || []).find((p) => p.id === c.pet) : null;
    const line = entry && entry.lines ? entry.lines[gtSplit(key).ident] : null;
    if (!pet) return line && line.discarded ? t('themes.gets.from_aside') : t('themes.gets.from_unplaced');
    const holder = Object.keys(v.cards).find((k) => gtBase(k) === `${c.case}/${pet.id}` && !v.discarded.includes(k));
    const get = holder ? gtTopOf(v, holder, parents) : null;
    // said as what it is, the PET it sits in on its case's board and that PET's GET (20 October: Adam read a PET's
    // title here, "A dog giving her days a start", as a note of unknown source)
    const unit = TH.lgets ? t('themes.unit.lpet') : t('themes.unit.pet');
    return get ? t('themes.gets.from_get', { unit, title: pet.title, get: thGetWord(), label: thLabelShown(get.label) }) : t('themes.gets.from_pet', { unit, title: pet.title });
  }
  if (c.kind !== 'pet' && c.kind !== 'sub') return '';
  const base = gtBase(key);
  const others = Object.keys(v.cards).filter((k) => k !== key && gtBase(k) === base && !v.discarded.includes(k));
  if (!others.length) return '';
  const gets = others.map((k) => gtTopOf(v, k, parents)).filter(Boolean).map((g) => thLabelShown(g.label));
  return gets.length ? t('themes.gets.also_under', { names: [...new Set(gets)].join(', ') }) : t('themes.gets.also_here');
}

/* the marks a card carries: its case's PETs not complete, or no longer in its case */
function gtMarks(c) {
  if (c.gone) return [c.kind === 'es' ? t('themes.table.gone') : t('themes.gets.gone', { who: c.who })];
  return c.open && !thTa() ? [gtNotComplete()] : [];
}

/* a PET's or a sub-PET's description on its card on the GETs board, as its participant's board holds it (21 October) */
const gtCardDesc = (c) => ((c && (c.kind === 'pet' || c.kind === 'sub') && !c.gone) ? thDescOf(c) : '');

function gtCardHtml(v, key, c, parents) {
  if (thTa() && c.kind === 'es') return gtCodeCardHtml(v, key, c, parents);
  const from = gtFrom(v, key, c, parents);
  const why = thWhyHtml(v, key, parents[key]);
  const n = Number(c.statements) || 0;
  // a PET's or a sub-theme's count is its chevron too, which unfolds the card in place (21 October)
  const folds = gtUnfoldable(key, c);
  const open = folds && TH.unfolded.has(key);
  const count = esc(t('themes.count.statements', { n }));
  const foot = c.kind === 'es' ? `<span class="th-time">${esc(c.time || '')}</span>${thSheetTag(c.sheet)}`
    : folds ? `<button type="button" class="gt-unfold gt-n${open ? ' open' : ''}" tabindex="-1" data-unfold="${escAttr(key)}" `
      + `aria-expanded="${open}" title="${escAttr(open ? t('themes.gets.fold') : t('themes.gets.unfold'))}">${GT_CHEV}${count}</button>`
      : (c.kind === 'pet' || c.kind === 'sub') && !c.gone ? `<span class="gt-n">${count}</span>` : '';
  const words = c.text || (c.kind === 'pn' ? t('themes.kind.pn') : '');
  return `<p class="gt-kicker">${gtBadgeHtml(c.case)}<span class="gt-ktext">${esc(gtKicker(c))}</span></p><p class="th-text${c.text ? '' : ' gt-empty'}">${esc(words)}</p>`
    + (gtCardDesc(c) ? `<p class="gt-desc">${esc(gtCardDesc(c))}</p>` : '')
    + (from ? `<p class="gt-from">${esc(from)}</p>` : '')
    + thKqHtml(v, key) + thEnHtml(v, key)
    + `<div class="th-foot">${foot}${gtMarks(c).map((m) => `<span class="gt-mark">${esc(m)}</span>`).join('')}</div>`
    + (open ? gtUnfoldHtml(key, c) : '') + why
    // and the "⋯" a selected card carries on the PETs canvas, which opens its menu under it, since dressing
    // the card for GETs wrote over the one thRender gave it (17 October)
    + TH_MORE;
}

/* ── a PET card unfolded in place (Adam, 20 October, from a tester's wish to see a PET's statements on GETs) ── */

/* A PET's or a sub-theme's card unfolds in place from the chevron on its count, or Unfold in its menu: under
   its foot its sub-themes, each statement with its quote, its exploratory notes when Notes on cards is on, and a
   statement's stack under its top, as its participant's board holds them. Nothing is placed: no card comes on
   the board. It folds again the same way. A view, so no step of undo and nothing in the GETs file: which cards
   are unfolded is kept in the browser with the board's view, by the project and the board, across a reload. The
   room the taller card takes is made as a quote's is (see thRoomMake), so Arrange and Fit all take its height.
   The Table view and the print are unchanged. */
const GT_UNFOLD_KEY = 'idiograph-gets-unfolded';

/* the PET or sub-theme of a card's participant, or null */
function gtUnfoldPet(key, c) {
  if (!c || (c.kind !== 'pet' && c.kind !== 'sub') || c.gone) return null;
  const entry = gtCase(c.case);
  const id = gtSplit(key).ident;
  const pet = entry ? (entry.pets || []).find((p) => p.id === id) : null;
  return pet ? { entry, pet } : null;
}

/* a card unfolds when its PET or sub-theme holds a statement or a sub-theme */
function gtUnfoldable(key, c) {
  const at = gtUnfoldPet(key, c);
  if (!at) return false;
  const lines = at.entry.lines || {};
  return (at.pet.statements || []).some((k) => lines[k]) || (at.pet.subs || []).length > 0;
}

/* What an unfolded card shows under its foot: its own statements, then each sub-theme by its title with the
   statements under it at any depth, as the Participants panel's tree has them, each statement stacked under
   another standing under its top. */
function gtUnfoldHtml(key, c) {
  const at = gtUnfoldPet(key, c);
  if (!at) return '';
  const lines = at.entry.lines || {};
  const byId = Object.fromEntries((at.entry.pets || []).map((p) => [p.id, p]));
  const under = gtStacked(lines);
  const stacked = new Set(Object.values(under).flat());
  const deep = (p, seen) => {
    if (!p || seen.has(p.id)) return [];
    seen.add(p.id);
    return [...(p.statements || []), ...(p.subs || []).flatMap((s) => deep(byId[s], seen))];
  };
  const line = (k, kids = true) => {
    const l = lines[k];
    if (!l) return '';
    const q = gtLineQuotes(l, k)[0];
    const quote = q ? thBareQuote(q.text) : '';
    const notes = thNotesOn() ? (l.notes || []).map((x) => String(x || '').trim()).filter(Boolean) : [];
    const stack = kids ? (under[k] || []).filter((x) => lines[x]) : [];
    return `<li class="gt-uline"><p class="gt-utext">${esc(l.text || '')}</p>`
      // three lines at most, or whole while Quotes on cards is at Full (30 October)
      + (quote ? (thQuotesWay() === 'full' ? `<p class="gt-uq gt-uq-full">${esc(thQuoted(quote))}</p>`
        : `<p class="gt-uq" title="${escAttr(thQuoted(quote))}">${esc(thQuoted(quote))}</p>`) : '')
      + (notes.length ? `<p class="gt-uen" title="${escAttr(notes.join('\n'))}">${esc(notes.join(' · '))}</p>` : '')
      + `<p class="gt-ufoot"><span class="th-time">${esc(l.time || '')}</span>${thSheetTag(l.sheet)}</p>`
      + (stack.length ? `<ul class="gt-ustack">${stack.map((x) => line(x, false)).join('')}</ul>` : '')
      + '</li>';
  };
  const list = (keys) => keys.filter((k) => lines[k] && !stacked.has(k)).map((k) => line(k)).join('');
  const seen = new Set([at.pet.id]);
  let html = list(at.pet.statements || []);
  html = html ? `<ul class="gt-ulist">${html}</ul>` : '';
  for (const sid of at.pet.subs || []) {
    const s = byId[sid];
    if (!s || seen.has(s.id)) continue;
    const rows = list(deep(s, seen));
    html += `<p class="gt-usub"><span class="gt-ukind">${esc(t('themes.kind.sub'))}</span>${esc(s.title || '')}</p>`
      + (rows ? `<ul class="gt-ulist">${rows}</ul>` : '');
  }
  return `<div class="gt-unfolded">${html}</div>`;
}

/* the cards left unfolded on the board now on the canvas, of those it has */
function gtUnfoldRead(cards) {
  TH.unfolded = new Set();
  try {
    const held = JSON.parse(localStorage.getItem(GT_UNFOLD_KEY) || '{}') || {};
    const keys = held[thFaceKey('gets', TH.path, TH.meta && TH.meta.id)];
    if (Array.isArray(keys)) TH.unfolded = new Set(keys.map(String).filter((k) => !cards || cards[k]));
  } catch { /* a private window, or nothing kept */ }
}

function gtUnfoldKeep() {
  try {
    const held = JSON.parse(localStorage.getItem(GT_UNFOLD_KEY) || '{}') || {};
    const at = thFaceKey('gets', TH.path, TH.meta && TH.meta.id);
    if (TH.unfolded.size) held[at] = [...TH.unfolded];
    else delete held[at];
    localStorage.setItem(GT_UNFOLD_KEY, JSON.stringify(held));
  } catch { /* a private window keeps it for the page alone */ }
}

/* a card unfolded, or folded again, what stands below it making way and easing there */
function gtUnfold(key) {
  const v = TH.v;
  if (!v || TH.drag || TH.mode !== 'gets') return;
  if (TH.unfolded.has(key)) TH.unfolded.delete(key);
  else if (gtUnfoldable(key, v.cards[key])) TH.unfolded.add(key);
  else return;
  gtUnfoldKeep();
  const from = thSpots(v);
  thRender();
  thEase(from);
}

const gtCountText = (n, total) => t('themes.gets.count', { count: n, n: total });

/* After the canvas is drawn the PETs way, each card takes its kind and pseudonym over its words and
   its marks, its case's colour along its top edge and its badge (16 October), and each GET's badge
   its count of the cases in the study, "6 of 8", a GET under the minimum with a dashed outline and
   "Under the minimum of 3" in its tooltip. A sub-theme inside a GET carries its own count with no
   mark. */
function gtDress(v) {
  const parents = thParents(v);
  const minimum = TH.gets ? TH.gets.minimum : 0;
  const total = TH.gets ? TH.gets.total : 0;
  for (const [key, el] of Object.entries(TH.els.cards)) {
    const c = v.cards[key];
    if (!c) continue;
    for (const name of [...el.classList]) if (name.startsWith('case-')) el.classList.remove(name);
    // a thematic analysis project's code is every participant's, so it takes no one participant's colour (codes)
    const code = thTa() && c.kind === 'es';
    el.classList.add('gt-card', `gt-${c.kind || 'pet'}`);
    if (code) el.classList.add('gt-code'); else el.classList.remove('gt-code');
    if (!code) el.classList.add(`case-${gtLook(c.case).colour}`);
    el.innerHTML = gtCardHtml(v, key, c, parents);
    const from = gtFrom(v, key, c, parents);
    const why = parents[key] === undefined && !v.discarded.includes(key) && thWhy(v, key) ? t('themes.card.left_out', { why: thWhy(v, key) }) : '';
    el.title = [gtKicker(c), c.text, gtCardDesc(c), from, ...gtMarks(c), why].filter(Boolean).join('\n');
  }
  for (const g of v.groups) {
    const n = gtCount(v, g.id);
    const top = parents[g.id] === undefined;
    const under = top && n < minimum;
    const frame = TH.els.frames[g.id];
    if (frame && frame.firstElementChild) {
      const badge = frame.firstElementChild;
      badge.textContent = t('themes.gets.of', { count: n, total });
      badge.classList.toggle('under', under);
      badge.title = under ? t('themes.gets.under_min', { min: minimum }) : gtCountText(n, total);
      if (under) badge.removeAttribute('aria-hidden');
    }
    const label = TH.els.labels[g.id];
    if (!label) continue;
    const noted = thNoteOf(g);
    const counted = under ? t('themes.gets.count_under', { count: gtCountText(n, total), min: minimum }) : gtCountText(n, total);
      label.title = (thDescOf(g) ? `${thLabelShown(g.label)}\n${thDescOf(g)}\n\n` : '') + (noted ? t('themes.label.tip_noted', { count: counted, note: noted, unit: thUnit(v, g.id, parents) }) : t('themes.label.tip', { count: counted, unit: thUnit(v, g.id, parents) }));
  }
  // the panel's rows show which are on the canvas
  gtCasesDraw();
}

/* The counts on the status bar, the GETs, the cards placed in them, those not placed and those binned, a
   participant note never among them (see thStatusNumbers), and the bin's own count as on the PETs screen. */
function gtDrawCounts() {
  const v = TH.v;
  thStatusDraw();
  $('th-pile-count').textContent = String(v.discarded.length);
  $('th-pile-count').hidden = !v.discarded.length;
  $('th-discard').classList.toggle('has', v.discarded.length > 0);
  $('th-discard').setAttribute('aria-label', t('themes.gets.bin_label', { n: v.discarded.length }));
  if (TH.pileOpen) thPileList();
}

/* The foot of the board menu: Mark GETs complete, or Reopen GETs once marked. Marking is refused,
   saying which cases, unless every case of the study is in from its marked board and unchanged. */
function gtMenuFoot() {
  const at = TH.done ? whenOf(TH.done.at) : null;
  // Export, the GETs in print, the table, the trail, the full set or the canvas, after a hairline
  // of their own, named as the PETs screen's Export is, in a thematic analysis project in its words (tagaps)
  const exp = '<div class="row-menu-rule"></div>'
    + `<button type="button" class="ghost" tabindex="-1" data-gprint="table" title="${escAttr(t('themes.gets.export_tip'))}">${esc(t('themes.gets.export'))}</button>`;
  // a thematic analysis project's themes are not marked complete in its phase one (tadraw)
  if (thTa()) return exp;
  return exp + '<div class="row-menu-rule"></div>' + (TH.done
    ? `<button type="button" class="ghost" tabindex="-1" data-vop="pets-reopen" title="${escAttr(t(at.time ? (TH.done.name ? 'themes.gets.done_tip_time_name' : 'themes.gets.done_tip_time') : (TH.done.name ? 'themes.gets.done_tip_name' : 'themes.gets.done_tip'), { day: at.day, time: at.time, name: TH.done.name }))}">${esc(t('themes.gets.reopen'))}</button>`
    : `<button type="button" class="ghost" tabindex="-1" data-vop="pets-done" title="${escAttr(t('themes.gets.done_mark_tip'))}">${esc(t('themes.gets.done_mark'))}</button>`);
}

/* Mark GETs complete, or Reopen GETs: through the board op, never the autosave, the third level
   of confetti on marking, as for PETs. A refusal names the cases it waits on, in the menu. */
async function gtDone(mark) {
  if (!TH.live || !TH.meta) return;
  const was = !!TH.done;
  const data = await thBoardOp(mark ? 'complete' : 'reopen');
  if (!data) return;
  thTakeBoards(data);
  gtLoad(data);
  if (TH.vmenu) thVmenuDraw();
  if (mark && TH.done && !was) { confetti(3); say(t('themes.gets.marked_complete'), 2400); }
  else if (!mark && was) say(t('themes.gets.reopened'), 2400);
}

/* Add every sub-theme, in the board menu (item 193): a card for each sub-theme of the study that has
   no card on this board, a board made before sub-themes came in as cards of their own. The server
   places them as one pile in the nearest free spot clear of every card, label, frame and sticky
   note, and writes nothing, and they land here in no GET as one step of undo, which the autosave
   writes. None to add is one line, in the menu. A server from before it knows no such op, unknown_op, and
   the line asks for a restart. */

async function gtAddSubs() {
  if (!TH.live || TH.busy || !TH.meta || !thGets() || thRefuse('subs')) return;
  thTitleDone(true);
  thNoteDone(true);
  thViewEnd();
  const id = TH.meta.id;
  TH.busy = true;
  let data = null;
  try {
    await thFlush();
    if (TH.dirty) { thVsaid(t('themes.unsaved.added')); return; }
    data = await api('/api/gets-boards', { workbook: TH.path, op: 'subs', id });
  } catch (err) {
    thVsaid(needsRestart(err) || refusedAs(err, 'unknown_op') ? RESTART_LINE : err.message);
    return;
  } finally {
    TH.busy = false;
  }
  const v = TH.v;
  if (!data || !Array.isArray(data.added) || !v || !TH.live || !TH.meta || TH.meta.id !== id) return;
  const added = data.added.filter((c) => !v.cards[c.key]);
  if (!added.length) return;
  const keys = added.map((c) => c.key);
  const before = thSnap(v, new Set([...TH.removed, ...keys]));
  for (const c of added) v.cards[c.key] = Object.assign({}, c);
  TH.z = TH.z.filter((k) => !keys.includes(k)).concat(keys);
  thVmenu(false);
  thDone(before, t('themes.step.added_subs', { n: keys.length }));
  say(t('themes.gets.added_subs', { n: keys.length }), 3000);
}

/* ── Arrange by participant (Adam, 19 October, way 2 of the drawings) ── */

/* Arrange by participant, in the board menu and on a right click on empty canvas, a board-wide act beside
   each GET's Auto-arrange, from a tester's reflection on IPA in ATLAS.ti, where each participant's themes are
   set out in a row of their own before the GETs are made. Every PET and sub-theme card in no GET and not in
   the bin goes in a row for its participant, the rows in the Cases panel's order, each PET in the case's
   PET order with its sub-themes beside it after it, and each PET after the first a little further off, so
   it starts a group of its own. A second card of a PET follows its first. A sub-theme whose PET is in a GET
   or in the bin goes at its row's end, after every PET with its own. The rows go below everything
   that stays, at the left edge of it: every GET with all it holds, a statement's card, a participant note
   and a sticky note, none of which moves. One step of undo. */
const GT_BY_GAP = 14;     // between one card of a row and the next, as drawn
const GT_BY_PET = 14;     // and that much more before each PET after the first
const GT_BY_ROW = 40;     // between one participant's row and the next
const GT_BY_BELOW = 60;   // between what stays and the first row
const GT_BY_NONE = t('themes.gets.by_none');
const GT_BY_TIP = t('themes.gets.by_tip');

/* The cards Arrange by participant moves, laid out in their rows on `v` itself, in the order they now
   read, and none when every PET and sub-theme is in a GET or in the bin. `cases` is the Cases panel's,
   each with its name and its PETs, `size` a card's size by its key. */
function gtByParticipant(v, cases, size) {
  const parents = thParents(v);
  const moving = Object.keys(v.cards).filter((k) => {
    const c = v.cards[k];
    return (c.kind === 'pet' || c.kind === 'sub') && parents[k] === undefined && thOnCanvas(v, k);
  });
  if (!moving.length) return [];
  const going = new Set(moving);
  const layout = thLayout(v, size, null);
  const stays = [];
  for (const g of v.groups) {
    const l = layout[g.id];
    if (parents[g.id] === undefined && l) stays.push(l.body ? l.frame : l.label);
  }
  for (const k of Object.keys(v.cards)) if (!going.has(k) && parents[k] === undefined && thOnCanvas(v, k)) stays.push(thSolid(v, size, layout, k));
  for (const n of thStickies(v)) if (!n.in) stays.push(Object.assign({ x: n.x, y: n.y }, size(n.id)));
  let x0;
  let y;
  if (stays.length) {
    x0 = Math.min(...stays.map((b) => b.x));
    y = Math.max(...stays.map((b) => b.y + b.h)) + GT_BY_BELOW;
  } else {
    x0 = Math.min(...moving.map((k) => v.cards[k].x));
    y = Math.min(...moving.map((k) => v.cards[k].y));
  }
  const byCase = new Map();
  for (const k of moving) {
    const kase = gtSplit(k).kase;
    if (!byCase.has(kase)) byCase.set(kase, []);
    byCase.get(kase).push(k);
  }
  const names = cases.map((c) => c.case).filter((n) => byCase.has(n));
  for (const n of [...byCase.keys()].sort()) if (!names.includes(n)) names.push(n);
  const out = [];
  for (const name of names) {
    const entry = cases.find((c) => c.case === name);
    const pets = (entry && entry.pets) || [];
    const at = new Map(pets.map((p, i) => [p.id, i]));
    const byId = new Map(pets.map((p) => [p.id, p]));
    // the PET a card's PET or sub-theme stands under, the card's own when it is a PET
    const topOf = (pid) => {
      let id = pid;
      const seen = new Set();
      while (byId.has(id) && byId.get(id).parent !== null && byId.get(id).parent !== undefined && !seen.has(id)) {
        seen.add(id);
        id = byId.get(id).parent;
      }
      return id;
    };
    const groups = new Map();
    for (const k of byCase.get(name)) {
      const top = topOf(gtSplit(k).ident);
      if (!groups.has(top)) groups.set(top, []);
      groups.get(top).push(k);
    }
    const place = (id) => (at.has(id) ? at.get(id) : pets.length);
    const inGroup = (top) => (k) => {
      const s = gtSplit(k);
      return [s.ident === top ? 0 : 1, place(s.ident), s.copy ? Number(s.copy) || 1 : 0, k];
    };
    const cmp = (a, b) => { for (let i = 0; i < a.length; i += 1) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1; return 0; };
    // each PET with its own sub-themes in the case's PET order, and after them the sub-themes whose PET is in
    // a GET or in the bin, so a row never starts with a sub-theme or puts one after a PET not its own
    const headed = (top) => groups.get(top).some((k) => gtSplit(k).ident === top);
    const tops = [...groups.keys()].sort((a, b) => (headed(a) ? 0 : 1) - (headed(b) ? 0 : 1)
      || place(a) - place(b) || String(a).localeCompare(String(b)));
    let x = x0;
    let tall = 0;
    tops.forEach((top, i) => {
      if (i) x += GT_BY_PET;
      const order = groups.get(top).map((k) => [inGroup(top)(k), k]).sort((a, b) => cmp(a[0], b[0])).map((p) => p[1]);
      for (const k of order) {
        const s = size(k);
        v.cards[k].x = Math.round(x);
        v.cards[k].y = Math.round(y);
        x += s.w + GT_BY_GAP;
        tall = Math.max(tall, s.h);
        out.push(k);
      }
    });
    y += tall + GT_BY_ROW;
  }
  return out;
}

/* Arrange by participant done on the board on the canvas, one step of undo, what moved easing there */
function gtArrangeByParticipant() {
  if (!TH.live || TH.busy || !TH.v || !thGets() || thRefuse('arrange')) return;
  thVmenu(false);
  thKqClose();
  const v = TH.v;
  const before = thSnap(v, TH.removed);
  const from = thSpots(v);
  const moved = gtByParticipant(v, (TH.gets && TH.gets.cases) || [], thSize);
  if (!moved.length) { say(GT_BY_NONE, 4000); return; }
  thDone(before, t('themes.step.arranged_by_participant'), { from });
}

/* ── the Inspector, on the GETs screen ── */

/* a case's quotes by row, for a pick named by its sheet, row and place */
function gtPickText(entry, key) {
  const found = gtQuoteAt(entry, key);
  return found ? found.text : '';
}

const gtList = (items, none) => (items.length ? `<ul class="gt-list">${items.join('')}</ul>` : `<p class="th-qnone">${esc(none)}</p>`);

function gtLineHtml(line) {
  return `<li><span class="th-time">${esc(line.time || '')}</span>${thSheetTag(line.sheet)} <span class="gt-said">${esc(line.text)}</span></li>`;
}

/* The Inspector on a card or a label of the GETs canvas. A PET or a sub-theme shows its note, its
   sub-themes, its statements and its picks, a statement its sheet and timecode, its quotes and
   exploratory notes, its PET and that PET's GET, and a participant note his words in a box. A GET
   shows its count, the minimum when it is under it, its note, and who is in it. */
function gtPanelDraw(v, item, owner) {
  const parents = thParents(v);
  let html = '';
  if (item.kind === 'card') {
    const c = v.cards[item.id];
    const entry = gtCase(c.case) || { pets: [], lines: {} };
    const marks = gtMarks(c).map((m) => `<span class="gt-mark">${esc(m)}</span>`).join('');
    if (c.kind === 'es' && thTa()) {
      // a thematic analysis project's code (themesbuild)
      html = gtCodePanelHtml(v, item.id, owner);
    } else if (c.kind === 'pn') {
      const typed = TH.pnBox && TH.pnBox.key === item.id ? TH.pnBox.value : (c.text || '');
      html = (thLocked(v) ? `<p class="gt-read">${esc(c.text || '')}</p>`
        : `<textarea class="th-vedit gt-pn" id="th-pn-box" data-pn="${escAttr(item.id)}" rows="4" spellcheck="true" `
          + `placeholder="${escAttr(t('themes.gets.pn_placeholder', { who: c.who }))}" aria-label="${escAttr(t('themes.kind.pn'))}">${esc(typed)}</textarea>`)
        + thLeaveHtml(v, item.id, owner);
    } else if (c.kind === 'es') {
      const line = entry.lines[gtSplit(item.id).ident] || { quotes: [], notes: [] };
      const pet = c.pet ? (entry.pets || []).find((p) => p.id === c.pet) : null;
      const holder = pet ? Object.keys(v.cards).find((k) => gtBase(k) === `${c.case}/${pet.id}` && !v.discarded.includes(k)) : null;
      const get = holder ? gtTopOf(v, holder, parents) : null;
      // under a GET its quotes carry a tick each, which makes one the quote of its row
      const ticks = gtTickHtml(v, item.id, parents);
      // and a double-click on the statement opens it for editing in place, as on PETs (30 October)
      const edit = c.gone ? '' : ` data-edit="${escAttr(item.id)}" title="${escAttr(t('themes.inspector.edit_tip'))}"`;
      html = `<p class="th-panel-title"${edit}>${esc(c.text)}</p>`
        + `<p class="th-panel-meta"><span class="th-time">${esc(c.time || '')}</span>${thSheetTag(c.sheet)}${marks}</p>`
        + thLeftOutHtml(v, item.id, owner)
        + thLeaveHtml(v, item.id, owner)
        + `<dl class="gt-facts"><dt>${esc(t('themes.unit.pet'))}</dt><dd>${esc(pet ? pet.title : line.discarded ? t('themes.gets.binned') : t('themes.status.name_unplaced'))}</dd>`
        + `<dt>${esc(t('themes.unit.get'))}</dt><dd>${esc(get ? thLabelShown(get.label) : t('themes.status.name_unplaced'))}</dd></dl>`
        + (ticks || (`<h3 class="section-label">${esc(t('themes.quote'))}</h3>`
          + gtList(gtLineQuotes(line, gtSplit(item.id).ident).map((q) => `<li class="gt-quote">${esc(q.text)}</li>`), t('themes.inspector.no_quote'))))
        + `<h3 class="section-label">${esc(t('themes.gets.notes'))}</h3>`
        + gtList((line.notes || []).map((q) => `<li>${esc(q)}</li>`), t('themes.gets.no_notes'));
    } else {
      const pet = (entry.pets || []).find((p) => p.id === gtSplit(item.id).ident) || null;
      const n = Number(c.statements) || 0;
      html = `<p class="th-panel-title">${esc(c.text)}</p>`
        + `<p class="th-panel-meta">${c.gone ? '' : `<span>${esc(t('themes.count.statements', { n }))}</span>`}${marks}</p>`
        + thLeftOutHtml(v, item.id, owner)
        + thLeaveHtml(v, item.id, owner);
      if (pet) {
        const subs = (pet.subs || []).map((id) => (entry.pets || []).find((p) => p.id === id)).filter(Boolean);
        if (pet.note) html += `<h3 class="section-label">${esc(t('themes.kind.note'))}</h3><p class="gt-read">${esc(pet.note)}</p>`;
        // a PET's sub-themes, or the groups riding inside a sub-theme's card
        if (subs.length) html += `<h3 class="section-label">${esc(pet.parent ? t('themes.gets.groups') : t('themes.gets.subs'))}</h3>` + gtList(subs.map((s) => `<li>${esc(s.title)}</li>`), '');
        // under a GET its picks and its statements' quotes carry a tick each for the row's quote
        const ticks = gtTickHtml(v, item.id, parents);
        if (ticks) html += ticks;
        const stacks = gtStacked(entry.lines);
        html += `<h3 class="section-label">${esc(t('themes.gets.statements'))}</h3>`
          + gtList((pet.statements || []).filter((k) => entry.lines[k]).map((k) => gtLineHtml(entry.lines[k])
            + ((stacks[k] || []).length ? `<li class="gt-stacked"><span class="gt-said">${esc(t('themes.gets.stacked_under'))}</span><ul class="gt-list">`
              + `${stacks[k].map((x) => gtLineHtml(entry.lines[x])).join('')}</ul></li>` : '')), t('themes.gets.no_statements'));
        const picks = (pet.picks || []).map((k) => gtPickText(entry, k)).filter(Boolean);
        if (picks.length && !ticks) html += `<h3 class="section-label">${esc(t('themes.gets.picks'))}</h3>` + gtList(picks.map((q) => `<li class="gt-quote">${esc(q)}</li>`), '');
      }
    }
  } else if (thTa()) {
    // a thematic analysis project's theme or subtheme (themesbuild)
    html = gtThemePanelHtml(v, thGroup(v, item.id), owner);
  } else {
    const g = thGroup(v, item.id);
    const n = gtCount(v, g.id);
    const total = TH.gets ? TH.gets.total : 0;
    const minimum = TH.gets ? TH.gets.minimum : 0;
    const under = owner === undefined && n < minimum;
    const inside = gtInside();
    const there = new Set(thCardsUnder(v, g.id).map((k) => v.cards[k]).filter((c) => c && c.kind !== 'pn').map((c) => c.case));
    const rows = ((TH.gets && TH.gets.cases) || []).filter((c) => inside.has(c.case))
      .map((c) => `<li class="${there.has(c.case) ? '' : 'gt-none'}"><span>${esc(c.who)}</span>${there.has(c.case) ? '' : `<span class="gt-said">${esc(t('themes.gets.nothing_under'))}</span>`}</li>`);
    // a GET's audit trail opens from here, and from under its title in the board's Table view
    const trail = owner === undefined
      ? `<button type="button" class="ghost small gt-trail-go" tabindex="-1" data-gtrail="${escAttr(g.id)}">${esc(t('themes.gets.trail'))}</button>` : '';
    html = thDescHtml(v, g) + `<p class="kicker">${esc(owner !== undefined ? t('themes.kind.sub') : t('themes.unit.get'))}</p>`
      + `<p class="th-panel-meta"><span>${esc(gtCountText(n, total))}</span>${under ? `<span class="gt-mark">${esc(t('themes.gets.under_min', { min: minimum }))}</span>` : ''}</p>`
      + thArrangeHtml(g.id, trail) + thLeaveHtml(v, g.id, owner) + thNoteHtml(v, g)
      // three titles from the AI for a GET or a sub-theme, with the sparkles, and Undo puts the old back
      + thNamesHtml(item, { unit: owner !== undefined ? t('themes.unit.sub') : t('themes.unit.get') })
      + `<h3 class="section-label">${esc(t('themes.cases.head'))}</h3>` + gtList(rows, t('themes.gets.no_participant'));
  }
  const box = $('th-gnote');
  const held = TH.noting && box && document.activeElement === box
    ? { start: box.selectionStart, end: box.selectionEnd, top: box.scrollTop } : null;
  const descHeld = thDescHeld();
  TH.noteRedraw = true;
  $('th-panel-body').className = `th-panel-body gt-inspect${item.kind === 'group' ? ` ${thTintClass(thTints(v)[item.id])}` : ''}`;
  $('th-panel-body').innerHTML = html;
  TH.noteRedraw = false;
  const again = held ? $('th-gnote') : null;
  if (again) { again.focus(); again.setSelectionRange(held.start, held.end); again.scrollTop = held.top; }
  thDescRefocus(descHeld);
  thPlayerDraw();
}

/* A statement's words written from a card of this board taken into the Participants panel's copy of its
   participant, as the server took them into the file's, so the panel, an unfolded PET and the Inspector
   read them at once (30 October). */
function gtLineTook(key, text) {
  const split = gtSplit(key);
  const entry = gtCase(split.kase);
  const line = entry && entry.lines ? entry.lines[split.ident] : null;
  if (!line) return;
  line.text = text;
  gtCasesDraw();
}

/* A double-click on a card other than a statement's opens the Inspector on it, and on a participant
   note with its box ready to type in. A statement's opens its words for editing (see thCardEditOpen). */
function gtCardOpen(key) {
  if (!TH.live || !TH.v || !TH.v.cards[key]) return;
  thSelectOnly({ kind: 'card', id: key });
  TH.lastPick = { kind: 'card', id: key };
  thInspectorOpen({ kind: 'card', id: key });
  const box = $('th-pn-box');
  if (box && box.dataset.pn === key) { box.focus(); box.setSelectionRange(box.value.length, box.value.length); }
}

/* A participant note's words, kept with Enter or a click away, a new line with Shift + Enter, and
   let go with Esc. A change is one step of undo. */
function gtPnStart(box) {
  const key = box.dataset.pn;
  if (TH.pnBox && TH.pnBox.key === key) return;
  gtPnDone(true);
  if (!TH.live || !TH.v || !TH.v.cards[key] || thLocked(TH.v)) return;
  TH.pnBox = { key, value: box.value };
}

function gtPnDone(keep) {
  const ed = TH.pnBox;
  if (!ed) return;
  TH.pnBox = null;
  const box = $('th-pn-box');
  const text = box && box.dataset.pn === ed.key ? box.value : ed.value;
  const v = TH.v;
  const c = v && v.cards[ed.key];
  if (keep && c && !thLocked(v)) {
    const now = thStickyClean(text);
    if (now !== (c.text || '')) {
      const before = thSnap(v, TH.removed);
      c.text = now;
      thDone(before, t('themes.step.participant_note_written'));
      return;
    }
  }
  if (TH.panelOpen) thPanelDraw();
}

/* ── the menu: Place also under, with One GET per PET off ── */

/* A card's or a label's menu on the GETs canvas, the PETs one less Copy to board, and on a PET's or
   a sub-theme's card, with One GET per PET off in Settings, Place also under. */
function gtMenuItems(v, item, base) {
  const items = base.filter((it) => it.act !== 'copyto');
  const c = item.kind === 'card' ? v.cards[item.id] : null;
  // Unfold or Fold on a PET's or a sub-theme's card, after Inspect (21 October)
  if (c && gtUnfoldable(item.id, c)) {
    const at = items.findIndex((it) => it.act === 'inspect');
    items.splice(at + 1, 0, { label: TH.unfolded.has(item.id) ? t('themes.gets.fold') : t('themes.gets.unfold'), act: 'unfold' });
  }
  const many = TH.gets && TH.gets.settings && TH.gets.settings.one_per_pet === false;
  if (c && many && (c.kind === 'pet' || c.kind === 'sub') && !thLocked(v) && gtAlsoTargets(v, item.id).length) {
    const at = items.findIndex((it) => it.act === 'discard');
    items.splice(at < 0 ? items.length : at, 0, { label: t('themes.gets.also_menu'), act: 'also', rule: true });
    const after = items[at < 0 ? items.length - 1 : at + 1];
    if (after && after.act === 'discard') after.rule = false;
  }
  if (items.length && items[0].rule) items[0].rule = false;
  return items;
}

/* the GETs and sub-themes a PET's card can go under besides the ones a card of it is under */
function gtAlsoTargets(v, key) {
  const base = gtBase(key);
  const parents = thParents(v);
  const held = new Set(Object.keys(v.cards).filter((k) => gtBase(k) === base && !v.discarded.includes(k))
    .map((k) => parents[k]).filter(Boolean));
  return v.groups.filter((g) => !held.has(g.id));
}

function gtAlsoList() {
  const open = TH.menu;
  if (!open) return;
  const targets = gtAlsoTargets(TH.v, open.item.id);
  open.el.innerHTML = `<p class="th-cmenu-head">${esc(t('themes.gets.also_head'))}</p>`
    + targets.map((g) => `<button type="button" class="ghost small" role="menuitem" tabindex="-1" data-also="${escAttr(g.id)}"><span>${esc(thLabelShown(g.label))}</span></button>`).join('');
  const box = open.el.getBoundingClientRect();
  if (box.bottom > window.innerHeight - 8) open.el.style.top = `${Math.max(8, window.innerHeight - 8 - box.height)}px`;
}

/* A second card of a PET or a sub-theme under another GET, each card then naming the other. One
   step of undo. */
function gtPlaceAlso(key, gid) {
  const v = TH.v;
  const c = v.cards[key];
  if (!c || !thIsGroup(v, gid) || thRefuse('join')) return;
  const base = gtBase(key);
  let n = 2;
  while (v.cards[`${base}/${n}`]) n += 1;
  const fresh = `${base}/${n}`;
  const frame = TH.layout[gid] && (TH.layout[gid].frame || TH.layout[gid].label);
  const before = thSnap(v, new Set([...TH.removed, fresh]));
  v.cards[fresh] = Object.assign({}, c, { key: fresh, copy: String(n),
    x: frame ? Math.round(frame.x + TH_FRAME_X) : Math.round(c.x + 40), y: frame ? Math.round(frame.y + frame.h) : Math.round(c.y + 40) });
  thGroup(v, gid).members.push(fresh);
  TH.z = TH.z.concat([fresh]);
  TH.sel.cards.clear();
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  TH.sel.cards.add(fresh);
  TH.lastPick = { kind: 'card', id: fresh };
  thDone(before, t('themes.step.placed_under_get'), { settle: [fresh] });
}

/* ── the Cases panel ── */

/* ── the board's sidebar: Not placed and Set aside (Adam, 20 October, way A of the drawings) ──

   No bin. On the PETs board the Cases panel's place at the left of the canvas holds the participant's
   statements not on the board, Not placed, in interview order, each with its time, and under it, pinned to
   the panel's foot and folded until he opens it, Set aside, what the bin held. On the GETs board the Cases
   panel stays as it was and gains Set aside at its foot. A row is selected as the Table view's are, a click,
   Shift for a run and Cmd for one more, and the rows selected drag onto the canvas together: let go on empty
   canvas they lie there loose, placed but in no PET yet, and let go on a PET's title strip or in its body they
   go into it. Put all on the board puts every statement waiting on the canvas as one pile in the middle. A
   card dragged from the canvas onto Not placed waits there again, and onto Set aside is set aside. */
const TH_SIDE_KEY = 'idiograph-pets-side';
const TH_SIDE_FOLDS = 'idiograph-side-folds';

function thSideFoldsRead() {
  if (TH.sfold) return TH.sfold;
  TH.sfold = { wait: true, aside: false };
  try {
    const held = JSON.parse(localStorage.getItem(TH_SIDE_FOLDS) || '{}');
    if (held && typeof held === 'object') {
      if (typeof held.wait === 'boolean') TH.sfold.wait = held.wait;
      if (typeof held.aside === 'boolean') TH.sfold.aside = held.aside;
    }
  } catch { /* a private window, or nothing kept */ }
  return TH.sfold;
}

function thSideFold(sec, open) {
  const folds = thSideFoldsRead();
  folds[sec] = open === undefined ? !folds[sec] : !!open;
  try { localStorage.setItem(TH_SIDE_FOLDS, JSON.stringify(folds)); } catch { /* a private window */ }
  thListDraw();
}

/* the statements set aside, in interview order on PETs, and on GETs in the order they were set aside */
function thAsideKeys(v) {
  const keys = v.discarded.filter((key) => v.cards[key] && !v.cards[key].missing);
  return thWaits(v) ? keys.sort((a, b) => thInterviewCmp(v, a, b, TH.sheets)) : keys;
}

/* the rows a section shows, the search kept to what it finds */
function thSideKeys(sec) {
  const v = TH.v;
  if (!v) return [];
  const keys = sec === 'wait' ? thWaitingKeys(v, TH.sheets) : thAsideKeys(v);
  const find = String(TH.cfind || '').trim().toLowerCase();
  if (!find) return keys;
  return keys.filter((key) => thSideWords(v, key).some((t) => String(t || '').toLowerCase().includes(find)));
}

function thSideWords(v, key) {
  const c = v.cards[key] || {};
  if (TH.mode === 'gets') {
    const it = gtItemOf(v, key);
    return [it.title, it.text, c.who];
  }
  return [c.text, ...thStackOf(v, key).map((k) => (v.cards[k] || {}).text)];
}

function thSideRow(v, key, sec) {
  const c = v.cards[key] || {};
  const locked = thLocked(v);
  const held = TH.mode === 'gets' ? 0 : thStackOf(v, key).length;
  let lead;
  let words = c.text;
  if (TH.mode === 'gets') {
    const it = gtItemOf(v, key);
    words = it.kind === 'pet' || it.kind === 'sub' ? it.title : it.text;
    lead = `<span class="ts-lead">${gtBadgeHtml(it.kase)}</span>`;
  } else lead = `<span class="th-time ts-time">${esc(c.time || '')}</span>`;
  const why = sec === 'wait' && thWhy(v, key) ? `<span class="ts-why">${esc(thWhy(v, key))}</span>` : '';
  const chip = held ? `<span class="ts-stk">${esc(t('themes.stack.count', { n: held }))}</span>` : '';
  const act = locked ? ''
    : c.missing ? `<button type="button" class="ghost small btn-remove ts-act" tabindex="-1" data-tsremove="${escAttr(key)}">${esc(t('themes.pile.remove'))}</button>`
      : sec === 'aside' ? `<button type="button" class="ghost small ts-act" tabindex="-1" data-tsback="${escAttr(key)}" title="${escAttr(TH.mode === 'gets'
        ? t('themes.side.back_gets') : t('themes.menu.back_unplaced'))}">${esc(t('themes.pile.put_back'))}</button>` : '';
  return `<li class="ts-row${TH.ssel.has(key) ? ' sel' : ''}${c.missing ? ' missing' : ''}" data-tskey="${escAttr(key)}" data-tssec="${sec}">`
    + `${lead}<span class="ts-body"><span class="ts-text">${esc(words || '')}</span>${chip}${why}</span>${act}</li>`;
}

/* a section's head: its fold, its name and its count at the right */
function thSideHead(sec, name, n, open) {
  return `<div class="ts-head" data-tshead="${sec}"><button type="button" class="ts-fold${open ? ' open' : ''}" tabindex="-1" data-tsfold="${sec}" `
    + `aria-expanded="${open}">${GT_CHEV}<span class="ts-name">${esc(name)}</span></button><span class="ts-n">${n}</span></div>`;
}

/* Not placed's rows in interview order, a sheet after the first under its name, and a statement missing from
   the workbook last under its own */
function thWaitRows(v, keys) {
  const first = TH.sheets[0];
  let sheet = first;
  let gone = false;
  let html = '';
  for (const key of keys) {
    const c = v.cards[key];
    if (c.missing && !gone) { gone = true; html += `<li class="ts-sheet">${esc(t('themes.pile.missing'))}</li>`; }
    else if (!c.missing && c.sheet && c.sheet !== sheet) { sheet = c.sheet; html += `<li class="ts-sheet">${esc(c.sheet)}</li>`; }
    html += thSideRow(v, key, 'wait');
  }
  return html;
}

/* the panel drawn afresh: on PETs Not placed in the list, and on both screens Set aside at its foot */
function thListDraw() {
  thDoorCount();
  const v = TH.v;
  if (!v || !TH.casesOpen) return;
  const folds = thSideFoldsRead();
  for (const key of [...TH.ssel]) if (!thWaiting(v, key) && !v.discarded.includes(key)) TH.ssel.delete(key);
  if (TH.mode !== 'gets') {
    const list = $('gt-cases');
    const all = thWaitingKeys(v, TH.sheets);
    const keys = thSideKeys('wait');
    let html = thSideHead('wait', t('themes.status.name_unplaced'), all.length, folds.wait);
    if (folds.wait) {
      if (all.length && !thLocked(v)) {
        html += `<div class="ts-acts"><button type="button" class="ghost small ts-all" tabindex="-1" data-tsall `
          + `title="${escAttr(t('themes.side.all_tip'))}">${esc(t('themes.side.all'))}</button></div>`;
      }
      html += keys.length ? `<ul class="ts-list" data-tslist="wait">${thWaitRows(v, keys)}</ul>`
        : (TH.cfind.trim() && all.length ? `<p class="th-qnone">${esc(t('themes.side.no_match'))}</p>` : '');
    }
    const top = list.scrollTop;
    list.innerHTML = html;
    list.scrollTop = top;
  }
  thAsideDraw();
}

function thAsideDraw() {
  const box = $('th-aside');
  const v = TH.v;
  if (!box || !v) return;
  const folds = thSideFoldsRead();
  const all = thAsideKeys(v);
  const keys = thSideKeys('aside');
  let html = thSideHead('aside', t('themes.status.name_binned'), all.length, folds.aside);
  if (folds.aside && keys.length) html += `<ul class="ts-list" data-tslist="aside">${keys.map((k) => thSideRow(v, k, 'aside')).join('')}</ul>`;
  box.classList.toggle('open', !!folds.aside);
  const top = box.scrollTop;
  box.innerHTML = html;
  box.scrollTop = top;
}

/* the count of statements waiting on the sidebar's button, on PETs alone, none said while none waits, and its
   name and tooltip as the screen has it */
function thDoorCount() {
  const b = $('th-open-cases');
  if (!b) return;
  const pets = TH.mode !== 'gets';
  const name = pets ? t('themes.gets.statements') : TH.lpets ? t('themes.tp.head') : t('themes.cases.head');
  const word = b.querySelector('.bar-word');
  if (word) word.textContent = name;
  b.setAttribute('aria-label', name);
  b.title = TH.casesOpen ? t('themes.side.hide', { name }) : t('themes.side.show', { name });
  const n = pets && TH.v ? thWaitingKeys(TH.v).length : 0;
  let badge = b.querySelector('.th-door-n');
  if (!badge) {
    badge = document.createElement('span');
    badge.className = 'th-door-n';
    badge.setAttribute('aria-hidden', 'true');
    b.appendChild(badge);
  }
  badge.textContent = String(n);
  badge.hidden = !n;
  if (n) b.setAttribute('aria-label', t('themes.side.door_label', { name, n }));
  const head = $('th-cpanel') && $('th-cpanel').querySelector('.th-pname');
  if (head) head.textContent = name;
  const find = $('gt-find');
  if (find) {
    find.placeholder = pets ? t('themes.side.search_statements') : t('themes.side.search');
    find.setAttribute('aria-label', pets ? t('themes.side.search_statements_label') : TH.lpets ? t('themes.side.search_timepoints') : t('themes.side.search_participants'));
  }
}

/* the sidebar opened on a section, unfolded, from the status bar's count */
function thListOpenAt(sec) {
  if (!TH.live) return;
  thSideFoldsRead()[sec] = true;
  try { localStorage.setItem(TH_SIDE_FOLDS, JSON.stringify(TH.sfold)); } catch { /* a private window */ }
  if (!TH.casesOpen) gtCasesOpen(); else thListDraw();
}

/* rows lit for a moment where they landed, the list scrolled to the first, or a folded section's head lit */
function thSideFlash(keys, sec) {
  if (!TH.casesOpen) return;
  const scope = sec === 'aside' ? $('th-aside') : $('gt-cases');
  if (!scope) return;
  const rows = keys.map((k) => scope.querySelector(`.ts-row[data-tskey="${CSS.escape(k)}"]`)).filter(Boolean);
  const lit = rows.length ? rows : [scope.querySelector(`[data-tshead="${sec}"]`)].filter(Boolean);
  // the list scrolls to the first row, itself alone, never the page round it
  if (rows.length) {
    const r = rows[0].getBoundingClientRect();
    const box = scope.getBoundingClientRect();
    if (r.top < box.top) scope.scrollTop -= box.top - r.top + 8;
    else if (r.bottom > box.bottom) scope.scrollTop += r.bottom - box.bottom + 8;
  }
  for (const el of lit) {
    el.classList.remove('ts-lit');
    void el.offsetWidth;
    el.classList.add('ts-lit');
  }
}

/* Take out of PET, Backspace on a card: back to Not placed, at its own time in the order, one step of undo */
function thWaitDo(keys) {
  if (thRefuse('leave')) return false;
  const v = TH.v;
  const live = keys.filter((key) => thOnCanvas(v, key));
  if (!live.length) return false;
  const before = thSnap(v, TH.removed);
  const was = thLabelBoxes(TH.layout);
  thAck(live);
  const sent = thSendWaiting(v, live);
  for (const key of sent) TH.sel.cards.delete(key);
  thDone(before, t('themes.step.back_to_unplaced', { n: sent.length }), { was });
  thSideFlash(sent, 'wait');
  return true;
}

/* rows of the sidebar onto the canvas at the pointer: into the PET, sub-theme or group under it, or loose on
   empty canvas, several side by side. One step of undo */
function thSideDrop(keys, clientX, clientY, lean = 0) {
  const v = TH.v;
  if (!v || thLocked(v) || thRefuse('drag')) return;
  const live = keys.filter((k) => v.cards[k] && (thWaiting(v, k) || v.discarded.includes(k)));
  if (!live.length) return;
  const at = thToWorld(clientX, clientY);
  const hit = thTargetAt(clientX, clientY);
  const before = thSnap(v, TH.removed);
  // each where it was let go, and it lands as a card dropped on the canvas does (21 October)
  live.forEach((key, i) => {
    const spot = thPullSpot(i, live.length);
    thPutOn(v, key, at.x + spot.x, at.y + spot.y);
  });
  if (hit && hit.group && thIsGroup(v, hit.group)) thJoin(v, live, hit.group);
  thAck(live);
  TH.z = TH.z.filter((k) => !live.includes(k)).concat(live);
  TH.ssel.clear();
  TH.sel.cards = new Set(live);
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  TH.lastPick = { kind: 'card', id: live[live.length - 1] };
  thDone(before, t('themes.step.put_on_board', { n: live.length }),
    { settle: live, lifted: new Set(live), lean });
  thPanelFollow();
}

/* Put all on the board: every statement waiting, onto the canvas as one pile in the middle of what is in view,
   loose, in interview order. One step of undo */
function thSideAll() {
  const v = TH.v;
  if (!v || thLocked(v) || thRefuse('drag')) return;
  const keys = thWaitingKeys(v, TH.sheets).filter((k) => !v.cards[k].missing);
  if (!keys.length) return;
  const r = thStage().getBoundingClientRect();
  const mid = thToWorld(r.left + r.width / 2, r.top + r.height / 2);
  const cols = Math.max(1, Math.ceil(Math.sqrt(keys.length * 0.6)));
  const rows = Math.ceil(keys.length / cols);
  const w = TH_CARD.w + TH_MARGIN;
  const h = TH_CARD.h + TH_MARGIN;
  const before = thSnap(v, TH.removed);
  keys.forEach((key, i) => thPutOn(v, key, mid.x - (cols * w) / 2 + (i % cols) * w, mid.y - (rows * h) / 2 + Math.floor(i / cols) * h));
  thAck(keys);
  TH.z = TH.z.filter((k) => !keys.includes(k)).concat(keys);
  TH.ssel.clear();
  thDone(before, t('themes.step.put_all_on_board', { n: keys.length }), { settle: keys });
  thFit();
}

/* Put back from Set aside: to wait in Not placed, or on GETs onto the board in no GET */
function thSideBack(key) {
  if (TH.mode === 'gets') { thPutBack(key); return; }
  const v = TH.v;
  if (!v || !v.discarded.includes(key) || thRefuse('restore')) return;
  const before = thSnap(v, TH.removed);
  thAck([key]);
  thRestore(v, key, v.cards[key].x, v.cards[key].y);
  TH.ssel.delete(key);
  thDone(before, t('themes.step.put_back'));
  thSideFlash([key], 'wait');
}

/* a click on a row: it alone selected, Shift a run from the last clicked in that section, Cmd one more */
function thSideClick(key, sec, e) {
  if (TH.ssec !== sec) { TH.ssel.clear(); TH.ssec = sec; }
  if (e.shiftKey && TH.sanchor) {
    const keys = thSideKeys(sec);
    const a = keys.indexOf(TH.sanchor);
    const b = keys.indexOf(key);
    if (a >= 0 && b >= 0) {
      if (!MOD(e)) TH.ssel.clear();
      for (const k of keys.slice(Math.min(a, b), Math.max(a, b) + 1)) TH.ssel.add(k);
    }
  } else if (MOD(e)) {
    if (TH.ssel.has(key)) TH.ssel.delete(key); else TH.ssel.add(key);
    TH.sanchor = key;
  } else {
    TH.ssel = new Set([key]);
    TH.sanchor = key;
  }
  thListDraw();
  thStatusDraw();
}

/* Cmd + A in the sidebar: every row of the section clicked last */
function thSideSelectAll() {
  const sec = TH.ssec || 'wait';
  TH.ssel = new Set(thSideKeys(sec));
  thListDraw();
}

function thSPullDown(e) {
  const row = e.target.closest('.ts-row');
  if (!row || e.button !== 0 || !TH.live || TH.busy) return;
  TH.sideLast = true;
  if (e.target.closest('button')) return;
  e.preventDefault();
  TH.spull = { key: row.dataset.tskey, sec: row.dataset.tssec, x0: e.clientX, y0: e.clientY, ghost: null,
    shift: e.shiftKey, mod: MOD(e) };
}

function thSPullMove(e) {
  const p = TH.spull;
  if (!p) return;
  const v = TH.v;
  if (!p.ghost) {
    if (Math.hypot(e.clientX - p.x0, e.clientY - p.y0) < 4) return;
    if (thLocked(v) || thRefuse('drag')) { TH.spull = null; return; }
    // the rows selected go together when the one picked up is among them, and it alone otherwise
    p.keys = TH.ssel.has(p.key) && TH.ssec === p.sec ? thSideKeys(p.sec).filter((k) => TH.ssel.has(k)) : [p.key];
    // each row a card, laid out as the drop will lay them, the count on the one picked up
    const cards = p.keys.map((key, i) => {
      const c = v.cards[key] || {};
      const card = document.createElement('div');
      card.className = 'th-card ts-ghost';
      const words = TH.mode === 'gets' ? (() => { const it = gtItemOf(v, key); return it.title || it.text; })() : c.text;
      card.innerHTML = `<p class="th-text">${esc(words || '')}</p>${TH.mode === 'gets' ? '' : `<div class="th-foot"><span class="th-time">${esc(c.time || '')}</span></div>`}`
        + (i === 0 && p.keys.length > 1 ? `<span class="ts-ghost-n">${p.keys.length}</span>` : '');
      return card;
    });
    thPullLift(p, cards, e);
    for (const k of p.keys) {
      const el = document.querySelector(`#th-cpanel .ts-row[data-tskey="${CSS.escape(k)}"]`);
      if (el) el.classList.add('ts-lifted');
    }
  }
  thPullFollow(p, e);
  const hit = TH.face === 'table' ? null : thTargetAt(e.clientX, e.clientY);
  for (const el of Object.values(TH.els.frames)) el.classList.remove('target');
  if (hit && hit.group && TH.els.frames[hit.group]) TH.els.frames[hit.group].classList.add('target');
}

function thSPullEnd(e, cancel = false) {
  const p = TH.spull;
  if (!p) return;
  TH.spull = null;
  for (const el of Object.values(TH.els.frames || {})) el.classList.remove('target');
  for (const el of document.querySelectorAll('#th-cpanel .ts-lifted')) el.classList.remove('ts-lifted');
  if (!p.ghost) { if (!cancel) thSideClick(p.key, p.sec, e); return; }
  thPullGone(p);
  if (cancel || TH.face === 'table') return;
  const el = document.elementFromPoint(e.clientX, e.clientY);
  if (!el || !thStage().contains(el) || el.closest('.th-ui')) return;
  thSideDrop(p.keys, e.clientX, e.clientY, p.lean);
}

/* the sidebar a canvas drag is over, armed while a drag runs and lit where a drop would go */
function thSideArm(on, hit = null) {
  const panel = $('th-cpanel');
  if (!panel) return;
  panel.classList.toggle('armed', !!on && !panel.hidden);
  const list = $('gt-cases');
  const aside = $('th-aside');
  if (list) list.classList.toggle('over', !!(hit && hit.wait));
  if (aside) aside.classList.toggle('over', !!(hit && hit.discard));
}

function thSideBoot() {
  TH.ssel = new Set();
  const aside = $('th-aside');
  const list = $('gt-cases');
  for (const box of [list, aside]) {
    box.addEventListener('pointerdown', (e) => {
      if (TH.mode === 'gets' && box === list) return;
      if (e.target.closest('.ts-fold, .ts-all')) { e.preventDefault(); return; }
      thSPullDown(e);
    });
    box.addEventListener('click', (e) => {
      const fold = e.target.closest('[data-tsfold]');
      if (fold) { thSideFold(fold.dataset.tsfold); return; }
      if (e.target.closest('[data-tsall]')) { thSideAll(); return; }
      const back = e.target.closest('[data-tsback]');
      if (back) { thSideBack(back.dataset.tsback); return; }
      const gone = e.target.closest('[data-tsremove]');
      if (gone) thRemove(gone.dataset.tsremove);
    });
  }
  document.addEventListener('pointermove', (e) => { if (TH.spull) thSPullMove(e); });
  document.addEventListener('pointerup', (e) => { if (TH.spull) thSPullEnd(e); });
  // a press on the canvas makes Cmd + A the canvas's again
  thStage().addEventListener('pointerdown', () => { TH.sideLast = false; }, true);
  // Not placed and Set aside on the status bar open the sidebar on that section
  $('th-status-counts').addEventListener('click', (e) => {
    const stat = e.target.closest('[data-stat]');
    if (!stat) return;
    if (stat.dataset.stat === 'unplaced' && TH.mode !== 'gets') thListOpenAt('wait');
    else if (stat.dataset.stat === 'binned') thListOpenAt('aside');
  });
}

/* Select all (Cmd + A and the palette's button): every row of the sidebar's section when a row there was
   pressed last, and otherwise every statement on the canvas, or in the Table view every statement it lists */
function thSelectAll() {
  if (!TH.live || !TH.v) return;
  if (TH.sideLast && TH.casesOpen && TH.ssec) { thSideSelectAll(); return; }
  const v = TH.v;
  const table = TH.face === 'table';
  TH.sel.cards = new Set(Object.keys(v.cards).filter((k) => thOnCanvas(v, k) && (!table || !v.cards[k].missing)));
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  thDrawSel();
  thPanelFollow();
}

function gtCasesStored() {
  try { return localStorage.getItem(TH.mode === 'gets' ? GT_CASES_KEY : TH_SIDE_KEY) !== 'closed'; } catch { return true; }
}

function gtCasesKeep() {
  try { localStorage.setItem(TH.mode === 'gets' ? GT_CASES_KEY : TH_SIDE_KEY, TH.casesOpen ? 'open' : 'closed'); } catch { /* private window */ }
}

/* the panel at the left of the canvas: the Cases panel on GETs, and on PETs the statements' sidebar (20 October) */
function gtCasesOpen(keep = true) {
  if (!TH.live) return;
  TH.casesOpen = true;
  $('th-cpanel').hidden = false;
  gtDoorDraw();
  gtCasesDraw();
  if (keep) gtCasesKeep();
}

function gtCasesShut(keep = true) {
  TH.casesOpen = false;
  if ($('th-cpanel')) $('th-cpanel').hidden = true;
  gtDoorDraw();
  if (keep) gtCasesKeep();
}

function gtDoorDraw() {
  const b = $('th-open-cases');
  if (!b) return;
  b.classList.toggle('on', !!TH.casesOpen);
  b.setAttribute('aria-pressed', String(!!TH.casesOpen));
  b.title = TH.casesOpen ? t('themes.side.hide', { name: t('themes.cases.head') }) : t('themes.side.show', { name: t('themes.cases.head') });
  thDoorCount();
}

/* what one search matches, any word of a case's PETs, notes, statements, quotes and exploratory notes */
const gtHit = (find, ...texts) => !find || texts.some((t) => String(t || '').toLowerCase().includes(find));

/* where a statement stands on its case's board: placed, unplaced or discarded, the class, and its word,
   "not placed" for one on no PET, as the bar and the manual say it (17 October) */
const gtWhere = (line) => (line.discarded ? 'discarded' : line.pet ? 'placed' : 'unplaced');
const GT_WHERE_SAID = { placed: t('themes.gets.where_placed'), unplaced: t('themes.gets.where_unplaced'), discarded: t('themes.gets.where_aside') };

/* The folds of the Cases panel's rows, kept in the browser for each project as the panel's open state
   is (16 October): a case folded open by its name, a PET or a sub-theme by `<case>/<id>`, and a
   case's Not in a PET by `<case>/:none`. A search opens the rows that hold what it finds, and a
   chevron pressed during it turns that row the other way until the search changes. */
const GT_FOLDS_KEY = 'idiograph-gets-folds';
const gtNoneId = (name) => `${name}/:none`;
const GT_CHEV = '<svg class="gt-chev" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M3 4.6 6 7.6l3-3"/></svg>';

function gtFoldsRead() {
  TH.foldRoot = TH.root;
  TH.cfold = new Set();
  try {
    const held = JSON.parse(localStorage.getItem(GT_FOLDS_KEY) || '{}');
    if (held && Array.isArray(held[TH.root])) TH.cfold = new Set(held[TH.root].map(String));
  } catch { /* a private window, or nothing kept */ }
}

function gtFoldsKeep() {
  try {
    const held = JSON.parse(localStorage.getItem(GT_FOLDS_KEY) || '{}') || {};
    if (TH.cfold.size) held[TH.root] = [...TH.cfold];
    else delete held[TH.root];
    localStorage.setItem(GT_FOLDS_KEY, JSON.stringify(held));
  } catch { /* a private window */ }
}

/* a row folded open or shut from its chevron, a case's from its name */
function gtFold(id) {
  const into = TH.cfind.trim() ? TH.cflip : TH.cfold;
  if (into.has(id)) into.delete(id);
  else into.add(id);
  if (into === TH.cfold) gtFoldsKeep();
  gtCasesDraw();
}

/* A case's tree in the Cases panel (16 October): each PET with its own statements, then its
   sub-themes each with theirs, a statement under the PET or the sub-theme it sits in on its case's
   board, one in a sub-theme's own groups under that sub-theme, as its card carries them, and every
   statement in none, unplaced or discarded, under Not in a PET, last. */
function gtTree(c) {
  const pets = c.pets || [];
  const lines = c.lines || {};
  const byId = Object.fromEntries(pets.map((p) => [p.id, p]));
  const deep = (p, seen) => {
    if (!p || seen.has(p.id)) return [];
    seen.add(p.id);
    return [...(p.statements || []), ...(p.subs || []).flatMap((s) => deep(byId[s], seen))];
  };
  const placed = new Set();
  // a statement stacked under another on its case's board goes with its top, listed under it wherever the top
  // is (20 October: PET stacks did not come through to GETs, and showed under Not in a PET)
  const under = gtStacked(lines);
  for (const keys of Object.values(under)) for (const k of keys) placed.add(k);
  const tops = pets.filter((p) => p.parent === null || p.parent === undefined).map((p) => {
    const seen = new Set([p.id]);
    const subs = (p.subs || []).map((s) => byId[s]).filter((s) => s && s.id !== p.id)
      .map((s) => ({ p: s, lines: deep(s, seen).filter((k) => lines[k]) }));
    const own = (p.statements || []).filter((k) => lines[k]);
    for (const k of own.concat(...subs.map((s) => s.lines))) placed.add(k);
    return { p, own, subs };
  });
  return { tops, none: Object.keys(lines).filter((k) => !placed.has(k)), under };
}

/* each top's statements stacked under it on its case's board, by the top's line, in the order the case holds
   them, a statement whose top the case no longer has standing on its own */
function gtStacked(lines) {
  const out = {};
  for (const [k, l] of Object.entries(lines || {})) {
    if (l && l.stacked && lines[l.stacked] && l.stacked !== k) (out[l.stacked] = out[l.stacked] || []).push(k);
  }
  return out;
}

/* Every case of the study in case order, each folding open to a tree of its PETs, their sub-themes
   and their statements, and Not in a PET last, each level folding on its own, each statement marked
   placed, unplaced or discarded on its case's board, with one search over all of it that opens the
   rows holding what it finds. A case's name found shows all of it, and so does a PET's or a
   sub-theme's title found. Its row carries the swatch of its colour, and its menu Add participant
   note and Open beside. A row on the canvas already shows it
   there. */
function gtCasesDraw() {
  if (TH.mode !== 'gets') { thListDraw(); return; }
  thAsideDraw();
  const list = $('gt-cases');
  gtPtabsDraw();
  if (!list || !TH.gets || !TH.casesOpen) return;
  // a thematic analysis project's codes, each once, on the Codes tab (themesbuild)
  if (gtPtabsOn() && TH.ptab === 'codes') { gtCodesPanelDraw(list); return; }
  const v = TH.v;
  const find = TH.cfind.trim().toLowerCase();
  // in a thematic analysis project a row is placed while its code's card is on the board (codes)
  const on = (key) => !!(v && Object.keys(v.cards).some((k) => (gtBase(k) === key || (thTa() && gtCodeOf(key) && gtCodeOf(k) === gtCodeOf(key)))
    && !v.discarded.includes(k)));
  // a row folded open by his chevron, or during a search a row that holds what it finds, which a
  // chevron then turns the other way
  const open = (id, holds) => (find ? holds !== TH.cflip.has(id) : TH.cfold.has(id));
  let html = '';
  TH.gets.cases.forEach((c, i) => {
    const lines = c.lines || {};
    const tree = gtTree(c);
    const found = (k) => !!find && gtHit(find, lines[k].text, ...(lines[k].quotes || []), ...(lines[k].notes || []));
    const stacks = tree.under;
    // a top found by what is stacked under it, so a search reaches a stacked statement
    const foundOrStack = (k) => found(k) || (stacks[k] || []).some(found);
    const whole = !find || gtHit(find, c.who);
    const shown = (keys, all) => (all ? keys : keys.filter(foundOrStack));
    const tops = tree.tops.map((t) => {
      const self = whole || gtHit(find, t.p.title, t.p.note);
      const subs = t.subs.map((s) => {
        const mine = self || gtHit(find, s.p.title, s.p.note);
        return { s, lines: shown(s.lines, mine), mine, holds: s.lines.some(foundOrStack) };
      }).filter((x) => x.mine || x.lines.length);
      const own = shown(t.own, self);
      // a row found only in a stack under a top opens the PET that holds the top, as a row found in it does
      return { t, self, subs, own, holds: t.own.some(foundOrStack) || subs.some((x) => x.holds || (!self && x.mine)) };
    }).filter((x) => x.self || x.subs.length || x.own.length);
    const none = shown(tree.none, whole);
    if (find && !whole && !tops.length && !none.length) return;
    const caseOpen = open(c.case, true);
    const look = gtLook(c.case);
    const marks = [];
    if (!c.in) marks.push(c.reason ? t('themes.gets.out_why', { why: c.reason }) : t('themes.gets.out'));
    if (c.status === 'unread') marks.push(t('themes.gets.unread'));
    else if (c.missing) marks.push(GT_NOT_INTERVIEWED);
    // a thematic analysis project's participants come in with no PETs, which nothing marks (tadraw)
    else if (thTa()) marks.push();
    else if (c.none) marks.push(gtNoPets());
    else if (!c.complete) marks.push(gtNotComplete());
    if (c.status === 'changed') marks.push(GT_CHANGED);
    html += `<section class="gt-case${c.in ? '' : ' out'}${c.status === 'changed' ? ' changed' : ''}">`
      + `<div class="gt-chead"><button type="button" class="gt-fold${caseOpen ? ' open' : ''}" tabindex="-1" data-gfold="${i}" aria-expanded="${caseOpen}">`
      + `${GT_CHEV}${c.person ? personPic(Object.assign({}, c.person, { colour: look.colour }), 26) : ''}`
      + `<span class="pp-gwho"${c.person && c.person.portrait ? ` title="${escAttr(c.person.portrait)}"` : ''}><span class="gt-cname">${esc(c.who)}</span>`
      + `${c.person && c.person.label ? `<span class="pp-label pp-glabel">${esc(c.person.label)}</span>` : ''}</span></button>`
      + `<button type="button" class="gt-swatch case-${look.colour}" tabindex="-1" data-gcolour="${i}" aria-haspopup="menu" `
      + `title="${escAttr(t('themes.gets.colour_tip', { colour: GT_COLOURS[look.colour] }))}" aria-label="${escAttr(t('themes.gets.colour_label', { who: c.who, colour: GT_COLOURS[look.colour] }))}">${esc(look.badge)}</button>`
      + `<button type="button" class="row-menu-open gt-cmenu" tabindex="-1" data-gmenu="${i}" title="${escAttr(t('themes.gets.case_menu_tip'))}">&#8943;</button></div>`
      + (marks.length ? `<p class="gt-cmarks">${marks.map((m) => `<span>${esc(m)}</span>`).join('')}</p>` : '');
    if (caseOpen) {
      const row = (k, extra = '') => {
        const l = lines[k];
        return `<li class="gt-row gt-line${on(`${c.case}/es/${k}`) ? ' on' : ''}" data-gi="${i}" data-gkind="es" data-gid="${escAttr(k)}">`
          + `<span class="gt-rtext">${esc(l.text)}</span><span class="gt-rfoot"><span class="th-time">${esc(l.time || '')}</span>`
          + `${thSheetTag(l.sheet)}${thTa() ? '' : `<span class="gt-where ${gtWhere(l)}">${GT_WHERE_SAID[gtWhere(l)]}</span>`}${extra}</span></li>`;
      };
      // a top with statements stacked under it carries "3 stacked", as its card on PETs does, which opens
      // them under it, each a row of its own to drag
      const stmt = (k) => {
        const kids = stacks[k] || [];
        if (!kids.length) return row(k);
        const id = `${c.case}/stack/${k}`;
        const isOpen = open(id, kids.some(found));
        const chip = `<button type="button" class="gt-stk${isOpen ? ' open' : ''}" tabindex="-1" data-gtw="${escAttr(id)}" `
          + `aria-expanded="${isOpen}" title="${escAttr(isOpen ? t('themes.stack.again') : t('themes.stack.show'))}">${esc(t('themes.stack.count', { n: kids.length }))}</button>`;
        return row(k, chip) + (isOpen ? `<li class="gt-stack"><ul>${kids.map((x) => row(x)).join('')}</ul></li>` : '');
      };
      // a PET's or a sub-theme's row, its chevron at its left, its statements counted at its right
      const hold = (kind, p, isOpen, n, kids) => `<li class="gt-node"><div class="gt-row gt-hold${on(`${c.case}/${p.id}`) ? ' on' : ''}" `
        + `data-gi="${i}" data-gkind="${kind}" data-gid="${escAttr(p.id)}">`
        + `<button type="button" class="gt-tw${isOpen ? ' open' : ''}" tabindex="-1" data-gtw="${escAttr(`${c.case}/${p.id}`)}" `
        + `aria-expanded="${isOpen}" aria-label="${escAttr(p.title)}">${GT_CHEV}</button>`
        + `<span class="gt-rkind">${kind === 'sub' ? 'Sub-theme' : 'PET'}</span><span class="gt-rtext">${esc(p.title)}</span>`
        + `<span class="gt-rn">${n}</span></div>${isOpen && kids ? `<ul>${kids}</ul>` : ''}</li>`;
      // a case with no PETs says so once, in the line under its name, folded or open, where a second line
      // under it stood at the panel's left edge (17 October)
      let rows = tops.map((x) => {
        const subs = x.subs.map((y) => hold('sub', y.s.p, open(`${c.case}/${y.s.p.id}`, y.holds), y.s.lines.length,
          y.lines.map(stmt).join(''))).join('');
        const n = x.t.own.length + x.t.subs.reduce((sum, s) => sum + s.lines.length, 0);
        return hold('pet', x.t.p, open(`${c.case}/${x.t.p.id}`, x.holds), n, x.own.map(stmt).join('') + subs);
      }).join('');
      if (none.length) {
        const noneOpen = open(gtNoneId(c.case), none.some(foundOrStack));
        rows += `<li class="gt-node gt-nonenode"><button type="button" class="gt-none${noneOpen ? ' open' : ''}" tabindex="-1" `
          + `data-gtw="${escAttr(gtNoneId(c.case))}" aria-expanded="${noneOpen}">${GT_CHEV}<span class="gt-rtext">${esc(t('themes.gets.not_in'))}</span>`
          + `<span class="gt-rn">${tree.none.length}</span></button>${noneOpen ? `<ul>${none.map(stmt).join('')}</ul>` : ''}</li>`;
      }
      if (rows) html += `<ul class="gt-tree">${rows}</ul>`;
    }
    html += '</section>';
  });
  if (!html) html = `<p class="th-qnone">${esc(find ? t('themes.side.no_match') : t('themes.gets.no_cases'))}</p>`;
  const top = list.scrollTop;
  list.innerHTML = html;
  list.scrollTop = top;
}

/* The colour choice, from the swatch on a case's row (21 October, drawing 08): Default, the case's own
   colour in case order, named by its colour, "Default (Olive)", then the first eight of the palette, a
   whole row each, the one it has ticked, each row's swatch the case's badge in that colour as its cards
   would carry it, then More colours, which opens the 25 in a grid beside the menu, in the picker's order, its
   own ringed. A colour another participant has is faint, with whose it is, and struck through in the grid,
   and cannot be chosen, so colour and badge together always tell participants apart. A choice is applied at
   once and kept in the GETs file, and is not a step of undo, since it is no part of a board. */
function gtTakenColours(name) {
  const out = new Map();
  for (const c of (TH.gets && TH.gets.cases) || []) {
    if (c.case === name) continue;
    const n = gtLook(c.case).colour;
    if (!out.has(n)) out.set(n, c.who || c.case);
  }
  return out;
}

function gtColourMenu(i, clientX, clientY) {
  thMenuClose();
  const c = TH.gets && TH.gets.cases[i];
  if (!c) return;
  const look = gtLook(c.case);
  const taken = gtTakenColours(c.case);
  const tick = `<span class="th-dot-on" aria-hidden="true">${TH_TICK_ICON}</span>`;
  const row = (n, label, act, ticked) => {
    const whose = act !== 'default' && taken.has(n) ? taken.get(n) : '';
    return `<button type="button" class="ghost small" role="menuitemradio" aria-checked="${ticked}" tabindex="-1" `
      + `data-gpick="${act}"${whose ? ` disabled title="${escAttr(t('themes.gets.whose_colour', { who: whose }))}"` : ''}><span class="th-dot gt-cdot case-${n}" aria-hidden="true">${esc(look.badge)}</span>`
      + `<span>${esc(label)}</span>${whose ? `<span class="gt-whose">${esc(t('themes.gets.whose', { who: whose }))}</span>` : ''}${ticked ? tick : ''}</button>`;
  };
  const pop = document.createElement('div');
  pop.className = 'row-menu th-cmenu gt-colours';
  pop.setAttribute('role', 'menu');
  pop.setAttribute('aria-label', t('themes.gets.whose_colour', { who: c.who }));
  pop.innerHTML = `<p class="th-cmenu-head">${esc(t('themes.gets.whose_colour', { who: c.who }))}</p>${row(look.default, t('themes.gets.colour_default', { colour: GT_COLOURS[look.default] }), 'default', !look.chosen)}`
    + '<div class="row-menu-rule" role="separator"></div>'
    + GT_COLOURS.slice(0, GT_FIRST_COLOURS).map((name, n) => row(n, name, String(n), look.chosen && look.colour === n)).join('')
    + '<div class="row-menu-rule" role="separator"></div>'
    + '<button type="button" class="ghost small gt-more" role="menuitem" tabindex="-1" aria-haspopup="menu" aria-expanded="false" data-gmore="1">'
    + `<span>${esc(t('themes.gets.more_colours'))}</span><span class="th-mkey th-msub" aria-hidden="true">&#8250;</span></button>`;
  document.body.appendChild(pop);
  pop.style.left = `${Math.max(8, Math.min(clientX + 2, window.innerWidth - pop.offsetWidth - 8))}px`;
  pop.style.top = `${Math.max(8, Math.min(clientY + 4, window.innerHeight - pop.offsetHeight - 8))}px`;
  pop.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); });
  pop.addEventListener('click', (e) => {
    if (e.target.closest('[data-gmore]')) { gtMoreColours(c, look, taken); return; }
    const chosen = e.target.closest('[data-gpick]');
    if (!chosen || chosen.disabled) return;
    thMenuClose();
    gtColourSet(c.case, chosen.dataset.gpick === 'default' ? null : Number(chosen.dataset.gpick));
  });
  TH.menu = { el: pop, item: { kind: 'case', id: c.case }, targets: [] };
}

/* More colours: the 25 in a grid of five beside the menu, in the picker's order, each a disc of the colour
   with the case's badge, its own ringed, another participant's struck through and not choosable, its name
   and whose it is in its tooltip, and a key under them saying what the stroke means. */
function gtMoreColours(c, look, taken) {
  const open = TH.menu;
  if (!open) return;
  if (open.sub) { open.sub.remove(); open.sub = null; open.el.querySelector('[data-gmore]').setAttribute('aria-expanded', 'false'); return; }
  const sub = document.createElement('div');
  sub.className = 'row-menu th-cmenu gt-more-colours';
  sub.setAttribute('role', 'menu');
  sub.setAttribute('aria-label', t('themes.gets.more_colours'));
  const cell = (name, n) => {
    const whose = taken.get(n);
    const own = look.colour === n;
    const said = whose ? t('themes.gets.cell_whose', { colour: name, who: whose }) : own ? t('themes.gets.cell_own', { colour: name, who: c.who }) : name;
    return `<button type="button" class="gt-cell case-${n}${own ? ' on' : ''}${whose ? ' taken' : ''}" role="menuitemradio" `
      + `aria-checked="${own}" tabindex="-1" data-gpick="${n}" title="${escAttr(said)}" aria-label="${escAttr(said)}"${whose ? ' disabled' : ''}>`
      + `<span aria-hidden="true">${whose ? '' : esc(look.badge)}</span></button>`;
  };
  sub.innerHTML = `<p class="th-cmenu-head">${esc(t('themes.gets.more_colours'))}</p>`
    + `<div class="gt-cells" style="--gt-cols: ${GT_MORE_COLUMNS}">${GT_COLOURS.map(cell).join('')}</div>`
    + (taken.size ? `<p class="gt-cells-key"><span class="gt-cell taken gt-key-cell" aria-hidden="true"></span>${esc(t('themes.gets.another'))}</p>` : '');
  document.body.appendChild(sub);
  open.sub = sub;
  open.el.querySelector('[data-gmore]').setAttribute('aria-expanded', 'true');
  const menu = open.el.getBoundingClientRect();
  // a clear gap from the menu, so the grid reads as its own panel beside it
  const right = menu.right + 12 + sub.offsetWidth <= window.innerWidth - 8;
  sub.style.left = `${right ? menu.right + 12 : Math.max(8, menu.left - 12 - sub.offsetWidth)}px`;
  sub.style.top = `${Math.max(8, Math.min(menu.top, window.innerHeight - sub.offsetHeight - 8))}px`;
  sub.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); });
  sub.addEventListener('click', (e) => {
    const chosen = e.target.closest('[data-gpick]');
    if (!chosen || chosen.disabled) return;
    thMenuClose();
    gtColourSet(c.case, Number(chosen.dataset.gpick));
  });
}

/* A colour chosen, or Default, written at once through the server after anything still to save, the
   cards, the panel and the table drawn again in it. The boards are as the file holds them, so the
   page knows them as they are and says nothing of a change from elsewhere. */
async function gtColourSet(name, colour) {
  if (!TH.live || !thGets()) return;
  let data;
  try {
    await thFlush();
    if (TH.dirty) { say(t('themes.unsaved.colour'), 6000); return; }
    data = await api('/api/gets-cases', { workbook: TH.path, op: 'colour', case: name, colour });
  } catch (err) {
    // a server from before the colours takes Take the changes alone and refuses any other op, unknown_op
    const old = needsRestart(err) || refusedAs(err, 'unknown_op');
    say(old ? RESTART_LINE : err.message, 8000);
    return;
  }
  if (!TH.live || !thGets()) return;
  // a case taken in on the way lands on every board, so the next save carries the version this wrote
  if (data.version && data.version.v && TH.meta && data.version.id === TH.meta.id) TH.meta.v = data.version.v;
  delete data.rows;
  gtLoad(data);
  if (Array.isArray(data.versions)) thKnow(data.versions);
  thRender();
  thTableDraw();
}

/* A case's menu in the Cases panel: Add participant note and Open beside, a case's changes coming in by
   themselves since 20 October (see gtTakeAll). On a
   case's name in a GET of the GET table, `gid`, the note added goes under that GET (20 October). */
function gtCaseMenu(i, clientX, clientY, gid = null) {
  thMenuClose();
  const c = TH.gets && TH.gets.cases[i];
  if (!c) return;
  const items = [{ label: t('themes.gets.add_pn'), act: 'pn' }];
  // its board beside the GET canvas, read-only
  if (c.path) items.push({ label: t('themes.gets.beside'), act: 'beside' });
  const pop = document.createElement('div');
  pop.className = 'row-menu th-cmenu';
  pop.setAttribute('role', 'menu');
  pop.innerHTML = items.map((it, k) => `<button type="button" class="ghost small" role="menuitem" tabindex="-1" data-gact="${k}"><span>${esc(it.label)}</span></button>`).join('');
  document.body.appendChild(pop);
  pop.style.left = `${Math.max(8, Math.min(clientX + 2, window.innerWidth - pop.offsetWidth - 8))}px`;
  pop.style.top = `${Math.min(clientY + 4, window.innerHeight - pop.offsetHeight - 8)}px`;
  pop.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); });
  pop.addEventListener('click', (e) => {
    const chosen = e.target.closest('[data-gact]');
    if (!chosen) return;
    const it = items[Number(chosen.dataset.gact)];
    thMenuClose();
    if (it.act === 'pn') gtNoteNew(c, gid);
    else if (it.act === 'beside') gtBesideOpen(c);
  });
  TH.menu = { el: pop, item: { kind: 'case', id: c.case }, targets: [] };
}

/* Add participant note: a card of his words on the canvas, in the middle of what is in view, the
   Inspector open on it with its box ready. It is never counted. From a case's name in a GET of the GET
   table, `gid`, it goes under that GET, in that case's row. */
function gtNoteNew(c, gid = null) {
  if (!TH.live || TH.busy || thRefuse('note')) return;
  const v = TH.v;
  let n = 1;
  while (v.cards[`${c.case}/pn/${n}`]) n += 1;
  const key = `${c.case}/pn/${n}`;
  const r = thStage().getBoundingClientRect();
  const mid = thToWorld(r.left + r.width / 2, r.top + r.height / 2);
  const before = thSnap(v, new Set([...TH.removed, key]));
  v.cards[key] = { key, kind: 'pn', case: c.case, who: c.who, text: '', time: '', sheet: '',
    x: Math.round(mid.x - TH_CARD.w / 2), y: Math.round(mid.y - TH_CARD.h / 2), open: false, gone: false };
  // never the PETs' mark: the note is his, not the case's
  TH.z = TH.z.concat([key]);
  if (gid && thIsGroup(v, gid)) {
    const at = TH.layout && TH.layout[gid];
    if (at && at.body) { v.cards[key].x = Math.round(at.body.x); v.cards[key].y = Math.round(at.body.y + at.body.h + TH_MARGIN); }
    thJoin(v, [key], gid);
  }
  thDone(before, t('themes.step.participant_note_added'), { settle: [key] });
  gtCardOpen(key);
}

/* A case's changes taken into the GETs by themselves (Adam, 20 October, from a tester's feedback: "just take the
   changes automatically"), on the GETs screen's open, when a window of this app changed the case's PETs while
   it was open, and from Update on Changes made elsewhere for a change from outside the app. The server keeps
   each GET board's place for every PET by id, then by title, brings new PETs in unplaced and leaves a PET
   gone from the case where it is, marked, each board keeping a revision first, "Before Mabel's
   changes came in", its line in History. On the canvas it is one step of undo, the board before and after. */
async function gtTakeAll(names) {
  // the stamp names them, read afresh, so the page's own copy of the cases, which a save does not bring up to
  // date, is not asked
  const list = [...new Set(names || [])].filter((n) => !!gtCase(n));
  if (!list.length || !TH.live || TH.busy || TH.viewing || !thGets() || !TH.meta) return false;
  const path = TH.path;
  const id = TH.meta.id;
  TH.busy = true;
  TH.taking = true;
  let data = null;
  const taken = [];
  try {
    await thFlush();
    if (TH.dirty) return false;
    const before = thSnap(TH.v, TH.removed);
    for (const name of list) {
      try {
        data = await api('/api/gets-cases', { workbook: path, op: 'take', case: name });
        taken.push(name);
      } catch (err) {
        say(needsRestart(err) ? RESTART_LINE : err.message, 8000);
        break;
      }
    }
    if (!data || TH.path !== path || !thGets()) return false;
    TH.busy = false;
    thLoad(data, { fit: false });
    if (TH.meta && TH.meta.id === id && TH.v) {
      const after = thSnap(TH.v, TH.removed);
      // a card the take brought in goes on undo, and one it renamed comes back on redo
      before.removed = [...new Set([...before.removed, ...Object.keys(after.cards).filter((k) => !(k in before.cards))])];
      after.removed = [...new Set([...after.removed, ...Object.keys(before.cards).filter((k) => !(k in after.cards))])];
      TH.undo.push({ before, after, what: gtTookSaid(taken) });
      if (TH.undo.length > TH_UNDO_DEPTH) TH.undo.shift();
      TH.redo.length = 0;
    }
    say(gtTookSaid(taken), 4000);
    // a notice of the same cases' changes, raised while they came in, is answered
    const o = TH.outside;
    if (o && !o.board && (o.cases || []).every((n) => taken.includes(n))) thOutside(null);
    return true;
  } finally {
    TH.busy = false;
    TH.taking = false;
  }
}

/* what the canvas says once they are in, "Brought in the changes to Mabel's PETs." */
function gtTookSaid(names) {
  const who = names.map((n) => (gtCase(n) || { who: n }).who);
  const said = tList(who);
  return t('themes.gets.took', { names: said });
}

/* ── a row of the Cases panel dragged onto the canvas ── */

/* The card a row of the panel makes: its kind and case, its words, a PET's statements counted and
   a statement's timecode, sheet and PET, from the case's copy. */
function gtCardFrom(entry, kind, ident) {
  const base = { case: entry.case, who: entry.who, open: !entry.complete && !entry.none, gone: false, time: '', sheet: '' };
  if (kind === 'es') {
    const line = (entry.lines || {})[ident] || {};
    // in a thematic analysis project a row whose code is on the board stands for that card (codes)
    const own = `${entry.case}/es/${ident}`;
    const held = thTa() ? gtCodeCard(TH.v, gtCodeOf(own)) : null;
    return Object.assign(base, { key: held || own, kind: 'es', text: line.text || '', time: line.time || '',
      sheet: line.sheet || '', seconds: line.seconds, pet: line.pet || null });
  }
  const byId = Object.fromEntries((entry.pets || []).map((p) => [p.id, p]));
  const p = byId[ident] || { title: '', statements: [], subs: [] };
  let n = 0;
  const stack = [ident];
  const seen = new Set();
  while (stack.length) {
    const at = stack.pop();
    if (seen.has(at) || !byId[at]) continue;
    seen.add(at);
    n += (byId[at].statements || []).length;
    stack.push(...(byId[at].subs || []));
  }
  return Object.assign(base, { key: `${entry.case}/${ident}`, kind: p.parent === null || p.parent === undefined ? 'pet' : 'sub',
    text: p.title, pet: ident, statements: n });
}

function gtPullDown(e) {
  const row = e.target.closest('.gt-row');
  if (!row || e.button !== 0 || !TH.live || TH.busy) return;
  e.preventDefault();
  TH.pull = { i: Number(row.dataset.gi), kind: row.dataset.gkind, ident: row.dataset.gid, x0: e.clientX, y0: e.clientY, ghost: null };
}

function gtPullMove(e) {
  const p = TH.pull;
  if (!p) return;
  if (!p.ghost) {
    if (Math.hypot(e.clientX - p.x0, e.clientY - p.y0) < 4) return;
    if (thRefuse('drag')) { TH.pull = null; return; }
    const entry = TH.gets && TH.gets.cases[p.i];
    if (!entry) { TH.pull = null; return; }
    const c = gtCardFrom(entry, p.kind, p.ident);
    const card = document.createElement('div');
    card.className = `th-card gt-card gt-${c.kind} gt-ghost case-${gtLook(c.case).colour}`;
    card.innerHTML = `<p class="gt-kicker">${gtBadgeHtml(c.case)}<span class="gt-ktext">${esc(gtKicker(c))}</span></p><p class="th-text">${esc(c.text)}</p>`;
    thPullLift(p, [card], e);
    p.card = c;
  }
  thPullFollow(p, e);
  // over the GET table, the GET or the sub-theme it would go under lit, as a frame is on the canvas
  if (TH.face === 'table') { gtTableIntoShow(gtTableTargetAt(e.clientX, e.clientY)); return; }
  const hit = thTargetAt(e.clientX, e.clientY);
  thHover(null);
  for (const el of Object.values(TH.els.frames)) el.classList.remove('target');
  if (hit && hit.group && TH.els.frames[hit.group]) TH.els.frames[hit.group].classList.add('target');
}

function gtPullUp(e) {
  const p = TH.pull;
  if (!p) return;
  TH.pull = null;
  for (const el of Object.values(TH.els.frames)) el.classList.remove('target');
  if (!p.ghost) { gtRowClick(p); return; }
  thPullGone(p);
  if (TH.face === 'table') {
    gtTableIntoShow(null);
    gtPullTableDrop(p.card, gtTableTargetAt(e.clientX, e.clientY));
    return;
  }
  const el = document.elementFromPoint(e.clientX, e.clientY);
  if (!el || !thStage().contains(el) || el.closest('.th-ui')) return;
  gtPullDrop(p.card, e.clientX, e.clientY, p.lean);
}

/* A row let go on the canvas: its card comes in where it was let go, or the one there already moves
   there, out of the bin when it was in it, and it joins the GET or the sub-theme under the pointer.
   One step of undo. */
function gtPullDrop(card, clientX, clientY, lean = 0) {
  const v = TH.v;
  if (!v || thLocked(v)) return;
  const key = card.key;
  const here = !!v.cards[key];
  const at = thToWorld(clientX, clientY);
  const hit = thTargetAt(clientX, clientY);
  const before = thSnap(v, here ? TH.removed : new Set([...TH.removed, key]));
  if (!here) v.cards[key] = Object.assign({}, card);
  const c = v.cards[key];
  if (v.discarded.includes(key)) v.discarded = v.discarded.filter((k) => k !== key);
  // where it was let go, and it lands as a card dropped on the canvas does (21 October)
  const spot = thPullSpot(0, 1);
  c.x = Math.round(at.x + spot.x);
  c.y = Math.round(at.y + spot.y);
  if (hit && hit.group && thIsGroup(v, hit.group)) thJoin(v, [key], hit.group);
  TH.z = TH.z.filter((k) => k !== key).concat([key]);
  TH.sel.cards.clear();
  TH.sel.groups.clear();
  TH.sel.stickies.clear();
  TH.sel.cards.add(key);
  TH.lastPick = { kind: 'card', id: key };
  thDone(before, here ? t('themes.step.moved_from_panel') : t('themes.step.brought_in'),
    { settle: [key], lifted: new Set([key]), lean });
  thPanelFollow();
}

/* Where a row of the Cases panel let go over the GET table goes (20 October): under the GET or the GET
   sub-theme whose section the pointer is in, its title strip or the rows it holds, the innermost, or into
   Not placed over that list. Null anywhere else, the bin among them. */
function gtTableTargetAt(x, y) {
  const box = $('th-table');
  const el = box && document.elementFromPoint(x, y);
  if (!el || !box.contains(el)) return null;
  const sec = el.closest('section[data-tkind="label"]');
  if (sec && thIsGroup(TH.v, sec.dataset.trow)) return { gid: sec.dataset.trow, el: sec };
  const loose = el.closest('.tb-rest');
  if (loose && !loose.classList.contains('tb-bin')) return { gid: null, el: loose };
  return null;
}

/* the place a Cases panel row would go lit in the table, and the last one put out */
function gtTableIntoShow(target) {
  const box = $('th-table');
  if (!box) return;
  for (const el of box.querySelectorAll('.tb-pullinto')) if (!target || el !== target.el) el.classList.remove('tb-pullinto');
  if (target) target.el.classList.add('tb-pullinto');
}

/* A row of the Cases panel let go on the GET table, as a drop on the canvas takes it: its card comes in, or
   the one there already moves, out of the bin when it was in it, under the GET or sub-theme let go on, or
   into Not placed, coming in under what that GET holds on the canvas. One step of undo. */
function gtPullTableDrop(card, target) {
  const v = TH.v;
  if (!v || thLocked(v) || !target) return;
  const key = card.key;
  const here = !!v.cards[key];
  const binned = v.discarded.includes(key);
  const parents = thParents(v);
  const now = parents[key];
  if (here && !binned && (target.gid ? now === target.gid : now === undefined)) {
    thSelectOnly({ kind: 'card', id: key });
    TH.lastPick = { kind: 'card', id: key };
    thTableDraw();
    thPanelFollow();
    return;
  }
  const before = thSnap(v, here ? TH.removed : new Set([...TH.removed, key]));
  if (!here) {
    const at = thEmptyAt(v, null);
    v.cards[key] = Object.assign({}, card, { x: Math.round(at.x), y: Math.round(at.y) });
  }
  if (binned) v.discarded = v.discarded.filter((k) => k !== key);
  if (target.gid) thTableJoin(v, [key], target.gid);
  else if (now !== undefined) thLeave(v, key);
  TH.z = TH.z.filter((k) => k !== key).concat([key]);
  thSelectOnly({ kind: 'card', id: key });
  TH.lastPick = { kind: 'card', id: key };
  thDone(before, here ? t('themes.step.moved_from_panel') : t('themes.step.brought_in'), { settle: [key] });
  thPanelFollow();
}

/* A click on a row shows its card, and a second click on the same statement's row soon after opens
   its passage on Experiential statements, as a double-click on its card does, its card on the board
   or not, the way back returning to this board (16 October). */
function gtRowClick(p) {
  const entry = TH.gets && TH.gets.cases[p.i];
  const now = Date.now();
  const last = TH.rowClick;
  const key = entry && p.kind === 'es' ? `${entry.case}/es/${p.ident}` : null;
  TH.rowClick = key ? { key, at: now } : null;
  if (key && last && last.key === key && now - last.at < 450) {
    TH.rowClick = null;
    thToPassage(key);
    return;
  }
  gtRowShow(p);
}

/* A click on a row: its card on the canvas selected and in view, when it is there. */
function gtRowShow(p) {
  const entry = TH.gets && TH.gets.cases[p.i];
  const v = TH.v;
  if (!entry || !v) return;
  const want = p.kind === 'es' ? `${entry.case}/es/${p.ident}` : `${entry.case}/${p.ident}`;
  const key = Object.keys(v.cards).find((k) => gtBase(k) === want && !v.discarded.includes(k));
  if (!key) return;
  thSelectOnly({ kind: 'card', id: key });
  TH.lastPick = { kind: 'card', id: key };
  thPanelFollow();
  const s = thSize(key);
  thFitTo({ x: v.cards[key].x, y: v.cards[key].y, w: s.w, h: s.h });
}

/* ── the GET table ── */

/* The GET table, the board's Table view on the GETs screen: each GET in canvas order with its note and its
   count, then a row for every case of the study in case order, what of the case sits under it, its
   quote and his note for the row, kept in the board's `rows`. The quote starts as the first
   pick of the participant's highest PET there, and a tick in the Inspector changes it. */

const GT_NOTHING = t('themes.gets.nothing_under');
/* a participant with no PETs says so in the one plain line of a row with nothing, in place of the mark
   beside the name and the line under it (17 October, after the screenshot check), as gets.py's
   NOTHING_NO_PETS says it in the trail and on paper */
const GT_NOTHING_NO_PETS = t('themes.gets.nothing_no_pets');
const GT_NOT_FROM = t('themes.gets.not_from');

/* a quote's key, `<sheet>:<row>:<place>`, read as the server's split_card_key reads it */
function gtQkey(qkey) {
  const parts = String(qkey || '').split(':');
  const at = Number(parts.pop());
  const row = Number(parts.pop());
  return { sheet: parts.join(':'), row, at };
}

/* A row's quotes as a statement's copy keeps them, by place, each with its key, sheet, row and
   timecode, an empty place or "(no quote)" left out. With `own`, the statement's key, its own
   quote alone, the one at its place (item 198). */
const gtNoQuote = (text) => !String(text || '').trim() || String(text).trim().toLowerCase() === '(no quote)';
const gtLineQuotes = (line, own) => ((line && line.quotes) || []).map((text, i) => ({
  key: `${line.sheet}:${line.row}:${i}`, text, sheet: line.sheet || '', row: line.row, time: line.time || '', seconds: line.seconds }))
  .filter((q, i) => !gtNoQuote(q.text) && (own === undefined || i === gtQkey(own).at));

/* a quote of a case's copy by its key, or null when the copy no longer holds it */
function gtQuoteAt(entry, qkey) {
  const k = gtQkey(qkey);
  if (!entry || !Number.isFinite(k.row) || !Number.isFinite(k.at)) return null;
  for (const line of Object.values(entry.lines || {})) {
    if (line.sheet !== k.sheet || line.row !== k.row) continue;
    const found = gtLineQuotes(line).find((q) => q.key === String(qkey));
    if (found) return found;
  }
  return null;
}

/* a PET's statements at any depth, its own first, then each sub-theme's */
function gtPetLines(entry, pid) {
  const pets = Object.fromEntries(((entry && entry.pets) || []).map((p) => [p.id, p]));
  const out = [];
  const seen = new Set();
  const walk = (at) => {
    if (seen.has(at) || !pets[at]) return;
    seen.add(at);
    for (const k of pets[at].statements || []) if (!out.includes(k)) out.push(k);
    for (const s of pets[at].subs || []) walk(s);
  };
  walk(pid);
  return out;
}

/* labels in the order the canvas reads them, tops within a card's height of the first in a row
   sharing it, as the server's canvas_order reads them */
function gtCanvasOrder(groups) {
  const rest = groups.map((g) => ({ id: g.id, x: g.x, y: g.y })).sort((a, b) => a.y - b.y || a.x - b.x);
  const out = [];
  while (rest.length) {
    const top = rest[0].y;
    const row = rest.filter((s) => s.y - top < TH_CARD.h).sort((a, b) => a.x - b.x || a.y - b.y);
    for (const s of row) { out.push(s.id); rest.splice(rest.indexOf(s), 1); }
  }
  return out;
}

/* The cards under a GET in the order the canvas reads them, higher first, at any depth, a
   sub-theme's where its frame's top sits, each with the sub-themes between it and the GET. */
function gtItems(v, gid, layout = TH.layout || {}) {
  const out = [];
  const walk = (at, within, seen) => {
    for (const m of thThemeOrder(v, at, layout)) {
      if (thIsGroup(v, m)) {
        if (!seen.has(m)) walk(m, within.concat([thGroup(v, m).label]), new Set([...seen, m]));
      } else if (thOnCanvas(v, m)) out.push({ key: m, within });
    }
  };
  walk(gid, [], new Set([gid]));
  return out;
}

/* One card under a GET as the table sets it out, as the server's item_of does: a PET or a
   sub-theme with its title, statements and picks, a statement with its sheet, timecode, quotes
   and exploratory notes, or a participant note, his words. */
function gtItemOf(v, key, within = []) {
  const c = v.cards[key] || {};
  const k = gtSplit(key);
  const entry = gtCase(k.kase) || { pets: [], lines: {} };
  const base = { key, kase: k.kase, within, gone: false };
  if (k.kind === 'pn') return Object.assign(base, { kind: 'pn', text: c.text || '' });
  if (k.kind === 'es') {
    const line = (entry.lines || {})[k.ident];
    if (!line) return Object.assign(base, { kind: 'es', gone: true, text: c.text || '', sheet: '', time: '', quotes: [], notes: [], line: k.ident });
    return Object.assign(base, { kind: 'es', text: line.text, sheet: line.sheet || '', time: line.time || '', seconds: line.seconds,
      quotes: gtLineQuotes(line, k.ident), notes: (line.notes || []).slice(), line: k.ident });
  }
  const pet = (entry.pets || []).find((p) => p.id === k.ident);
  if (!pet) return Object.assign(base, { kind: 'pet', gone: true, title: thLabelShown(c.text) || TH_UNTITLED, lines: [], picks: [], statements: 0 });
  const lines = gtPetLines(entry, pet.id);
  return Object.assign(base, { kind: pet.parent === null || pet.parent === undefined ? 'pet' : 'sub', title: pet.title, lines,
    picks: (pet.picks || []).map((q) => gtQuoteAt(entry, q)).filter(Boolean), statements: lines.length });
}

/* the quote a row starts with: the first pick of the participant's highest PET there, and
   failing a pick, the first quote of a statement there, in the order the GET reads */
function gtFirstQuote(items, entry) {
  for (const it of items) if ((it.kind === 'pet' || it.kind === 'sub') && it.picks.length) return it.picks[0];
  const lines = (entry && entry.lines) || {};
  for (const it of items) {
    if (it.kind === 'es' && it.quotes.length) return it.quotes[0];
    if (it.kind !== 'pet' && it.kind !== 'sub') continue;
    for (const k of it.lines) {
      const quotes = gtLineQuotes(lines[k], k);
      if (quotes.length) return quotes[0];
    }
  }
  return null;
}

/* the GET table's rows as the board holds them, by GET and then by case */
const gtRows = (v) => (v && v.rows) || {};

/* the rows as a save sends them: a GET still on the board, and a row with a quote or a note */
function gtRowsKept(v) {
  const out = {};
  for (const [gid, cases] of Object.entries(gtRows(v))) {
    if (!thIsGroup(v, gid) || !cases) continue;
    for (const [kase, row] of Object.entries(cases)) {
      const quote = String((row && row.quote) || '').trim();
      const note = String((row && row.note) || '').trim();
      // a key quote taken from the transcript on Trajectories (trajchoose), kept as it came while no quote is ticked
      const passage = !quote && row && row.passage && typeof row.passage === 'object' ? JSON.parse(JSON.stringify(row.passage)) : null;
      // his bold in the key quote, made on Trajectories (trajbuild2), goes back as it came while the quote stays
      const bold = (quote || passage) && row && Array.isArray(row.bold) && row.bold.length ? JSON.parse(JSON.stringify(row.bold)) : null;
      if (quote || note || passage) (out[gid] = out[gid] || {})[kase] = Object.assign({ quote, note }, passage ? { passage } : {}, bold ? { bold } : {});
    }
  }
  return out;
}

/* a case's cards under a GET, as the table sets them out */
const gtCaseItems = (v, gid, kase, under = gtItems(v, gid)) => under.filter((it) => gtSplit(it.key).kase === kase)
  .map((it) => gtItemOf(v, it.key, it.within));

/* a row's quote: the one he ticked while the copy still holds it, else the one it starts with */
function gtKeyQuote(v, gid, kase, items) {
  const entry = gtCase(kase);
  const stored = ((gtRows(v)[gid] || {})[kase] || {}).quote;
  const chosen = stored ? gtQuoteAt(entry, stored) : null;
  return { quote: chosen || gtFirstQuote(items, entry), chosen: !!chosen };
}

/* The GET table of a board: each GET in canvas order with its note and its count, then a row for
   every case of the study in case order. No DOM in it, so node checks it beside the server's. */
function gtTable(v) {
  const parents = thParents(v);
  const inside = gtInside();
  const cases = ((TH.gets && TH.gets.cases) || []).filter((c) => inside.has(c.case));
  return gtCanvasOrder(v.groups.filter((g) => parents[g.id] === undefined)).map((gid) => {
    const g = thGroup(v, gid);
    const under = gtItems(v, gid);
    const rows = cases.map((c) => {
      const items = gtCaseItems(v, gid, c.case, under);
      const kq = gtKeyQuote(v, gid, c.case, items);
      return { kase: c.case, who: c.who, items, counted: items.some((it) => it.kind !== 'pn'), quote: kq.quote,
        chosen: kq.chosen, note: ((gtRows(v)[gid] || {})[c.case] || {}).note || '', none: !!c.none,
        open: !c.none && !c.complete, changed: c.status === 'changed' };
    });
    return { id: gid, label: g.label, note: thNoteOf(g), count: gtCount(v, gid), rows };
  });
}

const gtCaseMarks = (row) => [thTa() ? '' : row.none ? gtNoPets() : row.open ? gtNotComplete() : '', row.changed ? GT_CHANGED : ''].filter(Boolean);

/* a row's note: his words, a click opening them in a box, or Note to add one */
function gtRowNoteHtml(gid, row) {
  const ed = TH.rowEdit;
  if (ed && ed.gid === gid && ed.kase === row.kase) {
    return `<textarea class="th-vedit gt-rnote-box" id="gt-rnote-box" rows="3" spellcheck="true" placeholder="${escAttr(t('themes.gets.row_note_placeholder'))}" `
      + `aria-label="${escAttr(t('themes.gets.row_note_label', { who: row.who }))}">${esc(ed.value)}</textarea>`;
  }
  if (row.note) return `<p class="gt-rnote" data-gnote="${escAttr(gid)}" data-gcase="${escAttr(row.kase)}" title="${escAttr(t('themes.gets.row_note_tip'))}">${esc(row.note)}</p>`;
  return thLocked(TH.v) ? '' : `<button type="button" class="ghost small gt-rnote-add" tabindex="-1" data-gnote="${escAttr(gid)}" data-gcase="${escAttr(row.kase)}">${esc(t('themes.kind.note'))}</button>`;
}

/* a row's note opened in its box, from a click on it or on Note */
function gtRowNoteOpen(gid, kase) {
  if (!TH.live || !TH.v || thRefuse('note')) return;
  gtRowNoteDone(true);
  TH.rowEdit = { gid, kase, value: ((gtRows(TH.v)[gid] || {})[kase] || {}).note || '', focus: true };
  thTableDraw();
}

/* a row's note kept, with Enter or a click away, or let go with Esc. A change is one step of undo. */
function gtRowNoteDone(keep) {
  const ed = TH.rowEdit;
  if (!ed) return;
  TH.rowEdit = null;
  const box = $('gt-rnote-box');
  const text = box ? box.value : ed.value;
  const v = TH.v;
  if (keep && v && !thLocked(v)) {
    const now = thStickyClean(text);
    const row = (gtRows(v)[ed.gid] || {})[ed.kase] || { quote: '', note: '' };
    if (now !== (row.note || '')) {
      const before = thSnap(v, TH.removed);
      gtRowSet(v, ed.gid, ed.kase, { note: now });
      thDone(before, t('themes.step.table_note'));
      return;
    }
  }
  thTableDraw();
}

/* one row of the table changed in the board's rows, a row left empty taken out */
function gtRowSet(v, gid, kase, change) {
  const rows = JSON.parse(JSON.stringify(gtRows(v)));
  const was = (rows[gid] || {})[kase] || {};
  const row = Object.assign({ quote: '', note: '' }, was, change);
  // a new key quote leaves the bold of the one before it, and the passage of the transcript it took the place of
  if (row.quote !== (was.quote || '')) { delete row.bold; delete row.passage; }
  rows[gid] = rows[gid] || {};
  if (row.quote || row.note || row.passage) rows[gid][kase] = row;
  else delete rows[gid][kase];
  if (!Object.keys(rows[gid]).length) delete rows[gid];
  v.rows = rows;
}

/* A tick in the Inspector on a quote of a case's card under a GET makes it that row's key
   quote, and a tick on the one he ticked takes his tick off, the row going back to the one it
   starts with. One step of undo. */
function gtTick(gid, kase, qkey) {
  const v = TH.v;
  if (!TH.live || !v || !thIsGroup(v, gid) || thRefuse('pick')) return;
  const stored = ((gtRows(v)[gid] || {})[kase] || {}).quote || '';
  const before = thSnap(v, TH.removed);
  gtRowSet(v, gid, kase, { quote: stored === qkey ? '' : qkey });
  thDone(before, stored === qkey ? t('themes.step.unticked_quote') : t('themes.step.ticked_quote'));
}

/* The quotes a card under a GET offers for its row, each with its tick: a PET's or a
   sub-theme's picks first, then its statements' quotes, and a statement's own. */
function gtTickHtml(v, key, parents) {
  const get = gtTopOf(v, key, parents);
  if (!get) return '';
  const kase = gtSplit(key).kase;
  const entry = gtCase(kase);
  const it = gtItemOf(v, key);
  let quotes = it.kind === 'es' ? it.quotes : it.kind === 'pn' ? [] : it.picks.slice();
  if (it.kind === 'pet' || it.kind === 'sub') {
    for (const k of it.lines) for (const q of gtLineQuotes(((entry && entry.lines) || {})[k], k)) if (!quotes.some((x) => x.key === q.key)) quotes.push(q);
  }
  if (!quotes.length) return '';
  const kq = gtKeyQuote(v, get.id, kase, gtCaseItems(v, get.id, kase));
  const picked = new Set(it.picks ? it.picks.map((q) => q.key) : []);
  const locked = thLocked(v);
  return `<h3 class="section-label">${esc(t('themes.gets.quote_for', { label: thLabelShown(get.label) }))}</h3><ul class="th-quotes gt-ticks">`
    + quotes.map((q) => {
      const on = kq.quote && kq.quote.key === q.key;
      return `<li class="th-quote gt-tickrow"><button type="button" class="th-tick${on ? ' on' : ''}${on && !kq.chosen ? ' gt-auto' : ''}" tabindex="-1"`
        + ` data-gtick="${escAttr(q.key)}" data-gget="${escAttr(get.id)}" data-gcase="${escAttr(kase)}"${locked ? ' disabled' : ''}`
        + ` aria-pressed="${on ? 'true' : 'false'}" title="${escAttr(on ? (kq.chosen ? t('themes.gets.tick_chosen') : t('themes.gets.tick_auto'))
          : t('themes.gets.tick_other', { who: (gtCase(kase) || { who: kase }).who, label: thLabelShown(get.label) }))}">${TH_TICK_ICON}</button>`
        + `<span class="gt-tickq"><span class="gt-quote">${esc(q.text)}</span><span class="th-time">${esc(q.time)}</span>`
        + `${picked.has(q.key) ? `<span class="gt-pickmark">${esc(t('themes.gets.pick'))}</span>` : ''}</span></li>`;
    }).join('') + '</ul>';
}

/* ── the audit trail ── */

/* For one GET, five columns, transcript turn, quote, statement, PET and GET, joined by thin
   lines in the GET's tint, a block per participant. The server draws it, the same as on paper, and
   the card shows it over the screen. A turn with a recording plays from its timecode on a click. */
async function gtTrailOpen(gid) {
  if (!TH.live || !TH.meta || TH.busy || !thIsGroup(TH.v, gid)) return;
  thTitleDone(true);
  thNoteDone(true);
  gtRowNoteDone(true);
  thMenuClose();
  const ask = ++TH.trailAsk;
  await thFlush();
  if (TH.dirty) { say(t('themes.unsaved.trail'), 6000); return; }
  const g = thGroup(TH.v, gid);
  TH.trail = { gid };
  $('gt-trail-title').textContent = thLabelShown(g.label);
  $('gt-trail-count').textContent = '';
  $('gt-trail-note').hidden = true;
  $('gt-trail-body').innerHTML = `<p class="th-qnone">${esc(t('themes.gets.trail_reading'))}</p>`;
  $('gt-trail-card').className = `card gt-trail-card ${thTintClass(thTints(TH.v)[gid])}`;
  show('gt-trail');
  let data;
  try {
    data = await api('/api/gets-trail', { workbook: TH.path, board: TH.meta.id, get: gid });
  } catch (err) {
    if (ask === TH.trailAsk) $('gt-trail-body').innerHTML = `<p class="th-qnone${needsRestart(err) ? '' : ' said-failed'}">${esc(needsRestart(err) ? RESTART_LINE : err.message)}</p>`;
    return;
  }
  if (ask !== TH.trailAsk || $('gt-trail').hidden) return;
  $('gt-trail-title').textContent = data.label;
  const count = $('gt-trail-count');
  count.textContent = t('themes.gets.of', { count: data.count, total: data.total });
  count.classList.toggle('under', !!data.under);
  count.title = data.under ? t('themes.gets.under_min', { min: data.minimum }) : gtCountText(data.count, data.total);
  $('gt-trail-note').textContent = data.note || '';
  $('gt-trail-note').hidden = !data.note;
  $('gt-trail-body').innerHTML = data.html;
}

function gtTrailShut() {
  TH.trailAsk += 1;
  TH.trail = null;
  if (TH.trailAudio) TH.trailAudio.pause();
  for (const el of document.querySelectorAll('#gt-trail-body .playing')) el.classList.remove('playing');
  hide('gt-trail');
}

/* a turn of the trail plays its recording from its timecode, and a second click pauses it */
function gtTrailPlay(turn) {
  if (!TH.trailAudio) {
    // the card's own player, the recording the server streams and never a file of the page's
    TH.trailAudio = $('gt-trail-audio');
    TH.trailAudio.addEventListener('pause', () => { for (const el of document.querySelectorAll('#gt-trail-body .playing')) el.classList.remove('playing'); });
  }
  const player = TH.trailAudio;
  if (turn.classList.contains('playing') && !player.paused) { player.pause(); return; }
  for (const el of document.querySelectorAll('#gt-trail-body .playing')) el.classList.remove('playing');
  if (player.getAttribute('src') !== turn.dataset.audio) player.src = turn.dataset.audio;
  const go = () => { player.currentTime = Number(turn.dataset.at) || 0; player.play().catch((err) => say(err.message, 6000)); };
  if (player.readyState >= 1) go(); else player.addEventListener('loadedmetadata', go, { once: true });
  turn.classList.add('playing');
}

/* ── printing ── */

/* The print card: the GET table, the audit trail, all of it in one document or the canvas on one
   page, then under each participant every statement and quote or their key quote only, which the
   canvas does without, and Include participant notes, unticked each time, since participant notes
   appear in no export unless he ticks it. From a GET's trail it prints that GET's trail. */
function gtPrintOpen(what = 'table', gid = null) {
  if (!TH.live || !TH.meta) return;
  thVmenu(false);
  TH.printing = { what: ['table', 'trail', 'all', 'canvas'].includes(what) ? what : 'table', detail: 'full', gid };
  $('gt-print-notes').checked = false;
  thIncludesDraw();
  $('gt-print-what').hidden = !!gid;
  $('gt-print-title').textContent = gid ? t('themes.gets.trail_of', { label: thLabelShown((thGroup(TH.v, gid) || { label: '' }).label) }) : (TH.meta.name || t('themes.unit.gets'));
  gtPrintDraw();
  show('gt-print');
  $('gt-print-go').focus();
}

function gtPrintDraw() {
  const p = TH.printing;
  if (!p) return;
  // each choice a radio inside its row's label (31 October)
  for (const row of document.querySelectorAll('#gt-print [data-what]')) row.querySelector('input').checked = row.dataset.what === p.what;
  for (const row of document.querySelectorAll('#gt-print [data-detail]')) row.querySelector('input').checked = row.dataset.detail === p.detail;
  // the canvas prints what it shows, so Under each participant goes while it is chosen
  $('gt-print-detail').hidden = p.what === 'canvas' && !p.gid;
  // the canvas has Save as PDF too, and Save as an image beside it (1 November 2026, exportA)
  if ($('gt-print-png')) $('gt-print-png').hidden = !(p.what === 'canvas' && !p.gid);
  // and a thematic analysis project's theme table Microsoft Word (taword)
  if ($('gt-print-word')) $('gt-print-word').hidden = !(thTa() && !TH.lpets && p.what === 'table' && !p.gid);
}

function gtPrintShut() {
  TH.printing = null;
  hide('gt-print');
}

/* the address of the print view, `/gets/print`, for the board on the canvas */
function gtPrintUrl(p, notes) {
  const q = { root: TH.root || '', board: TH.meta.id, what: p.gid ? 'trail' : p.what, detail: p.detail };
  // a participant's LPETs print from their own file (21 October)
  if (TH.lpets) Object.assign(q, { workbook: TH.path, lpets: '1' });
  if (notes) q.notes = '1';
  q.sending = thIncluded('export_for_sending') ? '1' : '0';
  q.descriptions = thIncluded('export_descriptions') ? '1' : '0';
  if (p.gid) q.get = p.gid;
  // the page is read on screen first, and its own Print opens the dialog (187)
  q.auto = '0';
  return `${TH.getsPrint || '/gets/print'}?${new URLSearchParams(q)}`;
}

/* Print: the view in a tab of its own, which opens the print dialog itself, a save still to go
   written first. Nothing is written by it. */
async function gtPrintGo() {
  const p = TH.printing;
  const notes = $('gt-print-notes').checked;
  gtPrintShut();
  if (!p || !TH.live || !TH.meta) return;
  // the canvas is taken from the screen, so it needs nothing of the server's print view
  if (p.what === 'canvas' && !p.gid) { thCanvasPrint({ notes }); return; }
  if (!TH.getsPrint) { say(RESTART_LINE, 6000); return; }
  thTitleDone(true);
  thNoteDone(true);
  gtRowNoteDone(true);
  const url = gtPrintUrl(p, notes);
  const waiting = !!(TH.dirty || TH.chain || TH.saveTimer);
  const tab = window.open(waiting ? 'about:blank' : url, '_blank');
  if (!tab) { say(t('themes.print.blocked'), 8000); return; }
  if (!waiting) return;
  await thFlush();
  if (TH.dirty) { tab.close(); say(t('themes.unsaved.printed'), 6000); return; }
  tab.location.href = url;
}

/* Save as PDF on the print card (31 October 2026, pdfexport): the page Print would show, as a PDF at the project's
   root where the agents' `gets export` puts it and named the same way, made by the server with Typst since 9
   November 2026 (typst5) and written there, the line after naming it or saying why it could not be made. For a
   participant's LPETs, Print. */
async function gtPdfGo() {
  const p = TH.printing;
  const notes = $('gt-print-notes').checked;
  if (!p || !TH.live || !TH.meta) { gtPrintShut(); return; }
  // the canvas's PDF is drawn from the board, as on PETs (exportA)
  if (p.what === 'canvas' && !p.gid) { gtPrintShut(); thCanvasOut('pdf', { notes }); return; }
  if (TH.lpets) { gtPrintGo(); return; }
  gtPrintShut();
  if (!TH.getsPrint) { say(RESTART_LINE, 6000); return; }
  thTitleDone(true);
  thNoteDone(true);
  gtRowNoteDone(true);
  await thFlush();
  if (TH.dirty) { say(t('themes.unsaved.exported'), 6000); return; }
  let made = null;
  try {
    made = await api('/api/gets-boards', { root: TH.root || '', board: TH.meta.id, op: 'pdf', what: p.gid ? 'trail' : p.what,
      detail: p.detail, notes, get: p.gid || '', sending: thIncluded('export_for_sending'),
      descriptions: thIncluded('export_descriptions') });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : (err.message || t('themes.pdf.failed')), 9000);
    return;
  }
  if (!made || !made.path) { say(RESTART_LINE, 6000); return; }
  thExported({ shown: made.shown, name: (made.version && made.version.name) || TH.meta.name, reveal: false, word: false });
}

/* Microsoft Word for a thematic analysis project's theme table (taword, 1 November 2026, Adam: "yes, add it"), from
   the print card with the theme table chosen or from Table view: the board of themes as a Word document at the
   project's root, where its PDF goes and named the same way, every code and extract or each participant's key
   extract alone as the card says, participant notes as ticked, Descriptions and Leave out the board's name as they
   are, its author Your name. The line after names it. */
async function gtWordGo(p, notes) {
  gtPrintShut();
  if (!p || !TH.live || !TH.meta) return;
  thTitleDone(true);
  thNoteDone(true);
  gtRowNoteDone(true);
  await thFlush();
  if (TH.dirty) { say(t('themes.unsaved.exported'), 6000); return; }
  let made = null;
  try {
    made = await api('/api/gets-boards', { root: TH.root || '', board: TH.meta.id, op: 'word', detail: p.detail, notes,
      sending: thIncluded('export_for_sending'), descriptions: thIncluded('export_descriptions') });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return;
  }
  if (!made || !made.word) { say(RESTART_LINE, 6000); return; }
  thExported({ shown: made.shown, name: (made.version && made.version.name) || TH.meta.name, reveal: false, word: false });
}

/* Save as an image on the print card, with Canvas on one page chosen (1 November 2026, exportA): the canvas's
   picture, as on PETs (thCanvasOut), at the project's root, a participant note only with Include participant
   notes. */
function gtPngGo() {
  const p = TH.printing;
  const notes = $('gt-print-notes').checked;
  gtPrintShut();
  if (!p || !TH.live || !TH.meta) return;
  thCanvasOut('png', { notes });
}

/* The keys while the print card or the trail is open: Enter prints and Esc closes the card, and
   Esc closes the trail. The canvas hears none of them. True when one of them is open. */
function gtKeys(e) {
  const printing = $('gt-print') && !$('gt-print').hidden;
  const trail = $('gt-trail') && !$('gt-trail').hidden;
  if (!printing && !trail) return false;
  // nothing behind the card hears a key, while the card's own controls keep theirs
  e.stopPropagation();
  if (printing) {
    if (e.key === 'Escape') { e.preventDefault(); gtPrintShut(); }
    else if (e.key === 'Enter' && !MOD(e) && !(e.target && e.target.closest && e.target.closest('button, input'))) {
      e.preventDefault(); gtPrintGo();
    }
  } else if (e.key === 'Escape') { e.preventDefault(); gtTrailShut(); }
  else if ((e.key === 'Enter' || e.key === ' ') && e.target && e.target.closest && e.target.closest('[data-audio]')) {
    e.preventDefault();
    gtTrailPlay(e.target.closest('[data-audio]'));
  }
  return true;
}

/* ── Open beside this one ── */

/* Another case's board beside the canvas, read-only as a revision on view is: on the PETs screen
   from the case switcher, on its Current board, else the board last open, and on the GETs screen
   from a case's menu in the Cases panel, on the board its PETs came in from. The canvas splits, his
   own on the left as it is, and below about 900px the two stack. Its cards, labels, frames and
   sticky notes are drawn as the PETs canvas draws them, with nothing on it to move: a drag pans,
   the wheel zooms, and Fit all brings it all in view. Opening it and closing it write nothing. */
async function gtBesideOpen(c) {
  if (!TH.live || !c || !c.path) return;
  thCasemenu(false);
  thMenuClose();
  const ask = ++TH.besideAsk;
  TH.beside = { path: c.path, who: c.who || c.case, v: null, view: { x: 0, y: 0, z: 1 }, sizes: {}, layout: {}, els: {} };
  $('th-beside-case').textContent = TH.beside.who;
  $('th-beside-board').textContent = c.board_name || '';
  $('th-bworld').innerHTML = '';
  gtBesideNote('');
  gtBesideShow(true);
  let data;
  try {
    // `beside` keeps this look from counting as opening the case's PETs, in the recent list
    data = await api('/api/themes', c.board ? { workbook: c.path, board: c.board, beside: true } : { workbook: c.path, beside: true });
  } catch (err) {
    if (ask === TH.besideAsk) gtBesideNote(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));
    return;
  }
  if (ask !== TH.besideAsk || !TH.beside) return;
  const cards = {};
  for (const x of data.cards || []) cards[x.key] = Object.assign({}, x);
  TH.beside.v = { cards, groups: (data.groups || []).map((g) => Object.assign({}, g, { members: g.members.slice() })),
    discarded: (data.discarded || []).slice(), picks: data.picks || {}, stacks: data.stacks || {},
    stickies: Array.isArray(data.stickies) ? data.stickies.map((n) => Object.assign({}, n)) : [], readonly: true };
  TH.beside.sheets = data.sheets || [];
  $('th-beside-case').textContent = data.case || TH.beside.who;
  $('th-beside-board').textContent = (data.version && data.version.name) || c.board_name || '';
  gtBesideRender();
  gtBesideFit();
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => { if (TH.beside && ask === TH.besideAsk) { gtBesideRender(); } });
  }
}

/* the split, on or off, and the canvas fitted to the room it has */
function gtBesideShow(on) {
  $('th-beside').hidden = !on;
  thStage().parentElement.classList.toggle('th-split', on);
  thCorners();
}

/* its cross: the canvas whole again, as it was, and nothing written */
function gtBesideShut() {
  TH.besideAsk += 1;
  TH.beside = null;
  if (!$('th-beside')) return;
  $('th-bworld').innerHTML = '';
  gtBesideShow(false);
}

function gtBesideNote(text, failed = false) {
  $('th-bnote').textContent = text;
  $('th-bnote').hidden = !text;
  $('th-bnote').classList.toggle('said-failed', !!(failed && text));
}

/* the board beside drawn as the PETs canvas draws it, every control and mark of an act left off */
function gtBesideRender() {
  const b = TH.beside;
  if (!b || !b.v) return;
  const v = b.v;
  const world = $('th-bworld');
  world.innerHTML = '<div class="th-frames"></div><div class="th-cards"></div><div class="th-stickies"></div><div class="th-labels"></div>';
  const [frames, cardBox, stickyBox, labelBox] = world.children;
  const parents = thParents(v);
  const tints = thTints(v);
  const first = b.sheets[0];
  b.els = { cards: {}, labels: {}, frames: {}, stickies: {} };
  for (const [key, c] of Object.entries(v.cards)) {
    if (!thOnCanvas(v, key)) continue;
    const el = document.createElement('div');
    const owner = parents[key];
    el.className = `th-card${owner !== undefined ? ` in ${thTintClass(tints[owner])}` : ''}${c.missing ? ' missing' : ''}`;
    el.title = c.text || '';
    el.innerHTML = `<p class="th-text">${esc(c.text)}</p><div class="th-foot"><span class="th-time">${esc(c.time || '')}</span>`
      + `${c.sheet && c.sheet !== first ? `<span class="th-sheet">${esc(c.sheet)}</span>` : ''}</div>`;
    cardBox.appendChild(el);
    b.els.cards[key] = el;
  }
  for (const n of thStickies(v)) {
    const el = document.createElement('div');
    el.className = `th-sticky sticky-${TH_STICKY_COLOURS.includes(n.colour) ? n.colour : TH_STICKY_COLOURS[0]}`;
    el.innerHTML = `<p class="th-sticky-text">${esc(n.text)}</p>`;
    stickyBox.appendChild(el);
    b.els.stickies[n.id] = el;
  }
  for (const g of v.groups) {
    const tint = thTintClass(tints[g.id]);
    const el = document.createElement('div');
    el.className = `th-label ${tint}${g.members.some((m) => thIsGroup(v, m)) ? ' upper' : ''}`;
    el.title = `${thLabelShown(g.label)}${thDescOf(g) ? `\n${thDescOf(g)}` : ''}\n${thCountText(v, g.id)}`;
    if (thDescOf(g)) el.classList.add('described');
    el.innerHTML = `<span class="th-swatch" aria-hidden="true"></span><span class="th-words"><span class="th-title">${esc(thLabelShown(g.label))}</span>`
      + `${thDescOf(g) ? `<span class="th-desc">${esc(thDescOf(g))}</span>` : ''}</span>`
      + (thNoteOf(g) ? `<span class="th-noted" role="img" aria-label="${escAttr(t('themes.label.has_note'))}">${TH_NOTE_ICON}</span>` : '');
    labelBox.appendChild(el);
    b.els.labels[g.id] = el;
    const frame = document.createElement('div');
    frame.className = `th-frame ${tint}`;
    frame.innerHTML = `<span class="th-badge" aria-hidden="true">${thBadgeText(v, g.id)}</span>`;
    frames.appendChild(frame);
    b.els.frames[g.id] = frame;
  }
  b.sizes = {};
  for (const [id, el] of [...Object.entries(b.els.cards), ...Object.entries(b.els.labels), ...Object.entries(b.els.stickies)]) {
    b.sizes[id] = { w: el.offsetWidth, h: el.offsetHeight };
  }
  const size = (id) => b.sizes[id] || (v.cards[id] ? TH_CARD : thIsSticky(v, id) ? TH_STICKY : TH_LABEL);
  thLabelsWiden(v, b.els.labels, b.sizes, size);
  b.layout = thLayout(v, size, null);
  const widths = Object.fromEntries(Object.entries(b.els.frames).map(([id, el]) => [id, el.firstElementChild.offsetWidth]));
  const spots = thBadgeSpots(v, b.layout, widths);
  const put = (el, at) => { el.style.left = `${at.x}px`; el.style.top = `${at.y}px`; };
  for (const [key, el] of Object.entries(b.els.cards)) put(el, v.cards[key]);
  for (const n of thStickies(v)) if (b.els.stickies[n.id]) put(b.els.stickies[n.id], n);
  for (const g of v.groups) {
    put(b.els.labels[g.id], g);
    const box = b.layout[g.id] && b.layout[g.id].body && b.layout[g.id].frame;
    const frame = b.els.frames[g.id];
    frame.hidden = !box;
    if (!box) continue;
    Object.assign(frame.style, { left: `${box.x}px`, top: `${box.y}px`, width: `${box.w}px`, height: `${box.h}px` });
    if (spots[g.id] !== undefined) frame.firstElementChild.style.left = `${spots[g.id]}px`;
  }
  gtBesideNote(Object.keys(v.cards).length ? '' : t('themes.empty.statements'));
  gtBesideView();
}

function gtBesideView() {
  const b = TH.beside;
  if (!b) return;
  const { x, y, z } = b.view;
  $('th-bworld').style.transform = `translate(${x}px, ${y}px) scale(${z})`;
  const stage = $('th-bstage');
  stage.style.backgroundSize = `${22 * z}px ${22 * z}px`;
  stage.style.backgroundPosition = `${x}px ${y}px`;
}

/* Fit all, beside: everything on its board in view, never closer than its own size */
function gtBesideFit() {
  const b = TH.beside;
  if (!b || !b.v) return;
  const stage = $('th-bstage');
  const boxes = [];
  for (const key of Object.keys(b.els.cards)) boxes.push({ x: b.v.cards[key].x, y: b.v.cards[key].y, w: b.sizes[key].w, h: b.sizes[key].h });
  for (const g of b.v.groups) if (b.layout[g.id]) boxes.push(b.layout[g.id].frame);
  for (const n of thStickies(b.v)) if (b.sizes[n.id]) boxes.push({ x: n.x, y: n.y, w: b.sizes[n.id].w, h: b.sizes[n.id].h });
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  if (!boxes.length) { b.view = { x: w / 2, y: h / 2, z: 1 }; gtBesideView(); return; }
  const u = thUnion(boxes);
  const pad = 40;
  const z = Math.min(1, Math.max(TH_ZOOM_MIN, Math.min((w - 2 * pad) / u.w, (h - 2 * pad) / u.h)));
  b.view = { x: w / 2 - (u.x + u.w / 2) * z, y: h / 2 - (u.y + u.h / 2) * z, z };
  gtBesideView();
}

/* the pane's own view: a drag anywhere on it pans, and the wheel zooms at the pointer, as the
   canvas's does */
function gtBesideWheel(e) {
  const b = TH.beside;
  if (!b) return;
  e.preventDefault();
  const stage = $('th-bstage');
  const r = stage.getBoundingClientRect();
  const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? stage.clientHeight : 1;
  const step = Math.max(-60, Math.min(60, (e.deltaY || (e.shiftKey ? e.deltaX : 0)) * unit));
  const next = Math.min(TH_ZOOM_MAX, Math.max(TH_ZOOM_MIN, b.view.z * Math.exp(-step * (e.ctrlKey ? 0.005 : 0.004))));
  const sx = e.clientX - r.left;
  const sy = e.clientY - r.top;
  b.view.x = sx - (sx - b.view.x) * (next / b.view.z);
  b.view.y = sy - (sy - b.view.y) * (next / b.view.z);
  b.view.z = next;
  gtBesideView();
}

function gtBesidePan(e) {
  const b = TH.beside;
  if (!b || e.button !== 0) return;
  e.preventDefault();
  const stage = $('th-bstage');
  const from = { x: e.clientX, y: e.clientY, vx: b.view.x, vy: b.view.y };
  stage.classList.add('th-panning');
  try { stage.setPointerCapture(e.pointerId); } catch { /* a nicety */ }
  const move = (m) => { b.view.x = from.vx + m.clientX - from.x; b.view.y = from.vy + m.clientY - from.y; gtBesideView(); };
  const up = () => {
    stage.classList.remove('th-panning');
    stage.removeEventListener('pointermove', move);
    stage.removeEventListener('pointerup', up);
    stage.removeEventListener('pointercancel', up);
  };
  stage.addEventListener('pointermove', move);
  stage.addEventListener('pointerup', up);
  stage.addEventListener('pointercancel', up);
}

/* the Cases panel's own wiring, run once from themesBoot */
function gtBoot() {
  for (const [id, step] of [['th-step-es', 'statements'], ['th-step-pets', 'pets'], ['th-step-lpets', 'lpets'], ['th-step-gets', 'gets'],
    ['th-step-lgets', 'lgets'], ['th-step-trajectories', 'trajectories'], ['th-step-codes', 'codes']]) {
    $(id).onclick = () => thStepTo(step);
  }
  dsTabsWatch('th-steps');
  thTpWire();
  $('th-open-cases').addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-open-cases').onclick = () => (TH.casesOpen ? gtCasesShut() : gtCasesOpen());
  $('th-cpanel-close').onclick = () => gtCasesShut();
  const list = $('gt-cases');
  // its top edge fades once it has scrolled, and a list at rest keeps its first row whole (see .gt-cases)
  list.addEventListener('scroll', () => list.classList.toggle('scrolled', list.scrollTop > 0), { passive: true });
  list.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.gt-fold, .gt-cmenu, .gt-tw, .gt-none, .gt-swatch, .gt-stk, .gt-nodrag')) { e.preventDefault(); return; }
    gtPullDown(e);
  });
  list.addEventListener('click', (e) => {
    const fold = e.target.closest('[data-gfold]');
    if (fold) {
      const c = TH.gets && TH.gets.cases[Number(fold.dataset.gfold)];
      if (c) gtFold(c.case);
      return;
    }
    // a PET's, a sub-theme's or Not in a PET's own fold, from its chevron (16 October)
    const twist = e.target.closest('[data-gtw]');
    if (twist) { gtFold(twist.dataset.gtw); return; }
    const swatch = e.target.closest('[data-gcolour]');
    if (swatch) { const r = swatch.getBoundingClientRect(); gtColourMenu(Number(swatch.dataset.gcolour), r.left, r.bottom); return; }
    const menu = e.target.closest('[data-gmenu]');
    if (menu) { const r = menu.getBoundingClientRect(); gtCaseMenu(Number(menu.dataset.gmenu), r.left, r.bottom); }
  });
  // the panel's tabs on a thematic analysis project's board, Codes and Participants (themesbuild)
  gtPtabRead();
  const ptabs = $('gt-ptabs');
  ptabs.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  ptabs.addEventListener('click', (e) => {
    const tab = e.target.closest('[data-ptab]');
    if (tab) gtPtabSet(tab.dataset.ptab);
  });
  document.addEventListener('pointermove', (e) => { if (TH.pull) gtPullMove(e); });
  document.addEventListener('pointerup', (e) => { if (TH.pull) gtPullUp(e); });
  const find = $('gt-find');
  find.addEventListener('input', () => { TH.cfind = find.value; TH.cflip.clear(); gtCasesDraw(); });
  find.addEventListener('keydown', (e) => {
    e.stopPropagation();
    if (e.key === 'Escape') { e.preventDefault(); find.value = ''; TH.cfind = ''; TH.cflip.clear(); gtCasesDraw(); find.blur(); }
  });
  const inspector = $('th-panel');
  inspector.addEventListener('focusin', (e) => { if (e.target && e.target.id === 'th-pn-box') gtPnStart(e.target); });
  inspector.addEventListener('input', (e) => {
    if (e.target && e.target.id === 'th-pn-box' && TH.pnBox && TH.pnBox.key === e.target.dataset.pn) TH.pnBox.value = e.target.value;
  });
  inspector.addEventListener('focusout', (e) => { if (e.target && e.target.id === 'th-pn-box' && !TH.noteRedraw) gtPnDone(true); });
  inspector.addEventListener('keydown', (e) => {
    if (!e.target || e.target.id !== 'th-pn-box') return;
    e.stopPropagation();
    if (e.isComposing) return;
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); gtPnDone(true); }
    else if (e.key === 'Escape') { e.preventDefault(); gtPnDone(false); }
  });
  // a tick on a quote in the Inspector, and a GET's Audit trail there
  inspector.addEventListener('click', (e) => {
    if (!thGets()) return;
    const tick = e.target.closest('[data-gtick]');
    if (tick) { gtTick(tick.dataset.gget, tick.dataset.gcase, tick.dataset.gtick); return; }
    const trail = e.target.closest('[data-gtrail]');
    if (trail) gtTrailOpen(trail.dataset.gtrail);
  });
  // Export in the board menu
  $('th-vmenu').addEventListener('click', (e) => {
    const printing = e.target.closest('[data-gprint]');
    if (printing && thGets()) gtPrintOpen(printing.dataset.gprint);
  });
  // the print card: what to print, under each participant, the ticks, Cancel, Save as PDF and Print. A choice is a
  // radio inside its row's label, so the whole row chooses it
  const card = $('gt-print');
  card.addEventListener('pointerdown', (e) => { if (e.target.closest('[data-what], [data-detail]')) e.preventDefault(); });
  card.addEventListener('click', (e) => {
    const what = e.target.closest('[data-what]');
    if (what && TH.printing) { TH.printing.what = what.dataset.what; gtPrintDraw(); return; }
    const detail = e.target.closest('[data-detail]');
    if (detail && TH.printing) { TH.printing.detail = detail.dataset.detail; gtPrintDraw(); }
  });
  $('gt-print-cancel').onclick = () => gtPrintShut();
  // Leave out the board's name saves as it changes, as it does in the PETs screen's Export
  $('gt-print-sending').onchange = (e) => thInclude('export_for_sending', e.target.checked);
  $('gt-print-close').onclick = () => gtPrintShut();
  $('gt-print-go').onclick = () => gtPrintGo();
  if ($('gt-print-pdf')) $('gt-print-pdf').onclick = () => gtPdfGo();
  if ($('gt-print-png')) $('gt-print-png').onclick = () => gtPngGo();
  if ($('gt-print-word')) $('gt-print-word').onclick = () => gtWordGo(TH.printing, $('gt-print-notes').checked);
  // the audit trail's card: its cross, Print, and a turn's recording
  $('gt-trail-close').onclick = () => gtTrailShut();
  $('gt-trail-print').onclick = () => { if (TH.trail) gtPrintOpen('trail', TH.trail.gid); };
  $('gt-trail-body').addEventListener('click', (e) => {
    const turn = e.target.closest('[data-audio]');
    if (turn) gtTrailPlay(turn);
  });
  // Open beside this one, from the case switcher, and the board beside: its cross, Fit all, a drag
  // to pan and the wheel to zoom
  $('th-casemenu').addEventListener('click', (e) => {
    const beside = e.target.closest('[data-beside]');
    if (beside) gtBesideOpen(TH.cases[Number(beside.dataset.beside)]);
  });
  $('th-beside-close').onclick = () => gtBesideShut();
  $('th-beside-fit').onclick = () => gtBesideFit();
  for (const id of ['th-beside-close', 'th-beside-fit']) $(id).addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-bstage').addEventListener('pointerdown', gtBesidePan);
  $('th-bstage').addEventListener('wheel', gtBesideWheel, { passive: false });
  if (window.ResizeObserver) new ResizeObserver(() => { if (TH.beside && TH.beside.v) gtBesideView(); }).observe($('th-bstage'));
}

/* ── wiring ── */

function themesBoot() {
  const stage = thStage();
  if (!stage) return;
  stage.addEventListener('pointerdown', thPointerDown);
  stage.addEventListener('pointermove', thPointerMove);
  stage.addEventListener('pointerup', thPointerUp);
  stage.addEventListener('pointercancel', thPointerUp);
  stage.addEventListener('wheel', thWheel, { passive: false });
  stage.addEventListener('contextmenu', thContextMenu);
  // a middle-button press otherwise starts the browser's own scrolling
  stage.addEventListener('auxclick', (e) => { if (e.button === 1) e.preventDefault(); });
  window.addEventListener('keydown', thKeyDown, true);
  window.addEventListener('keyup', thKeyUp, true);
  window.addEventListener('blur', () => { TH.space = false; stage.classList.remove('th-grab'); thDragAlt(false); });
  // a press anywhere outside the right-click menu puts it away
  document.addEventListener('pointerdown', (e) => {
    if (TH.menu && !TH.menu.el.contains(e.target) && !(TH.menu.sub && TH.menu.sub.contains(e.target))) thMenuClose();
  }, true);
  window.addEventListener('resize', () => thMenuClose());

  thTableBoot();
  // Group, Undo and Redo on the palette do what g, Cmd + Z and Shift + Cmd + Z do, and leave the focus on the canvas
  for (const id of ['th-group', 'th-undo']) $(id).addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-redo').addEventListener('pointerdown', (e) => e.preventDefault());
  // and New sticky note puts one in the middle of the canvas, its words taking the focus (18 October)
  $('th-sticky').addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-sticky').onclick = () => thStickyBar();
  $('th-group').onclick = () => { if (TH.live && !TH.busy) thGroupKey(); };
  // Select all on the palette does what Cmd + A does (20 October)
  $('th-selall').addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-selall').onclick = () => { if (TH.live && !TH.busy) thSelectAll(); };
  thSideBoot();
  $('th-undo').onclick = () => thUndo(true);
  $('th-redo').onclick = () => thUndo(false);
  // the toolbar's Auto-arrange repeats the last way, its small arrow opens the ways, Align's six and Spread's
  // two act on the selection, and the dots hold those eight where the bar has no room (21 October)
  const tools = $('th-palette');
  tools.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-arrange').onclick = () => thArrangeTool();
  $('th-arrange-way').onclick = (e) => { e.stopPropagation(); if (TH.menu && TH.menu.button === e.currentTarget) thMenuClose(); else thArrangeMenu(); };
  $('th-pal-more').onclick = (e) => { e.stopPropagation(); if (TH.menu && TH.menu.button === e.currentTarget) thMenuClose(); else thAlignMore(); };
  for (const b of tools.querySelectorAll('[data-align], [data-spread]')) b.onclick = () => thAlignDo(b.dataset.align || b.dataset.spread);
  // the palette's grip moves it, and as one of the canvas's own controls a press on it never starts a lasso
  $('th-palette-grip').addEventListener('pointerdown', thPaletteGrab);
  // the toolbar's words measured again once the app's own faces have loaded, narrower than the fallback's
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => thPaletteFit());
  $('th-help').addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-help').onclick = () => openHelp();
  // View's Status Bar in Idiograph's own window turns the bar on or off, through the window's menu
  window.thStatusToggle = thStatusToggle;
  // a right click on the status bar picks its counts, a tick in its menu kept at once
  $('th-status').addEventListener('contextmenu', (e) => {
    if (!thStatusOn()) return;
    e.preventDefault();
    e.stopPropagation();
    thStatusMenu(true, e.clientX, e.clientY);
  });
  $('th-smenu').addEventListener('change', (e) => {
    const box = e.target.closest('input[data-stat]');
    if (box) thStatusPick(box.dataset.stat, box.checked);
  });
  document.addEventListener('pointerdown', (e) => {
    if (TH.smenu && !e.target.closest('#th-smenu')) thStatusMenu(false);
  }, true);
  document.addEventListener('keydown', (e) => {
    if (TH.smenu && e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); thStatusMenu(false); }
  }, true);
  $('th-feedback').onclick = () => openFeedback(TH.mode === 'gets' ? 'gets' : 'pets');
  // the export control opens its menu, the view's own part (exportA): in Table view Print, Save as PDF, Microsoft Word,
  // Markdown and CSV, the ticks and PET labels, which saves at once and leaves the menu open, and on the canvas Print,
  // Save as PDF and Save as an image
  // opened from the keyboard, a menu's first item takes the focus (a11yfix)
  $('th-export').onclick = (e) => { thXmenu(!TH.xmenu); if (TH.xmenu && e.detail === 0) menuFirst($('th-xmenu')); };
  if (typeof menuRoles === 'function') menuRoles($('th-xmenu'));
  $('th-xmenu').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  // the two ticks, Include not placed and Include statements set aside, save as they change
  $('th-xmenu').addEventListener('change', (e) => {
    const box = e.target.closest('[data-include]');
    if (box) thInclude(box.dataset.include, box.checked);
  });
  $('th-xmenu').addEventListener('click', (e) => {
    const pick = e.target.closest('[data-labels]');
    if (pick) { thLabels(pick.dataset.labels); return; }
    const op = e.target.closest('[data-xop]');
    if (!op) return;
    if (op.dataset.xop === 'print') { thPrint(); return; }
    if (op.dataset.xop === 'canvas') { thCanvasPrint(); return; }
    if (op.dataset.xop === 'cpdf') { thCanvasOut('pdf'); return; }
    if (op.dataset.xop === 'cpng') { thCanvasOut('png'); return; }
    if (op.dataset.xop === 'pdf') { thXmenu(false); thPdf(); return; }
    thXmenu(false);
    thExport(op.dataset.xop === 'word');
  });
  document.addEventListener('pointerdown', (e) => {
    if (TH.xmenu && !e.target.closest('#th-xmenu, #th-export')) thXmenu(false);
  }, true);
  // Settings over this screen opens on PETs, its own category, with the model under AI
  $('th-settings').onclick = () => openSettings('pets');
  // the band's line when there is no question yet opens Project settings for the board's project
  $('th-band').addEventListener('click', (e) => { if (e.target.closest('.band-link')) openProjectSettings(TH.project); });
  if (window.ResizeObserver) {
    new ResizeObserver(() => thBandMeasure()).observe($('th-band'));
    // and the dock as the window changes its width, the toolbar's words giving way to the room
    new ResizeObserver(() => { thBandMeasure(); thPaletteFit(); }).observe($('th-dock'));
  }
  // the zoom bar keeps clear of the bin as the canvas narrows with the sidebars open beside it
  if (window.ResizeObserver) new ResizeObserver(() => thCorners()).observe($('th-stage'));
  // and the bar's counts fit again as the window changes width (see thCountFit)
  if (window.ResizeObserver) new ResizeObserver(() => thCountFit()).observe($('themes').querySelector('.rail'));
  // the pointer and the hand, by the zoom
  for (const id of ['th-mode-pointer', 'th-mode-hand']) $(id).addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-mode-pointer').onclick = () => thHand(false);
  $('th-mode-hand').onclick = () => thHand(true);
  // the minimap: its button at the end of the zoom bar, which leaves the focus on the canvas, a press and
  // a drag on the map, the pointer on it, which keeps it awake in Auto, and its width the zoom bar's as
  // the canvas changes width. The wheel over it goes on to the canvas's own (thWheel), and so does a
  // window crossing TH_MAP.narrow, through the canvas's width
  $('th-map-btn').addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-map-btn').onclick = () => thMapToggle();
  // Quotes on cards, its button beside the map's (Adam, 19 October), and a quote shown whole: its play
  // button, Show in passage, and a press anywhere else or the wheel putting it away. Since 30 October a click
  // takes the next of Off, Short and Full (A) or opens their menu (B), and a right click or a press held opens
  // the menu in both, as Close pairs' does its gap
  const quotesBtn = $('th-quotes-btn');
  let quotesHeld = null;
  quotesBtn.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    if (e.button !== 0 || TH_QUOTES_CONTROL === 'menu') return;
    clearTimeout(quotesHeld);
    quotesHeld = setTimeout(() => { quotesHeld = 'held'; thQuotesMenu(true, e.clientX, e.clientY); }, 550);
  });
  const quotesLet = () => { if (quotesHeld !== 'held') clearTimeout(quotesHeld); };
  quotesBtn.addEventListener('pointerup', quotesLet);
  quotesBtn.addEventListener('pointerleave', quotesLet);
  quotesBtn.onclick = () => {
    if (quotesHeld === 'held') { quotesHeld = null; return; }
    thQuotesToggle();
  };
  quotesBtn.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    e.stopPropagation();
    thQuotesMenu(true, e.clientX, e.clientY);
  });
  $('th-qmenu').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-qmenu').addEventListener('click', (e) => {
    const way = e.target.closest('[data-qway]');
    if (way) thQuotesSet(way.dataset.qway);
  });
  // a press anywhere else puts it away, and Esc does in thKeyDown
  document.addEventListener('pointerdown', (e) => {
    if (TH.qmenu && !e.target.closest('#th-qmenu, #th-quotes-btn')) thQuotesMenu(false);
  }, true);
  $('th-notes-btn').addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-notes-btn').onclick = () => thNotesToggle();
  // Compact, on a thematic analysis project's board (themesbuild)
  $('th-compact-btn').addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-compact-btn').onclick = () => thCompactToggle();
  // Close pairs beside it (20 October): a click turns the lines on or off, and a right click or a press held
  // opens the gap's menu
  const closeBtn = $('th-close-btn');
  let closeHeld = null;
  closeBtn.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    if (e.button !== 0) return;
    clearTimeout(closeHeld);
    closeHeld = setTimeout(() => { closeHeld = 'held'; thCloseMenu(true, e.clientX, e.clientY); }, 550);
  });
  const closeLet = () => { if (closeHeld !== 'held') clearTimeout(closeHeld); };
  closeBtn.addEventListener('pointerup', closeLet);
  closeBtn.addEventListener('pointerleave', closeLet);
  closeBtn.onclick = () => {
    if (closeHeld === 'held') { closeHeld = null; return; }
    thCloseToggle();
  };
  closeBtn.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (TH.mode !== 'gets') thCloseMenu(true, e.clientX, e.clientY);
  });
  $('th-cpmenu').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-cpmenu').addEventListener('click', (e) => {
    const gap = e.target.closest('[data-cgap]');
    if (gap) { thCloseGapPick(Number(gap.dataset.cgap)); return; }
    const again = e.target.closest('[data-cagain]');
    if (again && !again.disabled) thPairAgain(Number(again.dataset.cagain));
  });
  document.addEventListener('pointerdown', (e) => {
    if (TH.cpmenu && !e.target.closest('#th-cpmenu, #th-close-btn')) thCloseMenu(false);
    if (TH.pmenu && !TH.pmenu.el.contains(e.target)) thPairMenuClose();
  }, true);
  document.addEventListener('keydown', (e) => {
    if (TH.cpmenu && e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); thCloseMenu(false); }
  }, true);
  // the count's ‹ and › step through the pairs, and a click on the count itself takes the next
  $('th-status-counts').addEventListener('pointerdown', (e) => { if (e.target.closest('[data-stat="close"]')) e.preventDefault(); });
  $('th-status-counts').addEventListener('click', (e) => {
    const stat = e.target.closest('[data-stat="close"]');
    if (!stat || !TH.live) return;
    const step = e.target.closest('[data-cstep]');
    thPairStep(step ? Number(step.dataset.cstep) : 1);
  });
  // the pointer over a card lights its close pairs' lines
  $('th-world').addEventListener('pointerover', thLinksHover);
  $('th-world').addEventListener('pointerleave', () => { if (TH.linkHot && !TH.pmenu) { TH.linkHot = null; thLinksLit(); } });
  $('th-kqpop').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-kqpop').addEventListener('click', (e) => {
    const play = e.target.closest('[data-play]');
    if (play) { thPlayQuote(play.dataset.play, play.dataset.sheet, Number(play.dataset.at)); return; }
    if (e.target.closest('[data-kqgo]')) thKqGo();
  });
  document.addEventListener('pointerdown', (e) => {
    if (TH.kqpop && !e.target.closest('#th-kqpop')) thKqClose();
  }, true);
  stage.addEventListener('wheel', () => { if (TH.kqpop) thKqClose(); }, { passive: true });
  const mapArea = $('th-map-area');
  mapArea.addEventListener('pointerdown', thMapDown);
  mapArea.addEventListener('pointermove', thMapMove);
  mapArea.addEventListener('pointerup', thMapUp);
  mapArea.addEventListener('pointercancel', thMapUp);
  mapArea.addEventListener('lostpointercapture', thMapUp);
  $('th-map').addEventListener('pointerenter', () => { TH.mapOver = true; clearTimeout(thMapSleep); });
  $('th-map').addEventListener('pointerleave', thMapLeave);
  $('th-map').addEventListener('contextmenu', (e) => e.preventDefault());
  if (window.ResizeObserver) new ResizeObserver(() => thMapPlace()).observe($('th-stage'));
  // and drawn again as a sidebar opens or closes, which below 900px lies over it (thMapCovered)
  if (window.MutationObserver) {
    for (const id of ['th-side', 'th-cpanel']) new MutationObserver(() => thMapSchedule()).observe($(id), { attributes: true, attributeFilter: ['hidden'] });
  }

  // the boards: the switcher in the bar opens the menu, and a press anywhere outside it closes it
  $('th-board').onclick = (e) => { if (TH.live) { thVmenu(!TH.vmenu); if (TH.vmenu && e.detail === 0) menuFirst($('th-vmenu')); } };
  document.addEventListener('pointerdown', (e) => {
    if (TH.vmenu && !e.target.closest('#th-vmenu, #th-board')) thVmenu(false);
  }, true);
  $('th-vmenu').addEventListener('pointerdown', (e) => {
    if (e.target.closest('button')) e.preventDefault();  // the canvas keeps the keys
  });
  $('th-vmenu').addEventListener('click', (e) => {
    const to = e.target.closest('[data-switch]');
    if (to) { thSwitch(to.dataset.switch); return; }
    const op = e.target.closest('[data-vop]');
    if (!op || op.disabled) return;
    const what = op.dataset.vop;
    if (what === 'window') thWindow();
    else if (what === 'new' || what === 'new-canvas' || what === 'duplicate') thMakeBoard(what);
    else if (what === 'rename') thVEdit('name');
    else if (what === 'note') thVEdit('note');
    else if (what === 'revision') thVEdit('revision');
    else if (what === 'revision-go') { const box = $('th-vedit-rev'); thVmenu(false); thSaveRevision(box ? box.value : ''); }
    else if (what === 'subs') gtAddSubs();
    else if (what === 'bypart') gtArrangeByParticipant();
    else if (what === 'choose') thChoose();
    else if (what === 'pets-done') thPetsDone(true);
    else if (what === 'pets-reopen') thPetsDone(false);
    else if (what === 'delete') thAskDelete();
    else if (what === 'send-board' && typeof tmbSend === 'function') tmbSend();
  });
  $('th-confirm-cancel').onclick = () => { TH.doomed = null; hide('th-confirm'); };
  $('th-confirm-go').onclick = () => thDeleteGo();
  // the cases: the case's name in the bar opens the switcher, and a press anywhere outside it
  // closes it. A case opens its PETs, and Open as table its board in a tab of its own
  $('th-cases').onclick = (e) => {
    if (!TH.live) return;
    const keys = e.detail === 0;
    Promise.resolve(thCasemenu(!TH.casemenu)).then(() => { if (keys && TH.casemenu) menuFirst($('th-casemenu')); });
  };
  document.addEventListener('pointerdown', (e) => {
    if (TH.casemenu && !e.target.closest('#th-casemenu, #th-cases')) thCasemenu(false);
  }, true);
  $('th-casemenu').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-casemenu').addEventListener('click', (e) => {
    const table = e.target.closest('[data-table]');
    if (table) { thTable(TH.cases[Number(table.dataset.table)]); return; }
    const win = e.target.closest('[data-window]');
    if (win) { thCaseWindow(TH.cases[Number(win.dataset.window)]); return; }
    const to = e.target.closest('[data-case]');
    if (to) thCaseGo(TH.cases[Number(to.dataset.case)]);
  });

  // the Inspector keeps the focus off its own buttons, so g, x, Backspace and Cmd + Z still reach
  // the canvas while it is open
  const panel = $('th-panel');
  panel.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  panel.addEventListener('click', (e) => {
    const play = e.target.closest('[data-play]');
    if (play) { thPlayQuote(play.dataset.play, play.dataset.sheet, Number(play.dataset.at)); return; }
    const pick = e.target.closest('[data-pick]');
    if (pick && TH.panel && TH.panel.kind === 'group') { thPick(TH.panel.id, pick.dataset.pick); return; }
    const names = e.target.closest('[data-names]');
    if (names && names.dataset.names === 'go') { thNamesAsk(); return; }
    if (names && names.dataset.names === 'close') { TH.names = null; TH.namesAsk += 1; thPanelDraw(); return; }
    const named = e.target.closest('[data-name-pick], [data-name-edit]');
    if (named) { thNameApply(Number(named.dataset.namePick ?? named.dataset.nameEdit), named.dataset.nameEdit !== undefined); return; }
    const arrange = e.target.closest('[data-arrange]');
    if (arrange) { thArrangeGroup(arrange.dataset.arrange); return; }
    const colour = e.target.closest('[data-colour]');
    if (colour && TH.panel && TH.panel.kind === 'sticky') { thStickyRecolour(TH.panel.id, colour.dataset.colour); return; }
    const leave = e.target.closest('[data-leave]');
    if (leave && TH.live && !TH.busy) { thLeaveThemes([leave.dataset.leave]); return; }
    // on a thematic analysis project's code: Open in Code list, and Go to the passage of one of its extracts (themesbuild)
    const codeOpen = e.target.closest('[data-codeopen]');
    if (codeOpen) { gtCodeOpen(codeOpen.dataset.codeopen); return; }
    const goPass = e.target.closest('[data-gopass]');
    if (goPass) { thToPassage(goPass.dataset.gopass); return; }
    // the Inspector on a close pair: stack the later under the earlier, or Not the same
    const pstack = e.target.closest('[data-ipstack]');
    if (pstack && TH.panelPair && TH.live && !TH.busy) { thPairStack(TH.panelPair, pstack.dataset.ipstack); return; }
    if (e.target.closest('[data-ipapart]') && TH.panelPair && TH.live && !TH.busy) thPairApart(TH.panelPair);
  });
  // a double-click on the statement in the Inspector opens it for editing in place, by the same
  // path a double-click on its card takes
  panel.addEventListener('dblclick', (e) => {
    const words = e.target.closest('.th-panel-title[data-edit]');
    if (words && TH.panel && TH.panel.kind === 'card') thCardEditOpen(words.dataset.edit, { panel: true });
  });
  // the sidebar's tabs keep the focus off them the same way, and a click shows that tab
  const tabs = $('th-tabs');
  tabs.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  tabs.addEventListener('click', (e) => {
    const tab = e.target.closest('[data-tab]');
    if (tab) thSideOpen(tab.dataset.tab);
  });
  // the tabs about the board keep the focus off their buttons the same way: History's revisions
  const board = $('th-bpanel');
  board.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  board.addEventListener('click', (e) => {
    const view = e.target.closest('[data-rev-view]');
    if (view) { thViewRevision(view.dataset.revView); return; }
    const restore = e.target.closest('[data-rev-restore]');
    if (restore) { thRestoreRevision(restore.dataset.revRestore); return; }
    if (e.target.closest('[data-rev-save]')) { thSaveRevision(($('th-rev-name') || {}).value || ''); return; }
  });
  // the box for a revision's name in the History tab: Enter keeps the revision, Esc lets go, and
  // nothing on this screen or the turn screen hears its keys
  board.addEventListener('keydown', (e) => {
    if (!e.target || e.target.id !== 'th-rev-name') return;
    e.stopPropagation();
    if (e.key === 'Enter') { e.preventDefault(); thSaveRevision(e.target.value); }
    else if (e.key === 'Escape') { e.preventDefault(); e.target.blur(); }
  });
  // the sidebar button in the bar, after Export, opens the sidebar on the tab left showing and
  // closes it again. Like the sidebar's own buttons it leaves the focus on the canvas
  $('th-open-side').addEventListener('pointerdown', (e) => e.preventDefault());
  $('th-open-side').onclick = () => thSideDoor();
  // a theme's note: taking the box opens it, Cmd + Enter keeps it, Esc leaves it as it was, and a
  // click away keeps it, though the panel drawn afresh under it is no click away
  panel.addEventListener('focusin', (e) => { if (e.target && e.target.id === 'th-gnote') thNoteStart(e.target); });
  panel.addEventListener('input', (e) => {
    if (e.target && e.target.id === 'th-gnote' && TH.noting && TH.noting.id === e.target.dataset.note) TH.noting.value = e.target.value;
  });
  panel.addEventListener('focusout', (e) => {
    if (e.target && e.target.id === 'th-gnote' && !TH.noteRedraw) thNoteDone(true);
  });
  // the note's box keeps its own keys, which nothing on this screen or the turn screen hears
  panel.addEventListener('keydown', (e) => {
    if (e.target && e.target.id === 'th-gnote') {
      e.stopPropagation();
      if (e.key === 'Enter' && MOD(e)) { e.preventDefault(); thNoteDone(true); }
      else if (e.key === 'Escape') { e.preventDefault(); thNoteDone(false); }
    }
  });
  // a label's description: taking the box opens it, Enter or a click away keeps it, Esc leaves it as it was,
  // and a line break typed or pasted becomes a space (21 October)
  panel.addEventListener('focusin', (e) => { if (e.target && e.target.id === 'th-gdesc') thDescStart(e.target); });
  // a code's description in the Inspector, kept as the box loses the focus or on Enter, Esc leaving it (themesbuild)
  panel.addEventListener('focusin', (e) => { if (e.target && e.target.id === 'gt-cdesc') gtCodeDescStart(e.target); });
  panel.addEventListener('input', (e) => {
    if (e.target && e.target.id === 'gt-cdesc' && TH.codeDesc && TH.codeDesc.id === e.target.dataset.code) TH.codeDesc.value = e.target.value;
  });
  panel.addEventListener('focusout', (e) => { if (e.target && e.target.id === 'gt-cdesc' && !TH.noteRedraw) gtCodeDescDone(true); });
  panel.addEventListener('keydown', (e) => {
    if (!e.target || e.target.id !== 'gt-cdesc') return;
    e.stopPropagation();
    if (e.isComposing) return;
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); e.target.blur(); }
    else if (e.key === 'Escape') { e.preventDefault(); TH.codeDesc = null; e.target.blur(); thPanelDraw(); }
  });
  panel.addEventListener('input', (e) => {
    if (!e.target || e.target.id !== 'th-gdesc') return;
    if (/[\r\n]/.test(e.target.value)) e.target.value = e.target.value.replace(/[\r\n]+/g, ' ');
    if (TH.describing && TH.describing.id === e.target.dataset.desc) TH.describing.value = e.target.value;
  });
  panel.addEventListener('focusout', (e) => {
    if (e.target && e.target.id === 'th-gdesc' && !TH.noteRedraw) thDescDone(true);
  });
  panel.addEventListener('keydown', (e) => {
    if (!e.target || e.target.id !== 'th-gdesc') return;
    e.stopPropagation();
    if (e.isComposing) return;
    if (e.key === 'Enter') { e.preventDefault(); thDescDone(true); }
    else if (e.key === 'Escape') { e.preventDefault(); thDescDone(false); }
  });
  // a sticky note's words in the Inspector: taking the box opens them, Enter or a click away keeps
  // them, Shift + Enter starts a new line, and Esc leaves them as they were
  panel.addEventListener('focusin', (e) => { if (e.target && e.target.id === 'th-sticky-box') thStickyBoxStart(e.target); });
  panel.addEventListener('input', (e) => {
    if (e.target && e.target.id === 'th-sticky-box' && TH.stickyBox && TH.stickyBox.id === e.target.dataset.stickyBox) {
      TH.stickyBox.value = e.target.value;
    }
  });
  panel.addEventListener('focusout', (e) => {
    if (e.target && e.target.id === 'th-sticky-box' && !TH.noteRedraw) thStickyBoxDone(true);
  });
  panel.addEventListener('keydown', (e) => {
    if (!e.target || e.target.id !== 'th-sticky-box') return;
    e.stopPropagation();
    if (e.isComposing) return;
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); thStickyBoxDone(true); }
    else if (e.key === 'Escape') { e.preventDefault(); thStickyBoxDone(false); }
  });
  // the banner over a revision on view: Restore makes it the board, Back puts the board back
  $('th-viewing').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-viewing-restore').onclick = () => { if (TH.viewing) thRestoreRevision(TH.viewing.rev.id); };
  $('th-viewing-back').onclick = () => thViewEnd();
  // the automatic revisions, every fifteen minutes of work, asked for by the next save
  setInterval(thRevisionTick, 60 * 1000);
  // a board added or changed outside the page, and its line in the corner
  thOutsideBoot();

  // the export's line: Show in Finder, and its cross
  $('th-exported').addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('th-reveal').onclick = () => thReveal();
  $('th-exported-close').onclick = () => thExported(null);
  // the one-time line's link opens the Support card (the family's, shell.js)
  $('th-exported').addEventListener('click', (e) => {
    if (!e.target.closest('.th-once a')) return;
    e.preventDefault();
    if (window.openSupport) window.openSupport();
  });
  $('th-pplay').onclick = () => thPlayToggle();
  for (const ev of ['play', 'pause', 'ended', 'timeupdate', 'loadedmetadata', 'durationchange', 'seeked']) {
    $('th-player').addEventListener(ev, thPlayerDraw);
  }
  const scrub = $('th-pscrub');
  let scrubbing = false;
  scrub.addEventListener('pointerdown', (e) => {
    if (e.button !== 0 || !$('th-player').getAttribute('src')) return;
    e.preventDefault();
    scrubbing = true;
    try { scrub.setPointerCapture(e.pointerId); } catch { /* a nicety */ }
    thScrubTo(e.clientX);
  });
  scrub.addEventListener('pointermove', (e) => { if (scrubbing) thScrubTo(e.clientX); });
  const scrubEnd = (e) => {
    scrubbing = false;
    try { scrub.releasePointerCapture(e.pointerId); } catch { /* already gone */ }
  };
  scrub.addEventListener('pointerup', scrubEnd);
  scrub.addEventListener('pointercancel', scrubEnd);
  window.addEventListener('resize', () => { if (TH.vmenu) thVmenuPlace(); if (TH.xmenu) thXmenu(true); });
  $('th-fit').onclick = () => thFit();
  $('th-zoom-in').onclick = () => thZoomAt(TH.view.z * 1.25);
  $('th-zoom-out').onclick = () => thZoomAt(TH.view.z / 1.25);
  $('th-zoom-level').onclick = () => thZoomAt(1);
  $('th-discard').onclick = () => { if (TH.live) thPile(!TH.pileOpen); };
  $('th-pile-close').onclick = () => thPile(false);
  $('th-pile-body').addEventListener('click', (e) => {
    const back = e.target.closest('[data-restore]');
    if (back) { thPutBack(back.dataset.restore); return; }
    const gone = e.target.closest('[data-remove]');
    if (gone) thRemove(gone.dataset.remove);
  });
  // the small controls on a label: the cross deletes it, the way Backspace does on a label
  // selected, and the grid beside it, Auto-arrange, tidies what it holds
  $('th-world').addEventListener('click', (e) => {
    // the "⋯" on a selected card or a label opens its right-click menu under it
    const more = e.target.closest('.th-more');
    if (more) {
      const hit = more.closest('.th-card, .th-label');
      const at = more.getBoundingClientRect();
      if (hit && TH.live && !TH.busy) thMenuOpen(thItemOf(hit), at.left, at.bottom);
      return;
    }
    // the small cross a selected sticky note carries takes it off the board
    const unstick = e.target.closest('.th-sticky-del');
    if (unstick) { thStickyDelete([unstick.closest('.th-sticky').dataset.sticky]); return; }
    // a colour in a selected note's strip recolours it in one click, one step of undo
    const paper = e.target.closest('.th-strip-dot');
    if (paper) { thStickyRecolour(paper.closest('.th-sticky').dataset.sticky, paper.dataset.colour); return; }
    // a top's count, and Stack again under a stack shown open, show it or stack it again
    const shut = e.target.closest('.th-stackn, .th-restack');
    if (shut) { thStackShow(shut.dataset.stackn || shut.dataset.restack); return; }
    // a PET card's chevron on its count unfolds it in place, or folds it again
    const fold = e.target.closest('.gt-unfold');
    if (fold) { gtUnfold(fold.dataset.unfold); return; }
    const del = e.target.closest('.th-del, .th-arr');
    if (!del) return;
    const label = del.closest('.th-label');
    if (!label) return;
    if (del.classList.contains('th-arr')) thArrangeGroup(label.dataset.group);
    else thDeleteLabels([label.dataset.group]);
  });
  // a page closed with a save still to go sends it on the way out
  window.addEventListener('pagehide', () => {
    if (!TH.live || !TH.dirty || !TH.v) return;
    try {
      fetch(TH.mode === 'gets' ? '/api/gets-save' : '/api/themes-save', { method: 'POST', keepalive: true, headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workbook: TH.path, version: thBody(thLiveV(), TH.meta) }) });
    } catch { /* the page is going either way */ }
  });
  gtBoot();
}

if (typeof document !== 'undefined') themesBoot();
