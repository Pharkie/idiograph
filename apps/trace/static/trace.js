/* Trace (15 October), the third part of Idiograph beside Sift and Distil, grown from Sift's Check
   references of 14 October: each claim a manuscript makes of a reference, held by him against the
   reference itself. One row a claim, the sentence that cites the reference, with the sentence before it
   where the claim leans on it, its reference, his judgement, the reference's PDF, the section and his
   note, then a row for each citation no reference answers and each reference never cited. The family's
   table (table.js), its headings that sort and its filters, draws it. No framework, no build step.

   The server reads the manuscript afresh every time through trace_claims.py and never writes it. His
   judgement of a claim is Supports, Y, in the screening's green, Question, Q, in its amber, or Doesn't
   support, N, in its red, none until he gives one. Each goes to the project's own log at once with his
   note, and Undo takes back the last of them. A row opens its claim: the sentence whole under its
   section's heading, its reference with how many of its claims he has judged, the PDF beside it where
   Trace finds one, and his note. With the app's AI switch on, AI find passages asks the app's AI where
   the PDF supports each claim of a reference, for this reference or the rows shown, and shows only the
   passages Trace found in the PDF's own text, each with its page. It never judges a claim, which is his
   alone. */

'use strict';

const TR = {
  folder: null,      // the project open, its folder as the server names it back
  project: null,     // its name, for the title bar
  docs: [],          // its manuscripts
  list: null,        // its reference list, or null
  choose: false,     // the Mac's file dialog is there
  doc: '',           // the manuscript open, by the name its files take, or empty for the list alone
  name: '',
  path: '',
  source: '',        // where its references come from, the manuscript's own list or the project's
  rows: [],          // its claims in its order, then each reference never cited
  byId: new Map(),
  sections: [],
  ids: [],           // the rows the table shows, filtered and sorted
  at: 0,
  view: 'table',     // table, or record, a row opened from it
  sort: [],
  filters: {},
  facetsMore: new Set(),
  facetsFind: {},
  matchHead: [],
  facetsHtml: '',
  tvShape: '',
  tvRows: new Map(),
  undo: null,
  aiMaster: false,
  modelName: '',
  asking: null,      // the reference whose passages are being asked for
  batch: null,       // AI find passages for the rows shown under way, { done, of, stop }
  chain: Promise.resolve(),
  noteFor: null,
  frameFor: null,
  pageAt: null,      // the page of the PDF the pane was sent to by a passage's page
  askDone: null,
};

const TR_NAME = 'Trace';
const TR_DOC_KEY = 'idiograph-trace-doc';
const TR_FILTER_KEY = 'idiograph-trace-filters';
const TR_FACETS_KEY = 'idiograph-trace-facets';
// his three judgements, each in a screening decision's colour, the keys as Sift's decisions take them
// Trace's words from the catalogue, apps/trace/static/i18n/en/trace.json (i18nleft, 1 November 2026)
const TR_WORDS = { Y: t('trace.judge.y'), Q: t('trace.judge.q'), N: t('trace.judge.n') };
const TR_DEC = { Y: 'include', Q: 'maybe', N: 'exclude' };
const TR_KEYS = { y: 'Y', q: 'Q', n: 'N' };
const TR_PASS = { none: t('trace.pass.none'), failed: t('trace.pass.failed') };
const TR_NEVER = t('trace.never');
// the typed path's placeholder off a Mac, in the app's own nouns, a Markdown or Word manuscript or a CSV, RIS
// or BibTeX reference list (15 October, later)
const TR_PATH_SAID = t('trace.path_said');
const TR_NO_CLAIMS = t('trace.no_claims');
const TR_NOTHING = t('trace.nothing');
const trShown = () => !!$('trace') && !$('trace').hidden;
const trRow = () => TR.byId.get(TR.ids[TR.at]) || null;
const trAiReady = () => !!TR.aiMaster;
const trClaim = (r) => !!r && r.kind === 'claim';

/* ── the table's columns, as the family's table takes them (see tbValue, tbPicked and tbGroups in table.js) ── */

/* Claim, Reference, Judgement, PDF, Section and Note, and two the filters alone take, Judged and
   Citations. Below about 600px the table keeps the claim, its judgement and its PDF, the reference
   under the claim, and Section and Note stand on the record alone. */
const TR_RANK = { Y: 1, Q: 2, N: 3 };
const TR_COLS = [
  { key: 'sentence', label: t('trace.col.claim'), kind: 'text', cls: 'title' },
  { key: 'short', label: t('trace.col.reference'), kind: 'picks', cls: 'ref', value: (r) => r.short || '',
    pick: (r) => (r.kind === 'missing' ? [] : [r.short]) },
  { key: 'judged', label: t('trace.col.judgement'), kind: 'picks', cls: 'dec', value: (r) => (trClaim(r) && r.judged ? TR_RANK[r.judged] : null),
    pick: (r) => (trClaim(r) && r.judged ? [r.judged] : []),
    choices: ['Y', 'Q', 'N'].map((v) => ({ value: v, label: TR_WORDS[v], dec: TR_DEC[v] })) },
  { key: 'haspdf', label: t('trace.col.pdf'), kind: 'picks', num: true, first: 'desc', cls: 'pdf', value: (r) => (r.kind === 'missing' ? null : r.pdf ? 1 : 0),
    pick: (r) => (r.kind === 'missing' ? [] : [r.pdf ? 'yes' : 'no']),
    choices: [{ value: 'yes', label: t('trace.pdf.yes') }, { value: 'no', label: t('trace.pdf.no') }] },
  { key: 'section', label: t('trace.col.section'), kind: 'picks', cls: 'sections', value: (r) => r.section || '', pick: (r) => (r.section ? [r.section] : []) },
  { key: 'note', label: t('trace.col.note'), kind: 'text', cls: 'note' },
];
const TR_ONLY_FILTERS = [
  { key: 'isjudged', label: t('trace.col.judged'), kind: 'picks', pick: (r) => (trClaim(r) ? [r.judged ? 'yes' : 'no'] : []),
    choices: [{ value: 'yes', label: t('trace.judged.yes') }, { value: 'no', label: t('trace.judged.no') }] },
  { key: 'kind', label: t('trace.col.citations'), kind: 'picks', pick: (r) => [r.kind],
    choices: [{ value: 'claim', label: t('trace.kind.claim') }, { value: 'missing', label: t('trace.kind.missing') }, { value: 'uncited', label: t('trace.kind.uncited') }] },
];
// the filters' groups in the order he reaches for them, Judged first
const TR_GROUPS = ['isjudged', 'judged', 'haspdf', 'kind', 'section', 'short'];
const trGroupCols = () => TR_GROUPS.map((k) => TR_COLS.concat(TR_ONLY_FILTERS).find((c) => c.key === k));
const trBase = () => TR.rows.map((r) => r.key);

/* the rows the filters let through, in the sort's order, the manuscript's with no sort */
function trApply(keep) {
  const passed = tbFilterRows(trBase(), TR.byId, TR.filters, trGroupCols());
  TR.ids = tbSortRows(passed, TR.byId, TR.sort, TR_COLS);
  const at = keep ? TR.ids.indexOf(keep) : -1;
  TR.at = at >= 0 ? at : Math.min(TR.at, Math.max(0, TR.ids.length - 1));
}

/* the filters' groups, their counts as the filters stand and their choices by their counts, as the family's
   table orders them */
function trFacetsData() {
  const groups = tbGroups(TR.rows, trGroupCols(), TR.filters);
  const counts = tbFacetCounts(TR.rows, groups, TR.filters);
  groups.forEach((g) => { g.choices = tbFacetOrder(g, counts[g.key], null); });
  return { groups, counts };
}

/* ── the cells ── */

/* a judgement's pill in its own colour, and nothing at all until he gives one. A citation with no reference
   has nothing to judge, so its pill is the grey of Sift's To screen, never a judgement's colour, and a
   reference the manuscript never cites wears the same grey pill, Never cited, in the Reference column (15
   October, later) */
const trPill = (judged) => (judged ? `<span class="sf-pill" data-decision="${TR_DEC[judged]}">${esc(TR_WORDS[judged])}</span>` : '');
const trMissing = `<span class="sf-pill" data-decision="">${esc(t('trace.kind.missing'))}</span>`;
const trUncited = `<span class="sf-pill" data-decision="">${esc(t('trace.kind.uncited'))}</span>`;

/* the reference's label, after the pill where a row has one, on a line of its own rather than broken beside
   the pill, so Zeller et al., 2015 reads whole */
function trRef(r) {
  const pill = r.kind === 'missing' ? trMissing : r.kind === 'uncited' && TR.doc ? trUncited : '';
  return pill ? `${pill} <span class="tr-short">${esc(r.short)}</span>` : esc(r.short);
}

function trCell(r, c) {
  if (c.key === 'sentence') {
    if (r.kind === 'uncited') return `<td class="sf-c-title tr-c-claim"><span class="tr-c-under">${trRef(r)}</span></td>`;
    const before = r.before ? `<span class="tr-before">${esc(r.before)}</span> ` : '';
    const under = `<span class="tr-c-under">${trRef(r)}</span>`;
    return `<td class="sf-c-title tr-c-claim">${before}${esc(r.sentence)}${under}</td>`;
  }
  if (c.key === 'short') {
    return `<td class="tr-c-ref"${r.reference ? ` title="${escAttr(r.reference)}"` : ''}>${trRef(r)}</td>`;
  }
  if (c.key === 'section') return `<td class="tr-c-sec">${r.section ? `<span class="sf-cat">${esc(r.section)}</span>` : ''}</td>`;
  if (c.key === 'haspdf') return `<td class="sf-c-pdf">${r.pdf ? `<span class="sf-pill sf-pdfpill">${esc(t('trace.pdf.yes'))}</span>` : ''}</td>`;
  if (c.key === 'judged') return `<td class="sf-c-dec">${trClaim(r) ? trPill(r.judged) : ''}</td>`;
  return `<td class="sf-c-long tr-c-note">${esc(r.note || '')}</td>`;
}

const trRowHtml = (r) => `<tr data-rec="${escAttr(r.key)}"${r.kind !== 'claim' ? ` class="tr-${r.kind}"` : ''}>${TR_COLS.map((c) => trCell(r, c)).join('')}</tr>`;

/* the forms a claim cites its reference in, on its record over the reference, each form that is no more
   than the reference's author and year left out, since the full reference under it says that, so a page or
   every author's name still shows and the record says the author and year once. A citation with no
   reference keeps its form, having no reference under it */
const trForms = (r) => (r.as || []).filter((f) => r.kind === 'missing' || f !== r.short).join('; ');

/* ── opening ── */

/* A project from its card on the home screen: its manuscripts asked of the server, the one this browser
   left it on opened, else the first, else its reference list alone, and with neither the way to choose a
   file. */
async function trOpen(folder, gone) {
  let got;
  try {
    got = await api('/api/trace', { op: 'list', folder });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    if (gone) gone();
    return;
  }
  ['library', 'work', 'themes', 'sift', 'sift-search'].forEach((id) => { if ($(id)) $(id).hidden = true; });
  $('trace').hidden = false;
  TR.folder = folder;
  TR.project = got.project || null;
  TR.docs = got.docs || [];
  TR.list = got.list || null;
  // the Mac's file dialog, or in Idiograph's own window the system's own on either (17 October)
  TR.choose = !!got.choose || (typeof windowPicks === 'function' && windowPicks());
  TR.view = 'table';
  trHead();
  const kept = trKept()[folder];
  const doc = (TR.docs.find((d) => d.doc === kept) || TR.docs[0] || {}).doc || '';
  if (!doc && !TR.list) { trEmpty(); return; }
  await trRead(doc);
  window.scrollTo(0, 0);
}

function trKept() {
  try {
    const held = JSON.parse(localStorage.getItem(TR_DOC_KEY) || '{}');
    return held && typeof held === 'object' ? held : {};
  } catch { return {}; }
}

function trKeep(key, value) {
  try {
    const held = JSON.parse(localStorage.getItem(key) || '{}') || {};
    held[TR.folder] = value;
    localStorage.setItem(key, JSON.stringify(held));
  } catch { /* private window */ }
}

/* the title bar: the way back, Trace's mark and the project's name, never the part's word (15 October,
   later) */
function trHead() {
  const name = TR.project ? TR.project.name : '';
  bandNameSet('tr-name', name);
}

/* nothing added yet: the screen holds the way to choose a file alone */
function trEmpty() {
  TR.doc = '';
  TR.rows = [];
  TR.byId = new Map();
  TR.ids = [];
  $('tr-empty').hidden = false;
  $('tr-tv').hidden = true;
  $('tr-body').hidden = true;
  $('tr-top').hidden = true;
  $('tr-foot').hidden = true;
  $('tr-alone').hidden = true;
  trDocsDraw();
}

/* A manuscript read afresh, or with none the reference list alone, its rows taken, the filters this
   browser kept for it put back where its rows still offer them, and the table drawn on the row it was on. */
async function trRead(doc, keepAt) {
  let data;
  try {
    data = await api('/api/trace', { op: 'read', folder: TR.folder, doc });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  const same = TR.doc === data.doc && TR.rows.length > 0;
  trTake(data);
  if (!same) {
    const kept = trKeptFilters();
    TR.filters = kept ? tbKeptRead(kept, trFacetsData().groups) : {};
    TR.sort = [];
    TR.facetsMore = new Set();
    TR.facetsFind = {};
    TR.at = 0;
    TR.view = 'table';
    TR.facetsHtml = '';
    TR.tvShape = '';
  }
  trKeep(TR_DOC_KEY, TR.doc);
  $('tr-empty').hidden = true;
  $('tr-top').hidden = false;
  $('tr-foot').hidden = false;
  trFacetsOpen(trFacetsStored());
  trApply(keepAt || null);
  trDraw();
}

function trTake(data) {
  TR.doc = data.doc || '';
  TR.name = data.name || '';
  TR.path = data.path || '';
  TR.source = data.source || '';
  TR.docs = data.docs || TR.docs;
  TR.list = data.list || null;
  TR.project = data.project || TR.project;
  TR.rows = data.rows || [];
  TR.byId = new Map(TR.rows.map((r) => [r.key, r]));
  TR.sections = data.sections || [];
  TR.undo = data.undo || null;
  TR.aiMaster = !!(data.config && data.config.ai_suggest);
  TR.modelName = data.model_name || '';
}

/* the manuscripts of the project, the one open chosen, the reference list where the claims take their
   references from it, and Add file */
function trDocsDraw() {
  const pick = $('tr-doc');
  pick.innerHTML = TR.docs.map((d) => `<option value="${escAttr(d.doc)}"${d.doc === TR.doc ? ' selected' : ''}>${esc(d.name)}</option>`).join('');
  pick.hidden = TR.docs.length < 1;
  pick.title = (TR.docs.find((d) => d.doc === TR.doc) || {}).path || '';
  const from = TR.list && (!TR.doc || TR.source === 'list');
  $('tr-list').hidden = !from;
  $('tr-list').textContent = from ? t('trace.list_from', { name: TR.list.name }) : '';
  $('tr-list').title = from ? TR.list.path : '';
  // the typed path off a Mac alone, over the table and on an empty project, the Mac's file dialog standing in
  $('tr-path-line').hidden = TR.choose;
  $('tr-path-empty-line').hidden = TR.choose;
  // a reference list alone, with no manuscript yet, said once on the screen
  $('tr-alone').hidden = !!TR.doc || !TR.list;
}

/* Add file: the path typed beside it, else the Mac's file dialog, which off a Mac a path stands in for. A
   manuscript opens, and a reference list opens the manuscript it gives its references to, or itself. */
async function trAddFile(fromEmpty) {
  const typed = $(fromEmpty ? 'tr-path-empty' : 'tr-path');
  let path = typed && !typed.closest('[hidden]') ? typed.value.trim() : '';
  if (!TR.choose && !path) { if (typed) typed.focus(); return; }
  if (!path && typeof windowPicks === 'function' && windowPicks()) {
    path = String((await window.idiographPick(PICK_SAYS.traceFile, true)) || '');
    if (!path) return;
  }
  let got;
  try {
    got = await api('/api/trace', { op: 'add', folder: TR.folder, path });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  if (!got.chosen) return;
  TR.docs = got.docs || TR.docs;
  TR.list = got.list || TR.list;
  if (typed) typed.value = '';
  TR.rows = [];
  await trRead(got.doc || TR.doc || '');
}

/* ── drawing ── */

function trDraw() {
  const table = TR.view === 'table';
  $('tr-tv').hidden = !table;
  $('tr-body').hidden = table;
  $('tr-top').dataset.view = TR.view;
  $('tr-top').hidden = !table;
  bandTableDraw('tr-name');
  trDocsDraw();
  trBar();
  if (table) trTvDraw();
  else trRecordDraw();
  trAiDraw();
}

/* the foot: how many rows show, or on a record where it stands among them, Undo while there is something
   to take back, and how many claims stand at each judgement */
function trBar() {
  const claims = TR.rows.filter(trClaim);
  const n = (v) => claims.filter((r) => r.judged === v).length;
  $('tr-count').innerHTML = TR.view === 'table' ? t('trace.count_html', { shown: TR.ids.length, all: TR.rows.length })
    : t('trace.count_html', { shown: TR.ids.length ? TR.at + 1 : 0, all: TR.ids.length });
  $('tr-tally').innerHTML = TR.doc ? ['Y', 'Q', 'N'].map((v) => `<span class="sf-pill" data-decision="${TR_DEC[v]}">${esc(t('trace.tally', { judgement: TR_WORDS[v], count: n(v) }))}</span>`).join('') : '';
  const u = TR.undo;
  $('tr-undo').hidden = !u;
  $('tr-undo').title = u ? t('trace.undo_tip', { ref: (TR.byId.get(u.claim) || {}).short || u.ref || '' }) : '';
  trFacetsMark();
}

/* the table: the headings as the family's table draws them, the body built again when the rows changed, else each
   row drawn again alone, and the chosen row marked */
function trTvDraw() {
  $('tr-thead').innerHTML = tbTvHeadHtml(TR_COLS, TR.sort);
  const shape = `${TR.doc}\n${TR.ids.join('\n')}`;
  const body = $('tr-tbody');
  if (shape !== TR.tvShape) {
    TR.tvRows = new Map();
    const html = TR.ids.map((id) => trRowHtml(TR.byId.get(id)));
    body.innerHTML = html.join('');
    [...body.children].forEach((tr, k) => TR.tvRows.set(tr.dataset.rec, { el: tr, html: html[k] }));
    TR.tvShape = shape;
  } else {
    for (const id of TR.ids) {
      const held = TR.tvRows.get(id);
      const h = trRowHtml(TR.byId.get(id));
      if (!held || held.html === h) continue;
      const shell = document.createElement('tbody');
      shell.innerHTML = h;
      const tr = shell.firstElementChild;
      held.el.replaceWith(tr);
      TR.tvRows.set(id, { el: tr, html: h });
    }
  }
  const on = TR.ids[TR.at];
  TR.tvRows.forEach((held, id) => {
    held.el.classList.toggle('on', id === on);
    if (id === on) held.el.setAttribute('aria-selected', 'true');
    else held.el.removeAttribute('aria-selected');
  });
  $('tr-none').hidden = TR.ids.length > 0;
  trFacetsDraw();
}

function trReveal() {
  const held = TR.tvRows.get(TR.ids[TR.at]);
  if (!held) return;
  const box = $('tr-tv-box');
  const top = held.el.offsetTop;
  const head = $('tr-thead').offsetHeight;
  if (top - head < box.scrollTop) box.scrollTop = Math.max(0, top - head);
  else if (top + held.el.offsetHeight > box.scrollTop + box.clientHeight) box.scrollTop = top + held.el.offsetHeight - box.clientHeight;
}

/* ── the filters, the family's table's groups drawn in this screen's sidebar ── */

function trFacetsDraw() {
  if ($('tr-facets').hidden) return;
  const { groups, counts } = trFacetsData();
  const html = groups.map((g, i) => tbGroupHtml(g, counts[g.key] || {}, `tr-${i}`, TR)).join('');
  if (html === TR.facetsHtml) return;
  const box = $('tr-groups');
  const was = document.activeElement;
  const group = was && box.contains(was) ? was.closest('[data-g]') : null;
  const keep = group ? [group.dataset.g, was.dataset.v || '', was.dataset.act || ''] : null;
  box.innerHTML = html;
  TR.facetsHtml = html;
  if (!keep) return;
  const holder = [...box.querySelectorAll('[data-g]')].find((el) => el.dataset.g === keep[0]);
  const back = holder && [...holder.querySelectorAll('input, button')].find((el) => (el.dataset.v || '') === keep[1] && (el.dataset.act || '') === keep[2]);
  if (back) back.focus();
}

/* the toggle over the sidebar names how many groups are set, and Clear all stands beside it while any is */
function trFacetsMark() {
  const n = Object.keys(TR.filters).length + Object.values(TR.facetsFind).filter((v) => String(v || '').trim()).length;
  $('tr-facets-word').textContent = n ? t('trace.filters_n', { count: n }) : t('trace.filters');
  $('tr-facets-toggle').dataset.count = String(n > 0);
  $('tr-facets-toggle').setAttribute('aria-pressed', String(!$('tr-facets').hidden));
  $('tr-facets-clear').hidden = !n || TR.view !== 'table';
}

function trFacetsStored() {
  try {
    const held = localStorage.getItem(TR_FACETS_KEY);
    if (held === 'open') return true;
    if (held === 'shut') return false;
  } catch { /* private window */ }
  try { return !window.matchMedia('(max-width: 899px)').matches; } catch { return true; }
}

function trFacetsOpen(open, keep = false) {
  $('tr-facets').hidden = !open;
  if (keep) { try { localStorage.setItem(TR_FACETS_KEY, open ? 'open' : 'shut'); } catch { /* private window */ } }
  TR.facetsHtml = '';
  trFacetsMark();
  if (open) trFacetsDraw();
}

/* the filters this browser kept for the manuscript open, or null */
function trKeptFilters() {
  try {
    const held = JSON.parse(localStorage.getItem(TR_FILTER_KEY) || '{}') || {};
    return held[`${TR.folder}\n${TR.doc}`] || null;
  } catch { return null; }
}

/* the filters kept in this browser for the manuscript, at once after each change */
function trFiltersKeep() {
  try {
    const held = JSON.parse(localStorage.getItem(TR_FILTER_KEY) || '{}') || {};
    held[`${TR.folder}\n${TR.doc}`] = TR.filters;
    localStorage.setItem(TR_FILTER_KEY, JSON.stringify(held));
  } catch { /* private window */ }
}

function trRefilter() {
  trApply(trRow() ? trRow().key : null);
  $('tr-tv-box').scrollTop = 0;
  trDraw();
  trFiltersKeep();
}

function trTick(key, value, on) {
  const now = new Set(TR.filters[key] || []);
  if (on) now.add(value);
  else now.delete(value);
  if (now.size) TR.filters[key] = [...now];
  else delete TR.filters[key];
  trRefilter();
}

function trClear(key) {
  if (key) { delete TR.filters[key]; delete TR.facetsFind[key]; } else { TR.filters = {}; TR.facetsFind = {}; }
  trRefilter();
}

/* ── the record ── */

function trOpenRecord() {
  if (!trRow()) return;
  TR.view = 'record';
  trDraw();
  $('tr-record').scrollTop = 0;
}

function trToTable() {
  trNoteSave();
  TR.view = 'table';
  TR.frameFor = null;
  $('tr-frame').removeAttribute('src');
  trDraw();
  trReveal();
}

function trMove(delta) {
  if (!TR.ids.length) return;
  trNoteSave();
  TR.pageAt = null;
  TR.at = Math.max(0, Math.min(TR.ids.length - 1, TR.at + delta));
  trDraw();
  if (TR.view === 'table') trReveal();
}

/* the reference's PDF for the pane, fitted to its width with no thumbnails, at a passage's page where one
   sent it there */
const trPdfUrl = (r, page) => `/trace/pdf?folder=${encodeURIComponent(TR.folder)}&doc=${encodeURIComponent(TR.doc)}&ref=${encodeURIComponent(r.ref)}`
  + `${page ? `&page=${page}` : ''}#${page ? `page=${page}&` : ''}view=FitH&navpanes=0`;

/* One claim: his judgement and the day he gave it, nothing until he gives one, the section, the sentence
   before it where the claim leans on it, the sentence, the forms it cites the reference in, then the
   reference, its DOI, Open PDF and Show in Zotero, how many of its claims he has judged, and with the AI
   switch on the passage the AI found for this claim, then Supports, Question and Doesn't support and his
   note, and the PDF beside it, or No PDF and Add PDF. A citation with no reference shows its sentence alone,
   and a reference never cited its reference and its PDF. */
function trRecordDraw() {
  const r = trRow();
  $('tr-none-rec').hidden = !!r;
  $('tr-card').hidden = !r;
  if (!r) return;
  const claim = trClaim(r);
  const missing = r.kind === 'missing';
  $('tr-pill').hidden = !(claim && r.judged) && !missing;
  $('tr-pill').dataset.decision = missing ? '' : TR_DEC[r.judged] || '';
  $('tr-pill').textContent = missing ? t('trace.kind.missing') : TR_WORDS[r.judged] || '';
  $('tr-set').textContent = claim && r.judged && r.set ? t('trace.judged_on', { day: tbDayWords(r.set) }) : '';
  $('tr-meta').hidden = $('tr-pill').hidden;
  $('tr-sec').textContent = r.section || '';
  $('tr-before').textContent = r.before || '';
  $('tr-before').hidden = !r.before;
  $('tr-said').textContent = r.kind === 'uncited' ? (TR.doc ? TR_NEVER : '') : r.sentence;
  $('tr-said').classList.toggle('sf-blank', r.kind === 'uncited');
  $('tr-said').hidden = r.kind === 'uncited' && !TR.doc;
  $('tr-as').textContent = trForms(r);
  // the reference, its links and how many of its claims he has judged
  $('tr-refbox').hidden = missing;
  $('tr-ref').textContent = r.reference || '';
  const links = [];
  if (r.doi) links.push(`<a href="https://doi.org/${escAttr(r.doi)}" target="_blank" rel="noopener noreferrer">${esc(r.doi)}</a>`);
  if (r.pdf) links.push(`<button type="button" class="ghost small" id="tr-open">${esc(t('trace.open_pdf'))}</button>`);
  if (r.zotero) links.push(`<a href="${escAttr(r.zotero)}">${esc(t('trace.show_zotero'))}</a>`);
  $('tr-links').innerHTML = links.join('');
  $('tr-links').hidden = !links.length;
  $('tr-judged').textContent = claim ? t('trace.judged_of', { judged: r.ref_judged, n: r.ref_claims }) : '';
  // the AI's passage for this claim, with the AI switch on
  const found = claim && trAiReady() && r.passages ? r.passages : null;
  $('tr-pass').hidden = !found;
  if (found) {
    $('tr-pass-said').textContent = t('trace.pass.said', { model: found.model, day: tbDayWords(String(found.asked || '').slice(0, 10)) });
    $('tr-pass-body').innerHTML = trPassageHtml(r.passage);
  }
  $('tr-acts').hidden = !claim;
  $('tr-note').hidden = !claim;
  $('tr-acts').querySelectorAll('[data-judge]').forEach((b) => b.setAttribute('aria-pressed', String(claim && r.judged === b.dataset.judge)));
  if (TR.noteFor !== r.key) {
    $('tr-note').value = r.note || '';
    TR.noteFor = r.key;
  }
  // the PDF beside the record, the pane shown at the page a passage's page sent it to
  $('tr-pdf').hidden = missing;
  $('tr-nopdf').hidden = r.pdf || missing;
  $('tr-frame').hidden = !r.pdf;
  const want = r.pdf ? trPdfUrl(r, TR.pageAt) : null;
  if (r.pdf && TR.frameFor !== want) { $('tr-frame').src = want; TR.frameFor = want; }
  if (!r.pdf) { $('tr-frame').removeAttribute('src'); TR.frameFor = null; }
}

/* where the AI's passages found support for a claim: the passage in the PDF's own words with its page,
   which shows that page in the pane, or that it found none, or that its passage was not in the PDF */
function trPassageHtml(p) {
  if (p && p.passage) {
    return `<button type="button" class="quiet tr-page" data-page="${Number(p.page) || 1}">${esc(t('trace.pass.page', { page: Number(p.page) || 1 }))}</button>`
      + `<blockquote class="tr-passage">${esc(p.passage)}</blockquote>`;
  }
  return `<p class="tr-pass-none">${p && p.unverified ? TR_PASS.failed : TR_PASS.none}</p>`;
}

/* ── his acts ── */

function trQueue(work) {
  TR.chain = TR.chain.then(work).catch((err) => say(needsRestart(err) ? RESTART_LINE : err.message, 9000));
  return TR.chain;
}

/* an act's answer taken into its row, the judgement, the day and the note, its reference's passages into
   every claim of that reference, how many of the reference's claims he has judged, and what Undo would take
   back */
function trLand(got) {
  if (!got) return;
  if ('undo' in got) TR.undo = got.undo;
  const r = got.claim ? TR.byId.get(got.claim) : null;
  if (r && got.state) {
    r.judged = got.state.judged || '';
    r.set = got.state.set || '';
    r.note = got.state.note || '';
    if (TR.noteFor === r.key && document.activeElement !== $('tr-note')) $('tr-note').value = r.note;
  }
  const ref = got.ref || (r && r.ref);
  if (!ref) return;
  const mine = TR.rows.filter((x) => trClaim(x) && x.ref === ref);
  if ('passages' in got && got.passages !== undefined) {
    const p = got.passages;
    mine.forEach((x) => {
      x.passages = p ? { model: p.model, asked: p.asked, found: p.found, of: p.of } : null;
      x.passage = p ? (p.claims || []).find((c) => c.claim === x.key || (!c.claim && c.said === x.sentence)) || null : null;
    });
  }
  const judged = mine.filter((x) => x.judged).length;
  mine.forEach((x) => { x.ref_judged = judged; });
}

/* Y, Q or N on the row or claim in front of him, drawn at once and sent, the server's answer drawn over it */
function trJudge(value) {
  const r = trRow();
  if (!r) return;
  if (r.kind === 'missing') { say(TR_NOTHING); return; }
  if (!trClaim(r)) return;
  trNoteSave();
  const now = new Date();
  r.judged = value;
  r.set = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  trDraw();
  const folder = TR.folder;
  const doc = TR.doc;
  trQueue(async () => {
    const got = await api('/api/trace', { op: 'judge', folder, doc, claim: r.key, value });
    if (TR.folder === folder && TR.doc === doc) { trLand(got); trDraw(); }
  });
}

/* his note, kept as it is left */
function trNoteSave() {
  const r = TR.noteFor ? TR.byId.get(TR.noteFor) : null;
  if (!r || !trClaim(r) || $('tr-note').hidden) return;
  const note = $('tr-note').value;
  if (note === (r.note || '')) return;
  r.note = note;
  const folder = TR.folder;
  const doc = TR.doc;
  trQueue(async () => {
    const got = await api('/api/trace', { op: 'note', folder, doc, claim: r.key, note });
    if (TR.folder === folder && TR.doc === doc) { trLand(got); trBar(); if (TR.view === 'table') trTvDraw(); }
  });
}

function trUndo() {
  trNoteSave();
  const folder = TR.folder;
  const doc = TR.doc;
  trQueue(async () => {
    if (!TR.undo) return;
    const got = await api('/api/trace', { op: 'undo', folder, doc });
    if (TR.folder !== folder || TR.doc !== doc) return;
    trLand(got);
    if (got.claim && TR.noteFor === got.claim) $('tr-note').value = (TR.byId.get(got.claim) || {}).note || '';
    trDraw();
  });
}

async function trOpenPdf() {
  const r = trRow();
  if (!r || !r.pdf) return;
  try {
    await api('/api/trace', { op: 'open', folder: TR.folder, doc: TR.doc, ref: r.ref });
  } catch (err) { say(err.message, 9000); }
}

/* Add PDF: one chosen, kept in the project's pdfs/ under the reference's name, never over one there, and
   the manuscript read again so every row of that reference finds it */
async function trAddPdf(file) {
  const r = trRow();
  if (!r || !file) return;
  let data;
  try { data = await tbBase64(file); } catch { say(t('trace.unreadable'), 9000); return; }
  try {
    await api('/api/trace', { op: 'pdf', folder: TR.folder, doc: TR.doc, ref: r.ref, data });
  } catch (err) { say(err.message, 9000); return; }
  await trRead(TR.doc, r.key);
}

/* ── the AI's passages, with the app's AI switch on ── */

function trAiDraw() {
  const r = trRow();
  const ready = trAiReady();
  $('tr-ai').hidden = !ready || !trClaim(r) || TR.view !== 'record';
  $('tr-ai-all').hidden = !ready || TR.view !== 'table' || !TR.doc;
  if (!ready) return;
  const mine = TR.asking && r && TR.asking === r.ref;
  $('tr-ai-one-word').textContent = mine ? t('trace.ai.finding') : t('trace.ai.one');
  $('tr-ai-one').disabled = !!TR.asking || !!TR.batch || !(r && r.pdf);
  $('tr-ai-one').title = r && !r.pdf ? t('trace.ai.one_no_pdf') : t('trace.ai.one_tip');
  $('tr-ai-all-word').textContent = TR.batch
    ? (TR.batch.stop ? t('trace.ai.finishing') : t('trace.ai.finding_of', { done: TR.batch.done, of: TR.batch.of })) : t('trace.ai.all');
  $('tr-ai-all').disabled = !!TR.asking && !TR.batch;
}

async function trFindOne() {
  const r = trRow();
  if (!trClaim(r) || !trAiReady() || TR.asking || TR.batch) return;
  TR.asking = r.ref;
  trAiDraw();
  try {
    trLand(await api('/api/trace', { op: 'passages', folder: TR.folder, doc: TR.doc, ref: r.ref }));
  } catch (err) { say(err.message, 9000); }
  TR.asking = null;
  trDraw();
}

/* AI find passages for the rows shown: the references of the claims shown with a PDF and no passages yet,
   one call each, said first, once alone where there is one, a second press leaving the rest unasked */
async function trFindAll() {
  if (TR.batch) { TR.batch.stop = true; trAiDraw(); return; }
  if (!trAiReady() || TR.asking) return;
  let plan;
  try {
    plan = await api('/api/trace', { op: 'plan', folder: TR.folder, doc: TR.doc, ids: TR.ids.slice() });
  } catch (err) { say(err.message, 9000); return; }
  if (!plan.calls) { say(t('trace.ai.all_had')); return; }
  if (!(await trAsk(t('trace.ai.all'), t('trace.ai.ask_line', { n: plan.calls, model: TR.modelName }),
    `${TB_SPARKS}${esc(t('trace.ai.find_passages'))}`))) return;
  TR.batch = { done: 0, none: 0, of: plan.calls, stop: false };
  let said = '';
  for (const key of plan.ids) {
    if (TR.batch.stop) break;
    TR.asking = key;
    trAiDraw();
    let got;
    try {
      got = await api('/api/trace', { op: 'passages', folder: TR.folder, doc: TR.doc, ref: key });
    } catch (err) { said = err.message; break; }
    trLand(got);
    TR.batch.done += 1;
    if (got && got.passages && !Number(got.passages.found)) TR.batch.none += 1;
    trAiDraw();
  }
  const { done, none } = TR.batch;
  const left = TR.batch.stop ? TR.batch.of - done : 0;
  TR.batch = null;
  TR.asking = null;
  trDraw();
  say(said || trAskedLine(done, none, left), said ? 9000 : 4200);
}

/* what the rows shown came to, in counts that are true: how many references were asked, how many of them
   came back with no passage the PDF holds, and how many a second press left not asked */
const trAskedLine = (done, none, left) => (none > 0 && left > 0 ? t('trace.asked_none_left', { n: done, none, left })
  : none > 0 ? t('trace.asked_none', { n: done, none }) : left > 0 ? t('trace.asked_left', { n: done, left }) : t('trace.asked', { n: done }));

/* the one question, its answer true for Yes, its Yes carrying the sparkles where it asks the AI */
function trAsk(head, line, yes) {
  $('tr-ask-head').textContent = head;
  $('tr-ask-line').textContent = line;
  $('tr-ask-yes').innerHTML = yes;
  $('tr-ask-yes').classList.toggle('sf-ai-btn', yes.includes('btn-icon'));
  $('tr-ask').hidden = false;
  $('tr-ask-yes').focus();
  return new Promise((done) => {
    TR.askDone = (ok) => { $('tr-ask').hidden = true; TR.askDone = null; done(ok); };
  });
}

/* ── leaving ── */

async function trLeaving() {
  trNoteSave();
  if (TR.batch) TR.batch.stop = true;
  await TR.chain;
  if (TR.askDone) TR.askDone(false);
  TR.frameFor = null;
  $('tr-frame').removeAttribute('src');
  $('tr-keys').hidden = true;
}

async function trBack() {
  if (TR.view === 'record') { trToTable(); return; }
  await trLeaving();
  $('trace').hidden = true;
  loadLibrary().catch((err) => say(err.message, 9000));
}

/* a Save in Settings over the screen: the AI switch and the project's name as they now stand, read afresh */
function trSettingsSaved() {
  if (!trShown()) return;
  if (TR.doc || TR.list) trRead(TR.doc, trRow() ? trRow().key : null);
}

/* ── the keys ── */

function trKeyDown(e) {
  if (!trShown() || !$('settings').hidden || !$('feedback').hidden) return;
  // Search's card over the screen keeps its own keys (18 October, search.js)
  if (e.target && e.target.closest && e.target.closest('.search-card')) return;
  e.stopPropagation();
  if (!$('tr-keys').hidden) {
    if (e.key === 'Escape' || e.key === '?') { e.preventDefault(); $('tr-keys').hidden = true; }
    return;
  }
  if (!$('tr-ask').hidden) {
    if (e.key === 'Escape' || e.key === 'Enter') { e.preventDefault(); if (TR.askDone) TR.askDone(e.key === 'Enter'); }
    return;
  }
  const typing = e.target && e.target.closest && e.target.closest('textarea, input:not([type="checkbox"]), select');
  if (typing) {
    if (e.key === 'Escape' || (e.key === 'Enter' && MOD(e) && e.target === $('tr-note'))) { e.preventDefault(); e.target.blur(); trNoteSave(); }
    if (e.key === 'Enter' && (e.target === $('tr-path') || e.target === $('tr-path-empty'))) { e.preventDefault(); trAddFile(e.target === $('tr-path-empty')); }
    return;
  }
  if (!TR.rows.length) return;
  if (MOD(e) && (e.key === 'z' || e.key === 'Z') && !e.shiftKey) { e.preventDefault(); trUndo(); return; }
  if ((e.key === 'Enter' || e.key === ' ') && e.target && e.target.tagName === 'BUTTON') return;
  if (MOD(e) || e.altKey || e.ctrlKey) return;
  const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  if (key === 'Escape' && TR.view === 'table' && !$('tr-facets').hidden && window.matchMedia('(max-width: 759px)').matches) {
    e.preventDefault();
    trFacetsOpen(false, true);
    return;
  }
  if (TR.view === 'table') {
    if (key === 'ArrowDown' || key === 'ArrowUp') { e.preventDefault(); trMove(key === 'ArrowDown' ? 1 : -1); return; }
    if (key === 'Enter') { e.preventDefault(); trOpenRecord(); return; }
  } else {
    if (key === 'Escape') { e.preventDefault(); trToTable(); return; }
    if (key === 'ArrowLeft' || key === 'ArrowRight') { e.preventDefault(); trMove(key === 'ArrowRight' ? 1 : -1); return; }
    if (key === 't') { e.preventDefault(); $('tr-note').focus(); return; }
    if (key === 'p') { e.preventDefault(); $('tr-body').classList.toggle('pdf-shut'); return; }
  }
  if (TR_KEYS[key]) { e.preventDefault(); trJudge(TR_KEYS[key]); }
  else if (key === 'u') { e.preventDefault(); trUndo(); }
  else if (key === '?' || (e.shiftKey && key === '/')) { e.preventDefault(); $('tr-keys').hidden = false; }
}

/* ── the screen, made once ── */

function trBuild() {
  const screen = document.createElement('section');
  screen.id = 'trace';
  screen.className = 'screen sf-screen tr-screen';
  screen.hidden = true;
  const cog = TB_COG;
  const glass = TB_GLASS;
  const bug = { icon: TB_BUG, hidden: tbBugHidden() };
  screen.innerHTML = `
  <div class="rail sf-rail">
    <button type="button" class="rail-home bar-brand" id="tr-home" title="${escAttr(t('trace.bar.home_tip'))}" aria-label="${escAttr(t('trace.bar.home'))}"><svg
            class="mark part-trace bar-markonly" aria-hidden="true" focusable="false"><use href="/marks.svg#trace-18"/></svg></button>
    <nav class="ds-path" aria-label="${escAttr(t('trace.bar.where'))}">
      <button type="button" class="ds-proj" id="tr-name" aria-haspopup="true" aria-expanded="false"><span class="ds-proj-name"></span><svg class="ds-chevron" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M3 4.6 6 7.6l3-3"/></svg></button>
    </nav>
    <span class="rail-grow"></span>
    <button class="rail-btn bar-tool" id="tr-search" type="button" title="${escAttr(t('trace.bar.search_tip'))}" aria-label="${escAttr(t('trace.bar.search'))}" aria-haspopup="dialog"
            aria-expanded="false" aria-controls="search">${glass}<span class="bar-word" aria-hidden="true">${esc(t('trace.bar.search'))}</span></button>
    <button class="rail-btn bar-tool" id="tr-help" type="button" title="${escAttr(t('trace.bar.shortcuts_tip'))}" aria-label="${escAttr(t('trace.bar.shortcuts'))}">?<span class="bar-word" aria-hidden="true">${esc(t('trace.bar.shortcuts'))}</span></button>
    <button class="rail-btn bar-tool rail-feedback" id="tr-feedback" type="button" title="${escAttr(t('trace.bar.feedback_tip'))}" aria-label="${escAttr(t('trace.bar.feedback_tip'))}"${bug.hidden}>${bug.icon}<span class="bar-word" aria-hidden="true">${esc(t('trace.bar.feedback'))}</span></button>
    <button class="rail-btn bar-tool" id="tr-settings" type="button" title="${escAttr(t('trace.bar.settings_tip'))}" aria-label="${escAttr(t('trace.bar.settings_tip'))}">${cog}<span class="bar-word" aria-hidden="true">${esc(t('trace.bar.settings'))}</span></button>
  </div>
  <div class="sf-main">
    <div class="sf-tv-top tr-top" id="tr-top" data-view="table" hidden>
      <button class="sf-tv-tool sf-tv-only" id="tr-facets-toggle" type="button" title="${escAttr(t('trace.filters'))}" aria-label="${escAttr(t('trace.filters'))}" aria-pressed="false"
              aria-controls="tr-facets"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
              stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4 5.5h16l-6.2 7.2v5.6l-3.6 1.8v-7.4z"/></svg><span
              class="sf-tv-word" id="tr-facets-word" aria-hidden="true">${esc(t('trace.filters'))}</span></button>
      <button type="button" class="quiet sf-facets-clear" id="tr-facets-clear" hidden>${esc(t('trace.clear_all'))}</button>
      <label class="tr-doc-line sf-tv-only"><span class="sr-only">${esc(t('trace.manuscript'))}</span><select id="tr-doc" aria-label="${escAttr(t('trace.manuscript'))}"></select></label>
      <span class="tr-list sf-tv-only" id="tr-list" hidden></span>
      <span class="tr-path-line sf-tv-only" id="tr-path-line" hidden><input id="tr-path" type="text" spellcheck="false" placeholder="${escAttr(TR_PATH_SAID)}"
             aria-label="${escAttr(t('trace.path_label'))}"></span>
      <button type="button" class="ghost small sf-tv-only" id="tr-add">${esc(t('trace.add_file'))}</button>
      <span class="sf-tv-grow"></span>
      <button type="button" class="ghost small sf-ai-btn tr-ai-all" id="tr-ai-all" data-ai hidden title="${escAttr(t('trace.ai.all_tip'))}">${TB_SPARKS}<span id="tr-ai-all-word">${esc(t('trace.ai.all'))}</span></button>
    </div>
    <p class="tr-alone" id="tr-alone" hidden>${esc(TR_NO_CLAIMS)}</p>
    <div class="sf-views">
    <div class="sf-area">
      <div class="tr-empty" id="tr-empty" hidden>
        <p class="tr-empty-line">${esc(t('trace.no_document'))}</p>
        <p class="tr-empty-go"><span class="tr-path-line" id="tr-path-empty-line"><input id="tr-path-empty" type="text" spellcheck="false"
           placeholder="${escAttr(TR_PATH_SAID)}" aria-label="${escAttr(t('trace.path_label'))}"></span><button type="button" class="primary" id="tr-add-empty">${esc(t('trace.add_file'))}</button></p>
      </div>
      <div class="sf-body" id="tr-body" hidden>
        <main class="sf-record" id="tr-record">
          <p class="sf-none" id="tr-none-rec" hidden>${esc(t('trace.no_claims_shown'))}</p>
          <article class="sf-card tr-card" id="tr-card">
            <p class="sf-meta" id="tr-meta"><span class="sf-pill" id="tr-pill" data-decision=""></span><span class="tr-set" id="tr-set"></span></p>
            <p class="tr-sec" id="tr-sec"></p>
            <p class="tr-before-rec" id="tr-before" hidden></p>
            <h1 class="sf-title tr-said" id="tr-said"></h1>
            <p class="tr-as" id="tr-as"></p>
            <div class="tr-refbox" id="tr-refbox">
              <p class="tr-ref" id="tr-ref"></p>
              <p class="sf-links tr-links" id="tr-links"></p>
              <p class="tr-judged" id="tr-judged"></p>
            </div>
            <div class="tr-pass" id="tr-pass" data-ai hidden>
              <p class="tr-pass-head">${TB_SPARKS}<span id="tr-pass-said"></span></p>
              <div class="tr-pass-body" id="tr-pass-body"></div>
            </div>
            <div class="sf-ai" id="tr-ai" data-ai hidden>
              <button type="button" class="ghost small sf-ai-btn" id="tr-ai-one">${TB_SPARKS}<span id="tr-ai-one-word">${esc(t('trace.ai.one'))}</span></button>
            </div>
            <div class="sf-acts tr-acts" id="tr-acts" role="group" aria-label="${escAttr(t('trace.judgement'))}">
              <button type="button" class="sf-act sf-accept" data-judge="Y" aria-pressed="false"><span class="sf-act-word">${esc(TR_WORDS.Y)}</span> <span class="mono sf-act-key">Y</span></button>
              <button type="button" class="sf-act sf-maybe" data-judge="Q" aria-pressed="false"><span class="sf-act-word">${esc(TR_WORDS.Q)}</span> <span class="mono sf-act-key">Q</span></button>
              <button type="button" class="sf-act sf-reject" data-judge="N" aria-pressed="false"><span class="sf-act-word">${esc(TR_WORDS.N)}</span> <span class="mono sf-act-key">N</span></button>
            </div>
            <textarea class="sf-note" id="tr-note" rows="2" placeholder="${escAttr(t('trace.note'))}" aria-label="${escAttr(t('trace.note'))}" spellcheck="true"
                      data-gramm="false" data-gramm_editor="false" data-enable-grammarly="false"></textarea>
          </article>
        </main>
        <aside class="sf-pdf" id="tr-pdf" aria-label="${escAttr(t('trace.pdf'))}">
          <iframe class="sf-frame" id="tr-frame" title="${escAttr(t('trace.pdf'))}" hidden></iframe>
          <p class="sf-nopdf" id="tr-nopdf">${esc(t('trace.no_pdf'))} <button type="button" class="ghost small" id="tr-pdf-add">${esc(t('trace.add_pdf'))}</button></p>
          <input type="file" id="tr-pdf-file" accept="application/pdf,.pdf" hidden>
        </aside>
      </div>
      <div class="sf-tv" id="tr-tv">
        <div class="sf-tv-main">
          <aside class="sf-facets" id="tr-facets" aria-label="${escAttr(t('trace.filters'))}" hidden>
            <h2 class="sr-only">${esc(t('trace.filters'))}</h2>
            <div class="sf-groups" id="tr-groups"></div>
          </aside>
          <div class="sf-tv-box" id="tr-tv-box"><table class="sf-tbl tr-tbl" id="tr-tbl"><thead id="tr-thead"></thead><tbody
               id="tr-tbody"></tbody></table><p class="sf-none" id="tr-none" hidden>${esc(t('trace.no_claims_shown'))}</p></div>
        </div>
      </div>
    </div>
    </div>
  </div>
  <div class="sf-foot" id="tr-foot" hidden>
    <span class="sf-count" id="tr-count"></span>
    <button type="button" class="ghost small sf-undo" id="tr-undo" hidden>${esc(t('trace.undo'))}</button>
    <span class="sf-tally" id="tr-tally"></span>
  </div>`;
  const ask = document.createElement('div');
  ask.className = 'overlay';
  ask.id = 'tr-ask';
  ask.hidden = true;
  ask.innerHTML = `<div class="card" role="dialog" aria-labelledby="tr-ask-head"><p class="kicker">${TR_NAME}</p><h2 id="tr-ask-head"></h2>`
    + `<p class="trim-line" id="tr-ask-line"></p><div class="card-actions"><button type="button" class="ghost" id="tr-ask-no">${esc(t('trace.cancel'))}</button>`
    + '<button type="button" class="primary" id="tr-ask-yes"></button></div></div>';
  const keys = document.createElement('div');
  keys.className = 'overlay';
  keys.id = 'tr-keys';
  keys.hidden = true;
  keys.innerHTML = `<div class="card"><button class="card-close" id="tr-keys-close" type="button" tabindex="-1" aria-label="${escAttr(t('trace.close'))}" title="${escAttr(t('trace.close'))}">`
    + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M5 5l14 14M19 5L5 19"/></svg></button>'
    + `<p class="kicker">${esc(t('trace.keys.head'))}</p><h2>${TR_NAME}</h2><table class="keys">`
    + `<tr><td class="mono">Y</td><td>${esc(TR_WORDS.Y)}</td></tr><tr><td class="mono">Q</td><td>${esc(TR_WORDS.Q)}</td></tr>`
    + `<tr><td class="mono">N</td><td>${esc(TR_WORDS.N)}</td></tr>`
    + `<tr><td class="mono">&#8593; / &#8595;</td><td>${esc(t('trace.keys.move'))}</td></tr>`
    + `<tr><td class="mono">${esc(t('trace.keys.open_key'))}</td><td>${esc(t('trace.keys.open'))}</td></tr>`
    + `<tr><td class="mono">&#8592; / &#8594;</td><td>${esc(t('trace.keys.step'))}</td></tr>`
    // the key as this machine names it, Cmd or Ctrl, through keyName as on the statements screen (17 October)
    + `<tr><td class="mono">${esc(keyName(t('trace.keys.undo_key')))}</td><td>${esc(t('trace.keys.undo'))}</td></tr>`
    + `<tr><td class="mono">T</td><td>${esc(t('trace.keys.note'))}</td></tr>`
    + `<tr><td class="mono">P</td><td>${esc(t('trace.keys.pdf'))}</td></tr>`
    + `<tr><td class="mono">${esc(keyName(t('trace.keys.search_key')))}</td><td>${esc(t('trace.keys.search'))}</td></tr>`
    + `<tr><td class="mono">?</td><td>${esc(t('trace.keys.card'))}</td></tr><tr><td class="mono">${esc(t('trace.keys.esc_key'))}</td><td>${esc(t('trace.keys.esc'))}</td></tr>`
    + '</table></div>';
  // before the line at the foot's status, which holds it (a11yfix)
  const before = $('toast-live') || $('toast');
  document.body.insertBefore(screen, before || null);
  document.body.insertBefore(ask, before || null);
  // the lockup drawn in from Home's, and the bar's words fitted to its room (shell.js)
  if (typeof barLockups === 'function') barLockups();
  document.body.insertBefore(keys, before || null);
}

function trBoot() {
  trBuild();
  // the lockup goes home (option C of the bars, 26 October 2026, where the back arrow stood, the path's Home gone since
  // option D, 6 November 2026), and the path's project opens its menu, its card's on Home (barsD)
  $('tr-home').onclick = () => goHome();
  bandMenuWire('tr-name', traceBandMenu);
  // and the way back to the table from a record, the link before the name (sifttable, 8 November 2026)
  bandTableWire('tr-name', { word: t('trace.band.table'), away: () => TR.view === 'record', go: () => trToTable() });
  $('tr-help').onclick = () => { $('tr-keys').hidden = false; };
  $('tr-keys-close').onclick = () => { $('tr-keys').hidden = true; };
  $('tr-feedback').onclick = () => openFeedback('trace');
  $('tr-settings').onclick = () => openSettings('trace');
  $('tr-doc').onchange = () => { trNoteSave(); TR.chain.then(() => trRead($('tr-doc').value)); };
  $('tr-add').onclick = () => trAddFile(false);
  $('tr-add-empty').onclick = () => trAddFile(true);
  $('tr-facets-toggle').onclick = () => trFacetsOpen($('tr-facets').hidden, true);
  $('tr-facets-clear').onclick = () => trClear(null);
  $('tr-undo').onclick = trUndo;
  $('tr-ai-one').onclick = trFindOne;
  $('tr-ai-all').onclick = trFindAll;
  $('tr-ask-yes').onclick = () => { if (TR.askDone) TR.askDone(true); };
  $('tr-ask-no').onclick = () => { if (TR.askDone) TR.askDone(false); };
  $('tr-pdf-add').onclick = () => $('tr-pdf-file').click();
  $('tr-pdf-file').onchange = () => { const f = $('tr-pdf-file').files[0]; $('tr-pdf-file').value = ''; trAddPdf(f); };
  $('tr-note').addEventListener('blur', trNoteSave);
  $('tr-acts').addEventListener('click', (e) => {
    const b = e.target.closest('[data-judge]');
    if (b) trJudge(b.dataset.judge);
  });
  $('tr-links').addEventListener('click', (e) => { if (e.target.closest('#tr-open')) trOpenPdf(); });
  $('tr-pass-body').addEventListener('click', (e) => {
    const b = e.target.closest('[data-page]');
    if (!b) return;
    TR.pageAt = Number(b.dataset.page) || 1;
    $('tr-body').classList.remove('pdf-shut');
    trRecordDraw();
  });
  // a row opens its claim, a heading sorts, Shift adding the next key
  $('tr-tbody').addEventListener('click', (e) => {
    const tr = e.target.closest('tr[data-rec]');
    if (!tr || e.target.closest('a, button')) return;
    const sel = window.getSelection ? window.getSelection() : null;
    if (sel && String(sel).trim() && tr.contains(sel.anchorNode)) return;
    TR.at = Math.max(0, TR.ids.indexOf(tr.dataset.rec));
    TR.pageAt = null;
    trOpenRecord();
  });
  $('tr-thead').addEventListener('click', (e) => {
    const btn = e.target.closest('.sf-th');
    const col = btn && TR_COLS.find((c) => c.key === btn.dataset.sort);
    if (!col) return;
    TR.sort = tbSortNext(TR.sort, col, e.shiftKey);
    trRefilter();
  });
  // the filters, as the family's table's sidebar takes them
  const groups = $('tr-groups');
  groups.addEventListener('change', (e) => {
    const box = e.target.closest('input[type="checkbox"][data-v]');
    const group = box && box.closest('[data-g]');
    if (group) trTick(group.dataset.g, box.dataset.v, box.checked);
  });
  groups.addEventListener('input', (e) => {
    const el = e.target;
    if (!el.dataset || el.dataset.act !== 'find') return;
    const group = el.closest('[data-g]');
    if (!group) return;
    TR.facetsFind[group.dataset.g] = el.value;
    trFacetsDraw();
  });
  groups.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-act]');
    const group = btn && btn.closest('[data-g]');
    if (!group) return;
    const key = group.dataset.g;
    if (btn.dataset.act === 'clear') { trClear(key); return; }
    if (TR.facetsMore.has(key)) TR.facetsMore.delete(key);
    else TR.facetsMore.add(key);
    trFacetsDraw();
  });
  window.addEventListener('keydown', trKeyDown, true);
  // Trace's New project and Open project folder, the family's card in Trace's words (15 October), and Remove
  // from Idiograph under Trace in Settings
  $('trace-new').onclick = () => openReviewCard('new', 'trace');
  $('trace-open').onclick = () => openReviewCard('open', 'trace');
  $('trp-remove').onclick = () => trpRemove();
}


/* ── Trace's Home section, its Settings pane and Search's landing (from app.js and search.js, the family
   codebase's second build, 22 October 2026) ── */

// its projects' route, which the family's New project and Open project folder card asks for Trace
const TR_ROUTE = '/api/trace-project';

/* Trace's projects for Open Recent in the File menu of its own window, each by its folder (app.js's windowRecent) */
const trRecent = (data) => (Array.isArray(data.traces) ? data.traces : []).filter((r) => r && r.there !== false && r.folder)
  .map((r) => ({ part: 'trace', name: String(r.name || '').trim() || t('trace.project_unnamed'), folder: r.folder }));

/* Trace, after Sift (15 October): a card for each Trace project, newest first, its name and
   one line, its newest manuscript and how many of its claims are judged, and New project and
   Open project folder under them. A card opens the project's claims (trace.js). A server from before Trace
   sends no `traces`, and the section stays hidden. */
function drawTraceHome(data) {
  const rows = data && Array.isArray(data.traces) ? data.traces : null;
  $('trace-home').hidden = !rows;
  if (!rows) return;
  foldable($('trace-home'), $('trace-head'), 'trace');
  const list = $('trace-list');
  // each card's "..." and its menu, the family's, as an Idiograph card has them (barsD, 6 November 2026)
  const where = { window: windowPicks(), mac: MAC };
  list.innerHTML = rows.map((r, i) => {
    const menu = traceMenuRows(traceMenuItems(r, where), where);
    return `<li class="sf-row home-card-li${menu.length ? ' has-menu' : ''}"><button type="button" class="sf-row-open home-card" data-i="${i}"${r.there ? '' : ' disabled'}`
      + ` title="${escAttr(homeHover(r))}"><span class="pc-label hc-name">${esc(r.name)}</span>`
      // its newest manuscript and its claims judged, never its folder, which the card's hover names (the split's pages)
      + `<span class="pc-line">${esc(r.line || '')}</span></button>${projectDotsHtml(r.name, menu)}</li>`;
  }).join('');
  list.querySelectorAll('.sf-row-open').forEach((btn) => {
    btn.onclick = () => trOpen(rows[Number(btn.dataset.i)].folder);
  });
  projectMenus(list, (act, li) => traceMenuDo(act, rows[Number(li.querySelector('.sf-row-open').dataset.i)]));
}

/* A Trace project's menu (barsD, Adam, 6 November 2026: "Add a menu to both"), on its card on Home and behind its name
   in the bar, by the family's code (projectMenuHtml and the rest in shell.js): Show in Finder, in the app's own window
   alone as an Idiograph card's, Project settings, which opens Settings on Projects with this project in front, where
   its name is, and Remove from Trace. A project whose folder is gone has Remove alone. Trace keeps no History of a
   project and makes no shared copy, so neither is there. */
function traceMenuItems(r, where) {
  if (!r || !r.folder) return [];
  if (r.there === false) return ['remove'];
  return [...(where.window ? ['show'] : []), 'settings', 'remove'];
}

function traceMenuRows(items, where) {
  return items.map((act) => ({ act, word: projectMenuWord(act, where.mac), remove: act === 'remove' }));
}

/* an item of a project's menu, `r` the project as the list or the screen has it, `inside` from its own screen */
function traceMenuDo(act, r, inside = false) {
  if (!r) return;
  if (act === 'show') traceShowFolder(r.folder);
  else if (act === 'settings') { TRP.want = r.folder; openSettings('trace'); }
  else if (act === 'remove') traceRemove(r, inside);
}

/* Show in Finder, or in Explorer: the server shows the project's folder, which a browser's page cannot */
async function traceShowFolder(folder) {
  try { await api(TR_ROUTE, { op: 'reveal', folder }); } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* Remove from Trace from a project's menu, as Settings has it: one line to confirm, then from the project's own screen
   the screen left as Home leaves it, a note that will not save keeping him there with the project kept, then the
   project taken out of the list, its folder and every file in it left as they are, and Home without it */
async function traceRemove(r, inside = false) {
  // Remove's card, its tick moving the folder to the system's Trash too (removetrash, 10 November 2026)
  const asked = await askRemove(r.name || '');
  if (!asked) return;
  if (inside && !(await goHome())) return;
  let data;
  try { data = await api(TR_ROUTE, { op: 'forget', folder: r.folder, trash: asked.trash, page: pageId() }); } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return;
  }
  if (S.lib && Array.isArray(data.traces)) S.lib.traces = data.traces;
  say(removedSaid(data.name || r.name, data, t('trace.removed', { name: data.name || r.name })));
  loadLibrary().catch((err) => say(err.message, 9000));
}

/* the menu behind the bar's name on Trace's screen, the project open there */
function traceBandMenu() {
  if (!onScreen('trace') || !TR.folder) return null;
  const where = { window: windowPicks(), mac: MAC };
  const r = { folder: TR.folder, name: (TR.project && TR.project.name) || $('tr-name').title, there: true };
  return { rows: traceMenuRows(traceMenuItems(r, where), where), pick: (act) => traceMenuDo(act, r, true) };
}

/* Under Trace in Settings (15 October), a Trace project's name and its folder, as a Sift project's are under
   Sift: a row of the Trace projects' names when there are several, the one open on Trace's screen first and
   chosen, the name as typed and not yet saved, else as the list gives it, saved with Save into the app's own
   list and never its folder, and Remove from Idiograph. With no Trace project the pane says so. */
const TRP = { list: [], at: null, drafts: new Map(), want: null };

function trpLoad() {
  const rows = (S.lib && Array.isArray(S.lib.traces) ? S.lib.traces : []).filter((r) => r.there);
  const open = onScreen('trace') && typeof TR !== 'undefined' && TR.folder ? TR.folder : null;
  // or the project whose menu asked for its settings (barsD), from Home or its bar
  const asked = TRP.want || open;
  TRP.want = null;
  const at = asked ? rows.findIndex((r) => r.folder === asked) : -1;
  TRP.list = at >= 0 ? [rows[at], ...rows.filter((_, i) => i !== at)] : rows;
  TRP.drafts = new Map();
  TRP.at = null;
  $('trp-block').hidden = !TRP.list.length;
  $('trp-none').hidden = TRP.list.length > 0;
  if (TRP.list.length) trpShow(TRP.list[0]);
}

function trpShow(item) {
  trpKeep();
  TRP.at = item;
  const pick = $('trp-pick');
  pick.hidden = TRP.list.length < 2;
  pick.innerHTML = TRP.list.map((r, i) => `<button type="button" class="ghost small${r === item ? ' on' : ''}" data-i="${i}"`
    + ` aria-pressed="${r === item}">${esc(r.name)}</button>`).join('');
  pick.querySelectorAll('button').forEach((b) => { b.onclick = () => trpShow(TRP.list[Number(b.dataset.i)]); });
  const draft = TRP.drafts.get(item.folder);
  $('trp-name').value = draft !== undefined ? draft : item.name || '';
  $('trp-root').innerHTML = pathHtml(item.folder);
  trpSaid('');
}

/* what is typed for the project shown, kept while another is shown */
function trpKeep() {
  if (TRP.at && !$('trp-block').hidden) TRP.drafts.set(TRP.at.folder, $('trp-name').value);
}

function trpSaid(text, failed = false) {
  saidIn('trp-said', text || '', failed);
  $('trp-said').hidden = !text;
}

/* What Save sends for the Trace projects: each one whose name changed, by its folder. A name left empty
   keeps the one it had. */
function trpSaves() {
  trpKeep();
  const out = [];
  for (const item of TRP.list) {
    const draft = TRP.drafts.get(item.folder);
    if (draft === undefined) continue;
    const name = draft.trim() || item.name;
    if (name !== item.name) out.push({ op: 'rename', folder: item.folder, name });
  }
  return out;
}

/* Remove from Idiograph, after one line to confirm: the project taken out of the list, its folder and every
   file in it left as they are. From over the project itself the page opens on the home screen. */
async function trpRemove() {
  const item = TRP.at;
  if (!item) return;
  const asked = await askRemove(item.name || '');
  if (!asked) return;
  let data;
  try {
    data = await api(TR_ROUTE, { op: 'forget', folder: item.folder, trash: asked.trash, page: pageId() });
  } catch (err) { trpSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); return; }
  if (onScreen('trace') && typeof TR !== 'undefined' && TR.folder === item.folder) { S.noSpot = true; location.reload(); return; }
  if (S.lib && Array.isArray(data.traces)) S.lib.traces = data.traces;
  TRP.drafts.delete(item.folder);
  TRP.list = TRP.list.filter((r) => r !== item);
  TRP.at = null;
  $('trp-block').hidden = !TRP.list.length;
  $('trp-none').hidden = TRP.list.length > 0;
  if (TRP.list.length) trpShow(TRP.list[0]);
  if (!$('library').hidden) loadLibrary().catch((err) => say(err.message, 9000));
  say(removedSaid(data.name || item.name, data, t('trace.removed', { name: data.name || item.name })));
}

/* the project this page is in front of, by its folder, for the beat (beat.js), so another window's Remove never
   moves it to the Trash (removetrash) */
window.idiographAt = () => (onScreen('trace') && typeof TR !== 'undefined' && TR.folder ? TR.folder : '');

/* Save's sends for the Trace projects sent, each answer's cards kept and the project open on Trace's screen
   taking its name at once */
async function trpSend(sends) {
  for (const sent of sends) {
    const answer = await api(TR_ROUTE, sent);
    if (S.lib && Array.isArray(answer.traces)) S.lib.traces = answer.traces;
    if (TR.folder === sent.folder && answer.project) {
      TR.project = answer.project;
      if (onScreen('trace')) trHead();
    }
  }
}

/* Search's place on Trace's screen, the project open */
const trSearchWhere = () => (searchShown('trace') && TR.folder ? { screen: 'trace', folder: TR.folder } : null);

/* Search leaving Trace's screen, its note kept first, the screen put away */
async function trSearchLeave() {
  if (!searchShown('trace')) return true;
  await trLeaving();
  $('trace').hidden = true;
  return true;
}

/* A Trace result: the project opened, on the screen already when it is the one open, at the manuscript,
   or the reference list alone, and there the claim's row opened, a reference's first claim or for one
   never cited its own row, with the caret in the claim's note for a note. A row the table's filters
   leave out stands among the rows in the table's order until the filters next change. */
async function searchToTrace(go) {
  const here = SEARCH.here;
  if (!(here && here.screen === 'trace' && searchShown('trace') && TR.folder === go.folder)) {
    if (!(await searchLeaveFor(here))) return;
    await trOpen(go.folder);
    if (!searchShown('trace')) return;
  }
  if (TR.doc !== (go.doc || '')) {
    trNoteSave();
    await TR.chain;
    await trRead(go.doc || '');
  }
  if (!TR.byId.has(go.key)) { say(SEARCH_GONE, 6000); return; }
  if (!TR.ids.includes(go.key)) {
    const keep = new Set([...TR.ids, go.key]);
    TR.ids = tbSortRows(trBase(), TR.byId, TR.sort, TR_COLS).filter((id) => keep.has(id));
    TR.tvShape = '';
  }
  TR.at = TR.ids.indexOf(go.key);
  TR.pageAt = null;
  if (TR.view === 'record') trDraw();
  else trOpenRecord();
  if (go.field === 'note' && trClaim(trRow())) $('tr-note').focus();
}

/* the screen kept for a reload, the project by its folder, the manuscript open kept in this browser */
const trSpot = () => ($('trace') && !$('trace').hidden && TR.folder ? { screen: 'trace', path: TR.folder } : null);

FAMILY_APPS.trace = {
  screen: 'trace', route: TR_ROUTE, open: trOpen, home: drawTraceHome, recent: trRecent, settingsLoad: trpLoad, settingsSends: trpSaves,
  settingsSend: trpSend, settingsSaved: trSettingsSaved, spot: trSpot, searchWhere: trSearchWhere,
  searchLeave: trSearchLeave, searchTo: searchToTrace,
};
// the home screen's answer may come before this script is read, and Trace's section then takes it now
if (APP === 'trace' && S.lib) drawTraceHome(S.lib);

trBoot();

/* Trace's commands by name for people in its agent log (siftlog, 3 November 2026), each by its words, an MCP tool's
   by its command, added to the family's table (agentlog.js) */
Object.assign(AL_OPS, {
  'trace': 'agentlog_trace.claims',
  'search': 'agentlog_trace.search',
});
