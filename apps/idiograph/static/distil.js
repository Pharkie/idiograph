/* Idiograph's own script, Distil (the family codebase's fifth build, 23 October 2026, until then in app.js): its
   Home, its projects and their pages, the statements screen, a case's turns, quotes, notes and rounds, the
   audio, find and replace, the cards it opens, and its parts of Settings. The server holds the workbook and the
   progress file. This holds one case in memory, moves between turns, and posts every commit at once. It comes
   after the family's shell.js, whose names it uses, and registers its part with the family at its foot
   (FAMILY_APPS.idiograph), then wires its controls (distilBoot). */

'use strict';

/* ────────────────────────────────────────────────────── away time ── */

/* The pace is measured from the gap between saves. A window he has left, or a tab he has moved
   away from, is not work, so the seconds spent hidden or unfocused are counted here and taken off
   the gap by the server. The counter starts again at every save.

   The round clock in the bar keeps a running total of its own, the time away since the case
   opened, which a save never clears, so the time at the screen is the time since then less that
   total: it stands still while he is away and goes on when he comes back. Each round keeps its own
   count of that time, taken while the turn in front of him is in it (item 156). Moving into a round
   shows its count, zero the first time, and going back to an earlier one resumes its count where it
   was, so a step back to check a turn never wipes the round he is on. The glyph beside it sets the
   current round's count to zero and nothing else, and opening a case clears every count. Nothing
   about it is saved anywhere. */
let awaySince = null;
let awaySeconds = 0;
const clock = { from: Date.now(), away: 0, awaySince: null, round: null, mark: 0, counts: new Map() };

function awayStart() {
  if (awaySince === null) awaySince = Date.now();
  if (clock.awaySince === null) clock.awaySince = Date.now();
}
function awayStop() {
  if (clock.awaySince !== null) { clock.away += Date.now() - clock.awaySince; clock.awaySince = null; }
  if (awaySince === null) return;
  awaySeconds += (Date.now() - awaySince) / 1000;
  awaySince = null;
}
function awayTally() {
  const open = awaySince === null ? 0 : (Date.now() - awaySince) / 1000;
  return Math.round(awaySeconds + open);
}
function awayReset() {
  awaySeconds = 0;
  if (awaySince !== null) awaySince = Date.now();
}

/* the milliseconds at the screen since the case opened, the time away left out */
function screenMs() {
  const now = Date.now();
  const open = clock.awaySince === null ? 0 : now - clock.awaySince;
  return Math.max(0, now - clock.from - clock.away - open);
}
/* the whole seconds on the current round: its banked count and the time since it was entered */
function clockSeconds() {
  const banked = clock.counts.get(clock.round) || 0;
  return Math.max(0, Math.floor((banked + screenMs() - clock.mark) / 1000));
}
/* the turn in front of him has moved: the round left banks its time, and the round entered picks
   up its own, zero the first time */
function clockRound(round) {
  if (round === clock.round) return;
  const at = screenMs();
  clock.counts.set(clock.round, (clock.counts.get(clock.round) || 0) + at - clock.mark);
  clock.round = round;
  clock.mark = at;
}
/* the glyph: the current round's count back to zero, every other round's left as it was */
function clockReset() {
  clock.counts.set(clock.round, 0);
  clock.mark = screenMs();
}
/* opening a case: every count cleared */
function clockClear() {
  clock.from = Date.now();
  clock.away = 0;
  if (clock.awaySince !== null) clock.awaySince = clock.from;
  clock.counts.clear();
  clock.round = null;
  clock.mark = 0;
}
function drawClock() {
  const s = clockSeconds();
  $('rail-clock').textContent = `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
}

/* ── the family at the foot of each Home (the split's third build), Idiograph's part ── */

/* The sections from the case list's answer: `projects`, or from a server from before them one
   section of its root, its rows made here from the old rows when it sends no `participants`, so
   every case still opens. */
function sectionsOf(data) {
  if (Array.isArray(data.projects)) return data.projects;
  if (!data.root) return [];
  return [{ id: data.root, project: data.project || { name: '', research_question: '' }, there: true,
    participants: Array.isArray(data.participants) ? data.participants : cardsFrom(data.cases, data.recent),
    gets: data.gets || null }];
}
const DEMO_ID = 'demo';
// the thematic analysis demo's id, as the server names it back (demos, 3 November 2026)
const DEMO_TA_ID = 'demo-ta';
const isDemoId = (id) => id === DEMO_ID || id === DEMO_TA_ID;

/* The two demos as Home draws them (demos, Adam, 3 November 2026), each built on this machine: the IPA demo and
   the thematic analysis demo, each with its id, its rows and cards, its project and its tag. A server from before
   the second sends no `demos_ta`, and Home draws the IPA demo alone. */
function demosOf(data) {
  const out = [];
  if (demoRows(data).length) {
    out.push({ id: DEMO_ID, rows: demoRows(data), cards: demoCards(data), project: data.demo_project || {},
      tag: t('distil.tag.demo_ipa'), method: 'ipa' });
  }
  const ta = data && Array.isArray(data.demos_ta) ? data.demos_ta.filter((d) => d && d.path) : [];
  if (ta.length) {
    const cards = Array.isArray(data.demo_ta_participants) ? data.demo_ta_participants : cardsFrom(ta, []);
    out.push({ id: DEMO_TA_ID, rows: ta, cards: cards.map((c) => ({ ...c, demo: true })), project: data.demo_ta_project || {},
      tag: t('distil.tag.demo_ta'), method: 'ta' });
  }
  return out;
}

/* Idiograph's Home: the picker, or the page of the project `S.home` names, a demo's among them. A project gone
   from the list since is the picker again. */
function distilHomeDraw(data) {
  const sections = sectionsOf(data);
  const demo = isDemoId(S.home) ? demosOf(data).find((d) => d.id === S.home) || null : null;
  const page = demo || (S.home && !isDemoId(S.home) && sections.find((s) => s.id === S.home)) || null;
  // a project's page in its method's words, a demo's in its own, the picker in IPA's (tadraw)
  tMethod(demo ? demo.method : page && page.project ? page.project.method : 'ipa');
  if (S.home && !page) homeKeep('');
  $('home-pick').hidden = !!page;
  $('home-project').hidden = !page;
  if (demo) drawDemoPage(demo);
  else if (page) drawPage(page);
  else { drawPick(data, sections); homeHoldsRead(); }
}

/* Idiograph's projects for Open Recent (see windowRecent), in the home screen's order with the demo last */
function distilRecent(data) {
  const list = [];
  for (const s of sectionsOf(data)) {
    if (s && s.there !== false) list.push({ part: 'distil', name: (s.project && s.project.name) || t('distil.home.project'), id: s.id });
  }
  if (demoRows(data).length) list.push({ part: 'distil', name: (data.demo_project && data.demo_project.name) || t('distil.home.demo'), id: DEMO_ID, demo: true });
  // and the thematic analysis demo after it (demos)
  if (Array.isArray(data.demos_ta) && data.demos_ta.some((d) => d && d.path)) {
    list.push({ part: 'distil', name: (data.demo_ta_project && data.demo_ta_project.name) || t('distil.tag.demo_ta'), id: DEMO_TA_ID, demo: true });
  }
  return list;
}

/* Where a project stands, its card's lines as drawn (the split's pages, 21 October): its participants and how
   many of them have PETs, "3 participants, 2 with PETs", the word participant and never case, and under it its
   GETs (see `cardGetsLine`). A participant has PETs once a PETs board is there or its PETs are marked complete. A
   folder gone says so, and a project with no participant says that. */
function standLine(rows, gets, there = true) {
  if (!there) return t('distil.home.folder_gone');
  const cards = (rows || []).filter(Boolean);
  if (!cards.length) return t('distil.home.no_participants');
  const pets = cards.filter((p) => Number(p.boards) > 0 || (p.pets_complete && p.pets_complete.at)).length;
  return t('distil.home.stand', { n: cards.length, pets });
}

/* a project card's GETs line on Home: complete once marked, the group themes on its Current board, not started with none, and
   nothing for a project with no GETs card (no participant, or the demo's, whose GETs its page asks for) */
function cardGetsLine(gets) {
  if (!gets) return '';
  // a project of two or more timepoints has LGETs in the GETs' place (21 October)
  if (gets.done) return gets.lgets ? t('distil.home.lgets_complete') : t('distil.home.gets_complete');
  const n = Number(gets.themes) || 0;
  if (gets.lgets) return n ? t('distil.home.lgets_count', { n }) : t('distil.home.lgets_not_started');
  return n ? t('distil.home.gets_count', { n }) : t('distil.home.gets_not_started');
}

/* What a project card's menu holds (Adam's Way A, 21 October): Share a copy, Show in Finder (Show in
   Explorer on Windows) in Idiograph's own window alone, since a browser's page cannot open a folder,
   Project settings, Project history under it (historyui; Adam, 3 November 2026), and Remove from Idiograph,
   which a run of one project never offers. The demo's card has Project settings alone, since the demo keeps no History, and a
   card whose folder is gone Remove from Idiograph alone. */
function homeMenuItems(c, where) {
  if (c.demo) return ['settings'];
  if (c.missing) return where.oneRun ? [] : ['remove'];
  // Export as REFI-QDA under Share a copy, the other way the project leaves Idiograph (qdpxout, 8 November 2026)
  return ['share', 'qdpx', ...(where.window ? ['show'] : []), 'settings', 'history', ...(where.oneRun ? [] : ['remove'])];
}

/* the line under Share a copy, which the save panel shows in Idiograph's own window and the menu shows
   beside the item in a browser, where the copy downloads at once */
const SHARE_LINE = t('distil.share.line');

/* The card's items as the family's menu draws them (projectMenuHtml in shell.js, barsD): Share a copy and Project
   history Idiograph's own words, Show in Finder, Project settings and Remove from Idiograph the family's, and in a
   browser Share a copy's line under it */
function homeMenuRows(items, where) {
  const own = { share: t('distil.home.menu.share'), qdpx: t('distil.home.menu.qdpx'), history: t('distil.home.menu.history') };
  return items.map((act) => ({ act, word: own[act] || projectMenuWord(act, where.mac), remove: act === 'remove',
    line: act === 'share' && !where.window ? SHARE_LINE : '' }));
}

function homeMenuHtml(items, where) {
  return projectMenuHtml(homeMenuRows(items, where));
}

/* One project's card: the project's name in the serif, the demo's with its tag and a shared copy's
   with its "copy" tag, its research question, and its lines. The whole card is the button that opens
   its page. Its dots at the top right, beside the button and never in it, open its menu (see
   homeMenuItems). */
function homeCardHtml(c) {
  const where = { window: windowPicks(), mac: MAC, oneRun: !!S.oneRun };
  const items = homeMenuItems(c, where);
  // its dots and their menu, the family's (projectDotsHtml in shell.js), as Sift's and Trace's cards have them
  const dots = projectDotsHtml(c.name, homeMenuRows(items, where));
  // each demo's own tag, IPA demo or Thematic analysis demo (demos)
  const tags = (c.demo ? `<span class="tag demo">${esc(c.tag || t('distil.tag.demo'))}</span>` : '') + (c.copy ? `<span class="tag copy">${esc(t('distil.tag.copy'))}</span>` : '');
  return `<li class="home-card-li${items.length ? ' has-menu' : ''}"><button type="button" class="home-card${c.demo ? ' is-demo' : ''}" data-id="${escAttr(c.id)}">`
    + `<span class="hc-head"><span class="hc-name">${esc(c.name)}</span>${tags}</span>`
    + (c.question ? `<span class="hc-question">${esc(c.question)}</span>` : '')
    + `<span class="pc-line hc-line">${esc(c.line)}</span>`
    + (c.more ? `<span class="pc-line hc-more">${esc(c.more)}</span>` : '') + `</button>${dots}</li>`;
}

/* each card's dots open its menu, the family's (projectMenus in shell.js), and each item does its job (see
   homeMenuItems) */
function homeMenus(list) {
  projectMenus(list, (act, li) => {
    const id = li.querySelector('.home-card').dataset.id;
    homeMenuDo(act, id, li.querySelector('.hc-name').textContent, HOME_PROJECTS.get(id));
  });
}

/* What an item of a project's menu does, the menu on its card on Home and the one its "..." opens in a screen's band
   (option D of the bars, 6 November 2026), its name: `p` the project, for Project settings, and `inside` true from a screen
   of the project's own, where Remove from Idiograph leaves the screen and ends on Home (see homeRemove) */
function homeMenuDo(act, id, name, p, inside = false) {
  if (act === 'share') sendProject(id, name);
  else if (act === 'qdpx') exportQdpx(id, name);
  else if (act === 'show') showProjectFolder(id);
  else if (act === 'history') openProjectHistory(id, name);
  else if (act === 'settings') projectSettingsFor(p);
  else if (act === 'remove') homeRemove(id, name, inside);
}

/* ─────────────────────────────────────────────── Project history ── */

/* Project history, from a project's menu on Home (historyui, Adam, 3 November 2026: not a setting, so not in
   Settings): a tall sheet over Home, the project's name in its head, every change newest first under its day,
   each with its time, who made it (you in the app, or the agent by name, approved in the app or without asking
   where a hold applied), every line of what changed and the agent's account of your request. All, In the app or
   By an agent over the list, which scrolls inside the sheet and is read a page at a time from
   /api/project-history as its end comes near, as `project history` reads it, the agent's words cleaned by the
   server. Done at its foot, and Esc, shut it. */
const PH_PAGE = 50;
const PH = { id: '', by: '', list: [], total: 0, busy: false, ask: 0, back: null };

const phSameDay = (a, b) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
  && a.getDate() === b.getDate();

/* the day a change is listed under: Today, Yesterday, or the date with its year */
function phDay(d, now = new Date()) {
  const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  if (phSameDay(d, now)) return t('distil.project_history.today');
  if (phSameDay(d, yesterday)) return t('distil.project_history.yesterday');
  return tDate(d, { day: 'numeric', month: 'long', year: 'numeric' });
}

/* who made a change, as its line says */
function phWho(h) {
  // a teammate's suggestion you accepted (wtsuggest, 10 November 2026)
  if (h.by === 'member') return t('distil.project_history.member', { member: h.member || '' });
  if (h.by !== 'agent') return t('distil.project_history.you');
  const agent = h.agent || t('distil.project_history.an_agent');
  if (h.hold === 'approved') return t('distil.project_history.agent_approved', { agent });
  if (h.hold === 'without') return t('distil.project_history.agent_without', { agent });
  return agent;
}

/* one change: its time, who, every line, and what the agent says you asked */
function phRecord(h) {
  const d = new Date(h.when);
  const asked = h.by === 'agent' && h.request
    ? `<div class="ph-asked">${esc(t('distil.project_history.says', { agent: h.agent || t('distil.project_history.an_agent'), request: h.request }))}</div>` : '';
  return `<li class="ph-rec"><span class="ph-time">${esc(Number.isNaN(d.getTime()) ? '' : tTime(d))}</span><div class="ph-body">`
    + `<div class="ph-who">${esc(phWho(h))}</div>`
    + (h.changes || []).map((c) => `<div class="ph-line">${esc(c)}</div>`).join('')
    + `${asked}</div></li>`;
}

/* records under their days, each day a section with its head, which sticks at the list's top as it scrolls */
function phDays(items) {
  const days = [];
  for (const h of items) {
    const d = new Date(h.when);
    const day = Number.isNaN(d.getTime()) ? '' : phDay(d);
    if (!days.length || days[days.length - 1].day !== day) days.push({ day, items: [] });
    days[days.length - 1].items.push(h);
  }
  return days;
}

const phSection = (g) => `<section class="ph-day" data-day="${escAttr(g.day)}"><h3 class="ph-day-head">${esc(g.day)}</h3>`
  + `<ul class="ph-recs">${g.items.map(phRecord).join('')}</ul></section>`;

/* A page as it comes: the first in place of what the list held, a later one added at its foot, its first day's
   records under the last day's head where they share it, so nothing already drawn is drawn again. Then the
   head's count, the line for none and the filter's pressed choice. */
function phDraw(added, first) {
  const box = $('ph-list');
  const days = phDays(added);
  if (first) {
    box.innerHTML = days.map(phSection).join('');
    box.scrollTop = 0;
  } else {
    const last = box.lastElementChild;
    if (days.length && last && last.dataset.day === days[0].day) {
      last.querySelector('.ph-recs').insertAdjacentHTML('beforeend', days.shift().items.map(phRecord).join(''));
    }
    box.insertAdjacentHTML('beforeend', days.map(phSection).join(''));
  }
  const none = !PH.list.length;
  box.hidden = none;
  $('ph-none').hidden = !none;
  $('ph-none').textContent = PH.by === 'agent' ? t('distil.project_history.none_agent')
    : PH.by === 'app' ? t('distil.project_history.none_app') : t('distil.project_history.none_yet');
  $('ph-count').hidden = !PH.total;
  $('ph-count').textContent = t('distil.project_history.count', { n: PH.total });
  for (const b of $('ph-filter').querySelectorAll('[data-by]')) {
    const on = b.dataset.by === PH.by;
    b.classList.toggle('on', on);
    b.setAttribute('aria-checked', String(on));
  }
}

/* the next page, the first while the list is empty, an answer for another filter or project passed over. The
   list stands as it is while a page is read */
async function phMore() {
  if (PH.busy || (PH.list.length && PH.list.length >= PH.total)) return;
  PH.busy = true;
  const ask = ++PH.ask;
  const first = !PH.list.length;
  let data = null;
  try {
    data = await api('/api/project-history', { root: PH.id, by: PH.by, offset: PH.list.length, limit: PH_PAGE });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  }
  if (ask !== PH.ask) return;
  PH.busy = false;
  const added = data && Array.isArray(data.history) ? data.history : [];
  if (data) PH.total = Number(data.total) || 0;
  PH.list = PH.list.concat(added);
  if (data || first) phDraw(added, first);
  if (added.length) phNear();
}

/* more read while the list's end is within a screen of sight, so a long record reads through */
function phNear() {
  const box = $('ph-list');
  if (!$('project-history').hidden && box.scrollHeight - box.scrollTop - box.clientHeight < box.clientHeight) phMore();
}

/* All, In the app or By an agent: the list read again from its newest */
function phFilter(by) {
  if (by === PH.by) return;
  // the list stands as it is until the filter's first page comes, which takes its place
  Object.assign(PH, { by, list: [], total: 0, busy: false });
  PH.ask++;
  phMore();
}

function openProjectHistory(id, name) {
  Object.assign(PH, { id, by: '', list: [], total: 0, busy: false, back: document.activeElement });
  PH.ask++;
  $('ph-project').textContent = name;
  $('ph-list').innerHTML = '';
  $('ph-list').scrollTop = 0;
  $('ph-none').hidden = true;
  $('ph-count').hidden = true;
  $('ph-filter').onclick = (e) => { const b = e.target.closest('[data-by]'); if (b) phFilter(b.dataset.by); };
  $('ph-list').onscroll = phNear;
  $('ph-done').onclick = phShut;
  show('project-history');
  $('ph-done').focus();
  phMore();
}

function phShut() {
  hide('project-history');
  PH.ask++;
  PH.busy = false;
  if (PH.back && PH.back.isConnected) PH.back.focus();
}

/* The project open in this window, for the menu bar's File, Project History (histmenu; Adam, 4 November 2026): the
   project whose page, participant, board or code list is on screen, as `S.home` keeps it, with the name its card has.
   None on the home screen and in the demos, which keep no History, so the item stays grey there. */
function projectNow() {
  const id = S.home || '';
  if (!id || isDemoId(id)) return null;
  const p = HOME_PROJECTS.get(id) || (S.data && S.data.project && (S.data.project.id || '') === id ? S.data.project : null);
  return p && !p.demo ? { id, name: p.name || t('distil.home.project') } : null;
}
window.idiographProjectNow = () => !!projectNow();

/* The project open here for File, Project Settings (settingsplit, Adam, 5 November 2026): as projectNow has it, and
   the demos too, whose sheet is read-only as their cards' Project settings is, so the item is grey on Home alone */
function projectHere() {
  const id = S.home || '';
  if (!id) return null;
  return HOME_PROJECTS.get(id) || (S.data && S.data.project && (S.data.project.id || '') === id ? S.data.project : null);
}
window.idiographProjectSettingsNow = () => !!projectHere();
window.idiographProjectSettings = () => {
  const p = projectHere();
  if (!p) return false;
  openProjectSettings(p);
  return true;
};

/* Edit, Find and Replace in Idiograph's own window (barsD, 6 November 2026): on while the statements screen is in
   front, where its card is, as Cmd + Shift + F opens it, and grey everywhere else */
window.idiographReplaceNow = () => !!S.data && !$('work').hidden;

/* File, Project History: the same sheet Home's project menu opens, for the project open here */
window.idiographProjectHistory = () => {
  const p = projectNow();
  if (!p) return false;
  openProjectHistory(p.id, p.name);
  return true;
};

/* the sheet's keys: Esc shuts it, and the rest stay in it */
function phKeys(e) {
  if ($('project-history').hidden) return false;
  if (e.key === 'Escape') { e.preventDefault(); phShut(); }
  return true;
}

/* Send: the whole project as one file, its name the project's with .idiograph after it, which a
   browser downloads and Idiograph's own window saves where he chooses in its save dialog. The server
   writes it from the folder as it is and changes nothing in the project. */
function sentName(name) {
  const clean = String(name || '').replace(/[\\/:*?"<>|\u0000-\u001f]/g, ' ').replace(/\s+/g, ' ').trim()
    .replace(/^[. ]+|[. ]+$/g, '');
  return `${clean || t('distil.home.project')}.idiograph`;
}

/* every project card's project by its id, the demo's among them, for Project settings on its menu */
const HOME_PROJECTS = new Map();

/* Share a copy's card (23 October, Adam's design E): the project's name as its kicker, then Whole
   project, everything as it is with one tick for the audio recordings, or Choose participants, a row
   for each: its tick and name, the statements and notes always going, a PETs tick where it has PETs and
   an Audio recordings tick with their size where it has recordings, nothing where it has neither and
   dashes on a row not ticked. The rows come from /api/send-list as the card opens, so the card never
   shows a choice that would not happen. The server turns the choice into the send (`card_options`).
   Share… is there with a participant ticked. Under the choice, Boards, Current board only or All boards
   (Adam's option A, 26 October), in both forms, there only when a board file that would go holds two or
   more boards, All boards to start. */
const SC = { id: '', name: '', list: null, busy: false, back: null };
const SC_MARK = '<svg class="sc-mark" viewBox="0 0 13 13" aria-hidden="true"><path d="M2 6.8 5.2 10 11 3.2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const SC_DASH = '<span class="sc-dash" aria-hidden="true">–</span>';

// whether a choice of boards would change the send: a board file going with two or more boards, any
// participant's or the GETs' in Whole project, the PETs or LPETs of a participant ticked with their PETs
// ticked in Choose participants, where the GETs never go
function scBoardsMatter(list, whole, on, petsOn) {
  const many = (files) => (files || []).some((b) => Number(b.boards) > 1);
  const people = (list && list.participants) || [];
  if (whole) return many(list.gets_boards) || people.some((p) => many(p.boards));
  return people.some((p) => on.has(p.label) && petsOn.has(p.label) && many(p.boards));
}

// the card shut, the focus back on the dots it was opened from
function scShut() {
  hide('share-card');
  if (SC.back && SC.back.isConnected) SC.back.focus();
}

// what Whole project holds, said as one line: every participant, then their PETs and the GETs where
// the project has them
function scWholeLine(got) {
  const more = [];
  const pets = (got.participants || []).some((p) => p.pets);
  if (got.gets) {
    if (pets) return got.lgets ? t('distil.share.whole_pets_lgets') : t('distil.share.whole_pets_gets');
    return got.lgets ? t('distil.share.whole_lgets') : t('distil.share.whole_gets');
  }
  return pets ? t('distil.share.whole_pets') : t('distil.share.whole');
}

async function sendProject(id, name) {
  let got;
  try { got = await api('/api/send-list', { root: id }); } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return;
  }
  Object.assign(SC, { id, name, list: got, busy: false, back: document.activeElement });
  const people = got.participants || [];
  const pets = people.some((p) => p.pets), audio = people.some((p) => p.audio);
  $('sc-project').textContent = name;
  $('sc-whole-line').textContent = scWholeLine(got);
  $('sc-whole-audio-word').textContent = t('distil.share.audio_size', { size: got.audio_size });
  $('sc-whole-audio').checked = false;
  // a row for each participant, ticked to start, PETs ticked where it has them and recordings not
  const head = [t('distil.share.head.participants'), t('distil.share.head.statements'), pets && t('distil.share.head.pets'), audio && t('distil.share.head.audio')].filter(Boolean);
  $('sc-rows').style.gridTemplateColumns = ['minmax(0, 1fr)', 'var(--sc-st)', pets && 'var(--sc-pe)', audio && 'var(--sc-au)'].filter(Boolean).join(' ');
  $('sc-rows').innerHTML = head.map((h) => `<span class="sc-head">${h}</span>`).join('') + people.map((p, i) => {
    const cells = [`<label class="sc-name"><input type="checkbox" data-i="${i}" data-k="on" checked> ${esc(p.name || p.label)}</label>`,
      `<span class="sc-cell" data-i="${i}"><span class="sc-fixed">${SC_MARK}</span>${SC_DASH}</span>`];
    if (pets) cells.push(p.pets ? `<span class="sc-cell" data-i="${i}"><label class="sc-tick"><input type="checkbox" data-i="${i}" data-k="pets" checked aria-label="${escAttr(t('distil.share.pets_of', { name: p.name || p.label }))}"></label>${SC_DASH}</span>` : '<span></span>');
    if (audio) cells.push(p.audio ? `<span class="sc-cell" data-i="${i}"><label class="sc-tick"><input type="checkbox" data-i="${i}" data-k="audio" aria-label="${escAttr(t('distil.share.audio_of', { name: p.name || p.label }))}"> +${esc(p.audio_size)}</label>${SC_DASH}</span>` : '<span></span>');
    return cells.join('');
  }).join('');
  $('sc-whole').checked = true;
  $('sc-boards-all').checked = true;
  scSaid('');
  scDraw();
  show('share-card');
  $('sc-whole').focus();
}

// the boxes ticked in a column, by the participant's label
const scTicked = (k) => [...$('sc-rows').querySelectorAll(`input[data-k="${k}"]:checked`)].map((b) => SC.list.participants[Number(b.dataset.i)].label);

function scSaid(line) {
  $('sc-said').textContent = line;
  $('sc-said').hidden = !line;
}

// the card as the choice stands: what is under the choice made, each row's cells a tick or the muted
// mark when ticked and a dash when not, and Share… there when something would go
function scDraw() {
  const whole = $('sc-whole').checked;
  $('sc-whole-below').hidden = !whole || !SC.list.audio;
  $('sc-rows-below').hidden = whole;
  const on = new Set(scTicked('on'));
  $('sc-boards-below').hidden = !scBoardsMatter(SC.list, whole, on, new Set(scTicked('pets')));
  $('sc-rows').querySelectorAll('.sc-cell').forEach((cell) => {
    const ticked = on.has(SC.list.participants[Number(cell.dataset.i)].label);
    cell.firstElementChild.hidden = !ticked;
    cell.lastElementChild.hidden = ticked;
  });
  $('sc-go').disabled = (!whole && !on.size) || SC.busy;
}

// the card's choice as the server takes it: Whole project with its audio tick, or the rows ticked,
// and Boards, current or all, all whenever the row is not there
function scChoice() {
  const whole = $('sc-whole').checked;
  const on = new Set(whole ? [] : scTicked('on'));
  const pets = whole ? [] : scTicked('pets').filter((l) => on.has(l));
  const boards = $('sc-boards-current').checked && scBoardsMatter(SC.list, whole, on, new Set(pets)) ? 'current' : 'all';
  if (whole) return { whole: true, audio: !SC.list.audio || $('sc-whole-audio').checked, boards };
  return { participants: [...on], pets, audio: scTicked('audio').filter((l) => on.has(l)), boards };
}

/* Share…: the window's save panel with its line, the server writing the file straight to the path
   chosen, so a project with recordings never passes through the page. A browser downloads it from the
   same choice. */
async function scGo() {
  const card = scChoice();
  if ((!card.whole && !card.participants.length) || SC.busy || $('share-card').hidden) return;
  if (typeof window.idiographSavePath === 'function') {
    SC.busy = true;
    scDraw();
    try {
      const to = await window.idiographSavePath(sentName(SC.name), SHARE_LINE);
      if (!to) return;
      await api('/api/send-project', { root: SC.id, to: String(to), card });
      scShut();
    } catch (err) {
      scSaid(needsRestart(err) ? RESTART_LINE : err.message);
    } finally {
      SC.busy = false;
      if (!$('share-card').hidden) scDraw();
    }
    return;
  }
  scShut();
  const a = document.createElement('a');
  a.href = `/project/send?${new URLSearchParams({ root: SC.id, card: JSON.stringify(card) })}`;
  a.download = sentName(SC.name);
  document.body.appendChild(a);
  a.click();
  a.remove();
}

/* Export as REFI-QDA's card (qdpxout, 8 November 2026): the project's name as its kicker, Whole project or Choose
   participants, a tick each, ticked to start, and the audio recordings' tick where the project has any, off to start.
   Export… writes the .qdpx as Share… writes the copy: the window's save panel, or a browser's download. */
const QX = { id: '', name: '', list: null, busy: false, back: null };

async function exportQdpx(id, name) {
  let got;
  try { got = await api('/api/send-list', { root: id }); } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return;
  }
  Object.assign(QX, { id, name, list: got, busy: false, back: document.activeElement });
  const people = got.participants || [];
  $('qx-project').textContent = name;
  $('qx-rows').innerHTML = people.map((p, i) => `<label><input type="checkbox" data-i="${i}" checked> ${esc(p.name || p.label)}</label>`).join('');
  $('qx-audio-row').hidden = !people.some((p) => p.audio);
  $('qx-audio-word').textContent = t('distil.share.audio_size', { size: got.audio_size });
  $('qx-audio').checked = false;
  $('qx-whole').checked = true;
  qxSaid('');
  qxDraw();
  show('qdpx-card');
  $('qx-whole').focus();
}

const qxTicked = () => [...$('qx-rows').querySelectorAll('input:checked')].map((b) => QX.list.participants[Number(b.dataset.i)].label);

function qxSaid(line) {
  $('qx-said').textContent = line;
  $('qx-said').hidden = !line;
}

function qxDraw() {
  const whole = $('qx-whole').checked;
  $('qx-rows-below').hidden = whole;
  $('qx-go').disabled = (!whole && !qxTicked().length) || QX.busy;
}

// the card's choice as the server takes it: every participant, or those ticked, and the recordings' tick
function qxChoice() {
  return { participants: $('qx-whole').checked ? [] : qxTicked(), recordings: !$('qx-audio-row').hidden && $('qx-audio').checked };
}

function qxShut() {
  hide('qdpx-card');
  if (QX.back && QX.back.isConnected) QX.back.focus();
}

const qdpxName = (name) => sentName(name).replace(/\.idiograph$/, '.qdpx');

async function qxGo() {
  const card = qxChoice();
  if ((!$('qx-whole').checked && !card.participants.length) || QX.busy || $('qdpx-card').hidden) return;
  if (typeof window.idiographSavePath === 'function') {
    QX.busy = true;
    qxDraw();
    try {
      const to = await window.idiographSavePath(qdpxName(QX.name), '');
      if (!to) return;
      const done = await api('/api/qdpx-export', { root: QX.id, to: String(to), ...card });
      qxShut();
      say(t('distil.qdpx.saved', { name: done.file }), 6000);
    } catch (err) {
      qxSaid(needsRestart(err) ? RESTART_LINE : err.message);
    } finally {
      QX.busy = false;
      if (!$('qdpx-card').hidden) qxDraw();
    }
    return;
  }
  qxShut();
  const a = document.createElement('a');
  a.href = `/project/qdpx?${new URLSearchParams({ root: QX.id, card: JSON.stringify(card) })}`;
  a.download = qdpxName(QX.name);
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function qxKeys(e) {
  if ($('qdpx-card').hidden) return false;
  if (e.key === 'Escape') { e.preventDefault(); qxShut(); return true; }
  if (e.key === 'Enter' && !MOD(e) && document.activeElement !== $('qx-cancel')) { e.preventDefault(); qxGo(); }
  return true;
}

/* the card's keys: Esc shuts it, Enter presses Share… unless Cancel has the focus, and the rest stay
   in the card */
function scKeys(e) {
  if ($('share-card').hidden) return false;
  if (e.key === 'Escape') { e.preventDefault(); scShut(); return true; }
  if (e.key === 'Enter' && !MOD(e) && document.activeElement !== $('sc-cancel')) { e.preventDefault(); scGo(); }
  return true;
}

/* Show in Finder, or Show in Explorer: the server shows the project's folder, which a browser's page
   cannot, so the item is there in Idiograph's own window alone */
async function showProjectFolder(id) {
  try { await api('/api/projects', { op: 'reveal', root: id }); } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* Project settings from this card's menu: its own sheet for this card's project, the demo's read-only as ever */
function projectSettingsFor(p) {
  if (p) openProjectSettings(p);
}

/* Remove from Idiograph on the card, as Settings has it: Remove's card, the project off Home, its folder and every
   file in it left as they are, or with the card's tick moved to the system's Trash (removetrash, 10 November 2026),
   a move refused said at the foot with the project kept. From the "..." in a screen's band, `inside`, the screen is
   left first as Home leaves it, what is typed saved and a canvas flushed, a save that fails keeping him where he is
   with the project kept, and then the project goes and Home shows without it (barsD, 6 November 2026) */
async function homeRemove(id, name, inside = false) {
  const asked = await askRemove(name);
  if (!asked) return;
  if (inside && !(await goHome())) return;
  let data;
  try { data = await api('/api/projects', { op: 'remove', root: id, trash: asked.trash, page: pageId() }); } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  const shown = data.name || name;
  say(removedSaid(shown, data, t('distil.home.removed', { name: shown })), 6000);
  loadLibrary().catch((err) => say(err.message, 9000));
}

/* the project this page is in front of, by its id, for the beat (beat.js): a case's, a board's or a project page's
   behind, or the project Home shows, so another window's Remove never moves it to the Trash (removetrash) */
window.idiographAt = () => {
  const ctx = settingsCase();
  if (ctx && ctx.project && ctx.project.id) return ctx.project.id;
  return !$('library').hidden && S.home ? S.home : '';
};

/* the folder dialog's line once the shared copy is read, naming the new folder made inside the one
   chosen, as the server's own dialog says it (`into_prompt`) */
function intoSays(folder) {
  const name = String(folder || '').trim();
  return name ? t('distil.sent.into_named', { pick: PICK_SAYS.sentInto, name }) : PICK_SAYS.sentInto;
}

/* Open a shared copy, under Distil's cards: a .idiograph file opened as a copy in a new folder in the
   folder he chooses, its own name, or with "copy" after it when that is taken, then listed and opened
   like any project. In Idiograph's own window its dialogs, the file first, which the server reads
   before the folder is asked for, on a Mac in a browser the Mac's dialogs through the server, and
   off a Mac the browser's file chooser and the folder's path typed. A file that is a copy of one of
   his projects coming back opens the card (Adam's option A, 26 October, see cbOpen) before any folder
   is asked for. */
const SENT = { data: null, name: '', from: '' };

async function openSentPress() {
  const btn = $('sent-open');
  if (windowPicks()) {
    const file = await window.idiographPick(PICK_SAYS.sent, true);
    if (!file) return;
    await openSentFile(String(file));
    return;
  }
  if (S.chooseRoot) {
    // the Mac's file dialog through the server, the file read before the folder is asked for
    let read;
    try { read = await picking(() => api('/api/open-sent', { check: true }), btn); } catch (err) {
      say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
      return;
    }
    if (!read || !read.checked || !read.file) return;
    if (read.returning && await cbOpen(read, { file: read.file })) return;
    openSent({ file: read.file }, btn);
    return;
  }
  $('sent-file').click();
}

/* Open a shared copy in Idiograph's own window once the file is chosen, in its dialog or by the window (sentHanded):
   the file read first, so one it refuses says so in the server's words and asks for no folder, then the card for a
   copy coming back, or the folder for the copy */
async function openSentFile(file) {
  let read;
  try { read = await api('/api/open-sent', { file, check: true }); } catch (err) { say(err.message, 9000); return; }
  if (read && read.returning && await cbOpen(read, { file })) return;
  await sentInto({ file }, read);
}

/* A shared copy opened from outside the app (fileassoc, Adam, 6 November 2026: a tester's copy came back and the
   Finder did not know a .idiograph file for Idiograph's): a double click in the Finder or Explorer, a drop on the
   app's icon or Open With, which Idiograph's own window hands the page, a file at a time. It is Home's
   Open a shared copy with the file already chosen, so a copy coming back offers its boards to its project. The page
   finishes its start first, a card he has open is his to close first, as Home's button waits under it, and the
   screen in front is left as Home leaves it, what is typed saved, a save that fails keeping him where he is. Files
   handed together open one after another. */
const SENT_HANDED = [];
let sentHanding = false;

window.idiographOpenFile = (file) => {
  const path = String(file || '').trim();
  if (!path) return false;
  SENT_HANDED.push(path);
  if (!sentHanding) sentHanded();
  return true;
};

// a card open over the screen, or a dialog of the window's on its way
const sentWaits = () => (typeof PICKING !== 'undefined' && PICKING) || (typeof searchCovered === 'function' && searchCovered());

function sentClear() {
  return new Promise((done) => {
    const look = () => (sentWaits() ? setTimeout(look, 300) : done());
    look();
  });
}

async function sentHanded() {
  sentHanding = true;
  try {
    if (S.started) await S.started;
    while (SENT_HANDED.length) {
      await sentClear();
      const here = typeof searchWhere === 'function' ? searchWhere() : null;
      if (here && here.screen !== 'home') {
        await goHome();
        const now = searchWhere();
        // the screen would not leave, its save failing, so he stays where he is with what he typed
        if (now && now.screen !== 'home') { SENT_HANDED.length = 0; return; }
      }
      await openSentFile(SENT_HANDED.shift());
    }
  } finally { sentHanding = false; }
}

/* the copy's folder asked for, as Open a shared copy has always asked it once the file is read: the
   window's own dialog, the Mac's through the server, or off a Mac the field for the folder's path */
async function sentInto(given, read, from = '') {
  const extra = from ? { from_name: from } : {};
  if (given.data) {
    Object.assign(SENT, { data: given.data, name: given.name || '', from });
    $('sent-file-name').textContent = given.name || '';
    $('sent-typed').hidden = false;
    $('sent-into').focus();
    return;
  }
  if (windowPicks()) {
    const into = await window.idiographPick(intoSays(read && read.folder), false);
    if (into) openSent(Object.assign({ file: given.file, into: String(into) }, extra), $('sent-open'));
    return;
  }
  openSent(Object.assign({ file: given.file }, extra), $('sent-open'));
}

/* the file chosen in a browser off a Mac: read, then the card for a copy coming back, or its name shown
   and the field for the folder's path */
async function sentChosen() {
  const file = $('sent-file').files && $('sent-file').files[0];
  $('sent-file').value = '';
  if (!file) return;
  let data;
  try { data = await npBase64(file); } catch { say(t('distil.sent.unreadable'), 9000); return; }
  const given = { data, name: file.name };
  let read = null;
  try { read = await api('/api/open-sent', { data, name: file.name, check: true }); } catch (err) { say(err.message, 9000); return; }
  if (read && read.returning && await cbOpen(read, given)) return;
  sentInto(given, read);
}

function sentGo() {
  const into = $('sent-into').value.trim();
  if (!into || !SENT.data) return;
  openSent(Object.assign({ data: SENT.data, name: SENT.name, into }, SENT.from ? { from_name: SENT.from } : {}), $('sent-go'));
}

async function openSent(body, btn) {
  let data;
  try {
    data = body.into || body.data ? await api('/api/open-sent', body)
      : await picking(() => api('/api/open-sent', body), btn);
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  if (!data || !data.opened) return;
  Object.assign(SENT, { data: null, name: '', from: '' });
  $('sent-typed').hidden = true;
  $('sent-into').value = '';
  if (data.project && data.project.id) homeKeep(data.project.id);
  say(t('distil.sent.copy_in', { folder: data.folder }), 6000);
  loadLibrary().catch((err) => say(err.message, 9000));
}

/* Open a shared copy's card for a copy of one of his projects coming back (Adam's option A, 26 October, the
   card rebuilt 6 November, copyback): the copy's line, the name on the boards, filled from the name the file
   carries, and what a board comes in as, then Add its boards to the project, the choice it starts on, with
   each participant's boards from the copy, a tick each, all ticked to start, and once under them how their
   statements came, or Open as its own project. What it shows is /api/boards-in's dry run, asked again as the
   name is typed, so the names and counts are the op's own. Add brings the boards ticked in, never current,
   and opens the first participant's PETs board with its board menu open. Its button works with a board
   ticked and a name, and a line beside it says what is missing. Open as its own project goes on as Open a
   shared copy does for any file, the copy named as the other analyst's. */
const CB = { given: null, read: null, root: '', project: '', dry: null, off: new Set(), seq: 0, timer: 0, busy: false, back: null };

// the file as the card's calls send it: its path, or from a browser's file chooser its contents and name
const cbFile = () => (CB.given.data ? { data: CB.given.data, name: CB.given.name } : { file: CB.given.file });

// whose, as the board's name says it: Curt's, or Jess' for a name ending in s (the server's `whose`)
function cbWhose(name) {
  const n = String(name || '').trim().replace(/\s+/g, ' ');
  if (!n) return '';
  return /s$/i.test(n) ? t('distil.copy.whose_s', { name: n }) : t('distil.copy.whose', { name: n });
}

// a day as the board's name says it, 26 Oct
function cbDay(iso) {
  return tDate(iso, { day: 'numeric', month: 'short' });
}

/* his own boards as he sent them, untouched in the copy, which the op leaves out unless asked for (copyback2,
   8 November 2026, Adam's option A): the card leaves them out of the list, a line under the participant
   saying how many */

// each new board a row, the participants in the order of their names
const cbRowsOf = (dry) => (dry.participants || []).flatMap((p) => (p.boards || [])
  .map((b) => Object.assign({ who: p.case, path: p.path, tp: p.timepoint }, b)))
  .sort((x, y) => x.who.localeCompare(y.who));

// a board's tick, by its participant, its timepoint and its name in the copy
const cbId = (b) => JSON.stringify([b.who, b.tp || 1, b.from]);

// each participant's new boards together, as the card lists them, a timepoint after its name where there are several,
// and `sent`, how many of its boards are his own as he sent them, so a participant with only those is listed too
function cbGroupsOf(dry) {
  const rows = cbRowsOf(dry);
  return (dry.participants || []).slice().sort((x, y) => x.case.localeCompare(y.case))
    .map((p) => ({ who: p.case, tp: p.timepoint, at: p.timepoint_label || '', sent: (p.as_sent || []).length,
      boards: rows.filter((b) => b.who === p.case && b.tp === p.timepoint) }))
    .filter((g) => g.boards.length || g.sent);
}

/* how a participant's statements came, said once under its boards: those you reworded since you sent the copy
   and those you removed, the other analyst's own rewording and additions, then which wording each keeps on
   the boards, every statement counted once whichever boards hold it. `name` is the name typed. */
function cbLineSaid(group, name) {
  const keys = { reworded: new Set(), removed: new Set(), theirs: new Set(), added: new Set() };
  let n = 0;
  for (const b of group.boards) {
    n = Math.max(n, b.statements || 0);
    for (const s of b.not_matched || []) {
      const yours = s.wording === 'yours';
      const own = s.kind === 'own';
      keys[yours ? (own ? 'theirs' : 'reworded') : (own ? 'added' : 'removed')].add(s.key);
    }
  }
  const [r, x, th, a] = ['reworded', 'removed', 'theirs', 'added'].map((k) => keys[k].size);
  if (!r && !x && !th && !a) return t('distil.copy.p_all', { n });
  const who = String(name || '').trim().replace(/\s+/g, ' ') || t('distil.copy.p_other');
  const whose = cbWhose(name) || t('distil.copy.p_others');
  const said = [];
  if (r && x) said.push(t('distil.copy.p_reworded_removed', { r, x }));
  else if (r) said.push(t('distil.copy.p_reworded', { n: r }));
  else if (x) said.push(t('distil.copy.p_removed', { n: x }));
  if (th && a) said.push(t('distil.copy.p_theirs_added', { who, t: th, a }));
  else if (th) said.push(t('distil.copy.p_theirs', { who, n: th }));
  else if (a) said.push(t('distil.copy.p_added', { who, n: a }));
  const linked = r + th;
  const copy = x + a;
  if (linked && copy) said.push(a ? t('distil.copy.keep_rest', { whose }) : t('distil.copy.keep_removed', { whose }));
  else if (linked) said.push(t('distil.copy.keep_yours'));
  else said.push(t('distil.copy.keep_copy', { whose }));
  return said.join(' ');
}

// the boards ticked, as the op takes them
const cbTicked = () => cbRowsOf(CB.dry).filter((b) => !CB.off.has(cbId(b)));

// the card opened once the file is read, or false, and Open a shared copy goes on as for any file, when
// the dry run refuses it or finds no participant
async function cbOpen(read, given) {
  Object.assign(CB, { given, read, root: read.returning.root, project: read.returning.name, dry: null, off: new Set(), busy: false,
    back: document.activeElement });
  try { CB.dry = await api('/api/boards-in', Object.assign({ root: CB.root, dry_run: true }, cbFile())); } catch { return false; }
  if (!CB.dry || !(CB.dry.participants || []).length) return false;
  $('cb-project').textContent = CB.project;
  $('cb-copy').textContent = t('distil.copy.sent', { project: CB.project, day: cbDay(CB.dry.sent) });
  // the name the file carries, its sender's own, when it has one
  $('cb-who').value = CB.dry.sender || '';
  $('cb-add-word').textContent = t('distil.copy.add_to', { project: CB.project });
  const any = cbRowsOf(CB.dry).length > 0;
  $('cb-add').disabled = !any;
  $('cb-add').checked = any;
  $('cb-own').checked = !any;
  cbSaid('');
  cbDraw();
  show('copy-back');
  $('cb-who').focus();
  return true;
}

function cbSaid(line) {
  $('cb-said').textContent = line;
  $('cb-said').hidden = !line;
}

// the card as the choice, the ticks and the name stand
function cbDraw() {
  const name = $('cb-who').value;
  const who = cbWhose(name);
  const rows = cbRowsOf(CB.dry);
  const ticked = cbTicked();
  const add = $('cb-add').checked;
  $('cb-add-line').textContent = rows.length
    ? t('distil.copy.new_boards', { n: rows.length })
    : t('distil.copy.boards_there', { project: CB.project });
  $('cb-own-line').textContent = who ? t('distil.copy.own_line', { project: CB.project, who }) : CB.project;
  // what a board comes in as, the first one ticked, once a name is there
  const first = add && who ? ticked[0] : null;
  $('cb-as').textContent = first ? t('distil.copy.comes_in_as', { name: first.name }) : '';
  $('cb-as').hidden = !first;
  $('cb-below').hidden = !add;
  $('cb-all-row').hidden = rows.length < 2;
  $('cb-all').checked = ticked.length === rows.length;
  $('cb-all').indeterminate = ticked.length > 0 && ticked.length < rows.length;
  $('cb-rows').innerHTML = cbGroupsOf(CB.dry).map((g) => {
    const head = g.at ? t('distil.copy.at', { who: caseShown(g.who), at: g.at }) : caseShown(g.who);
    return `<div class="cb-group"><p class="cb-p">${esc(head)}</p>`
      + g.boards.map((b) => `<label class="cb-tick"><input type="checkbox" data-cb="${escAttr(cbId(b))}"${CB.off.has(cbId(b)) ? '' : ' checked'}>`
        + `<span>${esc(b.from)}</span></label>`).join('')
      + (g.boards.length ? `<p class="cb-line">${esc(cbLineSaid(g, name))}</p>` : '')
      + (g.sent ? `<p class="cb-line cb-sent">${esc(t('distil.copy.as_sent_left', { n: g.sent }))}</p>` : '')
      + '</div>';
  }).join('');
  // the button by the boards ticked, and while it cannot be pressed, the line beside it saying what is missing
  const none = add && !ticked.length;
  const nameless = add && !who;
  $('cb-go').textContent = add ? t('distil.copy.add_n', { n: ticked.length }) : t('distil.copy.open');
  $('cb-go').disabled = CB.busy || none || nameless;
  const need = CB.busy ? '' : none && nameless ? t('distil.copy.need_both') : none ? t('distil.copy.need_tick') : nameless ? t('distil.copy.need_name') : '';
  $('cb-need').textContent = need;
  $('cb-need').hidden = !need;
}

// the name typed: the card drawn at once, and the dry run asked again for the boards' names
function cbTyped() {
  cbSaid('');
  cbDraw();
  clearTimeout(CB.timer);
  CB.timer = setTimeout(async () => {
    const seq = ++CB.seq;
    let dry;
    try { dry = await api('/api/boards-in', Object.assign({ root: CB.root, dry_run: true, from_name: $('cb-who').value.trim() }, cbFile())); } catch (err) {
      if (seq === CB.seq && !$('copy-back').hidden) cbSaid(err.message);
      return;
    }
    if (seq !== CB.seq || $('copy-back').hidden) return;
    CB.dry = dry;
    cbDraw();
  }, 250);
}

// a board's tick, or the tick for all of them, the focus kept on the tick drawn again
function cbTick(e) {
  const box = e.target.closest('input[type="checkbox"]');
  if (!box) return;
  if (box.id === 'cb-all') {
    if (box.checked) CB.off.clear();
    else for (const b of cbRowsOf(CB.dry)) CB.off.add(cbId(b));
    cbDraw();
    return;
  }
  const id = box.dataset.cb;
  if (box.checked) CB.off.delete(id); else CB.off.add(id);
  cbDraw();
  const again = [...$('cb-rows').querySelectorAll('input[data-cb]')].find((x) => x.dataset.cb === id);
  if (again) again.focus();
}

function cbShut() {
  clearTimeout(CB.timer);
  CB.seq++;
  hide('copy-back');
  if (CB.back && CB.back.isConnected) CB.back.focus();
}

/* Add, the boards ticked, or Open… for Open as its own project */
async function cbGo() {
  if (CB.busy || $('copy-back').hidden || $('cb-go').disabled) return;
  const from = $('cb-who').value.trim();
  if (!$('cb-add').checked) {
    const { given, read } = CB;
    cbShut();
    sentInto(given, read, from);
    return;
  }
  const boards = cbTicked().map((b) => ({ participant: b.who, board: b.from, timepoint: b.tp || 1 }));
  CB.busy = true;
  cbDraw();
  let done;
  try {
    done = await api('/api/boards-in', Object.assign({ root: CB.root, from_name: from, boards }, cbFile()));
  } catch (err) {
    cbSaid(needsRestart(err) ? RESTART_LINE : err.message);
    CB.busy = false;
    if (!$('copy-back').hidden) cbDraw();
    return;
  }
  CB.busy = false;
  cbShut();
  // he lands on the first participant's PETs board, its board menu open with the new board in it
  const first = cbRowsOf(done)[0];
  if (!first || !first.path) { loadLibrary().catch((err) => say(err.message, 9000)); return; }
  const more = first.tp > 1 ? { timepoint: first.tp } : {};
  const land = () => openThemes(first.path, 'library', first.who, more);
  await navGo(land, land);
  if (!$('themes').hidden) thVmenu(true);
}

/* the card's keys: Esc shuts it, Enter presses its button unless a button has the focus */
function cbKeys(e) {
  if ($('copy-back').hidden) return false;
  if (e.key === 'Escape') { e.preventDefault(); cbShut(); return true; }
  if (e.key === 'Enter' && !MOD(e) && !e.isComposing && !(document.activeElement && document.activeElement.tagName === 'BUTTON')) {
    e.preventDefault();
    cbGo();
  }
  return true;
}

/* The Demo projects section's fold (demos, Adam, 3 November 2026: "their own thing as demo projects that's
   collapsed by default"): shut until he opens it, and kept as he leaves it, opened or shut, as Projects' fold is.
   Before he has done either, a Home with no project of his yet draws it open, so a first run finds the demos. */
const DEMOS_OPEN = 'demos:open';
const DEMOS_SHUT = 'demos:shut';

function demosFold(none) {
  const section = $('home-demos');
  const head = $('demos-head');
  const held = shutIds();
  const draw = (shut) => {
    section.classList.toggle('shut', shut);
    head.setAttribute('aria-expanded', String(!shut));
  };
  draw(held.includes(DEMOS_SHUT) || (!held.includes(DEMOS_OPEN) && !none));
  head.onclick = () => {
    const shut = !section.classList.contains('shut');
    draw(shut);
    keepFold(DEMOS_SHUT, shut);
    keepFold(DEMOS_OPEN, !shut);
  };
}

/* The picker: Distil's cards, then New project, Open project and Open a shared copy, which a run of one project
   hides, then the Demo projects section, the IPA demo and the thematic analysis demo each with its tag, then Sift's
   section and Trace's, each drawn into its own place on the page, Sift's above Distil's. */
function drawPick(data, sections) {
  foldable($('home-analysis'), $('analysis-head'), 'analysis');
  HOME_PROJECTS.clear();
  const cards = sections.map((s) => {
    if (s.project) HOME_PROJECTS.set(s.id, s.project);
    return { id: s.id, name: (s.project && s.project.name) || t('distil.home.project'), missing: s.there === false,
      copy: !!(s.project && s.project.copy), question: (s.project && s.project.research_question) || '',
      // each card in its own method's words (tadraw)
      ...tIn(s.project && s.project.method, () => ({ line: standLine(s.participants, s.gets, s.there !== false),
        more: s.there === false ? '' : cardGetsLine(s.gets) })) };
  });
  $('projects').innerHTML = cards.map(homeCardHtml).join('');
  $('projects').querySelectorAll('.home-card').forEach((b) => { b.onclick = () => openPage(b.dataset.id); });
  homeMenus($('projects'));
  // the demos in a section of their own, apart from his projects (demos)
  const demos = demosOf(data).map((d) => {
    if (d.project && d.project.name) HOME_PROJECTS.set(d.id, d.project);
    return { id: d.id, demo: true, tag: d.tag, name: d.project.name || d.tag, question: String(d.project.research_question || ''),
      line: tIn(d.method, () => standLine(d.cards)) };
  });
  $('home-demos').hidden = !demos.length;
  $('demo-projects').innerHTML = demos.map(homeCardHtml).join('');
  $('demo-projects').querySelectorAll('.home-card').forEach((b) => { b.onclick = () => openPage(b.dataset.id); });
  homeMenus($('demo-projects'));
  demosFold(!sections.length);
  $('np-line').hidden = S.oneRun;
  $('add-home-typed').hidden = true;
  if (S.oneRun) $('sent-typed').hidden = true;
}

/* A card opens its project's page at the top, the way back focused, and the way back opens the
   picker with the card it came from focused. */
function openPage(id) {
  // its entry names the way in, which Forward takes again through navGo, so no entry more is pushed
  return navGo(() => openPage(id), () => openPageNow(id));
}

function openPageNow(id) {
  homeKeep(id);
  drawHome();
  window.scrollTo(0, 0);
  $('hp-back').focus({ preventScroll: true });
}

function closePage() {
  const was = S.home;
  homeKeep('');
  drawHome();
  window.scrollTo(0, 0);
  const card = [...$('projects').querySelectorAll('.home-card'), ...$('demo-projects').querySelectorAll('.home-card')]
    .find((b) => b.dataset.id === was);
  if (card) card.focus({ preventScroll: true });
}

/* the page's head: the project's name, a demo's own tag on a demo's, `demo` the IPA demo's or `ta` the thematic
   analysis demo's, the copy tag on a shared copy's, and its question */
function pageHead(name, question, demo, copy = false) {
  $('hp-name').textContent = name;
  $('hp-demo').hidden = !demo || demo === 'ta';
  $('hp-demo-ta').hidden = demo !== 'ta';
  $('hp-copy').hidden = !copy;
  $('hp-question').textContent = question;
  $('hp-question').hidden = !question;
  if (typeof wtPageDraw === 'function') wtPageDraw(null);
  $('hp-gets').innerHTML = '';
  $('hp-gets').hidden = true;
}

/* A project's page in the order of the work (18 October): its rows, its GETs card after them and a quiet Add
   transcripts under them, which a folder that is gone does without. */
function drawPage(s) {
  const p = s.project || {};
  pageHead(p.name || t('distil.home.project'), p.research_question || '', false, !!p.copy);
  const list = $('hp-list');
  if (s.there === false) list.innerHTML = `<li class="empty">${esc(t('distil.page.folder_gone'))}</li>`;
  else drawCards(list, s.participants || [], { id: s.id });
  // Working together's tags on the rows and its lines under the question, while it is on (team.js, wtowners)
  if (typeof wtPageDraw === 'function') wtPageDraw(s.team || null);
  drawGetsCard($('hp-gets'), s.gets);
  $('hp-transcripts').hidden = s.there === false;
  $('hp-transcripts').onclick = () => openAddTranscripts(s.id);
  $('demo-reset').hidden = true;
}

/* Open project folder on the home screen: the Mac's own folder dialog, or off a Mac a field for the
   folder's path. The project added opens on its page. */
function openFolderPress() {
  if (S.chooseRoot) { addFromHome(); return; }
  $('add-home-typed').hidden = false;
  $('add-home-path').focus();
}

async function addFromHome(path) {
  const data = await addProject(path, $('add-project-home'));
  if (!data) return;
  if (data.project && data.project.id) homeKeep(data.project.id);
  loadLibrary().catch((err) => say(err.message, 9000));
}

/* Open project folder: the one page function that adds one, on the home screen and under Projects
   in Settings alike, and the one a later New project calls. With no path it opens the Mac's folder
   dialog through the server, and with one it takes the folder typed. The answer is every project
   afterwards with the one added, or null for a cancelled dialog or a refusal, which it says. */
async function addProject(path, btn) {
  let data;
  try {
    data = path ? await api('/api/projects', { op: 'add', path })
      : await picking((chosen) => api('/api/projects', { op: 'add', path: chosen }), btn, PICK_SAYS.project);
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return null; }
  return data && data.added ? data : null;
}

/* ── Back and Forward on Distil's screens (19 October) ── */

/* The browser's Back and Forward, a mouse's back and forward buttons and Cmd + [ and Cmd + ] (Alt and
   the arrows on Windows) walk Distil's screens as Sift's record walks its table (sift.js, SF_HISTORY).
   Every way in that gives a screen its way back, a statement's passage from a card, a step on a bar, a
   case, PETs or GETs from the home screen, is an entry of its own in the browser's history, which names
   the entry it was taken from. Back on such an entry does what the bar's way back does, and the bar's
   way back, its arrow, Esc and a step that goes where it goes, is Back itself, so the two never part.
   Forward after a Back takes the same way in again from the screen Back came to, the passage opened
   from the same card, and where that screen is no longer the one it was taken from Forward does
   nothing. A way back that refuses, a canvas not yet saved, keeps the screen and its entry. What is
   typed is saved on the way, as every way back saves it. The entries are the page's own, so a reload
   keeps them, and Forward then does nothing, the ways to take them again gone with the page. */
const NAV_KIND = 'idiograph-distil';
const NAV = {
  // entry numbers grow across reloads, so an entry newer in the history has a higher number
  seq: Date.now(),
  // each entry this page pushed: where it was taken from and how to take it again
  ways: new Map(),
  // each entry seen, by number, for the one it was taken from
  seen: new Map(),
  // the entry the page is on, null on one not Distil's
  cur: null,
  // the entry Forward is taking again, which its way in finds rather than pushing one
  replay: 0,
  // the browser's own moves that put back a step that did nothing, to pass over
  skip: 0,
  // one Back or Forward after another
  chain: Promise.resolve(),
};

function navHeld() {
  try {
    const held = history.state;
    return held && held.kind === NAV_KIND ? held : null;
  } catch { return null; }
}

/* the screen in front and its workbook, the place a way in is taken from */
function navHere() {
  if (!$('work').hidden) return { screen: 'statements', path: S.data ? S.data.path : '' };
  const th = $('themes');
  if (th && !th.hidden && typeof TH !== 'undefined') return { screen: TH.mode === 'gets' ? 'gets' : 'pets', path: TH.path || '' };
  if ($('traj') && !$('traj').hidden && typeof TJ !== 'undefined') return { screen: 'trajectories', path: TJ.path || '' };
  if ($('codes-screen') && !$('codes-screen').hidden && typeof CD !== 'undefined') return { screen: 'codes', path: CD.path || '' };
  // a project's page is a screen of its own, so Back from it is Home and Forward goes in again (20 October)
  if (!$('library').hidden) return !$('home-project').hidden && S.home ? { screen: 'project', path: S.home } : { screen: 'home', path: '' };
  return { screen: '', path: '' };
}

const navSame = (a, b) => !!a && !!b && a.screen === b.screen && a.path === b.path;

/* A way in taken: `open` opens the screen, and once it is in front an entry of its own is pushed,
   naming the entry it was taken from, with `again` to take it once more on Forward. Taken again by
   Forward, the browser is on that entry already, and it pushes nothing. */
async function navGo(again, open) {
  const from = navHere();
  const done = await open();
  const now = navHere();
  if (!now.screen || navSame(now, from)) return done;
  if (NAV.replay) { NAV.replay = 0; return done; }
  const held = navHeld();
  const entry = { kind: NAV_KIND, n: ++NAV.seq, p: held ? held.n : 0 };
  NAV.ways.set(entry.n, { from, again });
  NAV.seen.set(entry.n, entry);
  try { history.pushState(entry, ''); NAV.cur = entry; } catch { /* no history */ }
  return done;
}

/* The bar's way back on a screen with its entry: Back, which then takes the way back (navPop). False
   where the screen has no entry of its own, and the way back is then taken at once. */
function navBackNow() {
  if (NAV.busy || !navHeld() || !navHere().screen || navHere().screen === 'home') return false;
  history.back();
  return true;
}

/* the way back of the screen in front, taken once, true when it left */
async function navWayBack() {
  const here = navHere().screen;
  if (here === 'statements') return toLibraryNow();
  if (here === 'pets' || here === 'gets') return themesLeave();
  if (here === 'trajectories') return trajLeave();
  if (here === 'codes') return codesLeave();
  if (here === 'project') { closePage(); return true; }
  return false;
}

/* how many steps of entries lie from `from` back to the entry numbered `to` */
function navSteps(from, to) {
  let k = 1;
  let at = from;
  while (at && at.p !== to && NAV.seen.has(at.p) && k < 50) { at = NAV.seen.get(at.p); k += 1; }
  return at && at.p === to ? k : 1;
}

function navPop(e) {
  const to = e.state && e.state.kind === NAV_KIND ? e.state : null;
  const was = NAV.cur;
  NAV.cur = to;
  if (to) NAV.seen.set(to.n, to);
  if (NAV.skip) { NAV.skip -= 1; return; }
  const toN = to ? to.n : 0;
  const wasN = was ? was.n : 0;
  if (toN === wasN) return;
  NAV.chain = NAV.chain.then(() => (toN < wasN ? navBack(was, toN) : navForward(to, wasN))).catch(() => {});
}

/* Back: the way back once for each entry stepped over. One that refuses keeps the screen, and its
   entry is put back so Back stays where it was. */
async function navBack(was, toN) {
  if (!navHere().screen || navHere().screen === 'home') return;
  const steps = navSteps(was, toN);
  NAV.busy = true;
  try {
    for (let k = 0; k < steps; k += 1) {
      if (!(await navWayBack())) {
        try { history.pushState(was, ''); NAV.cur = was; } catch { /* no history */ }
        return;
      }
    }
  } finally { NAV.busy = false; }
}

/* Forward: the way in taken again from the screen Back came to, where it is still the one it was taken
   from, and otherwise nothing, the browser put back where it was */
async function navForward(to, wasN) {
  const way = NAV.ways.get(to.n);
  const undo = () => {
    NAV.skip += 1;
    NAV.cur = NAV.seen.get(wasN) || null;
    history.go(-navSteps(to, wasN));
  };
  if (!way || NAV.busy || !navSame(navHere(), way.from)) { undo(); return; }
  NAV.replay = to.n;
  await way.again();
  if (NAV.replay) { NAV.replay = 0; undo(); }
}

/* The back arrow, to the case's project's page. A field typed into and not saved is saved on the
   way, as it is on any move, and a save that fails keeps him on the case with the words still in
   the field. With its entry in the browser's history the arrow is Back, which comes here. */
async function toLibrary() {
  if (navBackNow()) return;
  await toLibraryNow();
}

async function toLibraryNow() {
  if (S.dirty && S.data && current()) {
    await commit(current(), false);
    if (S.dirty) return false;
  }
  closeFind();
  // a passage opened from a statement's card goes back to the board it came from (16 October)
  if (S.backTo) {
    const to = S.backTo;
    S.backTo = null;
    $('player').pause();
    $('library').hidden = true;
    $('work').hidden = true;
    await to.back();
    return true;
  }
  try { await loadLibrary(); } catch (err) { say(err.message, 9000); }
  return true;
}

/* Idiograph's part of Home's way (goHome): nothing while a Back is under way, and the Trajectories board puts
   itself away (trajectories.js). Undefined when Home goes on as for any screen */
async function distilHomeFirst() {
  if (NAV.busy) return false;
  if ($('traj') && !$('traj').hidden && typeof trajHome === 'function') { await trajHome(); return true; }
  if ($('codes-screen') && !$('codes-screen').hidden && typeof codesHome === 'function') { await codesHome(); return true; }
  return undefined;
}

/* Home's key, Cmd + Shift + H on a Mac as Safari's and Finder's, Alt + Home elsewhere as a browser's, on
   every screen but under a card */
const HOME_KEY_PRESSED = (e) => (MAC ? e.metaKey && e.shiftKey && !e.altKey && !e.ctrlKey
  && (e.key === 'h' || e.key === 'H' || e.code === 'KeyH')
  : e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey && e.key === 'Home');

/* The project in a screen's band (option D of the bars, Adam, 6 November 2026, after Curt found the lockup and the
   path's Home doing the same thing): its name a button with a chevron, as the participant's chooser beside it is
   (Adam, 6 November about 18:00, in place of a "..." after the name), no longer a way to its page ("everything that
   you could do from it, you can do better, quicker from inside"), opening the menu its card has on Home, drawn by
   the family's code (bandMenuOpen in shell.js) from the card's own items (homeMenuItems, homeMenuRows) and answered by
   them (homeMenuDo). The lockup at the bar's left is the way Home. */
const PATH_NAMES = ['rail-project', 'th-project', 'tj-project', 'cd-project'];

/* the project of the screen in front, the statements screen's, a board's, Trajectories' or the code list's, with
   its id, a demo's by its own, its name and whether it is a demo's, or null */
function pathProject() {
  const on = (id) => $(id) && !$(id).hidden;
  let p = null;
  let demo = false;
  if (on('work') && S.data) { p = S.data.project; demo = !!S.data.demo; }
  else if (on('themes') && typeof TH !== 'undefined') { p = TH.project; demo = !!TH.demo; }
  else if (on('traj') && typeof TJ !== 'undefined') { p = TJ.project; demo = !!(TJ.data && TJ.data.demo); }
  else if (on('codes-screen') && typeof CD !== 'undefined') { p = CD.project; demo = !!(CD.data && CD.data.demo); }
  if (!p) return null;
  const id = demo ? p.id || S.home || DEMO_ID : p.id || S.home || '';
  if (!id) return null;
  return { id, demo, name: p.name || t('distil.home.project'), project: HOME_PROJECTS.get(id) || Object.assign({}, p, { id, demo }) };
}

/* the menu of the project in front, its card's items in the same words, the demo's Project settings alone and Show in
   Finder in Idiograph's own window alone, each done from inside the project: Remove from Idiograph ends on Home */
function pathMenu() {
  const here = pathProject();
  if (!here) return null;
  const where = { window: windowPicks(), mac: MAC, oneRun: !!S.oneRun };
  return { rows: homeMenuRows(homeMenuItems(here, where), where),
    pick: (act) => homeMenuDo(act, here.id, here.name, here.project, true) };
}

function pathMenuBoot() {
  for (const id of PATH_NAMES) bandMenuWire(id, pathMenu);
}

/* the participant's name alone in the path's chooser, `P1 - Wren` shown as Wren on every stage, as a card's kicker
   has it (gets.who), the case's whole label in its tooltip */
const whoName = (label) => String(label || '').replace(/^P\d+\s*-\s*/, '').trim() || String(label || '');

/* the path's project, its whole name in its tooltip where the band cuts it short (bandNameSet in shell.js) */
function pathProjectDraw(id, project) {
  bandNameSet(id, (project && project.name) || '');
}

/* The statements bar's steps (18 October, see thStepTo in themes.js): PETs and GETs for this case, each the
   way back where the screen was opened from a card on that board, so the board comes back as he left it,
   and otherwise opened afresh, the passage in front saved first, its way back returning to this passage. */
function esStep(step) {
  if (!S.data) return;
  // in a project of two or more timepoints, PETs open on the timepoint in front of him (21 October)
  const tp = tpList() ? (tpHere() || {}).n : null;
  // the way back names its board by the step's key (TH_STEPS in themes.js)
  if (S.backTo && S.backTo.to === step && (step !== 'pets' || !tp || (S.backTo.timepoint || 1) === tp)) { toLibrary(); return; }
  const again = () => esStep(step);
  if (step === 'pets') navGo(again, () => openThemes(S.data.path, 'work', S.data.name, tp > 1 ? { timepoint: tp } : {}));
  else if (step === 'gets') navGo(again, esToGets);
  else if (step === 'lpets') navGo(again, () => esToGets({ lpets: true }));
  // in a project of two or more timepoints the project's board is its LGETs, which the server opens in the
  // GETs' place, and the Trajectories board follows them (21 October, timepoints part 3)
  else if (step === 'lgets') navGo(again, esToGets);
  else if (step === 'trajectories') navGo(again, esToTraj);
  else if (step === 'codes') navGo(again, esToCodes);
}

/* the Trajectories board from the statements bar, the passage in front saved first, its way back this passage */
async function esToTraj() {
  if (S.dirty && S.data && current()) {
    await commit(current(), false);
    if (S.dirty) return false;
  }
  $('player').pause();
  closeFind();
  const back = () => {
    if (S.recut && S.data) { S.recut = false; openCase(S.data.path); return; }
    $('work').hidden = false; measureBand(); centreCurrent(false); focusEntry();
  };
  return trajOpen(S.data.path, { back, to: 'statements', leave: () => { $('library').hidden = true; $('work').hidden = true; } });
}

/* the code list from the statements bar, a thematic analysis project's (codes), the passage saved first, its way
   back this passage */
async function esToCodes() {
  if (S.dirty && S.data && current()) {
    await commit(current(), false);
    if (S.dirty) return false;
  }
  $('player').pause();
  closeFind();
  const back = () => {
    if (S.recut && S.data) { S.recut = false; openCase(S.data.path); return; }
    $('work').hidden = false; measureBand(); centreCurrent(false); focusEntry();
  };
  return codesOpen(S.data.path, { back, to: 'statements', leave: () => { $('library').hidden = true; $('work').hidden = true; } });
}

async function esToGets(more = {}) {
  if (S.dirty && S.data && current()) {
    await commit(current(), false);
    if (S.dirty) return;
  }
  $('player').pause();
  closeFind();
  const back = () => {
    if (S.recut && S.data) { S.recut = false; openCase(S.data.path); return; }
    $('work').hidden = false; measureBand(); centreCurrent(false); focusEntry();
  };
  openGets(S.data.path, Object.assign({ back, label: '', to: 'statements' }, more));
}

/* The demo's rows from the case list's answer: `demos`, the three cases, Juno, Rowan and Mabel, or
   from a server from before them `demo`, Juno's alone, and none from a server from before the
   demo. */
function demoRows(data) {
  if (data && Array.isArray(data.demos)) return data.demos.filter((d) => d && d.path);
  return data && data.demo && data.demo.path ? [data.demo] : [];
}

/* the demo's cards, each with the demo tag. A server from before the rows sends no
   `demo_participants`, and the rows are made here from its rows */
function demoCards(data) {
  const cards = Array.isArray(data.demo_participants) ? data.demo_participants : cardsFrom(demoRows(data), []);
  return cards.map((p) => ({ ...p, demo: true }));
}

/* A demo's page, as a project's is drawn: a row for each of its three cases with the demo tag, in an
   order that is fixed, so no row has a handle, then its GETs, or the thematic analysis demo's Themes, as the
   same wide card, asked of the server afresh each time, then one quiet Reset demo that puts all three back.
   `demo` is one of `demosOf`. */
function drawDemoPage(demo) {
  const p = demo.project || {};
  pageHead(p.name || demo.tag, String(p.research_question || ''), demo.method === 'ta' ? 'ta' : true);
  drawCards($('hp-list'), demo.cards, { fixed: true });
  drawGetsHead($('hp-gets'), demo.rows[0].path, () => S.home === demo.id);
  $('hp-transcripts').hidden = true;
  $('demo-reset').hidden = false;
}

/* Reset demo on a demo's page: the demo in front put back, the thematic analysis demo's by its word */
async function resetDemo() {
  const ta = S.home === DEMO_TA_ID;
  const gone = ta ? t('distil.demo.reset_ask_ta') : t('distil.demo.reset_ask');
  if (!await askSure(gone)) return;
  try {
    await api('/api/reset-demo', ta ? { demo: 'ta' } : {});
    say(t('distil.demo.reset_done'));
    loadLibrary();
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* The GETs card's line, "3 of 6 cases in · Board 2": the cases the GETs file holds of the cases of
   the study, then the Current board's name, and "GETs complete" once marked. A server from before
   the cards sends only the cases of the study. */
function getsLine(gets) {
  const n = Number(gets.cases) || 0;
  const parts = [gets.held === undefined ? t('distil.gets.cases', { n }) : t('distil.gets.held', { held: Number(gets.held) || 0, n })];
  if (gets.board) parts.push(gets.board);
  else if (Number(gets.boards)) parts.push(t('distil.card.no_current'));
  if (gets.done) parts.push(gets.lgets ? t('distil.home.lgets_complete') : t('distil.home.gets_complete'));
  return parts.join(' · ');
}

/* The GETs of a project, a wide card after its rows since 18 October, opening the GETs screen. One
   function for any project, the case root's and the demo's alike. A server from before GETs sends
   none, and nothing is drawn. */
function drawGetsCard(box, gets) {
  if (!box || !gets || !gets.path) return;
  const title = gets.name ? t(gets.lgets ? 'distil.gets.card_title_lgets' : 'distil.gets.card_title', { name: gets.name })
    : t(gets.lgets ? 'distil.gets.card_title_lgets_this' : 'distil.gets.card_title_this');
  box.innerHTML = `<button class="gets-wide" type="button" title="${escAttr(title)}">`
    + `<span class="pc-name">${esc(t(gets.lgets ? 'distil.gets.card_name_lgets' : 'distil.gets.card_name'))}</span>`
    + `<span class="pc-line">${esc(getsLine(gets))}</span></button>`;
  box.querySelector('button').onclick = () => openGetsIn(gets.path);
  box.hidden = false;
}

/* The GETs card of the project a workbook belongs to, asked of the server: the demo's. A server
   from before it draws nothing, and an answer that lands once `still` says the page has gone is
   dropped. */
async function drawGetsHead(box, path, still = () => true) {
  if (!box || !path) return;
  let data;
  try { data = await api('/api/gets-head', { workbook: path }); } catch { return; }
  if (!data || !data.gets || !still() || box.querySelector('.gets-wide')) return;
  drawGetsCard(box, data.gets);
}

/* Experiential statements' line on a card: "64 of 207 turns", with "complete" once the phase is
   marked. A server from before the cards sends no counts, and the sheets stand in. */
function esLine(p) {
  const parts = [];
  if (p.turns && Number.isFinite(Number(p.turns.total))) parts.push(t('distil.card.passages_done', { done: Number(p.turns.done) || 0, n: Number(p.turns.total) }));
  else if ((p.sheets || []).length) parts.push(p.sheets.join(', '));
  if (p.complete) parts.push(t('distil.card.complete'));
  return parts.join(' · ');
}

/* PETs' line on a card: the Current board's name, "PETs complete" once marked and "in GETs" when
   the GETs file holds the case. A case with boards and none of them Current says "No Current
   board", and one with no board at all "No PETs yet". */
function petsLine(p) {
  const boards = p.boards === undefined ? null : Number(p.boards) || 0;
  if (!p.board && boards === 0) return t('distil.card.no_pets');
  const parts = [p.board || (boards ? t('distil.card.no_current') : '')];
  if (p.pets_complete && p.pets_complete.at) parts.push(t('distil.card.pets_complete'));
  if (p.in_gets) parts.push(t('distil.card.in_gets'));
  return parts.filter(Boolean).join(' · ');
}

/* The cards from the rows of a server from before them: one for each case label, its workbook the
   annotated one opened last, else the newest. */
function cardsFrom(rows, recent) {
  const order = new Map((recent || []).map((r, i) => [r.path, i]));
  const groups = new Map();
  for (const row of rows || []) {
    const key = row.case || row.name;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }
  const newest = (list) => list.slice().sort((a, b) => (b.modified || 0) - (a.modified || 0))[0] || null;
  const cards = [];
  for (const [name, list] of groups) {
    const books = list.filter((r) => r.kind === 'annotated');
    const opened = books.filter((r) => order.has(r.path)).sort((a, b) => order.get(a.path) - order.get(b.path));
    const pick = opened[0] || newest(books);
    const card = { case: name, demo: !!(pick || list[0]).demo, path: null, name: null, sheets: [], locked: false,
      turns: null, complete: null, board: null, pets_complete: null, in_gets: false, start: null,
      files: pick ? [pick, ...list.filter((r) => r !== pick)] : list.slice() };
    if (pick) {
      Object.assign(card, { path: pick.path, name: pick.name, sheets: pick.sheets || [], locked: !!pick.locked,
        complete: pick.complete || null, board: pick.board || null, pets_complete: pick.pets_complete || null });
    } else {
      card.start = newest(list.filter((r) => r.kind === 'raw')) || newest(list.filter((r) => r.kind === 'transcript'));
    }
    cards.push(card);
  }
  return cards;
}

/* One row, the full width of the column. At its left the handle he drags it by, none on the
   demo's, whose order is fixed. Then the case, its tags and the dots that hold Files, then the two
   halves side by side, each a button with its line in the small type: Experiential statements,
   disabled while Excel has the workbook open, and PETs, which opens all the same. A case with no
   annotated workbook reads Not started and carries Start experiential statements. On a phone the
   halves stack under the name. */
function cardHtml(p, fixed) {
  const tags = (p.demo ? `<span class="tag demo">${esc(t('distil.tag.demo'))}</span>` : '')
    + (p.locked ? `<span class="tag locked">${esc(t('distil.tag.locked'))}</span>` : '');
  // the case as the row names it, "P1 Ada", its P-number and pseudonym with no dash between
  const name = String(p.case || '').replace(/^(P\d+)\s*-\s*/, '$1 ');
  let html = fixed || p.demo ? '<span class="pc-grip none" aria-hidden="true"></span>' : gripHtml(name);
  // Edit, the participant's picture, label and pen portrait, on every row but the demo's (pbiobuild)
  const edits = !fixed && !p.demo && !!p.person;
  const dotsTitle = edits ? t('distil.card.files_edit') : t('distil.card.files');
  // the participant's picture before the name and their label under it (pbiobuild, layout A), the second rank
  // under the project's name for a screen reader, its look the h3's (a11yfix)
  html += `<div class="pc-head${p.person ? ' pp-head' : ''}">${p.person ? personPic(p.person, 44) : ''}`
    + `<div class="pp-who"><h3 class="pc-name" aria-level="2" title="${escAttr(name)}">${esc(name)}</h3>`
    + `${p.person && p.person.label ? `<span class="pp-label" title="${escAttr(p.person.label)}">${esc(p.person.label)}</span>` : ''}</div>${tags}`
    + `<button type="button" class="pc-dots" data-act="menu" aria-haspopup="true" aria-expanded="false" title="${escAttr(dotsTitle)}" aria-label="${escAttr(t('distil.card.files_of', { name }))}">&#8943;</button>`
    + `<div class="row-menu pc-menu" role="menu" hidden>`
    + `${edits ? `<button type="button" class="ghost" role="menuitem" data-act="edit">${esc(t('distil.card.edit'))}</button>` : ''}`
    + `<button type="button" class="ghost" role="menuitem" data-act="files">${esc(t('distil.card.files'))}</button></div></div>`;
  if (p.path && Array.isArray(p.timepoints) && p.timepoints.length >= 2) {
    // a project of two or more timepoints (20 October): a cell a timepoint, its label and description,
    // then where it stands, and a timepoint with no interview a dashed cell, then PETs as before
    html += `<div class="pc-tps" style="--tps:${p.timepoints.length}">` + p.timepoints.map((tp) => (tp.state === 'none'
      ? `<div class="pc-half pc-tp none"><span class="pc-label"><b>${esc(tp.label)}</b> ${esc(tp.description || '')}</span>`
        + `<span class="pc-line">${esc(t('distil.card.not_interviewed'))}</span></div>`
      : `<button type="button" class="pc-half pc-tp" data-act="timepoint" data-tp="${tp.n}"${p.locked ? ' disabled' : ''}`
        + ` title="${escAttr(t('distil.card.statements_at', { tp: [tp.label, tp.description].filter(Boolean).join(', ') }))}">`
        + `<span class="pc-label"><b>${esc(tp.label)}</b> ${esc(tp.description || '')}</span>`
        + `<span class="pc-line">${esc(tp.state === 'complete' ? t('distil.card.statements_complete')
          : t('distil.card.passages_done', { done: Number(tp.done) || 0, n: Number(tp.total) || 0 }))}</span></button>`)).join('')
      + '<button type="button" class="pc-half pc-pets" data-act="pets">'
      + `<span class="pc-label">${esc(t('distil.card.pets'))}</span><span class="pc-line">${esc(petsLine(p))}</span></button></div>`;
  } else if (p.path) {
    html += `<button type="button" class="pc-half pc-es" data-act="statements"${p.locked ? ' disabled' : ''}>`
      + `<span class="pc-label">${esc(t('distil.card.statements'))}</span><span class="pc-line">${esc(esLine(p))}</span></button>`
      // a thematic analysis project has no PETs (tadraw)
      + (tMethodNow() === 'ta' ? '' : '<button type="button" class="pc-half pc-pets" data-act="pets">'
      + `<span class="pc-label">${esc(t('distil.card.pets'))}</span><span class="pc-line">${esc(petsLine(p))}</span></button>`);
  } else {
    html += `<div class="pc-unstarted"><p class="pc-none">${esc(t('distil.card.not_started'))}</p>`
      + (p.start ? `<button type="button" class="ghost pc-start" data-act="start">${esc(t('distil.card.start'))}</button>` : '')
      + '</div>';
  }
  // the pen portrait's first two lines across the row under the name, the whole in its tooltip (pbiobuild)
  if (p.person) html += ppPortraitHtml(p.person);
  return `${html}<div class="pc-files" hidden><ul class="case-list"></ul></div>`;
}

/* ──────────────────────────── a participant's picture, label and pen portrait ── */

/* Each participant's own set (pbiobuild, 11 November 2026, Adam's layout A of pbiodraw's proposal): their picture,
   one of the app's drawn set or his own file, their label, a few words, and their pen portrait, a short paragraph,
   kept once for the project and carried by every answer that names them as `person` (see participants.py). The
   picture stands before the name wherever the participant is chosen or named, the label beside it, and on the
   project page's rows and in the pickers the pen portrait's first two lines under them. With no picture, the
   initial on their colour, as Trajectories draws it. */

/* the picture as a circle `size` pixels across, decorative beside the name it stands by */
function personPic(person, size) {
  const p = person || {};
  const colour = `case-${(Number(p.colour) || 0) % 25}`;
  const box = `width:${size}px;height:${size}px`;
  if (p.picture_url) return `<span class="tf-pic pp-pic ${colour}" style="${box}"><img src="${escAttr(p.picture_url)}" alt=""></span>`;
  const initial = String(p.who || p.case || '?').replace(/^P\d+\s*-\s*/, '').slice(0, 1) || '?';
  return `<span class="tf-pic tf-pic-none pp-pic ${colour}" style="${box};font-size:${Math.round(size * 0.42)}px" aria-hidden="true">${esc(initial)}</span>`;
}

/* the pen portrait on a row, two lines and the whole in its tooltip, nothing when there is none */
function ppPortraitHtml(person) {
  const text = person && person.portrait ? String(person.portrait) : '';
  return text ? `<p class="pp-portrait" title="${escAttr(text)}">${esc(text)}</p>` : '';
}

/* The fields across the row (layout A): the picture with Change picture..., Choose from the set and Remove, the
   participant greyed, the label and the pen portrait, each kept as it is left, Done at the foot. Choose from the set
   opens the drawn faces under the fields, shut each time the fields open. */
const PP = { editing: '', faces: false, busy: false, root: '', li: null, p: null };

function ppEditHtml(p) {
  const person = p.person || {};
  const name = caseShown(p.case);
  // a field drawn again while its save is on its way shows what was typed, never the set before it
  const typed = (key) => (PP.sent && key in PP.sent ? PP.sent[key] : String(person[key] || ''));
  const faces = PP.faces ? `<div class="tf-faces pp-faces" role="group" aria-label="${escAttr(t('trajectories.choose_face'))}">`
    + (PP_FACES.map((f, i) => `<button type="button" class="tf-face${person.picture === `set:${f}` ? ' on' : ''}" data-pp-face="${f}"`
      + ` aria-pressed="${person.picture === `set:${f}`}" aria-label="${escAttr(t('trajectories.face_n', { n: i + 1 }))}"><img src="/faces/${f}.svg" alt=""></button>`).join(''))
    + '</div>' : '';
  return `<div class="pp-edit" role="group" aria-label="${escAttr(t('distil.person.edit_label', { who: name }))}">`
    + `<div class="tf-edit-pic pp-edit-pic">${personPic(person, 64)}<div class="tf-edit-picb">`
    + `<button type="button" class="ghost small" data-pp="own">${esc(t('trajectories.change_picture'))}</button>`
    + `<button type="button" class="ghost small" data-pp="faces" aria-expanded="${PP.faces}">${esc(t('trajectories.choose_from_set'))}</button>`
    + (person.picture ? `<button type="button" class="ghost small" data-pp="nopic">${esc(t('trajectories.remove_picture'))}</button>` : '')
    + '</div></div><div class="pp-edit-fields">'
    + `<label class="pp-l"><span>${esc(t('distil.person.participant'))}</span><span class="pp-namerow"><input class="tf-edit-in pp-in" value="${escAttr(name)}" disabled>`
    // Rename... after the greyed name, on a participant in a folder of its own and never the demo's, whose names are fixed
    + `${!p.demo && p.folder !== false ? `<button type="button" class="ghost small pp-rename" data-pp="rename">${esc(t('distil.card.rename_ellipsis'))}</button>` : ''}</span></label>`
    + `<label class="pp-l"><span>${esc(t('distil.person.label'))}</span><input class="tf-edit-in pp-in pp-in-label" maxlength="60" data-pp-field="label" value="${escAttr(typed('label'))}"></label>`
    + `<label class="pp-l top"><span>${esc(t('distil.person.portrait'))}</span><textarea class="tf-edit-in pp-in pp-in-portrait" maxlength="800" rows="4" data-pp-field="portrait">${esc(typed('portrait'))}</textarea></label>`
    + `${faces}<div class="pp-foot"><button type="button" class="primary small" data-pp="done">${esc(t('trajectories.done'))}</button></div></div></div>`;
}

/* a participant in a picker: the name as the rows say it, their label under it and the pen portrait's first two
   lines under that, for the statements screen's picker and the PETs and LPETs switcher alike */
function ppMenuText(label, person) {
  const p = person || {};
  return `<span class="pp-mi"><span class="pp-mname">${esc(caseShown(label))}</span>`
    + (p.label ? `<span class="pp-label">${esc(p.label)}</span>` : '')
    + (p.portrait ? `<span class="pp-bio">${esc(p.portrait)}</span>` : '') + '</span>';
}

/* the picture and the label beside the name in the bar over a participant's screens (layout A): `pic` and `lab`
   the bar's two spans, the label giving way first in a narrow window, the whole in its tooltip */
function ppBarDraw(pic, lab, person) {
  const p = person || null;
  if (pic) {
    pic.innerHTML = p ? personPic(p, 24) : '';
    pic.hidden = !p;
  }
  if (lab) {
    lab.textContent = p && p.label ? p.label : '';
    lab.title = p && p.label ? p.label : '';
    lab.hidden = !(p && p.label);
  }
}

// the app's drawn set, static/faces/face01.svg to face24.svg, as Trajectories offers it
const PP_FACES = Array.from({ length: 24 }, (_, i) => `face${String(i + 1).padStart(2, '0')}`);

/* the fields opened across a row, any other row's shut first, the field he double-clicked in front */
function ppOpen(li, p, where, field = 'label') {
  if (!li || !p || !p.person || p.demo || !where.id) return;
  ppClose();
  Object.assign(PP, { editing: p.case, faces: false, root: where.id, li, p, sent: {} });
  li.classList.add('pp-open');
  ppDraw();
  const f = li.querySelector(field === 'portrait' ? '.pp-in-portrait' : '.pp-in-label');
  if (f) { f.focus(); f.setSelectionRange(f.value.length, f.value.length); }
}

/* the fields drawn again in place, the field in front kept in front */
function ppDraw() {
  const li = PP.li;
  if (!li) return;
  const front = document.activeElement && li.contains(document.activeElement) ? document.activeElement.dataset.ppField || document.activeElement.dataset.pp : '';
  const old = li.querySelector('.pp-edit');
  const was = li.querySelector('.pp-portrait');
  const box = document.createElement('div');
  box.innerHTML = ppEditHtml(PP.p);
  const edit = box.firstElementChild;
  if (old) old.replaceWith(edit);
  else li.insertBefore(edit, li.querySelector('.pc-files'));
  if (was) was.hidden = true;
  ppFit(edit.querySelector('.pp-in-portrait'));
  if (front) {
    const again = li.querySelector(`[data-pp-field="${front}"], [data-pp="${front}"]`);
    if (again) again.focus();
  }
}

/* the pen portrait's box as tall as its words, five lines at the least (its CSS), so no line is ever cut */
function ppFit(box) {
  if (!box) return;
  box.style.height = 'auto';
  box.style.height = `${box.scrollHeight + box.offsetHeight - box.clientHeight}px`;
}

/* the fields shut, what was typed kept first, and the row drawn again with what is kept */
function ppClose(focusRow = false) {
  const li = PP.li;
  if (!li) return;
  ppKeepFields();
  const edit = li.querySelector('.pp-edit');
  if (edit) edit.remove();
  li.classList.remove('pp-open');
  ppRowFill(li, PP.p);
  const name = li.querySelector('.pc-dots');
  Object.assign(PP, { editing: '', faces: false, li: null, p: null });
  if (focusRow && name) name.focus();
}

/* the row's picture, label and pen portrait as the participant's set now stands */
function ppRowFill(li, p) {
  if (!li || !p) return;
  const person = p.person || {};
  const pic = li.querySelector('.pc-head > .pp-pic');
  if (pic) pic.outerHTML = personPic(person, 44);
  const who = li.querySelector('.pp-who');
  let label = who && who.querySelector('.pp-label');
  if (who && person.label) {
    if (!label) { label = document.createElement('span'); label.className = 'pp-label'; who.appendChild(label); }
    label.textContent = person.label;
    label.title = person.label;
  } else if (label) label.remove();
  const was = li.querySelector('.pp-portrait');
  const box = document.createElement('div');
  box.innerHTML = ppPortraitHtml(person);
  if (was) was.remove();
  if (box.firstElementChild && !li.querySelector('.pp-edit')) li.insertBefore(box.firstElementChild, li.querySelector('.pc-files'));
}

/* a change to the participant's set, through the one route agents use too, one at a time in the order made, the
   answer taken as the row's own. A refusal says its line and keeps nothing. */
PP.chain = Promise.resolve();
function ppSave(given) {
  const p = PP.p;
  const root = PP.root;
  if (!p) return Promise.resolve(false);
  const run = async () => {
    try {
      const got = await api('/api/participant', Object.assign({ root, case: p.case }, given));
      if (got && got.person) p.person = Object.assign({}, p.person, got.person);
      return true;
    } catch (err) {
      say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
      return false;
    }
  };
  const done = PP.chain.then(run);
  PP.chain = done.catch(() => false);
  return done;
}

/* the label and the pen portrait kept as they stand in their fields, each only when it differs from what was last
   kept or sent */
function ppKeepFields() {
  const li = PP.li;
  const p = PP.p;
  if (!li || !p) return Promise.resolve();
  PP.sent = PP.sent || {};
  const given = {};
  for (const f of li.querySelectorAll('[data-pp-field]')) {
    const key = f.dataset.ppField;
    const now = f.value.replace(/\s+/g, ' ').trim();
    const was = key in PP.sent ? PP.sent[key] : String((p.person || {})[key] || '');
    if (now !== was) given[key] = now;
  }
  if (!Object.keys(given).length) return Promise.resolve();
  Object.assign(PP.sent, given);
  return ppSave(given).then((ok) => {
    if (!ok) for (const key of Object.keys(given)) delete PP.sent[key];
    if (PP.li !== li) ppRowFill(li, p);
  });
}

/* his own picture, read in the page and made a square of 256 pixels at its middle, as Trajectories makes it */
async function ppOwnPicture(file) {
  if (!file || !PP.p) return;
  const url = URL.createObjectURL(file);
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    const side = Math.min(img.naturalWidth, img.naturalHeight);
    if (!side) throw new Error('empty');
    const to = Math.min(256, side);
    const canvas = document.createElement('canvas');
    canvas.width = to;
    canvas.height = to;
    canvas.getContext('2d').drawImage(img, (img.naturalWidth - side) / 2, (img.naturalHeight - side) / 2, side, side, 0, 0, to, to);
    if (await ppSave({ data: canvas.toDataURL('image/png') })) ppDraw();
  } catch {
    say(t('trajectories.picture_unread'), 9000);
  } finally {
    URL.revokeObjectURL(url);
  }
}

/* the fields' own clicks and keys, wired once on the rows' list */
function ppWire() {
  const list = $('hp-list');
  if (!list || list.dataset.ppWired) return;
  list.dataset.ppWired = '1';
  list.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-pp], [data-pp-face]');
    if (!b || !PP.li || !PP.li.contains(b)) return;
    e.stopPropagation();
    if (b.dataset.ppFace) { if (await ppSave({ picture: `set:${b.dataset.ppFace}` })) ppDraw(); return; }
    const what = b.dataset.pp;
    if (what === 'done') { ppClose(true); return; }
    if (what === 'rename') { openRename(PP.root, PP.p); return; }
    if (what === 'faces') { PP.faces = !PP.faces; ppDraw(); return; }
    if (what === 'nopic') { if (await ppSave({ picture: '' })) ppDraw(); return; }
    if (what === 'own') $('pp-picture-file').click();
  });
  list.addEventListener('focusout', (e) => {
    const f = e.target.closest && e.target.closest('[data-pp-field]');
    if (f && PP.li && PP.li.contains(f)) ppKeepFields();
  });
  // the pen portrait's box grows with its words as they are typed
  list.addEventListener('input', (e) => {
    if (e.target.classList && e.target.classList.contains('pp-in-portrait')) ppFit(e.target);
  });
  list.addEventListener('keydown', (e) => {
    if (!PP.li || !PP.li.contains(e.target)) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); ppClose(true); return; }
    if (e.key === 'Enter' && e.target.dataset.ppField === 'label') { e.preventDefault(); ppKeepFields(); }
  });
  $('pp-picture-file').addEventListener('change', (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    ppOwnPicture(file);
  });
}

/* The rows of a project, in the order the server sends, his order. Each row's buttons do what
   the rows of the old list did: the Statements half opens the case at its last turn, PETs opens
   its PETs screen, Start runs the create card on a raw source or the make a workbook card on a
   transcript in another shape, and Files lists every file of the case under the row, each doing
   what its row did. The handle drags the row, and Alt and an arrow on it move the row one place,
   and either way the order is saved in the project's file (see `saveOrder`). `where` is the
   project, `{id}`, or `{fixed: true}` for the demo, whose rows have no handle. */
function drawCards(list, cards, where = {}) {
  // fields open on a row of this list are kept as they stand and shut, the rows drawn afresh (pbiobuild)
  if (PP.li && list.contains(PP.li)) {
    ppKeepFields();
    Object.assign(PP, { editing: '', faces: false, li: null, p: null });
  }
  ppWire();
  list.innerHTML = '';
  if (!cards.length) {
    list.innerHTML = `<li class="empty">${esc(t('distil.card.no_workbooks'))}</li>`;
    return;
  }
  const fixed = !!where.fixed || !where.id;
  for (const p of cards) {
    const li = document.createElement('li');
    li.className = `pcard prow${p.path ? '' : ' unstarted'}${tMethodNow() === 'ta' ? ' ta' : ''}${p.path && Array.isArray(p.timepoints) && p.timepoints.length >= 2 ? ' longi' : ''}`;
    li.dataset.case = p.case;
    li.innerHTML = cardHtml(p, fixed);
    renderFiles(li.querySelector('.pc-files ul'), p.files || []);
    const menu = li.querySelector('.pc-menu');
    const dots = li.querySelector('.pc-dots');
    const files = li.querySelector('.pc-files');
    const shut = () => { menu.hidden = true; dots.setAttribute('aria-expanded', 'false'); };
    li.onclick = (e) => {
      const act = e.target.closest('[data-act]');
      if (!act || act.disabled) return;
      const what = act.dataset.act;
      if (what === 'grip') return;
      if (what === 'menu') {
        const open = menu.hidden;
        closeCardMenus();
        menu.hidden = !open;
        dots.setAttribute('aria-expanded', String(open));
        if (open) menu.querySelector('button').focus();
        return;
      }
      if (what === 'files') {
        shut();
        files.hidden = !files.hidden;
        menu.querySelector('[data-act="files"]').textContent = files.hidden ? t('distil.card.files') : t('distil.card.hide_files');
        dots.focus();
        return;
      }
      if (what === 'edit') { shut(); ppOpen(li, p, where); return; }
      // Working together: Ask for review, on a participant he owns (review.js)
      if (what === 'wtask') { shut(); rvwAskOpen(where.id, p); return; }
      if (what === 'statements') openCaseIn(p.path);
      else if (what === 'timepoint') openCaseIn(p.path, { timepoint: Number(act.dataset.tp) });
      else if (what === 'pets') openThemesIn(p.path, p.case);
      else if (what === 'start') (p.start.kind === 'transcript' ? offerImport(p.start) : offerCreate(p.start));
    };
    // a double-click on the name, the label or the pen portrait opens the participant's fields across the row
    // (pbiobuild, layout A), the one double-clicked in front
    li.ondblclick = (e) => {
      if (fixed || p.demo || PP.li === li) return;
      const on = e.target.closest('.pc-name, .pp-label, .pp-portrait');
      if (!on) return;
      e.preventDefault();
      const sel = window.getSelection && window.getSelection();
      if (sel) sel.removeAllRanges();
      ppOpen(li, p, where, on.classList.contains('pp-portrait') ? 'portrait' : 'label');
    };
    // the arrows walk the menu as the band's does, and Esc gives the dots the focus back (a11yfix)
    menu.onkeydown = (e) => menuKeys(e, menu, () => { shut(); dots.focus(); });
    const grip = li.querySelector('button.pc-grip');
    if (grip && !fixed) {
      const how = cardGrip(list, where.id);
      grip.onpointerdown = (e) => gripDrag(e, li, list, how);
      // a block body, so a key the handle does not take goes on its way, Tab among them (a11yfix)
      grip.onkeydown = (e) => { gripKeys(e, li, list, how); };
    }
    if (typeof rvwRow === 'function') rvwRow(li, p, where);
    list.appendChild(li);
  }
}

/* ─────────────────────────────────────────── rename a participant ── */

/* Rename, in the dots on a case's row (16 October, Adam's word on a tester's feedback, since a
   pseudonym given once sometimes changes): the case's name now, a field for the new one, one unticked
   row, Rename the folder too, and the list of what will change, asked of the server as the card opens
   and again as the name or the tick changes, so it stands before anything is written. Rename writes,
   the card goes and the rows are drawn again under the new name. A refusal is one line in the card and
   changes nothing, and Cancel and Esc change nothing. */
const RN = { root: '', label: '', ask: 0, busy: false, timer: 0 };

// a case as its row names it, "P1 Ada", its P-number and pseudonym with no dash between
const caseShown = (label) => String(label || '').replace(/^(P\d+)\s*-\s*/, '$1 ');

function openRename(root, p) {
  Object.assign(RN, { root: root || '', label: p.case, busy: false });
  RN.ask += 1;
  $('rn-now').textContent = caseShown(p.case);
  $('rn-name').value = '';
  $('rn-folder').checked = false;
  $('rn-list').innerHTML = '';
  $('rn-go').disabled = false;
  rnSaid('');
  show('rename');
  $('rn-name').focus();
  rnPlan();
}

function rnSaid(line) {
  $('rn-said').textContent = line;
  $('rn-said').hidden = !line;
  rnListShow();
}

/* The list stands under its lead-in while it holds a line and no refusal shows, since a refused name
   changes nothing (17 October, after the screenshot check found the list beside the refusal), and the line
   about the copies goes with them, since a refused rename keeps none (17 October, later) */
function rnListShow() {
  const shown = $('rn-said').hidden && $('rn-list').children.length > 0;
  $('rn-list').hidden = !shown;
  $('rn-lead').hidden = !shown;
  $('rn-copy').hidden = !shown;
}

const rnAsked = () => ({ root: RN.root, case: RN.label, name: $('rn-name').value, folder: $('rn-folder').checked });

/* What will change, each file a line, the folder's and the moves' after the rest while the tick is on.
   An answer that lands after a later ask, or once the card has gone, is dropped. */
async function rnPlan() {
  const ask = ++RN.ask;
  let got;
  try {
    got = await api('/api/rename', { op: 'plan', ...rnAsked() });
  } catch (err) {
    if (ask === RN.ask && !$('rename').hidden) rnSaid(needsRestart(err) ? RESTART_LINE : err.message);
    return;
  }
  if (ask !== RN.ask || $('rename').hidden) return;
  const lines = [...(got.lines || []), ...($('rn-folder').checked ? got.folder_lines || [] : [])];
  $('rn-list').innerHTML = lines.map((l) => `<li>${esc(l)}</li>`).join('');
  rnListShow();
}

/* the list asked again a moment after the typing stops, and at once for the tick */
function rnTyped() {
  rnSaid('');
  clearTimeout(RN.timer);
  RN.timer = setTimeout(rnPlan, 180);
}

async function rnGo() {
  if (RN.busy || $('rename').hidden) return;
  RN.busy = true;
  $('rn-go').disabled = true;
  try {
    const got = await api('/api/rename', { op: 'rename', ...rnAsked() });
    hide('rename');
    say(t('distil.rename.done', { old: caseShown(got.old), now: caseShown(got.case) }));
    loadLibrary().then(() => rnShowRow(got.case)).catch((err) => say(err.message, 9000));
  } catch (err) {
    rnSaid(needsRestart(err) ? RESTART_LINE : err.message);
  } finally {
    RN.busy = false;
    $('rn-go').disabled = false;
  }
}

/* The renamed row once the rows are drawn again, in the middle of the window and clear of the line at
   the foot that says the rename (16 October, after the screenshot check at 360): a row the page
   cannot scroll far enough to clear the line has the line stand just above it instead, until the
   next line is said. */
function rnShowRow(label) {
  const row = [...$('hp-list').querySelectorAll(':scope > li.prow')].find((li) => li.dataset.case === label);
  if (!row || $('library').hidden) return;
  row.scrollIntoView({ block: 'center' });
  const toast = $('toast');
  if (toast.hidden) return;
  const at = row.getBoundingClientRect();
  const line = toast.getBoundingClientRect();
  if (at.bottom + 8 <= line.top || at.top >= line.bottom + 8) return;
  toast.style.bottom = `${Math.max(8, window.innerHeight - at.top + 8)}px`;
}

/* the case labels of a project's rows, top to bottom, as `order` keeps them */
const labelsOf = (list) => [...list.querySelectorAll(':scope > li.prow')].map((li) => li.dataset.case);

/* His order, saved in the project's file as `order` once a row has moved, every other key of the
   file kept by the server. A server from before it says to restart, and the rows stay where he
   put them until the next listing. */
async function saveOrder(id, list) {
  try {
    await api('/api/order', { root: id, order: labelsOf(list) });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* the handle's `how` on a project's rows: the case said by its P-number and pseudonym, and his order
   saved in the project's file */
function cardGrip(list, id) {
  return {
    rows: ':scope > li.prow',
    live: 'order-said',
    said: (li, to, n) => `${String(li.dataset.case).replace(/^(P\d+)\s*-\s*/, '$1 ')}, ${to + 1} of ${n}`,
    moved: () => saveOrder(id, list),
  };
}

/* a click anywhere else shuts any card's menu, as a menu does */
function closeCardMenus(except) {
  for (const menu of document.querySelectorAll('#library .pc-menu')) {
    if (menu === except || menu.hidden) continue;
    menu.hidden = true;
    const dots = menu.parentElement.querySelector('.pc-dots');
    if (dots) dots.setAttribute('aria-expanded', 'false');
  }
}
document.addEventListener('click', (e) => {
  if (!e.target.closest || !e.target.closest('.pc-head')) closeCardMenus();
  else closeCardMenus(e.target.closest('.pc-head').querySelector('.pc-menu'));
});

/* Every checkbox and radio ticks from its whole row (13 October), Distil and Sift alike. The row
   is the tick's <label> wherever it can be, and the shared rule in style.css gives it a pointer and
   the row's wash on hover. Where a row holds other controls too, a name box, Remove or a handle, the
   row carries `data-tick-row` and its tick sits in a label of its own: a press anywhere on the row
   but on a control or on that label, which ticks by itself, ticks its box. A press that began on a
   control, a handle's drag among them, ticks nothing. The suite's checkbox scan fails on a tick
   outside a label. */
const TICK_SKIP = 'label, a, button, input, select, textarea, summary, [contenteditable="true"]';
let tickPressed = null;
function tickRowClick(e) {
  const t = e.target;
  const row = t && t.closest ? t.closest('[data-tick-row]') : null;
  if (!row || e.defaultPrevented || t.closest(TICK_SKIP)) return false;
  const began = tickPressed;
  if (began && (!row.contains(began) || (began.closest && began.closest(TICK_SKIP)))) return false;
  const box = row.querySelector('input[type="checkbox"], input[type="radio"]');
  if (!box || box.disabled) return false;
  box.click();
  return true;
}
document.addEventListener('pointerdown', (e) => { tickPressed = e.target; }, true);
document.addEventListener('click', (e) => { tickRowClick(e); tickPressed = null; });

/* Files: every file of a case the old list showed, each a row with its tag that does what its row
   did, its sheets and marks in the small type. An annotated workbook opens the case and carries
   PETs beside it, a raw source opens the create card and a transcript in another shape the make a
   workbook card. */
function renderFiles(list, items) {
  list.innerHTML = '';
  for (const item of items) {
    const li = document.createElement('li');
    // a transcript in another shape is offered as a raw source is, to be made into a workbook first
    const transcript = item.kind === 'transcript';
    const raw = item.kind === 'raw' || transcript;
    // the sheets of the workbook, never a path, which carries the folder's full name
    const meta = (item.sheets || []).join(', ');
    // the two phases each say so in the row's small type once marked, Statements complete and PETs
    // complete, the date in the tooltip, and a case with both says Case complete in their place. An
    // older server sends no mark, and nothing shows
    const marks = raw ? '' : caseMarks(item);
    li.innerHTML = `<button class="case-row" type="button" ${item.locked ? 'disabled' : ''}>
        <span class="case-name">${esc(item.name)}</span>
        ${raw ? `<span class="tag raw">${esc(transcript ? t('distil.files.make_workbook') : t('distil.files.create_workbook'))}</span>` : ''}
        ${item.locked ? `<span class="tag locked">${esc(t('distil.tag.locked'))}</span>` : ''}
        <span class="case-meta">${esc(meta)}${marks}</span>
        ${!raw && item.board ? `<span class="case-board" title="${escAttr(t('distil.files.current_title'))}">${esc(t('distil.files.current', { board: item.board }))}</span>` : ''}
      </button>`;
    li.querySelector('button').onclick = () => (transcript ? offerImport(item) : raw ? offerCreate(item) : openCaseIn(item.path));
    // an annotated workbook opens on its PETs screen from here too. The workbook is only read
    // there, so one Excel has open opens as well
    if (!raw) {
      const themes = document.createElement('button');
      themes.type = 'button';
      themes.className = 'case-themes';
      themes.textContent = t('distil.card.pets');
      themes.title = t('distil.files.pets_title');
      themes.onclick = () => openThemesIn(item.path, item.case);
      li.classList.add('has-themes');
      li.appendChild(themes);
    }
    list.appendChild(li);
  }
}

/* ─────────────────────────────────────────────────────── the days ── */

/* In the head of the home screen, top right beside the wordmark and under it on a narrow screen
   (item 195), eight weeks of small squares (item 159): a column a week, Monday at the top and
   the newest week on the right, each day tinted by the rounds closed on it across every case under
   the root, in four steps of the accent, none, one, two, and three or more, with today outlined
   and its figure in a tooltip, "Thu 1 Oct: 3 rounds". Days still to come in this week are left
   blank. One line under it gives the run of days the target was met and how often it was met in
   the last fourteen days, "4 days running. Target met 9 of the last 14 days.", counting today
   once its target is met, the way the round card's streak does, and it is left out while the
   eight weeks hold no round at all. The tally comes from `/api/days`, which sums every case's, and
   a server without it draws nothing. Nothing here writes. */
const DAYS_WEEKS = 8;
const DAYS_SPAN = 14;
/* a square's day in its tooltip, Thu 3 Sep, through Intl in UTC (i18n.js's tDate) */
const DAYS_TIP = { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' };

const isoDay = (d) => d.toISOString().slice(0, 10);
const dayShift = (d, k) => { const x = new Date(d.getTime()); x.setUTCDate(x.getUTCDate() + k); return x; };

/* The squares and the line, from the server's answer: the columns, oldest first, each of seven
   days from Monday, a day still to come as null, every other with its rounds, its step and its
   tooltip. Dates are taken in UTC throughout, so a change of the clocks never moves a day. */
function daysModel(data) {
  const today = new Date(`${data && data.today}T00:00:00Z`);
  if (Number.isNaN(today.getTime())) return null;
  const tally = (data && data.days) || {};
  const target = Math.max(1, Number(data.dailyTarget) || 2);
  const rounds = (d) => Number(tally[isoDay(d)]) || 0;
  const first = dayShift(today, -((today.getUTCDay() + 6) % 7) - 7 * (DAYS_WEEKS - 1));
  const columns = [];
  let any = false;
  for (let w = 0; w < DAYS_WEEKS; w += 1) {
    const column = [];
    for (let k = 0; k < 7; k += 1) {
      const d = dayShift(first, 7 * w + k);
      if (d > today) { column.push(null); continue; }
      const n = rounds(d);
      if (n) any = true;
      column.push({ iso: isoDay(d), rounds: n, step: Math.min(3, n), today: d.getTime() === today.getTime(),
        tip: n ? t('distil.days.tip', { day: tDate(d, DAYS_TIP), n }) : t('distil.days.tip_none', { day: tDate(d, DAYS_TIP) }) });
    }
    columns.push(column);
  }
  const last = rounds(today) >= target ? today : dayShift(today, -1);
  let running = 0;
  for (let d = last; rounds(d) >= target; d = dayShift(d, -1)) running += 1;
  let met = 0;
  for (let k = 0; k < DAYS_SPAN; k += 1) if (rounds(dayShift(last, -k)) >= target) met += 1;
  const line = !any ? '' : running ? t('distil.days.line_running', { n: running, met, span: DAYS_SPAN })
    : t('distil.days.line', { met, span: DAYS_SPAN });
  return { columns, line, running, met };
}

function drawDays(data) {
  const box = $('days');
  const model = data ? daysModel(data) : null;
  box.hidden = !model;
  if (!model) { box.innerHTML = ''; return; }
  const cells = model.columns.flat().map((d) => (d
    ? `<span class="day s${d.step}${d.today ? ' today' : ''}" title="${escAttr(d.tip)}"></span>`
    : '<span class="day ahead"></span>')).join('');
  box.innerHTML = `<div class="days-grid" role="img" aria-label="${escAttr(t('distil.days.label', { weeks: DAYS_WEEKS }))}">${cells}</div>`
    + (model.line ? `<p class="days-line">${esc(model.line)}</p>` : '');
}

/* fetched beside the case list and drawn when it lands, unless a newer list has been asked for, and
   with Work in rounds off never asked for, the squares and their line left out (15 October) */
async function loadDays(ask) {
  if (!roundsOn(S.libConfig)) { drawDays(null); return; }
  let data = null;
  try { data = await api('/api/days'); } catch (err) { data = null; }
  if (ask !== libraryAsk) return;
  drawDays(data);
}

/* A row's marks, after the case and its sheets: " · Statements complete", " · PETs complete" or,
   with both, " · Case complete", each with when it was marked in its tooltip, and nothing for a case
   with neither. */
function caseMarks(item) {
  const es = item.complete ? t('distil.files.es_marked', { day: dayOf(item.complete) }) : '';
  const done = item.pets_complete && item.pets_complete.at ? item.pets_complete : null;
  const pets = !done ? '' : done.name ? t('distil.files.pets_marked_on', { day: dayOf(done.at), board: done.name })
    : t('distil.files.pets_marked', { day: dayOf(done.at) });
  const [word, title] = es && pets ? [t('distil.files.participant_complete'), t('distil.files.both_marked', { es, pets })]
    : es ? [t('distil.card.statements_complete'), es] : pets ? [t('distil.card.pets_complete'), pets] : ['', ''];
  return word ? ` · <span class="case-mark" title="${escAttr(title)}">${word}</span>` : '';
}

/* The card names the source by its case and its file, and asks only for the new file's name. The
   folder it goes in is the case folder, whose full name never shows on the screen, so it is added
   back here, and a name typed with a folder in it is taken as it stands. */
const fileOf = (p) => String(p || '').split(/[/\\]/).pop();

/* The source as the create and import cards name it, the case and the file, or the file alone where its name
   already holds the participant's, so "Ivy - interview.xlsx" never stands after "Ivy ·" (17 October, later) */
function sourceSaid(item) {
  const file = fileOf(item.path);
  const who = String(item.case || '').replace(/^P\d+\s*-?\s*/, '').trim();
  const named = who && new RegExp(`(^|[^A-Za-z])${who.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^A-Za-z]|$)`).test(file);
  return named ? file : [item.case, file].filter(Boolean).join(' · ');
}

function offerCreate(item, opts = {}) {
  const folder = String(item.suggested || '').replace(/[^/\\]*$/, '');
  $('create-from').textContent = sourceSaid(item);
  $('create-out').value = fileOf(item.suggested);
  show('create');
  $('create-go').onclick = async () => {
    const typed = $('create-out').value.trim();
    const out = !typed ? '' : (/[/\\]/.test(typed) ? typed : folder + typed);
    try {
      hide('create');
      say(t('distil.create.building'));
      const data = await api('/api/create', { path: item.path, out, ...(opts.timepoint ? { timepoint: opts.timepoint } : {}) });
      startCase(data);
    } catch (err) { say(err.message, 9000); }
  };
}

/* A transcript in another shape, a VTT or SRT file, plain text, a Word file, or a CSV or Excel file
   with other columns, in a case's Source folder. Its card reads it through /api/import: the first
   turns as the app takes them, the interviewer among the speakers, preset by the server and his to
   change, and for a Word table, a CSV or an Excel file every column with a chooser at its head,
   Speaker, Time, Transcript, Exploratory notes, Experiential statements or Leave out, guessed by the
   server and his to change, a changed one reading the file again (19 October, Adam: "let them check
   that it's correctly detected the columns"). Make writes the columns beside the file and goes on to
   the create card, so one pass ends in a case ready to open. A file with no turns in it, or two
   columns on one role, says so in one line and Make waits, and a server from before the route says
   to restart it. */
const IMPORT = { item: null, read: null, busy: false, ask: 0, audio: '', picked: [] };

/* The card also takes (20 October, Adam: work done elsewhere "marked up to any degree") each
   speaker's role, Interviewer, Participant or Other speaker, the guess first, the format of a Time
   column's times, found and his to set, and the recording, copied into the case, with an offset in
   seconds that playback adds to every time code. One transcript is always one case. */
function offerImport(item) {
  IMPORT.item = item;
  IMPORT.read = null;
  IMPORT.audio = '';
  IMPORT.picked = [];
  $('import-from').textContent = sourceSaid(item);
  $('import-map').hidden = true;
  $('import-map').innerHTML = '';
  $('import-time-row').hidden = true;
  $('import-bad').hidden = true;
  $('import-turns').innerHTML = '';
  $('import-speakers').innerHTML = '';
  $('import-who-row').hidden = true;
  $('import-as').hidden = true;
  $('import-audio-row').hidden = true;
  $('import-offset').value = '0';
  $('import-tp-row').hidden = true;
  $('import-tp').innerHTML = '';
  IMPORT.tpSet = false;
  importSaid('');
  $('import-go').disabled = true;
  show('import');
  readImport();
}

function importSaid(line) {
  $('import-said').textContent = line;
  $('import-said').hidden = !line;
}

/* what the card asks of the file as it stands: each column's role, each speaker's, how the times
   are read, the recording and its offset, the first read asking nothing so the server guesses */
function importAsks() {
  if (!IMPORT.read) return {};
  const speakers = {};
  for (const sel of $('import-speakers').querySelectorAll('select[data-speaker]')) speakers[sel.dataset.speaker] = sel.value;
  return {
    columns: importColumns(), speakers,
    times: { format: $('import-time').value, fps: $('import-fps').value },
    audio: $('import-audio').value, offset: $('import-offset').value,
    ...($('import-tp-row').hidden || !$('import-tp').value ? {} : { timepoint: Number($('import-tp').value) }),
  };
}

async function readImport() {
  const ask = ++IMPORT.ask;
  $('import-go').disabled = true;
  let data;
  try {
    data = await api('/api/import', { path: IMPORT.item.path, op: 'read', ...importAsks() });
  } catch (err) {
    if (ask === IMPORT.ask) importSaid(needsRestart(err) ? RESTART_LINE : err.message);
    return;
  }
  if (ask !== IMPORT.ask) return;
  IMPORT.read = data;
  drawImport(data);
  importFades();
}

const turnsWord = (n) => t('distil.import.passages', { n });

/* what a Word table of transcript and notes brings beside the words, and what it leaves out, in the
   server's line, on the import card and on New project's rows alike (19 October) */
const importBrings = (data) => (data && data.count && data.brings ? `<p class="fineprint import-brings">${esc(data.brings)}</p>` : '');

/* The roles a table's column can take, in the order the workbook holds them, and Leave out. Quote since 9 November
   2026 (ayabuild12): its lines pair with the statements on the same row by order. */
const IMPORT_ROLES = [['name', t('distil.import.role.speaker')], ['ts', t('distil.import.role.time')], ['text', t('distil.import.role.transcript')], ['en', t('distil.import.role.notes')], ['es', t('distil.import.role.statements')], ['kq', t('distil.import.role.quote')], ['', t('distil.import.role.leave_out')]];
const importRole = (role) => (IMPORT_ROLES.find(([r]) => r === role) || ['', ''])[1];

/* a table's columns, each its own chooser over its heading as the file gives it, on the import card
   and on New project's rows alike, `attr` the chooser's attribute for column i */
function importMapHtml(data, attr) {
  const roles = data.roles || [];
  return (data.columns || []).map((h, i) => `<label class="import-col"><select ${attr(i)}>`
    + IMPORT_ROLES.map(([r, label]) => `<option value="${r}"${(roles[i] || '') === r ? ' selected' : ''}>${label}</option>`).join('')
    + `</select><span class="import-col-head">${esc(h)}</span></label>`).join('');
}

/* The first passages as they will land. A table's in a column for each role chosen, Speaker, Time,
   Transcript, Exploratory notes, Experiential statements, the notes beside their words with their
   lines kept, in a box of their own that scrolls sideways on a phone. Any other file's as before,
   the speaker, the time and the words. */
function importPreviewHtml(data, most) {
  const turns = (data.turns || []).slice(0, most);
  if (!data.columns) {
    return turns.map((t) => `<div class="import-turn"><span class="import-name">${esc(t.name)}</span>`
      + `<span class="import-time">${esc(t.time)}</span><span class="import-text">${esc(t.text)}</span></div>`).join('');
  }
  if (!turns.length) return '';
  const shown = data.shown || ['name', 'ts', 'text'];
  const cell = (t, r) => (r === 'name' ? t.name : r === 'ts' ? t.time : r === 'text' ? t.text : t[r] || '');
  // on a phone the columns stack (20 October), each notes and statements cell under its heading
  const head = (r) => (r === 'en' || r === 'es' || r === 'kq' ? ` data-head="${escAttr(importRole(r))}"` : '');
  // a time the format cannot read stands as written, struck through, so it is never silently dropped
  const td = (turn, r) => (r === 'ts' && turn.bad
    ? `<td class="ip-ts"><s class="import-unread" title="${escAttr(t('distil.import.unread_title'))}">${esc(turn.bad)}</s></td>`
    : `<td class="ip-${r}"${head(r)}>${esc(cell(turn, r))}</td>`);
  // the Time column as wide as its longest time, so a time is never broken across two lines
  const longest = Math.max(4, ...turns.map((t) => String(t.bad || t.time || '').length));
  const width = (r) => (r === 'ts' ? ` style="width: calc(${longest}ch + 14px)"` : '');
  return `<div class="import-fade"><div class="import-preview"><table class="import-table n${shown.length}"><thead><tr>`
    + shown.map((r) => `<th class="ip-${r}"${width(r)}>${importRole(r)}</th>`).join('') + '</tr></thead><tbody>'
    + turns.map((t) => '<tr>' + shown.map((r) => td(t, r)).join('') + '</tr>').join('')
    + '</tbody></table></div></div>';
}

/* the fade at each edge of a preview with more columns beyond it, set again as it scrolls */
function importFade(box) {
  const more = box.scrollWidth - box.clientWidth;
  box.parentElement.classList.toggle('more-left', box.scrollLeft > 1);
  box.parentElement.classList.toggle('more-right', box.scrollLeft < more - 1);
}

function importFades() {
  for (const box of document.querySelectorAll('.import-fade > .import-preview')) importFade(box);
}

const SPEAKER_ROLES = [['interviewer', t('distil.import.speaker.interviewer')], ['participant', t('distil.import.speaker.participant')], ['other', t('distil.import.speaker.other')]];

/* each speaker with their passages and a chooser of their role, the import card's and New project's
   rows alike (20 October), `attr` any further attribute of a speaker's chooser */
function speakerChoosersHtml(speakers, roles, attr) {
  return speakers.map((sp) => `<label class="setting import-speaker">`
    + `<span class="setting-label">${esc(sp.name)}<span class="import-speaker-n">, ${turnsWord(sp.turns)}</span></span>`
    + `<select data-speaker="${escAttr(sp.name)}"${attr(sp)}>`
    + SPEAKER_ROLES.map(([r, label]) => `<option value="${r}"${(roles[sp.name] || 'participant') === r ? ' selected' : ''}>${label}</option>`).join('')
    + '</select></label>').join('');
}

function drawImport(data) {
  // a table's columns, each with its chooser, the role the server guessed or he chose preselected
  const map = !!(data.columns && data.roles);
  $('import-map').hidden = !map;
  $('import-map').innerHTML = map ? importMapHtml(data, (i) => `data-col="${i}" aria-label="${escAttr(data.columns[i])}"`) : '';
  drawImportTime(data);
  const turns = data.turns || [];
  $('import-turns').className = data.columns ? 'import-turns is-table' : 'import-turns';
  $('import-turns').innerHTML = importPreviewHtml(data, turns.length)
    + (data.count ? `<p class="fineprint import-count">${data.count > turns.length ? t('distil.import.shown_of', { shown: turns.length, n: data.count }) : turnsWord(data.count)}</p>` : '')
    + importBrings(data);
  // every speaker in the order they first speak, each with a chooser, the server's guess first
  const speakers = data.speakers || [];
  $('import-speakers').innerHTML = speakerChoosersHtml(speakers, data.speaker_roles || {}, () => '');
  $('import-who-row').hidden = !speakers.length;
  drawImportAs();
  drawImportAudio(data);
  importSaid(data.said || '');
  $('import-go').disabled = !!data.said || !data.count;
  if (typeof drawImportTp === 'function') drawImportTp(data);
}

/* The Timepoint chooser, in a project of two or more (20 October): the project's timepoints, the first
   the participant has no interview at chosen once, as the card opens, and the file read again for it.
   With a workbook already, the line under it says the sheet it adds there. One transcript is always one
   participant's. A project of one, and a server from before, show no chooser. */
function drawImportTp(data) {
  const tps = Array.isArray(data.timepoints) ? data.timepoints : [];
  $('import-tp-row').hidden = tps.length < 2;
  if (tps.length < 2) return;
  const chosen = Number(data.timepoint) || 1;
  $('import-tp').innerHTML = tps.map((t) => `<option value="${t.n}"${t.n === chosen ? ' selected' : ''}>`
    + `${esc([t.label, t.description].filter(Boolean).join(' '))}</option>`).join('');
  const joins = fileOf(data.joins || '');
  $('import-tp-joins').textContent = joins ? t('distil.import.joins', { file: joins, sheet: data.sheet }) : '';
  $('import-tp-joins').hidden = !joins;
  if (!IMPORT.tpSet) {
    IMPORT.tpSet = true;
    const open = tps.find((t) => !t.held);
    if (open && open.n !== chosen) {
      $('import-tp').value = String(open.n);
      readImport();
    }
  }
}

/* the format a Time column's times were found in, beside a chooser to set it by hand, the frame rate
   when they count frames, and a line naming each time that cannot be read */
function drawImportTime(data) {
  const timed = !!(data.columns && data.mapping && data.mapping.ts !== null && data.mapping.ts !== undefined);
  $('import-time-row').hidden = !timed;
  const chosen = (data.timing && data.timing.format) || '';
  const found = data.time_found_name;
  $('import-time').innerHTML = `<option value="">${esc(found ? t('distil.import.as_found_named', { format: found }) : t('distil.import.as_found'))}</option>`
    + (data.time_formats || []).map(([k, label]) => `<option value="${k}"${k === chosen ? ' selected' : ''}>${esc(label)}</option>`).join('');
  $('import-time').value = chosen;
  const frames = chosen === 'frames' || (!chosen && data.time_found === 'frames');
  $('import-fps-row').hidden = !timed || !frames;
  if (data.timing && document.activeElement !== $('import-fps')) $('import-fps').value = data.timing.fps;
  const bad = timed ? (data.bad_times || []) : [];
  const as = chosen ? (data.time_formats || []).find(([k]) => k === chosen)[1] : found;
  // a time is one piece, never broken across two lines (20 October)
  const whole = (text) => `<span class="nowrap">${esc(text)}</span>`;
  const where = (b) => t('distil.import.bad_where_html', { time: whole(b.time), passage: esc(b.passage) });
  // the format by its example, "1:02:03:12 frames" in the sentence, where the chooser has a comma
  const read = as ? whole(as.replace(', ', ' ')) : '';
  const list = bad.slice(0, 4).map(where).join(', ');
  const listed = bad.length > 4 ? t('distil.import.bad_more_html', { list, more: bad.length - 4 }) : list;
  $('import-bad').innerHTML = !bad.length ? ''
    : bad.length === 1 ? t(read ? 'distil.import.bad_one_as_html' : 'distil.import.bad_one_html', { where: where(bad[0]), as: read })
      : t(read ? 'distil.import.bad_many_as_html' : 'distil.import.bad_many_html', { n: bad.length, as: read, list: listed });
  $('import-bad').hidden = !bad.length;
}

/* the recordings beside the file and in the case's Source folder, any chosen with Choose, and None,
   the offset beside them once one is chosen */
function drawImportAudio(data) {
  const found = (data.audio_found || []).concat(IMPORT.picked.filter((p) => !(data.audio_found || []).some((f) => f.path === p.path)));
  const was = data.audio || IMPORT.audio || '';
  $('import-audio').innerHTML = `<option value="">${esc(t('distil.import.no_audio'))}</option>`
    + found.map((f) => `<option value="${escAttr(f.path)}">${esc(f.name)}</option>`).join('');
  $('import-audio').value = found.some((f) => f.path === was) ? was : '';
  $('import-audio-row').hidden = false;
  $('import-audio-pick').hidden = !S.chooseRoot;
  $('import-offset-row').hidden = !$('import-audio').value;
}

/* the line under the speakers when the interviewer's turns go into the workbook under another name,
   the one Settings gives, so the app reads them as context */
const importInterviewer = () => {
  const sel = Array.from($('import-speakers').querySelectorAll('select[data-speaker]')).find((x) => x.value === 'interviewer');
  return sel ? sel.dataset.speaker : '';
};

function drawImportAs() {
  const to = IMPORT.read && IMPORT.read.as ? IMPORT.read.as[importInterviewer()] : null;
  $('import-as').textContent = to ? t('distil.import.written_as', { name: to }) : '';
  $('import-as').hidden = !to;
}

/* Choose for a recording elsewhere on the computer: the window's own picker, or the Mac's file
   dialog through the server */
async function pickImportAudio() {
  const got = await picking((chosen) => (chosen ? Promise.resolve({ chosen: true, path: chosen })
    : api('/api/import', { path: IMPORT.item.path, op: 'pick-audio' })), $('import-audio-pick'), PICK_SAYS.audio, true)
    .catch((err) => { importSaid(err.message); return { chosen: false }; });
  if (!got || !got.chosen || !got.path) return;
  const name = fileOf(got.path);
  if (!IMPORT.picked.some((p) => p.path === got.path)) IMPORT.picked.push({ path: got.path, name });
  IMPORT.audio = got.path;
  const opt = document.createElement('option');
  opt.value = got.path;
  opt.textContent = name;
  if (!Array.from($('import-audio').options).some((o) => o.value === got.path)) $('import-audio').appendChild(opt);
  $('import-audio').value = got.path;
  readImport();
}

/* the role chosen for each column, in the file's order, "" for one left out */
const importColumns = () => (IMPORT.read && IMPORT.read.columns
  ? Array.from($('import-map').querySelectorAll('select[data-col]'), (s) => s.value) : undefined);

async function makeImport() {
  if (IMPORT.busy || !IMPORT.read || IMPORT.read.said || !IMPORT.read.count) return;
  IMPORT.busy = true;
  $('import-go').disabled = true;
  try {
    const data = await api('/api/import', {
      path: IMPORT.item.path, op: 'make', ...importAsks(), interviewer: importInterviewer(),
    });
    hide('import');
    // a later interview of a participant with a workbook joined it, and the case opens at its timepoint
    if (data.joined) { openCaseIn(data.joined, { timepoint: data.timepoint }); return; }
    // the list behind the cards shows the raw source in place of the file, should the next be cancelled
    loadLibrary().catch(() => {});
    offerCreate(data.source, data.timepoint > 1 ? { timepoint: data.timepoint } : {});
  } catch (err) {
    importSaid(needsRestart(err) ? RESTART_LINE : err.message);
  } finally {
    IMPORT.busy = false;
    $('import-go').disabled = !$('import-said').hidden;
  }
}

/* New project (item 204): a folder he picks, which Idiograph then manages, its name and research
   question, and the transcripts dropped onto the card or chosen with Choose files. The page reads
   each file and sends its contents, since a drop gives no path, and the server keeps a copy in the
   new case's folder, the original never touched. Each file is a row: its turns as the import card
   reads them, the interviewer among the speakers, the participant's number, preset in order from
   the folder's next free number, the pseudonym, typed and never filled from a speaker's label or a
   file's name, either of which may carry a real name, and the interview's name, guessed from the
   file's name or Interview. Each case's folder is `P<n> - Pseudonym`. Files under one pseudonym are
   one case of several interviews, and a number typed on one of its rows is the case's. Create
   project has the server check every row and say in one line what to fix, and then the project's
   page opens. Add transcripts opens the same card for a project that stands, `NP.add`, its id, its
   name and its cases by pseudonym, and is null for New project. */
const NP = { folder: '', next: 1, rows: [], busy: false, key: 0, add: null, qdpx: null };
const NP_MAX = 25 * 1024 * 1024;
const NP_PREVIEW = 3;
const NP_CROSS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"'
  + ' aria-hidden="true" focusable="false"><path d="M5 5l14 14M19 5L5 19"/></svg>';

function openNewProject() {
  Object.assign(NP, { folder: '', next: 1, rows: [], busy: false, add: null, tps: [], held: new Map(), qdpx: null, names: null });
  npMode(null);
  $('np-folder').value = '';
  $('np-name').value = '';
  $('np-question').value = '';
  npMethodSet('ipa', false);
  $('np-choose').hidden = !S.chooseRoot;
  $('np-go').disabled = false;
  npSaid('');
  drawNpRows();
  show('newproject');
  (S.chooseRoot ? $('np-choose') : $('np-folder')).focus();
}

/* Cancel, and the way out after Make: the files' contents go with the card */
function closeNewProject() {
  hide('newproject');
  NP.rows = [];
  $('np-rows').innerHTML = '';
  if (NP.qdpx) clearTimeout(NP.qdpx.timer);
  NP.qdpx = null;
  drawQd();
}

/* The card as New project, or as Add transcripts: the project's name in the kicker, and the folder,
   the name and the question hidden, since the project has them already. */
function npMode(add) {
  const card = $('newproject');
  card.querySelector('.kicker').textContent = add ? add.name || t('distil.home.project') : t('distil.home.project');
  card.querySelector('h2').textContent = add ? t('distil.np.add_title') : t('distil.np.new_title');
  for (const el of card.querySelectorAll('.np-new')) el.hidden = !!add;
  $('np-go').textContent = add ? t('distil.np.add') : t('distil.np.create');
  drawQd();
}

/* Add transcripts, from a project's page: the server answers its name, its next free number and its
   cases, each by label and pseudonym, and the card opens on the drop place with no rows. A server
   from before it says to restart. */
async function openAddTranscripts(id) {
  let data;
  try {
    data = await api('/api/add-transcripts', { op: 'project', root: id });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  Object.assign(NP, { folder: '', next: Number(data.next) || 1, rows: [], busy: false, qdpx: null, names: null,
    add: { id, name: String(data.name || ''), cases: new Map((data.cases || []).map((c) => [String(c.pseudonym), String(c.label)])) },
    // the project's timepoints with two or more, and the ones each case has an interview at (20 October)
    tps: Array.isArray(data.timepoints) ? data.timepoints : [],
    held: new Map((data.cases || []).map((c) => [String(c.pseudonym), Array.isArray(c.held) ? c.held : []])) });
  npMode(NP.add);
  $('np-go').disabled = false;
  npSaid('');
  drawNpRows();
  show('newproject');
  $('np-pick').focus();
}

/* In Add, a row under the pseudonym of a case there says which case it joins, by its label as its
   row on the project's page names it, and its number stands hidden, since the case has one. */
function npJoinsDraw() {
  for (const li of $('np-rows').querySelectorAll('.np-row')) {
    const row = npRow(li);
    const line = li.querySelector('.np-joins');
    if (!row || !line) continue;
    const label = NP.add ? NP.add.cases.get(row.pseudonym.trim()) || '' : '';
    line.textContent = label ? t('distil.np.joins', { name: label.replace(/^(P\d+)\s*-\s*/, '$1 ') }) : '';
    line.hidden = !label;
    const input = li.querySelector('[data-np="number"]');
    if (input) input.closest('.np-field').hidden = !!label;
  }
}

function npSaid(line) {
  $('np-said').textContent = line;
  $('np-said').hidden = !line;
}

/* The project's method on New project's card (tadraw, 31 October 2026): IPA, ticked as the card opens, or
   Thematic analysis, sent with Create project and fixed once the project is made. A folder whose project file
   names one already shows it ticked and fixed. */
function npMethod() {
  const on = $('np-method').querySelector('.th-from-opt.on');
  return on ? on.dataset.method : 'ipa';
}

function npMethodSet(method, fixed) {
  for (const b of $('np-method').querySelectorAll('[data-method]')) {
    const on = b.dataset.method === method;
    b.classList.toggle('on', on);
    b.setAttribute('aria-checked', String(on));
    b.disabled = !!fixed;
  }
}

/* The folder, from the Mac's dialog with no path or typed, checked by the server as Add project
   checks one. It answers the folder's next free number and the name and question a project file
   there already gives, which fill the fields only while they are empty. */
async function npFolder(path) {
  let data;
  try {
    data = path ? await api('/api/new-project', { op: 'folder', path })
      : await picking((chosen) => api('/api/new-project', { op: 'folder', path: chosen }), $('np-choose'), PICK_SAYS.newProject);
  } catch (err) { npSaid(needsRestart(err) ? RESTART_LINE : err.message); return false; }
  if (!data.chosen) return false;
  npSaid('');
  NP.folder = data.folder;
  NP.next = Number(data.next) || 1;
  // a folder whose project file sets two or more timepoints gives each row a Timepoint chooser
  const had = (NP.tps || []).length;
  NP.tps = Array.isArray(data.timepoints) ? data.timepoints : [];
  NP.held = new Map();
  if (had !== NP.tps.length) drawNpRows();
  $('np-folder').value = data.folder;
  if (!$('np-name').value.trim()) $('np-name').value = data.name || '';
  if (!$('np-question').value.trim()) $('np-question').value = data.research_question || '';
  // a folder whose project file is there already keeps its method (tadraw)
  npMethodSet(data.method || npMethod(), !!data.method);
  npNumbersDraw();
  // a project from ATLAS.ti, NVivo or MAXQDA read again for the folder's timepoints and participants
  if (NP.qdpx) qdRead();
  // a folder with a project there already brings its list of names (namesui)
  else nmSoon();
  return true;
}

function npBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',', 2)[1] || '');
    reader.onerror = () => reject(new Error('unread'));
    reader.readAsDataURL(file);
  });
}

/* the files dropped or chosen, a row each at once, then read one after another */
async function npAdd(files) {
  const list = Array.from(files || []);
  // a project from ATLAS.ti, NVivo or MAXQDA comes in on its own (21 October)
  if (NP.qdpx || list.some((f) => isQdpx(f.name))) {
    if (NP.qdpx || NP.rows.length || list.length > 1) npSaid(QD_ALONE);
    else await qdAdd(list[0]);
    return;
  }
  const added = [];
  for (const file of list) {
    const row = { key: ++NP.key, file: file.name, data: null, read: null, said: '', pseudonym: '', real: '', skips: new Set(),
      interview: '', roles: {}, columns: undefined, number: '' };
    NP.rows.push(row);
    added.push([row, file]);
  }
  drawNpRows();
  for (const [row, file] of added) {
    if (file.size > NP_MAX) { row.said = t('distil.np.too_large', { file: file.name }); drawNpRow(row); continue; }
    try {
      row.data = await npBase64(file);
    } catch {
      row.said = t('distil.np.unreadable', { file: file.name });
      drawNpRow(row);
      continue;
    }
    await npRead(row);
  }
}

/* a row's file read by the server, with the columns chosen for a table */
async function npRead(row, columns, speakers) {
  let data;
  try {
    data = await api('/api/new-project', { op: 'read', name: row.file, data: row.data, columns, speakers, ...(row.sheet ? { sheet: row.sheet } : {}) });
  } catch (err) {
    row.said = needsRestart(err) ? RESTART_LINE : err.message;
    drawNpRow(row);
    return;
  }
  if (!NP.rows.includes(row)) return;
  row.read = data;
  // an Excel file's sheets, kept from its first read so the chooser stays when a sheet will not read
  if (data.sheets && data.sheets.length) row.sheets = data.sheets;
  row.columns = data.columns ? columns : undefined;
  // each speaker's role, the server's guess or his choice, as the import card has them (20 October)
  row.roles = { ...(data.speaker_roles || {}) };
  if (!row.interview) row.interview = data.interview || t('distil.np.interview');
  row.said = data.said || '';
  drawNpRow(row);
}

function npRowHtml(row) {
  const r = row.read;
  const opt = (value, label, on) => `<option value="${escAttr(value)}"${on ? ' selected' : ''}>${esc(label)}</option>`;
  let html = `<div class="np-row-head"><span class="np-file">${esc(row.file)}</span>`
    + (r && r.count ? `<span class="np-count">${turnsWord(r.count)}</span>` : '')
    + `<button type="button" class="np-remove" data-np="remove" aria-label="${escAttr(t('distil.np.remove_file', { file: row.file }))}" title="${escAttr(t('distil.np.remove'))}">${NP_CROSS}</button></div>`;
  if (row.said) html += `<p class="warn np-row-said">${esc(row.said)}</p>`;
  // an Excel file of two sheets or more: the sheet read, its first with anything in it until he picks another
  const sheets = row.sheets || [];
  if (sheets.length > 1) {
    const on = row.sheet || (r && r.sheet) || '';
    html += `<div class="np-fields np-sheet-row"><label class="import-col np-sheet"><select data-np="sheet">`
      + sheets.map((s) => opt(s, s, s === on)).join('') + `</select><span class="import-col-head">${esc(t('distil.np.sheet'))}</span></label></div>`;
  }
  if (r && r.columns && r.roles) {
    html += `<div class="import-map np-map" role="group" aria-label="${escAttr(t('distil.np.columns'))}">`
      + importMapHtml(r, (i) => `data-np="col-${i}" aria-label="${escAttr(r.columns[i])}"`) + '</div>';
  }
  if (r && r.turns && r.turns.length) {
    html += `<div class="import-turns np-turns${r.columns ? ' is-table' : ''}">${importPreviewHtml(r, NP_PREVIEW)}</div>`;
  }
  html += importBrings(r);
  if (!r || !r.count) return html;
  if ((r.speakers || []).length) {
    html += `<div class="import-who np-who" role="group" aria-label="${escAttr(t('distil.np.speakers'))}"><p class="import-sub">${esc(t('distil.np.speakers'))}</p>`
      + speakerChoosersHtml(r.speakers, row.roles, (sp) => ` data-np="speaker-${escAttr(sp.name)}"`) + '</div>';
  }
  const field = (name, label, value, more = '') => `<label class="np-field${more}"><span>${label}</span><input data-np="${name}"`
    + ` type="text" spellcheck="false" autocomplete="off"${name === 'pseudonym' ? ' list="np-names"' : ''}`
    + `${name === 'number' ? ` inputmode="numeric" aria-label="${escAttr(t('distil.np.number'))}"` : ''} value="${escAttr(value)}"></label>`;
  // in a project of two or more timepoints, the one this interview was at (20 October)
  const tps = NP.tps || [];
  const tpField = tps.length >= 2
    ? `<label class="np-field np-tp"><span>${esc(t('distil.np.timepoint'))}</span><select data-np="timepoint">${tps.map((tp) => opt(String(tp.n),
      [tp.label, tp.description].filter(Boolean).join(' '), tp.n === npTimepoint(row))).join('')}</select></label>` : '';
  // the Real name beside the pseudonym makes the list's entry for this participant (namesui), and the Names line
  // under the fields says what the list replaces in this file
  return html + '<div class="np-fields">' + field('number', esc(t('distil.np.p')), row.number, ' np-num')
    + field('real', esc(t('distil.names.real')), row.real || '', ' np-real') + field('pseudonym', esc(t('distil.np.pseudonym')), row.pseudonym)
    + field('interview', esc(t('distil.np.interview')), row.interview) + tpField + '</div>'
    + '<p class="np-joins" hidden></p>' + npNamesHtml();
}

/* A row's timepoint: the one he chose, else for a participant there already the first they have no
   interview at, else T1 */
function npTimepoint(row) {
  if (row.timepoint) return row.timepoint;
  const held = (NP.held && NP.held.get(row.pseudonym.trim())) || [];
  const open = (NP.tps || []).find((t) => !held.includes(t.n));
  return held.length && open ? open.n : 1;
}

/* the rows' Timepoint choosers as their pseudonyms now stand, each he has not chosen himself */
function npTimepointsDraw() {
  for (const li of $('np-rows').querySelectorAll('.np-row')) {
    const row = npRow(li);
    const pick = li.querySelector('[data-np="timepoint"]');
    if (row && pick && !row.timepoint && pick !== document.activeElement) pick.value = String(npTimepoint(row));
  }
}

function drawNpRows() {
  $('np-rows').innerHTML = NP.rows.map((row) => `<li class="np-row" data-key="${row.key}">${npRowHtml(row)}</li>`).join('');
  importFades();
  npNumbersDraw();
  npNamesDraw();
  npJoinsDraw();
  nmDrawRows();
}

/* one row drawn again, after its read, the field he was in keeping the focus */
function drawNpRow(row) {
  const li = $('np-rows').querySelector(`[data-key="${row.key}"]`);
  if (!li) return;
  const held = document.activeElement && li.contains(document.activeElement) ? document.activeElement.dataset.np : null;
  li.innerHTML = npRowHtml(row);
  importFades();
  npNumbersDraw();
  npJoinsDraw();
  nmDrawRow(row, li);
  nmSoon();
  const back = held ? li.querySelector(`[data-np="${CSS.escape(held)}"]`) : null;
  if (back) back.focus();
}

function npRow(el) {
  const li = el && el.closest ? el.closest('.np-row') : null;
  return li ? NP.rows.find((r) => String(r.key) === li.dataset.key) || null : null;
}

/* Each case's number: the one typed on its first row that has one, and for the rest the next free
   number in the order the cases first come, from the folder's own next free number. In Add a case
   there already keeps its own, and takes none here. */
function npNumbers() {
  const out = {};
  const used = new Set();
  const there = (p) => !!(NP.add && NP.add.cases.has(p));
  for (const r of NP.rows) {
    const p = r.pseudonym.trim();
    const n = parseInt(r.number, 10);
    if (p && !(p in out) && !there(p) && n > 0) { out[p] = n; used.add(n); }
  }
  let next = NP.next;
  for (const r of NP.rows) {
    const p = r.pseudonym.trim();
    if (!p || p in out || there(p)) continue;
    while (used.has(next)) next += 1;
    out[p] = next;
    used.add(next);
  }
  return out;
}

function npNumbersDraw() {
  const numbers = npNumbers();
  for (const li of $('np-rows').querySelectorAll('.np-row')) {
    const row = npRow(li);
    const input = li.querySelector('[data-np="number"]');
    if (!row || !input || input === document.activeElement) continue;
    const p = row.pseudonym.trim();
    input.value = p && numbers[p] ? String(numbers[p]) : row.number;
  }
}

/* the pseudonyms typed so far, and in Add the project's cases' too, offered under each pseudonym
   field, so a further interview takes its case's name in a keystroke */
function npNamesDraw() {
  const names = [...new Set([...NP.rows.map((r) => r.pseudonym.trim()), ...(NP.add ? NP.add.cases.keys() : [])].filter(Boolean))];
  $('np-names').innerHTML = names.map((n) => `<option value="${escAttr(n)}"></option>`).join('');
}

function npFieldSet(row, name, value) {
  const li = $('np-rows').querySelector(`[data-key="${row.key}"]`);
  const input = li ? li.querySelector(`[data-np="${name}"]`) : null;
  if (input && input !== document.activeElement) input.value = value;
}

function npInput(e) {
  const name = e.target && e.target.dataset ? e.target.dataset.np : null;
  const row = npRow(e.target);
  if (!row || !name) return;
  const value = e.target.value;
  if (name === 'pseudonym') {
    row.pseudonym = value;
    const p = value.trim();
    const mate = p ? NP.rows.find((r) => r !== row && r.pseudonym.trim() === p) : null;
    if (mate) row.number = mate.number;
    npNumbersDraw();
    npNamesDraw();
    npJoinsDraw();
    npTimepointsDraw();
  } else if (name === 'number') {
    const p = row.pseudonym.trim();
    for (const r of NP.rows) {
      if (r !== row && !(p && r.pseudonym.trim() === p)) continue;
      r.number = value;
      if (r !== row) npFieldSet(r, 'number', value);
    }
    npNumbersDraw();
  } else if (name === 'interview') {
    row.interview = value;
  } else if (name === 'real') {
    row.real = value;
  }
  // the names the list replaces read again as the pseudonym, the Real name or the interview's name changes
  if (['pseudonym', 'real', 'interview'].includes(name)) nmSoon();
}

function npChange(e) {
  const name = e.target && e.target.dataset ? e.target.dataset.np : null;
  const row = npRow(e.target);
  if (!row || !name) return;
  if (name === 'timepoint') { row.timepoint = Number(e.target.value) || 1; return; }
  // another sheet read afresh, its columns guessed again and the speakers' roles with them
  if (name === 'sheet') { row.sheet = e.target.value; row.columns = undefined; npRead(row); return; }
  const li = e.target.closest('.np-row');
  const columns = () => (row.columns !== undefined || li.querySelector('[data-np^="col-"]')
    ? Array.from(li.querySelectorAll('[data-np^="col-"]'), (s) => s.value) : undefined);
  // a speaker's role, read again so the row says at once when two are Interviewer or none Participant
  if (name.startsWith('speaker-')) {
    row.roles[e.target.dataset.speaker] = e.target.value;
    npRead(row, columns(), row.roles);
    return;
  }
  if (!/^col-\d+$/.test(name)) return;
  // the role chosen for each of the row's columns, in the file's order, the file read again, the
  // speakers' roles he chose kept
  npRead(row, columns(), row.roles);
}

function npClick(e) {
  // a row's Names line: Review its finds, or the project's list (namesui)
  const names = e.target && e.target.closest ? e.target.closest('[data-np="names-review"], [data-np="names-list"]') : null;
  if (names) {
    const row = npRow(names);
    if (row && names.dataset.np === 'names-review') nmReviewRow(row);
    else if (NP.add) nmListOpen(NP.add.id, NP.add.name);
    return;
  }
  const button = e.target && e.target.closest ? e.target.closest('[data-np="remove"]') : null;
  const row = button ? npRow(button) : null;
  if (!row) return;
  NP.rows = NP.rows.filter((r) => r !== row);
  button.closest('.np-row').remove();
  npNumbersDraw();
  npNamesDraw();
  nmSoon();
  $('np-pick').focus();
}

/* Create project, or in Add, Add: every row sent to the server, which checks them all before it
   writes anything. A row that joins a case there sends no number. A project made opens on its page. */
async function npMake() {
  if (NP.busy) return;
  if (NP.qdpx) { await qdMake(); return; }
  const add = NP.add;
  const typed = add ? '' : $('np-folder').value.trim();
  if (typed && typed !== NP.folder && !(await npFolder(typed))) return;
  const held = NP.rows.find((r) => r.data === null && r.said);
  if (held) { npSaid(held.said); return; }
  const files = npFilesSent();
  NP.busy = true;
  $('np-go').disabled = true;
  try {
    // the names as the rows now stand, so each find he unticked is sent by its number as the Add will count it
    await nmPreview();
    const skip = nmSkipsSent();
    if (add) await api('/api/add-transcripts', { op: 'add', root: add.id, files, skip });
    else {
      const made = await api('/api/new-project', { op: 'make', folder: typed, name: $('np-name').value.trim(),
        research_question: $('np-question').value.trim(), method: npMethod(), files, skip });
      if (made && made.project && made.project.id) homeKeep(made.project.id);
    }
    closeNewProject();
    loadLibrary().catch((err) => say(err.message, 9000));
  } catch (err) {
    npSaid(needsRestart(err) ? RESTART_LINE : err.message);
  } finally {
    NP.busy = false;
    $('np-go').disabled = false;
  }
}

/* Names replaced as a transcript comes in (namesui, 8 November 2026, Adam's picks that evening, drawings 01 to 04
   of pseudodraw). On Add transcripts and New project each row has a Real name beside its Pseudonym, which makes an
   entry of the project's list for that participant, and the server runs every row through the list as the Add will
   (`/api/names` op preview): the preview draws each replacement tinted, the name it replaced as its tooltip, and the
   row's Names line says how many were replaced and left, with Review, a card of every find with its tick, and Names
   to replace, the project's list. A find unticked is left as written, sent with the Add as its entry and its place
   among that entry's finds. The list is the project's file in its folder, `idiograph-names.json`, never in a copy
   he shares. From the list's card, Check transcripts already in finds its names in the transcripts there, and
   Review and replace replaces the ones ticked, each workbook kept as it was in its participant's _Archive first. */
const NM = { timer: 0, ask: 0, review: null, list: null };
const NM_INITIALS = /^(?:[A-Z]\.\s?){2,4}$|^[A-Z]{2,4}$/;
const NM_MOST = 240;

/* a run of segments, plain words and finds, drawn as the card draws them: a replacement tinted with the name it
   replaced as its tooltip, a find left as written underlined, cut at `most` characters at a word's end */
function nmSegHtml(segs, most = NM_MOST) {
  let html = '';
  let used = 0;
  for (const s of segs || []) {
    if (used >= most) { html += '…'; break; }
    if (typeof s === 'string') {
      let text = s;
      if (used + text.length > most) {
        const cut = text.slice(0, most - used + 1);
        const space = Math.max(cut.lastIndexOf(' '), cut.lastIndexOf('\n'));
        text = (space > 0 ? cut.slice(0, space) : cut.slice(0, most - used)).replace(/[ ,;:\n]+$/, '') + '…';
        html += esc(text);
        break;
      }
      html += esc(text);
      used += text.length;
    } else if (s.kept) {
      html += `<span class="nm-kept" title="${escAttr(t('distil.names.left_title'))}">${esc(s.was)}</span>`;
      used += s.was.length;
    } else {
      html += `<span class="nm-swap" title="${escAttr(s.was)}">${esc(s.to)}</span>`;
      used += s.to.length;
    }
  }
  return html;
}

/* the rows as the server reads them for the preview and the Add alike, each with its Real name */
function npFilesSent() {
  const add = NP.add;
  const numbers = npNumbers();
  return NP.rows.map((r) => {
    const p = r.pseudonym.trim();
    const joins = !!(add && add.cases.has(p));
    return { name: r.file, data: r.data || '', columns: r.columns, speakers: r.roles, pseudonym: p, ...(r.sheet ? { sheet: r.sheet } : {}),
      interview: r.interview.trim(), number: joins ? null : numbers[p] || null, real: (r.real || '').trim(),
      ...((NP.tps || []).length >= 2 ? { timepoint: npTimepoint(r) } : {}) };
  });
}

/* the preview asked again a moment after the last change, the rows' names drawn when it answers */
function nmSoon() {
  clearTimeout(NM.timer);
  NM.timer = setTimeout(() => { nmPreview().catch(() => {}); }, 350);
}

async function nmPreview() {
  clearTimeout(NM.timer);
  const ask = ++NM.ask;
  if (NP.qdpx || !NP.rows.some((r) => r.data && r.read && r.read.count)) {
    NP.names = null;
    nmDrawRows();
    return null;
  }
  let data;
  try {
    data = await api('/api/names', { op: 'preview', ...(NP.add ? { root: NP.add.id } : { folder: NP.folder }), files: npFilesSent() });
  } catch { return null; }
  if (ask !== NM.ask) return null;
  NP.names = data;
  nmDrawRows();
  return data;
}

/* a find's place in its file, which a tick keeps across previews as the list and the rows change */
function nmFindKey(f, k) {
  const w = f.where || {};
  return `${w.part || ''}|${w.turn || ''}|${f.found}|${k}`;
}

/* each find of a file with its key, the k-th of the same words in the same place */
function nmKeyed(finds) {
  const seen = new Map();
  return (finds || []).map((f) => {
    const base = nmFindKey(f, 0);
    const k = seen.get(base) || 0;
    seen.set(base, k + 1);
    return { f, key: nmFindKey(f, k) };
  });
}

/* a row's finds as the server numbered them, each marked left when he unticked it */
function nmRowFinds(row) {
  const at = NP.rows.indexOf(row);
  const file = NP.names && NP.names.files ? NP.names.files[at] : null;
  if (!file) return [];
  row.skips = row.skips || new Set();
  return nmKeyed(file.finds).map(({ f, key }) => ({ ...f, key, skipped: row.skips.has(key) }));
}

/* the skips the Add sends, each find unticked by its entry and its place among that entry's finds */
function nmSkipsSent() {
  const out = [];
  for (const row of NP.rows) for (const f of nmRowFinds(row)) if (f.skipped) out.push(`${f.entry}:${f.nth}`);
  return out;
}

/* each row's preview, its speakers and its Names line as the list leaves them */
function nmDrawRows() {
  for (const li of $('np-rows').querySelectorAll('.np-row')) {
    const row = npRow(li);
    if (row) nmDrawRow(row, li);
  }
}

function nmDrawRow(row, li) {
  const at = NP.rows.indexOf(row);
  const file = NP.names && NP.names.files ? NP.names.files[at] : null;
  const finds = nmRowFinds(row);
  const skipped = new Set(finds.filter((f) => f.skipped).map((f) => `${(f.where || {}).part}|${(f.where || {}).turn}|${f.at}`));
  // the first passages drawn again from the server's segments, a find he unticked drawn as written
  const turns = li.querySelectorAll('.np-turns .import-turn');
  const shown = file ? file.turns || [] : [];
  const mark = (segs, part, turn) => {
    let pos = 0;
    return (segs || []).map((s) => {
      if (typeof s === 'string') { pos += s.length; return s; }
      const kept = skipped.has(`${part}|${turn}|${pos}`);
      pos += s.was.length;
      return { ...s, kept };
    });
  };
  // each speaker by what their name becomes, in the preview's passages and under Speakers
  const spoken = new Map((file ? file.speakers || [] : []).map((sp) => [sp.name, nmSegHtml(mark(sp.segments, 'speaker', sp.turn), 200)]));
  const turnsRead = (row.read && row.read.turns) || [];
  turns.forEach((el, i) => {
    const seg = shown[i];
    const name = el.querySelector('.import-name');
    const text = el.querySelector('.import-text');
    if (name && turnsRead[i] && spoken.has(turnsRead[i].name)) name.innerHTML = spoken.get(turnsRead[i].name);
    if (seg && text) text.innerHTML = nmSegHtml(mark(seg.text, 'words', i + 1));
  });
  // a table's preview: its speaker and transcript cells
  li.querySelectorAll('.np-turns .import-table tbody tr').forEach((tr, i) => {
    const seg = shown[i];
    const name = tr.querySelector('.ip-name');
    const text = tr.querySelector('.ip-text');
    if (name && turnsRead[i] && spoken.has(turnsRead[i].name)) name.innerHTML = spoken.get(turnsRead[i].name);
    if (seg && text) text.innerHTML = nmSegHtml(mark(seg.text, 'words', i + 1));
  });
  for (const label of li.querySelectorAll('.import-speaker > .setting-label')) {
    const sp = label.parentElement.querySelector('select[data-speaker]');
    let head = label.querySelector('.nm-speaker');
    if (!head) {
      head = document.createElement('span');
      head.className = 'nm-speaker';
      if (label.firstChild && label.firstChild.nodeType === 3) label.firstChild.replaceWith(head);
      else label.prepend(head);
    }
    const was = sp ? sp.dataset.speaker : '';
    head.innerHTML = spoken.has(was) ? spoken.get(was) : esc(was);
  }
  // the Names line under the row's fields
  const line = li.querySelector('.np-names');
  if (!line) return;
  const any = NP.names && NP.names.entries > 0;
  line.hidden = !any || !row.read || !row.read.count;
  if (line.hidden) return;
  const left = finds.filter((f) => f.skipped).length;
  const replaced = finds.length - left;
  line.querySelector('.np-names-said').textContent = !finds.length ? t('distil.names.none_here')
    : left ? t('distil.names.line_left', { replaced, left }) : t('distil.names.line', { replaced });
  line.querySelector('[data-np="names-review"]').hidden = !finds.length;
  line.querySelector('[data-np="names-list"]').hidden = !NP.add;
}

/* the row's part of the card: its Names line, under the fields */
function npNamesHtml() {
  return `<div class="np-names" hidden><p class="import-sub">${esc(t('distil.names.head'))}</p><div class="np-names-line">`
    + '<span class="np-names-said"></span>'
    + `<button type="button" class="ghost small" data-np="names-review">${esc(t('distil.names.review'))}</button>`
    + `<button type="button" class="ghost small" data-np="names-list">${esc(t('distil.names.open'))}</button></div></div>`;
}

/* ── Review: every find by its entry, a tick each ── */

/* a find's place as its row says it: the passage, a speaker, the file's name or the interview's, and on the
   list's card the participant first */
const NM_AT = { words: 'distil.names.at.words', notes: 'distil.names.at.notes', statements: 'distil.names.at.statements',
  quotes: 'distil.names.at.quotes', speaker: 'distil.names.at.speaker', file: 'distil.names.at.file', interview: 'distil.names.at.interview' };
const NM_WHO = { words: 'distil.names.who.words', notes: 'distil.names.who.notes', statements: 'distil.names.who.statements',
  quotes: 'distil.names.who.quotes', speaker: 'distil.names.who.speaker', file: 'distil.names.who.file', interview: 'distil.names.who.interview' };
const NM_PARTS = { notes: 'distil.names.part.notes', statements: 'distil.names.part.statements', quotes: 'distil.names.part.quotes' };

function nmWhere(f, who) {
  const w = f.where || {};
  const part = NM_AT[w.part] ? w.part : 'words';
  return who ? t(NM_WHO[part], { who: w.participant || '', n: w.turn || '' }) : t(NM_AT[part], { n: w.turn || '' });
}

function nmContext(f) {
  if ((f.where || {}).part === 'speaker' && f.speaks) {
    return `<b>${esc(f.found)}</b>${esc(t('distil.names.speaks', { n: f.speaks }))}`;
  }
  const before = String(f.before || '');
  const after = String(f.after || '');
  const b = before.length > 30 ? '…' + before.slice(-30) : before;
  const a = after.length > 34 ? after.slice(0, 34) + '…' : after;
  return `${esc(b)}<b>${esc(f.found)}</b>${esc(a)}`;
}

/* The card: `finds`, each with its `key` and `skipped`, grouped under its entry of `list`, a speaker's name one
   row however many passages or sheets it heads. `who` names each row's participant. `onTick(keys, on)` keeps a
   tick. `actions` is the card's foot. */
function nmReviewOpen({ kicker, title, finds, list, who, onTick, actions }) {
  const card = $('nm-review');
  NM.review = { finds, onTick };
  card.querySelector('.kicker').textContent = kicker || '';
  card.querySelector('h2').textContent = title;
  const groups = new Map();
  for (const f of finds) {
    if (!groups.has(f.entry)) groups.set(f.entry, []);
    const rows = groups.get(f.entry);
    const w = f.where || {};
    if (w.part === 'speaker') {
      const had = rows.find((r) => r.speaker && r.speaker === `${w.participant}|${f.found}`);
      if (had) { had.keys.push(f.key); had.off = had.off && f.skipped; continue; }
    }
    rows.push({ keys: [f.key], off: f.skipped, f, speaker: w.part === 'speaker' ? `${w.participant}|${f.found}` : '' });
  }
  let html = '';
  for (const [n, rows] of groups) {
    const e = list[n - 1] || { real: [], to: rows[0].f.to };
    html += `<div class="nm-group" data-entry="${n}"><div class="nm-group-head"><b>${esc((e.real || []).join(', '))}</b>`
      + `<span>${esc(t('distil.names.to'))}</span><span class="nm-to">${esc(e.to)}</span><span class="nm-n"></span></div>`;
    for (const r of rows) {
      html += `<label class="nm-hit${r.off ? ' is-off' : ''}" data-keys="${escAttr(r.keys.join('\n'))}"><input type="checkbox"${r.off ? '' : ' checked'}>`
        + `<span class="nm-who">${esc(nmWhere(r.f, who))}</span><span class="nm-ctx">${nmContext(r.f)}</span></label>`;
    }
    html += '</div>';
  }
  $('nm-review-body').innerHTML = html;
  $('nm-review-foot').innerHTML = actions.map((a, i) => `<button type="button" class="${a.primary ? 'primary' : 'ghost'}" data-act="${i}">${esc(a.label)}</button>`).join('');
  NM.review.actions = actions;
  nmReviewCounts();
  show('nm-review');
}

function nmReviewCounts() {
  for (const g of $('nm-review-body').querySelectorAll('.nm-group')) {
    const hits = [...g.querySelectorAll('.nm-hit')];
    const total = hits.reduce((a, h) => a + h.dataset.keys.split('\n').length, 0);
    const on = hits.filter((h) => h.querySelector('input').checked).reduce((a, h) => a + h.dataset.keys.split('\n').length, 0);
    g.querySelector('.nm-n').textContent = on === total ? String(total) : t('distil.names.of', { on, n: total });
  }
}

function nmReviewChange(e) {
  const box = e.target.closest('.nm-hit input');
  if (!box || !NM.review) return;
  const hit = box.closest('.nm-hit');
  hit.classList.toggle('is-off', !box.checked);
  NM.review.onTick(hit.dataset.keys.split('\n'), box.checked);
  nmReviewCounts();
}

function nmReviewClose() {
  hide('nm-review');
  NM.review = null;
}

/* Review on a row of Add transcripts: its finds, Done keeping the ticks for the Add */
async function nmReviewRow(row) {
  await nmPreview();
  const finds = nmRowFinds(row);
  if (!finds.length) return;
  const list = (NP.names && NP.names.list) || [];
  nmReviewOpen({ kicker: row.file, title: t('distil.names.review_title'), finds, list, who: false,
    onTick: (keys, on) => {
      row.skips = row.skips || new Set();
      for (const k of keys) { if (on) row.skips.delete(k); else row.skips.add(k); }
    },
    actions: [{ label: t('distil.names.done'), primary: true,
      run: () => { nmReviewClose(); nmDrawRows(); } }] });
}

/* ── Names to replace: the project's list ── */

async function nmListOpen(id, name) {
  let data;
  try {
    data = await api('/api/names', { op: 'list', root: id });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  NM.list = { id, name: name || '', rows: (data.entries || []).map((e) => ({ real: e.real.join(', '), to: e.to, for: e.for || '', case: !!e.case })),
    who: Array.isArray(data.participants) ? data.participants : [], check: null, said: '' };
  $('nm-list').querySelector('.kicker').textContent = NM.list.name;
  nmListDraw();
  show('nm-list');
}

function nmListDraw() {
  const L = NM.list;
  const opts = (f) => [['', t('distil.names.everyone')], ...L.who.map((p) => [p, p])]
    .map(([v, label]) => `<option value="${escAttr(v)}"${(f || '') === v ? ' selected' : ''}>${esc(label)}</option>`).join('');
  $('nm-list-rows').innerHTML = L.rows.map((r, i) => {
    const initials = NM_INITIALS.test(r.real.split(',')[0].trim());
    return `<tr data-i="${i}"><td><input type="text" data-nm="real" spellcheck="false" autocomplete="off" aria-label="${escAttr(t('distil.names.col_name'))}" value="${escAttr(r.real)}"></td>`
      + `<td><input type="text" data-nm="to" spellcheck="false" autocomplete="off" aria-label="${escAttr(t('distil.names.col_to'))}" value="${escAttr(r.to)}"></td>`
      + `<td class="nm-in"><select data-nm="for" aria-label="${escAttr(t('distil.names.col_in'))}">${opts(r.for)}</select></td>`
      + `<td class="nm-case"><label><input type="checkbox" data-nm="case"${r.case || initials ? ' checked' : ''}${initials ? ' disabled' : ''}>${esc(t('distil.names.match_case'))}</label></td>`
      + `<td class="nm-x"><button type="button" class="np-remove" data-nm="remove" aria-label="${escAttr(t('distil.names.remove', { name: r.real }))}" title="${escAttr(t('distil.np.remove'))}">${NP_CROSS}</button></td></tr>`;
  }).join('');
  $('nm-list-table').hidden = !L.rows.length;
  nmCheckDraw();
}

/* the list as the server keeps it: every row with a name and its replacement */
function nmListEntries() {
  return NM.list.rows.filter((r) => r.real.trim() && r.to.trim())
    .map((r) => ({ real: r.real, to: r.to.trim(), for: r.for || null, case: r.case || NM_INITIALS.test(r.real.split(',')[0].trim()) }));
}

async function nmListSave() {
  const L = NM.list;
  if (!L) return;
  try {
    await api('/api/names', { op: 'set', root: L.id, entries: nmListEntries() });
    L.said = '';
  } catch (err) { L.said = needsRestart(err) ? RESTART_LINE : err.message; }
  L.check = null;
  nmCheckDraw();
}

function nmListInput(e) {
  const el = e.target;
  const tr = el.closest('tr[data-i]');
  if (!tr || !NM.list) return;
  const r = NM.list.rows[Number(tr.dataset.i)];
  if (el.dataset.nm === 'real' || el.dataset.nm === 'to') r[el.dataset.nm] = el.value;
}

function nmListChange(e) {
  const el = e.target;
  const tr = el.closest('tr[data-i]');
  if (!tr || !NM.list) return;
  const r = NM.list.rows[Number(tr.dataset.i)];
  if (el.dataset.nm === 'for') r.for = el.value;
  else if (el.dataset.nm === 'case') r.case = el.checked;
  else if (el.dataset.nm === 'real') {
    r.real = el.value;
    // initials are matched by their case always, so their tick stands ticked and fixed
    const box = tr.querySelector('[data-nm="case"]');
    const initials = NM_INITIALS.test(r.real.split(',')[0].trim());
    box.disabled = initials;
    if (initials) box.checked = true;
  } else if (el.dataset.nm === 'to') r.to = el.value;
  nmListSave();
}

function nmListClick(e) {
  const b = e.target.closest('[data-nm="remove"]');
  if (!b || !NM.list) return;
  NM.list.rows.splice(Number(b.closest('tr').dataset.i), 1);
  nmListDraw();
  nmListSave();
  $('nm-add').focus();
}

function nmListAdd() {
  NM.list.rows.push({ real: '', to: '', for: '', case: false });
  nmListDraw();
  const inputs = $('nm-list-rows').querySelectorAll('[data-nm="real"]');
  if (inputs.length) inputs[inputs.length - 1].focus();
}

/* Add from a file: a two-column key he keeps, real name then pseudonym, read by the server and added to the list */
async function nmListFile(file) {
  if (!file || !NM.list) return;
  let data;
  try {
    data = await api('/api/names', { op: 'read-key', root: NM.list.id, name: file.name, data: await npBase64(file) });
  } catch (err) { NM.list.said = needsRestart(err) ? RESTART_LINE : err.message; nmCheckDraw(); return; }
  const had = new Set(NM.list.rows.map((r) => r.real.trim().toLowerCase()));
  for (const e of data.entries || []) {
    const real = e.real.join(', ');
    if (!had.has(real.toLowerCase())) NM.list.rows.push({ real, to: e.to, for: '', case: !!e.case });
  }
  nmListDraw();
  await nmListSave();
}

/* Check transcripts already in, its line and Review and replace beside it */
async function nmCheck() {
  const L = NM.list;
  if (!L) return;
  try {
    const data = await api('/api/names', { op: 'check', root: L.id, names_preview: true });
    L.check = data.names;
    L.list = data.list || [];
    L.skips = new Set();
    L.said = '';
  } catch (err) { L.said = needsRestart(err) ? RESTART_LINE : err.message; }
  nmCheckDraw();
}

function nmCheckLine(check) {
  const finds = check.finds || [];
  if (!finds.length) return t('distil.names.none_in');
  const who = [...new Set(finds.map((f) => (f.where || {}).participant).filter(Boolean))];
  const parts = [...new Set(finds.map((f) => (f.where || {}).part))].filter((p) => NM_PARTS[p]);
  const times = t('distil.names.times', { n: finds.length });
  const rest = parts.length ? t('distil.names.found_also', { parts: tList(parts.map((p) => t(NM_PARTS[p]))) }) : '';
  return who.length === 1 ? t('distil.names.found_one', { times, who: who[0], rest })
    : t('distil.names.found_many', { times, who: tList(who), rest });
}

function nmCheckDraw() {
  const L = NM.list;
  if (!L) return;
  const line = $('nm-check-line');
  line.hidden = !L.check;
  if (L.check) {
    $('nm-check-said').textContent = nmCheckLine(L.check);
    $('nm-replace').hidden = !(L.check.finds || []).length;
  }
  saidIn('nm-list-said', L.said || '', !!L.said);
  $('nm-list-said').hidden = !L.said;
}

/* Review and replace: every find in the transcripts already in, a tick each, Replace writing the ones ticked */
function nmReplaceReview() {
  const L = NM.list;
  if (!L || !L.check) return;
  L.skips = L.skips || new Set();
  const finds = nmKeyedProject(L.check.finds || []).map(({ f, key }) => ({ ...f, key, skipped: L.skips.has(key) }));
  nmReviewOpen({ kicker: L.name, title: t('distil.names.review_in_title'), finds, list: L.list || [], who: true,
    onTick: (keys, on) => { for (const k of keys) { if (on) L.skips.delete(k); else L.skips.add(k); } },
    actions: [{ label: t('distil.names.cancel'), run: () => nmReviewClose() },
      { label: t('distil.names.replace_go'), primary: true, run: () => nmReplace(finds) }] });
}

function nmKeyedProject(finds) {
  const seen = new Map();
  return finds.map((f) => {
    const w = f.where || {};
    const base = `${w.participant}|${w.interview}|${w.part}|${w.row || ''}|${f.found}`;
    const k = seen.get(base) || 0;
    seen.set(base, k + 1);
    return { f, key: `${base}|${k}` };
  });
}

async function nmReplace(finds) {
  const L = NM.list;
  const skip = finds.filter((f) => L.skips.has(f.key)).map((f) => `${f.entry}:${f.nth}`);
  // what is typed on a participant open behind is saved first, so the replace meets it and nothing writes over it
  if (S.data && typeof savePending === 'function' && !(await savePending())) return;
  let data;
  try {
    data = await api('/api/names', { op: 'replace', root: L.id, skip });
  } catch (err) {
    nmReviewClose();
    L.said = needsRestart(err) ? RESTART_LINE : err.message;
    nmCheckDraw();
    return;
  }
  nmReviewClose();
  L.check = null;
  nmCheckDraw();
  L.said = '';
  saidIn('nm-list-said', t('distil.names.replaced', { replaced: data.names.replaced,
    participants: t('distil.names.participants', { n: data.participants }) }), false);
  $('nm-list-said').hidden = false;
  // the screen behind reads the words as they are now
  NM.changed = true;
}

function nmListClose() {
  hide('nm-list');
  NM.list = null;
  if (NM.changed) {
    NM.changed = false;
    if (!$('library').hidden) loadLibrary().catch(() => {});
    else if (S.data) location.reload();
  }
  if (!$('newproject').hidden) nmSoon();
}

/* Esc on these cards: the Review first, then the list */
function nmKeys(e) {
  if (e.key !== 'Escape') return false;
  if (!$('nm-review').hidden) { e.preventDefault(); nmReviewClose(); return true; }
  if (!$('nm-list').hidden) { e.preventDefault(); nmListClose(); return true; }
  return false;
}

function nmWire() {
  $('nm-review-body').addEventListener('change', nmReviewChange);
  $('nm-review-foot').addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]');
    if (b && NM.review) NM.review.actions[Number(b.dataset.act)].run();
  });
  $('nm-list-rows').addEventListener('input', nmListInput);
  $('nm-list-rows').addEventListener('change', nmListChange);
  $('nm-list-rows').addEventListener('click', nmListClick);
  $('nm-add').onclick = () => nmListAdd();
  $('nm-file-pick').onclick = () => $('nm-file').click();
  $('nm-file').onchange = () => { nmListFile($('nm-file').files[0]); $('nm-file').value = ''; };
  $('nm-check').onclick = () => nmCheck();
  $('nm-replace').onclick = () => nmReplaceReview();
  $('nm-list-done').onclick = () => nmListClose();
  $('names-open').onclick = () => { const p = projectAt(); if (p && p.id && !p.demo) nmListOpen(p.id, p.name); };
}


/* A project from ATLAS.ti, NVivo or MAXQDA, a .qdpx (21 October), on New project's card and Add
   transcripts': dropped or chosen, it comes in on its own, as one row a source. The page sends the
   file once and the server keeps a copy, read again under its key as each choice changes (see
   `api_qdpx`). Each row has its tick, its first eight passages as they will land in the import
   card's columns, its speakers' roles, and its number, pseudonym, interview and timepoint. Under the
   rows the choosers, each at Adam's default (21 October), and the lines of what comes in and what is
   left out. Create project or Add brings in the sources ticked. */
const QD_ALONE = t('distil.qd.alone');
const QD_MAX = 256 * 1024 * 1024;
const QD_CHOICES = [
  ['codes', t('distil.qd.codes'), [['statements', t('distil.qd.as_statements')], ['notes', t('distil.qd.as_notes')], ['leave', t('distil.import.role.leave_out')]]],
  ['comments', t('distil.qd.comments'), [['notes', t('distil.qd.as_notes')], ['statements', t('distil.qd.as_statements')]]],
  ['loose', t('distil.qd.loose'), [['blank', t('distil.qd.as_quotes')], ['leave', t('distil.import.role.leave_out')]]],
  ['memos', t('distil.qd.memos'), [['source', t('distil.qd.to_source')], ['leave', t('distil.import.role.leave_out')]]],
  ['recordings', t('distil.qd.recordings'), [['copy', t('distil.qd.copy_player')], ['leave', t('distil.import.role.leave_out')]]],
];
const QD_HEADS = { name: t('distil.import.role.speaker'), ts: t('distil.import.role.time'), text: t('distil.import.role.transcript'),
  en: t('distil.import.role.notes'), es: t('distil.import.role.statements'), kq: t('distil.qd.quote') };
const isQdpx = (name) => /\.qdpx$/i.test(String(name || ''));
// a speaker's role as the server names it, in the API's own English words, to its chooser's value
const qdRoleKey = (label) => ({ Interviewer: 'interviewer', Participant: 'participant', 'Other speaker': 'other' }[label] || 'participant');

async function qdAdd(file) {
  if (file.size > QD_MAX) { npSaid(t('distil.qd.too_large', { file: file.name })); return; }
  let data;
  try {
    data = await npBase64(file);
  } catch { npSaid(t('distil.qd.unreadable', { file: file.name })); return; }
  NP.qdpx = { file: file.name, data, held: '', read: null, ask: 0, rows: new Map(), roles: {}, said: '', timer: 0,
    choices: Object.fromEntries(QD_CHOICES.map(([k, , opts]) => [k, opts[0][0]])), pets: false };
  npSaid('');
  drawQd();
  await qdRead();
}

/* Each participant's number, as `npNumbers` gives New project's rows theirs, over the rows ticked */
function qdNumbers() {
  const out = {};
  const used = new Set();
  const rows = NP.qdpx ? [...NP.qdpx.rows.values()].filter((r) => r.on) : [];
  const there = (p) => !!(NP.add && NP.add.cases.has(p));
  for (const r of rows) {
    const p = r.pseudonym.trim();
    const n = parseInt(r.number, 10);
    if (p && !(p in out) && !there(p) && n > 0) { out[p] = n; used.add(n); }
  }
  let next = NP.next;
  for (const r of rows) {
    const p = r.pseudonym.trim();
    if (!p || p in out || there(p)) continue;
    while (used.has(next)) next += 1;
    out[p] = next;
    used.add(next);
  }
  return out;
}

/* the sources ticked as the server takes them, a participant there already sending no number */
function qdSources() {
  const numbers = qdNumbers();
  const long = (NP.tps || []).length >= 2;
  return [...NP.qdpx.rows.values()].filter((r) => r.on).map((r) => {
    const p = r.pseudonym.trim();
    const joins = !!(NP.add && NP.add.cases.has(p));
    return { source: r.source, pseudonym: p, number: joins ? null : numbers[p] || null, interview: r.interview.trim(),
      ...(long ? { timepoint: npTimepoint(r) } : {}) };
  });
}

const qdAsks = () => ({ ...NP.qdpx.choices, pets: NP.qdpx.pets && NP.qdpx.choices.codes === 'statements',
  speakers: NP.qdpx.roles, sources: qdSources() });

/* The file read as the card now stands: sent whole the first time, by its key after, and whole again
   when the server no longer holds it (a restart between). Each source with passages gets its row,
   ticked, the first time it comes. */
async function qdRead() {
  const q = NP.qdpx;
  if (!q) return;
  clearTimeout(q.timer);
  const ask = ++q.ask;
  const where = NP.add ? { root: NP.add.id } : NP.folder ? { folder: NP.folder } : {};
  const send = () => api('/api/qdpx', { op: 'read', ...(q.held ? { held: q.held } : { name: q.file, data: q.data }), ...where, ...qdAsks() });
  let data;
  try {
    try {
      data = await send();
    } catch (err) {
      // the server no longer holds the file sent before (a restart between), file_not_held
      if (!q.held || !refusedAs(err, 'file_not_held')) throw err;
      q.held = '';
      data = await send();
    }
  } catch (err) {
    if (NP.qdpx !== q || ask !== q.ask) return;
    q.said = needsRestart(err) ? RESTART_LINE : err.message;
    drawQd();
    return;
  }
  if (NP.qdpx !== q || ask !== q.ask) return;
  q.held = data.held || q.held;
  q.read = data;
  q.said = '';
  for (const src of data.sources || []) {
    if (!src.passages || q.rows.has(src.source)) continue;
    q.rows.set(src.source, { source: src.source, on: true, pseudonym: '', number: '', interview: src.interview || t('distil.np.interview'), timepoint: 0 });
    for (const sp of src.speakers || []) if (!(sp.name in q.roles)) q.roles[sp.name] = qdRoleKey(sp.role);
  }
  drawQd();
}

/* a read a moment after the last key, so typing a pseudonym does not read the file at each letter */
function qdSoon() {
  const q = NP.qdpx;
  if (!q) return;
  clearTimeout(q.timer);
  q.timer = setTimeout(qdRead, 400);
}

/* A source's first passages in the import card's columns, Speaker and Transcript, then Time,
   Exploratory notes, Experiential statements and Quote where any passage has them */
function qdPreviewHtml(src) {
  const turns = (src.passages || []).map((p) => ({ name: p.speaker, ts: p.time, text: p.words,
    en: (p.notes || []).join('\n'), es: (p.statements || []).map((s) => s.statement || '').filter(Boolean).join('\n\n'),
    kq: (p.statements || []).map((s) => s.quote || '').join('\n\n') }));
  if (!turns.length) return '';
  const has = (k) => turns.some((t) => String(t[k] || '').trim());
  const shown = ['name', ...(has('ts') ? ['ts'] : []), 'text', ...['en', 'es', 'kq'].filter(has)];
  const head = (r) => (r === 'en' || r === 'es' || r === 'kq' ? ` data-head="${escAttr(QD_HEADS[r])}"` : '');
  const longest = Math.max(4, ...turns.map((t) => String(t.ts || '').length));
  const width = (r) => (r === 'ts' ? ` style="width: calc(${longest}ch + 14px)"` : '');
  return `<div class="import-fade"><div class="import-preview"><table class="import-table n${shown.length}"><thead><tr>`
    + shown.map((r) => `<th class="ip-${r}"${width(r)}>${esc(QD_HEADS[r])}</th>`).join('') + '</tr></thead><tbody>'
    + turns.map((t) => '<tr>' + shown.map((r) => `<td class="ip-${r}"${head(r)}>${esc(t[r] || '')}</td>`).join('') + '</tr>').join('')
    + '</tbody></table></div></div>';
}

function qdRowHtml(src, numbers) {
  const q = NP.qdpx;
  const row = q.rows.get(src.source);
  const shown = (src.passages || []).length;
  let html = `<li class="np-row qd-row${row.on ? '' : ' is-off'}" data-source="${src.source}">`
    + `<label class="np-row-head qd-tick"><input type="checkbox" data-qd="on"${row.on ? ' checked' : ''}>`
    + `<span class="np-file">${esc(src.name)}</span><span class="np-count">${turnsWord(src.count)}</span></label>`;
  if (!row.on) return `${html}</li>`;
  html += `<div class="import-turns np-turns is-table">${qdPreviewHtml(src)}</div>`;
  if (src.count > shown) html += `<p class="fineprint import-count">${esc(t('distil.import.shown_of', { shown, n: src.count }))}</p>`;
  if ((src.speakers || []).length) {
    html += `<div class="import-who np-who" role="group" aria-label="${escAttr(t('distil.np.speakers'))}"><p class="import-sub">${esc(t('distil.np.speakers'))}</p>`
      + speakerChoosersHtml(src.speakers, q.roles, () => ' data-qd="speaker"') + '</div>';
  }
  const p = row.pseudonym.trim();
  const joins = NP.add ? NP.add.cases.get(p) || '' : '';
  const field = (name, label, value, more = '') => `<label class="np-field${more}"><span>${label}</span><input data-qd="${name}"`
    + ` type="text" spellcheck="false" autocomplete="off"${name === 'pseudonym' ? ' list="np-names"' : ''}`
    + `${name === 'number' ? ` inputmode="numeric" aria-label="${escAttr(t('distil.np.number'))}"` : ''} value="${escAttr(value)}"></label>`;
  const tps = NP.tps || [];
  const tpField = tps.length >= 2
    ? `<label class="np-field np-tp"><span>${esc(t('distil.np.timepoint'))}</span><select data-qd="timepoint">${tps.map((tp) => `<option value="${tp.n}"`
      + `${tp.n === npTimepoint(row) ? ' selected' : ''}>${esc([tp.label, tp.description].filter(Boolean).join(' '))}</option>`).join('')}</select></label>` : '';
  html += '<div class="np-fields">' + (joins ? '' : field('number', esc(t('distil.np.p')), row.number || (p && numbers[p]) || '', ' np-num'))
    + field('pseudonym', esc(t('distil.np.pseudonym')), row.pseudonym) + field('interview', esc(t('distil.np.interview')), row.interview) + tpField + '</div>';
  if (joins) html += `<p class="np-joins">${esc(t('distil.np.joins', { name: joins.replace(/^(P\d+)\s*-\s*/, '$1 ') }))}</p>`;
  return `${html}</li>`;
}

function qdChoosersHtml(r) {
  const q = NP.qdpx;
  const srcs = r.sources || [];
  const offered = (k) => (k !== 'memos' || srcs.some((s) => s.memos)) && (k !== 'recordings' || srcs.some((s) => s.recording));
  const rows = QD_CHOICES.filter(([k]) => offered(k)).map(([k, label, opts]) => `<label class="setting import-speaker qd-choice">`
    + `<span class="setting-label">${esc(label)}</span><select data-qd="choice-${k}">`
    + opts.map(([v, l]) => `<option value="${v}"${q.choices[k] === v ? ' selected' : ''}>${esc(l)}</option>`).join('') + '</select></label>');
  const pets = q.choices.codes === 'statements' && (r.groups || []).length
    ? `<label class="view-row qd-pets"><input type="checkbox" data-qd="pets"${q.pets ? ' checked' : ''}> ${esc(t('distil.qd.draft_pets'))}</label>` : '';
  return `<div class="import-who qd-choices" role="group" aria-label="${escAttr(t('distil.qd.what_comes'))}"><p class="import-sub">${esc(t('distil.qd.what_comes'))}</p>${rows.join('')}${pets}</div>`;
}

function qdHtml() {
  const q = NP.qdpx;
  const r = q.read;
  const kind = r && r.package ? t('distil.qd.from', { package: r.package }) : t('distil.qd.from_any');
  let html = `<div class="np-row-head qd-head"><span class="np-file">${esc(q.file)}</span><span class="np-count">${esc(kind)}</span>`
    + `<button type="button" class="np-remove" data-qd="remove" aria-label="${escAttr(t('distil.np.remove_file', { file: q.file }))}" title="${escAttr(t('distil.np.remove'))}">${NP_CROSS}</button></div>`;
  if (r) {
    const numbers = qdNumbers();
    html += '<ol class="np-rows qd-rows">' + (r.sources || []).filter((s) => q.rows.has(s.source)).map((s) => qdRowHtml(s, numbers)).join('') + '</ol>';
    html += qdChoosersHtml(r);
    html += `<div class="qd-lines">${(r.lines || []).map((l) => `<p class="fineprint">${esc(l)}</p>`).join('')}</div>`;
  }
  // the server's refusal once every source ticked has its pseudonym, so a row being filled is never told off
  const ticked = [...q.rows.values()].filter((x) => x.on);
  const said = q.said || (r && r.said && ticked.length && ticked.every((x) => x.pseudonym.trim()) ? r.said : '');
  if (said) html += `<p class="warn qd-said">${esc(said)}</p>`;
  return html;
}

/* The block drawn again, the field he was in keeping the focus and its caret, and the drop place away
   while a project is on the card, since it comes in on its own */
function drawQd() {
  const box = $('np-qdpx');
  const q = NP.qdpx;
  $('np-drop').hidden = !!q;
  box.hidden = !q;
  if (!q) { box.innerHTML = ''; return; }
  const active = document.activeElement && box.contains(document.activeElement) ? document.activeElement : null;
  const li = active ? active.closest('[data-source]') : null;
  const was = active ? { qd: active.dataset.qd, speaker: active.dataset.speaker, source: li ? li.dataset.source : '',
    at: typeof active.selectionStart === 'number' ? [active.selectionStart, active.selectionEnd] : null } : null;
  box.innerHTML = qdHtml();
  importFades();
  npNamesDraw();
  if (!was || !was.qd) return;
  const scope = was.source ? box.querySelector(`[data-source="${CSS.escape(was.source)}"]`) : box;
  const sel = `[data-qd="${CSS.escape(was.qd)}"]${was.speaker ? `[data-speaker="${CSS.escape(was.speaker)}"]` : ''}`;
  const back = scope ? scope.querySelector(sel) : null;
  if (!back) return;
  back.focus();
  if (was.at && typeof back.setSelectionRange === 'function') back.setSelectionRange(was.at[0], was.at[1]);
}

const qdRowOf = (el) => {
  const li = el && el.closest ? el.closest('[data-source]') : null;
  return li && NP.qdpx ? NP.qdpx.rows.get(Number(li.dataset.source)) || null : null;
};

/* each number field as the pseudonyms now stand, the one he is in left alone */
function qdNumbersDraw() {
  const numbers = qdNumbers();
  for (const input of $('np-qdpx').querySelectorAll('[data-qd="number"]')) {
    const row = qdRowOf(input);
    if (!row || input === document.activeElement) continue;
    const p = row.pseudonym.trim();
    input.value = row.number || (p && numbers[p]) || '';
  }
}

function qdInput(e) {
  const name = e.target && e.target.dataset ? e.target.dataset.qd : null;
  const row = qdRowOf(e.target);
  if (!row || !['pseudonym', 'number', 'interview'].includes(name)) return;
  row[name] = e.target.value;
  if (name === 'pseudonym') {
    const p = e.target.value.trim();
    const mate = p ? [...NP.qdpx.rows.values()].find((r) => r !== row && r.on && r.pseudonym.trim() === p) : null;
    if (mate) row.number = mate.number;
    npNamesDraw();
  }
  qdNumbersDraw();
  qdSoon();
}

function qdChange(e) {
  const q = NP.qdpx;
  const name = e.target && e.target.dataset ? e.target.dataset.qd : null;
  if (!q || !name) return;
  const row = qdRowOf(e.target);
  if (name === 'on' && row) row.on = e.target.checked;
  else if (name === 'timepoint' && row) row.timepoint = Number(e.target.value) || 1;
  else if (name === 'speaker') q.roles[e.target.dataset.speaker] = e.target.value;
  else if (name === 'pets') q.pets = e.target.checked;
  else if (name.startsWith('choice-')) q.choices[name.slice(7)] = e.target.value;
  else return;
  // a tick or the codes' choice changes what the card holds at once, before the server's answer
  if (name === 'on' || name === 'choice-codes') drawQd();
  qdRead();
}

function qdClick(e) {
  const button = e.target && e.target.closest ? e.target.closest('[data-qd="remove"]') : null;
  if (!button || !NP.qdpx) return;
  clearTimeout(NP.qdpx.timer);
  NP.qdpx = null;
  drawQd();
  npSaid('');
  $('np-pick').focus();
}

/* Create project, or in Add, Add: the sources ticked brought in by the server, which checks them all
   before it writes anything. New project makes its project first, through its own make. */
async function qdMake() {
  const q = NP.qdpx;
  const add = NP.add;
  const typed = add ? '' : $('np-folder').value.trim();
  if (typed && typed !== NP.folder && !(await npFolder(typed))) return;
  if (!q.held) await qdRead();
  if (!q.held) return;
  NP.busy = true;
  $('np-go').disabled = true;
  npSaid('');
  const asks = qdAsks();
  try {
    if (add) await api('/api/qdpx', { op: 'make', root: add.id, held: q.held, ...asks });
    else {
      const made = await api('/api/new-project', { op: 'make', folder: typed, name: $('np-name').value.trim(),
        research_question: $('np-question').value.trim(), method: npMethod(), files: [], qdpx: { held: q.held, ...asks } });
      if (made && made.project && made.project.id) homeKeep(made.project.id);
    }
    closeNewProject();
    loadLibrary().catch((err) => say(err.message, 9000));
  } catch (err) {
    npSaid(needsRestart(err) ? RESTART_LINE : err.message);
  } finally {
    NP.busy = false;
    $('np-go').disabled = false;
  }
}

/* A file dragged over the window while the card is open lands on the card, wherever it is let go,
   and the drop place shows it. With the card shut a drop does what it always did. */
const npShown = () => !$('newproject').hidden;
const npFilesIn = (e) => !!(e.dataTransfer && Array.from(e.dataTransfer.types || []).includes('Files'));

function npDrag(e) {
  if (!npShown() || !npFilesIn(e)) return;
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
  $('np-drop').classList.add('dragging');
}

function npDragEnd(e) {
  if (e.type === 'dragleave' && e.relatedTarget) return;
  $('np-drop').classList.remove('dragging');
}

function npDrop(e) {
  if (!npShown() || !npFilesIn(e)) return;
  e.preventDefault();
  $('np-drop').classList.remove('dragging');
  npAdd(e.dataTransfer.files);
}

/* ───────────────────────────────────────────────────────────── case ── */

/* "Opening." stands at the foot while the case loads and goes the moment it is shown (17 October),
   where it stayed its four seconds over the open case */
const OPENING_LINE = t('distil.case.opening');

/* a case, its PETs or its project's GETs from the home screen, each a way in with its entry in the
   browser's history, so Back returns to the home screen and Forward opens it again */
const openCaseIn = (path, opts) => navGo(() => openCaseIn(path, opts), () => openCase(path, opts));
const openThemesIn = (path, label) => navGo(() => openThemesIn(path, label), () => openThemes(path, 'library', label));
const openGetsIn = (path) => navGo(() => openGetsIn(path), () => openGets(path));

async function openCase(path, opts = {}) {
  try {
    say(OPENING_LINE);
    const data = await api('/api/open', { path });
    // a case opened from its row goes back to the case list, whatever a passage opened before
    S.backTo = null;
    startCase(data, opts && opts.timepoint ? { timepoint: opts.timepoint } : {});
    unsay(OPENING_LINE);
  } catch (err) { say(err.message, 9000); }
}

/* Experiential statements from a step on the PETs or GETs bar (18 October, see thToStatements in themes.js):
   the case opened, at the passage it was on when this screen still holds it, the board put away only once it
   is, and the bar's way back named for the board it returns to. `how` is as `openPassage` takes it. */
async function openStatements(path, how) {
  let data;
  try {
    say(OPENING_LINE);
    data = await api('/api/open', { path });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return false; }
  const row = S.data && S.data.path === data.path ? current() : null;
  how.leave();
  S.backTo = { back: how.back, to: how.to, timepoint: how.timepoint || null };
  startCase(data, row ? { at: { sheet: row.sheet, row: row.row } } : {});
  unsay(OPENING_LINE);
  return true;
}

// the line for a statement whose passage has gone, as the server says it
const NO_PASSAGE_LINE = t('distil.case.no_passage');

/* A statement's passage, from a card on the PETs or GETs canvas (16 October, see `thToPassage` in
   themes.js): the case opened at that passage, which the server first checks is still a passage of
   the participant's in the transcript, the board put away only once it is, the caret in that
   statement with its quote's marks lit, and the bar's way back named for the board it returns
   to. `how` is `leave`, which puts the board away, `back`, which brings it back, and `to`, its name.
   A refusal is one line and leaves the board as it is. */
async function openPassage(path, at, how) {
  let data;
  try {
    data = await api('/api/open', { path, passage: { sheet: at.sheet, row: at.row } });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return false; }
  // and looked for here too, as a server from before the check opens the case whatever it holds
  const who = String((data.config || {}).interviewer || 'Adam').trim().toLowerCase();
  const sheet = (data.sheets || []).find((s) => s.name === at.sheet);
  const there = sheet && sheet.rows.some((r) => r.row === at.row && r.name && r.name.trim().toLowerCase() !== who);
  if (!there) { say(NO_PASSAGE_LINE, 6000); return false; }
  how.leave();
  S.backTo = { back: how.back, to: how.to, timepoint: how.timepoint || null };
  startCase(data, { at: { sheet: at.sheet, row: at.row } });
  const row = current();
  const el = row && row.sheet === at.sheet && row.row === at.row ? pairEls()[at.line] : null;
  if (el) {
    S.kqLit = el.dataset.pid;
    S.pairFocus = el.dataset.pid;
    if (!guideHolds()) el.querySelector('.pair-es').focus({ preventScroll: true });
    lightMarks();
  }
  passageStartInView();
  // and again once the column's own second centring has run (see drawTurn)
  requestAnimationFrame(passageStartInView);
  return true;
}

/* The passage opened from a board lands with its start in view at every width (17 October, after the
   screenshot check, where at 360 it landed with none of it in view): a passage taller than the column
   stands with its first line at the column's head, where centring it put its start above, and at a
   phone's width, with the fields under the column, the page comes back up to the passage, where the
   caret's field had taken it down past it. The caret stays in the statement's field. */
function passageStartInView() {
  const col = $('transcript');
  const turn = col && col.querySelector('.turn.current');
  if (!turn) return;
  const head = col.getBoundingClientRect().top;
  const start = turn.getBoundingClientRect().top;
  if (start < head + SPEAKER_CLEAR) col.scrollTop -= head + SPEAKER_CLEAR - start;
  const under = stickyBottom();
  const now = turn.getBoundingClientRect().top;
  if (now < under + 8 || now > window.innerHeight - 48) window.scrollBy(0, now - under - 8);
}

/* The foot of what sticks at the top of the statements screen, the title bar and the research
   question's band under it, each measured as it stands, so a passage brought into view keeps its
   speaker line below them at every width (17 October, after the screenshot check, where at 360 the
   band's height was left out and the speaker and time stood under it). */
function stickyBottom() {
  let foot = 0;
  for (const el of [$('work').querySelector('.rail'), $('band')]) {
    if (el && !el.hidden && el.offsetHeight) foot = Math.max(foot, el.getBoundingClientRect().bottom);
  }
  return foot;
}

/* `opts.land` is a reload in place after an assignment or its undo: the same workbook, the rows
   renumbered under it. The turn it lands on is the one he was on, wherever it has moved to, the
   round clock keeps every count it had and the player is left exactly where it was. `opts.at`, a
   sheet and a row, is the turn a page coming back from a restart was on, or the stop nearest it. */
function startCase(data, opts = {}) {
  // an interviewer note still open is kept against the rows it was opened on, before they go
  if (S.note) keepNote();
  // the undo stack belongs to one workbook: opening another one leaves nothing of the first
  if (!S.data || S.data.path !== data.path) undoClear();
  // and the find and replace card closes with it
  if (!S.data || S.data.path !== data.path) closeFind();
  const inPlace = !!(opts.land && S.data && S.data.path === data.path);
  const was = S.at;
  // the rows read afresh hold every passage as it is saved now
  hideStale();
  S.data = data;
  // the participant's project's method, whose words the screen takes (tadraw)
  tMethod(data.project && data.project.method);
  // a thematic analysis project's codes, for Add a code's suggestions (codes.js)
  if (typeof cxCodesRead === 'function' && tMethodNow() === 'ta') cxCodesRead(data.path);
  // and the guidance of its method, a thematic analysis project's its own (tarail)
  guideRail();
  aiPage(data.config);
  drawFeedback(data.feedback);
  S.flat = [];
  for (const sheet of data.sheets) for (const row of sheet.rows) S.flat.push(row);
  // a server that sends no rounds leaves an empty list, so no marker is drawn and nothing raises
  if (!Array.isArray(data.rounds)) data.rounds = [];
  const roundOf = {};
  for (const r of data.rounds) for (const k of r.rows) roundOf[`${k.sheet}:${k.row}`] = r.number;
  S.flat.forEach((row, i) => { row.i = i; row.key = `${row.sheet}:${row.row}`; row.round = roundOf[row.key]; });
  const interviewer = (data.config.interviewer || 'Adam').trim().toLowerCase();
  S.stops = [];
  for (const row of S.flat) {
    row.stop = !!(row.name && row.name.trim().toLowerCase() !== interviewer);
    // another speaker's turn, which the workbook marks (20 October), can be coded, and a step from
    // passage to passage passes it as it passes the interviewer's
    row.other = !!row.context;
    if (row.stop) { row.pos = S.stops.length; S.stops.push(row.i); }
  }
  S.sheetDrawn = null;
  if (!inPlace) S.audioSheet = null;
  // a reload in place renumbers the rows, so an open find counts again over them before the
  // column is drawn
  if (findOpen()) { findCount(); FIND.at = -1; FIND.painted = new Set(); drawToPair(); }
  S.pending = [];
  S.pairsRow = null;
  S.listening = null;
  S.spansSheet = null;
  S.at = 0;
  if (inPlace) {
    S.at = stopNear(opts.land.sheet, Number(opts.land.row), was);
  } else if (data.last) {
    const found = S.stops.findIndex((i) => S.flat[i].key === `${data.last.sheet}:${data.last.row}`);
    // the passage after the last one he was on, past another speaker's turns (20 October)
    let next = found + 1;
    while (found >= 0 && next < S.stops.length - 1 && S.flat[S.stops[next]].other) next += 1;
    if (found >= 0) S.at = Math.min(next, S.stops.length - 1);
  } else {
    const first = S.stops.findIndex((i) => !S.flat[i].other && (data.progress.states[S.flat[i].key] || 'unvisited') === 'unvisited');
    if (first >= 0) S.at = first;
  }
  if (!inPlace && opts.at && opts.at.sheet) S.at = stopNear(opts.at.sheet, Number(opts.at.row), S.at);
  // a timepoint's cell on the home screen opens at that timepoint, where he was in it or its first
  // undecided passage (20 October)
  if (!inPlace && opts.timepoint && tpList()) {
    const here = tpOfSheet((S.flat[S.stops[S.at]] || {}).sheet);
    if (!here || here.n !== opts.timepoint) {
      const k = tpStop(opts.timepoint);
      if (k >= 0) S.at = k;
    }
  }
  if (!inPlace) { clockClear(); drawClock(); }
  $('library').hidden = true;
  $('work').hidden = false;
  // the turns an agent has written so far, counted from here
  if (!inPlace) esStampStart();
  // the project's name beside the mark, and the participant's in the tab's picker, each truncating when the
  // bar runs short, the whole name in its tooltip (20 October)
  const who = data.case || data.name;
  // its number and pseudonym, P2 Mabel, as the rows and the picker say it (pbiobuild, layout A as drawn)
  $('rail-case').textContent = caseShown(who);
  $('rail-case').title = who;
  $('es-who').title = t('distil.case.who_title', { who });
  // their picture before the name and their label after it (pbiobuild, layout A)
  if (typeof ppBarDraw === 'function') ppBarDraw($('rail-pic'), $('rail-label'), data.person);
  pathProjectDraw('rail-project', data.project);
  esWhoMenu(false);
  dsTabsDraw('es-steps', data.project, 'statements');
  drawRoundsShown();
  // the view as the settings have it, the menus shut
  viewMenu(false);
  colsMenu(false);
  drawView();
  $('rail-demo').hidden = !data.demo;
  drawBand();
  // the toolbar docked under the band or floating where it was left (barsD)
  thPalettePlace(undefined, ES_TOOLS);
  fillSheetSwitch();
  fillTpPick();
  $('note-hint').textContent = keyName(t('distil.keys.cmd_enter'));
  drawTurn({ keepPlayer: inPlace });
  drawProgress();
  loadExamples();
  // a round that is done and was never recorded, the ones he passed the end of before a passed turn
  // counted among the decided, is recorded as the case opens, oldest first, with no card
  closeRounds(roundsToClose(Infinity), { quiet: true });
}

/* The stop at a row, or the first one after it on that sheet, or the last one before it. A turn
   given to the interviewer is no longer a stop, and this is where that lands instead. */
function stopNear(sheet, row, fallback) {
  const on = (k) => S.flat[S.stops[k]].sheet === sheet;
  for (let k = 0; k < S.stops.length; k += 1) if (on(k) && S.flat[S.stops[k]].row >= row) return k;
  for (let k = S.stops.length - 1; k >= 0; k -= 1) if (on(k)) return k;
  return Math.max(0, Math.min(fallback || 0, S.stops.length - 1));
}

/* ──────────────────────────────────────────────────────────── themes ── */

/* The PETs screen lives in themes.js. These are its ways in, from a row of the case list and from
   Experiential statements, and the way back to whichever it was, which its back control names.
   From Experiential statements a field typed into and not saved is saved first, as on any move, and the recording stops.
   `more` goes to `themesOpen`, a board and what to do when it or the case is gone, for a restart. */
async function openThemes(path, from, label, more = {}) {
  if (!path) return;
  if (from === 'work') {
    if (S.dirty && S.data && current()) {
      await commit(current(), false);
      if (S.dirty) return;
    }
    $('player').pause();
    closeFind();
  }
  // a save from Settings over the PETs screen that recut the rounds reopens the case on the way back
  const back = from === 'work'
    ? () => {
      if (S.recut && S.data) { S.recut = false; openCase(S.data.path); return; }
      $('work').hidden = false; measureBand(); centreCurrent(false); focusEntry();
    }
    : () => { loadLibrary().catch((err) => say(err.message, 9000)); };
  $('library').hidden = true;
  $('work').hidden = true;
  // the board loaded is what a search waits on before it selects on it (search.js)
  return themesOpen(path, Object.assign({ back, label, to: from === 'work' ? 'statements' : 'cases' }, more));
}

/* The GETs screen, from the row at the head of All cases or under the Demo card: the GETs of the
   project the workbook belongs to, with the way back to the case list. It lives in themes.js, the
   PETs canvas one layer up. `more` goes to `getsOpen`, as `openThemes` passes it. */
function openGets(path, more = {}) {
  if (!path) return;
  $('library').hidden = true;
  $('work').hidden = true;
  return getsOpen(path, Object.assign({ back: () => { loadLibrary().catch((err) => say(err.message, 9000)); }, label: '', to: 'cases' }, more));
}

/* ───────────────────────────────────────────────────── turn screen ── */

const current = () => S.flat[S.stops[S.at]];

/* A turn's text as the column draws it: its words, its quotes marked, and the find's washes over
   them while the find and replace card is open. A highlight the workbook holds, an orange run, is
   kept in the file and drawn as plain words, since the quotes are the marks in the text (16
   October). */
function rowHtml(row) {
  return markedHtml(row.runs, [...kqLayer(row), ...pendingLayer(row), ...findLayer(row)]);
}

/* The whole sheet, in order, interviewer turns included. Built once per sheet: navigating moves
   the `current` class and re-centres, and a quote marked redraws one turn, so nothing here runs
   on a keystroke. */
/* Three things hang in the margin and they do different work: the speaker name goes to the turn,
   the timecode plays the recording from there and a double-click on it corrects it, and the small
   control opens the row's menu. The control sits on the timecode's line, so on a turn of one line it
   stays inside the row and under the pointer rather than hanging over the next turn's name. The
   timecode is drawn on its own so a correction redraws it alone. */
function timeHtml(row) {
  return (row.seconds === null || row.seconds === undefined)
    ? `<span class="mono time">${esc(row.time)}</span>`
    : `<button type="button" tabindex="-1" class="mono time seek" data-seek="${row.seconds}" title="${escAttr(t('distil.turn.seek_title'))}">${esc(row.time)}</button>`;
}

function turnHtml(row) {
  const speaker = row.stop
    ? `<button type="button" tabindex="-1" class="speaker go-turn" data-go="${row.pos}" title="${escAttr(t('distil.turn.go_title'))}">${esc(row.name)}</button>`
    : `<span class="speaker">${esc(row.name)}</span>`;
  // her passages carry their experiential statements and their exploratory notes in the columns beside
  // their words (17 October), and the interviewer's carry neither
  const cells = row.stop
    ? `<div class="turn-es">${statementsHtml(row)}</div><div class="turn-notes">${notesHtml(row)}</div>` : '';
  return `<article class="turn${row.stop ? '' : ' aside'}" data-i="${row.i}">
      <div class="turn-gutter${row.stop ? ' stop' : ''}">
        ${speaker}
        <span class="gutter-time"><button type="button" tabindex="-1" class="row-menu-open" data-menu="${row.i}"
                title="${escAttr(t('distil.turn.menu_title'))}">&#8943;</button>${timeHtml(row)}${noteMarkHtml(row)}</span>
      </div>
      <div class="turn-text">${rowHtml(row)}</div>${cells}<span class="turn-done" aria-hidden="true"></span>
    </article>`;
}

/* ───────────────────────────────────────────────────── the columns ── */

/* The statements screen in the book's three columns (17 October, Adam's decision on a tester's "J-way",
   Smith, Flowers and Larkin 2022, Box 5.4): experiential statements, the transcript and exploratory
   notes side by side, each of her passages a row across the three and the three scrolling as one. The
   order is his: the book's on a new install, and any of the six from a heading's grip, kept in
   config.json as `statements_columns`, and Columns at the headings' right puts the book's back. A
   config from before, with the notes' place, `notes_place`, reads the order nearest the screen it
   drew, as the server reads it. Since 18 October, Adam's drawing of four layouts and one menu, Columns
   also hides the statements, the notes or both, the transcript always shown, and stacks the notes
   under the statements in one column beside the transcript, `columns_hidden`, `columns_stacked` and
   `stack_split` beside the order, Settings' View holding the same. Each part of a row stands in its
   column by the column's place, `--es-col`, `--tx-col` and `--en-col` on #work, three columns of `--cols` from 801px,
   two of `--cols2` up to 800px with each passage's notes under its words, and at a phone's width one,
   each passage's words first and its other two columns under them in their order, `--es-ord` and
   `--en-ord`. The current passage's statements are its card and its notes the notes field, placed in
   its row as it becomes the current one (`placeCard`, `placeNotes`). The larger current passage stays
   a View choice, `larger_passage`, on when absent. */
const COLUMNS = ['statements', 'transcript', 'notes'];
// read as each is asked, so a column's name follows the method in front (tadraw)
const COLUMN_WORDS = { get statements() { return t('distil.cols.statements'); }, get transcript() { return t('distil.cols.transcript'); }, get notes() { return t('distil.cols.notes'); } };
const COLUMN_KEYS = { statements: 'es', transcript: 'tx', notes: 'en' };
// the notes' three places until 17 October, each read as the order nearest the screen it drew
const NOTES_PLACE_COLUMNS = {
  right: ['transcript', 'notes', 'statements'],
  left: ['notes', 'transcript', 'statements'],
  under: ['transcript', 'statements', 'notes'],
};
// any of the six orders is a grip's to make, where until 18 October Columns and Settings listed the six
const isColumns = (v) => Array.isArray(v) && v.length === COLUMNS.length && COLUMNS.every((c) => v.includes(c));
function columnsOf(cfg) {
  if (cfg && isColumns(cfg.statements_columns)) return cfg.statements_columns.slice();
  return ((cfg && NOTES_PLACE_COLUMNS[cfg.notes_place]) || COLUMNS).slice();
}
// an order in words, "statements, transcript, notes", as Columns' tooltip says it
const columnsSaid = (order) => order.map((c) => ({ statements: t('distil.cols.short.statements'), transcript: t('distil.cols.short.transcript'), notes: t('distil.cols.short.notes') }[c])).join(', ');
function largerPassage(cfg) { return !(cfg && cfg.larger_passage === false); }
const viewConfig = () => (S.data && S.data.config) || S.libConfig || null;

/* The columns shown and how the statements and the notes stand (18 October, Adam's drawing of four
   layouts and one menu): the columns hidden, the statements, the notes or both and never the transcript,
   hidden meaning not shown and never deleted, and Stacked, the notes under the statements in one column
   beside the transcript, which holds only while both are shown, so with either hidden it has nothing to
   stack and is not offered. The divider between the two halves starts at half and keeps its place. A
   config with none of them reads as the three side by side, as the server reads it. */
const HIDEABLE_COLUMNS = ['statements', 'notes'];
const STACK_SPLIT = 0.5;
const STACK_RANGE = [0.2, 0.8];
function columnsHiddenOf(cfg) {
  const v = cfg && cfg.columns_hidden;
  if (!Array.isArray(v) || !v.every((c) => HIDEABLE_COLUMNS.includes(c))) return [];
  return HIDEABLE_COLUMNS.filter((c) => v.includes(c));
}
function stackSplitOf(cfg) {
  const v = cfg && cfg.stack_split;
  if (typeof v !== 'number' || !Number.isFinite(v)) return STACK_SPLIT;
  return Math.min(STACK_RANGE[1], Math.max(STACK_RANGE[0], v));
}
/* The column above in the stacked column (21 October, from Adam's backlog: a heading dropped on the other
   column stacks the two either way up), the statements unless the settings say the notes, `stack_top` */
const STACK_OTHER = { statements: 'notes', notes: 'statements' };
const stackTopOf = (cfg) => (cfg && cfg.stack_top === 'notes' ? 'notes' : 'statements');
function columnsLayout(cfg) {
  const hidden = columnsHiddenOf(cfg);
  const chose = !!(cfg && cfg.columns_stacked === true);
  const top = cfg && cfg.stack_top === 'notes' ? 'notes' : 'statements';
  return { order: columnsOf(cfg), hidden, chose, stacked: chose && !hidden.length, split: stackSplitOf(cfg), top };
}
// Stacked's row in Columns' menu and in Settings, as the stack stands either way up
function stackedWords(top) {
  return top === 'notes' ? t('distil.cols.stacked_notes_top') : t('distil.cols.stacked_statements_top');
}
// a column hidden now, and the notes stacked under the statements now, which holds above 800px alone, where
// today's rules put the notes under the words whatever was chosen
const colsHidden = (name) => !!(S.layout && S.layout.hidden.includes(name));
const colsNarrow = () => typeof matchMedia === 'function' && matchMedia('(max-width: 800px)').matches;
const stackedNow = () => !!(S.layout && S.layout.stacked) && !colsNarrow();

/* The places of an order's columns as the stylesheet reads them: each column's place among those shown
   and the tracks in their order, its place among two with the notes under the words, and at a phone's
   width the place of the statements and the notes after the words. A hidden column takes no track and
   stands at the first place, out of sight (18 October). The tracks of the stacked column and the
   transcript, `--stk-cols`, stand in the statements' place beside the transcript. */
function colsVars(order, hidden = []) {
  const shown = order.filter((c) => !hidden.includes(c));
  const two = shown.filter((c) => c !== 'notes');
  const after = order.filter((c) => c !== 'transcript');
  const track = (c) => `var(--${COLUMN_KEYS[c]}-track)`;
  const at = (list, c) => String(Math.max(0, list.indexOf(c)) + 1);
  return {
    '--es-col': at(shown, 'statements'),
    '--tx-col': at(shown, 'transcript'),
    '--en-col': at(shown, 'notes'),
    '--cols': shown.map(track).join(' '),
    '--es-col2': at(two, 'statements'),
    '--tx-col2': at(two, 'transcript'),
    '--cols2': two.map(track).join(' '),
    '--es-ord': String(after.indexOf('statements') + 2),
    '--en-ord': String(after.indexOf('notes') + 2),
    '--stk-cols': order.filter((c) => c !== 'notes').map((c) => (c === 'statements' ? 'var(--st-track)' : track(c))).join(' '),
  };
}

/* An order with one column moved: before `before`, or with no `before` after the last of the columns
   on screen, `shown`, so a column dropped at the end of two keeps the notes, out of sight under the
   words, where they stood. Answers the new order. */
function colsMoved(order, name, before, shown = order) {
  // let go at its own place, it stays
  if (before === name) return order.slice();
  const rest = order.filter((c) => c !== name);
  let at = before ? rest.indexOf(before) : -1;
  if (at < 0) {
    const last = shown.filter((c) => c !== name).pop();
    at = last ? rest.indexOf(last) + 1 : rest.length;
  }
  rest.splice(at, 0, name);
  return rest;
}

/* One column moved a place to the left, -1, or the right, 1, among the columns on screen, `shown`, the
   one out of sight keeping its place among the three. Null at either end. */
function colsStep(order, name, delta, shown = order) {
  const seen = order.filter((c) => shown.includes(c));
  const at = seen.indexOf(name);
  const to = at + delta;
  if (at < 0 || to < 0 || to >= seen.length) return null;
  const swapped = seen.slice();
  [swapped[at], swapped[to]] = [swapped[to], swapped[at]];
  let k = 0;
  return order.map((c) => (shown.includes(c) ? swapped[k++] : c));
}

/* Stacks by dragging a heading (21 October, from Adam's backlog). A heading let go over the other column's
   lower half stacks the two in one column, the one dropped below, and over its upper half above, the stack
   standing where the column dropped on stood. With the two stacked, the stacked column and the transcript
   are two units in the order, the stack standing where the statements stand: the upper heading or the
   transcript's moves its unit, the lower one let go in a gap stands alone there, and either let go over the
   other's half changes places with it. Above 800px alone, with both shown. Each answers the settings it
   changes, or null for none. */
function stackUnits(order) {
  return order.indexOf('statements') < order.indexOf('transcript') ? ['stack', 'transcript'] : ['transcript', 'stack'];
}
// the units as the three, the stack its upper column then its lower, side by side
const stackExpand = (units, top) => units.flatMap((u) => (u === 'stack' ? [top, STACK_OTHER[top]] : [u]));

/* What a heading let go does: `drop` a gap, `{ kind: 'gap', before, shown }` as the bar at a heading's edge
   marks it, or a half, `{ kind: 'stack', onto, half }`, 'upper' or 'lower' */
function colsDropped(lay, name, drop) {
  if (!lay || !drop) return null;
  const order = lay.order;
  const same = (next) => next.join() === order.join();
  if (lay.stacked) {
    const lower = STACK_OTHER[lay.top];
    if (drop.kind === 'stack') {
      if ((name === lower && drop.half === 'upper') || (name === lay.top && drop.half === 'lower')) return { stack_top: lower };
      return null;
    }
    if (name === lower) {
      return { columns_stacked: false, statements_columns: colsMoved(order, name, drop.before, drop.shown || order) };
    }
    const unit = (c) => (c === 'transcript' ? 'transcript' : c ? 'stack' : null);
    const next = stackExpand(colsMoved(stackUnits(order), unit(name), unit(drop.before)), lay.top);
    return same(next) ? null : { statements_columns: next };
  }
  if (drop.kind === 'stack') {
    if (lay.hidden.length || STACK_OTHER[name] !== drop.onto) return null;
    const rest = order.filter((c) => c !== name);
    rest.splice(rest.indexOf(drop.onto) + (drop.half === 'lower' ? 1 : 0), 0, name);
    return { columns_stacked: true, stack_top: drop.half === 'lower' ? drop.onto : name, statements_columns: rest };
  }
  const next = colsMoved(order, name, drop.before, drop.shown || order);
  return same(next) ? null : { statements_columns: next };
}

/* The heading's menu, for the keyboard and for those who do not drag: Stack under the other column while
   the two stand side by side, Stand alone while they are stacked, and nothing at 800px and below, with a
   column hidden or for the transcript */
function colMenuItems(lay, name, narrow) {
  if (!lay || narrow || !STACK_OTHER[name] || lay.hidden.length) return [];
  if (lay.stacked) return [{ act: 'alone', words: t('distil.cols.stand_alone') }];
  return [{ act: 'under', words: STACK_OTHER[name] === 'notes' ? t('distil.cols.under_notes') : t('distil.cols.under_statements') }];
}
function colMenuChange(lay, name, act) {
  if (act === 'alone') return lay.stacked ? { columns_stacked: false } : null;
  if (act === 'under') return colsDropped(lay, name, { kind: 'stack', onto: STACK_OTHER[name], half: 'lower' });
  return null;
}

/* Reset widths puts every column back alone as well as every edge (21 October): what it changes of the
   stack, the two side by side, the statements above for the next stack and its divider at half */
function stackResetChange(cfg) {
  const out = {};
  if (cfg && cfg.columns_stacked === true) out.columns_stacked = false;
  if (stackTopOf(cfg) !== 'statements') out.stack_top = 'statements';
  if (stackSplitOf(cfg) !== STACK_SPLIT) out.stack_split = STACK_SPLIT;
  return out;
}

/* a passage's notes as its notes column shows them while it is not the current one, read-only and quiet */
function notesHtml(row) {
  return `<div class="turn-notes-text">${esc(row.en || '')}</div>`;
}

/* A passage's statements as its statements column shows them while it is not the current one (17
   October): each numbered as its pair is in the card, read-only, and a click on one goes to the passage
   with the caret in that statement. A pair with a quote and no statement yet shows its quote, so
   every number keeps its place, and a passage with none shows nothing. Each number stands in a dot of
   its statement's colour, as on the card (18 October). */
function statementsHtml(row) {
  const items = rowPairs(row).map((p, n) => {
    const es = p.es.trim();
    const kq = p.kq.trim();
    if (!es && !kq) return '';
    const words = es ? esc(es) : `<span class="es-quote">${esc(kq)}</span>`;
    return `<li><button type="button" tabindex="-1" class="es-go" data-es="${n}" title="${escAttr(t('distil.turn.go_statement'))}">`
      + `<span class="es-n" data-es-colour="${n % 6}">${n + 1}</span><span class="es-words">${words}</span></button></li>`;
  }).join('');
  return items ? `<ol class="es-list">${items}</ol>` : '';
}

/* The screen drawn as the settings say: the columns in their order, the classes, the card and the notes
   field in the current passage's row, and the menus' rows. Called as a case opens, on a choice in a
   menu or by a grip, and on a Save in Settings. */
function drawView() {
  const cfg = viewConfig();
  drawColumns(columnsLayout(cfg));
  $('work').classList.toggle('same-size', !largerPassage(cfg));
  const mm = minimapMode(cfg);
  $('work').classList.toggle('minimap-on', mm !== 'off');
  $('work').classList.toggle('minimap-always', mm === 'on');
  // an opening of his goes with Off
  $('work').classList.toggle('minimap-peek', mm !== 'off' && $('work').classList.contains('minimap-peek'));
  cellsAgain();
  placeCard();
  placeNotes();
  drawViewMenu();
  scheduleMinimap();
  // Quotes on the status bar, whole or folded to a line (21 October)
  if (typeof quotesDraw === 'function') quotesDraw();
}

/* The columns as a layout has them: their places for the stylesheet, the classes for the columns hidden,
   the transcript alone and the notes stacked under the statements, the divider's place, the headings
   moved into the order so Tab and a screen reader meet them as the eye does, each a grip and its name,
   Columns saying the columns shown in its tooltip at their right, and its menu's rows. */
function drawColumns(lay) {
  const order = lay.order;
  S.columns = order;
  S.layout = lay;
  const work = $('work');
  for (const [name, value] of Object.entries(colsVars(order, lay.hidden))) work.style.setProperty(name, value);
  work.classList.toggle('hide-es', lay.hidden.includes('statements'));
  work.classList.toggle('hide-en', lay.hidden.includes('notes'));
  work.classList.toggle('cols-alone', lay.hidden.length === HIDEABLE_COLUMNS.length);
  work.classList.toggle('cols-stacked', lay.stacked);
  work.classList.toggle('stack-notes-top', lay.stacked && lay.top === 'notes');
  drawStack(lay.split);
  const head = $('cols-head');
  for (const c of order) {
    let el = head.querySelector(`.col-head[data-col="${c}"]`);
    if (!el) {
      el = document.createElement('div');
      el.className = 'col-head';
      el.dataset.col = c;
      el.innerHTML = `${gripHtml(COLUMN_WORDS[c])}<span class="field-label col-name">${esc(COLUMN_WORDS[c])}</span>`;
    } else if (el.querySelector('.col-name')) {
      // its name in the words of the method in front (tadraw)
      el.querySelector('.col-name').textContent = COLUMN_WORDS[c];
    }
    head.insertBefore(el, $('cols-pick'));
  }
  $('cols-pick').title = t('distil.cols.title', { shown: columnsShownSaid(lay) });
  if (typeof colMenuClose === 'function') colMenuClose();
  drawColsMenu();
  measureColumns();
}

/* the columns shown in words, as Columns' tooltip says them: "statements, transcript, notes", the
   transcript alone as "transcript", and stacked "statements over notes, transcript" */
function columnsShownSaid(lay) {
  const shown = lay.order.filter((c) => !lay.hidden.includes(c));
  if (!lay.stacked) return columnsSaid(shown);
  const pair = lay.top === 'notes' ? t('distil.cols.notes_over') : t('distil.cols.statements_over');
  return shown.filter((c) => c !== 'notes').map((c) => (c === 'statements' ? pair : columnsSaid([c]))).join(', ');
}

/* The divider's place in the stacked column, the statements' share above it and the notes' below, as
   the grid's two rows and the separator's value say it */
function drawStack(split) {
  const stack = $('stack');
  stack.style.setProperty('--stack-a', `${Math.round(split * 1000)}fr`);
  stack.style.setProperty('--stack-b', `${Math.round((1 - split) * 1000)}fr`);
  $('stack-divider').setAttribute('aria-valuenow', String(Math.round(split * 100)));
}

/* The divider moved, by a drag, the up and down arrows a twentieth of the column at a time, Home and End to
   either end of its range, or a double click back to half, its place kept as Columns keeps a choice. A
   drag draws as it goes and is kept as it is let go. */
const STACK_STEP = 0.05;
const stackClamp = (v) => Math.round(Math.min(STACK_RANGE[1], Math.max(STACK_RANGE[0], v)) * 1000) / 1000;
function stackSplitKeep(value) {
  const split = stackClamp(value);
  drawStack(split);
  if (S.layout) S.layout.split = split;
  if (!S.data || !S.data.config || S.data.config.stack_split === split) return;
  setView('stack_split', split);
}

function stackDividerDown(e) {
  if (e.button !== 0) return;
  e.preventDefault();
  const bar = $('stack-divider');
  const box = $('stack').getBoundingClientRect();
  const room = box.height - bar.offsetHeight;
  if (room <= 0) return;
  const pointer = e.pointerId;
  let split = S.layout ? S.layout.split : STACK_SPLIT;
  bar.classList.add('dragging');
  bar.focus({ preventScroll: true });
  const move = (ev) => {
    if (ev.pointerId !== pointer) return;
    split = stackClamp((ev.clientY - box.top - bar.offsetHeight / 2) / room);
    drawStack(split);
  };
  const end = (ev) => {
    if (ev.pointerId !== pointer) return;
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', end);
    window.removeEventListener('pointercancel', end);
    bar.classList.remove('dragging');
    stackSplitKeep(ev.type === 'pointerup' ? split : (S.layout ? S.layout.split : STACK_SPLIT));
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', end);
  window.addEventListener('pointercancel', end);
}

function stackDividerKeys(e) {
  const now = S.layout ? S.layout.split : STACK_SPLIT;
  const to = { ArrowUp: now - STACK_STEP, ArrowDown: now + STACK_STEP, Home: STACK_RANGE[0], End: STACK_RANGE[1] }[e.key];
  if (to === undefined || MOD(e) || e.altKey) return;
  e.preventDefault();
  e.stopPropagation();
  stackSplitKeep(to);
}

/* Every column edge dragged (20 October, Adam's way C, from a tester's letterbox: on a wide screen the columns
   stopped growing at 1,480 pixels). The outer edge of the first column and of the last, and the edges
   between them, each an edge the pointer finds with the resize cursor and a thin line in the ink, which
   Tab reaches and the left and right arrows move. A drag moves that edge alone, the columns either side
   taking up the room and the transcript the rest, its words then the width of their column. A double click
   puts that edge back where the screen opens. Kept in config.json as `column_widths`, for each width of
   screen, so a laptop and a wide screen keep their own: the first column's distance from the window's left,
   the last one's from its right and the statements', the notes' and the stacked column's widths. A screen
   with none opens as it always has, and Reset widths in Columns' menu and in Settings puts it back. At
   800px and below the edges give way to the narrow layout, and the transcript alone keeps its measure. */
const EDGE_MINS = { statements: 210, notes: 160, stack: 280, transcript: 300 };
const EDGE_STEP = 16;
const EDGE_SLOT = 8;
const EDGES = { drag: null, natural: null, saveTimer: null };
const colsScreen = () => String(Math.round((typeof screen !== 'undefined' && screen.width) || window.innerWidth || 0));
const pageWidth = () => document.documentElement.clientWidth || window.innerWidth;

function widthsHeld(cfg = viewConfig()) {
  const all = cfg && cfg.column_widths;
  const mine = all && typeof all === 'object' ? all[colsScreen()] : null;
  return mine && typeof mine === 'object' && Object.keys(mine).length ? mine : null;
}

// the edges are offered while two columns or more stand side by side above 800px
const edgesOffered = () => !!S.layout && !colsNarrow() && S.layout.hidden.length < HIDEABLE_COLUMNS.length && !$('work').hidden;

// a heading's width key: the upper column's heading stands over the stacked column while the two are stacked
const edgeKey = (name) => (name === 'transcript' ? null : (stackedNow() && name === S.layout.top ? 'stack' : name));

/* The columns as they stand, measured: each shown column's name and box, left to right, and what lies
   between the window's edges and the columns that no width changes, the headings' padding and the
   transcript's scrollbar, `inL` and `inR`. */
function edgeColumns() {
  const reading = document.querySelector('#work .reading');
  const box = reading.getBoundingClientRect();
  const css = getComputedStyle(reading);
  const heads = colsShown().map((h) => ({ name: h.dataset.col, box: h.getBoundingClientRect() }))
    .sort((a, b) => a.box.left - b.box.left);
  if (!heads.length) return null;
  const contentL = box.left + parseFloat(css.paddingLeft);
  const contentR = box.right - parseFloat(css.paddingRight);
  return { heads, inL: heads[0].box.left - contentL, inR: contentR - heads[heads.length - 1].box.right };
}

/* The geometry the screen opens with at this width, measured with the widths taken off for a moment */
function edgesNatural() {
  const work = $('work');
  const had = work.classList.contains('cols-sized');
  const kept = {};
  for (const v of ['--es-track', '--en-track', '--st-track', '--tx-track', '--read-l', '--read-r']) {
    kept[v] = work.style.getPropertyValue(v);
    work.style.removeProperty(v);
  }
  work.classList.remove('cols-sized');
  const cols = edgeColumns();
  if (had) work.classList.add('cols-sized');
  for (const [v, value] of Object.entries(kept)) if (value) work.style.setProperty(v, value);
  if (!cols) return null;
  const heads = cols.heads;
  const out = { left: heads[0].box.left, right: pageWidth() - heads[heads.length - 1].box.right, inL: cols.inL, inR: cols.inR,
    order: heads.map((h) => h.name), widths: {} };
  for (const h of heads) if (edgeKey(h.name)) out.widths[edgeKey(h.name)] = h.box.width;
  // a column hidden now still has the width it opens with, so it comes back where it would stand
  return out;
}

const colGap = () => parseFloat(getComputedStyle($('work')).getPropertyValue('--col-gap')) || 28;

/* A model of the edges, `left`, `right` and each side column's width, from what is held over what the
   screen opens with, and the transcript's width from what is left */
function edgesModel(nat, held) {
  const m = { left: nat.left, right: nat.right, widths: Object.assign({}, nat.widths) };
  if (held) {
    if (Number.isFinite(held.left)) m.left = held.left;
    if (Number.isFinite(held.right)) m.right = held.right;
    for (const k of ['statements', 'notes', 'stack']) if (Number.isFinite(held[k]) && k in m.widths) m.widths[k] = held[k];
  }
  return m;
}

function edgesTx(m, nat) {
  const sides = nat.order.reduce((a, c) => a + (edgeKey(c) ? m.widths[edgeKey(c)] : 0), 0);
  return pageWidth() - m.left - m.right - sides - colGap() * (nat.order.length - 1);
}

const edgesFit = (m, nat) => m.left >= nat.inL + 8 && m.right >= nat.inR + 8 && edgesTx(m, nat) >= EDGE_MINS.transcript
  && nat.order.every((c) => !edgeKey(c) || m.widths[edgeKey(c)] >= EDGE_MINS[edgeKey(c)]);

/* A model held on a narrower window than it was made on: the margins give first, then the side columns,
   each down to its least, so the transcript keeps its 300 pixels. Nothing of this is kept. */
function edgesSqueezed(m, nat) {
  const out = { left: m.left, right: m.right, widths: Object.assign({}, m.widths) };
  let short = EDGE_MINS.transcript - edgesTx(out, nat);
  if (short <= 0) return out;
  const lMin = nat.inL + 8;
  const rMin = nat.inR + 8;
  const room = Math.max(0, out.left - lMin) + Math.max(0, out.right - rMin);
  if (room > 0) {
    const take = Math.min(short, room);
    const fromL = take * Math.max(0, out.left - lMin) / room;
    out.left -= fromL;
    out.right -= take - fromL;
    short -= take;
  }
  if (short <= 0) return out;
  const keys = nat.order.map(edgeKey).filter(Boolean);
  const spare = keys.reduce((a, k) => a + Math.max(0, out.widths[k] - EDGE_MINS[k]), 0);
  if (spare > 0) {
    const take = Math.min(short, spare);
    for (const k of keys) out.widths[k] -= take * Math.max(0, out.widths[k] - EDGE_MINS[k]) / spare;
  }
  return out;
}

/* Edge `k` moved by `dx` pixels: 0 is the first column's outer edge, the last the last one's, and the rest
   lie between two columns. The columns either side take up the room, the transcript the rest. */
function edgeShifted(m, nat, k, dx) {
  const out = { left: m.left, right: m.right, widths: Object.assign({}, m.widths) };
  const order = nat.order;
  const n = order.length;
  const grow = (name, by) => { const key = edgeKey(name); if (key) out.widths[key] += by; };
  if (k === 0) { out.left += dx; grow(order[0], -dx); }
  else if (k === n) { out.right -= dx; grow(order[n - 1], dx); }
  else { grow(order[k - 1], dx); grow(order[k], -dx); }
  return out;
}

// the move as far towards `dx` as every column's least width and the window's edges allow
function edgeMove(m, nat, k, dx) {
  if (edgesFit(edgeShifted(m, nat, k, dx), nat)) return edgeShifted(m, nat, k, dx);
  let lo = 0;
  let hi = 1;
  for (let i = 0; i < 18; i += 1) {
    const mid = (lo + hi) / 2;
    if (edgesFit(edgeShifted(m, nat, k, dx * mid), nat)) lo = mid; else hi = mid;
  }
  return edgeShifted(m, nat, k, Math.trunc(dx * lo));
}

// edge `k` alone back where the screen opens, the double click's
function edgeHome(m, nat, k) {
  const dx = edgesAt(nat, nat)[k] - edgesAt(m, nat)[k];
  return Math.abs(dx) < 1 ? m : edgeMove(m, nat, k, dx);
}

/* What is kept for this screen from a model: the margins and the widths of the columns shown, with what
   was held for a column hidden now, or null when every edge stands where the screen opens */
function edgesKept(m, nat, held) {
  const next = Object.assign({}, held || {}, { left: Math.round(m.left), right: Math.round(m.right) });
  for (const [k, v] of Object.entries(m.widths)) next[k] = Math.round(v);
  const same = Math.abs(next.left - nat.left) <= 1 && Math.abs(next.right - nat.right) <= 1
    && Object.entries(nat.widths).every(([k, v]) => Math.abs(next[k] - v) <= 1)
    && Object.keys(next).every((k) => ['left', 'right'].includes(k) || k in nat.widths);
  return same ? null : next;
}

/* What an edge's drawing needs besides its place (6 November, the handle): whether it lies between two columns, `between`,
   where the rule and the pill are and the outer two, the margins, are not, and `mid`, the middle of the columns' visible
   height from the edge's top, `top` being the headings' top and the body's top and foot where the columns scroll */
function edgePlace(k, n, top, bodyTop, bodyBottom) {
  return { between: k > 0 && k < n, mid: Math.round((bodyTop + bodyBottom) / 2 - top) };
}

// each edge's place across the window, the outer two at the columns' outer edges, the rest in the gaps
function edgesAt(m, nat) {
  const gap = colGap();
  const xs = [m.left];
  let x = m.left;
  nat.order.forEach((c, i) => {
    x += edgeKey(c) ? m.widths[edgeKey(c)] : edgesTx(m, nat);
    xs.push(i === nat.order.length - 1 ? x : x + gap / 2);
    x += gap;
  });
  return xs;
}

/* The widths drawn: the reading area's margins from the window's edges, each side column's track in
   pixels and the transcript's the rest, with the class that lets the transcript's words run its width.
   None held, or the edges not offered, and the screen stands as it always has. */
function edgesApply(m) {
  const work = $('work');
  const nat = EDGES.natural;
  if (!m || !nat) {
    work.classList.remove('cols-sized');
    for (const v of ['--es-track', '--en-track', '--st-track', '--tx-track', '--read-l', '--read-r']) work.style.removeProperty(v);
    return;
  }
  const s = edgesSqueezed(m, nat);
  work.classList.add('cols-sized');
  work.style.setProperty('--read-l', `${Math.round(s.left - nat.inL)}px`);
  work.style.setProperty('--read-r', `${Math.round(s.right - nat.inR)}px`);
  const track = { statements: '--es-track', notes: '--en-track', stack: '--st-track' };
  for (const [k, v] of Object.entries(track)) {
    if (k in s.widths) work.style.setProperty(v, `${Math.round(s.widths[k])}px`);
    else work.style.removeProperty(v);
  }
  work.style.setProperty('--tx-track', `minmax(${EDGE_MINS.transcript}px, 1fr)`);
}

/* The widths as held for this screen drawn, and the edges placed over the columns, called whenever the
   columns are measured */
function edgesDraw() {
  const box = $('col-edges');
  if (!box) return;
  if (!edgesOffered()) {
    EDGES.natural = null;
    edgesApply(null);
    box.hidden = true;
    return;
  }
  if (!EDGES.drag) {
    EDGES.natural = edgesNatural();
    if (!EDGES.natural) { box.hidden = true; return; }
    const held = widthsHeld();
    edgesApply(held ? edgesModel(EDGES.natural, held) : null);
  }
  const nat = EDGES.natural;
  const cols = edgeColumns();
  if (!cols) { box.hidden = true; return; }
  box.hidden = false;
  const n = nat.order.length;
  while (box.children.length > n + 1) box.lastElementChild.remove();
  while (box.children.length < n + 1) {
    const el = document.createElement('div');
    el.className = 'col-edge';
    el.tabIndex = 0;
    el.setAttribute('role', 'separator');
    el.setAttribute('aria-orientation', 'vertical');
    el.title = t('distil.cols.edge_title');
    box.appendChild(el);
  }
  const heads = cols.heads;
  const gap = colGap();
  const xs = [heads[0].box.left - EDGE_SLOT / 2];
  heads.forEach((h, i) => xs.push(i === n - 1 ? h.box.right + EDGE_SLOT / 2 : h.box.right + gap / 2));
  const top = $('cols-head').getBoundingClientRect().top;
  const body = $('cols-body').getBoundingClientRect();
  const reading = document.querySelector('#work .reading').getBoundingClientRect();
  [...box.children].forEach((el, k) => {
    el.dataset.edge = String(k);
    el.style.left = `${Math.round(xs[k] - reading.left - EDGE_SLOT / 2)}px`;
    el.style.top = `${Math.round(top - reading.top)}px`;
    el.style.height = `${Math.round(body.bottom - top)}px`;
    const place = edgePlace(k, n, top, body.top, body.bottom);
    el.classList.toggle('between', place.between);
    el.style.setProperty('--edge-mid', `${place.mid}px`);
    const said = k === 0 ? t('distil.cols.edge_outer', { column: COLUMN_WORDS[heads[0].name] })
      : k === n ? t('distil.cols.edge_outer', { column: COLUMN_WORDS[heads[n - 1].name] })
        : t('distil.cols.edge_between', { left: COLUMN_WORDS[heads[k - 1].name], right: COLUMN_WORDS[heads[k].name] });
    el.setAttribute('aria-label', t('distil.cols.edge_label', { said }));
  });
  drawWidthsReset();
}

// the edges' model now: what is held for this screen over what it opens with
const edgesNow = () => (EDGES.natural ? edgesModel(EDGES.natural, widthsHeld()) : null);

// a model kept for this screen (see edgesKept)
function edgesKeep(m) {
  if (EDGES.natural) widthsSave(edgesKept(m, EDGES.natural, widthsHeld()));
}

function widthsSave(widths) {
  const cfg = viewConfig();
  if (!cfg) return;
  const screenKey = colsScreen();
  const all = Object.assign({}, cfg.column_widths || {});
  delete all[screenKey];
  if (widths) all[screenKey] = widths;
  for (const c of [cfg, S.data && S.data.config, S.libConfig, typeof TH !== 'undefined' ? TH.config : null]) if (c) c.column_widths = all;
  measureColumns();
  drawWidthsReset();
  clearTimeout(EDGES.saveTimer);
  EDGES.saveTimer = setTimeout(() => {
    api('/api/settings', { column_widths: { screen: screenKey, widths } }).then((data) => {
      if (!data.config || data.config.column_widths === undefined) say(RESTART_LINE, 9000);
    }).catch((err) => say(needsRestart(err) ? RESTART_LINE : err.message, 9000));
  }, 250);
}

/* Reset widths, in Columns' menu and in Settings: every edge back where the screen opens, on this screen,
   and since 21 October every column back alone, a stack standing side by side again, the statements above
   for the next stack and its divider at half. Settings' Statements and notes say so at once, so its Save
   never stacks them again. */
function widthsReset() {
  const stack = stackResetChange(viewConfig());
  if (!widthsHeld() && !('columns_stacked' in stack)) return;
  colsMenu(false);
  if (Object.keys(stack).length) {
    setViews(stack);
    if ($('set-side')) colsStackRows($('set-side'), $('set-stacked'), false, !$('set-side').disabled);
    if ($('set-stacked-word')) $('set-stacked-word').textContent = stackedWords('statements');
    if (S.viewOpened) S.viewOpened.columns_stacked = false;
  }
  if (widthsHeld()) widthsSave(null);
  if (!$('work').hidden && current()) centreCurrent(false);
}

// Reset widths faint while every edge stands where the screen opens and no column is stacked, in the menu
// and in Settings
function drawWidthsReset() {
  const cfg = viewConfig();
  const none = !widthsHeld() && !(cfg && cfg.columns_stacked === true);
  for (const id of ['cols-widths', 'set-widths-reset']) if ($(id)) $(id).disabled = none;
}

function edgeDown(e) {
  const el = e.target.closest('.col-edge');
  if (!el || e.button !== 0 || !EDGES.natural) return;
  e.preventDefault();
  const k = Number(el.dataset.edge);
  const from = edgesNow();
  const startX = e.clientX;
  const pointer = e.pointerId;
  let now = from;
  EDGES.drag = { k };
  el.classList.add('dragging');
  document.body.classList.add('edge-dragging');
  const move = (ev) => {
    if (ev.pointerId !== pointer) return;
    now = edgeMove(from, EDGES.natural, k, ev.clientX - startX);
    edgesApply(now);
    edgesDraw();
  };
  const end = (ev) => {
    if (ev.pointerId !== pointer) return;
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', end);
    window.removeEventListener('pointercancel', end);
    el.classList.remove('dragging');
    document.body.classList.remove('edge-dragging');
    EDGES.drag = null;
    if (ev.type === 'pointerup' && Math.abs(ev.clientX - startX) >= 1) edgesKeep(now);
    else edgesDraw();
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', end);
  window.addEventListener('pointercancel', end);
}

// a double click on an edge puts that edge alone back where the screen opens
function edgeBack(e) {
  const el = e.target.closest('.col-edge');
  if (!el || !EDGES.natural) return;
  const m = edgesNow();
  const back = edgeHome(m, EDGES.natural, Number(el.dataset.edge));
  if (back !== m) edgesKeep(back);
}

function edgeKeys(e) {
  const el = e.target.closest('.col-edge');
  if (!el || !EDGES.natural || MOD(e) || e.altKey) return;
  const dx = { ArrowLeft: -EDGE_STEP, ArrowRight: EDGE_STEP }[e.key];
  if (dx === undefined) return;
  e.preventDefault();
  e.stopPropagation();
  const k = Number(el.dataset.edge);
  edgesKeep(edgeMove(edgesNow(), EDGES.natural, k, e.shiftKey ? dx * 4 : dx));
  const again = $('col-edges').querySelector(`[data-edge="${k}"]`);
  if (again) again.focus({ preventScroll: true });
}

/* What the stylesheet cannot know, measured as the screen stands: the room the transcript's scrollbar
   takes, which the headings leave at their right so each stands over its column, the last heading on
   screen, which leaves room for Columns, the place of the count over the transcript's column, and where
   the guidance's sheet stands. At a desk width it lies over the last column whole, its left edge at the
   column's, where that column is 300 pixels or more, and else it is 340 pixels with the rest of the
   screen under a wash of the paper, so no strip of a column's words is ever cut at its edge. */
const GUIDE_WHOLE = 300;
function measureColumns() {
  const work = $('work');
  if (work.hidden) return;
  // a long passage's caps for the column's new size (cardlarge), and the columns' widths moved the quotes, so
  // each statement's box goes level with its own again
  reachDraw();
  if (typeof levelSoon === 'function') levelSoon();
  const col = $('transcript');
  work.style.setProperty('--sb', `${Math.max(0, col.offsetWidth - col.clientWidth)}px`);
  // the widths held for this screen first, and the edges over the columns (20 October)
  edgesDraw();
  const shown = [...$('cols-head').querySelectorAll('.col-head')].filter((h) => h.getClientRects().length);
  const last = shown[shown.length - 1];
  // Columns says its word alone at every width, the order in its tooltip and its menu, where until 18
  // October it said the order beside its word where the last heading left the room, which only the
  // transcript's heading at 800px did. The name is measured before the room for Columns is taken from
  // its heading
  for (const h of $('cols-head').querySelectorAll('.col-head')) h.classList.remove('col-last');
  const name = last ? last.querySelector('.col-name') : null;
  work.classList.remove('cols-tight');
  // and where the last heading's longest word would not stand whole beside Columns' word, Columns keeps its
  // chevron alone, its word in its tooltip, so no name is ever cut through a letter
  if (last && name) {
    const word = name.textContent.split(' ').reduce((a, b) => (b.length > a.length ? b : a), '');
    const probe = document.createElement('span');
    probe.className = 'field-label col-name';
    probe.style.cssText = 'position: absolute; visibility: hidden; white-space: nowrap;';
    probe.textContent = word;
    last.appendChild(probe);
    const room = last.getBoundingClientRect().width - (name.getBoundingClientRect().left - last.getBoundingClientRect().left)
      - $('cols-pick').offsetWidth - 12;
    work.classList.toggle('cols-tight', probe.offsetWidth > room);
    probe.remove();
  }
  if (last) last.classList.add('col-last');
  work.style.setProperty('--pick-w', `${$('cols-pick').offsetWidth + 12}px`);
  const tx = shown.find((h) => h.dataset.col === 'transcript');
  const wrap = col.parentElement.getBoundingClientRect();
  if (tx) {
    const box = tx.getBoundingClientRect();
    work.style.setProperty('--flash-x', `${Math.round(box.left + box.width / 2 - wrap.left)}px`);
  } else work.style.removeProperty('--flash-x');
  const edge = last ? last.getBoundingClientRect() : null;
  const whole = !!edge && shown.length > 1 && window.innerWidth > MINIMAP_NARROW && edge.width >= GUIDE_WHOLE;
  work.classList.toggle('guide-whole', whole);
  if (whole) work.style.setProperty('--guide-w', `${Math.ceil(window.innerWidth - edge.left + 14)}px`);
}

/* The current passage's card in its statements column (17 October), the way its notes field stands in
   its notes column: one card for every passage, so its saving, its undo, Tab and Cmd + Enter never know
   where it stands. The passage it stood in first takes its statements back as words. */
function placeCard() {
  const cell = cardCell();
  if (!cell) { parkCard(); return; }
  const card = $('es-card');
  if (card.parentElement === cell) return;
  parkCard();
  cell.replaceChildren(card);
  growPairs();
  footStuck();
  if (typeof levelSoon === 'function') levelSoon();
}

/* Where the current passage's card and its notes field stand (18 October): in its row's statements and
   notes cells, in the stacked column's two halves while the notes stand under the statements, and in the
   park, out of sight and with their words kept, while their column is hidden or no passage is current. */
function cardCell() {
  if (colsHidden('statements')) return null;
  const cell = $('transcript-rows').querySelector('.turn.current .turn-es');
  return cell && stackedNow() ? $('stack-es') : cell;
}
function notesCell() {
  if (colsHidden('notes')) return null;
  const cell = $('transcript-rows').querySelector('.turn.current .turn-notes');
  return cell && stackedNow() ? $('stack-en-cell') : cell;
}

/* Every passage's statements and notes cells drawn again from what is saved, but the cells holding the
   card or the notes field, as the screen is drawn again. While the card stood in the stacked column or
   the park, the passages it left kept the words their cells had, so a column shown again or the notes
   back beside the words shows each passage as saved. */
function cellsAgain() {
  const card = $('es-card');
  const field = $('en');
  for (const holder of $('transcript-rows').querySelectorAll('.turn')) {
    const row = (S.flat || [])[Number(holder.dataset.i)];
    if (!row || !row.stop) continue;
    const es = holder.querySelector('.turn-es');
    const en = holder.querySelector('.turn-notes:not(.note-cell)');
    if (es && !es.contains(card)) es.innerHTML = statementsHtml(row);
    if (en && !en.contains(field)) en.innerHTML = notesHtml(row);
  }
}

/* The card's foot marked `stuck` while it keeps to the column's foot with more of the card below it
   (18 October), so it ends the card there with the row's paper under it and the fields above fading
   into it. Run on every scroll of the column and every change to its size or the card's. */
function footStuck() {
  const card = $('es-card');
  const foot = card.querySelector('.es-foot');
  if (!foot) return;
  // a card held in view scrolls inside itself, its foot kept to its own foot while more of it waits below
  // (cardlarge)
  const held = $('work').classList.contains('reach-hold') && !!card.closest('.reach-long');
  const stuck = !!card.closest('.turn-es, .stack-es') && (held
    ? card.scrollTop + card.clientHeight < card.scrollHeight - 1
    : card.getBoundingClientRect().bottom - foot.getBoundingClientRect().bottom > 1);
  if (foot.classList.contains('stuck') !== stuck) foot.classList.toggle('stuck', stuck);
  stackFade();
}

/* A stacked half with more of it above or below its edge fades there (21 October), as the transcript's
   column and the search's results do, so a card cut at the half's foot says the half scrolls. Below, with
   the card's foot kept at the half's foot, the fade ends just over the foot and the foot stays whole. */
function stackFade() {
  for (const half of [$('stack-es'), $('stack-en')]) {
    if (!half) continue;
    const on = !!half.getClientRects().length;
    const above = on && half.scrollTop > 1;
    const below = on && half.scrollTop + half.clientHeight < half.scrollHeight - 1;
    if (below) {
      const foot = half.querySelector('.es-foot.stuck');
      const h = foot ? Math.round(half.getBoundingClientRect().bottom - foot.getBoundingClientRect().top) : -2;
      half.style.setProperty('--fade-foot', `${h}px`);
    }
    half.classList.toggle('more-above', above);
    half.classList.toggle('more-below', below);
  }
}

/* the card back where it waits, before the column is drawn again and whenever no passage holds it, and
   the passage it stood in showing its statements as the rest do */
function parkCard() {
  const card = $('es-card');
  const park = $('es-park');
  if (card.parentElement === park) return;
  const cell = card.closest('.turn-es');
  park.prepend(card);
  const holder = cell ? cell.closest('.turn') : null;
  const row = holder ? S.flat[Number(holder.dataset.i)] : null;
  if (cell && row) cell.innerHTML = statementsHtml(row);
}

/* The one notes field in the current passage's notes column, under the column's heading. It is the same
   field for every passage, so its saving, its undo, Tab and Cmd + Enter never know where it stands. */
function placeNotes() {
  const cell = notesCell();
  if (!cell) { parkNotes(); return; }
  const field = $('en');
  if (field.parentElement === cell) return;
  // the passage it stood beside first takes its notes back as text
  parkNotes();
  cell.replaceChildren(field);
  growNotes();
}

/* the field back where it waits, before the column is drawn again and whenever no passage holds it */
function parkNotes() {
  const field = $('en');
  const park = $('es-park');
  if (field.parentElement === park) return;
  const cell = field.closest('.turn-notes');
  park.appendChild(field);
  // the passage it stood beside shows its notes as the rest do
  const holder = cell ? cell.closest('.turn') : null;
  const row = holder ? S.flat[Number(holder.dataset.i)] : null;
  if (cell && row) cell.innerHTML = notesHtml(row);
}

/* The notes field starts about five lines tall and grows with its words as the card grows with its pairs,
   never a box that scrolls inside, so a note longer than the passage beside it takes the room it needs and
   the row grows with it (18 October, Adam's word, where it started at two lines and a long note felt cramped).
   Its lines measured in its own face, its padding and its edge added. */
const NOTES_LINES = 5;
function growNotes() {
  const field = $('en');
  // in the stacked column it fills its half and scrolls there, so it takes no height of its own (18 October)
  if (field.closest('#stack')) { field.style.height = ''; return; }
  const style = getComputedStyle(field);
  const line = parseFloat(style.lineHeight) || 20;
  const pad = (parseFloat(style.paddingTop) || 0) + (parseFloat(style.paddingBottom) || 0);
  const edge = (parseFloat(style.borderTopWidth) || 0) + (parseFloat(style.borderBottomWidth) || 0);
  field.style.height = 'auto';
  field.style.height = `${Math.ceil(Math.max(field.scrollHeight + edge, NOTES_LINES * line + pad + edge))}px`;
}

/* The View menu, under its button on the bar: the larger current passage as a tick and the minimap's
   three as radio rows, each from its whole row. Each change is drawn at once and kept, and the menu
   stays open on it. Esc closes it, and so does a click anywhere else. */
function viewMenu(open) {
  const menu = $('view-menu');
  menu.hidden = !open;
  $('btn-view').setAttribute('aria-expanded', String(!!open));
  if (!open) return;
  drawViewMenu();
  const box = $('btn-view').getBoundingClientRect();
  menu.style.left = `${Math.max(8, Math.min(box.right - menu.offsetWidth, window.innerWidth - menu.offsetWidth - 8))}px`;
  menu.style.top = `${box.bottom + 8}px`;
}

/* Columns' menu, under its button at the headings' right, as Adam's drawing of 18 October has it: Show,
   a tick for the statements and one for the notes, then Side by side or Stacked, notes under statements,
   offered while both are shown, then Back to the book's order, where until then it listed the six orders.
   Each row from its whole row, each change drawn at once and kept, the menu staying open on it as View's
   does, and the one action closing it. Opened from the keyboard, the first tick takes the focus and Tab
   keeps to the menu. Where it would leave a strip of the last column showing beside it, less than half
   its own width, it takes that column's whole width, so no sliver of the notes field stands at its left
   (18 October). */
function colsMenu(open, keys = false) {
  const menu = $('cols-menu');
  menu.hidden = !open;
  $('cols-pick').setAttribute('aria-expanded', String(!!open));
  if (!open) return;
  drawColsMenu();
  colsMenuPlace();
  if (keys) $('cols-show-statements').focus();
}

function colsMenuPlace() {
  const menu = $('cols-menu');
  if (menu.hidden) return;
  menu.style.minWidth = '';
  const box = $('cols-pick').getBoundingClientRect();
  const last = $('cols-head').querySelector('.col-head.col-last');
  if (last) {
    const strip = box.right - menu.offsetWidth - last.getBoundingClientRect().left;
    if (strip > 0 && strip < menu.offsetWidth / 2) menu.style.minWidth = `${Math.ceil(box.right - last.getBoundingClientRect().left)}px`;
  }
  menu.style.left = `${Math.max(8, Math.min(box.right - menu.offsetWidth, window.innerWidth - menu.offsetWidth - 8))}px`;
  menu.style.top = `${box.bottom + 6}px`;
}

/* Columns' menu as the layout stands: a tick for each column shown, Side by side or Stacked checked as
   chosen and offered while both are shown, its row faint while it is not, the choice kept for when both
   are shown again, and Back to the book's order offered while the order is another. */
function drawColsMenu() {
  const lay = S.layout || columnsLayout(null);
  $('cols-show-statements').checked = !lay.hidden.includes('statements');
  $('cols-show-notes').checked = !lay.hidden.includes('notes');
  colsStackRows($('cols-side'), $('cols-stacked'), lay.chose, !lay.hidden.length);
  if ($('cols-stacked-word')) $('cols-stacked-word').textContent = stackedWords(lay.top);
  // the book's order puts the statements back above the notes in a stack (21 October)
  $('cols-book').disabled = (S.columns || COLUMNS).join() === COLUMNS.join() && !(lay.stacked && lay.top === 'notes');
  if (typeof drawWidthsReset === 'function') drawWidthsReset();
}

// the two rows of Side by side and Stacked, checked as chosen, and offered, or faint and not, as both columns
// are shown, in Columns' menu and Settings' View alike
function colsStackRows(side, stacked, chose, offered) {
  side.checked = !chose;
  stacked.checked = chose;
  for (const input of [side, stacked]) {
    input.disabled = !offered;
    input.closest('label').classList.toggle('row-off', !offered);
  }
}

// the columns hidden as the two ticks say, the statements, the notes or both
const colsTicked = (statements, notes) => HIDEABLE_COLUMNS.filter((c, k) => !(k ? notes : statements).checked);

/* Tab and Shift + Tab keep to Columns' menu while it is open, round its ticks, the checked choice of the
   two, as a radio group takes one stop, and its action while it is offered */
function colsMenuKeys(e) {
  if (e.key !== 'Tab') return;
  const menu = $('cols-menu');
  const radios = [...menu.querySelectorAll('input[type="radio"]:not(:disabled)')];
  const stop = radios.find((r) => r.checked) || radios[0];
  const stops = [...menu.querySelectorAll('input[type="checkbox"], input[type="radio"], button')]
    .filter((el) => !el.disabled && (el.type !== 'radio' || el === stop));
  if (!stops.length) return;
  e.preventDefault();
  e.stopPropagation();
  const at = stops.indexOf(document.activeElement);
  const to = at < 0 ? 0 : (at + (e.shiftKey ? stops.length - 1 : 1)) % stops.length;
  stops[to].focus();
}

/* Back to the book's order, the menu's one action: the order the book's, statements, transcript, notes,
   and since 21 October in a stack the statements above the notes, the columns hidden and the stacking left
   as they are, and the menu closed, the focus back on Columns */
function colsBookOrder() {
  colsMenu(false);
  $('cols-pick').focus();
  const flip = !!(S.layout && S.layout.stacked && S.layout.top === 'notes');
  const moved = (S.columns || COLUMNS).join() !== COLUMNS.join();
  if (flip) setViews(Object.assign({ stack_top: 'statements' }, moved ? { statements_columns: COLUMNS.slice() } : {}));
  else if (moved) setView('statements_columns', COLUMNS.slice());
}

/* the four as View under Distil in Settings holds them, the columns shown, the statements and notes side by
   side or stacked, and the two choices, where until 18 October the columns' six orders stood first, and
   since 19 October the PETs and GETs boards' status bar, under View in the PETs category */
const viewChoice = () => ({
  columns_hidden: colsTicked($('set-show-statements'), $('set-show-notes')),
  columns_stacked: $('set-stacked').checked,
  larger_passage: $('set-larger').checked,
  minimap: MINIMAP_MODES.find((m) => $(`set-minimap-${m}`).checked) || 'auto',
  status_bar: $('set-status-bar').checked,
});

function drawViewMenu() {
  const cfg = viewConfig();
  $('view-larger').checked = largerPassage(cfg);
  for (const m of MINIMAP_MODES) $(`view-minimap-${m}`).checked = minimapMode(cfg) === m;
}

/* The columns shown and the stacking as Settings' View holds them, the same as Columns' menu, Stacked
   offered while both ticks stand (18 October, where the columns' six orders stood in a list here). A tick
   changed in the card offers or takes back Stacked at once, and Save keeps them. */
function fillColumnsSet(lay) {
  $('set-show-statements').checked = !lay.hidden.includes('statements');
  $('set-show-notes').checked = !lay.hidden.includes('notes');
  colsStackRows($('set-side'), $('set-stacked'), lay.chose, !lay.hidden.length);
  if ($('set-stacked-word')) $('set-stacked-word').textContent = stackedWords(lay.top);
  if (typeof drawWidthsReset === 'function') drawWidthsReset();
}

function colsSetTicked() {
  const offered = !colsTicked($('set-show-statements'), $('set-show-notes')).length;
  colsStackRows($('set-side'), $('set-stacked'), $('set-stacked').checked, offered);
}

/* A column's grip moves its column, a drag by the pointer or Alt and an arrow from the keyboard, as a
   row's grip moves its row elsewhere in the app (12 October): the drag marks where it goes with a bar at
   a heading's edge, the nearest to the pointer, as Sift's headings do, and a let go there moves it, the
   order kept as Columns keeps it. */
function colsShown() {
  return [...$('cols-head').querySelectorAll('.col-head')].filter((h) => h.getClientRects().length);
}

function colsGaps() {
  const heads = colsShown();
  const gaps = heads.map((h) => ({ x: h.getBoundingClientRect().left, before: h.dataset.col, head: h, side: 'before' }));
  const last = heads[heads.length - 1];
  if (last) gaps.push({ x: last.getBoundingClientRect().right, before: null, head: last, side: 'after' });
  return gaps;
}

/* Where a heading let go would stack (21 October): the other column of the two that stack, its heading's
   width from the top of the headings to the foot of the columns, both halves offered, and with the two
   stacked the stacked column, the lower one's heading offered its upper half and the upper one's its lower.
   Null at 800px and below, with a column hidden, for the transcript and for a heading over its own place. */
function colsStackZone(name) {
  const lay = S.layout;
  if (!lay || colsNarrow() || lay.hidden.length || !STACK_OTHER[name]) return null;
  const top = $('cols-head').getBoundingClientRect().top;
  if (lay.stacked) {
    const box = $('stack').getBoundingClientRect();
    if (!box.width) return null;
    return { left: box.left, right: box.right, top, bottom: box.bottom, onto: lay.top,
      halves: [name === lay.top ? 'lower' : 'upper'] };
  }
  const head = $('cols-head').querySelector(`.col-head[data-col="${STACK_OTHER[name]}"]`);
  if (!head || !head.getClientRects().length) return null;
  const box = head.getBoundingClientRect();
  return { left: box.left, right: box.right, top, bottom: $('cols-body').getBoundingClientRect().bottom,
    onto: STACK_OTHER[name], halves: ['upper', 'lower'] };
}

/* Where the two would meet in a column (21 October): the gap between two of its cards, lines or fields
   nearest its middle, so the line drawn there never runs through words. Each thing that holds words in
   the column's width is a block, the blocks that touch or overlap are one, and the middle of each space
   between two is a gap. With no gap away from the column's ends, its middle. */
const SPLIT_BLOCKS = '.col-head, .pair, .es-foot, .ai-block, .stale:not([hidden]), .es-list > li, .turn-notes-text, '
  + '.note-cell, #en, .stack-head, .stack-divider';
function colsSplit(zone) {
  const mid = (zone.top + zone.bottom) / 2;
  const spans = [];
  for (const el of document.querySelectorAll(SPLIT_BLOCKS)) {
    if (el.closest('#es-park')) continue;
    const r = el.getBoundingClientRect();
    if (!r.height || !r.width || r.right <= zone.left || r.left >= zone.right) continue;
    if (r.bottom <= zone.top || r.top >= zone.bottom) continue;
    spans.push([Math.max(r.top, zone.top), Math.min(r.bottom, zone.bottom)]);
  }
  spans.sort((a, b) => a[0] - b[0]);
  const merged = [];
  for (const sp of spans) {
    const last = merged[merged.length - 1];
    if (last && sp[0] <= last[1]) last[1] = Math.max(last[1], sp[1]);
    else merged.push([...sp]);
  }
  let best = null;
  for (let i = 1; i < merged.length; i++) {
    const y = (merged[i - 1][1] + merged[i][0]) / 2;
    if (y < zone.top + 40 || y > zone.bottom - 40) continue;
    if (best === null || Math.abs(y - mid) < Math.abs(best - mid)) best = y;
  }
  return best === null ? mid : best;
}

// the drop under the pointer: a half of the column it would stack with, or else the nearest gap, as before
const STACK_INSET = 16;
function colsDropAt(name, x, y) {
  const zone = colsStackZone(name);
  if (zone && x >= zone.left + STACK_INSET && x <= zone.right - STACK_INSET && y >= zone.top && y <= zone.bottom) {
    zone.split = colsSplit(zone);
    const half = y < zone.split ? 'upper' : 'lower';
    return zone.halves.includes(half) ? { kind: 'stack', onto: zone.onto, half, zone } : null;
  }
  const gap = colsGaps().reduce((best, g) => (!best || Math.abs(g.x - x) < Math.abs(best.x - x) ? g : best), null);
  return gap ? { kind: 'gap', before: gap.before, gap, shown: colsShown().map((h) => h.dataset.col) } : null;
}

/* The drop marked: a bar in the ink at a heading's edge for a gap, and for a stack a box in the ink round
   the column it would stack with, its heading and all, the half it would take in a faint tint of the ink
   with a line in the ink where the two would meet, in a gap between its cards (colsSplit) */
function colsMark(drop) {
  for (const h of $('cols-head').querySelectorAll('.col-head')) h.classList.remove('drop-before', 'drop-after');
  const mark = $('stack-drop');
  if (drop && drop.gap) drop.gap.head.classList.add(`drop-${drop.gap.side}`);
  if (!mark) return;
  if (!drop || drop.kind !== 'stack') { mark.hidden = true; return; }
  const z = drop.zone;
  const reading = document.querySelector('#work .reading').getBoundingClientRect();
  mark.style.left = `${Math.round(z.left - reading.left - 16)}px`;
  mark.style.width = `${Math.round(z.right - z.left + 32)}px`;
  mark.style.top = `${Math.round(z.top - reading.top)}px`;
  mark.style.height = `${Math.round(z.bottom - z.top)}px`;
  mark.dataset.half = drop.half;
  // the half placed inside the box's 2px border, its line on the gap colsSplit found
  const split = Math.round((z.split || (z.top + z.bottom) / 2) - z.top) - 2;
  const inner = Math.round(z.bottom - z.top) - 4;
  const half = mark.firstElementChild;
  half.style.top = drop.half === 'upper' ? '0px' : `${split - 1}px`;
  half.style.height = drop.half === 'upper' ? `${split + 1}px` : `${inner - split + 1}px`;
  mark.hidden = false;
}

// a heading's grip by its column's name, over the columns or in the stacked column
const colGrip = (name) => document.querySelector(`#cols-head .col-head[data-col="${name}"] .pc-grip, #stack .stack-head[data-col="${name}"] .pc-grip`);
const COL_GRIPS = '.col-head .pc-grip, .stack-head .pc-grip';

function colGripDown(e) {
  const grip = e.target.closest && e.target.closest(COL_GRIPS);
  if (!grip || e.button !== 0) return;
  e.preventDefault();
  const head = grip.closest('.col-head, .stack-head');
  const name = head.dataset.col;
  const pointer = e.pointerId;
  const from = { x: e.clientX, y: e.clientY };
  let drop = null;
  let moved = false;
  head.classList.add('dragging');
  $('cols-head').classList.add('dragging');
  document.body.classList.add('col-dragging');
  const move = (ev) => {
    if (ev.pointerId !== pointer) return;
    // a press that stays where it was is a click, which opens the heading's menu
    if (!moved && Math.hypot(ev.clientX - from.x, ev.clientY - from.y) < 4) return;
    if (!moved) colMenuClose();
    moved = true;
    drop = colsDropAt(name, ev.clientX, ev.clientY);
    colsMark(drop);
  };
  const end = (ev) => {
    if (ev.pointerId !== pointer) return;
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', end);
    window.removeEventListener('pointercancel', end);
    colsMark(null);
    head.classList.remove('dragging');
    $('cols-head').classList.remove('dragging');
    document.body.classList.remove('col-dragging');
    S.colDragged = moved;
    if (ev.type !== 'pointerup' || !drop) return;
    const change = colsDropped(S.layout || columnsLayout(viewConfig()), name, drop);
    if (!change) return;
    if (Object.keys(change).length === 1 && change.statements_columns) setView('statements_columns', change.statements_columns);
    else setViews(change);
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', end);
  window.addEventListener('pointercancel', end);
}

/* Alt and an arrow moves a column a place among those on screen, and with two stacked the stacked column
   and the transcript change places, from either grip in the stack */
function colGripKeys(e) {
  const grip = e.target.closest && e.target.closest(COL_GRIPS);
  if (!grip || !e.altKey || (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight')) return;
  e.preventDefault();
  e.stopPropagation();
  const name = grip.closest('[data-col]').dataset.col;
  const shown = colsShown().map((h) => h.dataset.col);
  const delta = e.key === 'ArrowLeft' ? -1 : 1;
  const order = S.columns || COLUMNS;
  let next;
  if (stackedNow()) {
    const units = colsStep(stackUnits(order), name === 'transcript' ? 'transcript' : 'stack', delta);
    next = units ? stackExpand(units, S.layout.top) : null;
  } else next = colsStep(order, name, delta, shown);
  if (!next) return;
  setView('statements_columns', next);
  const again = colGrip(name);
  if (again) again.focus();
  const said = stackedNow() && name !== 'transcript' ? S.layout.top : name;
  $('cols-said').textContent = t('distil.cols.place', { column: COLUMN_WORDS[name], at: next.filter((c) => shown.includes(c)).indexOf(said) + 1, of: shown.length });
}

/* The heading's menu (21 October), from a click on its grip, Enter or Space with the grip in focus, or a
   right-click on the heading: its one entry as colMenuItems has it, the up and down arrows between entries,
   Esc closing it and a click anywhere else. Opened from the keyboard its entry takes the focus. */
function colMenuOpen(name, grip, keys) {
  colMenuClose();
  colsMenu(false);
  const items = colMenuItems(S.layout, name, colsNarrow());
  const menu = $('col-menu');
  if (!items.length || !menu) return;
  menu.setAttribute('aria-label', COLUMN_WORDS[name]);
  menu.innerHTML = items.map((it) => `<button type="button" class="ghost small" role="menuitem" data-act="${it.act}">${esc(it.words)}</button>`).join('');
  menu.dataset.col = name;
  menu.hidden = false;
  const box = grip.getBoundingClientRect();
  menu.style.left = `${Math.max(8, Math.min(box.left, window.innerWidth - menu.offsetWidth - 8))}px`;
  menu.style.top = `${box.bottom + 6}px`;
  grip.setAttribute('aria-expanded', 'true');
  S.colMenu = { name, grip };
  if (keys) menu.querySelector('button').focus();
}

function colMenuClose(focus = false) {
  const menu = $('col-menu');
  if (!menu || menu.hidden) return;
  menu.hidden = true;
  const open = S.colMenu;
  S.colMenu = null;
  if (open && open.grip) {
    open.grip.setAttribute('aria-expanded', 'false');
    if (focus && open.grip.isConnected) open.grip.focus();
  }
}

function colMenuChoose(act) {
  const open = S.colMenu;
  if (!open) return;
  const change = colMenuChange(S.layout, open.name, act);
  colMenuClose();
  if (change) setViews(change);
  // the focus on the moved column's grip, wherever it now stands
  const again = colGrip(open.name);
  if (again && again.getClientRects().length) again.focus();
}

// a click on a grip that was not a drag opens its menu, Enter and Space from the keyboard with the focus in it
function colGripClick(e) {
  const grip = e.target.closest && e.target.closest(COL_GRIPS);
  if (!grip) return;
  if (S.colDragged) { S.colDragged = false; return; }
  const name = grip.closest('[data-col]').dataset.col;
  if (S.colMenu && S.colMenu.name === name) { colMenuClose(); return; }
  colMenuOpen(name, grip, e.detail === 0);
}

function colHeadContext(e) {
  const head = e.target.closest && e.target.closest('.col-head, .stack-head');
  if (!head || e.shiftKey || !colMenuItems(S.layout, head.dataset.col, colsNarrow()).length) return;
  e.preventDefault();
  colMenuOpen(head.dataset.col, head.querySelector('.pc-grip'), false);
}

function colMenuKeys(e) {
  const buttons = [...$('col-menu').querySelectorAll('button')];
  if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); colMenuClose(true); return; }
  if (e.key === 'Tab') { colMenuClose(); return; }
  if ((e.key !== 'ArrowDown' && e.key !== 'ArrowUp') || !buttons.length) return;
  e.preventDefault();
  const k = buttons.indexOf(document.activeElement);
  buttons[(k + (e.key === 'ArrowDown' ? 1 : buttons.length - 1) + buttons.length) % buttons.length].focus();
}

/* ───────────────────────────────────────────────────── the minimap ── */

/* The minimap (16 October, Adam's decision after a tester lost his place in a long transcript, a
   small card at the bottom right of the transcript column since 17 October, where until then it was
   a strip the column's full height, and since 17 October, later, Adam's drawing of that evening, where
   for a few hours it stood in short columns side by side). One card of one size whatever the
   interview's length, its contents scaled to fit it, like a measuring jug. The transcript stands in
   it as one narrow column, as if its words were wrapped narrow: each of her passages a block in a mid
   grey as tall as its words, joined with its neighbours into one block where it would come out under
   MINIMAP_LEAST, so a short interview shows every passage and three hours a few to a block, and the
   interviewer's turns a thin pale mark where they fall between blocks. A track down its left holds the
   green of saved beside each passage done, a skipped one with them, and nothing beside one not done,
   the part of the column in view is a box in a solid line of the ink with the rest of the column
   dimmed, never under MINIMAP_BOX tall (18 October), and the time stands at its right in
   dashes like a jug's. Nothing else: the box shows where he is. A click glides the column there, a
   drag on the box scrolls it, the wheel over the card scrolls it, and a passage under the pointer
   names its speaker and time in a tip, while the passage being worked on stays where it is.
   `minimap` in config.json is auto, on or off, auto when absent, an old true reading as auto and an
   old false as off. In Auto the card shows as he scrolls the column or moves to another passage,
   stays while the pointer is on it or a drag lasts, and fades MINIMAP_AWAKE after, On keeps it there
   and Off leaves nothing in the corner. In Auto and On its button and M show it until the next
   passage, or hide it until then while it shows. */
const MINIMAP_MODES = ['auto', 'on', 'off'];
function minimapMode(cfg) {
  const v = cfg ? cfg.minimap : undefined;
  return v === false || v === 'off' ? 'off' : v === 'on' ? 'on' : 'auto';
}

/* the column's room in the card, its width and height, the least a block is drawn at before it is
   joined with its neighbours, the gap between two blocks and the interviewer's mark's place in it,
   the finer least and gap of a long interview and the lengths in seconds it grows finer between, the
   column's place in the card's area, the box's least height, the least room between two time
   labels, the time the card stays in Auto after the last scroll or move, the window's width at and
   below which the card gives way to its button, where the sheet and the fields stack, and the card's
   room from the column's right edge, the room between it and Back to where I was, the room Back to
   where I was takes on one line with its longest time and its gap from the column's left edge */
const MINIMAP_ROOM = { width: 62, height: 280 };
const MINIMAP_LEAST = 4.5;
const MINIMAP_GAP = 2.1;
const MINIMAP_MARK = 0.6;
const MINIMAP_FINE = { least: 2.5, gap: 1.6, from: 3600, to: 10800 };
const MINIMAP_AT = { left: 17, top: 5 };
const MINIMAP_BOX = 12;
const MINIMAP_APART = 11;
const MINIMAP_AWAKE = 2000;
const MINIMAP_NARROW = 1100;
const MINIMAP_CLEAR = { right: 14, gap: 8, back: 200 };
const mmPx = (v) => `${Math.round(v * 100) / 100}px`;
const minimapWords = (text) => Math.max(1, String(text || '').split(/\s+/).filter(Boolean).length);

/* What the card draws, read from the column as it is laid out, in the column's own pixels from the
   top of what scrolls: each passage's top and height, its place in the sheet's rows, hers or the
   interviewer's, its done level as its bar has it, its words and its timecode in seconds. */
function minimapLayout(col) {
  const base = col.getBoundingClientRect().top - col.scrollTop;
  const rows = [...col.querySelectorAll('.turn')].map((el) => {
    const box = el.getBoundingClientRect();
    const i = Number(el.dataset.i);
    const row = S.flat[i] || {};
    return { top: box.top - base, height: box.height, i, hers: !el.classList.contains('aside'),
      done: Number(el.dataset.done) || 0, words: minimapWords(row.text),
      seconds: typeof row.seconds === 'number' ? row.seconds : null };
  });
  return { height: col.scrollHeight, rows };
}

/* The column at one scale that fills the room whatever the length: her passages in blocks, each
   passage its words' share of the room's height less the gaps. While the smallest block would come
   out under MINIMAP_LEAST it is joined with the smaller of its neighbours and the scale worked out
   again for the fewer gaps, so a short interview keeps every passage and a long one joins only what it
   must. An interviewer's turn before her first passage or after her last takes a gap of its own. Each
   passage gets its place in the map, her span in her block, an interviewer's turn a point at the mark
   between two blocks or at the meeting of two passages joined, then the done track's runs, each from a
   passage done to the last done after it with only the interviewer's turns between, and the time
   marks. The least and the gap grow finer past an hour, as minimapGrain says. Null with nothing of
   hers to draw. */
function minimapPlan(layout, room) {
  const rows = layout.rows;
  const hers = rows.map((r, n) => (r.hers ? n : -1)).filter((n) => n >= 0);
  if (!hers.length || !(room.height > 0)) return null;
  const grain = minimapGrain(rows);
  const total = hers.reduce((sum, n) => sum + rows[n].words, 0);
  const lead = hers[0] > 0 ? 1 : 0;
  const trail = hers[hers.length - 1] < rows.length - 1 ? 1 : 0;
  const scale = (count) => (room.height - (count - 1 + lead + trail) * grain.gap) / total;
  const groups = hers.map((n) => ({ rows: [n], words: rows[n].words }));
  while (groups.length > 1) {
    const k = scale(groups.length);
    let least = 0;
    groups.forEach((g, b) => { if (g.words < groups[least].words) least = b; });
    if (k > 0 && groups[least].words * k >= grain.least) break;
    const before = groups[least - 1];
    const after = groups[least + 1];
    const into = !after || (before && before.words <= after.words) ? least - 1 : least + 1;
    const [a, b] = into < least ? [into, least] : [least, into];
    groups.splice(a, 2, { rows: groups[a].rows.concat(groups[b].rows), words: groups[a].words + groups[b].words });
  }
  const k = Math.max(0, scale(groups.length));
  const spans = new Array(rows.length);
  const blocks = [];
  const marks = [];
  const point = (y) => ({ top: y, bottom: y });
  let y = 0;
  const gap = (from, to) => {
    const between = rows.slice(from, to);
    const at = y + MINIMAP_MARK;
    if (between.some((r) => !r.hers)) marks.push(at);
    between.forEach((_, n) => { spans[from + n] = point(at + 0.5); });
    y += grain.gap;
  };
  if (lead) gap(0, hers[0]);
  groups.forEach((g, b) => {
    if (b > 0) gap(groups[b - 1].rows[groups[b - 1].rows.length - 1] + 1, g.rows[0]);
    const top = y;
    g.rows.forEach((n, at) => {
      // the interviewer's turns inside a block stand where her two passages meet
      if (at > 0) for (let m = g.rows[at - 1] + 1; m < n; m += 1) spans[m] = point(y);
      spans[n] = { top: y, bottom: y + rows[n].words * k };
      y = spans[n].bottom;
    });
    blocks.push({ top, height: y - top, rows: g.rows });
  });
  if (trail) gap(hers[hers.length - 1] + 1, rows.length);
  const done = [];
  let run = null;
  for (const n of hers) {
    if (rows[n].done) {
      if (run) run.bottom = spans[n].bottom;
      else run = { top: spans[n].top, bottom: spans[n].bottom };
    } else if (run) { done.push(run); run = null; }
  }
  if (run) done.push(run);
  return { k, height: room.height, rows, spans, blocks, marks, done, times: minimapTimes(rows, spans) };
}

/* How finely the column is drawn (18 October, Adam's drawing of the evening before, where three hours
   stood in more and smaller blocks than an hour, and the card drew them much as it drew an hour): up
   to an hour each block at least MINIMAP_LEAST with MINIMAP_GAP between, and from an hour to three
   hours both growing evenly finer to MINIMAP_FINE's, so three hours joins fewer of her passages to a
   block. The length is the last timecode, or for a sheet with none its words at 150 a minute. */
function minimapGrain(rows) {
  const last = rows.reduce((t, r) => (typeof r.seconds === 'number' && r.seconds > t ? r.seconds : t), 0);
  const seconds = last > 0 ? last : (rows.reduce((sum, r) => sum + (r.words || 0), 0) / 150) * 60;
  const f = Math.max(0, Math.min(1, (seconds - MINIMAP_FINE.from) / (MINIMAP_FINE.to - MINIMAP_FINE.from)));
  return { least: MINIMAP_LEAST - f * (MINIMAP_LEAST - MINIMAP_FINE.least), gap: MINIMAP_GAP - f * (MINIMAP_GAP - MINIMAP_FINE.gap) };
}

/* The time down the column's right, like a jug's dashes, each at the place its minute falls between
   the timecodes of the passages either side of it: labelled every five minutes in an interview under
   half an hour, every fifteen up to ninety minutes and every thirty beyond, with a short dash and no
   label at each fifteen between, a label read as minutes and seconds, 00:00, and past an hour still in
   minutes, 90:00, never hours. A timecode out of order is left out, and a label that would crowd the
   one above it is left to its dash. None for a sheet with no timecodes. */
function minimapTimes(rows, spans) {
  const kept = [];
  rows.forEach((r, n) => {
    if (r.seconds !== null && (!kept.length || r.seconds > kept[kept.length - 1][0])) kept.push([r.seconds, spans[n].top]);
  });
  if (!kept.length) return [];
  // 00:00 stands at the column's head
  if (kept[0][0] > 0) kept.unshift([0, 0]);
  else kept[0][1] = 0;
  const end = kept[kept.length - 1][0];
  const step = end < 1800 ? 300 : end <= 5400 ? 900 : 1800;
  const each = step === 1800 ? 900 : step;
  const place = (t) => {
    let j = 0;
    while (j < kept.length - 1 && kept[j + 1][0] <= t) j += 1;
    if (j === kept.length - 1) return kept[j][1];
    const [t0, y0] = kept[j];
    const [t1, y1] = kept[j + 1];
    return y0 + ((t - t0) / (t1 - t0)) * (y1 - y0);
  };
  const out = [];
  let last = -Infinity;
  for (let t = 0; t <= end; t += each) {
    const y = place(t);
    const named = t % step === 0 && y - last >= MINIMAP_APART;
    if (named) last = y;
    out.push({ y, label: named ? `${String(Math.round(t / 60)).padStart(2, '0')}:00` : '', short: t % step !== 0 });
  }
  return out;
}

/* The ties between the column and the map, each passage's top and foot in the column's pixels against
   its place in the map, and the column's head and foot against the map's, so a place in either reads
   as a place in the other however tall the passages stand in the column. */
function minimapAnchors(layout, plan) {
  const out = [[0, 0]];
  layout.rows.forEach((r, n) => {
    out.push([r.top, plan.spans[n].top], [r.top + r.height, plan.spans[n].bottom]);
  });
  out.push([Math.max(layout.height, out[out.length - 1][0]), plan.height]);
  return out;
}

/* a place in the column, in its own pixels, as a place in the map, and back, the first place in the
   column for a point of the map an interviewer's turn stands at */
function minimapToMap(plan, y) {
  const a = plan.anchors;
  if (y <= a[0][0]) return a[0][1];
  for (let j = 1; j < a.length; j += 1) {
    if (y <= a[j][0]) {
      const [c0, m0] = a[j - 1];
      const [c1, m1] = a[j];
      return c1 > c0 ? m0 + ((y - c0) / (c1 - c0)) * (m1 - m0) : m1;
    }
  }
  return a[a.length - 1][1];
}

function minimapToCol(plan, m) {
  const a = plan.anchors;
  if (m <= a[0][1]) return a[0][0];
  for (let j = 1; j < a.length; j += 1) {
    if (m <= a[j][1] && a[j][1] > a[j - 1][1]) {
      const [c0, m0] = a[j - 1];
      const [c1, m1] = a[j];
      return c0 + ((m - m0) / (m1 - m0)) * (c1 - c0);
    }
  }
  return a[a.length - 1][0];
}

/* The marks at the plan's place in the map, from the column's head: the done track and its runs of
   green, the blocks, the interviewer's marks, then the time's dashes and labels. */
function minimapHtml(plan) {
  const out = ['<i class="mm-track"></i>'];
  for (const d of plan.done) out.push(`<i class="mm-done" style="top:${mmPx(d.top)};height:${mmPx(d.bottom - d.top)}"></i>`);
  for (const b of plan.blocks) out.push(`<i class="mm-block" style="top:${mmPx(b.top)};height:${mmPx(b.height)}"></i>`);
  for (const m of plan.marks) out.push(`<i class="mm-ask" style="top:${mmPx(m)}"></i>`);
  for (const t of plan.times) {
    out.push(`<i class="mm-dash${t.short ? ' short' : ''}" style="top:${mmPx(t.y)}"></i>`);
    if (t.label) out.push(`<span class="mm-time" style="top:${mmPx(t.y)}">${t.label}</span>`);
  }
  return out.join('');
}

/* The box over the part of the column in view, `top` and `tall` in the column's own pixels, from the
   map's place for its head to its place for its foot, and never under MINIMAP_BOX, a short one centred
   on its place and kept inside the map. */
function minimapView(plan, top, tall) {
  const a = minimapToMap(plan, top);
  const b = minimapToMap(plan, top + tall);
  if (b - a >= MINIMAP_BOX) return { top: a, height: b - a };
  const height = Math.min(MINIMAP_BOX, plan.height);
  return { top: Math.max(0, Math.min(plan.height - height, (a + b) / 2 - height / 2)), height };
}

/* The card drawn again from the column, once a frame at most, on every change to what the column
   holds or where: a sheet drawn, a move, a passage redrawn, the progress, the view and any change of
   size. While it is not wanted in the corner nothing is read but what it gives way to. A move to
   another passage ends an opening or a hiding of his and wakes the card in Auto. */
let minimapFrame = 0;
function scheduleMinimap() {
  if (minimapFrame) return;
  minimapFrame = requestAnimationFrame(() => { minimapFrame = 0; drawMinimap(); });
}

function drawMinimap() {
  const now = current();
  const at = now ? now.i : -1;
  if (S.mmAt !== at) {
    $('work').classList.toggle('minimap-peek', false);
    S.mmHeld = false;
    S.mmHush = false;
    if (at !== -1) minimapWake(false);
  }
  S.mmAt = at;
  if ($('work').hidden || !minimapWanted()) { S.mm = null; minimapTip(null); drawMinimapView(); return; }
  const layout = minimapLayout($('transcript'));
  const plan = minimapPlan(layout, MINIMAP_ROOM);
  S.mm = plan && Object.assign(plan, { anchors: minimapAnchors(layout, plan) });
  $('minimap-map').innerHTML = plan ? minimapHtml(plan) : '';
  drawMinimapView();
}

/* the box over the part of the column in view, set again on every scroll, so it follows the column
   as it glides to a new passage, and what the card gives way to looked at again with it */
function drawMinimapView() {
  minimapYield();
  const plan = S.mm;
  // a card going as it sleeps keeps its box while it fades, so the box fades with the map and never goes
  // first, leaving the card a moment with no box (18 October, polish 10)
  if (!plan) { if (!$('minimap').classList.contains('shut')) $('minimap-views').innerHTML = ''; return; }
  const col = $('transcript');
  const v = minimapView(plan, col.scrollTop, col.clientHeight);
  $('minimap-views').innerHTML = `<i class="minimap-view" style="top:${mmPx(v.top)};height:${mmPx(v.height)}"></i>`;
}

/* Whether a box on the page overlaps any of `rects`, each a passage's words, its notes field or a
   field in focus, an empty one counting for nothing. */
function minimapOver(box, rects) {
  return rects.some((r) => r.width > 0 && r.height > 0 && r.left < box.right && r.right > box.left
    && r.top < box.bottom && r.bottom > box.top);
}

/* Whether the card is wanted in the corner, before it gives way: never with Off or while he has hidden
   it for this passage, at 1100px and below only for an opening of his, and wider for an opening of
   his, with On, or in Auto while it is awake. Shown is wanted and not given way. */
function minimapNarrow() { return window.matchMedia(`(max-width: ${MINIMAP_NARROW}px)`).matches; }

function minimapWanted() {
  const work = $('work');
  if (!work.classList.contains('minimap-on') || S.mmHush) return false;
  if (work.classList.contains('minimap-peek')) return true;
  if (minimapNarrow()) return false;
  return work.classList.contains('minimap-always') || !!S.mmAwake;
}

function minimapShown() {
  return minimapWanted() && ($('work').classList.contains('minimap-peek')
    || !($('minimap').classList.contains('yield') || $('minimap').classList.contains('gone')));
}

/* The card gives way (17 October, later): the words he is writing and the passage being worked on
   never stand under it. While the current passage's words, its card of statements (17 October), its
   exploratory notes, a passage open for correction, a quote being built or a field in focus in the
   columns would stand under the card where
   it is wanted, the card goes and the button stays, and where they would stand under the button as
   well both go, at every width, coming back as soon as they are clear (17 October, later, where at
   1100px and below the button stayed over the last line of his passage). Never while a press on it is
   under way or the pointer is on it, so it never goes from under his hand. An opening of his, from the button or M, shows the card over what stands
   in the corner as he opens it, and once the current passage, its notes or a field in focus comes
   under it after that, or his pointer leaves the card while they are under it, the opening ends: the
   card closes to its button at 1100px and below and gives way as at any time at a wider window (17
   October, later, where an opening of his lasted for the passage and at 1100px covered the notes he
   was writing). A scroll by his hand on the words ends that opening as well. Back to where I was stands
   clear to the card's left, or at the column's head where the column has no room beside it, and the
   button says whether the map shows. */
function minimapYield() {
  const card = $('minimap');
  const work = $('work');
  const wanted = minimapWanted();
  if (!(S.mmDrag || S.mmOver)) {
    const cur = $('transcript-rows').querySelector('.turn.current');
    const words = cur ? [...cur.querySelectorAll('.turn-text, .turn-edit, .quote-preview, #es-card, #en')] : [];
    const focus = document.activeElement;
    const field = focus && focus !== document.body && $('transcript').contains(focus) && /^(TEXTAREA|INPUT)$/.test(focus.tagName)
      ? focus.getBoundingClientRect() : null;
    const rects = words.map((el) => el.getBoundingClientRect()).concat(field ? [field] : []);
    const box = $('minimap-card').getBoundingClientRect();
    const over = wanted && minimapOver(box, rects);
    // the corner clear once, what comes under the card after that ends his opening, and a field in focus at once
    if (wanted && !over) S.mmHeld = false;
    let peek = work.classList.contains('minimap-peek');
    if (peek && over && (!S.mmHeld || (field && minimapOver(box, [field])))) {
      work.classList.toggle('minimap-peek', false);
      S.mmHeld = false;
      peek = false;
      scheduleMinimap();
    }
    card.classList.toggle('yield', !peek && over);
    card.classList.toggle('gone', !peek && !work.hidden && minimapOver($('minimap-btn').getBoundingClientRect(), rects));
  }
  const shown = minimapShown();
  const off = !work.classList.contains('minimap-on');
  card.classList.toggle('shut', !shown);
  card.classList.toggle('off', off);
  $('minimap-btn').setAttribute('aria-pressed', String(shown));
  // and the status bar's Minimap with it (21 October), pressed in while the map shows
  if ($('es-map-btn')) $('es-map-btn').setAttribute('aria-pressed', String(shown));
  // Back to where I was beside the card on one line where the column has the room, and where it has not,
  // as at 360px with the card open, at the column's head at the card's right edge, over a strip where
  // the column's words fade out, so it never cuts through a line, where it stood squeezed to two lines
  // into the column's words and then over a line above the card (17 October, later)
  const wrap = card.parentElement;
  const wide = off || card.classList.contains('gone') ? 0 : shown ? card.offsetWidth : $('minimap-btn').offsetWidth;
  const beside = !wide || wrap.clientWidth - MINIMAP_CLEAR.right - wide - MINIMAP_CLEAR.gap >= MINIMAP_CLEAR.back;
  const room = !wide ? '' : beside ? `${MINIMAP_CLEAR.right + wide + MINIMAP_CLEAR.gap}px` : `${MINIMAP_CLEAR.right}px`;
  const lift = !beside && wrap.classList.contains('away');
  if (room !== S.mmRoom) { S.mmRoom = room; wrap.style.setProperty('--mm-room', room); }
  if (lift !== S.mmLift) { S.mmLift = lift; wrap.classList.toggle('mm-lift', lift); }
  // the button standing alone at 1100px and below, as at 360 over a passage's words (18 October, polish 10)
  const alone = !shown && !off && !work.hidden && !card.classList.contains('gone') && minimapNarrow();
  // a card he opened by a press over the transcript's words stands on a band where they fade out, so
  // its edges never cut a line, as at 360px (18 October), and so does the button alone
  const band = shown && work.classList.contains('minimap-peek') ? minimapBand() : alone ? minimapButtonBand() : '';
  if (band !== S.mmBand) { S.mmBand = band; wrap.style.setProperty('--mm-band', band); wrap.classList.toggle('mm-band', !!band); }
}

/* Where the card stands over the words of a passage level with it, its words, the box open for their
   correction or a quote being built, the band under the card: its height from the column's foot to 12
   pixels above the card, over which the column's words fade out across its full width. Otherwise '',
   and '' too while a field in focus in the column would stand in the band, so the words he is writing
   never fade. Only the passages level with the card are read. */
function minimapBand() {
  const plan = S.mm;
  if (!plan) return '';
  const col = $('transcript');
  const at = col.getBoundingClientRect();
  const box = $('minimap-card').getBoundingClientRect();
  const focus = document.activeElement;
  if (focus && focus !== document.body && col.contains(focus) && /^(TEXTAREA|INPUT)$/.test(focus.tagName)
    && focus.getBoundingClientRect().bottom > box.top - 36) return '';
  const top = col.scrollTop + box.top - at.top;
  const foot = col.scrollTop + box.bottom - at.top;
  const rows = $('transcript-rows');
  const words = plan.rows.filter((r) => r.top < foot && r.top + r.height > top)
    .map((r) => rows.querySelector(`.turn[data-i="${r.i}"]`)).filter(Boolean)
    .flatMap((el) => [...el.querySelectorAll('.turn-text, .turn-edit, .quote-preview')])
    .map((el) => el.getBoundingClientRect());
  return minimapOver(box, words) ? `${Math.max(0, Math.round(at.bottom - box.top + 12))}px` : '';
}

/* The same band under the button standing alone, where no map is drawn to say which passages are level
   with it: the words under the button, found at nine points across it, a passage's words, the box open
   for their correction or a quote being built, and none while a field in focus in the column would
   stand in the band. */
function minimapButtonBand() {
  const btn = $('minimap-btn');
  const col = $('transcript');
  const box = btn.getBoundingClientRect();
  if (!box.width || !box.height) return '';
  const at = col.getBoundingClientRect();
  const focus = document.activeElement;
  if (focus && focus !== document.body && col.contains(focus) && /^(TEXTAREA|INPUT)$/.test(focus.tagName)
    && focus.getBoundingClientRect().bottom > box.top - 36) return '';
  const steps = [0.1, 0.5, 0.9];
  const under = steps.some((fx) => steps.some((fy) => document.elementsFromPoint(box.left + fx * box.width, box.top + fy * box.height)
    .some((el) => el !== btn && col.contains(el) && !!el.closest('.turn-text, .turn-edit, .quote-preview'))));
  return under ? `${Math.max(0, Math.round(at.bottom - box.top + 12))}px` : '';
}

/* In Auto the card wakes as he scrolls the column or moves to another passage, and sleeps
   MINIMAP_AWAKE after the last of them, the time starting again once the pointer leaves it or a drag
   ends, so it never goes from under his hand. With On or Off there is nothing to wake. */
let minimapSleep = 0;
function minimapWake(draw = true) {
  const work = $('work');
  if (!work.classList.contains('minimap-on') || work.classList.contains('minimap-always')) return;
  const was = !!S.mmAwake;
  S.mmAwake = true;
  minimapRest();
  if (!was && draw) scheduleMinimap();
}

function minimapRest() {
  clearTimeout(minimapSleep);
  if (!S.mmAwake || S.mmOver || S.mmDrag) return;
  minimapSleep = setTimeout(() => {
    if (S.mmOver || S.mmDrag) return;
    S.mmAwake = false;
    scheduleMinimap();
  }, MINIMAP_AWAKE);
}

/* the pointer off the card: what it covers looked at again, an opening of his held over the corner
   ends, since he has left it, and in Auto its time starts again */
function minimapLeave() {
  S.mmOver = false;
  S.mmHeld = false;
  minimapRest();
  minimapYield();
}

/* A scroll of the column wakes the card in Auto, and a scroll by his hand on the words, the pointer
   off the card and no press under way, ends an opening of his held over the corner, since he is back
   at the words. */
function minimapScrolled() {
  minimapWake();
  if (S.mmOver || S.mmDrag || !S.mmHeld) return;
  S.mmHeld = false;
  minimapYield();
}

/* a point of the card's area as a place in the map, from the column's head, held inside it */
function minimapPoint(plan, e) {
  const box = $('minimap-area').getBoundingClientRect();
  return { x: e.clientX - box.left - MINIMAP_AT.left, m: Math.max(0, Math.min(plan.height, e.clientY - box.top - MINIMAP_AT.top)) };
}

/* the passage under a point of the map, its own span or the nearest within 2 pixels, or null off the
   column */
function minimapRowAt(plan, x, m) {
  if (x < -3 || x > MINIMAP_ROOM.width + 3) return null;
  let best = null;
  plan.rows.forEach((r, n) => {
    const s = plan.spans[n];
    const off = m < s.top ? s.top - m : m > s.bottom ? m - s.bottom : 0;
    if (!best || off < best.off || (off === best.off && r.hers && !best.r.hers)) best = { r, off };
  });
  return best && best.off <= 2 ? S.flat[best.r.i] || null : null;
}

/* the column scrolled so the top of what it shows is `top`, in its own pixels, gliding for a click */
function minimapTo(top, smooth) {
  if (!S.mm) return;
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  $('transcript').scrollTo({ top: Math.max(0, Math.round(top)), behavior: smooth && !still ? 'smooth' : 'auto' });
}

/* A press on the card brings the place pressed to the middle of the column, and a drag carries on
   from there. A press on the box takes the box where the pointer goes. Only the column moves: the
   passage being worked on stays, the way back shows as it does for any scroll by hand, and the caret
   stays in the fields. */
function minimapDown(e) {
  const plan = S.mm;
  if (e.button !== 0 || !plan) return;
  e.preventDefault();
  minimapTip(null);
  const { m } = minimapPoint(plan, e);
  const col = $('transcript');
  const at = minimapToCol(plan, m);
  const v = minimapView(plan, col.scrollTop, col.clientHeight);
  const onBox = m >= v.top - 1 && m <= v.top + v.height + 1;
  const grab = onBox ? Math.max(0, Math.min(col.clientHeight, at - col.scrollTop)) : col.clientHeight / 2;
  S.mmDrag = { grab, x: e.clientX, y: e.clientY, moved: onBox };
  clearTimeout(minimapSleep);
  if (!onBox) minimapTo(at - col.clientHeight / 2, true);
  const area = $('minimap-area');
  if (area.setPointerCapture) area.setPointerCapture(e.pointerId);
  area.classList.add('dragging');
}

function minimapMove(e) {
  const drag = S.mmDrag;
  if (!drag) { minimapHover(e); return; }
  // a click that wanders a pixel or two leaves the glide alone
  if (!drag.moved && Math.abs(e.clientY - drag.y) < 4 && Math.abs(e.clientX - drag.x) < 4) return;
  drag.moved = true;
  minimapTo(minimapToCol(S.mm, minimapPoint(S.mm, e).m) - drag.grab, false);
}

function minimapUp() {
  S.mmDrag = null;
  $('minimap-area').classList.remove('dragging');
  minimapRest();
  minimapYield();
}

/* The tip over a passage under the pointer, its speaker and its timecode as the column's margin
   gives them, above the pointer and inside the window, and gone off the column, on a press and as
   the card closes. A touch shows none. */
function minimapHover(e) {
  if (!S.mm || e.pointerType === 'touch') { minimapTip(null); return; }
  const { x, m } = minimapPoint(S.mm, e);
  const row = minimapRowAt(S.mm, x, m);
  minimapTip(row && { row, x: e.clientX, y: e.clientY });
}

function minimapTip(at) {
  const tip = $('minimap-tip');
  if (!at) { tip.hidden = true; return; }
  const words = `${esc(at.row.name || '')}${at.row.time ? ` <span class="mono">${esc(at.row.time)}</span>` : ''}`;
  if (tip.innerHTML !== words) tip.innerHTML = words;
  tip.hidden = false;
  const w = tip.offsetWidth;
  tip.style.left = `${Math.round(Math.max(8, Math.min(at.x - w / 2, window.innerWidth - w - 8)))}px`;
  tip.style.top = `${Math.round(Math.max(8, at.y - tip.offsetHeight - 10))}px`;
}

/* the wheel over the card scrolls the column as it would over the words, a pinch left to the browser */
function minimapWheel(e) {
  if (e.ctrlKey) return;
  e.preventDefault();
  const col = $('transcript');
  const step = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? col.clientHeight : 1;
  col.scrollBy({ top: e.deltaY * step, left: 0, behavior: 'auto' });
}

/* The button and M, in Auto and On: shown, the card hides until the next passage, and hidden, it shows
   until then, held over what stands in the corner as minimapYield says. With Off they do nothing, the
   button gone with the card. */
function minimapToggle() {
  const work = $('work');
  if (!work.classList.contains('minimap-on')) return;
  const show = !minimapShown();
  work.classList.toggle('minimap-peek', show);
  S.mmHeld = show;
  S.mmHush = !show;
  scheduleMinimap();
}

/* A choice of Auto, On or Off in View or Settings' View, kept as View keeps it: any opening or hiding
   of his goes with it, and Auto shows the card at once so he sees it, then lets it sleep. */
function minimapChoose(mode) {
  $('work').classList.toggle('minimap-peek', false);
  S.mmHeld = false;
  S.mmHush = false;
  S.mmAwake = mode === 'auto';
  minimapRest();
  return setView('minimap', mode);
}

/* A choice in the menu: drawn at once and sent alone to the settings, every other key kept. A
   server from before the two keys keeps neither, and the line says to restart. */
async function setView(key, value) {
  if (!S.data || !S.data.config) return;
  S.data.config[key] = value;
  if (S.libConfig) S.libConfig[key] = value;
  if (typeof TH !== 'undefined' && TH.config) TH.config[key] = value;
  drawView();
  // the passage keeps the middle of the column as the screen changes round it
  if (!$('work').hidden && current()) centreCurrent(false);
  try {
    const data = await api('/api/settings', { [key]: value });
    if (!data.config || data.config[key] === undefined) say(RESTART_LINE, 9000);
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

// several of the view's keys at once, drawn once and sent in one save, as a heading dropped to stack sends
// the order, the stacking and the column above together (21 October)
async function setViews(changes) {
  if (!S.data || !S.data.config) return;
  const keys = Object.keys(changes || {});
  if (!keys.length) return;
  for (const c of [S.data.config, S.libConfig, typeof TH !== 'undefined' ? TH.config : null]) if (c) Object.assign(c, changes);
  drawView();
  // the passage keeps the middle of the column as the screen changes round it
  if (!$('work').hidden && current()) centreCurrent(false);
  try {
    const data = await api('/api/settings', changes);
    if (!data.config || keys.some((k) => data.config[k] === undefined)) say(RESTART_LINE, 9000);
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* ───────────────────────────────────────────────── round markers ── */

/* A thin rule across the column before the first row of every round on the sheet, round 1 at the
   top, with its name in the margin in the speaker's small capitals and its state under the name,
   where a turn carries its timecode (item 155). A round closed reads done with the small tick, the
   round holding the current turn reads now with its rule in the current turn's orange, and a round
   not reached reads to do. Closed wins over now. A marker is never a turn: never a stop, never
   current, never counted, and the rules that dim and mark the turns never reach it. Its state is a
   class and a word changed in place on every move and every round close, at the same height in
   all three, so the column is never redrawn for it and the sheet never jumps. A click goes to the
   round's first undecided participant turn, or its first one when every turn is decided, the way
   a click on a speaker's name goes to a turn. A server that sends no rounds gets no markers. */
const MARK_TICK = '<svg class="round-mark-tick" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4.5 12.7 9.6 17.8 19.5 7"/></svg>';
const MARK_WORDS = { done: t('distil.round.done'), now: t('distil.round.now'), todo: t('distil.round.todo') };

/* the round's number on its sheet, the one every round number on screen uses */
function sheetRound(rnd) {
  if (!rnd) return 0;
  if (typeof rnd.on_sheet === 'number') return rnd.on_sheet;
  return S.data.rounds.filter((r) => r.sheet === rnd.sheet).indexOf(rnd) + 1;
}

/* the clock's tooltip names the round by its number on the sheet, and with no rounds the screen */
function clockTitle(rnd) {
  return rnd ? t('distil.round.clock_title', { round: sheetRound(rnd) }) : t('distil.round.clock_title_screen');
}

function roundMarkHtml(rnd) {
  return `<button type="button" tabindex="-1" class="round-mark" data-round="${rnd.number}">
      <span class="round-mark-gutter"><span class="round-mark-name">${esc(t('distil.round.name', { round: sheetRound(rnd) }))}</span><span
        class="round-mark-state">${MARK_TICK}<span class="round-mark-word"></span></span></span>
      <span class="round-mark-rule" aria-hidden="true"></span>
    </button>`;
}

function roundMarkState(number) {
  const done = (S.data.progress && S.data.progress.roundsDone) || [];
  if (done.includes(number)) return 'done';
  const row = current();
  return row && row.round === number ? 'now' : 'todo';
}

/* Where a click on the marker goes, and its tooltip: the participant turns in the round, the
   timecodes of its first and last rows, and which turn the click lands on. */
function roundTarget(number) {
  const states = (S.data.progress && S.data.progress.states) || {};
  const rows = S.flat.filter((r) => r.round === number);
  const stops = rows.filter((r) => r.stop);
  const open = stops.find((r) => (states[r.key] || 'unvisited') === 'unvisited');
  const timed = rows.filter((r) => r.time);
  const rnd = S.data.rounds.find((r) => r.number === number);
  const said = { round: sheetRound(rnd), n: stops.length };
  const first = timed.length ? t('distil.round.mark_title_span', { ...said, from: timed[0].time, to: timed[timed.length - 1].time })
    : t('distil.round.mark_title', said);
  const go = !stops.length ? '' : open ? t('distil.round.go_open') : t('distil.round.go_first');
  return {
    pos: open ? open.pos : stops.length ? stops[0].pos : -1,
    title: go ? t('distil.round.mark_title_go', { first, go }) : first,
  };
}

/* the three states and the tooltips, taken again in place on every move and every round close */
function drawRoundMarks() {
  if (!S.data) return;
  for (const el of $('transcript-rows').querySelectorAll('.round-mark')) {
    const number = Number(el.dataset.round);
    const state = roundMarkState(number);
    if (!el.classList.contains(state)) {
      el.classList.remove('done', 'now', 'todo');
      el.classList.add(state);
      el.querySelector('.round-mark-word').textContent = MARK_WORDS[state];
    }
    el.title = roundTarget(number).title;
  }
}

/* a click on a marker, by the path a click on a speaker's name takes, and never the count */
function toRound(number) {
  const k = roundTarget(number).pos;
  if (k < 0) return Promise.resolve();
  if (k === S.at) cueAudio(S.flat[S.stops[k]].seconds);
  return goTo(k);
}

/* ────────────────────────────────────────────────── done marks ── */

/* A thin bar at the edge of the words of every participant passage he has worked, in the margin
   where the current passage's rule stands (16 October, after a tester lost track of the work he had
   done in long passages): full where the passage has a statement, fainter where he skipped it, and
   none where it is undecided or only passed, a passage he jumped over on the way further, since
   Adam's word of 16 October that a jump ahead never reads as done up to here. Each passage says its
   own state, so work done in any order shows as it is. The interviewer's passages between two of hers
   carry the bar on, at the fainter of the two, so a stretch of worked passages reads as one. Never the
   crux orange, which marks the quotes. The states are the server's, and the counts and the rounds
   still take a passed passage as decided. The bars are drawn as an attribute in place on every change
   to the progress and as the column is built, so nothing is redrawn for them. */
const DONE_LEVEL = { 'has-content': 2, 'reviewed-empty': 1 };

function doneLevels(rows, states) {
  const level = new Map();
  let last = null;
  let between = [];
  for (const row of rows) {
    if (!row.stop) { between.push(row); continue; }
    const now = DONE_LEVEL[states[row.key]] || 0;
    level.set(row.i, now);
    // the interviewer's passages since the last of hers take the fainter of the two either side
    for (const aside of between) level.set(aside.i, last === null ? 0 : Math.min(last, now));
    between = [];
    last = now;
  }
  for (const aside of between) level.set(aside.i, 0);
  return level;
}

function drawDoneMarks() {
  if (!S.data || !S.sheetDrawn) return;
  const states = (S.data.progress && S.data.progress.states) || {};
  const level = doneLevels(S.flat.filter((r) => r.sheet === S.sheetDrawn), states);
  for (const el of $('transcript-rows').querySelectorAll('.turn')) {
    const n = level.get(Number(el.dataset.i)) || 0;
    if (n) el.dataset.done = String(n);
    else delete el.dataset.done;
  }
  // the minimap's done track follows the column's bars
  scheduleMinimap();
}

/* The sheet's rows in order, a marker before the first row of each round, each round once, so a
   row out of time order never draws a second marker mid-round. With Work in rounds off there are no
   markers at all. */
function drawTranscript(sheet) {
  const rounds = new Map(roundsHere() ? S.data.rounds.map((r) => [r.number, r]) : []);
  const drawn = new Set();
  const html = [];
  for (const row of S.flat) {
    if (row.sheet !== sheet) continue;
    if (rounds.has(row.round) && !drawn.has(row.round)) {
      drawn.add(row.round);
      html.push(roundMarkHtml(rounds.get(row.round)));
    }
    html.push(turnHtml(row));
  }
  // the card, the notes field and an interviewer note go back where they wait before the rows they may
  // stand in are replaced
  parkCard();
  parkNotes();
  parkNote();
  $('transcript-rows').innerHTML = html.join('');
  S.sheetDrawn = sheet;
  // the sheet is a fact about the file, not about a row, so it stands in the top bar beside the
  // case name and never in a turn's margin
  drawSheetLabel(sheet);
  // the column is new, so the playhead mark and the timecode index are built again from it
  S.listening = null;
  S.spansSheet = null;
  drawDoneMarks();
}

/* `turn-text` travels with the current turn, so the selection and quote code keeps working on one
   element and never reaches into a dimmed turn. */
function markCurrent(row) {
  const box = $('transcript-rows');
  const was = box.querySelector('.turn.current');
  if (was) {
    // the turn being left goes back to plain runs, so no pending quote mark is stranded on it, and
    // keeps the find's washes while the find is open
    const old = S.flat[Number(was.dataset.i)];
    const text = was.querySelector('.turn-text');
    if (old && text) text.innerHTML = rowHtml(old);
    const preview = was.querySelector('.quote-preview');
    if (preview) preview.remove();
    was.classList.remove('current');
    was.removeAttribute('id');
    was.querySelector('.turn-text').removeAttribute('id');
  }
  const el = box.querySelector(`.turn[data-i="${row.i}"]`);
  if (!el) return null;
  el.classList.add('current');
  el.id = 'turn';
  el.querySelector('.turn-text').id = 'turn-text';
  // the card of statements and the notes field travel with the current passage, the passage left
  // showing its statements and notes as the rest do
  placeCard();
  placeNotes();
  watchCurrent(el, row);
  // and the minimap is drawn again for the passage redrawn
  scheduleMinimap();
  return el;
}

/* The way back. The button is hidden while the turn is in the column's viewport and shows as soon
   as it is scrolled out of it, so it is only ever there when it is needed. While it shows, the column
   gives up a strip at its foot for it, so it never covers a line (16 October). */
let turnWatch;
function wayBack(on) {
  $('back-to-turn').hidden = !on;
  $('transcript').parentElement.classList.toggle('away', on);
}

function watchCurrent(el, row) {
  $('back-to-turn-time').textContent = row.time;
  wayBack(false);
  if (turnWatch) turnWatch.disconnect();
  if (!('IntersectionObserver' in window)) return;
  turnWatch = new IntersectionObserver(([entry]) => {
    wayBack(!(entry.isIntersecting || performance.now() < centringUntil));
  }, { root: $('transcript'), rootMargin: '-24px 0px -24px 0px', threshold: 0 });
  turnWatch.observe(el);
}

/* how far below the column's head a passage brought into view starts, so its speaker line clears the
   column's faded top edge, 30 pixels of the mask (17 October) */
const SPEAKER_CLEAR = 24;

/* The current passage's card in reach where a long passage leaves the column too short for it (cardlarge, 30
   October 2026). zoomsweep's shot at Text size Large in a 1280 by 800 window had the card of a long passage, level
   with a quote low in its words, below the window's foot, and at 720 the card under the words was always there.
   Three ways were drawn for Adam, and this line chooses one. 'cap' (A): the passage's words capped to what the
   column leaves and scrolling inside themselves, the card level with its quote only as far as their box shows it.
   'hold' (B): the card kept in view in the column, beside the words at their head or foot, or over the foot of the
   words where it stands under them, its own height capped and scrolling inside itself. 'scroll' (C): as the
   passage opens the column goes down until the card's first statement and its foot stand in view, the passage's
   start above the column's head. '' leaves the screen as it was. In all three a passage that fits the column with
   its speaker line is left as it was, and so is a card in the stacked column or parked. */
const CARD_REACH = 'hold';

/* What a long passage leaves its card (cardlarge): whether the card stands under the words rather than beside
   them, `need`, the height from the card's top to the foot of its first statement's box with the card's own foot
   under it, the part that must stand in view for the card to be in reach, `room`, the height the column leaves
   the words, and `long`, the words taller than that, `reachOf` answering null where the card is not in the current
   passage's row. `settle` and `glide` are the times until which a passage just centred is still opening and its
   glide still running. */
const REACH = { need: 0, room: 0, long: false, under: false, settle: 0, glide: 0 };

function reachOf(el) {
  const card = $('es-card');
  const col = $('transcript');
  const words = el ? el.querySelector('.turn-text') : null;
  if (!words || !el.contains(card) || !card.getClientRects().length) return null;
  const w = words.getBoundingClientRect();
  const c = card.getBoundingClientRect();
  const under = c.left < w.right - 1 && c.right > w.left + 1;
  const first = card.querySelector('.pair');
  const field = first ? first.querySelector('.pair-es') : null;
  const foot = card.querySelector('.es-foot');
  const need = (field ? field.getBoundingClientRect().bottom - c.top + 12 : 0) + (foot ? foot.offsetHeight : 0);
  // what stands above the words in their row, the name and time where they lie along the top, the row's 9 pixels
  // under them, and the card's 12 pixels under them where it stands there, never under two lines
  const line = parseFloat(getComputedStyle(words).lineHeight) || 24;
  const above = w.top - el.getBoundingClientRect().top;
  const room = Math.max(line * 2, col.clientHeight - SPEAKER_CLEAR - 30 - above - 9 - (under ? need + 12 : 0));
  return { need: Math.ceil(need), room: Math.floor(room), long: words.scrollHeight > room + 1, under, line };
}

/* The current passage marked `reach-long` while its words leave the column too short for its card, measured with
   the mark taken off, on each centring and each change to the column's size, never as he types. Under 'cap' its
   words take `--reach-cap`, the room the column leaves them, and under 'hold' its card does, the column less its
   faded edges beside the words and at most half the column over their foot, its first statement and its foot
   always whole. */
function reachDraw() {
  const col = $('transcript');
  if (!col) return;
  const el = col.querySelector('.turn.current');
  for (const was of col.querySelectorAll('.turn.reach-long')) {
    was.classList.remove('reach-long');
    was.style.removeProperty('--reach-cap');
  }
  for (const box of document.querySelectorAll('.reach-above, .reach-below')) box.classList.remove('reach-above', 'reach-below');
  $('work').classList.toggle('reach-cap', CARD_REACH === 'cap');
  $('work').classList.toggle('reach-hold', CARD_REACH === 'hold');
  const r = CARD_REACH ? reachOf(el) : null;
  Object.assign(REACH, r || { need: 0, room: 0, long: false, under: false });
  if (!r || !r.long) return;
  el.classList.add('reach-long');
  if (CARD_REACH === 'cap') el.style.setProperty('--reach-cap', `${r.room}px`);
  if (CARD_REACH === 'hold') {
    const most = col.clientHeight - 30 - 30 - 4;
    const cap = r.under ? Math.min(most - r.line * 3, Math.max(r.need + 8, col.clientHeight / 2)) : most;
    el.style.setProperty('--reach-cap', `${Math.floor(Math.max(r.need, cap))}px`);
  }
  requestAnimationFrame(() => {
    reachFade(el.querySelector('.turn-text'));
    reachFade($('es-card'));
  });
}

/* A passage's words or a held card scrolling inside themselves fade at an edge with more beyond it, as the
   column does (cardlarge) */
function reachFade(box) {
  if (!box || !box.matches || !box.matches('.reach-cap .reach-long > .turn-text, .reach-hold .reach-long .es-card')) return;
  const above = box.scrollTop > 1;
  const below = box.scrollTop + box.clientHeight < box.scrollHeight - 1;
  box.classList.toggle('reach-above', above);
  box.classList.toggle('reach-below', below);
}

/* Under 'scroll', the column down until the long passage's card has its first statement and its foot whole
   above the column's faded foot, as `centreCurrent` leaves it (cardlarge) */
function reachInView() {
  const col = $('transcript');
  const card = $('es-card');
  const el = col.querySelector('.turn.current.reach-long');
  if (!el || !el.contains(card)) return;
  const over = card.getBoundingClientRect().top + REACH.need - (col.getBoundingClientRect().bottom - 38);
  if (over > 1) col.scrollTop += over;
}

/* What stands in view in the column, kept where it stands across a resize of the window (18 October, the
   sweep's narrowing while typing, which scrolled the passage and the field away for good). The field
   holding the caret when it is in view, else the passage being worked on when it is, is taken with its
   distance from the column's top on every scroll and every move of the focus, and once the column has
   its new size it is put back at that distance, and whole in view where it fits. A place read while a new
   size is still to be laid out is left alone, and nothing is kept once he has scrolled both out of view. */
const VIEW = { el: null, at: 0, w: 0, h: 0 };

function viewAnchor() {
  const col = $('transcript');
  if ($('work').hidden || !col) return;
  if (VIEW.el && (col.clientWidth !== VIEW.w || col.clientHeight !== VIEW.h)) return;
  const box = col.getBoundingClientRect();
  const seen = (el) => {
    if (!el || !col.contains(el)) return false;
    const b = el.getBoundingClientRect();
    return (b.width || b.height) && b.bottom > box.top && b.top < box.bottom;
  };
  const focus = document.activeElement;
  const field = focus && focus !== col && focus.matches && focus.matches('textarea, input') ? focus : null;
  const el = [field, col.querySelector('.turn.current')].find(seen) || null;
  VIEW.el = el;
  VIEW.at = el ? el.getBoundingClientRect().top - box.top : 0;
  VIEW.w = col.clientWidth;
  VIEW.h = col.clientHeight;
}

function keepView() {
  const col = $('transcript');
  const el = VIEW.el;
  if ($('work').hidden || !col) return;
  if (col.clientWidth === VIEW.w && col.clientHeight === VIEW.h) return;
  VIEW.w = col.clientWidth;
  VIEW.h = col.clientHeight;
  if (!el || !col.contains(el)) return;
  const box = col.getBoundingClientRect();
  col.scrollTop += el.getBoundingClientRect().top - box.top - VIEW.at;
  const b = el.getBoundingClientRect();
  const foot = box.bottom - 30;
  if (b.bottom > foot) col.scrollTop += Math.max(0, Math.min(b.bottom - foot, b.top - box.top - SPEAKER_CLEAR));
  else if (b.top < box.top + SPEAKER_CLEAR) col.scrollTop -= box.top + SPEAKER_CLEAR - b.top;
  VIEW.at = el.getBoundingClientRect().top - box.top;
}

let centringUntil = 0;
function centreCurrent(smooth) {
  const col = $('transcript');
  const el = col.querySelector('.turn.current');
  if (!el) return;
  // the column takes back the way back's strip first, so the middle is the whole column's
  wayBack(false);
  // and a long passage's words or card take their caps and its boxes their level before it is measured (cardlarge)
  reachDraw();
  if (CARD_REACH && REACH.long) levelPairs();
  const colBox = col.getBoundingClientRect();
  const elBox = el.getBoundingClientRect();
  let top = col.scrollTop + (elBox.top - colBox.top) - (col.clientHeight - elBox.height) / 2;
  // a passage taller than the column with its notes field or its card under its words, as at 800px and
  // below, stands with the end of its words and the lowest of them in view, since centring it left the
  // field under the column's foot (16 October), as far as its speaker line allows
  const words = el.querySelector('.turn-text');
  const end = words ? words.getBoundingClientRect().bottom - 2 : 0;
  const under = words ? [$('en'), $('es-card')].filter((f) => el.contains(f)).map((f) => f.getBoundingClientRect())
    .filter((b) => b.top >= end) : [];
  const field = under.length ? under.reduce((a, b) => (b.bottom > a.bottom ? b : a)) : null;
  if (field && elBox.height > col.clientHeight - 24) {
    top = col.scrollTop + (field.bottom - colBox.top) - col.clientHeight + 24;
  }
  // and never so far that its speaker line goes into the column's faded head, or under the bars that
  // stick at the top of the page where it scrolls, measured: a passage taller than the column stands
  // with its name and time at the head (17 October, after the screenshot check at 360)
  const below = Math.max(colBox.top + SPEAKER_CLEAR, stickyBottom() + 8);
  const head = below < colBox.bottom - 48 ? below : colBox.top + SPEAKER_CLEAR;
  top = Math.min(top, col.scrollTop + (elBox.top - head));
  // under 'scroll' a long passage whose card would stand below the column's foot goes down until the card's
  // first statement and its foot stand whole above the column's faded foot, its speaker line going above the
  // head (cardlarge)
  const card = $('es-card');
  if (CARD_REACH === 'scroll' && REACH.long && el.contains(card)) {
    const reach = card.getBoundingClientRect().top + REACH.need - (colBox.bottom - 30 - 8);
    top = Math.max(top, col.scrollTop + reach);
  }
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const gliding = smooth && !still;
  // the turn is out of view while a long glide is still running, and the way back should not
  // blink into sight on its way there
  centringUntil = performance.now() + (gliding ? 800 : 120);
  REACH.settle = performance.now() + 1500;
  REACH.glide = gliding ? centringUntil : 0;
  col.scrollTo({ top: Math.max(0, top), behavior: gliding ? 'smooth' : 'auto' });
}

function drawTurn(opts) {
  const row = current();
  if (!row) return;
  // an interviewer note left open is kept by the move, and the three fields come back
  if (S.note) keepNote();
  // a turn left open for correction is cancelled by the move, before the column is rebuilt under it
  if (S.editing) closeEditor();
  closeTimeEdit();
  closeRowMenu();
  selBarHide();
  // the card saying the passage was changed in another window belongs to the passage it was said on
  if (!S.stale || S.stale.key !== row.key) hideStale();
  const rebuilt = S.sheetDrawn !== row.sheet;
  // the pieces held in her passages beside the one left go with the move (quotespan)
  const held = pendingRows();
  S.pending = [];
  if (rebuilt) drawTranscript(row.sheet);
  markCurrent(row);
  if (!rebuilt) for (const r of held) if (r.sheet === row.sheet) repaintRow(r);
  // with the find open, the occurrences on a sheet newly on screen take the washes
  if (rebuilt && findOpen()) findSheetDrawn();
  resetAI();
  S.prompt = placeholderLine();
  // the player follows the turn: a sheet change loads the recording first, then cues. A reload in
  // place after an assignment leaves it where it is and marks the playhead again on the new rows
  if (opts && opts.keepPlayer && S.audioSheet === row.sheet) {
    if ($('player').getAttribute('src')) markListening();
  } else loadAudio(row.sheet, row.seconds);
  // each statement with its own quote under it, as the turn holds them
  S.pairFocus = null;
  S.kqHover = null;
  S.kqFocus = null;
  // the quote lit by a statement's card goes with any move (16 October)
  S.kqLit = null;
  // the fields hold this passage's pairs from here, so its quotes are marked from them as they change.
  // It is named before they are drawn, so the count drawn with them takes this passage from the fields
  // and the one just left as saved, where it took this one twice and the other not at all (countdrift)
  S.pairsRow = row.key;
  drawPairs(rowPairs(row));
  S.kqDrawn = kqSignature();
  S.kqFar = kqFarKeys(row);
  $('en').value = row.en || '';
  S.dirty = false;
  $('saved').classList.remove('on');
  growNotes();
  drawAct();

  const rnd = S.data.rounds.find((r) => r.number === row.round);
  const inRound = rnd ? rnd.stops.findIndex((s) => `${s.sheet}:${s.row}` === row.key) + 1 : 0;
  // the speaker's name before the place, then with Work in rounds on the place in the round, and
  // with it off the passage among the sheet's participant passages, "Juno, passage 8 of 120" (15
  // October)
  const rounds = roundsHere();
  const passage = sheetPlace(row);
  $('rail-speaker').textContent = row.name;
  $('rail-turn').textContent = rounds ? inRound : passage.on;
  $('rail-turns').textContent = rounds ? (rnd ? rnd.stops.length : 0) : passage.of;
  // a narrow bar drops the speaker's name first, then the sheet's label, and keeps "passage" and the
  // numbers at every width. With rounds on it says "in round 1" for "in this round" and the round's
  // own count, and the tooltip keeps them all, "Juno, passage 7 of 16 in this round, round 1 of 3"
  // (16 October)
  const place = roundPlace(row, rnd);
  const placed = { name: row.name, at: inRound, of: rnd ? rnd.stops.length : 0, round: place.on, rounds: place.of, more: place.title };
  $('rail-place').title = rounds
    ? (place.title ? t('distil.bar.place_round_sheet', placed) : t('distil.bar.place_round', placed))
    : t('distil.bar.place', { name: row.name, place: passage.title });
  $('rail-round-n').textContent = place.on;
  $('rail-round').textContent = place.on;
  $('rail-rounds').textContent = place.of;
  $('rail-round-item').title = place.title;
  drawRoundBar();
  // the markers in the column say which round is now, and the clock shows this round's own count
  drawRoundMarks();
  clockRound(row.round);
  drawClock();
  $('rail-clock').title = clockTitle(rnd);
  // last, because at a narrow width the fields sit under the column and set the height it is
  // centred inside: a turn carrying notes and a quote opens both and leaves the column shorter
  centreCurrent(!rebuilt);
  // a freshly built column settles again as the serif loads, so the first centring is taken twice
  if (rebuilt) requestAnimationFrame(() => centreCurrent(false));
  // and a long passage once the serif has loaded, which moves its words, its quote and its card's fields, so the
  // card's place is measured on the words he reads (cardlarge)
  if (rebuilt && CARD_REACH && document.fonts && document.fonts.status !== 'loaded') {
    document.fonts.ready.then(() => { if (current() === row && REACH.long) centreCurrent(false); });
  }
  focusEntry();
  loadExamples();
  // Working together: the passage's comments, and the editor of another passage's put away (review.js)
  if (typeof rvwTurnMoved === 'function') rvwTurnMoved();
}

/* The statement of the pair being worked on takes the caret back after a move, after a click in
   the column and when a panel closes, the last pair's on a turn just opened. A turn or a timecode
   open for correction owns the caret while it is open, so none of those take it out of the box. */
function focusEntry() {
  if (guideHolds()) return;
  // an interviewer note open beside his passage keeps the caret
  if (S.note && !S.editing && !S.timeEdit) { $('note').focus({ preventScroll: true }); return; }
  if (S.editing || S.timeEdit) return;
  // the card stands in the scrolling columns since 17 October, so the caret goes in without a scroll
  // of its own, which would cut short the column's glide to the passage. With the statements hidden it
  // goes into the notes, and with both hidden it stays where it is (18 October)
  const pair = colsHidden('statements') ? null : workingPair();
  if (pair) pair.querySelector('.pair-es').focus({ preventScroll: true });
  else if (colsHidden('statements') && !colsHidden('notes')) $('en').focus({ preventScroll: true });
}

/* While the guidance's sheet stands open over the fields the keyboard goes into it, as its tool takes
   it there, and stays where it is inside it, so the caret never stands in a field under the sheet,
   which a reload with the sheet open, a passage opened from a board or a move by its keys left it in
   (17 October). Answers whether it did. */
function guideHolds() {
  if (!guideOpen() || $('work').hidden) return false;
  if (!$('guide').contains(document.activeElement)) $('guide-close').focus({ preventScroll: true });
  return true;
}

/* One way in and out of a turn: a dirty field is committed before the move, whether the move came
   from a button, a shortcut or a click on a speaker label in the column. The promise is what undo
   waits on when the action it is reversing belongs to another turn. `opts.count` is a step on by
   `Cmd + K`, the arrow or a click on a speaker's name, which flashes the count when it decides the
   turn it leaves, by a save on the way or by passing a blank turn (item 157). Every other move, a
   round marker's, the sheet switcher's and undo's, never does. */
function goTo(next, opts = {}) {
  if (next < 0 || next >= S.stops.length) {
    say(next < 0 ? t('distil.move.first_passage') : t('distil.move.last_passage'));
    return Promise.resolve();
  }
  // any move keeps an interviewer note left open, a click back on the turn being worked on too
  if (S.note) keepNote();
  // the turn it is already on, which is where a click inside an open editor used to land: with a
  // turn open for correction nothing is re-centred and nothing is refocused
  if (next === S.at) {
    if (!S.editing) { centreCurrent(true); focusEntry(); }
    return Promise.resolve();
  }
  const leaving = current();
  const states = (S.data.progress && S.data.progress.states) || {};
  const counted = !!opts.count && next > S.at && (S.dirty || (states[leaving.key] || 'unvisited') === 'unvisited');
  // a save that fails, a passage changed in another window among them, keeps him on the passage
  // with his words in the fields, and the move goes on only once it is saved (18 October)
  if (S.dirty) {
    return commit(leaving, false).then(() => {
      if (S.dirty) return;
      S.at = next;
      drawTurn();
      flashCount(counted);
      closeLeftRounds();
    });
  }
  S.at = next;
  drawTurn();
  flashCount(counted);
  closeLeftRounds();
  return Promise.resolve();
}

/* the passage a step lands on, past another speaker's turns (20 October), as move, afterCommit and the
   landing on a case each step in their own lines */
function stepTo(from, delta) {
  let k = from + delta;
  while (k >= 0 && k < S.stops.length && S.flat[S.stops[k]].other) k += delta;
  return k;
}

const move = (delta) => { let k = S.at + delta; while (k >= 0 && k < S.stops.length && S.flat[S.stops[k]].other) k += delta; return goTo(k, { count: delta > 0 }); };

/* ───────────────────────────────────────────────────── the sheets ── */

/* The sheets of the case, in workbook order. With more than one, the label in the top bar is a
   switcher: a choice goes to the first undecided participant turn on that sheet, or to its first
   turn when every one is decided, through goTo like any other move, so the column is redrawn, the
   player cued and a dirty field saved on the way. Rounds, the two bars and the passed rule are left
   as they are, because each of them already runs sheet by sheet. */
const sheetNames = () => (S.data ? S.data.sheets.map((s) => s.name) : []);
const sheetLabel = (name) => `"${name}" sheet`;

function sheetStop(sheet) {
  const states = (S.data && S.data.progress && S.data.progress.states) || {};
  let first = -1;
  for (let k = 0; k < S.stops.length; k += 1) {
    const row = S.flat[S.stops[k]];
    if (row.sheet !== sheet) continue;
    if (first < 0) first = k;
    if ((states[row.key] || 'unvisited') === 'unvisited') return k;
  }
  return first;
}

function fillSheetSwitch() {
  const names = sheetNames();
  const many = names.length > 1;
  const pick = $('sheet-switch');
  pick.innerHTML = '';
  if (many) {
    for (const name of names) {
      const option = new Option(sheetLabel(name), name);
      option.disabled = sheetStop(name) < 0;
      pick.appendChild(option);
    }
  }
  $('sheet-pick').hidden = !many;
  $('rail-sheet').hidden = many;
}

function drawSheetLabel(sheet) {
  $('rail-sheet').textContent = sheetLabel(sheet);
  if (!$('sheet-pick').hidden) $('sheet-switch').value = sheet;
  fitSheetSwitch();
  drawTpPick(sheet);
}

/* ─────────────────────────────────────────── the participant's timepoints ── */

/* A project of two or more timepoints (20 October, Adam's longitudinal model after Farr and Nizza
   2019): each timepoint of the participant is a set of their sheets, and the bar shows the timepoint
   of the sheet in front of him where the sheet switch stood, "T2" large and "Midsummer" smaller beside
   it. Its menu lists the project's timepoints in order, each with where it stands, and under one of two
   or more sheets its sheets. Choosing a timepoint goes to its first undecided passage, and one he has
   no interview at says so. Statements complete is the timepoint's, its counts the timepoint's alone. A
   project of one, and a server from before, send no `timepoints`, and the bar is the bar it always was. */
const tpList = () => {
  const list = S.data && S.data.progress && S.data.progress.timepoints;
  return Array.isArray(list) && list.length >= 2 ? list : null;
};
const tpOfSheet = (sheet) => {
  const list = tpList();
  return list ? (list.find((t) => (t.sheets || []).includes(sheet)) || list[0]) : null;
};
// the timepoint in front of him, by the current passage's sheet, else the one the column holds
const tpHere = () => {
  const row = current();
  return tpOfSheet((row && row.sheet) || S.sheetDrawn || '');
};
// the Statements complete mark the bar and the cards go by, the timepoint's in a project of two or more
const markOf = (p) => {
  const tp = tpList() ? tpHere() : null;
  return tp ? (tp.complete || null) : (p ? p.complete : null);
};
const tpName = (tp) => [tp.label, tp.description].filter(Boolean).join(' ');
const tpState = (tp) => (tp.state === 'none' ? t('distil.tp.not_interviewed') : tp.state === 'complete' ? t('distil.card.complete')
  : t('distil.card.passages_done', { done: tp.done, n: Number(tp.total) || 0 }));

function fillTpPick() {
  const list = tpList();
  $('tp-pick').hidden = !list;
  if (list) {
    $('sheet-pick').hidden = true;
    $('rail-sheet').hidden = true;
  }
  tpMenu(false);
}

function drawTpPick(sheet) {
  if (!tpList()) return;
  const tp = tpOfSheet(sheet);
  if (!tp) return;
  $('tp-now-label').textContent = tp.label;
  $('tp-now-desc').textContent = tp.description || '';
  $('tp-now').setAttribute('aria-label', t('distil.tp.now_label', { tp: tpName(tp), sheet }));
  // into another timepoint, the bar's counts and its Statements complete are that timepoint's
  if (S.tpDrawn !== tp.n) {
    S.tpDrawn = tp.n;
    if (S.data && S.data.progress && current()) drawProgress();
  }
}

function tpMenu(open) {
  const menu = $('tp-menu');
  if (!open) {
    menu.hidden = true;
    $('tp-now').setAttribute('aria-expanded', 'false');
    return;
  }
  const list = tpList();
  if (!list) return;
  const here = tpHere();
  const sheet = S.sheetDrawn || (current() || {}).sheet;
  const who = String((S.data && (S.data.case || S.data.name)) || '').replace(/^P\d+\s*-?\s*/, '').trim();
  let html = `<p class="tp-menu-head">${esc(who ? t('distil.tp.whose', { who }) : t('distil.tp.head'))}</p>`;
  for (const t of list) {
    const on = here && here.n === t.n;
    html += `<button type="button" class="ghost" role="menuitemradio" aria-checked="${on}" data-tp="${t.n}"${t.state === 'none' ? ' disabled' : ''}>`
      + `<span class="tp-tick" aria-hidden="true">${on ? '&#10003;' : ''}</span><span>${esc(t.label)}</span>`
      + `<span class="tp-item-desc">${esc(t.description || '')}</span><span class="tp-item-state">${esc(tpState(t))}</span></button>`;
    if ((t.sheets || []).length > 1) {
      for (const name of t.sheets) {
        html += `<button type="button" class="ghost tp-sheet" role="menuitemradio" aria-checked="${name === sheet}" data-sheet="${escAttr(name)}">`
          + `<span aria-hidden="true"></span><span class="tp-tick" aria-hidden="true">${name === sheet ? '&#10003;' : ''}</span>`
          + `<span>${esc(name)}</span><span></span></button>`;
      }
    }
  }
  menu.innerHTML = html;
  menu.hidden = false;
  $('tp-now').setAttribute('aria-expanded', 'true');
  const first = menu.querySelector('[aria-checked="true"]') || menu.querySelector('button:not(:disabled)');
  if (first) first.focus();
}

/* the first undecided passage of a timepoint's sheets, else its first passage, or -1 with none */
function tpStop(n) {
  const t = (tpList() || []).find((x) => x.n === n);
  if (!t) return -1;
  const states = (S.data && S.data.progress && S.data.progress.states) || {};
  let first = -1;
  for (let k = 0; k < S.stops.length; k += 1) {
    const row = S.flat[S.stops[k]];
    if (!(t.sheets || []).includes(row.sheet)) continue;
    if (first < 0) first = k;
    if (!row.other && (states[row.key] || 'unvisited') === 'unvisited') return k;
  }
  return first;
}

function toTimepoint(n) {
  const tp = (tpList() || []).find((x) => x.n === n);
  if (!tp) return Promise.resolve();
  const k = tpStop(n);
  if (k < 0) { say(t('distil.tp.not_at', { tp: tp.label })); return Promise.resolve(); }
  const here = tpHere();
  if (here && here.n === n) return Promise.resolve();
  return goTo(k);
}

function tpPickWire() {
  $('tp-now').onclick = (e) => { e.stopPropagation(); tpMenu($('tp-menu').hidden); };
  $('tp-menu').onclick = (e) => {
    e.stopPropagation();
    const b = e.target.closest('button');
    if (!b || b.disabled) return;
    tpMenu(false);
    if (b.dataset.sheet) toSheet(b.dataset.sheet);
    else toTimepoint(Number(b.dataset.tp));
  };
  $('tp-menu').onkeydown = (e) => {
    const items = [...$('tp-menu').querySelectorAll('button:not(:disabled)')];
    const at = items.indexOf(document.activeElement);
    if (e.key === 'Escape') { e.stopPropagation(); tpMenu(false); $('tp-now').focus(); }
    else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const next = items[(at + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length];
      if (next) next.focus();
    }
  };
  document.addEventListener('click', (e) => {
    if (!$('tp-menu').hidden && !e.target.closest('#tp-pick')) tpMenu(false);
  });
}

/* ─────────────────────────────────────────────────────── the stage tabs ── */

/* Idiograph's bar holds a fixed tab per stage (Adam, 20 October, in place of the steps of 18 October):
   Experiential statements, PETs and GETs, and in a project of two or more timepoints Experiential
   statements, PETs, LPETs, LGETs and Trajectories, after Farr and Nizza (2019). Never closed or doubled,
   since New Window gives two side by side. A tab shows only once its screen exists, and since 21 October
   (timepoints part 3) all five do, LGETs standing where GETs would, since a project of timepoints has no GETs
   at a single timepoint. The statements, PETs, GETs and Trajectories bars draw the same tabs from this list. */
const DS_STAGES = [
  { step: 'statements', one: true, many: true, built: true },
  { step: 'pets', one: true, many: true, built: true },
  { step: 'lpets', one: false, many: true, built: true },
  { step: 'gets', one: true, many: true, built: true },
  { step: 'lgets', one: false, many: true, built: true },
  { step: 'trajectories', one: false, many: true, built: true },
];

/* the stages a project shows, by its number of timepoints, a thematic analysis project's its coding and its
   themes alone (tadraw: no PETs, no timepoints, no trajectories in its phase one) */
function dsStages(project) {
  // and since codes (2 November 2026) its code list, a tab of its own between the two
  if (project && project.method === 'ta') return ['statements', 'codes', 'gets'];
  const many = !!(project && Array.isArray(project.timepoints) && project.timepoints.length >= 2);
  const lgets = DS_STAGES.find((s) => s.step === 'lgets');
  return DS_STAGES.filter((s) => s.built && (many ? s.many : s.one) && !(many && s.step === 'gets' && lgets.built))
    .map((s) => s.step);
}

/* a bar's tabs drawn for its project, `here` the stage in front of him, marked and holding the picker */
function dsTabsDraw(nav, project, here) {
  const bar = typeof nav === 'string' ? $(nav) : nav;
  if (!bar) return;
  const shown = dsStages(project);
  for (const tab of bar.querySelectorAll('.ds-tab')) {
    const step = tab.dataset.step;
    tab.hidden = !shown.includes(step);
    if (here === undefined) continue;
    tab.classList.toggle('on', step === here);
    const name = tab.querySelector('.ds-tab-name');
    if (step === here) name.setAttribute('aria-current', 'page');
    else name.removeAttribute('aria-current');
  }
  dsTabsFit(bar);
  // the bar's words fit again to the tabs it now holds
  if (typeof barFit === 'function' && bar.closest) barFit(bar.closest('.rail'));
}

/* the tabs' fade at their right while one waits past the edge, on their own row at a phone's width */
function dsTabsFit(bar) {
  if (!bar) return;
  bar.classList.toggle('over', bar.scrollLeft + bar.clientWidth < bar.scrollWidth - 1);
}

function dsTabsWatch(id) {
  const bar = $(id);
  if (!bar) return;
  bar.addEventListener('keydown', dsTabsKeys);
  bar.addEventListener('scroll', () => dsTabsFit(bar), { passive: true });
  if (window.ResizeObserver) new ResizeObserver(() => dsTabsFit(bar)).observe(bar);
}

/* the keys along a bar's tabs: Left and Right move between them, Home and End to the first and last,
   each tab's name and picker a stop of its own */
function dsTabsKeys(e) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key) || MOD(e) || e.altKey) return;
  const bar = e.currentTarget;
  const stops = [...bar.querySelectorAll('.ds-tab:not([hidden]) button')].filter((b) => b.offsetParent !== null);
  const at = stops.indexOf(document.activeElement);
  if (at < 0) return;
  e.preventDefault();
  const to = e.key === 'Home' ? 0 : e.key === 'End' ? stops.length - 1
    : Math.max(0, Math.min(stops.length - 1, at + (e.key === 'ArrowRight' ? 1 : -1)));
  stops[to].focus();
  stops[to].scrollIntoView({ block: 'nearest', inline: 'nearest' });
}

/* The participant picker in the statements tab: the participants of the project, by their labels, in
   case order, the one in front ticked, each opening on its statements, and Open in a new window beside
   each. Asked for each time it opens, and nothing is written. */
const ES_WHO = { ask: 0, list: [] };

async function esWhoMenu(open) {
  const menu = $('es-whomenu');
  ES_WHO.ask += 1;
  if (!open || !S.data) {
    menu.hidden = true;
    $('es-who').setAttribute('aria-expanded', 'false');
    return;
  }
  const ask = ES_WHO.ask;
  tpMenu(false);
  esWhoDraw([]);
  menu.hidden = false;
  $('es-who').setAttribute('aria-expanded', 'true');
  let data;
  try {
    data = await api('/api/participants', { workbook: S.data.path });
  } catch (err) {
    if (ask === ES_WHO.ask) esWhoDraw([], needsRestart(err) ? RESTART_LINE : err.message);
    return;
  }
  if (ask !== ES_WHO.ask) return;
  esWhoDraw(data.participants || []);
  const first = menu.querySelector('.ds-who-row.on') || menu.querySelector('button');
  if (first) first.focus();
}

function esWhoDraw(list, said = '') {
  ES_WHO.list = list;
  const menu = $('es-whomenu');
  let html = `<p class="tp-menu-head">${esc(t('distil.who.head'))}</p>`;
  // each participant with their picture, label and the pen portrait's first two lines (pbiobuild, layout A)
  const people = list.some((p) => p.person);
  list.forEach((p, i) => {
    const who = people ? `${personPic(p.person, 32)}${ppMenuText(p.case, p.person)}` : `<span>${esc(p.case)}</span>`;
    html += `<div class="ds-who-item"><button type="button" class="ghost ds-who-row${p.current ? ' on' : ''}" role="menuitemradio"`
      + ` aria-checked="${p.current}" data-who="${i}"${p.person && p.person.portrait ? ` title="${escAttr(p.person.portrait)}"` : ''}>`
      + `<span class="tp-tick" aria-hidden="true">${p.current ? '&#10003;' : ''}</span>`
      + `${who}</button><button type="button" class="ghost small ds-who-window" data-window="${i}"`
      + ` title="${escAttr(t('distil.who.window_title', { who: p.case }))}">${esc(t('distil.who.window'))}</button></div>`;
  });
  if (said) html += `<p class="th-vsaid">${esc(said)}</p>`;
  menu.classList.toggle('pp-menu', people);
  menu.innerHTML = html;
  // under the chooser in the path, and with the participants' pictures and portraits hung clear of the band's foot,
  // which the label can make two lines tall (pbiobuild, as drawn)
  const box = $('es-who').getBoundingClientRect();
  const foot = people && $('band') ? $('band').getBoundingClientRect().bottom + 10 : 0;
  menu.style.left = `${Math.max(8, Math.min(box.left - 6, window.innerWidth - menu.offsetWidth - 8))}px`;
  menu.style.top = `${Math.max(box.bottom + 6, foot)}px`;
}

/* another participant from the picker: the passage in front saved first, then theirs opened on their
   statements, the way back to the case list */
async function esWhoGo(p) {
  esWhoMenu(false);
  if (!p || p.current || !S.data) return;
  if (S.dirty && current()) {
    await commit(current(), false);
    if (S.dirty) return;
  }
  navGo(() => esWhoGo(p), () => openCase(p.path));
}

function esWhoWire() {
  $('es-who').onclick = (e) => { e.stopPropagation(); esWhoMenu($('es-whomenu').hidden); };
  $('es-whomenu').onclick = (e) => {
    e.stopPropagation();
    const win = e.target.closest('[data-window]');
    if (win) {
      const p = ES_WHO.list[Number(win.dataset.window)];
      esWhoMenu(false);
      if (p) openInWindow({ screen: 'work', path: p.path });
      return;
    }
    const b = e.target.closest('[data-who]');
    if (b) esWhoGo(ES_WHO.list[Number(b.dataset.who)]);
  };
  $('es-whomenu').onkeydown = (e) => {
    const items = [...$('es-whomenu').querySelectorAll('button')];
    const at = items.indexOf(document.activeElement);
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); esWhoMenu(false); $('es-who').focus(); }
    else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const next = items[(at + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length];
      if (next) next.focus();
    }
  };
  document.addEventListener('click', (e) => {
    if (!$('es-whomenu').hidden && !e.target.closest('#es-whomenu, #es-who')) esWhoMenu(false);
  });
  dsTabsWatch('es-steps');
}

/* The switch is as wide as the sheet it shows, its chevron's room after it, where a select left to
   itself is as wide as its longest sheet. So the bar keeps that room for the case name, and a case of
   two sheets fits a phone's width as a case of one does (13 October, later). */
function fitSheetSwitch() {
  const pick = $('sheet-switch');
  if ($('sheet-pick').hidden || !pick.options.length) { pick.style.width = ''; return; }
  const on = pick.options[pick.selectedIndex] || pick.options[0];
  const cs = getComputedStyle(pick);
  fitSheetSwitch.ctx = fitSheetSwitch.ctx || document.createElement('canvas').getContext('2d');
  fitSheetSwitch.ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
  const text = fitSheetSwitch.ctx.measureText(on.text).width;
  pick.style.width = `${Math.ceil(text + parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight)) + 2}px`;
}

function toSheet(sheet) {
  const row = current();
  if (!row) return Promise.resolve();
  const k = sheetStop(sheet);
  if (sheet === row.sheet || k < 0) {
    if (k < 0) say(t('distil.move.no_passages', { sheet }));
    drawSheetLabel(row.sheet);
    return Promise.resolve();
  }
  return goTo(k);
}

function stepSheet(delta) {
  const row = current();
  if (!row) return Promise.resolve();
  const names = sheetNames().filter((name) => sheetStop(name) >= 0);
  const next = names[names.indexOf(row.sheet) + delta];
  if (!next) {
    say(delta < 0 ? t('distil.move.first_sheet') : t('distil.move.last_sheet'));
    return Promise.resolve();
  }
  return toSheet(next);
}

/* Two bars. The line under the top bar is the whole case, participant turns decided over all of
   them, so it moves on every Next, every Skip and every turn moved past. The short one beside "n of m
   in this round" is the round in front of him. A turn is decided once it is saved, skipped or passed.
   A server that has not been restarted sends no counts, and the states it does send answer instead. */
function barNumbers(p, rnd) {
  const states = p.states || {};
  const decided = (key) => (states[key] || 'unvisited') !== 'unvisited';
  const all = Object.keys(states);
  const tally = rnd && (p.roundTurns || []).find((r) => r.number === rnd.number);
  const keys = rnd ? rnd.stops.map((s) => `${s.sheet}:${s.row}`) : [];
  // in a project of two or more timepoints the line is the timepoint's, as its Statements complete is
  const tp = typeof tpList === 'function' && tpList() ? tpHere() : null;
  if (tp) {
    return { caseDone: Number(tp.done) || 0, caseTotal: Number(tp.total) || 0,
      roundDone: tally ? tally.decided : keys.filter(decided).length, roundTotal: tally ? tally.total : keys.length };
  }
  return {
    caseDone: typeof p.turnsDone === 'number' ? p.turnsDone : all.filter(decided).length,
    caseTotal: typeof p.turnsTotal === 'number' ? p.turnsTotal : all.length,
    roundDone: tally ? tally.decided : keys.filter(decided).length,
    roundTotal: tally ? tally.total : keys.length,
  };
}

function currentRound() {
  const row = current();
  return row ? S.data.rounds.find((r) => r.number === row.round) : null;
}

/* The round's place in the bar is the sheet's: "round 2 of 4" on the sheet in front of him, its
   name already beside it in a case with more than one, and the case figure in the tooltip, "round
   6 of 9 in the case". A case with one sheet reads exactly as it always did, and a server from
   before the rounds belonged to a sheet sends no place on one, so the case's numbers stand. */
function roundPlace(row, rnd) {
  const all = S.data.rounds.length;
  const number = (row && row.round) || 0;
  if (!rnd || typeof rnd.on_sheet !== 'number') return { on: number, of: all, title: '' };
  const of = typeof rnd.sheet_rounds === 'number' ? rnd.sheet_rounds
    : S.data.rounds.filter((r) => r.sheet === rnd.sheet).length;
  const many = new Set(S.data.rounds.map((r) => r.sheet)).size > 1;
  return { on: rnd.on_sheet, of, title: many ? t('distil.bar.round_of_case', { round: number, all }) : '' };
}

/* The passage's place on its sheet, among that sheet's participant passages, "passage 8 of 120",
   which the bar shows with Work in rounds off, and in a case of more than one sheet its place in the
   case after it in the tooltip, "passage 8 of 120 on this sheet, 128 of 300 in the case", as the
   round's place gives the case's figure (15 October). */
function sheetPlace(row) {
  const here = S.stops.filter((i) => S.flat[i].sheet === row.sheet);
  const on = here.indexOf(row.i) + 1;
  const many = new Set(S.stops.map((i) => S.flat[i].sheet)).size > 1;
  const line = t('distil.bar.passage_of', { on, of: here.length });
  return { on, of: here.length, title: many ? t('distil.bar.passage_of_sheet', { on, of: here.length, at: row.pos + 1, all: S.stops.length }) : line };
}

/* Every part of the bar that belongs to rounds shows with Work in rounds on and hides with it off,
   as a case opens and as Settings saves: the words "in this round", or "in round 1" on a narrow bar,
   and the short bar, the round's count, the clock and its reset, and the line to today's target
   (15 October). "passage" stands before the number either way (16 October). drawMark hides the
   counts again once the phase is finished. */
function drawRoundsShown() {
  const on = roundsHere();
  $('work').classList.toggle('rounds-off', !on);
  for (const id of ['rail-in-round', 'rail-in-round-n', 'round-bar', 'rail-clock-sep', 'rail-clock', 'rail-clock-reset']) $(id).hidden = !on;
}

const share = (done, total) => `${total ? Math.round((done / total) * 1000) / 10 : 0}%`;

function drawRoundBar(n) {
  n = n || barNumbers(S.data.progress, currentRound());
  $('round-fill').style.width = share(n.roundDone, n.roundTotal);
  $('round-bar').title = t('distil.bar.round_done', { done: n.roundDone, total: n.roundTotal });
}

function drawProgress() {
  const p = S.data.progress;
  const n = barNumbers(p, currentRound());
  $('progress-fill').style.width = share(n.caseDone, n.caseTotal);
  // decided, the bar's own word, "120 of 300 passages decided" (16 October)
  $('progress-strip').title = t('distil.bar.decided', { done: n.caseDone, total: n.caseTotal });
  drawRoundBar(n);
  const left = Math.max(0, p.dailyTarget - p.todayRounds);
  $('rail-daily').textContent = left === 0
    ? (p.streak ? t('distil.bar.today_done_streak', { streak: p.streak }) : t('distil.bar.today_done'))
    : t('distil.bar.today_left', { n: left });
  drawMark(n, p);
  // a round closed turns its marker to done where it stands
  drawRoundMarks();
  // and a passage decided takes its bar at the edge of its words
  drawDoneMarks();
}

/* ─────────────────────────────────────────────── the phase complete ── */

/* Working through the transcript to write the statements is a phase, and it ends. Once every
   participant turn is decided the round counts give way to one quiet control, Mark complete, and
   once it is marked the bar says so, with a small tick and the date, in their place. The thin line
   under the bar goes, and so does the line to today's target, while the clock stays. The numbers
   stay in the tooltip. The statements stay editable: a turn undecided while it is marked, which an
   untrim can bring back, brings the counts back beside the mark, so nothing is hidden. The mark is
   `complete` in the progress file, the time or nothing, and a server from before it sends no such
   key, so the bar is the bar it always was. */
/* the day and the time of an ISO time the server wrote, read as it is written, with no time zone
   brought into it: "3 Oct 2026" and "14:05", the day through Intl (i18n.js's tDate) since i18ncore and
   the time through tTime since fmtsweep, so both follow Language and formats */
function whenOf(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/.exec(String(iso || ''));
  if (!m) return { day: '', time: '' };
  const day = tDay(iso);
  return { day: day ? tDate(day, { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }) : '',
    time: m[4] ? tTime(new Date(Date.UTC(2000, 0, 1, Number(m[4]), Number(m[5]))), { timeZone: 'UTC' }) : '' };
}
const dayOf = (iso) => whenOf(iso).day;

function drawMark(n, p) {
  n = n || barNumbers(p, currentRound());
  const known = p.complete !== undefined;
  const mark = typeof markOf === 'function' ? markOf(p) : p.complete;
  const marked = !!mark;
  const allDone = n.caseTotal > 0 && n.caseDone >= n.caseTotal;
  const open = Math.max(0, n.caseTotal - n.caseDone);
  const markable = known && !marked && allDone;
  // the counts stand unless the case is finished: marked with every turn decided, or ready to mark
  const counts = !(marked && allDone) && !markable;
  $('rail-mark').hidden = !marked;
  $('rail-markable').hidden = !markable;
  $('rail-mark-sep').hidden = !(marked && !allDone);
  // and with Work in rounds off the round's count and the line to today's target never show
  const rounds = roundsHere();
  $('rail-place').hidden = !counts;
  $('rail-round-item').hidden = !counts || !rounds;
  // with the place gone to the status bar (21 October) the rule after the sheet's label stands only before
  // something, the mark or the round's counts and clock, and the rule that stood between the place and the
  // round's counts has nothing to part. Since 26 October 2026 it stands before the mark alone: the clock brings
  // its own rule, so with rounds alone this one stood beside it, two rules with nothing between
  $('es-sheet-sep').hidden = !(marked || markable);
  $('rail-round-sep').hidden = true;
  $('rail-daily').hidden = marked || !rounds;
  $('work').classList.toggle('es-complete', marked && allDone);
  $('work').classList.toggle('es-reopened', marked && !allDone);
  // decided, the word the bar's own tooltip says (16 October)
  const place = rounds ? t('distil.bar.decided_round', { done: n.caseDone, total: n.caseTotal, round: $('rail-round').textContent,
    rounds: $('rail-rounds').textContent }) : t('distil.bar.decided', { done: n.caseDone, total: n.caseTotal });
  if (marked) {
    const when = whenOf(mark);
    $('rail-mark').classList.toggle('undecided', !allDone);
    // "Complete · 2 passages undecided", the word passages going below 1140px and the rest below 940px
    $('rail-mark-left').innerHTML = allDone ? '' : t('distil.bar.mark_left_html', { n: open });
    $('rail-mark-date').textContent = allDone ? when.day : '';
    const markedSaid = when.time ? t('distil.bar.marked_at', { day: when.day, time: when.time }) : t('distil.bar.marked_on', { day: when.day });
    $('rail-mark').title = allDone ? t('distil.bar.mark_title', { marked: markedSaid, place })
      : t('distil.bar.mark_title_still', { marked: markedSaid, still: t('distil.bar.undecided', { n: open }), place });
  }
  if (markable) $('rail-markable').title = t('distil.bar.markable_title', { place });
}

/* `/api/complete` writes the mark and nothing else, never the workbook. A card that closes the
   last round says so once it is marked, and the bar takes the answer at once. */
async function markComplete(op = 'mark') {
  if (!S.data || S.marking) return;
  S.marking = true;
  const path = S.data.path;
  const long = typeof tpList === 'function' && !!tpList();
  const was = !!(long ? markOf(S.data.progress) : S.data.progress && S.data.progress.complete);
  // the timepoint in front of him, in a project of two or more
  const tp = long ? tpHere() : null;
  try {
    const data = await api('/api/complete', { workbook: path, op, ...(tp ? { timepoint: tp.n } : {}) });
    if (!S.data || S.data.path !== path) return;
    S.data.progress = data.progress;
    drawProgress();
    // pressed from the bar, with no card on screen, on a case finished before, the mark fires the
    // third level of confetti once. The case-complete card fired it when it opened
    if (op === 'mark' && data.complete && !was && $('round-done').hidden) confetti(3);
    if (!$('round-done').hidden) drawDoneMark(S.doneFinished);
    if (op === 'reopen') say(t('distil.mark.reopened'), 2400);
    else if ($('round-done').hidden) say(t('distil.mark.marked'), 2400);
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
  finally { S.marking = false; }
}

/* the card behind a click on the bar's line: when it was marked, and Reopen beside Cancel */
function openComplete() {
  const p = S.data && S.data.progress;
  const mark = p && (typeof markOf === 'function' ? markOf(p) : p.complete);
  if (!mark) return;
  const when = whenOf(mark);
  $('complete-line').textContent = when.time ? t('distil.mark.line_at', { day: when.day, time: when.time }) : t('distil.mark.line', { day: when.day });
  show('complete');
}

async function reopenComplete() {
  hide('complete');
  await markComplete('reopen');
  focusEntry();
}

/* The case-complete card, the one the last round closes with: Mark complete is its filled button
   until it is pressed, then the card says the case is marked and the way back to the list is the
   filled one. A server from before the mark offers no button. */
function drawDoneMark(finished) {
  const p = S.data.progress;
  const known = p.complete !== undefined;
  const mark = typeof markOf === 'function' ? markOf(p) : p.complete;
  const offer = !!finished && known && !mark;
  $('done-mark').hidden = !offer;
  $('done-marked').hidden = !(finished && mark);
  $('done-marked').textContent = finished && mark ? t('distil.mark.done_marked', { day: dayOf(mark) }) : '';
  $('done-library').classList.toggle('primary', !offer);
  $('done-library').classList.toggle('ghost', offer);
}

/* ─────────────────────────────────────────────────────────── audio ── */

/* The recording the sheet was transcribed from, served with Range support so the scrubber works.
   A missing or evicted file is one quiet line and nothing else changes.

   The controls belong to the app. The audio element is the engine and never shows: the button, the
   bar and the two times are drawn from its events, so a seek from anywhere lands on them. */

const PLAY_GLYPH = '▶';
const PAUSE_GLYPH = '❚❚';

/* A timecode, the project's way (Adam, 28 October): 75:12 folds the hours into the minutes, 1:15:12
   writes them once past the hour, the default, and 01:15:12 always. The server writes the rows' and the
   cards' the same way (workbook.timecode), so the player's clock and the box's prefill agree with the
   margin. A project from a server before it carries no `timecodes` and reads 1:15:12. */
const TIMECODES = ['75:12', '1:15:12', '01:15:12'];
const timecodesOf = (p) => (p && TIMECODES.includes(p.timecodes) ? p.timecodes : '1:15:12');

function timecode(seconds, form) {
  const s = Math.max(0, Math.floor(Number(seconds) || 0));
  const two = (n) => String(n).padStart(2, '0');
  if (form === '75:12') return `${two(Math.floor(s / 60))}:${two(s % 60)}`;
  const h = Math.floor(s / 3600);
  const rest = `${two(Math.floor((s % 3600) / 60))}:${two(s % 60)}`;
  if (form === '01:15:12') return `${two(h)}:${rest}`;
  return h ? `${h}:${rest}` : rest;
}

const caseTimecodes = () => timecodesOf(S.data && S.data.project);

function drawPlayer() {
  const player = $('player');
  const duration = Number.isFinite(player.duration) && player.duration > 0 ? player.duration : 0;
  // before the file has said how long it is, the cued timecode is what the elapsed shows
  const at = player.readyState >= 1 ? (player.currentTime || 0) : (S.cueAt || 0);
  const share = duration ? Math.max(0, Math.min(1, at / duration)) : 0;
  $('player-elapsed').textContent = timecode(at, caseTimecodes());
  $('player-total').textContent = duration ? timecode(duration, caseTimecodes()) : '--:--';
  $('player-fill').style.width = `${share * 100}%`;
  $('player-knob').style.left = `${share * 100}%`;
  const playing = !player.paused && !player.ended;
  $('player-play').textContent = playing ? PAUSE_GLYPH : PLAY_GLYPH;
  $('player-play').setAttribute('aria-label', playing ? t('distil.audio.pause') : t('distil.audio.play'));
  $('player-bar').classList.toggle('playing', playing);
}

/* The player follows the turn. The turn's timecode shows at once and the position is taken as soon
   as the metadata is there. Playing carries on from the new place, paused stays paused: a turn
   change never starts the audio, and a turn with no timecode leaves the player where it is.

   Any cue moves the playhead mark to the cued turn, playing or paused, so the mark and the clock
   never say different things. */
function cueAudio(seconds) {
  if (seconds === null || seconds === undefined) return;
  markTurnAt(seconds);
  const player = $('player');
  if (!player.getAttribute('src')) return;
  const said = Math.max(0, Number(seconds) || 0);
  // a cue to anywhere else ends the toggle a timecode click set up, so that timecode plays from
  // its own place again rather than pausing
  if (S.seekAt !== null && S.seekAt !== said) S.seekAt = null;
  // the recording's offset, plus or minus, added to every time code (20 October)
  const at = Math.max(0, said + (S.audioOffset || 0));
  S.cueAt = at;
  drawPlayer();
  const go = () => {
    if (S.cueAt !== at) return; // a later turn has already asked for somewhere else
    try { player.currentTime = at; } catch { /* the file is still arriving */ }
    drawPlayer();
  };
  if (player.readyState >= 1) go();
  else player.addEventListener('loadedmetadata', go, { once: true });
}

/* The player shows once a recording is found, and a sheet with none shows nothing at the foot (17 October),
   where a line said "No recording found for" the sheet on every case without one. Its note still holds the
   server's words, which a press on a timecode or Space says at the foot, as a line after an act. A demo
   participant's recording is copied in by the server as it answers, never made (recvoices, 12 November 2026). */
async function loadAudio(sheet, cueSeconds) {
  if (S.audioSheet === sheet) { cueAudio(cueSeconds); return; }
  S.audioSheet = sheet;
  const player = $('player');
  player.pause();
  player.removeAttribute('src');
  S.cueAt = 0;
  S.audioOffset = 0;
  $('player-offset').hidden = true;
  S.listening = null;
  $('player-bar').hidden = true;
  $('player-wrap').hidden = true;
  $('player-note').textContent = '';
  drawPlayer();
  try {
    const data = await api(`/api/audio?${new URLSearchParams({ path: S.data.path, sheet })}`);
    if (S.audioSheet !== sheet) return;
    if (data.found) {
      player.src = data.url;
      S.audioOffset = Number(data.offset) || 0;
      drawOffsetButton();
      $('player-bar').hidden = false;
      $('player-wrap').hidden = false;
      $('player-note').textContent = data.name;
      // the whole name under the pointer, where a narrow window cuts it at its end
      $('player-note').title = data.name;
      cueAudio(cueSeconds);
    } else {
      $('player-wrap').hidden = true;
      $('player-note').textContent = data.note || t('distil.audio.none');
    }
  } catch {
    if (S.audioSheet === sheet) {
      $('player-wrap').hidden = true;
      $('player-note').textContent = t('distil.audio.none');
    }
  }
}

/* Clicking a timecode in the margin plays from there, as it always did. The same timecode again
   pauses, and a click after that carries on from where it stopped rather than going back to the
   timecode, because a pause is a place he has chosen. Another timecode jumps there and keeps
   playing. Any other cue, and a drag on the scrub bar, end the toggle. */
function playFrom(seconds) {
  const player = $('player');
  if (!player.getAttribute('src')) { say($('player-note').textContent || t('distil.audio.none')); return; }
  const from = Math.max(0, Number(seconds) || 0);
  if (S.seekAt !== null && S.seekAt === from) { togglePlay(); return; }
  S.seekAt = from;
  cueAudio(from);
  const go = () => {
    const played = player.play();
    if (played && played.catch) played.catch(() => say(t('distil.audio.would_not_play')));
  };
  if (player.readyState >= 1) go();
  else player.addEventListener('loadedmetadata', go, { once: true });
}

function togglePlay() {
  const player = $('player');
  if (!player.getAttribute('src')) { say($('player-note').textContent || t('distil.audio.none')); return; }
  if (player.paused || player.ended) {
    const played = player.play();
    if (played && played.catch) played.catch(() => say(t('distil.audio.would_not_play')));
  } else {
    player.pause();
  }
}

function scrubTo(clientX) {
  const player = $('player');
  const box = $('player-scrub').getBoundingClientRect();
  if (!box.width || !Number.isFinite(player.duration) || !player.duration) return;
  const share = Math.max(0, Math.min(1, (clientX - box.left) / box.width));
  S.cueAt = share * player.duration;
  S.seekAt = null;
  try { player.currentTime = S.cueAt; } catch { /* the file is still arriving */ }
  drawPlayer();
}

/* Five seconds either way, from wherever the clock sits. `Cmd + Left` and `Cmd + Right` reach this
   from inside the fields too, because the plain arrows belong to the caret. The playhead mark and
   the elapsed time both move at once, so nothing on screen lags the recording. */
const AUDIO_STEP = 5;

function nudgeAudio(delta) {
  const player = $('player');
  if (!player.getAttribute('src')) { say($('player-note').textContent || t('distil.audio.none')); return; }
  const duration = Number.isFinite(player.duration) && player.duration > 0 ? player.duration : 0;
  const from = player.readyState >= 1 ? (player.currentTime || 0) : (S.cueAt || 0);
  const at = Math.max(0, duration ? Math.min(from + delta, duration) : from + delta);
  S.cueAt = at;
  S.seekAt = null;
  try { player.currentTime = at; } catch { /* the file is still arriving */ }
  markTurnAt(heardAt(at));
  drawPlayer();
}

/* The recording's place as the transcript's time codes have it, its offset taken off */
const heardAt = (at) => at - (S.audioOffset || 0);

/* The offset beside the recording's name, "Offset" while there is none, and its card (20 October): a
   number of seconds, plus or minus, which playback adds to every time code, kept beside the
   recording in the case, so it holds across a restart and on the PETs and GETs screens too. */
const offsetWords = (v) => (v ? t('distil.audio.offset_value', { value: `${v > 0 ? '+' : '\u2212'}${String(Math.abs(Math.round(v * 100) / 100))}` })
  : t('distil.audio.offset'));

function drawOffsetButton() {
  $('player-offset').textContent = offsetWords(S.audioOffset || 0);
  $('player-offset').hidden = false;
}

function openOffset() {
  if (!S.data || !S.audioSheet) return;
  $('offset-of').textContent = `${$('player-note').textContent} · ${S.audioSheet}`;
  $('offset-seconds').value = String(S.audioOffset || 0);
  $('offset-said').hidden = true;
  show('offset');
  $('offset-seconds').focus();
  $('offset-seconds').select();
}

async function saveOffset() {
  const sheet = S.audioSheet;
  try {
    const data = await api('/api/audio-offset', { path: S.data.path, sheet, offset: $('offset-seconds').value });
    hide('offset');
    if (S.audioSheet !== sheet) return;
    S.audioOffset = Number(data.offset) || 0;
    drawOffsetButton();
    const now = current();
    if (now && now.sheet === sheet) cueAudio(now.seconds);
  } catch (err) {
    $('offset-said').textContent = needsRestart(err) ? RESTART_LINE : err.message;
    $('offset-said').hidden = false;
  }
}

/* ──────────────────────────────────────────────────────── playhead ── */

/* While the recording plays, the turn its clock is inside carries a mark in the margin. The turn
   being worked on never moves with it: this only carries one class from turn to turn, and the
   column glides to keep the marked turn in sight unless a selection or a drag on the scrub bar is
   under way. A cue with no play leaves the mark where it is, so moving between turns with the
   audio paused, and pausing itself, both leave it where it stopped. */

function playSpans() {
  if (S.spansSheet !== S.sheetDrawn) {
    S.spans = S.flat
      .filter((r) => r.sheet === S.sheetDrawn && r.seconds !== null && r.seconds !== undefined)
      .map((r) => ({ i: r.i, at: Number(r.seconds) }));
    S.spansSheet = S.sheetDrawn;
    S.spanAt = 0;
  }
  return S.spans;
}

/* A turn's span runs from its own timecode to the next one, the interviewer's turns included.
   The search walks from where it was last, so a second of playing costs a step or two. */
function turnAtTime(seconds) {
  const spans = playSpans();
  if (!spans.length || seconds < spans[0].at) return null;
  let k = Math.min(Math.max(S.spanAt, 0), spans.length - 1);
  while (k + 1 < spans.length && spans[k + 1].at <= seconds) k += 1;
  while (k > 0 && spans[k].at > seconds) k -= 1;
  S.spanAt = k;
  return spans[k];
}

/* The column moves for the playhead only while the clock is running, never mid-selection or
   mid-drag on the scrub bar, and never for the turn being worked on, which centreCurrent owns. */
function followListening(el) {
  const player = $('player');
  if (player.paused || player.ended || S.scrubbing || S.selecting) return;
  if (el.classList.contains('current')) return;
  const sel = window.getSelection();
  if (sel && sel.rangeCount && !sel.isCollapsed
      && $('transcript').contains(sel.getRangeAt(0).commonAncestorContainer)) return;
  const col = $('transcript');
  const colBox = col.getBoundingClientRect();
  const box = el.getBoundingClientRect();
  if (box.top >= colBox.top + 48 && box.bottom <= colBox.bottom - 48) return;
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const top = col.scrollTop + (box.top - colBox.top) - (col.clientHeight - box.height) / 2;
  col.scrollTo({ top: Math.max(0, top), behavior: still ? 'auto' : 'smooth' });
}

/* One class moves from turn to turn and nothing else changes, so the turn being worked on and
   everything in the fields stay exactly where they were. */
function markTurn(i) {
  if (i === null || i === undefined || i === S.listening) return;
  const box = $('transcript-rows');
  const was = box.querySelector('.turn.listening');
  if (was) was.classList.remove('listening');
  S.listening = i;
  const el = box.querySelector(`.turn[data-i="${i}"]`);
  if (!el) return;
  el.classList.add('listening');
  followListening(el);
}

function markTurnAt(seconds) {
  const span = turnAtTime(Math.max(0, Number(seconds) || 0));
  if (span) markTurn(span.i);
}

function markListening() { markTurnAt(heardAt($('player').currentTime || 0)); }

/* ───────────────────────────────────────────────────────── commits ── */

async function commit(row, advance) {
  row = row || current();
  try {
    // the pairs, and the two cells they make beside them for a server from before the pairs
    const pairs = pairsNow();
    const cells = pairsToCells(pairs);
    // `v` is the passage as this page last read it, so a save over one changed in another window is
    // refused with nothing written (18 October)
    const data = await api('/api/commit', {
      path: S.data.path, sheet: row.sheet, row: row.row, round: row.round,
      pairs, es: cells.es, en: $('en').value, kq: cells.kq, away: awayTally(), v: row.v,
    });
    awayReset();
    if (data.v) row.v = data.v;
    hideStale();
    row.pairs = Array.isArray(data.pairs) ? data.pairs : rowPairs({ es: cells.es, kq: cells.kq });
    row.es = row.pairs.map((p) => p.es).filter((t) => t.trim()).join('\n');
    row.kq = row.pairs.map((p) => p.kq).filter((t) => t.trim()).join('\n');
    row.unpaired = !!data.unpaired;
    row.en = $('en').value;
    S.data.progress = data.progress;
    S.dirty = false;
    // the code list read again, for the suggestions' counts and a name typed as New code (codes.js)
    if (typeof cxCodesRead === 'function' && tMethodNow() === 'ta') cxCodesRead(S.data.path);
    clearPending(true);
    $('saved').textContent = t('distil.save.saved');
    $('saved').classList.add('on');
    setTimeout(() => $('saved').classList.remove('on'), 1600);
    drawProgress();
    drawAct();
    drawToPair();
    if (advance) afterCommit(row);
  } catch (err) {
    if (err.data && err.data.stale && row === current()) showStale(row, err.data.stale);
    else say(err.message, 9000);
  }
}

/* A passage changed since this page loaded it, by another window, an agent or anything else that writes
   the workbook (18 October, the words Adam's of 19 October). The save is refused with nothing written, the
   fields keep what was typed, and the card says so in one line with two buttons. Reload loads the passage
   as it now is into the fields, and what was typed stays under the line in plain text he can copy from,
   with Put my words back one click away. Overwrite saves what was typed over the change. Any move off the
   passage, and any save that goes through, puts the card away. */
function showStale(row, now) {
  S.stale = { key: row.key, now, mine: null };
  $('stale').hidden = false;
  $('stale-line').textContent = STALE_LINE;
  $('stale-acts').hidden = false;
  $('stale-mine').hidden = true;
  $('stale').scrollIntoView({ block: 'nearest' });
}

const STALE_LINE = t('distil.save.stale');
const STALE_RELOADED = t('distil.save.stale_reloaded');

function hideStale() {
  S.stale = null;
  if ($('stale')) $('stale').hidden = true;
}

/* the fields drawn from `words`, pairs and notes, the passage's own record left as it is saved */
function drawFieldsFrom(row, words) {
  const kept = {};
  for (const k of ['es', 'en', 'kq', 'pairs', 'unpaired']) kept[k] = row[k];
  row.pairs = words.pairs;
  row.es = words.pairs.map((p) => p.es).filter((x) => x.trim()).join('\n');
  row.kq = words.pairs.map((p) => p.kq).filter((x) => x.trim()).join('\n');
  row.en = words.en;
  try { drawTurn({ keepPlayer: true }); } finally { Object.assign(row, kept); }
}

/* the passage as it now is loaded into the fields, what was typed kept under the line */
function staleReload() {
  const row = current();
  if (!S.stale || !row || S.stale.key !== row.key) { hideStale(); return; }
  const stale = S.stale;
  const mine = { pairs: pairsNow().map((p) => ({ es: p.es, kq: p.kq })), en: $('en').value };
  for (const k of ['es', 'en', 'kq', 'pairs', 'unpaired', 'v']) row[k] = stale.now[k];
  drawTurn({ keepPlayer: true });
  S.dirty = false;
  drawAct();
  // drawTurn put the card away: it comes back with his words under the line
  S.stale = { key: row.key, now: stale.now, mine };
  $('stale').hidden = false;
  $('stale-line').textContent = STALE_RELOADED;
  $('stale-acts').hidden = true;
  const list = $('stale-pairs');
  list.textContent = '';
  for (const p of mine.pairs) {
    if (!p.es.trim() && !p.kq.trim()) continue;
    const li = document.createElement('li');
    for (const [cls, text] of [['stale-es', p.es], ['stale-kq', p.kq]]) {
      if (!text.trim()) continue;
      const span = document.createElement('span');
      span.className = cls;
      span.textContent = text;
      li.appendChild(span);
    }
    list.appendChild(li);
  }
  list.hidden = !list.children.length;
  $('stale-notes').textContent = mine.en;
  $('stale-notes-wrap').hidden = !mine.en.trim();
  $('stale-mine').hidden = false;
  $('stale').scrollIntoView({ block: 'nearest' });
}

/* what was typed back in the fields, over the passage as reloaded, to save with Next when he chooses */
function staleBack() {
  const row = current();
  if (!S.stale || !S.stale.mine || !row || S.stale.key !== row.key) { hideStale(); return; }
  const mine = S.stale.mine;
  hideStale();
  drawFieldsFrom(row, mine);
  S.dirty = true;
  drawAct();
}

/* what was typed saved over the change */
function staleOverwrite() {
  const row = current();
  if (!S.stale || !row || S.stale.key !== row.key) { hideStale(); return; }
  row.v = S.stale.now.v;
  hideStale();
  commit(row, false);
}

/* Skip is a positive act: the turn is recorded as read and nothing at all is written to the
   workbook. The three fields are left out of the payload, which is the path through the commit
   endpoint that touches no cell, and the move on is a save's move. */
async function skipTurn() {
  const row = current();
  if (!row) return;
  try {
    const data = await api('/api/commit', {
      path: S.data.path, sheet: row.sheet, row: row.row, round: row.round, away: awayTally(),
    });
    awayReset();
    S.data.progress = data.progress;
    S.dirty = false;
    clearPending(true);
    drawProgress();
    say(t('distil.save.skipped'), 2000);
    afterCommit(row);
  } catch (err) { say(err.message, 9000); }
}

/* One filled button goes on from the turn, and it says what it does. With all three fields empty
   and nothing in the workbook for this turn it reads Skip, and with words in any field it reads
   Next. A turn that had words in the workbook and has had them all deleted reads Next, because the
   empty fields have to be written over them, which Skip never does. Both words and both icons sit in
   the button and the stylesheet shows the pair its state names, so the word changes as he types
   with nothing redrawn. `Cmd + Enter` does what the button says. While an interviewer note is
   open in place of the three fields it reads Next, with the tick, as on her turns, and keeps the
   note. */
const ACT = {
  skip: { word: t('distil.act.skip'), title: t('distil.act.skip_title') },
  next: { word: t('distil.act.next'), title: t('distil.act.next_title') },
};
const NOTE_ACT_TITLE = t('distil.act.note_title');

function turnAct() {
  const row = current();
  const typed = !!$('en').value.trim() || pairsNow().some((p) => p.es.trim() || p.kq.trim());
  const stored = !!row && ['es', 'en', 'kq'].some((k) => String(row[k] || '').trim());
  return typed || stored ? 'next' : 'skip';
}

function drawAct() {
  // while an interviewer note is open the button reads Next, with the tick, and keeps the note
  const act = S.note ? 'next' : turnAct();
  const title = keyName(t('distil.act.title_keys', { title: S.note ? NOTE_ACT_TITLE : ACT[act].title }));
  const button = $('btn-commit');
  if (button.dataset.act === act && button.title === title) return;
  button.dataset.act = act;
  button.title = title;
  button.setAttribute('aria-label', ACT[act].word);
}

const pressAct = () => (S.note ? keepNote(true) : turnAct() === 'next' ? commit(null, true) : skipTurn());

function afterCommit(row) {
  const p = S.data.progress;
  const done = p.roundsDone.includes(row.round);
  const lastOfRound = !S.flat[S.stops[S.at + 1]] || S.flat[S.stops[S.at + 1]].round !== row.round;
  // the card shows once, when the round closes: a save on the last turn of a round already
  // recorded moves on as any save does, with no card, marked complete or not, and the round is not
  // recorded again
  const tally = (p.roundTurns || []).find((r) => r.number === row.round);
  const again = !!(tally && tally.recorded);
  // with Work in rounds off a round closes with no card, quietly on the move, unless it ends its
  // sheet or the case
  if (done && lastOfRound && !again && (roundsHere() || endsSheet(row.round))) { celebrate(row.round); return; }
  // the next passage, past another speaker's turns (20 October)
  let ahead = S.at + 1;
  while (ahead < S.stops.length && S.flat[S.stops[ahead]].other) ahead += 1;
  if (ahead < S.stops.length) { S.at = ahead; drawTurn(); flashCount(); }
  else say(t('distil.move.was_last'));
  closeLeftRounds();
}

/* ──────────────────────────────────────────────────────── the count ── */

/* Every step on that decides a turn, Next after a save, a save with nothing in it, Skip and a pass,
   flashes the new place in the round large over the middle of the sheet's column, "8 / 20" in the
   numeral face, the numbers alone growing in and out of a blur, 850ms in all (items 157, 166). At the
   round's midpoint turn, the first place at or past half its participant turns, it reads Halfway,
   and on its last turn Last one. In the same instant the place in the top bar brightens, so the eye
   learns where the number lives. It counts turns, never statements. A move that closes a round
   raises none, because the round card and the confetti have that moment, a new one replaces one
   still showing, it takes no pointer and no focus, and under reduced motion nothing shows at all. */
function countWord(place, total) {
  if (!(place > 0) || !(total > 0) || place > total) return '';
  if (place === total && total > 1) return t('distil.count.last');
  if (place > 1 && place === Math.ceil(total / 2)) return t('distil.count.half');
  return `${place} / ${total}`;
}

/* the move about to close a round, whose card takes the moment, and with Work in rounds off only a
   round that ends its sheet or the case, since no other brings a card */
function closingOnMove() {
  const row = current();
  if (!(row && row.round)) return false;
  const closing = roundsToClose(row.round - 1).filter((n) => !S.closing.has(n));
  return roundsHere() ? closing.length > 0 : closing.some(endsSheet);
}

function flashCount(on = true) {
  if (!on || closingOnMove()) return;
  // Sound's tick goes with every step on that decides a turn, under reduced motion too, and the
  // Celebrations switch takes the count and the tick away together
  sound('tick');
  if (!cheerOn() || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const row = current();
  const rnd = currentRound();
  if (!row) return;
  // the place in the round, or with Work in rounds off the place on the sheet, as the bar has it
  let total = 0;
  let place = 0;
  if (roundsHere()) {
    if (!rnd) return;
    total = rnd.stops.length;
    place = rnd.stops.findIndex((s) => `${s.sheet}:${s.row}` === row.key) + 1;
  } else {
    const here = sheetPlace(row);
    total = here.of;
    place = here.on;
  }
  const word = countWord(place, total);
  if (!word) return;
  const flash = $('count-flash');
  flash.innerHTML = word === `${place} / ${total}` ? `${place}<span class="count-of"> / ${total}</span>` : esc(word);
  // the class is taken off and put back, so a flash still showing starts again from the top
  for (const [el, cls] of [[flash, 'on'], [$('rail-turn'), 'tick']]) {
    el.classList.remove(cls);
    void el.offsetWidth;
    el.classList.add(cls);
  }
}

/* ─────────────────────────────────────────────────── round complete ── */

const LINES = [
  t('distil.done.line_1'),
  t('distil.done.line_2'),
  t('distil.done.line_3'),
  t('distil.done.line_4'),
];

/* A round is done once every turn in it is decided, and it closes by itself. A save of its last
   turn closes it at once, with the card, and the card's Next round moves on. A move closes every
   round below the turn it lands on that is done and unrecorded, the one with a turn passed at its
   end among them, and the card shows for the round just left. A case opening closes every such
   round quietly, with no card. Each goes to the server once, oldest first, and is counted today. */
function roundsToClose(through) {
  const p = S.data && S.data.progress;
  if (!p || !p.roundTurns) return [];
  return p.roundTurns
    .filter((r) => r.number <= through && r.total > 0 && !r.recorded && p.roundsDone.includes(r.number))
    .map((r) => r.number);
}

function closeLeftRounds() {
  const row = current();
  if (row && row.round) closeRounds(roundsToClose(row.round - 1));
}

function celebrate(number) {
  return closeRounds([...roundsToClose(number - 1), number], { advance: true });
}

async function closeRounds(numbers, opts = {}) {
  const todo = numbers.filter((n, k) => !S.closing.has(n) && numbers.indexOf(n) === k);
  if (!todo.length || !S.data) return;
  const path = S.data.path;
  todo.forEach((n) => S.closing.add(n));
  try {
    for (const n of todo) {
      const data = await api('/api/round-complete', { path, round: n });
      if (!S.data || S.data.path !== path) return;
      S.data.progress = data.progress;
    }
  } catch (err) { say(err.message); }
  finally { todo.forEach((n) => S.closing.delete(n)); }
  if (!S.data || S.data.path !== path) return;
  drawProgress();
  const closed = todo.filter((n) => S.data.progress.roundsDone.includes(n));
  // with Work in rounds off the rounds close all the same, so the daily tally stays true, and the
  // card comes only for the one that ends its sheet or the case
  if (!opts.quiet && closed.length && (roundsHere() || closed.some(endsSheet))) roundDone(closed, !!opts.advance);
}

/* A round whose close leaves nothing on its sheet, or nothing in the case, by the figures the server
   last sent: the one that brings the sheet-done card or the case-complete card. */
function endsSheet(number) {
  const p = S.data && S.data.progress;
  if (!p) return false;
  if (p.roundsLeft === 0) return true;
  const rnd = (S.data.rounds || []).find((r) => r.number === number);
  const here = rnd && (p.sheetRounds || []).find((x) => x.sheet === rnd.sheet);
  return !!(here && here.left === 0);
}

/* Rounds belong to a sheet. In a case with more than one, the card counts the sheet the round
   closed on: the rounds done and left on it and the time left on it at his pace, with one small
   line under the figures for the sheet to come, "Then the 2d sheet, 5 rounds.". The round that
   finishes a sheet, with the case not finished, shows the sheet-done card: the sheet's own kicker,
   "The 2d sheet is next.", the rounds on the sheet, the sheets left and the time left
   on the rest of the case, and Next sheet as the filled button. The round that finishes the case
   shows the case-complete card. The confetti rises with them, level 1, 2 and 3. A case with one
   sheet, and a page in front of a server that sends no figures for a sheet, read as they always
   did. With Work in rounds off the card comes only at a sheet's end and the case's, and says nothing
   of rounds, a target, a streak or the time left: the passages on the sheet and the sheets left, or
   the passages decided and the sheets in the case (15 October). */
function roundDone(numbers, advance) {
  const p = S.data.progress;
  const paced = roundsHere();
  const number = numbers[numbers.length - 1];
  // nothing left in the case: the card says so, drops the pace, and offers the way back to the list
  // in place of a next round there is not
  const finished = p.roundsLeft === 0;
  const rounds = S.data.rounds || [];
  const rnd = rounds.find((r) => r.number === number);
  const sheets = p.sheetRounds || [];
  const here = rnd && sheets.length > 1 ? sheets.find((s) => s.sheet === rnd.sheet) || null : null;
  // the sheet to come: the next one in workbook order with rounds left on it, round to the first
  const at = here ? sheets.indexOf(here) : -1;
  const then = here ? [...sheets.slice(at + 1), ...sheets.slice(0, at)].find((s) => s.left > 0) || null : null;
  const sheetDone = !finished && !!here && here.left === 0 && !!then;
  if (!paced && !finished && !sheetDone) return;
  // the sheet's own numbers, "Round 2 done", wherever the server sends a place on the sheet
  const shown = (n) => {
    const r = rounds.find((x) => x.number === n);
    return r && typeof r.on_sheet === 'number' ? r.on_sheet : n;
  };
  S.doneAdvance = advance;
  S.doneSheet = sheetDone;
  S.nextSheet = then ? then.sheet : null;
  $('done-kicker').textContent = sheetDone ? t('distil.done.sheet_done', { sheet: here.sheet })
    : !paced ? t('distil.done.all_decided')
    : numbers.length > 1
      ? t('distil.done.rounds_done', { list: tList([...numbers.slice(0, -1), number].map(shown)) })
      : t('distil.done.round_done', { round: shown(number) });
  $('done-line').textContent = finished ? t('distil.done.participant_complete')
    : sheetDone ? t('distil.done.sheet_next', { sheet: then.sheet }) : LINES[number % LINES.length];
  const sheetCard = paced && here && !finished && !sheetDone;
  if (paced) {
    $('done-count-label').textContent = sheetDone ? t('distil.done.rounds_on_sheet') : t('distil.done.rounds_done_label');
    $('done-left-label').textContent = sheetDone ? t('distil.done.sheets_left') : sheetCard ? t('distil.done.left_on_sheet') : t('distil.done.left_for_participant');
    $('done-count').textContent = sheetDone ? here.rounds : sheetCard ? here.done : p.roundsDone.length;
    $('done-left').textContent = sheetDone ? p.sheetsLeft : sheetCard ? here.left : p.roundsLeft;
  } else {
    const onSheet = (name) => S.stops.filter((i) => S.flat[i].sheet === name).length;
    $('done-count-label').textContent = sheetDone ? t('distil.done.passages_on_sheet') : t('distil.done.passages_decided');
    $('done-left-label').textContent = sheetDone ? t('distil.done.sheets_left') : t('distil.done.sheets');
    $('done-count').textContent = sheetDone ? onSheet(here.sheet) : typeof p.turnsDone === 'number' ? p.turnsDone : S.stops.length;
    $('done-left').textContent = sheetDone ? p.sheetsLeft : new Set(S.stops.map((i) => S.flat[i].sheet)).size;
  }
  // the minutes once a round has been timed. Until then the figure says when it will be one, in
  // the small type, because a sentence set in the numeral face reads as a number. The round-done
  // card's are the sheet's, the sheet-done card's the rest of the case's
  const minutes = sheetCard ? here.minutesLeft : p.minutesLeft;
  const measured = !!minutes;
  $('done-eta').textContent = measured ? formatMinutes(minutes) : t('distil.done.eta_pending');
  $('done-eta').classList.toggle('pending', !measured);
  $('done-eta-box').hidden = finished || !paced;
  $('done-figures').classList.toggle('two', finished || !paced);
  // with other sheets to come, one small line under the figures says which and how many rounds
  const thenLine = sheetCard && then;
  $('done-then').textContent = thenLine ? t('distil.done.then', { sheet: then.sheet, n: then.left }) : '';
  $('done-then').hidden = !thenLine;
  const left = Math.max(0, p.dailyTarget - p.todayRounds);
  const target = left === 0
    ? (p.streak ? t('distil.done.target_met_streak', { n: p.streak }) : t('distil.done.target_met'))
    : t('distil.done.target_left', { n: left });
  const daily = !paced ? '' : finished ? t('distil.done.finished_target', { target }) : target;
  $('done-daily').textContent = daily;
  $('done-daily').hidden = !daily;
  $('done-next').hidden = finished || sheetDone;
  $('done-sheet').hidden = !sheetDone;
  $('done-library').hidden = !finished;
  // the last round closes the case, and the card offers to mark the phase complete
  S.doneFinished = finished;
  drawDoneMark(finished);
  show('round-done');
  confetti(finished ? 3 : sheetDone ? 2 : 1);
}

/* Next sheet on the sheet-done card goes to the next sheet's first undecided turn, the way the
   switcher does. Take a break leaves him where he is, at the end of a round or of a sheet, and the
   card never speaks of stopping: when to stop is his. */
function nextSheet() {
  hide('round-done');
  const name = S.nextSheet;
  if (!name) { focusEntry(); return Promise.resolve(); }
  return toSheet(name).then(() => focusEntry());
}

function stopHere() {
  hide('round-done');
  say(S.doneSheet ? t('distil.done.break_sheet')
    : S.doneFinished ? t('distil.done.break_participant')
      : t('distil.done.break_round'));
  haulShow();
}

/* ─────────────────────────────────────────────────── today's haul ── */

/* Take a break, on the round card, the sheet-done card and the case-complete card, closes the card
   and shows, where it stood, one quiet line in the card's style for about four seconds, then it
   fades (item 158): today's rounds, the turns in them and the time measured on them, "Today: 3
   rounds, 47 turns, 1 h 12 min.". The figures are the summary's, `todayRounds`, the daily tally the
   target counts, with `todayTurns` and `todaySeconds` beside it, and a figure the server does not
   send, as one from before them does not, is left out of the line, as is a time under half a minute. A
   click or a key takes it away at once and goes on to do what it does. It never takes the pointer
   or the focus, the Celebrations switch silences it, and under reduced motion it shows and goes
   without the fade. */
const HAUL_MS = 4000;
let haulTimer = null;

function haulTime(seconds) {
  const m = Math.round(Number(seconds) / 60);
  return m >= 1 ? formatMinutes(m) : '';
}

function haulLine(p) {
  if (!p) return '';
  const some = (n) => typeof n === 'number' && n > 0;
  // with Work in rounds off the line leaves the rounds out
  const parts = [roundsHere() && some(p.todayRounds) ? t('distil.haul.rounds', { n: p.todayRounds }) : '',
    some(p.todayTurns) ? t('distil.haul.passages', { n: p.todayTurns }) : '',
    typeof p.todaySeconds === 'number' ? haulTime(p.todaySeconds) : ''].filter(Boolean);
  return parts.length ? t('distil.haul.line', { parts: parts.join(', ') }) : '';
}

function haulShow() {
  const line = cheerOn() ? haulLine(S.data && S.data.progress) : '';
  if (!line) return;
  const el = $('haul');
  el.textContent = line;
  el.hidden = false;
  el.classList.remove('on');
  void el.offsetWidth;
  el.classList.add('on');
  clearTimeout(haulTimer);
  haulTimer = setTimeout(haulHide, HAUL_MS);
  // once the press that showed it has gone by, so that press never takes it away
  setTimeout(() => {
    if ($('haul').hidden) return;
    window.addEventListener('pointerdown', haulHide, true);
    window.addEventListener('keydown', haulHide, true);
  }, 0);
}

function haulHide() {
  clearTimeout(haulTimer);
  haulTimer = null;
  $('haul').hidden = true;
  $('haul').classList.remove('on');
  window.removeEventListener('pointerdown', haulHide, true);
  window.removeEventListener('keydown', haulHide, true);
}

/* A length of time in whole minutes as the break's line and the end card's time left both say it (fmtsweep,
   28 October 2026, one form for the two): 45 min, 1 h, 1 h 30 min, each a sentence of the catalogue's. */
function formatMinutes(m) {
  const h = Math.floor(m / 60);
  if (!h) return t('distil.length.minutes', { m });
  return m % 60 ? t('distil.length.hours_minutes', { h, m: m % 60 }) : t('distil.length.hours', { h });
}

/* ─────────────────────────────────────────────────────────── the pairs ── */

/* Each experiential statement is a field of its own with its quote under it, a pair, because the
   first quote belongs to the first statement and the second to the second (item 198). A turn
   opens with its pairs as the server reads them, by place, one empty pair on a turn with none, and
   Add another puts an empty pair under the last. Each pair stands in the current passage's card in the
   statements column since 17 October, its number, 1, 2 and on, numbered again after every change,
   beside its statement, where until then it opened with the heading Experiential statement 1 in the
   panel, and Remove, a bin alone at the pair's top right since 18 October, where it stood at the right
   of its Quote label, takes the whole pair away, statement and quote alike, one step of undo,
   the pair outlined in red while the bin has the pointer or the focus (14 October). A field grows with its words and, empty, with its prompt, so the card and its row grow
   with them and never scroll inside. The pair being worked on is the one whose
   statement or quote last had the focus, else the last pair: `q` and a candidate taken from the AI
   go to it. `q` fills that pair's quote while it has none, and else adds a pair under the last
   with the quote in it, never writing over a quote (16 October). The same words may be the quote of
   two pairs. */

let pairSeq = 0;
// the empty quote's line names the arrow beside it too (Adam's ruling of 21 October), Ctrl off a Mac
const PAIR_QUOTE_HINT = keyName(t('distil.pair.quote_hint'));
const GRAMM_OFF = 'spellcheck="true" data-gramm="false" data-gramm_editor="false" data-enable-grammarly="false"';

const pairEls = () => [...$('pairs').querySelectorAll('.pair')];
const pairOf = (el) => ({ es: el.querySelector('.pair-es').value, kq: el.querySelector('.pair-kq').value });
const pairsNow = () => pairEls().map(pairOf);
const pairEmpty = (p) => !p.es.trim() && !p.kq.trim();

/* a field of a pair, or the exploratory notes: the fields the app's undo tells apart from its own */
const isEntryField = (el) => !!el && (el.id === 'en'
  || !!(el.classList && (el.classList.contains('pair-es') || el.classList.contains('pair-kq')
    // a thematic analysis project's Add a code (codes.js)
    || el.classList.contains('cx-field'))));

/* The turn's pairs as the page draws them: the server's, and for a server from before the pairs the
   two fields paired by order, as `pairsByOrder` in quote.js pairs them. */
function rowPairs(row) {
  if (Array.isArray(row.pairs)) return row.pairs.map((p) => ({ es: p.es || '', kq: p.kq || '' }));
  const lines = (text) => String(text || '').split('\n');
  return pairsByOrder(lines(row.es), lines(row.kq).filter((l) => l.trim()));
}

/* Since 21 October each pair also carries, once its quote is set, `.pair-qtoggle`, its label as a
   toggle that folds or opens this quote alone, its chevron drawn by the stylesheet and its state by pairsFoldDraw, and
   `.pair-kq-line`, the quote folded to one line, which a press opens as the toggle does. Then `.pair-take`,
   the arrow beside the quote, lit while words are selected in the passage, a press taking them as this
   statement's quote, as Q and the selection's Quote do (pairTake). */
function pairHtml(id) {
  return `<div class="pair" data-pid="${id}">`
    // its number from pairsDrawn beside its statement, as the passage's other statements are numbered
    + `<label class="pair-num" for="es-${id}"></label><div class="pair-body">`
    + `<textarea class="pair-es" id="es-${id}" rows="1" ${GRAMM_OFF}></textarea>`
    // one number for the statement, amber past fifteen words, the band the length nudge reads
    + '<div class="wordcount"></div><div class="nudges"></div>'
    // the quote's label alone on its line, where Remove stood at its right until 18 October
    + `<div class="pair-qhead"><label class="field-label pair-qlabel" for="kq-${id}">${escAttr(t('distil.pair.quote'))}</label>`
    + `<button type="button" class="pair-qtoggle" aria-controls="kq-${id}">${escAttr(t('distil.pair.quote'))}</button></div>`
    + `<textarea class="pair-kq" id="kq-${id}" rows="1" placeholder="${escAttr(PAIR_QUOTE_HINT)}" ${GRAMM_OFF}></textarea>`
    + '<div class="pair-kq-line" aria-hidden="true"></div>'
    + `<button type="button" class="pair-take" data-take="${id}" tabindex="-1" aria-disabled="true" title="${escAttr(t('distil.pair.take_title'))}" aria-label="${escAttr(t('distil.pair.take'))}">`
    + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    + 'aria-hidden="true" focusable="false"><path d="M19 12H5.5M11 6l-6 6 6 6"/></svg></button>'
    // and the pair's bin, drawn at the top right beside the statement's first line, last in the pair for Tab.
    // A bin alone in the quiet ink, red under the pointer and in focus (18 October, Adam's drawing, where a
    // red-edged Remove with its word stood beside the quote's label, too near the fields and too loud for
    // an act this rare). It takes the pair as Remove did, one step of undo
    + `<button type="button" class="pair-remove" data-remove="${id}" title="${escAttr(t('distil.pair.remove'))}" aria-label="${escAttr(t('distil.pair.remove'))}">`
    + '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
    + 'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4 6.5h16M9.5 6.5V4.2h5v2.3M6.2 6.5l.9 13.3h9.8l.9-13.3M10 10.5v6M14 10.5v6"/></svg>'
    + '</button></div></div>';
}

/* After any change to the pairs: each pair's number, numbered by place, each statement's name, the craft
   prompt in the first, the heights, the counts and the nudges. Its bin is "Remove this statement" to the
   eye and a screen reader alike, met after its statement and quote (18 October, where until then its
   name said the statement's number). */
function pairsDrawn() {
  pairEls().forEach((el, i) => {
    const es = el.querySelector('.pair-es');
    el.querySelector('.pair-num').textContent = String(i + 1);
    // its colour by its place, one of six and then round again, as its marks in the passage take it, so its
    // dot and its stripe follow a removal or a move (18 October)
    el.dataset.esColour = String(i % 6);
    es.setAttribute('aria-label', t('distil.pair.statement_n', { n: i + 1 }));
    // and its quote by the same number, since its label goes once the quote is filled (a11yfix)
    const kq = el.querySelector('.pair-kq');
    if (kq) kq.setAttribute('aria-label', t('distil.pair.quote_n', { n: i + 1 }));
    es.placeholder = i === 0 ? (S.prompt || PROMPT_FALLBACK) : '';
  });
  if (typeof pairsFoldDraw === 'function') pairsFoldDraw();
  growPairs();
  drawWordCount();
  runNudges();
  if (typeof pairTakeDraw === 'function') pairTakeDraw();
  if (typeof esCountDraw === 'function') esCountDraw();
  // in a thematic analysis project each extract a box with its codes as chips (codes.js)
  if (typeof cxDraw === 'function') cxDraw();
  if (typeof levelSoon === 'function') levelSoon();
  // Working together: Comment under each statement for a reviewer (review.js)
  if (typeof rvwPairsDrawn === 'function') rvwPairsDrawn();
}

/* A pair's field at the height of its words, and empty at the height of its prompt, so a prompt of two
   lines in a narrow card reads whole, where a field of one line cut it (17 October). The prompt is
   measured in a twin of the field out of sight, so the field's own words and its undo are never
   touched. */
let hintTwin = null;
function growField(field) {
  grow(field, 1);
  if (field.value || !field.placeholder || !field.offsetWidth) return;
  if (!hintTwin) {
    hintTwin = document.createElement('textarea');
    hintTwin.setAttribute('aria-hidden', 'true');
    hintTwin.tabIndex = -1;
  }
  hintTwin.className = `${field.className} hint-twin`;
  hintTwin.style.width = `${field.offsetWidth}px`;
  field.after(hintTwin);
  hintTwin.value = field.placeholder;
  hintTwin.style.height = 'auto';
  const tall = hintTwin.scrollHeight + 2;
  hintTwin.remove();
  if (tall > field.offsetHeight) field.style.height = `${tall}px`;
}

function growPairs() {
  for (const field of $('pairs').querySelectorAll('.pair-es, .pair-kq')) growField(field);
}

function drawPairs(list) {
  const pairs = list && list.length ? list : [{ es: '', kq: '' }];
  $('pairs').innerHTML = pairs.map(() => pairHtml(`p${++pairSeq}`)).join('');
  pairEls().forEach((el, i) => {
    el.querySelector('.pair-es').value = pairs[i].es || '';
    el.querySelector('.pair-kq').value = pairs[i].kq || '';
  });
  pairsDrawn();
}

/* A pair put in at `place` among the pairs, or under the last. */
function insertPair(pair, place) {
  const els = pairEls();
  const id = `p${++pairSeq}`;
  const before = place !== undefined && place < els.length ? els[place] : null;
  if (before) before.insertAdjacentHTML('beforebegin', pairHtml(id));
  else $('pairs').insertAdjacentHTML('beforeend', pairHtml(id));
  const el = $('pairs').querySelector(`.pair[data-pid="${id}"]`);
  el.querySelector('.pair-es').value = pair.es || '';
  el.querySelector('.pair-kq').value = pair.kq || '';
  return el;
}

/* the pair being worked on: the one whose statement or quote last had the focus, else the last */
function workingPair() {
  const els = pairEls();
  return els.find((el) => el.dataset.pid === S.pairFocus) || els[els.length - 1] || null;
}

const workingPlace = () => pairEls().indexOf(workingPair());

function pairsChanged() {
  pairsDrawn();
  S.dirty = true;
  drawAct();
  markKeyQuotes();
}

/* ─────────────────────────────── quote first: the arrow, the boxes level, Quotes folded ── */

/* Adam's ruling of 21 October, from a tester, who selects the words first and then writes the statement. Beside
   each statement's quote an arrow, lit while words are selected in the passage being worked on, or pieces
   are held with Cmd: a press takes them as that statement's quote, as Q and the selection's Quote do, the
   statement being the pair worked on (`quoteTarget`), so a quote is never written over and a statement that
   has one gets a new pair under the last with the words in it. */
function pairTakeDraw() {
  const on = !!(S.data && !$('work').hidden && ((S.pending && S.pending.length) || selectionInTurn()));
  for (const b of $('pairs').querySelectorAll('.pair-take')) {
    if (b.classList.contains('lit') !== on) b.classList.toggle('lit', on);
    b.setAttribute('aria-disabled', String(!on));
  }
}

async function pairTake(el) {
  if (!el) return;
  if (!(S.pending && S.pending.length) && !selectionInTurn()) {
    say(t('distil.pair.select_first_arrow'));
    return;
  }
  S.pairFocus = el.dataset.pid;
  await commitQuote();
}

/* Each statement's box level with its own quote (Adam's ruling of 21 October): in a long passage the box
   sits beside the top of its quote's first line, the card lifted for the first and each later box dropped
   for its own, never above the foot of the box before it, so two close quotes stack their boxes in order
   and never overlap. A statement with no quote keeps its place, at the passage's top for the first and
   under the one before for the rest, and does not follow a selection. The boxes are placed when the
   passage opens and when a quote is set, by Q, the arrow, the selection's Quote or an undo, and as the
   columns change size, never while he types, so a box never moves under his hands. Only where the
   statements stand beside the words, never stacked under them or in the stacked column. */
let levelFrame = 0;
function levelSoon() {
  cancelAnimationFrame(levelFrame);
  levelFrame = requestAnimationFrame(() => {
    levelPairs();
    // the columns settling just after a long passage opened can move its card down again, so under 'scroll' the
    // column follows it while the passage is still opening, never in a glide (cardlarge)
    const now = performance.now();
    if (CARD_REACH === 'scroll' && REACH.long && now < REACH.settle && now >= REACH.glide) reachInView();
  });
}

function levelPairs() {
  const card = $('es-card');
  const els = pairEls();
  card.style.removeProperty('--lift');
  els.forEach((el) => el.style.removeProperty('--drop'));
  const cell = card.closest('.turn-es');
  if (cell) cell.style.removeProperty('--reach-lift');
  const holder = cell ? cell.closest('.turn.current') : null;
  const words = holder ? holder.querySelector('.turn-text') : null;
  if (!words || !cell.getClientRects().length) return;
  const w = words.getBoundingClientRect();
  const c = cell.getBoundingClientRect();
  if (!(c.right <= w.left + 1 || c.left >= w.right - 1)) return;
  const marks = [...words.querySelectorAll('[data-kq]')];
  // beside a long passage's capped words the first box stands no lower than their box leaves its statement and
  // the card's foot whole, and a held card is lifted by its cell so it can still rise to the column's foot from
  // there (cardlarge)
  const long = holder.classList.contains('reach-long');
  const held = CARD_REACH === 'hold' && long;
  const lowest = CARD_REACH === 'cap' && long ? w.bottom - REACH.need : Infinity;
  els.forEach((el, i) => {
    const mark = marks.find((m) => String(m.dataset.kq).split(' ').includes(String(i)));
    const line = mark ? mark.getClientRects()[0] : null;
    // a pair drawn nowhere, as a thematic analysis project's are under its extracts' boxes, has no place to measure
    // from, and measured from the top of the window it pushed the card far down (taaibuild, 4 November 2026)
    if (!el.getClientRects().length) return;
    if (!line || (held && i > 0)) return;
    // a held card's place is its cell's top, wherever the column has carried it
    const top = held ? c.top - 6 : el.getBoundingClientRect().top;
    const d = Math.round((i === 0 ? Math.min(line.top, lowest) : line.top) - top);
    if (d <= 0) return;
    if (held) cell.style.setProperty('--reach-lift', `${d}px`);
    else if (i === 0) card.style.setProperty('--lift', `${d}px`);
    else el.style.setProperty('--drop', `${d}px`);
  });
  footStuck();
}

/* Quotes on the status bar (21 October): pressed in, as on a new install, each quote shows whole, and out,
   each quote's words are hidden. Kept in the settings as `es_quotes`, so a reload keeps it. Each
   quote also folds and opens on its own whatever the bar says (21 October, for a tester's long quotes), from its
   label's toggle or a press on its folded line: `kq-shut` folds one to its first line while the bar shows
   them whole and `kq-open` opens one while the bar hides them. Quotes off hides each quote's words entirely,
   no first line, its label and chevron left (Adam, later on 21 October: "clear the wood for the trees"), which
   the stylesheet does. A press on the bar puts every quote back to the bar's state.
   A quote of several pieces is one field, so it folds to one line, its pieces and their ellipses together. */
const quotesFolded = () => !!(S.data && S.data.config && S.data.config.es_quotes === false);

/* whether a pair's quote shows whole: the bar's state, unless this quote goes its own way */
const quoteShown = (el) => (quotesFolded() ? el.classList.contains('kq-open') : !el.classList.contains('kq-shut'));

function pairsFoldDraw() {
  for (const el of pairEls()) {
    const kq = el.querySelector('.pair-kq').value;
    const filled = !!kq.trim();
    el.classList.toggle('kq-filled', filled);
    if (!filled) el.classList.remove('kq-open', 'kq-shut');
    el.querySelector('.pair-kq-line').textContent = kq.replace(/\s+/g, ' ').trim();
    const open = quoteShown(el);
    const toggle = el.querySelector('.pair-qtoggle');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.title = open ? t('distil.pair.fold') : t('distil.pair.unfold');
  }
}

function quotesDraw() {
  const folded = quotesFolded();
  $('work').classList.toggle('quotes-folded', folded);
  $('es-quotes-btn').setAttribute('aria-pressed', String(!folded));
  // the bar pressed, here or in a reload's settings, puts every quote back to its state
  if (S.quotesWere !== folded) pairEls().forEach((el) => el.classList.remove('kq-open', 'kq-shut'));
  S.quotesWere = folded;
  pairsFoldDraw();
  growPairs();
  levelSoon();
}

function quotesToggle() { setView('es_quotes', quotesFolded()); }

/* one quote opened alone, or folded alone, against the bar's state, the caret going into it as it opens */
function quoteOpen(el, open) {
  const folded = quotesFolded();
  el.classList.toggle('kq-open', folded && open);
  el.classList.toggle('kq-shut', !folded && !open);
  pairsFoldDraw();
  const field = el.querySelector('.pair-kq');
  growField(field);
  levelSoon();
  if (open) field.focus();
}

/* the participant's statements counted at the status bar's left, the passage being worked on as its
   fields hold it, "41 statements". Every row's, an interviewer's turn's too, as the board's cards and the
   agents' `statements` count them, so the three say one number (countdrift, 30 October) */
function esCountDraw() {
  const el = $('es-count');
  if (!el) return;
  if (!S.data || !Array.isArray(S.flat)) { el.textContent = ''; return; }
  let n = 0;
  // in a thematic analysis project its coded extracts and the codes they use, "49 extracts, 11 codes" (codes)
  const ta = typeof cxOn === 'function' && cxOn();
  const extracts = new Set();
  const used = new Set();
  for (const row of S.flat) {
    if (!row) continue;
    for (const p of livePairs(row).filter((x) => String(x.es || '').trim())) {
      n += 1;
      if (!ta) continue;
      used.add(String(p.es).split(/\s+/).filter(Boolean).join(' ').toLowerCase());
      extracts.add(`${row.key}|${String(p.kq || '').split(/\s+/).filter(Boolean).join(' ')}`);
    }
  }
  el.textContent = ta ? t('distil.find.coded', { extracts: t('codes.n.extracts', { n: extracts.size }),
    codes: t('codes.n.codes', { n: used.size }) }) : t('distil.find.statements', { n });
}

/* Add another: an empty pair under the last, its statement taking the caret. */
function addAnother() {
  const el = insertPair({ es: '', kq: '' });
  pairsChanged();
  el.querySelector('.pair-es').focus();
  return el;
}

/* Remove on a pair's heading takes the whole pair away, one step of undo, and a turn always keeps
   one pair. */
function removePair(el) {
  const row = current();
  const els = pairEls();
  const place = els.indexOf(el);
  if (!row || place < 0) return;
  const held = pairOf(el);
  el.remove();
  if (!pairEls().length) insertPair({ es: '', kq: '' });
  pairsChanged();
  const next = pairEls()[Math.min(place, pairEls().length - 1)];
  if (next) next.querySelector('.pair-es').focus();
  if (pairEmpty(held)) return;
  undoPush({
    key: row.key, what: 'the pair', place, held,
    undo: (e) => pairPut(e, true),
    redo: (e) => pairPut(e, false),
  });
}

/* Undo of a removal puts the pair back where it stood, into a turn left with one empty pair in
   place of it, and redo takes it out again. */
function pairPut(entry, back) {
  if (back) {
    if (pairsNow().every(pairEmpty)) pairEls().forEach((el) => el.remove());
    insertPair(entry.held, entry.place);
  } else {
    const same = (el) => { const p = pairOf(el); return p.es === entry.held.es && p.kq === entry.held.kq; };
    const els = pairEls();
    const el = els[entry.place] && same(els[entry.place]) ? els[entry.place] : els.find(same);
    if (el) el.remove();
    if (!pairEls().length) insertPair({ es: '', kq: '' });
  }
  pairsChanged();
  say(back ? t('distil.undo.statement_back') : t('distil.undo.statement_out_again'), 2000);
}

/* Enter never breaks a line in a pair, since one field is one statement or one quote: it goes from
   a statement to its quote and on from a quote to the next statement, adding one under the last. */
function pairEnter(field) {
  const el = field.closest('.pair');
  if (field.classList.contains('pair-es')) { el.querySelector('.pair-kq').focus(); return; }
  const next = el.nextElementSibling;
  if (next) next.querySelector('.pair-es').focus();
  else addAnother();
}

/* ─────────────────────────────────────────────────────────── the word count ── */

/* One statement is one field, so the count is one number under each: "8 words", in amber and bold
   past the project's statement length, 15 by default, the band the length nudge reads (wordBand, 20
   October), and nothing at all is said about a short
   one. The words are counted the way `nudges.py` counts them, so the number and the nudge never
   disagree, and it runs on the keystroke rather than behind the debounce, because it costs nothing. */

const WORD = /[A-Za-z0-9']+/g;

const countWords = (line) => (line.match(WORD) || []).length;

function pairCount(el) {
  const box = el.querySelector('.wordcount');
  const text = el.querySelector('.pair-es').value.trim();
  if (!text) { box.innerHTML = ''; return; }
  const n = countWords(text);
  const said = esc(t('distil.pair.words', { n }));
  box.innerHTML = n > wordBand() ? `<span class="over">${said}</span>` : said;
}

function drawWordCount() { pairEls().forEach(pairCount); }

/* ─────────────────────────────────────────────────────────── nudges ── */

/* Each statement's nudges stand under it, so none needs to say which statement it means. The
   statements go in one request, one a line, and come back by line. */
let nudgeTimer;
function runNudges() {
  clearTimeout(nudgeTimer);
  // the nudges hold a statement to IPA's book, and a thematic analysis project's codes to none yet (tadraw)
  if (typeof tMethodNow === 'function' && tMethodNow() === 'ta') { for (const el of pairEls()) el.querySelector('.nudges').innerHTML = ''; return; }
  nudgeTimer = setTimeout(async () => {
    const els = pairEls();
    const lines = els.map((el) => el.querySelector('.pair-es').value.replace(/\s*\n\s*/g, ' '));
    const clear = () => els.forEach((el) => { el.querySelector('.nudges').innerHTML = ''; });
    if (!lines.some((l) => l.trim())) { clear(); return; }
    try {
      // the workbook's path, so the length nudge speaks at its project's statement length
      const data = await api('/api/nudges', { text: lines.join('\n'), ...(S.data && S.data.path ? { path: S.data.path } : {}) });
      const by = {};
      for (const line of data.lines) by[line.line] = line.flags;
      els.forEach((el, i) => {
        el.querySelector('.nudges').innerHTML = (by[i] || []).map((f) =>
          `<div class="nudge"><i>·</i><span>${esc(f.note)}</span></div>`).join('');
      });
    } catch { /* nudges never get in the way */ }
  }, 220);
}

/* ──────────────────────────────────────────────────────── quotes to pair ── */

/* Under Find, the turns saved before the pairs whose count of quotes differs from their
   statements', each opening its turn. They pair by order on screen, and a save writes the turn
   paired, so it leaves the list. */
function toPairRows() {
  return S.flat.filter((r) => r.stop && r.unpaired);
}

function drawToPair() {
  if (!$('find-pair')) return;
  const rows = findOpen() ? toPairRows() : [];
  $('find-pair').hidden = !rows.length;
  const many = new Set(S.flat.map((r) => r.sheet)).size > 1;
  $('find-pair-list').innerHTML = rows.map((r) => {
    const pairs = rowPairs(r);
    const n = pairs.filter((p) => p.es.trim()).length;
    const q = pairs.filter((p) => p.kq.trim()).length;
    const where = [many ? r.sheet : '', r.time].filter(Boolean).join(' ');
    return `<li><button type="button" class="find-pair-go" data-pair-row="${r.i}">`
      + `<span class="mono">${esc(where)}</span> ${esc(t('distil.find.pair_counts', { statements: t('distil.find.statements', { n }), quotes: t('distil.find.quotes', { n: q }) }))}</button></li>`;
  }).join('');
}

function openToPair(i) {
  const row = S.flat[i];
  if (row && row.stop) goTo(row.pos);
}

/* ───────────────────────────────────────────────────────── examples ── */

async function loadExamples() {
  try {
    const data = await api('/api/examples', { gravity_only: $('gravity-only').checked });
    $('examples').innerHTML = data.examples.map((e) =>
      `<li><q>${esc(e.text)}</q><span class="src">${esc(e.source)}</span></li>`).join('');
  } catch { /* the panel is a prompt, not a requirement */ }
}

/* ──────────────────────────────────────────────────── selection, quote ── */

function selectionInTurn() {
  const box = $('turn-text');
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount || sel.isCollapsed) return null;
  const range = sel.getRangeAt(0);
  if (!box.contains(range.commonAncestorContainer)) return null;
  const before = range.cloneRange();
  before.selectNodeContents(box);
  before.setEnd(range.startContainer, range.startOffset);
  const start = before.toString().length;
  const text = range.toString();
  if (!text.trim()) return null;
  return { start, end: start + text.length, text };
}

/* The words selected inside one of her passages on screen that is not the one being worked on, as
   offsets into its text, or null: nothing selected, a selection in the passage being worked on, in
   one of the interviewer's or across two passages, each of which `q` takes as it always did. */
function selectionElsewhere() {
  const hits = selectionTurns();
  if (!hits || hits.length !== 1) return null;
  const holder = hits[0].box.closest('.turn');
  const row = holder ? S.flat[Number(holder.dataset.i)] : null;
  const now = current();
  if (!row || !row.stop || (now && row.i === now.i)) return null;
  // words just taken as a piece of the quote being built, in her passage next to this one, are that piece
  if (S.pending.some((p) => p.key === row.key && p.start <= hits[0].start && p.end >= hits[0].end)) return null;
  const text = row.runs.map((r) => r.text).join('').slice(hits[0].start, hits[0].end);
  return text.trim() ? { row, start: hits[0].start, end: hits[0].end, text } : null;
}

/* A highlight the workbook holds, an orange run, as one flag per character. The app draws none and
   makes none since 16 October, and the find still counts the occurrences inside one, because a
   replace there drops it from the file. */
function cruxMask(runs) {
  const mask = [];
  for (const run of runs || []) for (let i = 0; i < run.text.length; i += 1) mask.push(!!run.crux);
  return mask;
}

/* ───────────────────────────────────────── quotes in the passage ── */

/* Every statement's quote is marked where it stands in its passage, in the crux orange, each
   piece of a quote put together with an ellipsis marked on its own (16 October, after a tester lost
   track in long passages of the words he had drawn on). Highlights went the same day, and the key
   quotes are the marks in the text now. The passage being worked on is marked from its pairs as the
   fields hold them, so a quote shows as it goes in, and every other passage from its pairs as saved.
   A quote the passage no longer holds, its text corrected since, goes unmarked (`quoteSpans`). Each
   mark names its pairs by place, so a click on it brings its statement forward, and a quote
   under the pointer or holding the caret lights its marks. */
function livePairs(row) {
  return row && S.pairsRow === row.key ? pairsNow() : rowPairs(row);
}

/* A quote across her passages (quotespan, 30 October 2026, Adam: "Adjacent passages may combine into one
   block quote with a timecode range"). One quote may take in the same speaker's passages next to its
   statement's own, adjacent when nothing but the interviewer's turns stand between, so no participant
   passage is skipped. The quote stays its statement's, kept in its row as the words alone, and which passages
   it takes in is found from its words, `quoteReach` in quote.js, as print and the command line find it. Each
   passage it takes in marks its pieces, so a quote's marks in a passage come from its own statements and from
   the statements of her passages either side whose quotes run on into it, each named by its passage and
   place. KQ_NEAR is how far either side the page looks for them, past any quote it is likely to meet. */
const KQ_NEAR = 8;
const speakerKey = (row) => String((row && row.name) || '').trim().toLowerCase();
const rowText = (row) => (row ? row.runs.map((r) => r.text).join('') : '');

/* the same speaker's passages either side of `row`, up to `most` each way, adjacent with nothing but the
   interviewer's turns between, in transcript order with `home` its own place among them */
function quoteRun(row, most) {
  const rows = [row];
  let home = 0;
  if (!row || !row.stop || row.other) return { rows, home };
  const me = speakerKey(row);
  for (const step of [-1, 1]) {
    let n = 0;
    for (let k = row.i + step; n < most && k >= 0 && k < S.flat.length; k += step) {
      const r = S.flat[k];
      if (r.sheet !== row.sheet) break;
      if (!r.stop) continue;
      if (r.other || speakerKey(r) !== me) break;
      if (step < 0) { rows.unshift(r); home += 1; } else rows.push(r);
      n += 1;
    }
  }
  return { rows, home };
}

/* where the quote of a statement on `row` stands, one `{row, start, end}` a piece, in its own passage and
   the passages it runs on into, none when its words are not there */
function quoteTurns(row, quote) {
  const own = quoteSpans(quote, rowText(row));
  if (own.length) return own.map((p) => ({ row, start: p.start, end: p.end }));
  const n = quotePieces(quote).length;
  if (n < 2 || !row || !row.stop) return [];
  const run = quoteRun(row, n - 1);
  return quoteReach(quote, run.rows.map(rowText), run.home)
    .map((p) => ({ row: run.rows[p.turn], start: p.start, end: p.end }));
}

function kqLayer(row) {
  if (!row || !row.stop) return [];
  const spans = [];
  const near = quoteRun(row, KQ_NEAR);
  near.rows.forEach((from, at) => {
    const away = Math.abs(at - near.home);
    // in a thematic analysis project each pair's extract, by its place among the passage's extracts (codes.js)
    const ex = typeof cxPlaces === 'function' && cxOn() ? cxPlaces(livePairs(from)) : null;
    livePairs(from).forEach((p, n) => {
      // a quote of a passage `away` off reaches this one only with more pieces than that
      if (away && quotePieces(p.kq).length <= away) return;
      for (const piece of quoteTurns(from, p.kq)) {
        if (piece.row !== row) continue;
        spans.push(away ? { start: piece.start, end: piece.end, cls: 'kq', kq: n, from: from.i, ...(ex ? { ex: ex[n] } : {}) }
          : { start: piece.start, end: piece.end, cls: 'kq', kq: n, ...(ex ? { ex: ex[n] } : {}) });
      }
    });
  });
  return spans;
}

/* the passages beside `row` its statements' quotes run on into now, by key */
function kqFarKeys(row) {
  const keys = [];
  for (const p of livePairs(row)) {
    for (const piece of quoteTurns(row, p.kq)) if (piece.row !== row && !keys.includes(piece.row.key)) keys.push(piece.row.key);
  }
  return keys;
}

/* the passages the quotes of the passage being worked on ran on into and run on into now drawn again, as
   its quotes change */
function kqFarPaint(row) {
  const was = S.kqFar || [];
  const now = kqFarKeys(row);
  S.kqFar = now;
  for (const key of new Set([...was, ...now])) {
    const r = rowByKey(key);
    if (r && r !== row && r.sheet === S.sheetDrawn) repaintRow(r);
  }
}

const kqSignature = () => JSON.stringify(pairsNow().map((p) => p.kq));

/* what a mark's tooltip says, the statement it belongs to, or the statements when two pairs hold the
   same words */
function kqTitle(list) {
  const n = list.map((k) => k + 1);
  return n.length === 1 ? t('distil.pair.statement_n', { n: n[0] }) : t('distil.pair.statements_n', { list: tList(n) });
}

/* the tooltip of a piece of the quote of her passage next to this one, its statement and that passage's
   time, "Experiential statement 1, 25:51" (quotespan) */
function kqFarTitle(far) {
  const [i, n] = String(far[0]).split(':').map(Number);
  const home = S.flat[i];
  return home && home.time ? t('distil.pair.statement_at', { n: n + 1, time: home.time }) : t('distil.pair.statement_n', { n: n + 1 });
}

/* The passage being worked on marked again once its quotes have changed, a quote taken, typed,
   cleared or moved with its pair, and only then, with the selection in it kept. */
function markKeyQuotes() {
  const row = current();
  if (!row || S.pairsRow !== row.key) return;
  const now = kqSignature();
  if (now === S.kqDrawn) return;
  S.kqDrawn = now;
  paintTurn(selectionInTurn());
  kqFarPaint(row);
}

/* A quote under the pointer or holding the caret lights its marks in the passage, the pointer's
   first. */
function lightMarks() {
  const box = $('turn-text');
  if (!box) return;
  const pid = S.kqHover || S.kqFocus || S.kqLit;
  const n = pid ? pairEls().findIndex((el) => el.dataset.pid === pid) : -1;
  // and a quote that runs on into her passages either side, its pieces there (quotespan)
  const now = current();
  const far = now && n >= 0 ? `${now.i}:${n}` : null;
  const runs = (el) => !!far && (el.dataset.kqFar || '').split(' ').includes(far);
  for (const el of box.querySelectorAll('.kq')) {
    el.classList.toggle('lit', (n >= 0 && (el.dataset.kq || '').split(' ').includes(String(n))) || runs(el));
  }
  const column = $('transcript-rows');
  for (const el of column ? column.querySelectorAll('.kq[data-kq-far]') : []) {
    if (!box.contains(el)) el.classList.toggle('lit', runs(el));
  }
}

/* A click on a mark brings its statement forward: on the passage being worked on its pair takes the
   caret, and on another passage the move goes there first, the way a click on its row goes, and then
   the pair takes the caret. An interviewer note open is kept first. Since 21 October (a tester's long
   quotes, many to a passage) the statement's box also scrolls into sight in its column when it stood out
   of it, by no more than it takes, and its top first when the box is taller than the column's view. */
function pairIntoView(el) {
  let pane = el.parentElement;
  while (pane && pane !== document.body) {
    const y = getComputedStyle(pane).overflowY;
    if ((y === 'auto' || y === 'scroll') && pane.scrollHeight > pane.clientHeight) break;
    pane = pane.parentElement;
  }
  if (!pane || pane === document.body) return;
  const edge = pane.getBoundingClientRect();
  // the card's foot, Add another and Next, held at the column's foot while the card runs past it, hides
  // what is under it, so the view ends over it
  const card = el.closest ? el.closest('#es-card') : null;
  const foot = card ? card.querySelector('.es-foot') : null;
  const under = foot ? foot.getBoundingClientRect().height + (parseFloat(getComputedStyle(foot).bottom) || 0) : 0;
  const view = { top: edge.top, bottom: edge.bottom - under, height: edge.height - under };
  const box = el.getBoundingClientRect();
  const room = 16;
  if (box.top >= view.top + room && box.bottom <= view.bottom - room) return;
  const by = box.height > view.height - 2 * room || box.top < view.top + room
    ? box.top - view.top - room : box.bottom - view.bottom + room;
  pane.scrollTop += by;
}

function toStatement(row, n) {
  const focusPair = () => {
    const el = pairEls()[n];
    if (!el || S.editing || S.timeEdit) return;
    S.pairFocus = el.dataset.pid;
    el.querySelector('.pair-es').focus({ preventScroll: true });
    pairIntoView(el);
  };
  if (S.note) keepNote();
  if (row.pos === S.at) { focusPair(); return Promise.resolve(); }
  return goTo(row.pos, { count: true }).then(() => {
    const now = current();
    if (now && now.key === row.key) focusPair();
  });
}

/* ──────────────────────────────────────────────── the quote being built ── */

/* A quote can be made of several pieces of one turn. A plain selection starts a fresh one, a
   selection with Cmd held adds a piece. The rule that turns the pieces into a quote lives in
   `quote.js`, which holds no DOM and is checked on its own. Since 30 October (quotespan) a piece may be
   in the same speaker's passage just before or after, each piece naming its passage by `key`, one with
   none the passage being worked on's, and the quote takes them in transcript order, an ellipsis at every
   gap, the interviewer's words between never in it. */

function turnPlainText() {
  return rowText(current());
}

/* the pieces held in one passage */
function piecesIn(row) {
  const now = current();
  return row ? S.pending.filter((p) => (p.key || (now && now.key)) === row.key) : [];
}

/* the passages holding pieces, in transcript order */
function pendingRows() {
  const now = current();
  const keys = new Set(S.pending.map((p) => p.key || (now && now.key)));
  if (!keys.size) return [];
  // pieces in the passage being worked on alone, as a quote of one passage always was
  if (now && keys.size === 1 && keys.has(now.key)) return [now];
  return S.flat.filter((r) => keys.has(r.key));
}

const pendingQuote = () => assembleAcross(pendingRows().map((row) => ({ pieces: piecesIn(row), text: rowText(row) })));

/* the pieces held in a passage beside the one being worked on, marked as the pieces there are */
const pendingLayer = (row) => (row && row !== current() ? mergePieces(piecesIn(row), rowText(row)) : []);

/* The runs with marks laid over them: the quotes, the pieces of a quote being built and the
   find's washes, each span carrying its class (`pending` when it names none) and a quote's the
   places of its pairs, so a character under two marks takes both. A highlight the workbook holds is
   drawn as plain words (16 October). A quote's mark carries its statement's colour by place since
   18 October (Adam's choice from a drawing), `data-es-colour`, the first statement's the crux orange,
   the next five the board map's participant colours and a seventh round again, as style.css sets them,
   and on words two statements share the second's, `data-es-colour-b`. */
function markedHtml(runs, spans) {
  let html = '';
  let at = 0;
  // a thematic analysis project's extracts, each numbered where its words end in the passage (codes.js)
  const ta = typeof cxOn === 'function' && cxOn();
  const ends = new Map();
  const numbered = new Set();
  if (ta) {
    for (const sp of spans) {
      if (!Number.isInteger(sp.ex) || sp.ex < 0 || Number.isInteger(sp.from)) continue;
      ends.set(sp.ex, Math.max(ends.get(sp.ex) || 0, sp.end));
    }
  }
  for (const run of runs) {
    let pos = 0;
    while (pos < run.text.length) {
      const abs = at + pos;
      let next = run.text.length;
      const cls = [];
      const kq = [];
      // a thematic analysis project's extracts the words belong to (codes)
      const exs = [];
      // a piece of the quote of her passage next to this one, by that passage and its place (quotespan)
      const far = [];
      for (const s of spans) {
        if (abs >= s.start && abs < s.end) {
          for (const c of (s.cls || 'pending').split(' ')) if (!cls.includes(c)) cls.push(c);
          if (Number.isInteger(s.ex) && s.ex >= 0 && !Number.isInteger(s.from) && !exs.includes(s.ex)) exs.push(s.ex);
          if (Number.isInteger(s.kq) && Number.isInteger(s.from)) {
            if (!far.includes(`${s.from}:${s.kq}`)) far.push(`${s.from}:${s.kq}`);
          } else if (Number.isInteger(s.kq) && !kq.includes(s.kq)) kq.push(s.kq);
          next = Math.min(next, s.end - at);
        } else if (s.start > abs) next = Math.min(next, s.start - at);
      }
      const chunk = esc(run.text.slice(pos, next));
      kq.sort((x, y) => x - y);
      exs.sort((x, y) => x - y);
      // the colour of its first statement by place, one of six and then round again, and on words two
      // statements share the second's too (18 October), a piece of another passage's quote its statement's
      // in a thematic analysis project an extract's codes share its words, coloured as the extract (codes)
      const places = (ta && exs.length ? exs : kq).concat(far.map((f) => Number(f.split(':')[1])));
      const colour = places.length > 1 ? ` data-es-colour="${places[0] % 6}" data-es-colour-b="${places[1] % 6}"`
        : places.length ? ` data-es-colour="${places[0] % 6}"` : '';
      const data = kq.length ? ` data-kq="${kq.join(' ')}"${far.length ? ` data-kq-far="${far.join(' ')}"` : ''}${colour} title="${escAttr(kqTitle(kq))}"`
        : far.length ? ` data-kq-far="${far.join(' ')}"${colour} title="${escAttr(kqFarTitle(far))}"` : '';
      html += cls.length ? `<span class="${cls.join(' ')}"${data}>${chunk}</span>` : chunk;
      // the extract's number after its last words, as its box is numbered (codes)
      if (ta) {
        for (const [place, end] of ends) {
          if (end === at + next && !numbered.has(place)) {
            numbered.add(place);
            // its number drawn by the stylesheet, so it is never among the passage's words a selection counts
            html += `<span class="cx-pn" data-es-colour="${place % 6}" data-n="${place + 1}" aria-hidden="true"></span>`;
          }
        }
      }
      pos = next;
    }
    at += run.text.length;
  }
  return html;
}

/* The assembled quote, under the turn. It says what it is, because until it was labelled it read
   as something the app had already done. Its key is the toolbar's tooltip's and the shortcuts card's
   alone, where a line beside the label said it a fourth time (17 October). A plain click in the
   column clears it, and so does Esc. */
function drawQuotePreview() {
  const turn = $('turn');
  if (!turn) return;
  let line = turn.querySelector('.quote-preview');
  const quote = pendingQuote();
  if (!quote) { if (line) line.remove(); return; }
  if (!line) {
    line = document.createElement('div');
    line.className = 'quote-preview';
    line.innerHTML = '<div class="quote-preview-head">'
      + `<span class="field-label">${esc(t('distil.pair.candidate'))}</span>`
      + '</div><div class="quote-preview-text"></div>';
    turn.appendChild(line);
  }
  line.querySelector('.quote-preview-text').textContent = quote;
}

function paintTurn(keep) {
  const row = current();
  const box = $('turn-text');
  if (!row || !box) return;
  // a save taken on the way out of a turn lands here while the column still holds the old one,
  // and drawTurn is about to redraw both
  const holder = box.closest('.turn');
  if (!holder || Number(holder.dataset.i) !== row.i) return;
  box.innerHTML = markedHtml(row.runs, [...kqLayer(row), ...mergePieces(piecesIn(row), turnPlainText()), ...findLayer(row)]);
  drawQuotePreview();
  lightMarks();
  if (keep) restoreSelection(box, keep.start, keep.end);
  // the minimap drawn again with the passage
  scheduleMinimap();
  if (typeof pairTakeDraw === 'function') pairTakeDraw();
}

function clearPending(repaint) {
  const had = S.pending.length > 0;
  const far = pendingRows().filter((r) => r !== current());
  S.pending = [];
  $('transcript-rows').querySelectorAll('.quote-preview').forEach((n) => n.remove());
  if (repaint && had) paintTurn(null);
  for (const row of far) repaintRow(row);
  if (typeof pairTakeDraw === 'function') pairTakeDraw();
}

/* the pieces held drawn again where they are, the passage being worked on and those beside it */
function paintPending() {
  paintTurn(null);
  for (const row of pendingRows()) if (row !== current()) repaintRow(row);
}

function takeSelection(add) {
  const sel = selectionInTurn();
  if (!sel) return add ? takeBeside() : false;
  const now = current();
  sel.key = now ? now.key : undefined;
  if (add) S.pending.push(sel); else S.pending = [sel];
  paintTurn(sel);
  return true;
}

/* A piece from her passage next to the one being worked on (quotespan, 30 October 2026, Adam): with a piece
   held, Cmd and words selected in the same speaker's passage just before or just after the passages the
   pieces are in add a piece there, the same gesture that adds a piece in one passage, so one quote takes in
   her adjacent passages. The interviewer's words, another speaker's and a passage further off are refused
   with a line, and nothing is taken. Answers whether the selection was its business. */
function takeBeside() {
  const now = current();
  if (!now || !S.pending.length) return false;
  const hits = selectionTurns();
  if (!hits || !hits.length) return false;
  if (hits.length > 1) { say(t('distil.assign.two_passages'), 4200); return true; }
  const holder = hits[0].box.closest('.turn');
  const row = holder ? S.flat[Number(holder.dataset.i)] : null;
  if (!row || row.i === now.i) return false;
  const why = besideRefusal(now, row);
  if (why) { say(why, 5200); return true; }
  const text = rowText(row);
  S.pending.push({ key: row.key, start: hits[0].start, end: hits[0].end, text: text.slice(hits[0].start, hits[0].end) });
  repaintRow(row);
  const box = holder.querySelector('.turn-text');
  if (box) restoreSelection(box, hits[0].start, hits[0].end);
  drawQuotePreview();
  if (typeof pairTakeDraw === 'function') pairTakeDraw();
  return true;
}

/* why words in `row` cannot be a piece of the quote being built on `now`, or '' when they can: a turn of the
   interviewer's, another speaker's passage, or one of hers that is not next to the passages the pieces are
   in, with nothing but the interviewer between */
function besideRefusal(now, row) {
  if (!row.stop) return t('distil.pair.span_interviewer');
  if (row.other || now.other || row.sheet !== now.sheet || speakerKey(row) !== speakerKey(now)) return t('distil.pair.span_speaker');
  const run = quoteRun(now, S.flat.length);
  const held = new Set([now.key, ...S.pending.map((p) => p.key || now.key)]);
  const places = run.rows.map((r, k) => (held.has(r.key) ? k : -1)).filter((k) => k >= 0);
  const at = run.rows.indexOf(row);
  if (at < 0 || at < Math.min(...places) - 1 || at > Math.max(...places) + 1) return t('distil.pair.span_next');
  return '';
}

/* Undo and redo of an empty quote `q` filled. Undo gives the quote of the pair holding the
   new quote back exactly what it held before, empty or "(no quote)", its statement and anything
   written in it since left as they are, and redo puts the new quote back into the pair it went
   into, holding what it finds there as the old one for the next undo. The pieces come back with an
   undo so a second `q` takes the same quote again, and a turn that had already been saved with the
   quote in it is saved again, so the workbook ends where the fields do. */
async function quotePut(entry, adding) {
  const row = rowByKey(entry.key);
  if (!row) throw new Error(t('distil.undo.passage_gone'));
  const stored = rowPairs(row).some((p) => p.kq === entry.quote);
  const els = pairEls();
  if (adding) {
    const place = Math.max(0, Math.min(entry.place, els.length - 1));
    const field = els[place].querySelector('.pair-kq');
    Object.assign(entry, { place, old: field.value });
    field.value = entry.quote;
  } else {
    const out = quoteOut(pairsNow(), entry.place, entry.quote);
    if (out) els[out.place].querySelector('.pair-kq').value = entry.old || '';
  }
  pairsChanged();
  // the save comes first, because it clears the pieces on its way through
  if (adding ? entry.resaved : stored) {
    entry.resaved = !adding;
    await commit(row, false);
  }
  if (adding) clearPending(true);
  else { S.pending = entry.pieces.map((p) => ({ ...p })); paintPending(); }
  if (adding) say(t('distil.undo.quote_back'), 2400);
  else say(t('distil.undo.quote_out'), 2400);
}

/* `q` and the Quote button beside it, one act for a quote (16 October, Adam's decision on a
   tester's feedback). The words selected in the passage, or the pieces held with Cmd, are put
   together as one quote, verbatim, and go into the quote of the pair being worked on while it
   has none, and else into a pair of their own under the last, as Add another puts one
   (`quoteTarget`), the caret landing in that pair's statement either way. A quote is changed by
   clearing it, then `q`, so none is ever written over. Words selected in another of her passages on
   screen go there first, the way a click on it goes, then act the same. An interviewer note open
   is kept first, as a click on the button keeps it, so the quote never goes into a pair out of
   sight. One step of undo either way: an empty quote filled goes back to what it held
   (`quotePut`), and a pair added goes with its quote (`statementPut`). Until 16 October `q` replaced
   the quote of the pair in hand and `s`, or New statement, made the new pair. In a thematic analysis project
   `opts.code` or `opts.vivo` puts a code on the new extract at once, the quick keys' R, 1 to 5 and V (codes.js,
   cxQuickPut, quickkeysB). */
async function commitQuote(opts = {}) {
  if (!S.data || $('work').hidden || S.quoting) return;
  selBarHide();
  const there = selectionElsewhere();
  if (!there && !S.pending.length && !selectionInTurn()) {
    say(t('distil.pair.select_first_q'));
    return;
  }
  if (S.note) keepNote();
  if (there) {
    S.quoting = true;
    try { await goTo(there.row.pos, { count: true }); } finally { S.quoting = false; }
    const now = current();
    if (!now || now.key !== there.row.key) return;
    S.pending = [{ key: there.row.key, start: there.start, end: there.end, text: there.text }];
    // a card the move raised, a round closed, stands in front: the words wait as the candidate
    if (anyOverlayOpen()) { paintTurn(null); return; }
  } else if (!S.pending.length) takeSelection(false);
  const quote = pendingQuote();
  if (!quote) { say(t('distil.pair.nothing_selected')); return; }
  const row = current();
  if ((opts.code || opts.vivo) && typeof cxQuickPut === 'function') { cxQuickPut(row, quote, opts); return; }
  const pieces = S.pending.map((p) => ({ ...p, key: p.key || row.key }));
  const { place, added, old } = quoteTarget(pairsNow(), workingPlace());
  const el = added ? insertPair({ es: '', kq: quote }) : pairEls()[place];
  el.querySelector('.pair-kq').value = quote;
  S.pairFocus = el.dataset.pid;
  pairsChanged();
  clearPending(true);
  el.querySelector('.pair-es').focus();
  // in a thematic analysis project the new extract's Add a code takes the caret (codes.js)
  if (typeof cxOn === 'function' && cxOn()) cxFocusPair(el);
  undoPush(added
    ? { key: row.key, what: 'the new pair', quote, pieces, resaved: false, place, taken: false,
      undo: (e) => statementPut(e, false), redo: (e) => statementPut(e, true) }
    : { key: row.key, what: 'the quote', quote, old, pieces, resaved: false, place,
      undo: (e) => quotePut(e, false), redo: (e) => quotePut(e, true) });
  say(t('distil.pair.quote_added'), 2200);
}

/* Undo and redo of a pair `q` added. Undo finds the pair holding exactly its quote, as `quoteOut`
   finds one, and takes it out while its statement is still empty. A statement written there since
   stays, with its quote emptied, so an undo never takes his words. Redo puts the pair back at
   its place, or the quote back into the pair the undo left. The pieces come back marked with an
   undo, so a second `q` makes the same pair, and a passage already saved with the quote is saved
   again, as `quotePut` does. */
async function statementPut(entry, adding) {
  const row = rowByKey(entry.key);
  if (!row) throw new Error(t('distil.undo.passage_gone'));
  const stored = rowPairs(row).some((p) => p.kq === entry.quote);
  if (adding) {
    const els = pairEls();
    if (entry.taken) insertPair({ es: '', kq: entry.quote }, entry.place);
    else els[Math.max(0, Math.min(entry.place, els.length - 1))].querySelector('.pair-kq').value = entry.quote;
  } else {
    const out = quoteOut(pairsNow(), entry.place, entry.quote);
    const el = out ? pairEls()[out.place] : null;
    entry.taken = !!el && !el.querySelector('.pair-es').value.trim();
    if (el) entry.place = out.place;
    if (el && entry.taken) el.remove();
    else if (el) el.querySelector('.pair-kq').value = '';
    if (!pairEls().length) insertPair({ es: '', kq: '' });
  }
  pairsChanged();
  // the save comes first, because it clears the pieces on its way through
  if (adding ? entry.resaved : stored) {
    entry.resaved = !adding;
    await commit(row, false);
  }
  if (adding) clearPending(true);
  else { S.pending = entry.pieces.map((p) => ({ ...p })); paintPending(); }
  if (adding) say(entry.taken ? t('distil.undo.statement_back') : t('distil.undo.quote_back'), 2400);
  else say(entry.taken ? t('distil.undo.statement_out') : t('distil.undo.quote_out'), 2400);
}

/* ─────────────────────────────────────────── the toolbar by the selection ── */

/* Words selected in one of her passages bring a small toolbar beside them, Quote and Give to
   another speaker, the same acts as `q` and `c` (16 October, after a tester found too much hidden
   behind keys and right-click), each key in its tooltip and the shortcuts card, never on its face
   (17 October). It stands above the selection's first line, or
   under its last where the column has no room above, so it never covers the words, and inside the
   column. Above and under are measured from every rectangle of the selection, the highest and the
   lowest, and where the notes stand beside the words it keeps to the words' side of them, wrapping
   there if it must, so it never covers the notes (16 October, later, after it was found on the first
   line and the notes' edge at 1280). Selecting moves the keyboard to the transcript, so `q` and `c`
   act at once even when the caret was in a field, where until then a `c` could type itself into a
   statement. Esc, a click elsewhere, a selection gone or a move takes it away. */
function selBarPick() {
  if ($('work').hidden || S.editing || S.timeEdit) return null;
  const hits = selectionTurns();
  if (!hits || hits.length !== 1) return null;
  const holder = hits[0].box.closest('.turn');
  const row = holder ? S.flat[Number(holder.dataset.i)] : null;
  if (!row || !row.stop) return null;
  const rects = [...window.getSelection().getRangeAt(0).getClientRects()].filter((r) => r.width || r.height);
  if (!rects.length) return null;
  return { row, holder, rects, first: rects[0], top: Math.min(...rects.map((r) => r.top)),
    bottom: Math.max(...rects.map((r) => r.bottom)) };
}

/* The room the toolbar may stand in across the screen: the column less a few pixels either side, and
   where the passage's statements and notes stand in columns beside its words (17 October), only the
   transcript's column, from its heading, so it never covers a statement or a note */
function selBarRoom(holder, col) {
  const room = { left: col.left + 4, right: col.right - 4 };
  const head = $('cols-head').querySelector('.col-head[data-col="transcript"]');
  const words = holder.querySelector('.turn-text');
  if (!head || !head.getClientRects().length || !words) return room;
  const w = words.getBoundingClientRect();
  const beside = [...holder.querySelectorAll(':scope > .turn-es, :scope > .turn-notes')]
    .filter((c) => c.getClientRects().length).map((c) => c.getBoundingClientRect());
  if (!beside.some((b) => b.left >= w.right - 1 || b.right <= w.left + 1)) return room;
  const t = head.getBoundingClientRect();
  room.left = Math.max(room.left, t.left);
  room.right = Math.min(room.right, t.right);
  return room;
}

/* the box of a passage's speaker line, its name and time, or null where it shows none */
function selBarSpeaker(holder) {
  const name = holder.querySelector('.turn-gutter');
  return name && name.getClientRects().length ? name.getBoundingClientRect() : null;
}

/* The lines of words near the toolbar, each line's box as the page draws it: every passage's words, the
   notes under them where they stand in the transcript's column, and every speaker line, of the rows
   within `reach` pixels of `top` to `bottom` */
function selBarLines(top, bottom, reach = 120) {
  const out = [];
  for (const row of $('transcript-rows').querySelectorAll('.turn')) {
    const box = row.getBoundingClientRect();
    if (box.bottom < top - reach || box.top > bottom + reach) continue;
    for (const el of row.querySelectorAll('.turn-text, .turn-notes-text, .turn-gutter > *')) {
      if (!el.getClientRects().length) continue;
      const range = document.createRange();
      range.selectNodeContents(el);
      for (const r of range.getClientRects()) if (r.width && r.height) out.push(r);
    }
  }
  return out;
}

/* the line of words across the toolbar's own width, `left` to `left + w`, that `edge` would cut through its
   box, or none */
function selBarCut(edge, lines, left, w) {
  return lines.find((r) => r.left < left + w && r.right > left && edge > r.top + 1 && edge < r.bottom - 1);
}

/* The toolbar's far edge, `edge`, moved out past any line of words it would cut through its letters, so the
   toolbar covers a line whole or not at all (18 October, where above the selection it covered half the line
   above): up to the line's top for a toolbar above the words, `up`, and down to its foot for one below. */
function selBarWhole(edge, lines, left, w, up) {
  let at = edge;
  for (let pass = 0; pass <= lines.length; pass += 1) {
    const cut = selBarCut(at, lines, left, w);
    if (!cut) break;
    at = up ? cut.top - 1 : cut.bottom + 1;
  }
  return at;
}

function selBarPlace() {
  const bar = $('sel-bar');
  const pick = selBarPick();
  if (!pick || S.rowMenu) { bar.hidden = true; return false; }
  bar.hidden = false;
  const col = $('transcript').getBoundingClientRect();
  const room = selBarRoom(pick.holder, col);
  // measured at its room's left edge and never wider than the room, so on a phone, or beside the
  // notes, it wraps inside it, where a place left from before squeezed it and it ran past the edge,
  // and at its own height before it grows over a line
  bar.style.maxWidth = `${Math.max(0, Math.round(room.right - room.left))}px`;
  bar.style.left = `${Math.round(room.left)}px`;
  bar.style.minHeight = '';
  const w = bar.offsetWidth;
  const h = bar.offsetHeight;
  const gap = 6;
  const left = Math.max(room.left, Math.min(pick.first.left, room.right - w));
  // the passage's speaker line, its name and time, is kept clear as the words are: above the selection
  // the toolbar goes over that line too where the two would meet (17 October, after the screenshot
  // check, where at 360 it covered the name)
  const line = selBarSpeaker(pick.holder);
  const meets = (at) => !!line && at < line.bottom && at + h > line.top && left < line.right && left + w > line.left;
  const lines = selBarLines(pick.top - 3 * h, pick.bottom + 3 * h);
  // a line's box holds a little room over its letters and its descenders' room under them, these shares of
  // its height, which an edge may cut where it cannot step clear
  const head = 0.12;
  const tail = 0.22;
  // Above the selection, its foot clear of the line above. A line its top would cut: it steps down clear of
  // that line where its foot still stands 2 pixels over the words, else grows up over the line whole where
  // it would cut the letters, and leaves it be where only the room under them, a descender's tail, is cut
  let foot = Math.min(selBarWhole(pick.top - gap, lines, left, w, false), pick.top - 1);
  if (meets(foot - h)) foot = line.top - gap;
  let top = foot - h;
  const over = selBarCut(top, lines, left, w);
  if (over && over.bottom + 1 - top <= gap - 2) {
    foot += over.bottom + 1 - top;
    top = over.bottom + 1;
  } else if (over && top < over.bottom - tail * (over.bottom - over.top)) top = selBarWhole(top, lines, left, w, true);
  if (top < col.top + 2) {
    // and with no room there, under it the same way: a step up clear of a line its foot would cut, or down
    // over that line whole where it would cut its letters, the room over them left be
    top = Math.max(selBarWhole(pick.bottom + gap, lines, left, w, true), pick.bottom + 1);
    if (meets(top)) top = line.bottom + gap;
    foot = top + h;
    const under = selBarCut(foot, lines, left, w);
    if (under && foot - (under.top - 1) <= gap - 2) {
      top -= foot - (under.top - 1);
      foot = under.top - 1;
    } else if (under && foot > under.top + head * (under.bottom - under.top)) foot = selBarWhole(foot, lines, left, w, false);
  }
  // with no room above or below inside the column it stays away rather than cover the words
  if (foot > col.bottom - 2 || pick.bottom < col.top || pick.top > col.bottom) {
    bar.hidden = true;
    return false;
  }
  if (foot - top > h + 0.5) bar.style.minHeight = `${Math.ceil(foot - top)}px`;
  bar.style.left = `${Math.round(left)}px`;
  bar.style.top = `${Math.round(top)}px`;
  return true;
}

function selBarShow() {
  // a thematic analysis project's In vivo code and the codes used last, before it is measured (quickkeysB)
  if (typeof cxQuickBar === 'function') cxQuickBar();
  selBarPlace();
  if (!selBarPick()) return;
  // the keyboard follows the selection, so q and c are the transcript's and never type into a field
  const focus = document.activeElement;
  if (focus && focus !== document.body && /TEXTAREA|INPUT/.test(focus.tagName)) {
    $('transcript').focus({ preventScroll: true });
  }
}

const selBarHide = () => { if ($('sel-bar')) $('sel-bar').hidden = true; };
const selBarOn = () => !!$('sel-bar') && !$('sel-bar').hidden;

/* ────────────────────────────────────────────────── editing a turn ── */

/* The transcript carries slips, and a slip is easier to correct while the turn is in front of him
   than in Excel afterwards. `e` opens the turn being worked on, a double-click opens any turn,
   hers and Adam's alike. The box holds the plain text of the cell with every run flattened, and
   `Cmd + Enter` saves it.

   Nothing else moves. The statement fields, the pace clock, the speaker, the timecode and the
   playhead are all left where they are, and only the transcript cell is written. The
   server keeps the cell's style, adds no fill, finds every highlight again by phrase and records
   the old and the new text in the progress file. The raw source a case was built from is not
   touched, which is the same gap a trim leaves. */

function growBox(box) {
  box.style.height = 'auto';
  box.style.height = `${box.scrollHeight + 2}px`;
}

/* One turn redrawn from its runs. The turn being worked on goes through paintTurn, so a quote
   being built there keeps its marks. */
function repaintRow(row) {
  const now = current();
  if (now && now.i === row.i) { paintTurn(null); return; }
  const el = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"] .turn-text`);
  if (el) el.innerHTML = rowHtml(row);
  scheduleMinimap();
}

function openEditor(row) {
  if (!row) return;
  if (S.note) keepNote();                   // the interviewer note is kept, and the box takes the caret
  if (S.editing) closeEditor();             // one at a time, and the one already open is cancelled
  const holder = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"]`);
  const text = holder ? holder.querySelector('.turn-text') : null;
  if (!holder || !text) return;
  closeTimeEdit();
  clearPending(true);
  const box = document.createElement('div');
  box.className = 'turn-edit';
  // Grammarly is told to stay out: the transcript is speech and its grammar is the speaker's
  box.innerHTML = `<textarea class="turn-edit-box" spellcheck="true" data-gramm="false" data-gramm_editor="false" data-enable-grammarly="false"></textarea>
      <div class="turn-edit-foot">
        <span class="mono turn-edit-hint">${esc(keyName(t('distil.edit.hint')))}</span>
        <button type="button" class="ghost small" data-edit="cancel">${esc(t('distil.edit.cancel'))}</button>
        <button type="button" class="ghost small" data-edit="save">${esc(t('distil.edit.save'))}</button>
      </div>`;
  const field = box.querySelector('.turn-edit-box');
  field.value = row.text || '';
  text.hidden = true;
  holder.insertBefore(box, text.nextSibling);
  S.editing = { i: row.i, key: row.key, holder, text, box, field };
  field.addEventListener('input', () => growBox(field));
  // the box keeps its own two keys: the page's Cmd + Enter saves the statement fields, and its
  // Esc has three other jobs, so neither is allowed past the box while it is open
  const ownKeys = (e) => {
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeEditor(); return; }
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      saveEdit();
    }
  };
  field.addEventListener('keydown', ownKeys);
  box.addEventListener('click', (e) => {
    const pick = e.target.closest('[data-edit]');
    if (!pick) return;
    if (pick.dataset.edit === 'save') saveEdit(); else closeEditor();
  });
  growBox(field);
  field.focus();
  try { field.setSelectionRange(field.value.length, field.value.length); } catch { /* not a field */ }
}

/* Cancel: the box goes, the text comes back as it was, and nothing was written. */
function closeEditor() {
  const open = S.editing;
  if (!open) return;
  S.editing = null;
  open.box.remove();
  open.text.hidden = false;
  const row = S.flat[open.i];
  if (row) repaintRow(row);
  if (!$('work').hidden) focusEntry();
}

/* The endpoint takes the whole text and hands back the row as the reader renders it, so one turn
   is redrawn and the sheet is not rebuilt. Undo comes back through here with the old text, which
   re-keys the highlights again. A timecode goes with the text only from the box in the margin,
   which sends the text unchanged, and the answer carries the timecode as the cell now holds it. */
async function editApply(key, text, timecode) {
  const row = rowByKey(key);
  if (!row) throw new Error(t('distil.undo.passage_gone'));
  const body = { path: S.data.path, sheet: row.sheet, row: row.row, text };
  if (timecode !== undefined) body.timecode = timecode;
  const sameText = text === row.text;
  const data = await api('/api/edit-turn', body);
  // a server from before the timecode field reads the text and never the timecode, and says
  // nothing about it, so the answer with no time in it is the sign. The text went unchanged, so
  // nothing was written
  if (timecode !== undefined && data.time === undefined) throw new Error(RESTART_LINE);
  row.runs = data.runs;
  row.text = data.text;
  repaintRow(row);
  // an open find counts the corrected turn again
  findRefresh();
  if (data.time !== undefined && data.time !== row.time) {
    row.seconds = data.seconds;
    row.time = data.time;
    drawRowTime(row);
  }
  const dropped = data.dropped || [];
  if (dropped.length) say(dropped.map((p) => t('distil.edit.dropped', { quote: p })).join(' · '), 8000);
  else if (timecode !== undefined && sameText) {
    say(data.changed === false ? t('distil.edit.same_time') : t('distil.edit.time_saved'), 2200);
  } else say(t('distil.edit.saved'), 2200);
  return data;
}

/* One kind of entry for a correction, to the text or to the timecode. `was` and `now` each carry
   the text, and the timecode as well when that is what moved, so undo and redo go back through the
   same endpoint and the highlights are re-keyed on the way. */
function pushEditUndo(row, was, now) {
  undoPush({
    key: row.key,
    what: now.time === undefined ? 'the correction to this passage' : 'the timecode of this passage',
    was,
    now,
    undo: (e) => editApply(e.key, e.was.text, e.was.time),
    redo: (e) => editApply(e.key, e.now.text, e.now.time),
  });
}

async function saveEdit() {
  const open = S.editing;
  if (!open) return;
  const row = S.flat[open.i];
  const before = row ? row.text : '';
  const after = open.field.value;
  if (!row || after === before) { closeEditor(); return; }
  try {
    await editApply(row.key, after);
  } catch (err) {
    // the box stays open with his text in it, so nothing is lost to a server that is behind
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return;
  }
  pushEditUndo(row, { text: before }, { text: after });
  closeEditor();
}

/* A timecode corrected in the margin shows there at once, a button that plays from the new place.
   The playhead's index of timecodes is built again and the mark is taken again from the clock, so
   a click on the timecode, a move to the turn and the mark all go by the new time. The player
   itself is left exactly where it is. */
function drawRowTime(row) {
  const el = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"] .turn-gutter .time`);
  if (el) el.outerHTML = timeHtml(row);
  S.spansSheet = null;
  const now = current();
  if (now && now.i === row.i) $('back-to-turn-time').textContent = row.time;
  const player = $('player');
  if (S.audioSheet === row.sheet && player.getAttribute('src')) {
    markTurnAt(heardAt(player.readyState >= 1 ? (player.currentTime || 0) : (S.cueAt || 0)));
  }
}

/* ──────────────────────────────────────────────── correcting a timecode ── */

/* A timecode is corrected where it stands. A double-click on it in the margin, or Edit timecode in
   the row's menu, puts a small box in its place, prefilled the way the player's clock writes it,
   MM:SS or H:MM:SS past the hour, with the text selected. Enter saves, Esc cancels, and so does a
   click anywhere else. The first click of the double-click has already played from the timecode,
   and the player is left as that click left it.

   Saving goes through the endpoint a correction to the text goes through, with the text unchanged,
   so the server writes the timestamp cell in the representation it already holds and records the
   old and the new timecode under `edits`. One it cannot read is refused with its own line, and the
   box stays open with what he typed in it. */
function openTimeEdit(row) {
  if (!row) return;
  if (S.editing) closeEditor();
  closeTimeEdit();
  closeRowMenu();
  const time = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"] .turn-gutter .time`);
  if (!time) return;
  const field = document.createElement('input');
  field.type = 'text';
  field.className = 'mono time-edit';
  field.spellcheck = false;
  field.autocomplete = 'off';
  field.dataset.gramm = 'false';   // Grammarly stays out of a timecode
  field.title = t('distil.time.title');
  field.setAttribute('aria-label', t('distil.time.label'));
  const was = (row.seconds === null || row.seconds === undefined) ? '' : timecode(row.seconds, caseTimecodes());
  field.value = was;
  time.hidden = true;
  time.after(field);
  S.timeEdit = { i: row.i, key: row.key, time, field, was, busy: false };
  // the box keeps its own keys: Enter saves here and never reaches the page, Esc has other jobs
  // there, and Cmd + Z is the box's own undo while he types
  field.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeTimeEdit(); return; }
    if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); saveTimeEdit(); return; }
    if ((e.metaKey || e.ctrlKey) && (e.key === 'z' || e.key === 'Z')) e.stopPropagation();
  });
  field.focus({ preventScroll: true });
  field.select();
}

/* Cancel: the box goes, the timecode comes back as it was, and nothing was written. The caret goes
   back to the statement field when it was in the box, or nowhere in particular. */
function closeTimeEdit() {
  const open = S.timeEdit;
  if (!open) return;
  S.timeEdit = null;
  const focus = document.activeElement;
  const hadFocus = focus === open.field || !focus || focus === document.body;
  open.field.remove();
  open.time.hidden = false;
  if (hadFocus && !$('work').hidden) focusEntry();
}

async function saveTimeEdit() {
  const open = S.timeEdit;
  if (!open || open.busy) return;
  const row = S.flat[open.i];
  const typed = open.field.value.trim();
  if (!row || typed === open.was) { closeTimeEdit(); return; }
  if (!typed) { say(t('distil.time.empty')); return; }
  open.busy = true;
  const text = row.text;
  let data;
  try {
    data = await editApply(row.key, text, typed);
  } catch (err) {
    open.busy = false;
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    if (S.timeEdit === open) { open.field.focus({ preventScroll: true }); open.field.select(); }
    return;
  }
  if (S.timeEdit === open) closeTimeEdit();
  if (data.changed === false) return;
  // a turn that had no timecode the reader could take has nothing for an undo to put back
  if (!open.was) { say(keyName(t('distil.time.saved_new')), 4200); return; }
  pushEditUndo(row, { text, time: open.was }, { text, time: typed });
}

/* ──────────────────────────────────────────────── find and replace ── */

/* Find and replace over the transcript column, every row of every sheet, the interviewer's turns
   included (item 139). `Cmd + Shift + F` or the magnifier in the bar opens one card at the top
   right with no veil, so the sheet stays in sight. As Find is typed the page counts over the text
   it already holds, every sheet of it, and washes each occurrence on the sheet on screen in a
   yellow that is never written anywhere, the one in focus stronger, with the column taken to it
   the way the playhead takes it. Next and Previous walk them in transcript order, and across the
   sheets through the switcher's own path. The match is literal, never a pattern, and a whole word
   is bounded by anything that is not a letter or a digit, the rules `workbook.find_spans` keeps on
   the server, so the two never disagree.

   Replace and Replace all go to `/api/replace`, which counts again, writes the transcript cells
   through the per-cell write a correction takes and records every row under one batch id. The
   page redraws the rows it answers with and nothing else, names a highlight dropped with the
   sheet and the timecode before it, and counts again. One press is one step of undo. A focus only
   ever sits on the sheet on screen, so Replace never touches words out of sight. */

const FIND = {
  hits: [],          // every occurrence on every sheet, in transcript order
  byRow: new Map(),  // the occurrences of each row, by its place in S.flat
  at: -1,            // the one in focus, an index into hits, or none
  painted: new Set(), // the rows on screen drawn with a wash
  timer: null,
  busy: false,
};
const FIND_FIELDS = ['find-text', 'find-with', 'find-word', 'find-case'];
const FIND_WORDISH = /[\p{L}\p{N}]/u;
const findOpen = () => !$('find').hidden;
const wordish = (ch) => !!ch && FIND_WORDISH.test(ch);

/* Every occurrence of `find` in `text`, as {start, end}, left to right and never overlapping. With
   `word` on an occurrence may not run into a letter or a digit at an end that is one itself, so
   "so" is never found inside "also" or "sofa" and is found in "so," and "So". */
function findSpans(text, find, word, matchCase) {
  const spans = [];
  if (!find || !text) return spans;
  const re = new RegExp(find.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&'), matchCase ? 'gu' : 'giu');
  let pos = 0;
  while (pos <= text.length) {
    re.lastIndex = pos;
    const m = re.exec(text);
    if (!m) break;
    const start = m.index;
    const end = start + m[0].length;
    if (word && ((wordish(text[start]) && wordish(text[start - 1]))
        || (wordish(text[end - 1]) && wordish(text[end])))) {
      pos = start + 1;
      continue;
    }
    spans.push({ start, end });
    pos = end;
  }
  return spans;
}

const findOptions = () => ({
  find: $('find-text').value, word: $('find-word').checked, matchCase: $('find-case').checked,
});

/* Count over every row the page holds. Each occurrence knows its row, its place among the row's
   matches, which is what Replace names it by, and whether it touches a highlight. Replace all
   changes the words in the statements, the quotes and the notes too (24 October, "Everything
   follows"), so those are counted beside the transcript, by the same matcher, into `more`. */
function findCount() {
  const { find, word, matchCase } = findOptions();
  FIND.hits = [];
  FIND.byRow = new Map();
  FIND.more = 0;
  if (!find || !S.data) return;
  for (const row of S.flat) {
    for (const field of [row.es, row.kq, row.en, row.note]) {
      for (const line of String(field || '').split('\n')) FIND.more += findSpans(line, find, word, matchCase).length;
    }
    const spans = findSpans(row.text || '', find, word, matchCase);
    if (!spans.length) continue;
    const mask = cruxMask(row.runs);
    const list = spans.map((s, ord) => ({
      i: row.i, sheet: row.sheet, start: s.start, end: s.end, ord, n: FIND.hits.length + ord,
      crux: mask.slice(s.start, s.end).some(Boolean),
    }));
    FIND.hits.push(...list);
    FIND.byRow.set(row.i, list);
  }
}

/* the washes on one row, the one in focus stronger, while the card is open */
function findLayer(row) {
  if (!findOpen() || !row) return [];
  return (FIND.byRow.get(row.i) || []).map((h) => ({
    start: h.start, end: h.end, cls: h.n === FIND.at ? 'find-hit find-on' : 'find-hit',
  }));
}

/* the first occurrence on the sheet on screen at or after the turn being worked on, or the first
   on that sheet, or none */
function findNear() {
  const here = current();
  const on = FIND.hits.filter((h) => h.sheet === S.sheetDrawn);
  if (!on.length) return -1;
  const after = here && here.sheet === S.sheetDrawn ? on.find((h) => h.i >= here.i) : null;
  return (after || on[0]).n;
}

/* the first occurrence on the sheet on screen from a place in a row on, or none */
function findAfter(at) {
  const hit = FIND.hits.find((h) => h.sheet === S.sheetDrawn
    && (h.i > at.i || (h.i === at.i && h.start >= at.start)));
  return hit ? hit.n : -1;
}

/* Every row on screen that carries a wash, or carried one, drawn again, and nothing else. */
function drawFindMarks() {
  const want = new Set();
  if (findOpen()) for (const h of FIND.hits) if (h.sheet === S.sheetDrawn) want.add(h.i);
  for (const i of new Set([...FIND.painted, ...want])) {
    const row = S.flat[i];
    if (row && row.sheet === S.sheetDrawn) repaintRow(row);
  }
  FIND.painted = want;
}

/* The count line: "14 on Initial, 3 on 2d" and "17 on 2 sheets" in the small type beside it, the
   occurrences that touch a highlight after a dot, "No occurrences", or nothing while Find is
   empty. When the words also stand in the statements, quotes or notes it reads "8 in all: 3 in the
   transcript, 5 in your analysis" (26 October, Adam's wording C). Replace all carries the number, so it is in front of him when he presses it. */
function drawFindCount() {
  const { find } = findOptions();
  const n = FIND.hits.length;
  const more = FIND.more || 0;
  let line = '';
  let total = '';
  if (find && !n && !more) line = t('distil.find.none');
  else if (n || more) {
    const per = new Map();
    for (const h of FIND.hits) per.set(h.sheet, (per.get(h.sheet) || 0) + 1);
    const names = sheetNames().filter((s) => per.has(s));
    const parts = [names.map((s) => t('distil.find.on_sheet', { n: per.get(s), sheet: s })).join(', ')];
    const inside = FIND.hits.filter((h) => h.crux).length;
    if (inside) parts.push(t('distil.find.inside', { n: inside }));
    line = parts.filter(Boolean).join(' · ');
    if (more) line = t('distil.find.in_all', { all: n + more, n, more });
    if (names.length > 1) total = t('distil.find.total', { n, sheets: names.length });
  }
  $('find-said').textContent = line;
  $('find-total').textContent = total;
  $('find-all').textContent = n + more ? t('distil.find.replace_all_n', { n: n + more }) : t('distil.find.replace_all');
  $('find-all').disabled = !(n + more) || FIND.busy;
  $('find-one').disabled = !FIND.hits[FIND.at] || FIND.busy;
  $('find-prev').disabled = !n;
  $('find-next').disabled = !n;
  findRoom();
}

/* Stacked, below 1100px, the card stands at the foot of the window, where the line the app says
   things in would cover it, so that line rises above the card while it is open. */
function findRoom() {
  const box = $('find').getBoundingClientRect();
  const low = findOpen() && box.bottom > window.innerHeight - 40;
  document.body.style.setProperty('--find-room', low ? `${Math.round(window.innerHeight - box.top)}px` : '0px');
}

/* Count again and draw. `where` places the focus: 'near' for a fresh find, a place in a row for
   the words after a replace, and nothing to keep it where it was. */
function findRefresh(where) {
  if (!findOpen()) return;
  const was = FIND.hits[FIND.at];
  findCount();
  if (where === 'near') FIND.at = findNear();
  else if (where) FIND.at = findAfter(where);
  else FIND.at = was ? findAfter({ i: was.i, start: was.start }) : findNear();
  drawFindMarks();
  drawFindCount();
}

/* A new sheet on screen: its occurrences take the washes, and the focus moves onto it. */
function findSheetDrawn() {
  const hit = FIND.hits[FIND.at];
  if (!hit || hit.sheet !== S.sheetDrawn) FIND.at = findNear();
  FIND.painted = new Set();
  drawFindMarks();
  drawFindCount();
}

/* The column taken to the occurrence in focus the way the playhead takes it: only when it is out
   of sight, centred, and gliding unless motion is reduced. */
function findScroll() {
  const el = $('transcript-rows').querySelector('.find-on');
  if (!el) return;
  const col = $('transcript');
  const colBox = col.getBoundingClientRect();
  const box = el.getBoundingClientRect();
  if (box.top >= colBox.top + 48 && box.bottom <= colBox.bottom - 48) return;
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const top = col.scrollTop + (box.top - colBox.top) - (col.clientHeight - box.height) / 2;
  col.scrollTo({ top: Math.max(0, top), behavior: still ? 'auto' : 'smooth' });
}

/* Focus one occurrence. One on another sheet goes there through the switcher's own path, and the
   caret comes back to the card, so Enter goes on finding rather than typing in the fields. */
async function findFocus(n) {
  const hit = FIND.hits[n];
  if (!hit) return;
  if (hit.sheet !== S.sheetDrawn) {
    const caret = document.activeElement;
    await toSheet(hit.sheet);
    if (S.sheetDrawn !== hit.sheet || FIND.hits[n] !== hit) return;
    FIND.at = n;
    drawFindMarks();
    drawFindCount();
    if (caret && $('find').contains(caret)) caret.focus({ preventScroll: true });
    // after the move has centred the turn it landed on
    requestAnimationFrame(() => requestAnimationFrame(findScroll));
    return;
  }
  FIND.at = n;
  drawFindMarks();
  drawFindCount();
  findScroll();
}

/* Next and Previous, in transcript order across the sheets, round from the last to the first.
   With none in focus they start from the turn being worked on. */
function findStep(delta) {
  const all = FIND.hits;
  if (!all.length || FIND.busy) return Promise.resolve();
  let n;
  if (all[FIND.at]) n = (FIND.at + delta + all.length) % all.length;
  else {
    const here = current();
    const at = here ? here.i : -1;
    if (delta > 0) {
      n = all.findIndex((h) => h.i >= at);
      if (n < 0) n = 0;
    } else {
      n = -1;
      all.forEach((h, k) => { if (h.i < at) n = k; });
      if (n < 0) n = all.length - 1;
    }
  }
  return findFocus(n);
}

function openFind() {
  if (!S.data || $('work').hidden) return;
  // the card cancels a turn open for correction, as a move does, and the margin's small boxes
  if (S.editing) closeEditor();
  closeTimeEdit();
  closeRowMenu();
  // words selected on one line of the column start the find
  const sel = window.getSelection();
  const picked = sel && sel.rangeCount && !sel.isCollapsed
    && $('transcript').contains(sel.getRangeAt(0).commonAncestorContainer) ? sel.toString() : '';
  const fresh = picked && !/\n/.test(picked) && picked.length <= 80 && picked !== $('find-text').value;
  if (fresh) $('find-text').value = picked;
  const was = findOpen();
  show('find');
  $('find-text').focus();
  $('find-text').select();
  if (!was || fresh) { findRefresh('near'); findScroll(); }
  drawToPair();
  findRoom();
}

function closeFind() {
  if (!findOpen()) return;
  hide('find');
  clearTimeout(FIND.timer);
  FIND.at = -1;
  drawFindMarks();
  FIND.hits = [];
  FIND.byRow = new Map();
  findRoom();
  if (!$('work').hidden) focusEntry();
}

/* The rows a replace, its undo or its redo answered with, taken into the page and drawn again.
   A quote being built on a turn whose text changed loses its pieces, which named the old text.
   The statements, quotes and notes the replace changed come in with the row and its version, and
   the fields of the passage being worked on are drawn again from them, unless he has typed in them
   since: then they keep what he typed, and the row keeps the version he read, so his save meets the
   card saying the passage has changed, as one over a change from another window does. An
   interviewer note open on a row keeps what is in its field the same way. */
function findApply(data) {
  const rows = [];
  let redraw = false;
  for (const r of (data && data.rows) || []) {
    const row = rowByKey(`${r.sheet}:${r.row}`);
    if (!row) continue;
    row.text = r.text;
    row.runs = r.runs;
    const here = current() && current().i === row.i;
    if (here) clearPending(false);
    if (r.v !== undefined && !(here && S.dirty)) {
      for (const k of ['es', 'en', 'kq', 'pairs', 'unpaired', 'v']) if (r[k] !== undefined) row[k] = r[k];
      if (here) redraw = true;
    }
    if (r.note !== undefined && !(S.note && S.note.key === row.key)) {
      row.note = r.note;
      drawNoteMark(row);
    }
    repaintRow(row);
    rows.push({ row, dropped: r.dropped || [] });
  }
  if (redraw) findFieldsAgain(current());
  return rows;
}

/* The fields of the passage being worked on drawn again from its row, as a move onto it draws them,
   with the caret left where it was, in the find card as a rule, and the column where it is. */
function findFieldsAgain(row) {
  if (!row) return;
  const caret = document.activeElement;
  S.pairFocus = null;
  S.kqHover = null;
  S.kqFocus = null;
  S.kqLit = null;
  // named before the pairs are drawn, as drawTurn names it, so the count drawn with them is right
  S.pairsRow = row.key;
  drawPairs(rowPairs(row));
  S.kqDrawn = kqSignature();
  $('en').value = row.en || '';
  S.dirty = false;
  growNotes();
  drawAct();
  drawToPair();
  repaintRow(row);
  if (caret && caret !== document.body && caret.isConnected) caret.focus({ preventScroll: true });
}

/* each highlight dropped, with the sheet and the timecode before it */
const droppedLine = (rows) => rows
  .flatMap(({ row, dropped }) => dropped.map((p) => t('distil.find.dropped', { sheet: row.sheet, time: row.time, quote: p })))
  .join(' · ');

/* "17 replaced, 14 on Initial and 3 on 2d." for a case of several sheets */
function replacedWords(data) {
  const n = data.replaced || 0;
  const per = sheetNames().filter((s) => (data.counts || {})[s]).map((s) => t('distil.find.on_sheet', { n: data.counts[s], sheet: s }));
  const where = per.length > 1 ? tList(per) : '';
  return { n, where };
}

/* Replace the occurrence in focus, or all of them. The server counts again and refuses a place
   that has moved, so what is written is what the washes showed. */
async function findReplace(all) {
  if (FIND.busy || !S.data) return;
  const { find, word, matchCase } = findOptions();
  const replace = $('find-with').value;
  if (!find) { $('find-text').focus(); return; }
  if (replace === find) { say(t('distil.find.same')); return; }
  if (S.editing) { say(t('distil.find.editing')); return; }
  const hit = all ? null : FIND.hits[FIND.at];
  if (!all && (!hit || hit.sheet !== S.sheetDrawn)) return;
  if (all && !FIND.hits.length && !FIND.more) return;
  const body = { path: S.data.path, find, replace, word, case: matchCase };
  if (hit) {
    const row = S.flat[hit.i];
    Object.assign(body, { sheet: row.sheet, row: row.row, ordinal: hit.ord, text: row.text });
  }
  FIND.busy = true;
  drawFindCount();
  let data;
  try {
    data = await api('/api/replace', body);
  } catch (err) {
    FIND.busy = false;
    drawFindCount();
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return;
  }
  FIND.busy = false;
  const rows = findApply(data);
  if (!rows.length || !data.batch) {
    findRefresh();
    say(t('distil.find.nothing'), 2200);
    return;
  }
  // the entry's turn is the first row changed on the sheet on screen, or the first changed at all
  const first = rows.find((r) => r.row.sheet === S.sheetDrawn) || rows[0];
  undoPush({
    key: first.row.key, what: 'the replace', batch: data.batch,
    undo: (e) => replaceBack(e, false),
    redo: (e) => replaceBack(e, true),
  });
  // the focus goes on past the words just put in, and never round to the top
  findRefresh(hit ? { i: hit.i, start: hit.start + replace.length } : 'near');
  findScroll();
  const { n, where } = replacedWords(data);
  const lost = droppedLine(rows);
  const keys = keyName(t('distil.keys.undo'));
  const said = !all ? t('distil.find.replaced_one') : where ? t('distil.find.replaced_where', { n, where, keys })
    : t('distil.find.replaced', { n, keys });
  say(lost ? `${said} ${lost}` : said, lost ? 12000 : (all ? 6000 : 2200));
}

/* Undo puts every row the replace changed back as it was, a highlight it dropped included, and
   redo applies it again from the same records. Either is refused whole when a row reads otherwise
   now. */
async function replaceBack(entry, redo) {
  let data;
  try {
    data = await api('/api/replace-undo', { path: S.data.path, batch: entry.batch, redo });
  } catch (err) {
    throw new Error(needsRestart(err) ? RESTART_LINE : err.message);
  }
  const rows = findApply(data);
  findRefresh();
  const { n, where } = replacedWords(data);
  const lost = droppedLine(rows);
  const said = redo ? (where ? t('distil.find.again_where', { n, where }) : t('distil.find.again', { n }))
    : (where ? t('distil.find.back_where', { n, where }) : t('distil.find.back', { n }));
  say(lost ? `${said} ${lost}` : said, lost ? 12000 : 3600);
}

/* ──────────────────────────────────────────────── interviewer notes ── */

/* Her turns take the statements, the quotes and the notes. His own turns take one thing, a note on
   the intervention: it moved her on, it was a poor one, the next question belonged here. A plain
   click on one of his turns cues the recording and marks the row as it always did, and puts one
   field, Interviewer note, in the notes column beside it (17 October, where until then it stood in
   the panel in place of the three fields). The current passage keeps its card and its notes, and the
   turn being worked on does not change. Cmd + Enter, Next, a click away and any move keep the note,
   and Esc leaves it as it was. The note goes to the workbook's Interviewer notes column through a
   route of its own and nowhere else: it is never a stop, never counted, never nudged and never in
   anything sent to a model. */

const NOTE_PROMPTS = [
  t('distil.note.prompt_1'),
  t('distil.note.prompt_2'),
  t('distil.note.prompt_3'),
  t('distil.note.prompt_4'),
];
const notePrompt = () => NOTE_PROMPTS[Math.floor(Math.random() * NOTE_PROMPTS.length)];
// a note as the workbook keeps it: its lines trimmed, the empty ones dropped
const noteLines = (text) => String(text || '').split('\n').map((l) => l.trim()).filter(Boolean).join('\n');

/* One of the interviewer's own turns, named as Settings names him. A server from before this sends
   no `note` on any row, and then a click on his turn cues the recording and does nothing more. */
function noteable(row) {
  if (!S.data || !row || row.stop || row.note === undefined || !row.name) return false;
  return row.name.trim().toLowerCase() === (S.data.config.interviewer || 'Adam').trim().toLowerCase();
}

// the mark in the margin of a row carrying a note, a pen in the app's one stroke style
const NOTE_PEN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M16.4 4.4l3.2 3.2L8.8 18.4l-4.3 1.1 1.1-4.3L16.4 4.4Z"/><path d="M14.2 6.6l3.2 3.2"/></svg>';

function noteMarkHtml(row) {
  return noteLines(row.note) ? `<span class="note-mark" title="${escAttr(t('distil.note.mark'))}">${NOTE_PEN}</span>` : '';
}

function drawNoteMark(row) {
  const line = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"] .gutter-time`);
  if (!line) return;
  const had = line.querySelector('.note-mark');
  if (had) had.remove();
  line.insertAdjacentHTML('beforeend', noteMarkHtml(row));
}

/* `shown` is what the field opens with when an undo or a redo opens it. Otherwise it opens with
   the note the workbook holds, or with words the workbook refused, kept for the next open. The field
   stands in the notes column beside his passage (17 October), where until then it stood in the panel
   in place of the three fields, and the current passage keeps its card. */
function openNote(row, shown) {
  if (!noteable(row)) return;
  if (S.note && S.note.key !== row.key) keepNote();
  if (S.note && shown === undefined) { $('note').focus({ preventScroll: true }); return; }
  if (S.editing) closeEditor();
  if (!S.note) {
    S.note = { key: row.key };
    $('note').placeholder = notePrompt();
    $('note-entry').hidden = false;
  }
  const el = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"]`);
  if (el) {
    el.classList.add('noting');
    let cell = el.querySelector('.turn-notes');
    if (!cell) {
      cell = document.createElement('div');
      cell.className = 'turn-notes note-cell';
      el.appendChild(cell);
    }
    cell.replaceChildren($('note-entry'));
  }
  $('note-time').textContent = row.time;
  const draft = row.noteDraft;
  delete row.noteDraft;
  $('note').value = shown !== undefined ? shown : draft !== undefined ? draft : row.note || '';
  grow($('note'));
  drawAct();
  $('note').focus({ preventScroll: true });
  // his passage and the field beside it brought whole into the column where they run past its head or its foot
  if (el) bringIntoColumn(el);
}

/* An element of the columns scrolled the least way into the column's view, clear of its faded head and foot. */
function bringIntoColumn(el) {
  const col = $('transcript');
  const c = col.getBoundingClientRect();
  const b = el.getBoundingClientRect();
  const head = c.top + SPEAKER_CLEAR + 8;
  const foot = c.bottom - 40;
  if (b.top < head) col.scrollTop -= head - b.top;
  else if (b.bottom > foot) col.scrollTop += Math.min(b.bottom - foot, b.top - head);
}

/* the note's field back where it waits, and the cell made for it beside his passage gone */
function parkNote() {
  const entry = $('note-entry');
  if (entry.parentElement === $('es-park')) return;
  const cell = entry.closest('.note-cell');
  $('es-park').appendChild(entry);
  if (cell) cell.remove();
}

/* The note's field goes, and the card's button is the one it had. */
function closeNote() {
  if (!S.note) return;
  S.note = null;
  $('transcript-rows').querySelectorAll('.turn.noting').forEach((el) => el.classList.remove('noting'));
  $('note-entry').hidden = true;
  parkNote();
  drawAct();
}

/* Esc: back to the three fields with nothing written, and nothing kept for the next open. */
function discardNote() {
  const open = S.note;
  if (!open) return;
  const row = rowByKey(open.key);
  if (row) delete row.noteDraft;
  closeNote();
  focusEntry();
}

const noteUnkept = () => {
  const row = S.note ? rowByKey(S.note.key) : null;
  return !!row && noteLines($('note').value) !== noteLines(row.note);
};

/* Cmd + Enter and Next (`stay`) wait for the workbook and leave the field open when it refuses. A
   click away and any move close the field at once and write behind it, and words the workbook
   refuses come back in the field the next time that turn is clicked. A note that has not changed
   writes nothing. The answer is whether the note is kept. */
async function keepNote(stay = false) {
  const open = S.note;
  if (!open) return true;
  const row = rowByKey(open.key);
  const text = $('note').value;
  const was = row ? row.note || '' : '';
  const same = !row || noteLines(text) === noteLines(was);
  if (same || !stay) {
    closeNote();
    if (stay) focusEntry();
  }
  if (same) return true;
  row.noteDraft = text;
  const path = S.data.path;
  let data;
  try {
    data = await noteApply(row.key, text);
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return false;
  }
  // a case opened while the note travelled has a stack of its own, and this entry is not in it
  if (data.changed && S.data && S.data.path === path) pushNoteUndo(row, was, row.note);
  if (stay && S.note === open) { closeNote(); focusEntry(); }
  return true;
}

async function noteApply(key, text) {
  const row = rowByKey(key);
  if (!row) throw new Error(t('distil.undo.passage_gone'));
  const data = await api('/api/interviewer-note', { path: S.data.path, sheet: row.sheet, row: row.row, text });
  row.note = data.text;
  delete row.noteDraft;
  // the mark is drawn only while the column still holds this row, not one a reload put in its place
  if (S.flat[row.i] === row) drawNoteMark(row);
  return data;
}

/* One entry for a note kept, the old text and the new, so undo and redo go back through the same
   route. Either opens the field on that turn again, on its own sheet and in sight, holding what the
   workbook now holds. */
function pushNoteUndo(row, was, now) {
  undoPush({
    key: row.key,
    what: 'the interviewer note',
    was,
    now,
    undo: (e) => noteBack(e.key, e.was),
    redo: (e) => noteBack(e.key, e.now),
  });
}

/* An undo or a redo with a note open keeps it first, so its words are on the stack before anything
   is reversed. One the workbook refuses stays open, and nothing is undone. */
async function keepBeforeUndo() {
  S.undoBusy = true;
  try { return await keepNote(true); } finally { S.undoBusy = false; }
}

async function noteBack(key, text) {
  let row = rowByKey(key);
  if (!row) throw new Error(t('distil.undo.passage_gone'));
  if (row.sheet !== S.sheetDrawn) await goTo(stopNear(row.sheet, row.row, S.at));
  await noteApply(key, text);
  row = rowByKey(key);
  openNote(row, row.note || '');
  // the field took no keystroke, so the next Cmd + Z or Cmd + Shift + Z is the app's again
  S.lastInput.note = 0;
  const el = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"]`);
  if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
}

/* Include interviewer notes, under Markdown and CSV in the PETs board's Export menu (Settings' Export pane's until
   settingsplit), off until ticked and remembered in this browser. */
const EXPORT_NOTES_KEY = 'idiograph-export-notes';

function exportNotesStored() {
  try { return localStorage.getItem(EXPORT_NOTES_KEY) === '1'; } catch { return false; }
}

function exportNotesSave(on) {
  try { localStorage.setItem(EXPORT_NOTES_KEY, on ? '1' : '0'); } catch { /* private window */ }
}

/* ─────────────────────────────────────────────────────────── undo ── */

/* The app's own actions, newest last: a quote taken with `q`, the pair it added with it, a pair
   taken away, a correction, an assignment, a trim, a replace and an interviewer note kept. Every
   entry knows the turn it belongs to, so undoing
   one that is not the turn on screen goes there first and then reverses it. Typing in the three
   fields is not in here: the browser keeps its own undo for that, and the two are told apart by
   which of them happened last. The stack is in memory for the open workbook. */

const UNDO_DEPTH = 60;

/* Where the press that began a click landed, and which field held the caret when it did. A click
   that travelled is a drag, and a drag in the column is a selection, never a move. */
let pressAt = null;
let pressFocus = null;

const pressMoved = (e) => !!pressAt
  && (Math.abs(e.clientX - pressAt.x) > 4 || Math.abs(e.clientY - pressAt.y) > 4);

function selectionLive() {
  const sel = window.getSelection();
  return !!(sel && sel.rangeCount && !sel.isCollapsed
    && $('transcript').contains(sel.getRangeAt(0).commonAncestorContainer));
}

const rowByKey = (key) => S.flat.find((r) => r.key === key);

/* Past UNDO_DEPTH the oldest entry goes. From 14 October a quote `q` replaced on the turn in
   front of him was held past it, and since 16 October `q` replaces none, so nothing is held. */
function undoPush(entry) {
  entry.at = Date.now();
  S.undoStack.push(entry);
  if (S.undoStack.length > UNDO_DEPTH) S.undoStack.shift();
  S.redoStack.length = 0;
}

function undoClear() { S.undoStack.length = 0; S.redoStack.length = 0; }

/* Whose undo this keystroke is. A field he is typing in keeps its own while its last keystroke is
   more recent than anything the app has on the stack. */
function nativeUndoOwns(backwards) {
  const el = document.activeElement;
  if (!el) return false;
  // a turn open for correction and the timecode box keep the browser's own undo outright: they
  // are text boxes the app's stack knows nothing about until they are saved. The interviewer note
  // is told apart the way the three fields are, so a redo after an undo that opened it is the app's,
  // and so are the find and replace card's fields and ticks, so a replace just made undoes from there
  if (!isEntryField(el) && el.id !== 'note' && !FIND_FIELDS.includes(el.id)) return /TEXTAREA|INPUT/.test(el.tagName);
  const stack = backwards ? S.undoStack : S.redoStack;
  const top = stack[stack.length - 1];
  if (!top) return true;
  return (S.lastInput[el.id] || 0) > top.at;
}

async function undoStep(backwards) {
  if (S.undoBusy || !S.data || $('work').hidden) return;
  // a note not yet kept is kept first (see keepBeforeUndo)
  if (S.note && !(await keepBeforeUndo())) return;
  const stack = backwards ? S.undoStack : S.redoStack;
  if (!stack.length) {
    say(backwards ? t('distil.undo.none') : t('distil.undo.no_redo'), 2000);
    return;
  }
  const entry = stack[stack.length - 1];
  // an assignment renumbers rows, so it carries its own block and reloads onto its own turn
  const row = entry.anywhere ? null : rowByKey(entry.key);
  if (!entry.anywhere && !row) { stack.pop(); say(t('distil.undo.passage_gone')); return; }
  S.undoBusy = true;
  try {
    // an edit can belong to one of Adam's turns, which is not a stop and has nowhere to go to
    if (row && row.stop && (!current() || current().key !== entry.key)) await goTo(row.pos);
    await (backwards ? entry.undo(entry) : entry.redo(entry));
    stack.pop();
    (backwards ? S.redoStack : S.undoStack).push(entry);
  } catch (err) {
    say(err.message, 9000);
  } finally {
    S.undoBusy = false;
  }
}

/* ─────────────────────────────────────────── assigning words to a speaker ── */

/* A turn sometimes carries words another speaker said. Select them and press `c`, or right-click
   them and choose from the row's menu, and they become a turn of that speaker's, the rows either
   side keeping the speaker they had. With nothing selected the whole turn goes, after a card that
   says what it will merge.

   The speakers of a sheet are its distinct names, in the order they first appear, however many
   there are. On a sheet of two, `c` assigns to the other one at once. On a sheet of more, it opens
   the row's menu with the assignments alone, and a name the sheet has never had is typed in. */

function sheetSpeakers(sheet) {
  const seen = new Set();
  const out = [];
  for (const r of S.flat) {
    if (r.sheet !== sheet) continue;
    const name = (r.name || '').trim();
    if (name && !seen.has(name.toLowerCase())) { seen.add(name.toLowerCase()); out.push(name); }
  }
  return out;
}

const othersFor = (row) => sheetSpeakers(row.sheet)
  .filter((n) => n.toLowerCase() !== (row.name || '').trim().toLowerCase());

/* Widened to whole words, never half of one, with the spaces at the edges left outside. The
   server widens it the same way, so the two always agree on which words go. */
function snapWords(text, start, end) {
  let a = Math.max(0, Math.min(start, text.length));
  let b = Math.max(a, Math.min(end, text.length));
  while (a < b && /\s/.test(text[a])) a += 1;
  while (b > a && /\s/.test(text[b - 1])) b -= 1;
  if (a >= b) return null;
  while (a > 0 && !/\s/.test(text[a - 1])) a -= 1;
  while (b < text.length && !/\s/.test(text[b])) b += 1;
  return { start: a, end: b };
}

/* A drag's selection in the passages taken out to whole words as he drags, as a word processor's drag
   takes them, so the highlight he sees is the words he gets, for a quote, an assignment and anything
   else that reads the selection (18 October, the sweep's "t is the same walk. Ou", and Adam's ruling of 19
   October: a word cut off at its start or end is a mistake the app helps him avoid). Each end is widened
   inside its own passage by `snapWords` out to the spaces, so punctuation touching a word goes with it,
   an ellipsis, a comma, a full stop, quote marks or brackets, and the spaces at the edges stay outside.
   The selection keeps its direction, so a drag back up the passage goes on from where it began. */
function snapDrag() {
  const hits = selectionTurns();
  if (!hits || !hits.length) return;
  const first = hits[0];
  const last = hits[hits.length - 1];
  const a = snapWords(first.box.textContent, first.start, first.end);
  const b = hits.length === 1 ? a : snapWords(last.box.textContent, last.start, last.end);
  if (!a || !b) return;
  if (a.start === first.start && b.end === last.end) return;
  const from = boxPoint(first.box, a.start, false);
  const to = boxPoint(last.box, b.end, true);
  if (!from || !to) return;
  try {
    const sel = window.getSelection();
    const range = sel.getRangeAt(0);
    // a selection made upwards has its focus at its start
    const back = sel.focusNode === range.startContainer && sel.focusOffset === range.startOffset
      && !(sel.anchorNode === range.startContainer && sel.anchorOffset === range.startOffset);
    if (back) sel.setBaseAndExtent(to.node, to.offset, from.node, from.offset);
    else sel.setBaseAndExtent(from.node, from.offset, to.node, to.offset);
  } catch { /* the selection stands as the drag left it */ }
}

/* The text node and the offset in it of a place in a passage's words, a start taken at the head of the
   node after a boundary and an end at the foot of the node before it */
function boxPoint(box, offset, end) {
  const walk = document.createTreeWalker(box, NodeFilter.SHOW_TEXT);
  let pos = 0;
  let lastNode = null;
  for (let node = walk.nextNode(); node; node = walk.nextNode()) {
    const len = node.nodeValue.length;
    if (end ? offset <= pos + len : offset < pos + len) return { node, offset: offset - pos };
    pos += len;
    lastNode = node;
  }
  return lastNode ? { node: lastNode, offset: lastNode.nodeValue.length } : null;
}

/* The live selection as the turns it covers, in any turn on the sheet, his as well as hers: null
   with nothing selected in the column, otherwise one entry for every turn it has words in. The
   margin counts for nothing, so a drag that runs on into the next turn's name is still one turn. */
function selectionTurns() {
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount || sel.isCollapsed) return null;
  const range = sel.getRangeAt(0);
  const rows = $('transcript-rows');
  if (!rows.contains(range.commonAncestorContainer)) return null;
  const hits = [];
  for (const box of rows.querySelectorAll('.turn-text')) {
    if (box.hidden || !range.intersectsNode(box)) continue;
    const whole = document.createRange();
    whole.selectNodeContents(box);
    const part = range.cloneRange();
    if (part.compareBoundaryPoints(Range.START_TO_START, whole) < 0) part.setStart(whole.startContainer, whole.startOffset);
    if (part.compareBoundaryPoints(Range.END_TO_END, whole) > 0) part.setEnd(whole.endContainer, whole.endOffset);
    const text = part.toString();
    if (!text.trim()) continue;
    const lead = whole.cloneRange();
    lead.setEnd(part.startContainer, part.startOffset);
    const start = lead.toString().length;
    hits.push({ box, start, end: start + text.length });
  }
  return hits;
}

/* What `c` and the menu act on: the words selected inside one turn, widened to whole words, or a
   line saying why not. `whole` is a selection over every word of its turn, which is the turn. */
function assignSelection() {
  const hits = selectionTurns();
  if (hits === null) return null;
  if (!hits.length) return { refuse: t('distil.assign.no_words') };
  if (hits.length > 1) return { refuse: t('distil.assign.two_passages') };
  const hit = hits[0];
  const row = S.flat[Number(hit.box.closest('.turn').dataset.i)];
  if (!row) return null;
  const text = row.runs.map((r) => r.text).join('');
  const span = snapWords(text, hit.start, hit.end);
  if (!span) return { refuse: t('distil.assign.no_words') };
  return { row, start: span.start, end: span.end,
    whole: !text.slice(0, span.start).trim() && !text.slice(span.end).trim() };
}

function selectionAnchor() {
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount) return null;
  const box = sel.getRangeAt(0).getBoundingClientRect();
  return box && (box.width || box.height) ? { x: box.left, y: box.bottom } : null;
}

function closeRowMenu() {
  const open = S.rowMenu;
  if (!open) return;
  S.rowMenu = null;
  const hadFocus = open.el.contains(document.activeElement);
  open.el.remove();
  if (hadFocus && !$('work').hidden) focusEntry();
}

/* The rows and the timecodes a cut takes, in the small type under its entry and on the card. */
function spanNote(span) {
  return t('distil.trim.span_note', { n: span.count, from: span.from, to: span.to });
}

/* The row's menu. One menu for the whole row, opened by a right-click anywhere on it, the margin or
   the text, and by the small control in the margin, in groups with a thin rule between them. First
   the assignments, one entry for every speaker of the sheet but the turn's own: "Assign to <name>" for the words selected in this turn, "Assign this turn to <name>"
   always, and a last one that asks for a name. The words are never quoted, because a selection can
   be a long passage. Then Edit text and Edit timecode, then the two cuts, "Cut this turn and 3
   before", each with the rows and the timecodes it takes under it. `c` opens the same menu with
   the assignments alone. */
function rowMenuGroups(row, pick, only) {
  // in a thematic analysis project, words selected bring the quick keys' acts first, each with its key (codes.js)
  const groups = !only && pick && typeof cxQuickMenu === 'function' ? cxQuickMenu(pick) : [];
  const others = othersFor(row);
  const assign = [];
  if (pick) for (const name of others) assign.push({ label: t('distil.assign.words_to', { name }), to: name, words: true });
  for (const name of others) assign.push({ label: t('distil.assign.passage_to', { name }), to: name, words: false });
  assign.push(pick
    ? { label: t('distil.assign.words_to_else'), ask: true, words: true }
    : { label: t('distil.assign.passage_to_else'), ask: true, words: false });
  groups.push(assign);
  if (only === 'assign') return groups;
  groups.push([{ label: t('distil.assign.edit_text'), act: 'edit' }, { label: t('distil.assign.edit_time'), act: 'time' }]);
  groups.push(['before', 'after'].map((direction) => ({
    label: trimShort(trimSpan(row, direction)), note: spanNote(trimSpan(row, direction)),
    act: 'cut', direction,
  })));
  return groups;
}

/* Built in the menus' paper, at the pointer, kept inside the row's width and
   turned upwards when the column has no room for it below. The arrows move through it and Esc puts
   it away, and so does a click anywhere else. */
function openRowMenu(row, opts = {}) {
  // an interviewer note is kept before anything in the menu can move the rows under it
  if (S.note) keepNote();
  closeRowMenu();
  closeTimeEdit();
  selBarHide();
  const holder = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"]`);
  if (!holder) return;
  const pick = opts.pick && !opts.pick.refuse && opts.pick.row.i === row.i ? opts.pick : null;
  const items = [];
  const pop = document.createElement('div');
  pop.className = 'row-menu';
  pop.setAttribute('role', 'menu');
  pop.innerHTML = rowMenuGroups(row, pick, opts.only).map((group) => group.map((item) => {
    if (item.head) return `<div class="row-menu-head" role="presentation">${esc(item.head)}</div>`;
    items.push(item);
    const note = item.note ? `<span class="row-menu-note">${esc(item.note)}</span>` : '';
    // a key in a column at the right, as a window's menus show theirs (quickkeysB)
    const key = item.key ? `<span class="row-menu-key" aria-hidden="true">${esc(item.key)}</span>` : '';
    return `<button type="button" class="ghost small${note ? ' with-note' : ''}${key ? ' with-key' : ''}" role="menuitem" data-item="${items.length - 1}"`
      + `${item.key ? ` aria-keyshortcuts="${escAttr(item.key)}"` : ''}><span>${esc(item.label)}</span>${note}${key}</button>`;
  }).join('')).join('<div class="row-menu-rule" role="separator"></div>');
  holder.appendChild(pop);
  const frame = holder.getBoundingClientRect();
  const col = $('transcript').getBoundingClientRect();
  const at = opts.at || { x: frame.left + 108, y: frame.top + 30 };
  const tall = pop.offsetHeight;
  const up = at.y + 6 + tall > col.bottom && at.y - 6 - tall >= col.top;
  // too tall for the room either side of the pointer, as with a thematic analysis project's quick keys over it
  // (quickkeysB), it stands as high as its foot needs to clear the column's, never above the column
  const neither = at.y + 6 + tall > col.bottom && !up;
  pop.style.left = `${Math.max(0, Math.min(at.x - frame.left, holder.clientWidth - pop.offsetWidth - 4))}px`;
  pop.style.top = `${neither ? Math.max(col.top, col.bottom - 4 - tall) - frame.top
    : up ? at.y - frame.top - 6 - tall : Math.max(0, at.y - frame.top + 6)}px`;
  S.rowMenu = { el: pop, row, pick };
  pop.addEventListener('click', (e) => {
    const chosen = e.target.closest('[data-item]');
    if (!chosen) return;
    e.stopPropagation();
    chooseFromMenu(items[Number(chosen.dataset.item)]);
  });
  pop.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    const buttons = [...pop.querySelectorAll('button')];
    if (!buttons.length) return;
    e.preventDefault();
    const k = buttons.indexOf(document.activeElement);
    buttons[(k + (e.key === 'ArrowDown' ? 1 : buttons.length - 1) + buttons.length) % buttons.length].focus();
  });
  const first = pop.querySelector('button');
  if (first) first.focus({ preventScroll: true });
}

function chooseFromMenu(item) {
  const open = S.rowMenu;
  if (!open || !item) return;
  if (item.ask) { askAssignName(item); return; }
  if (item.quick && open.pick) {
    // the menu goes without taking the caret back to a field, and the words it was opened on are coded
    S.rowMenu = null;
    open.el.remove();
    cxQuickChosen(item, open.pick);
    return;
  }
  closeRowMenu();
  if (item.act === 'edit') openEditor(open.row);
  else if (item.act === 'time') openTimeEdit(open.row);
  else if (item.act === 'cut') confirmTrim(open.row, item.direction);
  else if (item.words && open.pick) assignWords(open.pick, item.to);
  else confirmAssignTurn(open.row, item.to);
}

/* Somebody the sheet has not had yet: a small box for the name, in the menu's place, and a name
   like any other once it is in. A name already on the sheet is taken as it is spelled there. */
function askAssignName(item) {
  const open = S.rowMenu;
  open.el.innerHTML = `<label class="assign-ask"><span class="field-label">${esc(item.words ? t('distil.assign.ask_words') : t('distil.assign.ask_passage'))}</span>
      <input type="text" class="assign-name" spellcheck="false" autocomplete="off" placeholder="${escAttr(t('distil.assign.ask_placeholder'))}"></label>
    <span class="mono assign-hint">${esc(t('distil.assign.ask_hint'))}</span>`;
  const field = open.el.querySelector('.assign-name');
  field.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    e.stopPropagation();
    const name = field.value.trim();
    if (!name) { say(t('distil.assign.ask_empty')); return; }
    if (name.toLowerCase() === (open.row.name || '').trim().toLowerCase()) {
      say(t('distil.assign.already', { name: open.row.name }));
      return;
    }
    const known = sheetSpeakers(open.row.sheet).find((n) => n.toLowerCase() === name.toLowerCase());
    chooseFromMenu({ ...item, ask: false, to: known || name });
  });
  field.focus();
}

/* `c`: outside the fields and outside the turn editor, like `h` and `q`. */
function assignKey() {
  if (!S.data || S.editing || S.assignBusy) return;
  selBarHide();
  const pick = assignSelection();
  if (pick && pick.refuse) { say(pick.refuse); return; }
  const row = pick ? pick.row : current();
  if (!row) return;
  const others = othersFor(row);
  // two speakers on the sheet, so the other one is the only place the words can go
  if (sheetSpeakers(row.sheet).length === 2 && others.length === 1) {
    if (pick) assignWords(pick, others[0]);
    else confirmAssignTurn(row, others[0]);
    return;
  }
  openRowMenu(row, { pick, at: pick ? selectionAnchor() : null, only: 'assign' });
}

/* A selection goes straight through, because it is precise and undoable. One over every word of
   the turn is the whole turn, and that goes through the card. */
function assignWords(pick, to) {
  if (pick.whole) { confirmAssignTurn(pick.row, to); return; }
  runAssign({ sheet: pick.row.sheet, row: pick.row.row, to, start: pick.start, end: pick.end });
}

/* The whole turn shows the card first, in the style of the trim confirm: one line naming exactly
   what will merge, which may be nothing, and what the rows carry across. Enter goes, Esc cancels. */
async function confirmAssignTurn(row, to) {
  let plan;
  try {
    plan = await api('/api/rows', { op: 'preview', path: S.data.path, sheet: row.sheet, row: row.row, to });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
  const name = plan.to || to;
  S.assignPlan = { sheet: row.sheet, row: row.row, to: name };
  $('assign-title').textContent = t('distil.assign.passage_to', { name });
  $('assign-line').textContent = plan.line || '';
  $('assign-carries').textContent = plan.carries || '';
  $('assign-carries').hidden = !plan.carries;
  show('assign');
  $('assign-go').focus();
}

function runAssignTurn() {
  const plan = S.assignPlan;
  S.assignPlan = null;
  hide('assign');
  if (plan) runAssign(plan);
}

/* The line a row change answers with, and after it the server's one line when the themes file
   could not be read and so did not move with the rows. A server from before this sends none. */
const withThemes = (line, data) => (data && data.themes ? `${line} ${data.themes}` : line);

function assignedLine(data) {
  if (!data.whole) {
    return data.merged ? t('distil.assign.words_joined', { name: data.to }) : t('distil.assign.words_own', { name: data.to });
  }
  if (!data.merged) return t('distil.assign.passage_now', { name: data.to });
  return data.merged > 1 ? t('distil.assign.passage_either', { name: data.to }) : t('distil.assign.passage_beside', { name: data.to });
}

/* Reopen the case where it stands, the rows renumbered, on the turn the server says he is on. */
async function reloadInPlace(land) {
  startCase(await api('/api/open', { path: S.data.path }), { land });
}

/* One call does the whole of it, and the answer carries the block it touched, which is what undo
   hands back. A field typed into and not yet saved is saved first, because the reload redraws the
   fields: a server that has not been restarted is asked first, so a 404 leaves everything alone. */
async function assignApply(req) {
  const body = { path: S.data.path, sheet: req.sheet, row: req.row, to: req.to, start: req.start, end: req.end };
  if (S.dirty) {
    await api('/api/rows', { ...body, op: 'preview' });
    await commit(current(), false);
    if (S.dirty) throw new Error(t('distil.assign.not_saved'));
  }
  const here = current();
  const data = await api('/api/rows', {
    ...body, op: 'assign', current: here ? { sheet: here.sheet, row: here.row } : null,
  });
  await reloadInPlace(data.land);
  return data;
}

async function runAssign(req) {
  if (S.assignBusy) return;
  S.assignBusy = true;
  try {
    const data = await assignApply(req);
    // redo re-applies from the offsets as the server snapped them
    const again = { ...req, start: data.start === null ? undefined : data.start, end: data.end === null ? undefined : data.end };
    undoPush({
      anywhere: true, key: `${req.sheet}:${req.row}`, what: 'the assignment', req: again, result: data,
      undo: (e) => assignRestore(e),
      redo: (e) => assignRedo(e),
    });
    say(withThemes(assignedLine(data), data), data.themes ? 9000 : 3600);
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  } finally {
    S.assignBusy = false;
  }
}

/* Undo puts the rows back from the backup the assignment made, and whatever was written into
   those rows since goes onto the turn it was made on. */
async function assignRestore(entry) {
  if (S.dirty) await commit(current(), false);
  const b = entry.result.block;
  const here = current();
  const data = await api('/api/rows', {
    op: 'restore', path: S.data.path, id: entry.result.id,
    sheet: b.sheet, first: b.first, before: b.before, after: b.after, backup: b.backup,
    current: here ? { sheet: here.sheet, row: here.row } : null,
  });
  await reloadInPlace(data.land);
  say(withThemes(data.appended
    ? t('distil.assign.restored_lines', { n: data.appended })
    : t('distil.assign.restored'), data), data.themes ? 9000 : 3600);
}

async function assignRedo(entry) {
  entry.result = await assignApply(entry.req);
  say(withThemes(assignedLine(entry.result), entry.result), entry.result.themes ? 9000 : 3600);
}

/* ──────────────────────────────────────────────────────────── trim ── */

/* Every recording opens with consent talk and closes with scheduling. Those turns are transcribed
   and are not data. Cutting takes whole rows at one end, so the sheet stays in sequence, and the
   workbook is archived before a single row goes. */

/* `t` opens the trim card on the turn being worked on with both ends offered, the nearer end of
   the sheet first, so the consent talk at the top and the goodbyes at the bottom are each one key
   and one Enter away. */
function trimKey() {
  const row = current();
  if (!row || S.editing || anyOverlayOpen()) return;
  const onSheet = S.flat.filter((r) => r.sheet === row.sheet);
  const at = onSheet.findIndex((r) => r.i === row.i);
  confirmTrim(row, at < onSheet.length / 2 ? 'before' : 'after', true);
}

function trimSpan(row, direction) {
  const rows = S.flat.filter((r) => r.sheet === row.sheet
    && (direction === 'before' ? r.row <= row.row : r.row >= row.row));
  const marked = rows.filter((r) => (r.es || '').trim() || (r.en || '').trim() || (r.kq || '').trim()
    || (r.runs || []).some((x) => x.crux));
  return {
    direction,
    count: rows.length,
    marked: marked.length,
    from: rows.length ? rows[0].time : '',
    to: rows.length ? rows[rows.length - 1].time : '',
  };
}

/* What a cut takes, said plainly. The turn he is on is always one of the rows cut, which is what
   surprised him in "Cut this and everything before", so the card says "Cut 4 rows: this turn and
   the 3 before it, 00:00 to 01:35.", and the menu entries and the `t` buttons say the same shape
   in short, "Cut this turn and 3 before". One other row is "the one before it", and a cut of the
   turn alone is "this turn only". */
function trimLine(span) {
  const others = span.count - 1;
  const which = others < 1 ? t('distil.trim.which_only')
    : span.direction === 'before' ? t('distil.trim.which_before', { n: others }) : t('distil.trim.which_after', { n: others });
  const when = span.count === 1 || !span.to ? span.from : t('distil.trim.when', { from: span.from, to: span.to });
  return when ? t('distil.trim.line_when', { n: span.count, which, when }) : t('distil.trim.line', { n: span.count, which });
}

function trimShort(span) {
  const others = span.count - 1;
  return others < 1 ? t('distil.trim.short_only')
    : span.direction === 'before' ? t('distil.trim.short_before', { n: others }) : t('distil.trim.short_after', { n: others });
}

/* A cut in the row's menu goes straight to one card, Trim the transcript, which carries what
   decides and nothing else: the line naming the cut, with the rows and the timecodes it takes, a
   line when any of those rows carries a statement, a note, a quote or a workbook highlight, and that the
   workbook is copied to `_Archive` first. Enter cuts, Esc cancels. */
/* From the menu the direction is known and the card carries one cut. From the `t` key it carries
   both: the cut toward the nearer end of the sheet on the filled button, ready on Enter, and the
   other end on a second button, which redraws the card for that direction and asks once more. */
function confirmTrim(row, direction, both = false) {
  if (!row) return;
  const span = trimSpan(row, direction);
  S.trimRow = row;
  S.trimDirection = direction;
  const other = direction === 'before' ? 'after' : 'before';
  const otherSpan = both ? trimSpan(row, other) : null;
  $('trim-go').textContent = both ? trimShort(span) : t('distil.trim.go');
  $('trim-other').hidden = !(both && otherSpan && otherSpan.count > 0);
  if (!$('trim-other').hidden) {
    $('trim-other').textContent = trimShort(otherSpan);
    $('trim-other').onclick = () => confirmTrim(row, other);
  }
  $('trim-line').textContent = trimLine(span);
  $('trim-warn').hidden = span.marked === 0;
  // a workbook highlight, an orange run the workbook holds, which the app has drawn and made none of since 16
  // October, named as the find names it (17 October, later, where the card said "a highlight")
  $('trim-warn').textContent = span.marked === 1 ? t('distil.trim.warn_one') : t('distil.trim.warn', { n: span.marked });
  show('trim');
  $('trim-go').focus();
}

/* A trim is one step of undo and redo, in order with the rest of the stack. The rows below a cut
   at the front are renumbered, and everything under the trim on the stack names rows as they were
   before it, which is where they are again once the trim is undone, so the stack keeps its place
   rather than being cleared. */
async function runTrim() {
  const row = S.trimRow;
  const direction = S.trimDirection;
  S.trimRow = null;
  hide('trim');
  if (!row) return;
  const entry = {
    anywhere: true, key: `${row.sheet}:${row.row}`, what: 'the trim',
    req: { sheet: row.sheet, row: row.row, direction },
    undo: (e) => trimRestore(e),
    redo: (e) => trimRedo(e),
  };
  try {
    await trimApply(entry);
    undoPush(entry);
    // last, so it is not overwritten by the line the reopen puts up
    say(trimmedLine(entry.result), 12000);
  } catch (err) { say(err.message, 9000); }
}

function trimmedLine(data) {
  const n = data.removed;
  // a server from before this build keeps no record an undo could hand back
  if (!data.id) return t('distil.trim.cut', { n });
  const cut = t('distil.trim.cut_undo', { n, keys: keyName(t('distil.keys.undo')) });
  // and the server's one line more when the themes file could not move with the rows
  return data.themes ? `${cut} ${data.themes}` : cut;
}

/* One trim, from the card or again from redo, which is a fresh call with the same sheet, row and
   direction and makes a backup of its own. A field typed into and not yet saved is saved first,
   because the reload redraws the fields. The answer is the trim's record, with the id an undo hands
   back, and the turn to land on. The entry keeps the turn he was on and the turn the reload put
   him on, so an undo with no move in between goes back to the turn he cut from. */
async function trimApply(entry) {
  if (S.dirty) {
    await commit(current(), false);
    if (S.dirty) throw new Error(t('distil.trim.not_saved'));
  }
  const here = current();
  const data = await api('/api/trim', {
    path: S.data.path, ...entry.req, current: here ? { sheet: here.sheet, row: here.row } : null,
  });
  if (data.land) await reloadInPlace(data.land);
  else await openCase(S.data.path);
  entry.result = data;
  entry.here = here ? { sheet: here.sheet, row: here.row } : null;
  entry.landed = current() ? current().key : null;
  return data;
}

/* Undo puts the cut rows back from the backup the trim made, at the place they were cut from, and
   the rows that survived keep whatever was written on them since. A trim made in front of a
   server from before this has no id to hand back: Cmd + Z says to restart and does nothing else,
   and the entry stays where it is, because everything under it names rows the trim renumbered. A
   server that knows no such op answers unknown_op, and the line asks for a restart too. */
async function trimRestore(entry) {
  const id = entry.result && entry.result.id;
  if (!id) throw new Error(RESTART_LINE);
  if (S.dirty) await commit(current(), false);
  const here = current();
  let data;
  try {
    data = await api('/api/rows', {
      op: 'untrim', path: S.data.path, id, current: here ? { sheet: here.sheet, row: here.row } : null,
    });
  } catch (err) {
    throw new Error(needsRestart(err) || refusedAs(err, 'unknown_op') ? RESTART_LINE : err.message);
  }
  // no move since the cut: back to the turn he cut from, and otherwise the turn he is on
  const land = entry.here && here && here.key === entry.landed ? entry.here : data.land;
  await reloadInPlace(land);
  const n = data.restored;
  const back = t('distil.trim.restored', { n });
  say(withThemes(back, data), data.themes ? 9000 : 3600);
}

async function trimRedo(entry) {
  await trimApply(entry);
  say(trimmedLine(entry.result), 12000);
}

/* ─────────────────────────────────────────────────── ai suggestions ── */

/* The button stands under the statement field, where its answers appear. One press takes the
   button away and puts the section in its place: the key concepts of the turn, then three
   candidate statements, under a heading of their own. It stays that way for the turn, and the next
   turn draws the button again. Nothing here reaches the workbook, and a candidate only moves when
   it is clicked. */

function resetAI() {
  S.candidates = [];
  $('ai').hidden = true;
  saidIn('ai-note', '');
  $('ai-label').hidden = true;
  $('ai-tags').innerHTML = '';
  $('ai-candidates').innerHTML = '';
  $('btn-ai').hidden = !(S.data && aiFor(S.data.config, 'statements'));
}

async function askAI() {
  const row = current();
  if (!row) return;
  // the button becomes the section, and comes back when the answer is put away or on the next turn
  $('btn-ai').hidden = true;
  $('ai').hidden = false;
  $('ai-label').hidden = true;
  saidIn('ai-note', t('distil.ai.asking'));
  $('ai-tags').innerHTML = '';
  $('ai-candidates').innerHTML = '';
  const before = S.flat[row.i - 1];
  try {
    const data = await api('/api/suggest', suggestBody(row.text, before ? before.text : '', row.time, row.name,
      keyQuotes(pairsNow().map((p) => p.kq).join('\n'))));
    const tags = data.tags || [];
    S.candidates = data.candidates || [];
    // a server from before the quotes never counts them, so the head never claims they went
    saidIn('ai-note', data.quotes ? t('distil.ai.with_quotes') : '');
    $('ai-label').hidden = tags.length === 0;
    $('ai-tags').innerHTML = tags.map((t) => `<li>${esc(t)}</li>`).join('');
    $('ai-candidates').innerHTML = S.candidates.length
      ? S.candidates.map((c, i) => `<li><button type="button" data-cand="${i}">${esc(c)}</button></li>`).join('')
      : `<li class="empty">${esc(t('distil.ai.no_candidates'))}</li>`;
  } catch (err) {
    S.candidates = [];
    saidErr('ai-note', err);
  }
}

/* What a suggestion is asked with, from the button and from the bench alike: the turn, the turn
   before it, its time and its speaker, and the case, so the prompt carries its project's question,
   the demo's for the demo. The button adds the quotes already taken from the turn, and the
   bench sends none. */
function suggestBody(turn, prior, time, name, quotes = []) {
  const body = { turn, prior, time, name, path: S.data ? S.data.path : '' };
  if (quotes.length) body.quotes = quotes;
  return body;
}

/* The turn's quotes as a suggestion carries them: one a pair that has one, the quote marks
   round each taken off, ten at most and each cut at 400 characters. A turn with none gives none. */
const QUOTES_MAX = 10;
const QUOTE_CHARS = 400;
function keyQuotes(text) {
  return String(text || '').split('\n')
    .map((line) => line.trim().replace(/^["\u201c\u201d]+|["\u201c\u201d]+$/g, '').trim())
    .filter(Boolean).slice(0, QUOTES_MAX).map((q) => q.slice(0, QUOTE_CHARS));
}

/* A candidate fills the statement of the pair being worked on when it is empty, and else comes in
   as a pair of its own under the last. */
function takeCandidate(index) {
  const text = S.candidates[index];
  if (!text) return;
  const { place, added } = candidateTarget(pairsNow(), workingPlace());
  const el = added ? insertPair({ es: text, kq: '' }) : pairEls()[place];
  if (!added) el.querySelector('.pair-es').value = text;
  pairsChanged();
  el.querySelector('.pair-es').focus();
}

/* ── panels, Idiograph's part ── */

/* The shortcuts card. Over the PETs or GETs screen it shows that group alone, with the general rows
   that still apply there, and not one of the transcript's, and over GETs its own rows where a mouse
   act differs there. Over the turn screen it shows them all. */
function openHelp() {
  $('help').classList.toggle('on-themes', !$('themes').hidden);
  $('help').classList.toggle('on-gets', !$('themes').hidden && typeof TH !== 'undefined' && TH.mode === 'gets');
  show('help');
}

/* Idiograph's answer to settingsCase */
function distilSettingsCase() {
  if (!$('themes').hidden && typeof TH !== 'undefined' && TH.path) {
    return { path: TH.path, themes: true, project: TH.project || null,
      config: TH.config || (S.data && S.data.config) || S.libConfig || {} };
  }
  if (!$('library').hidden) {
    const own = homeProject();
    return { path: null, gets: own ? own.gets : null, themes: false, project: own ? own.project : null,
      config: S.libConfig || (S.data && S.data.config) || {} };
  }
  return { path: S.data ? S.data.path : null, themes: false, project: project(), config: S.data ? S.data.config : {} };
}

/* the project whose page the home screen shows, its project and its GETs' workbook, or null on the
   picker */
function homeProject() {
  const data = S.lib || {};
  if (!S.home) return null;
  if (isDemoId(S.home)) {
    const demo = demosOf(data).find((d) => d.id === S.home);
    return demo && demo.project.name ? { project: demo.project, gets: demo.rows.length ? demo.rows[0].path : null } : null;
  }
  const s = sectionsOf(data).find((x) => x.id === S.home);
  return s ? { project: s.project || null, gets: s.gets && s.gets.path ? s.gets.path : null } : null;
}

/* Idiograph's screens' categories, for screenPane */
function distilScreenPane() {
  // the PETs and GETs boards' own, their status bar and their AI, GETs' rules being the project's since settingsplit
  if (onScreen('themes')) return 'pets';
  if (onScreen('work')) return 'statements';
  return null;
}

/* Idiograph's parts of Settings as the card opens (openSettings): the statements screen's interviewer, rounds
   and view, the statement prompt and the nudges, the app's own alone since settingsplit (Adam, 5
   November 2026), a project's being in Project settings */
function distilSettingsOpen(ctx, c) {
  // Dangerously skip permissions, off unless the settings say it is on
  if ($('set-skip-holds')) $('set-skip-holds').checked = c.skip_permissions === true;
  $('set-interviewer').value = c.interviewer || 'Adam';
  // Your name, the name documents carry, empty unless set (31 October)
  if ($('set-your-name')) $('set-your-name').value = c.your_name || '';
  // Work in rounds, off unless the settings say so, and its two fields only while it is ticked
  $('set-rounds').checked = roundsOn(c);
  $('rounds-fields').hidden = !$('set-rounds').checked;
  $('cheer-line').textContent = cheerLine($('set-rounds').checked);
  $('set-minutes').value = c.round_minutes || 10;
  $('set-target').value = c.daily_target || 2;
  // the statements screen's view, as Columns and its View menu hold it, the book's order and the
  // current passage larger unless the settings say otherwise
  fillColumnsSet(columnsLayout(c));
  $('set-larger').checked = largerPassage(c);
  for (const m of MINIMAP_MODES) $(`set-minimap-${m}`).checked = minimapMode(c) === m;
  // the boards' status bar, on unless the settings say otherwise, as a server from before says nothing
  $('set-status-bar').checked = c.status_bar !== false;
  S.viewOpened = viewChoice();
  $('set-prompt').value = c.ai_prompt || S.promptDefault || '';
  $('nudge-switches').innerHTML = Object.entries(NUDGES).map(([k, [label, about]]) =>
    nudgeRow(k, label, about, !!(c.nudges || {})[k])).join('');
}

/* ──────────────────────────────────────── GETs in Project settings ── */

/* Under GETs in Project settings (in Settings until settingsplit): One GET per PET, the minimum a GET needs,
   Smith's (2011a) band until he changes it, and each case of the study with a tick, a case taken out with one
   line of reason. They live in the GETs file at the case root, since the demo's project file refuses a save,
   read when the sheet opens and written on Save only when they have changed. A server from before GETs says to
   restart in their place. */
// `target`, what the GETs file is asked by, a workbook of the project or its id, and `key` the same as one string
const GETS_SET = { target: null, key: null, opened: null, now: null, said: '' };
const smithBand = (n) => (n <= 3 ? n : n <= 8 ? 3 : Math.ceil(n / 2));

async function loadGetsPane(target) {
  const key = target ? JSON.stringify(target) : null;
  Object.assign(GETS_SET, { target: target || null, key, opened: null, now: null, said: '' });
  $('gets-fields').hidden = true;
  $('gets-restart').hidden = true;
  $('gets-block').hidden = true;
  if (!target) return;
  let data;
  try {
    data = await api('/api/gets-settings', target);
  } catch (err) {
    if (GETS_SET.key === key && needsRestart(err)) { $('gets-restart').hidden = false; $('gets-block').hidden = false; }
    return;
  }
  if (GETS_SET.key !== key || !data.settings) return;
  GETS_SET.opened = { minimum: data.settings.minimum === null || data.settings.minimum === undefined ? null : Number(data.settings.minimum),
    one: data.settings.one_per_pet !== false, study: (data.study || []).map((c) => ({ ...c })) };
  GETS_SET.now = JSON.parse(JSON.stringify(GETS_SET.opened));
  drawGetsPane();
  $('gets-fields').hidden = false;
  $('gets-block').hidden = false;
}

function drawGetsPane() {
  const g = GETS_SET.now;
  if (!g) return;
  const inside = g.study.filter((c) => c.in).length;
  const n = g.minimum === null ? smithBand(inside) : g.minimum;
  $('set-one-per-pet').checked = g.one;
  $('set-min-n').textContent = String(n);
  $('set-min-text').lastChild.textContent = t('distil.gets_set.after_n', { n });
  $('set-min-down').disabled = n <= 1;
  $('set-min-up').disabled = n >= Math.max(1, inside);
  $('set-min-band').hidden = g.minimum !== null;
  $('gets-study').innerHTML = g.study.map((c, i) => `<li><label><input type="checkbox" data-gstudy="${i}"${c.in ? ' checked' : ''}> ${esc(c.who)}</label>`
    + (c.in ? '' : `<input type="text" class="gets-why" data-gwhy="${i}" value="${escAttr(c.reason || '')}" spellcheck="true" `
      + `placeholder="${escAttr(t('distil.gets_set.why_placeholder'))}" aria-label="${escAttr(t('distil.gets_set.why_label', { who: c.who }))}">`) + '</li>').join('')
    + (GETS_SET.said ? `<li class="gets-said">${esc(GETS_SET.said)}</li>` : '');
}

function getsMinStep(by) {
  const g = GETS_SET.now;
  if (!g) return;
  const inside = g.study.filter((c) => c.in).length;
  const n = g.minimum === null ? smithBand(inside) : g.minimum;
  g.minimum = Math.max(1, Math.min(Math.max(1, inside), n + by));
  drawGetsPane();
}

/* What Save sends for GETs, or null when nothing there has changed. A case taken out with no
   reason stops the Save with one line, the card left open. */
function getsBody() {
  const was = GETS_SET.opened;
  const now = GETS_SET.now;
  if (!was || !now) return null;
  const body = { op: 'save', ...GETS_SET.target };
  if (now.minimum !== was.minimum) body.minimum = now.minimum;
  if (now.one !== was.one) body.one_per_pet = now.one;
  const study = {};
  now.study.forEach((c, i) => {
    const old = was.study[i] || {};
    const reason = String(c.reason || '').trim();
    if (c.in !== old.in || (!c.in && reason !== String(old.reason || '').trim())) study[c.case] = c.in ? { in: true } : { in: false, reason };
  });
  if (Object.keys(study).length) body.study = study;
  const lacking = now.study.find((c) => !c.in && !String(c.reason || '').trim());
  if (lacking) return { lacking: lacking.who };
  return Object.keys(body).length > 1 + Object.keys(GETS_SET.target).length ? body : null;
}

/* ── AI features, Idiograph's part ── */

/* Each nudge with what it catches, an example made up for it, and why it is there where the code
   gives a reason, in the info mark's tooltip beside its tick. The manual's Nudges entry carries the
   same words. */
const NUDGES = {
  length: [t('distil.nudge.length'), t('distil.nudge.length_about')],
  lead: [t('distil.nudge.lead'), t('distil.nudge.lead_about')],
  quote: [t('distil.nudge.quote'), t('distil.nudge.quote_about')],
  semicolon: [t('distil.nudge.semicolon'), t('distil.nudge.semicolon_about')],
  emdash: [t('distil.nudge.emdash'), t('distil.nudge.emdash_about')],
  arrow: [t('distil.nudge.arrow'), t('distil.nudge.arrow_about')],
  readsas: [t('distil.nudge.readsas'), t('distil.nudge.readsas_about')],
};

/* the circled i, a mark of its own and never the sparkles, which belong to the AI's controls */
const INFO_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><circle cx="8" cy="8" r="6.4" '
  + 'fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M8 7.3v4" fill="none" stroke="currentColor" '
  + 'stroke-width="1.4" stroke-linecap="round"/><circle cx="8" cy="5" r=".9" fill="currentColor"/></svg>';

/* One tick under Nudges: the box and its label, then the info mark, a button in the tab order that
   names the nudge, with the tooltip as its description, shown on hover and on focus. The length nudge's
   number, the project's statement length, is in Project settings since settingsplit (Adam, 5 November 2026),
   and its row speaks of it in words, the open project's number used. */
function nudgeRow(key, label, about, on) {
  return `<div class="nudge-row"><label><input type="checkbox" data-nudge="${key}" ${on ? 'checked' : ''}> <span class="nudge-name">${esc(label)}</span></label>`
    + `<button type="button" class="info-mark" aria-label="${escAttr(t('distil.nudge.about', { label }))}" aria-describedby="nudge-about-${key}">${INFO_ICON}</button>`
    + `<span class="info-tip" role="tooltip" id="nudge-about-${key}">${esc(about)}</span></div>`;
}

/* The tooltip opens under its row, or over it when the column has too little room below to show
   it whole, as for the last nudges with the column scrolled to the top. */
function placeTip(e) {
  const mark = e.target.closest && e.target.closest('.info-mark');
  const tip = mark && mark.nextElementSibling;
  if (!tip) return;
  const room = $('settings-panes').getBoundingClientRect().bottom - mark.getBoundingClientRect().bottom;
  tip.classList.toggle('up', room < (tip.offsetHeight || 120) + 12);
}

/* The test bench: one turn of the demo case, with the turn before it above the box, sent through the
   same two passes as the button under the statement field, with the fields that button sends and
   the provider, the model, the prompt and the question as they stand in the panel, saved or not.
   The button and its answer behave as they do under the statement field, and nothing is written
   anywhere. A box he has edited keeps his text for the session, and Reset to default fetches the
   turn again. */
let benchBusy = false;

async function loadSample(force = false) {
  if (!force && $('bench-text').value.trim()) return;
  try {
    const data = await api('/api/suggest-sample');
    $('bench-prior').value = data.prior || '';
    $('bench-text').value = data.turn || '';
    S.bench = { time: data.time || '', name: data.name || '' };
    if (force) closeBench();
  } catch (err) {
    if (needsRestart(err)) return;
    $('btn-bench').hidden = true;
    $('bench-out').hidden = false;
    saidIn('bench-note', err.message, true);
  }
}

function closeBench() {
  $('bench-out').hidden = true;
  saidIn('bench-note', '');
  $('bench-label').hidden = true;
  $('bench-tags').innerHTML = '';
  $('bench-candidates').innerHTML = '';
  $('btn-bench').hidden = false;
}

async function runBench() {
  if (benchBusy) return;
  const text = $('bench-text').value;
  // the button becomes the section, as it does under the statement field
  $('btn-bench').hidden = true;
  $('bench-out').hidden = false;
  $('bench-label').hidden = true;
  $('bench-tags').innerHTML = '';
  $('bench-candidates').innerHTML = '';
  if (!text.trim()) { saidIn('bench-note', t('distil.bench.empty')); return; }
  benchBusy = true;
  saidIn('bench-note', t('distil.ai.asking'));
  const body = suggestBody(text, $('bench-prior').value, S.bench.time, S.bench.name);
  // the provider, the model and the address as the card holds them, saved or not (shell.js aiTryBody)
  aiTryBody(body);
  if ($('set-prompt').value.trim()) body.ai_prompt = $('set-prompt').value;
  // the question of the case's own project, as saved, since it is Project settings' since settingsplit
  const own = settingsCase().project;
  if (own) body.research_question = String(own.research_question || '');
  try {
    const data = await api('/api/suggest-sample', body);
    // a server from before this answers the four fields with the sample itself
    if (!data.tags && !data.candidates && data.turn !== undefined) throw olderServer();
    const tags = data.tags || [];
    const found = data.candidates || [];
    const took = tNum(Number(data.seconds || 0), { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    saidIn('bench-note', t('distil.bench.took', { model: data.model_name || data.model || t('distil.bench.the_model'), seconds: took }));
    $('bench-label').hidden = tags.length === 0;
    $('bench-tags').innerHTML = tags.map((t) => `<li>${esc(t)}</li>`).join('');
    $('bench-candidates').innerHTML = found.length
      ? found.map((c) => `<li><span class="said">${esc(c)}</span></li>`).join('')
      : `<li class="empty">${esc(t('distil.ai.no_candidates'))}</li>`;
  } catch (err) {
    saidErr('bench-note', err);
  } finally {
    benchBusy = false;
  }
}

/* Idiograph's keys in Settings' Save (saveSettings): the statements screen's interviewer and rounds, the
   nudges, the statement prompt, the view's keys once they have moved and the PETs limit once it has */
function distilSettingsBody(body) {
  // the screen it was opened over, for what Idiograph does once the settings are saved. A project's own settings
  // are Project settings' to save since settingsplit
  DISTIL_SAVED.sends = { ctx: settingsCase(), saved: null };
  const nudges = {};
  document.querySelectorAll('[data-nudge]').forEach((el) => { nudges[el.dataset.nudge] = el.checked; });
  Object.assign(body, {
    interviewer: $('set-interviewer').value.trim() || 'Adam',
    your_name: $('set-your-name') ? $('set-your-name').value.trim() : undefined,
    work_in_rounds: $('set-rounds').checked,
    round_minutes: Number($('set-minutes').value) || 10,
    daily_target: Number($('set-target').value) || 2,
    nudges,
  });
  if (APP === 'idiograph' && $('set-prompt').value.trim()) body.ai_prompt = $('set-prompt').value;
  if ($('set-skip-holds')) body.skip_permissions = $('set-skip-holds').checked;
  // the view's keys, each only once it has moved since the card opened, so a choice the View menu or
  // Columns made since the settings were read is never put back by a card opened over another screen.
  // The columns' order is a list, so each is compared as it is written
  const view = viewChoice();
  const said = (v) => JSON.stringify(v);
  for (const key of Object.keys(view)) if (!S.viewOpened || said(view[key]) !== said(S.viewOpened[key])) body[key] = view[key];
}


/* the last Save's sends, for what Idiograph does once the settings are saved */
const DISTIL_SAVED = { sends: null };

/* over the PETs screen the bar takes the switch and the model at once, and the band the question */
function distilSettingsSaved(data) {
  const sends = DISTIL_SAVED.sends;
  if (sends && sends.ctx.themes && typeof thSettingsSaved === 'function') thSettingsSaved(data, sends.saved);
}

/* the case behind, under the turn screen or the PETs screen, and never one left from before Sift */
async function distilSettingsAfter(data) {
  const { ctx } = DISTIL_SAVED.sends || { ctx: settingsCase() };
  if (S.data && (onScreen('work') || ctx.themes)) {
    const before = JSON.stringify([S.data.config.round_minutes, S.data.config.interviewer]);
    const paced = roundsOn(S.data.config);
    S.data.config = data.config;
    // the view as Settings left it, the notes field moved where it now stands, its words kept, and
    // the passage in the middle of the column again
    drawView();
    if (!ctx.themes && current()) centreCurrent(false);
    $('btn-ai').hidden = !aiFor(data.config, 'statements');
    if (!aiFor(data.config, 'statements')) $('ai').hidden = true;
    const recut = before !== JSON.stringify([data.config.round_minutes, data.config.interviewer]);
    // Work in rounds ticked or unticked: the bar, the markers and the count drawn again in place,
    // a field typed into and not saved saved first, as on any move (15 October)
    const turned = paced !== roundsOn(data.config);
    // over the PETs screen the turn screen is out of sight, so it reopens on the way back
    if (ctx.themes) { if (recut || turned) S.recut = true; }
    else if (recut) {
      // a new interviewer recuts the rounds too, which are only spoken of while he works in them
      say(roundsOn(data.config) ? t('distil.settings.rounds_reopening') : t('distil.settings.reopening'));
      openCase(S.data.path);
    } else if (turned) {
      if (S.dirty && current()) await commit(current(), false);
      S.sheetDrawn = null;
      drawRoundsShown();
      drawTurn({ keepPlayer: true });
      drawProgress();
    } else { runNudges(); }
  }
}

/* ───────────────────────────────────────────────────── the project ── */

/* The project is the root folder the case sits under, and its research question is what every
   statement answers, so it stands in a band over the three columns. It comes with the case, from the
   project file at that root, or from the demo's own file for the demo. A server from before the
   project sends none: the band then says there is no question yet, and Projects says to restart. */
const project = () => (S.data && S.data.project) || null;
const NO_QUESTION = t('distil.band.no_question');

function drawBand() {
  const p = project();
  const question = p ? String(p.research_question || '').trim() : '';
  const full = $('band-question');
  full.classList.toggle('band-none', !question);
  if (question) full.textContent = question;
  else full.innerHTML = t('distil.band.no_question_html', { none: esc(NO_QUESTION) });
  measureBand();
}

/* The columns under the band keep the rest of the screen: its height goes into --band, which
   theirs take off, whenever it changes, rewrapped or redrawn, with the toolbar's row under it while the toolbar is
   docked there (barsD, 6 November 2026). */
function measureBand() {
  // and the title bar's rows past the one the stylesheet allows for, as below 760px where it takes three, so
  // the player stays whole above the status bar at a phone's width (21 October)
  const band = $('band');
  const dock = $('es-dock');
  const tools = dock && !dock.hidden ? dock.offsetHeight : 0;
  // and the reviewer's tray, a row under the dock while it stands on this screen (review.js, trayfix)
  const tray = $('wt-tray');
  const review = tray && !tray.hidden && tray.parentElement === $('work') ? tray.offsetHeight : 0;
  const h = $('work').hidden ? 0 : band.offsetHeight + tools + review + Math.max(0, Math.round(band.getBoundingClientRect().top) - 48);
  $('work').style.setProperty('--band', `${h}px`);
}

/* The statements screen's own toolbar (barsD, Adam, 6 November 2026): a row under the band in line with the boards'
   toolbar, its grip at the left pulling it off to float over the columns as the boards' floats over the canvas, by
   the boards' own code (thPalettePlace and the rest in themes.js), docked by default and its place kept in the
   settings, `es_palette_docked` and `es_palette_place`. Find and replace opens its card as Cmd + Shift + F does, the
   previous and the next passage move as Cmd + J and Cmd + K do, and Undo and Redo at its right end are the screen's
   own, as Cmd + Z and Shift + Cmd + Z are, a field's own where its typing is newer than the screen's last change.
   Its words give way where the row runs short, as the boards' toolbar's do. */
const ES_TOOLS = {
  pal: 'es-palette', dock: 'es-dock', stage: 'es-stage', slot: 'es-dock-slot', docked: 'es_palette_docked',
  place: 'es_palette_place', alone: true,
  config: () => (S.data && S.data.config) || S.libConfig || {},
  // the player at the columns' foot, which the floating toolbar keeps clear of
  foot: () => { const p = $('player-wrap'); return p && !p.hidden ? p.offsetHeight + 8 : 0; },
  measure: () => measureBand(),
  save: (key, value, more) => esToolsSave(key, value, more),
};

/* the toolbar's place kept, every copy of the settings told and the toolbar put where they now say */
async function esToolsSave(key, value, more = {}) {
  const all = Object.assign({ [key]: value }, more);
  for (const c of [S.data && S.data.config, S.libConfig, typeof TH !== 'undefined' ? TH.config : null]) if (c) Object.assign(c, all);
  thPalettePlace(undefined, ES_TOOLS);
  try {
    const data = await api('/api/settings', all);
    if (!data.config || data.config[key] === undefined) say(RESTART_LINE, 9000);
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* Undo or Redo from the toolbar, as its key: the field's own while its typing is the newer, else the screen's */
function esUndoTool(backwards) {
  if (!S.data || $('work').hidden) return;
  if (nativeUndoOwns(backwards)) { document.execCommand(backwards ? 'undo' : 'redo'); return; }
  undoStep(backwards);
}

/* The toolbar's tools, each doing what its key does, a press leaving the focus where it was, in a field or on the
   passage, as the boards' tools leave it on the canvas, and its grip moving it as the boards' grip moves theirs */
function esToolsBoot() {
  const pal = $('es-palette');
  if (!pal) return;
  pal.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  $('es-find').onclick = () => openFind();
  $('es-prev').onclick = () => { if (S.data && !$('work').hidden) move(-1); };
  $('es-next').onclick = () => { if (S.data && !$('work').hidden) move(1); };
  $('es-undo').onclick = () => esUndoTool(true);
  $('es-redo').onclick = () => esUndoTool(false);
  $('es-palette-grip').addEventListener('pointerdown', (e) => thPaletteGrab(e, ES_TOOLS));
  // the boards' code is themes.js's, which loads after this script, so nothing asks it before it is there
  const fit = () => { if (typeof thPaletteFit === 'function') thPaletteFit(ES_TOOLS); };
  if (window.ResizeObserver) {
    new ResizeObserver(() => { measureBand(); fit(); }).observe($('es-dock'));
    // floating, it keeps its place on the columns as the window changes
    new ResizeObserver(() => {
      if (!$('work').hidden && typeof thDocked === 'function' && !thDocked(ES_TOOLS)) thPalettePlace(undefined, ES_TOOLS);
    }).observe($('es-stage'));
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
}

/* Project settings (settingsplit, Adam, 5 November 2026): one project's own sheet, for the project it was opened
   for and no other, with no picker, where Settings' Projects category held a row of every project's name. Its
   name, its research question, its method, PET labels, timecodes and timepoints, its root folder with Remove from
   Idiograph beside it, the statement length, GETs' rules and the privacy tick with the agents' guide. A thematic
   analysis project's sheet has what applies to it alone. The demos' are fixed, their fields read-only under a
   line that says so. A server from before the project sent none, and the sheet says to restart and nothing else. */
// `p`, the project shown, and `own`, the project of the screen it was opened over when it is this one, whose case's
// workbook goes with its requests
const PROJ = { p: null, own: null };

const projectAt = () => PROJ.p;

/* the project of the screen behind, the PETs or GETs board's, a case's or a project page's, when it is `p` */
function projectBehind(p) {
  const ctx = settingsCase();
  return ctx.project && (ctx.project.id || '') === (p.id || '') ? ctx.project : null;
}

/* what GETs' rules are asked by: a workbook of the project open behind the sheet, a demo's own, or the project's id */
function getsTarget(p) {
  const ctx = settingsCase();
  const own = projectBehind(p);
  if (own && ctx.path) return { workbook: ctx.path };
  if (own && ctx.gets) return { workbook: ctx.gets };
  if (isDemoId(p.id || '')) {
    const demo = demosOf(S.lib || {}).find((d) => d.id === p.id);
    return demo && demo.rows.length ? { workbook: demo.rows[0].path } : null;
  }
  return p.id ? { root: p.id } : null;
}

/* The sheet opens for `p`: the copy the screen behind holds when it is the same project, the freshest, its fields
   drawn, the AI agents' part only while AI features is on, and GETs' rules asked of the server */
function openProjectSettings(p) {
  if (!p) return;
  const own = projectBehind(p);
  const shown = own || p;
  PROJ.own = own || (shown.demo ? shown : null);
  PROJ.p = shown;
  $('projset-kicker').textContent = shown.demo ? (shown.id === DEMO_TA_ID ? t('distil.tag.demo_ta') : t('distil.home.demo'))
    : (shown.name || t('distil.home.project'));
  projectSaid('');
  drawProjectPane(shown);
  const c = settingsCase().config || S.libConfig || {};
  $('agents-block').hidden = !aiOn(c);
  // GETs' rules and the statement length are IPA's: a thematic analysis project's codes take no nudges and its
  // themes no GETs file
  const ta = shown.method === 'ta';
  $('words-block').hidden = ta;
  // the project's list of names to replace, none for a demo (namesui)
  $('names-block').hidden = !!shown.demo || !shown.id;
  loadGetsPane(ta ? null : getsTarget(shown));
  // Working together (wtkeys, team.js), off until turned on, drawn once the server says how it stands
  if (typeof wtOpen === 'function') wtOpen(shown);
  show('projset');
  $('projset-body').scrollTop = 0;
  $('set-project-name').focus();
}

/* one project's fields, as the server sent them */
function drawProjectPane(p = project()) {
  $('project-restart').hidden = !!p;
  $('project-fields').hidden = !p;
  if (!p) return;
  const fixed = !!p.demo;
  $('set-project-name').value = p.name || '';
  $('set-question').value = p.research_question || '';
  $('set-project-name').readOnly = fixed;
  $('set-question').readOnly = fixed;
  $('project-fixed').hidden = !fixed;
  $('project-root').innerHTML = pathHtml(p.root);
  // Remove from Idiograph beside the root folder, never for the demo's own project or in a run of one
  $('project-remove').hidden = fixed || !p.id || !!S.oneRun;
  $('project-remove').onclick = () => removeProject(p);
  // the project's method, shown and never changed (tadraw), a thematic analysis project's settings in its own
  // words, with no PET labels and no timepoints
  const ta = p.method === 'ta';
  $('set-method').textContent = ta ? t('method.name_ta') : t('method.name_ipa');
  $('set-labels-row').hidden = ta;
  $('tp-block').hidden = ta;
  tIn(p.method, () => {
    drawLabels(p);
    drawTimecodes(p);
    drawTimepoints(p);
    drawWords(p);
    drawAgents(p);
  });
}

/* The project a request from this sheet is for: its id, and the case's workbook beside it when it is the
   project of the case behind, so a server from before the projects finds it as it always did. */
function projectBody(p = projectAt()) {
  const body = { root: p ? p.id : '' };
  const ctx = settingsCase();
  if (p && PROJ.own && p.id === PROJ.own.id && ctx.path) body.path = ctx.path;
  return body;
}

/* What Save sends for the project: its name and question when either changed, and its tick, on its own with its
   date, when that changed, the demo's never */
function projectSaves() {
  const p = projectAt();
  const out = [];
  if (!p || p.demo) return out;
  const name = $('set-project-name').value.trim();
  const question = $('set-question').value.trim();
  if (name !== String(p.name || '') || question !== String(p.research_question || '')) {
    out.push({ ...projectBody(p), name, research_question: question });
  }
  if (p.agents && $('set-agents').checked !== !!p.agents.allowed) out.push({ ...projectBody(p), agents: $('set-agents').checked });
  return out;
}

function projectSaid(text, failed = false) {
  saidIn('project-said', text || '', failed);
  $('project-said').hidden = !text;
}

/* Save: GETs' rules to their file, refused with a line while a participant out has no reason, then the project to
   its file, each only when it changed. The screen behind takes what changed: a GETs board read again, the band's
   question, Home's cards and the project's page, and a case or a board opened again once the timepoints changed */
async function saveProjectSettings() {
  const p = projectAt();
  if (!p) { hide('projset'); return; }
  const gets = getsBody();
  if (gets && gets.lacking) {
    GETS_SET.said = t('distil.gets_set.say_why', { who: gets.lacking });
    drawGetsPane();
    return;
  }
  const sends = projectSaves();
  try {
    if (gets) {
      const over = !$('themes').hidden && typeof TH !== 'undefined' && TH.mode === 'gets' && TH.live;
      if (over) await thFlush();
      const answer = await api('/api/gets-settings', gets);
      if (over && typeof thLoad === 'function' && answer.cards) thLoad(answer);
    }
    let saved = null;
    for (const sent of sends) saved = (await api('/api/project', sent)).project || saved;
    projectSaid('');
    hide('projset');
    if (saved && !saved.demo) projectTake(saved);
  } catch (err) { projectSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
}

/* the project as the server now has it, in every copy the page holds and on every screen that shows it */
function projectTake(saved) {
  const id = saved.id || '';
  if (S.data && S.data.project && !S.data.project.demo && (S.data.project.id || '') === id) { S.data.project = saved; drawBand(); }
  if (typeof TH !== 'undefined' && TH.project && !TH.project.demo && (TH.project.id || '') === id && typeof thSettingsSaved === 'function') {
    thSettingsSaved(null, saved);
  }
  if (!$('library').hidden) loadLibrary().catch((err) => say(err.message, 9000));
}

/* Remove from Idiograph, after Remove's card: the project forgotten, its folder and every file in it left as they
   are, or with the card's tick moved to the system's Trash (removetrash). From over one of its own cases, what is
   typed is saved first and the page opens on the home screen's picker, since the case belongs to no project now. */
async function removeProject(p) {
  const asked = await askRemove(p.name);
  if (!asked) return;
  const own = !!PROJ.own && p.id === PROJ.own.id;
  if (own && !(await savePending())) return;
  let data;
  try {
    data = await api('/api/projects', { op: 'remove', root: p.id, trash: asked.trash, page: pageId() });
  } catch (err) { projectSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); return; }
  if (own) { S.noSpot = true; homeKeep(''); location.reload(); return; }
  hide('projset');
  // from a project's page, Home's own list, since the page belongs to no project now
  if (!$('library').hidden && S.home === p.id) homeKeep('');
  if (!$('library').hidden) loadLibrary().catch((err) => say(err.message, 9000));
  say(removedSaid(data.name || p.name, data, t('distil.home.removed', { name: data.name || p.name })), 6000);
}

/* ───────────────────────────────────────────────────── PET labels ── */

/* Under Projects: PET labels, the book's letters, A, A1, A1.1, or numbers, PET 1, PET 1a, 1a.1, the
   same pair as under Export on the PETs screen, for the project shown. A press saves `pet_labels` in
   its project file at once, every other key kept, for every case of the project, and the PETs
   screen under the card takes it at once too. The demo's are fixed, the letters. A server from
   before it sends no `pet_labels`, and a press says to restart under the pair. */
const petLabelsOf = (p) => (p && p.pet_labels === 'numbers' ? 'numbers' : 'letters');

function drawLabels(p) {
  const box = $('set-labels');
  if (!box) return;
  box.querySelectorAll('[data-labels]').forEach((b) => {
    const on = b.dataset.labels === petLabelsOf(p);
    b.classList.toggle('on', on);
    b.setAttribute('aria-checked', String(on));
    b.disabled = !p || !!p.demo;
  });
  $('labels-said').hidden = true;
}

async function saveLabels(value) {
  const p = projectAt();
  if (!p || p.demo || petLabelsOf(p) === value) return;
  const said = $('labels-said');
  let answer = null;
  try {
    answer = (await api('/api/project', { ...projectBody(p), pet_labels: value })).project || null;
  } catch (err) {
    saidErr('labels-said', err);
    said.hidden = false;
    return;
  }
  if (!answer || !answer.pet_labels) {
    saidIn('labels-said', RESTART_LINE);
    said.hidden = false;
    return;
  }
  // every copy of this project the page holds takes it, the PETs screen's among them
  const held = [p, PROJ.own, S.data && S.data.project, typeof TH !== 'undefined' ? TH.project : null];
  for (const one of held) if (one && (one.id || '') === p.id) one.pet_labels = answer.pet_labels;
  if (projectAt() === p) drawLabels(p);
}

/* ───────────────────────────────────────────────────── timecodes ── */

/* Under Projects, after PET labels (28 October): Timecodes, 75:12, 1:15:12 or 01:15:12, each written as
   itself. A press saves `timecodes` in the project file at once, every other key kept, and every
   timecode of the project follows: the transcript and the player at once, a board read again, and
   print and Word from the server. The demo's are fixed. A server from before it sends no `timecodes`,
   and a press says to restart under the row. */
function drawTimecodes(p) {
  const box = $('set-timecodes');
  if (!box) return;
  box.querySelectorAll('[data-tc]').forEach((b) => {
    const on = b.dataset.tc === timecodesOf(p);
    b.classList.toggle('on', on);
    b.setAttribute('aria-checked', String(on));
    b.disabled = !p || !!p.demo;
  });
  $('tc-said').hidden = true;
}

async function saveTimecodes(value) {
  const p = projectAt();
  if (!p || p.demo || timecodesOf(p) === value) return;
  const said = $('tc-said');
  let answer = null;
  try {
    answer = (await api('/api/project', { ...projectBody(p), timecodes: value })).project || null;
  } catch (err) {
    saidErr('tc-said', err);
    said.hidden = false;
    return;
  }
  if (!answer || !answer.timecodes) {
    saidIn('tc-said', RESTART_LINE);
    said.hidden = false;
    return;
  }
  const held = [p, PROJ.own, S.data && S.data.project, typeof TH !== 'undefined' ? TH.project : null];
  for (const one of held) if (one && (one.id || '') === p.id) one.timecodes = answer.timecodes;
  if (projectAt() === p) drawTimecodes(p);
  // the case open behind the card takes them at once: the margin from each row's seconds, a board read again
  if (S.data && S.data.project && (S.data.project.id || '') === p.id) retimeRows(answer.timecodes);
  if (typeof TH !== 'undefined' && TH.live && TH.project && (TH.project.id || '') === p.id) thOwnLoad({ changed: false });
}

/* Every row's timecode written again from its seconds, the time cited with a timepoint keeping it. */
function retimeRows(form) {
  for (const row of S.flat || []) {
    if (row.seconds === null || row.seconds === undefined) continue;
    row.time = String(row.time || '').replace(/\d+:\d{2}(:\d{2})?$/, '') + timecode(row.seconds, form);
    const el = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"] .turn-gutter .time`);
    if (el) el.outerHTML = timeHtml(row);
  }
  const now = current();
  if (now) $('back-to-turn-time').textContent = now.time;
  if ($('player').getAttribute('src')) drawPlayer();
}

/* ───────────────────────────────────────────────────── timepoints ── */

/* Under Projects, after PET labels (20 October, Adam's longitudinal model after Farr and Nizza 2019):
   Timepoints, how many times each participant was interviewed, 1 by default, which is the app as it
   always was. With two or more, a row each, its label, T1, and its description, Before the season,
   his to rename. The number saves at once, and a label or a description once it is left. Lowering
   the number while a timepoint holds an interview is refused in one line under the rows, naming the
   participants, and the number stays. The demo's are fixed. A server from before them sends no
   `timepoints`, and the row stands disabled. */
const TP_MAX = 10;
const timepointsOf = (p) => (p && Array.isArray(p.timepoints) && p.timepoints.length
  ? p.timepoints : [{ n: 1, label: 'T1', description: '' }]);
const longitudinal = (p) => !!(p && Array.isArray(p.timepoints) && p.timepoints.length >= 2);

function drawTimepoints(p) {
  const known = !!(p && Array.isArray(p.timepoints));
  const tps = timepointsOf(p);
  const fixed = !p || !!p.demo || !known;
  $('tp-count').textContent = String(tps.length);
  $('tp-less').disabled = fixed || tps.length <= 1;
  $('tp-more').disabled = fixed || tps.length >= TP_MAX;
  const rows = $('tp-rows');
  rows.hidden = tps.length < 2;
  rows.innerHTML = tps.length < 2 ? ''
    : `<span class="tp-head" aria-hidden="true">${esc(t('distil.tp.label_head'))}</span><span class="tp-head" aria-hidden="true">${esc(t('distil.tp.desc_head'))}</span>`
      + tps.map((tp) => `<input type="text" class="tp-label" data-n="${tp.n}" maxlength="12" spellcheck="false"`
        + ` aria-label="${escAttr(t('distil.tp.label_of', { n: tp.n }))}" value="${escAttr(tp.label)}"${fixed ? ' readonly' : ''}>`
        + `<input type="text" class="tp-desc" data-n="${tp.n}" maxlength="60" spellcheck="true"`
        + ` aria-label="${escAttr(t('distil.tp.desc_of', { n: tp.n }))}" value="${escAttr(tp.description || '')}"${fixed ? ' readonly' : ''}>`).join('');
  rows.onchange = () => saveTimepoints(typedTimepoints());
  $('tp-less').onclick = () => saveTimepoints(typedTimepoints().slice(0, -1));
  $('tp-more').onclick = () => {
    const now = typedTimepoints();
    saveTimepoints([...now, { label: `T${now.length + 1}`, description: '' }]);
  };
  tpSaid('');
}

/* the timepoints as the rows stand, typed and not saved included */
function typedTimepoints() {
  const p = projectAt();
  const tps = timepointsOf(p);
  if (tps.length < 2) return tps.map((t) => ({ label: t.label, description: t.description || '' }));
  return tps.map((t) => ({
    label: ($(`tp-rows`).querySelector(`.tp-label[data-n="${t.n}"]`) || {}).value || '',
    description: ($(`tp-rows`).querySelector(`.tp-desc[data-n="${t.n}"]`) || {}).value || '',
  }));
}

function tpSaid(text, failed = false) {
  saidIn('tp-said', text || '', failed);
  $('tp-said').hidden = !text;
}

async function saveTimepoints(list) {
  const p = projectAt();
  if (!p || p.demo || !list.length) return;
  let answer;
  try {
    answer = (await api('/api/project', { ...projectBody(p), timepoints: list })).project || null;
  } catch (err) {
    tpSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));
    return;
  }
  if (!answer || !Array.isArray(answer.timepoints)) { tpSaid(RESTART_LINE); return; }
  // every copy of this project the page holds takes them
  const held = [p, PROJ.own, S.data && S.data.project, typeof TH !== 'undefined' ? TH.project : null];
  for (const one of held) if (one && (one.id || '') === p.id) one.timepoints = answer.timepoints;
  if (projectAt() === p) {
    const focused = document.activeElement;
    const at = focused && focused.dataset ? [focused.className, focused.dataset.n] : null;
    drawTimepoints(p);
    if (at) {
      const again = $('tp-rows').querySelector(`.${at[0].split(' ')[0]}[data-n="${at[1]}"]`);
      if (again) again.focus();
    }
  }
  S.tpChanged = true;
}

/* Settings shut once the timepoints changed: the home screen's cards read again, or the case behind
   opened again, so its bar and its timepoints are the project's as they now stand */
function tpAfter() {
  if (!S.tpChanged) return;
  S.tpChanged = false;
  if (!$('library').hidden) loadLibrary().catch((err) => say(err.message, 9000));
  else if (S.data && onScreen('work')) openCase(S.data.path);
}

/* ─────────────────────────────────────────────── the statement length ── */

/* Under Experiential statements, in the length nudge's own row (Adam, 20 October, Settled 13, and 21
   October, the number in the row it governs): the words past which the length nudge speaks, the
   project's own number, 15 by default, the book's band. It is the project's that Projects shows, named
   in the number's tooltip, saved in its file a moment after the last change, every other key kept, and
   the statements screen's counts and nudges take it at once. The demo's is fixed. A server from before
   it sends no `statement_words`, and the number stands disabled. */
const WORDS_DEFAULT = 15;
const WORDS_MIN = 5;
const WORDS_MAX = 60;
const WORDS = { timer: null, shown: null };

function wordsOf(p) {
  const n = p ? Number(p.statement_words) : NaN;
  return Number.isInteger(n) && n >= WORDS_MIN && n <= WORDS_MAX ? n : WORDS_DEFAULT;
}

/* the statements screen's own length, its project's */
const wordBand = () => wordsOf(S.data && S.data.project);

function drawWords(p) {
  const field = $('words-n');
  if (!field) return;
  const known = !!(p && p.statement_words !== undefined);
  const fixed = !p || !!p.demo || !known;
  const n = WORDS.shown !== null && WORDS.timer ? WORDS.shown : wordsOf(p);
  if (document.activeElement !== field || !WORDS.timer) field.value = String(n);
  field.disabled = fixed;
  field.title = !p ? '' : p.demo ? t('distil.words.title_demo') : p.name ? t('distil.words.title', { name: p.name })
    : t('distil.words.title_this');
  if (!WORDS.timer) wordsSaid('');
}

function wordsSaid(text, failed = false) {
  saidIn('words-said', text || '', failed);
  $('words-said').hidden = !text;
}

/* the number as typed or stepped, saved once the changes stop, between 5 and 60 */
function wordsSet(value, done = false) {
  const p = projectAt() || project();
  if (!p || p.demo || p.statement_words === undefined) return;
  const typed = Math.round(Number(value));
  if (!Number.isFinite(typed) || String(value).trim() === '') { if (done) drawWords(p); return; }
  WORDS.shown = Math.min(WORDS_MAX, Math.max(WORDS_MIN, typed));
  clearTimeout(WORDS.timer);
  WORDS.timer = setTimeout(() => saveWords(p, WORDS.shown), 450);
  if (done) $('words-n').value = String(WORDS.shown);
}

async function saveWords(p, n) {
  let answer = null;
  try {
    answer = (await api('/api/project', { ...projectBody(p), statement_words: n })).project || null;
  } catch (err) {
    WORDS.timer = null;
    WORDS.shown = null;
    drawWords(p);
    wordsSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));
    return;
  }
  WORDS.timer = null;
  WORDS.shown = null;
  if (!answer || answer.statement_words === undefined) { drawWords(p); wordsSaid(RESTART_LINE); return; }
  // every copy of this project the page holds takes it, the statements screen's among them
  const held = [p, PROJ.own, S.data && S.data.project, typeof TH !== 'undefined' ? TH.project : null];
  for (const one of held) if (one && (one.id || '') === p.id) one.statement_words = answer.statement_words;
  if ((projectAt() || project()) === p) drawWords(p);
  if (S.data && S.data.project && (S.data.project.id || '') === p.id) { drawWordCount(); runNudges(); }
}

/* ────────────────────────────────────────────────────── AI agents ── */

/* Under Project: Allow AI agents to read this project, the privacy tick the command line asks for
   before it reads anything (see docs/agents.md). Off by default and kept in the project file with
   the date it was set, saved with Save. The demo's is always on, and fixed. A server from before it
   sends no `agents`, and the tick stands disabled over the restart line. Then Write a guide for AI
   agents, which writes AGENTS.md at the case root at once, never over a file of his own, and asks
   before it writes again over the one it wrote. */
const AGENTS_LINE = t('distil.agents.line');

function agentsLine(p) {
  if (!p.agents) return RESTART_LINE;
  if (p.demo) return t('distil.agents.demo');
  if (p.agents.allowed && p.agents.at) return t('distil.agents.allowed', { day: dayWords(p.agents.at), line: AGENTS_LINE });
  return AGENTS_LINE;
}

function dayWords(iso) {
  const at = new Date(iso);
  return Number.isNaN(at.getTime()) ? String(iso)
    : tDate(at, { day: 'numeric', month: 'long', year: 'numeric' });
}

function drawAgents(p) {
  $('set-agents').checked = !!(p.agents && p.agents.allowed);
  $('set-agents').disabled = !p.agents || !!p.demo;
  $('agents-line').textContent = agentsLine(p);
  $('agents-guide').hidden = !!p.demo;
  $('agents-guide-update').hidden = true;
  $('agents-said').hidden = true;
  drawMcp();
}

async function agentsGuide(update) {
  const said = $('agents-said');
  try {
    const data = await api('/api/agents-guide', update ? { ...projectBody(), update: true } : projectBody());
    saidIn('agents-said', data.said || '');
    $('agents-guide-update').hidden = !data.ours || !!data.written;
  } catch (err) {
    saidErr('agents-said', err);
    $('agents-guide-update').hidden = true;
  }
  said.hidden = !said.textContent;
}

/* ── Add Idiograph to Claude Desktop ── */

/* Under the agents' guide: the button opens a card with the entry that runs Idiograph's MCP server,
   the command line's commands as tools, on this project, as Claude Desktop's settings file will
   hold it, and Add writes it there, every other entry kept and the file as it was copied beside it
   first. Any other client takes the same entry, and Claude Code one line, each with Copy. A server
   from before it says to restart, under the button. */
function drawMcp() {
  $('mcp-card').hidden = true;
  $('mcp-show').setAttribute('aria-expanded', 'false');
  $('mcp-said').hidden = true;
  saidIn('mcp-said', '');
}

function mcpSaid(text, failed = false) {
  saidIn('mcp-said', text || '', failed);
  $('mcp-said').hidden = !text;
}

async function mcpShow() {
  if (!$('mcp-card').hidden) { drawMcp(); return; }
  try {
    const data = await api('/api/mcp', { ...projectBody(), op: 'show' });
    $('mcp-where').textContent = t('distil.mcp.where', { file: data.desktop });
    $('mcp-entry').textContent = data.json;
    $('mcp-line').textContent = data.claude_code;
    $('mcp-card').hidden = false;
    $('mcp-show').setAttribute('aria-expanded', 'true');
    mcpSaid('');
  } catch (err) { mcpSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
}

async function mcpAdd() {
  try {
    const data = await api('/api/mcp', { ...projectBody(), op: 'add' });
    mcpSaid(data.said || '');
  } catch (err) { mcpSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
}

/* Copy puts the block above it on the clipboard and says Copied for a moment. */
async function mcpCopy(button, from) {
  try {
    await navigator.clipboard.writeText($(from).textContent);
    button.textContent = t('distil.mcp.copied');
    setTimeout(() => { button.textContent = t('distil.mcp.copy'); }, 1600);
  } catch { mcpSaid(t('distil.mcp.clipboard_refused'), true); }
}

/* ── Restart and Quit, Idiograph's part ── */

/* Idiograph's: the turn's fields and an interviewer note, and the canvas's last save */
async function distilSavePending() {
  if (S.note && noteUnkept() && !(await keepNote(true))) return false;
  if (S.dirty && S.data && current()) {
    await commit(current(), false);
    if (S.dirty) return false;
  }
  if (!$('themes').hidden && typeof thFlush === 'function') await thFlush();
  return true;
}

/* Idiograph's screen in front, for spotNow */
function distilSpot() {
  const turn = () => {
    const row = S.flat.length ? current() : null;
    return Object.assign({ screen: 'work', path: S.data.path }, row ? { sheet: row.sheet, row: row.row } : {});
  };
  if (!$('work').hidden && S.data) return turn();
  // the Trajectories board, by the workbook it was opened through (21 October)
  if ($('traj') && !$('traj').hidden && typeof TJ !== 'undefined' && TJ.path) return { screen: 'trajectories', path: TJ.path };
  if ($('themes').hidden || typeof TH === 'undefined' || !TH.live || !TH.path || !TH.meta) return null;
  // a participant's LPETs, and a timepoint's PETs, come back to the same canvas (21 October)
  if (TH.mode === 'gets') return Object.assign({ screen: 'gets', path: TH.path, board: TH.meta.id }, TH.lpets ? { lpets: true } : {});
  const under = TH.to === 'statements' && S.data ? turn() : null;
  return Object.assign({ screen: 'pets', path: TH.path, board: TH.meta.id, label: TH.label || '', under },
    TH.tp ? { timepoint: TH.tp } : {});
}

/* Idiograph's screen kept, opened again (see comeBack) */
async function distilComeBack(spot, home) {
  if (spot.screen === 'trajectories') { $('library').hidden = true; trajOpen(spot.path, { back: home, to: 'cases', gone: home }); return; }
  const turn = spot.screen === 'work' ? spot : spot.under;
  if (turn && turn.path) {
    let data;
    try {
      data = await api('/api/open', { path: turn.path });
    } catch { home(); return; }
    startCase(data, { at: turn.sheet ? { sheet: turn.sheet, row: turn.row } : null });
    if (spot.screen === 'work') return;
  }
  const more = Object.assign({ board: spot.board || null, gone: home }, spot.lpets ? { lpets: true } : {},
    Number(spot.timepoint) > 1 ? { timepoint: Number(spot.timepoint) } : {});
  if (spot.screen === 'pets') openThemes(spot.path, turn ? 'work' : 'library', spot.label || '', more);
  else openGets(spot.path, more);
}

/* ── a turn written in a conversation ── */

/* An AI agent may write a turn's statements, notes and quotes through the command line, and the
   progress file records each under `edits` with `by: agent`. On a focus of the window and every
   thirty seconds the turn screen asks /api/stamp how many there are, and one more than when the
   case opened shows one line under the right end of the bar. Show it saves the turn in front of
   him first, as any move does, then reads the case again on that turn. Nothing moves before. */
const ES_STAMP = { path: null, count: null, ask: 0, last: null };

async function esStampTick() {
  if (!S.data || $('work').hidden || document.hidden) return;
  const path = S.data.path;
  const ask = ++ES_STAMP.ask;
  let data;
  try {
    data = await api('/api/stamp', { workbook: path });
  } catch { return; }
  if (ask !== ES_STAMP.ask || !S.data || S.data.path !== path || !data.turns) return;
  await esStepTake(path, data.workbook);
  const n = Number(data.turns.count) || 0;
  if (ES_STAMP.path !== path || ES_STAMP.count === null) { Object.assign(ES_STAMP, { path, count: n }); return; }
  if (n > ES_STAMP.count && data.turns.last) {
    ES_STAMP.last = data.turns.last;
    $('es-outside-line').textContent = t('distil.stamp.outside', { n: n - ES_STAMP.count });
    $('es-outside').hidden = false;
  }
}

/* Two windows in step (20 October, Adam's way C, for two screens): the workbook's time, from the same
   stamp, and when a window of this app has written it since, a passage's statements, notes or quotes
   reworded in the other window or on a board, the case is read again where it stands, the current passage
   and the place in the column kept, and each statement that changed takes a brief wash of the crux orange
   that fades, as a quote's does. Nothing to press, and nothing moves while a field here holds words
   not yet saved: the next look takes it once they are. A change from outside the app keeps its notice. */
const ES_STEP = { path: null, at: null, busy: false };
const ES_STEP_EVERY = 4 * 1000;

async function esStepTake(path, wb) {
  if (!wb || !wb.at) return;
  if (ES_STEP.path !== path || ES_STEP.at === null) { Object.assign(ES_STEP, { path, at: wb.at }); return; }
  if (wb.at === ES_STEP.at || ES_STEP.busy) return;
  if (!wb.here) { ES_STEP.at = wb.at; return; }
  if (S.dirty || S.editing || S.timeEdit || S.note || S.quoting || anyOverlayOpen()) return;
  ES_STEP.busy = true;
  try {
    let data;
    try { data = await api('/api/open', { path }); } catch { return; }
    if (!S.data || S.data.path !== path || S.dirty || S.editing || S.timeEdit || S.note) return;
    ES_STEP.at = wb.at;
    const sig = (r) => JSON.stringify([r.v || '', r.runs || null, r.name || '', r.time || ''].concat(r.v ? [] : [r.es || '', r.en || '', r.kq || '']));
    const before = new Map(S.flat.map((r) => [r.key, sig(r)]));
    const was = new Map(S.flat.map((r) => [r.key, r]));
    const changed = [];
    for (const sheet of data.sheets || []) for (const r of sheet.rows || []) {
      const key = `${r.sheet}:${r.row}`;
      if (before.get(key) !== sig(r)) changed.push({ key, was: was.get(key) || null });
    }
    if (!changed.length && S.flat.length === before.size) return;
    const row = current();
    const col = $('transcript');
    const top = col.scrollTop;
    startCase(data, { land: row ? { sheet: row.sheet, row: row.row } : { sheet: '', row: 0 } });
    col.scrollTop = top;
    requestAnimationFrame(() => { col.scrollTop = top; });
    esStepWash(changed);
  } finally { ES_STEP.busy = false; }
}

// what came in from the other window, washed for a moment: each statement that changed, alone, as the
// drawing has it, and a passage's notes only when the notes themselves changed
function esStepWash(changed) {
  const wash = (el) => {
    if (!el) return;
    el.classList.remove('came-in');
    void el.offsetWidth;
    el.classList.add('came-in');
    setTimeout(() => el.classList.remove('came-in'), 2200);
  };
  const byKey = new Map(changed.map((c) => [c.key, c.was]));
  for (const r of S.flat) {
    if (!byKey.has(r.key) || !r.stop) continue;
    const old = byKey.get(r.key);
    const el = $('transcript-rows').querySelector(`.turn[data-i="${r.i}"]`);
    if (!el) continue;
    const now = rowPairs(r);
    const then = old ? rowPairs(old) : [];
    const cards = [...el.querySelectorAll(':scope > .turn-es .pair')];
    now.forEach((p, n) => {
      const t = then[n];
      if (t && t.es === p.es && t.kq === p.kq) return;
      if (!p.es.trim() && !p.kq.trim()) return;
      const go = el.querySelector(`:scope > .turn-es .es-go[data-es="${n}"]`);
      wash(go ? go.closest('li') : (cards[n] && cards[n].querySelector('.pair-es')));
    });
    if ((old ? old.en || '' : '') !== (r.en || '') && (r.en || '').trim()) wash(el.querySelector(':scope > .turn-notes'));
  }
}

/* A case newly open starts the count from what its file holds now. */
function esStampStart() {
  Object.assign(ES_STEP, { path: S.data ? S.data.path : null, at: null });
  Object.assign(ES_STAMP, { path: S.data ? S.data.path : null, count: null, last: null });
  $('es-outside').hidden = true;
  esStampTick();
}

async function esOutsideShow() {
  const last = ES_STAMP.last;
  $('es-outside').hidden = true;
  if (!S.data || !last) return;
  if (S.dirty && current()) {
    await commit(current(), false);
    if (S.dirty) return;
  }
  try {
    const data = await api('/api/open', { path: S.data.path });
    startCase(data, { land: { sheet: last.sheet, row: last.row } });
    esStampStart();
  } catch (err) { say(err.message, 9000); }
}

function esOutsideClose() {
  $('es-outside').hidden = true;
  ES_STAMP.count = null;
  esStampTick();
}

/* ── wiring, Idiograph's part ── */

/* The guidance, a sheet over the right of the screen (16 October, Adam's decision on a tester's
   feedback, where until then it was a rail with a column of its own and a slim tab once put away):
   closed by default, so the notes stand beside the transcript at a desk width, it opens from the
   bar's Guidance tool or `g` and closes from its own close button, the same tool, `g`, Esc or a click
   outside it. Open or closed is kept in the browser, so a reload opens it the way he left it, and
   anything but `open`, nothing kept or the rail's old `away` and `here`, reads as closed. */
const GUIDE_KEY = 'idiograph-guide';

function guideStored() {
  try { return localStorage.getItem(GUIDE_KEY) === 'open'; } catch { return false; }
}

const guideOpen = () => $('guide').classList.contains('open');

/* `how.keep` keeps the choice, as every press does and the page's start does not, and `how.focus`
   takes the keyboard into the sheet as it opens and back to the bar's tool as it closes. A sheet
   closed with the focus inside it always hands the focus back to the tool, so it is never lost. */
/* The guidance's lines, each with its two examples behind a small arrow at its end, opened in place
   in two columns, Less this and More this (Adam, 21 October). One stands open at a time, and a line
   with no examples in guidance.md has no arrow. The arrow is a button, so Enter and Space open it. */
const RULE_CHEVRON = '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M4.5 6.5 8 10l3.5-3.5" '
  + 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function drawRules(lines, examples) {
  $('rules').innerHTML = lines.map((line, i) => {
    const ex = examples[i];
    if (!ex || !ex.less || !ex.more) return `<li><span class="rule-text">${esc(line)}</span></li>`;
    return `<li><span class="rule-text">${esc(line)}</span>`
      + `<button type="button" class="rule-ex-open" aria-expanded="false" aria-controls="rule-ex-${i}" `
      + `aria-label="${escAttr(t('distil.rules.examples'))}" title="${escAttr(t('distil.rules.examples'))}">${RULE_CHEVRON}</button>`
      + `<div class="rule-ex" id="rule-ex-${i}" hidden>`
      + `<div class="rule-ex-side"><span class="rule-ex-head">${esc(t('distil.rules.less'))}</span><span class="rule-ex-text">${esc(ex.less)}</span></div>`
      + `<div class="rule-ex-side"><span class="rule-ex-head">${esc(t('distil.rules.more'))}</span><span class="rule-ex-text">${esc(ex.more)}</span></div>`
      + '</div></li>';
  }).join('');
}

function ruleExamples(button) {
  const open = button.getAttribute('aria-expanded') !== 'true';
  for (const other of $('rules').querySelectorAll('.rule-ex-open')) {
    const shown = open && other === button;
    other.setAttribute('aria-expanded', String(shown));
    $(other.getAttribute('aria-controls')).hidden = !shown;
  }
}

/* The rail of the project in front, IPA's from guidance.md or a thematic analysis project's from ta_guidance.md
   (tarail, 3 November 2026), drawn again only when the method changes: its lines and their examples, the framing
   under the list, and the craft prompts the first field shows one of. A server from before tarail sends no TA
   rail, and its Guidance tool then stands hidden in a TA project, as it did before. */
function guideRail() {
  if (!S.rails) return;
  const method = typeof tMethodNow === 'function' && tMethodNow() === 'ta' ? 'ta' : 'ipa';
  const rail = S.rails[method];
  $('btn-guide').hidden = !rail;
  if (!rail) { if (guideOpen()) guide(false); return; }
  $('guide-examples').hidden = method === 'ta';
  if (S.railDrawn === method) return;
  S.railDrawn = method;
  S.guidanceLines = rail.lines;
  S.prompts = rail.prompts || [];
  drawRules(rail.lines, rail.examples || []);
  // Adam's framing under the list, from the guidance file, none from a server too old to send it
  $('rules-framing').textContent = rail.framing || '';
  $('rules-framing').hidden = !rail.framing;
  if ($('work').hidden) return;
  S.prompt = placeholderLine();
  const first = pairEls()[0];
  if (first && first.querySelector('.pair-es').value === '') first.querySelector('.pair-es').placeholder = S.prompt;
}

function guide(open, how = {}) {
  // a thematic analysis project's rail from a server that sends none (tarail)
  if (typeof S !== 'undefined' && S.rails && !S.rails[typeof tMethodNow === 'function' && tMethodNow() === 'ta' ? 'ta' : 'ipa']) open = false;
  const inside = $('guide').contains(document.activeElement);
  $('guide').classList.toggle('open', open);
  $('btn-guide').setAttribute('aria-expanded', String(open));
  if (how.keep) {
    try { localStorage.setItem(GUIDE_KEY, open ? 'open' : 'closed'); } catch { /* private window */ }
  }
  if (open && how.focus) $('guide-close').focus({ preventScroll: true });
  if (!open && (how.focus || inside)) $('btn-guide').focus({ preventScroll: true });
}

const toggleGuide = (focus) => guide(!guideOpen(), { keep: true, focus });

/* Idiograph's screen's title, for pageTitle: the app, the project from the bar's path, the participant as the
   screens name them, "P2 Wren" (caseShown, so the dash that joins the number to the name is not read as a
   separator), then the screen (headroom, 6 November 2026). The GETs and LGETs are the project's, so they name no
   participant, a participant's LPETs do. */
function distilTitle() {
  const shown = titleShown;
  const text = titleText;
  const app = APP_NAME;
  // the case by its label, as PETs names it, never the workbook's name (17 October, the third Tauri build)
  if (shown('work')) return titled(app, text('rail-project'), caseShown((S.data && S.data.case) || text('rail-case')), t('distil.title.statements'));
  if (shown('themes')) {
    const gets = typeof TH !== 'undefined' && TH.mode === 'gets';
    const project = text('th-project') || (typeof TH !== 'undefined' && TH.project && TH.project.name) || '';
    const who = caseShown(($('th-case').dataset || {}).label || text('th-case'));
    if (gets && TH.lpets) return titled(app, project, who, t('distil.title.lpets'));
    if (gets) return titled(app, project, TH.lgets ? t('distil.title.lgets') : t('distil.title.gets'));
    return titled(app, project, who, t('distil.title.pets'));
  }
  if (shown('traj')) return titled(app, text('tj-project'), t('distil.title.trajectories'));
  if (shown('codes-screen')) return titled(app, text('cd-project'), t('codes.tab'));
  if (shown('library') && shown('home-project') && text('hp-name')) return titled(app, text('hp-name'));
  return null;
}

/* Idiograph's part of the page wired, its statements screen's controls and keys, its cards, its Home's and its
   parts of Settings (the family codebase's fifth build, 23 October 2026: until then app.js's boot) */
function distilBoot() {
  // on Linux, the two places of this screen where a Tab with Orca on ended WebKitGTK's page (axGuard, orcacrash):
  // after the statements' group, past its quote's arrow and its bin, and inside Columns, the last of its group
  axGuard($('pairs'));
  axGuard($('cols-pick'), true);
  guide(guideStored());
  drawBand();
  if (window.ResizeObserver) new ResizeObserver(() => measureBand()).observe($('band'));
  // the columns measured again whenever the transcript's box changes, a scrollbar coming or going
  // among them, and the fields of the card and the notes taking their heights at the new width
  if (window.ResizeObserver) {
    new ResizeObserver(() => {
      if ($('work').hidden) return;
      measureColumns();
      growPairs();
      growNotes();
      // the field holding the caret, or the passage, back where it stood before the new size
      keepView();
      footStuck();
    }).observe($('transcript'));
    // the card growing or shrinking with its pairs, or taken into its row or back to the park, and the stacked
    // column's upper half changing height as the divider moves (18 October)
    new ResizeObserver(() => footStuck()).observe($('es-card'));
    new ResizeObserver(() => footStuck()).observe($('stack-es'));
    // the notes' half fades at an edge with more beyond it, as the statements' does (21 October)
    new ResizeObserver(() => stackFade()).observe($('stack-en'));
  }
  $('transcript').addEventListener('scroll', footStuck, { passive: true });
  // a long passage's words or its held card scrolling inside themselves (cardlarge)
  $('transcript').addEventListener('scroll', (e) => reachFade(e.target), { passive: true, capture: true });
  $('es-card').addEventListener('scroll', footStuck, { passive: true });
  // what stands in view, taken as he scrolls, moves the caret and types, for a resize to keep (see keepView)
  $('transcript').addEventListener('scroll', viewAnchor, { passive: true });
  document.addEventListener('focusin', () => requestAnimationFrame(viewAnchor));
  $('transcript').addEventListener('input', () => requestAnimationFrame(viewAnchor));

  // the statements screen's guidance, Idiograph's alone
  $('rules').addEventListener('click', (e) => {
    const button = e.target.closest && e.target.closest('.rule-ex-open');
    if (button) ruleExamples(button);
  });
  if (APP === 'idiograph') api('/api/guidance').then((data) => {
    S.promptDefault = data.prompt_default || '';
    // IPA's rail and a thematic analysis project's, ta_guidance.md's, none from a server too old to send it (tarail)
    S.rails = { ipa: data, ta: data.ta || null };
    S.railDrawn = null;
    guideRail();
  }).catch(() => {});

  // the project's name in every screen's band, opening its card's menu on Home (option D of the bars, 6 November
  // 2026), and the statements screen's own toolbar under the band (barsD)
  pathMenuBoot();
  esToolsBoot();
  // the browser's Back and Forward on Distil's screens, and where the page starts in its history
  NAV.cur = navHeld();
  if (NAV.cur) { NAV.seen.set(NAV.cur.n, NAV.cur); NAV.seq = Math.max(NAV.seq, NAV.cur.n); }
  window.addEventListener('popstate', navPop);
  $('sheet-switch').onchange = () => toSheet($('sheet-switch').value);
  tpPickWire();
  esWhoWire();
  $('btn-commit').onclick = () => pressAct();
  $('stale-reload').onclick = () => staleReload();
  $('stale-overwrite').onclick = () => staleOverwrite();
  $('stale-back').onclick = () => staleBack();
  // the columns' grips and Columns over them (17 October), where Previous and Quote under the fields
  // stood until then: a click on a passage moves, and a quote comes from the toolbar by the words
  $('cols-head').addEventListener('pointerdown', colGripDown);
  $('cols-head').addEventListener('keydown', colGripKeys);
  // and since 21 October the lower column's heading in a stack, a grip's click opening the heading's menu
  for (const h of document.querySelectorAll('#stack .stack-head')) h.insertAdjacentHTML('afterbegin', gripHtml(COLUMN_WORDS[h.dataset.col]));
  $('stack').addEventListener('pointerdown', colGripDown);
  $('stack').addEventListener('keydown', colGripKeys);
  for (const id of ['cols-head', 'stack']) {
    $(id).addEventListener('click', colGripClick);
    $(id).addEventListener('contextmenu', colHeadContext);
  }
  $('col-menu').addEventListener('click', (e) => { const b = e.target.closest('[data-act]'); if (b) colMenuChoose(b.dataset.act); });
  $('col-menu').addEventListener('keydown', colMenuKeys);
  // a press from the keyboard, a click with no pointer's count, puts the focus on the menu's first tick
  $('cols-pick').onclick = (e) => colsMenu($('cols-menu').hidden, e.detail === 0);
  // the menu's ticks and its two choices, each drawn at once and kept, the menu staying open and placed
  // again under Columns, since the last heading may have changed (18 October)
  $('cols-menu').addEventListener('change', (e) => {
    const t = e.target;
    if (t.type === 'checkbox') setView('columns_hidden', colsTicked($('cols-show-statements'), $('cols-show-notes')));
    else if (t.name === 'cols-stack' && t.checked) setView('columns_stacked', t.value === 'stacked');
    colsMenuPlace();
  });
  $('cols-menu').addEventListener('keydown', colsMenuKeys);
  $('cols-book').onclick = () => colsBookOrder();
  // the column edges, dragged, moved by the arrows or put back by a double click, and Reset widths in
  // Columns' menu and Settings (20 October)
  $('col-edges').addEventListener('pointerdown', edgeDown);
  $('col-edges').addEventListener('dblclick', edgeBack);
  $('col-edges').addEventListener('keydown', edgeKeys);
  $('cols-widths').onclick = () => { widthsReset(); $('cols-pick').focus(); };
  $('set-widths-reset').onclick = () => widthsReset();
  $('view-set').addEventListener('change', () => colsSetTicked());
  // the divider between the statements and the notes stacked, by the pointer and by the keyboard
  $('stack-divider').addEventListener('pointerdown', stackDividerDown);
  $('stack-divider').addEventListener('keydown', stackDividerKeys);
  $('stack-divider').ondblclick = () => stackSplitKeep(STACK_SPLIT);
  $('stack-es').addEventListener('scroll', footStuck, { passive: true });
  $('stack-en').addEventListener('scroll', stackFade, { passive: true });
  // across 800px the notes stacked under the statements go under the words, and come back, as today's rules
  // have it for whatever is shown
  if (typeof matchMedia === 'function') {
    matchMedia('(max-width: 800px)').addEventListener('change', () => {
      if (!S.layout) return;
      cellsAgain();
      placeCard();
      placeNotes();
      measureColumns();
    });
  }
  $('btn-ai').onclick = () => askAI();
  // Put away takes the answer down and brings the button back, so a second press asks afresh
  $('ai-close').onclick = () => resetAI();
  $('btn-prompt-reset').onclick = () => {
    if (S.promptDefault) { $('set-prompt').value = S.promptDefault; saidIn('key-said', ''); }
    else saidIn('key-said', RESTART_LINE);
  };
  $('ai-candidates').addEventListener('click', (e) => {
    const pick = e.target.closest('[data-cand]');
    if (pick) takeCandidate(Number(pick.dataset.cand));
  });
  $('btn-help').onclick = () => openHelp();
  // and the statements screen's shortcuts card each key as this machine names it, Cmd or Ctrl, where
  // it said "Cmd / Ctrl" beside a line saying one of them (17 October)
  for (const el of document.querySelectorAll('#help .keys td.mono')) el.textContent = keyName(el.textContent);
  // find and replace: the card's controls and its own keys, opened by Cmd + Shift + F and by Replace in
  // the transcript under a This case search, the bar's magnifier being Search's since 17 October
  // (search.js). Find counts as it is typed, a breath after the last key
  $('find-text').addEventListener('input', () => {
    S.lastInput['find-text'] = Date.now();
    clearTimeout(FIND.timer);
    FIND.timer = setTimeout(() => { findRefresh('near'); findScroll(); }, 160);
  });
  $('find-with').addEventListener('input', () => { S.lastInput['find-with'] = Date.now(); });
  for (const id of ['find-word', 'find-case']) {
    $(id).addEventListener('change', () => { findRefresh('near'); findScroll(); });
  }
  $('find-prev').onclick = () => findStep(-1);
  $('find-next').onclick = () => findStep(1);
  $('find-one').onclick = () => findReplace(false);
  $('find-all').onclick = () => findReplace(true);
  $('find-cancel').onclick = () => closeFind();
  window.addEventListener('resize', () => { if (findOpen()) findRoom(); });
  // the columns' headings, the guidance's room and the count's place follow the window
  window.addEventListener('resize', () => { if (!$('work').hidden) measureColumns(); });
  // Enter in Find is Next and with Shift Previous, Enter in Replace with replaces the one in focus,
  // and Esc closes the card. Cmd + Enter stops here, so it never presses Next on the turn behind
  $('find').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeFind(); return; }
    if (e.key !== 'Enter') return;
    if (MOD(e)) { e.preventDefault(); e.stopPropagation(); return; }
    if (e.target === $('find-text')) { e.preventDefault(); e.stopPropagation(); findStep(e.shiftKey ? -1 : 1); return; }
    if (e.target === $('find-with')) { e.preventDefault(); e.stopPropagation(); findReplace(false); }
  });
  // Send feedback from the turn screen's bug, and from the home screen's, which says project on a
  // project's page: the PETs and GETs bar's says pets or gets, in themes.js
  $('btn-feedback').onclick = () => openFeedback('statements');
  // the tabs on the statements bar, Experiential statements the screen in front of him (20 October)
  $('es-step-pets').onclick = () => esStep('pets');
  $('es-step-gets').onclick = () => esStep('gets');
  $('es-step-lpets').onclick = () => esStep('lpets');
  $('es-step-lgets').onclick = () => esStep('lgets');
  $('es-step-trajectories').onclick = () => esStep('trajectories');
  $('es-step-codes').onclick = () => esStep('codes');
  $('help-close').onclick = () => hide('help');
  $('btn-settings').onclick = () => openSettings();
  // the statement length a word fewer or more, saved for the project shown in Project settings
  $('words-n').addEventListener('input', (e) => wordsSet(e.target.value));
  $('words-n').addEventListener('change', (e) => wordsSet(e.target.value, true));
  // the round's two fields show only while Work in rounds is ticked, and Celebrations' line follows it
  $('set-rounds').onchange = () => {
    $('rounds-fields').hidden = !$('set-rounds').checked;
    $('cheer-line').textContent = cheerLine($('set-rounds').checked);
  };
  // a nudge's tooltip, under its row or over it, as the room in the column allows
  for (const kind of ['mouseover', 'focusin']) $('nudge-switches').addEventListener(kind, placeTip);
  $('btn-bench').onclick = () => runBench();
  $('bench-close').onclick = () => closeBench();
  $('btn-bench-reset').onclick = () => loadSample(true);
  $('create-cancel').onclick = () => hide('create');
  // Rename's card: the list asked again as the name is typed and as the tick changes, Enter in the
  // field presses Rename, and Cancel and Esc change nothing
  // Share a copy's card: each choice and tick draws the card again
  $('sc-cancel').onclick = () => scShut();
  $('sc-go').onclick = () => scGo();
  $('share-card').addEventListener('change', () => { scSaid(''); scDraw(); });
  // Export as REFI-QDA's card, the same way
  $('qx-cancel').onclick = () => qxShut();
  $('qx-go').onclick = () => qxGo();
  $('qdpx-card').addEventListener('change', () => { qxSaid(''); qxDraw(); });
  $('rn-cancel').onclick = () => hide('rename');
  $('rn-go').onclick = () => rnGo();
  $('rn-name').addEventListener('input', rnTyped);
  $('rn-name').addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); rnGo(); } });
  $('rn-folder').addEventListener('change', () => { rnSaid(''); rnPlan(); });
  $('import-cancel').onclick = () => hide('import');
  // the recording's offset, from the button beside its name under the player
  $('player-offset').onclick = () => openOffset();
  $('offset-cancel').onclick = () => hide('offset');
  $('offset-go').onclick = () => saveOffset();
  $('offset-seconds').addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); saveOffset(); } });
  $('import-go').onclick = () => makeImport();
  // a speaker's role, the times' format, the frame rate, the recording and its offset each read the file again
  $('import-speakers').addEventListener('change', () => { drawImportAs(); readImport(); });
  $('import-time').onchange = () => readImport();
  $('import-tp').onchange = () => readImport();
  $('import-fps').onchange = () => readImport();
  $('import-audio').onchange = () => { IMPORT.audio = $('import-audio').value; readImport(); };
  $('import-offset').onchange = () => readImport();
  $('import-audio-pick').onclick = () => pickImportAudio();
  // a preview's fades follow its sideways scroll, which never bubbles, and the window's width
  document.addEventListener('scroll', (e) => { if (e.target.matches && e.target.matches('.import-fade > .import-preview')) importFade(e.target); }, true);
  window.addEventListener('resize', importFades);
  $('import-map').addEventListener('change', (e) => { if (e.target.matches('select[data-col]')) readImport(); });
  // New project: its card, the folder chosen or typed, the files dropped anywhere on it or chosen,
  // and its rows
  $('np-open').onclick = () => openNewProject();
  $('np-cancel').onclick = () => closeNewProject();
  $('np-go').onclick = () => npMake();
  $('np-method').onclick = (e) => {
    const b = e.target.closest('[data-method]');
    if (b && !b.disabled) npMethodSet(b.dataset.method, false);
  };
  $('np-choose').onclick = () => npFolder();
  const npTyped = () => {
    const typed = $('np-folder').value.trim();
    if (typed && typed !== NP.folder) npFolder(typed);
  };
  $('np-folder').addEventListener('change', npTyped);
  $('np-folder').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); npTyped(); } });
  $('np-pick').onclick = () => $('np-files').click();
  $('np-files').onchange = () => { npAdd($('np-files').files); $('np-files').value = ''; };
  $('np-rows').addEventListener('input', npInput);
  $('np-rows').addEventListener('change', npChange);
  $('np-rows').addEventListener('click', npClick);
  $('np-rows').addEventListener('focusout', () => setTimeout(npNumbersDraw, 0));
  $('np-qdpx').addEventListener('input', qdInput);
  $('np-qdpx').addEventListener('change', qdChange);
  $('np-qdpx').addEventListener('click', qdClick);
  // the names' Review card and Names to replace (namesui)
  nmWire();
  // the home screen: Open project folder, its typed field off a Mac, Settings at its head on
  // General, a project page's way back and the demo's Reset demo
  $('add-project-home').onclick = () => openFolderPress();
  $('add-home-go').onclick = () => addFromHome($('add-home-path').value.trim());
  $('add-home-path').onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); addFromHome($('add-home-path').value.trim()); } };
  // Open a shared copy, and off a Mac in a browser its file chosen and the folder typed
  $('sent-open').onclick = () => openSentPress();
  $('sent-file').onchange = () => sentChosen();
  $('sent-go').onclick = () => sentGo();
  $('sent-into').onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); sentGo(); } };
  // its card for a copy coming back: the name typed asks the dry run again, each choice and tick draws it again
  $('cb-who').addEventListener('input', cbTyped);
  $('cb-add').addEventListener('change', () => { cbSaid(''); cbDraw(); });
  $('cb-own').addEventListener('change', () => { cbSaid(''); cbDraw(); });
  $('cb-below').addEventListener('change', cbTick);
  $('cb-cancel').onclick = () => cbShut();
  $('cb-go').onclick = () => cbGo();
  // the project page's way back is Back, where the page has its entry, so the two never part
  $('hp-back').onclick = () => { if (!navBackNow()) closePage(); };
  // the bars' lockup is Home, as Fusion's mark is, from every screen (20 October), and the path's Home, its first step
  // since option C of the bars (26 October 2026), is gone since option D (6 November 2026), the two doing one thing
  for (const id of ['es-home', 'th-home']) $(id).onclick = () => goHome();
  window.addEventListener('keydown', (e) => {
    if (APP !== 'idiograph' || !HOME_KEY_PRESSED(e) || anyOverlayOpen()) return;
    e.preventDefault();
    e.stopPropagation();
    goHome();
  }, true);
  $('demo-reset').onclick = () => resetDemo();
  window.addEventListener('dragenter', npDrag);
  window.addEventListener('dragover', npDrag);
  window.addEventListener('dragleave', npDragEnd);
  window.addEventListener('dragend', npDragEnd);
  window.addEventListener('drop', npDrop);
  // View on the bar opens its menu, and each of its rows draws its choice at once and keeps it. A
  // press anywhere off the menu and its button shuts it
  // and opened from the keyboard its first row takes the focus, the arrows walk it, Esc gives View the focus back and
  // Tab shuts it and goes on from View, the menu's keys (a11yfix)
  $('btn-view').onclick = (e) => {
    const open = $('view-menu').hidden;
    viewMenu(open);
    if (open && e.detail === 0) menuFirst($('view-menu'));
  };
  menuRoles($('view-menu'));
  $('view-menu').addEventListener('keydown', (e) => {
    const back = () => { viewMenu(false); $('btn-view').focus(); };
    if (menuKeys(e, $('view-menu'), back)) return;
    if (e.key === 'Tab') back();
  });
  $('view-menu').addEventListener('change', (e) => {
    if (e.target.id === 'view-larger') setView('larger_passage', $('view-larger').checked);
    else if (e.target.name === 'view-minimap' && e.target.checked) minimapChoose(e.target.value);
  });
  // the minimap: a press moves the column there and a drag scrolls it, a passage under the pointer
  // names itself in a tip, the wheel over the card scrolls the column, its button shows or hides it,
  // its box follows every scroll, a scroll wakes it in Auto, and it is drawn again whenever the
  // column, its rows or the card change size
  $('minimap-area').addEventListener('pointerdown', minimapDown);
  $('minimap-area').addEventListener('pointermove', minimapMove);
  $('minimap-area').addEventListener('pointerup', minimapUp);
  $('minimap-area').addEventListener('pointercancel', minimapUp);
  $('minimap-area').addEventListener('lostpointercapture', minimapUp);
  $('minimap-area').addEventListener('pointerleave', () => minimapTip(null));
  // the card keeps its place under his hand, and gives way once the pointer leaves, a field taking the
  // focus or giving it up looked at again with it
  $('minimap').addEventListener('pointerenter', () => { S.mmOver = true; });
  $('minimap').addEventListener('pointerleave', minimapLeave);
  document.addEventListener('focusin', () => scheduleMinimap());
  document.addEventListener('focusout', () => scheduleMinimap());
  $('minimap').addEventListener('mousedown', (e) => e.preventDefault());
  $('minimap').addEventListener('wheel', minimapWheel, { passive: false });
  $('minimap-btn').addEventListener('click', () => minimapToggle());
  // the status bar's Minimap and Quotes (21 October), which keep the focus and a selection where they are
  for (const id of ['es-map-btn', 'es-quotes-btn']) $(id).addEventListener('pointerdown', (e) => e.preventDefault());
  $('es-map-btn').addEventListener('click', () => minimapToggle());
  $('es-quotes-btn').addEventListener('click', () => quotesToggle());
  $('transcript').addEventListener('scroll', drawMinimapView, { passive: true });
  $('transcript').addEventListener('scroll', minimapScrolled, { passive: true });
  if (window.ResizeObserver) {
    const sized = new ResizeObserver(() => scheduleMinimap());
    for (const id of ['transcript', 'transcript-rows', 'minimap']) sized.observe($(id));
  }
  document.addEventListener('pointerdown', (e) => {
    if (!$('view-menu').hidden && !e.target.closest('#view-menu, #btn-view')) viewMenu(false);
    if (!$('cols-menu').hidden && !e.target.closest('#cols-menu, #cols-pick')) colsMenu(false);
    if (S.colMenu && !e.target.closest('#col-menu') && e.target !== S.colMenu.grip && !S.colMenu.grip.contains(e.target)) colMenuClose();
  }, true);
  // the guidance's sheet: the bar's tool opens and closes it, its close button closes it, and a press
  // anywhere outside it closes it and goes on to do what it does
  $('btn-guide').onclick = () => toggleGuide(true);
  $('guide-close').onclick = () => guide(false, { keep: true, focus: true });
  document.addEventListener('pointerdown', (e) => {
    if (guideOpen() && !$('work').hidden && !e.target.closest('#guide, #btn-guide')) guide(false, { keep: true });
  }, true);
  // the link in the line that says there is no question yet opens Settings on Project
  $('band').addEventListener('click', (e) => { if (e.target.closest('.band-link')) openProjectSettings(project()); });
  $('gravity-only').onchange = () => loadExamples();
  // Every row answers a plain click, the margin and the text alike. One of her turns goes to that
  // turn. One of Adam's leaves the turn being worked on where it is and cues the recording there,
  // carrying on from the new place if it was playing, and opens the interviewer note on it. The timecode keeps playing from there, a
  // double-click on it corrects it, and the small control beside it opens the row's menu.
  //
  // A click that selected or extended text, a click that travelled far enough to be a drag, and a
  // click with Cmd, Ctrl, Shift or Alt held all pass straight through, because the text has to
  // stay free to select for a quote, built from one piece or several.
  $('transcript').addEventListener('click', (e) => {
    // the row's menu keeps its own click, and any other click in the column takes it away first
    if (e.target.closest('.row-menu')) return;
    // a turn open for correction keeps every click inside its box: nothing navigates, nothing is
    // re-centred, nothing is redrawn under it and the caret stays where he put it
    if (e.target.closest('.turn-edit')) return;
    // and so does a timecode open for correction in the margin
    if (e.target.closest('.time-edit')) return;
    // the current passage's card and an interviewer note open beside his passage keep their own
    // clicks, their fields and their buttons (17 October)
    if (e.target.closest('#es-card, #note-entry')) return;
    closeRowMenu();
    closeTimeEdit();
    // the notes beside the passage being worked on are its notes field: a click there is the
    // field's, and anywhere else in their column puts the caret in it (16 October)
    if (e.target.closest('.turn.current .turn-notes')) { if (e.target !== $('en')) $('en').focus(); return; }
    // the small control in the margin opens the row's menu under it. The click that opens it stops
    // here, or the page's own close on a click outside the menu would take it straight away again
    const opener = e.target.closest('[data-menu]');
    if (opener) {
      e.stopPropagation();
      const row = S.flat[Number(opener.dataset.menu)];
      const box = opener.getBoundingClientRect();
      if (row) openRowMenu(row, { pick: assignSelection(), at: { x: box.left, y: box.bottom } });
      return;
    }
    // the second click of a double-click on the timecode belongs to the box it opens: the first
    // has already played from here, and the player is left exactly as that click left it
    const seek = e.target.closest('[data-seek]');
    if (seek) { if (e.detail < 2) playFrom(Number(seek.dataset.seek)); return; }
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (pressMoved(e) || selectionLive()) return;
    // a round's marker goes to its first open turn, or its first turn, and never flashes the count
    const marker = e.target.closest('.round-mark');
    if (marker) { toRound(Number(marker.dataset.round)); return; }
    const el = e.target.closest('.turn');
    const row = el ? S.flat[Number(el.dataset.i)] : null;
    if (!row) return;
    // a plain click on a quote's mark brings its statement forward, on another passage after the
    // move there (16 October). The second click of a double-click is left alone, because that one
    // belongs to the editor
    const quoted = e.detail >= 2 ? null : e.target.closest('.turn-text .kq');
    if (quoted && row.stop && quoted.dataset.kq !== undefined) { toStatement(row, Number(String(quoted.dataset.kq).split(' ')[0])); return; }
    // a piece of the quote of her passage next to this one brings that passage's statement forward (quotespan)
    if (quoted && row.stop && quoted.dataset.kqFar) {
      const [i, n] = quoted.dataset.kqFar.split(' ')[0].split(':').map(Number);
      if (S.flat[i] && S.flat[i].stop) { toStatement(S.flat[i], n); return; }
    }
    // a click on one of another passage's statements goes there with the caret in that statement, as a
    // quote's mark does (17 October)
    const said = e.target.closest('.turn-es .es-go');
    if (said && row.stop) { toStatement(row, Number(said.dataset.es)); return; }
    if (row.stop) {
      // the turn already being worked on is a target like any other: a click on it cues the
      // recording back to its timecode, carrying on if it was playing, before goTo re-centres.
      // goTo alone returns early on the current turn and so never reached the player.
      if (row.pos === S.at) cueAudio(row.seconds);
      // a click on to a later turn is a step on like Cmd + K, and flashes the count when it decides.
      // A click on another passage's notes goes there with the caret in them
      const toNotes = !!e.target.closest('.turn-notes');
      const went = goTo(row.pos, { count: true });
      if (toNotes) went.then(() => { if (!S.editing && !S.note && !guideHolds()) $('en').focus({ preventScroll: true }); });
      return;
    }
    cueAudio(row.seconds);
    markTurn(row.i);
    // and from item 140 one of the interviewer's own turns opens his note on it, in the notes column
    // beside it since 17 October, while the turn being worked on stays where it is
    if (noteable(row)) { openNote(row); return; }
    // the caret stays in the field it was in: a click in the column is not a move away from it
    if (!S.editing && pressFocus && isEntryField(pressFocus) && pressFocus.isConnected) pressFocus.focus();
  });
  // one menu for the whole row, on a right-click anywhere on it, the margin or the text. The words
  // selected in this turn are what it assigns. Shift keeps the browser's own menu.
  $('transcript').addEventListener('contextmenu', (e) => {
    if (e.shiftKey) return;
    // the notes field beside the current passage, its card and an interviewer note keep the browser's
    // own menu, as every field does
    if (e.target.closest('.turn-edit') || e.target.closest('.time-edit')
        || e.target.closest('.row-menu')
        || e.target.closest('.turn.current .turn-notes, #es-card, #note-entry')) return;
    const holder = e.target.closest('.turn');
    const row = holder ? S.flat[Number(holder.dataset.i)] : null;
    if (!row) return;
    e.preventDefault();
    const pick = assignSelection();
    const inThis = !!(pick && !pick.refuse && pick.row.i === row.i);
    openRowMenu(row, { pick: inThis ? pick : null, at: { x: e.clientX, y: e.clientY } });
  });
  // a click anywhere off the menu takes the menu away, and anywhere off a timecode open for
  // correction cancels it
  document.addEventListener('click', (e) => {
    // a click away from an interviewer note keeps it: anywhere but the field, its own row, the
    // player and the button that keeps it already, and never a click that selected words
    if (S.note && !e.target.closest('#note-entry, .turn.noting, #player-wrap, #btn-commit')
        && !selectionLive()) keepNote();
    if (S.rowMenu && !S.rowMenu.el.contains(e.target)) closeRowMenu();
    if (S.timeEdit && e.target !== S.timeEdit.field) closeTimeEdit();
  });
  $('assign-cancel').onclick = () => { S.assignPlan = null; hide('assign'); };
  $('assign-go').onclick = () => runAssignTurn();
  $('trim-cancel').onclick = () => { S.trimRow = null; hide('trim'); };
  $('trim-go').onclick = () => runTrim();
  // a piece of a quote is taken on mouse up, after the browser has settled the selection. The
  // playhead leaves the column alone while the drag is under way.
  $('transcript-rows').addEventListener('mousedown', (e) => {
    S.selecting = true;
    pressAt = { x: e.clientX, y: e.clientY };
    // a drag begun in a passage's words takes whole words as it goes (see snapDrag), never one in the
    // open box, the notes or the card, which are fields of their own
    S.dragWords = false;
    S.wordsPress = e.button === 0 && !!e.target.closest('.turn-text')
      && !e.target.closest('.turn-edit, .turn-notes, #es-card, #note-entry');
    const focus = document.activeElement;
    pressFocus = focus && isEntryField(focus) ? focus : null;
  });
  $('transcript-rows').addEventListener('mouseup', (e) => {
    // a right-click is the menu's, never a piece of a quote
    if (e.button !== 0) { S.selecting = false; return; }
    // and neither is a click in the menu itself, or in a timecode open for correction
    if (e.target.closest('.row-menu') || e.target.closest('.time-edit')) { S.selecting = false; return; }
    // selecting inside the open box is the box's own business, never a piece of a quote, and so is
    // selecting in the notes field beside the current passage, in its card or in an interviewer note
    if (e.target.closest('.turn-edit') || e.target.closest('.turn.current .turn-notes, #es-card, #note-entry')) { S.selecting = false; return; }
    const add = MAC ? e.metaKey : e.ctrlKey;
    // the word a double-click picks out belongs to the editor it opens, never to a quote
    if (e.detail >= 2) { S.selecting = false; return; }
    const held = e.metaKey || e.ctrlKey || e.shiftKey || e.altKey;
    const dragged = pressMoved(e);
    setTimeout(() => {
      // a drag takes whole words, so a quote never holds part of one
      if (dragged && S.wordsPress) snapDrag();
      S.wordsPress = false;
      S.dragWords = false;
      const took = takeSelection(add);
      // a plain click that leaves nothing selected clears the candidate and the pieces under it
      if (!took && !held && !dragged) clearPending(true);
      S.selecting = false;
      // and words selected in one of her passages bring the toolbar beside them
      selBarShow();
    }, 0);
  });
  // the toolbar by the selection keeps the selection and the focus as it is pressed, follows the words
  // as the column scrolls, and goes once nothing is selected in the column
  $('sel-bar').addEventListener('mousedown', (e) => e.preventDefault());
  $('sel-quote').onclick = () => commitQuote();
  $('sel-give').onclick = () => assignKey();
  $('transcript').addEventListener('scroll', () => { if (selBarOn()) selBarPlace(); }, { passive: true });
  window.addEventListener('resize', () => { if (selBarOn()) selBarPlace(); });
  document.addEventListener('selectionchange', () => {
    if (selBarOn() && !S.selecting && !selectionLive()) selBarHide();
    // while he drags over the words the selection is widened to whole words at every step
    if (S.selecting && S.dragWords) snapDrag();
    // the arrow beside each quote lit while words are selected in the passage (21 October)
    if (!$('work').hidden) pairTakeDraw();
  });
  document.addEventListener('mousemove', (e) => {
    if (S.selecting && S.wordsPress && !S.dragWords && (e.buttons & 1) && pressMoved(e)) {
      S.dragWords = true;
      snapDrag();
    }
  });
  // a double-click on the text of a turn opens it for correction, hers and Adam's alike, and a
  // double-click on its timecode opens that in the margin. The rest of the margin keeps its own
  // jobs, and the selection the browser made is dropped on the way in.
  $('transcript-rows').addEventListener('dblclick', (e) => {
    if (e.target.closest('.turn-edit') || e.target.closest('.time-edit')) return;
    const el = e.target.closest('.turn');
    const row = el ? S.flat[Number(el.dataset.i)] : null;
    if (!row) return;
    if (e.target.closest('.turn-gutter .time')) { e.preventDefault(); openTimeEdit(row); return; }
    if (!e.target.closest('.turn-text')) return;
    e.preventDefault();
    const sel = window.getSelection();
    if (sel) sel.removeAllRanges();
    openEditor(row);
  });
  // the player's own controls. Everything visible is drawn from the audio element's events, so a
  // cue or a seek from anywhere in the app shows here without being told.
  $('player-play').onclick = () => togglePlay();
  // five seconds either way, the buttons through the function the keys use
  $('player-back').onclick = () => nudgeAudio(-AUDIO_STEP);
  $('player-fwd').onclick = () => nudgeAudio(AUDIO_STEP);
  for (const ev of ['loadedmetadata', 'durationchange', 'timeupdate', 'seeked', 'play', 'pause', 'ended']) {
    $('player').addEventListener(ev, drawPlayer);
  }
  // the playhead mark, moved from the clock and from nothing else
  $('player').addEventListener('timeupdate', markListening);
  $('player').addEventListener('play', markListening);
  const scrub = $('player-scrub');
  const scrubEnd = (e) => {
    if (!S.scrubbing) return;
    S.scrubbing = false;
    try { scrub.releasePointerCapture(e.pointerId); } catch { /* the pointer is already gone */ }
  };
  scrub.addEventListener('pointerdown', (e) => {
    if (!$('player').getAttribute('src')) return;
    e.preventDefault();
    S.scrubbing = true;
    try { scrub.setPointerCapture(e.pointerId); } catch { /* capture is a nicety, not a need */ }
    scrubTo(e.clientX);
  });
  scrub.addEventListener('pointermove', (e) => { if (S.scrubbing) scrubTo(e.clientX); });
  scrub.addEventListener('pointerup', scrubEnd);
  scrub.addEventListener('pointercancel', scrubEnd);

  $('back-to-turn').onclick = () => { centreCurrent(true); focusEntry(); };
  // the count's flash and the bar's brightening each end by themselves, ready for the next
  $('count-flash').addEventListener('animationend', () => $('count-flash').classList.remove('on'));
  $('rail-turn').addEventListener('animationend', () => $('rail-turn').classList.remove('tick'));
  $('done-stop').onclick = () => stopHere();
  $('done-sheet').onclick = () => nextSheet();
  $('done-library').onclick = () => { hide('round-done'); toLibrary(); };
  // the phase complete: Mark complete on the case-complete card and in the bar, and the bar's line
  // once marked opens the card that reopens it
  $('done-mark').onclick = () => markComplete('mark');
  $('rail-markable').onclick = () => markComplete('mark');
  $('rail-mark').onclick = () => openComplete();
  $('complete-cancel').onclick = () => { hide('complete'); focusEntry(); };
  $('complete-reopen').onclick = () => reopenComplete();
  // GETs in Settings: the switch, the minimum's stepper, and each case's tick and reason
  $('set-min-down').onclick = () => getsMinStep(-1);
  $('set-min-up').onclick = () => getsMinStep(1);
  $('set-one-per-pet').onchange = () => { if (GETS_SET.now) GETS_SET.now.one = $('set-one-per-pet').checked; };
  $('gets-study').addEventListener('change', (e) => {
    const box = e.target.closest('[data-gstudy]');
    if (!box || !GETS_SET.now) return;
    const c = GETS_SET.now.study[Number(box.dataset.gstudy)];
    c.in = box.checked;
    GETS_SET.said = '';
    const inside = GETS_SET.now.study.filter((x) => x.in).length;
    if (GETS_SET.now.minimum !== null) GETS_SET.now.minimum = Math.max(1, Math.min(GETS_SET.now.minimum, Math.max(1, inside)));
    drawGetsPane();
    const why = $('gets-study').querySelector(`[data-gwhy="${box.dataset.gstudy}"]`);
    if (why) why.focus();
  });
  $('gets-study').addEventListener('input', (e) => {
    const why = e.target.closest('[data-gwhy]');
    if (why && GETS_SET.now) GETS_SET.now.study[Number(why.dataset.gwhy)].reason = why.value;
  });
  $('done-next').onclick = () => {
    hide('round-done');
    // a card shown on a move has already moved, so it only closes
    if (S.doneAdvance && stepTo(S.at, 1) < S.stops.length) { S.at = stepTo(S.at, 1); drawTurn(); }
    else focusEntry();
  };
  // Include interviewer notes, under Markdown and CSV in the PETs board's Export menu since settingsplit, off until
  // ticked and remembered in this browser
  $('export-notes').checked = exportNotesStored();
  $('export-notes').onchange = () => exportNotesSave($('export-notes').checked);

  $('en').addEventListener('input', () => {
    S.dirty = true;
    S.lastInput.en = Date.now();
    growNotes();
    drawAct();
  });
  // the pairs: a keystroke in either field, the count and the nudges of a statement, the pair
  // being worked on, Enter from field to field, Remove and Add another
  $('pairs').addEventListener('input', (e) => {
    const field = e.target;
    if (!isEntryField(field)) return;
    S.dirty = true;
    S.lastInput[field.id] = Date.now();
    growField(field);
    if (field.classList.contains('pair-es')) { pairCount(field.closest('.pair')); runNudges(); esCountDraw(); }
    else { markKeyQuotes(); pairsFoldDraw(); }
    drawAct();
  });
  // the arrow beside a quote keeps the selection as it is pressed (21 October)
  $('pairs').addEventListener('mousedown', (e) => { if (e.target.closest('.pair-take')) e.preventDefault(); });
  $('pairs').addEventListener('focusin', (e) => {
    const el = e.target.closest('.pair');
    if (el) S.pairFocus = el.dataset.pid;
    S.kqFocus = el && e.target.classList.contains('pair-kq') ? el.dataset.pid : null;
    lightMarks();
  });
  $('pairs').addEventListener('focusout', () => { S.kqFocus = null; lightMarks(); });
  $('pairs').addEventListener('mouseover', (e) => {
    const field = e.target.closest('.pair-kq');
    const pid = field ? field.closest('.pair').dataset.pid : null;
    if (pid !== S.kqHover) { S.kqHover = pid; lightMarks(); }
  });
  $('pairs').addEventListener('mouseleave', () => { S.kqHover = null; lightMarks(); });
  $('pairs').addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' || MOD(e) || e.altKey || e.isComposing || !isEntryField(e.target)) return;
    e.preventDefault();
    pairEnter(e.target);
  });
  $('pairs').addEventListener('click', (e) => {
    const remove = e.target.closest('[data-remove]');
    if (remove) removePair(remove.closest('.pair'));
    const take = e.target.closest('.pair-take');
    if (take) { pairTake(take.closest('.pair')); return; }
    const fold = e.target.closest('.pair-qtoggle, .pair-kq-line');
    if (fold) { const el = fold.closest('.pair'); quoteOpen(el, !quoteShown(el)); }
  });
  // in a thematic analysis project Add an extract takes the selected words, as Q does (codes)
  $('pair-add').onclick = () => (typeof cxOn === 'function' && cxOn() ? commitQuote() : addAnother());
  $('find-pair-list').addEventListener('click', (e) => {
    const go = e.target.closest('[data-pair-row]');
    if (go) openToPair(Number(go.dataset.pairRow));
  });

  // the interviewer note grows as it is typed into, and its keystrokes are told apart from the
  // app's own undo as the three fields' are
  $('note').addEventListener('input', () => { S.lastInput.note = Date.now(); grow($('note')); });

  document.addEventListener('visibilitychange', () => (document.hidden ? awayStart() : awayStop()));
  window.addEventListener('blur', awayStart);
  window.addEventListener('focus', awayStop);
  // a turn an agent wrote, asked about on a focus and every thirty seconds, and the guide for agents
  window.addEventListener('focus', esStampTick);
  // every few seconds, so a change in another window of this app shows here a moment later (20 October)
  setInterval(esStampTick, ES_STEP_EVERY);
  $('es-outside-show').onclick = () => esOutsideShow();
  $('es-outside-close').onclick = () => esOutsideClose();
  // an agent's action waiting for his yes, asked after every few seconds on the screens that show its line
  holdsBoot();
  // PET labels under Projects, saved at once
  $('set-labels').addEventListener('click', (e) => {
    const pick = e.target.closest('[data-labels]');
    if (pick) saveLabels(pick.dataset.labels);
  });
  // Timecodes under Projects, saved at once
  $('set-timecodes').addEventListener('click', (e) => {
    const pick = e.target.closest('[data-tc]');
    if (pick) saveTimecodes(pick.dataset.tc);
  });
  $('agents-guide').onclick = () => agentsGuide(false);
  $('agents-guide-update').onclick = () => agentsGuide(true);
  $('mcp-show').onclick = () => mcpShow();
  // Project settings: beside the project's name on its page, Save, its close
  $('hp-settings').onclick = () => openProjectSettings(HOME_PROJECTS.get(S.home) || (homeProject() || {}).project);
  $('projset-save').onclick = () => saveProjectSettings();
  $('projset-close').onclick = () => hide('projset');
  $('mcp-add').onclick = () => mcpAdd();
  $('mcp-copy').onclick = (e) => mcpCopy(e.currentTarget, 'mcp-entry');
  $('mcp-copy-line').onclick = (e) => mcpCopy(e.currentTarget, 'mcp-line');

  // the clock reads the time at the screen every second, so a blur stops it within one and a focus
  // starts it again. The glyph sets the current round's count to zero and leaves the others alone
  setInterval(drawClock, 1000);
  $('rail-clock-reset').onclick = () => { clockReset(); drawClock(); if (!$('work').hidden) focusEntry(); };

  window.addEventListener('beforeunload', (e) => {
    if (S.dirty || noteUnkept()) { e.preventDefault(); e.returnValue = ''; }
  });
}

/* Idiograph's keys, from the shell's one keydown (boot): Esc's first, before the panels go */
function distilKeysEscape(e) {
  // Share a copy's card over Home first, and Open a shared copy's, and the names' Review and list (namesui)
  if (scKeys(e) || qxKeys(e) || cbKeys(e) || phKeys(e) || nmKeys(e)) return true;
  // the turn-on card of Dangerously skip permissions over Settings, and an agent's action's card
  if (holdKeys(e)) return true;
  // Working together's cards and comment boxes (review.js)
  if (typeof rvwKeys === 'function' && rvwKeys(e)) return true;
  // the menus go first, then a timecode or a turn open for correction, then the quote
  // candidate, and only then the panels, the way back to the turn and leaving the field
  if (!$('view-menu').hidden) { e.preventDefault(); viewMenu(false); $('btn-view').focus(); return true; }
  if (!$('cols-menu').hidden) { e.preventDefault(); colsMenu(false); $('cols-pick').focus(); return true; }
  if (S.colMenu) { e.preventDefault(); colMenuClose(true); return true; }
  // the guidance's sheet next, unless a card stands over it
  if (guideOpen() && !$('work').hidden && !anyOverlayOpen()) {
    e.preventDefault(); guide(false, { keep: true, focus: true }); return true;
  }
  if (S.rowMenu) { e.preventDefault(); closeRowMenu(); return true; }
  // the toolbar by the selection goes with the selection and the pieces under it
  if (selBarOn()) {
    e.preventDefault();
    selBarHide();
    window.getSelection().removeAllRanges();
    clearPending(true);
    return true;
  }
  if (S.timeEdit) { e.preventDefault(); closeTimeEdit(); return true; }
  if (S.editing) { e.preventDefault(); closeEditor(); return true; }
  // an interviewer note goes back to the three fields with nothing written
  if (S.note) { e.preventDefault(); discardNote(); return true; }
  if (S.pending.length) { e.preventDefault(); clearPending(true); return true; }
  // the find and replace card closes, its washes with it
  if (findOpen() && !$('work').hidden) { e.preventDefault(); closeFind(); return true; }
  // on the sheet-done card Esc is Take a break
  if (!$('round-done').hidden && !$('done-sheet').hidden) { e.preventDefault(); stopHere(); return true; }
  return false;
}

/* Idiograph's cards busy with their work, which a click outside them leaves open (clickout, the shell's cardHeld): a
   copy or a REFI-QDA file being written, boards coming back, a workbook or a project being made, a participant being
   renamed, an agent's actions being answered and a review being sent */
function distilCardBusy(o) {
  const review = typeof RVW !== 'undefined' && RVW.busy;
  const busy = {
    'share-card': SC.busy, 'qdpx-card': QX.busy, 'copy-back': CB.busy, import: IMPORT.busy, newproject: NP.busy,
    rename: RN.busy, 'hold-card': HOLDS.busy, 'holds-batch': HOLDS.busy, 'wt-ask': review, 'wt-review': review,
  };
  return !!busy[o.id];
}

/* Esc's last, after the panels: the way back to the turn */
function distilKeysEscapeLast(e) {
  // first it brings the column back to the turn, from wherever the caret is and without
  // touching the field. Only once the turn is in view does it leave the field, as it always did
  if (!$('work').hidden && !$('back-to-turn').hidden) { e.preventDefault(); centreCurrent(true); return true; }
  return false;
}

/* Enter on Idiograph's own cards */
function distilKeysCards(e) {
  if (scKeys(e) || qxKeys(e) || cbKeys(e) || phKeys(e)) return true;
  if (holdKeys(e)) return true;
  // the confirm card for a whole turn goes on Enter, the way it says it does, and so does the trim
  if (!$('assign').hidden && e.key === 'Enter' && !MOD(e)) { e.preventDefault(); runAssignTurn(); return true; }
  if (!$('trim').hidden && e.key === 'Enter' && !MOD(e)) { e.preventDefault(); runTrim(); return true; }
  // Enter on the case-complete card presses Mark complete while it is offered, and Enter on the
  // card the bar's line opens reopens, the way it says it does
  if (!$('round-done').hidden && !$('done-mark').hidden && e.key === 'Enter' && !MOD(e)) {
    e.preventDefault(); markComplete('mark'); return true;
  }
  // and Enter on the sheet-done card presses Next sheet
  if (!$('round-done').hidden && !$('done-sheet').hidden && e.key === 'Enter' && !MOD(e)) {
    e.preventDefault(); nextSheet(); return true;
  }
  if (!$('complete').hidden && e.key === 'Enter' && !MOD(e)) { e.preventDefault(); reopenComplete(); return true; }
  return false;
}

/* the statements screen's keys, with no card over it, the last the shell asks */
function distilKeys(e) {
  const typing = document.activeElement && /TEXTAREA|INPUT/.test(document.activeElement.tagName);

  // Ctrl+Y redoes off a Mac, as Windows has it and the window's Edit menu names it (17 October)
  if ((MOD(e) && (e.key === 'z' || e.key === 'Z')) || REDO_Y(e)) {
    const backwards = !e.shiftKey && !REDO_Y(e);
    if (nativeUndoOwns(backwards)) return;   // the field he is typing in keeps its own undo
    e.preventDefault();
    undoStep(backwards);
    return;
  }
  if (MOD(e) && e.key === 'Enter') { e.preventDefault(); pressAct(); return; }
  if (MOD(e) && (e.key === 'j' || e.key === 'J')) { e.preventDefault(); move(-1); return; }
  if (MOD(e) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); move(1); return; }
  // find and replace, from anywhere on the turn screen, the fields included (item 139)
  if (MOD(e) && e.shiftKey && !e.altKey && ((e.key || '').toLowerCase() === 'f' || e.code === 'KeyF')
      && !$('work').hidden) {
    e.preventDefault(); openFind(); return;
  }
  // the sheet before and the sheet after, from anywhere including inside the fields, on the
  // same modifiers as the seek: Ctrl + Cmd and an arrow, up and down for the sheets, left and
  // right for the recording. Cmd + Shift and a bracket would have been the browser's own
  // tab-switching keys
  const sheetStep = SEEK(e) && !$('work').hidden
    && (e.key === 'ArrowUp' ? -1 : e.key === 'ArrowDown' ? 1 : 0);
  if (sheetStep) { e.preventDefault(); stepSheet(sheetStep); return; }
  // five seconds either way, from anywhere including inside the fields, on a chord of its own
  // (item 33): one chord that means one thing wherever the caret is
  if (SEEK(e) && e.key === 'ArrowLeft' && !$('work').hidden) {
    e.preventDefault(); nudgeAudio(-AUDIO_STEP); return;
  }
  if (SEEK(e) && e.key === 'ArrowRight' && !$('work').hidden) {
    e.preventDefault(); nudgeAudio(AUDIO_STEP); return;
  }
  const onBin = !!(document.activeElement && document.activeElement.closest && document.activeElement.closest('.pair-remove'));
  if (e.key === 'Tab' && (typing || onBin) && !$('work').hidden) {
    // the fields in the order they sit in the card, pair by pair, a statement, its quote and its bin
    // (18 October), and last the notes in their own column, each only while its column is shown
    // and on a thematic analysis project's Coding screen each extract's Add a code, under the pairs (a11yfix)
    const order = [...$('pairs').querySelectorAll('.pair-es, .pair-kq, .pair-remove'),
      ...($('cx-list') ? $('cx-list').querySelectorAll('.cx-field') : []), $('en')]
      .filter((el) => el.getClientRects().length);
    const at = order.indexOf(document.activeElement);
    if (at >= 0) {
      e.preventDefault();
      const next = order[(at + (e.shiftKey ? order.length - 1 : 1)) % order.length];
      next.focus();
    }
    return;
  }
  if (typing || MOD(e) || e.altKey) return;
  // the player takes space, the arrows and the rest of its own keys once one of its controls has
  // focus, the way the native element did before the controls became the app's own
  const focus = document.activeElement;
  if (focus && focus.closest && focus.closest('#player-wrap')) return;
  // a letter key in either case, so Q works with Caps Lock on as PETs', Sift's and Trace's keys do
  // (18 October)
  const key = (e.key || '').length === 1 ? e.key.toLowerCase() : e.key;
  // Space did nothing here before: in a field it types a space, as it always did, and outside
  // one it plays or pauses from wherever the clock sits
  if (e.key === ' ' && !$('work').hidden) { e.preventDefault(); togglePlay(); }
  else if (key === 'e' && !$('work').hidden) { e.preventDefault(); openEditor(current()); }
  else if (key === 'q' && !$('work').hidden) { e.preventDefault(); commitQuote(); }
  // a thematic analysis project's quick keys on words selected, R, V and 1 to 5, nothing without words (codes.js)
  else if ((key === 'r' || key === 'v' || /^[1-5]$/.test(e.key)) && !$('work').hidden
    && typeof cxQuickKey === 'function' && cxQuickKey(key)) { e.preventDefault(); }
  else if (key === 'c' && !$('work').hidden) { e.preventDefault(); assignKey(); }
  else if (key === 't' && !$('work').hidden) { e.preventDefault(); trimKey(); }
  else if ((e.key === '?' || (e.shiftKey && e.key === '/')) && APP === 'idiograph') { e.preventDefault(); openHelp(); }
  else if (key === 'g' && !$('work').hidden) { toggleGuide(); }
  else if (key === 'm' && !$('work').hidden) { e.preventDefault(); minimapToggle(); }
  else if (key === 'p' && !$('work').hidden && S.data) { e.preventDefault(); esStep('pets'); }
  else if (e.key === 'ArrowLeft' && !$('work').hidden) { move(-1); }
  else if (e.key === 'ArrowRight' && !$('work').hidden) { move(1); }
}


/* ── Search's openers and landings on Idiograph's screens (search.js's until the family codebase's fifth build,
   23 October 2026), each registered with the family (FAMILY_APPS.idiograph) ── */

/* the screen in front for Search, the statements screen, PETs, GETs or a project's page, or null */
function distilSearchWhere() {
  if (searchShown('work') && S.data) return { screen: 'statements', path: S.data.path };
  if (searchShown('themes') && TH.path) return { screen: TH.mode === 'gets' ? 'gets' : 'pets', path: TH.path };
  // the Trajectories board, the project's, searched as the GETs are (option C of the bars, 26 October 2026)
  if (searchShown('traj') && typeof TJ !== 'undefined' && TJ.path) return { screen: 'trajectories', path: TJ.path };
  // a thematic analysis project's code list, searched as the project is (codes)
  if (searchShown('codes-screen') && typeof CD !== 'undefined' && CD.path) return { screen: 'codes', path: CD.path };
  if (searchShown('library') && searchShown('home-project') && S.home) return { screen: 'project', root: S.home };
  return null;
}

/* the cards and menus the screen keeps open put away as Search opens, Find and replace among them, so none
   stands over the card or out of the wash */
function distilSearchClear(here) {
  if (here.screen === 'statements') {
    closeFind();
    if (S.editing) closeEditor();
    closeTimeEdit();
    closeRowMenu();
    viewMenu(false);
  } else if (here.screen === 'pets' || here.screen === 'gets') {
    thVmenu(false);
    thXmenu(false);
    thCasemenu(false);
    thMenuClose();
  }
}

/* the caret back on the statements screen as Search closes */
function distilSearchClosed(here) {
  if (here.screen === 'statements' && !$('work').hidden) focusEntry();
}

/* Replace in the transcript: Find and replace opened with the words typed */
function distilSearchReplace(words) {
  if (words) $('find-text').value = words;
  openFind();
}

/* A result opened on Idiograph's screens: a passage, an item on its board, the project's page */
async function distilSearchTo(go, r) {
  if (go.screen === 'statements') await searchToPassage(go, r);
  else if (go.screen === 'pets' || go.screen === 'gets') await searchToBoard(go, r);
  else if (go.screen === 'project') await searchToProject(go);
}

/* The screen in front left as any way out of it leaves it: on the statements screen a field typed into and not
   saved saved first, an interviewer note kept and the recording stopped, on PETs and GETs the canvas saved. A
   save that fails keeps him where he is, and the answer is false. */
async function distilSearchLeave(here) {
  if (here.screen === 'statements') {
    if (S.dirty && S.data && current()) {
      await commit(current(), false);
      if (S.dirty) return false;
    }
    if (S.note) await keepNote();
    closeFind();
    $('player').pause();
    return true;
  }
  if (here.screen === 'pets' || here.screen === 'gets') {
    thTitleDone(true);
    thNoteDone(true);
    thVmenu(false);
    thViewEnd();
    await thFlush();
    if (TH.live && TH.dirty) { say(t('distil.search.canvas_unsaved'), 6000); return false; }
  }
  // a title or a note in hand on Trajectories kept first
  if (here.screen === 'trajectories' && typeof trajIdle === 'function') await trajIdle();
  return true;
}

/* a board left for another part's put away as the way to a statement's passage puts it away */
function distilSearchAway(here) {
  if (here.screen === 'pets' || here.screen === 'gets') searchBoardAway();
  if (here.screen === 'trajectories' && $('traj') && typeof TJ !== 'undefined') { $('traj').hidden = true; TJ.ask += 1; }
  if (here.screen === 'codes' && $('codes-screen') && typeof CD !== 'undefined') { $('codes-screen').hidden = true; CD.ask += 1; }
}

/* The board put away as the way to a statement's passage puts it away, saved as it stands. */
function searchBoardAway() {
  TH.live = false;
  TH.ask += 1;
  thPile(false);
  thXmenu(false);
  thCasemenu(false);
  thSideShut(false);
  thExported(null);
  thMenuClose();
  $('themes').hidden = true;
}

/* The way back to the board in front, with its place and selection, as a statement's passage opened
   from it keeps them (see thToPassage), or null on any other screen. */
function searchBoardBack(here) {
  if (!here || (here.screen !== 'pets' && here.screen !== 'gets') || !TH.v) return null;
  const gets = here.screen === 'gets';
  const kept = {
    mode: TH.mode, path: TH.path, label: TH.label, back: TH.back, board: TH.meta ? TH.meta.id : null,
    to: TH.to,
    view: { x: TH.view.x, y: TH.view.y, z: TH.view.z }, pick: TH.lastPick ? { ...TH.lastPick } : null,
    sel: { cards: [...TH.sel.cards], groups: [...TH.sel.groups], stickies: [...TH.sel.stickies] },
  };
  const again = () => (kept.mode === 'gets' ? getsOpen : themesOpen)(kept.path,
    { back: kept.back, label: kept.label, to: kept.to, board: kept.board, restore: kept });
  return { back: again, to: gets ? 'gets' : 'pets' };
}

/* A workbook's result: the case opened at the passage, or at the participant's passage nearest an
   interviewer's, and there the statement's or the quote's field of its pair, the exploratory notes or
   the interviewer's note takes the caret. On the case already open the move is any move's. From a board
   the bar's way back names it, as a statement's passage opened from a card does. */
async function searchToPassage(go, r) {
  const here = SEARCH.here;
  const same = here && here.screen === 'statements' && S.data && S.data.path === go.path;
  if (!same) {
    const back = searchBoardBack(here);
    if (!(await searchLeave(here))) return;
    let data;
    try {
      data = await api('/api/open', { path: go.path });
    } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); return; }
    if (here && (here.screen === 'pets' || here.screen === 'gets')) searchBoardAway();
    S.backTo = back;
    startCase(data, { at: { sheet: go.sheet, row: go.row } });
  }
  const row = S.flat.find((x) => x.sheet === go.sheet && x.row === go.row);
  if (!row) { say(NO_PASSAGE_LINE, 6000); return; }
  const stop = row.stop ? row.pos : stopNear(row.sheet, row.row, S.at);
  if (stop !== S.at) await goTo(stop);
  else if (same) centreCurrent(true);
  if (go.field === 'note' && noteable(row)) { openNote(row); return; }
  if (!row.stop) {
    const el = $('transcript-rows').querySelector(`.turn[data-i="${row.i}"]`);
    if (el) el.scrollIntoView({ block: 'nearest' });
    focusEntry();
    return;
  }
  if (go.field === 'en') {
    if (!guideHolds()) $('en').focus({ preventScroll: true });
    return;
  }
  if (go.field === 'es' || go.field === 'kq') {
    const pair = pairEls()[Number(go.line) || 0];
    if (pair && !guideHolds()) {
      S.pairFocus = pair.dataset.pid;
      S.kqLit = pair.dataset.pid;
      pair.querySelector(go.field === 'kq' ? '.pair-kq' : '.pair-es').focus();
      lightMarks();
      return;
    }
  }
  focusEntry();
}

/* A board's result: PETs of its case, or the project's GETs, on that board, and there the PET, the
   sub-theme, the GET, the sticky note or the card selected and fitted in the middle of the canvas, as a
   GET of the table is shown. The board in front with the same board selects at once. */
async function searchToBoard(go, r) {
  const here = SEARCH.here;
  const gets = go.screen === 'gets';
  const onScreen = here && here.screen === go.screen && TH.live && (gets || TH.path === go.path);
  if (!(onScreen && TH.meta && String(TH.meta.id) === String(go.board))) {
    if (!(await searchLeave(here))) return;
    if (onScreen) {
      await (gets ? getsOpen : themesOpen)(TH.path, { back: TH.back, label: TH.label, to: TH.to, board: go.board });
    } else if (gets) {
      await openGets(go.path, { board: go.board });
    } else if (here && here.screen === 'statements' && S.data && S.data.path === go.path) {
      await openThemes(S.data.path, 'work', S.data.name, { board: go.board });
    } else {
      $('library').hidden = true;
      $('work').hidden = true;
      await themesOpen(go.path, { back: () => { loadLibrary().catch((err) => say(err.message, 9000)); },
        label: r.case, to: 'cases', board: go.board });
    }
  }
  if (!TH.live || !TH.v || $('themes').hidden) return;
  searchShowItem(go);
}

/* the item a board's result names selected and in view, as the GET table's rows show theirs */
function searchShowItem(go) {
  const v = TH.v;
  let item = null;
  let box = null;
  if (go.item === 'group' && thIsGroup(v, go.id)) {
    item = { kind: 'group', id: go.id };
    box = TH.layout[go.id] && (TH.layout[go.id].frame || TH.layout[go.id].label);
  } else if (go.item === 'card' && v.cards[go.id]) {
    item = { kind: 'card', id: go.id };
    const s = thSize(go.id);
    box = { x: v.cards[go.id].x, y: v.cards[go.id].y, w: s.w, h: s.h };
  } else if (go.item === 'sticky') {
    const n = thStickies(v).find((x) => x.id === go.id);
    if (n) {
      item = { kind: 'sticky', id: go.id };
      const s = thSize(go.id);
      box = { x: n.x, y: n.y, w: s.w, h: s.h };
    }
  }
  if (!item) return;
  thSelectOnly(item);
  TH.lastPick = item;
  thPanelFollow();
  thFitTo(box);
  // and in the board's Table view, its row (19 October)
  if (typeof thTableShow === 'function') thTableShow(go.id);
}

/* A case's or the research question's result: the project's page, the case's row in view with the
   caret on its Experiential statements, or the page's head. */
async function searchToProject(go) {
  const here = SEARCH.here;
  if (!(here && here.screen === 'project' && S.home === go.id)) {
    if (!(await searchLeave(here))) return;
    if (here && (here.screen === 'pets' || here.screen === 'gets')) searchBoardAway();
    S.backTo = null;
    homeKeep(go.id);
    try { await loadLibrary(); } catch (err) { say(err.message, 9000); return; }
  }
  const row = go.case ? [...$('hp-list').querySelectorAll('li.pcard')].find((li) => li.dataset.case === go.case) : null;
  if (row) {
    row.scrollIntoView({ block: 'center' });
    const first = ['button.pc-es:not([disabled])', 'button[data-act="start"]', 'button.pc-half', 'button:not(.pc-grip)']
      .map((s) => row.querySelector(s)).find(Boolean);
    if (first) first.focus({ preventScroll: true });
  } else {
    window.scrollTo(0, 0);
    $('hp-back').focus({ preventScroll: true });
  }
}

/* ── An agent's action waiting for his yes (holds.py, 27 October 2026, Adam's ruling: build it as drawn) ── */

/* An agent's action that deletes a board, puts an old revision over one or replaces words across every participant
   waits for his yes while Dangerously skip permissions is off. The app asks after them every few seconds on the
   screens that show an agent's line, the statements screen, PETs and GETs, and shows the bright line in that
   line's corner: the one action's words, or how many wait, and Review, which opens the card for the oldest.
   Approve runs it as the agent asked, Decline writes nothing but History's line, and the same line then says what
   happened, with its cross. Only the page answers one, through /api/holds. */
const HOLDS = { list: [], after: '', open: null, busy: false };
const HOLDS_EVERY = 4 * 1000;
// how long one action may take before its card says it is working (holdsprog)
const HOLD_SLOW_MS = 500;

const holdAgent = (h) => (h && h.tool) || t('distil.holds.the_agent');

/* The screen behind the line, the statements screen or PETs and GETs, or none */
function holdScreen() {
  if ($('work') && !$('work').hidden) return 'work';
  if ($('themes') && !$('themes').hidden) return 'themes';
  return null;
}

/* The line in the corner where this screen's agent line sits, below that line while it shows */
function holdPlace() {
  const box = $('hold-line');
  const gutter = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--gutter')) || 24;
  let top = 54, right = gutter;
  if (holdScreen() === 'themes' && $('th-stage')) {
    const stage = $('th-stage').getBoundingClientRect();
    top = stage.top + gutter;
    right = window.innerWidth - stage.right + gutter;
    const other = $('th-outside');
    if (other && !other.hidden) top = other.getBoundingClientRect().bottom + 8;
  } else if ($('es-outside') && !$('es-outside').hidden) {
    top = $('es-outside').getBoundingClientRect().bottom + 8;
  }
  box.style.top = `${Math.round(top)}px`;
  box.style.right = `${Math.round(right)}px`;
}

function holdDraw() {
  const box = $('hold-line');
  if (!box) return;
  const n = HOLDS.list.length;
  if (!holdScreen() || (!HOLDS.after && !n)) { box.hidden = true; return; }
  if (HOLDS.after) {
    $('hold-line-words').textContent = HOLDS.after;
    $('hold-review').hidden = true;
    $('hold-line-close').hidden = false;
  } else {
    $('hold-line-words').textContent = n === 1 ? HOLDS.list[0].waiting : t('distil.holds.waiting', { n });
    $('hold-review').hidden = false;
    $('hold-line-close').hidden = true;
  }
  box.hidden = false;
  holdPlace();
}

/* every action waiting in the app's projects, as the server has them now */
async function holdsRead() {
  try {
    const data = await api('/api/holds', { op: 'list' });
    HOLDS.list = Array.isArray(data.holds) ? data.holds : [];
  } catch { HOLDS.list = []; }
}

async function holdsTick() {
  if (!$('hold-line') || HOLDS.busy || document.hidden || !holdScreen()) { holdDraw(); return; }
  await holdsRead();
  holdDraw();
}

/* ── Waiting actions on Home's project cards (holdsprog, Adam, 11 November 2026: 13 waited and Home never said) ── */

/* A project with actions waiting for his yes says so on its card, "13 actions are waiting for your yes", in the crux
   orange the Preview note's sign is, and a press on the line opens the project on a participant's PETs screen,
   where the line in the corner stands, with the card for them open. The counts are one call after the picker is
   drawn, `/api/holds` with `counts`, for every project the page lists: the server reads each project's holds file
   and nothing else of it (holds.counts), and a project with none shows no line. Home asks each time the picker is
   drawn, so each time it is shown again, and not while it stays up. The line is a button beside the card's own and
   never in it. An answer that lands after a newer ask is dropped. */
let homeHoldsAsk = 0;

async function homeHoldsRead() {
  const ask = ++homeHoldsAsk;
  // the room for the line goes with the old cards, and comes back with the line
  for (const id of ['projects', 'demo-projects']) if ($(id)) $(id).classList.remove('has-holds');
  let counts = [];
  try {
    const data = await api('/api/holds', { op: 'counts' });
    counts = Array.isArray(data.counts) ? data.counts : [];
  } catch { counts = []; }
  if (ask !== homeHoldsAsk) return;
  const by = new Map(counts.filter((c) => c && Number(c.n) > 0).map((c) => [String(c.id), Number(c.n)]));
  for (const li of document.querySelectorAll('#projects .home-card-li, #demo-projects .home-card-li')) {
    const id = li.querySelector('.home-card').dataset.id;
    const old = li.querySelector('.hc-hold');
    if (old) old.remove();
    li.classList.toggle('has-hold', by.has(id));
    if (by.has(id)) {
      li.insertAdjacentHTML('beforeend',
        `<button type="button" class="hc-hold" data-id="${escAttr(id)}">${esc(t('distil.home.holds_waiting', { n: by.get(id) }))}</button>`);
    }
  }
  for (const id of ['projects', 'demo-projects']) if ($(id)) $(id).classList.toggle('has-holds', !!$(id).querySelector('.hc-hold'));
}

/* The line pressed: the project opens as his own way in opens it, its page and then the first participant's PETs,
   so Back walks the same way, and the list of actions is read afresh for the card, which opens over the screen */
async function holdsOpenFromHome(id) {
  const there = isDemoId(id) ? (demosOf(S.lib).find((d) => d.id === id) || {}).cards : (sectionsOf(S.lib).find((s) => s.id === id) || {}).participants;
  const first = (there || []).find((p) => p && p.path);
  await openPage(id);
  if (first) await openThemesIn(first.path, first.case);
  await holdsRead();
  holdDraw();
  holdReview();
}

/* The card for one action, its words as the server last read them */
function holdFill(h, note) {
  HOLDS.open = h;
  $('hold-agent').textContent = h.tool || t('distil.holds.ai_agent');
  $('hold-title').textContent = h.question;
  $('hold-asked').textContent = h.asked;
  $('hold-changed').textContent = note || '';
  $('hold-changed').hidden = !note;
  // what it would do, a line each, as the server says it from the op's dry run (holds.would_lines)
  $('hold-would').textContent = (h.would_do || []).join('\n');
}

/* what changed since the agent asked, naming whose files when the server says (`changed_what`, holdbatchA) */
const holdChangedLine = (h, done) => (h.changed_what
  ? t(done ? 'distil.holds.what_changed_done' : 'distil.holds.what_changed', { what: h.changed_what, agent: holdAgent(h) })
  : t(done ? 'distil.holds.changed_done' : 'distil.holds.changed', { agent: holdAgent(h) }));

/* Review: the card for the oldest waiting, then its dry run again, which says when it changed since. With more
   than one waiting, the card for several (holdsBatchOpen) */
async function holdReview() {
  if (HOLDS.list.length > 1) { holdsBatchOpen(); return; }
  const h = HOLDS.list[0];
  if (!h) return;
  holdFill(h);
  show('hold-card');
  $('hold-decline').focus();
  try {
    const data = await api('/api/holds', { op: 'check', root: h.root, id: h.id });
    if (HOLDS.open && HOLDS.open.id === h.id) holdFill(Object.assign({}, h, data.hold), data.changed ? holdChangedLine(Object.assign({}, h, data.hold), false) : '');
  } catch (err) { say(err.message, 9000); }
}

/* an agent's Remove from Idiograph approved (removetrash, 10 November 2026): Home lists the projects afresh */
function holdProjectGone() {
  if (!$('library').hidden) loadLibrary().catch((err) => say(err.message, 9000));
}

async function holdAnswer(op) {
  const h = HOLDS.open;
  if (!h || HOLDS.busy) return;
  HOLDS.busy = true;
  $('hold-approve').disabled = true;
  $('hold-decline').disabled = true;
  // a quiet line, and no bar for one action, only when the answer takes longer than about half a second (holdsprog)
  const slow = setTimeout(() => {
    $('hold-run').textContent = t(op === 'approve' ? 'distil.holds.approving' : 'distil.holds.declining');
    $('hold-run').hidden = false;
  }, HOLD_SLOW_MS);
  try {
    const data = await api('/api/holds', { op, root: h.root, id: h.id, page: pageId() });
    if (data.changed) {
      holdFill(Object.assign({}, h, data.hold), holdChangedLine(Object.assign({}, h, data.hold), true));
      return;
    }
    hide('hold-card');
    HOLDS.open = null;
    HOLDS.after = data.hold.line || '';
    HOLDS.list = HOLDS.list.filter((x) => !(x.id === h.id && x.root === h.root));
    holdDraw();
    // the screen behind sees the change as it sees any agent's, its own line offering Update
    if (op === 'approve') {
      if (h.op === 'project remove') holdProjectGone();
      if (holdScreen() === 'themes' && typeof thStampTick === 'function') thStampTick(true);
      if (holdScreen() === 'work' && typeof esStampTick === 'function') esStampTick();
    }
  } catch (err) {
    say(err.message, 9000);
    hide('hold-card');
    HOLDS.open = null;
  } finally {
    clearTimeout(slow);
    $('hold-run').hidden = true;
    HOLDS.busy = false;
    $('hold-approve').disabled = false;
    $('hold-decline').disabled = false;
    holdsTick();
  }
}

function holdLineClose() {
  HOLDS.after = '';
  holdDraw();
}

/* ── The card for several (holdbatchA, Adam's option A of 1 November 2026) ──
   With more than one action waiting, Review opens one card listing them all under his request, a row each: what
   it would do in a line, the agent and when, its tick, and Details, which opens the row's own card in place (his
   request, what it would do, the copy kept, what stays). Every row is ticked as the card opens but one that
   changed since the agent asked, which says so. Decline and Approve answer the ticked rows in order, through
   /api/holds with `holds`, and the same card then says what was done, each not done with its reason, the rows
   not ticked still waiting. The server never counts his own earlier answers as a change (holds.carry). */
const HB = { list: [], ticked: new Set(), open: new Set(), after: null };
const HB_CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M6 9l6 6 6-6"/></svg>';
const HB_TICK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
const HB_WARN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.1"/></svg>';
const hbKey = (h) => `${h.root}\n${h.id}`;
const hbWhat = (h) => String(h.question || '').replace(/\?$/, '');

/* when it was asked, the time alone today, else the day and the time */
function hbWhen(at) {
  const d = new Date(at);
  if (Number.isNaN(d.getTime())) return '';
  if (d.toDateString() === new Date().toDateString()) return tTime(d);
  return `${tDate(d, { day: 'numeric', month: 'short' })}, ${tTime(d)}`;
}

/* the agent over the card: the one that asked, or AI agents when more than one did */
function hbAgent(list) {
  const tools = [...new Set(list.map((h) => h.tool || ''))];
  return tools.length === 1 ? (tools[0] || t('distil.holds.ai_agent')) : t('distil.holds.agents');
}

/* the rows under each request, a project's requests in the order first asked, each as the agent that asked says it,
   its words cleaned by the server (holds.agent_words, agentholds) */
function hbGroups(list) {
  const groups = [];
  for (const h of list) {
    const g = groups.find((x) => x.root === h.root && x.request === (h.request || '') && x.agent === holdAgent(h));
    if (g) g.items.push(h); else groups.push({ root: h.root, request: h.request || '', agent: holdAgent(h), items: [h] });
  }
  return groups;
}

/* the line under a row: what changed since the agent asked and whose, or that his own answers since changed what
   it would do */
function hbChangedLine(h) {
  if (h.changed) return h.changed_what ? t('distil.holds.what_changed', { what: h.changed_what, agent: holdAgent(h) }) : t('distil.holds.changed', { agent: holdAgent(h) });
  if (h.since_yours) return t(h.since_yours === 'deleted' ? 'distil.holds.since_yours_deleted' : 'distil.holds.since_yours_changed');
  return '';
}

function hbDraw() {
  $('holds-batch').querySelector('.holds-batch').classList.remove('running');
  const n = HB.list.length;
  const k = HB.list.filter((h) => HB.ticked.has(hbKey(h))).length;
  $('hb-agent').textContent = hbAgent(HB.list);
  $('hb-title').textContent = t('distil.holds.batch_title', { n });
  $('hb-sum').hidden = true;
  $('hb-all').hidden = false;
  $('hb-all').textContent = k === n ? t('distil.holds.untick_all') : t('distil.holds.tick_all');
  let rows = '';
  for (const g of hbGroups(HB.list)) {
    rows += `<p class="hb-ask">${esc(g.request ? t('distil.holds.agent_says', { agent: g.agent, request: g.request }) : t('distil.holds.no_request'))}</p><ul class="hb-rows">`;
    for (const h of g.items) {
      const key = hbKey(h);
      const open = HB.open.has(key);
      const changed = hbChangedLine(h) ? `<span class="hb-changed">${esc(hbChangedLine(h))}</span>` : '';
      rows += `<li class="hb-row" data-tick-row data-key="${escAttr(key)}">`
        + `<label><input type="checkbox"${HB.ticked.has(key) ? ' checked' : ''}><span><span class="hb-what">${esc(hbWhat(h))}</span>${changed}</span></label>`
        + `<span class="hb-when">${esc(holdAgent(h))}, ${esc(hbWhen(h.at))}</span>`
        + `<button type="button" class="ghost small hb-more" aria-expanded="${open}">${esc(t('distil.holds.details'))} ${HB_CHEV}</button></li>`;
      if (open) {
        rows += `<li class="hb-detail"><p class="hold-asked">${esc(h.asked || '')}</p>`
          + `<p class="hold-what">${esc(h.changed || h.since_yours ? t('distil.holds.what_now') : t('distil.holds.what_would_do'))}</p>`
          + `<pre class="mcp-code">${esc((h.would_do || []).join('\n'))}</pre></li>`;
      }
    }
    rows += '</ul>';
  }
  $('hb-list').innerHTML = rows;
  hbCount(k);
  for (const id of ['hb-decline', 'hb-approve']) { $(id).hidden = false; $(id).disabled = !k || HOLDS.busy; }
  $('hb-again').hidden = true;
  $('hb-done').hidden = true;
}

/* Decline and Approve naming how many are ticked, plain Decline and Approve, greyed, while none is */
function hbCount(k) {
  $('hb-decline').textContent = k ? t('distil.holds.decline_n', { n: k }) : t('page_idiograph.cards_more.decline');
  $('hb-approve').textContent = k ? t('distil.holds.approve_n', { n: k }) : t('page_idiograph.cards_more.approve');
}

async function holdsBatchOpen() {
  HB.list = HOLDS.list.slice();
  HB.after = null;
  HB.open = new Set();
  HB.ticked = new Set(HB.list.filter((h) => !h.changed).map(hbKey));
  hbDraw();
  show('holds-batch');
  $('hb-list').scrollTop = 0;
  // the focus on Tick all, never on Approve or Decline, so Enter answers nothing by itself
  $('hb-all').focus();
  // each row's dry run again, which says the ones that changed since the agent asked, and unticks them
  try {
    const data = await api('/api/holds', { op: 'check', holds: HB.list.map((h) => ({ root: h.root, id: h.id })) });
    if (HB.after || $('holds-batch').hidden) return;
    const seen = new Set();
    for (const c of data.checks || []) {
      const i = HB.list.findIndex((h) => h.id === c.hold.id && h.root === c.root);
      if (i < 0) continue;
      seen.add(hbKey(HB.list[i]));
      if (c.changed) HB.ticked.delete(hbKey(HB.list[i]));
      HB.list[i] = Object.assign({}, HB.list[i], c.hold, { root: c.root });
    }
    // one answered elsewhere meanwhile is no longer waiting
    HB.list = HB.list.filter((h) => seen.has(hbKey(h)) && h.status === 'waiting');
    hbDraw();
  } catch (err) { say(err.message, 9000); }
}

/* While a list is answered the card is its heading and a bar (holdsprog, Adam, 11 November 2026, after 13 slow approvals
   that "just sat there"): the list, the ticks, Tick all and both buttons give way to "Approving 4 of 13" and a bar
   that fills as each finishes, and nothing on the card can be changed meanwhile. Esc does nothing until the run ends
   (holdKeys looks at HOLDS.busy) and the card has no other way to close. `done` is how many have finished, so the
   line and the bar agree */
function hbRun(op, done, total) {
  $('holds-batch').querySelector('.holds-batch').classList.add('running');
  $('hb-title').textContent = t(op === 'approve' ? 'distil.holds.approving_of' : 'distil.holds.declining_of', { n: done, m: total });
  $('hb-bar').setAttribute('aria-valuemax', String(total));
  $('hb-bar').setAttribute('aria-valuenow', String(done));
  $('hb-fill').style.width = `${total ? (done / total) * 100 : 0}%`;
}

/* Decline N or Approve N: the ticked rows answered one at a time, in the order shown, each through /api/holds with
   one id so the card can count them, then the card says what happened. An error on one keeps what was done before
   it, says that one was not done with the error's words, and leaves the rest waiting, unasked */
async function hbAnswer(op) {
  const picked = HB.list.filter((h) => HB.ticked.has(hbKey(h)));
  if (!picked.length || HOLDS.busy) return;
  HOLDS.busy = true;
  hbRun(op, 0, picked.length);
  const outcomes = [];
  let reached = picked.length;
  try {
    for (const [i, h] of picked.entries()) {
      try {
        const data = await api('/api/holds', { op, holds: [{ root: h.root, id: h.id }], page: pageId() });
        outcomes.push(...(data.outcomes || []));
      } catch (err) {
        outcomes.push({ root: h.root, id: h.id, outcome: 'failed', reason: err.message });
        reached = i + 1;
        break;
      }
      hbRun(op, outcomes.length, picked.length);
    }
    HB.after = { op, picked, outcomes, left: HB.list.filter((h) => !HB.ticked.has(hbKey(h))), unreached: picked.slice(reached) };
    hbAfter();
    if (op === 'approve' && picked.some((h) => h.op === 'project remove')) holdProjectGone();
    if (op === 'approve' && HB.after.outcomes.some((o) => o.outcome === 'approved')) {
      if (holdScreen() === 'themes' && typeof thStampTick === 'function') thStampTick(true);
      if (holdScreen() === 'work' && typeof esStampTick === 'function') esStampTick();
    }
  } finally {
    HOLDS.busy = false;
    $('hb-all').disabled = false;
    holdsTick();
  }
}

/* After: how many of those ticked were done, each row with its outcome, a row not done with its reason, and the
   rows not ticked still waiting. Review the N waiting opens the card again for those still waiting */
function hbAfter() {
  const a = HB.after;
  $('holds-batch').querySelector('.holds-batch').classList.remove('running');
  const done = a.outcomes.filter((o) => o.outcome === a.op + 'd');
  const notDone = a.outcomes.filter((o) => o.outcome !== a.op + 'd');
  const unreached = a.unreached || [];
  const still = notDone.filter((o) => o.outcome === 'changed').length + a.left.length + unreached.length;
  $('hb-title').textContent = t(a.op === 'approve' ? 'distil.holds.approved_of' : 'distil.holds.declined_of', { n: done.length, m: a.picked.length });
  const sum = [notDone.length ? t('distil.holds.not_done', { n: notDone.length }) : '', still ? t('distil.holds.still_wait', { n: still }) : '']
    .filter(Boolean).join(' ');
  $('hb-sum').textContent = sum;
  $('hb-sum').hidden = !sum;
  $('hb-all').hidden = true;
  const byKey = new Map(a.picked.map((h) => [hbKey(h), h]));
  let rows = '';
  for (const o of done) {
    const h = Object.assign({}, byKey.get(`${o.root}\n${o.id}`), o.hold || {});
    rows += `<li class="hb-done">${HB_TICK}<span>${esc(h.said || hbWhat(h))}</span><span class="hb-state">${esc(t(a.op === 'approve' ? 'distil.holds.state_done' : 'distil.holds.state_declined'))}</span></li>`;
  }
  for (const o of notDone) {
    const h = Object.assign({}, byKey.get(`${o.root}\n${o.id}`), o.hold || {});
    rows += `<li class="hb-done not">${HB_WARN}<span>${esc(hbWhat(h))}<span class="hb-why">${esc(o.reason || '')}</span></span><span class="hb-state">${esc(t('distil.holds.state_not_done'))}</span></li>`;
  }
  // the ticked rows a run did not reach, then the rows not ticked
  for (const [list, why] of [[unreached, 'distil.holds.not_reached'], [a.left, 'distil.holds.not_ticked']]) {
    for (const h of list) {
      rows += `<li class="hb-done not">${HB_WARN}<span>${esc(hbWhat(h))}<span class="hb-why">${esc(t(why))}</span></span><span class="hb-state">${esc(t('distil.holds.state_waiting'))}</span></li>`;
    }
  }
  $('hb-list').innerHTML = `<ul class="hb-done-list">${rows}</ul>`;
  $('hb-list').scrollTop = 0;
  $('hb-decline').hidden = true;
  $('hb-approve').hidden = true;
  $('hb-again').hidden = !still;
  $('hb-again').textContent = t('distil.holds.review_waiting', { n: still });
  $('hb-done').hidden = false;
  $('hb-done').focus();
}

/* Done: the card closes, and the line in the corner says how many still wait with Review, or what was done */
function hbClose() {
  const a = HB.after;
  hide('holds-batch');
  HB.after = null;
  if (a) {
    const waits = HOLDS.list.length;
    HOLDS.after = waits ? '' : $('hb-title').textContent + '.';
  }
  holdDraw();
}

/* Review the N waiting: the card again for those still waiting, read afresh */
async function hbAgain() {
  hide('holds-batch');
  HB.after = null;
  await holdsTick();
  holdReview();
}

function hbClick(e) {
  const more = e.target.closest('.hb-more');
  if (more) {
    const key = more.closest('.hb-row').dataset.key;
    if (HB.open.has(key)) HB.open.delete(key); else HB.open.add(key);
    const top = $('hb-list').scrollTop;
    hbDraw();
    $('hb-list').scrollTop = top;
    const again = [...$('hb-list').querySelectorAll('.hb-row')].find((r) => r.dataset.key === key);
    if (again) again.querySelector('.hb-more').focus();
  }
}

function hbTick(e) {
  const box = e.target;
  if (!box.matches('.hb-row input[type="checkbox"]')) return;
  const key = box.closest('.hb-row').dataset.key;
  if (box.checked) HB.ticked.add(key); else HB.ticked.delete(key);
  const k = HB.list.filter((h) => HB.ticked.has(hbKey(h))).length;
  $('hb-all').textContent = k === HB.list.length ? t('distil.holds.untick_all') : t('distil.holds.tick_all');
  hbCount(k);
  $('hb-decline').disabled = !k;
  $('hb-approve').disabled = !k;
}

function hbAll() {
  const all = HB.list.every((h) => HB.ticked.has(hbKey(h)));
  HB.ticked = all ? new Set() : new Set(HB.list.map(hbKey));
  const top = $('hb-list').scrollTop;
  hbDraw();
  $('hb-list').scrollTop = top;
  $('hb-all').focus();
}

/* Dangerously skip permissions: ticking it asks first, as ticking AI features does, and unticking asks nothing.
   Either way it is saved with Save, as every setting is */
function skipSwitch() {
  const box = $('set-skip-holds');
  if (!box.checked) return;
  box.checked = false;
  show('skip-confirm');
  $('skip-confirm-cancel').focus();
}

function skipConfirm(yes) {
  hide('skip-confirm');
  $('set-skip-holds').checked = yes;
  $('set-skip-holds').focus();
}

/* Esc and Enter on the two cards: Esc keeps it off, or closes the action's card with the action still waiting,
   and Enter on the turn-on card keeps it off unless I understand the risks has the focus */
function holdKeys(e) {
  if ($('skip-confirm') && !$('skip-confirm').hidden) {
    if (e.key === 'Escape') { e.preventDefault(); skipConfirm(false); return true; }
    if (e.key === 'Enter') { e.preventDefault(); skipConfirm(e.target === $('skip-confirm-go')); return true; }
  }
  if ($('hold-card') && !$('hold-card').hidden && e.key === 'Escape') {
    e.preventDefault();
    if (!HOLDS.busy) { hide('hold-card'); HOLDS.open = null; }
    return true;
  }
  // Esc on the card for several closes it, the actions still waiting, or after an answer as Done does. While it
  // answers (hbAnswer) it does nothing, and the card has no other way to close until the run ends (holdsprog)
  if ($('holds-batch') && !$('holds-batch').hidden && e.key === 'Escape') {
    e.preventDefault();
    if (!HOLDS.busy) hbClose();
    return true;
  }
  return false;
}

function holdsBoot() {
  if (!$('hold-line')) return;
  $('hold-review').onclick = () => holdReview();
  $('hold-line-close').onclick = () => holdLineClose();
  $('hold-approve').onclick = () => holdAnswer('approve');
  $('hold-decline').onclick = () => holdAnswer('decline');
  if ($('holds-batch')) {
    $('hb-approve').onclick = () => hbAnswer('approve');
    $('hb-decline').onclick = () => hbAnswer('decline');
    $('hb-all').onclick = () => hbAll();
    $('hb-done').onclick = () => hbClose();
    $('hb-again').onclick = () => hbAgain();
    $('hb-list').addEventListener('click', hbClick);
    $('hb-list').addEventListener('change', hbTick);
  }
  if ($('set-skip-holds')) {
    $('set-skip-holds').onchange = () => skipSwitch();
    $('skip-confirm-go').onclick = () => skipConfirm(true);
    $('skip-confirm-cancel').onclick = () => skipConfirm(false);
  }
  // a project's card's line for the actions waiting (holdsprog), on Home's two lists of cards
  for (const list of ['projects', 'demo-projects']) {
    if ($(list)) $(list).addEventListener('click', (e) => { const b = e.target.closest('.hc-hold'); if (b) holdsOpenFromHome(b.dataset.id); });
  }
  window.addEventListener('focus', () => holdsTick());
  window.addEventListener('resize', () => { if (!$('hold-line').hidden) holdPlace(); });
  setInterval(holdsTick, HOLDS_EVERY);
  holdsTick();
}

/* Idiograph's part of the page, registered with the family the way Sift's and Trace's are (sift_settings.js,
   trace.js), so the family's script names none of Idiograph's: see FAMILY_APPS in shell.js for what each is. Each
   hook calls its function when asked, so a piece of the page run alone in the suite's node harnesses can carry
   the table without every function it names */
FAMILY_APPS.idiograph = {
  // its screens, as a restart keeps them and as Search names them
  screens: ['work', 'statements', 'pets', 'gets', 'trajectories', 'project'],
  searchWhere: (...a) => distilSearchWhere(...a),
  searchClear: (...a) => distilSearchClear(...a),
  searchClosed: (...a) => distilSearchClosed(...a),
  searchReplace: (...a) => distilSearchReplace(...a),
  searchTo: (...a) => distilSearchTo(...a),
  searchLeave: (...a) => distilSearchLeave(...a),
  searchAway: (...a) => distilSearchAway(...a),
  scope: (path, body) => (typeof thScopeFor === 'function' ? thScopeFor(path, body) : body),
  homeRoute: '/api/cases',
  homeTaken: (data) => {
    // a run of one project, named by --root, opens on its page, until he goes back to the home screen
    const first = sectionsOf(data)[0];
    if (S.home === null && S.oneRun && first) homeKeep(first.id);
  },
  homeDraw: (...a) => distilHomeDraw(...a),
  homeAfter: (ask) => loadDays(ask),
  homeFirst: (...a) => distilHomeFirst(...a),
  recent: (...a) => distilRecent(...a),
  config: () => (typeof TH !== 'undefined' && TH && TH.config) || null,
  cheerScreen: () => {
    const th = typeof document !== 'undefined' && typeof document.getElementById === 'function' ? document.getElementById('themes') : null;
    if (th && !th.hidden && typeof TH !== 'undefined' && TH) return TH.mode === 'gets' ? 'gets' : 'pets';
    return null;
  },
  title: (...a) => distilTitle(...a),
  screenPane: (...a) => distilScreenPane(...a),
  settingsCase: (...a) => distilSettingsCase(...a),
  settingsOpen: (...a) => distilSettingsOpen(...a),
  settingsBody: (...a) => distilSettingsBody(...a),
  settingsSaved: (...a) => distilSettingsSaved(...a),
  settingsAfter: (...a) => distilSettingsAfter(...a),
  settingsShut: () => tpAfter(),
  // Project settings shut, by Save, its close or Esc, the screen behind drawn again once its timepoints changed
  projsetShut: () => tpAfter(),
  aiLoad: () => loadSample(),
  refocus: () => { if (!$('work').hidden) focusEntry(); },
  savePending: (...a) => distilSavePending(...a),
  spot: (...a) => distilSpot(...a),
  comeBack: (...a) => distilComeBack(...a),
  keysEscape: (...a) => distilKeysEscape(...a),
  keysEscapeLast: (...a) => distilKeysEscapeLast(...a),
  keysCards: (...a) => distilKeysCards(...a),
  keys: (...a) => distilKeys(...a),
  cardBusy: (...a) => distilCardBusy(...a),
};

distilBoot();

