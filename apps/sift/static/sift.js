/* Sift, screening for a systematic review. No framework, no build step.

   The server reads and writes the screening through sift.py: every decision goes to the log beside
   the CSV at once and the CSV's decision columns are written afresh from it, so there is nothing to
   save. This holds the records in memory, the round he chose and his place in it. A round is fixed
   when it is chosen, so a decision never moves the records under him, and choosing it again takes in
   what changed. The PRISMA flow comes from the server as Mermaid with every answer and is drawn here
   by the vendored Mermaid, loaded from the app itself, in a sidebar at the right that he opens and
   closes from the title bar, its state kept in this browser.

   Every AI part follows the app's AI switch, `aiOn(config)`: with it off there is no AI suggestion, no
   AI control and no AI setting, and screening is whole by hand, a suggestion the CSV says keyword rules
   made, or says nothing of, still shown (14 October). With it on, every suggestion the CSV holds is
   shown under its title, which says what made it and its source, and with the screening's own switch
   on, Sift asks the app's AI for a proposal of its own, for this record or for the rows shown. An AI
   never decides a record, and Accept suggestion is his own decision, as a press of that decision is.
   Find open-access PDFs, Fill from OpenAlex and Export to Zotero call no model, so they stand
   outside the switch. Sift's settings are under Sift in Settings, which its cog opens.

   Sift opens on the table: a row for each record of the stage, its number first, sorted by its
   headings and filtered from a sidebar at its left, each choice a tick box with a live count of the
   rows it would show, Decision the one filter of where a record stands (12 October). A double-click
   or Enter on a row opens that record, the one-record screen, which walks
   the table's rows in their order, and its way back or Esc returns to the table on the same row, its
   filters and sort kept. The rows are set when the stage, a sort or a filter is chosen, so a
   decision never moves them under him, and each row is drawn again alone when its record changes.
   His own fields, the rating, the participants, the notes, the digest, the critique and his columns,
   go to the server one change at a time, as the decisions do, and so do his key excerpts, words of the
   title or abstract kept with H, which Undo takes back as it takes back a decision (14 October). */

'use strict';

const SF = {
  folder: null,      // the screening open, as the server names it back
  name: '',
  review: null,      // its review, for the steps, as the server names it
  records: [],       // every record, in the CSV's order
  byId: new Map(),
  reasons: { ta: [], ft: [] },
  counts: null,
  prisma: '',        // the flow as Mermaid, from the server's last answer
  undo: null,        // what Undo would take back, or null
  stamp: null,       // the files' stamp as last read, to tell another writer's change
  aiMaster: false,   // the app's AI switch
  ai: null,          // the screening's AI settings, null with the app's switch off
  stage: 'ta',
  round: 'all',      // every record of the stage, which the table's filters narrow, Decision among them
  ids: [],           // the records the table shows
  at: 0,
  picking: false,    // the reasons stand open after R, waiting for a number
  pick: -1,          // the reason chosen among them
  chain: Promise.resolve(),   // the acts in the order he made them, one after another
  flowChain: Promise.resolve(),
  flowDrawn: '',     // the flow and the colours it was last drawn with
  flowN: 0,
  asking: null,      // the record a proposal is being asked for
  batch: null,       // a proposal for the round under way, { done, of, stop }
  askDone: null,     // the question card's answer, while it stands open
  openedAt: 0,       // when a click on a row last opened its record, for its double-click's second press
  tvTyping: false,   // a cell of the table was open for typing as the press on the table began
  pdfAt: {},         // when a record's PDF was last kept from a drop, so the pane takes the new one
  frameFor: null,    // the record whose PDF the pane holds
  noteFor: null,     // the record and stage the note field holds
  view: 'table',     // table, where Sift opens, or record, a row opened from it
  table: null,       // the table's columns, in his order, and his own columns, from sift.json
  roundIds: [],      // the round's records as the server gave them, before the table's filters and sort
  sort: [],          // the table's sort, its keys in order, each { key, dir }
  filters: {},       // the table's filters by column, each the list of choices ticked in its group
  facetsMore: new Set(), // the long groups of the sidebar shown whole
  facetsFind: {},    // what is typed in each long group's find box, by column
  facetsHtml: '',    // the sidebar as last drawn, so it is built again only when it changes
  facetsOrder: {},   // each group's choices in the order last drawn, by column
  facetsHold: null,  // the group he last ticked in, its order held, { key, order }, until the sidebar is drawn afresh
  world: null,       // the map Country's counts stand on, static/world.json, read once
  mapFrom: null,     // the control that opened the map, given its focus back as the map shuts
  kept: '',          // the filters and the find boxes' words as sift.json last kept them, to tell a change
  keepTimer: null,   // a find box's words waiting to be kept a moment after the last letter typed
  tvRows: new Map(), // each row drawn, by rec_id, its element and the markup it was drawn from
  tvShape: '',       // the columns and rows last drawn, so the body is built again only when they change
  tvHead: '',
  tvSel: null,       // the row marked as chosen
  tvScroll: 0,       // where the table stood when the record screen opened over it
  tvReveal: false,   // the chosen row brought into view at the next drawing
  editing: null,     // a cell of the table open for typing, { rec, field }
  fieldsFor: null,   // the record the fields under the record screen hold
  marksHidden: false, // the grounds marked in the abstract hidden, as this browser keeps it
  email: '',         // the email Unpaywall asks of Find open-access PDFs, from config.json
  oa: null,          // a run of Find open-access PDFs under way, { done, of, found, stop }
  fill: null,        // a run of Fill from OpenAlex under way, { done, of, filled, stop }
  keyWorks: [],      // the review's key works, each its key and its label, which Cites key works names
  matchHead: [],     // the two lines over a block's lines in the filters, as the server words them
  bench: null,       // the bench under Sift in Settings, { folder, stage, model, records }
  benchBusy: false,  // the bench asking
  zot: null,         // Export to Zotero, { folder, plan, running, said, done }
  second: null,      // the second screener's side as the server sends it, blind both ways (see sift_second.py)
  form: false,       // Extract and appraise, the stage after full text, the screen standing at full text under it
  formInc: new Set(), // its records included at full text, as the server listed them
  formBench: new Set(), // the review's benchmark papers among the records, whatever their decision
  benchIds: [],      // the same as the screening's read gives them
  formFor: null,     // the record the form on the record pane holds
  psgAdd: {},        // the blank passages added to a Passages field, by record and field, not yet kept
  fcWhen: {},        // a field's Shown when on Set up the form while a value of it is still to be ticked
  blocks: [],        // the plan's blocks with their terms, for the filters (see sfTermCols)
  pieces: [],        // the pieces of the key excerpt being built, each { in, start, end } in the title or abstract
  piecesFor: null,   // the record they belong to
  exPress: null,     // where the last press on the record began, to tell a click from a drag
};

// The round the old dropdown over the table kept in this browser, read once into the Decision filter,
// the one filter of where a record stands since 12 October: each round as its tick, All as none
const SF_ROUND_TICKS = { undecided: 'undecided', maybe: 'maybe', accepted: 'include', rejected: 'exclude',
  differs: 'differs', apart: 'apart' };
// What a decision reads as at each stage (12 October, later): title and abstract is a filter, so Yes,
// Maybe and No, Yes and Maybe both going on to full text, and full text the decision, so Include, Maybe
// and Exclude, the same words on the buttons, the pills, the filters, the counts and a proposal, and a
// record waiting at either To screen. Words only: the CSV, the log, sift.json and the second screener's
// files keep include, maybe and exclude, and an empty decision, as before (see SHOWN_WORDS in sift.py).
const SF_WORDS = { ta: { include: t('sift.ta.include'), maybe: t('sift.ta.maybe'), exclude: t('sift.ta.exclude') },
  ft: { include: t('sift.ft.include'), maybe: t('sift.ft.maybe'), exclude: t('sift.ft.exclude') } };
const SF_TO_SCREEN = t('sift.to_screen');
const sfWords = (stage) => SF_WORDS[stage === 'ft' ? 'ft' : 'ta'];
// what each decision does at each stage, on its button's hover: at title and abstract Yes and Maybe
// take the record on to full text, Maybe marked unsure, and No goes no further, and at full text
// Include and Exclude decide it, Maybe keeping it there, neither included nor excluded
const SF_SAYS = { ta: { include: t('sift.says.ta.include'), maybe: t('sift.says.ta.maybe'), exclude: t('sift.says.ta.exclude') },
  ft: { include: t('sift.says.ft.include'), maybe: t('sift.says.ft.maybe'), exclude: t('sift.says.ft.exclude') } };
// each stage's keys for its decisions, shown on the buttons and the shortcuts card, Y, M and N at title
// and abstract and I, M and E at full text, and the old A and R, which keep working at both stages
// without being shown, so his hands are not broken (12 October, later)
const SF_KEYS = { ta: { include: 'Y', maybe: 'M', exclude: 'N' }, ft: { include: 'I', maybe: 'M', exclude: 'E' } };
const SF_KEYS_OLD = { a: 'include', r: 'exclude' };
// the decision a key takes at a stage, or none
function sfKeyDecision(key, stage) {
  const keys = SF_KEYS[stage === 'ft' ? 'ft' : 'ta'];
  return Object.keys(keys).find((d) => keys[d].toLowerCase() === key) || SF_KEYS_OLD[key] || '';
}
// The suggestion box's title by what made the suggestion (14 October, Adam's words), every title's words
// here alone: a model named in the CSV's proposed_by, "model:" and its name, or Sift's own AI, gives an AI
// suggestion with the sparkles, keyword rules or nothing said a suggestion without them, each with its
// source, and the longer sense on hover, the model named where it is known. An AI suggestion hides with the
// app's AI switch off, and one by keyword rules or that says nothing shows either way
const SF_SUGGESTION = {
  sift: { ai: true, title: t('sift.suggestion.sift'), tip: t('sift.suggestion.sift_tip') },
  sift_model: { ai: true, title: t('sift.suggestion.sift'), tip: t('sift.suggestion.sift_model_tip') },
  model: { ai: true, title: t('sift.suggestion.model'), tip: t('sift.suggestion.model_tip') },
  rules: { ai: false, title: t('sift.suggestion.rules'), tip: t('sift.suggestion.rules_tip') },
  unstated: { ai: false, title: t('sift.suggestion.unstated'), tip: t('sift.suggestion.unstated_tip') },
};
const sfSuggestionOf = (p) => SF_SUGGESTION[p && p.kind] || SF_SUGGESTION[p && p.source === 'sift' ? 'sift' : 'unstated'];
// the suggestions a record shows at its stage, the review's first, two at most, an AI's only with the switch on
const sfSuggestions = (st) => ((st && st.proposals) || []).filter((p) => SF.aiMaster || !sfSuggestionOf(p).ai).slice(0, 2);
// whose proposal the words marked in the abstract are the grounds of, in the line that names them:
// the screening file's, Sift's own or both (9 October)
const SF_GROUNDS = { csv: t('sift.grounds.csv'), sift: t('sift.grounds.sift') };
const SF_GROUNDS_BOTH = t('sift.grounds.both');
const SF_PLACE_KEY = 'idiograph-sift-place';
const SF_PDF_KEY = 'idiograph-sift-pdf';
const SF_FLOW_KEY = 'idiograph-sift-flow';
const SF_MARKS_KEY = 'idiograph-sift-marks';
const SF_FACETS_KEY = 'idiograph-sift-filters';
const SF_NARROW = '(max-width: 759px)';
// the width under which the filters' sidebar starts shut
const SF_FACETS_NARROW = '(max-width: 899px)';
const SF_MERMAID = '/vendor/mermaid.min.js';

const sfShown = () => !$('sift').hidden;
const sfRecord = () => SF.byId.get(SF.ids[SF.at]) || null;
const sfStage = (r) => (r ? r.stages[SF.stage] : null);
const sfCodes = () => SF.reasons[SF.stage] || [];
const sfAiReady = () => !!(SF.aiMaster && SF.ai && SF.ai.on);

/* where he was in each screening, the stage, the record and the sort, kept in this browser alone */
function sfPlaces() {
  try {
    const held = JSON.parse(localStorage.getItem(SF_PLACE_KEY) || '{}');
    return held && typeof held === 'object' ? held : {};
  } catch { return {}; }
}

function sfKeepPlace() {
  const r = sfRecord();
  try {
    const held = sfPlaces();
    held[SF.folder] = { stage: SF.form ? 'ex' : SF.stage, rec: r ? r.rec_id : null, sort: SF.sort };
    localStorage.setItem(SF_PLACE_KEY, JSON.stringify(held));
  } catch { /* private window */ }
}

/* A review's screening opened on its Screening step, from the review's row on the home screen, its
   steps or its runs, or on the way back from a restart, always on the table, at the stage, the row
   and the sort it was left on, at title and abstract while no record has passed it. A round the old
   dropdown kept is read into the Decision filter when sift.json keeps none there. A stage chosen from
   the steps on Search strategy, `stage`, opens in place of the one it was left on (12 October). One
   that cannot be read says why and stays where he was, or goes to `gone`. */
async function siftOpen(folder, gone, stage) {
  if (!folder) return;
  let data;
  try {
    data = await api('/api/sift', { op: 'read', folder });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    if (gone) gone();
    return;
  }
  $('library').hidden = true;
  // Idiograph's screens are on Idiograph's page alone since the page split (23 October), so Sift's own page
  // has none to hide, and a plain $('work') stopped the screening opening there (zoomsweep, 30 October)
  for (const id of ['work', 'themes']) if ($(id)) $(id).hidden = true;
  if ($('sift-search')) $('sift-search').hidden = true;
  if ($('trace')) $('trace').hidden = true;
  $('sift').hidden = false;
  sfTake(data);
  const kept = sfPlaces()[SF.folder] || {};
  // Extract and appraise stands at full text underneath (13 October, later)
  SF.form = (stage || kept.stage) === 'ex';
  SF.stage = SF.form || ((stage || kept.stage) === 'ft' && sfFtOn()) ? 'ft' : 'ta';
  SF.round = 'all';
  SF.view = 'table';
  // a record's entry in the browser's history left from an earlier visit opens nothing now
  sfHistoryDrop();
  const known = new Set(sfAllCols().map((c) => c.key));
  SF.sort = (Array.isArray(kept.sort) ? kept.sort : []).filter((s) => s && known.has(s.key))
    .map((s) => ({ key: s.key, dir: s.dir === 'desc' ? 'desc' : 'asc' }));
  // the filters and the find boxes' words as sift.json keeps them for this screening, a tick that
  // names a choice no record now carries let go
  const table = SF.table || {};
  const groups = sfGroups(SF.records, SF.records, sfAllCols(), SF.stage, sfCodes(), {});
  SF.kept = sfKeptJson(table.filters, table.find);
  SF.filters = sfKeptRead(table.filters, groups);
  // Benchmark papers, a filter of Extract and appraise beyond the table's columns
  if (SF.form && tbTicks(table.filters, SF_BENCH).length) SF.filters[SF_BENCH] = ['yes'];
  // the round the old dropdown kept, its tick in the Decision filter when that holds none, kept in
  // sift.json once the round is drawn
  const tick = SF_ROUND_TICKS[kept.round];
  const decision = groups.find((g) => g.key === 'decision');
  if (tick && !SF.filters.decision && decision && decision.choices.some((c) => c.value === tick)) SF.filters.decision = [tick];
  // the two sidebars at the widths sift.json keeps for this screening, the filters' and the flow's
  sfEdgeWidth('facets', table.sidebar);
  sfEdgeWidth('flow', table.flow);
  SF.facetsMore = new Set();
  SF.facetsFind = sfFindRead(table.find, groups);
  SF.facetsHtml = '';
  SF.facetsHold = null;
  SF.tvShape = '';
  SF.tvHead = '';
  SF.tvScroll = 0;
  SF.marksHidden = sfMarksStored();
  sfPdfShut(sfPdfStored());
  // the flow's sidebar as this browser left it, open the first time, and shut at phone width, where
  // it stands over the screen
  sfFlowOpen(!sfNarrow() && sfFlowStored() !== false, false);
  // the filters' sidebar the same way, open the first time on a wide screen and shut under 900 pixels
  sfFacetsOpen(!sfFacetsNarrow() && sfFacetsStored() !== false, false);
  if (data.reasons && data.reasons.said) say(data.reasons.said, 9000);
  await sfRound(kept.rec || null);
  window.scrollTo(0, 0);
}

function sfTake(data) {
  SF.folder = data.folder;
  SF.name = data.name || '';
  SF.records = data.records || [];
  SF.byId = new Map(SF.records.map((r) => [r.rec_id, r]));
  SF.reasons = data.reasons || { ta: [], ft: [] };
  SF.counts = data.counts || null;
  SF.undo = data.undo || null;
  SF.stamp = data.stamp || null;
  SF.aiMaster = aiOn(data.config);
  if (typeof aiPage === 'function' && data.config) aiPage(data.config);
  SF.ai = SF.aiMaster ? data.ai || null : null;
  SF.table = data.table || null;
  SF.email = typeof data.email === 'string' ? data.email : SF.email;
  SF.second = data.second || null;
  SF.review = data.review || null;
  SF.keyWorks = Array.isArray(data.key_works) ? data.key_works : SF.keyWorks;
  SF.blocks = Array.isArray(data.blocks) ? data.blocks : [];
  SF.matchHead = Array.isArray(data.match_head) ? data.match_head : SF.matchHead;
  SF.benchIds = Array.isArray(data.bench) ? data.bench : [];
  sfMarkAll();
  bandNameSet('sf-name', SF.name);
  // the review's name and its steps at the head, from its searches' script
  if (typeof rvHead === 'function') rvHead('screening', SF.review);
  sfFlowTake(data.prisma);
}

/* A record's marks at each stage, which the filters read with no page (12 October): `proposed`, a
   proposal of it shows, the app's AI switch on, and `apart`, the second screener's side holds it as a
   record where the two of you differ, beside `differs`, which the server gives, his decision against
   the proposal he saw. Marked as the screening is read and as each answer lands. */
function sfMark(r) {
  const two = SF.second && SF.second.records ? SF.second.records[r.rec_id] || {} : {};
  for (const stage of ['ta', 'ft']) {
    const st = (r.stages || {})[stage];
    if (!st) continue;
    st.proposed = !!SF.aiMaster && (st.proposals || []).length > 0;
    st.apart = !!(two[stage] || {}).differs;
  }
}

const sfMarkAll = () => SF.records.forEach(sfMark);

/* Full text, the next stage, once a record has passed title and abstract, with Yes or Maybe there (12
   October) */
const sfFtOn = () => !!(SF.counts && SF.counts.stages && SF.counts.stages.ft && Number(SF.counts.stages.ft.records));

/* A stage chosen from the review's steps on this screen, its records asked afresh, Full text only once
   a record has passed title and abstract (12 October), and Extract and appraise, `ex`, standing at full
   text underneath (13 October, later) */
function sfStageTo(stage) {
  if (!['ta', 'ft', 'ex'].includes(stage) || (SF.form ? 'ex' : SF.stage) === stage || (stage === 'ft' && !sfFtOn())) return;
  SF.form = stage === 'ex';
  SF.stage = stage === 'ta' ? 'ta' : 'ft';
  SF.facetsHold = null;
  if (SF.form && SF.view === 'record') SF.picking = false;
  // its round answered, so Search can land on a record once the stage stands (18 October)
  return sfRound(null);
}

/* The stage's records asked of the server, every one of them, the table's filters and sort laid over
   them, Decision among the filters, and the place set on `land` when they hold it, else on the
   first. */
async function sfRound(land) {
  let data;
  try {
    data = SF.form ? await api('/api/sift', { op: 'form', act: 'list', folder: SF.folder })
      : await api('/api/sift', { op: 'list', folder: SF.folder, stage: SF.stage, round: 'all' });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  // Extract and appraise lists the records included at full text and the benchmark papers, one or the
  // other shown as Benchmark papers is ticked (see sfBaseIds)
  SF.formInc = new Set(SF.form ? data.ids || [] : []);
  SF.formBench = new Set(SF.form ? data.bench || [] : []);
  SF.roundIds = SF.form ? [...new Set([...(data.ids || []), ...(data.bench || [])])] : data.ids || [];
  sfApply(land);
  SF.picking = false;
  SF.tvReveal = true;
  sfDraw();
  sfFiltersKeep();
}

/* the round's records as the server gave them, each record itself */
const sfRoundRows = () => sfBaseIds().map((id) => SF.byId.get(id)).filter(Boolean);

/* The records the two views walk: the round's, through the table's filters, in its sort. The ticks
   are read first, whatever form they were held in, and those no group offers are let go. */
function sfApply(land) {
  const cols = sfAllCols();
  const base = sfBaseIds();
  const bench = SF.form ? tbTicks(SF.filters, SF_BENCH) : [];
  SF.filters = sfTicksRead(SF.filters, sfGroups(sfRoundRows(), SF.records, cols, SF.stage, sfCodes(), {}));
  if (bench.length) SF.filters[SF_BENCH] = bench;
  const read = sfRead(SF.stage);
  SF.ids = tbSortRows(tbFilterRows(base, SF.byId, SF.filters, cols, read), SF.byId, SF.sort, cols, read);
  const at = land ? SF.ids.indexOf(land) : -1;
  SF.at = at >= 0 ? at : 0;
}

/* ── drawing ── */

/* stage 2 before any record has passed stage 1, with Yes or Maybe there */
const sfFtEmpty = () => (SF.form ? !SF.roundIds.length : SF.stage === 'ft' && !!(SF.counts && SF.counts.stages && SF.counts.stages.ft)
  && !Number(SF.counts.stages.ft.records));

/* A decision as a pill, its word always inside it beside its colour, in the words of the stage, its
   own by default, To screen grey for none, and the reason for No or Exclude a pill of its own after it,
   its code inside and its meaning from reasons.csv on hover. A proposal takes the same words. */
function sfPillHtml(decision, reason, stage = SF.stage) {
  const words = sfWords(stage);
  const d = words[decision] ? decision : '';
  return `<span class="sf-pill" data-decision="${d}">${d ? words[d] : SF_TO_SCREEN}</span>`
    + `${d === 'exclude' && reason ? sfReasonPill(reason) : ''}`;
}

/* the decision pill at a record's head, in the stage's words, and the reason pill after it with No
   or Exclude */
function sfPillSet(el, decision, reason, stage = SF.stage) {
  const words = sfWords(stage);
  const d = words[decision] ? decision : '';
  el.dataset.decision = d;
  el.textContent = d ? words[d] : SF_TO_SCREEN;
  const next = el.nextElementSibling;
  if (!next || !next.classList.contains('sf-rpill')) return;
  next.textContent = d === 'exclude' && reason ? reason : '';
  next.title = d === 'exclude' && reason ? sfMeaning(reason) : '';
}

/* The title bar, the line under it and the foot bar: the review's steps in one row, Search strategy
   and the two stages, each stage with its count and Full text greyed until a record has passed title
   and abstract, drawn by the searches' script, the tools of the view showing, the table's own on the
   line only on the table, and at the foot how many records show, or on a record where it stands
   among them, then each decision's count as a pill. */
function sfBar() {
  const all = SF.counts && SF.counts.stages ? SF.counts.stages : {};
  if (typeof rvStepsDraw === 'function') rvStepsDraw($('sf-steps'), SF.review, SF.form ? 'ex' : SF.stage, all);
  const table = SF.view === 'table';
  const empty = sfFtEmpty();
  $('sf-ft-empty').hidden = !empty;
  $('sf-ft-empty').textContent = SF.form ? SF_EMPTY_FORM : SF_EMPTY_FT;
  // Set up the form on the line over the table at Extract and appraise alone, and Export the form in
  // Export's menu while the form has a field and a record is included at full text
  $('sf-form-set').hidden = !SF.form;
  $('sf-form-export').disabled = !(sfFormFields().length && all.ft && Number(all.ft.include));
  $('sf-body').hidden = table || empty;
  $('sf-tv').hidden = !table || empty;
  $('sf-pdf-toggle').hidden = table;
  // the bar fitted again to the steps just drawn, as Idiograph's bars are once theirs are (shell.js barFit): a
  // bar watched for its own size alone kept the tools' words it no longer held, and at Text size Large in a 1280
  // window Settings stood past its right edge (zoomsweep, 30 October)
  if (typeof barFit === 'function') barFit($('sf-steps').closest('.rail'));
  // Filters, Clear all and Set columns on the table alone, and PRISMA flow on either view (12 October)
  $('sf-tv-top').dataset.view = empty ? 'empty' : SF.view;
  sfFacetsMark();
  // the band's way back to the table, there only on a record
  bandTableDraw('sf-name');
  const c = all[SF.stage] || null;
  const n = (k) => (c ? Number(c[k]) || 0 : 0);
  $('sf-count').innerHTML = empty ? ''
    : table ? t('sift.count_html', { shown: SF.ids.length, all: sfBaseIds().length })
      : t('sift.count_html', { shown: SF.ids.length ? SF.at + 1 : 0, all: SF.ids.length });
  if (SF.form) {
    // at Extract and appraise how many of the stage's records are done, in place of the decisions' counts
    const rows = sfRoundRows();
    $('sf-tally').innerHTML = sfFormFields().length && rows.length
      ? `<span class="sf-done-count">${esc(t('sift.form_done', { done: rows.filter(sfFormDone).length, all: rows.length }))}</span>` : '';
    $('sf-undo').hidden = true;
    $('sf-flow-toggle').setAttribute('aria-pressed', String(!$('sf-side').hidden));
    $('sf-two-btn').hidden = !sfTwoOn();
    $('sf-key-enter').hidden = true;
    $('sf-included').disabled = !(all.ft && Number(all.ft.include));
    return;
  }
  const pill = (d, word, k) => `<span class="sf-pill" data-decision="${d}">${word} ${n(k)}</span>`;
  // each count in the stage's words, Yes, Maybe and No or Include, Maybe and Exclude, then To screen
  const w = sfWords(SF.stage);
  $('sf-tally').innerHTML = c
    ? pill('include', w.include, 'include') + pill('maybe', w.maybe, 'maybe') + pill('exclude', w.exclude, 'exclude')
      + pill('', SF_TO_SCREEN, 'undecided')
      // the decisions against the proposals, once there is a proposal to count them by
      + (SF.aiMaster && n('matched') + n('overruled') ? `<span class="sf-against">${esc(t('sift.against', { matched: n('matched'), overruled: n('overruled') }))}</span>` : '')
    : '';
  $('sf-flow-toggle').setAttribute('aria-pressed', String(!$('sf-side').hidden));
  $('sf-two-btn').hidden = !sfTwoOn();
  // Enter on the shortcuts card while a record of the stage shows a suggestion, an AI's with the switch on alone
  $('sf-key-enter').hidden = !SF.records.some((r) => sfSuggestions(sfStage(r)).length);
  // Undo at the foot once there is a decision or a note to take back, the record and stage it takes
  // back on hover, as U does (12 October)
  const u = SF.undo;
  $('sf-undo').hidden = !u;
  $('sf-undo').title = !u ? '' : u.what === 'excerpt' ? t('sift.undo.excerpt_tip', { rec: u.rec_id })
    : u.stage === 'ft' ? t('sift.undo.tip_ft', { rec: u.rec_id }) : t('sift.undo.tip_ta', { rec: u.rec_id });
  // Export included records, in Export's menu, stands off while no record is included at full text
  const ft = all.ft || null;
  $('sf-included').disabled = !(ft && Number(ft.include));
  $('sf-included').title = $('sf-included').disabled ? t('sift.included.off_tip')
    : t('sift.included.tip');
}

/* the abstract with the grounds marked where they were found in it, and since 14 October the abstract or the
   title with `spans` laid over them too, each { start, end, cls }, his key excerpts and the pieces of the one
   being built, a word under two marks carrying both classes */
function sfMarked(text, marks, spans = []) {
  const all = (marks || []).map(([a, b]) => ({ start: a, end: b, cls: 'sf-ground' })).concat(spans)
    .filter((m) => m.end > m.start);
  const cuts = [...new Set([0, text.length, ...all.flatMap((m) => [m.start, m.end])])]
    .filter((x) => x >= 0 && x <= text.length).sort((x, y) => x - y);
  let html = '';
  for (let i = 0; i + 1 < cuts.length; i += 1) {
    const [a, b] = [cuts[i], cuts[i + 1]];
    const cls = [...new Set(all.filter((m) => m.start <= a && m.end >= b).map((m) => m.cls))];
    const chunk = esc(text.slice(a, b));
    html += cls.length ? `<mark class="${cls.join(' ')}">${chunk}</mark>` : chunk;
  }
  return html;
}

/* the grounds of every proposal shown, as one run of marks in order, an overlap joined */
function sfMarks(props) {
  const all = props.flatMap((p) => p.marks || []).map(([a, b]) => [a, b]).sort((x, y) => x[0] - y[0] || x[1] - y[1]);
  const out = [];
  for (const [a, b] of all) {
    const last = out[out.length - 1];
    if (last && a <= last[1]) last[1] = Math.max(last[1], b);
    else out.push([a, b]);
  }
  return out;
}

function sfMeaning(code) {
  const found = sfCodes().find((r) => r.code === code);
  return found ? found.meaning : '';
}

/* the record's PDF as the server serves it, from the screening's own pdfs folder */
function sfPdfUrl(r) {
  const query = { folder: SF.folder, rec: r.rec_id };
  if (SF.pdfAt[r.rec_id]) query.v = String(SF.pdfAt[r.rec_id]);
  return `/sift/pdf?${new URLSearchParams(query)}`;
}

/* The line that names the words marked in the abstract, the grounds of the review's proposal, of
   Sift's own or of both, and since 14 October Key excerpts, each in its mark's colour, with Hide or Show,
   which hides or shows both, shown only while a proposal's grounds or a key excerpt of the record `r` are
   marked. */
function sfGroundsLine(props, r) {
  const marked = props.filter((p) => (p.marks || []).length);
  const kept = !!r && sfExShown(r).length > 0;
  $('sf-gline').hidden = !marked.length && !kept;
  if ($('sf-gline').hidden) return;
  $('sf-gline-said').hidden = !marked.length;
  $('sf-gline-said').textContent = !marked.length ? '' : marked.length > 1 ? SF_GROUNDS_BOTH : SF_GROUNDS[marked[0].source] || SF_GROUNDS.csv;
  $('sf-gline-ex').hidden = !kept;
  $('sf-gline-btn').textContent = SF.marksHidden ? t('sift.marks.show') : t('sift.marks.hide');
  $('sf-gline').classList.toggle('off', SF.marksHidden);
}

function sfMarksStored() {
  try { return localStorage.getItem(SF_MARKS_KEY) === 'hidden'; } catch { return false; }
}

function sfMarksHide(hidden) {
  SF.marksHidden = hidden;
  try { localStorage.setItem(SF_MARKS_KEY, hidden ? 'hidden' : 'shown'); } catch { /* private window */ }
  sfDraw();
}

function sfDraw() {
  sfBar();
  if (sfFtEmpty()) {
    sfReasonsDraw();
    sfKeepPlace();
    return;
  }
  if (SF.view === 'table') {
    sfTvDraw();
    sfKeepPlace();
    return;
  }
  const r = sfRecord();
  $('sf-none').hidden = !!r;
  $('sf-card').hidden = !r;
  sfPdf(r);
  sfKeepPlace();
  sfHistoryKeep();
  sfReasonsDraw();
  if (!r) return;
  // the pieces of a key excerpt being built belong to the record they were taken from
  if (SF.piecesFor !== r.rec_id) { SF.pieces = []; SF.piecesFor = r.rec_id; }
  const st = sfStage(r);
  // the record named by its ID, Record R010, as the table's first column names it (13 October), then
  // where it stands as a pill
  $('sf-num').textContent = t('sift.record_num', { rec: r.rec_id });
  sfPillSet($('sf-pill'), st.decision, st.reason);
  // at full text, where the record stood at title and abstract, Yes or Maybe (12 October)
  $('sf-tadec').hidden = SF.stage !== 'ft';
  if (SF.stage === 'ft') sfPillSet($('sf-tadec-pill'), ((r.stages || {}).ta || {}).decision, '', 'ta');
  // its year, No year when it has none (12 October), and its journal
  $('sf-meta').textContent = [r.year || SF_BLANK_WORDS.year, r.journal].filter(Boolean).join(' · ');
  // the title, its key excerpts marked in it (14 October), and beside it a plain word when the paper was
  // retracted, questioned or corrected (13 October)
  $('sf-title').innerHTML = `<span class="sf-title-text" id="sf-title-text">${sfTitleHtml(r)}</span>${sfNoticeTags(r)}`;
  $('sf-authors').textContent = r.authors;
  $('sf-authors').hidden = !r.authors;
  // the DOI and the record's web address as links that open a new tab, its PDF opened the same way
  // or Add PDF, its count of citations with the day OpenAlex gave it on hover, and the databases that
  // found it under the word Database, each a pill in its colour
  const links = [];
  if (r.doi) links.push(`<a href="${escAttr(r.link)}" target="_blank" rel="noopener noreferrer">${esc(r.doi)}</a>`);
  if (r.url) links.push(`<a href="${escAttr(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.url)}</a>`);
  links.push(r.pdf ? `<a href="${escAttr(sfPdfUrl(r))}" target="_blank" rel="noopener">PDF</a>`
    : `<button type="button" class="ghost small" data-act="add-pdf">${esc(t('sift.add_pdf'))}</button>`);
  if (typeof r.cited === 'number') links.push(`<span class="sf-cited"${sfCitedTitle(r)}>${esc(t('sift.cited_by', { n: r.cited }))}</span>`);
  if ((r.found || []).length) {
    links.push(`<span class="sf-dbs"><span class="sf-dbs-word">${esc(SF_COLS.found.label)}</span>${r.found.map(sfDbPill).join('')}</span>`);
  }
  $('sf-links').innerHTML = links.join('<span class="sf-dot"> · </span>');
  $('sf-links').hidden = !links.length;
  // at Extract and appraise the record's form stands under its links, in place of the screening's parts
  $('sf-form').hidden = !SF.form;
  $('sf-screening-parts').hidden = SF.form;
  $('sf-fm-done').hidden = true;
  if (SF.form) {
    sfFormDraw(r);
    return;
  }
  // the suggestions, the review's first and then Sift's own, an AI's with the app's AI switch on and one by
  // keyword rules or that says nothing either way (see sfSuggestions), each under its title, the sparkles
  // on an AI's alone, then its decision as a pill, a reason for No or Exclude as a pill with its meaning
  // beside it, its grounds under it when the abstract does not hold them word for word, and Accept
  // suggestion in the suggested decision's colour, where the stage knows the decision
  const props = sfSuggestions(st);
  sfGroundsLine(props, r);
  $('sf-abstract').innerHTML = r.abstract ? sfAbstractHtml(r, SF.marksHidden ? [] : sfMarks(props))
    : `<span class="sf-empty">${esc(t('sift.no_abstract'))}</span>`;
  [['', props[0]], ['-2', props[1]]].forEach(([s, prop]) => {
    const box = $(`sf-proposal${s}`);
    box.hidden = !prop;
    if (!prop) return;
    box.dataset.decision = prop.decision || '';
    $(`sf-prop-word${s}`).innerHTML = sfWords(SF.stage)[prop.decision] ? sfPillHtml(prop.decision, '') : '';
    const said = sfSuggestionOf(prop);
    $(`sf-prop-spark${s}`).hidden = !said.ai;
    $(`sf-prop-said${s}`).textContent = said.title;
    $(`sf-prop-title${s}`).title = said.tip.replace('{model}', prop.model || '');
    const take = $(`sf-take${s}`);
    take.hidden = !sfWords(SF.stage)[prop.decision];
    take.dataset.decision = take.hidden ? '' : prop.decision;
    // on hover what the decision does there, as its own button says (see sfActsDraw)
    take.title = take.hidden ? '' : SF_SAYS[SF.stage === 'ft' ? 'ft' : 'ta'][prop.decision];
    $(`sf-prop-reason${s}`).innerHTML = sfPropReasonHtml(prop);
    $(`sf-prop-reason${s}`).hidden = !prop.reason;
    const lost = prop.found === false && prop.grounds;
    $(`sf-grounds${s}`).hidden = !lost;
    $(`sf-grounds${s}`).innerHTML = lost ? t('sift.grounds_lost_html', { grounds: esc(prop.grounds) }) : '';
  });
  sfAiDraw();
  $('sf-acts').querySelectorAll('.sf-act').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.decision === st.decision)));
  sfActsDraw();
  $('sf-code').textContent = st.decision === 'exclude' && st.reason ? ` ${st.reason}` : '';
  if (document.activeElement !== $('sf-note') || SF.noteFor !== `${r.rec_id}|${SF.stage}`) {
    $('sf-note').value = st.note || '';
    SF.noteFor = `${r.rec_id}|${SF.stage}`;
  }
  sfExList(r);
  sfFieldsDraw(r);
  sfTwoRecDraw(r);
  sfStudyDraw(r);
  sfFactsDraw(r);
  sfTermsDraw(r);
  // the columns beyond the head, a value that is one web address a link that opens a new tab, the
  // databases an abstract came from and the publication type as pills
  const more = r.more || [];
  $('sf-more').hidden = !more.length;
  $('sf-more').innerHTML = more.map(([k, v]) => `<div><dt>${esc(sfExtraLabel(k))}</dt><dd>${sfReviewCell(k, v)}</dd></div>`).join('');
}

/* "R2", "R2 and R5", "R2, R5 and R9", as the language joins a list */
const sfAnd = (list) => tList(list);

/* The record's study (13 October): the study he linked it to with its other reports, and Unlink, then
   Sift's suggestions of reports of the same study, each its reasons, the strongest first, the other
   record's title and Same study, which links the two, never a link by itself, and last Same study as a
   record named by its ID, for a report Sift did not suggest. Drawn again only when it changes, so an ID
   being typed keeps its place. */
function sfStudyDraw(r) {
  const box = $('sf-study');
  const now = r.study ? `<p class="sf-study-now"><span>${esc(r.study)}${(r.study_with || []).length ? esc(t('sift.study.with', { others: sfAnd(r.study_with) })) : ''}</span>`
    + `<button type="button" class="ghost small" data-study="unlink">${esc(t('sift.study.unlink'))}</button></p>` : '';
  const ideas = (r.suggest || []).map((s) => `<div class="sf-suggest"><p class="sf-suggest-line">${esc(s.reasons[0])}</p>`
    + `${s.reasons.length > 1 ? `<p class="sf-suggest-more">${esc(s.reasons.slice(1).join('. '))}.</p>` : ''}`
    + `<p class="sf-suggest-title">${esc(s.title)}${s.year ? ` (${esc(s.year)})` : ''}${s.study ? esc(t('sift.study.in', { study: s.study })) : ''}</p>`
    + `<button type="button" class="ghost small" data-study="link" data-with="${escAttr(s.rec_id)}">${esc(t('sift.study.same'))}</button></div>`).join('');
  const html = `<span class="sf-flabel">${esc(t('sift.study.head'))}</span><div class="sf-study-body">${now}${ideas}`
    + `<p class="sf-study-as"><input type="text" id="sf-study-id" placeholder="${escAttr(t('sift.study.record_id'))}" aria-label="${escAttr(t('sift.study.as_label'))}"`
    + ` spellcheck="false" autocomplete="off"><button type="button" class="ghost small" data-study="as">${esc(t('sift.study.same'))}</button></p></div>`;
  if (box.dataset.html === html && box.dataset.rec === r.rec_id) return;
  const typed = box.dataset.rec === r.rec_id && $('sf-study-id') ? $('sf-study-id').value : '';
  box.innerHTML = html;
  box.dataset.html = html;
  box.dataset.rec = r.rec_id;
  $('sf-study-id').value = typed;
}

/* Same study and Unlink sent to the server, one act after another as the decisions are, and every
   record the link moved drawn as the answer lands */
function sfStudy(act, rec, other) {
  sfQueue(async () => {
    sfLand(await api('/api/sift', { op: 'study', folder: SF.folder, act, rec_id: rec, with: other }));
    sfDraw();
  });
}

/* Same study as the record whose ID is typed, its case set aside */
function sfStudyAs() {
  const r = sfRecord();
  const typed = ($('sf-study-id') ? $('sf-study-id').value : '').trim();
  if (!r || !typed) return;
  const hit = SF.byId.has(typed) ? typed : SF.records.map((x) => x.rec_id).find((id) => id.toLowerCase() === typed.toLowerCase());
  if (!hit) { say(t('sift.study.no_record', { rec: typed })); return; }
  $('sf-study-id').value = '';
  sfStudy('link', r.rec_id, hit);
}

/* What OpenAlex and Crossref say of the record (13 October), each in plain words and Unknown while it
   was never asked: Retracted or corrected with each notice's date and its DOI as a link, Open access
   with where the paper is open, Country, and Cites key works while the review has key works, which says
   why where Sift cannot check them (14 October, later) */
function sfFactsDraw(r) {
  const kinds = sfNoticeKinds(r);
  // a notice's day, or its month alone, November 2030, where Crossref gives no day
  const day = (d) => (/^\d{4}-\d{2}$/.test(d) ? tbDayWords(`${d}-01`).replace(/^1 /, '') : tbDayWords(d));
  const notices = ((r.notices || {}).list || []).map((n) => {
    const kind = esc(SF_NOTICE_WORDS[n.kind] || n.kind);
    const head = n.date ? t('sift.notice.dated', { kind, day: esc(day(n.date)) }) : kind;
    if (n.doi) {
      const doi = `<a href="${escAttr(`https://doi.org/${n.doi}`)}" target="_blank" rel="noopener noreferrer">${esc(n.doi)}</a>`;
      return t('sift.notice.doi_html', { head, doi });
    }
    return n.from ? t('sift.notice.says', { head, from: esc(n.from) }) : head;
  });
  const rows = [[SF_COLS.retracted.label, kinds === null ? sfBlankHtml('retracted')
    : kinds.length ? notices.join('<br>') || esc(kinds.map((k) => SF_NOTICE_WORDS[k]).join(', ')) : SF_NOTICE_WORDS.none],
  [SF_COLS.oa.label, !r.oa ? sfBlankHtml('oa') : r.oa === 'closed' ? esc(t('sift.oa.closed')) : esc(t('sift.oa.open_as', { how: SF_OA_WORDS[r.oa] || r.oa }))],
  [SF_COLS.country.label, (r.countries || []).length ? esc(r.countries.join(', ')) : sfBlankHtml('country')]];
  if ((SF.keyWorks || []).length) {
    rows.push([SF_COLS.keyworks.label, !Array.isArray(r.cites) ? `<span class="sf-blank">${SF_CITES_UNCHECKED}</span>` : r.cites.length
      ? r.cites.map((k) => `<span class="sf-cat">${esc((sfKeyWork(k) || {}).label || k)}</span>`).join('') : SF_NOTICE_WORDS.none]);
  }
  $('sf-facts').innerHTML = rows.map(([t, d]) => `<div><dt>${esc(t)}</dt><dd>${d}</dd></div>`).join('');
  // a record never asked of either service shows none of it, its table cells reading Unknown
  $('sf-facts').hidden = kinds === null && !r.oa && !(r.countries || []).length && !Array.isArray(r.cites)
    && !r.openalex_date && !r.crossref_date;
}

/* The three decisions' buttons in the stage's words, Yes, Maybe and No at title and abstract and
   Include, Maybe and Exclude at full text, each with its key and on hover what it does there, Maybe's
   at title and abstract going on to full text marked unsure (12 October, later). */
function sfActsDraw() {
  const stage = SF.stage === 'ft' ? 'ft' : 'ta';
  const words = sfWords(stage);
  $('sf-acts').querySelectorAll('.sf-act').forEach((b) => {
    const d = b.dataset.decision;
    b.querySelector('.sf-act-word').textContent = words[d];
    b.querySelector('.sf-act-key').textContent = SF_KEYS[stage][d];
    b.title = SF_SAYS[stage][d];
  });
}

/* The shortcuts card's decisions in the stage's words and keys, drawn as it opens, then the card shown */
function sfKeysOpen() {
  const stage = SF.stage === 'ft' ? 'ft' : 'ta';
  const words = sfWords(stage);
  ['include', 'maybe', 'exclude'].forEach((d) => {
    $(`sf-kk-${d}`).textContent = d === 'exclude' ? `${SF_KEYS[stage][d]}, then a number` : SF_KEYS[stage][d];
    $(`sf-kw-${d}`).textContent = d === 'exclude' ? t('sift.keys.for_reason', { word: words[d] }) : words[d];
  });
  $('sf-keys').hidden = false;
}

/* a value as a link when it is one web address and nothing else, else as text */
function sfLinked(value) {
  const v = String(value || '').trim();
  return /^https?:\/\/[^\s<>"']+$/i.test(v) ? `<a href="${escAttr(v)}" target="_blank" rel="noopener noreferrer">${esc(v)}</a>` : esc(value);
}

/* the choices the reasons offer at the stage: at title and abstract No reason first, since a reason is
   optional there, then the stage's codes, and at full text the codes alone, as one is required there
   (12 October, later) */
const sfReasonChoices = () => (SF.stage === 'ta' ? [{ code: '', meaning: t('sift.no_reason'), none: true }] : []).concat(sfCodes());

/* The reasons of the stage, a short list over the record or the table once No or N is pressed at title
   and abstract, Exclude or E at full text, R at either, numbered for the keys, No reason 0 at title and
   abstract, the proposal's code chosen when the proposal was No or Exclude, else the one he gave before. One is taken by a press or its number, and Esc or
   a press beside the list cancels. */
function sfReasonsDraw() {
  const list = $('sf-reasons');
  $('sf-why').hidden = !SF.picking;
  if (!SF.picking) { list.innerHTML = ''; return; }
  const r = sfRecord();
  // in the stage's words, Reason for No on record R012, Reason to exclude record R012, the record by
  // its ID (13 October)
  const ft = SF.stage === 'ft';
  $('sf-why-head').textContent = r ? (ft ? t('sift.why.ft_record', { rec: r.rec_id }) : t('sift.why.ta_record', { rec: r.rec_id }))
    : (ft ? t('sift.why.ft') : t('sift.why.ta'));
  const choices = sfReasonChoices();
  const off = choices.length - sfCodes().length;
  list.innerHTML = choices.map((c, i) => `<li><button type="button" role="radio" data-i="${i}" aria-checked="${i === SF.pick}"`
    + ` class="sf-reason${i === SF.pick ? ' on' : ''}${c.none ? ' sf-reason-none' : ''}"><span class="mono sf-n">${i - off < 9 ? i - off + 1 : ''}</span>`
    + `<span class="mono sf-rc">${esc(c.code)}</span><span class="sf-rm">${esc(c.meaning)}</span></button></li>`).join('');
  list.querySelectorAll('button').forEach((b) => { b.onclick = () => sfDecide('exclude', sfReasonChoices()[Number(b.dataset.i)].code, true); });
}

function sfPreselect() {
  const r = sfRecord();
  const st = sfStage(r);
  const choices = sfReasonChoices().map((c) => c.code);
  const off = choices.length - sfCodes().length;
  if (st && st.decision === 'exclude' && (st.reason ? choices.slice(off).includes(st.reason) : off)) {
    return st.reason ? choices.indexOf(st.reason, off) : 0;
  }
  const prop = sfSuggestions(st)[0] || {};
  if (prop.decision === 'exclude' && prop.reason && choices.slice(off).includes(prop.reason)) return choices.indexOf(prop.reason, off);
  return -1;
}

/* ── the PRISMA flow ── */

/* the vendored Mermaid, loaded from the app the first time the flow is drawn, never from the web */
let sfMermaidLoad = null;
function sfMermaid() {
  if (window.mermaid) return Promise.resolve(window.mermaid);
  if (!sfMermaidLoad) {
    sfMermaidLoad = new Promise((resolve, reject) => {
      const tag = document.createElement('script');
      tag.src = SF_MERMAID;
      tag.onload = () => (window.mermaid ? resolve(window.mermaid) : reject(new Error(t('sift.flow_not_drawn'))));
      tag.onerror = () => { sfMermaidLoad = null; reject(new Error(t('sift.flow_not_drawn'))); };
      document.head.appendChild(tag);
    });
  }
  return sfMermaidLoad;
}

function sfFlowTake(source) {
  if (typeof source !== 'string' || !source) return;
  SF.prisma = source;
  sfFlow();
}

/* the flow drawn again, one drawing after another, when its words or the theme's colours changed */
function sfFlow() {
  SF.flowChain = SF.flowChain.then(sfFlowDraw).catch(() => { SF.flowDrawn = ''; });
  return SF.flowChain;
}

async function sfFlowDraw() {
  const source = SF.prisma;
  // never into the shut sidebar, where it would measure nothing
  if (!source || !sfShown() || $('sf-side').hidden) return;
  const css = getComputedStyle(document.documentElement);
  const tok = (name) => css.getPropertyValue(name).trim();
  const tone = ['--paper', '--card', '--ink', '--ink-soft', '--ink-faint', '--rule-firm'].map(tok).join(' ');
  const want = `${tone}\n${source}`;
  if (want === SF.flowDrawn) return;
  const m = await sfMermaid();
  m.initialize({
    startOnLoad: false, securityLevel: 'strict', theme: 'base', fontFamily: tok('--sans') || 'sans-serif',
    flowchart: { htmlLabels: true, useMaxWidth: true, nodeSpacing: 12, rankSpacing: 22, padding: 6, curve: 'basis' },
    themeVariables: {
      fontSize: '12px', background: tok('--paper'), primaryColor: tok('--card'), mainBkg: tok('--card'),
      primaryTextColor: tok('--ink'), textColor: tok('--ink'), primaryBorderColor: tok('--rule-firm'),
      nodeBorder: tok('--rule-firm'), lineColor: tok('--ink-faint'),
    },
  });
  SF.flowN += 1;
  const { svg } = await m.render(`sf-flow-svg-${SF.flowN}`, source);
  if (SF.prisma !== source) return;
  $('sf-flow').innerHTML = svg;
  SF.flowDrawn = want;
}

const sfNarrow = () => { try { return window.matchMedia(SF_NARROW).matches; } catch { return false; } };

/* the sidebar's state as this browser keeps it, true open, false shut, null never set */
function sfFlowStored() {
  try {
    const held = localStorage.getItem(SF_FLOW_KEY);
    return held === null ? null : held === 'open';
  } catch { return null; }
}

/* The PRISMA flow's sidebar opened or shut, from the line under the title bar on either view, kept in
   this browser unless `keep` is false, and the flow drawn as it opens. Its left edge stands beside
   it while it is open (12 October). */
function sfFlowOpen(open, keep = true) {
  $('sf-side').hidden = !open;
  $('sf-side-edge').hidden = !open;
  $('sf-flow-toggle').setAttribute('aria-pressed', String(open));
  if (keep) {
    try { localStorage.setItem(SF_FLOW_KEY, open ? 'open' : 'shut'); } catch { /* private window */ }
  }
  if (open) sfFlow();
}

/* ── the filters' sidebar ── */

const sfFacetsNarrow = () => { try { return window.matchMedia(SF_FACETS_NARROW).matches; } catch { return false; } };

/* the filters' sidebar as this browser keeps it, true open, false shut, null never set */
function sfFacetsStored() {
  try {
    const held = localStorage.getItem(SF_FACETS_KEY);
    return held === null ? null : held === 'open';
  } catch { return null; }
}

/* The filters' sidebar at the left of the table opened or shut, from its toggle at the top left of
   the table, over the sidebar it opens, kept in this browser unless `keep` is false, as a screening
   opens, when the round drawn next draws it. Opened by a press, it is drawn at once. Its right edge
   stands beside it while it is open. Opened, it is drawn afresh, every group in its count's order. */
function sfFacetsOpen(open, keep = true) {
  if (open && $('sf-facets').hidden) SF.facetsHold = null;
  $('sf-facets').hidden = !open;
  $('sf-facets-edge').hidden = !open;
  $('sf-facets-toggle').setAttribute('aria-pressed', String(open));
  sfFacetsMark();
  if (!keep) return;
  try { localStorage.setItem(SF_FACETS_KEY, open ? 'open' : 'shut'); } catch { /* private window */ }
  if (open) sfFacetsDraw();
}

/* The filters' toggle at the top left of the table (12 October): its funnel and its word, with how
   many filters are on, Filters (2), a group with anything set counting one, open or shut, and Clear
   all beside it while anything is set, a tick, a slider or words in a find box. */
function sfFacetsMark() {
  const n = Object.keys(SF.filters || {}).length;
  const words = n > 0 ? t('sift.filters_n', { n }) : t('sift.filters');
  const btn = $('sf-facets-toggle');
  btn.title = words;
  btn.setAttribute('aria-label', words);
  btn.dataset.count = String(n > 0);
  $('sf-facets-word').textContent = words;
  $('sf-facets-clear').hidden = !n && !Object.values(SF.facetsFind || {}).some((w) => String(w).trim());
}

/* ── the two sidebars' widths ── */

/* Each sidebar that drags wider or narrower by an edge (12 October): the filters at the table's left,
   their edge at their right, and the PRISMA flow at the right of either view, its edge at its left.
   Each has its width at first, its narrowest and its widest, how far an arrow key on its edge moves
   it, which way the edge widens it, `way`, 1 to the right and -1 to the left, the key sift.json
   keeps it under in the table's settings, `table`, and the name the view op takes it by, `op`. */
const SF_EDGES = {
  facets: { box: 'sf-facets', edge: 'sf-facets-edge', prop: '--sf-facets-w', first: 220, min: 180, max: 560, step: 16,
    way: 1, table: 'sidebar', op: 'filters' },
  flow: { box: 'sf-side', edge: 'sf-side-edge', prop: '--sf-side-w', first: 300, min: 240, max: 720, step: 16,
    way: -1, table: 'flow', op: 'flow' },
};

/* A sidebar's width as sift.json keeps it for the screening, or the width at first, set on it and on
   its edge for a screen reader. The flow's diagram takes the width it is given. */
function sfEdgeWidth(which, w) {
  const s = SF_EDGES[which];
  const n = Number(w);
  const width = Number.isFinite(n) && n > 0 ? Math.max(s.min, Math.min(s.max, Math.round(n))) : null;
  const box = $(s.box);
  if (width) box.style.setProperty(s.prop, `${width}px`);
  else box.style.removeProperty(s.prop);
  const edge = $(s.edge);
  edge.setAttribute('aria-valuemin', String(s.min));
  edge.setAttribute('aria-valuemax', String(s.max));
  edge.setAttribute('aria-valuenow', String(width || s.first));
  return width;
}

/* the width he left a sidebar at, kept in sift.json for the screening through the server */
function sfEdgeKeep(which, w) {
  const s = SF_EDGES[which];
  const width = sfEdgeWidth(which, w);
  if (!SF.folder || !width) return;
  SF.table = Object.assign({}, SF.table, { [s.table]: width });
  const folder = SF.folder;
  sfQueue(() => api('/api/sift', { op: 'view', folder, sidebar: { [s.op]: width } }));
}

/* A sidebar's edge dragged wider or narrower, its width following the pointer and kept once it is
   let go, or moved by the arrow keys a step at a time, Home and End to its narrowest and its widest */
function sfEdgeBoot(which) {
  const s = SF_EDGES[which];
  const edge = $(s.edge);
  edge.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    const from = $(s.box).getBoundingClientRect().width;
    const x0 = e.clientX;
    let now = from;
    edge.setPointerCapture(e.pointerId);
    edge.classList.add('dragging');
    const move = (ev) => { now = sfEdgeWidth(which, from + s.way * (ev.clientX - x0)) || now; };
    const done = () => {
      edge.removeEventListener('pointermove', move);
      edge.removeEventListener('pointerup', done);
      edge.removeEventListener('pointercancel', done);
      edge.classList.remove('dragging');
      if (Math.round(now) !== Math.round(from)) sfEdgeKeep(which, now);
    };
    edge.addEventListener('pointermove', move);
    edge.addEventListener('pointerup', done);
    edge.addEventListener('pointercancel', done);
  });
}

/* a key on a sidebar's edge: the arrows move the edge a step left or right, narrower or wider as the
   edge stands, Home and End to its limits. Answers whether it took the key. */
function sfEdgeKey(e) {
  const which = Object.keys(SF_EDGES).find((k) => e.target === $(SF_EDGES[k].edge));
  if (!which) return false;
  const s = SF_EDGES[which];
  const now = $(s.box).getBoundingClientRect().width || s.first;
  const to = { ArrowLeft: now - s.way * s.step, ArrowRight: now + s.way * s.step, Home: s.min, End: s.max }[e.key];
  if (to === undefined) return false;
  e.preventDefault();
  sfEdgeKeep(which, to);
  return true;
}

// how long after the last letter typed in a find box its words wait to be kept, so they are kept once
// he pauses
const SF_KEEP_WAIT = 400;

/* The filters and the find boxes' words kept in sift.json for the screening when they changed since
   it last kept them, through the server like every act, at once after a tick, a slider, a Clear, a
   round or a column, and with `now` false a moment after the last letter typed in a find box, or as
   the screen is left if that is sooner. */
function sfFiltersKeep(now = true) {
  clearTimeout(SF.keepTimer);
  SF.keepTimer = null;
  if (!SF.folder) return;
  const held = sfKeptJson(SF.filters, SF.facetsFind);
  if (held === SF.kept) return;
  const folder = SF.folder;
  const send = () => {
    SF.keepTimer = null;
    if (SF.folder === folder) SF.kept = held;
    sfQueue(() => api('/api/sift', Object.assign({ op: 'view', folder }, JSON.parse(held))));
  };
  if (now) send();
  else SF.keepTimer = setTimeout(send, SF_KEEP_WAIT);
}

/* ── the PDF ── */

function sfPdfStored() {
  try { return localStorage.getItem(SF_PDF_KEY) === 'shut'; } catch { return false; }
}

function sfPdfShut(shut) {
  $('sf-body').classList.toggle('pdf-shut', shut);
  $('sf-pdf-toggle').setAttribute('aria-pressed', String(!shut));
  try { localStorage.setItem(SF_PDF_KEY, shut ? 'shut' : 'open'); } catch { /* private window */ }
  if (!shut) sfPdf(sfRecord());
}

/* the record's PDF in the pane, served from the screening's own pdfs folder, or the line that there is none */
function sfPdf(r) {
  const frame = $('sf-frame');
  const has = !!(r && r.pdf);
  $('sf-nopdf').hidden = has;
  frame.hidden = !has;
  if ($('sf-body').classList.contains('pdf-shut')) return;
  // the viewer opened at the pane's width, its page list folded away, and a PDF just dropped
  // asked for afresh
  const want = has ? `${sfPdfUrl(r)}#view=FitH&navpanes=0` : null;
  if (want === SF.frameFor) return;
  SF.frameFor = want;
  if (want) frame.src = want;
  else frame.removeAttribute('src');
}

const sfFiles = (e) => !!(e.dataTransfer && Array.from(e.dataTransfer.types || []).includes('Files'));
// an Excel workbook dragged, as the browser names its type while it is dragged, for the second screener's side
const SF_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
const sfXlsx = (e) => !!(e.dataTransfer && Array.from(e.dataTransfer.items || []).some((i) => i.kind === 'file' && i.type === SF_XLSX));
const sfOnRecord = (e) => SF.view === 'record' && !$('sf-body').hidden && !!(e.target && e.target.closest && e.target.closest('#sf-body'));

/* A file dragged over a record lays a layer over its PDF pane, so the PDF viewer never takes the
   drop, and the record and the pane both take it. A workbook returned by the second screener is taken
   anywhere on the screen, and any other drop elsewhere goes nowhere. */
function sfDrag(e) {
  if (!sfShown() || !sfFiles(e)) return;
  e.preventDefault();
  const book = sfXlsx(e);
  if (SF.view === 'record' && !book) $('sf-body').classList.add('dragging');
  if (e.dataTransfer) e.dataTransfer.dropEffect = book || sfOnRecord(e) ? 'copy' : 'none';
}

function sfDragEnd(e) {
  if (!sfShown()) return;
  if (e.type === 'dragleave' && e.relatedTarget) return;
  $('sf-body').classList.remove('dragging');
}

function sfDrop(e) {
  if (!sfShown() || !sfFiles(e)) return;
  e.preventDefault();
  $('sf-body').classList.remove('dragging');
  const file = e.dataTransfer.files && e.dataTransfer.files[0];
  if (file && /\.xlsx$/i.test(file.name || '')) sfTwoTakeFile(file);
  else if (file && sfOnRecord(e)) sfDropPdf(file);
}

/* Add PDF: the Mac's file dialog for one PDF, kept for the record showing as a dropped one is */
function sfPdfChoose() {
  if (!sfRecord()) return;
  const input = $('sf-pdf-file');
  input.value = '';
  input.click();
}

/* A PDF dropped on the record or chosen with Add PDF, kept as pdfs/<rec_id>.pdf for the record
   showing through the pdf op, after asking when the record has one already, then shown in the pane
   and opened from the record's PDF link. Nothing is fetched from the web. */
async function sfDropPdf(file) {
  const r = sfRecord();
  if (!r) return;
  if (!/\.pdf$/i.test(file.name || '') && file.type !== 'application/pdf') { say(t('sift.pdf.not_pdf')); return; }
  try {
    const data = await tbBase64(file);
    const ask = (replace) => api('/api/sift', { op: 'pdf', folder: SF.folder, rec_id: r.rec_id, data, replace });
    let got = await ask(false);
    if (got.exists && !got.saved) {
      if (!(await sfAsk(t('sift.pdf.replace_head'), t('sift.pdf.replace_line', { rec: r.rec_id, file: file.name }), t('sift.pdf.replace')))) return;
      got = await ask(true);
    }
    SF.pdfAt[r.rec_id] = Date.now();
    sfLand(got);
    sfDraw();
    say(t('sift.pdf.kept', { rec: r.rec_id }));
  } catch (err) { say(err.message, 9000); }
}

/* ── the acts ── */

/* one act after another, in the order he made them, each answer drawn as it lands */
function sfQueue(work) {
  SF.chain = SF.chain.then(work).catch((err) => say(needsRestart(err) ? RESTART_LINE : err.message, 9000));
  return SF.chain;
}

function sfLand(data) {
  if (data.counts) SF.counts = data.counts;
  if (data.second) SF.second = data.second;
  if ('undo' in data) SF.undo = data.undo;
  if (data.stamp) SF.stamp = data.stamp;
  // the record of the act, and every record a link of a study moved with it (13 October)
  const moved = [...(data.record ? [data.record] : []), ...(Array.isArray(data.records) ? data.records : [])];
  moved.forEach((rec) => {
    const i = SF.records.findIndex((r) => r.rec_id === rec.rec_id);
    if (i >= 0) SF.records[i] = rec;
    SF.byId.set(rec.rec_id, rec);
  });
  if (data.second) sfMarkAll();
  else if (data.record) sfMark(data.record);
  if (!data.second && Array.isArray(data.records)) data.records.forEach(sfMark);
  sfFlowTake(data.prisma);
}

/* His decision on the record in front of him, with the note as the field has it, drawn at once and
   the place moved on to the next record shown, so the keys keep pace with him, and the
   server's answer drawn over it as it lands. No or Exclude with no reason while the stage has codes opens
   the reasons, unless `chosen` says the reason was chosen there, No reason at title and abstract among
   them. One the server refuses says why, and the screening is read again as it stands. */
function sfDecide(decision, reason = '', chosen = false) {
  const r = sfRecord();
  if (!r) return;
  if (decision === 'exclude' && !reason && !chosen && sfCodes().length) { sfPicking(true); return; }
  SF.picking = false;
  // the table has no note field, so a decision there leaves the note as it stands
  const note = SF.view === 'table' ? undefined : $('sf-note').value;
  const stage = SF.stage;
  Object.assign(r.stages[stage], { decision, reason: decision === 'exclude' ? reason : '' },
    note === undefined ? {} : { note: note.trim() });
  if (SF.at < SF.ids.length - 1) SF.at += 1;
  else say(t('sift.last_shown'));
  if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
  SF.tvReveal = true;
  sfDraw();
  sfQueue(async () => {
    try {
      sfLand(await api('/api/sift', { op: 'decide', folder: SF.folder, rec_id: r.rec_id, stage, decision, reason, note }));
    } catch (err) {
      say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
      await sfReload();
      return;
    }
    sfDraw();
  });
}

/* the screening read again, the round and the place kept */
async function sfReload() {
  try {
    sfTake(await api('/api/sift', { op: 'read', folder: SF.folder }));
  } catch { return; }
  sfDraw();
}

function sfPicking(on) {
  SF.picking = on && sfCodes().length > 0;
  SF.pick = SF.picking ? sfPreselect() : -1;
  sfReasonsDraw();
}

/* Accept suggestion in a suggestion's box, `i` the box, and Enter, the first box's: exactly what pressing
   the suggested decision and choosing its reason does, through sfDecide, so the note, the step on and
   Undo are a decision's own and nothing records which control made it (14 October). No or Exclude takes
   the suggestion's reason, and with none No reason at title and abstract, while at full text the reasons
   open as Exclude's press opens them. A suggestion the record does not show takes nothing. */
function sfTakeProposal(i = 0) {
  const r = sfRecord();
  if (!r) return;
  const prop = sfSuggestions(sfStage(r))[i] || {};
  if (!sfWords(SF.stage)[prop.decision]) { say(t('sift.no_suggestion')); return; }
  if (prop.decision !== 'exclude') { sfDecide(prop.decision); return; }
  const codes = sfCodes().map((c) => c.code);
  if (prop.reason && codes.includes(prop.reason)) sfDecide('exclude', prop.reason, true);
  else if (!prop.reason && (SF.stage === 'ta' || !codes.length)) sfDecide('exclude', '', true);
  else sfDecide('exclude');
}

function sfNoteSave() {
  const r = sfRecord();
  if (!r) return;
  const st = sfStage(r);
  const text = $('sf-note').value;
  if (text.trim() === String(st.note || '').trim()) return;
  const stage = SF.stage;
  // held at once, as a decision is, so a draw before the server answers shows the note as he left it
  st.note = text.trim();
  sfQueue(async () => {
    sfLand(await api('/api/sift', { op: 'note', folder: SF.folder, rec_id: r.rec_id, stage, note: text }));
    sfBar();
    // and the box given the note as kept, should the answer to an act before it have drawn the record
    // over it with none
    const now = sfRecord();
    if (now && now.rec_id === r.rec_id && SF.stage === stage && document.activeElement !== $('sf-note')) {
      $('sf-note').value = (sfStage(now) || {}).note || '';
    }
  });
}

/* Undo: the newest decision, note or key excerpt kept or removed not yet undone put back, by one more line
   in the log, and the place moved to its record when the round holds it, a key excerpt's at either stage.
   Undo of a key excerpt kept leaves its words marked as the pieces of the one being built, so H keeps it
   again, as `q`'s undo does on Experiential statements (14 October). */
function sfUndo() {
  sfQueue(async () => {
    const data = await api('/api/sift', { op: 'undo', folder: SF.folder });
    sfLand(data);
    if (!data.undone) { say(t('sift.undo.nothing')); return; }
    const at = SF.ids.indexOf(data.undone.rec_id);
    const excerpt = data.undone.what === 'excerpt';
    if ((data.undone.stage === SF.stage || excerpt) && at >= 0) SF.at = at;
    else say(data.undone.stage === 'ft' ? t('sift.undo.done_ft', { rec: data.undone.rec_id }) : t('sift.undo.done_ta', { rec: data.undone.rec_id }));
    if (excerpt && at >= 0) {
      const gone = data.undone.change === 'add';
      SF.pieces = gone ? ((data.undone.excerpt || {}).pieces || []).map((p) => ({ ...p })) : [];
      SF.piecesFor = data.undone.rec_id;
      say(gone ? t('sift.undo.excerpt_out') : t('sift.undo.excerpt_back'), 2400);
    }
    SF.picking = false;
    SF.tvReveal = true;
    sfDraw();
  });
}

function sfMove(delta) {
  if (!SF.ids.length) return;
  const next = Math.max(0, Math.min(SF.ids.length - 1, SF.at + delta));
  if (next === SF.at) return;
  SF.at = next;
  SF.picking = false;
  SF.tvReveal = true;
  // in the table only the mark moves, so a held arrow keeps pace however many rows there are
  if (SF.view === 'table') {
    sfTvMark();
    sfReasonsDraw();
    sfKeepPlace();
    return;
  }
  sfDraw();
}

/* ── Export's menu ── */

/* Export, in the title bar (12 October): one menu for what leaves the screening, Export to Zotero,
   Export included records and Export PRISMA counts, under its button, which the bar may scroll, so
   it stands over the screen at the button's place. Opened, its first item that can be pressed takes
   the focus. Shut by a press beside it, Esc or Tab, the focus back on the button unless `back` is
   false. */
const sfMenuItems = () => [...$('sf-export-menu').querySelectorAll('.sf-menu-item')].filter((b) => !b.disabled);

function sfMenuOpen(open, back = true) {
  const menu = $('sf-export-menu');
  const btn = $('sf-export');
  if (!open) {
    if (menu.hidden) return;
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    if (back) btn.focus();
    return;
  }
  sfBar();
  menu.hidden = false;
  btn.setAttribute('aria-expanded', 'true');
  const at = btn.getBoundingClientRect();
  const width = menu.offsetWidth;
  menu.style.top = `${Math.round(at.bottom + 4)}px`;
  menu.style.left = `${Math.round(Math.max(8, Math.min(window.innerWidth - width - 8, at.right - width)))}px`;
  const first = sfMenuItems()[0];
  if (first) first.focus();
}

/* an item's work, the menu shut first and the focus left where the work puts it */
function sfMenuTake(work) {
  sfMenuOpen(false, false);
  work();
}

/* the menu's keys: the arrows move among its items, Home and End to the first and the last, Esc and
   Tab shut it. Answers whether the menu stood open, so no other key of Sift's acts behind it. */
function sfMenuKey(e) {
  if ($('sf-export-menu').hidden) return false;
  const items = sfMenuItems();
  const at = items.indexOf(document.activeElement);
  const go = (i) => { e.preventDefault(); if (items.length) items[(i + items.length) % items.length].focus(); };
  if (e.key === 'ArrowDown') go(at + 1);
  else if (e.key === 'ArrowUp') go(at < 0 ? items.length - 1 : at - 1);
  else if (e.key === 'Home') go(0);
  else if (e.key === 'End') go(items.length - 1);
  else if (e.key === 'Escape') {
    e.preventDefault();
    sfMenuOpen(false);
  } else if (e.key === 'Tab') sfMenuOpen(false, false);
  return true;
}

/* Export PRISMA counts, in Export's menu (Write the counts until 12 October): the flow's numbers and
   the decisions against the proposals written beside the screening as screening.counts.csv. */
async function sfExport() {
  try {
    const data = await api('/api/sift', { op: 'export', folder: SF.folder });
    sfLand(data);
    say(t('sift.wrote', { file: data.file }));
  } catch (err) { say(err.message, 9000); }
}

/* Export included records (12 October): the records included at full text written beside the
   screening as RIS and CSV, as Export PRISMA counts writes its file there. Its item in Export's menu
   stands off while none is included at full text (see sfBar). */
async function sfIncluded() {
  try {
    const data = await api('/api/sift', { op: 'included', folder: SF.folder });
    if (!data.written) { say(t('sift.none_included')); return; }
    say(t('sift.wrote_records', { n: data.records, files: tList(data.files) }));
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* Start again, under the flow, to trial the screening and begin afresh: the server says what it
   clears, one question says it with the copy kept, and once every act is in the screening is
   started again and read afresh on the first record of its round. Undo cannot bring it back, and
   the log stays whole in _Archive. */
async function sfReset() {
  let plan;
  try {
    plan = await api('/api/sift', { op: 'reset', folder: SF.folder, dry_run: true });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  const line = t('sift.reset.line', { decisions: t('sift.n_decisions', { n: plan.decisions }), notes: t('sift.n_notes', { n: plan.notes }) });
  if (!(await sfAsk(t('sift.reset.head'), line, t('sift.reset.head')))) return;
  await SF.chain;
  try {
    await api('/api/sift', { op: 'reset', folder: SF.folder });
  } catch (err) { say(err.message, 9000); return; }
  try { sfTake(await api('/api/sift', { op: 'read', folder: SF.folder })); } catch { /* drawn as it stands */ }
  await sfRound(null);
  say(t('sift.reset.done'));
}

/* ── Sift's own AI proposals ── */

/* the two AI controls, there with both switches on, each saying what it is doing while it does it */
function sfAiDraw() {
  const r = sfRecord();
  $('sf-ai').hidden = !sfAiReady() || !r;
  if ($('sf-ai').hidden) return;
  const mine = SF.asking && r && SF.asking === r.rec_id;
  $('sf-ai-one-word').textContent = mine ? t('sift.asking') : t('sift.ai.propose');
  $('sf-ai-one').disabled = !!SF.asking || !!SF.batch;
  $('sf-ai-all-word').textContent = SF.batch
    ? (SF.batch.stop ? t('sift.ai.finishing') : t('sift.ai.proposing', { done: SF.batch.done, of: SF.batch.of })) : t('sift.ai.propose_rows');
  $('sf-ai-all').disabled = !!SF.asking && !SF.batch;
}

/* a proposal's answer taken into the record it names, its proposals alone, so a decision he made
   while it was asked is never drawn back */
function sfLandProposal(data) {
  const fresh = data && data.record;
  const r = fresh ? SF.byId.get(fresh.rec_id) : null;
  if (!r) return;
  for (const stage of ['ta', 'ft']) {
    if (!fresh.stages[stage] || !r.stages[stage]) continue;
    r.stages[stage].proposal = fresh.stages[stage].proposal;
    r.stages[stage].proposals = fresh.stages[stage].proposals;
  }
  sfMark(r);
}

async function sfAiOne() {
  const r = sfRecord();
  if (!r || !sfAiReady() || SF.asking || SF.batch) return;
  SF.asking = r.rec_id;
  sfAiDraw();
  try {
    sfLandProposal(await api('/api/sift', { op: 'propose', folder: SF.folder, rec_id: r.rec_id, stage: SF.stage }));
  } catch (err) { say(err.message, 9000); }
  SF.asking = null;
  sfDraw();
}

/* A proposal for every record still to screen the table shows with none of Sift's yet, the calls it will
   make said and agreed first, then asked one after another. Pressed again it stops after the call
   under way. The first refusal stops it, since the rest would meet it too. */
async function sfAiAll() {
  if (SF.batch) { SF.batch.stop = true; sfAiDraw(); return; }
  if (!sfAiReady() || SF.asking) return;
  const stage = SF.stage;
  let plan;
  try {
    plan = await api('/api/sift', { op: 'plan', folder: SF.folder, stage, round: 'all', ids: SF.ids.slice() });
  } catch (err) { say(err.message, 9000); return; }
  if (!plan.calls) { say(t('sift.ai.all_have')); return; }
  if (!(await sfAsk(t('sift.ai.propose_rows'), t('sift.ai.ask_line', { n: plan.calls, model: SF.ai.model_name }),
    `${TB_SPARKS}${esc(t('sift.ai.propose_btn'))}`))) return;
  SF.batch = { done: 0, of: plan.calls, stop: false };
  let said = '';
  for (const rec of plan.ids) {
    if (SF.batch.stop) break;
    SF.asking = rec;
    sfAiDraw();
    try {
      sfLandProposal(await api('/api/sift', { op: 'propose', folder: SF.folder, rec_id: rec, stage }));
    } catch (err) { said = err.message; break; }
    SF.batch.done += 1;
    if (sfRecord() && sfRecord().rec_id === rec) sfDraw();
    else sfAiDraw();
  }
  const done = SF.batch.done;
  // a second press leaves the rest for later, as Find open-access PDFs does
  const left = SF.batch.stop ? SF.batch.of - done : 0;
  SF.batch = null;
  SF.asking = null;
  sfDraw();
  say(said || (left > 0 ? t('sift.ai.done_left', { n: done, left }) : t('sift.ai.done', { n: done })),
    said ? 9000 : 4200);
}

/* ── PDFs and the bench, under Sift in Settings, and the one question ── */

/* Sift's own settings are under Sift in Settings, which its cog opens (9 October): Find open-access
   PDFs with the email Unpaywall asks for, whatever the AI switch, and with it on the AI proposals,
   their prompt and the bench, each for the Sift project chosen there, the screening open first (see
   sfpLoad in sift_settings.js). These are the PDFs part and the bench. */

/* the PDFs part for the project chosen: the email as config.json keeps it, and the button as a run
   under way stands, whichever project it works on */
function sfOaShow() {
  const held = typeof S !== 'undefined' && S.libConfig ? S.libConfig.sift_email : '';
  $('sf-oa-email').value = SF.email || held || '';
  if (!SF.oa) sfSaid('sf-oa-said', '');
  if (!SF.fill) sfSaid('sf-fill-said', '');
  sfOaDraw();
  sfFillDraw();
}

/* the line beside Find open-access PDFs or Fill from OpenAlex, one that says a failure in the one warning tint
   as every failure line is, where it stood in the small print's grey (17 October, later) */
function sfSaid(id, text, failed = false) {
  $(id).textContent = text;
  $(id).classList.toggle('said-failed', !!(failed && text));
}

/* an error as the line says it: a server from before the change asks for a restart, which is no failure */
const sfSaidErr = (id, err) => sfSaid(id, needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));

/* ── Find open-access PDFs ── */

/* the email Unpaywall asks for, kept in config.json once he gives it, so it is asked once */
async function sfEmailSave() {
  const email = $('sf-oa-email').value.trim();
  if (email === (SF.email || '')) return true;
  const folder = sfaFolder() || SF.folder;
  if (!folder) return false;
  try {
    SF.email = (await api('/api/sift', { op: 'email', folder, email })).email || '';
    if (typeof S !== 'undefined' && S.libConfig) S.libConfig.sift_email = SF.email;
    return true;
  } catch (err) {
    sfSaidErr('sf-oa-said', err);
    return false;
  }
}

function sfOaDraw() {
  const run = SF.oa;
  $('sf-oa-word').textContent = run ? t('sift.oa.finding', { done: run.done, of: run.of }) : t('sift.oa.find');
  $('sf-oa-go').title = run ? t('sift.press_again') : '';
}

/* Each record that passed title and abstract with no PDF, of the project chosen under Sift in Settings, looked for, one after
   another, in Unpaywall and OpenAlex by the server, which keeps a PDF only when its first page
   carries the record's title and never writes over one there. Pressed again it leaves the rest for
   later, after the record under way. The count is said at the end. It calls no model. */
async function sfOaRun() {
  if (SF.oa) { SF.oa.stop = true; return; }
  if (!$('sf-oa-email').value.trim()) {
    sfSaid('sf-oa-said', t('sift.oa.email_first'));
    $('sf-oa-email').focus();
    return;
  }
  if (!(await sfEmailSave())) return;
  const folder = sfaFolder() || SF.folder;
  if (!folder) return;
  let plan;
  try {
    plan = await api('/api/sift', { op: 'oa_plan', folder });
  } catch (err) { sfSaidErr('sf-oa-said', err); return; }
  // only the records that passed title and abstract are sought, as PRISMA seeks their reports (12 October)
  if (!plan.ids.length) {
    sfSaid('sf-oa-said', Number(plan.passed) === 0 ? t('sift.oa.none_passed')
      : t('sift.oa.all_have'));
    return;
  }
  const run = { done: 0, of: plan.ids.length, found: 0, stop: false };
  SF.oa = run;
  sfSaid('sf-oa-said', '');
  sfOaDraw();
  let said = '';
  for (const rec of plan.ids) {
    if (run.stop) break;
    try {
      const got = await api('/api/sift', { op: 'oa_find', folder, rec_id: rec });
      if (got.saved && SF.folder === folder) {
        run.found += 1;
        SF.pdfAt[rec] = Date.now();
        sfLand(got);
        if (sfShown() && sfRecord() && sfRecord().rec_id === rec && SF.view === 'record') sfDraw();
      } else if (got.saved) run.found += 1;
    } catch (err) { said = needsRestart(err) ? RESTART_LINE : err.message; break; }
    run.done += 1;
    sfOaDraw();
  }
  const { done, of, found } = run;
  SF.oa = null;
  sfOaDraw();
  const line = said || (done < of ? t('sift.oa.found_left', { found, done, left: of - done })
    : t('sift.oa.found', { found, of }));
  sfSaid('sf-oa-said', line, !!said && said !== RESTART_LINE);
  if ($('settings').hidden) say(line, 6000);
  if (sfShown() && SF.folder === folder) sfDraw();
}

/* ── Fill from OpenAlex ── */

function sfFillDraw() {
  const run = SF.fill;
  $('sf-fill-word').textContent = run ? t('sift.fill.filling', { done: run.done, of: run.of }) : t('sift.fill.go');
  $('sf-fill-go').title = run ? t('sift.press_again') : '';
}

/* Fill from OpenAlex, under Sift in Settings beside Find open-access PDFs, for the project chosen there
   (13 October, in place of Find citation counts): for a screening whose run came before runs filled
   them, each record with a DOI that lacks one of Sift's own columns asked of OpenAlex and Crossref, fifty
   at a time by the server, which writes what they say with the day into Sift's own columns, Cited by,
   Retracted or corrected, Open access, Country and the references Cites key works reads, never the
   review's. The button counts as it goes, pressed again it leaves the rest for later after the fifty
   under way, and the end says how many it filled. It calls no model, so it stands outside the AI switch. */
async function sfFillRun() {
  if (SF.fill) { SF.fill.stop = true; return; }
  const folder = sfaFolder() || SF.folder;
  if (!folder) return;
  let plan;
  try {
    plan = await api('/api/sift', { op: 'fill_plan', folder });
  } catch (err) { sfSaidErr('sf-fill-said', err); return; }
  if (!Number(plan.of)) { sfSaid('sf-fill-said', t('sift.fill.no_doi')); return; }
  if (!Number(plan.missing)) { sfSaid('sf-fill-said', t('sift.fill.all_filled')); return; }
  const run = { done: 0, of: Number(plan.of), filled: 0, stop: false };
  SF.fill = run;
  sfSaid('sf-fill-said', '');
  sfFillDraw();
  let said = '';
  while (run.done < run.of && !run.stop) {
    let got;
    try {
      got = await api('/api/sift', { op: 'fill', folder, at: run.done });
    } catch (err) { said = needsRestart(err) ? RESTART_LINE : err.message; break; }
    if (got.said) { said = got.said; break; }
    run.filled += Number(got.filled) || 0;
    run.done = Math.min(run.of, Number(got.at) || run.of);
    sfFillDraw();
  }
  SF.fill = null;
  sfFillDraw();
  const left = run.of - run.done;
  const line = said || (left > 0 ? t('sift.fill.done_left', { filled: run.filled, n: Number(plan.missing), left })
    : t('sift.fill.done', { filled: run.filled, n: Number(plan.missing) }));
  sfSaid('sf-fill-said', line, !!said && said !== RESTART_LINE);
  if ($('settings').hidden) say(line, 6000);
  if (sfShown() && SF.folder === folder) await sfReload();
}

/* ── the bench ── */

const sfShort = (s, n = 70) => { const t = String(s || '').replace(/\s+/g, ' ').trim(); return t.length > n ? `${t.slice(0, n - 1)}…` : t; };

/* The records the bench can try for the project chosen, those of the stage, the record open or the
   row chosen first: the screen's own when the project is the one open, else asked of the server, a
   title each, named by its ID (13 October). `model` names the model the calls go to. */
async function sfBenchFill(folder, model) {
  const open = folder === SF.folder && SF.records.length;
  const stage = open ? SF.stage : 'ta';
  SF.bench = { folder, stage, model: model || '', records: [] };
  $('sf-bench-out').hidden = true;
  if (open) {
    SF.bench.records = SF.records.filter((r) => stage === 'ta' || ((r.stages || {}).ft || {}).in)
      .map((r) => ({ rec_id: r.rec_id, title: r.title }));
  } else {
    sfBenchCost();
    try {
      const got = await api('/api/sift', { op: 'titles', folder, stage });
      if (!SF.bench || SF.bench.folder !== folder) return;
      SF.bench.records = got.records || [];
    } catch (err) {
      sfSaidErr('sf-bench-cost', err);
      return;
    }
  }
  const now = open ? sfRecord() : null;
  $('sf-bench-rec').innerHTML = SF.bench.records.map((r) =>
    `<option value="${escAttr(r.rec_id)}">${esc(r.title ? `${r.rec_id} · ${sfShort(r.title)}` : r.rec_id)}</option>`).join('');
  if (now && SF.bench.records.some((r) => r.rec_id === now.rec_id)) $('sf-bench-rec').value = now.rec_id;
  sfBenchCost();
}

/* what Try will send and to whom, said before it is pressed, as the app's other AI asks say theirs */
function sfBenchCost() {
  const b = SF.bench || { records: [] };
  const r = b.records.find((x) => x.rec_id === $('sf-bench-rec').value);
  const who = b.model || t('sift.bench.model_chosen');
  sfSaid('sf-bench-cost', r
    ? t('sift.bench.line', { rec: r.rec_id, who }) : '');
  $('sf-bench-try').disabled = !r || SF.benchBusy;
}

/* Try: the record picked sent with the prompt as the box holds it, saved or not, and what came back
   shown, its decision as a pill, its reason and its grounds. Nothing is written anywhere. */
async function sfBenchTry() {
  const rec = $('sf-bench-rec').value;
  const b = SF.bench;
  if (!rec || !b || SF.benchBusy || !$('set-ai').checked) return;
  SF.benchBusy = true;
  $('sf-bench-word').textContent = t('sift.asking');
  $('sf-bench-try').disabled = true;
  $('sf-bench-out').hidden = false;
  $('sf-bench-pill').innerHTML = '';
  $('sf-bench-reason').textContent = '';
  $('sf-bench-grounds').textContent = '';
  sfSaid('sf-bench-note', 'asking');
  try {
    const data = await api('/api/sift', { op: 'try', folder: b.folder, rec_id: rec, stage: b.stage,
      prompt: $('sfa-prompt').value });
    sfPillSet($('sf-bench-pill'), data.decision, '', b.stage);
    // its reason a pill, with its meaning when the screening open is the one tried
    const mine = !!data.reason && b.folder === SF.folder;
    const meaning = mine ? sfMeaning(data.reason) : '';
    const pill = mine ? sfReasonPill(data.reason) : `<span class="sf-pill sf-rpill">${esc(data.reason || '')}</span>`;
    $('sf-bench-reason').innerHTML = data.reason ? `${pill}${meaning ? ` ${esc(meaning)}` : ''}` : '';
    sfSaid('sf-bench-note', t('sift.bench.took', { model: data.model_name || t('sift.bench.the_model'), seconds: tNum(Number(data.seconds || 0), { minimumFractionDigits: 1, maximumFractionDigits: 1 }) }));
    $('sf-bench-grounds').textContent = data.grounds
      ? (data.found ? t('sift.bench.grounds', { grounds: data.grounds }) : t('sift.bench.grounds_lost', { grounds: data.grounds })) : '';
  } catch (err) {
    sfSaidErr('sf-bench-note', err);
  } finally {
    SF.benchBusy = false;
    $('sf-bench-word').textContent = t('sift.bench.try');
    sfBenchCost();
  }
}

/* ── the second screener ── */

/* The second screener (PRISMA 2020 item 8), whose side the server sends with every read and every
   act that moves it, blind both ways: while a draw is blind the screen says how many came back and
   how many of its records he has still to decide, never which way theirs went. The settings are the
   project's, under Sift in Settings. Their workbook and the differences workbook are written beside
   the screening, and a returned one is taken back by a drop anywhere on the screen or by Take back a
   workbook. A difference's outcome is his to set, and a decision of his it changes goes to the log
   marked after discussion. */
const SF_TWO_STATE = { open: t('sift.two.state.open'), agreed: t('sift.two.state.agreed'), third: t('sift.two.state.third'),
  decided: t('sift.two.state.decided') };

const sfTwoOn = () => !!(SF.second && (SF.second.on || SF.second.any));
const sfTwoStage = () => (SF.second && SF.second.stages ? SF.second.stages[SF.stage] || null : null);
const sfTwoRecOf = (r) => (SF.second && SF.second.records && r ? (SF.second.records[r.rec_id] || {})[SF.stage] || null : null);
const sfTwoThem = () => (SF.second && SF.second.name) || t('sift.two.screener');
const sfTwoKappa = (k) => (k === null || k === undefined ? t('sift.two.kappa_none') : tNum(Number(k), { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
const sfTwoPc = (p) => (p === null || p === undefined ? '' : `${Math.round(Number(p) * 100)}%`);

function sfTwoOpen() {
  if (!SF.folder || !sfTwoOn()) return;
  sfSaid('sf-two-said', '');
  $('sf-two').hidden = false;
  sfTwoDraw();
  $('sf-two-make').focus();
}

function sfTwoClose() {
  $('sf-two').hidden = true;
}

/* a line from an act of the card, in the card while it stands open, else as a toast */
function sfTwoTell(text, long = false, failed = false) {
  if (!$('sf-two').hidden) sfSaid('sf-two-said', text, failed);
  else say(text, long ? 9000 : 4200);
}

/* his decisions against theirs, a row for each of his and a column for each of theirs, in the stage's
   words, Maybe only at title and abstract */
function sfTwoTable(table) {
  const keys = SF.stage === 'ft' ? ['include', 'exclude'] : ['include', 'maybe', 'exclude'];
  const w = sfWords(SF.stage);
  const head = `<tr><td></td>${keys.map((k) => `<th scope="col">${w[k]}</th>`).join('')}</tr>`;
  const rows = keys.map((a) => `<tr><th scope="row">${w[a]}</th>${keys.map((b) => `<td>${Number(((table || {})[a] || {})[b]) || 0}</td>`).join('')}</tr>`);
  return `<table class="sf-two-table"><caption>${t('sift.two.caption', { them: esc(sfTwoThem()) })}</caption>${head}${rows.join('')}</table>`;
}

/* The card for the stage showing: who screens what share, the calibration records, each draw and its
   seed, how many came back, while a draw is blind how many of its records he has still to decide,
   then once both have decided a draw's records its agreement before any discussion, its kappa and
   table, the further draw below the setting, and the differences by where they stand. */
function sfTwoDraw() {
  if ($('sf-two').hidden) return;
  const two = SF.second || {};
  const ts = sfTwoStage();
  const words = SF.stage === 'ft' ? t('sift.stage.ft') : t('sift.stage.ta');
  $('sf-two-head').textContent = t('sift.two.head', { stage: words });
  if (!ts) { $('sf-two-body').innerHTML = ''; return; }
  const share = ts.draws.length ? Number(ts.draws[0].share) : Number(two.share);
  const facts = [];
  const fact = (dt, dd) => facts.push(`<div><dt>${dt}</dt><dd>${dd}</dd></div>`);
  if (ts.calibration) {
    // the first records by ID, since the numbers sift_second.py orders them by are given in ID order (13 October)
    const left = ts.calibration_left;
    fact(t('sift.two.calibration'), left ? t('sift.two.calibration_left', { n: ts.calibration, left })
      : t('sift.two.calibration_line', { n: ts.calibration }));
  }
  if (!ts.draws.length) fact(t('sift.two.draw'), ts.size ? t('sift.two.none_yet_share', { n: ts.size }) : t('sift.two.none_yet'));
  ts.draws.forEach((d) => fact(ts.draws.length > 1 ? t('sift.two.draw_n', { draw: d.draw }) : t('sift.two.draw'),
    t('sift.two.draw_line', { n: d.records, seed: d.seed })));
  if (ts.draws.length) fact(t('sift.two.came_back'), t('sift.two.of', { part: ts.back, all: ts.drawn }));
  if (ts.blind_left) fact(t('sift.two.still_to_decide'), t('sift.two.blind_left', { left: ts.blind_left }));
  const many = ts.agreements.length > 1;
  ts.agreements.forEach((a) => {
    fact(many ? t('sift.two.draw_n', { draw: a.draw }) : t('sift.two.decided_alike'), many
      ? t('sift.two.alike_kappa', { alike: a.alike, records: a.records, pc: sfTwoPc(a.proportion), kappa: sfTwoKappa(a.kappa) })
      : t('sift.two.alike', { alike: a.alike, records: a.records, pc: sfTwoPc(a.proportion) }));
    if (!many) fact(t('sift.two.kappa'), sfTwoKappa(a.kappa));
  });
  const all = many ? ts.pooled : ts.agreements[0] || null;
  if (many && all) {
    fact(t('sift.two.decided_alike'), t('sift.two.alike', { alike: all.alike, records: all.records, pc: sfTwoPc(all.proportion) }));
    fact(t('sift.two.kappa'), sfTwoKappa(all.kappa));
  }
  const d = ts.differences || {};
  if (d.all) {
    const parts = [[d.agreed, (n) => t('sift.two.diff.agreed', { n })], [d.decided, (n) => t('sift.two.diff.decided', { n })],
      [d.third, (n) => t('sift.two.diff.third', { n })], [d.open, (n) => t('sift.two.diff.open', { n })]]
      .filter(([n]) => n).map(([n, w]) => w(n));
    // one part alone is the whole, 2 open, and more than one follow the whole, 3: 2 open, 1 settled by discussion
    fact(t('sift.two.differences'), parts.length === 1 ? parts[0] : t('sift.two.diff.all', { all: d.all, parts: parts.join(', ') }));
  }
  const lead = share >= 100 ? t('sift.two.lead_every', { them: esc(sfTwoThem()), stage: words })
    : t('sift.two.lead_share', { them: esc(sfTwoThem()), share, stage: words });
  let html = `<p class="sf-two-lead">${lead}</p><dl class="sf-two-facts">${facts.join('')}</dl>`;
  if (all) html += sfTwoTable(all.table);
  // why the first draw waits, unless it is the calibration records left, which the list above says
  if (ts.waits && !ts.draws.length && !ts.waits_calibration) html += `<p class="sf-two-wait">${esc(ts.waits)}</p>`;
  const btns = [];
  if (ts.further) btns.push(`<button type="button" class="ghost small" data-act="further">${esc(t('sift.two.further'))}</button>`);
  if (d.all) btns.push(`<button type="button" class="ghost small" data-act="apart">${esc(t('sift.two.apart'))}</button>`);
  if (ts.further) html += `<p class="sf-two-low">${esc(t('sift.two.kappa_below', { kappa: tNum(Number(two.kappa), { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }))}</p>`;
  if (btns.length) html += `<p class="sf-two-more">${btns.join('')}</p>`;
  $('sf-two-body').innerHTML = html;
  $('sf-two-make').disabled = !two.on || (ts.draws.length ? !ts.to_send : !!ts.waits);
  $('sf-two-diff').disabled = !d.open;
}

/* their workbook for the stage showing, the first draw made with it, written beside the screening,
   and at full text the PDFs of its records in a folder beside it, to zip and send */
async function sfTwoMake() {
  $('sf-two-make').disabled = true;
  try {
    await SF.chain;
    const data = await api('/api/sift', { op: 'second', act: 'workbook', folder: SF.folder, stage: SF.stage });
    sfLand(data);
    let line = t('sift.two.wrote', { file: data.file, n: data.records });
    if (data.pdfs) line += ` ${t('sift.two.zip', { folder: data.pdfs })}`;
    if (data.missing) line += ` ${t('sift.two.no_pdf', { n: data.missing })}`;
    sfTwoTell(line, true);
  } catch (err) { sfTwoTell(needsRestart(err) ? RESTART_LINE : err.message, true, !needsRestart(err)); }
  sfBar();
  sfTwoDraw();
}

/* the differences workbook, of the differences still open at the stage showing */
async function sfTwoDifferences() {
  $('sf-two-diff').disabled = true;
  try {
    await SF.chain;
    const data = await api('/api/sift', { op: 'second', act: 'differences', folder: SF.folder, stage: SF.stage });
    sfLand(data);
    sfTwoTell(t('sift.two.wrote_differences', { file: data.file, n: data.records }), true);
  } catch (err) { sfTwoTell(needsRestart(err) ? RESTART_LINE : err.message, true, !needsRestart(err)); }
  sfTwoDraw();
}

/* a further draw at the stage showing, offered while the kappa is below the setting */
async function sfTwoFurther() {
  try {
    await SF.chain;
    const data = await api('/api/sift', { op: 'second', act: 'draw', folder: SF.folder, stage: SF.stage });
    sfLand(data);
    sfTwoTell(t('sift.two.drew', { n: data.records, seed: data.seed }));
  } catch (err) { sfTwoTell(needsRestart(err) ? RESTART_LINE : err.message, true, !needsRestart(err)); }
  sfBar();
  sfTwoDraw();
}

function sfTwoChoose() {
  const input = $('sf-two-file');
  input.value = '';
  input.click();
}

/* what a returned workbook brought, in one line */
function sfTwoTook(got) {
  if (got.kind === 'differences') {
    return got.taken ? t('sift.two.took_replies', { n: got.taken, file: got.file, agreed: got.agreed, keep: got.keep })
      : t('sift.two.no_reply', { file: got.file });
  }
  const blank = got.blank ? ` ${t('sift.two.blank_left', { n: got.blank })}` : '';
  return (got.taken ? t('sift.two.took_decisions', { n: got.taken, file: got.file }) : t('sift.two.no_decision', { file: got.file })) + blank;
}

/* A workbook returned, dropped anywhere on the screen or chosen with Take back a workbook, taken in
   once every act before it is in. The server checks it is one Sift made for this screening and
   refuses any other in one line. */
async function sfTwoTakeFile(file) {
  if (!SF.folder) return;
  try {
    const data = await tbBase64(file);
    await SF.chain;
    const got = await api('/api/sift', { op: 'second', act: 'take', folder: SF.folder, data, name: file.name });
    sfLand(got);
    sfTwoTell(sfTwoTook(got));
  } catch (err) { sfTwoTell(needsRestart(err) ? RESTART_LINE : err.message, true, !needsRestart(err)); }
  sfDraw();
  sfTwoDraw();
}

/* a difference's outcome set by his hand, the record drawn afresh from the answer */
function sfTwoOutcome(outcome, decision) {
  const r = sfRecord();
  if (!r) return;
  const stage = SF.stage;
  sfQueue(async () => {
    sfLand(await api('/api/sift', { op: 'second', act: 'outcome', folder: SF.folder, rec_id: r.rec_id, stage, outcome, decision }));
    sfDraw();
  });
}

/* one side of a drawn record, the screener's name, the decision as a pill with its reason, and
   the note under it */
function sfTwoSide(who, decision, reason, note, missing) {
  const dec = missing ? `<span class="sf-empty">${esc(t('sift.two.not_back'))}</span>` : sfPillHtml(decision, reason);
  return `<div class="sf-two-side"><p class="sf-two-who">${esc(who)}</p><p class="sf-two-dec">${dec}</p>`
    + `${note ? `<p class="sf-two-note">${esc(note)}</p>` : ''}</div>`;
}

/* The record's calibration mark, and once he can see the second screener's side of a drawn record his
   decision and theirs side by side, his before discussion when it has changed since, and where the
   two differ the outcome with its buttons and the replies from the differences workbook. */
function sfTwoRecDraw(r) {
  const box = $('sf-two-rec');
  const x = sfTwoRecOf(r);
  $('sf-cal').hidden = !(x && x.calibration);
  if (!x || !x.drawn) { box.hidden = true; box.innerHTML = ''; return; }
  const st = sfStage(r);
  const them = sfTwoThem();
  const th = x.theirs;
  let html = `<div class="sf-two-sides">${sfTwoSide(t('sift.two.you'), st.decision, st.reason, st.note, false)}`
    + `${sfTwoSide(them, th ? th.decision : '', th ? th.reason : '', th ? th.note : '', !th)}</div>`;
  const b = x.before || {};
  if (b.decision && (b.decision !== st.decision || (b.reason || '') !== (st.reason || ''))) {
    html += `<p class="sf-two-before">${t('sift.two.before_html', { pill: sfPillHtml(b.decision, b.reason) })}</p>`;
  }
  if (x.differs) {
    const o = x.outcome || { state: 'open' };
    const said = o.state === 'agreed' || o.state === 'decided' ? ` ${sfPillHtml(o.decision, o.reason)}` : '';
    html += `<p class="sf-two-out"><span class="sf-two-label">${esc(t('sift.two.outcome'))}</span> ${SF_TWO_STATE[o.state] || SF_TWO_STATE.open}${said}</p>`;
    const btn = (out, dec, word) => `<button type="button" class="ghost small" data-out="${out}" data-decision="${dec}">${word}</button>`;
    let acts = '';
    // in the stage's words, Agreed: Yes or Agreed: Exclude and the rest (12 October, later)
    const w = sfWords(SF.stage);
    if (o.state === 'open') {
      acts = btn('agreed', 'include', t('sift.two.agreed_as', { word: w.include })) + btn('agreed', 'exclude', t('sift.two.agreed_as', { word: w.exclude }))
        + btn('third', '', t('sift.two.to_third'));
    } else if (o.state === 'third') {
      acts = btn('decided', 'include', t('sift.two.third_as', { word: w.include })) + btn('decided', 'exclude', t('sift.two.third_as', { word: w.exclude }))
        + btn('open', '', t('sift.two.reopen'));
    } else acts = btn('open', '', t('sift.two.reopen'));
    html += `<p class="sf-two-btns">${acts}</p>`;
  }
  (x.replies || []).forEach((rep) => {
    const reply = rep.reply === 'agree' ? t('sift.two.reply_agree') : t('sift.two.reply_keep');
    html += `<p class="sf-two-reply">${rep.note ? t('sift.two.replied_note', { them: esc(them), reply, note: esc(rep.note) })
      : t('sift.two.replied', { them: esc(them), reply })}</p>`;
  });
  box.innerHTML = html;
  box.hidden = false;
}

/* ── Export to Zotero ── */

/* Export to Zotero, from Export's menu in the title bar (Sync to Zotero until 12 October, its card
   and what it does the same): the records that go, those included at full text, the rows the table
   shows or every record, each with its count, then what Export would do, asked of Zotero as soon as
   the card opens or the choice changes and said before Export is pressed, how many items it adds,
   updates and leaves and how many PDFs it uploads. It runs on the server, the card says how far it
   has gone and at the end what it did, and the card may close while it runs. A choice of no records
   asks nothing and leaves Export off. It calls no model, so it stands outside the AI switch. A server
   from before it says to restart. */
const sfZotWhich = () => (document.querySelector('input[name="sf-zot-which"]:checked') || {}).value || 'included';

function sfZotCounts() {
  const included = SF.records.filter((r) => ((r.stages || {}).ft || {}).decision === 'include').length;
  return { included, filter: SF.ids.length, all: SF.records.length };
}

function sfZotOpen() {
  if (!SF.folder) return;
  const n = sfZotCounts();
  $('sf-zot-w-included').textContent = t('sift.zot.included', { n: n.included });
  $('sf-zot-w-filter').textContent = t('sift.zot.filter', { n: n.filter });
  $('sf-zot-w-all').textContent = t('sift.zot.all', { n: n.all });
  $('sf-zot').hidden = false;
  if (SF.zot && SF.zot.folder === SF.folder && SF.zot.running) { sfZotDraw(); return; }
  SF.zot = { folder: SF.folder, plan: null, running: false, said: '', ask: (SF.zot ? SF.zot.ask : 0) + 1 };
  sfZotDraw();
  sfZotPlan();
  (document.querySelector('input[name="sf-zot-which"]:checked') || $('sf-zot-go')).focus();
}

function sfZotClose() {
  $('sf-zot').hidden = true;
}

function sfZotDraw() {
  const z = SF.zot || {};
  sfSaid('sf-zot-said', z.said || '', !!z.failed);
  const work = z.plan ? z.plan.adds + z.plan.updates + z.plan.pdfs : 0;
  $('sf-zot-go').disabled = !!z.running || !!z.done || !z.plan || !work;
  $('sf-zot-go').textContent = z.running ? t('sift.zot.exporting') : t('sift.zot.export');
  $('sf-zot-cancel').textContent = z.running || z.done ? t('sift.close') : t('sift.cancel');
  $('sf-zot-which').querySelectorAll('input').forEach((el) => { el.disabled = !!z.running; });
}

/* the preview for the choice as it stands, the rows the table shows sent by their ids */
async function sfZotPlan() {
  const z = SF.zot;
  if (!z || z.running) return;
  z.ask += 1;
  const ask = z.ask;
  z.plan = null;
  z.done = false;
  z.said = '';
  z.failed = false;
  sfZotDraw();
  const which = sfZotWhich();
  if (!sfZotCounts()[which]) return;
  try {
    const got = await api('/api/zotero', { op: 'plan', folder: z.folder, which, ids: which === 'filter' ? SF.ids.slice() : undefined });
    if (SF.zot !== z || ask !== z.ask) return;
    z.plan = got;
    z.said = got.said || '';
  } catch (err) {
    if (SF.zot !== z || ask !== z.ask) return;
    z.said = needsRestart(err) ? RESTART_LINE : err.message;
    z.failed = !needsRestart(err);
  }
  sfZotDraw();
}

/* Export: started on the server, then asked after until it ends */
async function sfZotGo() {
  const z = SF.zot;
  if (!z || z.running || !z.plan) return;
  const which = sfZotWhich();
  try {
    await api('/api/zotero', { op: 'sync', folder: z.folder, which, ids: which === 'filter' ? SF.ids.slice() : undefined });
  } catch (err) {
    z.said = needsRestart(err) ? RESTART_LINE : err.message;
    z.failed = !needsRestart(err);
    sfZotDraw();
    return;
  }
  z.running = true;
  z.said = t('sift.zot.exporting');
  sfZotDraw();
  for (;;) {
    await new Promise((resolve) => setTimeout(resolve, 700));
    let got;
    try { got = await api('/api/zotero', { op: 'progress', folder: z.folder }); } catch (err) { z.said = err.message; z.failed = true; break; }
    const run = got.running || {};
    if (run.running) {
      z.said = run.of ? t('sift.zot.exporting_of', { done: run.done, of: run.of }) : t('sift.zot.exporting');
      if (SF.zot === z) sfZotDraw();
      continue;
    }
    z.said = run.error || (run.result ? run.result.said : '');
    z.failed = !!(run.error || (run.result && run.result.note));
    break;
  }
  z.running = false;
  z.done = true;
  if (SF.zot === z) sfZotDraw();
  if ($('sf-zot').hidden && z.said) say(z.said, 9000);
}

/* the question card, answered by its buttons, Enter or Esc */
function sfAsk(head, line, yes, removes = false) {
  if (SF.askDone) SF.askDone(false);
  return new Promise((resolve) => {
    $('sf-ask-head').textContent = head;
    $('sf-ask-line').textContent = line;
    $('sf-ask-yes').innerHTML = yes;
    // a Yes that removes is red with its bin, from the one rule every Remove and Delete button shares
    $('sf-ask-yes').className = removes ? 'primary btn-remove' : 'primary';
    $('sf-ask').hidden = false;
    SF.askDone = (answer) => {
      $('sf-ask').hidden = true;
      SF.askDone = null;
      resolve(answer);
    };
    $('sf-ask-yes').focus();
  });
}

/* Another writer, a script adding records or proposals, is noticed when the window comes back:
   the records, the codes and the counts are read again, the round and the place kept. So is the
   app's AI switch turned in Settings. */
async function sfFresh() {
  if (!sfShown() || !SF.folder) return;
  let now;
  try { now = await api('/api/sift', { op: 'stamp', folder: SF.folder }); } catch { return; }
  const turned = !!now.config && aiOn(now.config) !== SF.aiMaster;
  if (!turned && (!now.stamp || JSON.stringify(now.stamp) === JSON.stringify(SF.stamp))) return;
  await SF.chain;
  await sfReload();
}


/* The screen left once every act is in, its cards shut and its PDF let go, for the home screen or the
   review's Searches step, `then` */
function sfLeave(then) {
  if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
  sfHistoryDrop();
  // the words waiting to be kept go first, so they are there when he comes back
  if (SF.keepTimer) sfFiltersKeep();
  if (SF.batch) SF.batch.stop = true;
  if (SF.oa) SF.oa.stop = true;
  if (SF.fill) SF.fill.stop = true;
  sfMenuOpen(false, false);
  SF.chain.then(() => {
    $('sift').hidden = true;
    $('sf-keys').hidden = true;
    $('sf-zot').hidden = true;
    $('sf-two').hidden = true;
    $('sf-cols').hidden = true;
    $('sf-fc').hidden = true;
    $('sf-why').hidden = true;
    SF.picking = false;
    SF.view = 'table';
    if (SF.askDone) SF.askDone(false);
    SF.frameFor = null;
    $('sf-frame').removeAttribute('src');
    then();
  });
}

function sfBack() {
  sfLeave(() => loadLibrary().catch((err) => say(err.message, 9000)));
}

/* ── the table's rows: its columns, sort and filter, worked out with no page ── */

/* the table's columns of its own, as sift.py names them, each with its heading, the kind that says
   how it sorts and filters, whether it shows at first, and which way a first press sorts it. The
   abstract and the DOI are hidden at first, each read on the record, and Columns offers them, and
   since 12 October Found by is Database, Rating is My rating and Cited by, OpenAlex's count of
   citations, stands after Year. */
const SF_COLS = {
  found: { label: t('sift.col.found'), kind: 'found', on: true, first: 'desc' },
  title: { label: t('sift.col.title'), kind: 'text', on: true },
  authors: { label: t('sift.col.authors'), kind: 'text', on: true },
  year: { label: t('sift.col.year'), kind: 'number', on: true },
  cited: { label: t('sift.col.cited'), kind: 'number', on: true, first: 'desc' },
  abstract: { label: t('sift.col.abstract'), kind: 'text' },
  participants: { label: t('sift.col.participants'), kind: 'number', on: true },
  doi: { label: t('sift.col.doi'), kind: 'text' },
  pdf: { label: t('sift.col.pdf'), kind: 'pdf', on: true },
  decision: { label: t('sift.col.decision'), kind: 'decision', on: true },
  study: { label: t('sift.col.study'), kind: 'study' },
  rating: { label: t('sift.col.rating'), kind: 'number', on: true, first: 'desc' },
  notes: { label: t('sift.col.notes'), kind: 'text' },
  digest: { label: t('sift.col.digest'), kind: 'text' },
  critique: { label: t('sift.col.critique'), kind: 'text' },
  journal: { label: t('sift.col.journal'), kind: 'text' },
  retracted: { label: t('sift.col.retracted'), kind: 'notice', first: 'desc' },
  oa: { label: t('sift.col.oa'), kind: 'oa' },
  country: { label: t('sift.col.country'), kind: 'country' },
  // the record's languages by their English names, hidden at first (14 October)
  language: { label: t('sift.col.language'), kind: 'language' },
  keyworks: { label: t('sift.col.keyworks'), kind: 'keyworks', first: 'desc' },
  // where the record's terms of each block were found, or how a database found it without them, hidden at
  // first (14 October)
  matched: { label: t('sift.col.matched'), kind: 'matched' },
};
/* The five columns of 13 October, each hidden at first and offered by Set columns: Retracted or
   corrected, what OpenAlex and Crossref say of a retraction, a correction or an expression of concern,
   Open access, Country, the countries of the authors' institutions, Study, the reports he linked as one
   study, and Cites key works, which of the review's key works a record cites. A record never asked of
   OpenAlex or Crossref reads Unknown in each of them, and one he linked to no study Not linked. Cites key
   works reads Can't check instead, since Sift asks references of Crossref and OpenAlex and for a record
   neither decides cannot check them (Adam's dialog, 14 October, later). */
const SF_NOTICE_WORDS = { retracted: t('sift.notice.retracted'), 'expression of concern': t('sift.notice.concern'),
  corrected: t('sift.notice.corrected'), none: t('sift.none') };
const SF_NOTICE_RANK = { retracted: 3, 'expression of concern': 2, corrected: 1 };
const SF_OA_WORDS = { diamond: t('sift.oa.diamond'), gold: t('sift.oa.gold'),
  hybrid: t('sift.oa.hybrid'), bronze: t('sift.oa.bronze'), green: t('sift.oa.green') };
const sfOaWord = (r) => (!r.oa ? '' : r.oa === 'closed' ? t('sift.oa.closed') : t('sift.oa.open'));
const sfNoticeKinds = (r) => ((r.notices || {}).kinds === null || (r.notices || {}).kinds === undefined ? null : r.notices.kinds);
const sfKeyWork = (key) => (SF.keyWorks || []).find((k) => k.key === key) || null;
// a retracted, questioned or corrected record says so beside its title, in the table and on the record,
// a plain word in a quiet tag, never an alarm
const sfNoticeTags = (r) => (sfNoticeKinds(r) || []).map((k) => ` <span class="sf-notice" data-kind="${escAttr(k)}">`
  + `${esc(SF_NOTICE_WORDS[k])}</span>`).join('');
const SF_EXTRA = 'csv:';
// a review column's heading: a name the searches write in plain words, any other with its underscores as spaces
const SF_EXTRA_NAMES = { pub_type: t('sift.extra.pub_type'), abstract_from: t('sift.extra.abstract_from'), url: t('sift.extra.url') };
const sfExtraLabel = (name) => SF_EXTRA_NAMES[name]
  || String(name).replace(/_/g, ' ').replace(/^./, (ch) => ch.toUpperCase());
// the found-by filter's choice of the records more than one search found, which no source can be
// named, since a bar parts the sources in the CSV
const SF_MANY = '|many';
// and its choice of the records new in this run, in a screening that follows an earlier run's
const SF_NEW = '|new';
// the choice of the records that hold nothing in a column, the family's table's (table.js): no year,
// no count of participants or no value, which no value can be, since a bar never stands alone in one
const SF_CHOICE_WORDS = { [SF_MANY]: t('sift.choice.many'), [SF_NEW]: t('sift.choice.new'), [TB_BLANK]: t('sift.none') };
// What a record that holds nothing in a column reads, in the filters, the table and the record (12
// October): a count of participants never given is Unknown, never nought, which is a count of its own,
// and a year, a rating and a count of citations each say what is missing
const SF_BLANK_WORDS = { year: t('sift.blank.year'), participants: t('sift.unknown'), rating: t('sift.blank.rating'),
  cited: t('sift.blank.cited') };
// and the columns of 13 October, Unknown for a record never asked of OpenAlex or Crossref, Can't check for
// key works neither Crossref's references nor OpenAlex's decide (14 October, later), and Not linked for one
// he linked to no study
Object.assign(SF_BLANK_WORDS, { retracted: t('sift.unknown'), oa: t('sift.unknown'), country: t('sift.unknown'),
  keyworks: t('sift.blank.keyworks'), study: t('sift.blank.study') });
// and the record's words for key works Sift cannot check, as the command line says them (see CITES_UNCHECKED
// in sift.py)
const SF_CITES_UNCHECKED = t('sift.cites_unchecked');
// and the record's language, Unknown for one no source gave a language (14 October)
SF_BLANK_WORDS.language = t('sift.unknown');
// the Decision filter's ticks beyond where a record stands: its decision differs from the proposal it
// stood against, shown while proposals are, and the second screener's Where we differ, shown while
// one of you took a record forward and the other left it out (12 October)
const SF_DIFFERS = 'differs';
const SF_APART = 'apart';
// the columns a slider with two handles filters, from a lowest to a highest whole number, a small bar
// chart over it of where the rows stand, each with the records with none a tick of its own under it,
// the rating from one star to five
const SF_RANGES = ['year', 'cited', 'participants', 'rating'];
// whether a column is one a slider filters: one of those, or a Number column of his, which filters as
// the participants do, its bars theirs and a blank Unknown (13 October)
const sfIsRange = (col) => !!col && (SF_RANGES.includes(col.key) || (!!col.own && col.kind === 'number'));
const sfRangeKey = (key) => sfIsRange(sfAllCols().find((c) => c.key === key));
// what a record with nothing in a slider's column reads: the column's own words, and a Number
// column's the participants', Unknown
const sfBlankWord = (col) => SF_BLANK_WORDS[col.key] || (col.own && col.kind === 'number' ? SF_BLANK_WORDS.participants : '');
// the choice of the records whose value stands between the slider's two handles
const SF_RANGE = '|range';
// A slider's chart: the year a bar for each five years, from a year that ends in 0 or 5, so 2015 to
// 2019 and 2020 to 2024, and wider runs of years past 30 bars, the participants a bar for each five up
// to 50, 1 to 5, 6 to 10 and on, then the wider bars past 50, and the rating a bar for each star.
const SF_BAR_YEARS = [5, 10, 25, 50, 100];
const SF_BAR_FIVES = 50;
const SF_BAR_WIDE = [[51, 100], [101, 200], [201, 500], [501, 1000]];
const SF_BARS = 30;
// the count of citations a bar for nought, then 1 to 5, 6 to 10, 11 to 25 and wider runs, then 1001 and over
const SF_BAR_CITED = [[0, 0], [1, 5], [6, 10], [11, 25], [26, 50], [51, 100], [101, 250], [251, 500], [501, 1000]];
// the words a group's heading carries in place of its column's, and the line its ⓘ says on hover
const SF_GROUP_WORDS = { pdf: t('sift.group.pdf') };
const SF_GROUP_ABOUT = { 'csv:abstract_from': t('sift.group.abstract_from') };
// a review column a pick can filter holds at least 2 different values and at most 30, and the
// journal and the publication type are always one, however many they hold, for any search
const SF_PICK_MIN = 2;
const SF_PICK_MAX = 30;
const SF_PICK_ALWAYS = ['journal', 'csv:pub_type'];
// each database Sift names in a colour of its own, the same wherever it stands, by its name or the
// short name the searches give it, and any other in one of a palette's colours by its name. None of
// them is red, so none is taken for the PDF.
const SF_DB_COLOURS = { scopus: 'scopus', psycinfo: 'psycinfo', 'apa psycinfo': 'psycinfo', 'web of science': 'wos', wos: 'wos',
  pubmed: 'pubmed', 'europe pmc': 'epmc', epmc: 'epmc', openalex: 'openalex', 'citation chasing': 'chasing',
  'citation search': 'chasing' };
const SF_DB_PALETTE = 6;
// a value as a pick knows it, its case and spacing set aside, so article and Article are one choice
const sfPickKey = (s) => String(s || '').toLowerCase().replace(/\s+/g, ' ').trim();
// the values a cell of the review holds, a list parted at a semicolon or a bar as the searches write one
const sfParts = (s) => String(s || '').split(/[;|]/).map((x) => x.replace(/\s+/g, ' ').trim()).filter(Boolean);

/* A publication type in plain words, as the table, the record and the filters show it (12 October),
   the CSV's pub_type as the databases wrote it and never changed: Journal article for PubMed's
   Journal Article, Europe PMC's research-article and the like, Dissertation or thesis, Review, Book
   chapter and the rest of `SF_TYPE_WORDS`, the first that fits, and any other as written, a word
   joined by hyphens or underscores parted and its first letter raised. */
const SF_TYPE_WORDS = [
  [/academic journal|peer.?reviewed/, t('sift.type.article')],
  [/thesis|dissertation/, t('sift.type.thesis')],
  [/preprint|posted.?content/, t('sift.type.preprint')],
  [/chapter|book.?section|book.?part|incollection|reference.?entry/, t('sift.type.chapter')],
  [/\bbook\b|monograph/, t('sift.type.book')],
  [/conference|proceedings|congress|symposium|meeting/, t('sift.type.conference')],
  [/\breview\b|meta.?analysis/, t('sift.type.review')],
  [/editorial/, t('sift.type.editorial')],
  [/\bletter\b|\bcomment/, t('sift.type.letter')],
  [/errat|correction|corrigend/, t('sift.type.correction')],
  [/\breport\b|working.?paper/, t('sift.type.report')],
  [/protocol/, t('sift.type.protocol')],
  [/dataset/, t('sift.type.dataset')],
  [/journal|article/, t('sift.type.article')],
];
function sfTypeWord(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  const low = text.toLowerCase().replace(/[-_]/g, ' ');
  const hit = SF_TYPE_WORDS.find(([re]) => re.test(low));
  if (hit) return hit[1];
  if (/[-_]/.test(text) && text === text.toLowerCase()) return low.charAt(0).toUpperCase() + low.slice(1);
  return text;
}
// a cell's publication types in plain words, each once
const sfTypeParts = (value) => [...new Set(sfParts(value).map(sfTypeWord).filter(Boolean))];
const SF_ABSTRACT_WORDS = 100;
const SF_ORDER = { include: 1, maybe: 2, exclude: 3 };

/* The record's ID, R010, always the table's first column and in no list of columns, in place of the
   record's number (13 October), sorting in natural order, R002 before R010, as `TB_TEXT` compares. */
const SF_ID = { key: 'rec_id', label: 'ID', kind: 'id', shown: true };

/* the columns a sort or a filter can name: the ID, then every column of the list */
/* At title and abstract (12 October): at full text, after the Decision column, where each record
   stood at the first stage, Yes or Maybe, as a pill, a filter of its own and sorting as the
   decision does. It is not one of the table's columns, so Columns does not offer it, and at title
   and abstract there is none. */
const SF_TADEC = { key: 'tadec', label: t('sift.at_ta'), kind: 'tadec', shown: true };
const sfStageCols = (cols, stage) => {
  if (stage !== 'ft') return cols;
  const at = cols.findIndex((c) => c.key === 'decision');
  return [...cols.slice(0, at >= 0 ? at + 1 : cols.length), SF_TADEC, ...cols.slice(at >= 0 ? at + 1 : cols.length)];
};
const sfAllCols = () => [...sfViewCols([SF_ID, ...sfColumns(SF.table)]), ...sfTermCols()];

/* The columns of the view: at full text At title and abstract after Decision, and at Extract and appraise
   Form after the ID in its place (13 October, later) */
function sfViewCols(cols) {
  if (!sfFormOn()) return sfStageCols(cols, SF.stage);
  return [cols[0], SF_FORMDONE, ...cols.slice(1)];
}

/* ── the form's rules and the plan's terms, worked out with no page (13 October, later) ── */

/* What the table's rows and the record's form both read of Extract and appraise: the words of its types and
   places, a field's value, whether it is shown and whether a record is done, as sift.py works them out, and
   the plan's blocks as the filters' groups. */
const SF_FIELD_TYPES = { text: t('sift.field.text'), choice: t('sift.field.choice'), number: t('sift.field.number'),
  yesno: t('sift.field.yesno'), multi: t('sift.field.multi'), long: t('sift.field.long'), passages: t('sift.field.passages') };
const SF_WHERE_WORDS = { form: t('sift.where.form'), table: t('sift.where.table'), both: t('sift.where.both') };
// the Sift columns a field may start from, shown as its value until he changes it, and the types that may
const SF_FROM_WORDS = { citation: t('sift.from.citation'), title: t('sift.col.title'), authors: t('sift.col.authors'),
  journal: t('sift.col.journal'), year: t('sift.col.year'), doi: t('sift.col.doi'), country: t('sift.col.country'),
  study: t('sift.col.study'), participants: t('sift.col.participants') };
const SF_FROM_TYPES = ['text', 'long', 'number'];
// the types of field another may be shown for, by the values it holds
const SF_COND_TYPES = ['choice', 'yesno', 'multi'];
// Not reported as the CSV holds it, and as the screen says it
const SF_NR = 'not reported';
const SF_NR_WORD = t('sift.not_reported');
const SF_YES_NO = { yes: t('sift.yes'), no: t('sift.no') };
const SF_DONE_WORDS = { done: t('sift.done'), todo: t('sift.not_done') };
// the stage's own column, first after the ID, whether a record's form is done, a filter of its own
const SF_FORMDONE = { key: 'formdone', label: t('sift.form'), kind: 'formdone', shown: true };
// the filter Benchmark papers, the plan's benchmark papers whatever their decision in place of the
// records included at full text
const SF_BENCH = 'bench';
const SF_EMPTY_FT = t('sift.empty_ft');
const SF_EMPTY_FORM = t('sift.empty_form');

const sfOwnDefs = () => (SF.table && SF.table.own) || [];
const sfOnForm = (c) => c.where === 'form' || c.where === 'both';
const sfOnTable = (c) => !c.where || c.where === 'table' || c.where === 'both';
// whether the screen stands at Extract and appraise, read safely where these rules run with no screen
const sfFormOn = () => typeof SF !== 'undefined' && !!SF.form;
// a field's key as Set up the form and the export name it, its CSV column without col_
const sfPlainKey = (key) => String(key || '').replace(/^col_/, '');

/* his columns in the form's order, those in no section first, then each section's in the sections' order */
function sfFormOrder(own, sections) {
  const at = new Map((sections || []).map((s, i) => [s, i + 1]));
  return own.map((c, i) => ({ c, i, s: c.section ? at.get(c.section) || 0 : 0 })).sort((a, b) => a.s - b.s || a.i - b.i).map((x) => x.c);
}

const sfFormFields = () => sfFormOrder(sfOwnDefs(), (SF.table && SF.table.sections) || []).filter(sfOnForm);

/* the choices a Several choices cell holds, and the passages a Passages cell holds, each its page and words */
const sfMultiParts = (v) => [...new Set(String(v || '').split(';').map((p) => p.replace(/\s+/g, ' ').trim()).filter(Boolean))];
function sfPassages(v) {
  const text = String(v || '').trim();
  if (!text.startsWith('[')) return [];
  try {
    const list = JSON.parse(text);
    return Array.isArray(list) ? list.filter((p) => p && typeof p === 'object' && String(p.text || '').trim())
      .map((p) => ({ page: String(p.page || '').trim(), text: String(p.text || '').trim() })) : [];
  } catch { return []; }
}

/* A field's value on a record and whether it is Sift's: his own cell when it holds anything, else for a
   field that starts from a Sift column that column's value, which the server gives with the record */
function sfFieldValue(r, c) {
  const own = String(((r.fields || {}).own || {})[c.key] || '');
  if (own.trim() || !c.from) return { value: own, sift: false };
  const v = String((((r.form || {}).sift) || {})[c.key] || '');
  return { value: v, sift: !!v };
}

/* whether a field holds one of the values another field is shown for, Not reported none of them */
function sfHolds(c, value, wanted) {
  if (!String(value).trim() || value === SF_NR) return false;
  const parts = c.type === 'multi' ? sfMultiParts(value) : [String(value).replace(/\s+/g, ' ').trim()];
  return parts.some((p) => wanted.includes(p));
}

/* The fields of the form shown on a record, as sift.py's `shown_fields` works them out: each with no
   condition, and each shown for values of another field while that field is shown and holds one of
   them, a condition on a field no longer there shown always. A hidden field keeps its value. */
function sfShownKeys(r, fields) {
  const by = new Map(fields.map((c) => [c.key, c]));
  const held = new Map();
  const shown = (c, seen) => {
    if (held.has(c.key)) return held.get(c.key);
    const w = c.when;
    const ctl = w ? by.get(w.key) : null;
    let ok = true;
    if (ctl && SF_COND_TYPES.includes(ctl.type) && !seen.has(ctl.key) && ctl !== c) {
      ok = shown(ctl, new Set([...seen, c.key])) && sfHolds(ctl, sfFieldValue(r, ctl).value, w.values || []);
    }
    held.set(c.key, ok);
    return ok;
  };
  return new Set(fields.filter((c) => shown(c, new Set())).map((c) => c.key));
}

/* whether a field holds a value, Not reported among them, and whether a record's form is done: every
   field shown on it holding one, never on a form with no field */
function sfFilledIn(c, value) {
  if (value === SF_NR) return true;
  if (c.type === 'passages') return sfPassages(value).length > 0;
  if (c.type === 'multi') return sfMultiParts(value).length > 0;
  return String(value || '').trim() !== '';
}

function sfFormDone(r) {
  const fields = sfFormFields();
  const shown = sfShownKeys(r, fields);
  return shown.size > 0 && fields.every((c) => !shown.has(c.key) || sfFilledIn(c, sfFieldValue(r, c).value));
}

/* the records the stage lists: those included at full text, or the benchmark papers while that filter
   is ticked, before the table's other filters */
function sfBaseIds() {
  if (!SF.form) return SF.roundIds;
  const pick = tbTicks(SF.filters, SF_BENCH).length ? SF.formBench : SF.formInc;
  return SF.roundIds.filter((id) => pick.has(id));
}

/* a value of the form as a cell says it: Not reported, Yes or No, the choices, how many passages */
function sfFormWords(c, value) {
  if (value === SF_NR) return SF_NR_WORD;
  if (c.type === 'yesno') return SF_YES_NO[value] || value;
  if (c.type === 'multi') return sfMultiParts(value).join(', ');
  if (c.type === 'passages') { const n = sfPassages(value).length; return n ? t('sift.n_passages', { n }) : ''; }
  return value;
}

// the plan's terms: each block a column the filters alone take, with the lines that say how a database
// found a record holding none of them in the text Sift has (14 October), which the server words (see
// `MATCH_LINES` in sift.py), one for a record none of the others explains among them since 14 October, later
const sfTermCols = () => (SF.blocks || []).map((b) => ({ key: b.key, label: b.label, kind: 'terms', terms: b.terms || [],
  why: b.why || [], shown: false }));

/* Where a record matched a block (14 October): `in`, the fields its terms were found in, Title, Abstract
   or Keywords, and for a block it holds none of, `why`, each line that says how a database found it as
   the filters say it, and `said`, the record's sentence (14 October, later) */
const sfMatched = (r, b) => {
  const m = (r.matched || {})[b.key] || {};
  return { in: m.in || [], why: (m.why || []).map((w) => w.label), said: m.said || '' };
};

/* The Matched in column (14 October): each block of the plan in its order, the fields its terms were
   found in, else its lines in the filters' own words parted by a middle dot, so a line that starts in
   small letters never follows a full stop (14 October, later), and with several blocks each after its
   name, one to a line. */
function sfMatchedLines(r, html) {
  const blocks = SF.blocks || [];
  return blocks.map((b) => {
    const m = sfMatched(r, b);
    const said = m.in.length ? m.in.join(', ') : m.why.join(' · ');
    const text = html ? esc(said) : said;
    return blocks.length > 1 ? `${html ? esc(b.label) : b.label}: ${text}` : text;
  }).join('\n');
}

/* every column the table can show, in his order, each with its key, heading, kind and whether it
   shows, his own columns by his names, their choices and a Number column as a number (13 October),
   and a review column by its name */
function sfColumns(table) {
  // a column of his the form's alone stands on the table at Extract and appraise only (13 October, later),
  // read safely where this runs with no screen
  const formOn = typeof SF !== 'undefined' && !!SF.form;
  const own = new Map(((table && table.own) || []).filter((c) => formOn || c.where !== 'form').map((c) => [c.key, c]));
  const list = table && Array.isArray(table.columns) ? table.columns
    : Object.keys(SF_COLS).map((key) => ({ key, shown: !!SF_COLS[key].on }));
  return list.map(({ key, shown }) => {
    if (SF_COLS[key]) return Object.assign({ key }, SF_COLS[key], { shown: !!shown });
    if (own.has(key)) {
      const c = own.get(key);
      const kind = ['choice', 'number', 'yesno', 'multi', 'long', 'passages'].includes(c.type) ? c.type : 'text';
      return { key, label: c.name, kind, own: true, options: c.options || [], def: c, shown: !!shown };
    }
    if (String(key).startsWith(SF_EXTRA)) return { key, label: sfExtraLabel(key.slice(SF_EXTRA.length)), kind: 'text', extra: true, shown: !!shown };
    return null;
  }).filter(Boolean);
}

/* the first whole number in a value, a year of 2019a as 2019, or null */
function sfNumber(value) {
  const m = String(value === null || value === undefined ? '' : value).match(/\d+/);
  return m ? Number(m[0]) : null;
}

/* the first hundred words of an abstract, and whether there were more */
function sfFirstWords(text, n) {
  const words = String(text || '').split(/\s+/).filter(Boolean);
  return { text: words.slice(0, n).join(' '), cut: words.length > n };
}

/* a record's value in a column, as it sorts and filters: the searches' count, a number, a Number
   column's whole number or null, the decision and its reason at the stage, or the text shown, the ID
   among them */
function sfValue(r, col, stage) {
  const f = r.fields || {};
  const key = col.key;
  // a column that brings its own value and choices, as the reference check's do (14 October)
  if (col.kind === 'picks') return col.value ? col.value(r) : col.pick(r).join(', ');
  if (key === 'found') return (r.found || []).length;
  if (key === 'year') return sfNumber(r.year);
  if (key === 'cited') return typeof r.cited === 'number' ? r.cited : null;
  if (key === 'participants') return f.confirmed ? sfNumber(f.participants) : (f.guess || null);
  if (key === 'rating') return f.rating || null;
  if (key === 'pdf') return r.pdf ? 1 : 0;
  if (key === 'tadec') return ((r.stages || {}).ta || {}).decision || '';
  // a notice by its weight, a retraction first, None nought and Unknown none, and the key works by how many
  if (col.kind === 'notice') { const k = sfNoticeKinds(r); return k === null ? null : Math.max(0, ...k.map((x) => SF_NOTICE_RANK[x] || 0)); }
  if (col.kind === 'keyworks') return Array.isArray(r.cites) ? r.cites.length : null;
  if (col.kind === 'oa') return sfOaWord(r);
  if (col.kind === 'country') return (r.countries || []).join(', ');
  if (col.kind === 'language') return (r.language || []).join(', ');
  if (col.kind === 'study') return r.study || '';
  if (key === 'decision') {
    const st = (r.stages || {})[stage] || {};
    return st.decision ? `${st.decision}${st.decision === 'exclude' && st.reason ? `:${st.reason}` : ''}` : '';
  }
  if (['notes', 'digest', 'critique'].includes(key)) return String(f[key] || '');
  if (key === 'formdone') return sfFormDone(r) ? 1 : 0;
  if (col.kind === 'terms') return ((r.terms || {})[key] || []).length;
  if (col.kind === 'matched') return sfMatchedLines(r, false);
  if (col.own) {
    // a field's value, Sift's while it starts from one, as the form shows it (13 October, later)
    const v = col.def ? sfFieldValue(r, col.def).value : String((f.own || {})[key] || '');
    if (col.kind === 'number') return v === SF_NR ? null : sfNumber(v);
    if (col.kind === 'passages') return v === SF_NR ? 0 : sfPassages(v).length;
    return col.kind === 'multi' || col.kind === 'yesno' ? sfFormWords(col.def || col, v) : v;
  }
  if (col.extra) {
    const hit = (r.more || []).find(([name]) => name === key.slice(SF_EXTRA.length));
    return hit ? String(hit[1]) : '';
  }
  return String(r[key] || '');
}

/* two values of a column of Sift's in order, neither empty, as the family's table sorts them (tbCmp): a
   number by its size, a decision by its order then its reason, a choice of his in his order, and words
   and the ID in natural order, R002 before R010 */
function sfOrder(a, b, col) {
  if (['number', 'found', 'pdf', 'notice', 'keyworks', 'passages', 'formdone', 'terms'].includes(col.kind) || col.num) return a - b;
  if (col.kind === 'decision' || col.kind === 'tadec') {
    const [da, ra = ''] = a.split(':');
    const [db, rb = ''] = b.split(':');
    return (SF_ORDER[da] || 0) - (SF_ORDER[db] || 0) || TB_TEXT.compare(ra, rb);
  }
  if (col.kind === 'choice') {
    const at = (v) => { const i = (col.options || []).indexOf(v); return i < 0 ? 1e6 : i; };
    return at(a) - at(b) || TB_TEXT.compare(a, b);
  }
  return TB_TEXT.compare(a, b);
}

/* A slider's filter as held: the lowest and the highest whole number, either of them open, null, and
   whether the records with none are ticked. Anything else held reads as nothing set. */
function sfRangeHeld(f) {
  if (!f || typeof f !== 'object' || Array.isArray(f)) return { from: null, to: null, none: false };
  const end = (v) => (v === null || v === undefined || v === '' ? null : sfNumber(v));
  return { from: end(f.from), to: end(f.to), none: f.none === true };
}

/* a record's whole number in a slider's column, the year, the count of citations, the count of
   participants or the guess, nought among them, or its stars, and null when it has none, so a record
   not rated stands under Not rated and never at nought (12 October) */
function sfRangeValue(r, col, stage) {
  const v = sfValue(r, col, stage);
  return typeof v === 'number' ? v : null;
}

/* whether a column's filter holds anything: a tick, either end of a slider moved, or the tick of the
   records with none under a slider */
function sfFilterOn(col, f) {
  if (sfIsRange(col)) {
    const h = sfRangeHeld(f);
    return h.from !== null || h.to !== null || h.none;
  }
  return tbTickList(f).length > 0;
}

/* Whether a record passes a column's filter: with a slider, its number between the two ends when
   either is moved, or none when None is ticked, and with ticks any one ticked. A filter that holds
   nothing lets every record through. */
function sfPasses(r, col, f, stage) {
  if (!sfFilterOn(col, f)) return true;
  if (sfIsRange(col)) {
    const h = sfRangeHeld(f);
    const v = sfRangeValue(r, col, stage);
    if (v === null) return h.none;
    return (h.from !== null || h.to !== null) && (h.from === null || v >= h.from) && (h.to === null || v <= h.to);
  }
  const ticks = tbTickList(f);
  return sfPicked(r, col, stage).some((v) => ticks.includes(v));
}

/* a review column's values as picks know them, each once, a list in a cell parted, the publication
   type's in plain words so the databases' words for one type stand as one choice */
const sfIsType = (col) => !!col && col.key === `${SF_EXTRA}pub_type`;
const sfReviewPicks = (r, col) => [...new Set((sfIsType(col) ? sfTypeParts(sfValue(r, col, 'ta'))
  : sfParts(sfValue(r, col, 'ta'))).map(sfPickKey))];

/* Whether a column has a group in the filters' sidebar: Database, PDF, Decision, Year, Cited by, My
   rating and Participants, a choice or Number column of his, the journal and the publication type
   always, however many they hold, and any other review column whose records hold from 2 to 30
   different values. Words, the ID and the rest are found by the browser's own find. */
function sfPickable(col, records) {
  if (['found', 'pdf', 'decision', 'tadec', 'picks'].includes(col.kind) || sfIsRange(col)) return true;
  // the columns of 13 October once a record holds something in them, so a screening never filled from
  // OpenAlex or Crossref, or with no study linked, has no group of Unknown alone, and Cites key works
  // while the review has key works too
  const any = (has) => (records || []).some(has);
  if (col.kind === 'notice') return any((r) => sfNoticeKinds(r) !== null);
  if (col.kind === 'oa') return any((r) => !!r.oa);
  if (col.kind === 'country') return any((r) => (r.countries || []).length > 0);
  if (col.kind === 'language') return any((r) => (r.language || []).length > 0);
  if (col.kind === 'study') return any((r) => !!r.study);
  if (col.kind === 'keyworks') return (SF.keyWorks || []).length > 0 && any((r) => Array.isArray(r.cites));
  // Form at Extract and appraise, each block of the plan with terms, and a field of his that holds choices
  if (col.kind === 'formdone') return sfFormOn();
  if (col.kind === 'terms') return (col.terms || []).length > 0;
  if (col.own) return ['choice', 'yesno', 'multi'].includes(col.kind);
  if (!col.extra && col.key !== 'journal') return false;
  if (SF_PICK_ALWAYS.includes(col.key)) return true;
  const seen = new Set();
  for (const r of records || []) {
    sfReviewPicks(r, col).forEach((v) => seen.add(v));
    if (seen.size > SF_PICK_MAX) return false;
  }
  return seen.size >= SF_PICK_MIN;
}

/* The choices a record stands under in a column's group: each database that found it, once, More
   than one and New in this run, PDF or No PDF, its decision at the stage with its reason, and
   Differs from the proposal and Where we differ where it does, its stars or none, a value of his, each
   value a review column's cell holds, or its year or count of participants, and none when it holds
   nothing. A search's name and a review's value go by their key, case and spacing set aside. */
function sfPicked(r, col, stage) {
  if (col.kind === 'picks') return col.pick(r);
  if (col.kind === 'found') {
    const found = [...new Set((r.found || []).map(sfPickKey))].filter(Boolean);
    return [...found, ...(found.length > 1 ? [SF_MANY] : []), ...(r.new ? [SF_NEW] : [])];
  }
  if (col.kind === 'pdf') return [r.pdf ? 'yes' : 'no'];
  if (col.kind === 'notice') { const k = sfNoticeKinds(r); return k === null ? [TB_BLANK] : k.length ? k : ['none']; }
  if (col.kind === 'oa') return [r.oa ? (r.oa === 'closed' ? 'closed' : 'open') : TB_BLANK];
  if (col.kind === 'keyworks') return !Array.isArray(r.cites) ? [TB_BLANK] : r.cites.length ? r.cites : ['none'];
  if (col.kind === 'country') { const c = (r.countries || []).map(sfPickKey); return c.length ? c : [TB_BLANK]; }
  if (col.kind === 'language') { const l = (r.language || []).map(sfPickKey); return l.length ? l : [TB_BLANK]; }
  if (col.kind === 'study') return [r.study || TB_BLANK];
  if (col.kind === 'tadec') return [((r.stages || {}).ta || {}).decision || TB_BLANK];
  if (col.kind === 'formdone') return [sfFormDone(r) ? 'done' : 'todo'];
  if (col.kind === 'terms') {
    // a record holding two or more of the block's terms stands under More than one too, and one holding
    // none of them under each line that says how a database found it (14 October, later), the line for a
    // record none of the others explains being the bar and none, the blank
    const got = (r.terms || {})[col.key] || [];
    if (got.length) return got.length > 1 ? [...got, SF_MANY] : got;
    const why = (((r.matched || {})[col.key] || {}).why || []).map((w) => w.value);
    return why.length ? why : [TB_BLANK];
  }
  if (col.own && (col.kind === 'multi' || col.kind === 'yesno' || col.kind === 'choice')) {
    const v = col.def ? sfFieldValue(r, col.def).value : String(((r.fields || {}).own || {})[col.key] || '');
    if (v === SF_NR) return [SF_NR];
    const got = col.kind === 'multi' ? sfMultiParts(v) : [String(v).trim()].filter(Boolean);
    return got.length ? got : [TB_BLANK];
  }
  if (col.kind === 'decision') {
    const st = (r.stages || {})[stage] || {};
    const more = [...(st.differs ? [SF_DIFFERS] : []), ...(st.apart ? [SF_APART] : [])];
    if (!st.decision) return ['undecided', ...more];
    return (st.decision === 'exclude' && st.reason ? ['exclude', `exclude:${st.reason}`] : [st.decision]).concat(more);
  }
  if (col.extra || col.key === 'journal') {
    const picks = sfReviewPicks(r, col);
    return picks.length ? picks : [TB_BLANK];
  }
  if (sfIsRange(col)) {
    const v = sfRangeValue(r, col, stage);
    return [v === null ? TB_BLANK : String(v)];
  }
  const text = String(sfValue(r, col, stage) || '').trim();
  return [text || TB_BLANK];
}

/* each search's and review value's words as most records write them, by its key, a tie the first */
function sfWritten(records, col) {
  const forms = new Map();
  for (const r of records || []) {
    const said = col.kind === 'found' ? (r.found || []) : col.kind === 'country' ? (r.countries || [])
      : col.kind === 'language' ? (r.language || [])
      : sfIsType(col) ? sfTypeParts(sfValue(r, col, 'ta')) : sfParts(sfValue(r, col, 'ta'));
    for (const s of said) {
      const key = sfPickKey(s);
      if (!forms.has(key)) forms.set(key, new Map());
      forms.get(key).set(s, (forms.get(key).get(s) || 0) + 1);
    }
  }
  const out = new Map();
  forms.forEach((n, key) => { out.set(key, [...n.entries()].reduce((a, b) => (b[1] > a[1] ? b : a))[0]); });
  return out;
}

/* The filters' groups, one for each column a pick can filter, shown or hidden, in the columns'
   order, each under its column's name, PDF's as Full text PDF, with its ⓘ line where it has one, and
   with its choices in order, a choice its value, its words, a database's colour, and a reason's
   meaning and place under No or Exclude. Each database by name, once however many records or lists of them
   carry it, the one most rows of the round carry first, then More than one and New in this run, PDF
   and No PDF, To screen and the stage's words, Yes, Maybe and No or Include, Maybe and Exclude, with
   each reason of the stage, his choices in his
   order, a review column's values the most carried first, each once in the words most records write
   it, and none last where a row of the round holds nothing. Year, No. of participants, Rating and a
   Number column of his are each a slider, `range`, from the lowest whole
   number the round's rows hold to the highest, `low` and `high`, the rating always from nought to
   five, the others with None, the records with none, under it. A group whose choices never change
   is `fixed`, and any other offers the values the round's rows hold and every value ticked. */
function sfGroups(rows, records, cols, stage, codes, filters) {
  const out = [];
  for (const col of cols) {
    if (col.kind === 'id' || !sfPickable(col, records)) continue;
    const head = { key: col.key, label: SF_GROUP_WORDS[col.key] || col.label, about: SF_GROUP_ABOUT[col.key] || '', col };
    // beside Country the link that shows its counts on a map (13 October, later)
    if (col.kind === 'country') head.tool = { act: 'map', label: SF_MAP_WORDS.link };
    // the records with none in a slider's column, a tick of their own under it in plain words
    const none = [{ value: TB_BLANK, label: sfBlankWord(col) || SF_CHOICE_WORDS[TB_BLANK] }];
    if (col.key === 'rating') {
      out.push(Object.assign(head, { range: true, fixed: true, low: 1, high: 5, choices: none }));
      continue;
    }
    if (sfIsRange(col)) {
      const nums = rows.map((r) => sfRangeValue(r, col, stage)).filter((v) => v !== null);
      out.push(Object.assign(head, { range: true, fixed: true,
        low: nums.length ? Math.min(...nums) : null, high: nums.length ? Math.max(...nums) : null, choices: none }));
      continue;
    }
    const held = new Map();
    for (const r of rows) new Set(sfPicked(r, col, stage)).forEach((v) => held.set(v, (held.get(v) || 0) + 1));
    const written = col.kind === 'found' || col.extra || col.key === 'journal' || col.kind === 'country' || col.kind === 'language'
      ? sfWritten(records, col) : new Map();
    const word = (v) => ({ value: v, label: (v === TB_BLANK && SF_BLANK_WORDS[col.key]) || (v === SF_NR && col.own ? SF_NR_WORD : '')
      || SF_CHOICE_WORDS[v] || written.get(v) || v });
    const blank = held.has(TB_BLANK) ? [word(TB_BLANK)] : [];
    // the databases and the review's values most of the round's rows carry first, so a long group's
    // first four are its biggest, a tie in the order of their words
    const byWords = (a, b) => (held.get(b.value) || 0) - (held.get(a.value) || 0) || TB_TEXT.compare(a.label, b.label);
    let choices;
    let fixed = true;
    const unknown = { value: TB_BLANK, label: SF_BLANK_WORDS[col.key] || SF_CHOICE_WORDS[TB_BLANK] };
    if (col.kind === 'pdf') choices = [{ value: 'yes', label: t('sift.col.pdf') }, { value: 'no', label: t('sift.no_pdf') }];
    else if (col.kind === 'notice') {
      choices = ['retracted', 'expression of concern', 'corrected', 'none'].map((v) => ({ value: v, label: SF_NOTICE_WORDS[v] })).concat([unknown]);
    } else if (col.kind === 'oa') choices = [{ value: 'open', label: t('sift.oa.open') }, { value: 'closed', label: t('sift.oa.closed') }, unknown];
    else if (col.kind === 'keyworks') {
      choices = (SF.keyWorks || []).map((k) => ({ value: k.key, label: k.label })).concat([{ value: 'none', label: t('sift.none') }, unknown]);
    } else if (col.kind === 'study') {
      // each study he has linked, in its number's order, then the records linked to none
      fixed = false;
      choices = [...held.keys()].filter((v) => v !== TB_BLANK).sort((a, b) => TB_TEXT.compare(a, b)).map((v) => ({ value: v, label: v }))
        .concat(held.has(TB_BLANK) ? [unknown] : []);
      const known = new Set(choices.map((c) => c.value));
      tbTicks(filters, col.key).filter((v) => !known.has(v)).forEach((v) => choices.push({ value: v, label: v }));
    }
    else if (col.kind === 'formdone') choices = ['done', 'todo'].map((v) => ({ value: v, label: SF_DONE_WORDS[v] }));
    else if (col.kind === 'picks') {
      // its own choices where it brings them, else the values the round's rows hold, each in its own
      // words, and any ticked that none now holds (14 October), as the family's table groups them
      ({ fixed, choices } = tbGroups(rows, [col], filters)[0]);
    }
    else if (col.kind === 'terms') {
      // the block's terms as he wrote them, More than one where it has two or more, then the lines that say
      // how a database found a record holding none of them, `line`, each under the heading the server words
      // (14 October, later)
      choices = (col.terms || []).map((t) => ({ value: t, label: t }))
        .concat((col.terms || []).length > 1 ? [{ value: SF_MANY, label: SF_CHOICE_WORDS[SF_MANY] }] : [])
        .concat((col.why || []).map((w) => ({ value: w.value, label: w.label, wrap: true, line: true })));
    } else if (col.own && col.kind === 'yesno') {
      choices = [{ value: 'yes', label: SF_YES_NO.yes }, { value: 'no', label: SF_YES_NO.no }, { value: SF_NR, label: SF_NR_WORD }, unknown];
    }
    else if (col.kind === 'tadec') {
      const ta = sfWords('ta');
      choices = [{ value: 'include', label: ta.include, dec: 'include' }, { value: 'maybe', label: ta.maybe, dec: 'maybe' }];
    }
    else if (col.kind === 'decision') {
      // Differs from the proposal while a record shows a proposal at the stage, and Where we differ
      // while the second screener's side holds a difference there, each as `sfMark` marks the records,
      // the one filter of where a record stands, as the dropdown over the table was until 12 October
      const at = (r) => (r.stages || {})[stage] || {};
      const proposed = (records || []).some((r) => at(r).proposed);
      const apart = (records || []).some((r) => at(r).apart);
      // each decision with its colour's dot, To screen's grey (12 October), in the stage's words, the
      // ticks kept by their values, undecided, include, maybe and exclude, as sift.json holds them
      const w = sfWords(stage);
      choices = [['undecided', SF_TO_SCREEN], ['include', w.include], ['maybe', w.maybe], ['exclude', w.exclude]]
        .map(([value, label]) => ({ value, label, dec: value === 'undecided' ? '' : value }))
        .concat((codes || []).map((c) => ({ value: `exclude:${c.code}`, label: c.code, meaning: c.meaning || '', sub: true })))
        .concat(proposed ? [{ value: SF_DIFFERS, label: t('sift.differs') }] : [])
        .concat(apart ? [{ value: SF_APART, label: t('sift.two.apart') }] : []);
    } else {
      fixed = false;
      if (col.kind === 'found') {
        const names = [...held.keys()].filter((v) => v !== SF_MANY && v !== SF_NEW).map(word).sort(byWords)
          .map((c) => Object.assign(c, { db: sfDbKey(c.label) }));
        choices = [...names, word(SF_MANY), ...((records || []).some((r) => r.new) ? [word(SF_NEW)] : [])];
      } else {
        const mine = col.own ? (col.options || []) : [];
        const rest = [...held.keys()].filter((v) => v !== TB_BLANK && !mine.includes(v)).map(word).sort(byWords);
        // the databases an abstract was taken from, each with its colour
        if (col.key === 'csv:abstract_from') rest.forEach((c) => Object.assign(c, { db: sfDbKey(c.label) }));
        choices = [...mine.map(word), ...rest].concat(blank);
      }
      const known = new Set(choices.map((c) => c.value));
      tbTicks(filters, col.key).filter((v) => !known.has(v)).forEach((v) => { choices.push(word(v)); known.add(v); });
    }
    out.push(Object.assign(head, { fixed, choices }));
  }
  return out;
}

/* The filters as the sidebar holds them, read from whatever form they were held in. A group of ticks
   holds a list: a list as it is, and an older pick of one search, decision, PDF or choice of his as a
   list of one, a search by its key. A slider holds from, to and None: an older range as it was, and
   older ticks of years, stars, bands of participants or None as the ends they span and None, the
   rating never holding None, since a record with no stars stands at nought. A column with no group,
   words or a number searched, and a value a fixed group never offers are let go. */
function sfTicksRead(filters, groups) {
  const out = {};
  for (const g of groups) {
    const f = (filters || {})[g.key];
    const col = g.col || {};
    if (g.range) {
      let h = sfRangeHeld(f);
      if (Array.isArray(f)) {
        const ends = [];
        f.forEach((v) => {
          const m = String(v).match(/^(\d+)(?:-(\d+)|(\+))?$/);
          if (m) ends.push([Number(m[1]), m[3] ? null : Number(m[2] || m[1])]);
        });
        h = { from: ends.length ? Math.min(...ends.map((e) => e[0])) : null,
          to: ends.length && ends.every((e) => e[1] !== null) ? Math.max(...ends.map((e) => e[1])) : null,
          none: f.includes(TB_BLANK) };
      }
      if (!g.choices.length) h.none = false;
      if (h.from !== null && h.to !== null && h.from > h.to) h = Object.assign(h, { from: h.to, to: h.from });
      if (h.from !== null || h.to !== null || h.none) out[g.key] = h;
      continue;
    }
    let list = tbTickList(f);
    if (typeof f === 'string' && f.trim() && (['found', 'decision', 'pdf'].includes(col.kind) || col.own)) {
      list = [col.kind === 'found' ? sfPickKey(f) : f];
    }
    if (g.fixed) list = list.filter((v) => g.choices.some((c) => c.value === v));
    list = [...new Set(list)];
    if (list.length) out[g.key] = list;
  }
  return out;
}

/* The filters sift.json keeps read as a screening opens, as `sfTicksRead` reads any, with every group
   taken as fixed, so a tick naming a choice no record of the screening now carries, a database, a
   value or a reason gone, is let go, and a column gone with its group. `groups` come from every
   record of the screening. */
function sfKeptRead(kept, groups) {
  return sfTicksRead(kept, groups.map((g) => Object.assign({}, g, { fixed: true })));
}

/* the find boxes' words sift.json keeps, each for a group of ticks the screening still has */
function sfFindRead(find, groups) {
  const out = {};
  if (!find || typeof find !== 'object') return out;
  groups.forEach((g) => {
    if (!g.range && typeof find[g.key] === 'string' && find[g.key].trim()) out[g.key] = find[g.key];
  });
  return out;
}

/* The filters and the find boxes' words as one line, as sift.json keeps them: the columns in order,
   each find box's words on one line and an empty one left out, so the same filters give the same
   line and a change is told from none. */
function sfKeptJson(filters, find) {
  const sorted = (o, take) => Object.fromEntries(Object.keys(o && typeof o === 'object' ? o : {}).sort()
    .map((k) => [k, take(o[k])]).filter(([, v]) => v !== null));
  const words = (w) => (typeof w === 'string' && w.trim() ? w.split(/\s+/).filter(Boolean).join(' ').slice(0, 200) : null);
  return JSON.stringify({ filters: sorted(filters, (v) => v), find: sorted(find, words) });
}

/* What a record is counted under in a group, as the family's table counts the choices (tbFacetCounts):
   its picks at the stage, and under a slider `|range` while its number stands between the two ends,
   every record with a number while neither end is moved, and None with none. */
function sfUnder(r, g, f, stage) {
  if (!g.range) return sfPicked(r, g.col, stage);
  const h = sfRangeHeld(f);
  const v = sfRangeValue(r, g.col, stage);
  if (v === null) return [TB_BLANK];
  return (h.from === null || v >= h.from) && (h.to === null || v <= h.to) ? [SF_RANGE] : [];
}

/* Sift's records as the family's table reads them at a stage (TB_READ in table.js): their values and
   picks at the stage, its kinds in their order, its sliders' filters, and what each is counted under */
const sfRead = (stage) => ({
  value: (r, col) => sfValue(r, col, stage),
  order: sfOrder,
  picked: (r, col) => sfPicked(r, col, stage),
  on: sfFilterOn,
  passes: (r, col, f) => sfPasses(r, col, f, stage),
  under: (r, g, f) => sfUnder(r, g, f, stage),
});

/* The runs of numbers a slider's chart has a bar for, from its lowest to its highest: the year's five
   years each, from a year that ends in 0 or 5, or ten, 25 or more when five would make more than 30
   bars, the participants' five each to 50, 1 to 5 and on, then 51 to 100, 101 to 200, 201 to 500,
   501 to 1000 and 1001 and over, a nought among the first, the counts of citations' nought, then 1 to
   5, 6 to 10, 11 to 25 and wider runs to 1001 and over, and the rating's one star each. Each bar is
   `from` and `to`, its run kept to the lowest and the highest, `label`, the run in words, and `n`,
   nought. */
function sfBarSpans(key, low, high) {
  const runs = [];
  if (key === 'year') {
    const width = SF_BAR_YEARS.find((w) => Math.floor(high / w) - Math.floor(low / w) < SF_BARS) || SF_BAR_YEARS[SF_BAR_YEARS.length - 1];
    for (let at = Math.floor(low / width) * width; at <= high; at += width) runs.push([at, at + width - 1]);
  } else if (key === 'participants') {
    for (let at = 1; at <= SF_BAR_FIVES; at += 5) runs.push([at, at + 4]);
    runs.push(...SF_BAR_WIDE, [SF_BAR_WIDE[SF_BAR_WIDE.length - 1][1] + 1, Infinity]);
    runs[0] = [Math.min(runs[0][0], low), runs[0][1]];
  } else if (key === 'cited') {
    runs.push(...SF_BAR_CITED, [SF_BAR_CITED[SF_BAR_CITED.length - 1][1] + 1, Infinity]);
  } else for (let at = low; at <= high; at += 1) runs.push([at, at]);
  return runs.filter(([a, b]) => b >= low && a <= high).map(([a, b]) => {
    const bar = { from: Math.max(a, low), to: Math.min(b, high),
      label: a === b ? String(a) : b === Infinity ? t('sift.bar.over', { from: a }) : t('sift.bar.run', { from: a, to: b }), n: 0 };
    // its run as the tip says it, 2015 to 2019, kept on the bar out of its own fields
    Object.defineProperty(bar, 'said', { value: a === b ? String(a) : b === Infinity ? t('sift.bar.over', { from: a })
      : t('sift.bar.to', { from: a, to: b }) });
    return bar;
  });
}

/* A slider's chart, by group: a bar for each run of `sfBarSpans`, each with how many rows stand in it,
   counted as the counts are, the other groups' filters taken and its own set aside. */
function sfRangeBars(rows, groups, filters, stage) {
  const out = Object.create(null);
  // a Number column of his takes the participants' bars (13 October)
  groups.forEach((g) => {
    if (g.range && g.low !== null) out[g.key] = sfBarSpans(g.col && g.col.own ? 'participants' : g.key, g.low, g.high);
  });
  tbEachOpen(rows, groups, filters, (r, g) => {
    const bars = out[g.key];
    const v = bars ? sfRangeValue(r, g.col, stage) : null;
    const bar = v === null ? null : bars.find((b) => v >= b.from && v <= b.to);
    if (bar) bar.n += 1;
  }, sfRead(stage));
  return out;
}

/* A slider's track laid out by its chart's bars (12 October): each bar an equal stretch of it, the
   first from 0 to 1, the next from 1 to 2 and on, so each bar stands over its own stretch however many
   numbers it holds, and a handle dragged or moved with the arrows goes a whole bar at a time. The
   year's and the participants' tracks go so when they have two bars or more, as `[from, to]` runs,
   and the rating's, and one bar alone, stay a whole number a step, null. */
function sfTrack(key, bars) {
  if (key === 'rating' || !Array.isArray(bars) || bars.length < 2) return null;
  return bars.map((b) => [b.from, b.to]);
}

/* the runs a group carries in its data-runs, "2017-2019 2020-2024", or null */
function sfTrackRead(text) {
  const runs = String(text || '').trim().split(/\s+/).filter(Boolean)
    .map((part) => part.split('-').map(Number)).filter((r) => r.length === 2 && r.every(Number.isFinite));
  return runs.length > 1 ? runs : null;
}

/* the bar a number stands in, the first or the last for one outside them */
function sfTrackBar(runs, v) {
  const i = runs.findIndex(([a, b]) => v >= a && v <= b);
  return i >= 0 ? i : v < runs[0][0] ? 0 : runs.length - 1;
}

/* Where a number stands on a track by bars: the lower end at the start of its own place in its bar
   and the upper at the end of it, so a bar's first number is its left edge and its last its right.
   A number typed between two edges stands at its place inside its bar. */
function sfTrackAt(runs, v, end) {
  const i = sfTrackBar(runs, v);
  const [a, b] = runs[i];
  const width = b - a + 1;
  const into = Math.max(0, Math.min(width, v - a + (end === 'to' ? 1 : 0)));
  return i + into / width;
}

/* the edge a handle may stand at, a whole place on the track: the lower from the first bar's start to
   the last bar's, the upper from the first bar's end to the last bar's */
function sfTrackSnap(runs, pos, end) {
  const k = Math.round(Number(pos) || 0);
  return end === 'from' ? Math.max(0, Math.min(runs.length - 1, k)) : Math.max(1, Math.min(runs.length, k));
}

/* the number at an edge: the lower handle's the first number of the bar it starts, the upper's the
   last of the bar it ends */
function sfTrackEdge(runs, k, end) {
  const at = sfTrackSnap(runs, k, end);
  return end === 'from' ? runs[at][0] : runs[at - 1][1];
}

/* the next edge from where a handle stands, a bar on with `dir` 1 and a bar back with -1, from inside
   a bar to its own edge first */
function sfTrackStep(runs, pos, end, dir) {
  const p = Number(pos) || 0;
  return sfTrackSnap(runs, dir > 0 ? Math.floor(p + 1e-6) + 1 : Math.ceil(p - 1e-6) - 1, end);
}

/* a database's colour by its name: its own for each database Sift knows, and one of the palette's
   for any other, the same for the same name wherever it stands */
function sfDbKey(name) {
  const key = sfPickKey(name);
  if (SF_DB_COLOURS[key]) return SF_DB_COLOURS[key];
  let h = 0;
  for (const ch of key) h = (h * 31 + ch.charCodeAt(0)) % 1009;
  return `p${h % SF_DB_PALETTE}`;
}

/* a database as a pill in its colour, and a category's values as pills, each value of a list its own */
const sfDbPill = (name) => `<span class="sf-db" data-db="${sfDbKey(name)}">${esc(name)}</span>`;
const sfCatPills = (value) => sfTypeParts(value).map((v) => `<span class="sf-cat">${esc(v)}</span>`).join('');

/* a reason as a pill, its code inside and its meaning from reasons.csv on hover */
function sfReasonPill(code) {
  const meaning = sfMeaning(code);
  return `<span class="sf-pill sf-rpill"${meaning ? ` title="${escAttr(meaning)}"` : ''}>${esc(code)}</span>`;
}

/* a suggestion's reason under its decision: a reason code on a No or Exclude as its red pill with its meaning
   beside it, and anything else, a review's own words on a Maybe among them, as a plain sentence that wraps,
   since red means No and Exclude alone and a pill never wraps (17 October, where a Maybe's sentence ran out of
   its card at 360 as a red pill) */
function sfPropReasonHtml(prop) {
  const reason = String((prop && prop.reason) || '').trim();
  if (!reason) return '';
  const meaning = sfMeaning(reason);
  if (prop.decision === 'exclude' && (meaning || /^\S{1,12}$/.test(reason))) {
    return `${sfReasonPill(reason)}${meaning ? ` ${esc(meaning)}` : ''}`;
  }
  return `<span class="sf-prop-why">${esc(sfSentence(meaning ? `${reason} ${meaning}` : reason))}</span>`;
}

/* words shown as a sentence end with a full stop where they end with none of their own, a question mark, an
   exclamation mark or an ellipsis among their own, a closing quotation mark or bracket after it too, and a
   trailing comma, colon or semicolon giving way to it (17 October, later) */
function sfSentence(words) {
  const said = String(words || '').trim().replace(/[\s,;:]+$/, '');
  if (!said) return '';
  return /[.!?…]["'’”)\]]*$/.test(said) ? said : `${said}.`;
}

/* a review column's value as the table and the record show it: the databases an abstract was taken
   from as their pills, the publication type as pills, and any other as text or a link */
function sfReviewCell(name, value) {
  if (name === 'abstract_from') return sfParts(value).map(sfDbPill).join('');
  if (name === 'pub_type') return sfCatPills(value);
  return sfLinked(value);
}

/* what a cell or a field with nothing in it reads, in the faint ink: Unknown, No year, Not rated or
   No count (12 October) */
const sfBlankHtml = (key) => `<span class="sf-blank">${SF_BLANK_WORDS[key]}</span>`;

/* the line on hover that says where a record's count of citations came from and on which day */
const sfCitedTitle = (r) => (r.cited_date ? ` title="${escAttr(t('sift.cited_from', { day: tbDayWords(r.cited_date) }))}"` : '');

/* ── the filters' order and Country on a map, worked out with no page (13 October, later) ── */

/* Whether a group keeps its own order, being a scale: the sliders, At title and abstract, the form's
   Done and To do, and his own columns' choices as he set them. The decision keeps its four in order
   too, its reasons under Exclude going by their counts among themselves (see `sfFacetOrder`). */
const sfOwnOrder = (g) => !!g.range || ['tadec', 'formdone'].includes((g.col || {}).kind) || !!(g.col || {}).own;

/* A group's choices in the order the sidebar draws them (13 October, later), as the family's table puts
   them (tbFacetOrder): by their counts as the filters stand, the most first, the noughts last, a tie in
   the order the group gives them, the plan's for a block's terms, as Adam's other app orders its filters,
   so Show more shows the top of the list first. A block's terms go by their counts among themselves,
   then More than one, then its lines by their counts among themselves (14 October, later). A scale keeps
   its own order (see `sfOwnOrder`). */
function sfCountOrder(g, counts) {
  if (sfOwnOrder(g)) return g.choices;
  if ((g.col || {}).kind === 'terms') {
    const part = (keep) => g.choices.filter(keep);
    return [...tbByCount(part((c) => !c.line && c.value !== SF_MANY), counts), ...part((c) => c.value === SF_MANY),
      ...tbByCount(part((c) => c.line), counts)];
  }
  if ((g.col || {}).kind === 'decision') {
    const subs = tbByCount(g.choices.filter((c) => c.sub), counts);
    let k = 0;
    return g.choices.map((c) => (c.sub ? subs[k++] : c));
  }
  return tbByCount(g.choices, counts);
}

/* a group's choices in Sift's order, with `held`, the values of the group he is ticking in as last drawn,
   standing as the family's table keeps them */
const sfFacetOrder = (g, counts, held) => tbFacetOrder(g, counts, held, sfCountOrder);

/* The map's words, in one place: the link beside Country in the filters, the map's name for a screen
   reader and in a saved file, its two buttons, the file's name after the run's, the line when the
   map cannot be read, and the note under the map in the overlay alone, never in a saved file */
const SF_MAP_WORDS = { link: t('sift.map.link'), head: t('sift.map.head'), png: t('sift.map.png'), svg: t('sift.map.svg'),
  file: 'countries', missing: t('sift.map.missing'),
  note: t('sift.map.note') };
// the map in the light appearance on white, as a file saved for a paper carries it whatever the app's
// appearance, each the light value of its token in sift.css
const SF_MAP_PAPER = { paper: '#FFFFFF', sea: '#EAEFF1', land: '#D8D2C6', border: '#FFFFFF', dot: '#D65A4E', ring: '#FFFFFF',
  num: '#FFFFFF', line: '#8E887E', name: '#3E3A34' };
// a circle's radius in the map's frame, 1000 wide: the largest's, a count of one's at most, so a run
// of a few records is not all large circles, and the least, which still holds its number
const SF_MAP_MOST = 40;
const SF_MAP_UNIT = 14;
const SF_MAP_LEAST = 11;
// the gap kept between two circles, the steps they grow to their size in, the passes on each step
// that set them apart, and how far each is drawn back towards its own point on each pass
const SF_MAP_GAP = 2;
const SF_MAP_GROW = 40;
const SF_MAP_PASSES = 6;
const SF_MAP_PULL = 0.04;
// a country's name: its type, its gap from its circle, and how much further out it is tried in turn
const SF_MAP_NAME = 9;
const SF_MAP_PAD = 3;
const SF_MAP_OUT = [0, 5, 10, 16, 24, 34, 46];
// a saved PNG's width in pixels
const SF_MAP_PNG = 3000;

/* What the map shows (13 October, evening): a circle for each country the Country group counts a
   record under, its area following its count, the radius by the square root, scaled so the largest
   is SF_MAP_MOST across its radius, a count of one at most SF_MAP_UNIT, and none under SF_MAP_LEAST,
   so every circle holds its number, the largest first so the smaller are drawn over them. Each starts
   at its country's label point in world.json and is set apart from the others by sfMapLayout, and its
   country's name is placed beside it by sfMapNames. A country is known by the name the column gives
   it, world.json naming each as Sift does. `choices` and `counts` are the group's, `total` the records
   its counts stand on and `blank` those with no country, and a country the map has no point for is
   listed in `unplaced` with its count. */
function sfMapModel(world, choices, counts, total) {
  const n = counts || {};
  const named = new Map(Object.entries((world && world.names) || {}).map(([code, name]) => [sfPickKey(name), code]));
  const points = (world && world.points) || {};
  const circles = [];
  const unplaced = [];
  for (const c of choices || []) {
    const k = n[c.value] || 0;
    if (!k || c.value === TB_BLANK) continue;
    const code = named.get(c.value) || (/^[a-z]{2}$/.test(c.value) ? c.value.toUpperCase() : '');
    const at = code ? points[code] : null;
    if (Array.isArray(at)) circles.push({ code, name: c.label, n: k, x: at[0], y: at[1] });
    else unplaced.push({ name: c.label, n: k });
  }
  const most = circles.reduce((top, c) => Math.max(top, c.n), 1);
  const unit = Math.min(SF_MAP_UNIT, SF_MAP_MOST / Math.sqrt(most));
  circles.forEach((c) => { c.r = Math.round(Math.max(SF_MAP_LEAST, unit * Math.sqrt(c.n)) * 100) / 100; });
  circles.sort((a, b) => b.n - a.n || TB_TEXT.compare(a.name, b.name));
  unplaced.sort((a, b) => b.n - a.n || TB_TEXT.compare(a.name, b.name));
  const w = (world && world.width) || 1000;
  const h = (world && world.height) || 500;
  sfMapLayout(circles, w, h);
  sfMapNames(circles, w, h);
  return { circles, unplaced, blank: n[TB_BLANK] || 0, total: total || 0 };
}

/* The circles set apart (13 October, evening). Each starts at its country's point, `hx` and `hy`, as a
   circle of no size, and the circles grow to their full size over SF_MAP_GROW steps. On each pass of a
   step each is drawn back towards its own point by SF_MAP_PULL, then any two nearer than their radii
   and SF_MAP_GAP are pushed apart along the line between them, each kept inside the frame. Each takes
   a share of the push that falls steeply with its size, by the fourth power of its radius, so the
   larger stays nearest home and the smaller moves round it. Growing slowly, no circle passes through
   another, so each keeps its side of its neighbours as their countries do. Passes with no pull and a
   push shared by area follow until no two touch. A fixed order, a fixed number of passes and nothing
   random, so the same counts give the same map every time, as a figure must. `off` is how far a
   circle ended from its point, and `line` whether its point is out from under it, so a line runs back
   to it. */
function sfMapLayout(circles, w, h) {
  let grown = 0;
  const keep = (c) => {
    const r = c.r * grown;
    c.x = Math.min(w - r, Math.max(r, c.x));
    c.y = Math.min(h - r, Math.max(r, c.y));
  };
  const apart = (power) => {
    let touched = false;
    for (let i = 0; i < circles.length; i += 1) {
      for (let j = i + 1; j < circles.length; j += 1) {
        const a = circles[i];
        const b = circles[j];
        const need = (a.r + b.r + SF_MAP_GAP) * grown;
        if (Math.abs(b.x - a.x) >= need || Math.abs(b.y - a.y) >= need) continue;
        const d = Math.hypot(b.x - a.x, b.y - a.y);
        if (d >= need - 1e-6) continue;
        // two on the very same point part along a turn fixed by their places in the order
        const turn = (i * 7 + j * 13) * 0.618;
        const ux = d > 1e-6 ? (b.x - a.x) / d : Math.cos(turn);
        const uy = d > 1e-6 ? (b.y - a.y) / d : Math.sin(turn);
        const share = b.r ** power / (a.r ** power + b.r ** power);
        const push = need - d;
        a.x -= ux * push * share;
        a.y -= uy * push * share;
        b.x += ux * push * (1 - share);
        b.y += uy * push * (1 - share);
        keep(a);
        keep(b);
        touched = true;
      }
    }
    return touched;
  };
  circles.forEach((c) => {
    c.hx = c.x;
    c.hy = c.y;
  });
  for (let step = 1; step <= SF_MAP_GROW; step += 1) {
    grown = step / SF_MAP_GROW;
    for (let pass = 0; pass < SF_MAP_PASSES; pass += 1) {
      circles.forEach((c) => {
        c.x += (c.hx - c.x) * SF_MAP_PULL;
        c.y += (c.hy - c.y) * SF_MAP_PULL;
        keep(c);
      });
      apart(4);
    }
  }
  for (let pass = 0; pass < 400 && apart(2); pass += 1);
  circles.forEach((c) => {
    c.x = Math.round(c.x * 10) / 10;
    c.y = Math.round(c.y * 10) / 10;
    c.off = Math.round(Math.hypot(c.x - c.hx, c.y - c.hy) * 10) / 10;
    c.line = c.off > c.r;
  });
}

/* a name's width in the map's units at its size, by a rough measure of each letter in the app's
   face, so the names are placed the same with no page, in node and in a saved file */
const sfMapWide = (text, size) => [...String(text)].reduce((sum, ch) => sum + (
  ' .,\'’-'.includes(ch) ? 0.28 : 'ijlI|'.includes(ch) ? 0.27 : 'frt()'.includes(ch) ? 0.37
    : 'mwMW'.includes(ch) ? 0.86 : ch >= 'A' && ch <= 'Z' ? 0.68 : 0.56), 0) * size * 1.04;

/* Each country's name beside its circle (13 October, evening), the largest circle's first. It tries
   right of the circle, left, below and above, then the places between them round it, every 30 degrees
   and then every 15, then each again further out by SF_MAP_OUT, tied to its circle there by a short
   line. A place is clear when it and its tie overlap no circle, no name placed before it, no point a
   line runs to and nothing past the frame, and plain when its own circle is the nearest to it, so it
   reads as that circle's. The name takes the first place beside its circle both clear and plain, or
   else the first clear place further out, or else the first clear place beside it, or else, with none
   clear, the place that runs least into a circle or off the frame and then overlaps least of anything
   else, its `clear` then false. `label` holds where its text stands, which way it runs from there, and
   its tie. */
function sfMapNames(circles, w, h) {
  const high = SF_MAP_NAME * 0.92;
  const placed = [];
  const turns = [0, 180, 90, 270, 30, 150, 210, 330, 60, 120, 240, 300, 15, 165, 195, 345, 45, 135, 225, 315, 75, 105, 255, 285]
    .map((deg) => [Math.round(Math.cos((deg * Math.PI) / 180) * 1000) / 1000, Math.round(Math.sin((deg * Math.PI) / 180) * 1000) / 1000]);
  const near = (box, x, y) => Math.hypot(x - Math.max(box[0], Math.min(x, box[2])), y - Math.max(box[1], Math.min(y, box[3])));
  const cross = (p, q) => Math.max(0, Math.min(p[2], q[2]) - Math.max(p[0], q[0])) * Math.max(0, Math.min(p[3], q[3]) - Math.max(p[1], q[1]));
  const points = circles.filter((c) => c.line);
  for (const c of circles) {
    const wide = sfMapWide(c.name, SF_MAP_NAME);
    // only what lies within the farthest place's reach can touch it
    const span = c.r + SF_MAP_PAD + SF_MAP_OUT[SF_MAP_OUT.length - 1] + wide + high;
    const close = circles.filter((o) => Math.hypot(o.x - c.x, o.y - c.y) < span + o.r);
    const boxes = placed.filter((p) => near(p, c.x, c.y) < span);
    const dots = points.filter((o) => Math.hypot(o.hx - c.x, o.hy - c.y) < span + 3);
    const found = {};
    for (const out of SF_MAP_OUT) {
      for (const [ux, uy] of turns) {
        const reach = c.r + SF_MAP_PAD + out;
        const px = c.x + ux * reach;
        const py = c.y + uy * reach;
        const side = ux > 0.3 ? 1 : ux < -0.3 ? -1 : 0;
        const left = side > 0 ? px : side < 0 ? px - wide : px - wide / 2;
        const top = uy > 0.3 ? py : uy < -0.3 ? py - high : py - high / 2;
        const box = [left, top, left + wide, top + high];
        const tie = out ? [c.x + ux * (c.r + 1), c.y + uy * (c.r + 1), px - ux * 1.5, py - uy * 1.5] : null;
        // how far it runs into a circle or off the frame, and how much it overlaps of anything else
        let onto = 0;
        let rest = 0;
        close.forEach((o) => {
          onto += Math.max(0, o.r + 1 - near(box, o.x, o.y));
          if (tie && o !== c) onto += Math.max(0, o.r + 1 - sfMapReach(tie, o.x, o.y));
        });
        boxes.forEach((p) => {
          rest += cross(box, [p[0] - 1, p[1] - 1, p[2] + 1, p[3] + 1]);
          if (tie) rest += [0, 0.25, 0.5, 0.75, 1].filter((t) => !near(p, tie[0] + (tie[2] - tie[0]) * t, tie[1] + (tie[3] - tie[1]) * t)).length * 20;
        });
        dots.forEach((o) => { rest += Math.max(0, 2.5 - near(box, o.hx, o.hy)); });
        onto += (Math.max(0, -box[0]) + Math.max(0, box[2] - w) + Math.max(0, -box[1]) + Math.max(0, box[3] - h)) * 4;
        const hit = onto + rest;
        const at = { box, side, hit, tie };
        if (hit) {
          const was = found.least;
          if (!was || onto < was.onto || (onto === was.onto && rest < was.rest)) found.least = { ...at, onto, rest };
        } else if (out) {
          found.tied = found.tied || at;
        } else if (close.every((o) => o === c || near(box, o.x, o.y) - o.r >= near(box, c.x, c.y) - c.r)) {
          found.plain = at;
          break;
        } else {
          found.beside = found.beside || at;
        }
      }
      if (found.plain || found.tied) break;
    }
    const { box, side, hit, tie } = found.plain || found.tied || found.beside || found.least;
    placed.push(box);
    const tenth = (v) => Math.round(v * 10) / 10;
    c.label = { x: tenth(side > 0 ? box[0] : side < 0 ? box[2] : (box[0] + box[2]) / 2), y: tenth(box[3] - SF_MAP_NAME * 0.2),
      anchor: side > 0 ? 'start' : side < 0 ? 'end' : 'middle', box: box.map(tenth), clear: !hit, tie: tie ? tie.map(tenth) : null };
  }
}

/* how near a line from one point to another comes to a point */
function sfMapReach([x1, y1, x2, y2], x, y) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const t = dx || dy ? Math.max(0, Math.min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy))) : 0;
  return Math.hypot(x - (x1 + t * dx), y - (y1 + t * dy));
}

/* The map's counts as the filters stand, exactly the Country group's: its choices and counts, every
   other filter applied and its own ticks set aside, and the records they stand on, those that pass
   every other group's filter. With no Country group, nothing. */
function sfMapFrom(world, rows, groups, counts, filters, stage) {
  const g = (groups || []).find((x) => (x.col || {}).kind === 'country');
  if (!g) return sfMapModel(world, [], {}, 0);
  const others = groups.filter((x) => x !== g);
  const total = (rows || []).filter((r) => others.every((x) => sfPasses(r, x.col, (filters || {})[x.key], stage))).length;
  return sfMapModel(world, g.choices, (counts || {})[g.key] || {}, total);
}

// a country's count in words, as the tip, the keys and a screen reader say it
const sfMapSays = (c) => t('sift.map.says', { name: c.name, n: c.n });

/* The line under the map, the figure's denominator: how many of the records its counts stand on name
   no country, and any country the map has no point for, with its count. */
function sfMapLine(m) {
  // with no record to stand on it says so, where it said every one of 0 records had a country (17 October, later)
  const head = !m.total ? t('sift.map.none') : m.blank ? t('sift.map.blank', { blank: m.blank, n: m.total })
    : t('sift.map.every', { n: m.total });
  const off = m.unplaced.length ? ` ${t('sift.map.off', { places: m.unplaced.map((u) => t('sift.map.place', { name: u.name, n: u.n })).join(', ') })}` : '';
  return head + off;
}

/* a number's size in its circle, as large as the circle takes and smaller for more figures */
const sfMapFont = (c) => Math.round(Math.min(20, Math.max(9, c.r * 0.72), (2.6 * c.r) / String(c.n).length) * 10) / 10;

/* The map as SVG markup: the sea within the projection's edge, every country's outline, a thin line
   from each circle moved off its point back to a small dot on that point and a short one to each name
   set further out, under the circles, a circle
   for each country, each a group the keys reach that names its country and count, its number inside
   in bold, and each country's name beside its circle, ringed in the sea's colour so it shows over
   land and borders. No zoom and no pan, its frame world.json's. With `paint`, a file for a paper: the
   light colours written into it on a white ground, which no stylesheet reaches, the text kept as text
   in a stack of faces, each name's ring a copy of it drawn first, since not every program that opens
   the file paints a stroke under its text, its name and each circle's words as titles, and nothing
   the keys reach. */
function sfMapSvg(world, m, paint) {
  const w = world.width;
  const h = world.height;
  const face = 'font-family="Avenir Next, Helvetica, Arial, sans-serif"';
  const sea = `<path class="sf-map-sea" d="${world.sphere}"${paint ? ` fill="${paint.sea}"` : ''}/>`;
  const land = `<g class="sf-map-land"${paint ? ` fill="${paint.land}" stroke="${paint.border}"` : ''} stroke-width="0.5" stroke-linejoin="round">`
    + world.shapes.map((s) => `<path d="${s.d}"/>`).join('') + '</g>';
  const tie = (c) => {
    const k = c.r / c.off;
    const from = (v, home) => Math.round((v + (home - v) * k) * 10) / 10;
    return `<line x1="${from(c.x, c.hx)}" y1="${from(c.y, c.hy)}" x2="${c.hx}" y2="${c.hy}"/><circle cx="${c.hx}" cy="${c.hy}" r="1.6"/>`;
  };
  const held = (t) => `<line x1="${t[0]}" y1="${t[1]}" x2="${t[2]}" y2="${t[3]}"/>`;
  const lines = `<g class="sf-map-lines" aria-hidden="true"${paint ? ` stroke="${paint.line}" fill="${paint.line}"` : ''} stroke-width="0.8">`
    + m.circles.filter((c) => c.line).map(tie).join('') + m.circles.filter((c) => c.label.tie).map((c) => held(c.label.tie)).join('') + '</g>';
  const dots = m.circles.map((c) => {
    const num = `<text x="${c.x}" y="${c.y}" dy="0.35em" font-size="${sfMapFont(c)}"${paint ? ` fill="${paint.num}"` : ''}>${c.n}</text>`;
    const open = paint ? `<g class="sf-map-dot"><title>${esc(sfMapSays(c))}</title>`
      : `<g class="sf-map-dot" data-code="${c.code}" tabindex="0" role="img" aria-label="${escAttr(sfMapSays(c))}">`;
    return `${open}<circle cx="${c.x}" cy="${c.y}" r="${c.r}"${paint ? ` fill="${paint.dot}" stroke="${paint.ring}"` : ''} stroke-width="1"/>${num}</g>`;
  }).join('');
  const names = m.circles.map((c) => {
    const at = `x="${c.label.x}" y="${c.label.y}" text-anchor="${c.label.anchor}"`;
    const ring = paint ? `<text ${at} fill="${paint.sea}" stroke="${paint.sea}" stroke-width="2.6" stroke-linejoin="round">${esc(c.name)}</text>` : '';
    return `${ring}<text ${at}>${esc(c.name)}</text>`;
  }).join('');
  const named = `<g class="sf-map-names" aria-hidden="true" ${face} font-size="${SF_MAP_NAME}" font-weight="500"${paint ? ` fill="${paint.name}"` : ''}>${names}</g>`;
  const size = paint ? ` width="${w}" height="${h}"` : '';
  const said = paint ? `<title>${esc(SF_MAP_WORDS.head)}</title>` : '';
  return `<svg viewBox="0 0 ${w} ${h}"${size} role="group" aria-label="${escAttr(SF_MAP_WORDS.head)}">${said}`
    + `${paint ? `<rect width="${w}" height="${h}" fill="${paint.paper}"/>` : ''}${sea}${land}${lines}`
    + `<g ${face} font-weight="700" text-anchor="middle">${dots}</g>${named}</svg>`;
}

/* a saved file's name, the run's name before the map's, kept to letters a file name can hold */
const sfMapFile = (name, ext) => `${String(name || '').replace(/[\\/:*?"<>|]+/g, '-').trim()} ${SF_MAP_WORDS.file}`.trim() + `.${ext}`;

/* ── the table, drawn ── */

/* a rating's five stars, those up to it filled, each a button */
function sfStars(n) {
  let out = '';
  for (let i = 1; i <= 5; i += 1) {
    out += `<button type="button" class="sf-star${n && i <= n ? ' on' : ''}" data-star="${i}" aria-pressed="${n === i}"`
      + ` aria-label="${escAttr(t('sift.n_stars', { n: i }))}">&#9733;</button>`;
  }
  return out;
}

/* one cell of a row, all of it text the browser's find can reach, the abstract's first hundred words,
   each database that found the record a pill in its colour, the pills alone, and the categories as
   pills. A year, a count of participants, a count of citations or a rating it lacks says so in plain
   words, so none is taken for nought (12 October), and a Number column of his says Unknown as the
   participants do (13 October). The ID comes first, in the faint ink. */
function sfTvCell(r, c) {
  const f = r.fields || {};
  const key = c.key;
  if (key === 'rec_id') return `<td class="mono sf-c-id">${esc(r.rec_id)}</td>`;
  if (key === 'found') return `<td class="sf-c-found">${(r.found || []).map(sfDbPill).join('')}</td>`;
  if (key === 'title') return `<td class="sf-c-title">${esc(r.title || '')}${sfNoticeTags(r)}</td>`;
  if (c.kind === 'notice') {
    const k = sfNoticeKinds(r);
    return `<td class="sf-c-notice">${k === null ? sfBlankHtml('retracted') : k.length ? esc(k.map((x) => SF_NOTICE_WORDS[x]).join(', '))
      : `<span class="sf-blank">${SF_NOTICE_WORDS.none}</span>`}</td>`;
  }
  if (c.kind === 'oa') {
    const said = r.oa && SF_OA_WORDS[r.oa] ? ` title="${escAttr(t('sift.oa.open_as', { how: SF_OA_WORDS[r.oa] }))}"` : '';
    return `<td class="sf-c-oa"${said}>${r.oa ? esc(sfOaWord(r)) : sfBlankHtml('oa')}</td>`;
  }
  if (c.kind === 'country') return `<td class="sf-c-country">${(r.countries || []).length ? esc(r.countries.join(', ')) : sfBlankHtml('country')}</td>`;
  if (c.kind === 'language') return `<td class="sf-c-language">${(r.language || []).length ? esc(r.language.join(', ')) : sfBlankHtml('language')}</td>`;
  if (c.kind === 'study') return `<td class="sf-c-study">${r.study ? esc(r.study) : ''}</td>`;
  if (c.kind === 'keyworks') {
    if (!Array.isArray(r.cites)) return `<td class="sf-c-keyworks">${(SF.keyWorks || []).length ? sfBlankHtml('keyworks') : ''}</td>`;
    return `<td class="sf-c-keyworks">${r.cites.length ? r.cites.map((k) => `<span class="sf-cat">${esc((sfKeyWork(k) || {}).label || k)}</span>`).join('')
      : `<span class="sf-blank">${SF_NOTICE_WORDS.none}</span>`}</td>`;
  }
  // where the record matched each block of the plan (14 October)
  if (c.kind === 'matched') return `<td class="sf-c-long sf-c-matched">${sfMatchedLines(r, true)}</td>`;
  if (key === 'abstract') {
    const w = sfFirstWords(r.abstract, SF_ABSTRACT_WORDS);
    return `<td class="sf-c-abstract">${esc(w.text)}${w.cut ? '&#8230;' : ''}</td>`;
  }
  if (key === 'year') return `<td class="sf-c-num">${r.year ? esc(r.year) : sfBlankHtml('year')}</td>`;
  if (key === 'cited') {
    return `<td class="sf-c-num"${sfCitedTitle(r)}>${typeof r.cited === 'number' ? r.cited : sfBlankHtml('cited')}</td>`;
  }
  if (key === 'participants') {
    const given = String(f.participants || '').trim();
    const inner = f.confirmed ? (given ? esc(given) : sfBlankHtml('participants'))
      : f.guess ? `<button type="button" class="sf-guess" data-confirm="${f.guess}" title="${escAttr(t('sift.confirm'))}">${f.guess}?</button>`
        : sfBlankHtml('participants');
    return `<td class="sf-c-num sf-ed" data-edit="participants">${inner}</td>`;
  }
  if (key === 'doi') {
    return `<td class="sf-c-doi">${r.doi ? `<a href="${escAttr(r.link)}" target="_blank" rel="noopener noreferrer">${esc(r.doi)}</a>` : ''}</td>`;
  }
  // a record's PDF a red pill, no link, and a record without one blank
  if (key === 'pdf') return `<td class="sf-c-pdf">${r.pdf ? '<span class="sf-pill sf-pdfpill">PDF</span>' : ''}</td>`;
  if (key === 'decision') {
    const st = (r.stages || {})[SF.stage] || {};
    return `<td class="sf-c-dec">${sfPillHtml(st.decision, st.reason)}</td>`;
  }
  // at full text, where the record stood at title and abstract
  if (key === 'tadec') return `<td class="sf-c-dec">${sfPillHtml(((r.stages || {}).ta || {}).decision, '', 'ta')}</td>`;
  if (key === 'rating') {
    return `<td class="sf-c-rating"><span class="sf-stars"${f.rating ? '' : ` title="${SF_BLANK_WORDS.rating}"`}>${sfStars(f.rating)}</span></td>`;
  }
  if (key === 'notes') return `<td class="sf-c-long sf-ed" data-edit="notes">${esc(f.notes || '')}</td>`;
  if (key === 'digest' || key === 'critique') return `<td class="sf-c-long">${esc(f[key] || '')}</td>`;
  if (key === 'formdone') return `<td class="sf-c-done">${sfFormDone(r) ? SF_DONE_WORDS.done : `<span class="sf-blank">${SF_DONE_WORDS.todo}</span>`}</td>`;
  if (c.own) {
    // a value of his in the form's words, Not reported faint, Sift's while it starts from one, and a cell
    // opened for typing but for several choices and passages, which the record holds (13 October, later)
    const v = c.def ? sfFieldValue(r, c.def).value : String((f.own || {})[key] || '');
    const ed = ['multi', 'passages'].includes(c.kind) ? '' : ` sf-ed" data-edit="${escAttr(key)}`;
    if (v === SF_NR) return `<td class="sf-c-own${ed}"><span class="sf-blank">${SF_NR_WORD}</span></td>`;
    if (c.kind === 'number') {
      const n = sfNumber(v);
      return `<td class="sf-c-num sf-c-own${ed}">${n === null ? sfBlankHtml('participants') : n}</td>`;
    }
    if (c.kind === 'multi') return `<td class="sf-c-own">${sfMultiParts(v).map((x) => `<span class="sf-cat">${esc(x)}</span>`).join('')}</td>`;
    if (c.kind === 'long') return `<td class="sf-c-long sf-c-own${ed}">${esc(v)}</td>`;
    return `<td class="sf-c-own${ed}">${esc(c.def ? sfFormWords(c.def, v) : v)}</td>`;
  }
  return `<td>${c.extra ? sfReviewCell(c.key.slice(SF_EXTRA.length), sfValue(r, c, SF.stage)) : esc(sfValue(r, c, SF.stage))}</td>`;
}

function sfTvRowHtml(r, cols) {
  return `<tr data-rec="${escAttr(r.rec_id)}">${cols.map((c) => sfTvCell(r, c)).join('')}</tr>`;
}

/* a heading's class in Sift's table, as the family's table draws the headings (tbTvHeadHtml): a column
   of Sift's own its key's, one of his Own, and the rest the family's */
const sfHeadKind = (c) => (SF_COLS[c.key] ? c.key.replace('_', '-') : c.own ? 'own' : tbHeadKind(c));

function sfTvHeadDraw(cols) {
  $('sf-thead').innerHTML = tbTvHeadHtml(cols, SF.sort, sfHeadKind);
}

/* ── the filters, drawn ── */

/* where a slider's ends stand, the ends held kept to the round's lowest and highest, an open end at
   its own limit */
function sfRangeEnds(g, h) {
  const keep = (v, at) => (v === null ? at : Math.max(g.low, Math.min(g.high, v)));
  return [keep(h.from, g.low), keep(h.to, g.high)];
}

/* a slider's chart, a bar for each number or run of numbers as high as the rows standing there, one
   with any row never too low to see, those whose whole run stands between the two ends in the accent
   and the rest muted, and its run in words with its count of records in `data-tip`, which the app's
   own tip shows at once over the chart while the pointer is anywhere in the bar's column (see
   sfBarTip), "2020 to 2024: 12 records", a rating's run in stars (12 October) */
function sfBarsHtml(bars, lo, hi, key) {
  const most = Math.max(1, ...bars.map((b) => b.n));
  // a bar of sfBarSpans says its run as it was made, and one made elsewhere from its label, 2015–2019 as 2015 to 2019
  const ran = (b) => /^(\d+)–(\d+)$/.exec(String(b.label || ''));
  const run = (b) => (key === 'rating' ? t('sift.n_stars', { n: b.from })
    : String(b.said || (ran(b) ? t('sift.bar.to', { from: ran(b)[1], to: ran(b)[2] }) : '') || b.label
      || (b.from === b.to ? String(b.from) : t('sift.bar.to', { from: b.from, to: b.to }))));
  return `<div class="sf-bars" aria-hidden="true">${bars.map((b) => `<span class="sf-bar${b.from >= lo && b.to <= hi ? ' in' : ''}"`
    + ` data-from="${b.from}" data-to="${b.to}" style="height: ${b.n ? Math.max(8, Math.round((b.n / most) * 100)) : 0}%"`
    + ` data-tip="${esc(t('sift.bar.tip', { run: run(b), n: b.n }))}"></span>`).join('')}</div>`;
}

/* The tip over a slider's chart (12 October): the run and the count of the bar whose column the
   pointer is in, from the chart's foot to its top and across the gaps between bars, shown at once
   above the chart, kept inside the sidebar, never over the handles under it. Screen readers and the
   keys have the handles' own words, so the chart and its tip stay hidden from them. */
function sfBarTip(e) {
  const chart = e.target && e.target.closest ? e.target.closest('.sf-bars') : null;
  const bars = chart ? chart.querySelectorAll('.sf-bar') : [];
  if (!bars.length) { sfBarTipHide(); return; }
  const box = chart.getBoundingClientRect();
  const i = Math.max(0, Math.min(bars.length - 1, Math.floor(((e.clientX - box.left) / Math.max(1, box.width)) * bars.length)));
  const bar = bars[i];
  const tip = $('sf-bar-tip');
  if (tip.textContent !== bar.dataset.tip) tip.textContent = bar.dataset.tip || '';
  tip.hidden = false;
  const at = bar.getBoundingClientRect();
  const side = $('sf-facets').getBoundingClientRect();
  const w = tip.offsetWidth;
  const left = Math.max(side.left + 4, Math.min(side.right - w - 4, at.left + at.width / 2 - w / 2));
  tip.style.left = `${Math.round(Math.max(4, left))}px`;
  tip.style.top = `${Math.round(box.top - tip.offsetHeight - 6)}px`;
}

function sfBarTipHide() {
  const tip = $('sf-bar-tip');
  if (tip && !tip.hidden) tip.hidden = true;
}

/* A slider's group: under its column's name, a small chart of where the rows stand, two handles on
   one track from the lowest whole number the round's rows hold to the highest, the rating's from
   nought stars to five, the lower and the upper, the two numbers in boxes to type, how many rows
   stand between them at the right, then for the year and the participants None, the rows with no
   number, a tick of its own with its count. At its full range it filters nothing. The year's and the
   participants' handles stand on a track laid out by the chart's bars, `sfTrack`, carried in the
   group's data-runs, their place a bar's edge or, for a number typed, its place inside its bar, and
   the number each stands at said to a screen reader. The boxes take any whole number. */
function sfRangeHtml(g, counts, i, bars) {
  const h = sfRangeHeld(SF.filters[g.key]);
  const on = h.from !== null || h.to !== null || (h.none && g.choices.length > 0);
  const runs = g.low !== null ? sfTrack(g.key, bars) : null;
  let body = '';
  if (g.low !== null) {
    const [lo, hi] = sfRangeEnds(g, h);
    const span = g.high - g.low;
    const four = (x) => Math.round(x * 10000) / 10000;
    const at = (end, v) => (runs ? String(four(sfTrackAt(runs, v, end) / runs.length))
      : span ? String(four((v - g.low) / span)) : '0');
    const n = counts[SF_RANGE] || 0;
    const handle = (end, v) => (runs
      ? `<input type="range" class="sf-handle sf-${end}" data-end="${end}" min="0" max="${runs.length}" step="any"`
        + ` value="${four(sfTrackAt(runs, v, end))}" aria-valuetext="${v}"`
      : `<input type="range" class="sf-handle sf-${end}" data-end="${end}" min="${g.low}" max="${g.high}" step="1" value="${v}"`)
      + ` aria-label="${escAttr(`${g.label}, ${end}`)}">`;
    const box = (end, v) => `<input type="number" class="sf-rnum" data-end="${end}" min="${g.low}" max="${g.high}" step="1"`
      + ` value="${v}" inputmode="numeric" aria-label="${escAttr(`${g.label}, ${end}`)}">`;
    body = (bars && bars.length ? sfBarsHtml(bars, lo, hi, g.key) : '')
      + (span ? `<div class="sf-slider${!runs && lo === g.high ? ' low-top' : ''}" style="--lo: ${at('from', lo)}; --hi: ${at('to', hi)}">`
      + `${handle('from', lo)}${handle('to', hi)}</div>` : '')
      + `<div class="sf-rvals${n ? '' : ' zero'}">${box('from', lo)}<span class="sf-rto">${esc(t('sift.range.to'))}</span>${box('to', hi)}`
      + `${g.key === 'rating' ? `<span class="sf-runit">${esc(t('sift.range.stars'))}</span>` : ''}<span class="sf-cn">${n}</span></div>`;
  }
  return `<div class="sf-group sf-rgroup" role="group" aria-labelledby="sf-g-${i}" data-g="${escAttr(g.key)}" data-range="true"`
    + `${g.low !== null ? ` data-low="${g.low}" data-high="${g.high}"` : ''}`
    + `${runs ? ` data-runs="${runs.map(([a, b]) => `${a}-${b}`).join(' ')}"` : ''}>${tbGroupHead(g, i, on)}${body}`
    + `${g.choices.map((c) => tbChoiceHtml(c, counts[TB_BLANK] || 0, h.none)).join('')}</div>`;
}

/* the sidebar's rows, groups and counts as the filters stand, which the map's counts are too */
function sfFacetsData() {
  const rows = sfRoundRows();
  const groups = sfGroups(rows, SF.records, sfAllCols(), SF.stage, sfCodes(), SF.filters);
  return { rows, groups, counts: tbFacetCounts(rows, groups, SF.filters, sfRead(SF.stage)) };
}

/* the group he ticks in held in the order it was last drawn, the other groups taking their counts'
   order as the counts change (13 October, later) */
function sfFacetsHoldAt(key) {
  SF.facetsHold = { key, order: (SF.facetsOrder || {})[key] || [] };
}

/* The sidebar as the filters stand: a group for each column a pick can filter, each count live, each
   group's choices by their counts (see `sfFacetOrder`), the map redrawn with them while it is open,
   built again only when it changed, and the control he was on given back its focus and, in a box he
   types in, its caret. Clear all stands beside the toggle while anything is set (see sfFacetsMark).
   Nothing is drawn while it is shut. */
function sfFacetsDraw() {
  sfFacetsMark();
  if (!$('sf-map').hidden) sfMapDraw();
  if ($('sf-facets').hidden) return;
  const { rows, groups, counts } = sfFacetsData();
  const bars = sfRangeBars(rows, groups, SF.filters, SF.stage);
  // each group's choices by their counts, the group he last ticked in held as it was drawn (13 October, later)
  const hold = SF.facetsHold;
  SF.facetsOrder = {};
  groups.forEach((g) => {
    if (g.range) return;
    g.choices = sfFacetOrder(g, counts[g.key], hold && hold.key === g.key ? hold.order : null);
    SF.facetsOrder[g.key] = g.choices.map((c) => c.value);
  });
  const ticked = tbTicks(SF.filters, SF_BENCH).length > 0;
  const bench = SF.form && SF.formBench.size ? `<div class="sf-group" role="group" aria-labelledby="sf-g-bench" data-g="${SF_BENCH}">`
    + `${tbGroupHead({ label: t('sift.bench_papers'), about: '' }, 'bench', ticked)}`
    + `${tbChoiceHtml({ value: 'yes', label: t('sift.bench_show') }, SF.formBench.size, ticked)}</div>` : '';
  const html = bench + groups.map((g, i) => (g.range ? sfRangeHtml(g, counts[g.key] || {}, i, bars[g.key])
    : tbGroupHtml(g, counts[g.key] || {}, i, SF))).join('');
  if (html === SF.facetsHtml) return;
  const box = $('sf-groups');
  const was = document.activeElement;
  const group = was && box.contains(was) ? was.closest('[data-g]') : null;
  const id = (el) => [el.dataset.v || '', el.dataset.act || '', el.dataset.end || '', el.type || ''].join('\n');
  const keep = group ? [group.dataset.g, id(was)] : null;
  const caret = keep && was.type === 'search' ? [was.selectionStart, was.selectionEnd] : null;
  box.innerHTML = html;
  SF.facetsHtml = html;
  // a chart's tip names a bar drawn before, so it goes until the pointer moves again
  sfBarTipHide();
  if (!keep) return;
  const holder = [...box.querySelectorAll('[data-g]')].find((el) => el.dataset.g === keep[0]);
  const back = holder && [...holder.querySelectorAll('input, button')].find((el) => id(el) === keep[1]);
  if (!back) return;
  back.focus();
  if (caret) back.setSelectionRange(caret[0], caret[1]);
}

/* a choice ticked or unticked, its group widening with each tick, None under a slider among them,
   and the rows laid out again */
function sfTick(key, value, on) {
  if (sfRangeKey(key)) {
    sfRangeSet(key, Object.assign(sfRangeHeld(SF.filters[key]), { none: on }));
    return;
  }
  const now = new Set(SF.filters[key] || []);
  if (on) now.add(value);
  else now.delete(value);
  if (now.size) SF.filters[key] = [...now];
  else delete SF.filters[key];
  sfRefilter();
}

/* A slider's filter set, an end at the round's own limit held open so the slider at its full range
   filters nothing, and the rows laid out again. */
function sfRangeSet(key, h) {
  const g = sfGroups(sfRoundRows(), SF.records, sfAllCols().filter((c) => c.key === key), SF.stage, [], {})[0];
  const held = { from: h.from, to: h.to, none: !!h.none && !!g && g.choices.length > 0 };
  if (g && g.low !== null) {
    if (held.from !== null && held.from <= g.low) held.from = null;
    if (held.to !== null && held.to >= g.high) held.to = null;
  }
  if (held.from !== null || held.to !== null || held.none) SF.filters[key] = held;
  else delete SF.filters[key];
  sfRefilter();
}

/* A slider's two ends as its handles or boxes stand, the lower never past the upper. A handle moved
   gives its own end and the other stands as its box says. On a track by bars the handle goes to the
   edge of the bar it is nearest, a whole bar at a time, and dragged past the other it stops at the
   other's bar. While a handle moves, its numbers, its place, the track between the handles and the
   count follow it at once, and when it is let go, or a box is left, the rows are laid out again. */
function sfRangeMove(el, done) {
  const group = el.closest('[data-range]');
  if (!group || group.dataset.low === undefined) return;
  const key = group.dataset.g;
  const low = Number(group.dataset.low);
  const high = Number(group.dataset.high);
  const runs = sfTrackRead(group.dataset.runs);
  const moved = el.type === 'range' ? el.dataset.end : '';
  const read = (end) => {
    if (end === moved) {
      const pos = Number(el.value);
      if (runs) return sfTrackEdge(runs, sfTrackSnap(runs, pos, end), end);
      return Number.isFinite(pos) ? Math.max(low, Math.min(high, Math.round(pos))) : (end === 'from' ? low : high);
    }
    const box = group.querySelector(`.sf-rnum[data-end="${end}"]`);
    const v = sfNumber(box ? box.value : '');
    return v === null ? (end === 'from' ? low : high) : Math.max(low, Math.min(high, v));
  };
  let from = read('from');
  let to = read('to');
  if (from > to) {
    if (runs && moved === 'from') from = runs[sfTrackBar(runs, to)][0];
    else if (runs && moved === 'to') to = runs[sfTrackBar(runs, from)][1];
    else if (el.dataset.end === 'from') from = to;
    else to = from;
  }
  if (!done) {
    group.querySelectorAll('.sf-rnum[data-end="from"]').forEach((x) => { x.value = from; });
    group.querySelectorAll('.sf-rnum[data-end="to"]').forEach((x) => { x.value = to; });
    // each handle at its place, on a track by bars the moved one let go at its bar's edge
    const place = (end, v) => (runs ? Math.round(sfTrackAt(runs, v, end) * 10000) / 10000 : v);
    group.querySelectorAll('.sf-handle[data-end]').forEach((x) => {
      const v = x.dataset.end === 'from' ? from : to;
      x.value = place(x.dataset.end, v);
      if (runs) x.setAttribute('aria-valuetext', String(v));
    });
    const slider = group.querySelector('.sf-slider');
    const span = high - low;
    if (slider && runs) {
      slider.style.setProperty('--lo', String(sfTrackAt(runs, from, 'from') / runs.length));
      slider.style.setProperty('--hi', String(sfTrackAt(runs, to, 'to') / runs.length));
    } else if (slider && span) {
      slider.style.setProperty('--lo', String((from - low) / span));
      slider.style.setProperty('--hi', String((to - low) / span));
    }
    const held = Object.assign(sfRangeHeld(SF.filters[key]), { from, to });
    const rows = sfRoundRows();
    const filters = Object.assign({}, SF.filters, { [key]: held });
    const groups = sfGroups(rows, SF.records, sfAllCols(), SF.stage, [], filters);
    const n = (tbFacetCounts(rows, groups, filters, sfRead(SF.stage))[key] || {})[SF_RANGE] || 0;
    const count = group.querySelector('.sf-rvals .sf-cn');
    if (count) count.textContent = String(n);
    group.querySelectorAll('.sf-bar').forEach((b) => b.classList.toggle('in', Number(b.dataset.from) >= from && Number(b.dataset.to) <= to));
    return;
  }
  sfRangeSet(key, Object.assign(sfRangeHeld(SF.filters[key]), { from, to }));
}

/* A key on a handle of a track by bars: the arrows and Page Up or Down a bar on or back, Home and End
   to the first bar's edge or the last, the rows laid out again at once. Answers whether it took the
   key, and a handle on any other slider keeps the browser's own keys, a whole number a press. */
function sfHandleKey(e) {
  const el = e.target;
  if (!el || !el.classList || !el.classList.contains('sf-handle') || !el.dataset.end || MOD(e) || e.altKey) return false;
  const group = el.closest('[data-range]');
  const runs = group ? sfTrackRead(group.dataset.runs) : null;
  if (!runs) return false;
  const end = el.dataset.end;
  const dir = { ArrowRight: 1, ArrowUp: 1, PageUp: 1, ArrowLeft: -1, ArrowDown: -1, PageDown: -1 }[e.key];
  let k;
  if (dir) k = sfTrackStep(runs, el.value, end, dir);
  else if (e.key === 'Home') k = sfTrackSnap(runs, 0, end);
  else if (e.key === 'End') k = sfTrackSnap(runs, runs.length, end);
  else return false;
  e.preventDefault();
  el.value = k;
  sfRangeMove(el, true);
  return true;
}

/* what is typed in a long group's find box, its choices narrowed to those it names as he types */
function sfFind(el, typed) {
  const group = el.closest('[data-g]');
  if (!group) return;
  SF.facetsFind[group.dataset.g] = typed;
  if (el.value !== typed) el.value = typed;
  sfFacetsDraw();
  sfFiltersKeep(false);
}

/* a group cleared, its find box emptied, its order held as a tick holds it, or with no key every
   filter and every find box, every group then taking its count's order, and what sift.json keeps
   cleared with them */
function sfClear(key) {
  if (key) {
    sfFacetsHoldAt(key);
    delete SF.filters[key];
    delete SF.facetsFind[key];
  } else {
    SF.facetsHold = null;
    SF.filters = {};
    SF.facetsFind = {};
  }
  sfRefilter();
}

/* The table as it stands: the headings when the columns, the stage or the sort changed, the body
   built again when the rows or the columns changed, else each row drawn again alone when its record
   did, never the one he is typing in, and the chosen row marked. The ID comes first. */
function sfTvDraw() {
  const cols = sfViewCols([SF_ID, ...sfColumns(SF.table).filter((c) => c.shown)]);
  const keys = cols.map((c) => c.key).join('\n');
  const head = `${keys}\n${SF.stage}\n${SF.form}\n${JSON.stringify(SF.sort)}\n${(SF.table && JSON.stringify(SF.table.own)) || ''}`;
  if (head !== SF.tvHead) {
    sfTvHeadDraw(cols);
    SF.tvHead = head;
  }
  const shape = `${keys}\n${SF.stage}\n${SF.form}\n${SF.ids.join('\n')}`;
  const body = $('sf-tbody');
  if (shape !== SF.tvShape) {
    const html = [];
    SF.tvRows = new Map();
    for (const id of SF.ids) {
      const r = SF.byId.get(id);
      if (!r) continue;
      const h = sfTvRowHtml(r, cols);
      html.push(h);
      SF.tvRows.set(id, { html: h, el: null });
    }
    body.innerHTML = html.join('');
    for (const tr of body.children) {
      const held = SF.tvRows.get(tr.dataset.rec);
      if (held) held.el = tr;
    }
    SF.tvShape = shape;
    SF.tvSel = null;
    SF.editing = null;
  } else {
    for (const id of SF.ids) {
      const held = SF.tvRows.get(id);
      const r = SF.byId.get(id);
      if (!held || !held.el || !r || (SF.editing && SF.editing.rec === id)) continue;
      const h = sfTvRowHtml(r, cols);
      if (h === held.html) continue;
      const shell = document.createElement('tbody');
      shell.innerHTML = h;
      const tr = shell.firstElementChild;
      held.el.replaceWith(tr);
      held.el = tr;
      held.html = h;
      if (SF.tvSel === id) SF.tvSel = null;
    }
  }
  sfTvMark();
  sfFacetsDraw();
  sfReasonsDraw();
}

/* the chosen row marked, and brought into view under the headings when a key moved it */
function sfTvMark() {
  const id = SF.ids[SF.at] || null;
  if (SF.tvSel !== id) {
    const old = SF.tvSel && SF.tvRows.get(SF.tvSel);
    if (old && old.el) { old.el.classList.remove('on'); old.el.removeAttribute('aria-selected'); }
    const now = id && SF.tvRows.get(id);
    if (now && now.el) { now.el.classList.add('on'); now.el.setAttribute('aria-selected', 'true'); }
    SF.tvSel = id;
  }
  if (!SF.tvReveal || $('sf-tv').hidden) return;
  SF.tvReveal = false;
  const held = id && SF.tvRows.get(id);
  if (!held || !held.el) return;
  const box = $('sf-tv-box');
  const top = held.el.offsetTop;
  const head = $('sf-thead').offsetHeight;
  const bottom = top + held.el.offsetHeight;
  if (top - head < box.scrollTop) box.scrollTop = Math.max(0, top - head);
  else if (bottom > box.scrollTop + box.clientHeight) box.scrollTop = bottom - box.clientHeight;
}

/* The records laid out again after a sort or a filter, the table at its top on the first of them,
   or with `keep`, after a change of columns, the chosen one kept where it still shows. */
function sfRefilter(keep) {
  const r = keep ? sfRecord() : null;
  sfApply(r ? r.rec_id : null);
  SF.picking = false;
  if (!keep) $('sf-tv-box').scrollTop = 0;
  sfDraw();
  sfFiltersKeep();
}

/* A press on a heading sorts by it, the way its kind sorts first, again the other way, and a third
   time not at all. With Shift it adds the column as the next key, or turns or drops one there. */
function sfSortBy(key, add) {
  const col = sfAllCols().find((c) => c.key === key);
  if (!col) return;
  SF.sort = tbSortNext(SF.sort, col, add);
  sfRefilter();
}

/* A click on a heading sorts by it, Shift adding the next key, but the click that ends a drag of
   the heading sorts nothing, since that drag moved its column */
function sfThClick(e) {
  if (SF.thDragged) { SF.thDragged = false; return; }
  const btn = e.target.closest('.sf-th');
  if (btn) sfSortBy(btn.dataset.sort, e.shiftKey);
}

// how far the pointer travels before a press on a heading becomes a drag, as on the boards
const SF_TH_TRAVEL = 4;
// how near the box's edge the pointer comes before the box scrolls sideways under a drag, and how far a move scrolls it
const SF_TH_EDGE = 40;
const SF_TH_STEP = 16;

/* whether a heading drags: the ID stands first, At title and abstract after Decision and Form, `formdone`,
   after the ID at Extract and appraise, so none moves and none is a place to drop */
const sfThMoves = (key) => key !== SF_ID.key && key !== SF_TADEC.key && key !== 'formdone';

/* The places a heading dragged can go, each the left edge of a heading that moves, the column
   standing before that heading, then the right edge of the last heading, after the last column
   shown. Each place is `{x, before, th, side}`. */
function sfThGaps() {
  const ths = [...$('sf-thead').querySelectorAll('th')];
  const gaps = [];
  for (const th of ths) {
    const btn = th.querySelector('.sf-th');
    if (btn && sfThMoves(btn.dataset.sort)) gaps.push({ x: th.getBoundingClientRect().left, before: btn.dataset.sort, th, side: 'before' });
  }
  const last = ths[ths.length - 1];
  if (last && gaps.length) gaps.push({ x: last.getBoundingClientRect().right, before: null, th: last, side: 'after' });
  return gaps;
}

/* the marker in the place the column goes, a bar at that heading's edge, and none with no place */
function sfThMark(gap) {
  for (const th of $('sf-thead').querySelectorAll('th')) th.classList.remove('sf-drop-before', 'sf-drop-after');
  if (gap) gap.th.classList.add(`sf-drop-${gap.side}`);
}

/* A press on a heading that moves: once the pointer travels `SF_TH_TRAVEL` pixels it is a drag, the
   heading marked as it goes, the marker in the place nearest the pointer, the box scrolling sideways
   when the pointer nears its edge. Let go, the column moves to the marker's place and the order is
   saved as Set columns saves it, so the card shows it next time. A press that never travels is a
   click, and sorts. The window hears the pointer, so the drag goes on outside the headings. */
function sfThPress(e) {
  const btn = e.target.closest && e.target.closest('.sf-th');
  if (!btn || e.button !== 0 || !sfThMoves(btn.dataset.sort)) return;
  SF.thDragged = false;
  const key = btn.dataset.sort;
  const pointer = e.pointerId;
  const x0 = e.clientX;
  const y0 = e.clientY;
  let gap = null;
  let dragging = false;
  const move = (ev) => {
    if (ev.pointerId !== pointer) return;
    if (!dragging) {
      if (Math.hypot(ev.clientX - x0, ev.clientY - y0) < SF_TH_TRAVEL) return;
      dragging = true;
      const th = btn.closest('th');
      if (th) th.classList.add('dragging');
      $('sf-tbl').classList.add('sf-th-dragging');
    }
    const box = $('sf-tv-box');
    const edge = box.getBoundingClientRect();
    if (ev.clientX < edge.left + SF_TH_EDGE) box.scrollLeft -= SF_TH_STEP;
    else if (ev.clientX > edge.right - SF_TH_EDGE) box.scrollLeft += SF_TH_STEP;
    const gaps = sfThGaps();
    gap = gaps.reduce((best, g) => (!best || Math.abs(g.x - ev.clientX) < Math.abs(best.x - ev.clientX) ? g : best), null);
    sfThMark(gap);
  };
  const end = (ev) => {
    if (ev.pointerId !== pointer) return;
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', end);
    window.removeEventListener('pointercancel', end);
    if (!dragging) return;
    sfThMark(null);
    for (const th of $('sf-thead').querySelectorAll('th.dragging')) th.classList.remove('dragging');
    $('sf-tbl').classList.remove('sf-th-dragging');
    // the click that follows the let go sorts nothing, and the mark goes if no click comes
    SF.thDragged = true;
    setTimeout(() => { SF.thDragged = false; }, 0);
    if (ev.type !== 'pointerup' || !gap) return;
    const cols = sfColumns(SF.table).map((c) => ({ key: c.key, shown: c.shown }));
    const moved = sfColMoved(cols, key, gap.before);
    if (moved.map((c) => c.key).join('\n') !== cols.map((c) => c.key).join('\n')) sfColsSave(moved);
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', end);
  window.addEventListener('pointercancel', end);
}

/* a cell opened for typing: the notes, the participants or a column of his, a choice as its list,
   kept when it is left, Esc and Enter leaving it as they leave every field */
function sfTvEdit(td, rec, field) {
  const r = SF.byId.get(rec);
  if (!r || SF.editing) return;
  const f = r.fields || {};
  const own = ((SF.table && SF.table.own) || []).find((c) => c.key === field);
  // a field that starts from a Sift column opens on Sift's value, which leaving it unchanged keeps his own empty
  const eff = own ? sfFieldValue(r, own) : { value: '', sift: false };
  let el;
  if (own && (own.type === 'choice' || own.type === 'yesno')) {
    el = document.createElement('select');
    const now = (f.own || {})[field] || '';
    const list = own.type === 'yesno' ? ['yes', 'no'] : own.options;
    const opts = ['', ...list, ...(own.not_reported || now === SF_NR ? [SF_NR] : []),
      ...(now && now !== SF_NR && !list.includes(now) ? [now] : [])];
    el.innerHTML = opts.map((o) => `<option value="${escAttr(o)}">${esc(o === SF_NR ? SF_NR_WORD : own.type === 'yesno' ? SF_YES_NO[o] || o : o)}</option>`).join('');
  } else if (field === 'notes' || (own && own.type === 'long')) {
    el = document.createElement('textarea');
    el.rows = 3;
  } else {
    el = document.createElement('input');
    el.type = 'text';
    el.autocomplete = 'off';
    // a count, the participants or a Number column of his, with the number keys on a phone
    if (field === 'participants' || (own && own.type === 'number')) el.inputMode = 'numeric';
  }
  el.className = 'sf-field sf-cell-ed';
  el.value = eff.sift ? eff.value : sfFieldNow(f, field);
  el.setAttribute('aria-label', own ? own.name : SF_COLS[field] ? SF_COLS[field].label : field);
  if (field === 'participants' && !f.confirmed && f.guess) el.placeholder = `${f.guess}?`;
  td.textContent = '';
  td.appendChild(el);
  SF.editing = { rec, field };
  el.focus();
  const done = () => {
    el.removeEventListener('blur', done);
    SF.editing = null;
    const held = SF.tvRows.get(rec);
    if (held) held.html = '';
    if (!(eff.sift && el.value.trim() === eff.value.trim())) sfFieldSave(rec, field, el.value);
    sfDraw();
  };
  el.addEventListener('blur', done);
  if (el.tagName === 'SELECT') {
    el.addEventListener('change', () => el.blur());
    try { el.showPicker(); } catch { /* a browser that opens a list only on its own press */ }
  }
}

function sfTvBoot() {
  const body = $('sf-tbody');
  // A click on a row opens its record, as Enter does (12 October), while a star rates the row, a guess
  // is confirmed, a link opens, a cell of his opens for typing, a click that ends his typing in a cell
  // ends it alone, and words selected by a drag across the row stay selected for copying
  body.addEventListener('click', (e) => {
    const tr = e.target.closest('tr[data-rec]');
    if (!tr || e.target.closest('.sf-cell-ed')) return;
    const rec = tr.dataset.rec;
    const at = SF.ids.indexOf(rec);
    if (at >= 0 && at !== SF.at) {
      SF.at = at;
      SF.picking = false;
      sfDraw();
    }
    const r = SF.byId.get(rec);
    const star = e.target.closest('.sf-star');
    if (star && r) { const n = Number(star.dataset.star); sfFieldSave(rec, 'rating', (r.fields || {}).rating === n ? '' : String(n)); return; }
    const guess = e.target.closest('.sf-guess');
    if (guess) { sfFieldSave(rec, 'participants', guess.dataset.confirm); return; }
    if (e.target.closest('a, button, input, select, textarea, label')) return;
    if (SF.tvTyping) return;
    const td = e.target.closest('td.sf-ed');
    if (td && td.isConnected && !SF.editing) { sfTvEdit(td, rec, td.dataset.edit); return; }
    const sel = window.getSelection ? window.getSelection() : null;
    if (sel && String(sel).trim() && tr.contains(sel.anchorNode)) return;
    sfOpenRecord(true);
  });
  // the second press of a quick double-click selects no word of the row, while a drag across the text
  // still selects it for copying, and a press while a cell is open for typing is marked, so its click
  // ends the typing and opens nothing
  body.addEventListener('mousedown', (e) => {
    SF.tvTyping = !!SF.editing;
    if (e.detail > 1 && !e.target.closest('.sf-cell-ed, input, textarea, td.sf-ed') && e.target.closest('tr[data-rec]')) e.preventDefault();
  });
  // the whole abstract on hover, set when the pointer first reaches the cell
  body.addEventListener('mouseover', (e) => {
    const td = e.target.closest('td.sf-c-abstract');
    if (!td || td.title) return;
    const r = SF.byId.get(td.parentElement.dataset.rec);
    if (r && r.abstract) td.title = r.abstract;
  });
  // a heading sorts, Shift adding the next key, and dragged left or right it moves its column
  $('sf-thead').addEventListener('click', sfThClick);
  $('sf-thead').addEventListener('pointerdown', sfThPress);
  // the filters: a tick in a group, a slider's handles and boxes, a long group's find box, its Clear
  // and the way to show the rest of a long one, and over the table the toggle with Clear all beside
  // it and the sidebar's edge
  const groups = $('sf-groups');
  groups.addEventListener('change', (e) => {
    if (e.target.dataset && e.target.dataset.end) { sfRangeMove(e.target, true); return; }
    const box = e.target.closest('input[type="checkbox"][data-v]');
    const group = box && box.closest('[data-g]');
    if (!group) return;
    // the group he ticks in keeps its order while he is in it, so no choice moves under the pointer
    sfFacetsHoldAt(group.dataset.g);
    sfTick(group.dataset.g, box.dataset.v, box.checked);
  });
  groups.addEventListener('input', (e) => {
    const el = e.target;
    if (el.type === 'range' && el.dataset.end) sfRangeMove(el, false);
    else if (el.dataset && el.dataset.act === 'find') sfFind(el, el.value);
  });
  groups.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-act]');
    const group = btn && btn.closest('[data-g]');
    if (!group) return;
    const key = group.dataset.g;
    if (btn.dataset.act === 'clear') { sfClear(key); return; }
    if (btn.dataset.act === 'map') { sfMapOpen(btn); return; }
    if (SF.facetsMore.has(key)) SF.facetsMore.delete(key);
    else SF.facetsMore.add(key);
    sfFacetsDraw();
  });
  $('sf-facets-clear').onclick = () => sfClear(null);
  $('sf-facets-toggle').onclick = () => sfFacetsOpen($('sf-facets').hidden);
  sfEdgeBoot('facets');
  sfEdgeBoot('flow');
  // the slider charts' bars said on hover at once, whichever bar's column the pointer is in
  groups.addEventListener('pointermove', sfBarTip);
  groups.addEventListener('pointerleave', () => sfBarTipHide());
  $('sf-facets').addEventListener('scroll', () => sfBarTipHide(), { passive: true });
}

/* ── Country on a map (13 October, later) ── */

/* The map opened from Show on map beside Country: world.json read from the app the first time through
   the app's own `api`, never from the web, then the overlay holding the map alone, its card given the
   focus so the keys go on to its circles. */
async function sfMapOpen(from) {
  SF.mapFrom = from || null;
  if (!SF.world) {
    try {
      SF.world = await api('/world.json');
    } catch {
      say(SF_MAP_WORDS.missing, 9000);
      return;
    }
  }
  $('sf-map').hidden = false;
  sfMapDraw();
  $('sf-map-card').focus();
}

/* the map shut, by its close, Esc or a click outside it, the focus given back to the link */
function sfMapClose() {
  if ($('sf-map').hidden) return;
  $('sf-map').hidden = true;
  sfMapTipHide();
  const back = SF.mapFrom && SF.mapFrom.isConnected ? SF.mapFrom : $('sf-groups').querySelector('[data-act="map"]');
  SF.mapFrom = null;
  if (back) back.focus();
}

/* the map as the filters stand, Country's counts exactly as its group shows them, the list a screen
   reader hears, and the line under it */
function sfMapDraw() {
  if (!SF.world) return;
  const { rows, groups, counts } = sfFacetsData();
  const m = sfMapFrom(SF.world, rows, groups, counts, SF.filters, SF.stage);
  const html = sfMapSvg(SF.world, m, null);
  if ($('sf-map-box').innerHTML !== html) $('sf-map-box').innerHTML = html;
  $('sf-map-list').innerHTML = m.circles.map((c) => `<li>${esc(sfMapSays(c))}</li>`).join('');
  $('sf-map-line').textContent = sfMapLine(m);
  sfMapTipHide();
}

/* a circle's country and count in the app's own tip, over the circle, kept inside the map, on hover
   and on focus */
function sfMapTip(dot) {
  const tip = $('sf-map-tip');
  const frame = $('sf-map-frame').getBoundingClientRect();
  const at = dot.querySelector('circle').getBoundingClientRect();
  tip.textContent = dot.getAttribute('aria-label') || '';
  tip.hidden = false;
  const w = tip.offsetWidth;
  const left = Math.max(0, Math.min(frame.width - w, at.left - frame.left + at.width / 2 - w / 2));
  const top = at.top - frame.top - tip.offsetHeight - 6;
  tip.style.left = `${Math.round(left)}px`;
  tip.style.top = `${Math.round(top < 0 ? at.bottom - frame.top + 6 : top)}px`;
}

function sfMapTipHide() {
  const tip = $('sf-map-tip');
  if (tip && !tip.hidden) tip.hidden = true;
}

/* a file handed to the browser to save, under its name */
function sfSaveBlob(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
}

/* The map saved for a paper, as it stands: always in the light appearance on white, whatever the
   app's, an SVG as markup, or a PNG drawn from it about SF_MAP_PNG pixels wide, the run's name before
   `countries` in the file's name. The browser's own parser and serialiser make the file whole, its
   namespace among it. */
function sfMapSave(kind) {
  if (!SF.world) return;
  const { rows, groups, counts } = sfFacetsData();
  const m = sfMapFrom(SF.world, rows, groups, counts, SF.filters, SF.stage);
  const made = document.createElement('template');
  made.innerHTML = sfMapSvg(SF.world, m, SF_MAP_PAPER);
  const root = made.content.firstChild;
  const wide = SF_MAP_PNG;
  const high = Math.round((SF_MAP_PNG * SF.world.height) / SF.world.width);
  if (kind === 'svg') {
    sfSaveBlob(new Blob([new XMLSerializer().serializeToString(root)], { type: 'image/svg+xml' }), sfMapFile(SF.name, 'svg'));
    return;
  }
  // drawn at the PNG's own size, so its lines and numbers are as sharp as a vector's
  root.setAttribute('width', String(wide));
  root.setAttribute('height', String(high));
  const img = new Image();
  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(root)], { type: 'image/svg+xml' }));
  img.onload = () => {
    const canvas = document.createElement('canvas');
    canvas.width = wide;
    canvas.height = high;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = SF_MAP_PAPER.paper;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(url);
    canvas.toBlob((png) => { if (png) sfSaveBlob(png, sfMapFile(SF.name, 'png')); }, 'image/png');
  };
  img.onerror = () => { URL.revokeObjectURL(url); say(SF_MAP_WORDS.missing, 9000); };
  img.src = url;
}

/* the map's controls: its name, its note and its buttons' words from SF_MAP_WORDS, its close, a click
   outside it, the tip over a circle on hover and on focus, and its two buttons */
function sfMapBoot() {
  $('sf-map-head').textContent = SF_MAP_WORDS.head;
  $('sf-map-note').textContent = SF_MAP_WORDS.note;
  $('sf-map-png').textContent = SF_MAP_WORDS.png;
  $('sf-map-svg').textContent = SF_MAP_WORDS.svg;
  $('sf-map-close').onclick = sfMapClose;
  $('sf-map').addEventListener('click', (e) => { if (e.target === $('sf-map')) sfMapClose(); });
  const box = $('sf-map-box');
  const dot = (e) => (e.target && e.target.closest ? e.target.closest('.sf-map-dot') : null);
  box.addEventListener('pointerover', (e) => { const d = dot(e); if (d) sfMapTip(d); });
  box.addEventListener('pointerout', (e) => { if (dot(e) && !(e.relatedTarget && dot({ target: e.relatedTarget }))) sfMapTipHide(); });
  box.addEventListener('focusin', (e) => { const d = dot(e); if (d) sfMapTip(d); });
  box.addEventListener('focusout', sfMapTipHide);
  $('sf-map-png').onclick = () => sfMapSave('png');
  $('sf-map-svg').onclick = () => sfMapSave('svg');
}

/* ── the two views ── */

/* The table, where Sift opens, or the record screen, a row opened from it by a click or Enter. The
   table comes back by the record's way back, Esc or the browser's Back on the same row, at the scroll
   it had, its filters and sort as they were. Neither is kept anywhere, since Sift always opens on the
   table. */
function sfSetView(view) {
  if (!SF.folder || !['record', 'table'].includes(view) || view === SF.view) return;
  if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
  if (SF.view === 'table') SF.tvScroll = $('sf-tv-box').scrollTop;
  SF.view = view;
  SF.picking = false;
  sfDraw();
  if (view === 'table') {
    $('sf-tv-box').scrollTop = SF.tvScroll;
    SF.tvReveal = true;
    sfTvMark();
  } else {
    $('sf-record').scrollTop = 0;
    $('sf-body').scrollTop = 0;
  }
}

/* The chosen row's record opened, by a click on its row or Enter, as an entry of its own in the
   browser's history (12 October). A click marks when, so the second press of a double-click, out of
   habit, does nothing on the record it lands on. */
function sfOpenRecord(byClick = false) {
  if (!sfRecord() || SF.view === 'record') return;
  SF.openedAt = byClick ? Date.now() : 0;
  sfSetView('record');
  sfHistoryPush();
}

/* ── Back and Forward (12 October) ── */

/* The browser's Back and Forward, and a mouse's back and forward buttons, which send the same, walk
   between the table and a record within a screening. A record opened from the table is an entry of
   its own in the browser's history, which names the record he is on as he walks the records, so Back
   comes to the table where he left it and Forward goes back into the record he left. The record's
   way back and Esc go back the same way. A note or a field being typed is kept as the record is left,
   as every leaving keeps it. The other screens keep no history of their own, so Back from the table
   goes where it went before. */
const SF_HISTORY = 'idiograph-sift-record';
// how soon after a click opens a record its double-click's second press can come
const SF_SECOND_PRESS = 500;

function sfOnRecordEntry() {
  try {
    const held = history.state;
    return !!held && held.kind === SF_HISTORY && held.folder === SF.folder;
  } catch { return false; }
}

function sfHistoryPush() {
  const r = sfRecord();
  try { history.pushState({ kind: SF_HISTORY, folder: SF.folder, rec: r ? r.rec_id : null }, ''); } catch { /* no history */ }
}

/* the record's entry names the record he is on, so Forward comes back to it */
function sfHistoryKeep() {
  const r = sfRecord();
  if (!r || SF.view !== 'record' || !sfOnRecordEntry() || history.state.rec === r.rec_id) return;
  try { history.replaceState(Object.assign({}, history.state, { rec: r.rec_id }), ''); } catch { /* no history */ }
}

/* a record's entry left behind as the screen opens or is left, so Back and Forward open nothing on it */
function sfHistoryDrop() {
  if (!sfOnRecordEntry()) return;
  try { history.replaceState(null, ''); } catch { /* no history */ }
}

/* the record's way back and Esc: Back, when the record has its entry, else the table at once */
function sfToTable() {
  if (SF.view !== 'record') return;
  if (sfOnRecordEntry()) { history.back(); return; }
  sfSetView('table');
}

/* The browser's Back or Forward on the Sift screen: an entry of a record of this screening opens that
   record on the table's rows, and any other entry shows the table */
function sfPopState(e) {
  if (!sfShown() || !SF.folder) return;
  const held = e.state;
  if (held && held.kind === SF_HISTORY && held.folder === SF.folder) {
    if (SF.view === 'record') return;
    const at = SF.ids.indexOf(held.rec);
    if (at >= 0) SF.at = at;
    if (!sfRecord() || sfFtEmpty()) return;
    SF.openedAt = 0;
    sfSetView('record');
    return;
  }
  if (SF.view === 'record') sfSetView('table');
}

/* ── his own fields ── */

/* a field's value as it stands, the participants empty while they are a guess */
function sfFieldNow(f, field) {
  if (field === 'participants') return f.confirmed ? String(f.participants || '') : '';
  if (field === 'rating') return f.rating ? String(f.rating) : '';
  if (['notes', 'digest', 'critique'].includes(field)) return String(f[field] || '');
  return String((f.own || {})[field] || '');
}

/* One of his fields on a record, drawn at once and sent to the server, one change after another
   with the decisions. A value that changes nothing sends nothing, and a guess left as it was is
   never written. One the server refuses says why, and the screening is read again. */
function sfFieldSave(rec, field, value) {
  const r = SF.byId.get(rec);
  if (!r) return;
  const f = r.fields || (r.fields = { own: {} });
  const text = String(value === null || value === undefined ? '' : value);
  if (text.trim() === sfFieldNow(f, field).trim() && (field !== 'participants' || f.confirmed || !text.trim())) return;
  if (field === 'rating') f.rating = Number(text) || null;
  else if (field === 'participants') Object.assign(f, { participants: text.trim(), confirmed: true, guess: null });
  else if (['notes', 'digest', 'critique'].includes(field)) f[field] = text.trim();
  else f.own = Object.assign({}, f.own, { [field]: text.trim() });
  sfDraw();
  sfQueue(async () => {
    try {
      sfLand(await api('/api/sift', { op: 'field', folder: SF.folder, rec_id: rec, field, value: text }));
    } catch (err) {
      say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
      await sfReload();
      return;
    }
    sfDraw();
  });
}

/* the fields under the record: each as the record holds it, never the one he is typing in, the
   guess as the participants' faint text with Confirm beside it, and a box or a list for each
   column of his, a Number column's box as the participants', Unknown in it while it is empty */
function sfFieldsDraw(r) {
  const f = r.fields || {};
  const same = SF.fieldsFor === r.rec_id;
  const set = (el, value) => { if (!same || document.activeElement !== el) el.value = value; };
  $('sf-fields').dataset.rec = r.rec_id;
  const p = $('sf-f-participants');
  set(p, sfFieldNow(f, 'participants'));
  // the guess with its question mark, and with none Unknown, never nought (12 October)
  p.placeholder = !f.confirmed && f.guess ? `${f.guess}?` : SF_BLANK_WORDS.participants;
  $('sf-f-confirm').hidden = !!f.confirmed || !f.guess;
  $('sf-f-rating').innerHTML = sfStars(f.rating);
  $('sf-f-unrated').hidden = !!f.rating;
  ['notes', 'digest', 'critique'].forEach((k) => set($(`sf-f-${k}`), f[k] || ''));
  // his columns that show on the screening's table, the form's alone left to Extract and appraise, and
  // one of the form's types drawn as the form draws it (13 October, later)
  const all = ((SF.table && SF.table.own) || []).filter(sfOnTable);
  const own = all.filter((c) => ['text', 'choice', 'number'].includes(c.type) && !c.from && !c.not_reported);
  sfFormInto($('sf-f-form'), r, all.filter((c) => !own.includes(c)), 'sf-of', false);
  const shape = JSON.stringify(own);
  const holder = $('sf-f-own');
  if (holder.dataset.shape !== shape) {
    holder.innerHTML = own.map((c, i) => `<div class="sf-frow"><label class="sf-flabel" for="sf-o-${i}">${esc(c.name)}</label>`
      + (c.type === 'choice'
        ? `<span class="sf-fval"><select class="sf-field" id="sf-o-${i}" data-field="${escAttr(c.key)}"><option value=""></option>`
          + `${(c.options || []).map((o) => `<option value="${escAttr(o)}">${esc(o)}</option>`).join('')}</select></span>`
        : c.type === 'number'
          ? `<span class="sf-fval"><input class="sf-field sf-f-num" id="sf-o-${i}" data-field="${escAttr(c.key)}" type="text"`
            + ` inputmode="numeric" autocomplete="off" spellcheck="false" placeholder="${SF_BLANK_WORDS.participants}"></span>`
          : `<input class="sf-field" id="sf-o-${i}" data-field="${escAttr(c.key)}" type="text" autocomplete="off">`) + '</div>').join('');
    holder.dataset.shape = shape;
  }
  holder.querySelectorAll('[data-field]').forEach((el) => {
    const v = (f.own || {})[el.dataset.field] || '';
    if (el.tagName === 'SELECT' && v && ![...el.options].some((o) => o.value === v)) {
      el.insertAdjacentHTML('beforeend', `<option value="${escAttr(v)}">${esc(v)}</option>`);
    }
    set(el, v);
  });
  SF.fieldsFor = r.rec_id;
}

function sfFieldsBoot() {
  const box = $('sf-fields');
  // a field is kept when it is left, and a choice as soon as it is made
  box.addEventListener('focusout', (e) => {
    const el = e.target;
    if (el && el.dataset && el.dataset.field && box.dataset.rec) sfFieldSave(box.dataset.rec, el.dataset.field, el.value);
  });
  box.addEventListener('change', (e) => {
    if (e.target.tagName === 'SELECT' && e.target.dataset.field) sfFieldSave(box.dataset.rec, e.target.dataset.field, e.target.value);
  });
  box.addEventListener('click', (e) => {
    const star = e.target.closest('.sf-star');
    const r = box.dataset.rec ? SF.byId.get(box.dataset.rec) : null;
    if (star && r) { const n = Number(star.dataset.star); sfFieldSave(r.rec_id, 'rating', (r.fields || {}).rating === n ? '' : String(n)); }
  });
  $('sf-f-confirm').onclick = () => {
    const r = box.dataset.rec ? SF.byId.get(box.dataset.rec) : null;
    if (r && r.fields && !r.fields.confirmed && r.fields.guess) sfFieldSave(r.rec_id, 'participants', String(r.fields.guess));
  };
}

function sfColsBoot() {
  $('sf-tv-cols').onclick = sfColsOpen;
  $('sf-cols-close').onclick = sfColsClose;
  $('sf-col-add').onclick = sfColAdd;
  $('sf-cols-reset').onclick = () => sfColsSave(((SF.table && SF.table.defaults) || []).map((c) => ({ key: c.key, shown: c.shown })));
  $('sf-col-type').onchange = () => { $('sf-col-options').hidden = $('sf-col-type').value !== 'choice'; };
  const list = $('sf-cols-list');
  list.addEventListener('change', (e) => {
    if (e.target.dataset.act === 'show') sfColsShow(e.target.closest('li').dataset.key, e.target.checked);
  });
  list.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-act="remove"]');
    if (btn) sfColRemove(btn.closest('li').dataset.key);
  });
  // a row dragged up or down by its handle, the home screen's own
  list.addEventListener('pointerdown', (e) => {
    const grip = e.target.closest('button.pc-grip');
    if (grip) gripDrag(e, grip.closest('li'), list, sfColsGrip());
  });
  list.addEventListener('focusout', (e) => {
    const t = e.target;
    const li = t.closest('li[data-key]');
    const c = li && ((SF.table && SF.table.own) || []).find((o) => o.key === li.dataset.key);
    if (!c) return;
    if (t.dataset.act === 'name') {
      const name = t.value.trim();
      if (!name) t.value = c.name;
      else if (name !== c.name) sfColumn({ act: 'change', key: c.key, name });
    } else if (t.dataset.act === 'options') {
      const now = t.value.split('\n').map((s) => s.trim()).filter(Boolean);
      if (now.join('\n') !== (c.options || []).join('\n')) sfColumn({ act: 'change', key: c.key, options: t.value });
    }
  });
}

/* ── the columns ── */

function sfColsOpen() {
  if (!SF.table) return;
  sfColsDraw();
  $('sf-col-name').value = '';
  $('sf-col-type').value = 'text';
  $('sf-col-options').value = '';
  $('sf-col-options').hidden = true;
  $('sf-cols').hidden = false;
}

function sfColsClose() {
  if (document.activeElement && $('sf-cols').contains(document.activeElement)) document.activeElement.blur();
  $('sf-cols').hidden = true;
}

/* the card's keys: Alt and an arrow on a row's handle move the row, Esc closes it, Enter in the new
   name adds the column, and in a name leaves it */
function sfColsKey(e) {
  const t = e.target;
  const grip = t && t.closest && t.closest('#sf-cols-list button.pc-grip');
  if (grip && gripKeys(e, grip.closest('li'), $('sf-cols-list'), sfColsGrip())) return;
  if (e.key === 'Escape') { e.preventDefault(); sfColsClose(); return; }
  if (e.key !== 'Enter' || !t || t.tagName !== 'INPUT' || t.type !== 'text') return;
  e.preventDefault();
  if (t === $('sf-col-name')) sfColAdd();
  else t.blur();
}

/* Every column in his order: the handle that drags it up or down at its left, shown or hidden, his
   own by a name that renames it, their choices one a line, and Remove, then Reset to default. The
   whole row ticks its box (13 October): the box and the column's name are one label filling the row,
   and on his own column's row, where the name is a box to type in, the label holds the tick alone and
   a press anywhere else on the row but its controls ticks it too, through the app's `data-tick-row`. */
function sfColsDraw() {
  const cols = sfColumns(SF.table);
  const own = new Map(((SF.table && SF.table.own) || []).map((c) => [c.key, c]));
  $('sf-cols-list').innerHTML = cols.map((c) => {
    const mine = own.get(c.key);
    const tick = `<label class="sf-col-tick${mine ? '' : ' sf-col-whole'}"><input type="checkbox" data-act="show"`
      + ` aria-label="${escAttr(c.label)}"${c.shown ? ' checked' : ''}>${mine ? '' : `<span class="sf-col-label">${esc(c.label)}</span>`}</label>`;
    const name = mine
      ? `<input class="sf-col-name" type="text" data-act="name" value="${escAttr(mine.name)}" aria-label="${escAttr(t('sift.name'))}" autocomplete="off" spellcheck="false">`
      : '';
    const opts = mine && ['choice', 'multi'].includes(mine.type)
      ? `<textarea class="sf-col-opts" data-act="options" rows="2" aria-label="${escAttr(t('sift.choices'))}" spellcheck="false">${esc((mine.options || []).join('\n'))}</textarea>` : '';
    return `<li class="sf-col" data-key="${escAttr(c.key)}" data-tick-row>${gripHtml(c.label)}${tick}`
      + `${name}${mine ? `<button type="button" class="ghost small btn-remove sf-col-remove" data-act="remove">${esc(t('sift.remove'))}</button>` : ''}${opts}</li>`;
  }).join('');
  // Reset to default waits while the columns stand as they first did
  const first = ((SF.table && SF.table.defaults) || []).map((c) => `${c.key}:${c.shown}`).join('\n');
  $('sf-cols-reset').disabled = !first || first === cols.map((c) => `${c.key}:${c.shown}`).join('\n');
}

/* the handle's `how` on Set columns' rows: the column said by its heading, and the order saved */
function sfColsGrip() {
  return {
    rows: ':scope > li.sf-col',
    live: 'sf-cols-said',
    said: (li, to, n) => t('sift.grip.said', { name: (sfColumns(SF.table).find((c) => c.key === li.dataset.key) || { label: '' }).label,
      at: to + 1, n }),
    moved: sfColsMoved,
  };
}

/* Set columns' rows in the order a drag or Alt and an arrow left them, saved as his order, the
   handle that has the focus keeping it once the rows are drawn again */
function sfColsMoved(rows) {
  const by = new Map(sfColumns(SF.table).map((c) => [c.key, c]));
  const cols = rows.map((li) => by.get(li.dataset.key)).filter(Boolean).map((c) => ({ key: c.key, shown: c.shown }));
  if (cols.length !== by.size) return;
  const held = document.activeElement && document.activeElement.closest ? document.activeElement.closest('#sf-cols-list li[data-key]') : null;
  sfColsSave(cols, held ? [held.dataset.key, 'grip'] : null);
}

/* the columns shown and their order kept in sift.json, drawn at once, a sort on a column now hidden
   let go, and its filter kept, since the sidebar filters by a column whether it shows or not */
function sfColsSave(columns, focus) {
  SF.table = Object.assign({}, SF.table, { columns });
  const shown = new Set(columns.filter((c) => c.shown).map((c) => c.key).concat([SF_ID.key]));
  SF.sort = SF.sort.filter((s) => shown.has(s.key));
  sfColsDraw();
  if (focus) {
    const btn = [...$('sf-cols-list').querySelectorAll('li')].find((li) => li.dataset.key === focus[0]);
    const go = btn && btn.querySelector(`button[data-act="${focus[1]}"]`);
    if (go && !go.disabled) go.focus();
  }
  sfRefilter(true);
  sfQueue(async () => {
    const data = await api('/api/sift', { op: 'view', folder: SF.folder, columns });
    if (data.table) SF.table = data.table;
  });
}

function sfColsShow(key, shown) {
  sfColsSave(sfColumns(SF.table).map((c) => ({ key: c.key, shown: c.key === key ? shown : c.shown })));
}

/* The order with the column `key` moved to stand before the column `before`, or with no `before`
   after the last column shown, every hidden column keeping its place among the others. The same
   order back when nothing moves. */
function sfColMoved(cols, key, before) {
  const it = cols.find((c) => c.key === key);
  if (!it || key === before) return cols;
  const rest = cols.filter((c) => c.key !== key);
  const at = before ? rest.findIndex((c) => c.key === before) : rest.map((c) => c.shown).lastIndexOf(true) + 1;
  if (at < 0) return cols;
  return [...rest.slice(0, at), it, ...rest.slice(at)];
}

/* a column of his added, changed or removed on the server, the screening read again so every
   record carries it under its name, a sort or a filter on it following a new name */
async function sfColumn(body) {
  let data;
  try {
    await SF.chain;
    data = await api('/api/sift', Object.assign({ op: 'column', folder: SF.folder }, body));
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    sfColsDraw();
    return null;
  }
  const was = body.key;
  if (was && body.act === 'remove') {
    SF.sort = SF.sort.filter((s) => s.key !== was);
    delete SF.filters[was];
    delete SF.facetsFind[was];
  } else if (was && data.key && data.key !== was) {
    SF.sort = SF.sort.map((s) => (s.key === was ? { key: data.key, dir: s.dir } : s));
    if (was in SF.filters) { SF.filters[data.key] = SF.filters[was]; delete SF.filters[was]; }
    if (was in SF.facetsFind) { SF.facetsFind[data.key] = SF.facetsFind[was]; delete SF.facetsFind[was]; }
  }
  if (data.table) SF.table = data.table;
  const r = sfRecord();
  await sfReload();
  sfApply(r ? r.rec_id : null);
  sfDraw();
  sfFiltersKeep();
  if (!$('sf-cols').hidden) sfColsDraw();
  return data;
}

async function sfColAdd() {
  const name = $('sf-col-name').value.trim();
  if (!name) { $('sf-col-name').focus(); return; }
  // Text, Choice list or Number, a whole number such as a count of analysts (13 October)
  const type = ['choice', 'number'].includes($('sf-col-type').value) ? $('sf-col-type').value : 'text';
  const done = await sfColumn({ act: 'add', name, type, options: $('sf-col-options').value });
  if (!done) return;
  $('sf-col-name').value = '';
  $('sf-col-type').value = 'text';
  $('sf-col-options').value = '';
  $('sf-col-options').hidden = true;
}

/* a column of his removed, asked first, its values kept in the log's line */
async function sfColRemove(key) {
  const c = ((SF.table && SF.table.own) || []).find((o) => o.key === key);
  if (!c) return;
  if (!(await sfAsk(t('sift.cols.remove_head'), t('sift.cols.remove_line', { name: c.name }), t('sift.remove'), true))) return;
  await sfColumn({ act: 'remove', key });
}

/* ── Extract and appraise (13 October, later) ── */

/* The stage after full text, where each paper included there has its data extracted and its quality
   appraised on a form the project sets up, PRISMA 2020's items 9 to 11. Its name is `RV_FORM_NAME` in
   sift_search.js, the one place the page keeps it. The screen stands at full text underneath, `SF.form`
   true and `SF.stage` ft, so the table, its sort, its filters and Set columns work as Screening's, over
   the records included at full text, or with the filter Benchmark papers ticked the plan's benchmark
   papers whatever their decision, so he can pilot the form on them before any paper is included. The
   form is his own columns, one definition: each says where it shows, `where`, the screening's table, the
   form or both (see sift.py). A record opens its form on the record pane with its PDF and links, each
   field kept as he leaves it through the field op, a line in the log as his columns' values are. No AI
   anywhere in the stage. */
/* ── the form on the record ── */

/* the controls of one field of the form, named for its record so a radio group is its own, its value
   set by `sfFormSet` */
function sfFormRowHtml(c, r, id) {
  const k = escAttr(c.key);
  const nr = c.not_reported ? `<label class="sf-fm-nr"><input type="checkbox" data-fk="${k}" data-part="nr"> ${SF_NR_WORD}</label>` : '';
  const tags = `<span class="sf-fm-sift" hidden>${esc(t('sift.fm.from_sift'))}</span><span class="sf-fm-gone" hidden>${esc(t('sift.fm.gone'))}</span>`;
  const head = (inner) => `<div class="sf-frow sf-fm-row${['long', 'passages', 'multi', 'yesno'].includes(c.type) ? ' sf-frow-long' : ''}"`
    + ` data-fk="${k}">${inner}</div>`;
  const label = `<label class="sf-flabel" for="${id}">${esc(c.name)}</label>`;
  const named = `<span class="sf-flabel" id="${id}">${esc(c.name)}</span>`;
  const value = sfFieldValue(r, c).value;
  if (c.type === 'yesno' || c.type === 'multi') {
    const held = c.type === 'multi' ? sfMultiParts(value) : [value];
    const opts = c.type === 'yesno' ? Object.keys(SF_YES_NO) : [...c.options, ...held.filter((v) => v && v !== SF_NR && !c.options.includes(v))];
    const type = c.type === 'yesno' ? 'radio' : 'checkbox';
    const ticks = opts.map((o) => `<label class="sf-fm-tick"><input type="${type}" name="sf-fm-${escAttr(r.rec_id)}-${k}"`
      + ` data-fk="${k}" data-part="v" value="${escAttr(o)}"> ${esc(c.type === 'yesno' ? SF_YES_NO[o] : o)}`
      + `${c.type === 'multi' && !c.options.includes(o) ? ` <span class="sf-fm-gone">${esc(t('sift.fm.gone'))}</span>` : ''}</label>`).join('');
    return head(`${named}<span class="sf-fval sf-fm-ticks" role="group" aria-labelledby="${id}">${ticks}${nr}</span>`);
  }
  if (c.type === 'passages') {
    const list = sfPassages(value);
    const n = list.length + (SF.psgAdd[`${r.rec_id}|${c.key}`] || 0);
    const rows = Array.from({ length: Math.max(n, 1) }, (_, i) => `<div class="sf-psg" data-i="${i}"><textarea class="sf-field"`
      + ` data-fk="${k}" data-part="text" data-i="${i}" rows="2" aria-label="${escAttr(t('sift.fm.passage', { name: c.name, i: i + 1 }))}"`
      + ' spellcheck="true" data-gramm="false" data-gramm_editor="false" data-enable-grammarly="false"></textarea>'
      + `<input class="sf-field sf-psg-page" type="text" data-fk="${k}" data-part="page" data-i="${i}" placeholder="${escAttr(t('sift.fm.page'))}"`
      + ` aria-label="${escAttr(t('sift.fm.page_of', { name: c.name, i: i + 1 }))}" autocomplete="off" spellcheck="false">`
      + `<button type="button" class="ghost small btn-remove sf-psg-remove" data-fk="${k}" data-act="psg-remove" data-i="${i}">${esc(t('sift.remove'))}</button></div>`).join('');
    return head(`${named}<span class="sf-fval sf-fm-psgs" role="group" aria-labelledby="${id}">${rows}`
      + `<span class="sf-fm-foot"><button type="button" class="ghost small" data-fk="${k}" data-act="psg-add">${esc(t('sift.fm.add_passage'))}</button>${nr}</span></span>`);
  }
  let box;
  if (c.type === 'choice') {
    const gone = value && value !== SF_NR && !c.options.includes(value) ? [value] : [];
    box = `<select class="sf-field" id="${id}" data-fk="${k}" data-part="v"><option value=""></option>`
      + [...c.options, ...gone].map((o) => `<option value="${escAttr(o)}">${esc(o)}</option>`).join('') + '</select>';
  } else if (c.type === 'long') {
    box = `<textarea class="sf-field" id="${id}" data-fk="${k}" data-part="v" rows="3" spellcheck="true" data-gramm="false"`
      + ' data-gramm_editor="false" data-enable-grammarly="false"></textarea>';
  } else {
    box = `<input class="sf-field${c.type === 'number' ? ' sf-f-num' : ''}" id="${id}" data-fk="${k}" data-part="v" type="text"`
      + `${c.type === 'number' ? ` inputmode="numeric" placeholder="${SF_BLANK_WORDS.participants}"` : ''} autocomplete="off"`
      + `${c.type === 'number' ? ' spellcheck="false"' : ''}>`;
  }
  return head(`${label}<span class="sf-fval">${box}${tags}${nr}</span>`);
}

/* each field's value set into its controls, never into the box he is typing in, Not reported ticked and
   the box beside it off, From Sift beside a value taken from Sift, and each row shown or hidden by its
   condition, a section's heading with its fields */
function sfFormSet(box, r, fields) {
  const shown = sfShownKeys(r, fields);
  const by = new Map(fields.map((c) => [c.key, c]));
  box.querySelectorAll('.sf-fm-row[data-fk]').forEach((row) => {
    const c = by.get(row.dataset.fk);
    if (!c) return;
    row.hidden = !shown.has(c.key);
    const { value, sift } = sfFieldValue(r, c);
    const nr = value === SF_NR;
    const tick = row.querySelector('[data-part="nr"]');
    if (tick) tick.checked = nr;
    // the box he is in, which the shape keeps while the record stands, so another record's never is
    const typing = (el) => document.activeElement === el;
    if (c.type === 'yesno' || c.type === 'multi') {
      const held = c.type === 'multi' ? sfMultiParts(value) : [value];
      row.querySelectorAll('[data-part="v"]').forEach((el) => { el.checked = !nr && held.includes(el.value); el.disabled = nr; });
    } else if (c.type === 'passages') {
      const list = sfPassages(value);
      row.querySelectorAll('.sf-psg').forEach((p) => {
        const at = list[Number(p.dataset.i)] || { text: '', page: '' };
        p.querySelectorAll('[data-part]').forEach((el) => {
          if (!typing(el)) el.value = el.dataset.part === 'page' ? at.page : at.text;
          el.disabled = nr;
        });
      });
      row.querySelectorAll('[data-act]').forEach((el) => { el.disabled = nr; });
    } else {
      const el = row.querySelector('[data-part="v"]');
      if (el && !typing(el)) el.value = nr ? '' : value;
      if (el) el.disabled = nr;
      const gone = row.querySelector('.sf-fm-gone');
      if (gone) gone.hidden = !(c.type === 'choice' && value && !nr && !c.options.includes(value));
    }
    const tag = row.querySelector('.sf-fm-sift');
    if (tag) tag.hidden = !sift;
  });
  box.querySelectorAll('.sf-fm-sec').forEach((h) => {
    h.hidden = ![...box.querySelectorAll(`.sf-fm-row[data-sec="${CSS.escape(h.dataset.sec)}"]`)].some((row) => !row.hidden);
  });
}

/* the shape a form is drawn in: its record, its fields, the choices each holds that its list no longer
   does and its passages, so it is built again only when one of them changes and a box being typed in
   keeps its place */
function sfFormShape(r, fields, prefix) {
  return JSON.stringify([prefix, r.rec_id, fields, fields.map((c) => {
    const v = sfFieldValue(r, c).value;
    if (c.type === 'passages') return sfPassages(v).length + (SF.psgAdd[`${r.rec_id}|${c.key}`] || 0);
    if (c.type === 'multi') return sfMultiParts(v).filter((p) => !c.options.includes(p));
    return c.type === 'choice' && v && v !== SF_NR && !c.options.includes(v) ? v : '';
  })]);
}

/* The fields `fields` drawn into `box` for a record, under their sections' headings, with `prefix` for
   their ids, built again only when its shape changes, the control he was in given back its focus. */
function sfFormInto(box, r, fields, prefix, sections) {
  const shape = sfFormShape(r, fields, prefix);
  if (box.dataset.shape !== shape) {
    const was = document.activeElement && box.contains(document.activeElement) ? document.activeElement : null;
    const mark = was ? [was.dataset.fk || '', was.dataset.part || '', was.dataset.i || '', was.dataset.act || '', was.value || ''] : null;
    let html = '';
    let sec = null;
    fields.forEach((c, i) => {
      if (sections && c.section !== sec) {
        sec = c.section;
        if (sec) html += `<h3 class="sf-fm-sec" data-sec="${escAttr(sec)}">${esc(sec)}</h3>`;
      }
      html += sfFormRowHtml(c, r, `${prefix}-${i}`).replace('data-fk=', `data-sec="${escAttr(sections ? c.section : '')}" data-fk=`);
    });
    box.innerHTML = html;
    box.dataset.shape = shape;
    if (mark) {
      const back = [...box.querySelectorAll('[data-fk]')].find((el) => [el.dataset.fk || '', el.dataset.part || '', el.dataset.i || '',
        el.dataset.act || '', el.type === 'radio' || el.type === 'checkbox' ? el.value : mark[4]].join('\n') === mark.join('\n'));
      if (back) back.focus();
    }
  }
  sfFormSet(box, r, fields);
}

/* the form on the record pane, its fields under their headings, or a line while it has none, and the
   record's head marked Done once every field shown holds a value or Not reported */
function sfFormDraw(r) {
  const box = $('sf-form');
  const fields = sfFormFields();
  $('sf-fm-done').hidden = !sfFormDone(r);
  if (!fields.length) {
    box.dataset.shape = '';
    box.innerHTML = `<p class="sf-empty">${esc(t('sift.fm.no_fields'))}</p>`;
    return;
  }
  sfFormInto(box, r, fields, 'sf-fm', true);
  SF.formFor = r.rec_id;
}

/* One value of the form kept, drawn at once and sent through the field op, one change after another
   with the rest: a list of choices or of passages as the CSV holds it, a value that changes nothing
   sending nothing. One the server refuses says why, and the screening is read again. */
function sfFormSave(rec, key, value) {
  const r = SF.byId.get(rec);
  const c = sfOwnDefs().find((o) => o.key === key);
  if (!r || !c) return;
  const f = r.fields || (r.fields = { own: {} });
  const now = String((f.own || {})[key] || '');
  let cell;
  if (Array.isArray(value) && c.type === 'multi') {
    cell = [...c.options.filter((o) => value.includes(o)), ...value.filter((v) => !c.options.includes(v))].join('; ');
  } else if (Array.isArray(value)) {
    const list = value.map((p) => ({ page: String(p.page || '').trim(), text: String(p.text || '').trim() })).filter((p) => p.text);
    if (JSON.stringify(list) === JSON.stringify(sfPassages(now))) return;
    cell = list.length ? JSON.stringify(list) : '';
  } else cell = c.type === 'long' ? String(value).trim() : String(value).replace(/\s+/g, ' ').trim();
  if (cell === now) return;
  f.own = Object.assign({}, f.own, { [key]: cell });
  sfDraw();
  sfQueue(async () => {
    try {
      sfLand(await api('/api/sift', { op: 'field', folder: SF.folder, rec_id: rec, field: key, value }));
    } catch (err) {
      say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
      await sfReload();
      return;
    }
    sfDraw();
  });
}

/* a row's passages as its boxes hold them, in order */
function sfPsgRead(row) {
  return [...row.querySelectorAll('.sf-psg')].map((p) => ({
    text: (p.querySelector('[data-part="text"]') || {}).value || '',
    page: (p.querySelector('[data-part="page"]') || {}).value || '',
  }));
}

/* The form's controls, on the record pane and among his fields under the record: a box kept as it is
   left, a choice, a tick and Not reported as soon as they are made, a passage added or removed, and a
   value taken from Sift left as it is when it was not changed. */
function sfFormBoot(box) {
  const rec = () => (sfRecord() || {}).rec_id;
  const def = (el) => sfOwnDefs().find((o) => o.key === el.dataset.fk);
  box.addEventListener('focusout', (e) => {
    const el = e.target;
    const c = el && el.dataset && el.dataset.fk ? def(el) : null;
    const r = sfRecord();
    if (!c || !r || !['INPUT', 'TEXTAREA'].includes(el.tagName) || el.type === 'checkbox' || el.type === 'radio') return;
    const row = el.closest('.sf-fm-row');
    if (c.type === 'passages') {
      // a passage left whole for a moment while he goes to its page box, then kept as the row stands
      setTimeout(() => {
        if (row.contains(document.activeElement) && document.activeElement.tagName !== 'BUTTON') return;
        const list = sfPsgRead(row);
        SF.psgAdd[`${r.rec_id}|${c.key}`] = list.filter((p) => !p.text.trim()).length ? 1 : 0;
        sfFormSave(r.rec_id, c.key, list);
      }, 0);
      return;
    }
    const { value, sift } = sfFieldValue(r, c);
    if (sift && el.value.trim() === value.trim()) return;
    sfFormSave(r.rec_id, c.key, el.value);
  });
  box.addEventListener('change', (e) => {
    const el = e.target;
    const c = el && el.dataset && el.dataset.fk ? def(el) : null;
    if (!c || !rec()) return;
    const row = el.closest('.sf-fm-row');
    if (el.dataset.part === 'nr') { sfFormSave(rec(), c.key, el.checked ? SF_NR : ''); return; }
    if (el.tagName === 'SELECT' || el.type === 'radio') { sfFormSave(rec(), c.key, el.value); return; }
    if (el.type === 'checkbox' && c.type === 'multi') {
      sfFormSave(rec(), c.key, [...row.querySelectorAll('[data-part="v"]')].filter((x) => x.checked).map((x) => x.value));
    }
  });
  box.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-act]');
    const c = btn ? def(btn) : null;
    const r = sfRecord();
    if (!c || !r) return;
    const k = `${r.rec_id}|${c.key}`;
    const row = btn.closest('.sf-fm-row');
    if (btn.dataset.act === 'psg-add') {
      // an empty passage there already takes the words, else a new one is added under the rest
      const empty = [...row.querySelectorAll('textarea[data-part="text"]')].find((t) => !t.value.trim());
      if (empty) { empty.focus(); return; }
      SF.psgAdd[k] = (SF.psgAdd[k] || 0) + 1;
      sfDraw();
      const boxes = row.isConnected ? row.querySelectorAll('textarea[data-part="text"]')
        : document.querySelectorAll(`textarea[data-fk="${CSS.escape(c.key)}"][data-part="text"]`);
      if (boxes.length) boxes[boxes.length - 1].focus();
      return;
    }
    if (btn.dataset.act === 'psg-remove') {
      const list = sfPsgRead(row).filter((p, i) => i !== Number(btn.dataset.i));
      SF.psgAdd[k] = 0;
      if (!sfPassages(sfFieldValue(r, c).value).length) { sfDraw(); return; }
      sfFormSave(r.rec_id, c.key, list);
    }
  });
}

/* ── Set up the form ── */

/* Set up the form, on the line over the table at Extract and appraise, a card like Set columns that keeps
   each change as it is made and ends with Done: every field of his in the form's order, those in no
   section first and then each section under its heading, each with the one handle, its name, its type,
   where it shows, Remove, then its key, Not reported, its section and the Sift column it starts from, the
   field and values it is shown for, and a choice list's choices. A section's heading has the handle,
   its name and Remove, its fields joining the section before it. Add a field and Add a section at the
   foot. The same changes go through the form op the coordinator can call. */
function sfFcOpen() {
  if (!SF.table) return;
  sfFcDraw();
  $('sf-fc-name').value = '';
  $('sf-fc-type').value = 'text';
  $('sf-fc-options').value = '';
  $('sf-fc-options').hidden = true;
  $('sf-fc-sec-name').value = '';
  $('sf-fc').hidden = false;
}

function sfFcClose() {
  if (document.activeElement && $('sf-fc').contains(document.activeElement)) document.activeElement.blur();
  $('sf-fc').hidden = true;
}

const sfOpt = (value, words, on) => `<option value="${escAttr(value)}"${on ? ' selected' : ''}>${esc(words)}</option>`;

/* one field's row on the card */
function sfFcFieldHtml(c, own, sections) {
  const types = Object.keys(SF_FIELD_TYPES).map((t) => sfOpt(t, SF_FIELD_TYPES[t], t === c.type)).join('');
  const where = Object.keys(SF_WHERE_WORDS).map((w) => sfOpt(w, SF_WHERE_WORDS[w], w === c.where)).join('');
  const secs = [sfOpt('', t('sift.none'), !c.section), ...sections.map((s) => sfOpt(s, s, s === c.section))].join('');
  const from = SF_FROM_TYPES.includes(c.type)
    ? `<label class="sf-fc-pick">${esc(t('sift.fc.starts_from'))} <select data-act="from">${[sfOpt('', t('sift.fc.nothing'), !c.from),
      ...Object.keys(SF_FROM_WORDS).map((s) => sfOpt(s, SF_FROM_WORDS[s], s === c.from)),
      ...own.filter((o) => o.key !== c.key && o.type !== 'passages').map((o) => sfOpt(o.key, o.name, o.key === c.from))].join('')}</select></label>` : '';
  const ctls = own.filter((o) => o.key !== c.key && SF_COND_TYPES.includes(o.type));
  const ctl = c.when ? own.find((o) => o.key === c.when.key) : null;
  const pending = SF.fcWhen[c.key];
  const at = pending !== undefined ? own.find((o) => o.key === pending) || null : ctl;
  const values = at ? (at.type === 'yesno' ? Object.keys(SF_YES_NO) : at.options) : [];
  const ticked = at && ctl && at.key === ctl.key ? c.when.values : [];
  const when = ctls.length ? `<div class="sf-fc-line"><label class="sf-fc-pick">${esc(t('sift.fc.shown_when'))} <select data-act="when-key">`
    + `${[sfOpt('', t('sift.fc.always'), !at), ...ctls.map((o) => sfOpt(o.key, o.name, at && o.key === at.key))].join('')}</select></label>`
    + `${values.map((v) => `<label class="sf-fc-tick"><input type="checkbox" data-act="when-v" value="${escAttr(v)}"${ticked.includes(v) ? ' checked' : ''}>`
      + ` ${esc(at.type === 'yesno' ? SF_YES_NO[v] : v)}</label>`).join('')}</div>` : '';
  const opts = ['choice', 'multi'].includes(c.type)
    ? `<textarea class="sf-fc-opts" data-act="options" rows="2" aria-label="${escAttr(t('sift.choices'))}" spellcheck="false">${esc((c.options || []).join('\n'))}</textarea>` : '';
  return `<li class="sf-fc-field" data-key="${escAttr(c.key)}"><div class="sf-fc-line">${gripHtml(c.name)}`
    + `<input class="sf-col-name" type="text" data-act="name" value="${escAttr(c.name)}" aria-label="${escAttr(t('sift.name'))}" autocomplete="off" spellcheck="false">`
    // its type a select drawn as its row's others are, Shows on and Section, with the arrow that says it opens, where
    // it stood as a box with no arrow and read as a field holding the word Text (17 October, later)
    + `<label class="sf-fc-sel"><select data-act="type" aria-label="${escAttr(t('sift.type'))}">${types}</select></label>`
    + `<label class="sf-fc-pick">${esc(t('sift.fc.shows_on'))} <select data-act="where">${where}</select></label>`
    + `<button type="button" class="ghost small btn-remove" data-act="remove">${esc(t('sift.remove'))}</button></div>`
    + `<div class="sf-fc-line"><label class="sf-fc-pick">${esc(t('sift.fc.key'))} <input class="sf-fc-key" type="text" data-act="key" value="${escAttr(sfPlainKey(c.key))}"`
    + ' autocomplete="off" spellcheck="false"></label>'
    + `<label class="sf-fc-tick"><input type="checkbox" data-act="nr"${c.not_reported ? ' checked' : ''}> ${SF_NR_WORD}</label>`
    + `<label class="sf-fc-pick">${esc(t('sift.fc.section'))} <select data-act="section">${secs}</select></label>${from}</div>${when}${opts}</li>`;
}

/* The card's list: each section a row holding its fields, those in no section first with no heading */
function sfFcDraw() {
  const list = $('sf-fc-list');
  const own = sfOwnDefs();
  const sections = (SF.table && SF.table.sections) || [];
  const ordered = sfFormOrder(own, sections);
  const was = document.activeElement && list.contains(document.activeElement) ? document.activeElement : null;
  const holder = was ? was.closest('[data-key], [data-section]') : null;
  const mark = was ? [holder ? holder.dataset.key || holder.dataset.section || '' : '', was.dataset.act || '', was.value] : null;
  const group = (name) => ordered.filter((c) => (c.section || '') === name).map((c) => sfFcFieldHtml(c, own, sections)).join('');
  let html = `<li class="sf-fc-sec" data-section=""><ol class="sf-fc-fields">${group('')}</ol></li>`;
  sections.forEach((s) => {
    html += `<li class="sf-fc-sec" data-section="${escAttr(s)}" data-named="true"><div class="sf-fc-line sf-fc-head">${gripHtml(s)}`
      + `<input class="sf-col-name sf-fc-secname" type="text" data-act="sec-name" value="${escAttr(s)}" aria-label="${escAttr(t('sift.fc.section_heading'))}"`
      + ` autocomplete="off" spellcheck="false"><button type="button" class="ghost small btn-remove" data-act="sec-remove">${esc(t('sift.remove'))}</button></div>`
      + `<ol class="sf-fc-fields">${group(s)}</ol></li>`;
  });
  list.innerHTML = html;
  if (mark) {
    const back = [...list.querySelectorAll('[data-act]')].find((el) => {
      const holder = el.closest('[data-key], [data-section]');
      const id = holder ? holder.dataset.key || holder.dataset.section : '';
      return id === mark[0] && (el.dataset.act || '') === mark[1] && (el.type !== 'checkbox' || el.value === mark[2]);
    });
    if (back) back.focus();
  }
}

/* a change to the form's definition sent, the screening read again so every record carries it, a sort
   or a filter on a field following its new key, and the card drawn again */
async function sfFormDef(body) {
  let data;
  try {
    await SF.chain;
    data = await api('/api/sift', Object.assign({ op: 'form', folder: SF.folder }, body));
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    if (!$('sf-fc').hidden) sfFcDraw();
    return null;
  }
  const was = body.key;
  if (was && body.act === 'remove') {
    SF.sort = SF.sort.filter((s) => s.key !== was);
    delete SF.filters[was];
    delete SF.facetsFind[was];
  } else if (was && data.key && data.key !== was) {
    SF.sort = SF.sort.map((s) => (s.key === was ? { key: data.key, dir: s.dir } : s));
    if (was in SF.filters) { SF.filters[data.key] = SF.filters[was]; delete SF.filters[was]; }
    if (was in SF.facetsFind) { SF.facetsFind[data.key] = SF.facetsFind[was]; delete SF.facetsFind[was]; }
    if (was in SF.fcWhen) { SF.fcWhen[data.key] = SF.fcWhen[was]; delete SF.fcWhen[was]; }
  }
  if (data.table) SF.table = data.table;
  const r = sfRecord();
  await sfReload();
  sfApply(r ? r.rec_id : null);
  sfDraw();
  sfFiltersKeep();
  if (!$('sf-fc').hidden) sfFcDraw();
  return data;
}

const sfFcField = (key, field) => sfFormDef({ act: 'field', key, field });

/* the form's order as the card's rows now stand, sent whole: each section with its fields */
function sfFcOrder(rename) {
  const sections = [...$('sf-fc-list').querySelectorAll(':scope > li.sf-fc-sec')].map((li) => ({
    name: rename && rename[0] === li.dataset.section ? rename[1] : li.dataset.section,
    fields: [...li.querySelectorAll(':scope > ol > li.sf-fc-field')].map((f) => f.dataset.key),
  }));
  return sfFormDef({ act: 'order', sections });
}

/* the handle's `how` on the card's rows, a field among its section's and a section among the sections */
function sfFcGrip(li) {
  const field = li.classList.contains('sf-fc-field');
  return {
    rows: field ? ':scope > li.sf-fc-field' : ':scope > li.sf-fc-sec[data-named]',
    live: 'sf-fc-said',
    said: (row, to, n) => t('sift.grip.said', { name: field ? (sfOwnDefs().find((c) => c.key === row.dataset.key) || { name: '' }).name
      : row.dataset.section, at: to + 1, n }),
    moved: () => sfFcOrder(),
  };
}

async function sfFcAdd() {
  const name = $('sf-fc-name').value.trim();
  if (!name) { $('sf-fc-name').focus(); return; }
  const type = $('sf-fc-type').value in SF_FIELD_TYPES ? $('sf-fc-type').value : 'text';
  // a new field joins the last section, so a form is built from its head down
  const sections = (SF.table && SF.table.sections) || [];
  const field = { name, type, options: $('sf-fc-options').value, section: sections.length ? sections[sections.length - 1] : '' };
  const done = await sfFcField(null, field);
  if (!done) return;
  $('sf-fc-name').value = '';
  $('sf-fc-options').value = '';
  $('sf-fc-type').value = 'text';
  $('sf-fc-options').hidden = true;
  $('sf-fc-name').focus();
}

function sfFcSecAdd() {
  const name = $('sf-fc-sec-name').value.replace(/\s+/g, ' ').trim();
  if (!name) { $('sf-fc-sec-name').focus(); return; }
  if (((SF.table && SF.table.sections) || []).includes(name)) { say(t('sift.fc.section_there', { name })); return; }
  $('sf-fc-sec-name').value = '';
  $('sf-fc-list').insertAdjacentHTML('beforeend', `<li class="sf-fc-sec" data-section="${escAttr(name)}" data-named="true"><ol class="sf-fc-fields"></ol></li>`);
  sfFcOrder();
}

/* a field removed, asked first when a record holds a value in it, its values kept in the log */
async function sfFcRemove(key) {
  const c = sfOwnDefs().find((o) => o.key === key);
  if (!c) return;
  const held = SF.records.some((r) => String(((r.fields || {}).own || {})[key] || '').trim());
  if (held && !(await sfAsk(t('sift.fc.remove_head'), t('sift.cols.remove_line', { name: c.name }), t('sift.remove'), true))) return;
  await sfFormDef({ act: 'remove', key });
}

/* a section's heading removed, its fields joining the section before it */
function sfFcSecRemove(li) {
  const before = li.previousElementSibling;
  const into = before ? before.querySelector(':scope > ol') : null;
  if (into) li.querySelectorAll(':scope > ol > li.sf-fc-field').forEach((f) => into.appendChild(f));
  li.remove();
  sfFcOrder();
}

/* The card's keys: Alt and an arrow on a handle move its row, Esc closes the card, Enter in Add a field's
   name adds it, in Add a section's its heading, and in any other box leaves it */
function sfFcKey(e) {
  const t = e.target;
  const grip = t && t.closest && t.closest('#sf-fc-list button.pc-grip');
  if (grip) {
    const li = grip.closest('li');
    if (gripKeys(e, li, li.parentElement, sfFcGrip(li))) return;
  }
  if (e.key === 'Escape') { e.preventDefault(); sfFcClose(); return; }
  if (e.key !== 'Enter' || !t || t.tagName !== 'INPUT' || t.type !== 'text') return;
  e.preventDefault();
  if (t === $('sf-fc-name')) sfFcAdd();
  else if (t === $('sf-fc-sec-name')) sfFcSecAdd();
  else t.blur();
}

function sfFcBoot() {
  $('sf-form-set').onclick = sfFcOpen;
  $('sf-fc-close').onclick = sfFcClose;
  $('sf-fc-add').onclick = sfFcAdd;
  $('sf-fc-sec-add').onclick = sfFcSecAdd;
  $('sf-fc-type').onchange = () => { $('sf-fc-options').hidden = !['choice', 'multi'].includes($('sf-fc-type').value); };
  const list = $('sf-fc-list');
  const keyOf = (el) => { const li = el.closest('li.sf-fc-field'); return li ? li.dataset.key : ''; };
  list.addEventListener('pointerdown', (e) => {
    const grip = e.target.closest('button.pc-grip');
    if (!grip) return;
    const li = grip.closest('li');
    gripDrag(e, li, li.parentElement, sfFcGrip(li));
  });
  list.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-act]');
    if (!btn) return;
    if (btn.dataset.act === 'remove') sfFcRemove(keyOf(btn));
    else if (btn.dataset.act === 'sec-remove') sfFcSecRemove(btn.closest('li.sf-fc-sec'));
  });
  list.addEventListener('change', (e) => {
    const t = e.target;
    const key = keyOf(t);
    const c = sfOwnDefs().find((o) => o.key === key);
    if (!c) return;
    const act = t.dataset.act;
    if (act === 'type') sfFcField(key, { type: t.value });
    else if (act === 'where') sfFcField(key, { where: t.value });
    else if (act === 'nr') sfFcField(key, { not_reported: t.checked });
    else if (act === 'section') sfFcField(key, { section: t.value });
    else if (act === 'from') sfFcField(key, { from: t.value });
    else if (act === 'when-key') {
      // Always takes the condition off at once, and another field waits for a value of it to be ticked
      if (!t.value) { delete SF.fcWhen[key]; if (c.when) sfFcField(key, { when: null }); else sfFcDraw(); return; }
      SF.fcWhen[key] = t.value;
      sfFcDraw();
    } else if (act === 'when-v') {
      const li = t.closest('li.sf-fc-field');
      const values = [...li.querySelectorAll('[data-act="when-v"]')].filter((x) => x.checked).map((x) => x.value);
      const ctl = li.querySelector('[data-act="when-key"]').value;
      if (!values.length) { SF.fcWhen[key] = ctl; if (c.when) sfFcField(key, { when: null }); return; }
      delete SF.fcWhen[key];
      sfFcField(key, { when: { key: ctl, values } });
    }
  });
  list.addEventListener('focusout', (e) => {
    const t = e.target;
    const act = t.dataset.act;
    if (act === 'sec-name') {
      const li = t.closest('li.sf-fc-sec');
      const name = t.value.replace(/\s+/g, ' ').trim();
      if (!name) { t.value = li.dataset.section; return; }
      if (name !== li.dataset.section) sfFcOrder([li.dataset.section, name]);
      return;
    }
    const key = keyOf(t);
    const c = sfOwnDefs().find((o) => o.key === key);
    if (!c) return;
    if (act === 'name') {
      const name = t.value.trim();
      if (!name) t.value = c.name;
      else if (name !== c.name) sfFcField(key, { name });
    } else if (act === 'key') {
      const k = t.value.trim();
      if (!k) t.value = sfPlainKey(c.key);
      else if (k !== sfPlainKey(c.key)) sfFcField(key, { key: k });
    } else if (act === 'options') {
      const now = t.value.split('\n').map((s) => s.trim()).filter(Boolean);
      if (now.join('\n') !== (c.options || []).join('\n')) sfFcField(key, { options: t.value });
    }
  });
}

/* Export the form, in Export's menu: screening.form.csv beside the screening, a row for each record
   included at full text, `rec_id` and `study` first and then each field under its key */
async function sfFormExport() {
  try {
    const data = await api('/api/sift', { op: 'form', act: 'export', folder: SF.folder });
    if (!data.fields) { say(t('sift.fm.none_written')); return; }
    if (!data.written) { say(t('sift.none_included')); return; }
    say(t('sift.wrote_records', { n: data.records, files: data.file }));
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* ── the plan's terms (13 October, later) ── */

/* The terms of each block of the review's plan as Search strategy holds them now, a filter group for
   each block, Block 1 and its name, its terms as he wrote them, each with its count, and More than one.
   Which terms a record holds the server works out as it reads the screening (see `record_terms` in
   sift.py), so nothing is written and a plan edit is followed the next time the screening is read. Since
   14 October a record holding none of them stands under the lines that say how a database found it, from
   the fields each database searched (see `record_match`), worded so a reader understands them at once
   since 14 October, later. */

/* the terms of each block the record holds, under the record's facts, with Matched in and the fields
   they were found in beside them, and under Matched in, for each block it holds none of, one sentence
   after the block's name that says how a database found it (14 October, later) */
function sfTermsDraw(r) {
  const box = $('sf-terms');
  const held = r.terms || {};
  const blocks = SF.blocks || [];
  const rows = blocks.filter((b) => (held[b.key] || []).length).map((b) => {
    const m = sfMatched(r, b);
    const said = held[b.key].map((t) => `<span class="sf-cat">${esc(t)}</span>`).join('')
      + (m.in.length ? `<span class="sf-in">${esc(SF_COLS.matched.label)} ${esc(m.in.join(', '))}</span>` : '');
    return `<div><dt>${esc(b.label)}</dt><dd>${said}</dd></div>`;
  });
  const none = blocks.filter((b) => !(held[b.key] || []).length && sfMatched(r, b).said)
    .map((b) => `<span class="sf-why">${esc(`${b.label}: ${sfMatched(r, b).said}`)}</span>`);
  if (none.length) rows.push(`<div><dt>${esc(SF_COLS.matched.label)}</dt><dd>${none.join('')}</dd></div>`);
  box.innerHTML = rows.join('');
  box.hidden = !rows.length;
}

/* ── key excerpts ── */

/* His key excerpts (14 October, Adam's words): words of the record's title or abstract that support his
   decision, kept as `q` keeps a quote on Experiential statements and with its code, quote.js's
   `mergePieces` and `assembleQuote`. A selection in the title or abstract is a piece of the excerpt being
   built, marked until H keeps it, a selection with Cmd, Ctrl off a Mac, adding a piece and a plain one
   starting afresh. H joins the pieces in the text's own order with an ellipsis, never rearranged, the title's
   before the abstract's. Each excerpt is kept with the stage it was made at and its pieces' places, so its
   words are marked again whenever the record is drawn, in a mark of their own, and the list under the note
   holds them in the order made, each with Remove. Undo takes back the newest kept or removed. Nothing here is
   AI, so none of it follows the AI switch. */
// the title and the abstract as one text for quote.js, a character that is no space between them, so a piece
// of each is never joined into one
const SF_EX_GAP = '\u0000';
const SF_EX_SELECT = t('sift.ex.select');
// the stage an excerpt was made at, beside it when the screen stands at the other
const SF_EX_AT = { ta: t('sift.at_ta'), ft: t('sift.at_ft') };
const sfExText = (r) => `${r.title || ''}${SF_EX_GAP}${r.abstract || ''}`;
const sfExShift = (r, place) => (place === 'title' ? 0 : (r.title || '').length + SF_EX_GAP.length);
const sfExSpread = (r, pieces) => (pieces || []).map((p) => ({ start: p.start + sfExShift(r, p.in), end: p.end + sfExShift(r, p.in) }));

/* the pieces as quote.js leaves them, in the text's order, an overlap or a gap of spaces joined, each in its place */
function sfExMerged(r, pieces) {
  const at = sfExShift(r, 'abstract');
  return mergePieces(sfExSpread(r, pieces), sfExText(r))
    .map((m) => (m.start >= at ? { in: 'abstract', start: m.start - at, end: m.end - at } : { in: 'title', start: m.start, end: m.end }));
}

/* the words of the pieces joined with an ellipsis, as an excerpt keeps them, without the quotation marks */
const sfExWords = (r, pieces) => assembleQuote(sfExSpread(r, pieces), sfExText(r)).slice(1, -1);

/* the record's excerpts whose pieces still read as their words, the ones whose marks are drawn */
const sfExShown = (r) => (r.excerpts || []).filter((x) => sfExWords(r, x.pieces) === x.text);

/* The marks one place of the record takes beside the grounds: its key excerpts, hidden with the grounds by
   Hide, and the pieces of the one being built, which always show. */
function sfExSpans(r, place) {
  const mine = (list, cls) => list.filter((p) => p.in === place).map((p) => ({ start: p.start, end: p.end, cls }));
  return [...mine(SF.marksHidden ? [] : sfExShown(r).flatMap((x) => x.pieces), 'sf-excerpt'),
    ...mine(sfExMerged(r, SF.pieces), 'sf-piece')];
}

const sfTitleHtml = (r) => sfMarked(r.title || '', [], SF.form ? [] : sfExSpans(r, 'title'));
const sfAbstractHtml = (r, grounds) => sfMarked(r.abstract, grounds, sfExSpans(r, 'abstract'));

/* the title and the abstract drawn again with their marks, while a piece is taken or the pieces let go */
function sfExPaint(r) {
  if (!r || !$('sf-title-text')) return;
  $('sf-title-text').innerHTML = sfTitleHtml(r);
  if (r.abstract) $('sf-abstract').innerHTML = sfAbstractHtml(r, SF.marksHidden ? [] : sfMarks(sfSuggestions(sfStage(r))));
}

/* The words selected in the title or the abstract as a piece, { in, start, end }, its spaces at either end
   left out, or null for a selection anywhere else or one across the two. */
function sfExSelection(r) {
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount || sel.isCollapsed) return null;
  const range = sel.getRangeAt(0);
  for (const [place, id] of [['title', 'sf-title-text'], ['abstract', 'sf-abstract']]) {
    const box = $(id);
    const text = r[place] || '';
    if (!box || !text || !box.contains(range.commonAncestorContainer)) continue;
    const before = range.cloneRange();
    before.selectNodeContents(box);
    before.setEnd(range.startContainer, range.startOffset);
    let start = before.toString().length;
    let end = Math.min(text.length, start + range.toString().length);
    while (start < end && /\s/.test(text[start])) start += 1;
    while (end > start && /\s/.test(text[end - 1])) end -= 1;
    return end > start ? { in: place, start, end } : null;
  }
  return null;
}

/* The selection taken as a piece, added to the pieces with Cmd or Ctrl held and else in their place, the
   marks drawn again and the selection put back over them. False when nothing in the title or abstract is
   selected. */
function sfExTake(add) {
  const r = sfRecord();
  const piece = r && SF.view === 'record' && !SF.form ? sfExSelection(r) : null;
  if (!piece) return false;
  SF.pieces = add ? [...SF.pieces, piece] : [piece];
  SF.piecesFor = r.rec_id;
  sfExPaint(r);
  restoreSelection($(piece.in === 'title' ? 'sf-title-text' : 'sf-abstract'), piece.start, piece.end);
  return true;
}

/* the pieces let go, by a plain click on the text or Esc */
function sfExClear() {
  SF.pieces = [];
  try { window.getSelection().removeAllRanges(); } catch { /* nothing selected */ }
  sfExPaint(sfRecord());
}

/* H: the pieces, or the words selected, kept as one key excerpt made at the stage on the screen, after the
   record's others, drawn at once and the server's answer drawn over it as it lands */
function sfExKeep() {
  const r = sfRecord();
  if (!r || SF.form || SF.view !== 'record') return;
  if (!SF.pieces.length && !sfExTake(false)) { say(SF_EX_SELECT); return; }
  const pieces = sfExMerged(r, SF.pieces);
  const text = sfExWords(r, pieces);
  if (!text) { say(SF_EX_SELECT); return; }
  const stage = SF.stage;
  r.excerpts = [...(r.excerpts || []), { stage, text, pieces }];
  sfExClear();
  sfDraw();
  say(t('sift.ex.added'), 2200);
  sfExSend({ act: 'add', rec_id: r.rec_id, stage, pieces });
}

/* Remove on an excerpt of the list, `i` its place, its words sent with it so a list that changed refuses */
function sfExRemove(i) {
  const r = sfRecord();
  const x = r ? (r.excerpts || [])[i] : null;
  if (!x) return;
  r.excerpts = r.excerpts.filter((_, k) => k !== i);
  sfDraw();
  sfExSend({ act: 'remove', rec_id: r.rec_id, at: i, text: x.text });
}

/* an excerpt's act sent to the server in turn with the decisions, the screening read again should it refuse */
function sfExSend(body) {
  sfQueue(async () => {
    try {
      sfLand(await api('/api/sift', { op: 'excerpt', folder: SF.folder, ...body }));
    } catch (err) {
      say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
      await sfReload();
      return;
    }
    sfDraw();
  });
}

/* The list under the note, Key excerpts, each excerpt in quotation marks in the order made, the stage it was
   made at beside one made at the other stage, and Remove. */
function sfExList(r) {
  const list = r.excerpts || [];
  $('sf-ex-list').innerHTML = list.map((x, i) => `<li class="sf-ex"><q class="sf-ex-words">${esc(x.text)}</q>`
    + (x.stage !== SF.stage && SF_EX_AT[x.stage] ? `<span class="sf-ex-stage">${SF_EX_AT[x.stage]}</span>` : '')
    + `<button type="button" class="ghost small btn-remove sf-ex-remove" data-ex="${i}" aria-label="${escAttr(t('sift.ex.remove_label', { i: i + 1 }))}">${esc(t('sift.remove'))}</button></li>`).join('');
  $('sf-ex-list').hidden = !list.length;
}

/* ── keys ── */

/* Sift's keys, on its screen alone, ahead of every other screen's, which hear none of them. In the
   note and his fields every key types, and Esc or Cmd + Enter leave them, keeping what is typed, as
   Enter does in a field of one line. A card open over the screen takes Esc, and the question card
   Enter too. Cmd or Ctrl with any key but Z goes by untouched, so the browser's own find works on
   the table as on any page. Settings opened over the screen keeps its own keys. */
function sfKeyDown(e) {
  if (!sfShown() || !$('settings').hidden || !$('feedback').hidden) return;
  // Search's card over the screen keeps its own keys (18 October, search.js)
  if (e.target && e.target.closest && e.target.closest('.search-card')) return;
  e.stopPropagation();
  // Export's menu takes its own keys, and Enter or a space presses the item with the focus
  if (sfMenuKey(e)) return;
  if (!$('sf-keys').hidden) {
    if (e.key === 'Escape' || e.key === '?') { e.preventDefault(); $('sf-keys').hidden = true; }
    return;
  }
  if (!$('sf-ask').hidden) {
    if (e.key === 'Escape' || e.key === 'Enter') { e.preventDefault(); if (SF.askDone) SF.askDone(e.key === 'Enter'); }
    return;
  }
  if (!$('sf-zot').hidden) {
    if (e.key === 'Escape') { e.preventDefault(); sfZotClose(); }
    return;
  }
  // the map over the screen takes Esc, and Tab goes on through its circles and buttons
  if (!$('sf-map').hidden) {
    if (e.key === 'Escape') { e.preventDefault(); sfMapClose(); }
    return;
  }
  if (!$('sf-two').hidden) {
    if (e.key === 'Escape') { e.preventDefault(); sfTwoClose(); }
    return;
  }
  if (!$('sf-cols').hidden) {
    sfColsKey(e);
    return;
  }
  if (!$('sf-fc').hidden) {
    sfFcKey(e);
    return;
  }
  if (!$('toast').hidden && e.key === 'Escape') $('toast').hidden = true;
  // a handle on a track by bars moves a bar a press, as dragging it does
  if (sfHandleKey(e)) return;
  // and a sidebar's edge, the filters' or the flow's, a step a press
  if (sfEdgeKey(e)) return;
  // a tick box of the filters types nothing, so Sift's keys go on working from it
  const typing = e.target && e.target.closest && e.target.closest('textarea, input:not([type="checkbox"]), select');
  if (typing) {
    // Enter in Same study as's box links the record named, as its button does
    if (e.key === 'Enter' && e.target.id === 'sf-study-id') { e.preventDefault(); sfStudyAs(); return; }
    // Esc in a find box that holds words empties it, and the filters' boxes leave as every field does
    if (e.key === 'Escape' && e.target.dataset.act === 'find' && e.target.value) { e.preventDefault(); sfFind(e.target, ''); return; }
    const field = e.target === $('sf-note') || e.target.classList.contains('sf-field') || !!e.target.closest('#sf-facets, #sf-form');
    const line = e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT';
    if (field && (e.key === 'Escape' || (e.key === 'Enter' && (MOD(e) || line)))) { e.preventDefault(); e.target.blur(); }
    else if (e.target.tagName === 'SELECT' && e.key === 'Escape') e.target.blur();
    return;
  }
  // at Extract and appraise no key decides, notes or undoes, so the decisions stay as full text left them
  if (SF.form) {
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    if (MOD(e) && k === 'z') { e.preventDefault(); return; }
    if (!MOD(e) && !e.altKey && ['y', 'm', 'n', 'i', 'e', 'a', 'r', 'u', 't', 'h'].includes(k)) { e.preventDefault(); return; }
    if (SF.view === 'record' && k === 'Enter' && !(e.target && e.target.tagName === 'BUTTON')) { e.preventDefault(); return; }
  }
  if (MOD(e) && (e.key === 'z' || e.key === 'Z') && !e.shiftKey) { e.preventDefault(); sfUndo(); return; }
  // Enter or a space on a button of the title bar or the strip over the table with the focus presses
  // that button, Export among them, but while the reasons stand open, where Enter takes the reason chosen
  if (!SF.picking && (e.key === 'Enter' || e.key === ' ') && e.target && e.target.tagName === 'BUTTON'
    && e.target.closest('.sf-rail, .sf-tv-top')) return;
  if (MOD(e) || e.altKey || e.ctrlKey) return;
  const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  // at phone width the flow stands over the screen, and Esc shuts it first
  if (!SF.picking && key === 'Escape' && !$('sf-side').hidden && sfNarrow()) { e.preventDefault(); sfFlowOpen(false); return; }
  // and the filters, which stand over the table there too
  if (!SF.picking && key === 'Escape' && SF.view === 'table' && !$('sf-facets').hidden && sfNarrow()) {
    e.preventDefault();
    sfFacetsOpen(false);
    return;
  }
  if (!SF.picking && SF.view === 'table') {
    if (key === 'ArrowDown' || key === 'ArrowUp') { e.preventDefault(); sfMove(key === 'ArrowDown' ? 1 : -1); return; }
    if (key === 'Enter') { e.preventDefault(); sfOpenRecord(); return; }
    if (['t', 'p', 'ArrowLeft', 'ArrowRight'].includes(key)) return;
  }
  // Esc on a record lets the pieces of a key excerpt go first, then goes back to the table
  if (!SF.picking && SF.view === 'record' && key === 'Escape' && SF.pieces.length) { e.preventDefault(); sfExClear(); return; }
  if (!SF.picking && SF.view === 'record' && key === 'Escape') { e.preventDefault(); sfToTable(); return; }
  if (SF.picking) {
    const codes = sfCodes();
    const choices = sfReasonChoices();
    // No reason, 0, at title and abstract, where a reason is optional
    if (key === '0' && choices.length > codes.length) { e.preventDefault(); sfDecide('exclude', '', true); return; }
    if (/^[1-9]$/.test(key) && Number(key) <= codes.length) { e.preventDefault(); sfDecide('exclude', codes[Number(key) - 1].code, true); return; }
    if (key === 'Enter') { e.preventDefault(); if (SF.pick >= 0) sfDecide('exclude', choices[SF.pick].code, true); return; }
    if (key === 'ArrowDown' || key === 'ArrowUp') {
      e.preventDefault();
      const down = key === 'ArrowDown';
      SF.pick = SF.pick < 0 ? (down ? 0 : choices.length - 1) : (SF.pick + (down ? 1 : choices.length - 1)) % choices.length;
      sfReasonsDraw();
      return;
    }
    if (key === 'Escape' || sfKeyDecision(key, SF.stage) === 'exclude') { e.preventDefault(); sfPicking(false); return; }
  }
  // the stage's keys, Y, M and N or I, M and E, and the old A and R at both (see SF_KEYS)
  const decision = sfKeyDecision(key, SF.stage);
  if (decision === 'exclude') { e.preventDefault(); if (sfCodes().length) sfPicking(true); else sfDecide('exclude'); }
  else if (decision) { e.preventDefault(); sfDecide(decision); }
  else if (key === 'Enter') { e.preventDefault(); sfTakeProposal(); }
  else if (key === 'ArrowLeft') { e.preventDefault(); sfMove(-1); }
  else if (key === 'ArrowRight') { e.preventDefault(); sfMove(1); }
  else if (key === 'u') { e.preventDefault(); sfUndo(); }
  // the note on T since 12 October, later, N being No at title and abstract
  else if (key === 't') { e.preventDefault(); $('sf-note').focus(); }
  else if (key === 'p') { e.preventDefault(); sfPdfShut(!$('sf-body').classList.contains('pdf-shut')); }
  // H keeps a key excerpt on a record, never while the reasons stand open (14 October)
  else if (key === 'h' && SF.view === 'record' && !SF.picking) { e.preventDefault(); sfExKeep(); }
  else if (key === '?' || (e.shiftKey && key === '/')) { e.preventDefault(); sfKeysOpen(); }
}

function sfBoot() {
  // the lockup goes home (option C of the bars, 26 October 2026, where the back arrow stood, the path's Home gone
  // since option D, 6 November 2026), and the path's project opens its menu, its card's on Home (barsD)
  $('sf-home').onclick = () => sfBack();
  bandMenuWire('sf-name', () => siftBandMenu());
  // and the way back to the table from a record, the link before the name (sifttable, 8 November 2026)
  bandTableWire('sf-name', { word: t('sift.band.table'), away: () => SF.view === 'record', go: () => sfToTable() });
  window.addEventListener('popstate', sfPopState);
  // the second press of a double-click on a row, out of habit, lands on the record the first opened,
  // and does nothing there
  ['mousedown', 'click'].forEach((type) => $('sf-body').addEventListener(type, (e) => {
    if (SF.openedAt && Date.now() - SF.openedAt < SF_SECOND_PRESS) { e.preventDefault(); e.stopPropagation(); }
  }, true));
  $('sf-flow-toggle').onclick = () => sfFlowOpen($('sf-side').hidden);
  $('sf-side-close').onclick = () => sfFlowOpen(false);
  $('sf-gline-btn').onclick = () => sfMarksHide(!SF.marksHidden);
  // a piece of a key excerpt is taken on mouse up, after the browser has settled the selection, and a plain
  // click on the title or abstract that selects nothing lets the pieces go (14 October)
  $('sf-card').addEventListener('mousedown', (e) => { SF.exPress = { x: e.clientX, y: e.clientY }; });
  $('sf-card').addEventListener('mouseup', (e) => {
    if (e.button !== 0) return;
    const add = MOD(e);
    const held = e.metaKey || e.ctrlKey || e.shiftKey || e.altKey;
    const moved = !!SF.exPress && (Math.abs(e.clientX - SF.exPress.x) > 4 || Math.abs(e.clientY - SF.exPress.y) > 4);
    const onText = !!e.target.closest('#sf-title-text, #sf-abstract');
    setTimeout(() => {
      if (!sfExTake(add) && onText && !held && !moved && SF.pieces.length) sfExClear();
    }, 0);
  });
  $('sf-ex-list').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-ex]');
    if (b) sfExRemove(Number(b.dataset.ex));
  });
  // Add PDF, in the record's links alone, where its empty PDF pane held a second until 17 October
  $('sf-links').addEventListener('click', (e) => { if (e.target.closest('[data-act="add-pdf"]')) sfPdfChoose(); });
  $('sf-pdf-file').addEventListener('change', () => {
    const file = $('sf-pdf-file').files && $('sf-pdf-file').files[0];
    if (file) sfDropPdf(file);
  });
  // a press beside the reasons cancels them, as Esc does
  $('sf-why').addEventListener('click', (e) => { if (e.target === $('sf-why')) sfPicking(false); });
  // Find open-access PDFs, Find citation counts and the bench, under Sift in Settings
  $('sf-oa-go').onclick = sfOaRun;
  $('sf-fill-go').onclick = sfFillRun;
  // Same study, Unlink and Same study as on the record (13 October)
  $('sf-study').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-study]');
    const r = sfRecord();
    if (!b || !r) return;
    if (b.dataset.study === 'unlink') sfStudy('unlink', r.rec_id);
    else if (b.dataset.study === 'link') sfStudy('link', r.rec_id, b.dataset.with);
    else sfStudyAs();
  });
  $('sf-oa-email').addEventListener('change', sfEmailSave);
  $('sf-bench-rec').onchange = () => { $('sf-bench-out').hidden = true; sfBenchCost(); };
  $('sf-bench-try').insertAdjacentHTML('afterbegin', TB_SPARKS);
  $('sf-bench-try').onclick = sfBenchTry;
  sfTvBoot();
  sfFieldsBoot();
  sfColsBoot();
  sfFcBoot();
  sfMapBoot();
  // the form's controls on the record and among his fields under the record (13 October, later)
  sfFormBoot($('sf-form'));
  sfFormBoot($('sf-f-form'));
  $('sf-form-export').onclick = () => sfMenuTake(sfFormExport);
  $('sf-acts').querySelectorAll('.sf-act').forEach((b) => {
    b.onclick = () => (b.dataset.decision === 'exclude' ? (SF.picking ? sfPicking(false) : sfDecide('exclude')) : sfDecide(b.dataset.decision));
  });
  $('sf-note').addEventListener('blur', sfNoteSave);
  // Export's menu: the button opens and shuts it, and each item shuts it as it starts its work
  $('sf-export').onclick = () => sfMenuOpen($('sf-export-menu').hidden);
  $('sf-counts').onclick = () => sfMenuTake(sfExport);
  $('sf-included').onclick = () => sfMenuTake(sfIncluded);
  $('sf-zotero').onclick = () => sfMenuTake(sfZotOpen);
  document.addEventListener('pointerdown', (e) => {
    if (!$('sf-export-menu').hidden && !e.target.closest('#sf-export-menu, #sf-export')) sfMenuOpen(false, false);
  }, true);
  window.addEventListener('resize', () => { if (!$('sf-export-menu').hidden) sfMenuOpen(false, false); });
  $('sf-undo').onclick = () => sfUndo();
  $('sf-reset').onclick = sfReset;
  $('sf-pdf-toggle').onclick = () => sfPdfShut(!$('sf-body').classList.contains('pdf-shut'));
  $('sf-help').onclick = sfKeysOpen;
  $('sf-keys-close').onclick = () => { $('sf-keys').hidden = true; };
  // the shortcuts card's keys, and H's line, as this machine names them, Cmd or Ctrl, through keyName as on
  // the statements screen and Trace's card (17 October)
  for (const el of document.querySelectorAll('#sf-keys .keys td')) el.textContent = keyName(el.textContent);
  $('sf-feedback').onclick = () => openFeedback('sift');
  $('sf-settings').onclick = () => openSettings('sift');
  // Export to Zotero: the card, its choice of records, Export and the way out
  $('sf-zot-close').onclick = sfZotClose;
  $('sf-zot-cancel').onclick = sfZotClose;
  $('sf-zot-go').onclick = sfZotGo;
  $('sf-zot-which').addEventListener('change', sfZotPlan);
  // the second screener: the card, its workbooks, a returned one chosen, and the record's outcomes
  $('sf-two-btn').onclick = sfTwoOpen;
  $('sf-two-close').onclick = sfTwoClose;
  $('sf-two-make').onclick = sfTwoMake;
  $('sf-two-diff').onclick = sfTwoDifferences;
  $('sf-two-take').onclick = sfTwoChoose;
  $('sf-two-file').addEventListener('change', () => {
    const file = $('sf-two-file').files && $('sf-two-file').files[0];
    if (file) sfTwoTakeFile(file);
  });
  $('sf-two-body').addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]');
    if (!b) return;
    if (b.dataset.act === 'further') sfTwoFurther();
    else if (b.dataset.act === 'apart') {
      // Where we differ, the Decision filter's tick of its own, the rest of the filter let go
      sfTwoClose();
      SF.filters.decision = [SF_APART];
      if ($('sf-facets').hidden && !sfFacetsNarrow()) sfFacetsOpen(true);
      sfRefilter();
    }
  });
  $('sf-two-rec').addEventListener('click', (e) => {
    const b = e.target.closest('[data-out]');
    if (b) sfTwoOutcome(b.dataset.out, b.dataset.decision || undefined);
  });
  $('sf-ask-yes').onclick = () => { if (SF.askDone) SF.askDone(true); };
  $('sf-ask-no').onclick = () => { if (SF.askDone) SF.askDone(false); };
  $('sf-ai-one').insertAdjacentHTML('afterbegin', TB_SPARKS);
  $('sf-ai-all').insertAdjacentHTML('afterbegin', TB_SPARKS);
  // the sparkles on each suggestion box's title, shown for an AI's alone (see sfDraw), and its Accept suggestion
  $('sf-prop-spark').insertAdjacentHTML('afterbegin', TB_SPARKS);
  $('sf-prop-spark-2').insertAdjacentHTML('afterbegin', TB_SPARKS);
  $('sf-take').onclick = () => sfTakeProposal(0);
  $('sf-take-2').onclick = () => sfTakeProposal(1);
  $('sf-ai-one').onclick = sfAiOne;
  $('sf-ai-all').onclick = sfAiAll;
  window.addEventListener('keydown', sfKeyDown, true);
  window.addEventListener('focus', sfFresh);
  window.addEventListener('dragenter', sfDrag);
  window.addEventListener('dragover', sfDrag);
  window.addEventListener('dragleave', sfDragEnd);
  window.addEventListener('dragend', sfDragEnd);
  window.addEventListener('drop', sfDrop);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) sfFresh(); });
  try {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (sfShown()) sfFlow(); });
    // and a choice under Settings, General, Appearance, the flow drawn again in its colours
    document.addEventListener('idiograph-theme', () => { if (sfShown()) sfFlow(); });
  } catch { /* an older browser */ }
}

/* ── Search (the family codebase's third build, 22 October 2026, from search.js) ── */

/* Search's place on Sift's screen, its menus put away as Search's card opens, and its leaving, its acts and
   the words of a find box kept first, each through `FAMILY_APPS.sift` (sift_settings.js) */
const sfSearchWhere = () => (searchShown('sift') && SF.folder ? { screen: 'sift', folder: SF.folder } : null);

async function sfSearchLeave() {
  if (searchShown('sift')) await new Promise((done) => sfLeave(done));
  return true;
}

/* A Sift result: the screening opened at the record's stage, Title and abstract, Full text or Extract and
   appraise, on the screen already when it is the one open, and there the record opened, its title, its
   abstract, its authors or its journal brought into view, the caret in its decision note or the field, or
   its key excerpt marked under the find's yellow in the list under the note. A record the table's filters
   leave out stands among the rows in the table's order until the filters next change, so he lands on it
   with nothing of his changed. */
async function searchToSift(go) {
  const here = SEARCH.here;
  const same = here && here.screen === 'sift' && searchShown('sift') && SF.folder === go.folder;
  if (same) {
    if ((SF.form ? 'ex' : SF.stage) !== go.stage) await sfStageTo(go.stage);
  } else {
    if (!(await searchLeaveFor(here))) return;
    await siftOpen(go.folder, null, go.stage);
    if (!searchShown('sift')) return;
  }
  if (!searchSiftRecord(go.rec)) { say(SEARCH_GONE, 6000); return; }
  searchSiftField(go);
}

/* the record opened among the stage's rows, put among the rows the filters show where they leave it out */
function searchSiftRecord(rec) {
  if (!SF.byId.has(rec) || !SF.roundIds.includes(rec)) return false;
  if (!SF.ids.includes(rec)) {
    const keep = new Set([...SF.ids, rec]);
    SF.ids = tbSortRows(SF.roundIds, SF.byId, SF.sort, sfAllCols(), sfRead(SF.stage)).filter((id) => keep.has(id));
    SF.tvShape = '';
  }
  SF.at = SF.ids.indexOf(rec);
  SF.picking = false;
  SF.tvReveal = true;
  if (SF.view === 'record') sfDraw();
  else sfOpenRecord();
  return SF.view === 'record';
}

/* where on the record a Sift result lands: the part in view, the caret in the note or the field, the
   excerpt marked */
function searchSiftField(go) {
  const r = sfRecord();
  const field = String(go.field || '');
  if (!r || r.rec_id !== go.rec || !field) return;
  const parts = { title: 'sf-title', authors: 'sf-authors', journal: 'sf-meta', abstract: 'sf-abstract' };
  if (parts[field]) { $(parts[field]).scrollIntoView({ block: 'nearest' }); return; }
  if (field === 'note') { if (!SF.form) $('sf-note').focus(); return; }
  if (field === 'excerpt') {
    const one = $('sf-ex-list').children[Number(go.line) || 0];
    if (one) { one.classList.add('search-lit'); one.scrollIntoView({ block: 'nearest' }); }
    return;
  }
  if (!/^[\w-]+$/.test(field)) return;
  const row = go.form && SF.form ? $('sf-form').querySelector(`.sf-fm-row[data-fk="${field}"]`) : null;
  const el = row ? row.querySelector('input, select, textarea')
    : $('sf-fields').querySelector(`[data-field="${field}"], [data-fk="${field}"]:not(.sf-fm-row)`);
  if (el) el.focus();
  else if (row) row.scrollIntoView({ block: 'nearest' });
}

sfBoot();
