/* The family's table (22 October 2026, the family codebase's second build): a table whose headings sort and
   whose filters' sidebar ticks, worked out with no page, and the icons an app's own bar carries, for any
   app's screen. Trace's screen draws its claims through here, and Sift's its records since the family
   codebase's third build. It grew from Sift's own table (sift.js), whose columns of its own kinds, its sliders
   and its form stay Sift's, read through a reader of its own (see TB_READ), and the markup and the classes are
   Sift's table's, sf-*, so a table here looks as Sift's does, their styles the family's frame.css, which
   Sift's and Trace's pages link (30 October 2026).

   A column is `{ key, label, kind, cls }`. One of kind `picks` brings its own value and choices: `value(r)`,
   what it sorts by, `pick(r)`, the choices a row stands under in its filter, `choices`, a fixed list of them
   where it has one, `num` when it sorts as a number, and `first`, the way a first press sorts it. Any other
   column sorts by its row's own field of its key, as text, and has no filter. A row is any object, found by
   its id in a Map. No framework, no build step. */

'use strict';

// the AI's mark, the same as every AI control of the app carries
const TB_SPARKS = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 3.2c.95 4.2 2.65 5.9 6.85 6.85-4.2.95-5.9 2.65-6.85 6.85-.95-4.2-2.65-5.9-6.85-6.85C9.35 9.1 11.05 7.4 12 3.2Z"/><path d="M18.4 14.6c.42 1.85 1.17 2.6 3.02 3.02-1.85.42-2.6 1.17-3.02 3.02-.42-1.85-1.17-2.6-3.02-3.02 1.85-.42 2.6-1.17 3.02-3.02Z"/></svg>';
// the bug a bar's Send feedback carries, and its hidden state as the page holds it, so a bar built after the
// server has answered shows it at once
const TB_BUG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M9.3 8.3a2.7 2.7 0 0 1 5.4 0M10.3 6.1 9 4.2M13.7 6.1 15 4.2"/><rect x="7.3" y="8.3" width="9.4" height="12" rx="4.7"/><path d="M12 11.6v8.7"/><path d="M7.3 13.2H4M7.6 17.2l-3 1.6M7.8 10.4 5.2 8.5M16.7 13.2H20M16.4 17.2l3 1.6M16.2 10.4l2.6-1.9"/></svg>';
const tbBugHidden = () => (typeof FEEDBACK !== 'undefined' && FEEDBACK.on ? '' : ' hidden');
// the cog a bar's Settings carries, at the size of a row
const TB_COG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.49.49 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54A.48.48 0 0 0 13.92 2h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.49.49 0 0 0-.59.22L2.73 8.47a.49.49 0 0 0 .12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32a.49.49 0 0 0-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2z"/></svg>';
// the magnifier a bar's Search carries
const TB_GLASS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5.5 5.5"/></svg>';

// words and IDs in natural order, R002 before R010, case and accents set aside
const TB_TEXT = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
// what a row with nothing in a column stands under in its filter
const TB_BLANK = '|none';
// a group of more than four choices shows its first four, then Show more and Show less, and one of
// more than ten has a find box at its head
const TB_FACET_SHOW = 4;
const TB_FACET_FIND = 10;

/* ── the rows: sort and filter ── */

/* a row's value in a column, as it sorts: a column's own value where it brings one, its picks joined, or the
   row's own field */
function tbValue(r, col) {
  if (col.kind === 'picks') return col.value ? col.value(r) : col.pick(r).join(', ');
  return String(r[col.key] || '');
}

const tbEmpty = (v) => v === null || v === undefined || v === '';

/* two values of a column in order, neither empty, a number's by its size and words in natural order */
const tbOrder = (a, b, col) => (col.num ? a - b : TB_TEXT.compare(a, b));

/* two values of a column in order, the empty last whichever way it runs, the rest as `order` puts them */
function tbCmp(a, b, col, dir, order = tbOrder) {
  if (tbEmpty(a) || tbEmpty(b)) return tbEmpty(a) === tbEmpty(b) ? 0 : tbEmpty(a) ? 1 : -1;
  const c = order(a, b, col);
  return dir === 'desc' ? -c : c;
}

/* the rows in the sort's order, its first key first, a tie kept in the order they came, each read as `rd`
   reads it */
function tbSortRows(ids, byId, sort, cols, rd = TB_READ) {
  const keys = (sort || []).map((s) => ({ col: cols.find((c) => c.key === s.key), dir: s.dir === 'desc' ? 'desc' : 'asc' }))
    .filter((s) => s.col);
  const out = ids.filter((id) => byId.has(id));
  if (!keys.length) return out;
  const vals = new Map(out.map((id) => [id, keys.map((s) => rd.value(byId.get(id), s.col))]));
  const place = new Map(out.map((id, i) => [id, i]));
  return out.sort((x, y) => {
    const vx = vals.get(x);
    const vy = vals.get(y);
    for (let i = 0; i < keys.length; i += 1) {
      const c = tbCmp(vx[i], vy[i], keys[i].col, keys[i].dir, rd.order);
      if (c) return c;
    }
    return place.get(x) - place.get(y);
  });
}

/* the sort after a press on a column's heading, the way its kind sorts first, again the other way and a third
   time not at all, Shift adding it as the next key */
function tbSortNext(sort, col, add) {
  const key = col.key;
  const first = col.first || 'asc';
  const turn = (s) => (s.dir === first ? { key, dir: first === 'asc' ? 'desc' : 'asc' } : null);
  const i = sort.findIndex((s) => s.key === key);
  if (add) {
    if (i < 0) return sort.concat([{ key, dir: first }]);
    return sort.map((s, k) => (k === i ? turn(s) : s)).filter(Boolean);
  }
  if (i === 0 && sort.length === 1) return [turn(sort[0])].filter(Boolean);
  return [{ key, dir: first }];
}

/* the ticks held for a column, a list of the values ticked in its group, and none for anything else */
const tbTickList = (f) => (Array.isArray(f) ? f.filter((v) => typeof v === 'string') : []);
const tbTicks = (filters, key) => tbTickList((filters || {})[key]);

/* the choices a row stands under in a column's group: its picks, or its value, or none */
function tbPicked(r, col) {
  if (col.kind === 'picks') return col.pick(r);
  const text = String(tbValue(r, col) || '').trim();
  return [text || TB_BLANK];
}

/* whether a row passes a column's filter: any one ticked, and a filter that holds nothing lets every row through */
function tbPasses(r, col, f, rd = TB_READ) {
  const ticks = tbTickList(f);
  if (!ticks.length) return true;
  return rd.picked(r, col).some((v) => ticks.includes(v));
}

/* How a table reads its rows. A screen that reads its own its own way brings a reader with each of these parts:
   `value(r, col)`, what a row sorts by in a column, `order(a, b, col)`, two values of a column in order,
   neither empty, `picked(r, col)`, the choices a row stands under in a column's group, `on(col, f)`, whether a
   column's filter holds anything, `passes(r, col, f)`, whether a row passes it, and `under(r, g, f)`, what a
   row is counted under in a group. Sift's reads its records at a stage, its sliders among them. */
const TB_READ = {
  value: tbValue,
  order: tbOrder,
  picked: tbPicked,
  on: (col, f) => tbTickList(f).length > 0,
  passes: (r, col, f) => tbPasses(r, col, f),
  under: (r, g) => tbPicked(r, g.col),
};

/* the rows that pass the filters, in the order they came: in each group any choice ticked, and every group at once */
function tbFilterRows(ids, byId, filters, cols, rd = TB_READ) {
  const live = cols.filter((c) => c.kind !== 'id' && rd.on(c, (filters || {})[c.key]));
  return ids.filter((id) => byId.has(id) && live.every((c) => rd.passes(byId.get(id), c, filters[c.key])));
}

/* ── the filters' groups ── */

/* The filters' groups, one for each column that brings its picks, in the columns' order, each under its
   column's name with its own choices where it brings them, else the values the rows hold, the most carried
   first, each in its own words, and any ticked that none now holds. A group whose choices never change is
   `fixed`. */
function tbGroups(rows, cols, filters) {
  const out = [];
  for (const col of cols) {
    if (col.kind !== 'picks') continue;
    const held = new Map();
    for (const r of rows) new Set(tbPicked(r, col)).forEach((v) => held.set(v, (held.get(v) || 0) + 1));
    const byWords = (a, b) => (held.get(b.value) || 0) - (held.get(a.value) || 0) || TB_TEXT.compare(a.label, b.label);
    const fixed = !!col.choices;
    const choices = col.choices ? col.choices.slice() : [...held.keys()].map((v) => ({ value: v, label: v })).sort(byWords);
    const known = new Set(choices.map((c) => c.value));
    if (!fixed) tbTicks(filters, col.key).filter((v) => !known.has(v)).forEach((v) => choices.push({ value: v, label: v }));
    out.push({ key: col.key, label: col.label, about: col.about || '', col, fixed, choices });
  }
  return out;
}

/* each row and each group whose filter alone it might fail, every other group's filter letting it through, so
   what is counted for a group sets its own filter aside */
function tbEachOpen(rows, groups, filters, take, rd = TB_READ) {
  const held = groups.map((g) => (filters || {})[g.key]);
  for (const r of rows) {
    const pass = groups.map((g, i) => rd.passes(r, g.col, held[i]));
    const failing = pass.filter((p) => !p).length;
    groups.forEach((g, i) => { if (failing - (pass[i] ? 0 : 1) === 0) take(r, g, i, held[i]); });
  }
}

/* Each choice's count, by group and value: the rows that every other group's filter lets through and that
   stand under it, its own group's ticks set aside, so it is how many would show were it the one ticked there */
function tbFacetCounts(rows, groups, filters, rd = TB_READ) {
  const out = Object.create(null);
  groups.forEach((g) => { out[g.key] = Object.create(null); });
  tbEachOpen(rows, groups, filters, (r, g, i, f) => {
    const n = out[g.key];
    for (const v of new Set(rd.under(r, g, f))) n[v] = (n[v] || 0) + 1;
  }, rd);
  return out;
}

/* choices by their counts, the most first and the noughts last, a tie kept in the order they came */
function tbByCount(choices, counts) {
  const n = counts || {};
  return choices.map((c, i) => [c, i]).sort((a, b) => (n[b[0].value] || 0) - (n[a[0].value] || 0) || a[1] - b[1]).map((p) => p[0]);
}

/* a group's choices by their counts as the filters stand, the most first, the noughts last, a tie in the order
   the group gives them */
const tbCountOrder = (g, counts) => tbByCount(g.choices, counts);

/* A group's choices in the order the sidebar draws them, as `order` puts them, by their counts unless a screen
   orders its own. With `held`, the values of the group he is ticking in as last drawn, that order stands, so
   no choice moves under the pointer, and a choice new to the group comes after them. */
function tbFacetOrder(g, counts, held, order = tbCountOrder) {
  const out = order(g, counts);
  if (!Array.isArray(held) || !held.length) return out;
  const at = new Map(held.map((v, i) => [v, i]));
  return out.filter((c) => at.has(c.value)).sort((a, b) => at.get(a.value) - at.get(b.value))
    .concat(out.filter((c) => !at.has(c.value)));
}

/* The filters kept in the browser read as a table opens: each group's ticks a list, each once, a tick its
   group no longer offers let go, and a column gone with its group. */
function tbKeptRead(kept, groups) {
  const out = {};
  for (const g of groups) {
    const list = [...new Set(tbTickList((kept || {})[g.key]).filter((v) => g.choices.some((c) => c.value === v)))];
    if (list.length) out[g.key] = list;
  }
  return out;
}

/* ── the table and the filters, drawn ── */

/* the headings, each a button that sorts, its way and its place among the keys marked, each in the class
   `kindOf` gives its column */
const tbHeadKind = (c) => c.cls || 'extra';
function tbTvHeadHtml(cols, sort, kindOf = tbHeadKind) {
  const heads = cols.map((c) => {
    const i = sort.findIndex((s) => s.key === c.key);
    const s = i >= 0 ? sort[i] : null;
    const arrow = s ? `<span class="sf-arrow">${s.dir === 'desc' ? '&#8595;' : '&#8593;'}${sort.length > 1 ? `<sup>${i + 1}</sup>` : ''}</span>` : '';
    const sorted = s ? ` aria-sort="${s.dir === 'desc' ? 'descending' : 'ascending'}"` : '';
    const kind = c.kind === 'id' ? 'id' : kindOf(c);
    return `<th scope="col" class="sf-k-${kind}"${sorted}><button type="button" class="sf-th" data-sort="${escAttr(c.key)}">`
      + `${esc(c.label)}${arrow}</button></th>`;
  }).join('');
  return `<tr class="sf-heads">${heads}</tr>`;
}

/* whether a choice's words answer what is typed in its group's find box: every word typed in them somewhere,
   in any order, case and accents set aside */
function tbFindMatch(words, typed) {
  const fold = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const hay = fold(words);
  return fold(typed).split(/\s+/).filter(Boolean).every((w) => hay.includes(w));
}

/* One choice of a group: its tick box, a database's dot in its colour where it has one, `db`, else a judgement's
   or a decision's, `dec`, its words, a code's with its meaning where it is one, `sub`, and its count at the
   right, a nought in the faint ink. Its words are whole on hover and wrap under themselves, and a choice that
   is a line, `wrap`, wraps whole. A nought is there to be read, not ticked, so its box is off unless it is
   ticked already, which keeps it there to untick. */
function tbChoiceHtml(c, n, ticked) {
  const dot = c.db ? `<span class="sf-dbdot" data-db="${escAttr(c.db)}" aria-hidden="true"></span>`
    : typeof c.dec === 'string' ? `<span class="sf-decdot" data-decision="${escAttr(c.dec)}" aria-hidden="true"></span>` : '';
  const words = c.sub ? `<span class="sf-cw"><span class="mono">${esc(c.label)}</span> ${esc(c.meaning)}</span>`
    : `<span class="sf-cw">${esc(c.label)}</span>`;
  const title = ` title="${escAttr(c.sub && c.meaning ? `${c.label} ${c.meaning}` : c.label)}"`;
  return `<label class="sf-choice${c.sub ? ' sub' : ''}${c.wrap ? ' wrap' : ''}${n ? '' : ' zero'}"${title}><input type="checkbox" data-v="${escAttr(c.value)}"`
    + `${ticked ? ' checked' : ''}${!n && !ticked ? ' disabled' : ''}>${dot}${words}<span class="sf-cn">${n}</span></label>`;
}

/* a group's head: its name, an ⓘ that says its line on hover and on focus where it has one, the button of a
   dialog of its own where it brings one, `tool`, its act and its words, as Sift's Country brings its map, and
   Clear while it holds anything */
const tbGroupHead = (g, i, on) => `<div class="sf-group-top"><h3 class="sf-group-head" id="sf-g-${i}" title="${escAttr(g.label)}">${esc(g.label)}</h3>`
  + `${g.about ? `<span class="sf-about" tabindex="0" role="note" aria-label="${escAttr(g.about)}" data-tip="${escAttr(g.about)}">ⓘ</span>` : ''}`
  + `${g.tool ? `<button type="button" class="quiet sf-group-${escAttr(g.tool.act)}" data-act="${escAttr(g.tool.act)}" aria-haspopup="dialog">${esc(g.tool.label)}</button>` : ''}`
  + `${on ? `<button type="button" class="quiet sf-group-clear" data-act="clear">${esc(t('table.clear'))}</button>` : ''}</div>`;

/* A group of ticks under its column's name: Clear while anything in it is ticked, a find box at the head of
   one of more than ten, its choices, those the find box leaves while it holds words, a code's meaning among
   them, else a long one's first four and every one ticked, then Show more, or Show less once it is whole.
   Its choices that are lines, `line`, stand after them, always whole, each a tick with its count, under the
   heading of the screen's `matchHead`, shown only while one of them holds a row or is ticked. `st` is the
   screen's own state, its `filters`, `facetsFind`, `facetsMore` and `matchHead`. */
function tbGroupHtml(g, counts, i, st) {
  const ticks = new Set(st.filters[g.key] || []);
  const typed = (st.facetsFind || {})[g.key] || '';
  const find = g.choices.length > TB_FACET_FIND || typed
    ? `<input type="search" class="sf-gfind" data-act="find" value="${escAttr(typed)}" placeholder="${escAttr(t('table.find'))}" aria-label="${escAttr(t('table.find_in', { group: g.label }))}"`
      + ' autocomplete="off" spellcheck="false">' : '';
  const found = typed.trim() ? g.choices.filter((c) => ticks.has(c.value) || tbFindMatch(`${c.label} ${c.meaning || ''}`, typed)) : g.choices;
  const main = found.filter((c) => !c.line);
  const whole = !!typed.trim() || st.facetsMore.has(g.key);
  const shown = whole ? main : main.filter((c, k) => k < TB_FACET_SHOW || ticks.has(c.value));
  const more = typed.trim() ? '' : st.facetsMore.has(g.key) ? t('table.show_less') : shown.length < main.length ? t('table.show_more') : '';
  const lines = found.filter((c) => c.line);
  const head = (st.matchHead || []).map((t) => `<span>${esc(t)}</span>`).join('');
  const below = lines.some((c) => counts[c.value] || ticks.has(c.value))
    ? `<div class="sf-lines" role="group" aria-labelledby="sf-g-${i}-lines"><p class="sf-lines-head" id="sf-g-${i}-lines">${head}</p>`
      + `${lines.map((c) => tbChoiceHtml(c, counts[c.value] || 0, ticks.has(c.value))).join('')}</div>` : '';
  return `<div class="sf-group" role="group" aria-labelledby="sf-g-${i}" data-g="${escAttr(g.key)}">${tbGroupHead(g, i, ticks.size > 0)}${find}`
    + shown.map((c) => tbChoiceHtml(c, counts[c.value] || 0, ticks.has(c.value))).join('')
    + `${more ? `<button type="button" class="quiet sf-group-more" data-act="more">${esc(more)}</button>` : ''}${below}</div>`;
}

/* ── small things a screen needs ── */

/* a day as the screen says it, 12 October 2026 in English (through Intl since i18ncore, 28 October 2026), or as
   it stands when it is not a date */
function tbDayWords(iso) {
  const day = tDay(iso);
  return day ? tDate(day, { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }) : String(iso || '');
}

/* a file chosen or dropped, as base64 for the server */
function tbBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',', 2)[1] || '');
    reader.onerror = () => reject(new Error(t('table.file_unreadable')));
    reader.readAsDataURL(file);
  });
}
