/* The Trajectories board (21 October, timepoints part 3, Adam's model after Farr and Nizza 2019), laid out as his
   Freeform page lays revD out (layout F, trajbuild2, 10 November 2026).

   After the LGETs, in a project of two or more timepoints: the project's own trajectories, made and named on the
   board itself, never fixed by the app. Each is a band down the screen, its head shaded in its colour with its
   icon, its title and its sentence, then the timepoints across, "T1: Before the season", then each participant
   placed in it: their picture, name, own label and tags, and each of their LPETs a row, its title and domain, then
   at each timepoint its key quote over its state. A cell is that LPET's row of the LPET table at that timepoint, so
   its state is the row's note and its key quote the row's tick, the first quote standing in fainter until he ticks
   one, and a click on the quote opens the quotes it can take: the LPET's own, then the participant's other quotes
   from that interview, then a passage of the transcript, found in a picker under the row, any of their interviews
   (trajchoose, 11 November 2026). Words chosen in a key quote go bold with Cmd+B, kept on the row, never in the
   transcript.

   A trajectory's title and sentence are typed in place, its swatch opens its colour and icon, New trajectory adds
   one, and its cross takes it away, its participants going back to Not placed with all that is kept on them. A
   participant moves by dragging their cell onto a band, at the place they are dropped, by Move to in their menu,
   and with the keys while their cell has the focus: Up and Down in their trajectory, Left and Right to the one
   before or after, Backspace to Not placed. A double-click on their cell, or Edit in its menu, opens their editor
   in place: their picture, their own or one of the set, their label, their tags, a tag's colour, and which LPETs
   show here. The status bar along the foot counts them and holds Quotes, off, short or full, and Notes, each
   participant's note, the old Why, and the board's own note under the question (trajnote, 10 November 2026), typed
   in place as a sentence is, both kept in the settings.

   Every change goes through /api/trajectories-ops with the same operations an agent's command line sends
   (trajectories.py on the server, an LPET's row through gets.row_op), and the board is drawn again from the
   answer. Nothing is kept in the browser, except whether the Not placed band shows: its button at the bar's left
   end hides it and shows it again as the boards' left sidebar button does (10 November 2026). */

const TJ_SIDE_KEY = 'idiograph-trajectories-side';
const TJ = { path: '', back: null, to: 'cases', data: null, ask: 0, busy: false, drag: null, project: null, sideOpen: true,
  editing: '', picking: '', choosing: '', menu: '', faces: false, tagOpen: '',
  // Choose from the set's tab chosen, '' for the set of the picture now (picsets)
  faceSet: '',
  // the passage picker (trajchoose, 11 November 2026): the cell it is open for, the interview shown, the words
  // found, the turns read for each participant's interview, and the words chosen in a turn
  passage: '', passageAt: '', find: '', turns: {}, picked: null };
const TJ_NOT_PLACED = t('trajectories.not_placed');
const TJ_QUOTES_WAYS = ['off', 'short', 'full'];
// each way's words and each icon's name, every key written out so the catalogue's check finds it
const TJ_QUOTES_SAID = { off: () => t('trajectories.quotes_off'), short: () => t('trajectories.quotes_short'), full: () => t('trajectories.quotes_full') };
const TJ_ICON_SAID = { rising: () => t('trajectories.icon_rising'), mixed: () => t('trajectories.icon_mixed'),
  falling: () => t('trajectories.icon_falling'), level: () => t('trajectories.icon_level') };
const TJ_X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6L6 18"/></svg>';
const TJ_PLUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M12 5v14M5 12h14"/></svg>';
const TJ_MORE = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><circle cx="5.5" cy="12" r="1.7"/><circle cx="12" cy="12" r="1.7"/><circle cx="18.5" cy="12" r="1.7"/></svg>';
const TJ_ICONS = {
  rising: '<svg viewBox="0 0 48 32" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4 28 18 15l8 7 16-16"/><path d="M31 5h12v12"/></svg>',
  mixed: '<svg viewBox="0 0 48 32" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M3 12l9 9 9-9 9 9 8-8"/><path d="M33 9h7v7"/></svg>',
  falling: '<svg viewBox="0 0 48 32" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4 4l14 13 8-7 16 16"/><path d="M31 27h12V15"/></svg>',
  level: '<svg viewBox="0 0 48 32" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4 16h38"/><path d="M34 9l8 7-8 7"/></svg>',
};
// a trajectory's colour as its token, the names the file keeps
const TJ_TOKENS = { good: '--good', amber: '--amber', danger: '--danger', excerpt: '--excerpt', sift: '--part-sift',
  trace: '--part-trace', accent: '--accent', crux: '--crux' };
// the first eight of the participants' palette, which a tag's colour row offers
const TJ_TAG_COLOURS = 8;

/* the board opened for the project a workbook belongs to, `how` as openStatements takes it: `leave` puts the
   screen it came from away once the board is in, `back` returns there, `to` names that screen */
async function trajOpen(path, how = {}) {
  const ask = ++TJ.ask;
  let data;
  try {
    data = await api('/api/trajectories', { workbook: path });
  } catch (err) {
    if (ask !== TJ.ask) return false;
    if (how.gone) { how.gone(); return false; }
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return false;
  }
  if (ask !== TJ.ask) return false;
  if (how.leave) how.leave();
  TJ.path = path;
  TJ.back = how.back || null;
  TJ.to = typeof TH_STEPS !== 'undefined' && TH_STEPS.includes(how.to) ? how.to : 'cases';
  Object.assign(TJ, { editing: '', picking: '', choosing: '', menu: '', faces: false, tagOpen: '', passage: '', passageAt: '',
    find: '', turns: {}, picked: null });
  $('traj').hidden = false;
  TJ.sideOpen = trajSideStored();
  trajLoad(data);
  return true;
}

function trajLoad(data) {
  TJ.data = data;
  TJ.project = data.project || null;
  pathProjectDraw('tj-project', TJ.project);
  $('tj-demo').hidden = !data.demo;
  dsTabsDraw('tj-steps', TJ.project, 'trajectories');
  // the band always, for the path at its head, and the question after it where the project has one: the
  // screen's title is the research question (his ruling of 10 November)
  const question = TJ.project && TJ.project.research_question;
  $('tj-band').classList.toggle('band-unasked', !question);
  $('tj-band-question').textContent = question || '';
  trajDraw();
}

/* the way back, true once the board is put away */
async function trajLeave() {
  if (document.activeElement && $('traj').contains(document.activeElement)) document.activeElement.blur();
  await trajIdle();
  $('traj').hidden = true;
  TJ.ask += 1;
  if (TJ.back) await TJ.back();
  else loadLibrary().catch((err) => say(err.message, 9000));
  return true;
}

async function trajBack() {
  if (typeof navBackNow === 'function' && navBackNow()) return;
  await trajLeave();
}

/* a change in flight finished first, so a title or a note left on the way out is kept */
async function trajIdle() {
  for (let i = 0; TJ.busy && i < 50; i += 1) await new Promise((r) => setTimeout(r, 40));
}

/* ── drawing ── */

const tjCard = (case_) => ((TJ.data && TJ.data.participants) || []).find((c) => c.case === case_) || null;
const tjCol = (id) => ((TJ.data && TJ.data.columns) || []).find((c) => c.id === id) || null;
const tjConfig = () => (TJ.data && TJ.data.config) || {};
const tjQuotesWay = () => (TJ_QUOTES_WAYS.includes(tjConfig().traj_quotes) ? tjConfig().traj_quotes : 'short');
const tjNotesOn = () => tjConfig().traj_notes === true;
const tjTimepoints = () => {
  const tps = (TJ.data && TJ.data.timepoints) || [];
  return tps.map((tp) => ({ key: `T${tp.n}`, label: tp.label, description: tp.description || '' }));
};
const tjTpName = (tp) => (tp.description ? `${tp.label}: ${tp.description}` : tp.label);

/* whether the Not placed band shows, open unless he closed it, kept for the screen as the boards' sidebar is */
function trajSideStored() {
  try { return localStorage.getItem(TJ_SIDE_KEY) !== 'closed'; } catch { return true; }
}

function trajSideSet(open, keep = true) {
  TJ.sideOpen = !!open;
  if (keep) { try { localStorage.setItem(TJ_SIDE_KEY, TJ.sideOpen ? 'open' : 'closed'); } catch { /* private window */ } }
  trajDraw();
}

/* the button: pressed in while the band shows, the tooltip naming the other way, and the count not placed on
   it while the band is hidden, so a hidden band is never a lost one */
function trajDoorDraw() {
  const b = $('tj-open-side');
  if (!b) return;
  const name = TJ_NOT_PLACED;
  const n = ((TJ.data && TJ.data.unplaced) || []).length;
  b.classList.toggle('on', TJ.sideOpen);
  b.setAttribute('aria-pressed', String(TJ.sideOpen));
  b.title = TJ.sideOpen ? t('themes.side.hide', { name }) : t('themes.side.show', { name });
  b.setAttribute('aria-label', !TJ.sideOpen && n ? t('themes.side.door_label', { name, n }) : name);
  b.querySelector('.bar-word').textContent = name;
  let badge = b.querySelector('.th-door-n');
  if (!badge) {
    badge = document.createElement('span');
    badge.className = 'th-door-n';
    badge.setAttribute('aria-hidden', 'true');
    b.appendChild(badge);
  }
  badge.textContent = String(n);
  badge.hidden = !n || TJ.sideOpen;
}

/* the status bar: the counts in the boards' wording, then Quotes and Notes as they stand */
function trajStatusDraw() {
  const d = TJ.data || {};
  const all = (d.participants || []).length;
  const out = (d.unplaced || []).length;
  const n = (v) => `<span class="th-stat-n">${esc(String(v))}</span>`;
  const counts = $('tj-status-counts');
  if (counts) {
    counts.innerHTML = `<span class="th-stat">${t('trajectories.counts', { n: all, all: n(all), placed: n(all - out), unplaced: n(out) })}</span>`
      + `<span class="th-stat">${t('trajectories.n_trajectories', { n: (d.columns || []).length, count: n((d.columns || []).length) })}</span>`;
  }
  const q = $('tj-quotes-btn');
  if (q) {
    const way = tjQuotesWay();
    const said = TJ_QUOTES_SAID[way]();
    q.dataset.quotes = way;
    q.setAttribute('aria-pressed', String(way !== 'off'));
    q.title = said;
    q.setAttribute('aria-label', said);
  }
  const notes = $('tj-notes-btn');
  if (notes) {
    notes.setAttribute('aria-pressed', String(tjNotesOn()));
    notes.title = t('trajectories.notes_tip');
    notes.setAttribute('aria-label', t('trajectories.notes_tip'));
  }
}

/* the board drawn whole from TJ.data, the focus and a field's caret put back where they were */
function trajDraw() {
  const d = TJ.data;
  if (!d) return;
  const was = document.activeElement && $('tj-board').contains(document.activeElement) ? document.activeElement : null;
  const fkey = was && was.dataset ? was.dataset.fkey : '';
  const caret = was && typeof was.selectionStart === 'number' ? [was.selectionStart, was.selectionEnd] : null;
  trajDoorDraw();
  trajStatusDraw();
  trajNoteDraw();
  const bands = [...(TJ.sideOpen ? [{ id: '', title: TJ_NOT_PLACED, participants: d.unplaced || [], fixed: true }] : []), ...(d.columns || [])];
  let html = bands.map(trajBandHtml).join('');
  html += `<div class="tf-new"><button type="button" class="tj-new" id="tj-new" data-fkey="new">${TJ_PLUS}${esc(t('trajectories.new'))}</button></div>`;
  const board = $('tj-board');
  board.classList.add('tf-board');
  board.classList.toggle('tf-quotes-off', tjQuotesWay() === 'off');
  board.classList.toggle('tf-quotes-full', tjQuotesWay() === 'full');
  board.innerHTML = html;
  for (const box of board.querySelectorAll('textarea.tf-fit')) trajFit(box);
  if (fkey) {
    const again = board.querySelector(`[data-fkey="${CSS.escape(fkey)}"]`);
    if (again) {
      again.focus({ preventScroll: true });
      if (caret && typeof again.setSelectionRange === 'function') { try { again.setSelectionRange(caret[0], caret[1]); } catch { /* not a text field */ } }
    }
  }
}

/* the board's own note under the question, there only while Notes is on, its words left alone while he types */
function trajNoteDraw() {
  const box = $('tj-board-note');
  if (!box) return;
  box.hidden = !tjNotesOn();
  box.placeholder = t('trajectories.note_placeholder');
  box.setAttribute('aria-label', t('trajectories.board_note_label'));
  if (document.activeElement !== box) box.value = (TJ.data && TJ.data.note) || '';
  if (!box.hidden) trajFit(box);
}

/* a field as tall as its words, so the whole of a sentence, a state or a note shows */
function trajFit(box) {
  box.style.height = 'auto';
  box.style.height = `${box.scrollHeight + 2}px`;
}

function trajBandHtml(col) {
  const people = col.participants || [];
  const tc = col.fixed ? '' : (TJ_TOKENS[col.colour] ? `--tc:var(${TJ_TOKENS[col.colour]});` : '');
  const tps = tjTimepoints();
  let head;
  if (col.fixed) {
    head = `<header class="tf-head tf-head-none"><h2 class="tj-title tj-title-fixed">${esc(col.title)}</h2><span class="tj-count">${people.length}</span></header>`;
  } else {
    const icon = TJ_ICONS[col.icon] ? `<span class="tf-icon">${TJ_ICONS[col.icon]}</span>` : '<span class="tf-icon tf-icon-none"></span>';
    head = `<header class="tf-head">${icon}<div class="tf-headw">`
      + `<input class="tj-title tf-title" type="text" value="${escAttr(col.title)}" maxlength="60" data-col="${escAttr(col.id)}" data-fkey="title-${escAttr(col.id)}"
          aria-label="${escAttr(t('trajectories.title_label'))}" title="${escAttr(t('trajectories.title_tip'))}">`
      + `<textarea class="tf-desc tf-fit" rows="1" maxlength="400" data-desc="${escAttr(col.id)}" data-fkey="desc-${escAttr(col.id)}"
          aria-label="${escAttr(t('trajectories.sentence_label'))}" placeholder="${escAttr(t('trajectories.sentence_placeholder'))}">${esc(col.description || '')}</textarea></div>`
      + `<button type="button" class="tf-swatch" data-swatch="${escAttr(col.id)}" data-fkey="swatch-${escAttr(col.id)}" aria-expanded="${TJ.picking === col.id}"
          title="${escAttr(t('trajectories.colour_icon'))}" aria-label="${escAttr(t('trajectories.colour_icon'))}"><span></span></button>`
      + `<button type="button" class="tj-remove" data-remove="${escAttr(col.id)}" data-fkey="remove-${escAttr(col.id)}" aria-label="${escAttr(t('trajectories.remove_label', { title: col.title }))}"
          title="${escAttr(t('trajectories.remove_tip'))}">${TJ_X}</button><span class="tj-count">${people.length}</span></header>`;
  }
  const picker = !col.fixed && TJ.picking === col.id ? trajPickerHtml(col) : '';
  let rows = `<div class="tf-th tf-th0" aria-hidden="true"></div><div class="tf-th tf-th0" aria-hidden="true"></div>`
    + tps.map((tp) => `<div class="tf-th" title="${escAttr(tjTpName(tp))}">${esc(tjTpName(tp))}</div>`).join('');
  for (const case_ of people) rows += trajPersonHtml(case_, tps);
  // a band with nobody in it is its head alone, a place to drop a participant
  const grid = people.length ? `<div class="tf-grid" style="--tps:${tps.length}">${rows}</div>` : '<div class="tf-empty"></div>';
  return `<section class="tf-band${col.fixed ? ' tf-band-none' : ''}" role="listitem" data-col="${escAttr(col.id)}" style="${tc}">`
    + `${head}${picker}${grid}</section>`;
}

/* a trajectory's colour and icon, opened from its swatch, each kept at once */
function trajPickerHtml(col) {
  const palette = (TJ.data && TJ.data.palette) || {};
  const sw = Object.keys(TJ_TOKENS).map((k) => `<button type="button" class="tf-sw${col.colour === k ? ' on' : ''}" data-colour="${k}" data-col="${escAttr(col.id)}"
      data-fkey="sw-${escAttr(col.id)}-${k}" style="background:var(${TJ_TOKENS[k]})" title="${escAttr(palette[k] || k)}" aria-label="${escAttr(palette[k] || k)}" aria-pressed="${col.colour === k}"></button>`).join('');
  const ic = Object.keys(TJ_ICONS).map((k) => `<button type="button" class="tf-ic${col.icon === k ? ' on' : ''}" data-icon="${k}" data-col="${escAttr(col.id)}"
      data-fkey="ic-${escAttr(col.id)}-${k}" title="${escAttr(TJ_ICON_SAID[k]())}" aria-label="${escAttr(TJ_ICON_SAID[k]())}" aria-pressed="${col.icon === k}">${TJ_ICONS[k]}</button>`).join('')
    + `<button type="button" class="tf-ic tf-ic-none${col.icon ? '' : ' on'}" data-icon="" data-col="${escAttr(col.id)}" data-fkey="ic-${escAttr(col.id)}-none" aria-pressed="${!col.icon}">${esc(t('trajectories.none'))}</button>`;
  return `<div class="tf-cpick" role="group" aria-label="${escAttr(t('trajectories.colour_icon'))}"><span class="tf-cpick-l">${esc(t('trajectories.colour'))}</span>`
    + `<span class="tf-sws">${sw}<button type="button" class="tf-sw tf-sw-none${col.colour ? '' : ' on'}" data-colour="" data-col="${escAttr(col.id)}" data-fkey="sw-${escAttr(col.id)}-none"
        title="${escAttr(t('trajectories.none'))}" aria-label="${escAttr(t('trajectories.none'))}" aria-pressed="${!col.colour}"></button></span>`
    + `<span class="tf-cpick-l">${esc(t('trajectories.icon'))}</span><span class="tf-ics">${ic}</span>`
    + `<button type="button" class="primary small tf-done" data-pick-done="1" data-fkey="pick-done-${escAttr(col.id)}">${esc(t('trajectories.done'))}</button></div>`;
}

/* The app's drawn sets, each a tab in Choose from the set, in the order of trajectories.FACE_SETS on the server
   (picsets, 12 November 2026): eighty Open Peeps and forty Notionists, each a run of files in
   static/faces. The project page's fields (distil.js) offer the same, through faceSetsHtml. */
const FACE_SETS = [
  { set: 'peeps', name: 'trajectories.set_peeps', faces: tfFaceRun('peep', 80) },
  { set: 'notionists', name: 'trajectories.set_notionists', faces: tfFaceRun('notion', 40) },
];

function tfFaceRun(stem, count) {
  return Array.from({ length: count }, (_, i) => `${stem}${String(i + 1).padStart(2, '0')}`);
}

/* the set a picture is of, by where it is read, so one from the set before is on its nearest's tab, or none */
function faceSetOf(url) {
  return FACE_SETS.find((s) => s.faces.some((f) => url === `/faces/${f}.svg`)) || null;
}

/* Choose from the set: a tab for each set, `open` the one shown or, with none chosen yet, the set of the picture
   now, `url`, or the first, and that set's pictures under it, the picture now pressed. `pick` and `tab` are the
   data attributes its pictures' and its tabs' buttons carry, and `fkey` keeps Trajectories' focus across a draw. */
function faceSetsHtml(open, url, { pick, tab, fkey = false, cls = '' }) {
  const shown = FACE_SETS.find((s) => s.set === open) || faceSetOf(url) || FACE_SETS[0];
  const tabs = FACE_SETS.map((s) => {
    const on = s === shown;
    return `<button type="button" class="th-tab tf-settab${on ? ' on' : ''}" role="tab" aria-selected="${on}" tabindex="${on ? 0 : -1}"`
      + ` data-${tab}="${s.set}"${fkey ? ` data-fkey="faceset-${s.set}"` : ''}>${esc(t(s.name))}</button>`;
  }).join('');
  const faces = shown.faces.map((f, i) => {
    const on = url === `/faces/${f}.svg`;
    return `<button type="button" class="tf-face${on ? ' on' : ''}" data-${pick}="${f}"${fkey ? ` data-fkey="face-${f}"` : ''}`
      + ` aria-pressed="${on}" aria-label="${escAttr(t('trajectories.face_n', { n: i + 1 }))}"><img src="/faces/${f}.svg" alt=""></button>`;
  }).join('');
  return `<div class="tf-sets${cls ? ` ${cls}` : ''}"><div class="th-tabs tf-settabs" role="tablist" aria-label="${escAttr(t('trajectories.choose_face'))}">${tabs}</div>`
    + `<div class="tf-faces" role="tabpanel" aria-label="${escAttr(t(shown.name))}">${faces}</div></div>`;
}

/* a set's tab moved to by the arrow keys, Home and End, as a row of tabs answers them, or '' for another key */
function faceSetStep(key, now) {
  const at = Math.max(0, FACE_SETS.findIndex((s) => s.set === now));
  const to = { ArrowRight: at + 1, ArrowDown: at + 1, ArrowLeft: at - 1, ArrowUp: at - 1, Home: 0, End: FACE_SETS.length - 1 }[key];
  return to === undefined ? '' : FACE_SETS[(to + FACE_SETS.length) % FACE_SETS.length].set;
}

const tjPicHtml = (c, big) => {
  const size = big ? 56 : 40;
  const colour = `case-${(Number(c.colour) || 0) % 25}`;
  if (c.picture_url) {
    return `<span class="tf-pic ${colour}" style="width:${size}px;height:${size}px"><img src="${escAttr(c.picture_url)}" alt="${escAttr(t('trajectories.picture_of', { who: c.who }))}"></span>`;
  }
  return `<span class="tf-pic tf-pic-none ${colour}" style="width:${size}px;height:${size}px" aria-hidden="true">${esc((c.who || '?').slice(0, 1))}</span>`;
};
const tjPill = (word, n, more = '') => `<span class="tf-pill case-${(Number(n) || 0) % 25}"${more}>${esc(word)}</span>`;

function trajPersonHtml(case_, tps) {
  const c = tjCard(case_);
  if (!c) return '';
  const shown = (c.rows || []).filter((r) => r.shown !== false);
  // the passage picker open under one of their rows takes a row of the grid of its own
  const picking = shown.find((r) => TJ.passage.startsWith(`${c.case}|${r.id}|`));
  const span = Math.max(1, shown.length) + (picking ? 1 : 0);
  // the pills of the participant's demographics shown as pills, in place of its tags (demobuild), its tags from a
  // server from before
  const pills = Array.isArray(c.pills) ? c.pills : (c.tags || []);
  const tags = pills.length ? `<span class="tf-pills">${pills.map((tg) => tjPill(tg.word, tg.colour)).join('')}</span>` : '';
  const note = tjNotesOn()
    ? `<textarea class="tj-note tf-fit" rows="2" maxlength="2000" data-case="${escAttr(c.case)}" data-fkey="note-${escAttr(c.case)}"
        aria-label="${escAttr(t('trajectories.note_label', { who: c.who }))}" placeholder="${escAttr(t('trajectories.note_placeholder'))}">${esc(c.note || '')}</textarea>` : '';
  const menu = TJ.menu === c.case ? trajMenuHtml(c) : '';
  let html = TJ.editing === c.case ? trajEditHtml(c) : '';
  html += `<div class="tf-pcell" style="grid-row: span ${span}" draggable="true" tabindex="0" data-case="${escAttr(c.case)}" data-fkey="p-${escAttr(c.case)}"
      aria-label="${escAttr(c.who + (c.title ? `, ${c.title}` : ''))}"><div class="tf-who">${tjPicHtml(c)}`
    + `<b class="tf-name">${esc(c.who)}</b>${c.title ? `<span class="tf-label">${esc(c.title)}</span>` : ''}${tags}</div>`
    + `<button type="button" class="tf-more" data-more="${escAttr(c.case)}" data-fkey="more-${escAttr(c.case)}" aria-haspopup="menu" aria-expanded="${TJ.menu === c.case}"
        title="${escAttr(t('trajectories.menu', { who: c.who }))}" aria-label="${escAttr(t('trajectories.menu', { who: c.who }))}">${TJ_MORE}</button>${menu}${note}</div>`;
  if (!shown.length) {
    html += `<div class="tf-rowc tf-rowc-none" style="grid-column: 2 / -1">${esc(t((c.rows || []).length ? 'trajectories.no_lpets_shown' : 'trajectories.no_lpets'))}</div>`;
  }
  shown.forEach((r, i) => {
    const rule = i ? ' tf-rule' : '';
    // each of the LPET's domains a pill in its own colour, the server reading commas between them
    const domain = (r.domains || []).length ? `<span class="tf-pills">${r.domains.map((d) => tjPill(d.word, d.colour)).join('')}</span>` : '';
    html += `<div class="tf-rowc${rule}"><div class="tf-lpet"><p class="tf-ltitle">${esc(r.title)}</p>${domain}</div></div>`;
    for (const tp of tps) html += `<div class="tf-rowc${rule}">${trajCellHtml(c, r, tp)}</div>`;
    if (picking === r) html += trajPassHtml(c, r);
  });
  return `${html}<div class="tf-psep"></div>`;
}

/* a key quote's words with his bold, each span of `bold` a <b> */
function tjBoldHtml(text, bold) {
  const s = String(text || '');
  let out = '';
  let at = 0;
  for (const [a, b] of (bold || []).filter((x) => Array.isArray(x) && x[0] < x[1]).sort((x, y) => x[0] - y[0])) {
    if (a < at) continue;
    out += esc(s.slice(at, a)) + `<b>${esc(s.slice(a, b))}</b>`;
    at = b;
  }
  return out + esc(s.slice(at));
}

/* a quote's time without its timepoint, "T1, 03:12" read as 03:12 under the column T1 */
const tjTime = (time) => String(time || '').replace(/^[^,]*,\s*/, '');
/* a key quote's time in a cell: the timepoint before it only when the words come from another interview, as a
   passage of T3's transcript in a T2 cell does (trajchoose) */
const tjTimeIn = (q, tp) => (q.at && q.at !== tp.key ? String(q.time || '') : tjTime(q.time));
const TJ_TICK = '<span class="tf-tick" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" focusable="false"><path d="M3.5 8.5l3 3 6-7"/></svg></span>';

function trajCellHtml(c, r, tp) {
  const cell = (r.cells || {})[tp.key] || {};
  const id = `${c.case}|${r.id}|${tp.key}`;
  const q = cell.quote;
  let quote = '';
  if (tjQuotesWay() !== 'off') {
    const said = t('trajectories.key_quote', { tp: tp.label });
    // a cell with no quote of its own opens the chooser too, for a quote from elsewhere in the interview or the
    // transcript
    quote = q
      ? `<p class="tf-q${cell.chosen ? '' : ' tf-q-auto'}" tabindex="0" role="button" data-cell="${escAttr(id)}" data-fkey="q-${escAttr(id)}" aria-expanded="${TJ.choosing === id}"
          aria-label="${escAttr(said)}" title="${escAttr(t(cell.chosen ? 'trajectories.choose_quote' : 'trajectories.choose_quote_first'))}">“<span class="tf-qtext" data-qcell="${escAttr(id)}">${tjBoldHtml(q.text, cell.bold)}</span>” <span class="tf-time">${esc(tjTimeIn(q, tp))}</span></p>`
      : `<p class="tf-q tf-q-none" tabindex="0" role="button" data-cell="${escAttr(id)}" data-fkey="q-${escAttr(id)}" aria-expanded="${TJ.choosing === id}"
          aria-label="${escAttr(said)}" title="${escAttr(t('trajectories.choose_quote'))}">${esc(t('trajectories.no_quote'))}</p>`;
    if (TJ.choosing === id) quote += trajChooserHtml(id, c, cell, tp);
  }
  const state = `<textarea class="tf-state tf-fit" rows="1" maxlength="4000" data-state="${escAttr(id)}" data-fkey="s-${escAttr(id)}"
      aria-label="${escAttr(t('trajectories.state_label', { tp: tp.label, lpet: r.title }))}" placeholder="${escAttr(t('trajectories.state_placeholder'))}">${esc(cell.state || '')}</textarea>`;
  return `<div class="tf-cell">${quote}${state}</div>`;
}

/* the quotes a cell can take as its key quote, each with its tick, opened under the quote, from three places in
   his order (trajchoose, 11 November 2026): the LPET's own at that timepoint, the participant's other quotes from
   that interview, and a passage of the transcript, which opens the picker under the row */
function trajChooserHtml(id, c, cell, tp) {
  const q = cell.quote;
  const ticked = cell.chosen && q && q.source !== 'transcript' ? q.key : '';
  const own = cell.choices || [];
  const keys = new Set(own.map((x) => x.key));
  const others = ((c.quotes || {})[tp.key] || []).filter((x) => !keys.has(x.key));
  let n = 0;
  const row = (x) => `<button type="button" class="tf-choice${x.key === ticked ? ' on' : ''}" role="menuitemcheckbox"
      aria-checked="${x.key === ticked}" data-choose="${escAttr(id)}" data-qkey="${escAttr(x.key)}" data-fkey="ch-${escAttr(id)}-${n++}">`
    + `${TJ_TICK}<span class="tf-choice-w">“${esc(x.text)}” <span class="tf-time">${esc(tjTime(x.time))}</span></span></button>`;
  const part = (head, rows) => `<div class="tf-choose-part" role="group" aria-label="${escAttr(head)}"><p class="tf-choose-h" aria-hidden="true">${esc(head)}</p>${rows}</div>`;
  let html = '';
  if (own.length) html += part(t('trajectories.from_lpet'), own.map(row).join(''));
  if (others.length) html += part(t('trajectories.from_interview'), others.map(row).join(''));
  // the passage he took, ticked, then the way to choose one
  const taken = cell.chosen && q && q.source === 'transcript'
    ? `<button type="button" class="tf-choice on" role="menuitemcheckbox" aria-checked="true" data-choose="${escAttr(id)}" data-qkey="" data-fkey="ch-${escAttr(id)}-passage">`
      + `${TJ_TICK}<span class="tf-choice-w">“${esc(q.text)}” <span class="tf-time">${esc(tjTimeIn(q, tp))}</span></span></button>` : '';
  const open = TJ.passage === id;
  html += part(t('trajectories.from_transcript'), `${taken}<button type="button" class="tf-choice tf-choice-pass" role="menuitem" data-passage-open="${escAttr(id)}"
      data-fkey="ch-${escAttr(id)}-open" aria-expanded="${open}"><span class="tf-pass-ic" aria-hidden="true">${TJ_PLUS}</span><span class="tf-choice-w">${esc(t('trajectories.choose_passage'))}</span></button>`);
  return `<div class="tf-choose" role="menu" aria-label="${escAttr(t('trajectories.choose_quote'))}">${html}</div>`;
}

/* ── the passage picker: a turn of the participant's transcript found and its words taken as a key quote ── */

const tjTurnsKey = (case_, at) => `${case_}|${at}`;
const tjFlat = (s) => String(s || '').toLowerCase().replace(/\s+/g, ' ');

/* the picker under the row it was opened from: the interviews to switch between, the find box, the turns, and the
   words chosen in one taken or the whole turn */
function trajPassHtml(c, r) {
  const [, , tp] = TJ.passage.split('|');
  const at = TJ.passageAt || tp;
  const held = TJ.turns[tjTurnsKey(c.case, at)];
  const known = held ? held.interviews : [at];
  const tps = tjTimepoints().filter((x) => known.includes(x.key) || x.key === at);
  const tabs = tps.map((x) => `<button type="button" class="tf-pass-tp${x.key === at ? ' on' : ''}" data-pass-at="${escAttr(x.key)}" data-fkey="pass-at-${escAttr(x.key)}"
      aria-pressed="${x.key === at}" title="${escAttr(tjTpName(x))}">${esc(x.label)}</button>`).join('');
  const head = t('trajectories.from_transcript');
  return `<div class="tf-pass" role="group" aria-label="${escAttr(head)}" data-pass="${escAttr(TJ.passage)}">`
    + `<div class="tf-pass-head"><p class="tf-pass-l">${esc(head)}</p>`
    + `<span class="tf-pass-tps" role="group" aria-label="${escAttr(t('trajectories.interview'))}">${tabs}</span>`
    + `<input class="tf-pass-find" type="search" data-pass-find="1" data-fkey="pass-find" value="${escAttr(TJ.find)}"
        placeholder="${escAttr(t('trajectories.find_transcript'))}" aria-label="${escAttr(t('trajectories.find_transcript'))}"></div>`
    + `<div class="tf-pass-list" role="list">${trajPassListHtml(c, r, at)}</div>`
    + `<div class="tf-pass-foot"><button type="button" class="primary small" data-take-words="1" data-fkey="pass-take"${TJ.picked ? '' : ' disabled'}>${esc(t('trajectories.take_words'))}</button>`
    + `<button type="button" class="ghost small" data-pass-done="1" data-fkey="pass-done">${esc(t('trajectories.done'))}</button></div></div>`;
}

/* the turns of the interview shown, those holding the words found, each found word marked and the passage he
   took marked in its turn */
function trajPassListHtml(c, r, at) {
  const held = TJ.turns[tjTurnsKey(c.case, at)];
  if (!held) return '';
  const [, , tp] = TJ.passage.split('|');
  const cell = ((r.cells || {})[tp]) || {};
  const mine = cell.chosen && cell.quote && cell.quote.source === 'transcript' && cell.quote.at === at ? cell.quote.passage : null;
  const find = tjFlat(TJ.find).trim();
  return held.turns.filter((x) => !find || tjFlat(x.text).includes(find)).map((x) => {
    const marks = [];
    if (find) {
      const flat = String(x.text).toLowerCase();
      for (let i = flat.indexOf(find); i >= 0 && marks.length < 50; i = flat.indexOf(find, i + find.length)) marks.push([i, i + find.length, 'tf-found']);
    }
    if (mine && mine.turn === x.turn && !marks.some(([a, b]) => a < mine.end && mine.start < b)) marks.push([mine.start, mine.end, 'tf-taken']);
    marks.sort((p, q) => p[0] - q[0]);
    let words = '';
    let from = 0;
    for (const [a, b, cls] of marks) {
      words += esc(x.text.slice(from, a)) + `<mark class="${cls}">${esc(x.text.slice(a, b))}</mark>`;
      from = b;
    }
    words += esc(x.text.slice(from));
    return `<div class="tf-turn${mine && mine.turn === x.turn ? ' tf-turn-on' : ''}" role="listitem"><span class="tf-time">${esc(x.time)}</span>`
      + `<p class="tf-turn-w" data-turnw="${escAttr(x.turn)}">${words}</p>`
      + `<button type="button" class="ghost small tf-turn-all" data-whole="${escAttr(x.turn)}" data-fkey="whole-${escAttr(x.turn)}">${esc(t('trajectories.take_turn'))}</button></div>`;
  }).join('');
}

/* a participant's turns at an interview, read once for the picker */
async function trajTurnsLoad(case_, at) {
  const key = tjTurnsKey(case_, at);
  if (TJ.turns[key]) return TJ.turns[key];
  try {
    const answer = await api('/api/trajectories-turns', { workbook: TJ.path, participant: case_, timepoint: at });
    TJ.turns[key] = { turns: answer.turns || [], interviews: answer.interviews || [at] };
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    TJ.turns[key] = { turns: [], interviews: [at] };
  }
  return TJ.turns[key];
}

/* the picker opened for a cell, on the interview of the passage it holds, else its own, else the first the
   participant has */
async function trajPassOpen(id) {
  const [case_, lpet, tp] = id.split('|');
  const r = ((tjCard(case_) || {}).rows || []).find((x) => x.id === lpet);
  const q = r && ((r.cells || {})[tp] || {}).quote;
  Object.assign(TJ, { passage: id, find: '', picked: null, passageAt: q && q.source === 'transcript' && q.at ? q.at : tp });
  trajDraw();
  const held = await trajTurnsLoad(case_, TJ.passageAt);
  if (TJ.passage !== id) return;
  if (!held.turns.length && held.interviews.length && !held.interviews.includes(TJ.passageAt)) {
    TJ.passageAt = held.interviews[0];
    await trajTurnsLoad(case_, TJ.passageAt);
    if (TJ.passage !== id) return;
  }
  trajDraw();
  const on = document.querySelector('.tf-pass .tf-turn-on');
  if (on) on.scrollIntoView({ block: 'nearest' });
  const find = document.querySelector('.tf-pass-find');
  if (find) find.focus({ preventScroll: true });
}

/* another of the participant's interviews in the picker */
async function trajPassAt(at) {
  const id = TJ.passage;
  const [case_] = id.split('|');
  Object.assign(TJ, { passageAt: at, picked: null });
  await trajTurnsLoad(case_, at);
  if (TJ.passage === id) trajDraw();
}

/* the list alone drawn again as he types in the find box, so the box keeps its caret */
function trajPassFind(value) {
  TJ.find = value;
  TJ.picked = null;
  const [case_, lpet] = TJ.passage.split('|');
  const c = tjCard(case_);
  const r = c && (c.rows || []).find((x) => x.id === lpet);
  const list = document.querySelector('.tf-pass-list');
  if (c && r && list) list.innerHTML = trajPassListHtml(c, r, TJ.passageAt);
  trajPassPicked();
}

/* the words chosen in one turn of the picker, by character in its words, or null */
function trajPassPicked() {
  const sel = window.getSelection();
  let picked = null;
  if (sel && sel.rangeCount && !sel.isCollapsed) {
    const range = sel.getRangeAt(0);
    const node = (n) => (n.nodeType === 1 ? n : n.parentElement);
    const box = node(range.startContainer) && node(range.startContainer).closest('.tf-pass .tf-turn-w');
    if (box && box.contains(range.endContainer)) {
      const upTo = (n, offset) => { const rr = document.createRange(); rr.setStart(box, 0); rr.setEnd(n, offset); return rr.toString().length; };
      const a = upTo(range.startContainer, range.startOffset);
      const b = upTo(range.endContainer, range.endOffset);
      if (a < b && box.textContent.slice(a, b).trim()) picked = { turn: box.dataset.turnw, a, b };
    }
  }
  TJ.picked = picked;
  const take = document.querySelector('.tf-pass [data-take-words]');
  if (take) take.disabled = !picked;
}

/* a passage taken as the cell's key quote, the whole turn without `a` and `b` */
function trajPassTake(turn, a, b) {
  const [case_, lpet, tp] = TJ.passage.split('|');
  const passage = { interview: TJ.passageAt, turn };
  if (a !== undefined) Object.assign(passage, { start: a, end: b });
  Object.assign(TJ, { passage: '', choosing: '', picked: null, find: '' });
  window.getSelection().removeAllRanges();
  trajOps([{ op: 'quote', participant: case_, lpet, timepoint: tp, passage }]).then(() => {
    const back = document.querySelector(`[data-fkey="${CSS.escape(`q-${case_}|${lpet}|${tp}`)}"]`);
    if (back) back.focus();
  });
}

/* the participant's menu: Edit, then Move to each other trajectory or Not placed, Move up and Move down */
function trajMenuHtml(c) {
  const item = (attrs, word) => `<button type="button" role="menuitem" class="tf-mi" ${attrs}>${esc(word)}</button>`;
  let html = item(`data-edit="${escAttr(c.case)}" data-fkey="mi-edit"`, t('trajectories.edit'));
  const cols = [...((TJ.data && TJ.data.columns) || []).map((x) => ({ id: x.id, title: x.title })), { id: '', title: TJ_NOT_PLACED }];
  html += '<div class="tf-msep" role="separator"></div>';
  for (const col of cols) {
    if ((c.column || '') === col.id) continue;
    html += item(`data-move="${escAttr(c.case)}" data-to="${escAttr(col.id)}" data-fkey="mi-to-${escAttr(col.id)}"`, t('trajectories.move_to', { title: col.title }));
  }
  if (c.column) {
    html += '<div class="tf-msep" role="separator"></div>';
    html += item(`data-step="${escAttr(c.case)}" data-by="-1" data-fkey="mi-up"`, t('trajectories.move_up'));
    html += item(`data-step="${escAttr(c.case)}" data-by="1" data-fkey="mi-down"`, t('trajectories.move_down'));
  }
  return `<div class="tf-menu" role="menu" aria-label="${escAttr(t('trajectories.menu', { who: c.who }))}">${html}</div>`;
}

/* the participant's editor, opened in place: their picture, their label, their tags and which LPETs show,
   each kept at once, Done at its foot */
function trajEditHtml(c) {
  // Choose from the set: a tab for each set, the set of their picture now open first (picsets)
  const faces = TJ.faces ? faceSetsHtml(TJ.faceSet, c.picture_url, { pick: 'face', tab: 'faceset', fkey: true }) : '';
  const tags = (c.tags || []).map((tg) => `<span class="tf-pill tf-pill-x case-${(Number(tg.colour) || 0) % 25}${TJ.tagOpen === tg.word ? ' tf-pill-open' : ''}">`
    + `<button type="button" class="tf-pill-b" data-tag="${escAttr(tg.word)}" data-fkey="tag-${escAttr(tg.word)}" aria-expanded="${TJ.tagOpen === tg.word}"
        title="${escAttr(t('trajectories.tag_colour', { tag: tg.word }))}">${esc(tg.word)}</button>`
    + `<button type="button" class="tf-x" data-untag="${escAttr(tg.word)}" data-fkey="untag-${escAttr(tg.word)}" aria-label="${escAttr(t('trajectories.remove_tag', { tag: tg.word }))}"
        title="${escAttr(t('trajectories.remove_tag', { tag: tg.word }))}">${TJ_X}</button></span>`).join('');
  const open = (c.tags || []).find((tg) => tg.word === TJ.tagOpen);
  const dots = open ? `<span class="tf-dots" role="group" aria-label="${escAttr(t('trajectories.tag_colour', { tag: open.word }))}"><span class="tf-dots-l">${esc(open.word)}</span>`
    + Array.from({ length: TJ_TAG_COLOURS }, (_, i) => `<button type="button" class="tf-dot case-${i}${open.colour === i ? ' on' : ''}" data-tagcolour="${i}" data-fkey="dot-${i}"
        aria-pressed="${open.colour === i}" aria-label="${escAttr(t('trajectories.tag_colour_n', { tag: open.word, n: i + 1 }))}"></button>`).join('') + '</span>' : '';
  const lpets = (c.rows || []).length
    ? `<div class="tf-edit-l tf-edit-lpets"><span>${esc(t('trajectories.shown'))}</span><span class="tf-edit-ticks">${c.rows.map((r) => `<label class="tf-tickrow"><input type="checkbox"
        data-show="${escAttr(r.id)}" data-fkey="show-${escAttr(r.id)}"${r.shown !== false ? ' checked' : ''}><span>${esc(r.title)}</span></label>`).join('')}</span></div>` : '';
  return `<div class="tf-edit" role="group" aria-label="${escAttr(t('trajectories.edit_label', { who: c.who }))}" data-editing="${escAttr(c.case)}">`
    + `<div class="tf-edit-pic">${tjPicHtml(c, true)}<div class="tf-edit-picb">`
    + `<button type="button" class="ghost small" data-own="1" data-fkey="own">${esc(t('trajectories.change_picture'))}</button>`
    + `<button type="button" class="ghost small" data-faces="1" data-fkey="faces" aria-expanded="${TJ.faces}">${esc(t('trajectories.choose_from_set'))}</button>`
    + (c.picture ? `<button type="button" class="ghost small" data-nopic="1" data-fkey="nopic">${esc(t('trajectories.remove_picture'))}</button>` : '')
    + `</div></div><div class="tf-edit-fields">${faces}`
    + `<label class="tf-edit-l"><span>${esc(t('trajectories.name'))}</span><input class="tf-edit-in" value="${escAttr(c.who)}" disabled></label>`
    + `<label class="tf-edit-l"><span>${esc(t('trajectories.their_label'))}</span><input class="tf-edit-in tf-edit-label" maxlength="60" data-label="${escAttr(c.case)}"
        data-fkey="label" value="${escAttr(c.title || '')}"></label>`
    + `<div class="tf-edit-l"><span>${esc(t('trajectories.tags'))}</span><span class="tf-edit-tags">${tags}<input class="tf-edit-in tf-tagin" maxlength="40"
        data-addtag="${escAttr(c.case)}" data-fkey="addtag" placeholder="${escAttr(t('trajectories.add_tag'))}" aria-label="${escAttr(t('trajectories.add_tag'))}"></span></div>`
    + `${dots ? `<div class="tf-edit-l"><span></span>${dots}</div>` : ''}${lpets}</div>`
    + `<div class="tf-edit-done"><button type="button" class="primary small" data-edit-done="1" data-fkey="edit-done">${esc(t('trajectories.done'))}</button></div></div>`;
}

/* ── changes, each through the board's operations ── */

async function trajOps(ops) {
  if (!ops.length) return null;
  TJ.busy = true;
  $('tj-save').hidden = false;
  $('tj-save').textContent = t('trajectories.saving');
  try {
    const data = await api('/api/trajectories-ops', { workbook: TJ.path, ops });
    // the settings the bar keeps stay as the page holds them
    if (TJ.data && TJ.data.config && data.config) data.config = Object.assign({}, data.config, TJ.data.config);
    trajLoad(data);
    $('tj-save').textContent = t('trajectories.saved');
    return data;
  } catch (err) {
    $('tj-save').textContent = '';
    $('tj-save').hidden = true;
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    trajDraw();
    return null;
  } finally {
    TJ.busy = false;
  }
}

/* the bands in order, Not placed first, as their ids, '' for Not placed */
const tjOrder = () => ['', ...((TJ.data && TJ.data.columns) || []).map((c) => c.id)];
const tjColOf = (case_) => (tjCard(case_) || {}).column || '';

function trajFocus(case_) {
  const cell = document.querySelector(`.tf-pcell[data-case="${CSS.escape(case_)}"]`);
  if (cell) cell.focus();
}

/* a participant into a trajectory, `at` their place in it, at its end without it */
function trajPlace(case_, col, at) {
  const same = tjColOf(case_) === col;
  if (same && (at === undefined || at === null)) return Promise.resolve();
  const op = same && col ? { op: 'order', participant: case_, at } : { op: 'place', participant: case_, column: col || null };
  if (!same && col && at !== undefined && at !== null) op.at = at;
  return trajOps([op]).then(() => trajFocus(case_));
}

function trajTitleDone(input) {
  const col = input.dataset.col;
  const was = (tjCol(col) || {}).title || '';
  const now = input.value.trim().replace(/\s+/g, ' ');
  if (!now) { input.value = was; return; }
  if (now !== was) trajOps([{ op: 'rename', column: col, title: now }]);
}

/* New trajectory: a band whose title is typed at once, added when it has words, gone when left empty */
function trajNew() {
  const box = document.querySelector('.tf-new');
  if (!box || box.querySelector('input')) return;
  box.innerHTML = '<div class="tj-head"><input class="tj-title" id="tj-new-title" type="text" maxlength="60" '
    + `aria-label="${escAttr(t('trajectories.new_title_label'))}"></div>`;
  const input = $('tj-new-title');
  let done = false;
  const finish = (keep) => {
    if (done) return;
    done = true;
    const title = input.value.trim().replace(/\s+/g, ' ');
    if (keep && title) trajOps([{ op: 'add', title }]);
    else trajDraw();
  };
  input.onkeydown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); finish(true); }
    else if (e.key === 'Escape') { e.preventDefault(); finish(false); }
  };
  input.onblur = () => finish(true);
  input.focus();
}

/* the view kept in the settings at once, as the boards keep theirs */
async function trajSetting(key, value) {
  if (!TJ.data) return;
  TJ.data.config = Object.assign({}, TJ.data.config || {}, { [key]: value });
  if (typeof S !== 'undefined') {
    if (S.data && S.data.config) S.data.config[key] = value;
    if (S.libConfig) S.libConfig[key] = value;
  }
  trajDraw();
  try {
    await api('/api/settings', { [key]: value });
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  }
}

/* his own picture, read in the page and made a square of 256 pixels at its middle, sent as the op's data */
async function trajOwnPicture(case_, file) {
  if (!file) return;
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
    await trajOps([{ op: 'picture', participant: case_, data: canvas.toDataURL('image/png') }]);
  } catch {
    say(t('trajectories.picture_unread'), 9000);
  } finally {
    URL.revokeObjectURL(url);
  }
}

/* the offsets of the words chosen inside a key quote, by character, or null when the choice is not in one */
function trajChosenSpan() {
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return null;
  const range = sel.getRangeAt(0);
  const box = (range.commonAncestorContainer.nodeType === 1 ? range.commonAncestorContainer : range.commonAncestorContainer.parentElement)
    .closest('.tf-qtext');
  if (!box) return null;
  const upTo = (node, offset) => {
    const r = document.createRange();
    r.setStart(box, 0);
    r.setEnd(node, offset);
    return r.toString().length;
  };
  const a = upTo(range.startContainer, range.startOffset);
  const b = upTo(range.endContainer, range.endOffset);
  return a < b ? { id: box.dataset.qcell, a, b } : null;
}

/* Cmd+B on words of a key quote: bold where any of them is not, plain where all of them are */
function trajBold() {
  const span = trajChosenSpan();
  if (!span) return false;
  const [case_, lpet, tp] = span.id.split('|');
  const c = tjCard(case_);
  const r = c && (c.rows || []).find((x) => x.id === lpet);
  const cell = r && (r.cells || {})[tp];
  if (!cell || !cell.quote) return false;
  const len = cell.quote.text.length;
  const mask = new Array(len).fill(false);
  for (const [x, y] of cell.bold || []) for (let i = x; i < Math.min(y, len); i += 1) mask[i] = true;
  const all = mask.slice(span.a, span.b).every(Boolean);
  for (let i = span.a; i < Math.min(span.b, len); i += 1) mask[i] = !all;
  const spans = [];
  for (let i = 0; i < len; i += 1) {
    if (!mask[i]) continue;
    let j = i;
    while (j < len && mask[j]) j += 1;
    spans.push([i, j]);
    i = j;
  }
  window.getSelection().removeAllRanges();
  trajOps([{ op: 'bold', participant: case_, lpet, timepoint: tp, spans }]);
  return true;
}

function trajCloseAll() {
  const open = TJ.choosing || TJ.menu || TJ.picking || TJ.passage;
  Object.assign(TJ, { choosing: '', menu: '', picking: '', passage: '', picked: null, find: '' });
  return !!open;
}

/* where a participant dropped on a band goes: before the first participant whose middle is below the pointer */
function trajDropAt(band, y, case_) {
  const cells = [...band.querySelectorAll('.tf-pcell')].filter((el) => el.dataset.case !== case_);
  const at = cells.findIndex((el) => { const r = el.getBoundingClientRect(); return y < r.top + r.height / 2; });
  return at < 0 ? cells.length : at;
}

function trajWire() {
  // the lockup, Home (option C of the bars, 26 October 2026), and Send feedback, said as from the GETs, the
  // project's other board, a word of the collector's fixed list
  $('tj-home').onclick = () => trajHome();
  $('tj-feedback').onclick = () => openFeedback('gets');
  $('tj-settings').onclick = () => openSettings('pets');
  for (const [id, step] of [['tj-step-es', 'statements'], ['tj-step-pets', 'pets'], ['tj-step-lpets', 'lpets'],
    ['tj-step-gets', 'gets'], ['tj-step-lgets', 'lgets']]) {
    $(id).onclick = () => trajStep(step);
  }
  dsTabsWatch('tj-steps');
  $('tj-open-side').addEventListener('pointerdown', (e) => e.preventDefault());
  $('tj-open-side').onclick = () => trajSideSet(!TJ.sideOpen);
  $('tj-quotes-btn').onclick = () => trajSetting('traj_quotes', TJ_QUOTES_WAYS[(TJ_QUOTES_WAYS.indexOf(tjQuotesWay()) + 1) % TJ_QUOTES_WAYS.length]);
  $('tj-notes-btn').onclick = () => trajSetting('traj_notes', !tjNotesOn());
  $('tj-picture-file').addEventListener('change', (e) => {
    const file = e.target.files && e.target.files[0];
    const case_ = TJ.editing;
    e.target.value = '';
    if (file && case_) trajOwnPicture(case_, file);
  });
  // the board's note: Enter keeps it, Shift+Enter a new line, Esc leaves it as it was, kept as the focus leaves
  const note = $('tj-board-note');
  note.addEventListener('input', () => trajFit(note));
  note.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); note.blur(); }
    else if (e.key === 'Escape') { e.preventDefault(); note.value = (TJ.data && TJ.data.note) || ''; note.blur(); }
  });
  note.addEventListener('blur', () => {
    const now = note.value.trim();
    if (TJ.data && now !== (TJ.data.note || '')) trajOps([{ op: 'note_board', note: now }]);
    else trajFit(note);
  });
  const board = $('tj-board');
  board.addEventListener('click', (e) => {
    const el = (sel) => e.target.closest(sel);
    if (el('#tj-new')) { trajNew(); return; }
    let x;
    if ((x = el('[data-remove]'))) { trajOps([{ op: 'remove', column: x.dataset.remove }]); return; }
    if ((x = el('[data-swatch]'))) { const id = x.dataset.swatch; const was = TJ.picking === id; trajCloseAll(); TJ.picking = was ? '' : id; trajDraw(); return; }
    if (el('[data-pick-done]')) { TJ.picking = ''; trajDraw(); return; }
    if ((x = el('[data-colour]'))) { trajOps([{ op: 'colour', column: x.dataset.col, colour: x.dataset.colour || null }]); return; }
    if ((x = el('[data-icon]'))) { trajOps([{ op: 'icon', column: x.dataset.col, icon: x.dataset.icon || null }]); return; }
    if ((x = el('[data-more]'))) { const id = x.dataset.more; const was = TJ.menu === id; trajCloseAll(); TJ.menu = was ? '' : id; trajDraw(); if (TJ.menu) { const first = board.querySelector('.tf-menu .tf-mi'); if (first) first.focus(); } return; }
    if ((x = el('[data-edit]'))) { trajCloseAll(); TJ.editing = x.dataset.edit; TJ.faces = false; TJ.tagOpen = ''; trajDraw(); const f = board.querySelector('.tf-edit-label'); if (f) f.focus(); return; }
    if ((x = el('[data-move]'))) { const case_ = x.dataset.move; TJ.menu = ''; trajPlace(case_, x.dataset.to); return; }
    if ((x = el('[data-step]'))) { const case_ = x.dataset.step; TJ.menu = ''; trajMove(case_, Number(x.dataset.by)); return; }
    if (el('[data-edit-done]')) { const case_ = TJ.editing; Object.assign(TJ, { editing: '', faces: false, tagOpen: '' }); trajDraw(); trajFocus(case_); return; }
    if (el('[data-own]')) { $('tj-picture-file').click(); return; }
    if (el('[data-faces]')) { TJ.faces = !TJ.faces; TJ.faceSet = ''; trajDraw(); return; }
    if ((x = el('[data-faceset]'))) { TJ.faceSet = x.dataset.faceset; trajDraw(); return; }
    if ((x = el('[data-face]'))) { trajOps([{ op: 'picture', participant: TJ.editing, set: x.dataset.face }]); return; }
    if (el('[data-nopic]')) { trajOps([{ op: 'picture', participant: TJ.editing }]); return; }
    if ((x = el('[data-untag]'))) { trajTags(TJ.editing, (tags) => tags.filter((w) => w !== x.dataset.untag)); return; }
    if ((x = el('[data-tag]'))) { TJ.tagOpen = TJ.tagOpen === x.dataset.tag ? '' : x.dataset.tag; trajDraw(); return; }
    if ((x = el('[data-tagcolour]'))) { trajOps([{ op: 'tag_colour', tag: TJ.tagOpen, colour: Number(x.dataset.tagcolour) }]); return; }
    if ((x = el('[data-choose]'))) {
      const [case_, lpet, tp] = x.dataset.choose.split('|');
      const ticked = x.getAttribute('aria-checked') === 'true';
      if (TJ.passage) Object.assign(TJ, { passage: '', picked: null, find: '' });
      trajOps([{ op: 'quote', participant: case_, lpet, timepoint: tp, quote: ticked ? '' : x.dataset.qkey }]);
      return;
    }
    // the passage picker, opened from the chooser's last part, its clicks its own
    if ((x = el('[data-passage-open]'))) {
      const id = x.dataset.passageOpen;
      if (TJ.passage === id) { Object.assign(TJ, { passage: '', picked: null, find: '' }); trajDraw(); } else trajPassOpen(id);
      return;
    }
    if ((x = el('[data-pass-at]'))) { trajPassAt(x.dataset.passAt); return; }
    if ((x = el('[data-whole]'))) { trajPassTake(x.dataset.whole); return; }
    if (el('[data-take-words]')) { const p = TJ.picked; if (p) trajPassTake(p.turn, p.a, p.b); return; }
    if (el('[data-pass-done]')) { const back = TJ.passage; Object.assign(TJ, { passage: '', picked: null, find: '' }); trajDraw(); const to = back && board.querySelector(`[data-fkey="${CSS.escape(`ch-${back}-open`)}"]`); if (to) to.focus(); return; }
    if (el('.tf-pass') || el('.tf-choose')) return;
    if ((x = el('.tf-q[data-cell]'))) {
      // a click that chose words is for Cmd+B, not the chooser
      const sel = window.getSelection();
      if (sel && !sel.isCollapsed && x.contains(sel.anchorNode)) return;
      const id = x.dataset.cell;
      const was = TJ.choosing === id;
      trajCloseAll();
      TJ.choosing = was ? '' : id;
      trajDraw();
      if (TJ.choosing) { const first = board.querySelector('.tf-choose .tf-choice.on') || board.querySelector('.tf-choose .tf-choice'); if (first) first.focus(); }
      return;
    }
    if (trajCloseAll()) trajDraw();
  });
  board.addEventListener('change', (e) => {
    const box = e.target.closest('input[data-show]');
    if (box && TJ.editing) trajOps([{ op: box.checked ? 'show' : 'hide', participant: TJ.editing, lpet: box.dataset.show }]);
  });
  board.addEventListener('dblclick', (e) => {
    const cell = e.target.closest('.tf-pcell');
    if (!cell || e.target.closest('textarea, button')) return;
    trajCloseAll();
    TJ.editing = cell.dataset.case;
    TJ.faces = false;
    TJ.tagOpen = '';
    trajDraw();
    const f = board.querySelector('.tf-edit-label');
    if (f) f.focus();
  });
  board.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && !e.altKey && !e.shiftKey && (e.key === 'b' || e.key === 'B')) {
      if (trajBold()) { e.preventDefault(); return; }
    }
    const title = e.target.closest('input.tj-title[data-col]');
    if (title) {
      if (e.key === 'Enter') { e.preventDefault(); title.blur(); }
      else if (e.key === 'Escape') { e.preventDefault(); title.value = (tjCol(title.dataset.col) || {}).title || ''; title.blur(); }
      return;
    }
    const field = e.target.closest('textarea[data-desc], textarea[data-state], input[data-label]');
    if (field) {
      // Enter keeps the words, Shift+Enter a new line in a sentence or a state, Esc leaves them as they were
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); field.blur(); }
      else if (e.key === 'Escape') { e.preventDefault(); trajFieldReset(field); field.blur(); }
      return;
    }
    const add = e.target.closest('input[data-addtag]');
    if (add) {
      if (e.key === 'Enter' || e.key === ',') {
        e.preventDefault();
        const word = add.value.trim().replace(/\s+/g, ' ');
        if (word) trajTags(add.dataset.addtag, (tags) => [...tags, word]);
      } else if (e.key === 'Escape') { e.preventDefault(); add.value = ''; }
      return;
    }
    // Choose from the set's tabs: the arrows, Home and End move along them, the set under them following (picsets)
    const settab = e.target.closest('[data-faceset]');
    const step = settab ? faceSetStep(e.key, settab.dataset.faceset) : '';
    if (step) {
      e.preventDefault();
      TJ.faceSet = step;
      trajDraw();
      const again = board.querySelector(`[data-fkey="faceset-${step}"]`);
      if (again) again.focus();
      return;
    }
    if (e.key === 'Escape') {
      if (TJ.editing && e.target.closest('.tf-edit')) { const case_ = TJ.editing; Object.assign(TJ, { editing: '', faces: false, tagOpen: '' }); trajDraw(); trajFocus(case_); e.preventDefault(); return; }
      // Esc in the passage picker closes it alone, the chooser staying open
      if (TJ.passage && e.target.closest('.tf-pass')) {
        const back = TJ.passage;
        Object.assign(TJ, { passage: '', picked: null, find: '' });
        e.preventDefault();
        trajDraw();
        const to = board.querySelector(`[data-fkey="${CSS.escape(`ch-${back}-open`)}"]`);
        if (to) to.focus();
        return;
      }
      const back = TJ.choosing ? `q-${TJ.choosing}` : TJ.menu ? `more-${TJ.menu}` : TJ.picking ? `swatch-${TJ.picking}` : '';
      if (trajCloseAll()) {
        e.preventDefault();
        trajDraw();
        const to = back && board.querySelector(`[data-fkey="${CSS.escape(back)}"]`);
        if (to) to.focus();
      }
      return;
    }
    // inside the chooser and a menu the arrows move between its rows
    const row = e.target.closest('.tf-choice, .tf-mi');
    if (row && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault();
      const all = [...row.closest('.tf-choose, .tf-menu').querySelectorAll('.tf-choice, .tf-mi')];
      const to = all[Math.max(0, Math.min(all.length - 1, all.indexOf(row) + (e.key === 'ArrowDown' ? 1 : -1)))];
      if (to) to.focus();
      return;
    }
    const quote = e.target.closest('.tf-q[data-cell]');
    if (quote && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); quote.click(); return; }
    const cell = e.target.classList && e.target.classList.contains('tf-pcell') ? e.target : null;
    if (!cell || e.metaKey || e.ctrlKey || e.altKey) return;
    const case_ = cell.dataset.case;
    if (e.key === 'Enter') { e.preventDefault(); cell.dispatchEvent(new MouseEvent('dblclick', { bubbles: true })); return; }
    if (e.key === 'Backspace') { e.preventDefault(); trajPlace(case_, ''); return; }
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') { e.preventDefault(); trajMove(case_, e.key === 'ArrowDown' ? 1 : -1); return; }
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();
    const order = tjOrder();
    const at = order.indexOf(tjColOf(case_));
    const to = order[Math.max(0, Math.min(order.length - 1, at + (e.key === 'ArrowRight' ? 1 : -1)))];
    trajPlace(case_, to);
  });
  board.addEventListener('input', (e) => {
    if (e.target.classList && e.target.classList.contains('tf-fit')) trajFit(e.target);
    if (e.target.dataset && e.target.dataset.passFind) trajPassFind(e.target.value);
  });
  // the words chosen in a turn of the passage picker, so Take the words selected knows them; its own press keeps
  // the choice where a press would end it
  document.addEventListener('selectionchange', () => { if (TJ.passage) trajPassPicked(); });
  board.addEventListener('pointerdown', (e) => { if (e.target.closest('[data-take-words]')) e.preventDefault(); });
  board.addEventListener('focusout', (e) => {
    const title = e.target.closest('input.tj-title[data-col]');
    if (title) { trajTitleDone(title); return; }
    const desc = e.target.closest('textarea[data-desc]');
    if (desc) {
      const now = desc.value.trim().replace(/\s+/g, ' ');
      if (now !== ((tjCol(desc.dataset.desc) || {}).description || '')) trajOps([{ op: 'describe', column: desc.dataset.desc, description: now }]);
      return;
    }
    const state = e.target.closest('textarea[data-state]');
    if (state) {
      const [case_, lpet, tp] = state.dataset.state.split('|');
      const r = ((tjCard(case_) || {}).rows || []).find((x) => x.id === lpet);
      if (state.value.trim() !== (((r && r.cells) || {})[tp] || {}).state) trajOps([{ op: 'state', participant: case_, lpet, timepoint: tp, state: state.value.trim() }]);
      return;
    }
    const label = e.target.closest('input[data-label]');
    if (label) {
      const now = label.value.trim().replace(/\s+/g, ' ');
      if (now !== ((tjCard(label.dataset.label) || {}).title || '')) trajOps([{ op: 'title', participant: label.dataset.label, title: now }]);
      return;
    }
    const note = e.target.closest('textarea.tj-note');
    if (note && note.value.trim() !== ((tjCard(note.dataset.case) || {}).note || '')) {
      trajOps([{ op: 'note', participant: note.dataset.case, note: note.value.trim() }]);
    }
  });
  board.addEventListener('dragstart', (e) => {
    const cell = e.target.closest && e.target.closest('.tf-pcell');
    if (!cell || e.target.closest('textarea, input')) return;
    TJ.drag = cell.dataset.case;
    cell.classList.add('tj-lifted');
    try { e.dataTransfer.setData('text/plain', TJ.drag); e.dataTransfer.effectAllowed = 'move'; } catch { /* no transfer */ }
  });
  board.addEventListener('dragend', () => {
    TJ.drag = null;
    for (const el of board.querySelectorAll('.tj-lifted, .tj-over')) el.classList.remove('tj-lifted', 'tj-over');
  });
  board.addEventListener('dragover', (e) => {
    const band = TJ.drag && e.target.closest && e.target.closest('.tf-band[data-col]');
    if (!band) return;
    e.preventDefault();
    for (const el of board.querySelectorAll('.tj-over')) if (el !== band) el.classList.remove('tj-over');
    band.classList.add('tj-over');
  });
  board.addEventListener('drop', (e) => {
    const band = TJ.drag && e.target.closest && e.target.closest('.tf-band[data-col]');
    if (!band) return;
    e.preventDefault();
    const case_ = TJ.drag;
    TJ.drag = null;
    band.classList.remove('tj-over');
    const col = band.dataset.col;
    trajPlace(case_, col, col ? trajDropAt(band, e.clientY, case_) : undefined);
  });
}

/* a field's words put back as the board has them, for Esc */
function trajFieldReset(field) {
  if (field.dataset.desc !== undefined) field.value = (tjCol(field.dataset.desc) || {}).description || '';
  else if (field.dataset.label !== undefined) field.value = (tjCard(field.dataset.label) || {}).title || '';
  else if (field.dataset.state) {
    const [case_, lpet, tp] = field.dataset.state.split('|');
    const r = ((tjCard(case_) || {}).rows || []).find((x) => x.id === lpet);
    field.value = (((r && r.cells) || {})[tp] || {}).state || '';
  }
}

/* a participant's tags changed as `change` says, all of them sent */
function trajTags(case_, change) {
  const c = tjCard(case_);
  if (!c) return;
  const tags = change((c.tags || []).map((tg) => tg.word));
  trajOps([{ op: 'tags', participant: case_, tags }]).then(() => {
    const add = document.querySelector('input[data-addtag]');
    if (add) add.focus();
  });
}

/* a participant up or down their trajectory by one */
function trajMove(case_, by) {
  const col = tjCol(tjColOf(case_));
  if (!col) return;
  const order = col.participants || [];
  const at = order.indexOf(case_) + by;
  if (at < 0 || at >= order.length) return;
  trajOps([{ op: 'order', participant: case_, at }]).then(() => trajFocus(case_));
}

/* Home from the mark, a title or a note in hand kept first, then Home's picker as from every bar */
async function trajHome() {
  if (document.activeElement && $('traj').contains(document.activeElement)) document.activeElement.blur();
  await trajIdle();
  $('traj').hidden = true;
  TJ.ask += 1;
  S.backTo = null;
  if (typeof homeKeep === 'function') homeKeep('');
  try { await loadLibrary(); } catch (err) { say(err.message, 9000); }
  window.scrollTo(0, 0);
}

/* a tab of the Trajectories bar: that stage for the participant of the workbook the board came through, or
   the way back where it goes there already */
async function trajStep(step) {
  if (step === TJ.to) { trajBack(); return; }
  await trajIdle();
  const path = TJ.path;
  const back = () => trajOpen(path, { back: TJ.back, to: TJ.to });
  const kept = { back: TJ.back, to: TJ.to };
  const again = () => trajOpen(path, kept);
  const leave = () => { $('traj').hidden = true; TJ.ask += 1; };
  if (step === 'statements') {
    await navGo(() => trajStep(step), () => openStatements(path, { leave, back: again, to: 'trajectories' }));
    return;
  }
  leave();
  const opts = { back, label: '', to: 'trajectories' };
  if (step === 'pets') await navGo(() => trajStep(step), () => themesOpen(path, opts));
  else if (step === 'lpets') await navGo(() => trajStep(step), () => getsOpen(path, Object.assign(opts, { lpets: true })));
  else await navGo(() => trajStep(step), () => getsOpen(path, opts));
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', trajWire);
else trajWire();
