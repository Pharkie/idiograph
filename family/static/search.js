/* Search across the app (17 October, Adam's word, and 18 October): one field over what a case and its
   project hold, a passage, an interviewer note, a statement, a quote, an exploratory note, a PET, a
   sub-theme, a PET's note, a sticky note, a board's note, a GET and its notes, a participant note, a case
   and the research question, over a Sift project's records, decision notes, his own fields, his form's
   answers, his key excerpts, its search terms and exclusion reasons, over a Trace project's claims,
   references and claim notes, and over all of them, Everything. A card under the bar, the field and
   Search in at its right, the kinds found with their counts at its left, each ticking from its row, the
   case and the sheet too once the search is wider than a case, and with Everything the kinds under their
   parts' names and the projects. Every word typed, in any order, case and accents set aside, as Sift's
   find boxes match (`tbFindMatch`), narrowed by two ticks beside the field, Whole word, each word found only
   as a whole word, ticked at first as in Find and replace, and Match case, in the case typed, not ticked
   (searchmods, 6 November 2026). The server reads (`/api/search`, app_search.py), and nothing is written.

   By the book a case is taken in depth and on its own before another meets it, so a search starts in
   This case on the statements screen and on PETs, and in This project on the project's page and on GETs,
   where meeting across the cases is the step, in This Sift project on Sift's screens, in This Trace
   project on Trace's and in Everything on the home screen. Everything is the widest choice of Search in
   on every screen. A scope widened never carries into the next opening.

   Cmd + F, Ctrl + F off a Mac, opens it where he is on any of those screens, and the bar's Search does
   too. Arrows walk the results, Enter opens the one in focus, a click opens any, Esc and a click outside
   close the card, and the key again brings the last results back. Find and replace stays on
   Cmd + Shift + F on the statements screen, and Replace in the transcript under a This case search
   there opens it with the words typed. Under a card of the app's own the browser keeps its own Cmd + F. */

'use strict';

const SEARCH = {
  q: '',              // the words typed, kept for the next opening
  scope: 'case',      // 'case' or 'project', the screen's own at every opening
  kinds: new Set(),   // the kinds ticked, kept for the next opening in the same place
  cases: new Set(),   // the cases ticked, while the search is wider than a case
  sheets: new Set(),  // the sheets ticked, the same
  projects: new Set(), // the projects ticked, while the search is Everything
  data: null,         // the last answer, drawn again at the next opening
  at: -1,             // the result in focus, an index into data.results
  ask: 0,             // the search in flight, so a slow answer never lands on a newer one
  timer: 0,
  here: null,         // where it was opened, { screen, path }, { screen, root }, { screen, folder } or { screen }
  context: '',        // the same as one string, so the next opening knows a new place
  all: false,         // below 700px, every filter shown after More, the Kind heading and three rows of ticks till then
};

// each kind's name, one and many, in the order the server lists them
const SEARCH_KINDS = {
  passage: ['Passage', 'Passages'],
  inote: ['Interviewer note', 'Interviewer notes'],
  statement: ['Statement', 'Statements'],
  quote: ['Quote', 'Quotes'],
  enote: ['Exploratory note', 'Exploratory notes'],
  pet: ['PET', 'PETs'],
  sub: ['Sub-theme', 'Sub-themes'],
  petnote: ['PET note', 'PET notes'],
  sticky: ['Sticky note', 'Sticky notes'],
  boardnote: ['Board note', 'Board notes'],
  get: ['GET', 'GETs'],
  getnote: ['GET note', 'GET notes'],
  rownote: ['Row note', 'Row notes'],
  pnote: ['Participant note', 'Participant notes'],
  case: ['Participant', 'Participants'],
  question: ['Research question', 'Research question'],
  // Sift's (18 October)
  record: ['Record', 'Records'],
  dnote: ['Decision note', 'Decision notes'],
  field: ['Field', 'Fields'],
  form: ['Form answer', 'Form answers'],
  excerpt: ['Key excerpt', 'Key excerpts'],
  term: ['Search term', 'Search terms'],
  reason: ['Exclusion reason', 'Exclusion reasons'],
  // and Trace's
  claim: ['Claim', 'Claims'],
  reference: ['Reference', 'References'],
  cnote: ['Claim note', 'Claim notes'],
};
// a kind's name, one (0) or many (1), as the answer names it where its project's method says it otherwise, a thematic
// analysis project's Codes and Extracts (taword, 1 November 2026), else as above
const searchKind = (data, kind, many) => ((data && data.names && data.names[kind]) || SEARCH_KINDS[kind] || [kind, kind])[many ? 1 : 0];
const SEARCH_SCOPES = { case: 'This participant', project: 'This project', sift: 'This Sift project', trace: 'This Trace project',
  all: 'Everything' };
// Everything's kinds stand under their parts' names, in the order a study does them, as the server lists them
const SEARCH_PARTS = { sift: 'Sift', distil: 'Idiograph', trace: 'Trace' };
const SEARCH_NONE = 'Nothing found';
// a result whose record, row or passage is no longer where the search found it
const SEARCH_GONE = 'That is no longer where the search found it.';
const searchOpen = () => !$('search').hidden;
const searchShown = (id) => !!$(id) && !$(id).hidden;

/* Words as the server compares them, accents off and in lower case, as `tbFindMatch` folds them, and under
   Match case accents off alone. */
const searchPlain = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '');
const searchFold = (s) => searchPlain(s).toLowerCase();
// a letter or a digit, which a word typed may not run into under Whole word, as Find and replace reads one
const SEARCH_ALNUM = /[\p{L}\p{N}]/u;

/* The two ticks beside the field, Whole word and Match case, as the server is told them. Like Find and
   replace's own they are the card's boxes, never rebuilt, so they keep between openings and on every screen
   until the page is reloaded, and are saved nowhere. */
const searchOptions = () => ({ whole_word: !!$('search-word').checked, match_case: !!$('search-case').checked });

/* The screen in front, or null under a card or on none: the statements screen, PETs, GETs or a project's
   page in Distil, Sift's screening or its Search strategy, Trace's screen, or the home screen's picker. */
function searchWhere() {
  // an app's own screen, each by its own script: Idiograph's statements screen, PETs, GETs or a project's page,
  // Sift's screening or its Search strategy, and Trace's
  for (const own of Object.values(FAMILY_APPS)) { const at = own.searchWhere && own.searchWhere(); if (at) return at; }
  if (searchShown('library') && searchShown('home-pick')) return { screen: 'home' };
  return null;
}

/* the scopes a screen offers, its own first and Everything last: a case's screens This case and This
   project, the project's page and GETs This project, Sift's screens This Sift project, Trace's This Trace
   project, and the home screen Everything alone */
function searchScopes(here) {
  const screen = here ? here.screen : '';
  if (screen === 'statements' || screen === 'pets') return ['case', 'project', 'all'];
  if (screen === 'gets' || screen === 'trajectories' || screen === 'codes' || screen === 'project') return ['project', 'all'];
  if (screen === 'sift' || screen === 'searches') return ['sift', 'all'];
  if (screen === 'trace') return ['trace', 'all'];
  return ['all'];
}

/* a card of the app's own over the screen, Sift's and Trace's among them, under which the browser keeps
   its own Cmd + F */
const searchCovered = () => anyOverlayOpen() || [...document.querySelectorAll('.overlay')].some((el) => !el.hidden);

/* Open the card where he is, Search in at the screen's own scope, the last words typed brought back and
   searched again, with the kinds ticked when it is the same place, the field's words selected. Open
   already, the key takes the caret back to the field. */
function openSearch() {
  const here = searchWhere();
  if (!here) return false;
  if (searchOpen()) { $('search-text').focus(); $('search-text').select(); return true; }
  // the cards and menus the screen keeps open put away first, Find and replace among them, so none
  // stands over the card or out of the wash
  // an app's own screen's, Idiograph's and Sift's, by its own script
  if (familyApp(here.screen) && familyApp(here.screen).searchClear) familyApp(here.screen).searchClear(here);
  SEARCH.all = false;
  // another screen or another case starts with no filter ticked, the words kept
  const context = here.screen === 'project' ? `project:${here.root}` : `${here.screen}:${here.path || here.folder || ''}`;
  if (context !== SEARCH.context) { SEARCH.kinds.clear(); SEARCH.cases.clear(); SEARCH.sheets.clear(); SEARCH.projects.clear(); SEARCH.data = null; }
  SEARCH.here = here;
  SEARCH.context = context;
  const scopes = searchScopes(here);
  // the screen's own scope at every opening, so a widened one never carries
  if (SEARCH.scope !== scopes[0]) { SEARCH.cases.clear(); SEARCH.sheets.clear(); SEARCH.projects.clear(); SEARCH.kinds.clear(); SEARCH.data = null; }
  SEARCH.scope = scopes[0];
  $('search-scope').innerHTML = scopes.map((s) => `<option value="${s}">${SEARCH_SCOPES[s]}</option>`).join('');
  $('search-scope').value = SEARCH.scope;
  // Search in shows only where there is a choice, so the home screen's one place, Everything, offers no
  // drop-down of one (18 October, polish 10)
  $('search-scope').closest('.search-in').hidden = scopes.length < 2;
  $('search-text').value = SEARCH.q;
  // on a project's page the page comes up to the project's name, so the card stands under it and leaves it
  // in sight, where under the home screen's head it stood over the name
  if (here.screen === 'project') {
    const head = document.querySelector('#home-project .hp-head');
    if (head) window.scrollBy(0, head.getBoundingClientRect().top - 8);
  }
  // and on the picker it comes up to its head, so the card stands under the lockup and the head's tools
  if (here.screen === 'home') window.scrollTo(0, 0);
  $('search').hidden = false;
  searchPlace();
  searchBars(true);
  searchDraw();
  $('search-text').focus();
  $('search-text').select();
  searchRun(true);
  return true;
}

/* Esc, a click outside, a result opened and the bar's Search pressed again put the card away, and keep
   what it held for the next opening. `focus` gives the caret back to the screen. */
function closeSearch(focus = true) {
  if (!searchOpen()) return;
  $('search').hidden = true;
  clearTimeout(SEARCH.timer);
  SEARCH.ask += 1;
  searchBars(false);
  // the caret back to the screen, Idiograph's statements screen's field, by the app's own script
  const own = focus && SEARCH.here ? familyApp(SEARCH.here.screen) : null;
  if (own && own.searchClosed) own.searchClosed(SEARCH.here);
}

/* every bar's Search, the statements screen's, the boards', the home screen's, Sift's, its Search
   strategy's and Trace's (18 October) */
const SEARCH_BUTTONS = ['btn-search', 'th-search', 'tj-search', 'cd-search', 'lib-search', 'sf-search', 'sfs-search', 'tr-search'];

/* the bar's Search pressed in while the card is open, on whichever bar it stands */
function searchBars(open) {
  for (const id of SEARCH_BUTTONS) {
    const b = $(id);
    if (b) b.setAttribute('aria-expanded', String(!!open));
  }
}

/* The card's top under the bar of the screen in front, the research question's band under it
   included, on a project's page under the project's name and question, on the picker under the lockup
   and the head's tools, the days and the line under them left to the wash, so a phone's width keeps the
   room for the results, and on Sift's and Trace's screens under their bars, the steps wrapped under one
   included, measured as they stand. */
function searchPlace() {
  const here = SEARCH.here || searchWhere();
  const screen = here ? here.screen : '';
  let foot = 0;
  const bar = (id) => ($(id) ? $(id).querySelector('.rail') : null);
  const parts = screen === 'statements' ? [bar('work'), $('band')]
    : screen === 'pets' || screen === 'gets' ? [bar('themes'), $('th-band')] : screen === 'trajectories' ? [bar('traj'), $('tj-band')] : screen === 'codes' ? [bar('codes-screen'), $('cd-band')]
      : screen === 'sift' ? [bar('sift'), $('sf-band')] : screen === 'searches' ? [bar('sift-search'), $('sfs-band')] : screen === 'trace' ? [bar('trace')]
        : screen === 'home' ? [document.querySelector('#library .wordmark'), document.querySelector('#library .lib-tools')]
          : [document.querySelector('#home-project .hp-head')];
  for (const el of parts) {
    if (el && !el.hidden && el.offsetHeight) foot = Math.max(foot, el.getBoundingClientRect().bottom);
  }
  document.body.style.setProperty('--search-top', `${Math.max(0, Math.round(foot))}px`);
}

/* Ask the server, a breath after the last key, `now` at once. An answer that lands after a newer
   question is dropped. A failure is one line in the card. */
function searchRun(now = false) {
  clearTimeout(SEARCH.timer);
  const go = async () => {
    const here = SEARCH.here;
    if (!here || !searchOpen()) return;
    const ask = ++SEARCH.ask;
    // the page's own app, so Everything holds its projects alone (the split's third build)
    const body = { q: SEARCH.q, scope: SEARCH.scope, kinds: [...SEARCH.kinds], app: APP, ...searchOptions() };
    if (here.path) body.path = here.path;
    else if (here.root) body.root = here.root;
    else if (here.folder) body.folder = here.folder;
    if (SEARCH.scope === 'project') Object.assign(body, { cases: [...SEARCH.cases], sheets: [...SEARCH.sheets] });
    if (SEARCH.scope === 'all') body.projects = [...SEARCH.projects];
    let data;
    try {
      data = await api('/api/search', body);
    } catch (err) {
      if (ask !== SEARCH.ask) return;
      SEARCH.data = null;
      searchDraw(needsRestart(err) ? RESTART_LINE : err.message);
      return;
    }
    if (ask !== SEARCH.ask || !searchOpen()) return;
    SEARCH.data = data;
    SEARCH.at = data.results.length && SEARCH.q.trim() ? 0 : -1;
    searchDraw();
  };
  if (now) go(); else SEARCH.timer = setTimeout(go, 120);
}

/* A text with every word typed under the find's wash, as many times as each stands in it, case and
   accents aside, and each of their other forms the server found by (`forms`, "slept" for "sleep") where it
   stands as a whole word. A phrase in quotation marks is marked as typed. The text is set in its own words,
   never folded. `opts` is how the server read the words, Whole word, `whole_word`, marking each word only as a
   whole word, and Match case, `match_case`, in the case typed, the forms in that case too. */
function searchMarked(text, q, forms = [], opts = {}) {
  const whole = !!(opts && opts.whole_word);
  const keep = !!(opts && opts.match_case);
  const norm = keep ? searchPlain : searchFold;
  let typed = String(q || '').trim();
  const quote = (c) => c === '"' || c === '\u201c' || c === '\u201d';
  if (typed.length > 1 && quote(typed[0]) && quote(typed[typed.length - 1])) typed = typed.slice(1, -1);
  const words = norm(typed).split(/\s+/).filter(Boolean);
  const src = String(text || '');
  // each character's folded form, so a place in the folded text names a place in the text
  const map = [];
  let low = '';
  for (let i = 0; i < src.length; i += 1) {
    const f = norm(src[i]);
    for (let k = 0; k < f.length; k += 1) map.push(i);
    low += f;
  }
  const on = new Array(src.length).fill(false);
  // under Whole word a letter or a digit beside an end of the word that is one itself rules the place out, as
  // Find and replace's Whole word does, and elsewhere the other forms' edge is a letter or digit of a to z
  const alnum = whole ? SEARCH_ALNUM : (keep ? /[A-Za-z0-9]/ : /[a-z0-9]/);
  const edge = (k) => k < 0 || k >= low.length || !alnum.test(low[k]);
  const fits = (at, n) => !whole || ((!SEARCH_ALNUM.test(low[at]) || edge(at - 1)) && (!SEARCH_ALNUM.test(low[at + n - 1]) || edge(at + n)));
  for (const w of words) {
    let at = low.indexOf(w);
    while (at >= 0) {
      const ok = fits(at, w.length);
      if (ok) for (let k = at; k < at + w.length; k += 1) on[map[k]] = true;
      at = low.indexOf(w, at + (ok ? w.length : 1));
    }
  }
  for (const f of forms || []) {
    let at = low.indexOf(f);
    while (at >= 0) {
      if (edge(at - 1) && edge(at + f.length)) for (let k = at; k < at + f.length; k += 1) on[map[k]] = true;
      at = low.indexOf(f, at + 1);
    }
  }
  let html = '';
  let open = false;
  for (let i = 0; i < src.length; i += 1) {
    if (on[i] && !open) { html += '<mark class="search-mark">'; open = true; }
    if (!on[i] && open) { html += '</mark>'; open = false; }
    html += esc(src[i]);
  }
  return open ? `${html}</mark>` : html;
}

/* Where a result is, in small type: with Everything its project first, then its case once the search is
   wider than a case, then its sheet and timecode, its board and PET, GETs and its board, a record's ID
   and its part, Search strategy and the block, or a manuscript, its section and the reference, the
   project's name said once. */
function searchWhereLine(r) {
  const parts = [];
  const wide = SEARCH.scope === 'project' || SEARCH.scope === 'all';
  if (SEARCH.scope === 'all' && r.project) parts.push(r.project);
  if (wide && r.case && r.kind !== 'case') parts.push(r.case);
  if (r.where && !(SEARCH.scope === 'all' && r.where === r.project)) parts.push(r.where);
  return parts.join(' · ');
}

/* The card drawn from the last answer: the filters at the left, the kinds found with their counts,
   then Case and Sheet once wider than a case, each a tick in its row, a ticked one kept with a count
   of none, and the results at the right, each its kind, its words under the find's wash and where it
   is. `said` is a failure, in place of the results. */
function searchDraw(said = '') {
  const data = SEARCH.data;
  const typed = !!SEARCH.q.trim();
  const tick = (group, value, label, n) => {
    const on = SEARCH[group].has(value);
    return `<label class="search-tick${on ? ' on' : ''}"><input type="checkbox" data-group="${group}" value="${escAttr(value)}"${on ? ' checked' : ''}>`
      + `<span class="search-tick-word">${esc(label)}</span><span class="search-n">${n}</span></label>`;
  };
  let filters = '';
  if (data && typed) {
    const kindTicks = (list) => list.map((kind) => [kind, (data.counts || {})[kind] || 0])
      .filter(([kind, n]) => n || SEARCH.kinds.has(kind))
      .map(([kind, n]) => tick('kinds', kind, searchKind(data, kind, true), n)).join('');
    if (SEARCH.scope === 'all' && Array.isArray(data.parts)) {
      // Everything's kinds under their parts' names, Sift, Distil and Trace, in the order a study does them, then
      // the projects with theirs
      for (const [part, list] of data.parts) {
        const ticks = kindTicks(list);
        if (ticks) filters += `<p class="section-label search-group">${esc(data.parts.length > 1 ? (SEARCH_PARTS[part] || part) : 'Kind')}</p>${ticks}`;
      }
      const projects = (data.projects || []).filter((p) => p.count || SEARCH.projects.has(p.key));
      if ((data.projects || []).length > 1 && projects.length) {
        filters += `<p class="section-label search-group">Project</p>${projects.map((p) => tick('projects', p.key, p.name, p.count)).join('')}`;
      }
    } else {
      // the kinds under a heading of their own, as the cases and the sheets have theirs
      const kinds = kindTicks(Object.keys(data.counts || {}));
      if (kinds) filters += `<p class="section-label search-group">Kind</p>${kinds}`;
    }
    const cases = (data.cases || []).filter((c) => c.count || SEARCH.cases.has(c.name));
    if (SEARCH.scope === 'project' && (data.cases || []).length > 1 && cases.length) {
      filters += `<p class="section-label search-group">Participant</p>${cases.map((c) => tick('cases', c.name, c.name, c.count)).join('')}`;
    }
    const sheets = (data.sheets || []).filter((s) => s.count || SEARCH.sheets.has(s.name));
    if (SEARCH.scope === 'project' && (data.sheets || []).length > 1 && sheets.length) {
      filters += `<p class="section-label search-group">Sheet</p>${sheets.map((s) => tick('sheets', s.name, s.name, s.count)).join('')}`;
    }
  }
  $('search-filters').innerHTML = filters;
  $('search-side').hidden = !filters;
  // the results take the whole width while there is nothing to filter
  $('search').classList.toggle('bare', !filters);
  searchMore();
  const list = data && typed ? data.results : [];
  $('search-list').innerHTML = list.map((r, n) => `<li class="search-hit${n === SEARCH.at ? ' on' : ''}" role="option" id="search-hit-${n}" data-n="${n}" aria-selected="${n === SEARCH.at}">`
    + `<span class="search-kind">${esc(searchKind(data, r.kind, false))}</span>`
    + `<span class="search-words">${searchMarked(r.text, SEARCH.q, data.forms, data)}</span>`
    + `<span class="search-at">${esc(searchWhereLine(r))}</span></li>`).join('');
  $('search-list').hidden = !list.length;
  let line = said;
  if (!line && data && typed && !data.total) line = SEARCH_NONE;
  else if (!line && data && typed && data.total > list.length) line = `${list.length} of ${tNum(data.total)}`;
  $('search-said').textContent = line;
  $('search-said').hidden = !line;
  $('search-said').classList.toggle('warn', !!said);
  $('search-text').setAttribute('aria-activedescendant', SEARCH.at >= 0 && list[SEARCH.at] ? `search-hit-${SEARCH.at}` : '');
  // Find and replace from a This case search on the statements screen, with the words typed
  $('search-foot').hidden = !(SEARCH.here && SEARCH.here.screen === 'statements' && SEARCH.scope === 'case');
  // a fresh list starts at its head, faded at the card's foot while more wait
  $('search-results').scrollTop = 0;
  searchFade();
}

/* Below 700px the filters stand as the Kind heading and three whole rows of ticks, never a row cut through its letters, and More
   under them, while more rows wait, shows every one, Fewer the three again. At a desk width they stand in
   their column whole and More never shows. */
function searchMore() {
  const box = $('search-filters');
  box.classList.toggle('all', SEARCH.all);
  box.style.maxHeight = '';
  const narrow = window.matchMedia('(max-width: 700px)').matches;
  const more = narrow && !$('search-side').hidden && (SEARCH.all || box.scrollHeight > box.clientHeight + 1);
  $('search-more').hidden = !more;
  // a heading stands only over rows: while More holds the rest, a heading at the box's foot whose first row
  // is behind More is hidden with them, as Project stood over nothing at 360 (18 October, polish 10)
  const top = box.getBoundingClientRect().top;
  const foot = top + box.clientHeight;
  const heads = [...box.querySelectorAll('.search-group')];
  for (const head of heads) {
    const first = head.nextElementSibling;
    head.classList.toggle('over-none', more && !SEARCH.all
      && (!first || first.classList.contains('search-group') || first.getBoundingClientRect().bottom > foot + 1));
  }
  // and the box ends above the first such heading, so the row it stood on takes no room and More comes up
  // under the rows above it (19 October, polish 10)
  const orphan = heads.find((head) => head.classList.contains('over-none'));
  if (orphan) {
    const gap = parseFloat(getComputedStyle(box).rowGap) || 0;
    box.style.maxHeight = `${Math.max(0, Math.round(orphan.getBoundingClientRect().top - top - gap))}px`;
  }
  $('search-more').textContent = SEARCH.all ? 'Fewer' : 'More';
  $('search-more').setAttribute('aria-expanded', String(SEARCH.all));
}

/* A row behind More brought into the box, by Tab or by a click, opens every row, so the box never stands
   scrolled under More with the rows above it out of sight. */
function searchFiltersScrolled() {
  const box = $('search-filters');
  if (!box.scrollTop) return;
  box.scrollTop = 0;
  if (!SEARCH.all) { SEARCH.all = true; searchMore(); }
}

/* While more results wait below, the last row in sight fades at the card's foot, never cut through its
   letters, and once the list is at its end it stands whole. The filter column at a desk width does the
   same, so a group under the last one in sight, Case under a short card on a project's page, says it is
   there and the column scrolls to it. */
function searchFade() {
  for (const box of [$('search-results'), $('search-side')]) {
    box.classList.toggle('more-below', box.scrollTop + box.clientHeight < box.scrollHeight - 1);
  }
}

/* The arrows move the focus through the results, the one in focus kept in sight in the list. */
function searchStep(delta) {
  const list = (SEARCH.data && SEARCH.q.trim() && SEARCH.data.results) || [];
  if (!list.length) return;
  SEARCH.at = SEARCH.at < 0 ? (delta > 0 ? 0 : list.length - 1) : Math.max(0, Math.min(list.length - 1, SEARCH.at + delta));
  for (const el of $('search-list').querySelectorAll('.search-hit')) {
    const on = Number(el.dataset.n) === SEARCH.at;
    el.classList.toggle('on', on);
    el.setAttribute('aria-selected', String(on));
    if (on) el.scrollIntoView({ block: 'nearest' });
  }
  $('search-text').setAttribute('aria-activedescendant', `search-hit-${SEARCH.at}`);
}

/* Replace in the transcript: the card put away and Find and replace opened with the words typed. */
function searchReplace() {
  const words = SEARCH.q.trim();
  const own = SEARCH.here ? familyApp(SEARCH.here.screen) : null;
  closeSearch(false);
  if (own && own.searchReplace) own.searchReplace(words);
}

/* ── landing ── */

/* A result opened, where the server's `go` says: a passage, its field and its line on the statements
   screen, an item on its board on PETs or GETs, the project's page, a record at its stage on Sift's
   screen, Search strategy at a term or a reason, or a claim on Trace's screen, from whichever screen the
   search was made on. The card goes first and keeps what it held. A landing that leaves no screen in
   front, its file gone since, goes to the home screen. */
async function searchGo(n) {
  const r = SEARCH.data && SEARCH.data.results[n];
  if (!r) return;
  const go = r.go || {};
  closeSearch(false);
  // each app's landing by its own script, Idiograph's a passage, a board's item or a project's page
  if (familyApp(go.screen)) await familyApp(go.screen).searchTo(go, r);
  if (!['library', 'work', 'themes', 'sift', 'sift-search', 'trace'].some(searchShown)) {
    loadLibrary().catch((err) => say(err.message, 9000));
  }
}

/* The screen in front left as any way out of it leaves it: on the statements screen a field typed into
   and not saved saved first, an interviewer note kept and the recording stopped, on PETs and GETs the
   canvas saved, on Sift's screen its acts and the words of a find box kept first, on Search strategy the
   plan's last change saved and its run let alone, and on Trace's a note kept. Sift's, Search strategy's
   and Trace's screens are put away as they are left. A save that fails keeps him where he is, and the
   answer is false. */
async function searchLeave(here) {
  // an app's own screen, Sift's screening or Search strategy and Trace's, left by its own script
  // an app's own screen left by its own script, Idiograph's, Sift's screening or Search strategy and Trace's
  if (here && familyApp(here.screen) && familyApp(here.screen).searchLeave) return familyApp(here.screen).searchLeave(here);
  return true;
}

/* The screen in front left for another part's, a board put away as the way to a statement's passage puts
   it away. False when a save keeps him where he is. */
async function searchLeaveFor(here) {
  if (!(await searchLeave(here))) return false;
  // and put away as its app's own script puts it away, Idiograph's board
  const own = here ? familyApp(here.screen) : null;
  if (own && own.searchAway) own.searchAway(here);
  return true;
}

/* ── the keys and the controls ── */

/* Cmd + F, Ctrl + F off a Mac, on any screen of the app's, Distil's, Sift's, Trace's and the home
   screen's (18 October), taken before the screen hears it, from anywhere on it, the fields included, and
   left to the browser while a card of the app's own stands over the screen. Cmd + Shift + F stays Find
   and replace's, and puts this card away first. */
function searchKey(e) {
  if (!MOD(e) || e.altKey || !((e.key || '').toLowerCase() === 'f' || e.code === 'KeyF')) return;
  if (e.shiftKey) { if (searchOpen()) closeSearch(false); return; }
  if (searchCovered() || !searchWhere()) return;
  e.preventDefault();
  e.stopPropagation();
  openSearch();
}

function searchBoot() {
  window.addEventListener('keydown', searchKey, true);
  for (const id of SEARCH_BUTTONS) {
    const b = $(id);
    if (b) b.onclick = () => { if (searchOpen()) closeSearch(); else openSearch(); };
  }
  $('search-text').addEventListener('input', () => {
    SEARCH.q = $('search-text').value;
    searchRun();
  });
  $('search-scope').addEventListener('change', () => {
    const scopes = searchScopes(SEARCH.here);
    SEARCH.scope = scopes.includes($('search-scope').value) ? $('search-scope').value : scopes[0];
    SEARCH.cases.clear();
    SEARCH.sheets.clear();
    SEARCH.projects.clear();
    searchRun(true);
  });
  // Whole word and Match case, each searched again at once, the kinds and the other filters left as they were
  for (const id of ['search-word', 'search-case']) $(id).addEventListener('change', () => searchRun(true));
  $('search-filters').addEventListener('change', (e) => {
    const box = e.target.closest('input[data-group]');
    if (!box) return;
    const set = SEARCH[box.dataset.group];
    if (box.checked) set.add(box.value); else set.delete(box.value);
    box.closest('.search-tick').classList.toggle('on', box.checked);
    searchRun(true);
  });
  // a press on a result opens it, and never takes the caret from the field first
  $('search-list').addEventListener('pointerdown', (e) => { if (e.target.closest('.search-hit')) e.preventDefault(); });
  // and the click goes no further, so the screen it lands on never takes it for a click away, which kept an
  // interviewer's note it had just opened
  $('search-list').addEventListener('click', (e) => {
    const hit = e.target.closest('.search-hit');
    if (!hit) return;
    e.stopPropagation();
    searchGo(Number(hit.dataset.n));
  });
  $('search-replace').onclick = () => searchReplace();
  $('search-more').onclick = () => { SEARCH.all = !SEARCH.all; searchMore(); searchFade(); };
  $('search-filters').addEventListener('scroll', searchFiltersScrolled);
  $('search-results').addEventListener('scroll', searchFade, { passive: true });
  $('search-side').addEventListener('scroll', searchFade, { passive: true });
  // the card's keys stay in it, so nothing behind it hears them: the arrows walk, Enter opens and Esc
  // closes, from the field and from anywhere in the card
  $('search').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeSearch(); return; }
    const inField = e.target === $('search-text');
    if (e.key === 'ArrowDown' && inField) { e.preventDefault(); e.stopPropagation(); searchStep(1); return; }
    if (e.key === 'ArrowUp' && inField) { e.preventDefault(); e.stopPropagation(); searchStep(-1); return; }
    if (e.key === 'Enter' && inField && !e.isComposing) {
      e.preventDefault();
      e.stopPropagation();
      if (SEARCH.at >= 0) searchGo(SEARCH.at);
      return;
    }
    e.stopPropagation();
  });
  // a click outside the card and its bar buttons puts it away
  document.addEventListener('pointerdown', (e) => {
    if (!searchOpen() || e.target.closest(`#search, ${SEARCH_BUTTONS.map((id) => `#${id}`).join(', ')}`)) return;
    closeSearch(false);
  }, true);
  window.addEventListener('resize', () => { if (searchOpen()) { searchPlace(); searchMore(); searchFade(); } });
}

searchBoot();
