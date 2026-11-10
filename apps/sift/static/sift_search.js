/* Sift's Search strategy, PRISMA-S's name for it, the review's first step, on a screen of its own in
   one column in the order of the work (12 October, later): Plan, the question, the search terms in
   blocks, Block 1 and up, the limits and restrictions, the databases, the benchmark papers, the key
   works and the exclusion reasons, under one tag that says Draft or Registered, then Searches, a row for each
   database with how it runs and its search beside it, then Register, with Export search_plan.md and
   Mark as registered, then Search runs, a table of the runs made, newest first, and New run under it.
   The review's steps at the head of both its screens, and the way a review opens from its row on the
   home screen, are here too. No framework, no build step.

   The server reads and writes the plan through sift_search.py. This holds the plan as the fields
   have it and saves it a moment after each change, so there is nothing to save by hand, and the
   exclusion reasons the same way into the review's reasons.csv. An edit after a version is marked as
   registered becomes a draft of the next version on the server, which needs its reason before it is
   registered or run. Runs made before registering are trials, and a run of a registered version is
   the registered search. A run goes on the server's own thread, and this asks after it until it ends,
   drawing each database's state as it goes. Start new run always makes a new run, every run kept and
   numbered in the order made, Run 1 up. An export dropped on a database's row goes to the day's newest
   run, the one waiting on exports, and that run is written afresh with it. Since 14 October a phrase
   holding truncation keeps the plan unsaved and unrun, Rewrites under each search says what Sift
   changed for that database, and Check truncation under New run shows the dry run's counts. */

'use strict';

const SFS = {
  folder: null,      // the review folder open, as the server names it back
  name: '',
  review: null,      // the review, for its steps, as the server names it
  stages: null,      // its screening's count of records at each stage, for the steps, once asked
  data: null,        // the server's last answer: versions, strings, problems, runs
  plan: null,        // the plan as the fields hold it
  stale: null,       // a save refused since the plan changed in another window, { version, reasons }, until Reload or Overwrite
  reason: '',        // the reason for a draft's changes, as its field holds it
  catalog: null,     // the databases, their names, the scopes and the document types, from the server
  how: {},           // each database by API or by export
  listed: [],        // his own list of databases from Settings, in its order
  acc: null,         // each database's access as its cog draws it: the keys saved and the lines said
  accOpen: null,     // the database whose cog is open
  adding: false,     // Add database's name field shown
  titles: {},        // each benchmark DOI's title, where the plan or a run knows it
  keys: {},          // whether each keyed database has its key saved, never the key
  benchRows: null,   // the benchmark papers' DOIs as their boxes hold them
  finding: {},       // the DOIs whose title is being asked of OpenAlex
  notFound: {},      // the DOIs OpenAlex gave no title for
  keyWorks: [],      // the review's key works, kept beside the plan's versions, never in one (13 October)
  kwPicks: null,     // the works OpenAlex offers for a title being added, { text, year, works, said }
  kwAdding: false,   // Add a key work's line shown
  reasons: null,     // the exclusion reasons as their rows hold them
  reasonTimer: null,
  open: new Set(),   // the disclosures open, Earlier versions and each run's Details by `run:<folder>`
  ownOpen: new WeakSet(),  // the blocks whose Search in, by database stands open
  today: '',
  runs: [],
  running: null,     // a run under way, as the server says it
  follows: null,     // the earlier run the next run follows, a day or none, the newest with decisions at first
  terms: null,       // the last Check truncation's table, until the plan changes (14 October)
  checking: false,   // Check truncation asking the databases
  saveTimer: null,
  chain: Promise.resolve(),   // the saves in the order they were made
  poll: null,
  askDone: null,
};

const sfsShown = () => !!$('sift-search') && !$('sift-search').hidden;
// a database the plan names, `other`, then `other2` and up
const sfsIsOther = (s) => /^other(?:[2-9]|1\d|20)?$/.test(String(s || ''));
const sfsName = (s) => (sfsIsOther(s) ? (SFS.plan && (SFS.plan.others || {})[s]) || t('sift_search.other_database')
  : (SFS.catalog && SFS.catalog.names[s]) || s);

/* ── the review ── */

/* A review is one thing, its search strategy and then its screening, in PRISMA 2020's order, and its
   steps stand at the head of either screen. From its row it opens on the step it was left on, which
   this browser keeps, else on Search strategy until a run has a screening and on Screening after. A
   review with no searches has Screening alone. Screening opens the run whose screening he opened
   last, which the server keeps in its list of reviews, until he opens another from the runs on
   Search strategy, and for a review he has never opened a run of, its newest run with a screening. */
const RV_STEP_KEY = 'idiograph-sift-step';

function rvSteps() {
  try {
    const held = JSON.parse(localStorage.getItem(RV_STEP_KEY) || '{}');
    return held && typeof held === 'object' ? held : {};
  } catch { return {}; }
}

function rvKeepStep(folder, step) {
  try {
    const held = rvSteps();
    held[folder] = step;
    localStorage.setItem(RV_STEP_KEY, JSON.stringify(held));
  } catch { /* private window */ }
}

/* the step a review opens on, from the step it was left on, `kept`, and whether it has a screening. Check
   references, a step from 14 October that is Trace's since 15 October, opens Search strategy or Screening */
function rvStepOf(review, kept) {
  if (!review.searches) return 'screening';
  if (kept === 'searches') return 'searches';
  return review.screening ? 'screening' : 'searches';
}

/* a review's row on the home screen, asked of the server and opened on its step */
async function rvOpen(folder) {
  let got;
  try {
    got = await api('/api/sift-review', { op: 'read', folder });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  rvShow(got.review);
}

function rvShow(review) {
  if (!review) return;
  const step = rvStepOf(review, rvSteps()[review.folder]);
  if (step === 'screening') siftOpen(review.screening);
  else sfsOpen(review.folder);
}

/* The review's name and its steps at the head of the screen of `step`, the step kept for the next
   opening. A screening a run holds names the run in the name's title, by its number and its day,
   and a run of a draft says it was not registered. On Screening the screen draws the steps
   itself, at its stage and with its counts (see sfBar). */
function rvHead(step, review) {
  const name = $(step === 'screening' ? 'sf-name' : 'sfs-name');
  const box = $(step === 'screening' ? 'sf-steps' : 'sfs-steps');
  if (!name || !box) return;
  box.hidden = !review;
  // the project's research question heads the plan on Search strategy (12 October)
  const question = step === 'searches' ? $('sfs-question') : null;
  if (question) {
    question.textContent = (review && review.question) || '';
    question.hidden = !(review && review.question);
    // the band under the bar says the question since option C of the bars (26 October 2026), so the plan's own
    // part stays put away rather than say it a second time
    if ($('sfs-question-part')) $('sfs-question-part').hidden = question.hidden || !!$('sfs-band');
  }
  // and since option C of the bars (26 October 2026) the band under the bar on both screens, the path then the
  // question
  const band = $(step === 'screening' ? 'sf-band' : 'sfs-band');
  if (band && band.classList && band.querySelector) {
    const q = (review && review.question) || '';
    band.classList.toggle('band-unasked', !q);
    band.querySelector('.band-question').textContent = q;
  }
  if (!review) return;
  bandNameSet(name.id, review.name, review.run ? t('sift_search.name_run', { name: review.name, run: review.label || t('sift_search.run_of', { day: sfsDay(review.run) }) })
    : review.name);
  rvKeepStep(review.folder, step);
  if (step === 'searches') rvStepsDraw(box, review, step, SFS.stages);
}

/* The review's steps, one row in the order the work goes (12 October): Search strategy, then the
   screening's two stages, each named with its verb, Screen by title and abstract and Screen by full
   text, each stage with its count of records where `counts` knows it, then Extract and appraise with the
   count of records included at full text (13 October, later), and the one he is on, `step`, searches, ta,
   ft or ex, marked. A review with no searches has the stages alone. Screen by title and abstract waits
   for a run with a screening, and Screen by full text for a record with Yes or Maybe at title and
   abstract, each greyed until then with its reason on hover, still reached by the keys. Extract and
   appraise opens with the screening, so the form can be piloted on the benchmark papers before any paper
   is included. Check references, which stood last from 14 October, is Trace's own part since 15 October.
   The row is built again only when it changes, so the step with the focus keeps it. */
const RV_TA_LATER = t('sift_search.steps.ta_later');
const RV_FT_LATER = t('sift_search.steps.ft_later');
// the stage after full text, its name in this one place for every screen and line of the page
const RV_FORM_NAME = t('sift_search.steps.ex');
const RV_EX_LATER = t('sift_search.steps.ex_later');
const RV_DRAWN = new WeakMap();

function rvStepsHtml(review, step, counts) {
  const n = (s) => (s === 'ex' ? (counts && counts.ft ? Number(counts.ft.include) || 0 : null)
    : counts && counts[s] ? Number(counts[s].records) || 0 : null);
  // on Search strategy a run of its own may hold a screening
  const ta = step !== 'searches' || !!(review && review.screening)
    || (step === 'searches' && SFS.runs.some((r) => r.screening));
  const ft = step === 'ft' || step === 'ex' || (ta && n('ft') > 0);
  // each step's words over a hidden bold copy of themselves, so the step in front, in bold, is no wider than it is
  // behind and the row never moves (barsD, Adam, 6 November 2026, the tabs' own rule, style.css .tab-w)
  const one = (s, words, ready, wait) => `<button type="button" data-step="${s}"${s === step ? ' aria-current="step"' : ''}`
    + `${ready ? '' : ` aria-disabled="true" title="${wait}"`}><span class="tab-w" data-bold="${String(words).replace(/"/g, '&quot;')}">${words}</span>`
    + `${n(s) === null ? '' : ` <span class="sf-step-c">${n(s)}</span>`}</button>`;
  const sep = '<span class="sf-step-sep" aria-hidden="true">&#8250;</span>';
  return (review && review.searches ? `${one('searches', esc(t('sift_search.steps.searches')), true, '')}${sep}` : '')
    + `${one('ta', esc(t('sift_search.steps.ta')), ta, RV_TA_LATER)}${sep}${one('ft', esc(t('sift_search.steps.ft')), ft, RV_FT_LATER)}`
    + `${sep}${one('ex', RV_FORM_NAME, ta, RV_EX_LATER)}`;
}

/* Where the steps wrap under the bar at a narrow width, no chevron stands alone at a line's end or start
   (17 October, where one stood before the wrap at 360): one that ends a line is hidden in its place, and one
   that starts a line is taken out, neither changing which step stands on which line. Measured afresh each
   time the row is drawn or changes width. */
const RV_WATCHED = new WeakMap();

function rvStepsSeps(box) {
  if (!box || typeof box.querySelectorAll !== 'function') return;
  const seps = [...box.querySelectorAll('.sf-step-sep')];
  seps.forEach((sep) => { sep.style.display = ''; sep.style.visibility = ''; });
  for (const sep of seps) {
    const at = sep.getBoundingClientRect();
    if (!at.height) continue;
    const before = sep.previousElementSibling && sep.previousElementSibling.getBoundingClientRect();
    const after = sep.nextElementSibling && sep.nextElementSibling.getBoundingClientRect();
    if (before && before.bottom <= at.top + 1) sep.style.display = 'none';
    else if (after && after.top >= at.bottom - 1) sep.style.visibility = 'hidden';
  }
}

function rvStepsWatch(box) {
  if (!box || RV_WATCHED.has(box) || typeof ResizeObserver !== 'function') return;
  const seen = { width: -1 };
  const watch = new ResizeObserver(() => {
    const width = box.clientWidth;
    if (width === seen.width) return;
    seen.width = width;
    rvStepsSeps(box);
  });
  RV_WATCHED.set(box, watch);
  watch.observe(box);
}

function rvStepsDraw(box, review, step, counts) {
  const html = rvStepsHtml(review, step, counts);
  if (RV_DRAWN.get(box) !== html) {
    box.innerHTML = html;
    RV_DRAWN.set(box, html);
  }
  box.hidden = false;
  rvStepsSeps(box);
  rvStepsWatch(box);
  // the bar fitted again to the steps just drawn (shell.js barFit), on Search strategy as on the screening (sfBar)
  if (typeof barFit === 'function' && box.closest) barFit(box.closest('.rail'));
  box.onclick = (e) => {
    const b = e.target && e.target.closest ? e.target.closest('button[data-step]') : null;
    if (!b || b.getAttribute('aria-disabled') === 'true' || b.dataset.step === step) return;
    rvStep(review, b.dataset.step);
  };
}

/* The screening's count of records at each stage for the steps on Search strategy, asked of the
   screening its steps open, which the counts only read */
async function rvStageCounts(review) {
  if (!review || !review.screening) return;
  let got;
  try {
    got = await api('/api/sift', { op: 'counts', folder: review.screening });
  } catch { return; }
  if (SFS.review !== review || !got.counts) return;
  SFS.stages = got.counts.stages || null;
  if (sfsShown()) rvStepsDraw($('sfs-steps'), review, 'searches', SFS.stages);
}

/* A step chosen: on the screening a stage of it, else Title and abstract or Full text once the plan's
   last change is saved, its newest screening asked afresh, since a run may have made one, opened on
   that stage, or Search strategy once Sift's acts are in. */
async function rvStep(review, to) {
  if (to === 'ta' || to === 'ft' || to === 'ex') {
    if (sfShown()) { sfStageTo(to); return; }
    await sfsFlush();
    let got;
    try {
      got = await api('/api/sift-review', { op: 'read', folder: review.folder });
    } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
    if (got.review.screening) siftOpen(got.review.screening, null, to);
    return;
  }
  if (!review) return;
  const home = () => { loadLibrary().catch((err) => say(err.message, 9000)); };
  sfLeave(() => sfsOpen(review.folder, home));
}

/* ── opening ── */

/* A review's search strategy opened, from its row, its steps or a restart. A review that cannot be
   read says why and stays where he was, or goes to `gone`. */
async function sfsOpen(folder, gone) {
  let data;
  try {
    data = await api('/api/sift-search', { op: 'read', folder });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    if (gone) gone();
    return;
  }
  ['library', 'work', 'themes', 'sift', 'trace'].forEach((id) => { if ($(id)) $(id).hidden = true; });
  $('sift-search').hidden = false;
  SFS.folder = data.folder;
  SFS.name = data.name || '';
  SFS.catalog = data.catalog;
  SFS.how = data.how || {};
  SFS.listed = data.listed || [];
  SFS.today = data.today || '';
  SFS.plan = JSON.parse(JSON.stringify(data.plan));
  SFS.reason = (data.current && !data.current.registered && data.current.reason) || '';
  SFS.runs = data.runs || [];
  SFS.titles = data.titles || {};
  SFS.keys = data.keys || {};
  SFS.benchRows = null;
  SFS.finding = {};
  SFS.notFound = {};
  SFS.keyWorks = Array.isArray(data.key_works) ? data.key_works : [];
  SFS.kwPicks = null;
  SFS.kwAdding = false;
  SFS.reasons = null;
  SFS.open = new Set();
  SFS.ownOpen = new WeakSet();
  SFS.follows = null;
  SFS.terms = null;
  SFS.checking = false;
  SFS.running = data.running && data.running.running ? data.running : null;
  SFS.data = data;
  sfsStaleHide();
  SFS.review = data.review || null;
  SFS.stages = null;
  SFS.acc = null;
  SFS.accOpen = null;
  SFS.adding = false;
  bandNameSet('sfs-name', SFS.name);
  rvHead('searches', SFS.review);
  rvStageCounts(SFS.review);
  sfsDraw();
  if (SFS.running) sfsPoll();
  window.scrollTo(0, 0);
}

function sfsBack() {
  clearTimeout(SFS.poll);
  SFS.poll = null;
  const leave = () => {
    $('sift-search').hidden = true;
    $('sfs-ask').hidden = true;
    loadLibrary().catch((err) => say(err.message, 9000));
  };
  sfsFlush().then(leave);
}

/* ── drawing ── */

function sfsDraw() {
  sfsDrawBlocks();
  sfsDrawLimits();
  sfsDrawReasons(true);
  sfsDrawDatabases();
  sfsDrawBench(true);
  sfsDrawKeys();
  sfsDrawAnswer();
}

/* what each save's answer moves: the strings, the version, the problems, those under each block
   too, and the runs */
function sfsDrawAnswer() {
  sfsDrawStrings();
  sfsDrawVersion();
  sfsDrawBlockProblems();
  sfsDrawRun();
}

/* Sift's own order for the plan's databases, those the plan names after them in the order they were
   added, as the server keeps them */
function sfsInOrder(chosen) {
  const held = new Set(chosen);
  const rank = (s) => (s === 'other' ? 1 : Number(s.slice(5)));
  return SFS.catalog.sources.filter((s) => s !== 'other' && held.has(s))
    .concat([...held].filter(sfsIsOther).sort((a, b) => rank(a) - rank(b)));
}

/* the plan's id for a database he named, matched by its name, or null */
function sfsOtherId(name) {
  const want = String(name || '').trim().toLowerCase();
  const others = SFS.plan.others || {};
  return Object.keys(others).find((s) => SFS.plan.databases.includes(s) && others[s].toLowerCase() === want) || null;
}

/* the first id free for a database the plan names */
function sfsFreeOther() {
  const taken = new Set([...Object.keys(SFS.plan.others || {}), ...SFS.plan.databases]);
  for (let n = 1; n <= 20; n += 1) {
    const s = n === 1 ? 'other' : `other${n}`;
    if (!taken.has(s)) return s;
  }
  return null;
}

/* the platforms a database is offered on now, and one a plan or his list still names that its vendor
   no longer offers, kept among them with a word that says so */
function sfsPlatforms(cat, s, held) {
  const offered = ((cat.offered || {})[s]) || cat.platforms || [];
  const out = offered.slice();
  if (held && !offered.some(([k]) => k === held)) {
    const name = ((cat.platforms || []).find(([k]) => k === held) || [held, held])[1];
    out.push([held, t('sift_search.no_longer_offered', { name })]);
  }
  return out;
}

/* The databases in one list, in the plan's own order (12 October): every database Sift knows in its
   order, then each he named, those his list holds in its order and then any only the plan names. A
   row never moves when it is ticked or its access changes. Each
   is `{ key, s, name, listed, named }`, `s` the plan's id when the plan holds it. */
function sfsRows() {
  const cat = SFS.catalog;
  const listed = SFS.listed || [];
  const known = cat.sources.filter((s) => s !== 'other')
    .map((s) => ({ key: s, s, name: cat.names[s], listed: listed.find((r) => r.source === s) || null, named: false }));
  const named = listed.filter((r) => r.source === 'other')
    .map((r) => ({ key: `n:${r.name.toLowerCase()}`, s: sfsOtherId(r.name), name: r.name, listed: r, named: true }));
  const held = new Set(named.filter((r) => r.s).map((r) => r.s));
  const planOnly = sfsInOrder(SFS.plan.databases).filter((s) => sfsIsOther(s) && !held.has(s))
    .map((s) => ({ key: `n:${sfsName(s).toLowerCase()}`, s, name: sfsName(s), listed: null, named: true }));
  return known.concat(named, planOnly);
}

/* the plan's databases in the order the Databases part draws them, for the strings and the runs */
function sfsShownOrder() {
  const order = sfsRows().map((r) => r.s).filter(Boolean);
  return SFS.plan.databases.slice().sort((a, b) => {
    const i = order.indexOf(a);
    const j = order.indexOf(b);
    return (i < 0 ? 999 : i) - (j < 0 ? 999 : j);
  });
}

/* whether a database is set to go by API with a key not saved yet, so it goes by export until its
   access is set under its cog */
function sfsNeedsAccess(s) {
  const keyed = (SFS.catalog.keyed || {})[s];
  const listed = (SFS.listed || []).find((r) => r.source === s);
  return !!keyed && !!listed && listed.how === 'api' && !((SFS.keys || {})[s]);
}

/* One database's row in the plan (12 October, later): its box to tick, its platform where the plan
   holds one, how it runs, By API or By export, and Access not set for one set to go by API whose key
   is not saved. Its cog stands on its row under Searches once it is ticked. A database he named has
   Remove, since it lives in his list alone. The whole row ticks its box (13 October), a press on its
   tags or its padding too, through the app's `data-tick-row`, and Remove does only what it says. */
function sfsDbItem(row) {
  const cat = SFS.catalog;
  const on = !!row.s && SFS.plan.databases.includes(row.s);
  const s = row.s || '';
  const plat = !row.named && (cat.platformed || []).includes(s) && (on || row.listed)
    ? (on && (SFS.plan.platforms || {})[s]) || (row.listed && row.listed.platform) || 'ebsco' : '';
  const platName = plat ? ((cat.platforms || []).find(([k]) => k === plat) || [plat, plat])[1] : '';
  const exported = row.named || sfsExported(s);
  const tail = row.named
    ? `<button type="button" class="ghost small btn-remove sfs-db-remove" aria-label="${escAttr(t('sift_search.remove_name', { name: row.name }))}">${esc(t('sift_search.remove'))}</button>` : '';
  return `<div class="sfs-db" data-key="${escAttr(row.key)}" data-tick-row><div class="sfs-db-line">`
    + `<label class="sfs-db-pick"><input type="checkbox" aria-label="${escAttr(row.name)}"${on ? ' checked' : ''}>`
    + `<span class="sfs-db-name">${esc(row.name)}</span>${platName ? `<span class="sfs-db-plat">${esc(t('sift_search.on_platform', { platform: platName }))}</span>` : ''}</label>`
    + `<span class="sfs-tag${exported ? '' : ' api'}">${exported ? esc(t('sift_search.by_export')) : esc(t('sift_search.by_api'))}</span>`
    + `${!row.named && sfsNeedsAccess(s) ? `<span class="sfs-tag draft">${esc(t('sift_search.access_not_set'))}</span>` : ''}`
    + `${tail}</div></div>`;
}

function sfsDrawDatabases() {
  const all = sfsRows();
  $('sfs-dbs').innerHTML = all.map(sfsDbItem).join('');
  $('sfs-dbs').querySelectorAll('.sfs-db').forEach((el) => {
    const row = all.find((r) => r.key === el.dataset.key);
    if (!row) return;
    el.querySelector('input[type="checkbox"]').onchange = (e) => sfsTick(row, e.target.checked);
    const rm = el.querySelector('.sfs-db-remove');
    if (rm) rm.onclick = () => sfsRemoveNamed(row);
  });
  $('sfs-add-line').hidden = !SFS.adding;
  $('sfs-db-add').hidden = SFS.adding;
}

/* a database ticked or not: one Sift knows by its own id, one he named by an id of the plan's, its
   name kept, and a chosen PsycInfo or CINAHL on his list's platform to begin with */
function sfsTick(row, on) {
  const cat = SFS.catalog;
  const chosen = new Set(SFS.plan.databases);
  if (row.named) {
    const s = row.s || (on ? sfsFreeOther() : null);
    if (!s) { say(t('sift_search.twenty_already')); sfsDrawDatabases(); return; }
    if (on) {
      chosen.add(s);
      SFS.plan.others = Object.assign({}, SFS.plan.others, { [s]: row.name });
    } else sfsForget(s, chosen);
  } else if (on) {
    chosen.add(row.s);
    if ((cat.platformed || []).includes(row.s)) {
      SFS.plan.platforms = Object.assign({}, SFS.plan.platforms, { [row.s]: (row.listed && row.listed.platform) || 'ebsco' });
    }
  } else chosen.delete(row.s);
  SFS.plan.databases = sfsInOrder(chosen);
  sfsDrawDatabases();
  sfsDrawBlocks();
  sfsChanged(true);
}

/* a database he named taken out of the plan, with its name, its edited string and its fields */
function sfsForget(s, chosen) {
  chosen.delete(s);
  const others = Object.assign({}, SFS.plan.others);
  delete others[s];
  SFS.plan.others = others;
  if (SFS.plan.overrides) delete SFS.plan.overrides[s];
  (SFS.plan.blocks || []).forEach((b) => { if (b.scopes) delete b.scopes[s]; });
}

/* Remove on a database he named: out of his list and out of the plan */
async function sfsRemoveNamed(row) {
  const want = row.name.toLowerCase();
  if (row.s) {
    const chosen = new Set(SFS.plan.databases);
    sfsForget(row.s, chosen);
    SFS.plan.databases = sfsInOrder(chosen);
    sfsChanged(true);
  }
  const rows = (SFS.listed || []).filter((r) => !(r.source === 'other' && r.name.toLowerCase() === want));
  if (rows.length !== (SFS.listed || []).length) await sfsListSave(rows);
  sfsDrawDatabases();
  sfsDrawBlocks();
}

/* Add database: a name, Add, the row added to his list and ticked in the plan. A name Sift knows
   takes its own row, and a name his list holds already is ticked and not added twice. */
async function sfsAddDb() {
  const field = $('sfs-db-name');
  const name = field.value.trim().replace(/\s+/g, ' ').slice(0, 60);
  if (!name) { field.focus(); return; }
  const cat = SFS.catalog;
  const lower = name.toLowerCase();
  const own = cat.sources.find((s) => s !== 'other' && cat.names[s].toLowerCase() === lower);
  const rows = (SFS.listed || []).map((r) => Object.assign({}, r));
  field.value = '';
  if (own) {
    if (!rows.some((r) => r.source === own)) {
      const row = { source: own, how: (cat.apis || []).includes(own) ? 'api' : 'export' };
      if ((cat.platformed || []).includes(own)) row.platform = 'ebsco';
      rows.push(row);
      await sfsListSave(rows);
    }
    const listed = (SFS.listed || []).find((r) => r.source === own) || null;
    if (!SFS.plan.databases.includes(own)) sfsTick({ s: own, name: cat.names[own], listed, named: false }, true);
    else sfsDrawDatabases();
  } else {
    const held = rows.find((r) => r.source === 'other' && r.name.toLowerCase() === lower);
    if (!held) {
      rows.push({ source: 'other', name, how: 'export' });
      await sfsListSave(rows);
    }
    if (!sfsOtherId(name)) sfsTick({ s: null, name: held ? held.name : name, listed: null, named: true }, true);
    else say(t('sift_search.in_list', { name }));
  }
  field.focus();
}

/* his list written at once, as Settings' Databases holds it, then how each database goes read afresh */
async function sfsListSave(rows) {
  try {
    const got = await api('/api/databases', { op: 'save', rows });
    SFS.listed = got.rows || rows;
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  await sfsSettingsSaved();
}

/* A database's cog, on its row under Searches: its access opened under its name, or shut. The keys
   saved are asked for the first time a cog opens, never before. */
async function sfsCog(s) {
  if (SFS.accOpen === s) { SFS.accOpen = null; sfsDrawStrings(); return; }
  if (!SFS.acc) {
    try {
      const got = await api('/api/databases', { op: 'read' });
      SFS.acc = { saved: got.saved || {}, catalog: got.catalog || SFS.catalog, said: {}, failed: {} };
    } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  }
  SFS.accOpen = s;
  sfsDrawStrings();
}

/* the row of his list the cog sets, a copy, or a new one for a database his list does not hold,
   By export as the plan has it now */
function sfsAccRow(s) {
  const held = (SFS.listed || []).find((r) => r.source === s);
  // one his list does not hold goes by export, but PubMed, Europe PMC and OpenAlex, which need no key, by API
  const row = held ? Object.assign({}, held) : { source: s, how: (SFS.catalog.keyless || []).includes(s) ? 'api' : 'export' };
  if ((SFS.catalog.platformed || []).includes(s)) row.platform = (SFS.plan.platforms || {})[s] || row.platform || 'ebsco';
  return row;
}

function sfsAccHtml(s) {
  const r = sfsAccRow(s);
  const a = dbsAccessParts(SFS.acc, r, `sfs-key-${s}`, sfsName(s));
  return `<div class="dbs-head">${a.plats ? `<span class="sfs-acc-field">${t('sift_search.acc.platform_html', { plats: a.plats })}</span>` : ''}`
    + `<span class="sfs-acc-field">${t('sift_search.acc.searched_html', { how: a.how })}</span></div>${a.keys}`;
}

/* A change in a cog goes to his list at once, a platform to the plan too when the plan holds the
   database, and a key through the same calls as Settings' */
function sfsBindAcc(el, s) {
  const r = sfsAccRow(s);
  const changed = async () => {
    if ((SFS.catalog.platformed || []).includes(s) && SFS.plan.databases.includes(s) && r.platform) {
      SFS.plan.platforms = Object.assign({}, SFS.plan.platforms, { [s]: r.platform });
      sfsChanged(true);
    }
    const rows = (SFS.listed || []).map((x) => (x.source === s ? Object.assign({}, r) : x));
    if (!rows.some((x) => x.source === s)) rows.push(Object.assign({}, r));
    await sfsListSave(rows);
  };
  dbsBindAccess(SFS.acc, el, r, () => sfsSettingsSaved(), changed);
}

function sfsScopeOptions(chosen, first) {
  return (first ? `<option value="">${esc(first)}</option>` : '')
    + SFS.catalog.scopes.map(([k, w]) => `<option value="${k}"${k === chosen ? ' selected' : ''}>${esc(w)}</option>`).join('');
}

/* a disclosure on this screen: a button at the app's normal size with a chevron and its words, which
   turns as it opens, never a small marker (12 October, later) */
const SFS_CHEVRON = '<svg class="sfs-chev" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4.5 2.8 7.7 6 4.5 9.2"/></svg>';
const sfsToggleHtml = (cls, words, open) => `<button type="button" class="ghost small sfs-toggle ${cls}" aria-expanded="${open}">${SFS_CHEVRON}${esc(words)}</button>`;

/* a field scope by its words in a line, "full text" */
const sfsScopeWord = (k) => {
  const w = ((SFS.catalog.scopes || []).find(([x]) => x === k) || [k, String(k || '')])[1];
  return w.charAt(0).toLowerCase() + w.slice(1);
};

/* the chosen databases that look for a block's terms in other fields than the block's, each `[s, scope]` */
const sfsDiffers = (b) => SFS.plan.databases.filter((s) => (b.scopes || {})[s] && b.scopes[s] !== b.scope).map((s) => [s, b.scopes[s]]);

/* Each block (12 October, later): headed Block 1, Block 2 with its name beside it, then Search in,
   the fields its terms are looked for in, with the terms under it, any problem with a term, then
   Search in, by database, shut at first on every block and opened by its button, to look in other
   fields in one database, and while shut a line for each database that differs, so no difference is
   hidden. Remove at its foot and AND before the next. */
/* A block's terms open as tall as they are, a line to spare, never under four lines nor over thirty,
   past which the box scrolls, and grow or shrink with each edit, so a long list never has to be dragged
   open (Adam, 13 October) */
const SFS_TERM_ROWS = [4, 30];
// a save refused since the plan changed in another window (19 October), the boards' line with "plan"
const SFS_STALE_LINE = t('sift_search.stale');
function sfsTermRows(text) {
  const lines = String(text || '').split('\n').length + 1;
  return Math.min(SFS_TERM_ROWS[1], Math.max(SFS_TERM_ROWS[0], lines));
}

function sfsDrawBlocks() {
  const blocks = SFS.plan.blocks;
  const dbs = SFS.plan.databases;
  $('sfs-blocks').innerHTML = blocks.map((b, i) => {
    const open = SFS.ownOpen.has(b);
    const own = dbs.map((s) => `<label class="sfs-own-row"><span>${esc(sfsName(s))}</span><select class="sfs-select" data-own="${s}" aria-label="${escAttr(t('sift_search.block.own_label', { name: sfsName(s) }))}">`
      + `${sfsScopeOptions((b.scopes || {})[s] || '', t('sift_search.block.same'))}</select></label>`).join('');
    const differs = open ? [] : sfsDiffers(b);
    return `${i ? '<p class="sfs-and">AND</p>' : ''}<div class="sfs-block" data-i="${i}">`
      + `<div class="sfs-block-head"><span class="sfs-bnum">${esc(t('sift_search.block.n', { i: i + 1 }))}</span><input class="sfs-bname" type="text" value="${escAttr(b.name || '')}"`
      + ` placeholder="${escAttr(t('sift_search.name'))}" aria-label="${escAttr(t('sift_search.block.name_label', { i: i + 1 }))}" spellcheck="false"></div>`
      + `<p class="sfs-search-in"><label class="sfs-label" for="sfs-scope-${i}">${esc(t('sift_search.block.search_in'))}</label>`
      + `<select class="sfs-select sfs-bscope" id="sfs-scope-${i}">${sfsScopeOptions(b.scope, '')}</select></p>`
      + `<textarea class="sfs-terms" rows="${sfsTermRows((b.terms || []).join('\n'))}" spellcheck="false" placeholder="${escAttr(t('sift_search.block.terms_placeholder'))}" aria-label="${escAttr(t('sift_search.block.terms_label', { i: i + 1 }))}">${esc((b.terms || []).join('\n'))}</textarea>`
      + '<div class="sfs-problems sfs-bproblems" hidden></div>'
      + (dbs.length ? `<div class="sfs-own">${sfsToggleHtml('sfs-own-toggle', t('sift_search.block.by_database'), open)}`
        + differs.map(([s, k]) => `<p class="sfs-own-said">${esc(sfsName(s))}: ${esc(sfsScopeWord(k))}</p>`).join('')
        + (open ? `<div class="sfs-own-rows">${own}</div>` : '') + '</div>' : '')
      + `<p class="sfs-block-foot"><button type="button" class="ghost small btn-remove sfs-bremove">${esc(t('sift_search.remove'))}</button></p>`
      + '</div>';
  }).join('');
  $('sfs-blocks').querySelectorAll('.sfs-block').forEach((el) => {
    const b = blocks[Number(el.dataset.i)];
    el.querySelector('.sfs-bname').oninput = (e) => { b.name = e.target.value; sfsChanged(); };
    const toggle = el.querySelector('.sfs-own-toggle');
    if (toggle) {
      toggle.onclick = () => {
        if (SFS.ownOpen.has(b)) SFS.ownOpen.delete(b); else SFS.ownOpen.add(b);
        sfsDrawBlocks();
        const again = $('sfs-blocks').querySelectorAll('.sfs-own-toggle')[blocks.indexOf(b)];
        if (again) again.focus();
      };
    }
    el.querySelector('.sfs-bscope').onchange = (e) => {
      b.scope = e.target.value;
      Object.keys(b.scopes || {}).forEach((s) => { if (b.scopes[s] === b.scope) delete b.scopes[s]; });
      sfsDrawBlocks();
      sfsChanged();
    };
    el.querySelector('.sfs-terms').oninput = (e) => { b.terms = e.target.value.split('\n'); e.target.rows = sfsTermRows(e.target.value); sfsChanged(); };
    el.querySelector('.sfs-bremove').onclick = async () => {
      // a block that holds terms asks first, since its terms go with it, and an empty one goes at once
      const terms = (b.terms || []).filter((t) => String(t).trim()).length;
      if (terms && !(await sfsAsk(b.name && b.name.trim() ? t('sift_search.block.remove_named', { name: b.name.trim() })
        : t('sift_search.block.remove_this'), t('sift_search.block.remove_line', { n: terms }), t('sift_search.remove'), true))) return;
      const at = blocks.indexOf(b);
      if (at < 0) return;
      blocks.splice(at, 1);
      // the problems drawn under the blocks after it move up with them until the save answers
      if (SFS.data && Array.isArray(SFS.data.block_problems)) SFS.data.block_problems.splice(at, 1);
      sfsDrawBlocks();
      sfsChanged();
    };
    el.querySelectorAll('select[data-own]').forEach((sel) => {
      sel.onchange = () => {
        b.scopes = b.scopes || {};
        if (sel.value && sel.value !== b.scope) b.scopes[sel.dataset.own] = sel.value; else delete b.scopes[sel.dataset.own];
        sfsChanged();
      };
    });
  });
  sfsDrawBlockProblems();
}

/* Under each block, the problems with its own terms as the last save's answer has them, each one
   also among the problems under Register, and under the blocks a plan with no block holding a term
   says so there too, beside its cause, where it stood only under Register (17 October, later). Only
   these lines are drawn afresh, so a field being typed in keeps its place. */
function sfsDrawBlockProblems() {
  const said = (SFS.data && SFS.data.block_problems) || [];
  $('sfs-blocks').querySelectorAll('.sfs-block').forEach((el) => {
    const box = el.querySelector('.sfs-bproblems');
    if (!box) return;
    const lines = said[Number(el.dataset.i)] || [];
    box.innerHTML = lines.map((p) => `<p>${esc(p)}</p>`).join('');
    box.hidden = !lines.length;
  });
  const all = (SFS.data && SFS.data.terms_problems) || [];
  const box = $('sfs-terms-said');
  if (!box) return;
  box.innerHTML = all.map((p) => `<p>${esc(p)}</p>`).join('');
  box.hidden = !all.length;
}

function sfsDrawLimits() {
  const y = SFS.plan.years || {};
  $('sfs-from').value = y.from == null ? '' : String(y.from);
  $('sfs-to').value = y.to == null ? '' : String(y.to);
  const on = new Set(SFS.plan.types || []);
  $('sfs-types').innerHTML = SFS.catalog.types.map(([k, w]) => `<label class="sfs-type"><input type="checkbox" data-t="${k}" aria-label="${escAttr(w)}"${on.has(k) ? ' checked' : ''}>${esc(w)}</label>`).join('');
  $('sfs-types').querySelectorAll('input').forEach((box) => {
    box.onchange = () => {
      const chosen = new Set(SFS.plan.types || []);
      if (box.checked) chosen.add(box.dataset.t); else chosen.delete(box.dataset.t);
      SFS.plan.types = SFS.catalog.types.map(([k]) => k).filter((k) => chosen.has(k));
      sfsChanged();
    };
  });
}

/* the reasons as the server holds them: the review folder's reasons.csv when it is there, a file of
   before read into one list, else the plan's own */
function sfsReasonRows() {
  const file = SFS.data && SFS.data.reasons_file ? SFS.data.reasons_file : null;
  const held = file ? file.reasons : SFS.plan.reasons;
  return (Array.isArray(held) ? held : []).map((r) => ({ code: String(r.code || ''), meaning: String(r.meaning || '') }));
}

/* The exclusion reasons, one list edited here (12 October, later): a row each, the handle that drags
   it up or down at its left, the home screen's own, its code and what it means and Remove, then Add a
   reason. The app keeps the review folder's reasons.csv from the list, written a moment after each
   change. `fill` draws the rows from what the server holds, else from the rows as they are edited. */
function sfsDrawReasons(fill) {
  if (fill || !SFS.reasons) SFS.reasons = sfsReasonRows();
  const rows = SFS.reasons;
  $('sfs-reasons').innerHTML = rows.map((r, i) => `<div class="sfs-reason" data-i="${i}">${gripHtml(t('sift_search.reason.grip', { i: i + 1 }))}`
    + `<input class="sfs-rcode" type="text" value="${escAttr(r.code)}" maxlength="12" placeholder="${escAttr(t('sift_search.reason.code'))}" spellcheck="false" aria-label="${escAttr(t('sift_search.reason.code_label', { i: i + 1 }))}">`
    + `<input class="sfs-rmeaning" type="text" value="${escAttr(r.meaning)}" maxlength="200" placeholder="${escAttr(t('sift_search.reason.meaning'))}" aria-label="${escAttr(t('sift_search.reason.meaning_label', { i: i + 1 }))}">`
    + `<span class="sfs-rtools"><button type="button" class="ghost small btn-remove sfs-rremove" aria-label="${escAttr(t('sift_search.reason.remove_label', { i: i + 1 }))}">${esc(t('sift_search.remove'))}</button></span></div>`).join('');
  $('sfs-reasons').querySelectorAll('.sfs-reason').forEach((el) => {
    const i = Number(el.dataset.i);
    el.querySelector('.sfs-rcode').oninput = (e) => { rows[i].code = e.target.value; sfsReasonSaid(); sfsReasonsChanged(); };
    el.querySelector('.sfs-rmeaning').oninput = (e) => { rows[i].meaning = e.target.value; sfsReasonsChanged(); };
    el.querySelector('button.pc-grip').onpointerdown = (e) => gripDrag(e, el, $('sfs-reasons'), sfsReasonGrip());
    el.querySelector('.sfs-rremove').onclick = () => {
      rows.splice(i, 1);
      sfsDrawReasons(false);
      sfsReasonsChanged(true);
    };
  });
  sfsReasonSaid();
}

/* the handle's `how` on the reasons: a reason said by its code, and the order saved */
function sfsReasonGrip() {
  return {
    rows: ':scope > .sfs-reason',
    live: 'sfs-reasons-moved',
    said: (el, to, n) => t('sift_search.grip.said', { name: ((SFS.reasons || [])[Number(el.dataset.i)] || { code: '' }).code.trim()
      || t('sift_search.reason.n', { i: to + 1 }), at: to + 1, n }),
    moved: sfsReasonsMoved,
  };
}

/* The reasons in the order a drag or Alt and an arrow left their rows, drawn again and written at
   once, as Remove writes them, the handle that has the focus keeping it */
function sfsReasonsMoved(els) {
  const rows = SFS.reasons || [];
  const now = els.map((el) => rows[Number(el.dataset.i)]).filter(Boolean);
  if (now.length !== rows.length) return;
  const held = document.activeElement && document.activeElement.closest ? document.activeElement.closest('#sfs-reasons .sfs-reason') : null;
  const at = held ? els.indexOf(held) : -1;
  SFS.reasons = now;
  sfsDrawReasons(false);
  sfsReasonsChanged(true);
  const grip = at >= 0 ? $('sfs-reasons').querySelectorAll('button.pc-grip')[at] : null;
  if (grip) grip.focus();
}

/* under the reasons, what keeps one out of the file: a code held twice, a meaning with no code, or a
   file that cannot be read */
function sfsReasonSaid() {
  const rows = SFS.reasons || [];
  const lines = [];
  const seen = new Set();
  rows.forEach((r) => {
    const code = r.code.trim().toLowerCase();
    if (!code && r.meaning.trim()) lines.push(t('sift_search.reason.needs_code'));
    else if (code && seen.has(code)) lines.push(t('sift_search.reason.twice', { code: r.code.trim() }));
    seen.add(code);
  });
  const file = SFS.data && SFS.data.reasons_file;
  if (file && file.said) lines.push(file.said);
  const box = $('sfs-reasons-said');
  box.innerHTML = [...new Set(lines)].map((l) => `<p>${esc(l)}</p>`).join('');
  box.hidden = !lines.length;
}

/* a change to the reasons, written a moment after the last one, or at once for a click */
function sfsReasonsChanged(now = false) {
  clearTimeout(SFS.reasonTimer);
  if (now) { SFS.reasonTimer = null; sfsReasonsSave(); return; }
  SFS.reasonTimer = setTimeout(() => { SFS.reasonTimer = null; sfsReasonsSave(); }, 600);
}

/* The reasons written to reasons.csv through the reasons op, after any save of the plan before them,
   and the plan as the server now holds it, its version and its problems, drawn from the answer. The
   rows being typed in stay as they are. */
function sfsReasonsSave() {
  const rows = (SFS.reasons || []).filter((r) => r.code.trim()).map((r) => ({ code: r.code.trim(), meaning: r.meaning.trim() }));
  if (SFS.saveTimer) { clearTimeout(SFS.saveTimer); SFS.saveTimer = null; sfsSave(); }
  SFS.chain = SFS.chain.then(async () => {
    // a refused save waits for Reload or Overwrite, which sends these rows again
    if (SFS.stale) { SFS.stale.reasons = true; return; }
    const seen = (SFS.data && SFS.data.plan_version) || null;
    let got;
    try {
      got = await api('/api/sift-search', { op: 'reasons', folder: SFS.folder, rows, seen });
    } catch (err) {
      if (err && err.data && err.data.stale) { sfsStaleShow(err.data.stale); SFS.stale.reasons = true; return; }
      throw err;
    }
    SFS.data = Object.assign({}, SFS.data, got, { runs: SFS.data.runs });
    if (got.plan) SFS.plan.reasons = got.plan.reasons;
    sfsDrawAnswer();
    sfsReasonSaid();
  }).catch((err) => say(needsRestart(err) ? RESTART_LINE : err.message, 9000));
  return SFS.chain;
}

/* a DOI as the plan keeps it, as the server's norm_doi has it: lower case, with no address and no
   doi: before it */
const sfsDoi = (v) => String(v || '').trim().replace(/\s+/g, ' ').toLowerCase()
  .replace(/^(?:https?:\/\/)?(?:dx\.)?doi\.org\//, '').replace(/^doi:\s*/, '').trim().replace(/\.+$/, '');
const sfsIsDoi = (d) => /^10\.\d{3,9}\/\S+$/.test(d);

/* the words beside a benchmark paper's DOI: its title, the plan's or a run's, else why there is none */
function sfsPaperWords(raw) {
  const d = sfsDoi(raw);
  if (!d || SFS.finding[d]) return '';
  const title = (SFS.plan.benchmark_titles || {})[d] || (SFS.titles || {})[d];
  if (title) return `<span class="sfs-paper-name">${esc(title)}</span>`;
  if (!sfsIsDoi(d)) return `<span class="sfs-paper-not">${esc(t('sift_search.paper.not_doi'))}</span>`;
  return SFS.notFound[d] ? `<span class="sfs-dim">${esc(t('sift_search.paper.not_found'))}</span>` : '';
}

/* The benchmark papers (12 October, later): a row each, its DOI in a box with the paper's title
   beside it and Remove, then Add a paper. A DOI added or changed asks OpenAlex for its title once it
   is entered, which the plan keeps with it, and a title a run found stands for one the plan has none
   for. `fill` draws the rows from the plan, else from the rows as they are edited. */
function sfsDrawBench(fill) {
  if (fill || !SFS.benchRows) SFS.benchRows = (SFS.plan.benchmark || []).slice();
  const rows = SFS.benchRows;
  $('sfs-bench-rows').innerHTML = rows.map((d, i) => `<div class="sfs-paper" data-i="${i}">`
    + `<input class="sfs-doi" type="text" value="${escAttr(d)}" placeholder="${escAttr(t('sift_search.paper.doi'))}" spellcheck="false" aria-label="${escAttr(t('sift_search.paper.doi_label', { i: i + 1 }))}">`
    + `<span class="sfs-paper-title">${sfsPaperWords(d)}</span>`
    + `<button type="button" class="ghost small btn-remove sfs-paper-remove" aria-label="${escAttr(t('sift_search.paper.remove_label', { i: i + 1 }))}">${esc(t('sift_search.remove'))}</button></div>`).join('');
  $('sfs-bench-rows').hidden = !rows.length;
  $('sfs-bench-rows').querySelectorAll('.sfs-paper').forEach((el) => {
    const i = Number(el.dataset.i);
    const box = el.querySelector('.sfs-doi');
    box.oninput = () => { rows[i] = box.value; };
    box.onchange = () => {
      const d = sfsDoi(box.value);
      // a paper the list holds already takes no second row
      if (d && rows.some((v, j) => j !== i && sfsDoi(v) === d)) {
        rows.splice(i, 1);
        sfsBenchSync();
        sfsChanged(true);
        sfsDrawBench(false);
        say(t('sift_search.paper.there'));
        return;
      }
      box.value = d;
      rows[i] = d;
      sfsBenchSync();
      sfsChanged(true);
      sfsDrawBenchTitles();
      if (sfsIsDoi(d) && !(SFS.plan.benchmark_titles || {})[d] && !(SFS.titles || {})[d]) sfsFindTitle(d);
    };
    el.querySelector('.sfs-paper-remove').onclick = () => {
      rows.splice(i, 1);
      sfsBenchSync();
      sfsChanged(true);
      sfsDrawBench(false);
    };
  });
}

/* the titles beside the DOIs drawn afresh alone, so a DOI being typed keeps its place */
function sfsDrawBenchTitles() {
  $('sfs-bench-rows').querySelectorAll('.sfs-paper').forEach((el) => {
    const t = el.querySelector('.sfs-paper-title');
    if (t) t.innerHTML = sfsPaperWords((SFS.benchRows || [])[Number(el.dataset.i)]);
  });
}

/* the plan's benchmark from the rows, each DOI once in their order, a title kept for each it holds */
function sfsBenchSync() {
  const dois = [];
  (SFS.benchRows || []).forEach((v) => { const d = sfsDoi(v); if (d && !dois.includes(d)) dois.push(d); });
  const held = SFS.plan.benchmark_titles || {};
  SFS.plan.benchmark = dois;
  SFS.plan.benchmark_titles = Object.fromEntries(dois.filter((d) => held[d]).map((d) => [d, held[d]]));
}

/* A paper's title asked of OpenAlex by its DOI through the title op, kept in the plan's titles and
   saved, or Title not found beside it. Nothing else is sent. */
async function sfsFindTitle(d) {
  SFS.finding[d] = true;
  sfsDrawBenchTitles();
  let got = null;
  try {
    got = await api('/api/sift-search', { op: 'title', folder: SFS.folder, doi: d });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
  delete SFS.finding[d];
  if (got && got.title) {
    delete SFS.notFound[d];
    if (SFS.plan.benchmark.includes(d)) {
      SFS.plan.benchmark_titles = Object.assign({}, SFS.plan.benchmark_titles, { [d]: got.title });
      sfsChanged(true);
    }
  } else if (got) SFS.notFound[d] = got.said || t('sift_search.paper.not_found');
  sfsDrawBenchTitles();
}

/* ── the key works ── */

/* a DOI as the server's norm_doi has it, or empty for anything that is not one */
const sfsKwDoi = (v) => { const d = sfsDoi(v); return sfsIsDoi(d) ? d : ''; };
// a title as two are compared, its letters and digits alone, accents off and case folded
const sfsFold = (t) => String(t || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
const sfsKwName = (k) => (k.title ? `${k.title}${k.year ? ` (${k.year})` : ''}` : k.doi);
// whether a key work is in the list already, by its OpenAlex ID, its DOI or its title and year
const sfsKwHeld = (k) => SFS.keyWorks.some((h) => (k.id && h.id === k.id) || (k.doi && h.doi === k.doi)
  || (k.title && h.title && sfsFold(h.title) === sfsFold(k.title) && String(h.year || '') === String(k.year || '')));

/* The key works (13 October): works the studies of the review would cite, a row each, its title and
   year, its DOI where it has one, and Remove, then Add a key work, which opens a line for a DOI or a
   title and its year, and Find. A DOI is asked of OpenAlex and kept with the title it gives, and a
   title is looked up in OpenAlex's works, its first few offered to pick from, each its title, year,
   authors and count of citations, with Keep it by its title and year for none of them. A row keeps
   the title and year he typed, with the OpenAlex ID of the work he picked and never its DOI or
   authors. Each change is saved at once beside the plan's versions, so no draft is made. */
function sfsDrawKeys() {
  const rows = SFS.keyWorks || [];
  $('sfs-kw-rows').innerHTML = rows.map((k, i) => `<div class="sfs-paper sfs-kw" data-i="${i}">`
    + `<span class="sfs-paper-title">${esc(sfsKwName(k))}</span>`
    + `<span class="mono sfs-dim">${k.doi ? esc(k.doi) : ''}</span>`
    + `<button type="button" class="ghost small btn-remove sfs-kw-remove" aria-label="${escAttr(t('sift_search.remove_name', { name: sfsKwName(k) }))}">${esc(t('sift_search.remove'))}</button></div>`).join('');
  $('sfs-kw-rows').hidden = !rows.length;
  $('sfs-kw-rows').querySelectorAll('.sfs-kw-remove').forEach((b) => {
    b.onclick = () => sfsKwSave(rows.filter((_, j) => j !== Number(b.closest('.sfs-kw').dataset.i)));
  });
  $('sfs-kw-add').hidden = !SFS.kwAdding;
  $('sfs-kw-new').hidden = SFS.kwAdding;
  const p = SFS.kwPicks;
  $('sfs-kw-picks').hidden = !p;
  if (!p) return;
  const cited = (n) => (typeof n === 'number' ? t('sift_search.kw.cited', { n: tNum(n) }) : '');
  $('sfs-kw-picks').innerHTML = `${p.said ? `<p class="sfs-dim">${esc(p.said)}</p>` : ''}`
    + `${p.works.length ? `<p class="sfs-kw-which">${esc(t('sift_search.kw.which'))}</p>` : ''}`
    + p.works.map((w, i) => `<button type="button" class="sfs-kw-pick" data-i="${i}"><span class="sfs-kw-pt">${esc(w.title || w.doi)}</span>`
      + `<span class="sfs-dim">${esc([w.year, w.authors].filter(Boolean).join(', '))}${cited(w.cited)}</span></button>`).join('')
    + `<p><button type="button" class="ghost small" id="sfs-kw-keep">${esc(t('sift_search.kw.keep'))}</button></p>`;
  $('sfs-kw-picks').querySelectorAll('.sfs-kw-pick').forEach((b) => {
    b.onclick = () => { const w = p.works[Number(b.dataset.i)]; sfsKwAdd({ id: w.id, doi: '', title: p.text, year: p.year }); };
  });
  $('sfs-kw-keep').onclick = () => sfsKwAdd({ id: '', doi: '', title: p.text, year: p.year });
}

/* Find: a DOI asked of OpenAlex and added with the title it gives, or by the DOI alone when OpenAlex
   does not know it, and a title with its year looked up, its works offered to pick from */
async function sfsKwFind() {
  const text = $('sfs-kw-text').value.trim();
  const year = $('sfs-kw-year').value.trim();
  if (!text) { $('sfs-kw-text').focus(); return; }
  const doi = sfsKwDoi(text);
  if (!doi && !/^\d{4}$/.test(year)) { say(t('sift_search.kw.year_too')); $('sfs-kw-year').focus(); return; }
  $('sfs-kw-find').disabled = true;
  let got = null;
  try {
    got = await api('/api/sift-search', { op: 'works', folder: SFS.folder, text });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
  $('sfs-kw-find').disabled = false;
  if (!got) return;
  if (doi) {
    const w = got.works[0];
    sfsKwAdd(w ? { id: w.id, doi, title: w.title, year: year || w.year } : { id: '', doi, title: '', year });
    return;
  }
  SFS.kwPicks = { text, year, works: got.works || [], said: got.said || '' };
  sfsDrawKeys();
}

/* a key work added, refused in one line when the list holds it already, and the line shut */
function sfsKwAdd(k) {
  if (sfsKwHeld(k)) { say(t('sift_search.kw.there')); return; }
  SFS.kwPicks = null;
  SFS.kwAdding = false;
  $('sfs-kw-text').value = '';
  $('sfs-kw-year').value = '';
  sfsKwSave((SFS.keyWorks || []).concat([k]));
}

/* the key works written beside the plan's versions through the key_works op, the list drawn as the
   server keeps it */
function sfsKwSave(rows) {
  SFS.keyWorks = rows;
  sfsDrawKeys();
  SFS.chain = SFS.chain.then(async () => {
    const got = await api('/api/sift-search', { op: 'key_works', folder: SFS.folder, rows });
    SFS.keyWorks = got.key_works || [];
    sfsDrawKeys();
  }).catch((err) => say(needsRestart(err) ? RESTART_LINE : err.message, 9000));
  return SFS.chain;
}

/* a benchmark DOI as a line names it, with its title where one is known */
function sfsDoiWords(d) {
  const typed = ((SFS.data && SFS.data.plan) || SFS.plan || {}).benchmark_titles || {};
  const t = typed[d] || (SFS.titles || {})[d];
  return `<span class="mono">${esc(d)}</span>${t ? ` (${esc(t)})` : ''}`;
}

/* Whether a database is searched on its own site and its export dropped, from its row of a run under
   way where there is one, else from how his list sends it: a database he named always, and any other
   unless Sift has an API for it and it goes by API */
function sfsExported(s, r = {}) {
  const how = sfsIsOther(s) ? 'export' : r.how || SFS.how[s];
  return how !== 'api' || !((SFS.catalog.keyless || []).includes(s) || (SFS.catalog.apis || []).includes(s));
}

/* Searches (12 October): a row for each database of the plan, in the Databases part's order. At its
   left its name, how it runs, By API or By export, and its cog, which opens its access under the
   name, and for By export the steps in order. At its right its search as Sift writes it from the
   plan, with Edit manually, which opens it to edit with a reason beside it, kept in the version
   until Revert to automatic takes it away, and Copy for a search Sift runs itself, a search run on a
   database's own site copied by its first step. A row being typed in is left as it is while the rest
   are drawn afresh. */
function sfsDrawStrings() {
  const box = $('sfs-strings');
  const order = sfsShownOrder();
  const list = ((SFS.data && SFS.data.strings) || []).slice()
    .sort((a, b) => order.indexOf(a.source) - order.indexOf(b.source));
  const active = document.activeElement;
  const typing = active && active.matches && active.matches('textarea, input') ? active.closest('.sfs-str') : null;
  const held = typing ? typing.dataset.s : null;
  if (!list.length) { box.innerHTML = `<p class="sfs-none">${esc(t('sift_search.no_databases'))}</p>`; return; }
  const kept = held ? box.querySelector(`.sfs-str[data-s="${held}"]`) : null;
  box.innerHTML = list.map((s) => {
    const over = s.override;
    const exported = sfsExported(s.source);
    const named = sfsIsOther(s.source);
    const open = !named && SFS.accOpen === s.source;
    // a plan with no term yet writes no search, and Copy is held until there is one (17 October, later)
    const empty = !String((over ? over.query : s.query) || '').trim();
    const cog = named ? ''
      : `<button type="button" class="sfs-cog" aria-label="${escAttr(t('sift_search.str.access_label', { name: s.name }))}" title="${escAttr(t('sift_search.str.access'))}" aria-expanded="${open}">${TB_COG}</button>`;
    return `<div class="sfs-str${open ? ' open' : ''}" data-s="${s.source}"><div class="sfs-str-how">`
      + `<div class="sfs-str-head"><span class="sfs-str-name">${s.platform ? esc(t('sift_search.str.name_on', { name: s.name, platform: s.platform })) : esc(s.name)}</span>`
      + `<span class="sfs-tag${exported ? '' : ' api'}">${exported ? esc(t('sift_search.by_export')) : esc(t('sift_search.by_api'))}</span>${cog}</div>`
      + (open ? `<div class="sfs-acc">${sfsAccHtml(s.source)}</div>` : '')
      + (exported ? sfsSteps(s.source, empty) : '')
      + `</div><div class="sfs-str-text"><pre class="sfs-q">${esc(s.query || ' ')}</pre>`
      + (over ? `<div class="sfs-hand-box"><textarea class="sfs-hand-q" rows="4" spellcheck="false" aria-label="${escAttr(t('sift_search.str.the_search'))}">${esc(over.query)}</textarea>`
        + `<input class="sfs-hand-why" type="text" value="${escAttr(over.reason || '')}" placeholder="${escAttr(t('sift_search.str.reason'))}" aria-label="${escAttr(t('sift_search.str.reason'))}"></div>` : '')
      + `<p class="sfs-str-tools">${over ? `<span class="sfs-tag hand">${esc(t('sift_search.str.edited'))}</span>` : ''}`
      + `${exported ? '' : `<button type="button" class="ghost small sfs-copy"${empty ? ' disabled' : ''}>${esc(t('sift_search.copy'))}</button>`}`
      + `<button type="button" class="ghost small sfs-hand">${over ? esc(t('sift_search.str.revert')) : esc(t('sift_search.str.edit'))}</button></p>`
      + sfsRewritesHtml(s)
      + s.notes.map((n) => `<p class="sfs-note">${esc(n)}</p>`).join('')
      + (s.limits ? `<p class="sfs-note">${esc(s.limits)}</p>` : '')
      + '</div></div>';
  }).join('');
  if (kept) {
    const fresh = box.querySelector(`.sfs-str[data-s="${held}"]`);
    if (fresh) fresh.replaceWith(kept);
  }
  box.querySelectorAll('.sfs-str').forEach((el) => sfsBindString(el, list.find((s) => s.source === el.dataset.s)));
}

/* Beside each database's string, the rewrites Sift made for that database in plain words, the server's
   (see `rewrites` in sift_search.py), one to a line under Rewrites, or for a string edited manually its
   reason (14 October). Nothing when Sift changed nothing. */
function sfsRewritesHtml(s) {
  const said = (s && s.rewrites) || [];
  if (!said.length) return '';
  return `<div class="sfs-rewrites"><p class="sfs-rw-head">${esc(t('sift_search.str.rewrites'))}</p><ul>${said.map((w) => `<li>${esc(w)}</li>`).join('')}</ul></div>`;
}

function sfsBindString(el, s) {
  if (!s) return;
  const text = () => (el.querySelector('.sfs-hand-q') ? el.querySelector('.sfs-hand-q').value : s.query);
  el.querySelectorAll('.sfs-copy, .sfs-src-copy').forEach((btn) => { btn.onclick = () => sfsCopy(text()); });
  el.querySelector('.sfs-hand').onclick = () => {
    const over = SFS.plan.overrides || (SFS.plan.overrides = {});
    if (over[s.source]) delete over[s.source];
    else over[s.source] = { query: s.written, reason: '' };
    sfsChanged(true);
  };
  const cog = el.querySelector('.sfs-cog');
  if (cog) cog.onclick = () => sfsCog(s.source);
  const acc = el.querySelector('.sfs-acc');
  if (acc) sfsBindAcc(acc, s.source);
  sfsBindDrops(el);
  const q = el.querySelector('.sfs-hand-q');
  const why = el.querySelector('.sfs-hand-why');
  if (q) {
    grow(q, 3);
    q.oninput = () => {
      grow(q, 3);
      SFS.plan.overrides[s.source] = { query: q.value, reason: why.value };
      el.querySelector('.sfs-q').textContent = q.value || ' ';
      el.querySelectorAll('.sfs-copy, .sfs-src-copy').forEach((btn) => { btn.disabled = !q.value.trim(); });
      sfsChanged();
    };
    why.oninput = () => { SFS.plan.overrides[s.source] = { query: q.value, reason: why.value }; sfsChanged(); };
  }
}

async function sfsCopy(text) {
  try {
    await navigator.clipboard.writeText(text);
    say(t('sift_search.copied'));
  } catch { say(t('sift_search.no_copy'), 6000); }
}

/* where a version was registered, its registry and its number or link, a link opened in a new tab,
   or empty for one registered before the registry was kept */
function sfsWhere(v) {
  const registry = String((v && v.registry) || '').trim();
  const number = String((v && v.registration) || '').trim();
  if (!registry) return '';
  const said = /^https?:\/\/[^\s<>"']+$/i.test(number)
    ? `<a href="${escAttr(number)}" target="_blank" rel="noopener noreferrer">${esc(number)}</a>` : esc(number);
  return ` ${number ? t('sift_search.where_number_html', { registry: esc(registry), number: said }) : t('sift_search.where_html', { registry: esc(registry) })}`;
}

/* The plan's state and Register (12 October, later). The plan's state is one tag beside its heading,
   Draft or Registered with the date, and the version's number only once there is more than one
   version, the earlier ones under Earlier versions, each with its reason, where it was registered
   and its plan as search_plan.md had it. Register holds Export search_plan.md, which writes the file
   at any time, with Open and Copy once it is there, and the steps to register it on OSF or PROSPERO,
   then while the plan is a draft the line that says to mark it once registered, its reason after the
   first version, what stands in the way and Mark as registered, and once registered when and where
   with its number or link and that the next edit starts a new draft version. */
function sfsDrawVersion() {
  const d = SFS.data || {};
  const cur = d.current;
  const versions = d.versions || [];
  const many = versions.length > 1;
  const on = !!(cur && cur.registered);
  const tag = $('sfs-state');
  tag.textContent = many && cur
    ? (on ? t('sift_search.state.version_registered', { version: cur.version, day: sfsDay(cur.registered) })
      : t('sift_search.state.version_draft', { version: cur.version }))
    : on ? t('sift_search.state.registered', { day: sfsDay(cur.registered) }) : many ? t('sift_search.state.draft_lower') : t('sift_search.state.draft');
  tag.className = `sfs-tag sfs-state ${on ? 'api' : 'draft'}`;
  // while a phrase holds truncation the plan is not saved, every change of the screen held until it is
  // written in full (14 October)
  if (sfsUnsaved()) {
    tag.textContent = t('sift_search.state.not_saved');
    tag.className = 'sfs-tag sfs-state unsaved';
  }
  tag.hidden = false;
  const before = versions.filter((v) => !cur || v.version !== cur.version).reverse();
  $('sfs-versions').hidden = !before.length;
  const shut = !SFS.open.has('versions');
  $('sfs-versions-toggle').setAttribute('aria-expanded', String(!shut));
  $('sfs-version-list').hidden = shut;
  $('sfs-version-list').innerHTML = before.map((v) => `<div class="sfs-ver-one"><p class="sfs-ver-head">`
    + `${v.registered ? t('sift_search.state.version_registered_html', { version: esc(v.version), day: esc(sfsDay(v.registered)), where: sfsWhere(v) })
      : esc(t('sift_search.state.version_draft', { version: v.version }))}</p>`
    + `${v.reason ? `<p>${esc(v.reason)}</p>` : ''}${v.text ? `<pre class="sfs-q sfs-md">${esc(v.text)}</pre>` : ''}</div>`).join('');
  $('sfs-reg-when').hidden = !on;
  $('sfs-reg-when').innerHTML = on ? t('sift_search.reg_when_html', { day: esc(sfsDay(cur.registered)), where: sfsWhere(cur) }) : '';
  $('sfs-reg-draft').hidden = on;
  $('sfs-reg-steps').hidden = on;
  const draftAfter = !!(cur && !cur.registered && cur.version > 1);
  $('sfs-why-line').hidden = !draftAfter;
  if (document.activeElement !== $('sfs-why')) $('sfs-why').value = SFS.reason;
  const problems = d.problems || [];
  $('sfs-problems').innerHTML = problems.map((p) => `<p>${esc(p)}</p>`).join('');
  $('sfs-problems').hidden = !problems.length;
  $('sfs-mark').disabled = !cur || on || !!problems.length || sfsUnsaved();
  $('sfs-export').disabled = !cur;
  // Open beside Export once search_plan.md is there, and Copy once Export has written it here
  $('sfs-reg-open').hidden = !d.plan_file;
  $('sfs-md-copy').hidden = !d.exported;
  $('sfs-reg-next').hidden = !on;
}

function sfsDay(iso) {
  const at = new Date(iso);
  if (Number.isNaN(at.getTime())) return String(iso || '');
  return tDate(at, { day: 'numeric', month: 'long', year: 'numeric' });
}

// and since 14 October Checking truncation while a run counts a database's truncated terms first
const SFS_STATE = { waiting: t('sift_search.state.waiting'), running: t('sift_search.state.running'),
  awaiting: t('sift_search.state.awaiting'), checking: t('sift_search.state.checking') };

function sfsStateWord(row) {
  const hits = () => t('sift_search.state.hits', { n: Number(row.hits) || 0, saved: row.saved });
  if (row.state === 'done') return hits();
  if (row.state === 'failed') return t('sift_search.state.failed');
  // set_aside since 31 October, a run's file from before it saying so only in its note's words, which are English
  if (row.state === 'awaiting' && (row.set_aside || (row.set_aside === undefined && /set aside/.test(row.note || '')))) return t('sift_search.state.set_aside');
  if (SFS_STATE[row.state]) return SFS_STATE[row.state];
  return row.hits != null && String(row.hits) !== '' ? hits() : '';
}

/* where a database searched on its own site is searched: its page, and its name as the link says it,
   the platform's for PsycInfo and CINAHL, and none for a database he named */
function sfsSite(s) {
  const cat = SFS.catalog;
  if (sfsIsOther(s)) return null;
  if ((cat.platformed || []).includes(s)) {
    const p = (SFS.plan.platforms || {})[s] || 'ebsco';
    return { url: (cat.platform_sites || {})[p] || '', name: (cat.hosts || {})[p] || p };
  }
  return { url: (cat.sites || {})[s] || '', name: cat.names[s] || s };
}

/* the drop for a database's export, on its row under Searches, or on a run waiting for it, `run` */
const sfsDropHtml = (s, run) => `<label class="sfs-drop" data-s="${escAttr(s)}"${run ? ` data-run="${escAttr(run)}"` : ''}>`
  + `<input type="file" accept=".ris,.csv,.txt,.bib" hidden>${esc(t('sift_search.drop'))}</label>`;

/* What to do for a database searched on its own site, in order: copy the search, open its site in a
   new tab, run the search there, export the records, then drop the file on the row. Copy the search
   is held while there is no search to copy, `empty` (17 October, later) */
function sfsSteps(s, empty = false) {
  const site = sfsSite(s);
  const name = sfsName(s);
  const open = site && site.url
    ? `<li>${t('sift_search.todo.open_html', { link: `<a class="sfs-site" href="${escAttr(site.url)}" target="_blank" rel="noopener noreferrer">${esc(t('sift_search.todo.open_link', { name: site.name }))}</a>` })}</li>`
    : '';
  const run = s === 'scholar' ? `<li>${esc(t('sift_search.todo.scholar'))}</li><li>${esc(t('sift_search.todo.scholar_csv'))}</li>`
    : `<li>${site && site.url ? esc(t('sift_search.todo.run_there')) : esc(t('sift_search.todo.run_on', { name }))}</li>`
      + `<li>${esc(t('sift_search.todo.export'))}</li>`;
  return `<ol class="sfs-todo"><li><button type="button" class="ghost small sfs-src-copy"${empty ? ' disabled' : ''}>${esc(t('sift_search.todo.copy'))}</button></li>`
    + `${s === 'scholar' ? '' : open}${run}<li>${sfsDropHtml(s)}</li></ol>`;
}

/* each drop under `el` bound, a file chosen going where its row says */
function sfsBindDrops(el) {
  el.querySelectorAll('.sfs-drop input').forEach((input) => {
    input.onchange = () => {
      const zone = input.closest('.sfs-drop');
      if (input.files && input.files[0]) sfsDropFile(zone.dataset.s, input.files[0], zone.dataset.run || null);
    };
  });
}

/* the folder name of the run whose screening the review's Screening step opens, as the server keeps
   it: the run he opened last, else the newest that holds a screening */
function sfsOpensDay() {
  if (SFS.review && 'opens' in SFS.review) return SFS.review.opens || null;
  const r = SFS.runs.find((x) => x.screening);
  return r ? r.date : null;
}

/* a run by its folder's name, the one the runs list holds, else its day and the number the server gives
   beside its name for it, `label` (31 October 2026, read out of the label's words before), else that name as
   it stands */
function sfsRunNamed(name, label, number) {
  const held = SFS.runs.find((x) => x.date === name);
  if (held) return held;
  const m = /^(\d{4}-\d{2}-\d{2})(?:-(\d+))?$/.exec(String(name || ''));
  if (m && Number(number) > 0) return { date: name, day: m[1], number: Number(number) };
  return m && !label ? { date: name, day: m[1], n: Number(m[2] || 1) } : { date: name, label: label || String(name || '') };
}

/* A run by its number in the order the runs were made and its day, the year only when it is not this
   year (12 October, later): Run 1, 8 October, then Run 2, 12 October and Run 3, 12 October, the
   number the server keeps for it. A run named only as the server names it keeps those words. */
function sfsRunWords(r) {
  if (!r) return '';
  const day = String(r.day || r.date || '');
  const at = new Date(`${day}T12:00:00`);
  let words = day;
  if (/^\d{4}-\d{2}-\d{2}$/.test(day) && !Number.isNaN(at.getTime())) {
    const year = day.slice(0, 4) !== String(SFS.today || '').slice(0, 4);
    words = tDate(at, year ? { day: 'numeric', month: 'long', year: 'numeric' } : { day: 'numeric', month: 'long' });
  }
  if (Number(r.number) > 0) return t('sift_search.run_n', { n: Number(r.number), day: words });
  return r.label || words;
}

/* Search runs (12 October, later): a table of the runs made, newest first, a row each, then New run
   under it, what it will search, each database and how, and as a run goes each database's state,
   then Start new run and which run's decisions it keeps. */
function sfsDrawRun() {
  const d = SFS.data || {};
  const cur = d.current;
  const live = SFS.running;
  $('sfs-runs').innerHTML = SFS.runs.map(sfsRunRow).join('');
  $('sfs-runs-table').hidden = !SFS.runs.length;
  sfsBindOpen($('sfs-runs'));
  sfsBindDrops($('sfs-runs'));
  $('sfs-runs').querySelectorAll('.sfs-details-toggle').forEach((btn) => {
    btn.onclick = () => {
      const key = `run:${btn.dataset.date}`;
      if (SFS.open.has(key)) SFS.open.delete(key); else SFS.open.add(key);
      sfsDrawRun();
      const again = $('sfs-runs').querySelector(`.sfs-details-toggle[data-date="${btn.dataset.date}"]`);
      if (again) again.focus();
    };
  });
  // the line says nothing while the plan names no database, where it stood over an empty list (17 October)
  const shown = sfsShownOrder();
  $('sfs-new-what').textContent = !shown.length ? ''
    : cur && cur.registered ? t('sift_search.new.registered')
      : t('sift_search.new.trial');
  $('sfs-new-what').hidden = !shown.length;
  $('sfs-sources').innerHTML = shown.map((s) => {
    const r = (live && (live.sources || {})[s]) || {};
    const exported = sfsExported(s, r);
    return `<li class="sfs-src${r.state ? ` ${r.state}` : ''}" data-s="${s}"><span class="sfs-src-name">${sfDbPill(sfsName(s))}</span>`
      + `<span class="sfs-src-how">${exported ? esc(t('sift_search.by_export')) : esc(t('sift_search.by_api'))}</span><span class="sfs-src-state">${esc(live ? sfsStateWord(r) : '')}</span></li>`;
  }).join('');
  // held, as Mark as registered is, while something stands in the way of the plan, which a run would refuse
  // (17 October, later, where it stood filled and refused in a toast)
  $('sfs-run').disabled = !!live || !cur || SFS.checking || !!(d.problems || []).length || sfsUnsaved();
  sfsDrawCheck(live);
  sfsDrawFollows(live);
  // Screen by title and abstract ready once a run has a screening
  if (SFS.review && $('sfs-steps')) rvStepsDraw($('sfs-steps'), SFS.review, 'searches', SFS.stages);
}

/* Whether the plan on the screen stands unsaved, a phrase holding truncation (14 October), as the last
   save's answer says */
const sfsUnsaved = () => !!(SFS.data && (SFS.data.unsaved || []).length);

/* Whether Check truncation has anything to count: the newest version holds a truncated term and a
   database that takes truncation goes by API */
function sfsCheckable() {
  const d = SFS.data || {};
  const takes = (SFS.catalog && SFS.catalog.truncates) || [];
  return !!(d.current && Number(d.truncated) > 0 && (SFS.plan.databases || []).some((s) => takes.includes(s) && !sfsExported(s)));
}

/* Check truncation under New run (14 October), the dry run's truncation check on the screen: each
   truncated term counted alone in each database searched by API that takes truncation, with and
   without its asterisk, in a table, a row a term in each database, its flag beside it. Shown only when
   there is something to count, held while the plan is unsaved or a run goes, and the table kept until
   the plan changes. A run checks again first and keeps the table in its folder. */
function sfsDrawCheck(live) {
  const btn = $('sfs-check-go');
  btn.hidden = !sfsCheckable();
  btn.disabled = !!live || SFS.checking || sfsUnsaved();
  btn.textContent = SFS.checking ? t('sift_search.check.checking') : t('sift_search.check.go');
  const box = $('sfs-check');
  const rows = (SFS.terms && SFS.terms.rows) || [];
  box.hidden = !rows.length || btn.hidden;
  if (box.hidden) { box.innerHTML = ''; return; }
  const num = (n) => (n == null ? '' : tNum(Number(n)));
  const cell = (label, html, cls = '') => `<td class="${cls}" data-label="${label}">${html}</td>`;
  box.innerHTML = `<table class="sfs-terms-table"><caption>${esc(t('sift_search.check.caption'))}</caption>`
    + `<thead><tr><th scope="col">${esc(t('sift_search.check.term'))}</th><th scope="col">${esc(t('sift_search.check.database'))}</th>`
    + `<th scope="col" class="sfs-num">${esc(t('sift_search.check.with'))}</th>`
    + `<th scope="col" class="sfs-num">${esc(t('sift_search.check.without'))}</th><th scope="col">${esc(t('sift_search.check.flag'))}</th></tr></thead><tbody>`
    + rows.map((r) => `<tr${r.flag ? ' class="sfs-flagged"' : ''}><th scope="row">${esc(r.term)}</th>`
      + cell(esc(t('sift_search.check.database')), esc(r.name)) + cell(esc(t('sift_search.check.with')), num(r.with), 'sfs-num')
      + cell(esc(t('sift_search.check.without')), num(r.without), 'sfs-num')
      + cell(esc(t('sift_search.check.flag')), r.flag ? esc(r.flag) : r.said ? esc(r.said) : '', 'sfs-flag') + '</tr>').join('')
    + '</tbody></table>';
}

/* Check truncation pressed: the plan's last change saved, then the check asked of the server, which asks
   each database for its counts and writes nothing */
async function sfsCheck() {
  await sfsFlush();
  if (sfsUnsaved() || SFS.checking) return;
  SFS.checking = true;
  sfsDrawRun();
  try {
    SFS.terms = await api('/api/sift-search', { op: 'terms', folder: SFS.folder });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
  SFS.checking = false;
  sfsDrawRun();
}

/* The earlier runs the next run may follow: those whose screening holds a decision, an earlier run of
   today among them, since Run makes a new run after them, newest first, as the server lists the runs */
function sfsFollowChoices(runs, today) {
  return (runs || []).filter((r) => r.screening && Number(r.decided) > 0 && String(r.day || r.date) <= String(today));
}

/* Keep the decisions from, beside Start new run: the earlier runs with decisions, each by its name
   as the runs list gives it, the newest chosen at first, and No earlier run. A run that follows one
   carries its screening, every record with its decisions, and adds the new ones. */
function sfsDrawFollows(live) {
  const choices = sfsFollowChoices(SFS.runs, SFS.today);
  if (SFS.follows !== 'none' && !choices.some((r) => r.date === SFS.follows)) SFS.follows = choices.length ? choices[0].date : 'none';
  $('sfs-follow-line').hidden = !choices.length;
  $('sfs-follows').innerHTML = choices.map((r) => `<option value="${escAttr(r.date)}">${esc(sfsRunWords(r))}</option>`).join('')
    + `<option value="none">${esc(t('sift_search.follow.none'))}</option>`;
  $('sfs-follows').value = choices.length ? SFS.follows : 'none';
  $('sfs-follows').disabled = !!live;
}

/* What OpenAlex filled in a run, the abstracts, the records whose authors it filled and those whose
   counts of citations it filled, each said only when it is more than nought, the last two joined by
   and, or empty */
function sfsFilled(r) {
  const abstracts = Number(r.filled) || 0;
  const authors = Number(r.authors_filled) || 0;
  const cited = Number(r.cited_filled) || 0;
  const parts = [abstracts ? t('sift_search.filled.abstracts', { n: abstracts }) : '',
    authors ? t('sift_search.filled.authors', { n: authors }) : '',
    cited ? t('sift_search.filled.cited', { n: cited }) : ''].filter(Boolean);
  // and since 13 October Sift's own columns from OpenAlex, its retractions, open access, countries and references
  const own = Number(r.openalex_filled) || 0;
  if (own) parts.push(t('sift_search.filled.openalex', { n: own }));
  return tList(parts);
}

/* A run's row in the table (12 October, later): its number and day, Trial or Registered search, the
   records found, those after duplicates, a run that follows another counting its new records, and
   the benchmark papers found, then Active on the run Screening has open and Make active on another
   with a screening, which opens it in Screening. Under it, a run that waits for an export says which
   and takes the drop, a database that failed says so, and Details opens each database's search, what
   OpenAlex filled, the decisions kept and the benchmark papers missed. */
function sfsRunRow(r) {
  const opens = sfsOpensDay();
  const rows = r.rows || [];
  const awaiting = rows.filter((x) => x.state === 'awaiting' && x.source);
  const failed = rows.filter((x) => x.state === 'failed');
  const notRun = rows.some((x) => x.state === 'waiting');
  const f = r.follows && r.follows.date && r.follows.carried != null ? r.follows : null;
  const kind = !r.version ? '' : r.draft ? `<span class="sfs-tag draft">${esc(t('sift_search.runs.trial'))}</span>`
    : `<span class="sfs-tag api">${esc(t('sift_search.runs.registered'))}</span>`;
  let found = '';
  let after = '';
  let bench = '';
  if (notRun) found = esc(t('sift_search.runs.not_run'));
  else if (!r.screening && r.records != null && Number(r.records) === 0 && !awaiting.length) found = esc(t('sift_search.runs.none_came'));
  else if (r.records != null && r.merged != null) {
    const n = Number(r.benchmark) || 0;
    const missed = (r.missed || []).length;
    found = String(Number(r.records) || 0);
    after = f ? esc(t('sift_search.runs.new', { n: Number(f.new) || 0 })) : String(Number(r.merged) || 0);
    bench = n ? `<span${missed ? ' class="sfs-missed"' : ''}>${esc(t('sift_search.runs.of', { part: n - missed, all: n }))}</span>` : '';
  } else if (r.merged != null) after = String(Number(r.merged) || 0);
  const open = !r.screening ? ''
    : r.date === opens ? `<span class="sfs-tag sfs-open-tag">${esc(t('sift_search.runs.active'))}</span>`
      : `<button type="button" class="ghost small sfs-open-run" data-date="${escAttr(r.date)}">${esc(t('sift_search.runs.make_active'))}</button>`;
  const waits = awaiting.map((x) => `<div class="sfs-run-wait"><span>${esc(t('sift_search.runs.waiting', { name: x.name }))}</span>${sfsDropHtml(x.source, r.date)}</div>`).join('');
  // a failed database in the server's plain words, which database, what happened and its status in brackets,
  // never an address or what the server's answer held, which the run's log keeps (17 October, later)
  const fails = failed.map((x) => `<p class="sfs-run-fail">${esc(x.said || t('sift_search.runs.failed', { name: x.name }))}</p>`).join('');
  const more = sfsRunMore(r, f);
  const cell = (label, html, cls = '') => `<td class="${cls}" data-label="${label}">${html}</td>`;
  return `<tr class="sfs-run" data-date="${escAttr(r.date)}"><th scope="row" class="sfs-run-name">${esc(sfsRunWords(r))}</th>`
    + cell(esc(t('sift_search.runs.search')), kind, 'sfs-run-kind') + cell(esc(t('sift_search.screen.records_found')), found, 'sfs-num')
    + cell(esc(t('sift_search.screen.after_duplicates')), after, 'sfs-num')
    + cell(esc(t('sift_search.screen.benchmark_papers_found')), bench, 'sfs-num') + cell('', open, 'sfs-run-open') + '</tr>'
    + (waits || fails || more ? `<tr class="sfs-run-sub" data-date="${escAttr(r.date)}"><td colspan="6">${waits}${fails}${more}</td></tr>` : '');
}

/* a run's Details, opened by its button: each database's search, the plan's version when there is
   more than one, what OpenAlex filled, the decisions kept and the benchmark papers missed, each missed
   one with its title where known */
function sfsRunMore(r, f) {
  const lines = (r.rows || []).filter((x) => x.name).map((x) => {
    const how = !x.how ? x.name : x.how === 'api' ? t('sift_search.more.by_api', { name: x.name }) : t('sift_search.more.by_export', { name: x.name });
    const state = sfsStateWord(x);
    return `<li>${esc(state ? t('sift_search.more.state', { what: how, state }) : how)}</li>`;
  });
  if (r.version && ((SFS.data && SFS.data.versions) || []).length > 1) lines.push(`<li>${esc(t('sift_search.more.version', { version: r.version }))}</li>`);
  const filled = sfsFilled(r);
  if (filled) lines.push(`<li>${esc(t('sift_search.more.filled', { what: filled[0].toUpperCase() + filled.slice(1) }))}</li>`);
  if (f) {
    lines.push(`<li>${esc(t('sift_search.more.kept', { run: sfsRunWords(sfsRunNamed(f.date, f.label, f.number)),
      n: Number(f.carried) || 0, again: Number(f.again) || 0 }))}</li>`);
  }
  if ((r.missed || []).length && Number(r.benchmark)) lines.push(`<li class="sfs-missed">${t('sift_search.more.missed_html', { papers: r.missed.map(sfsDoiWords).join(', ') })}</li>`);
  // each flag of the truncation check the run made first (14 October)
  ((r.terms && r.terms.flags) || []).forEach((f) => lines.push(`<li class="sfs-missed">${esc(f)}</li>`));
  if (!lines.length) return '';
  const open = SFS.open.has(`run:${r.date}`);
  return `<div class="sfs-run-more">${sfsToggleHtml('sfs-details-toggle', t('sift_search.more.details'), open).replace('<button ', `<button data-date="${escAttr(r.date)}" `)}`
    + `${open ? `<ul>${lines.join('')}</ul>` : ''}</div>`;
}

/* Make active on a run: that run opened in Screening through the screening op, which makes it the
   run Screening opens from then on */
function sfsBindOpen(el) {
  el.querySelectorAll('.sfs-open-run').forEach((btn) => {
    btn.onclick = async () => {
      let got;
      try {
        got = await api('/api/sift-search', { op: 'screening', folder: SFS.folder, date: btn.dataset.date });
      } catch (err) { say(err.message, 9000); return; }
      $('sift-search').hidden = true;
      siftOpen(got.folder, () => { $('sift-search').hidden = false; });
    };
  });
}

/* search_plan.md of the review's folder opened in the computer's own app for it */
async function sfsOpenFile(file) {
  try {
    await api('/api/sift-search', { op: 'open', folder: SFS.folder, file });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* ── saving ── */

/* A change to the plan, saved a moment after the last one, or at once for a choice made with a click */
function sfsChanged(now = false) {
  clearTimeout(SFS.saveTimer);
  // a change to the plan leaves the last Check truncation's table behind it
  SFS.terms = null;
  if (now) { SFS.saveTimer = null; sfsSave(); return; }
  SFS.saveTimer = setTimeout(() => { SFS.saveTimer = null; sfsSave(); }, 500);
}

function sfsSave() {
  const plan = JSON.parse(JSON.stringify(SFS.plan));
  const reason = SFS.reason;
  SFS.chain = SFS.chain.then(async () => {
    // a save refused since the plan changed under the page waits for Reload or Overwrite
    if (SFS.stale) return;
    // the plan's version as this page last read it, so a save over another window's is refused
    const seen = (SFS.data && SFS.data.plan_version) || null;
    const got = await api('/api/sift-search', { op: 'save', folder: SFS.folder, plan, reason, seen });
    // the fields keep what is being typed, and the answer moves the strings, the version and the problems,
    // and since 14 October whether the plan stands unsaved, a phrase holding truncation
    SFS.data = Object.assign({}, SFS.data, got, { runs: SFS.data.runs, unsaved: got.unsaved || [] });
    sfsDrawAnswer();
    sfsDrawBenchTitles();
  }).catch(sfsSaveFailed);
  return SFS.chain;
}

/* A save that failed: one refused since the plan changed in another window shows the card at the
   head of the screen, with what he typed still in the fields, and any other says its line. */
function sfsSaveFailed(err) {
  if (err && err.data && err.data.stale) { sfsStaleShow(err.data.stale); return; }
  say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
}

function sfsStaleShow(stale) {
  SFS.stale = { version: String((stale && stale.version) || ''), reasons: !!(SFS.stale && SFS.stale.reasons) };
  const box = $('sfs-stale');
  if (box) box.hidden = false;
}

function sfsStaleHide() {
  SFS.stale = null;
  const box = $('sfs-stale');
  if (box) box.hidden = true;
}

/* Reload: the plan as the file holds it now, what was typed since the last save let go. */
function sfsStaleReload() {
  const folder = SFS.folder;
  clearTimeout(SFS.saveTimer);
  clearTimeout(SFS.reasonTimer);
  SFS.saveTimer = null;
  SFS.reasonTimer = null;
  sfsStaleHide();
  if (folder) sfsOpen(folder);
}

/* Overwrite: what is on the screen saved over the plan as it now stands, the plan's version the
   refusal named sent with it, so a change made after that one is refused in turn. */
function sfsStaleOverwrite() {
  const s = SFS.stale;
  sfsStaleHide();
  if (!s || !SFS.data) return;
  SFS.data = Object.assign({}, SFS.data, { plan_version: s.version });
  sfsSave();
  if (s.reasons) sfsReasonsSave();
}

/* the plan's last change and the reasons' saved before an act that reads them */
async function sfsFlush() {
  if (SFS.saveTimer) { clearTimeout(SFS.saveTimer); SFS.saveTimer = null; sfsSave(); }
  if (SFS.reasonTimer) { clearTimeout(SFS.reasonTimer); SFS.reasonTimer = null; sfsReasonsSave(); }
  await SFS.chain;
}

/* ── register and run ── */

/* the question card, its Yes a Remove button in red with its bin when it removes */
function sfsAsk(head, line, yes, removes = false) {
  $('sfs-ask-head').textContent = head;
  $('sfs-ask-line').textContent = line;
  $('sfs-ask-yes').textContent = yes;
  $('sfs-ask-yes').className = removes ? 'primary btn-remove' : 'primary';
  $('sfs-ask').hidden = false;
  $('sfs-ask-yes').focus();
  return new Promise((resolve) => {
    SFS.askDone = (ok) => { $('sfs-ask').hidden = true; SFS.askDone = null; resolve(ok); };
  });
}

/* Export search_plan.md: the newest version, a draft or registered, written to the review's folder
   through the export op, ready to register on OSF or PROSPERO. Nothing is frozen or sent. */
async function sfsExport() {
  await sfsFlush();
  try {
    const got = await api('/api/sift-search', { op: 'export', folder: SFS.folder });
    SFS.data = Object.assign({}, SFS.data, got, { runs: SFS.data.runs });
    sfsDrawAnswer();
    say(t('sift_search.plan_written'));
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* the registry Mark as registered names: OSF, PROSPERO or another by the name typed */
function sfsMarkRegistry() {
  if ($('sfs-reg-osf').checked) return 'OSF';
  if ($('sfs-reg-prospero').checked) return 'PROSPERO';
  return $('sfs-reg-other').checked ? $('sfs-registry-other').value.trim() : '';
}

/* Mark as registered held until the registry and its number or link are given */
function sfsMarkReady() {
  $('sfs-registry-other').hidden = !$('sfs-reg-other').checked;
  $('sfs-mark-yes').disabled = !sfsMarkRegistry() || !$('sfs-registration').value.trim();
}

/* Mark as registered (12 October, later): a card that says it freezes this version and asks where
   it is registered, OSF, PROSPERO or another, and its registration number or link, both needed */
async function sfsMark() {
  await sfsFlush();
  const cur = SFS.data && SFS.data.current;
  if (!cur || cur.registered) return;
  $('sfs-mark-line').textContent = t('sift_search.mark.line', { version: cur.version });
  ['sfs-reg-osf', 'sfs-reg-prospero', 'sfs-reg-other'].forEach((id) => { $(id).checked = false; });
  $('sfs-registry-other').value = '';
  $('sfs-registration').value = '';
  sfsMarkReady();
  $('sfs-mark-card').hidden = false;
  $('sfs-reg-osf').focus();
}

function sfsMarkShut() {
  $('sfs-mark-card').hidden = true;
  $('sfs-mark').focus();
}

/* the version frozen through the register op with its registry and its number or link */
async function sfsMarkGo() {
  const registry = sfsMarkRegistry();
  const registration = $('sfs-registration').value.trim();
  if (!registry || !registration) return;
  try {
    const got = await api('/api/sift-search', { op: 'register', folder: SFS.folder, reason: SFS.reason, registry, registration });
    SFS.data = Object.assign({}, SFS.data, got, { runs: SFS.data.runs });
    SFS.reason = '';
    $('sfs-mark-card').hidden = true;
    sfsDrawAnswer();
    say(t('sift_search.mark.done'));
  } catch (err) { say(err.message, 9000); }
}

/* Start new run: a new run of the newest version on the server's own thread, asked after until it ends */
async function sfsRun() {
  await sfsFlush();
  // a plan held unsaved by a phrase with truncation is not run, its last saved version neither (14 October)
  if (sfsUnsaved()) return;
  const follows = sfsFollowChoices(SFS.runs, SFS.today).length ? SFS.follows : 'none';
  try {
    const got = await api('/api/sift-search', { op: 'run', folder: SFS.folder, follows });
    SFS.running = got.running;
  } catch (err) { say(err.message, 9000); return; }
  sfsDrawRun();
  sfsPoll();
}

/* The run under way asked after until it ends, each database's state drawn as it lands. A run that
   ends opens nothing: its screening opens when he presses Make active on its row, and until then
   Screening opens the run he opened last, as the review the server sends back says. */
function sfsPoll() {
  clearTimeout(SFS.poll);
  SFS.poll = setTimeout(async () => {
    if (!sfsShown() || !SFS.folder) return;
    let got;
    try { got = await api('/api/sift-search', { op: 'progress', folder: SFS.folder }); } catch (err) { say(err.message, 9000); return; }
    const held = got.running;
    if (held && held.running) {
      SFS.running = held;
      sfsDrawRun();
      sfsPoll();
      return;
    }
    SFS.running = null;
    if (got.runs) SFS.runs = got.runs;
    if (got.titles) SFS.titles = got.titles;
    if (got.review) SFS.review = got.review;
    if (held && held.error) say(held.error, 9000);
    sfsDrawRun();
    sfsDrawBenchTitles();
  }, 700);
}

/* An export dropped on a database's row under Searches, or chosen, kept in the run the screen shows,
   today's newest, named by its folder, so it never goes into an earlier run of the day (12 October),
   and one dropped on a run waiting for it, `run`, in that run. With no run today the server begins
   one. A run made since the screen was drawn is said, and the runs drawn afresh. */
async function sfsDropFile(source, file, run = null) {
  if (!/\.(ris|csv|txt|bib)$/i.test(file.name || '')) { say(t('sift_search.not_ris')); return; }
  const shown = (run && SFS.runs.find((r) => r.date === run)) || SFS.runs.find((r) => (r.day || r.date) === SFS.today) || null;
  try {
    await SFS.chain;
    const data = await tbBase64(file);
    const got = await api('/api/sift-search', { op: 'drop', folder: SFS.folder, source, name: file.name, data,
      run: shown ? shown.date : undefined });
    SFS.runs = got.runs || SFS.runs;
    if (got.titles) SFS.titles = got.titles;
    if (got.review) SFS.review = got.review;
    sfsDrawRun();
    sfsDrawBenchTitles();
    say(t('sift_search.took', { n: got.taken.records, file: file.name }));
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    // the runs as they stand now, so a run made since shows and takes the next drop
    try {
      const now = await api('/api/sift-search', { op: 'runs', folder: SFS.folder });
      if (now.runs) { SFS.runs = now.runs; sfsDrawRun(); }
    } catch { /* drawn as it stands */ }
  }
}

/* a file dragged over the screen is taken by a database's row alone, and nowhere else opens it */
function sfsDrag(e) {
  if (!sfsShown() || !e.dataTransfer || !Array.from(e.dataTransfer.types || []).includes('Files')) return;
  e.preventDefault();
  const zone = e.target && e.target.closest ? e.target.closest('.sfs-drop') : null;
  document.querySelectorAll('.sfs-drop.dragging').forEach((z) => { if (z !== zone) z.classList.remove('dragging'); });
  if (zone) zone.classList.add('dragging');
  e.dataTransfer.dropEffect = zone ? 'copy' : 'none';
}

function sfsDrop(e) {
  if (!sfsShown() || !e.dataTransfer || !e.dataTransfer.files || !e.dataTransfer.files.length) return;
  e.preventDefault();
  const zone = e.target && e.target.closest ? e.target.closest('.sfs-drop') : null;
  document.querySelectorAll('.sfs-drop.dragging').forEach((z) => z.classList.remove('dragging'));
  if (zone) sfsDropFile(zone.dataset.s, e.dataTransfer.files[0], zone.dataset.run || null);
}


/* The screen's keys, ahead of every other screen's, which hear none of them: Esc closes the
   question card, Mark as registered's card, Add database's name field or a field, Enter takes the
   card's answer, adds the database named, saves the key typed, or takes a DOI or a reason as leaving
   its field does, and every other key types. */
function sfsKeyDown(e) {
  // Settings opened over the screen keeps its own keys
  if (!sfsShown() || ($('settings') && !$('settings').hidden) || ($('feedback') && !$('feedback').hidden)) return;
  // Search's card over the screen keeps its own keys (18 October, search.js)
  if (e.target && e.target.closest && e.target.closest('.search-card')) return;
  e.stopPropagation();
  if (!$('sfs-ask').hidden) {
    if (e.key === 'Escape' || e.key === 'Enter') { e.preventDefault(); if (SFS.askDone) SFS.askDone(e.key === 'Enter'); }
    return;
  }
  // Mark as registered's card: Esc shuts it, and Enter marks the plan once both are given
  if ($('sfs-mark-card') && !$('sfs-mark-card').hidden) {
    if (e.key === 'Escape') { e.preventDefault(); sfsMarkShut(); }
    if (e.key === 'Enter' && e.target && e.target.matches && e.target.matches('input[type="text"]')) {
      e.preventDefault();
      if (!$('sfs-mark-yes').disabled) sfsMarkGo();
    }
    return;
  }
  const t = e.target;
  // Alt and an arrow on a reason's handle move the reason, as on the home screen's rows
  const grip = t && t.closest && t.closest('#sfs-reasons button.pc-grip');
  if (grip && gripKeys(e, grip.closest('.sfs-reason'), $('sfs-reasons'), sfsReasonGrip())) return;
  if (e.key === 'Enter' && t && t.matches && t.matches('#sfs-db-name, #sift-search .dbs-key-field')) {
    e.preventDefault();
    const go = t.id === 'sfs-db-name' ? $('sfs-db-go') : t.parentElement.querySelector('.dbs-key-save');
    if (go) go.click();
    return;
  }
  // Enter in Add a key work's line finds it, and Esc there shuts the line
  if (t && t.matches && t.matches('#sfs-kw-text, #sfs-kw-year')) {
    if (e.key === 'Enter') { e.preventDefault(); sfsKwFind(); return; }
    if (e.key === 'Escape') { e.preventDefault(); SFS.kwAdding = false; SFS.kwPicks = null; sfsDrawKeys(); $('sfs-kw-new').focus(); return; }
  }
  // Enter in a benchmark paper's DOI or a reason's field takes it, as leaving the field does
  if (e.key === 'Enter' && t && t.matches && t.matches('.sfs-doi, .sfs-rcode, .sfs-rmeaning')) {
    e.preventDefault();
    t.blur();
    return;
  }
  if (e.key === 'Escape' && t && t.id === 'sfs-db-name') { SFS.adding = false; sfsDrawDatabases(); $('sfs-db-add').focus(); return; }
  if (e.key === 'Escape' && document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
}

/* ── Databases, under Sift in Settings ── */

/* His own list of the databases he searches, whatever the AI switch says: each row a database, the
   platform where it has several, By API where Sift has an API for it or By export, and for By API its
   key fields, Remove for the row, then Add from the databases Sift knows or Other by name. The list
   goes with Save at the foot of Settings. A key goes at once with its own Save, to the keychain as the
   Anthropic key does, and its field is emptied as it goes and shows only Saved or Not set. Check sends
   a search for one record with the key and says in one line whether the database took it. A server
   from before the list answers with no endpoint, and the section stands down behind one line. Each
   database's cog on Search strategy draws the same access through the same functions, and writes the
   same list at once. */
const DBS = { rows: null, saved: {}, catalog: null, said: {}, failed: {} };

async function dbsLoad(into = false) {
  if (!$('dbs-list')) return;
  DBS.rows = null;
  DBS.said = {};
  DBS.failed = {};
  let got;
  try {
    got = await api('/api/databases', { op: 'read' });
  } catch (err) {
    const old = needsRestart(err);
    $('dbs-restart').hidden = !old;
    $('dbs-list').innerHTML = old ? '' : `<li class="fineprint">${esc(err.message)}</li>`;
    $('dbs-add-line').hidden = true;
    return;
  }
  DBS.rows = (got.rows || []).map((r) => Object.assign({}, r));
  DBS.saved = got.saved || {};
  DBS.catalog = got.catalog;
  $('dbs-restart').hidden = true;
  $('dbs-add-line').hidden = false;
  dbsDraw();
  if (into) requestAnimationFrame(dbsInView);
}

/* the list as Save sends it, or null when it was never drawn, so a Save leaves the file's list alone */
function dbsBody() {
  return DBS.rows ? DBS.rows.map((r) => Object.assign({}, r)) : null;
}

const dbsLabel = (r) => (r.source === 'other' ? r.name : DBS.catalog.names[r.source]);

/* One database's access, drawn alike in Settings' list and under a cog on Search strategy: its
   platform where it has several, By API or By export, and for By API its key fields, each with Save
   and Remove and showing only Saved or Not set, then Check and the one line a key's Save, Remove or
   Check says. `st` is the state drawn from, Settings' own or the screen's, each with the catalogue,
   the keys saved and the lines said, and `id` names the key fields apart. */
function dbsAccessParts(st, r, id, label) {
  const cat = st.catalog;
  const fields = cat.fields || {};
  const opts = sfsPlatforms(cat, r.source, r.platform || 'ebsco');
  const plats = !(cat.platformed || []).includes(r.source) ? ''
    : opts.length > 1
      ? `<select class="dbs-plat" aria-label="${escAttr(t('sift_search.dbs.platform_label', { name: label }))}">${opts.map(([k, w]) => `<option value="${k}"${k === (r.platform || 'ebsco') ? ' selected' : ''}>${esc(w)}</option>`).join('')}</select>`
      : `<span class="dbs-fixed">${esc(opts.length ? opts[0][1] : '')}</span>`;
  const how = (cat.apis || []).includes(r.source)
    ? `<select class="dbs-how" aria-label="${escAttr(t('sift_search.dbs.how_label', { name: label }))}"><option value="api"${r.how === 'api' ? ' selected' : ''}>${esc(t('sift_search.by_api'))}</option>`
      + `<option value="export"${r.how === 'api' ? '' : ' selected'}>${esc(t('sift_search.by_export'))}</option></select>`
    : `<span class="dbs-fixed">${esc(t('sift_search.by_export'))}</span>`;
  const own = r.how === 'api' ? (fields[r.source] || []) : [];
  const keys = own.map((f, n) => `<div class="dbs-key" data-service="${escAttr(f.service)}"><label class="dbs-key-label" for="${id}-${n}">${esc(f.optional ? t('sift_search.dbs.optional', { label: f.label }) : f.label)}</label>`
    + `<input id="${id}-${n}" class="dbs-key-field" type="password" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="${escAttr(st.saved[f.service] ? t('sift_search.dbs.saved') : t('sift_search.dbs.not_set'))}">`
    + `<button type="button" class="ghost small dbs-key-save">${esc(t('sift_search.dbs.save'))}</button>`
    + `<button type="button" class="ghost small btn-remove dbs-key-clear"${st.saved[f.service] ? '' : ' hidden'}>${esc(t('sift_search.remove'))}</button>`
    + '</div>').join('');
  // Check at the foot of the key fields, and the one line a key's Save, Remove or Check says, one that failed in
  // the one warning tint as every failure line is (17 October, later)
  const failed = st.failed && st.failed[r.source] ? ' said-failed' : '';
  const said = st.said[r.source] ? `<span class="fineprint dbs-said${failed}">${esc(st.said[r.source])}</span>` : '';
  const foot = own.length ? `<div class="dbs-foot"><button type="button" class="ghost small dbs-check">${esc(t('sift_search.dbs.check'))}</button>${said}</div>`
    : (said ? `<div class="dbs-foot">${said}</div>` : '');
  return { plats, how, keys: keys + foot };
}

/* The access's controls bound: a platform or how it is searched told to `changed`, how it is searched
   drawn afresh by `redraw`, and each key saved, removed or checked through the same calls */
function dbsBindAccess(st, el, r, redraw, changed) {
  const plat = el.querySelector('.dbs-plat');
  if (plat) plat.onchange = () => { r.platform = plat.value; changed(); };
  const how = el.querySelector('select.dbs-how');
  if (how) how.onchange = async () => { r.how = how.value; await changed(); redraw(); };
  el.querySelectorAll('.dbs-key').forEach((row) => {
    const service = row.dataset.service;
    const field = row.querySelector('.dbs-key-field');
    row.querySelector('.dbs-key-save').onclick = () => dbsSaveKey(st, r.source, service, field, redraw);
    field.onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); dbsSaveKey(st, r.source, service, field, redraw); } };
    row.querySelector('.dbs-key-clear').onclick = () => dbsClearKey(st, r.source, service, redraw);
  });
  const chk = el.querySelector('.dbs-check');
  if (chk) chk.onclick = () => dbsCheck(st, r.source, chk, redraw);
}

function dbsDraw() {
  $('dbs-list').innerHTML = DBS.rows.map((r, i) => {
    const a = dbsAccessParts(DBS, r, `dbs-key-${i}`, dbsLabel(r));
    return `<li class="dbs-row" data-i="${i}"><div class="dbs-head"><span class="dbs-name">${esc(dbsLabel(r))}</span>${a.plats}${a.how}`
      + `<button type="button" class="ghost small btn-remove dbs-remove">${esc(t('sift_search.remove'))}</button></div>${a.keys}</li>`;
  }).join('');
  $('dbs-list').querySelectorAll('.dbs-row').forEach((li) => {
    const r = DBS.rows[Number(li.dataset.i)];
    dbsBindAccess(DBS, li, r, dbsDraw, () => {});
    li.querySelector('.dbs-remove').onclick = () => { DBS.rows.splice(Number(li.dataset.i), 1); dbsDraw(); };
  });
  dbsDrawPick();
}

/* Add offers the databases Sift knows that the list does not hold yet, then Other, which asks its name */
function dbsDrawPick() {
  const cat = DBS.catalog;
  const held = new Set(DBS.rows.map((r) => r.source));
  const left = cat.sources.filter((s) => s !== 'other' && !held.has(s));
  const was = $('dbs-pick').value;
  $('dbs-pick').innerHTML = left.map((s) => `<option value="${s}">${esc(cat.names[s])}</option>`).join('')
    + `<option value="other">${esc(t('sift_search.dbs.other'))}</option>`;
  if ([...left, 'other'].includes(was)) $('dbs-pick').value = was;
  $('dbs-other').hidden = $('dbs-pick').value !== 'other';
}

function dbsAdd() {
  const s = $('dbs-pick').value;
  if (!s || !DBS.rows) return;
  const row = { source: s, how: (DBS.catalog.apis || []).includes(s) ? 'api' : 'export' };
  if (s === 'other') {
    const name = $('dbs-other').value.trim();
    if (!name) { $('dbs-other').focus(); return; }
    if (DBS.rows.some((r) => r.source === 'other' && r.name.toLowerCase() === name.toLowerCase())) { say(t('sift_search.in_list', { name })); return; }
    row.name = name;
    $('dbs-other').value = '';
  }
  if ((DBS.catalog.platformed || []).includes(s)) row.platform = 'ebsco';
  DBS.rows.push(row);
  dbsDraw();
}

/* the field is emptied as soon as the value is on its way, so the key is not left sitting in the page */
async function dbsSaveKey(st, source, service, field, redraw) {
  const value = field.value;
  if (!value.trim()) { field.focus(); return; }
  field.value = '';
  try {
    await api('/api/databases', { op: 'key', service, key: value });
    st.saved[service] = true;
    dbsSaid(st, source, t('sift_search.dbs.key_saved'), false);
  } catch (err) { dbsSaid(st, source, needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
  redraw();
}

async function dbsClearKey(st, source, service, redraw) {
  try {
    const got = await api('/api/databases', { op: 'clear', service });
    st.saved[service] = false;
    dbsSaid(st, source, got.cleared ? t('sift_search.dbs.key_removed') : t('sift_search.dbs.no_key'), false);
  } catch (err) { dbsSaid(st, source, needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
  redraw();
}

/* the one line under a database's keys, and whether it says something failed, which draws it in the warning tint */
function dbsSaid(st, source, text, failed) {
  st.said[source] = text;
  st.failed = st.failed || {};
  st.failed[source] = !!failed;
}

/* the Databases heading at the top of the column, for Settings opened at its databases */
function dbsInView() {
  const panes = $('settings-panes');
  panes.scrollTop += $('dbs-sub').getBoundingClientRect().top - panes.getBoundingClientRect().top - 16;
}

/* A Save in Settings over the screen, or a change of a cog or Add database, gives the plan's databases
   the list and how each goes, read afresh */
async function sfsSettingsSaved() {
  if (!sfsShown() || !SFS.folder) return;
  await SFS.chain;
  let data;
  try { data = await api('/api/sift-search', { op: 'read', folder: SFS.folder }); } catch { return; }
  SFS.how = data.how || {};
  SFS.listed = data.listed || [];
  SFS.keys = data.keys || {};
  sfsDrawDatabases();
  sfsDrawStrings();
  sfsDrawRun();
}

async function dbsCheck(st, source, btn, redraw) {
  btn.disabled = true;
  try {
    const got = await api('/api/databases', { op: 'check', source });
    dbsSaid(st, source, got.said, !got.ok);
  } catch (err) { dbsSaid(st, source, needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
  redraw();
}

/* ── the screen, made once ── */

/* The screen in one column in the order its work goes, each part numbered (12 October, later): the
   plan under its one tag, the searches written from it, Register with Export search_plan.md and Mark
   as registered, then Search runs as a table and New run, and the card Mark as registered opens */
function sfsBuild() {
  const screen = document.createElement('section');
  screen.id = 'sift-search';
  screen.className = 'screen sfs-screen';
  screen.hidden = true;
  screen.innerHTML = `
  <div class="rail sfs-rail">
    <button type="button" class="rail-home bar-brand" id="sfs-home" title="${escAttr(t('sift_search.screen.home_cmd_shift_h'))}" aria-label="${escAttr(t('sift_search.screen.home'))}"><svg
            class="mark part-sift bar-markonly" aria-hidden="true" focusable="false"><use href="/marks.svg#sift-18"/></svg></button>
    <nav class="sf-steps" id="sfs-steps" aria-label="${escAttr(t('sift_search.screen.steps'))}" hidden></nav>
    <span class="rail-grow"></span>
    <button class="rail-btn bar-tool" id="sfs-search" type="button" title="${escAttr(t('sift_search.screen.search_cmd_f'))}" aria-label="${escAttr(t('sift_search.screen.search'))}" aria-haspopup="dialog"
            aria-expanded="false" aria-controls="search">${TB_GLASS}<span class="bar-word" aria-hidden="true">${esc(t('sift_search.screen.search'))}</span></button>
    <button class="rail-btn bar-tool rail-feedback" id="sfs-feedback" type="button" title="${escAttr(t('sift_search.screen.send_feedback'))}" aria-label="${escAttr(t('sift_search.screen.send_feedback'))}"${tbBugHidden()}>${TB_BUG}<span class="bar-word" aria-hidden="true">${esc(t('sift_search.screen.feedback'))}</span></button>
    <button class="rail-btn bar-tool" id="sfs-settings" type="button" title="${escAttr(t('sift_search.screen.sift_s_settings'))}" aria-label="${escAttr(t('sift_search.screen.sift_s_settings'))}">${TB_COG}<span class="bar-word" aria-hidden="true">${esc(t('sift_search.screen.settings'))}</span></button>
  </div>
  <div class="band" id="sfs-band">
    <nav class="ds-path" aria-label="${escAttr(t('sift_search.screen.where_you_are'))}">
      <button type="button" class="ds-proj" id="sfs-name" aria-haspopup="true" aria-expanded="false"><span class="ds-proj-name"></span><svg class="ds-chevron" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M3 4.6 6 7.6l3-3"/></svg></button>
    </nav>
    <span class="ds-path-rule" aria-hidden="true"></span>
    <span class="field-label band-label">${esc(t('sift_search.screen.research_question'))}</span>
    <p class="band-question" id="sfs-band-question"></p>
  </div>
  <div class="sfs-body">
    <div class="sfs-stale" id="sfs-stale" role="alert" hidden>
      <p class="sfs-stale-line">${esc(SFS_STALE_LINE)}</p>
      <p class="sfs-stale-acts"><button type="button" class="ghost small" id="sfs-stale-reload">${esc(t('sift_search.screen.reload'))}</button>
        <button type="button" class="ghost small" id="sfs-stale-over">${esc(t('sift_search.screen.overwrite'))}</button></p>
    </div>
    <section class="sfs-step" aria-labelledby="sfs-h-plan"><h2 class="sfs-h" id="sfs-h-plan"><span class="sfs-n">1</span>${esc(t('sift_search.screen.plan'))}<span class="sfs-tag sfs-state draft" id="sfs-state">${esc(t('sift_search.screen.draft'))}</span></h2>
      <div class="sfs-versions" id="sfs-versions" hidden><button type="button" class="ghost small sfs-toggle" id="sfs-versions-toggle"
        aria-expanded="false" aria-controls="sfs-version-list">${SFS_CHEVRON}${esc(t('sift_search.screen.earlier_versions'))}</button><div id="sfs-version-list" hidden></div></div>
      <section class="sfs-part" id="sfs-question-part" aria-labelledby="sfs-h-question" hidden><h3 class="sfs-h3" id="sfs-h-question">${esc(t('sift_search.screen.research_question'))}</h3>
        <p class="sfs-question" id="sfs-question" hidden></p></section>
      <section class="sfs-part" aria-labelledby="sfs-h-blocks"><h3 class="sfs-h3" id="sfs-h-blocks">${esc(t('sift_search.screen.search_terms'))}</h3>
        <p class="sfs-hint">${esc(t('sift_search.screen.each_block_holds_the_terms'))}</p>
        <div id="sfs-blocks"></div>
        <div class="sfs-problems" id="sfs-terms-said" hidden></div>
        <p><button type="button" class="ghost small" id="sfs-add">${esc(t('sift_search.screen.add_block'))}</button></p></section>
      <section class="sfs-part" aria-labelledby="sfs-h-limits"><h3 class="sfs-h3" id="sfs-h-limits">${esc(t('sift_search.screen.limits_and_restrictions'))}</h3>
        <p class="sfs-years"><span class="sfs-label">${esc(t('sift_search.screen.years'))}</span><label>${esc(t('sift_search.screen.from'))} <input id="sfs-from" type="text" inputmode="numeric" maxlength="4" aria-label="${escAttr(t('sift_search.screen.years_from'))}"></label>
          <label>${esc(t('sift_search.screen.to'))} <input id="sfs-to" type="text" inputmode="numeric" maxlength="4" aria-label="${escAttr(t('sift_search.screen.years_to'))}"></label></p>
        <p class="sfs-label">${esc(t('sift_search.screen.document_types'))}</p>
        <div class="sfs-types" id="sfs-types"></div></section>
      <section class="sfs-part" aria-labelledby="sfs-h-dbs"><h3 class="sfs-h3" id="sfs-h-dbs">${esc(t('sift_search.screen.databases'))}</h3>
        <div class="sfs-dbs" id="sfs-dbs"></div>
        <p class="sfs-add-db"><button type="button" class="ghost small" id="sfs-db-add">${esc(t('sift_search.screen.add_database'))}</button>
          <span class="sfs-add-line" id="sfs-add-line" hidden><input id="sfs-db-name" type="text" spellcheck="false" maxlength="60"
            placeholder="${escAttr(t('sift_search.screen.name'))}" aria-label="${escAttr(t('sift_search.screen.the_database_s_name'))}"><button type="button" class="ghost small" id="sfs-db-go">${esc(t('sift_search.screen.add'))}</button></span></p></section>
      <section class="sfs-part" aria-labelledby="sfs-h-bench"><h3 class="sfs-h3" id="sfs-h-bench">${esc(t('sift_search.screen.benchmark_papers'))}</h3>
        <p class="sfs-hint">${esc(t('sift_search.screen.papers_you_know_are_relevant'))}</p>
        <div class="sfs-bench-rows" id="sfs-bench-rows" hidden></div>
        <p><button type="button" class="ghost small" id="sfs-bench-add">${esc(t('sift_search.screen.add_a_paper'))}</button></p></section>
      <section class="sfs-part" aria-labelledby="sfs-h-keys"><h3 class="sfs-h3" id="sfs-h-keys">${esc(t('sift_search.screen.key_works'))}</h3>
        <p class="sfs-hint">${esc(t('sift_search.screen.works_the_studies_you_seek'))}</p>
        <div class="sfs-bench-rows" id="sfs-kw-rows" hidden></div>
        <div class="sfs-kw-add" id="sfs-kw-add" hidden>
          <p class="sfs-kw-line"><input id="sfs-kw-text" type="text" spellcheck="false" placeholder="${escAttr(t('sift_search.screen.doi_or_title'))}"
            aria-label="${escAttr(t('sift_search.screen.the_key_work_s_doi'))}"><input id="sfs-kw-year" type="text" inputmode="numeric" maxlength="4"
            placeholder="${escAttr(t('sift_search.screen.year'))}" aria-label="${escAttr(t('sift_search.screen.the_year_it_came_out'))}"><button type="button" class="ghost small" id="sfs-kw-find">${esc(t('sift_search.screen.find'))}</button></p>
          <div class="sfs-kw-picks" id="sfs-kw-picks" hidden></div>
        </div>
        <p><button type="button" class="ghost small" id="sfs-kw-new">${esc(t('sift_search.screen.add_a_key_work'))}</button></p></section>
      <section class="sfs-part" aria-labelledby="sfs-h-reasons"><h3 class="sfs-h3" id="sfs-h-reasons">${esc(t('sift_search.screen.exclusion_reasons'))}</h3>
        <p class="sfs-hint">${esc(t('sift_search.screen.offered_with_no_at_title'))}</p>
        <div class="sfs-reasons" id="sfs-reasons"></div><p class="sr-only" id="sfs-reasons-moved" aria-live="polite"></p>
        <div class="sfs-problems" id="sfs-reasons-said" hidden></div>
        <p><button type="button" class="ghost small" id="sfs-reason-add">${esc(t('sift_search.screen.add_a_reason'))}</button></p></section>
    </section>
    <section class="sfs-step sfs-wide" aria-labelledby="sfs-h-strings"><h2 class="sfs-h" id="sfs-h-strings"><span class="sfs-n">2</span>${esc(t('sift_search.screen.searches'))}</h2>
      <p class="sfs-hint">${esc(t('sift_search.screen.each_database_s_own_search'))}</p>
      <div class="sfs-strs" id="sfs-strings"></div></section>
    <section class="sfs-step sfs-wide" aria-labelledby="sfs-h-reg"><h2 class="sfs-h" id="sfs-h-reg"><span class="sfs-n">3</span>${esc(t('sift_search.screen.register'))}</h2>
      <p class="sfs-reg-when" id="sfs-reg-when" hidden></p>
      <div class="sfs-export">
        <p class="sfs-reg-tools"><button type="button" class="ghost" id="sfs-export">${esc(t('sift_search.screen.export_search_plan_md'))}</button>
          <button type="button" class="ghost small" id="sfs-reg-open" hidden>${esc(t('sift_search.screen.open_search_plan_md'))}</button>
          <button type="button" class="ghost small" id="sfs-md-copy" hidden>${esc(t('sift_search.screen.copy'))}</button></p>
        <ol class="sfs-reg-steps" id="sfs-reg-steps">
          <li>${t('sift_search.screen.export_plan_html')}</li>
          <li>${t('sift_search.screen.register_html')}</li>
        </ol>
      </div>
      <div id="sfs-reg-draft">
        <p class="sfs-reg-text">${esc(t('sift_search.screen.once_you_have_registered_the'))}</p>
        <p class="sfs-why-line" id="sfs-why-line" hidden><input id="sfs-why" type="text" placeholder="${escAttr(t('sift_search.screen.reason_for_the_changes'))}"
           aria-label="${escAttr(t('sift_search.screen.reason_for_the_changes'))}"></p>
        <div class="sfs-problems" id="sfs-problems" hidden></div>
        <p><button type="button" class="primary" id="sfs-mark">${esc(t('sift_search.screen.mark_as_registered'))}</button></p>
      </div>
      <p class="sfs-reg-next" id="sfs-reg-next" hidden>${esc(t('sift_search.screen.your_next_edit_to_the'))}</p></section>
    <section class="sfs-step sfs-wide sfs-runs-step" aria-labelledby="sfs-h-run"><h2 class="sfs-h" id="sfs-h-run"><span class="sfs-n">4</span>${esc(t('sift_search.screen.search_runs'))}</h2>
      <table class="sfs-runs-table" id="sfs-runs-table" hidden><thead><tr><th scope="col">${esc(t('sift_search.screen.run'))}</th><th scope="col">${esc(t('sift_search.screen.search'))}</th>
        <th scope="col" class="sfs-num">${esc(t('sift_search.screen.records_found'))}</th><th scope="col" class="sfs-num">${esc(t('sift_search.screen.after_duplicates'))}</th>
        <th scope="col" class="sfs-num">${esc(t('sift_search.screen.benchmark_papers_found'))}</th><th scope="col"><span class="sr-only">${esc(t('sift_search.screen.active_run'))}</span></th></tr></thead>
        <tbody id="sfs-runs"></tbody></table>
      <section class="sfs-new" aria-labelledby="sfs-h-new"><h3 class="sfs-h3" id="sfs-h-new">${esc(t('sift_search.screen.new_run'))}</h3>
        <p class="sfs-new-what" id="sfs-new-what"></p>
        <ul class="sfs-sources" id="sfs-sources"></ul>
        <p class="sfs-check-line"><button type="button" class="ghost small" id="sfs-check-go" hidden>${esc(t('sift_search.screen.check_truncation'))}</button></p>
        <div class="sfs-check" id="sfs-check" hidden></div>
        <p class="sfs-run-line"><button type="button" class="primary" id="sfs-run">${esc(t('sift_search.screen.start_new_run'))}</button>
          <label class="sfs-follow" id="sfs-follow-line" hidden>${esc(t('sift_search.screen.keep_the_decisions_from'))} <select id="sfs-follows" aria-label="${escAttr(t('sift_search.screen.keep_the_decisions_from'))}"></select></label></p>
      </section></section>
  </div>`;
  const ask = document.createElement('div');
  ask.className = 'overlay';
  ask.id = 'sfs-ask';
  ask.hidden = true;
  ask.innerHTML = `<div class="card"><p class="kicker">${esc(t('sift_search.steps.searches'))}</p><h2 id="sfs-ask-head"></h2><p class="trim-line" id="sfs-ask-line"></p>`
    + `<div class="card-actions"><button type="button" class="ghost" id="sfs-ask-no">${esc(t('sift_search.cancel'))}</button>`
    + '<button type="button" class="primary" id="sfs-ask-yes"></button></div></div>';
  // Mark as registered: where the plan is registered and its number or link, both needed
  const mark = document.createElement('div');
  mark.className = 'overlay';
  mark.id = 'sfs-mark-card';
  mark.hidden = true;
  mark.innerHTML = `<div class="card sfs-mark" role="dialog" aria-labelledby="sfs-mark-head"><p class="kicker">${esc(t('sift_search.steps.searches'))}</p>`
    + `<h2 id="sfs-mark-head">${esc(t('sift_search.screen.mark_as_registered'))}</h2><p class="trim-line" id="sfs-mark-line"></p>`
    + `<fieldset class="sfs-mark-where"><legend class="sfs-label">${esc(t('sift_search.mark.with'))}</legend>`
    + '<label><input type="radio" name="sfs-registry" id="sfs-reg-osf" value="OSF">OSF</label>'
    + '<label><input type="radio" name="sfs-registry" id="sfs-reg-prospero" value="PROSPERO">PROSPERO</label>'
    + `<label><input type="radio" name="sfs-registry" id="sfs-reg-other" value="other">${esc(t('sift_search.mark.another'))}</label>`
    + `<input id="sfs-registry-other" type="text" maxlength="60" placeholder="${escAttr(t('sift_search.mark.its_name'))}" aria-label="${escAttr(t('sift_search.mark.registry_name'))}" hidden></fieldset>`
    + `<p class="sfs-mark-number"><label class="sfs-label" for="sfs-registration">${esc(t('sift_search.mark.number'))}</label>`
    + '<input id="sfs-registration" type="text" maxlength="240" spellcheck="false"></p>'
    + `<div class="card-actions"><button type="button" class="ghost" id="sfs-mark-no">${esc(t('sift_search.cancel'))}</button>`
    + `<button type="button" class="primary" id="sfs-mark-yes" disabled>${esc(t('sift_search.screen.mark_as_registered'))}</button></div></div>`;
  // before the line at the foot's status, which holds it (a11yfix)
  const before = $('toast-live') || $('toast');
  document.body.insertBefore(screen, before || null);
  // the lockup drawn in from Home's, and the bar's words fitted to its room (shell.js)
  if (typeof barLockups === 'function') barLockups();
  document.body.insertBefore(ask, before || null);
  document.body.insertBefore(mark, before || null);
}

function sfsBoot() {
  sfsBuild();
  // the lockup goes home (option C of the bars, 26 October 2026, the path's Home gone since option D, 6 November
  // 2026), and the path's review opens its menu, its card's on Home (barsD)
  $('sfs-home').onclick = sfsBack;
  bandMenuWire('sfs-name', () => siftBandMenu());
  $('sfs-stale-reload').onclick = sfsStaleReload;
  $('sfs-stale-over').onclick = sfsStaleOverwrite;
  $('sfs-feedback').onclick = () => openFeedback('searches');
  $('sfs-settings').onclick = () => openSettings('databases');
  $('sfs-add').onclick = () => {
    SFS.plan.blocks.push({ name: '', terms: [], scope: 'tak', scopes: {} });
    sfsDrawBlocks();
    const names = $('sfs-blocks').querySelectorAll('.sfs-bname');
    if (names.length) names[names.length - 1].focus();
  };
  $('sfs-db-add').onclick = () => { SFS.adding = true; sfsDrawDatabases(); $('sfs-db-name').focus(); };
  $('sfs-db-go').onclick = sfsAddDb;
  const year = (v) => (v.trim() === '' ? null : v.trim());
  $('sfs-from').oninput = () => { SFS.plan.years.from = year($('sfs-from').value); sfsChanged(); };
  $('sfs-to').oninput = () => { SFS.plan.years.to = year($('sfs-to').value); sfsChanged(); };
  // Add a paper: an empty row with its DOI box ready, and Add a reason the same for a reason
  $('sfs-bench-add').onclick = () => {
    SFS.benchRows = (SFS.benchRows || []).concat(['']);
    sfsDrawBench(false);
    const boxes = $('sfs-bench-rows').querySelectorAll('.sfs-doi');
    if (boxes.length) boxes[boxes.length - 1].focus();
  };
  // Add a key work: its line, the box for a DOI or a title ready, and Find
  $('sfs-kw-new').onclick = () => { SFS.kwAdding = true; SFS.kwPicks = null; sfsDrawKeys(); $('sfs-kw-text').focus(); };
  $('sfs-kw-find').onclick = sfsKwFind;
  $('sfs-reason-add').onclick = () => {
    SFS.reasons = (SFS.reasons || []).concat([{ code: '', meaning: '' }]);
    sfsDrawReasons(false);
    const codes = $('sfs-reasons').querySelectorAll('.sfs-rcode');
    if (codes.length) codes[codes.length - 1].focus();
  };
  $('sfs-versions-toggle').onclick = () => {
    if (SFS.open.has('versions')) SFS.open.delete('versions'); else SFS.open.add('versions');
    sfsDrawVersion();
  };
  $('sfs-why').oninput = () => { SFS.reason = $('sfs-why').value; sfsChanged(); };
  $('sfs-export').onclick = sfsExport;
  $('sfs-mark').onclick = sfsMark;
  $('sfs-reg-open').onclick = () => sfsOpenFile('plan');
  $('sfs-run').onclick = sfsRun;
  $('sfs-check-go').onclick = sfsCheck;
  $('sfs-follows').onchange = () => { SFS.follows = $('sfs-follows').value; };
  $('sfs-md-copy').onclick = () => sfsCopy((SFS.data && SFS.data.exported) || '');
  $('sfs-ask-yes').onclick = () => { if (SFS.askDone) SFS.askDone(true); };
  $('sfs-ask-no').onclick = () => { if (SFS.askDone) SFS.askDone(false); };
  ['sfs-reg-osf', 'sfs-reg-prospero', 'sfs-reg-other'].forEach((id) => {
    $(id).onchange = () => { sfsMarkReady(); if (id === 'sfs-reg-other') $('sfs-registry-other').focus(); };
  });
  $('sfs-registry-other').oninput = sfsMarkReady;
  $('sfs-registration').oninput = sfsMarkReady;
  $('sfs-mark-yes').onclick = sfsMarkGo;
  $('sfs-mark-no').onclick = sfsMarkShut;
  if ($('dbs-add')) {
    $('dbs-add').onclick = dbsAdd;
    $('dbs-pick').onchange = () => {
      $('dbs-other').hidden = $('dbs-pick').value !== 'other';
      if (!$('dbs-other').hidden) $('dbs-other').focus();
    };
    $('dbs-other').onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); dbsAdd(); } };
  }
  window.addEventListener('keydown', sfsKeyDown, true);
  window.addEventListener('dragover', sfsDrag);
  window.addEventListener('dragenter', sfsDrag);
  window.addEventListener('drop', sfsDrop);
}

/* ── Search (the family codebase's third build, 22 October 2026, from search.js) ── */

/* Search's place on Search strategy, and its leaving, the plan's last change saved and its run let alone, the
   screen put away, each through `FAMILY_APPS.sift` (sift_settings.js) */
const sfsSearchWhere = () => (searchShown('sift-search') && SFS.folder ? { screen: 'searches', folder: SFS.folder } : null);

async function sfsSearchLeave() {
  if (!searchShown('sift-search')) return true;
  clearTimeout(SFS.poll);
  SFS.poll = null;
  await sfsFlush();
  $('sift-search').hidden = true;
  $('sfs-ask').hidden = true;
  return true;
}

/* A term or a reason of the plan: Search strategy opened, on the screen already when it is the one open,
   and there the caret at the start of the term's line in its block's terms, or in the reason's meaning,
   in the middle of the screen. Nothing is selected, so no key typed after replaces the words. */
async function searchToPlan(go) {
  const here = SEARCH.here;
  if (!(here && here.screen === 'searches' && searchShown('sift-search') && SFS.folder === go.folder)) {
    if (!(await searchLeaveFor(here))) return;
    await sfsOpen(go.folder);
    if (!searchShown('sift-search')) return;
  }
  let el = null;
  let at = 0;
  if (go.block !== undefined) {
    const block = $('sfs-blocks').querySelectorAll('.sfs-block')[Number(go.block)];
    el = block ? block.querySelector('.sfs-terms') : null;
    const lines = el ? el.value.split('\n') : [];
    for (let k = 0; k < Math.min(Number(go.line) || 0, lines.length); k += 1) at += lines[k].length + 1;
  } else if (go.reason !== undefined) {
    const row = $('sfs-reasons').querySelectorAll('.sfs-reason')[Number(go.reason)];
    el = row ? row.querySelector('.sfs-rmeaning') : null;
  }
  if (!el) { say(SEARCH_GONE, 6000); return; }
  el.scrollIntoView({ block: 'center' });
  el.focus({ preventScroll: true });
  el.setSelectionRange(at, at);
}

sfsBoot();
