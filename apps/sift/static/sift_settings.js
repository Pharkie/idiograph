/* Sift's part of the family's shell (the family codebase's third build, 22 October 2026, from app.js): its
   section on Home, a card for each Sift project with its lines, its parts of Settings, a Sift project's own
   parts, its AI proposals and their bench, and Zotero, what Save sends for them, the screen kept for a reload,
   and Search's place, leaving and landing on its two screens, all registered with the family's shell as
   `FAMILY_APPS.sift` at the foot, so app.js and search.js name none of Sift's. It comes after sift.js and
   sift_search.js, whose screens it opens and whose names it reads. */

'use strict';

/* ──────────────────────────────────────────────────── Sift on Home ── */

/* Sift, the first section, before Distil (15 October, later): a card for each Sift project, newest
   first, its name, its question and its lines (see `reviewLines`), and New project and Open project folder under
   them. A card opens the project on its steps (sift_search.js). A server from before the list sends
   `sift` in place of `reviews`, and the section says to restart. A server from before Sift sends
   neither, and it stays hidden. */
function reviewDay(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ''));
  if (!m) return String(iso || '');
  return tDate(new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]))),
    { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
}

/* how far a screening has got, its newest stage alone: the full text once it has a decision or the
   title and abstract stage has none left, else the title and abstract */
function reviewDecided(st) {
  const ta = (st && st.ta) || {};
  const ft = (st && st.ft) || {};
  if (Number(ft.records) && (Number(ft.decided) || !Number(ta.undecided))) {
    return t('sift_settings.decided_ft', { decided: Number(ft.decided) || 0, records: Number(ft.records) });
  }
  return t('sift_settings.decided_ta', { decided: Number(ta.decided) || 0, n: Number(ta.records) || 0 });
}

/* A card's one line, the project's newest step alone: with no searches its screening, else the run
   its Screening step opens, by its name, 9 October 2026, run 2 for a day's second, and that run's
   screening, never a newer run that brought nothing, else its newest run, else its plan's newest
   version */
function reviewLine(r) {
  if (r.said) return r.said;
  if (!r.there) return t('sift_settings.not_there');
  if (r.searches === false) {
    const line = reviewDecided(r.stages);
    return line.charAt(0).toUpperCase() + line.slice(1);
  }
  if (r.run) {
    if (r.run.said) return r.run.said;
    // a run by its number and its day, Run 3, 12 October 2026, as the server names it
    return t('sift_settings.run_line', { run: r.run.label || t('sift_settings.run_of', { day: reviewDay(r.run.date) }),
      state: r.run.screening ? reviewDecided(r.run.stages) : t('sift_settings.no_screening') });
  }
  if (r.version) return r.draft ? t('sift_settings.version_draft', { version: r.version }) : t('sift_settings.version_registered', { version: r.version });
  return t('sift_settings.no_plan');
}

/* A Sift card's lines as drawn (the split's pages, 21 October): its plan, Plan version 3, registered, or No
   search plan yet, and under it the run its Screening step opens and how far that screening has got. A
   project with no searches, or one that cannot be read or is not there, keeps its one line */
function reviewLines(r) {
  if (r.said || !r.there || r.searches === false) return [reviewLine(r)];
  const plan = r.version ? (r.draft ? t('sift_settings.plan_draft', { version: r.version }) : t('sift_settings.plan_registered', { version: r.version }))
    : t('sift_settings.no_plan');
  return r.run ? [plan, reviewLine(r)] : [plan];
}

/* Sift's projects for Open Recent in the File menu of its own window, each by its folder (app.js's windowRecent) */
const siftRecent = (data) => (Array.isArray(data.reviews) ? data.reviews : []).filter((r) => r && r.there !== false && r.folder)
  .map((r) => ({ part: 'sift', name: String(r.name || '').trim() || t('sift_settings.sift_project'), folder: r.folder }));

function drawSiftHome(data) {
  const rows = data && Array.isArray(data.reviews) ? data.reviews : null;
  const old = !rows && !!data && Array.isArray(data.sift);
  $('sift-home').hidden = !rows && !old;
  if (!rows && !old) return;
  foldable($('sift-home'), $('sift-head'), 'sift');
  const list = $('sift-list');
  if (old) { list.innerHTML = `<li class="empty">${esc(RESTART_LINE)}</li>`; return; }
  // each card's "..." and its menu, the family's, as an Idiograph card has them (barsD, 6 November 2026)
  const where = { window: windowPicks(), mac: MAC };
  list.innerHTML = rows.map((r, i) => {
    const menu = siftMenuRows(siftMenuItems(r, where), where);
    return `<li class="sf-row home-card-li${menu.length ? ' has-menu' : ''}"><button type="button" class="sf-row-open home-card" data-i="${i}"${r.there ? '' : ' disabled'}`
      + ` title="${escAttr(homeHover(r))}"><span class="pc-label hc-name">${esc(r.name)}</span>`
      // its research question under its name, as a Distil card has its own (12 October)
      + (r.question ? `<span class="hc-question">${esc(r.question)}</span>` : '')
      // its plan and its screening, never its folder, which the card's hover names (the split's pages)
      + reviewLines(r).map((line) => `<span class="pc-line">${esc(line)}</span>`).join('') + `</button>${projectDotsHtml(r.name, menu)}</li>`;
  }).join('');
  list.querySelectorAll('.sf-row-open').forEach((btn) => {
    btn.onclick = () => rvOpen(rows[Number(btn.dataset.i)].folder);
  });
  projectMenus(list, (act, li) => siftMenuDo(act, rows[Number(li.querySelector('.sf-row-open').dataset.i)]));
}

/* A Sift project's menu (barsD, Adam, 6 November 2026: "Add a menu to both"), on its card on Home and behind its name
   in the band, by the family's code (projectMenuHtml and the rest in shell.js): Show in Finder, in the app's own
   window alone as an Idiograph card's, Project settings, which opens Settings on Projects with this project in front,
   where its name, question, second screener and PDFs are, and Remove from Sift. A project whose folder is gone has
   Remove alone. Sift keeps no History of a project and makes no shared copy, so neither is there. */
function siftMenuItems(r, where) {
  if (!r || !r.folder) return [];
  if (r.there === false) return ['remove'];
  return [...(where.window ? ['show'] : []), 'settings', 'remove'];
}

function siftMenuRows(items, where) {
  return items.map((act) => ({ act, word: projectMenuWord(act, where.mac), remove: act === 'remove' }));
}

/* an item of a project's menu, `r` the project as the list or the screen has it, `inside` from its own screen */
function siftMenuDo(act, r, inside = false) {
  if (!r) return;
  if (act === 'show') siftShowFolder(r.folder);
  else if (act === 'settings') { SFA.want = r.folder; openSettings('sift'); }
  else if (act === 'remove') siftRemove(r, inside);
}

/* Show in Finder, or in Explorer: the server shows the project's folder, which a browser's page cannot */
async function siftShowFolder(folder) {
  try { await api('/api/sift-review', { op: 'reveal', folder }); } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

/* Remove from Sift from a project's menu, as Settings has it: Remove's card, then from the project's own screen
   the screen left as Home leaves it, a save that fails keeping him there with the project kept, then the project
   taken out of the list, its folder and every file in it left as they are or with the card's tick moved to the
   system's Trash (removetrash, 10 November 2026), and Home without it */
async function siftRemove(r, inside = false) {
  const asked = await askRemove(r.name || t('sift_settings.this_project'));
  if (!asked) return;
  if (inside && !(await goHome())) return;
  let data;
  try { data = await api('/api/sift-review', { op: 'forget', folder: r.folder, trash: asked.trash, page: pageId() }); } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return;
  }
  if (S.lib && Array.isArray(data.reviews)) S.lib.reviews = data.reviews;
  say(removedSaid(data.name || r.name, data, t('sift_settings.removed', { name: data.name || r.name })));
  loadLibrary().catch((err) => say(err.message, 9000));
}

/* the menu behind the band's name on Sift's screens, the review open there, or none for a screening with no review */
function siftBandMenu() {
  const rv = onScreen('sift') && typeof SF !== 'undefined' ? SF.review
    : onScreen('sift-search') && typeof SFS !== 'undefined' ? SFS.review : null;
  if (!rv || typeof rv !== 'object' || !rv.folder) return null;
  const where = { window: windowPicks(), mac: MAC };
  const r = { folder: rv.folder, name: rv.name, there: true };
  return { rows: siftMenuRows(siftMenuItems(r, where), where), pick: (act) => siftMenuDo(act, r, true) };
}

/* ──────────────────────────────── a Sift project's own parts ── */

/* Under Sift, after Databases, a Sift project's own parts, which Sift's own card held before (9
   October): a row of the Sift projects' names when there are several, each standing for its newest
   screening, the screening open on Sift's screen first and chosen, an earlier run's included. PDFs,
   whatever the AI switch says, Find open-access PDFs with the email Unpaywall asks for (see
   sfOaShow in sift.js). With AI features ticked, AI proposals, the switch, the prompt and the model
   its calls go to, and the bench under them, which tries the prompt as the box holds it on a record
   of the project chosen. The AI proposals live in sift.json beside the screening's CSV, read only
   with the switch on, and written on Save only when they have changed, after the switch itself is
   saved. A project with no screening yet has its Project part alone (12 October), and with no
   project at all the part stays hidden. A server from before it says to restart. */
const SFA = { list: [], at: null, rv: null, held: new Map(), drafts: new Map(), ask: 0, done: [], twoTurned: false, want: null };

/* the part emptied and hidden, as Settings opens, and nothing asked while the switch is off */
function sfaReset() {
  SFA.ask += 1;
  Object.assign(SFA, { list: [], at: null, rv: null, held: new Map(), drafts: new Map() });
  $('sfp-block').hidden = true;
  // the row of names stands over Databases, outside the project's block, so it goes with it (15 October, later)
  $('sfp-pick').hidden = true;
  $('sfa-inner').hidden = true;
  $('sfa-restart').hidden = true;
}

/* Every Sift project in the list whose folder is there, each `{ review, folder, name, question, root }`,
   `folder` the screening its Screening step opens or empty, the one open on Sift's screen or its
   Search strategy first, with the run open named, and the first chosen, drawn on every open whatever
   the switch says */
function sfpLoad() {
  const rows = (S.lib && Array.isArray(S.lib.reviews) ? S.lib.reviews : []).filter((r) => r.there);
  const list = rows.map((r) => ({ review: r.folder, folder: r.screening || '', name: r.name, question: r.question || '',
    root: r.folder, second: r.second || null }));
  const open = onScreen('sift') && typeof SF !== 'undefined' && SF.folder ? SF.folder : null;
  const rv = open && SF.review && typeof SF.review === 'object' ? SF.review : null;
  const searching = !open && onScreen('sift-search') && typeof SFS !== 'undefined' && SFS.review ? SFS.review : null;
  // or the project whose menu asked for its settings (barsD), from Home or its band
  const asked = SFA.want ? { folder: SFA.want } : null;
  SFA.want = null;
  const mine = rv || searching || asked;
  const at = mine ? list.findIndex((r) => r.review === mine.folder) : -1;
  if (open) {
    const named = (rv && rv.name) || t('sift_settings.this_screening');
    const name = rv && rv.run ? t('sift_settings.name_run', { name: named, day: reviewDay(rv.run) }) : named;
    const item = at >= 0 ? Object.assign(list.splice(at, 1)[0], { folder: open, label: name })
      : { review: null, folder: open, name, question: '', root: '', label: name };
    SFA.list = [item, ...list];
  } else SFA.list = at >= 0 ? [list[at], ...list.filter((_, i) => i !== at)] : list;
  $('sfp-none').hidden = SFA.list.length > 0;
  if (!SFA.list.length) return;
  $('sfp-block').hidden = false;
  sfpShow(SFA.list[0], false);
}

/* one project chosen: its Project part, its PDFs part at once when it has a screening, and its AI
   proposals with the switch ticked, which Settings' own opening asks for through `aiSetLoad` */
function sfpShow(item, ai = true) {
  sfaKeep();
  sfpKeep();
  SFA.rv = item;
  SFA.at = item.folder || null;
  sfaPick();
  sfpOwnDraw();
  $('sfp-pdfs').hidden = !SFA.at;
  if (!SFA.at) { $('sfa-inner').hidden = true; return; }
  if (typeof sfOaShow === 'function') sfOaShow();
  if (ai && $('set-ai').checked) sfaShow(SFA.at);
}

/* The Project part, as a Distil project's under Projects (12 October): the name and the research
   question as typed and not yet saved, else as the list gives them, the folder, and Remove from
   Idiograph. A screening opened from no project in the list has no Project part. */
function sfpOwnDraw() {
  const item = SFA.rv;
  $('sfp-own').hidden = !item || !item.review;
  sfpSaid('');
  if (!item || !item.review) return;
  const draft = SFA.drafts.get(item.review);
  $('sfp-name').value = draft ? draft.name : item.name || '';
  $('sfp-question').value = draft ? draft.question : item.question || '';
  $('sfp-root').innerHTML = pathHtml(item.root);
  sfpTwoDraw();
}

/* The Second screener part, under the Project part (12 October): the switch, off on a new project,
   then his name or initials and theirs, the share drawn at each stage, every record or a share in
   per cent, the calibration records and the kappa below which Sift offers a further draw, each as
   typed and not yet saved, else as the list gives them. The fields stand only while the switch is on. */
const SFP_TWO = { on: false, first: '', name: '', share: 100, calibration: 0, kappa: 0.6 };

function sfpTwoDraw() {
  const item = SFA.rv;
  $('sfp-two').hidden = !item || !item.review;
  if ($('sfp-two').hidden) return;
  const draft = SFA.drafts.get(item.review);
  const t = Object.assign({}, SFP_TWO, item.second || {}, (draft && draft.second) || {});
  const every = Number(t.share) >= 100;
  $('sfp-two-on').checked = !!t.on;
  $('sfp-two-first').value = t.first || '';
  $('sfp-two-name').value = t.name || '';
  $('sfp-two-every').value = every ? 'every' : 'share';
  $('sfp-two-share').value = every ? '' : String(t.share);
  $('sfp-two-cal').value = String(Number(t.calibration) || 0);
  $('sfp-two-kappa').value = String(t.kappa === undefined || t.kappa === null ? 0.6 : t.kappa);
  sfpTwoShow();
}

/* the fields shown while the switch is on, and the per cent while a share is chosen */
function sfpTwoShow() {
  $('sfp-two-fields').hidden = !$('sfp-two-on').checked;
  const every = $('sfp-two-every').value === 'every';
  $('sfp-two-share').hidden = every;
  $('sfp-two-pc').hidden = every;
}

/* the settings as the fields hold them, a number left empty taking its default and each kept to its
   bounds, a share chosen with no number 20 per cent */
function sfpTwoRead() {
  const num = (id, d) => { const v = Number($(id).value); return $(id).value.trim() !== '' && Number.isFinite(v) ? v : d; };
  const every = $('sfp-two-every').value === 'every';
  return { on: $('sfp-two-on').checked, first: $('sfp-two-first').value.trim(), name: $('sfp-two-name').value.trim(),
    share: every ? 100 : Math.max(1, Math.min(99, Math.round(num('sfp-two-share', 20)))),
    calibration: Math.max(0, Math.min(2000, Math.round(num('sfp-two-cal', 0)))),
    kappa: Math.round(Math.max(0, Math.min(1, num('sfp-two-kappa', 0.6))) * 100) / 100 };
}

/* the settings in one order, so two can be told apart by their text */
const sfpTwoKey = (t) => JSON.stringify(['on', 'first', 'name', 'share', 'calibration', 'kappa']
  .map((k) => (t || {})[k] === undefined ? SFP_TWO[k] : t[k]));

/* what is typed for the project shown, kept while another is shown */
function sfpKeep() {
  const item = SFA.rv;
  if (!item || !item.review || $('sfp-own').hidden) return;
  SFA.drafts.set(item.review, { name: $('sfp-name').value, question: $('sfp-question').value,
    second: $('sfp-two').hidden ? null : sfpTwoRead() });
}

function sfpSaid(text, failed = false) {
  saidIn('sfp-said', text || '', failed);
  $('sfp-said').hidden = !text;
}

/* What Save sends for the Sift projects: each one whose name or question changed, by its folder, and
   each whose second screener settings changed. A name left empty keeps the one it had. */
function sfpSaves() {
  sfpKeep();
  const out = [];
  for (const item of SFA.list) {
    const draft = item.review ? SFA.drafts.get(item.review) : null;
    if (!draft) continue;
    const name = draft.name.trim() || item.name;
    const question = draft.question.trim();
    if (name !== item.name || question !== String(item.question || '').trim()) {
      out.push({ op: 'rename', folder: item.review, name, question });
    }
    if (draft.second && sfpTwoKey(draft.second) !== sfpTwoKey(Object.assign({}, SFP_TWO, item.second || {}))) {
      out.push({ op: 'second', folder: item.review, second: draft.second });
    }
  }
  return out;
}

/* Remove from Sift, after Remove's card, as a Distil project's: the project taken out of the list, its folder and
   every file in it left as they are, or with the card's tick moved to the system's Trash (removetrash). From over
   the project itself the page opens on the home screen, since the screen belongs to no project now. */
async function sfpRemove() {
  const item = SFA.rv;
  if (!item || !item.review) return;
  const asked = await askRemove(item.name || t('sift_settings.this_project'));
  if (!asked) return;
  let data;
  try {
    data = await api('/api/sift-review', { op: 'forget', folder: item.review, trash: asked.trash, page: pageId() });
  } catch (err) { sfpSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); return; }
  const here = (onScreen('sift') && typeof SF !== 'undefined' && SF.review && SF.review.folder === item.review)
    || (onScreen('sift-search') && typeof SFS !== 'undefined' && SFS.review && SFS.review.folder === item.review);
  if (here) { S.noSpot = true; location.reload(); return; }
  if (S.lib && Array.isArray(data.reviews)) S.lib.reviews = data.reviews;
  SFA.drafts.delete(item.review);
  SFA.held.delete(item.folder);
  const left = SFA.list.filter((r) => r !== item);
  SFA.list = left;
  if (!left.length) { $('sfp-block').hidden = true; $('sfp-pick').hidden = true; } else sfpShow(left[0]);
  if (!$('library').hidden) loadLibrary().catch((err) => say(err.message, 9000));
  say(removedSaid(data.name || item.name, data, t('sift_settings.removed', { name: data.name || item.name })));
}

/* the screening this page is in front of, by its folder, for the beat (beat.js), so another window's Remove never
   moves it to the Trash (removetrash) */
window.idiographAt = () => {
  if (onScreen('sift') && typeof SF !== 'undefined' && SF.review && SF.review.folder) return SF.review.folder;
  if (onScreen('sift-search') && typeof SFS !== 'undefined' && SFS.review && SFS.review.folder) return SFS.review.folder;
  return '';
};

/* the screening chosen under Sift, which Find open-access PDFs and the bench work on */
const sfaFolder = () => SFA.at;

/* asked with the switch on, from `aiSetLoad`, as the card opens or the switch is ticked in it */
async function sfaLoad() {
  if (!SFA.at) return;
  await sfaShow(SFA.at);
}

/* one screening's AI settings, asked of the server once and kept while another is shown, and the
   bench given its records */
async function sfaShow(folder, ask = SFA.ask) {
  $('sfa-inner').hidden = false;
  if (!SFA.held.has(folder)) {
    let data;
    try {
      data = await api('/api/sift', { op: 'ai', folder });
    } catch (err) {
      if (ask !== SFA.ask) return;
      $('sfa-fields').hidden = true;
      $('sfa-restart').hidden = !needsRestart(err);
      if (!needsRestart(err)) say(err.message, 9000);
      return;
    }
    if (ask !== SFA.ask || !data.ai) return;
    SFA.held.set(folder, { was: { on: !!data.ai.on, prompt: data.ai.prompt || '' }, on: !!data.ai.on,
      prompt: data.ai.prompt || '', default: data.ai.default || '', model: data.ai.model_name || '' });
  }
  if (SFA.at !== folder) return;
  const h = SFA.held.get(folder);
  $('sfa-ai').checked = h.on;
  $('sfa-prompt').value = h.prompt;
  $('sfa-model').textContent = h.model ? t('sift_settings.calls_go', { model: h.model }) : '';
  $('sfa-restart').hidden = true;
  $('sfa-fields').hidden = false;
  if (typeof sfBenchFill === 'function') sfBenchFill(folder, h.model);
}

/* what is typed for the screening shown, kept while another is shown */
function sfaKeep() {
  const h = SFA.at ? SFA.held.get(SFA.at) : null;
  if (!h || $('sfa-fields').hidden) return;
  h.on = $('sfa-ai').checked;
  h.prompt = $('sfa-prompt').value;
}

/* the row of names, the one shown pressed, and none while there is one */
function sfaPick() {
  const box = $('sfp-pick');
  box.hidden = SFA.list.length < 2;
  box.innerHTML = SFA.list.map((r, i) => `<button type="button" class="ghost small${r === SFA.rv ? ' on' : ''}"`
    + ` data-i="${i}" aria-pressed="${r === SFA.rv}">${esc(r.label || r.name)}</button>`).join('');
  box.onclick = (e) => {
    const b = e.target.closest('[data-i]');
    const r = b ? SFA.list[Number(b.dataset.i)] : null;
    if (r && r !== SFA.rv) sfpShow(r);
  };
}

/* What Save sends for Sift's AI proposals: each screening whose switch or prompt changed, and
   nothing with AI features unticked. */
function sfaSaves() {
  sfaKeep();
  if (!$('set-ai').checked) return [];
  const out = [];
  for (const [folder, h] of SFA.held) {
    if (h.on !== h.was.on || h.prompt !== h.was.prompt) out.push({ op: 'settings', folder, ai_proposals: h.on, prompt: h.prompt });
  }
  return out;
}

/* ───────────────────────────────────────────── Zotero in Settings ── */

/* Under Sift, last, whatever the AI switch says, since a sync calls no model: the Zotero library a
   sync goes to, his own, which is the key's owner's, or a group's by its id, and the key. The key
   goes at once with its own Save, to the keychain as every key does, its field emptied as it goes
   and showing only Saved or Not set, and is checked at once, as the library is when it changes,
   Zotero's answer said in one line. Remove deletes it. The library and the group's id go with Save
   at the foot. A server from before it says to restart in their place. */
const ZOT = { opened: null, saved: false, ask: 0 };

async function zotLoad() {
  ZOT.ask += 1;
  const ask = ZOT.ask;
  ZOT.opened = null;
  saidIn('zot-said', '');
  $('zot-key').value = '';
  let got;
  try {
    got = await api('/api/zotero', { op: 'read' });
  } catch (err) {
    if (ask !== ZOT.ask) return;
    $('zot-restart').hidden = !needsRestart(err);
    $('zot-fields').hidden = needsRestart(err);
    if (!needsRestart(err)) saidIn('zot-said', err.message, true);
    return;
  }
  if (ask !== ZOT.ask) return;
  const st = got.settings || {};
  ZOT.opened = { library: st.library === 'group' ? 'group' : 'user', group_id: st.group_id || '' };
  ZOT.saved = !!got.saved;
  $('zot-library').value = ZOT.opened.library;
  $('zot-group').value = ZOT.opened.group_id;
  $('zot-restart').hidden = true;
  $('zot-fields').hidden = false;
  zotDraw();
}

function zotDraw() {
  $('zot-group-row').hidden = $('zot-library').value !== 'group';
  $('zot-key').placeholder = ZOT.saved ? t('sift_settings.saved') : t('sift_settings.not_set');
  $('zot-key-clear').hidden = !ZOT.saved;
}

/* the library and the group's id as the fields hold them, digits alone */
function zotNow() {
  const digits = (v) => String(v || '').replace(/\D/g, '').slice(0, 12);
  return { library: $('zot-library').value === 'group' ? 'group' : 'user', group_id: digits($('zot-group').value) };
}

/* What Save sends for Zotero, or null when nothing there has changed or it was never drawn. */
function zotBody() {
  if (!ZOT.opened) return null;
  const now = zotNow();
  return ['library', 'group_id'].some((k) => now[k] !== ZOT.opened[k]) ? now : null;
}

/* the field is emptied as soon as the value is on its way, so the key is not left sitting in the page */
async function zotSaveKey() {
  const value = $('zot-key').value;
  if (!value.trim()) { $('zot-key').focus(); return; }
  $('zot-key').value = '';
  try {
    await api('/api/zotero', { op: 'key', key: value });
    ZOT.saved = true;
    zotDraw();
    zotCheck();
    return;
  } catch (err) { saidErr('zot-said', err); }
  zotDraw();
}

async function zotClearKey() {
  try {
    const got = await api('/api/zotero', { op: 'clear' });
    ZOT.saved = false;
    saidIn('zot-said', got.cleared ? t('sift_settings.key_removed') : t('sift_settings.no_key'));
  } catch (err) { saidErr('zot-said', err); }
  zotDraw();
}

/* Zotero's answer for the key saved and the library as the fields hold them, the newest asked kept */
async function zotCheck() {
  const now = zotNow();
  if (!ZOT.saved || (now.library === 'group' && !now.group_id)) { saidIn('zot-said', ''); return; }
  ZOT.ask += 1;
  const ask = ZOT.ask;
  saidIn('zot-said', t('sift_settings.checking'));
  let said;
  let failed = false;
  try {
    const got = await api('/api/zotero', { op: 'check', settings: now });
    said = got.said || '';
    failed = got.ok === false;
  } catch (err) { said = needsRestart(err) ? RESTART_LINE : err.message; failed = !needsRestart(err); }
  if (ask === ZOT.ask) saidIn('zot-said', said, failed);
}

function zotBoot() {
  $('zot-library').onchange = () => { zotDraw(); zotCheck(); };
  $('zot-group').addEventListener('change', zotCheck);
  $('zot-key-save').onclick = zotSaveKey;
  $('zot-key').onkeydown = (e) => { if (e.key === 'Enter') { e.preventDefault(); zotSaveKey(); } };
  $('zot-key-clear').onclick = zotClearKey;
}

/* ─────────────────────────────────────── Sift's parts of the shell ── */

/* what the New project card's route made or opened, a Sift project, opened on its step: a project made on
   Search strategy, as Distil's New project opens the project it made, and one opened on its step */
function sfpMade(got) {
  if (got.review) rvShow(got.review);
  else loadLibrary().catch((err) => say(err.message, 9000));
}

/* a Sift project opened on the screen kept for a reload, its screening or its Search strategy */
function sfOpenOn(path, home, screen) {
  if (screen === 'searches') sfsOpen(path, home);
  else siftOpen(path, home);
}

/* Settings' parts that follow the AI's as the card opens: Zotero, whatever the AI switch says, since a sync
   calls no model, and Sift's databases, whatever the switch says, asked for on every open */
function sfpLater() {
  zotLoad();
  if (typeof dbsLoad === 'function') dbsLoad(false);
}

/* Save's body: Sift's databases as the list under Sift holds them, once the server has drawn it, and the
   Zotero library and its ids, once they have changed, never the key */
function sfpBody(body) {
  const dbs = typeof dbsBody === 'function' ? dbsBody() : null;
  if (dbs) body.databases = dbs;
  const zot = zotBody();
  if (zot) body.zotero = zot;
}

/* What Save sends for Sift, worked out before anything is sent: its AI proposals, each screening's to its own
   sift.json, after the switch is saved, and each Sift project's name, question and second screener, to the
   app's own list and never its folder (12 October) */
const sfpSendsAll = () => ({ ai: sfaSaves(), projects: sfpSaves() });

/* Save's sends for Sift, after the settings, each screening's AI proposals then each project's own, what came
   back kept for `sfpSettingsSaved`, the screen's second screener among it */
async function sfpSend(sends) {
  SFA.done = [];
  SFA.twoTurned = false;
  for (const sent of sends.ai) SFA.done.push({ folder: sent.folder, ai: (await api('/api/sift', sent)).ai || null });
  for (const sent of sends.projects) {
    const answer = (await api('/api/sift-review', sent)).review || null;
    if (!answer) continue;
    const own = { name: answer.name, question: answer.question, second: answer.second || null };
    if (S.lib && Array.isArray(S.lib.reviews)) {
      S.lib.reviews = S.lib.reviews.map((r) => (r.folder === sent.folder ? Object.assign({}, r, own) : r));
    }
    // the project open on Sift's screen or its Search strategy takes its name and question at once,
    // and Sift's screen its second screener, read afresh once Settings shuts
    if (typeof SF !== 'undefined' && SF.review && SF.review.folder === sent.folder) {
      Object.assign(SF.review, own);
      if (onScreen('sift') && typeof rvHead === 'function') rvHead('screening', SF.review);
      if (sent.op === 'second' && onScreen('sift')) SFA.twoTurned = true;
    }
    if (typeof SFS !== 'undefined' && SFS.review && SFS.review.folder === sent.folder) {
      Object.assign(SFS.review, { name: answer.name, question: answer.question });
      if (onScreen('sift-search') && typeof rvHead === 'function') rvHead('searches', SFS.review);
    }
  }
}

/* A Save over Sift's screens: over its searches the plan's databases take the list at once, and over its
   screen the screening takes its own AI settings at once, and a switch turned, a read afresh */
async function sfpSettingsSaved(data) {
  if (typeof sfsSettingsSaved === 'function') sfsSettingsSaved();
  if (onScreen('sift') && typeof SF !== 'undefined') {
    const mine = (SFA.done || []).find((d) => d.folder === SF.folder);
    if ((SFA.twoTurned || (data.config && aiOn(data.config) !== SF.aiMaster)) && typeof sfReload === 'function') { await SF.chain; sfReload(); }
    else if (mine && typeof sfDraw === 'function') { SF.ai = mine.ai; sfDraw(); }
  }
}

/* the screen kept for a reload: Sift on its screening, kept as the folder alone, since the record it was on
   is kept in the browser, and a review on its searches by the review's folder */
function siftSpot() {
  if ($('sift') && !$('sift').hidden && typeof SF !== 'undefined' && SF.folder) return { screen: 'sift', path: SF.folder };
  if ($('sift-search') && !$('sift-search').hidden && typeof SFS !== 'undefined' && SFS.folder) return { screen: 'searches', path: SFS.folder };
  return null;
}

/* Search on Sift's two screens: its place, its menus put away as the card opens, its leaving and its landing,
   the screening's in sift.js and Search strategy's in sift_search.js */
const siftSearchWhere = () => sfSearchWhere() || sfsSearchWhere();
const siftSearchClear = (here) => { if (here.screen === 'sift') sfMenuOpen(false, false); };
const siftSearchLeave = (here) => (here.screen === 'searches' ? sfsSearchLeave() : sfSearchLeave());
const siftSearchTo = (go) => (go.screen === 'searches' ? searchToPlan(go) : searchToSift(go));

/* the wiring of Sift's parts of Home and Settings */
function sfpBoot() {
  // Sift's AI proposals under Sift in Settings: Reset to default puts the prompt it ships with back
  $('sfa-reset').onclick = () => {
    const h = SFA.at ? SFA.held.get(SFA.at) : null;
    if (h) $('sfa-prompt').value = h.default;
  };
  // a Sift project's Remove from Idiograph under Sift in Settings
  $('sfp-remove').onclick = () => sfpRemove();
  $('sfp-two-on').addEventListener('change', sfpTwoShow);
  $('sfp-two-every').addEventListener('change', () => {
    if ($('sfp-two-every').value === 'share' && !$('sfp-two-share').value) $('sfp-two-share').value = '20';
    sfpTwoShow();
  });
  // Zotero under Sift in Settings: the library, its key's Save, checked at once, and Remove
  zotBoot();
  // Sift's New project and Open project folder, under its cards, and their card (app.js)
  $('sift-new').onclick = () => openReviewCard('new');
  $('sift-open').onclick = () => openReviewCard('open');
}

FAMILY_APPS.sift = {
  screen: 'sift', screens: ['sift', 'searches'], route: '/api/sift-review', made: sfpMade, open: sfOpenOn,
  home: drawSiftHome, recent: siftRecent, settingsReset: sfaReset, settingsLoad: sfpLoad, aiLoad: sfaLoad, settingsLater: sfpLater,
  settingsBody: sfpBody, settingsSends: sfpSendsAll, settingsSend: sfpSend, settingsSaved: sfpSettingsSaved,
  spot: siftSpot, searchWhere: siftSearchWhere, searchClear: siftSearchClear, searchLeave: siftSearchLeave,
  searchTo: siftSearchTo,
};
// the home screen's answer may come before this script is read, and Sift's section then takes it now
if (APP === 'sift' && S.lib) drawSiftHome(S.lib);

sfpBoot();

/* Sift's commands by name for people in its agent log (siftlog, 3 November 2026), each by its words, an MCP tool's
   by its command, added to the family's table (agentlog.js) */
Object.assign(AL_OPS, {
  'sift list': 'agentlog_sift.list',
  'sift show': 'agentlog_sift.show',
  'sift counts': 'agentlog_sift.counts',
  'sift export': 'agentlog_sift.export',
  'sift prisma': 'agentlog_sift.prisma',
  'sift form': 'agentlog_sift.form',
  'sift add': 'agentlog_sift.add',
  'sift propose': 'agentlog_sift.propose',
  'sift reset': 'agentlog_sift.reset',
  'sift plan': 'agentlog_sift.plan',
  'sift strings': 'agentlog_sift.strings',
  'sift register': 'agentlog_sift.register',
  'sift run': 'agentlog_sift.run',
  'sift runs': 'agentlog_sift.runs',
  'sift databases': 'agentlog_sift.databases',
  'sift sync': 'agentlog_sift.sync',
  'search': 'agentlog_sift.search',
});
