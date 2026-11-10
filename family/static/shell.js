/* The family's shell, the page's script every app shares (the family codebase's fifth build, 23 October 2026,
   until then app.js with Distil's in it): the plumbing, Home and its family of apps, the cards and Settings with
   its General, AI features and agents, celebrations, Restart and Quit, updates and What's new, About, and the
   page's start. No framework, no build step, nothing fetched from the network. Each app's own part registers
   itself in FAMILY_APPS from its own script, Idiograph's from distil.js, Sift's from sift_settings.js and Trace's
   from trace.js, and this script reaches an app only through that table. */

'use strict';

const $ = (id) => document.getElementById(id);
const MAC = navigator.platform.toUpperCase().includes('MAC');
/* Linux, WebKitGTK's window and a browser there, "Linux x86_64" or "Linux aarch64" (linuxfix, 9 November 2026) */
const LINUX = navigator.platform.toUpperCase().includes('LINUX');
/* A guard for Orca on Linux (orcacrash, 9 November 2026). WebKitGTK 2.52 ends the page's process when Orca asks for
   the line or word at a place in a group whose next caret place lies outside the group, past a button (its
   AccessibilityObjectTextAtspi.cpp reads its table of offsets past the end), so a Tab to the statement's quote or to
   Columns with Orca on left the window dead. A zero-width space out of sight and hidden from screen readers, after
   the group or inside its last button, gives that place a stop of its own and the crash does not come. Orca reads
   the same names and words, and off Linux nothing is added. `inside` puts it at the end of `el`, else after it. */
function axGuard(el, inside = false) {
  if (!LINUX || !el) return;
  const guard = document.createElement('span');
  guard.className = 'ax-guard';
  guard.setAttribute('aria-hidden', 'true');
  guard.textContent = '​';
  if (inside) el.append(guard);
  else el.after(guard);
}
const MOD = (e) => (MAC ? e.metaKey : e.ctrlKey);
/* Ctrl+Y, Redo off a Mac, as Windows names it beside Ctrl+Shift+Z (17 October) */
const REDO_Y = (e) => !MAC && e.ctrlKey && !e.shiftKey && !e.altKey && (e.key === 'y' || e.key === 'Y');
/* A key as this machine names it, in a tooltip, "Undo (Cmd + Z)", and since 17 October in every line,
   hint and placeholder of the statements screen and in its shortcuts card, so no two names of one key
   stand side by side: Cmd on a Mac and Ctrl elsewhere, a held Cmd as well, the sheet and seek chord,
   Ctrl + Cmd on a Mac, Ctrl + Alt elsewhere, as SEEK reads it, the card's "Cmd / Ctrl" and "Option /
   Alt" the one this machine has, a line's ends, Cmd and an arrow on a Mac, Home and End elsewhere, and
   Back and Forward, Cmd + [ and Cmd + ] on a Mac, Alt and the arrows elsewhere (20 October).
   Every button with a key names it in its tooltip (16 October). A letter key stands in its capital, as
   keyboards and the Mac's and Windows' menus print it, "Group (G)", "press Q.", Q alone on a card and
   after a +, every place that writes a key by hand writing it so too (17 October, later). */
/* The keys' names come from the catalogue (`shell.keys.*`, i18nleft, 1 November 2026), so a language writes its
   own, Strg for Ctrl, and its sentences name the keys in those words, the Mac's first where two stand together.
   One expression, which the checks lift out whole: `k` the names, `w` one made safe in a pattern, `at` a pattern
   that starts at a word's edge, `pair` the card's "Cmd / Ctrl" and "Option / Alt" */
const keyName = (text, k = { cmd: t('shell.keys.cmd'), ctrl: t('shell.keys.ctrl'), option: t('shell.keys.option'), alt: t('shell.keys.alt'), shift: t('shell.keys.shift'), home: t('shell.keys.home'), end: t('shell.keys.end') },
  w = (s) => String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), at = (s, edge = '') => new RegExp(`(?<![\\p{L}\\d_])${s}${edge}`, 'gu'),
  pair = at(`(${w(k.cmd)}|${w(k.option)}) \\/ (${w(k.ctrl)}|${w(k.alt)})`, '(?![\\p{L}\\d_])')) => (MAC ? String(text).replace(pair, '$1')
  : String(text).replace(at(`${w(k.cmd)} \\+ \u2190 \\/ \u2192`), `${k.home} / ${k.end}`).replace(at(`${w(k.ctrl)} \\+ ${w(k.cmd)} \\+ `), `${k.ctrl} + ${k.alt} + `)
    .replace(at(`${w(k.cmd)} \\+ \\[`), `${k.alt} + \u2190`).replace(at(`${w(k.cmd)} \\+ \\]`), `${k.alt} + \u2192`)
    .replace(at(`${w(k.cmd)} \\+ ${w(k.shift)} \\+ H`, '(?![\\p{L}\\d_])'), `${k.alt} + ${k.home}`)
    .replace(pair, '$2').replace(at(w(k.cmd), '(?![\\p{L}\\d_])'), k.ctrl))
  .replace(/^[a-z]$/, (m) => m.toUpperCase())
  .replace(/([A-Za-z] \(|\+ )([a-z])(?=\)|$|[^A-Za-z])/g, (m, before, key) => before + key.toUpperCase())
  // the letter after English's "press", which another language's sentences write in its capital already
  .replace(/\b([Pp]ress) ([a-z])(?=[.,:)]|$)/g, (m, word, key) => `${word} ${key.toUpperCase()}`);
// the chord that moves the recording five seconds: Ctrl + Cmd on a Mac, Ctrl + Alt elsewhere.
// Cmd and an arrow belong to the text on a Mac, the line ends and with Shift the selection to
// them, so the app never takes those, in a field or out of one
const SEEK = (e) => (MAC ? e.metaKey && e.ctrlKey : e.ctrlKey && e.altKey) && !e.shiftKey;

const S = {
  data: null,        // the open case
  flat: [],          // every row, in order, across sheets
  stops: [],         // indices into flat that are participant turns
  at: 0,             // position in stops
  dirty: false,
  guidanceLines: [],
  pendingRound: null,
  sheetDrawn: null,  // the sheet the transcript column currently holds
  pending: [],       // the pieces of the quote being built, as offsets into the current turn
  trimRow: null,     // the turn a trim is being confirmed against
  trimDirection: null,
  candidates: [],    // the last candidates offered for this turn
  prompts: [],       // the craft prompts, one of which is the placeholder on each turn
  promptDefault: '', // the prompt template as it ships, for the reset in settings
  models: null,      // both providers' model lists, from a server that has them
  audioSheet: null,  // the sheet the player is loaded for
  cueAt: 0,          // where the player has been asked to sit, in seconds
  seekAt: null,      // the timecode a click in the margin last played from, for the toggle
  scrubbing: false,  // a drag is under way on the scrub bar
  selecting: false,  // a drag is under way in the transcript column
  listening: null,   // the row the playhead mark sits on
  spans: [],         // the drawn sheet's turns by timecode, for the playhead
  spansSheet: null,
  spanAt: 0,
  undoStack: [],     // the app's own reversible actions, oldest first
  redoStack: [],
  undoBusy: false,
  lastInput: {},     // when each field last took a keystroke, for native undo
  editing: null,     // the turn open for correction, and the box it is open in
  mm: null,          // the minimap's plan, its blocks, scale and ties to the column, null while the card is not wanted
  mmDrag: null,      // a press on the minimap under way, where the box was taken and whether it has moved
  mmOver: false,     // the pointer on the minimap's card, which keeps it from giving way under his hand
  mmAt: -1,          // the passage the minimap was last drawn for, whose change ends an opening of his
  mmHeld: false,     // an opening of his not yet looked at again, which leaves the card over what was in the corner then
  mmHush: false,     // the card hidden by his button or M until the next passage
  mmAwake: false,    // in Auto, the card shown after a scroll or a move until it sleeps
  mmRoom: '',        // the room Back to where I was takes beside the card, as last set
  mmLift: false,     // Back to where I was in a strip at the column's head, where it has no room beside the card, as last set
  pairsRow: null,    // the passage whose pairs the fields hold, which marks its quotes from them
  kqDrawn: '',       // the quotes the passage being worked on was last marked with
  kqHover: null,     // the pair whose quote is under the pointer, which lights its marks
  kqFocus: null,     // the pair whose quote holds the caret, which lights them too
  quoting: false,    // a q on words in another passage is on its way there
  rowMenu: null,     // the row's menu, the turn it was opened on and the words selected in it
  timeEdit: null,    // the timecode open for correction in the margin, and its box
  note: null,        // the interviewer's turn whose note is open in place of the three fields
  assignPlan: null,  // the whole-turn assignment the confirm card stands in front of
  assignBusy: false,
  closing: new Set(), // rounds whose completion is on its way to the server, so none is sent twice
  doneAdvance: false, // whether Next round on the round-complete card moves on, or the move already has
  pairFocus: null,   // the pair whose statement or quote last had the focus, the pair being worked on
  prompt: '',        // the craft prompt in the first statement field, a fresh one on every turn
  bench: { time: '', name: '' },       // the bench turn's time and speaker, sent as the button sends them
  libConfig: null,   // the settings as the case list last had them
  lib: null,         // the case list's last answer, which the home screen and a project's page draw from
  home: null,        // the project whose page the home screen shows, '' for the picker (see homeKeep)
  recut: false,      // the rounds were recut from over the PETs screen, so the case reopens on the way back
  marking: false,    // a mark or a reopen is on its way to the server
  doneFinished: false, // the round card on screen is the case-complete card
  doneSheet: false,  // the round card on screen is the sheet-done card
  nextSheet: null,   // the sheet its Next sheet goes to
  capOpened: null,   // the limit on an AI board's PETs as Settings opened with it
};

/* ───────────────────────────────────────────────────────── plumbing ── */

async function api(path, body) {
  // a call about the PETs or GETs canvas names its timepoint or the LPETs (an app's `scope`, Idiograph's
  // thScopeFor in themes.js)
  if (body !== undefined) for (const own of Object.values(FAMILY_APPS)) if (own.scope) body = own.scope(path, body);
  // this start's key on every call, so what governs agents answers the app's own window and no other program on
  // this machine (agentlock, 2 November 2026, server.py `keyed`): the one the server put in a page served to a
  // browser, else the one the window handed its page before the page's own scripts ran. Never stored
  const meta = typeof document !== 'undefined' && document.querySelector
    ? document.querySelector('meta[name="idiograph-key"]') : null;
  const held = (meta && meta.content) || (typeof window !== 'undefined' && window.__IDIOGRAPH_KEY__) || '';
  const key = { 'X-Idiograph-Key': held };
  const res = await fetch(path, body === undefined
    ? { headers: key }
    : { method: 'POST', headers: { 'Content-Type': 'application/json', ...key }, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({ error: t('shell.server_unreadable') }));
  if (!res.ok || data.error) {
    // the answer goes with the error, for a refusal that carries more than its line (see showStale), and
    // its code, which the page tests in place of its words (refusedAs)
    const err = new Error(data.error || t('shell.request_failed', { status: res.status }));
    err.data = data;
    err.code = typeof data.code === 'string' ? data.code : '';
    throw err;
  }
  return data;
}

/* Whether a refusal is the one `code` names (i18ncodes, 31 October 2026). The server answers a refusal the page
   reacts to with a code beside its words, one of family/errors.py's CODES, so the page tests what was refused
   and never how the language of the day words it. */
const refusedAs = (err, code) => !!err && err.code === code;

/* Which of the family's three apps this page is (the split's third build, 20 October 2026): the server
   names it on the page's root, data-app, and the page shows that app's screens, Home, Settings, Search
   and shortcuts alone. A page served by a server from before the split says nothing, and is Idiograph. */
const APP = ['idiograph', 'sift', 'trace'].includes(document.documentElement.dataset.app)
  ? document.documentElement.dataset.app : 'idiograph';
const APP_NAMES = { idiograph: 'Idiograph', sift: 'Sift', trace: 'Trace' };
const APP_NAME = APP_NAMES[APP];
// each app's AI features, as AI features in Settings lists them and app_identity.AI_FEATURES names them
const AI_FEATURES = { idiograph: ['statements', 'pets', 'gets'], sift: ['proposals'], trace: ['passages'] };
const AI_OFF_KEY = 'ai_features_off';

/* The static files are served with no-store, so a change here reaches the page on a reload,
   before the server behind it has been restarted. An endpoint the old server has never heard of
   answers with the code no_endpoint (its words, "No such endpoint.", until 31 October), and the
   feature says so quietly rather than breaking. An op it has never heard of is unknown_op, which
   the features that send a newer op test beside this. */
const RESTART_LINE = t('shell.restart_line');
const needsRestart = (err) => refusedAs(err, 'no_endpoint');
// an answer that shows a server older than the page though it answered, taken as one with no such endpoint
const olderServer = () => Object.assign(new Error(RESTART_LINE), { code: 'no_endpoint' });

/* AI features, the one switch in Settings, off on a new install. Every AI control, tab, menu entry,
   shortcut and line in the page asks this one test, and the PETs and GETs screens hold its answer
   as `TH.ai.on` (see thAiOn in themes.js). The switch was called `haiku` before the suggestions
   stopped naming a model. A server that has not been restarted still sends the old key, so both
   are read. */
const aiOn = (cfg) => (cfg && cfg.ai_suggest !== undefined ? !!cfg.ai_suggest : !!(cfg && cfg.haiku));

/* Work in rounds, the tick under Distil, Experiential statements in Settings, off on a new install
   (15 October). A round is a pace, ten minutes of transcript with a daily target, a streak and the
   time left, and never a step of IPA, so it is a setting and not a default. Off, nothing about
   rounds shows: no round count, clock, marker, target, streak or squares, and the card comes only at
   a sheet's end and the case's. The rounds are still cut and still closed with the server, quietly,
   so the daily tally stays true for the day they are turned on. `work_in_rounds` in config.json,
   and a config without the key, a server from before it among them, reads off. */
function roundsOn(cfg) { return !!(cfg && cfg.work_in_rounds); }
function roundsHere() { return roundsOn(S.data && S.data.config); }

/* Celebrations' line in Settings names what it celebrates on all three screens, the end of a round only
   while Work in rounds is ticked, read from the tick as it stands in the card (16 October, the boards'
   part since the switch a screen of 20 October) */
function cheerLine(rounds) {
  return t(rounds ? 'shell.cheer.line_rounds' : 'shell.cheer.line');
}

/* Celebrations' switches in Settings, one a screen in Idiograph (20 October), the one switch in Sift and
   Trace, each ticked as the settings hold it, a file from before the three read as all three */
function cheerDraw(c) {
  document.querySelectorAll('[data-cheer]').forEach((box) => { box.checked = cheerOnFor(c, box.dataset.cheer); });
  $('set-celebrations').checked = c.celebrations !== false;
}

/* whether any Celebrations switch shown is on, which Sound waits on */
function cheerAny() {
  if (APP !== 'idiograph') return $('set-celebrations').checked;
  return [...document.querySelectorAll('[data-cheer]')].some((box) => box.checked);
}

function cheerSoundGate() { $('set-sound').disabled = !cheerAny(); }

/* what Save sends for Celebrations: in Idiograph the three by screen, with `celebrations` true while any
   is on for a page or an app from before them, and in Sift and Trace the one switch */
function cheerBody() {
  if (APP !== 'idiograph') return { celebrations: $('set-celebrations').checked };
  const screens = {};
  document.querySelectorAll('[data-cheer]').forEach((box) => { screens[box.dataset.cheer] = box.checked; });
  return { celebration_screens: screens, celebrations: Object.values(screens).some(Boolean) };
}

/* The switch put on the page, whenever settings arrive: the library's, a case's, the PETs or GETs
   screen's and a save's. Off, the body carries `ai-off`, and every part of the markup marked data-ai
   stands hidden. The record of what an AI made, the "with AI" after a board's name and its History,
   carries no data-ai, so it stays whatever the switch. */
function aiPage(cfg) {
  document.body.classList.toggle('ai-off', !aiOn(cfg));
  // and IPA's never in a thematic analysis project (tadraw), whose own AI draws by aiTaFor (taaibuild)
  if (typeof tMethodNow === 'function' && tMethodNow() === 'ta') document.body.classList.add('ai-off');
  // and each AI feature turned off under AI features in Settings, its controls gone on its own screen
  for (const list of Object.values(AI_FEATURES)) {
    for (const f of list) document.body.classList.toggle(`ai-off-${f}`, !aiFor(cfg, f));
  }
}

/* one AI feature on: AI features on, and its own switch under it not turned off */
function aiFor(cfg, feature) {
  const off = cfg && Array.isArray(cfg[AI_OFF_KEY]) ? cfg[AI_OFF_KEY] : [];
  if (typeof tMethodNow === 'function' && tMethodNow() === 'ta') return false;
  return aiOn(cfg) && !off.includes(feature);
}

/* A thematic analysis project's own AI, its codes for an extract on Coding under the Experiential statements
   switch and its review on Themes under the GETs one (taaibuild, 3 November 2026): on only in such a project, with
   AI features on and the feature's switch not turned off. IPA's controls, marked data-ai, stay away there. */
function aiTaFor(cfg, feature) {
  const off = cfg && Array.isArray(cfg[AI_OFF_KEY]) ? cfg[AI_OFF_KEY] : [];
  if (typeof tMethodNow !== 'function' || tMethodNow() !== 'ta') return false;
  return aiOn(cfg) && !off.includes(feature);
}

let toastTimer;
/* what the line at the foot says, or is about to say */
let toastWords = '';
/* A line at the foot that was put away is shown empty and given its words a frame later, so they come as a change
   inside the status that is already there, which a screen reader says. Orca on Linux said nothing of words that came
   with the line itself (linuxfix, 9 November 2026), and VoiceOver and NVDA hear the same words either way. A line
   that stands already takes the new words at once. */
function say(message, ms = 4200) {
  const el = $('toast');
  const standing = !el.hidden;
  toastWords = message;
  // each line at the foot's own place, whatever place a renamed row gave the one before (see rnShowRow)
  el.style.bottom = '';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, ms);
  // Linux's window says the line to Orca itself (linuxfix4), and the line shows as it does elsewhere
  if (LINUX && typeof window.idiographSay === 'function') window.idiographSay(message);
  else if (LINUX) {
    toastAnew(el, message);
    return;
  }
  if (standing) {
    el.textContent = message;
    toastClear(el);
    return;
  }
  el.textContent = '';
  el.hidden = false;
  const words = () => {
    if (el.hidden || toastWords !== message || el.textContent === message) return;
    el.textContent = message;
    toastClear(el);
  };
  // a frame, or a tenth of a second where a window out of sight draws no frames
  if (typeof requestAnimationFrame === 'function') requestAnimationFrame(words);
  setTimeout(words, 100);
}

/* The line about to show on Linux, its timer, none while no line waits */
let toastDue = null;
/* On Linux every line comes as a new line inside a status Orca knows (linuxfix3, 9 November 2026). WebKitGTK tells Orca
   nothing of a live region's words changing, only of a part added inside it, and only once the status itself has been
   named to Orca, which a status there since the page loaded need not have been, so Orca heard no line at all. So the
   line is put away, the status taken out and put back in its own place, which names it to Orca as a part added to the
   page, and the line shown with its words a little after, a part added inside the status. Since linuxfix4 the app's
   window says the line to Orca itself (idiographSay), and this is for the page in a browser on Linux. */
function toastAnew(el, message) {
  clearTimeout(toastDue);
  el.hidden = true;
  el.textContent = '';
  const live = el.parentElement;
  const home = live && live.parentNode;
  if (home) {
    const next = live.nextSibling;
    live.remove();
    home.insertBefore(live, next);
  }
  toastDue = setTimeout(() => {
    toastDue = null;
    if (toastWords !== message) return;
    el.textContent = message;
    el.hidden = false;
    toastClear(el);
  }, TOAST_ANEW_MS);
}
/* how long after the status is put back the line shows: WebKit names a part added to Orca once the page has settled */
const TOAST_ANEW_MS = 120;

/* What stands at the foot of the screen in front that the line at the foot keeps clear of: the canvas's zoom bar
   and its bin on PETs and GETs, which at 360 it covered (18 October) */
const TOAST_CLEAR = '#themes:not([hidden]) .th-zoomer, #themes:not([hidden]) #th-discard';

/* The line at the foot raised to stand 8px over any of those it would cover, and left at its place where it covers
   none, as at 1280, where it stands between them */
function toastClear(el) {
  const marks = [...document.querySelectorAll(TOAST_CLEAR)];
  if (!marks.length) return;
  const line = el.getBoundingClientRect();
  let top = Infinity;
  for (const it of marks) {
    const r = it.getBoundingClientRect();
    if (!r.width || !r.height || r.left >= line.right || r.right <= line.left || r.bottom <= line.top - 8) continue;
    top = Math.min(top, r.top);
  }
  if (top < Infinity) el.style.bottom = `${Math.max(0, Math.round(window.innerHeight - top + 8))}px`;
}

/* The line at the foot taken away at once while it still says `message`, so a line that says what is
   under way goes as soon as it is done, and a line put up since stays its time (17 October) */
function unsay(message) {
  const el = $('toast');
  if ((el.hidden && toastDue === null) || toastWords !== message) return;
  clearTimeout(toastDue);
  toastDue = null;
  clearTimeout(toastTimer);
  el.hidden = true;
}

/* A writing surface should not make him scroll a four-line field. A pair's fields start at one line. */
function grow(field, lines = 3) {
  field.style.height = 'auto';
  field.style.height = `${Math.max(field.scrollHeight, lines * 26) + 2}px`;
}

const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
/* a folder's path on a line of its own, as Settings shows a project's folder under Sift, Distil and Trace:
   each folder's name held whole in a part and a break allowed after each slash or backslash alone, so a long
   path wraps at its separators on a phone and never inside a name (15 October) */
const pathHtml = (p) => String(p || '').split(/(?<=[\\/])/).filter(Boolean)
  .map((part) => `<span class="path-part">${esc(part)}</span>`).join('<wbr>');
// a line from the server with a command in backticks, the command set in the code face
const withCode = (s) => esc(s).replace(/`([^`]+)`/g, '<span class="mono">$1</span>');

/* The line in the empty statement field: a craft prompt, a fresh one on every turn. They come
   from guidance.md through /api/guidance. A server too old to send them leaves the first one. */
const PROMPT_FALLBACK = t('shell.prompt_fallback');

function placeholderLine() {
  const list = S.prompts.length ? S.prompts : [PROMPT_FALLBACK];
  return list[Math.floor(Math.random() * list.length)];
}

/* ────────────────────────────────────────────────────────── library ── */

/* The home screen, a picker (9 October): the app's three parts named as verbs (15 October), each a
   section that folds, in the order a study does them (15 October, later), Sift, a card for each Sift
   project, newest first, then its own New project and Open project folder, Distil, a card for each
   project in the order they were added and the demo's card after them, then New project and Open
   project folder, and Trace, the same for each Trace project. The order is the page's own, Sift's
   section first in index.html, and drawPick fills them in any order.
   A Distil card opens its project's page, the way back at its
   head with the project's name and question, then its GETs as a wide card, a full-width row for
   each case in the order he drags them into, and Add transcripts under them. Which of the two
   shows is `S.home`, kept in this tab (see `homeKeep`), so a reload keeps it and every way back from
   a case lands on its project's page. The list is fetched afresh every time it shows, at boot and on
   the way back from a case. What was drawn last time is cleared first, so an old row never stands
   on the screen while the new answer is on its way, and an answer that lands after a newer one is
   dropped. With `show` off it is fetched and drawn out of sight, for a page coming back from a
   restart to another screen. */
let libraryAsk = 0;

async function loadLibrary(show = true) {
  if (show) {
    // the home screen alone: a screen left showing under it, Sift's or Trace's of 100vh, made the page
    // twice the window's height with a page scrollbar on every screen after (17 October, the window's
    // Windows shots, where the check went home from Sift and Trace by this function)
    for (const id of ['work', 'themes', 'traj', 'codes-screen', 'sift', 'sift-search', 'trace']) if ($(id)) $(id).hidden = true;
    $('library').hidden = false;
  }
  // the home screen ends any way back to a board a statement's passage was opened from
  if (show) S.backTo = null;
  const ask = ++libraryAsk;
  if ($('projects')) $('projects').innerHTML = '';
  if ($('hp-list')) $('hp-list').innerHTML = '';
  // Idiograph's Home is its projects' and the demo's (its `homeRoute`), and Sift's and Trace's their own
  // projects' (/api/home)
  const own = FAMILY_APPS[APP];
  const data = await api((own && own.homeRoute) || '/api/home');
  if (ask !== libraryAsk) return;
  // the settings as the library has them, which the PETs screen reads the AI switch from when the
  // server behind it is older than its help
  S.libConfig = data.config || null;
  aiPage(S.libConfig);
  // whether the Mac's folder dialog is there, and whether this run is of one project, for Open
  // project folder
  S.chooseRoot = !!data.choose || windowPicks();
  S.oneRun = !!data.one;
  S.lib = data;
  // the app's own reading of its Home's answer first, Idiograph's run of one project opening on its page
  if (own && own.homeTaken) own.homeTaken(data);
  drawFeedback(data.feedback);
  drawHome();
  // what the app's Home asks for after, Idiograph's days (distil.js)
  if (own && own.homeAfter) own.homeAfter(ask);
  loadFamily();
}

/* ── the mark coming in on Idiograph's Home (Adam, 22 October 2026) ── */

/* When the app opens on Home, the mark at its head comes in, in one movement (Adam's notes of 22 October, Home's
   own, the film to follow it): the two square brackets turn round each other in depth and come down from far
   out (since Adam's third notes of 23 October, circling in from up to seven times their size, homeMarkSpin), while the
   crux dot falls, bounces twice off the brackets' foot line and comes to rest in the middle, the two ending at
   the same moment, 1.4 s in. The name fades in while the brackets come in and is whole as they land. Then the
   Preview Edition stamp is stamped on, a quick scale down with a small settle, done by about 1.85 s. Once a window (the tab's session keeps that it has played, so a reload or a restart does not play it
   again, a new window does), never with the system's reduced motion, and never on Sift's or Trace's Home. Whether
   it plays is decided before the first paint by a small script in index.html's head (the class home-mark-due), so
   the resting mark never shows first. It is drawn over the lockup's own mark, which is hidden meanwhile, from the
   mark's own three parts (marks.svg) moved, never redrawn. At the end the cover goes and the lockup's mark shows
   again, so it rests on the very drawing it always was. The cover stands out of the page's flow, so nothing moves
   and nothing waits for it. The film's own title card keeps its three beats.
   The dot's physics are the film's (launchvideo9 film/bounce.js): one ground, the brackets' foot line, where the
   dot's centre is at 18.8 in the mark's 24 units, a fall from 26 above the mark's top, one restitution for both
   bounces worked out so the second rises exactly to the middle (e = 0.624), the first bounce one beat of the film's
   track long (0.526 s). */
const HOME_MARK_KEY = 'idiograph.homeMark';
const HOME_MARK_BOUNCE = (() => {
  const top = -26, ground = 18.8, rest = 12, tFirst = 0.526, squash = 0.22, squashTime = 0.05;
  const h0 = ground - top, h2 = ground - rest;
  const e = Math.pow(h2 / h0, 0.25), h1 = e * e * h0;
  const g = 8 * h1 / (tFirst * tFirst);
  const v1 = e * Math.sqrt(2 * g * h0), v2 = e * v1;
  return { top, ground, rest, tFirst, squash, squashTime, g, v1, v2,
    tFall: Math.sqrt(2 * h0 / g), tRise: Math.sqrt(2 * h2 / g) };
})();

// the dot at s seconds from its first touch of the ground: its centre's y in the mark's units, its squash, shown
function homeMarkDot(s) {
  const { top, ground, rest, g, tFall, tFirst, tRise, v1, v2, squash, squashTime } = HOME_MARK_BOUNCE;
  let y, shown = true;
  if (s < -tFall) { y = top; shown = false; }
  else if (s < 0) { const u = s + tFall; y = top + 0.5 * g * u * u; }
  else if (s < tFirst) y = ground - (v1 * s - 0.5 * g * s * s);
  else if (s < tFirst + tRise) { const u = s - tFirst; y = ground - (v2 * u - 0.5 * g * u * u); }
  else y = rest;
  let sq = 0;
  for (const [at, amt] of [[0, squash], [tFirst, squash * v2 / v1]]) {
    const d = Math.abs(s - at);
    if (d < squashTime) sq = Math.max(sq, amt * (1 - d / squashTime));
  }
  return { y, sx: 1 + sq, sy: 1 - sq, shown };
}

/* Since 23 October 2026 (Adam: one of a random set, different each time, in the Pixar lamp's spirit) the spin is
   one of seven ways in, each the mark become a character for a few seconds and each ending on the very lockup,
   then the stamp as the spin has it: the spin, Pong, Pinball, the anagram, Football and the kiss (Adam's ideas)
   and the race (the builder's, named by Adam). Which one plays is the next of a shuffled order kept in the page's
   own storage (homeMarkNext), so every one plays once before any plays again and never the same twice running. Given a name
   it plays that one (homeMarkPlay('pinball'), for a recording), with no control for it anywhere on the page. */
const HOME_MARK_ORDER_KEY = 'idiograph.homeMarkOrder';
const HOME_MARK_WAYS = ['spin', 'pong', 'pinball', 'anagram', 'football', 'kiss', 'race'];

// the next way in: the first left of this round's shuffled order, a new round shuffled when none is left, its
// first never the one that played last. A storage that will not answer gives a random one
function homeMarkNext(ways = HOME_MARK_WAYS, store = null, rand = Math.random) {
  try {
    const keep = store || localStorage;
    const held = JSON.parse(keep.getItem(HOME_MARK_ORDER_KEY) || 'null') || {};
    const last = ways.includes(held.last) ? held.last : null;
    let left = Array.isArray(held.left) ? held.left.filter((w, i, all) => ways.includes(w) && all.indexOf(w) === i) : [];
    if (!left.length) {
      left = ways.slice();
      for (let i = left.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [left[i], left[j]] = [left[j], left[i]]; }
      if (left[0] === last && left.length > 1) { const j = 1 + Math.floor(rand() * (left.length - 1)); [left[0], left[j]] = [left[j], left[0]]; }
    }
    const way = left.shift();
    keep.setItem(HOME_MARK_ORDER_KEY, JSON.stringify({ left, last: way }));
    return way;
  } catch { return ways[Math.floor(Math.random() * ways.length)]; }
}

function homeMarkPlay(which) {
  const root = document.documentElement;
  // asked for by name, for a recording: whatever is playing goes first, and the next frame starts this one
  if (typeof which === 'string') {
    const old = document.querySelector('.wordmark .home-mark');
    if (old) { old.remove(); requestAnimationFrame(() => homeMarkPlay(which)); return; }
    root.classList.add('home-mark-due');
  }
  // the head's own script (page.html) set home-mark-due before the first paint when this open is to play it,
  // so the lockup's mark and name never show first. Whatever happens here, the class goes at the end
  const due = root.classList.contains('home-mark-due');
  const still = () => root.classList.remove('home-mark-due');
  try { sessionStorage.setItem(HOME_MARK_KEY, '1'); } catch { /* private window */ }
  if (!due || APP !== 'idiograph' || window.matchMedia('(prefers-reduced-motion: reduce)').matches) { still(); return; }
  const box = document.querySelector('.wordmark .pe');
  const use = box && box.querySelector('.lockup use');
  const name = box && box.querySelector('.lockup > path');
  const stamp = box && box.querySelector('.pe-stamp');
  if (!use || !name || $('library').hidden) { still(); return; }
  const way = HOME_MARK_WAYS.includes(which) ? which : homeMarkNext();
  if (way === 'spin') homeMarkSpin(box, use, name, stamp, still);
  else homeMarkScene(way, box, use, name, stamp, still);
}

/* The spin (Adam's notes of 23 October, the second round): the brackets come in from far out as solid things with
   depth, circling each other. They start well apart and five times their size, as if high over the paper, and as
   they zoom in they circle closer, each turning with the circle, until they land in place on the paper's surface
   with a small thud and lie flat. Since Adam's fourth notes each is a real solid, a block in CSS 3D for each of its
   strokes, so its arms turn away from the viewer and come back round, their sides and tops showing. The dot's fall
   and bounce into the middle is as it was, coming to rest as they settle. Since his fifth notes they start further
   out and bigger still, as far and as large as the room round the mark allows (up to seven times their size and 22
   units out), so they travel further and faster, and they fade in from nothing, most of it late, whole as they
   land. Then the stamp. About 1.9 s */
function homeMarkSpin(box, use, name, stamp, still) {
  // the mark's own 15 units square in the lockup, where the page draws it (its box, not its strokes' bounds)
  const ctm = use.getScreenCTM(), from = box.getBoundingClientRect();
  const size = ctm ? ctm.a * Number(use.getAttribute('width') || 15) : 0;
  if (!size) { still(); return; }
  const k = size / 24, P = size * 16;
  // the room round the mark: to the window's left and top, down to whatever stands under the wordmark (the
  // notice) and along to just past the name's end, short of the toolbar. The circle starts as large and as far
  // apart as that room allows (5 times the size and 14 units out at most), moved over to where it fits, and
  // comes in to the mark
  const cx = ctm.e + size / 2, cy = ctm.f + size / 2, lock = use.ownerSVGElement.getBoundingClientRect();
  // (the head's top row holds the wordmark and the tools beside it since homehead, 5 November 2026, so what stands
  // under the wordmark comes after that row)
  let under = box.closest('.lib-top') || box.closest('.wordmark');
  under = under && under.nextElementSibling;
  while (under && !under.getBoundingClientRect().height) under = under.nextElementSibling;
  const floor = under ? under.getBoundingClientRect().top : innerHeight;
  const room = { l: cx - 8, r: Math.min(innerWidth - 8, lock.right + 20) - cx, t: cy - 4, b: floor - cy - 6 };
  const D0 = 2;
  // where a bracket is on the circle, e of the way in (0 at the start, 1 landed): its scale, the circle's radius
  // and turn, and the circle's centre moved over by C (all in px from the mark's middle)
  const at = (e, S0, R0, C, side) => {
    const S = 1 + (S0 - 1) * (1 - e), R = 5.5 + (R0 - 5.5) * (1 - e), phi = 1.5 * 2 * Math.PI * (1 - e);
    const x = C.x * (1 - e) + side * R * Math.cos(phi) * k * S, z = -side * R * Math.sin(phi) * k * S;
    return { S, phi, x, y: C.y * (1 - e) + 0.18 * z, z, tilt: -0.3 * (1 - e) * (1 - e) };
  };
  // how far a bracket reaches on the screen each way from the mark's middle all the way in, its corners turned and
  // seen in perspective as the page draws them
  const reach = (S0, R0, C) => {
    const out = { l: 0, r: 0, t: 0, b: 0 };
    for (let i = 0; i <= 60; i++) {
      for (const side of [-1, 1]) {
        const p = at(i / 60, S0, R0, C, side), cp = Math.cos(p.phi), sp = Math.sin(p.phi), ct = Math.cos(p.tilt), st = Math.sin(p.tilt);
        for (const [u, v, w] of [[-3, -9.5, -1], [3, -9.5, -1], [-3, 9.5, -1], [3, 9.5, -1], [-3, -9.5, 1], [3, -9.5, 1], [-3, 9.5, 1], [3, 9.5, 1]]) {
          const X = u * k * p.S, Y = v * k * p.S, Z = w * D0 / 2 * k * p.S;
          const x1 = X * cp + Z * sp, z1 = -X * sp + Z * cp, y2 = Y * ct - z1 * st, z2 = Y * st + z1 * ct;
          const f = P / (P - (p.z + z2)), sx = (p.x + x1) * f, sy = (p.y + y2) * f;
          out.l = Math.max(out.l, -sx); out.r = Math.max(out.r, sx); out.t = Math.max(out.t, -sy); out.b = Math.max(out.b, sy);
        }
      }
    }
    return out;
  };
  // the start's circle (Adam's fifth notes, 23 October: further out still and bigger, so it travels further and
  // faster): as large and as far apart as the room round the mark lets the whole way in, up to 7 times the size
  // and 22 units out, its centre moved over to where it fits. A plain halving search on one dial for the two
  const toward = (lo, hi) => Math.min(Math.max(0, lo), hi);
  const fit = (q) => {
    const S0 = 1.5 + 5.5 * q, R0 = 8 + 14 * q, o = reach(S0, R0, { x: 0, y: 0 });
    const C = { x: toward(o.l - room.l, room.r - o.r), y: toward(o.t - room.t, room.b - o.b) };
    const m = reach(S0, R0, C);
    return { S0, R0, C, fits: m.l <= room.l && m.r <= room.r && m.t <= room.t && m.b <= room.b };
  };
  let lo = 0, hi = 1;
  if (fit(1).fits) lo = 1;
  else for (let i = 0; i < 12; i++) { const q = (lo + hi) / 2; if (fit(q).fits) lo = q; else hi = q; }
  const { S0, R0, C: C0 } = fit(lo);
  // the brackets are drawn at their largest (Z times) and scaled down, so they are sharp all the way in
  const Z = Math.ceil(S0), kz = k * Z;
  const piece = (inner) => `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" style="position:absolute;left:0;top:0;overflow:visible">${inner}</svg>`;
  // a bracket as a solid thing (Adam's fourth notes, 23 October: real 3D, its arms turning away and back): each of
  // its three strokes a block, the stroke's own rectangle (square caps and mitred corner, as marks.svg draws it)
  // as its front and back, and four side faces as deep as the depth (--d). Each face's colour is set each frame
  // from which way it faces (paint), so the side faces read as sides in the mark's own ink
  const FACES = { front: '--c-front', back: '--c-back', left: '--c-left', right: '--c-right', top: '--c-top', bottom: '--c-bottom' };
  const block = ([x0, y0, x1, y1]) => {
    const w = (x1 - x0) * kz, h = (y1 - y0) * kz, f = 'position:absolute;display:block;backface-visibility:hidden;';
    const face = (name, css) => `<span style="${f}background:var(${FACES[name]});box-shadow:0 0 0 0.6px var(${FACES[name]});opacity:var(--o, 1);${css}"></span>`;
    return `<span style="position:absolute;display:block;left:${x0 * kz}px;top:${y0 * kz}px;width:${w}px;height:${h}px;transform-style:preserve-3d">`
      + face('front', `left:0;top:0;width:${w}px;height:${h}px;transform:translateZ(calc(var(--d) / 2))`)
      + face('back', `left:0;top:0;width:${w}px;height:${h}px;transform:rotateY(180deg) translateZ(calc(var(--d) / 2))`)
      + face('right', `left:calc(${w / 2}px - var(--d) / 2);top:0;width:var(--d);height:${h}px;transform:rotateY(90deg) translateZ(${w / 2}px)`)
      + face('left', `left:calc(${w / 2}px - var(--d) / 2);top:0;width:var(--d);height:${h}px;transform:rotateY(-90deg) translateZ(${w / 2}px)`)
      + face('top', `left:0;top:calc(${h / 2}px - var(--d) / 2);width:${w}px;height:var(--d);transform:rotateX(90deg) translateZ(${h / 2}px)`)
      + face('bottom', `left:0;top:calc(${h / 2}px - var(--d) / 2);width:${w}px;height:var(--d);transform:rotateX(-90deg) translateZ(${h / 2}px)`)
      + '</span>';
  };
  // the left bracket's spine and its two arms, and the right's, in the mark's 24 units
  const solid = (blocks) => `<span style="position:absolute;display:block;left:0;top:0;width:${24 * kz}px;height:${24 * kz}px;transform-style:preserve-3d">${blocks.map(block).join('')}</span>`;
  const cover = document.createElement('span');
  cover.className = 'home-mark';
  cover.setAttribute('aria-hidden', 'true');
  cover.style.cssText = `position:absolute;left:${ctm.e - from.left}px;top:${ctm.f - from.top}px;width:${size}px;height:${size}px;`
    + `perspective:${P}px;pointer-events:none;line-height:0`;
  cover.innerHTML = '<span class="spin" style="position:absolute;inset:0;transform-style:preserve-3d">'
    + solid([[3.5, 2.5, 5.5, 21.5], [5.5, 2.5, 9.5, 4.5], [5.5, 19.5, 9.5, 21.5]])
    + solid([[18.5, 2.5, 20.5, 21.5], [14.5, 2.5, 18.5, 4.5], [14.5, 19.5, 18.5, 21.5]]) + '</span>'
    + piece('<circle cx="12" cy="12" r="2.7" stroke="none" style="fill: var(--mark-dot, currentColor)"/>');
  const spin = cover.firstChild, [lb, rb] = spin.children, dot = cover.lastChild;
  // the paper behind the mark, which the side faces lean towards
  let paper = 'transparent';
  for (let el = box; el && paper === 'transparent'; el = el.parentElement) {
    const c = getComputedStyle(el).backgroundColor;
    if (c && c !== 'transparent' && !/rgba\(.*,\s*0\)$/.test(c)) paper = c;
  }
  if (paper === 'transparent') paper = getComputedStyle(document.body).backgroundColor || 'white';
  // a face's colour: the ink as it faces the viewer, leaning to the paper as it turns away, a face turned up a
  // little lighter and one turned down a little darker, as under a plain light from above. `ink` below 1 would
  // lean every face to the paper (the fade is each face's opacity since Adam's fifth notes, so the spin passes 1)
  const paint = (el, phi, tilt, ink) => {
    const cp = Math.cos(phi), sp = Math.sin(phi), ct = Math.cos(tilt), st = Math.sin(tilt);
    const normals = { front: [0, 0, 1], back: [0, 0, -1], left: [-1, 0, 0], right: [1, 0, 0], top: [0, -1, 0], bottom: [0, 1, 0] };
    for (const f of Object.keys(FACES)) {
      const [x, y, z] = normals[f];
      // rotateY(phi) then rotateX(tilt), as the transform has them
      const z1 = -x * sp + z * cp, y2 = y * ct - z1 * st, z2 = y * st + z1 * ct;
      const lean = (1 - Math.max(0, z2)) * (0.5 + 0.16 * -y2), mix = 1 - ink * (1 - lean);
      el.style.setProperty(FACES[f], `color-mix(in srgb, currentColor ${(100 * (1 - mix)).toFixed(1)}%, ${paper})`);
    }
  };
  lb.style.transformOrigin = `${6.5 * kz}px ${12 * kz}px`;
  rb.style.transformOrigin = `${17.5 * kz}px ${12 * kz}px`;
  dot.style.transformOrigin = `${size / 2}px ${size / 2}px`;
  // the brackets land at 1.25 s and settle by 1.4 s, the moment the dot comes to rest, so the dot starts its fall
  // while they circle. Then the stamp, from 1.5 s to 1.85 s
  const land = 1.25, still2 = land + 0.15;
  const hit = still2 - HOME_MARK_BOUNCE.tFirst - HOME_MARK_BOUNCE.tRise;
  const stampAt = still2 + 0.1, stampFor = 0.35, end = stampAt + stampFor;
  const span = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
  // one bracket: on the circle's side `side` (-1 the left), its place, its turn with the circle and its depth
  const place = (el, side, rest, e, depth, thud, fade) => {
    // the circle seen a little from above, so the near one sits a little lower and the blocks' tops show, the
    // tilt gone as they come down onto the paper (at)
    const { S, phi, x, y, z, tilt } = at(e, S0, R0, C0, side);
    el.style.transform = `translate3d(${12 * k + x - rest * kz}px, ${12 * k + y - 12 * kz}px, ${z}px) rotateX(${tilt * 180 / Math.PI}deg) rotateY(${phi * 180 / Math.PI}deg) scale3d(${S * thud / Z}, ${S * thud / Z}, ${S / Z})`;
    el.style.setProperty('--d', `${depth * kz}px`);
    // the fade on each face, never on the solid, since an opacity there would flatten it. A block shows at most
    // three faces to the viewer and they never overlap, so a face's own opacity reads as the solid's
    el.style.setProperty('--o', fade.toFixed(3));
    paint(el, phi, tilt, 1);
  };
  const frame = (t) => {
    // in fast from far out and slowing as they near the paper
    const kk = span(t, 0, land), e = 1 - Math.pow(1 - kk, 1.7);
    const th = span(t, land, still2), thud = th > 0 && th < 1 ? 1 - 0.06 * Math.sin(Math.PI * th) : 1;
    // the depth, full until they near the paper, flat as they land
    const depth = D0 * (1 - span(t, land - 0.4, land) ** 2 * (3 - 2 * span(t, land - 0.4, land)));
    // faded in from nothing at the start to whole as they land, on an ease in, most of it late (Adam's fifth
    // notes), so the mark comes clear as it arrives
    const fade = 1 - Math.cos(kk * Math.PI / 2);
    place(lb, -1, 6.5, e, depth, thud, fade);
    place(rb, 1, 17.5, e, depth, thud, fade);
    // the name fades in once the brackets have circled in off it, whole as they land (from 0.85 s since the
    // larger start of Adam's fifth notes, when at 360 they are over its first letters till about 0.8 s)
    const n = span(t, 0.85, land);
    name.style.opacity = String(n * n * (3 - 2 * n));
    // the stamp, once the mark and the name are done: it comes down onto the page from a little larger, a quick
    // scale down that goes just past its size and settles back, its ink there at once
    if (stamp) {
      const s = span(t, stampAt, end);
      const down = 0.55, over = 0.93;
      const sc = s <= 0 ? 1.45 : s < down ? 1.45 - (1.45 - over) * Math.pow(s / down, 2)
        : over + (1 - over) * Math.sin(((s - down) / (1 - down)) * Math.PI / 2);
      stamp.style.opacity = String(Math.min(1, s / 0.15));
      stamp.style.scale = String(sc);
    }
    const d = homeMarkDot(t - hit);
    // the dot comes clear with the brackets
    dot.style.opacity = d.shown ? fade.toFixed(3) : '0';
    dot.style.transform = `translateY(${(d.y - 12) * k}px) scale(${d.sx}, ${d.sy})`;
  };
  try { frame(0); box.appendChild(cover); } catch { cover.remove(); still(); return; }
  const done = () => {
    cover.remove(); name.style.opacity = '';
    if (stamp) { stamp.style.opacity = ''; stamp.style.scale = ''; }
    still();
  };
  let t0 = null;
  const step = (now) => {
    if (t0 === null) t0 = now;
    const t = (now - t0) / 1000;
    if (t >= end || !cover.isConnected) { done(); return; }
    try { frame(t); } catch { done(); return; }
    requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* The other six are drawn in the lockup's own units (its viewBox, 107.33 by 15) on a copy of the lockup laid
   exactly over it: the mark's two brackets and its dot (marks.svg, a mark's unit 15/24 of the lockup's) and, where
   the letters move or light, IDIOGRAPH's nine letters cut from the name's own path, never redrawn. Each piece is
   moved from where it rests, so the last frame is the lockup itself, and then the copy goes. One gravity for all,
   the spin's (HOME_MARK_BOUNCE), so the dot weighs the same in each. Only the spin's dot comes to rest by bouncing
   off the brackets' foot line (Adam, 23 October: a pinball would drain). In the six it comes into the middle of the
   mark by hmHome, a glide that slows into place with a touch of settle, never touching the foot line. */
const HM = (() => {
  const m = 15 / 24;
  return { m, g: HOME_MARK_BOUNCE.g * m, ground: HOME_MARK_BOUNCE.ground * m, mid: 7.5, r: 2.7 * m,
    lb: { x: 6.5 * m }, rb: { x: 17.5 * m }, nameX: 19.2, nameY: 12.5 };
})();
const hmSpan = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const hmSmooth = (k) => k * k * (3 - 2 * k);
const hmOut = (k) => 1 - Math.pow(1 - k, 3);
const hmInOut = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
const hmLerp = (a, b, k) => a + (b - a) * k;
const hmArc = (k) => Math.sin(Math.PI * Math.min(1, Math.max(0, k)));
// a bump up and back down over a to b, for a squash or a lean that comes and goes
const hmBump = (t, a, b) => (t > a && t < b ? Math.sin(Math.PI * (t - a) / (b - a)) : 0);
// the settle after a sudden stop: 1 at its start, swinging past nothing and back, nothing by its end
const hmSpring = (k) => (k <= 0 ? 1 : k >= 1 ? 0 : Math.exp(-4 * k) * Math.cos(2.5 * Math.PI * k) * (1 - k));

// the dot coming into the middle of the mark from (x0, y0), moving at (vx, vy) as it starts: a spring a little
// under critical damping (w its pace, z its damping), so it glides in, goes a touch past and settles back, drawn
// out a little along its path while it moves fast. `rest` is when it is within a twentieth of a unit
function hmHome(x0, y0, vx = 0, vy = 0, w = 14, z = 0.8) {
  const wd = w * Math.sqrt(1 - z * z), zw = z * w;
  const off = (d0, v0, s) => Math.exp(-zw * s) * (d0 * Math.cos(wd * s) + ((v0 + zw * d0) / wd) * Math.sin(wd * s));
  const pos = (s) => (s <= 0 ? [x0, y0] : [HM.mid + off(x0 - HM.mid, vx, s), HM.mid + off(y0 - HM.mid, vy, s)]);
  let rest = 0;
  while (rest < 3 && Math.hypot(...pos(rest).map((v) => v - HM.mid)) + Math.hypot(...pos(rest + 0.05).map((v) => v - HM.mid)) > 0.1) rest += 0.01;
  return { rest, at(s) {
    const [x, y] = pos(s), [x1, y1] = pos(s + 0.01), v = Math.hypot(x1 - x, y1 - y) / 0.01;
    const st = Math.min(0.14, v / 600);
    return { x, y, a: v > 1 ? Math.atan2(y1 - y, x1 - x) * 180 / Math.PI : 0, sx: 1 + st, sy: 1 - st * 0.6 };
  } };
}
// a value keyed at times, [[t, v], ...], eased in and out between keys and held before the first and after the last
const hmKeys = (t, keys) => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let j = 0; j < keys.length - 1; j++) {
    if (t < keys[j + 1][0]) return hmLerp(keys[j][1], keys[j + 1][1], hmInOut(hmSpan(t, keys[j][0], keys[j + 1][0])));
  }
  return keys[keys.length - 1][1];
};
// a lob under the same gravity from (x0, y0) to (x1, y1) in T seconds, s seconds into it
const hmLob = (x0, y0, x1, y1, T, s) => {
  const vy = (y1 - y0 - 0.5 * HM.g * T * T) / T, u = Math.min(T, Math.max(0, s));
  return { x: hmLerp(x0, x1, u / T), y: y0 + vy * u + 0.5 * HM.g * u * u };
};
// a squash at each touch in `at`, `amt` deep, over 0.06 s either side
const hmTouch = (t, at, amt = 0.22) => {
  let q = 0;
  for (const a of at) { const d = Math.abs(t - a); if (d < 0.06) q = Math.max(q, amt * (1 - d / 0.06)); }
  return q;
};
// the Preview Edition stamp meeting the page at `land`, as the spin and the film put it down (stamp.js's stampOn)
const HM_STAMP = { for: 0.35, down: 0.55 };
// the anagram's pause over GO RAPID HI before the sorting starts (Adam's fifth notes, 23 October)
const HM_PAUSE = 1.0;
function hmStamp(stamp, t, land) {
  if (!stamp) return;
  const { down } = HM_STAMP, over = 0.93, q = hmSpan(t, land - down * HM_STAMP.for, land + (1 - down) * HM_STAMP.for);
  const sc = q <= 0 ? 1.45 : q < down ? 1.45 - (1.45 - over) * Math.pow(q / down, 2)
    : over + (1 - over) * Math.sin(((q - down) / (1 - down)) * Math.PI / 2);
  stamp.style.opacity = String(Math.min(1, q / 0.15));
  stamp.style.scale = String(sc);
}

/* The six, each `{ letters, stamp, extra, init, frame }`: whether it moves IDIOGRAPH's letters itself (or lets the
   name fade in whole), when the stamp meets the page, what more it draws (Pinball's bumpers),
   what it works out once from the letters' places, and each frame, the pieces' places at t seconds set on S. A
   bracket is `{ x, y, r, sx, sy, px, py, o }`, its centre, a turn and a squash about its centre moved by (px, py),
   and its ink. The dot is `{ x, y, a, sx, sy, o }`, squashed along the angle a, and a letter `{ dx, dy, r, sx,
   sy, o }`, moved from its place, turned and squashed about the foot of its middle. */
const HOME_MARK_SCENES = {
  /* Pong (Adam's notes of 23 October, the fourth round: a paddle moves only up and down, as in the arcade game):
     the brackets slide apart to be paddles, and from then on each moves straight up and down on its own line,
     nothing else, never leaning or pushing at the ball. The dot, an 8-bit ball that never squashes, goes straight
     from paddle to paddle at a steady speed on each shot, bouncing off the top and the bottom of the court. Each
     tries to catch the other out: a steep shot off the bottom wall that the left first reads wrong, a smash into
     the bottom corner that the right reaches at the last moment, angled shots off the walls, and a smash the left
     reaches late too. Its return comes away at the rally's speed and slows evenly into the middle of the mark,
     while the paddles line up with it and slide in either side as IDIOGRAPH fades in. About 2.9 s */
  pong: { stamp: 2.7, frame(t, S, K) {
    const { lb, rb, dot } = S;
    lb.o = rb.o = dot.o = hmSpan(t, 0, 0.12);
    S.name = hmSmooth(hmSpan(t, 1.85, 2.45));
    // the court: the left paddle out past the mark as far as the window leaves room (less on a phone), the right
    // short of the name, the ball's walls a little over and under the lockup. The ball meets a paddle's spine
    // inside its mouth, 1.06 from its middle
    const L = Math.max(-11, 6.4 - K.room), R = 14, cL = L + 1.06, cR = R - 1.06;
    const top = -4, bottom = 19;
    // the shots: [time, x, y, the wall it comes off on the way to the next], the serve from the middle and six
    // hits, the last the left's late return
    const shots = [[0.38, HM.mid, HM.mid], [0.62, cR, 3, bottom], [0.9, cL, 9], [1.14, cR, 17, top], [1.4, cL, 2, bottom],
      [1.64, cR, 6], [1.88, cL, 16]];
    const last = shots[shots.length - 1], home = 2.5;
    if (t < shots[0][0]) { dot.x = HM.mid; dot.y = HM.mid; }
    else if (t >= last[0]) {
      // the return: off at the rally's own speed and slowing evenly to rest in the middle, no stop and no turn
      const k = 1 - Math.pow(1 - hmSpan(t, last[0], home), 3);
      dot.x = hmLerp(last[1], HM.mid, k); dot.y = hmLerp(last[2], HM.mid, k);
    } else {
      const i = shots.findIndex((s, j) => t >= s[0] && t < shots[j + 1][0]);
      const [a, x0, y0, wall] = shots[i], [b, x1, y1] = shots[i + 1], k = (t - a) / (b - a);
      // straight at a steady speed, a wall's bounce by unfolding the court about it
      dot.x = hmLerp(x0, x1, k);
      if (wall === undefined) dot.y = hmLerp(y0, y1, k);
      else { const y = hmLerp(y0, 2 * wall - y1, k); dot.y = (wall > HM.mid ? y > wall : y < wall) ? 2 * wall - y : y; }
    }
    // where each paddle is up and down its line: the left goes down with the first smash's line, finds it coming
    // off the wall and comes back up for it, is caught out by the right's smash and reaches it late. The right
    // edges up as the left's smash starts, then goes for the corner at the last moment. After the last return
    // both line up with the middle
    const LK = [[0.62, HM.mid], [0.79, 13.5], [0.89, 9.5], [0.95, 9.5], [1.3, 2.5], [1.4, 2], [1.66, 2], [1.74, 3],
      [1.87, 14.5], [1.92, 14.5], [2.15, HM.mid]];
    const RK = [[0.38, HM.mid], [0.58, 3.5], [0.62, 3], [0.75, 3], [0.95, 2], [1.02, 2.5], [1.13, 15.5], [1.18, 15.5],
      [1.5, 6.5], [1.64, 6], [1.8, 9], [2.1, HM.mid]];
    // across only before the serve, sliding apart to their lines, and after the last return, sliding in to the
    // mark once in line with it
    lb.x = t < 1.9 ? hmLerp(HM.lb.x, L, hmOut(hmSpan(t, 0.12, 0.32))) : hmLerp(L, HM.lb.x, hmInOut(hmSpan(t, 2.15, 2.5)));
    rb.x = t < 1.9 ? hmLerp(HM.rb.x, R, hmOut(hmSpan(t, 0.12, 0.32))) : hmLerp(R, HM.rb.x, hmInOut(hmSpan(t, 2.1, 2.45)));
    lb.y = hmKeys(t, LK); rb.y = hmKeys(t, RK);
  } },

  /* Pinball (Adam's notes of 23 October, the second round): the brackets are flippers from the first frame, lying
     either side of a wide gap, and three small bumpers stand over them in the mark's own room, faint outlines well
     clear of the name. The dot starts at the top of the left flipper and rolls down it, and the flipper kicks it up
     to the right bumper as it arrives (Adam's fourth notes). Each flip after is the same beat: the flipper dips under
     the dot, snaps up and sends it to a bumper, which pulses as it is struck, and the dot falls to the other flipper. Each
     strike lights one run of neighbouring letters at once, as a table's bumper lights the lamps beside it, the name
     faint (off) till then: RA, ID, PH, IOG in four hits (Adam's order since his third notes), left flipper to the
     right bumper, right to the left, left to the right again, right softly up to the top one. Then the bumpers go, the flippers stand up into the mark and
     the dot glides down from the top bumper into the middle, never dropping onto the foot line (a pinball would
     drain). Since Adam's fifth notes the first roll goes on a moment longer, nearly to the flipper's end, before the
     kick. About 3.45 s */
  pinball: { letters: true, stamp: 3.28,
    extra: '<g stroke="currentColor" stroke-width="0.55"><circle r="1.7"/><circle r="1.7"/><circle r="1.7"/></g>',
    init(K) {
      // the table, in the lockup's units: each flipper a bracket's spine (10.625 long) laid down from its outer end,
      // with a gap of 5.5 between the two (3.4 till Adam's second notes), the right one ending 3.6 short of the
      // name's I. With room on the left (10 units or more) they rest 38 degrees down and the gap's room is all taken
      // on the left. A phone's window leaves less, so there they rest steeper, 58 degrees down, which brings their
      // outer ends in, and the gap moves a little to the right, so nothing reaches the window's edge
      const wide = K.room >= 10, A0 = wide ? 38 : 58, D = 5.5, off = HM.r + 0.625, py = 6, cx = 5.5, len = 10.625;
      const reach = len * Math.cos(A0 * Math.PI / 180);
      K.A0 = A0; K.py = py;
      K.pl = wide ? cx - 3.8 - reach : cx - 1.6 - reach; K.pr = wide ? cx + 1.7 + reach : cx + 3.9 + reach;
      // where the dot sits on a flipper D along it, the flipper turned a degrees down (negative is up)
      K.on = (side, a, d = D) => {
        const c = Math.cos(a * Math.PI / 180), s = Math.sin(a * Math.PI / 180);
        return side < 0 ? [K.pl + d * c + off * s, py + d * s - off * c] : [K.pr - d * c - off * s, py + d * s - off * c];
      };
      K.bumpers = [[-2.25, -3.5], [13.25, -3.5], [6.5, -9.5]];
      // the dot meets a bumper a little outside its outline, so the bumper's pulse never swells into it
      const touch = 1.7 + 0.275 + HM.r + 0.35;
      // a bumper struck from (x, y): the dot's centre where it meets the bumper's outline
      const meet = ([x, y], [bx, by]) => { const d = Math.hypot(bx - x, by - y); return [bx - (bx - x) / d * touch, by - (by - y) / d * touch]; };
      // the first beat (Adam's fourth notes): the dot sits at the top of the left flipper, at its outer end, then
      // rolls down it, gathering speed as a ball rolls (five sevenths of gravity along the slope), and the flipper
      // kicks with no dip first. Since his fifth notes it sits a moment longer and rolls on nearly to the
      // flipper's inner end (d1, its edge a little short of the tip) before the kick
      K.roll = { d0: 1.4, d1: len - HM.r - 0.3, from: 0.3 };
      K.roll.a = (5 / 7) * HM.g * Math.sin(A0 * Math.PI / 180);
      K.roll.to = K.roll.from + Math.sqrt(2 * (K.roll.d1 - K.roll.d0) / K.roll.a);
      // the beats after: each flip dips 0.13 s and snaps up in 0.06 s, a shot takes 0.13 s to its bumper, and the
      // fall to the other flipper 0.23 s
      const up = -20, shot = 0.13, down = 0.23;
      const launchL = K.on(-1, up), launchR = K.on(1, up), restL = K.on(-1, A0), restR = K.on(1, A0);
      const hitR = meet(launchL, K.bumpers[1]), hitL = meet(launchR, K.bumpers[0]);
      // the first kick, from near the flipper's tip where the roll ended
      const launch0 = K.on(-1, up, K.roll.d1), hit0 = meet(launch0, K.bumpers[1]);
      const top = [K.bumpers[2][0], K.bumpers[2][1] + touch];
      // the first flip counted from 0.13 s before the dot reaches the sweet spot, as if it had dipped
      const l0 = K.roll.to - 0.13, t1 = l0 + 0.19, h1 = t1 + shot, land2 = h1 + down, t2 = land2 + 0.19, h2 = t2 + shot, land3 = h2 + down;
      K.nodip = l0;
      const t3 = land3 + 0.19, h3 = t3 + shot, land4 = h3 + down, t4 = land4 + 0.19;
      const h4 = t4 + Math.sqrt(2 * (launchR[1] - top[1]) / HM.g);
      K.lands = { left: [l0, land3], right: [land2, land4] };
      K.hits = [h1, h2, h3, h4];
      // which bumper each hit strikes: the right, the left, the right, the top
      K.struck = [1, 0, 1, 2];
      // each hit's run of neighbouring letters: RA, then ID, then PH, then IOG (Adam's order, 23 October)
      K.lamps = [[5, 6], [0, 1], [7, 8], [2, 3, 4]];
      // the dot's flights: [from time, to time, from, to, kind], shots to the bumpers, falls to the flippers
      K.legs = [[t1, h1, launch0, hit0, 'shot'], [h1, land2, hit0, restR, 'fall'], [t2, h2, launchR, hitL, 'shot'],
        [h2, land3, hitL, restL, 'fall'], [t3, h3, launchL, hitR, 'shot'], [h3, land4, hitR, restR, 'fall'],
        [t4, h4, launchR, top, 'shot']];
      K.up = up;
      K.home = h4;
      K.glide = hmHome(top[0], top[1]);
      K.bumperEls = [...K.extra.querySelectorAll('circle')];
    },
    frame(t, S, K) {
      const { lb, rb, dot } = S, A0 = K.A0;
      // a flipper's turn: at rest A0 down, it dips under the dot on it, then snaps up and eases back
      const turn = (lands) => {
        let a = A0;
        for (const l of lands) {
          const s = t - l;
          if (s < 0) break;
          const dip = l === K.nodip ? 0 : 8;
          a = s < 0.11 ? hmLerp(A0, A0 + dip, hmOut(s / 0.11)) : s < 0.13 ? A0 + dip
            : s < 0.19 ? hmLerp(A0 + dip, K.up, hmOut((s - 0.13) / 0.06)) : s < 0.27 ? K.up
            : s < 0.5 ? hmLerp(K.up, A0, hmInOut((s - 0.27) / 0.23)) : A0;
        }
        return a;
      };
      const aL = turn(K.lands.left), aR = turn(K.lands.right);
      // the letters faint (off) until their bumper is struck, then on at once
      S.letters.forEach((l, i) => {
        const n = K.lamps.findIndex((set) => set.includes(i));
        l.o = t >= K.hits[n] ? 1 : 0.26 * hmSmooth(hmSpan(t, 0, 0.3));
      });
      // the bumpers: faint outlines that pulse when struck, a quick swell and brightening that dies away, gone as
      // the dot comes home
      const go = hmSpan(t, K.home + 0.05, K.home + 0.3);
      K.bumperEls.forEach((c, i) => {
        let p = 0;
        K.struck.forEach((b, j) => { const s = t - K.hits[j]; if (b === i && s >= 0 && s < 0.4) p = Math.max(p, Math.exp(-s / 0.07)); });
        const [x, y] = K.bumpers[i];
        c.setAttribute('transform', `translate(${x} ${y}) scale(${(1 + 0.15 * p) * (1 - 0.4 * go)})`);
        c.setAttribute('opacity', String(Math.min(1, 0.35 + 0.6 * p) * hmSmooth(hmSpan(t, 0.25, 0.5)) * (1 - go)));
      });
      // the brackets: flippers from the first frame, each lying about its foot. At the end each swings up into the
      // mark again out at its place, a touch past upright and back, with a small thud, the left a little before
      // the right (`last`), and then the two step in together, so neither sweeps through the other or the dot
      const inAt = K.home + 0.12, inBy = K.home + 0.27;
      const pose = (b, side, a, last) => {
        const early = t < K.home;
        const go = early ? 1 : 1 - hmInOut(hmSpan(t, inAt, inBy));
        const lie = early ? 1 : 1 - hmInOut(hmSpan(t, K.home - 0.08 + last, K.home + 0.06 + last));
        // the right stands up a little in from where it lay, so it keeps clear of the name's I
        const far = (side < 0 ? K.pl : K.pr) - 1.25 * side;
        const lean = 6 * hmBump(t, inBy - 0.05, inBy + 0.13), thud = 1 - 0.05 * hmBump(t, inBy, inBy + 0.14);
        Object.assign(b, { px: 1.25 * side, py: 5.3125, r: -side * ((90 + a) * lie - lean), o: hmSpan(t, 0, 0.15),
          x: hmLerp(side < 0 ? HM.lb.x : HM.rb.x, hmLerp(side > 0 ? Math.min(far, 13.4) : far, far, lie), go),
          y: hmLerp(HM.mid, K.py - 5.3125, lie), sx: thud, sy: thud });
      };
      pose(lb, -1, aL, 0);
      pose(rb, 1, aR, 0.06);
      // the dot: resting on the left flipper, riding each flipper as it dips and snaps, squashed against each
      // flipper and each bumper and drawn out a little on a shot, then gliding home from the top bumper (hmHome)
      dot.o = hmSpan(t, 0, 0.15);
      if (t >= K.home) {
        const d = K.glide.at(t - K.home), q = hmTouch(t, [K.home], 0.18);
        Object.assign(dot, { x: d.x, y: d.y, a: q ? 0 : d.a, sx: d.sx - q, sy: d.sy + q });
        return;
      }
      const leg = K.legs.find(([a, b]) => t >= a && t < b);
      if (leg) {
        const [a, b, p0, p1, kind] = leg, p = hmLob(p0[0], p0[1], p1[0], p1[1], b - a, t - a);
        const v = hmLob(p0[0], p0[1], p1[0], p1[1], b - a, t - a + 0.01);
        Object.assign(dot, { x: p.x, y: p.y, a: Math.atan2(v.y - p.y, v.x - p.x) * 180 / Math.PI });
        if (kind === 'shot') {
          // drawn out along its flight, pressed as it leaves the flipper and as it meets the bumper
          const s = 0.1 * hmArc((t - a) / (b - a)), q = hmTouch(t, [a], 0.22) + hmTouch(t, [b], 0.24);
          dot.sx = 1 + s - q; dot.sy = 1 - s * 0.6 + q;
        } else {
          // squashed against the flipper it lands on, across the flipper's own slant
          const land = hmTouch(t, [b], 0.22);
          dot.a = K.lands.right.includes(b) ? -A0 : A0; dot.sx = 1 + land; dot.sy = 1 - land;
        }
        return;
      }
      // at the top of the left flipper, then rolling down it to the sweet spot
      if (t < K.roll.to) {
        const u = Math.max(0, t - K.roll.from), [x, y] = K.on(-1, A0, K.roll.d0 + 0.5 * K.roll.a * u * u);
        Object.assign(dot, { x, y, a: A0, sx: 1, sy: 1 });
        return;
      }
      // on a flipper, riding its dip and snap: a landing's squash fading, pressed again as it snaps
      const onRight = K.lands.right.some((x) => t >= x && t < x + 0.19);
      const l = (onRight ? K.lands.right : K.lands.left).find((x) => t >= x && t < x + 0.19);
      const [x, y] = K.on(onRight ? 1 : -1, onRight ? aR : aL, !onRight && l === K.nodip ? K.roll.d1 : undefined);
      const q = l === undefined ? 0 : (l > K.lands.left[0] ? hmTouch(t, [l], 0.22) : 0) + 0.2 * hmBump(t, l + 0.12, l + 0.2);
      Object.assign(dot, { x, y, a: onRight ? -aR : aL, sx: 1 + q, sy: 1 - q });
    } },

  /* The anagram (Adam's GO RAPID HI, the joke being that IPA is never rapid, with no comma since his notes of 23
     October): the name comes in as GO RAPID HI between the two brackets, who shake their heads at it. Then they
     sort it in three moves, one at a time, each a bracket taking hold of letters from the side with room between,
     lifting them clear over the line, carrying them and putting them down, while the rest of the phrase stays on
     its line as words. The left steps aside, and the right takes ID out of RAPID and puts it at the front: ID GO
     RAP HI. The left hops in after ID, takes G over O while RAP shuffles along: ID OGRAP HI. The right fetches the
     last I and, as the word closes up under it, drops it in after ID. Both hop home over the word and the dot glides
     into the middle of the mark. Since Adam's fifth notes GO RAPID HI has a beat to land: once the brackets are
     down they hold it in its wrong order for a second (HM_PAUSE), leaning in a little to read it, before they shake
     their heads and start. About 5.4 s */
  anagram: { letters: true, stamp: 5.25,
    init(K) {
      // GO RAPID HI laid out from a word space after the name's D, so ID can be put down at the front without
      // moving anything: word spaces of 10, room for a bracket with a clear gap either side, neighbours that stay
      // neighbours (R A P and I D) at the name's own spacing so they move as one, any other two letters 3 apart
      const order = [4, 3, ' ', 5, 6, 7, 0, 1, ' ', 8, 2], at = {};
      // (8 on a phone, so the right bracket keeps clear of the window's edge)
      K.space = K.room < 10 ? 8 : 10;
      let x = K.L[1].x1 + K.space, prev = null;
      for (const c of order) {
        if (c === ' ') x += K.space;
        else { if (typeof prev === 'number') x += c === prev + 1 ? K.L[c].x0 - K.L[prev].x1 : 3; at[c] = x; x += K.L[c].x1 - K.L[c].x0; }
        prev = c;
      }
      // where each letter's left edge is at the start, and after the left has put G down after O (RAP moved on
      // to keep the name's spacing after G)
      K.start = K.L.map((l, i) => at[i]);
      K.mid = K.start.slice();
      K.mid[4] = K.start[3] + (K.L[3].x1 - K.L[3].x0) + (K.L[4].x0 - K.L[3].x1);
      const rShift = K.mid[4] + (K.L[4].x1 - K.L[4].x0) + (K.L[5].x0 - K.L[4].x1) - K.start[5];
      for (const i of [5, 6, 7]) K.mid[i] = K.start[i] + rShift;
      K.glide = hmHome(HM.mid, -6);
    },
    frame(real, S, K) {
      // the pause over GO RAPID HI: from 0.37 s, with the brackets down and before they shake their heads, the
      // clock below stands still for a second, then runs on a second behind
      const P0 = 0.37, P1 = P0 + HM_PAUSE, t = real < P0 ? real : real < P1 ? P0 : real - HM_PAUSE;
      // on a phone the toolbar sits just over the name's end, so there everything is carried under the line
      // instead of over it, and the brackets come up into place from under it rather than dropping in
      const under = K.room < 10, side = under ? 1 : -1;
      const { lb, rb, dot } = S, Ls = S.letters, g = HM.g, HOLD = 4.6, LIFT = 15 * side, LET = 12.8 * side;
      // a letter's left edge along the name at t, from keyed places, as its offset from where the name has it
      const along = (i, keys) => { Ls[i].dx = hmKeys(t, keys) - K.L[i].x0; };
      const fin = (i) => K.L[i].x0;
      Ls.forEach((l) => { l.o = hmSmooth(hmSpan(t, 0, 0.25)); });
      // a letter let go just clear of what is under the bracket, falling under the same gravity into its place
      // (from under, tossed up so it comes to rest just as it reaches its place)
      const toss = Math.sqrt(2 * Math.abs(LET) / g), dropAt = under ? toss : (-40 + Math.sqrt(1600 - 2 * g * LET)) / g;
      const fall = (at) => (under ? LET * Math.pow(1 - Math.min(1, (t - at) / toss), 2)
        : Math.min(0, LET + 40 * (t - at) + 0.5 * g * (t - at) * (t - at)));
      // move 1, the right takes ID to the front: lift 0.86 to 1.0, carry 1.0 to 1.5, put down by 1.62
      for (const i of [0, 1]) {
        along(i, [[1.0, K.start[i]], [1.5, fin(i)]]);
        Ls[i].dy = hmKeys(t, [[0.86, 0], [1.0, LIFT], [1.5, LIFT], [1.62, 0]]);
        Ls[i].sy = 1 - 0.06 * hmBump(t, 0.78, 0.9) - 0.1 * hmBump(t, 1.6, 1.72);
      }
      // move 2, the left takes G over O: lift 2.0 to 2.12, carry 2.12 to 2.4 as RAP shuffles along, let go 2.5
      along(4, [[2.12, K.start[4]], [2.4, K.mid[4]], [2.8, K.mid[4]], [3.1, fin(4)]]);
      Ls[4].dy = t < 2.5 ? hmKeys(t, [[2.0, 0], [2.12, LIFT], [2.4, LIFT], [2.5, LET]]) : fall(2.5);
      Ls[4].sy = 1 - 0.06 * hmBump(t, 1.9, 2.02) - 0.06 * hmBump(t, 2.48 + dropAt, 2.6 + dropAt);
      for (const i of [5, 6, 7]) along(i, [[2.12, K.start[i]], [2.38, K.mid[i]], [2.8, K.mid[i]], [3.1, fin(i)]]);
      // move 3, the right fetches the last I: lift 2.65 to 2.77, carry 2.77 to 3.17 as the word closes up under
      // it (O, G, RAP and H along to their places), lowered till clear 3.17 to 3.25 and let go
      along(3, [[2.8, K.start[3]], [3.1, fin(3)]]);
      along(8, [[2.8, K.start[8]], [3.1, fin(8)]]);
      along(2, [[2.77, K.start[2]], [3.17, fin(2)]]);
      Ls[2].dy = t < 3.25 ? hmKeys(t, [[2.65, 0], [2.77, LIFT], [3.17, LIFT], [3.25, LET]]) : fall(3.25);
      Ls[2].sy = 1 - 0.06 * hmBump(t, 2.55, 2.67) - 0.08 * hmBump(t, 3.23 + dropAt, 3.35 + dropAt);
      // a bracket's place holding a letter from the side, 2.7 of room between its arms' tips and the letter
      const grip = (i) => HM.nameX + K.L[i].x0 + Ls[i].dx - HOLD, gripR = (i) => HM.nameX + K.L[i].x1 + Ls[i].dx + HOLD;
      const at = (pos) => HM.nameX + pos, w = (i) => K.L[i].x1 - K.L[i].x0;
      // a hop from (x0, y0) to (x1, y1) over k: straight up to `top` (high over the line, so it clears every letter),
      // across, and straight down, so it never sweeps through a letter beside where it takes off or lands
      const hop = (k, x0, y0, x1, y1, top) => [hmLerp(x0, x1, hmInOut(hmSpan(k, 0.2, 0.8))),
        k < 0.5 ? hmLerp(y0, top, hmSmooth(hmSpan(k, 0, 0.3))) : hmLerp(top, y1, hmSmooth(hmSpan(k, 0.7, 1)))];
      const over = HM.mid + 15 * side;
      // how far a bracket has closed in on what it holds, a little, so the taking hold shows
      const tight = (a, b) => 0.4 * (hmSmooth(hmSpan(t, a, a + 0.06)) - hmSmooth(hmSpan(t, b, b + 0.06)));
      lb.o = rb.o = hmSpan(t, 0.05, 0.15);
      lb.py = rb.py = 5.3125;
      // the brackets drop in either side of the phrase and shake their heads at it, leaning away, never into it
      const rise = Math.sqrt(2 * 14 / g), landed = under ? 0.05 + rise : 0.05 + Math.sqrt(2 * (HM.mid + 6) / g);
      const fallIn = under ? HM.mid + 14 * Math.pow(1 - hmSpan(t, 0.05, 0.05 + rise), 2)
        : Math.min(HM.mid, -6 + 0.5 * g * Math.pow(Math.max(0, t - 0.05), 2));
      const shake = t > 0.38 && t < 0.56 ? 6 * Math.sin(4 * Math.PI * (t - 0.38) / 0.18) * (1 - (t - 0.38) / 0.18) : 0;
      // the left: steps aside to the mark (0.6 to 0.85), hops in after ID (1.75 to 1.95), holds G till 2.5, home
      const gStart = at(K.start[4]) - HOLD;
      if (t < 0.6) { lb.x = gStart; lb.y = fallIn; lb.r = -Math.abs(shake); }
      else if (t < 0.85) { const k = hmSpan(t, 0.6, 0.85); [lb.x, lb.y] = hop(k, gStart, HM.mid, HM.lb.x, HM.mid, HM.mid - 5); lb.r = -6 * hmArc(k); }
      else if (t < 1.75) { lb.x = HM.lb.x; lb.y = HM.mid; }
      else if (t < 1.95) { const k = hmSpan(t, 1.75, 1.95); [lb.x, lb.y] = hop(k, HM.lb.x, HM.mid, gStart, HM.mid, over); lb.r = 6 * hmArc(k); }
      else if (t < 2.5) { lb.x = grip(4) + tight(1.94, 2.44); lb.y = HM.mid + Ls[4].dy; lb.r = 5 * hmArc(hmSpan(t, 2.12, 2.4)); }
      else { const k = hmSpan(t, 2.5, 2.9); [lb.x, lb.y] = hop(k, at(K.mid[4]) - HOLD, HM.mid + LET, HM.lb.x, HM.mid, over); lb.r = -7 * hmArc(k); }
      // the right: hops in after RAPID (0.6 to 0.8), holds ID till 1.62, hops to the last I (1.68 to 1.95), waits,
      // holds it from 2.6, home from 3.3
      const iStart = at(K.start[2] + w(2)) + HOLD, dStart = at(K.start[1] + w(1)) + HOLD, dEnd = at(K.L[1].x1) + HOLD;
      if (t < 0.6) { rb.x = iStart; rb.y = fallIn; rb.r = Math.abs(shake); }
      else if (t < 0.8) { const k = hmSpan(t, 0.6, 0.8); [rb.x, rb.y] = hop(k, iStart, HM.mid, dStart, HM.mid, over); rb.r = -6 * hmArc(k); }
      else if (t < 1.68) { rb.x = gripR(1) - tight(0.8, 1.62); rb.y = HM.mid + Ls[1].dy; rb.r = -5 * hmArc(hmSpan(t, 1.0, 1.5)); }
      else if (t < 1.98) { const k = hmSpan(t, 1.68, 1.98); [rb.x, rb.y] = hop(k, dEnd, HM.mid, iStart, HM.mid, over); rb.r = 6 * hmArc(k); }
      else if (t < 3.3) {
        rb.x = gripR(2) - tight(2.58, 3.19); rb.y = HM.mid + (t < 3.25 ? Ls[2].dy : LET) - (t < 2.6 ? 0.6 * hmBump(t, 2.2, 2.5) : 0);
        rb.r = -5 * hmArc(hmSpan(t, 2.77, 3.17));
      } else { const k = hmSpan(t, 3.3, 3.7); [rb.x, rb.y] = hop(k, at(K.L[2].x1) + HOLD, HM.mid + LET, HM.rb.x, HM.mid, over); rb.r = -7 * hmArc(k); }
      // squashes: landing from the drop, a crouch before each hop, each landing and the settle home
      const drop0 = 0.16 * hmBump(real, landed, landed + 0.14);
      const homeL = t > 2.9 ? 0.12 * hmSpring(hmSpan(t, 2.9, 3.15)) : 0, homeR = t > 3.7 ? 0.12 * hmSpring(hmSpan(t, 3.7, 3.95)) : 0;
      lb.sy = 1 - drop0 - 0.1 * hmBump(t, 0.52, 0.62) - 0.1 * hmBump(t, 0.83, 0.93) - 0.1 * hmBump(t, 1.67, 1.77)
        - 0.1 * hmBump(t, 1.93, 2.03) - 0.12 * hmBump(t, 2.88, 2.98) + homeL;
      lb.sx = 1 - homeL;
      rb.sy = 1 - drop0 - 0.12 * hmBump(t, 0.52, 0.62) - 0.1 * hmBump(t, 0.78, 0.86) - 0.1 * hmBump(t, 1.6, 1.7)
        - 0.1 * hmBump(t, 1.96, 2.06) - 0.12 * hmBump(t, 3.68, 3.78) + homeR;
      rb.sx = 1 - homeR;
      // in the pause, each leans its top in a little towards the phrase, reading it, and back, the right a beat
      // after the left, crouched a touch as if bending to look
      const readL = hmBump(real, P0 + 0.1, P1 - 0.15), readR = hmBump(real, P0 + 0.22, P1 - 0.05);
      lb.r += 4 * readL * readL; rb.r -= 4 * readR * readR;
      lb.sy -= 0.04 * readL; rb.sy -= 0.04 * readR;
      // the dot fades in over the mark and glides down into its middle as the right comes home
      dot.o = hmSpan(t, 3.55, 3.63);
      Object.assign(dot, K.glide.at(t - 3.55));
    } },

  /* Football, with a header (Adam's fourth notes of 23 October): the brackets stand apart as two players, the dot
     at the left one's foot, the right one ready on its toes. The left kicks it to the right, who takes it on its
     foot and lofts it back high to the left's head. The left leans back, jumps and heads it, its top swinging
     through, back to the right, who takes it, taps it out in front of itself and chips it into the middle: the
     players trot in and trap it between them as it comes down into the middle of the mark, dead, no bounce off the
     foot line. Each winds back before it kicks. About 3.6 s */
  football: { stamp: 3.45,
    init(K) {
      // the left player out past the mark as far as the window leaves room (less on a phone)
      K.Lp = Math.max(-14, 9.2 - K.room); K.Rp = 13; K.footL = K.Lp + 1.06; K.footR = K.Rp - 1.06;
      // the beats: the left's kick, the right's take and its lob to the head, the header, the right's take, its
      // tap out in front of it and its chip into the middle, landing in the middle as the players arrive
      K.b = { k1: 0.55, t1: 1.0, k2: 1.25, head: 1.75, t2: 2.2, back: [2.3, 2.48], k3: 2.6, mid: 3.15 };
      // where the tap leaves the dot, out of the right's mouth, so its top arm is clear of the chip
      K.chipX = K.footR - 2.4;
      // the header: the left jumps 1.4, and meets the dot with the middle of its top arm as its top swings forward
      // through upright, the dot's centre 12.94 over its foot (its height from the foot, 11.25, and the dot's radius)
      K.jump = 1.4;
      K.headAt = [K.Lp, HM.mid + 5.3125 - K.jump - 11.25 - HM.r];
      // the last kick: from the right's foot to the middle, its speed as it comes down there for the trap
      const T = K.b.mid - K.b.k3, a = hmLob(0, HM.ground, 0, HM.mid, T, T - 0.01), b = hmLob(0, HM.ground, 0, HM.mid, T, T);
      K.trap = hmHome(HM.mid, HM.mid, 0, (b.y - a.y) / 0.01, 40, 0.9);
    },
    frame(t, S, K) {
      const { lb, rb, dot } = S, { Lp, Rp, footL, footR, b: B } = K, G = HM.ground;
      lb.o = rb.o = dot.o = hmSpan(t, 0, 0.25);
      S.name = hmSmooth(hmSpan(t, 0.2, 3.0));
      // each turns about its foot: a wind back, the kick through and a settle
      const kick = (k, w = 20) => (t < k - 0.22 || t > k + 0.3 ? 0 : t < k - 0.04 ? -w * hmSmooth(hmSpan(t, k - 0.22, k - 0.04))
        : t < k ? hmLerp(-w, 12, hmSpan(t, k - 0.04, k)) : 12 * hmSpring(hmSpan(t, k, k + 0.3)));
      // the header: a lean back as the dot comes, its top swinging forward through upright as it meets it, a
      // little past and settling back as it lands
      const h = B.head, nod = t < h - 0.24 || t > h + 0.4 ? 0 : t < h - 0.04 ? -12 * hmSmooth(hmSpan(t, h - 0.24, h - 0.04))
        : t < h + 0.04 ? hmLerp(-12, 10, hmSpan(t, h - 0.04, h + 0.04)) : 10 * hmSpring(hmSpan(t, h + 0.04, h + 0.4));
      lb.py = rb.py = 5.3125;
      lb.r = kick(B.k1) + nod; rb.r = -kick(B.k2, 12) - kick(B.k3, 12);
      // the jump: a crouch, up to its height as it meets the dot, down again with a little give
      const lift = t > h - 0.16 && t < h + 0.16 ? -K.jump * Math.sin(Math.PI * (t - h + 0.16) / 0.32) : 0;
      const ready = -1.1 * (hmArc(hmSpan(t, 0.12, 0.27)) + hmArc(hmSpan(t, 0.27, 0.42)));
      const take = (k) => 0.1 * hmBump(t, k, k + 0.16);
      // the right's tap, a little nudge with its foot that rolls the dot out in front of it for the chip
      const tap = 6 * hmBump(t, B.back[0] - 0.08, B.back[0] + 0.08);
      rb.r -= tap;
      // they trot in under the chip, two small hops each, the left first, the right once the dot is below its arm
      const homeL = hmSpan(t, 2.65, 3.2), homeR = hmSpan(t, 2.75, 3.3);
      lb.x = hmLerp(Lp, HM.lb.x, hmInOut(homeL)); rb.x = hmLerp(Rp, HM.rb.x, hmInOut(homeR));
      lb.y = HM.mid + lift - 1.2 * Math.abs(Math.sin(2 * Math.PI * homeL));
      rb.y = HM.mid + ready - 1.2 * Math.abs(Math.sin(2 * Math.PI * homeR));
      const thudL = 0.05 * hmBump(t, 3.2, 3.35), thudR = 0.05 * hmBump(t, 3.3, 3.45);
      lb.sy = 1 - 0.12 * hmBump(t, h - 0.26, h - 0.14) - 0.08 * hmBump(t, h + 0.14, h + 0.28) - thudL; lb.sx = 1 - thudL;
      rb.sy = 1 - take(B.t1) - take(B.t2) - thudR; rb.sx = 1 - thudR;
      // the dot: at the left foot, lobbed to the right, lofted to the left's head, headed back to the right's foot,
      // then chipped into the middle, over the middle early so it comes down between the players, where they trap
      // it as they arrive: it gives a little and settles (hmHome from its speed as it comes down)
      let q = 0;
      if (t < B.k1) { dot.x = footL; dot.y = G; }
      else if (t < B.k2) { const p = hmLob(footL, G, footR, G, B.t1 - B.k1, t - B.k1); dot.x = p.x; dot.y = p.y; }
      else if (t < B.head) { const p = hmLob(footR, G, K.headAt[0], K.headAt[1], B.head - B.k2, t - B.k2); dot.x = p.x; dot.y = p.y; }
      else if (t < B.back[0]) { const p = hmLob(K.headAt[0], K.headAt[1], footR, G, B.t2 - B.head, t - B.head); dot.x = p.x; dot.y = p.y; }
      else if (t < B.k3) {
        // rolled out along the foot line, slowing, to just in front of the right's foot
        dot.x = hmLerp(footR, K.chipX, hmOut(hmSpan(t, B.back[0], B.back[1]))); dot.y = G;
      } else if (t < B.mid) {
        dot.x = hmLerp(K.chipX, HM.mid, Math.sin(hmSpan(t, B.k3, B.mid) * Math.PI / 2));
        dot.y = hmLob(K.chipX, G, HM.mid, HM.mid, B.mid - B.k3, t - B.k3).y;
      } else { const d = K.trap.at(t - B.mid); dot.x = d.x; dot.y = d.y; }
      q += hmTouch(t, [B.k1, B.t1, B.k2, B.head, B.t2, B.back[0], B.k3], 0.2) + hmTouch(t, [B.mid], 0.14);
      dot.sx = 1 + q; dot.sy = 1 - q;
    } },

  /* The kiss: the brackets stand a little apart leaning in, the tips of their tops meeting over the middle with
     the dot held between them like a kiss. They try to pull apart and the dot holds them, drawn out between the
     tips, and they spring back together. A moment, a crouch, a harder pull, trembling, and the dot pops out
     upwards, the brackets spring upright into their places and the dot floats back down between them into the
     middle of the mark, never dropping onto the foot line (Adam, 23 October). About 3.1 s */
  kiss: { stamp: 2.9,
    init(K) {
      // the tip of a bracket's top arm from its foot's middle, turned by r degrees (the left's, which the right's mirrors)
      K.tip = (r) => { const a = r * Math.PI / 180; return [1.875 * Math.cos(a) + 10.625 * Math.sin(a), 1.875 * Math.sin(a) - 10.625 * Math.cos(a)]; };
      K.lean = 10;
      K.base = HM.mid - HM.r + 0.15 - K.tip(K.lean)[0];
      K.lips = HM.mid + 5.3125 + K.tip(K.lean)[1];
      K.glide = hmHome(HM.mid, -4); K.up = Math.sqrt(2 * (K.lips + 4) / HM.g);
    },
    frame(t, S, K) {
      const { lb, rb, dot } = S, pull = 1.4;
      lb.o = rb.o = dot.o = hmSpan(t, 0, 0.2);
      S.name = hmSmooth(hmSpan(t, 0.2, 2.6));
      // how far each has pulled away from the kiss: in a little for the kiss itself and before each pull
      let d;
      if (t < 0.55) d = -0.3 * hmBump(t, 0.25, 0.5);
      else if (t < 0.65) d = -0.25 * hmSmooth(hmSpan(t, 0.55, 0.65));
      else if (t < 0.9) d = hmLerp(-0.25, 0.8, hmOut(hmSpan(t, 0.65, 0.9)));
      else if (t < 1.0) d = 0.8 + 0.06 * Math.sin(2 * Math.PI * 14 * (t - 0.9));
      else if (t < 1.5) d = 0.8 * hmSpring(hmSpan(t, 1.0, 1.35));
      else if (t < 1.6) d = -0.3 * hmSmooth(hmSpan(t, 1.5, 1.6));
      else if (t < 1.95) { const k = hmSpan(t, 1.6, 1.95); d = hmLerp(-0.3, pull, hmInOut(k)) + 0.12 * k * Math.sin(2 * Math.PI * 16 * (t - 1.6)); }
      else d = null;
      lb.py = rb.py = 5.3125;
      if (d !== null) {
        lb.x = K.base - d; rb.x = 2 * HM.mid - lb.x;
        lb.r = K.lean * (1 - 0.5 * Math.max(0, d) / pull) + 2 * hmBump(t, 0.25, 0.5); rb.r = -lb.r;
        lb.sy = rb.sy = 1 - 0.08 * hmBump(t, 1.5, 1.66);
        // the dot held between the two tips, drawn out as they pull, squeezed as they press
        const [tx, ty] = K.tip(lb.r), gap = 2 * (HM.mid - (lb.x + tx));
        dot.y = HM.mid + 5.3125 + ty;
        dot.sx = Math.max(0.7, (gap + 0.3) / (2 * HM.r)); dot.sy = 1 / Math.sqrt(dot.sx);
      } else {
        // the pop: the brackets spring upright into their places, the dot goes up and floats home between them
        const k = hmSpan(t, 1.95, 2.4), from = K.base - pull, spring = hmSpring(k);
        lb.x = HM.lb.x + (from - HM.lb.x) * spring; rb.x = 2 * HM.mid - lb.x;
        lb.r = K.lean * 0.5 * spring; rb.r = -lb.r;
        const top = 1.95 + K.up;
        if (t < top) {
          const u = top - t, s = 1 - hmSpan(t, 1.95, 2.08);
          dot.y = -4 + 0.5 * HM.g * u * u; dot.sx = 1 - 0.2 * s; dot.sy = 1 + 0.3 * s;
        } else { const p = K.glide.at(t - top); dot.y = p.y; dot.a = p.a; dot.sx = p.sx; dot.sy = p.sy; }
      }
    } },

  /* The race (the builder's own, after the lamp, named by Adam's notes of 23 October, about 18:05): the right
     bracket, the left bracket and the dot race to their places, all three in a hurry, as if late. The right comes
     first, sprinting in from beyond the window's right edge already at full pace, and the left the same way close
     behind. Each leaps up onto the H's right post and runs on along the tops of the letters, the right in even
     strides (R, O and D), the left in longer bounds (G and the second I) that close the gap, and on its last leap
     the left overtakes the right in the air, near the finish, so the right is in its place first and the left a
     moment after. Once in its place neither moves again. The dot comes third, late and trying to catch up, and has
     no say in any of it: a ball thrown hard from beyond the window's right edge by someone out of sight. It comes
     down on the G, bounces high over to the right bracket's top arm, each bounce keeping 0.84 of its speed up and
     losing most of its pace across (the arm nearly all of it), and from the arm it pops up and drops quickly,
     nearly straight down, into the middle, narrowing as it slips between the arms' tips (the dot is 5.4 of the
     mark's units across and the gap between the tips 5), where it is caught with a touch of give. Two big bounces,
     never a run of small hops, and never a hang (markplay8, the check of 23 October). The run in takes its pace
     from the room to the window's edge, so it is about 2.7 s at 360 wide and 3.2 s at 1280, stamp included */
  race: { letters: true,
    init(K) {
      const g = HM.g, shelf = 2.5 - 5.3125 - 0.625, half = 1.875;
      // the stones, where a bracket stands on the letters' tops: the H's right post, R, O, D, G and the second I
      const H = 106.67, R = 68.8, O = 45.2, D = 26.3, G = 57.9, I2 = 36.15;
      // the run in to the foot of the H, as quick as the room to the window's edge needs (never under 260 units a
      // second), then the leap up onto the H's post. Each starts wholly past the window's right edge, already at
      // full pace, its leading edge (3.6 ahead of its middle, leaning into the run) coming in two frames later
      const V = Math.max(260, (K.winR + half + 0.6 - 118) / 0.65), from = K.winR + 2.4 + V / 30, take = 118;
      const run = (from - take) / V, T0 = run + 0.34, lag = 0.3;
      // on a phone the run goes under Home's toolbar: low enough to keep 8 px clear of it
      const over = K.bars.filter((b) => b[2] > take - 4).reduce((y, b) => Math.max(y, b[3]), -Infinity);
      const low = HM.mid + Math.max(0, over + 8.5 / K.unit + 6.8 - HM.mid);
      // each way's legs, [kind, start, end, x0, y0, x1, y1]: a run along the ground, a leap (a lob under the one
      // gravity) and the leap home, across first and then down, so it is clear of the letters before it drops
      const leg = (kind, a, b, x0, y0, x1, y1) => [kind, a, b, x0, y0, x1, y1];
      K.right = { lean: 9, legs: [leg('run', 0, run, from, low, take, low), leg('leap', run, T0, take, low, H, shelf),
        leg('leap', T0 + 0.03, T0 + 0.35, H, shelf, R, shelf), leg('leap', T0 + 0.38, T0 + 0.64, R, shelf, O, shelf),
        leg('leap', T0 + 0.67, T0 + 0.91, O, shelf, D, shelf), leg('home', T0 + 0.94, T0 + 1.28, D, shelf, HM.rb.x, HM.mid)],
      stones: [8, 5, 3, 1] };
      K.left = { lean: 13, legs: [leg('run', lag, lag + run, from, low, take, low), leg('leap', lag + run, T0 + lag, take, low, H, shelf),
        leg('leap', T0 + lag + 0.03, T0 + 0.7, H, shelf, G, shelf), leg('leap', T0 + 0.73, T0 + 0.97, G, shelf, I2, shelf),
        leg('home', T0 + 1.0, T0 + 1.4, I2, shelf, HM.lb.x, HM.mid)], stones: [8, 4, 2] };
      // the ball's two bounces, on the G and on the right bracket's top arm, worked out once for the lockup's own
      // letters (docs/internals.md). It is thrown hard and falls quicker than the mark's other dots (its own gravity
      // about 3 of theirs, the same paths 1.75 times as fast), so it hurries all the way and never hangs. Backward from
      // the end: off the arm it pops up to 10.5 over the letters' tops and drops nearly straight down into the
      // middle, onto the arm it comes from the G at the speed that pop needs (each bounce keeping 0.84 of its speed
      // up), and onto the G from the throw. Each bounce takes most of its pace across, the arm almost all of it
      const e = 0.84, gb = 1.75 * 1.75 * g, arm = 2.5 * HM.m - HM.r, band = 3.5 * HM.m, xG = 57.6, yG = 0.837, xA = 9.8, top = -10.5;
      const upA = Math.sqrt(2 * gb * (arm - top)), upG = Math.sqrt(2 * gb * (yG - arm) + (upA / e) ** 2);
      const hits = [[xG, yG, upG], [xA, arm, upA]];
      const fall = (up, y0, y1) => (up + Math.sqrt(up * up + 2 * gb * (y1 - y0))) / gb;
      // it comes onto the arm a moment after the left bracket is home: late, third
      const tO = T0 + 1.48 - fall(upG, yG, arm), arcs = [];
      let t = tO;
      hits.forEach(([x0, y0, up], i) => {
        // the last, off the arm, crosses the arms' middle line at the mark's middle and goes on down to it
        const T = i < hits.length - 1 ? fall(up, y0, hits[i + 1][1]) : fall(up, y0, HM.mid);
        const vx = i < hits.length - 1 ? (x0 - hits[i + 1][0]) / T : (x0 - HM.mid) / fall(up, y0, band);
        arcs.push({ t0: t, t1: t + T, x0, y0, up, vx });
        t += T;
      });
      // the throw: it comes down onto the G at the speed the bounce off it needs, from beyond the window's right
      // edge, its pace across the one nearest a throw that enters level with the letters' tops that keeps 8 px
      // clear of Home's toolbar, and clear of the window's top and the letters on the way
      const vyT = hits[0][2] / e, edge = K.winR + HM.r + 0.5, pad = 8.5 / K.unit;
      const at = (vx, s) => [xG + vx * s, yG - vyT * s + 0.5 * gb * s * s];
      const clear = (vx) => {
        const te = (edge - xG) / vx;
        for (let s = 0.004; s <= te; s += 0.002) {
          const [x, y] = at(vx, s);
          if (x + HM.r <= K.winR && y - HM.r < K.winT + 0.8) return false;
          if (K.bars.some((b) => x > b[0] - HM.r - pad && x < b[2] + HM.r + pad && y > b[1] - HM.r - pad && y < b[3] + HM.r + pad)) return false;
          if (x > 19.2 - HM.r && x < 107.4 + HM.r && Math.abs(x - xG) > HM.r && y + HM.r > 2.2) return false;
        }
        return true;
      };
      const want = (edge - xG) * gb / (2 * vyT);
      let vx = 0;
      for (let v = 60; v <= 2000; v += 2) if (clear(v) && (!vx || Math.abs(v - want) < Math.abs(vx - want))) vx = v;
      if (!vx) vx = want;
      const throwAt = tO - (edge - xG) / vx;
      K.ball = { e, gb, vyT, vx, tO, throwAt, arcs, band, end: t };
      // caught in the middle: its speed as it gets there, damped quickly to rest
      const L = arcs[arcs.length - 1], tl = L.t1 - L.t0;
      K.catch = hmHome(L.x0 - L.vx * tl, HM.mid, -L.vx, -L.up + gb * tl, 60, 0.9);
      K.stamp = t + 0.2;
    },
    frame(t, S, K) {
      const { lb, rb, dot } = S, Ls = S.letters, B = K.ball, g = B.gb;
      Ls.forEach((l) => { l.o = hmSmooth(hmSpan(t, 0, 0.25)); });
      // a letter gives under a landing, as much as the weight that lands
      const dent = (i, at, amt) => { Ls[i].sy = Math.min(Ls[i].sy, 1 - amt * hmBump(t, at - 0.02, at + 0.18)); };
      // one bracket at t: off stage before its run, along its legs, standing a moment on a stone between leaps, and
      // in its place, the resting lockup's own, from the moment it lands there
      const way = (p, w) => {
        const legs = w.legs, home = legs[legs.length - 1];
        if (t >= home[2]) return;
        p.py = 5.3125;
        const i = legs.findIndex((l) => t < l[2]);
        const [kind, a, b, x0, y0, x1, y1] = legs[i];
        let air = 0;
        if (t < a) { p.x = x0; p.y = y0; }
        else if (kind === 'run') {
          // at full pace from the first frame, a stride every 0.1 s, its body bobbing and leaning into the run
          const s = t - a, k = s / (b - a);
          p.x = hmLerp(x0, x1, k); p.y = y0 - 0.45 * Math.abs(Math.sin(Math.PI * s / 0.1));
          p.r = -w.lean; p.sy = 1 + 0.04 * Math.cos(2 * Math.PI * s / 0.1); p.sx = 1 - 0.03 * Math.cos(2 * Math.PI * s / 0.1);
          return;
        } else {
          const k = (t - a) / (b - a), q = hmLob(x0, y0, x1, y1, b - a, t - a);
          p.x = kind === 'home' ? hmLerp(x0, x1, 1 - (1 - k) * (1 - k)) : q.x; p.y = q.y; air = hmArc(k);
          // leaning into each leap, upright as it lands, and out of the run still leaning as it springs up
          p.r = -w.lean * (i === 1 ? Math.max(air, 1 - k) : air) * (kind === 'home' ? 1 - k : 1);
        }
        // a quick squash as it lands on a stone and pushes off again (never in its place: it stands still there)
        let sq = 0;
        legs.forEach((l, j) => { if (j && l[0] !== 'home') sq += 0.16 * hmBump(t, l[2] - 0.01, l[2] + 0.06); });
        p.sx = 1 + sq * 0.6 - air * 0.04; p.sy = 1 - sq + air * 0.06;
      };
      way(rb, K.right);
      way(lb, K.left);
      [K.right, K.left].forEach((w) => w.legs.slice(1, -1).forEach((l, j) => dent(w.stones[j], l[2], 0.08)));
      // the ball: thrown in from beyond the window's right edge, then from bounce to bounce, drawn out along its
      // flight the faster it goes, squashed flat as it meets each, and narrowing as it drops between the arms
      const fly = (x, y, vx, vy) => {
        const v = Math.hypot(vx, vy), st = Math.min(0.16, v / 500);
        Object.assign(dot, { x, y, a: Math.atan2(vy, vx) * 180 / Math.PI, sx: 1 + st, sy: 1 - st * 0.6 });
      };
      dot.o = t >= B.throwAt ? 1 : 0;
      const A = B.arcs, last = A[A.length - 1];
      if (t < B.tO) {
        const s = B.tO - Math.max(t, B.throwAt);
        fly(A[0].x0 + B.vx * s, A[0].y0 - B.vyT * s + 0.5 * g * s * s, -B.vx, B.vyT - g * s);
      } else if (t < last.t1) {
        const c = A.find((r) => t < r.t1), s = t - c.t0;
        fly(c.x0 - c.vx * s, c.y0 - c.up * s + 0.5 * g * s * s, -c.vx, -c.up + g * s);
        if (c === last) {
          // through the arms' tips: as narrow as the gap needs, along its fall, from just above them to just below
          const y = dot.y, n = hmSmooth(hmSpan(y, HM.m * 2.5 - 2.6, HM.m * 2.5 - 1.4)) * (1 - hmSmooth(hmSpan(y, HM.m * 4.5 + 1.2, HM.m * 4.5 + 2.4)));
          dot.sx = 1 + 0.2 * n + (dot.sx - 1) * (1 - n); dot.sy = 1 - 0.2 * n + (dot.sy - 1) * (1 - n);
        }
      } else {
        const d = K.catch.at(t - last.t1);
        Object.assign(dot, { x: d.x, y: d.y, a: d.a, sx: d.sx, sy: d.sy });
      }
      const touches = A.map((r) => r.t0);
      dent(4, A[0].t0, 0.06);
      const q = hmTouch(t, touches, 0.24);
      if (q) { dot.a = 0; dot.sx = 1 + q; dot.sy = 1 - q; }
    } },
};

function homeMarkScene(way, box, use, name, stamp, still) {
  const scene = HOME_MARK_SCENES[way], lock = use.ownerSVGElement;
  const at = lock.getBoundingClientRect(), from = box.getBoundingClientRect();
  if (!at.width) { still(); return; }
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', lock.getAttribute('viewBox'));
  svg.setAttribute('class', 'home-mark');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('fill', 'none');
  svg.style.cssText = `position:absolute;left:${at.left - from.left}px;top:${at.top - from.top}px;width:${at.width}px;`
    + `height:${at.height}px;overflow:visible;pointer-events:none`;
  // IDIOGRAPH's nine letters from the name's own path, its subpaths in turn: I, D, I, O, G, R's two, A's two, P, H's three
  const parts = (name.getAttribute('d') || '').split(/(?=M)/), letterD = [];
  let n = 0;
  for (const c of [1, 1, 1, 1, 1, 2, 2, 1, 3]) { letterD.push(parts.slice(n, n + c).join('')); n += c; }
  const bracket = (d, cx) => `<g><path transform="scale(${HM.m}) translate(${-cx} -12)" d="${d}" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter"/></g>`;
  svg.innerHTML = (scene.letters ? `<g stroke="currentColor" stroke-width="1.3" stroke-linecap="square" stroke-linejoin="miter">${letterD.map((d) => `<path d="${d}"/>`).join('')}</g>` : '')
    + `<g>${scene.extra || ''}</g>`
    + bracket('M8.5 3.5H4.5V20.5H8.5', 6.5) + bracket('M15.5 3.5H19.5V20.5H15.5', 17.5)
    + `<circle r="${HM.r}" stroke="none" style="fill: var(--mark-dot, currentColor)"/>`;
  const kids = [...svg.children], dotEl = kids.pop(), rbEl = kids.pop(), lbEl = kids.pop(), extra = kids.pop();
  const letterEls = scene.letters ? [...kids[0].children] : [];
  // what more it draws, and the room left of the lockup to the window's edge, in the lockup's units
  const unit = at.width / Number(lock.viewBox.baseVal.width || 107.33);
  // and, for the race, the window's right edge and top and Home's toolbar's icons and words, all in those units
  const K = { extra: extra.firstElementChild, unit, room: at.left / unit, winR: (innerWidth - at.left) / unit, winT: -at.top / unit,
    bars: [...document.querySelectorAll('.lib-tools .bar-tool > *')].map((el) => el.getBoundingClientRect()).filter((r) => r.width)
      .map((r) => [(r.left - at.left) / unit, (r.top - at.top) / unit, (r.right - at.left) / unit, (r.bottom - at.top) / unit]),
    stamp: scene.stamp };
  // when the stamp meets the page, and the end: the scene's own, or (the race) what its init works out
  const ending = () => K.stamp + (1 - HM_STAMP.down) * HM_STAMP.for + 0.01;
  const rest = () => ({
    lb: { x: HM.lb.x, y: HM.mid, r: 0, sx: 1, sy: 1, px: 0, py: 0, o: 1 },
    rb: { x: HM.rb.x, y: HM.mid, r: 0, sx: 1, sy: 1, px: 0, py: 0, o: 1 },
    dot: { x: HM.mid, y: HM.mid, a: 0, sx: 1, sy: 1, o: 1 },
    letters: letterEls.map(() => ({ dx: 0, dy: 0, r: 0, sx: 1, sy: 1, o: 1 })), name: 1 });
  const put = (el, p) => {
    el.setAttribute('transform', `translate(${p.x + p.px} ${p.y + p.py}) rotate(${p.r}) scale(${p.sx} ${p.sy}) translate(${-p.px} ${-p.py})`);
    el.setAttribute('opacity', String(p.o));
  };
  const frame = (t) => {
    const S = rest();
    scene.frame(t, S, K);
    put(lbEl, S.lb); put(rbEl, S.rb);
    const d = S.dot;
    dotEl.setAttribute('transform', `translate(${d.x} ${d.y}) rotate(${d.a}) scale(${d.sx} ${d.sy}) rotate(${-d.a})`);
    dotEl.setAttribute('opacity', String(d.o));
    letterEls.forEach((el, i) => {
      const l = S.letters[i], cx = K.L[i].cx;
      el.setAttribute('transform', `translate(${HM.nameX + l.dx} ${HM.nameY + l.dy}) translate(${cx} -0.65) rotate(${l.r}) scale(${l.sx} ${l.sy}) translate(${-cx} 0.65)`);
      el.setAttribute('opacity', String(l.o));
    });
    name.style.opacity = scene.letters ? '0' : String(S.name);
    hmStamp(stamp, t, K.stamp);
  };
  try {
    box.appendChild(svg);
    // each letter's place along the name, its stroke's half width counted
    K.L = letterEls.map((el) => { const b = el.getBBox(); return { x0: b.x - 0.65, x1: b.x + b.width + 0.65, cx: b.x + b.width / 2 }; });
    if (scene.init) scene.init(K);
    frame(0);
  } catch { svg.remove(); still(); return; }
  const end = ending();
  const done = () => {
    svg.remove(); name.style.opacity = '';
    if (stamp) { stamp.style.opacity = ''; stamp.style.scale = ''; }
    still();
  };
  let t0 = null;
  const step = (now) => {
    if (t0 === null) t0 = now;
    const t = (now - t0) / 1000;
    if (t >= end || !svg.isConnected) { done(); return; }
    try { frame(t); } catch { done(); return; }
    requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ── the family at the foot of each Home (the split's third build) ── */

/* the other two apps, as /api/family lists them, each a card: its icon on the paper tile, its name, its one
   line and Open when installed here or Download when not (decision 4 of the plan: always shown). The
   heading names the two, "Sift and Trace" on Idiograph's Home. A server from before says nothing, and the
   foot stays hidden */
/* Each app's own part of the page, registered by its own script (the family codebase's second build, 22 October
   2026), so this script names none of an app's: Sift's from sift_settings.js (the third build) and Trace's from
   trace.js. Each is `{ screen, screens, route, made, open, home, settingsReset, settingsLoad, aiLoad,
   settingsLater, settingsBody, settingsSends, settingsSend, settingsSaved, spot, searchWhere, searchClear,
   searchLeave, searchTo }`: its screen's id, and every screen of its own where it has more than one, its
   projects' route, what its route made or opened from the New project card, opened, its project opened on a
   screen, its Home section drawn, its parts of Settings emptied as the card opens, loaded, loaded with the AI
   switch on and loaded after the AI's, its keys in Save's body, its Save's sends and their sending, a Save over
   its screen, the screen kept for a reload, and Search's place, its menus put away as the card opens, its
   leaving and its landing, any it lacks passed over. */
const FAMILY_APPS = {};
const familyApp = (screen) => Object.values(FAMILY_APPS).find((a) => a.screen === screen
  || (a.screens || []).includes(screen)) || null;

/* The first answer any app gives to one of the shell's questions, its `name` hook called with `args`, or null when
   none answers (the family codebase's fifth build, 23 October 2026): which screen is in front, the settings a
   screen holds, the title the page should have */
function appsSay(name, ...args) {
  if (typeof FAMILY_APPS === 'undefined') return null;
  for (const own of Object.values(FAMILY_APPS)) {
    const said = typeof own[name] === 'function' ? own[name](...args) : null;
    if (said) return said;
  }
  return null;
}

/* Each app's keys of a kind, `name`, asked in the family's order until one takes the key, true when one did */
function appsKeys(name, e) {
  for (const own of Object.values(FAMILY_APPS)) if (typeof own[name] === 'function' && own[name](e)) return true;
  return false;
}

const FAMILY = { apps: null, busy: false };

async function loadFamily() {
  let data = null;
  try { data = await api('/api/family'); } catch { data = null; }
  FAMILY.apps = data && Array.isArray(data.apps) ? data.apps : null;
  drawFamily();
}

/* each app's icon, the pack's tile where the page has it, else its mark drawn in the ink on the paper tile,
   its one point in the crux orange */
const FAMILY_ICONS = { idiograph: '/apps/idiograph.png', sift: '/apps/sift.png', trace: '/apps/trace.png' };

function familyIcon(app) {
  if (FAMILY_ICONS[app]) return `<span class="family-tile has-img"><img src="${escAttr(FAMILY_ICONS[app])}" alt=""></span>`;
  return `<span class="family-tile"><svg aria-hidden="true" focusable="false"><use href="/marks.svg#${escAttr(app)}"/></svg></span>`;
}

function drawFamily() {
  const apps = FAMILY.apps;
  const box = $('family');
  box.hidden = !apps || !apps.length;
  if (!apps || !apps.length) return;
  $('family-h').textContent = tList(apps.map((a) => a.name));
  $('family-list').innerHTML = apps.map((a) => `<li class="family-card">${familyIcon(a.app)}<div class="family-words">`
    + `<p class="family-name">${esc(a.name)}</p><p class="family-line">${esc(a.line)}</p></div>`
    + `<button type="button" class="ghost small family-go" data-app="${escAttr(a.app)}">${a.installed ? t('shell.family.open') : t('shell.family.download')}</button></li>`).join('');
  $('family-list').querySelectorAll('.family-go').forEach((b) => { b.onclick = () => familyOpen(b.dataset.app); });
}

/* Open starts the other app, or brings it forward, and Download opens its page of releases in the browser */
async function familyOpen(app) {
  if (FAMILY.busy) return;
  FAMILY.busy = true;
  try {
    const data = await api('/api/family-open', { app });
    if (Array.isArray(data.apps)) { FAMILY.apps = data.apps; drawFamily(); }
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); } finally { FAMILY.busy = false; }
}

/* Which the home screen shows, kept in this tab alone, so a reload keeps it and a new tab starts
   on the picker: a project's id, `demo` for the demo, or empty for the picker. Never kept at all
   is null, which a run of one project takes as its project's page. */
const HOME_KEY = 'idiograph-home';

function homeHeld() {
  try { return sessionStorage.getItem(HOME_KEY); } catch { return null; }
}

function homeKeep(id) {
  S.home = String(id || '');
  try { sessionStorage.setItem(HOME_KEY, S.home); } catch { /* private window */ }
}

/* Home as the app has it: Idiograph's picker or a project's page (its `homeDraw`, distil.js), and Sift's
   and Trace's their own section (`home`), Home's place kept as the picker. Then Open Recent's list. */
function drawHome() {
  const data = S.lib || {};
  const own = FAMILY_APPS[APP];
  if (own && own.homeDraw) own.homeDraw(data);
  else {
    if (S.home) homeKeep('');
    $('home-pick').hidden = false;
    if ($('home-project')) $('home-project').hidden = true;
    if (own && own.home) own.home(data);
  }
  windowRecent(data);
}

/* The home screen's projects, for Open Recent in the File menu of the app's own window (17 October), each
   with what opens it there, from the app's `recent`: a Distil project's id for its page with the demo last,
   a Sift or Trace project's folder. A browser's page has no `idiographRecent`, and nothing happens. */
function windowRecent(data) {
  if (typeof window === 'undefined' || typeof window.idiographRecent !== 'function') return;
  const own = FAMILY_APPS[APP];
  window.idiographRecent(recentNames(own && own.recent ? own.recent(data) : []), FEEDBACK.on);
}

/* Open Recent's names, each told apart from another of its part with the same name, where the list
   showed a project and the demo twice under one name with nothing between them (17 October, the third
   Tauri build): the demo by the word its card's tag carries, any other by its folder's own name, and
   when that is the same too, by the whole folder. A name no other shares stays as it is. */
function recentNames(list) {
  const key = (r) => `${r.part}\n${String(r.name).toLowerCase()}`;
  const counted = (rows) => rows.reduce((m, r) => m.set(key(r), (m.get(key(r)) || 0) + 1), new Map());
  const last = (path) => String(path || '').replace(/[\\/]+$/, '').split(/[\\/]/).pop() || String(path || '');
  const where = (r) => String(r.folder || r.id || '');
  const many = counted(list);
  const once = list.map((r) => (many.get(key(r)) > 1 ? Object.assign({}, r, { name: `${r.name} (${r.demo ? 'demo' : last(where(r))})` }) : r));
  const still = counted(once);
  return once.map((r, i) => (still.get(key(r)) > 1 && !list[i].demo ? Object.assign({}, r, { name: `${list[i].name} (${where(list[i])})` }) : r));
}

/* The Mac's folder dialog takes a second or so to come up, so while one is on its way a second
   click asks for none, the button pressed reads Wait and the pointer says it is coming. The server
   opens one at a time as well. */
let PICKING = false;

/* In Idiograph's own window the system's folder dialog opens on the window itself, on a Mac and on
   Windows alike (17 October), and the folder chosen there goes to the server as if typed, so `ask`
   takes the path, and a dialog cancelled sends nothing. Each dialog's words are the server's own for
   the Mac's dialog. Nothing else knows of the window: a browser's page has no `idiographPick`. */
const PICK_SAYS = {
  project: t('shell.pick.project'),
  newProject: t('shell.pick.new_project'),
  newSift: t('shell.pick.new_sift'),
  openSift: t('shell.pick.open_sift'),
  newTrace: t('shell.pick.new_trace'),
  openTrace: t('shell.pick.open_trace'),
  traceFile: t('shell.pick.trace_file'),
  sent: t('shell.pick.sent'),
  sentInto: t('shell.pick.sent_into'),
  audio: t('shell.pick.audio'),
};

function windowPicks() {
  return typeof window !== 'undefined' && typeof window.idiographPick === 'function';
}

async function picking(ask, btn, says = '', files = false) {
  if (PICKING) return { chosen: false };
  PICKING = true;
  document.body.classList.add('picking');
  const was = btn ? btn.textContent : '';
  if (btn) { btn.textContent = t('shell.pick.wait'); btn.disabled = true; }
  try {
    if (!windowPicks()) return await ask();
    const path = await window.idiographPick(says, files);
    return path ? await ask(String(path)) : { chosen: false };
  } finally {
    PICKING = false;
    document.body.classList.remove('picking');
    if (btn) { btn.textContent = was; btn.disabled = false; }
  }
}

/* The fold of each section of the picker, kept in this browser by its id, `analysis` or `sift`, so
   a reload keeps it. Nothing here reaches the server. */
const FOLD_KEY = 'idiograph-shut';

function shutIds() {
  try {
    const held = JSON.parse(localStorage.getItem(FOLD_KEY) || '[]');
    return Array.isArray(held) ? held.map(String) : [];
  } catch { return []; }
}

function keepFold(id, shut) {
  try {
    const held = new Set(shutIds());
    if (shut) held.add(String(id)); else held.delete(String(id));
    localStorage.setItem(FOLD_KEY, JSON.stringify([...held]));
  } catch { /* private window */ }
}

/* a section's head folds it and opens it again, the fold drawn as it was kept */
function foldable(section, head, id) {
  const draw = (shut) => {
    section.classList.toggle('shut', shut);
    head.setAttribute('aria-expanded', String(!shut));
  };
  draw(shutIds().includes(String(id)));
  head.onclick = () => {
    const shut = !section.classList.contains('shut');
    draw(shut);
    keepFold(id, shut);
  };
}

/* ── Back and Forward on Distil's screens (19 October), the family's part ── */

/* Home, from the mark on every bar, View, Home in Idiograph's own window and Cmd + Shift + H (Alt + Home
   off a Mac), Adam's call of 20 October: the screen in front left as its way back leaves it, what is typed
   saved first and a canvas flushed, a save that fails keeping him where he is, then Home's picker. */
async function goHome() {
  if (S.homing || typeof searchWhere !== 'function') return false;
  // an app's own way first, which says whether it went: Idiograph's, nothing while its Back is under way, and
  // the Trajectories board putting itself away (distilHomeFirst)
  for (const own of Object.values(FAMILY_APPS)) {
    const took = own.homeFirst ? await own.homeFirst() : undefined;
    if (took !== undefined) return took;
  }
  const here = searchWhere();
  if (!here || here.screen === 'home') return false;
  S.homing = true;
  try {
    if (here.screen !== 'project' && !(await searchLeaveFor(here))) return false;
    S.backTo = null;
    homeKeep('');
    try { await loadLibrary(); } catch (err) { say(err.message, 9000); }
    window.scrollTo(0, 0);
    return true;
  } finally { S.homing = false; }
}
window.idiographHome = goHome;

/* A line to confirm, OK or Cancel, true for OK: in the app's own window its message box (`idiographConfirm`, the window's),
   since the Mac's web view answers window.confirm with Cancel and shows nothing, which left Remove from Idiograph
   doing nothing there (removefix, 9 November 2026), and in a browser the browser's own. Every confirm asks here. */
async function askSure(message) {
  if (typeof window.idiographConfirm === 'function') return (await window.idiographConfirm(String(message))) === true;
  return window.confirm(String(message));
}

/* Remove from the app asks in the page's own card, since a system's box carries no tick (removetrash, 10 November
   2026): the project's name, Remove from the app, a line saying what happens to its folder, and one tick, off to
   start, to move the folder to the system's Trash too, the line following the tick. Answers null for Cancel or
   Esc, else `{ trash }`, and the app sends `trash` and this page's id with its remove. */
const RM = { done: null };
const trashWhere = () => t(MAC ? 'trash.where.mac' : LINUX ? 'trash.where.linux' : 'trash.where.windows');

function askRemove(name) {
  if (RM.done) rmAnswer(false);
  $('rm-project').textContent = name || '';
  $('rm-project').hidden = !name;
  $('rm-title').textContent = t('trash.card.title', { app: APP_NAME });
  $('rm-trash-word').textContent = t('trash.card.tick', { where: trashWhere() });
  $('rm-trash').checked = false;
  rmLine();
  show('remove-card');
  return new Promise((done) => { RM.done = done; });
}

function rmLine() {
  $('rm-line').textContent = $('rm-trash').checked ? t('trash.card.goes', { where: trashWhere() }) : t('trash.card.keeps');
}

function rmAnswer(go) {
  const done = RM.done;
  RM.done = null;
  const trash = $('rm-trash').checked;
  hide('remove-card');
  if (done) done(go ? { trash } : null);
}

function rmWire() {
  $('rm-trash').onchange = rmLine;
  $('rm-cancel').onclick = () => rmAnswer(false);
  $('rm-go').onclick = () => rmAnswer(true);
}

/* the foot's line once a project is removed: its name, and where its folder went when it went to the Trash */
function removedSaid(name, data, plain) {
  return data && data.trash ? t('trash.removed', { name, where: data.where || trashWhere() }) : plain;
}

/* this page's id, which its beat names (beat.js), sent with a remove so the page asking is not another window */
const pageId = () => window.idiographPageId || '';

/* ── a project's menu, the family's part (barsD, 6 November 2026) ── */

/* A project's menu, the same in Idiograph, Sift and Trace (Adam, 6 November 2026, "Add a menu to both"): behind the
   "..." on its card on Home, and behind its name in a screen's band, a button with a chevron as the participant's
   chooser beside it is. Each app gives the items that apply to its projects as rows, `{ act, word, line, remove }`,
   a line under an item where it has one and Remove from the app last after a rule, and does each item itself. The
   drawing, the opening, the keys and the shutting are these. */
function projectMenuHtml(rows) {
  return rows.map((r, i) => {
    if (r.remove) {
      return `${i ? '<div class="row-menu-rule" role="separator"></div>' : ''}`
        + `<button type="button" class="ghost btn-remove" role="menuitem" data-act="${escAttr(r.act)}">${esc(r.word)}</button>`;
    }
    if (r.line) {
      return `<button type="button" class="ghost with-note" role="menuitem" data-act="${escAttr(r.act)}"><span>${esc(r.word)}</span>`
        + `<span class="hc-menu-line">${esc(r.line)}</span></button>`;
    }
    return `<button type="button" class="ghost" role="menuitem" data-act="${escAttr(r.act)}">${esc(r.word)}</button>`;
  }).join('');
}

/* the words the three apps' menus share: Show in Finder, Show in Explorer or on Linux Show in Files, the name GNOME's
   file manager goes by (linuxfix, 9 November 2026), Project settings and Remove from the app */
function projectMenuWord(act, mac, linux = typeof LINUX !== 'undefined' && LINUX) {
  return ({ show: t(mac ? 'shell.project_menu.finder' : linux ? 'shell.project_menu.files' : 'shell.project_menu.explorer'),
    settings: t('shell.project_menu.settings'), remove: t('shell.project_menu.remove', { app: APP_NAME }) })[act] || '';
}

/* a card's "..." and its menu, beside the card's button and never in it, named for the card's project */
function projectDotsHtml(name, rows) {
  if (!rows.length) return '';
  return `<button type="button" class="pc-dots hc-dots" aria-haspopup="true" aria-expanded="false" title="${escAttr(t('shell.project_menu.more'))}"`
    + ` aria-label="${escAttr(t('shell.project_menu.more_for', { name }))}">&#8943;</button>`
    + `<div class="row-menu hc-menu" role="menu" hidden>${projectMenuHtml(rows)}</div>`;
}

/* every card's menu on Home shut but `except`, its dots told so */
function shutProjectMenus(except) {
  for (const menu of document.querySelectorAll('.home-card-li .hc-menu')) {
    if (menu === except || menu.hidden) continue;
    menu.hidden = true;
    const dots = menu.parentElement.querySelector('.hc-dots');
    if (dots) dots.setAttribute('aria-expanded', 'false');
  }
}

/* each card's dots in `list` open its menu, and an item is the app's to do, `pick(act, li)` */
function projectMenus(list, pick) {
  for (const li of list.querySelectorAll('.home-card-li.has-menu')) {
    const dots = li.querySelector('.hc-dots');
    const menu = li.querySelector('.hc-menu');
    if (!dots || !menu) continue;
    const shut = () => { menu.hidden = true; dots.setAttribute('aria-expanded', 'false'); };
    dots.onclick = (e) => {
      e.stopPropagation();
      const open = menu.hidden;
      shutProjectMenus();
      menu.hidden = !open;
      dots.setAttribute('aria-expanded', String(open));
      if (open) menu.querySelector('button').focus();
    };
    menu.onclick = (e) => {
      e.stopPropagation();
      const act = e.target.closest('[data-act]');
      if (!act) return;
      shut();
      dots.focus();
      pick(act.dataset.act, li);
    };
    menu.onkeydown = (e) => menuKeys(e, menu, () => { shut(); dots.focus(); });
  }
}
if (typeof document !== 'undefined' && document.addEventListener) {
  document.addEventListener('click', (e) => {
    const li = e.target.closest && e.target.closest('.home-card-li');
    shutProjectMenus(li ? li.querySelector('.hc-menu') : null);
  });
}

/* the project's name in a screen's band: its words in the name button's own span, the chevron after them kept, the
   whole name, or `title` where one is given, in its tooltip, as a long name is cut at 22em */
function bandNameSet(id, name, title) {
  const el = $(id);
  if (!el) return;
  const words = el.querySelector ? el.querySelector('.ds-proj-name') : null;
  if (words) words.textContent = name || '';
  else el.textContent = name || '';
  el.title = title || name || '';
}

/* The band's menu, `#path-menu`, under the project's name: the name marked open, the first item given the focus,
   Up and Down moving through the items and Esc shutting it with the focus back on the name, as the participant's
   chooser does, and a press elsewhere, a resize or an item shutting it too */
const BAND_MENU = { button: null, pick: null };

function bandMenuShut(focus = false) {
  const menu = $('path-menu');
  if (!menu || menu.hidden) return;
  menu.hidden = true;
  const button = BAND_MENU.button;
  Object.assign(BAND_MENU, { button: null, pick: null });
  if (!button) return;
  button.setAttribute('aria-expanded', 'false');
  if (focus) button.focus();
}

function bandMenuOpen(button, rows, pick) {
  const menu = $('path-menu');
  if (!menu || !button || !rows || !rows.length) return;
  menu.innerHTML = projectMenuHtml(rows);
  Object.assign(BAND_MENU, { button, pick });
  menu.hidden = false;
  button.setAttribute('aria-expanded', 'true');
  const r = button.getBoundingClientRect();
  menu.style.left = `${Math.round(Math.max(8, Math.min(r.left, window.innerWidth - menu.offsetWidth - 8)))}px`;
  menu.style.top = `${Math.round(r.bottom + 4)}px`;
  const first = menu.querySelector('button');
  if (first) first.focus();
}

/* a name's press opens its menu or shuts it again, `menu()` giving the rows and the pick of the project in front, or
   null where it has none */
function bandMenuWire(id, menu) {
  const button = $(id);
  if (!button) return;
  button.onclick = (e) => {
    e.stopPropagation();
    const again = BAND_MENU.button === button;
    bandMenuShut();
    if (again) return;
    const m = menu();
    if (m) bandMenuOpen(button, m.rows, m.pick);
  };
}

/* The way back to the table from a record (sifttable, Adam's choice of option C, 8 November 2026). Since barsD the
   project's name opens its menu, so a screen with a table gives its name button's id and `{ word, away(), go() }`:
   the table's own name, whether the screen is away from it, and the step back to it. A small link before the name,
   a left chevron and the table's name, stands only away from the table, and is drawn again by bandTableDraw each
   time the view changes. */
const BAND_TABLE = new Map();

function bandTableWire(id, spec) {
  BAND_TABLE.set(id, spec);
  bandTableDraw(id);
}

function bandTableDraw(id) {
  const way = BAND_TABLE.get(id);
  const name = $(id);
  if (!way || !name) return;
  let link = $(`${id}-back`);
  if (!link) {
    link = document.createElement('button');
    link.type = 'button';
    link.id = `${id}-back`;
    link.className = 'ds-back';
    link.innerHTML = '<svg class="ds-back-mark" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M7.4 3 4.4 6l3 3"/></svg><span class="ds-back-word"></span>';
    link.onclick = (e) => { e.stopPropagation(); bandMenuShut(); way.go(); };
    name.parentNode.insertBefore(link, name);
  }
  const back = t('shell.band.back_to', { table: way.word });
  link.querySelector('.ds-back-word').textContent = way.word;
  link.title = back;
  link.setAttribute('aria-label', back);
  link.hidden = !way.away();
}

/* A menu's keys, the band's menu's own made one for every menu (a11yfix, 8 November 2026): Down and Up the next item
   and the one before, round at the ends, Home and End the first and the last, Enter and Space an item's own press,
   and Esc shuts it with `back`, which gives its button the focus. A box for typing in the menu keeps its keys, Esc
   apart. Answers whether it took the key. */
function menuItems(menu) {
  return [...menu.querySelectorAll('button, input[type="checkbox"], input[type="radio"], [role^="menuitem"]')]
    .filter((el) => !el.disabled && !el.closest('[hidden]') && el.getClientRects().length);
}

function menuKeys(e, menu, back) {
  if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); if (back) back(); return true; }
  const typing = e.target && e.target.closest && e.target.closest('textarea, select, input:not([type="checkbox"]):not([type="radio"])');
  if (typing || e.altKey || MOD(e)) return false;
  // Enter ticks a tick, as Space does, where a button's own Enter presses it
  if (e.key === 'Enter' && e.target && e.target.matches && e.target.matches('input[type="checkbox"], input[type="radio"]')) {
    e.preventDefault(); e.stopPropagation(); e.target.click(); return true;
  }
  const step = { ArrowDown: 1, ArrowUp: -1 }[e.key];
  if (!step && e.key !== 'Home' && e.key !== 'End') return false;
  const items = menuItems(menu);
  if (!items.length) return false;
  e.preventDefault();
  e.stopPropagation();
  const at = items.indexOf(document.activeElement);
  const to = e.key === 'Home' ? 0 : e.key === 'End' ? items.length - 1
    : at < 0 ? (step > 0 ? 0 : items.length - 1) : (at + step + items.length) % items.length;
  items[to].focus();
  return true;
}

/* a menu's first item given the focus, for a menu opened from the keyboard */
function menuFirst(menu) {
  const first = menu ? menuItems(menu)[0] : null;
  if (first) first.focus();
}

/* the roles a screen reader hears a menu by: the menu, each plain button in it an item, and each tick a ticked item */
function menuRoles(menu) {
  if (!menu) return;
  menu.setAttribute('role', 'menu');
  for (const b of menu.querySelectorAll('button:not([role])')) b.setAttribute('role', 'menuitem');
  for (const b of menu.querySelectorAll('input[type="checkbox"]:not([role])')) b.setAttribute('role', 'menuitemcheckbox');
  for (const b of menu.querySelectorAll('input[type="radio"]:not([role])')) b.setAttribute('role', 'menuitemradio');
}

function bandMenuBoot() {
  const menu = $('path-menu');
  if (!menu) return;
  menu.onclick = (e) => {
    e.stopPropagation();
    const act = e.target.closest('[data-act]');
    if (!act) return;
    const pick = BAND_MENU.pick;
    bandMenuShut(true);
    if (pick) pick(act.dataset.act);
  };
  menu.onkeydown = (e) => menuKeys(e, menu, () => bandMenuShut(true));
  document.addEventListener('pointerdown', (e) => {
    if (BAND_MENU.button && !e.target.closest('#path-menu') && !BAND_MENU.button.contains(e.target)) bandMenuShut();
  }, true);
  window.addEventListener('resize', () => bandMenuShut());
}

/* a Sift or Trace card's hover: the folder it sits in and its name, joined by the separator that folder is
   written with, a backslash on Windows, so the whole path reads as one (GitHub's Windows run, 15 October) */
const homeHover = (r) => (r.where ? `${r.where}${r.where.includes('\\') && !r.where.includes('/') ? '\\' : '/'}${r.name}` : r.name);

/* Sift's New project and Open project folder, one card in New project's style: the folder, chosen
   in the Mac's dialog or typed, then the Sift project's name, and for a new one its question. The
   server checks the folder as it is chosen and fills the name, its own for a project opened, the
   folder's for an empty one, while the field is empty, and says in one line what it refuses. Create
   project makes the project and its card, and Open project keeps the project in the list, writing
   nothing into its folder, and opens it. */
const RVC = { mode: 'new', folder: '', busy: false, part: 'sift' };
// the route each part's card asks, from its own script, Sift's projects or Trace's (15 October)
const rvRoute = (part) => FAMILY_APPS[part].route;

function openReviewCard(mode, part = 'sift') {
  Object.assign(RVC, { mode, folder: '', busy: false, part: part === 'trace' ? 'trace' : 'sift' });
  const card = $('rv-card');
  $('rv-kicker').textContent = RVC.part === 'trace' ? 'Trace' : 'Sift';
  card.querySelector('h2').textContent = t(mode === 'open' ? 'shell.project.open_folder' : 'shell.project.new');
  $('rv-go').textContent = t(mode === 'open' ? 'shell.project.open' : 'shell.project.create');
  // a Trace project has a name alone, no research question
  $('rv-question-line').hidden = mode === 'open' || RVC.part === 'trace';
  $('rv-folder').value = '';
  $('rv-name').value = '';
  $('rv-question').value = '';
  $('rv-choose').hidden = !S.chooseRoot;
  $('rv-go').disabled = false;
  rvChoices([]);
  rvSaid('');
  show('rv-card');
  (S.chooseRoot ? $('rv-choose') : $('rv-folder')).focus();
}

function rvSaid(line) {
  $('rv-said').textContent = line;
  $('rv-said').hidden = !line;
}

/* the reviews inside a folder that holds several, a button each by its folder's name, which takes it */
function rvChoices(choices) {
  $('rv-choices').hidden = !choices.length;
  $('rv-pick').innerHTML = choices.map((c, i) => `<button type="button" class="ghost small" data-i="${i}">${esc(c.label)}</button>`).join('');
  $('rv-pick').querySelectorAll('button').forEach((b) => { b.onclick = () => rvFolder(choices[Number(b.dataset.i)].folder); });
}

/* the folder, from the Mac's dialog with no path or typed, checked by the server for the card's mode.
   For Open review a folder holding one review inside it gives that review, and one holding several
   stands in the field with them offered under it. */
async function rvFolder(path) {
  let data;
  try {
    data = path ? await api(rvRoute(RVC.part), { op: 'folder', mode: RVC.mode, path })
      : await picking((chosen) => api(rvRoute(RVC.part), { op: 'folder', mode: RVC.mode, path: chosen }), $('rv-choose'),
        PICK_SAYS[(RVC.mode === 'open' ? 'open' : 'new') + (RVC.part === 'trace' ? 'Trace' : 'Sift')]);
  } catch (err) { rvChoices([]); rvSaid(needsRestart(err) ? RESTART_LINE : err.message); return false; }
  rvChoices(data.choices || []);
  if (data.choices) {
    rvSaid('');
    RVC.folder = '';
    $('rv-folder').value = data.folder;
    $('rv-pick').querySelector('button').focus();
    return false;
  }
  if (!data.chosen) return false;
  rvSaid('');
  RVC.folder = data.folder;
  $('rv-folder').value = data.folder;
  if (!$('rv-name').value.trim()) $('rv-name').value = data.name || '';
  return true;
}

async function rvMake() {
  if (RVC.busy) return;
  const typed = $('rv-folder').value.trim();
  if (typed && typed !== RVC.folder && !(await rvFolder(typed))) return;
  // with no folder the server says to name one
  const folder = typed ? RVC.folder : '';
  const open = RVC.mode === 'open';
  RVC.busy = true;
  $('rv-go').disabled = true;
  try {
    const route = rvRoute(RVC.part);
    const got = open
      ? await api(route, { op: 'open', folder, name: $('rv-name').value.trim() })
      : await api(route, { op: 'new', folder, name: $('rv-name').value.trim(),
        question: $('rv-question').value.trim() });
    hide('rv-card');
    // a project made opens on Search strategy, as Distil's New project opens the project it made,
    // and one opened opens on its step, and a Trace project opens on its claims, each by its own script
    const own = FAMILY_APPS[RVC.part];
    if (own && own.made) own.made(got);
    else if (got.project && own) own.open(got.project.folder);
    else loadLibrary().catch((err) => say(err.message, 9000));
  } catch (err) {
    rvSaid(needsRestart(err) ? RESTART_LINE : err.message);
  } finally {
    RVC.busy = false;
    $('rv-go').disabled = false;
  }
}

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

/* ── rename a participant, the family's part ── */

/* One handle for every list he puts in his order (12 October): a project's rows here, and in Sift
   the rows of Set columns and the exclusion reasons. It is a button of six dots, `.pc-grip`, the
   name it had on the rows, with Drag to move on hover and a label naming what it moves and the keys.
   `gripDrag` and `gripKeys` move it, and each list gives them its own `how`: `rows`, the selector of
   its items within the list, `live`, the id of the line a screen reader hears, `said`, the words of
   an item's new place, and `moved`, called with the items in their new order once one has moved. */
function gripHtml(name) {
  return `<button type="button" class="pc-grip" data-act="grip" aria-label="${escAttr(t('shell.grip.label', { name }))}" title="${escAttr(t('shell.grip.title'))}">`
    + '<svg viewBox="0 0 12 18" aria-hidden="true" focusable="false"><circle cx="3" cy="3" r="1.4"/><circle cx="9" cy="3" r="1.4"/>'
    + '<circle cx="3" cy="9" r="1.4"/><circle cx="9" cy="9" r="1.4"/><circle cx="3" cy="15" r="1.4"/><circle cx="9" cy="15" r="1.4"/></svg></button>';
}

/* A drag by the handle: the item follows the pointer, taking its place among the others as it
   passes each one's middle, and `how.moved` hears when it is let go somewhere new. The window
   hears the pointer, since an item moved in the list loses any hold its handle had, so the drag goes
   on wherever the pointer goes, with a mouse, a pen or a finger alike. */
function gripDrag(e, li, list, how) {
  if (e.button !== 0) return;
  e.preventDefault();
  const pointer = e.pointerId;
  const before = [...list.querySelectorAll(how.rows)];
  li.classList.add('dragging');
  const move = (ev) => {
    if (ev.pointerId !== pointer) return;
    const others = [...list.querySelectorAll(how.rows)].filter((row) => row !== li);
    const next = others.find((row) => { const box = row.getBoundingClientRect(); return ev.clientY < box.top + box.height / 2; });
    if (next) { if (li.nextElementSibling !== next) list.insertBefore(li, next); }
    else if (list.lastElementChild !== li) list.appendChild(li);
  };
  const end = (ev) => {
    if (ev.pointerId !== pointer) return;
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', end);
    window.removeEventListener('pointercancel', end);
    li.classList.remove('dragging');
    const now = [...list.querySelectorAll(how.rows)];
    if (now.some((row, i) => row !== before[i])) how.moved(now);
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', end);
  window.addEventListener('pointercancel', end);
}

/* Alt + Up and Alt + Down on a handle move its item one place, the drag for the keyboard, and the
   handle keeps the focus. The new place is said for a screen reader. Answers whether it took the
   key, for Sift's screens, which hear every key first. */
function gripKeys(e, li, list, how) {
  if (!e.altKey || (e.key !== 'ArrowUp' && e.key !== 'ArrowDown')) return false;
  e.preventDefault();
  e.stopPropagation();
  const rows = [...list.querySelectorAll(how.rows)];
  const at = rows.indexOf(li);
  const to = at + (e.key === 'ArrowUp' ? -1 : 1);
  if (at < 0 || to < 0 || to >= rows.length) return true;
  if (e.key === 'ArrowUp') list.insertBefore(li, rows[to]);
  else list.insertBefore(li, rows[to].nextElementSibling);
  li.querySelector('button.pc-grip').focus();
  $(how.live).textContent = how.said(li, to, rows.length);
  how.moved([...list.querySelectorAll(how.rows)]);
  return true;
}

/* ── the quote being built, the family's part ── */

/* Re-drawing the turn drops the live selection, so the piece just taken is put back: `h` keeps
   working on it exactly as it did before. */
function restoreSelection(box, start, end) {
  try {
    const walk = document.createTreeWalker(box, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    let pos = 0;
    let started = false;
    let node = walk.nextNode();
    while (node) {
      const len = node.nodeValue.length;
      if (!started && start <= pos + len) { range.setStart(node, start - pos); started = true; }
      if (started && end <= pos + len) {
        range.setEnd(node, end - pos);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        return;
      }
      pos += len;
      node = walk.nextNode();
    }
  } catch { /* the mark on the page is the point, not the selection */ }
}

/* ──────────────────────────────────────────────────────── confetti ── */

/* Confetti in three levels: 1 when a round closes, 2 when the round closed finishes a sheet, 3
   when it finishes the case, and 3 again when the bar's Mark complete marks a case finished
   before. Six cannons at the left and right edges, at a quarter, a half and three quarters of the
   window's height, each a stream over time aimed inward and upward with a little scatter, the three
   on a side starting a beat apart from the bottom up so the eye reads a sweep. The third level adds
   two at the top corners firing down and inward. Every level runs longer and throws more than the
   one before it. The pieces keep gravity, drag, spin and the fade at the end, in the app's tints
   with the crux orange among them, rectangles that turn over and a few long thin strips that
   flutter. One canvas and one frame loop, sized for the device pixel ratio and again if the window
   changes mid-run, at most CONFETTI_ALIVE pieces alive at once so an old machine keeps its frame
   rate. A level fired while one runs replaces it, a hidden tab ends the run quietly, and nothing is
   drawn under reduced motion. The canvas sits over the page and the card, the pointer passes
   through it, and nothing is drawn over the card on screen, so its words stay readable. */
const CONFETTI_LEVELS = {
  1: { ms: 3500, pieces: 500, corners: false },
  2: { ms: 5000, pieces: 900, corners: false },
  3: { ms: 7000, pieces: 1500, corners: true },
};
const CONFETTI_ALIVE = 1200;
// the tints, tokens read from tokens.css as a run starts, so they follow the theme (15 October)
const CONFETTI_TINTS = ['--crux-excel', '--crux', '--accent', '--good', '--rule-firm'];
const CONFETTI_BEAT = 180;   // ms between the cannons on one side
const CONFETTI_FADE = 1000;  // ms of fade at the end of a run
const CONFETTI_TAIL = 1300;  // ms at the end of a run with nothing new fired, the fade inside it
let confettiRun = null;

/* A level's plan in a window w by h: how long it runs, how many pieces it throws, and its cannons,
   each with its place as a share of the window (fx, fy) and in pixels (x, y), its aim in radians
   on the canvas (0 is to the right, a negative angle is upward) and the ms before it starts. Any
   level but 2 and 3 is 1, which is what the bare call fires. */
function confettiPlan(level, w, h) {
  const n = CONFETTI_LEVELS[level] ? Number(level) : 1;
  const spec = CONFETTI_LEVELS[n];
  const deg = Math.PI / 180;
  const cannons = [];
  // from the bottom up, the lowest aimed steepest so every stream arcs toward the middle
  [[0.75, 62], [0.5, 48], [0.25, 34]].forEach(([fy, lift], k) => {
    cannons.push({ fx: 0, fy, aim: -lift * deg, delay: k * CONFETTI_BEAT });
    cannons.push({ fx: 1, fy, aim: -(180 - lift) * deg, delay: k * CONFETTI_BEAT });
  });
  if (spec.corners) {
    cannons.push({ fx: 0, fy: 0, aim: 24 * deg, delay: 3 * CONFETTI_BEAT });
    cannons.push({ fx: 1, fy: 0, aim: (180 - 24) * deg, delay: 3 * CONFETTI_BEAT });
  }
  for (const c of cannons) { c.x = c.fx * w; c.y = c.fy * h; }
  return { level: n, ms: spec.ms, pieces: spec.pieces, cannons };
}

/* ──────────────────────────────────────────────────── celebrations ── */

/* Celebrations, under General in Settings (item 161): one tick for the confetti, the count, the
   line a break shows and the PETs count, on by default, and one for Sound, off by default. They
   are `celebrations` and `sound` in config.json, read from the settings the page last had from the
   server, the case's, the case list's or the PETs screen's, which a save brings up to date
   together. A server from before the two keys sends neither, which reads as on, and sound off.
   Sound plays only with Celebrations on: a soft tick on every step on that decides a turn, a short
   two-note chime when a round closes, and a longer one when a sheet or the case is done. Each is
   made in the page with the Web Audio API, tones with a quick rise and a soft decay, quiet, with no
   audio file, the tick under 200ms. Reduced motion leaves the sound alone, since it is not motion. */
function cheerConfig() {
  const held = typeof S !== 'undefined' ? (S.data && S.data.config) || S.libConfig : null;
  // else the settings a screen of an app's holds, Idiograph's PETs or GETs screen's
  return held || appsSay('config') || {};
}
/* Since 20 October a switch for each screen, `celebration_screens` in the settings, {statements, pets,
   gets}, and the screen in front decides which is read. A settings file from before has only
   `celebrations`, which the server reads as all three (see `celebrations_of`), and a server from before
   sends only that, read the same way here. */
const CHEER_SCREENS = ['statements', 'pets', 'gets'];

function cheerScreen() {
  // the app's screen in front, Idiograph's PETs or GETs, else the statements'
  return appsSay('cheerScreen') || 'statements';
}

function cheerOnFor(c, screen) {
  const by = c && c.celebration_screens;
  if (by && typeof by === 'object' && screen in by) return by[screen] !== false;
  return !c || c.celebrations !== false;
}

const cheerOn = (screen = cheerScreen()) => cheerOnFor(cheerConfig(), screen);
const soundOn = () => cheerOn() && cheerConfig().sound === true;

/* each sound's wave, loudness and notes, [start, pitch, length] in seconds and hertz */
const SOUNDS = {
  tick: { wave: 'triangle', gain: 0.045, notes: [[0, 1760, 0.05]] },
  round: { wave: 'sine', gain: 0.06, notes: [[0, 784, 0.34], [0.12, 1175, 0.46]] },
  long: { wave: 'sine', gain: 0.06, notes: [[0, 659, 0.36], [0.13, 880, 0.36], [0.26, 1047, 0.4], [0.39, 1319, 0.7]] },
};
let soundCtx = null;

function playSound(kind) {
  const spec = SOUNDS[kind];
  const Ctx = spec && typeof window !== 'undefined' ? window.AudioContext || window.webkitAudioContext : null;
  if (!Ctx) return;
  try {
    if (!soundCtx) soundCtx = new Ctx();
    if (soundCtx.state === 'suspended') soundCtx.resume();
    const t0 = soundCtx.currentTime + 0.01;
    for (const [at, pitch, length] of spec.notes) {
      const tone = soundCtx.createOscillator();
      const level = soundCtx.createGain();
      tone.type = spec.wave;
      tone.frequency.value = pitch;
      level.gain.setValueAtTime(0.0001, t0 + at);
      level.gain.exponentialRampToValueAtTime(spec.gain, t0 + at + 0.006);
      level.gain.exponentialRampToValueAtTime(0.0001, t0 + at + length);
      tone.connect(level);
      level.connect(soundCtx.destination);
      tone.start(t0 + at);
      tone.stop(t0 + at + length + 0.02);
    }
  } catch (err) { /* a browser that cannot make the sound stays quiet */ }
}

const sound = (kind) => { if (soundOn()) playSound(kind); };

function confetti(level = 1) {
  if (confettiRun) confettiRun.end();
  // the Celebrations switch silences it, the chime with it, and Sound plays the chime, the longer
  // one for a sheet or the case
  if (!cheerOn()) return;
  sound(Number(level) === 2 || Number(level) === 3 ? 'long' : 'round');
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const canvas = $('confetti');
  const ctx = canvas.getContext('2d');
  let dpr = 1;
  let w = 0;
  let h = 0;
  const size = () => {
    dpr = window.devicePixelRatio || 1;
    w = innerWidth; h = innerHeight;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    canvas.style.width = `${w}px`; canvas.style.height = `${h}px`;
  };
  size();
  canvas.classList.add('on');
  const look = typeof getComputedStyle === 'function' && document.documentElement ? getComputedStyle(document.documentElement) : null;
  const tints = CONFETTI_TINTS.map((t) => (look ? look.getPropertyValue(t).trim() : '')).filter(Boolean);
  const plan = confettiPlan(level, w, h);
  const start = performance.now();
  const until = start + plan.ms;
  const stopAt = plan.ms - CONFETTI_TAIL;
  const share = plan.pieces / plan.cannons.length;
  const due = plan.cannons.map(() => 0);
  const fired = plan.cannons.map(() => 0);
  const bits = [];
  let last = start;
  let raf = 0;
  const run = {};
  const onHide = () => { if (document.hidden) run.end(); };
  run.end = () => {
    cancelAnimationFrame(raf);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvas.classList.remove('on');
    window.removeEventListener('resize', size);
    document.removeEventListener('visibilitychange', onHide);
    if (confettiRun === run) confettiRun = null;
  };
  confettiRun = run;
  window.addEventListener('resize', size);
  document.addEventListener('visibilitychange', onHide);

  const throwOne = (c) => {
    // a small window throws as far in its own terms as a wide one
    const reach = Math.max(0.5, Math.min(1.25, w / 1300));
    const strip = Math.random() < 0.14;
    const aim = c.aim + (Math.random() - 0.5) * 0.4;
    const speed = (1050 + Math.random() * 650) * reach;
    bits.push({
      x: c.fx * w, y: c.fy * h, vx: Math.cos(aim) * speed, vy: Math.sin(aim) * speed,
      w: strip ? 2 + Math.random() * 1.5 : 5 + Math.random() * 6,
      h: strip ? 13 + Math.random() * 11 : 3 + Math.random() * 4,
      a: Math.random() * Math.PI * 2, spin: (Math.random() - 0.5) * 9,
      turn: Math.random() * Math.PI * 2, flip: 3 + Math.random() * 8,
      sway: Math.random() * Math.PI * 2, fall: strip ? 110 + Math.random() * 80 : 170 + Math.random() * 150,
      strip, tint: tints[(Math.random() * tints.length) | 0] || 'currentColor',
    });
  };

  const frame = (now) => {
    if (confettiRun !== run) return;
    const dt = Math.min(0.05, Math.max(0, (now - last) / 1000));
    last = now;
    const t = now - start;
    // each cannon is a steady stream from its start to the tail, never more than its share
    plan.cannons.forEach((c, k) => {
      const span = stopAt - c.delay;
      if (t < c.delay || t > stopAt || fired[k] >= share) return;
      due[k] += (share / span) * dt * 1000;
      while (due[k] >= 1 && fired[k] < share) {
        due[k] -= 1; fired[k] += 1;
        if (bits.length < CONFETTI_ALIVE) throwOne(c);
      }
    });
    const gravity = 900;
    for (let i = bits.length - 1; i >= 0; i -= 1) {
      const b = bits[i];
      const drag = Math.exp(-(b.strip ? 2.2 : 1.5) * dt);
      b.vx *= drag;
      b.vy = b.vy * drag + gravity * dt;
      // falling, a piece of paper settles to its own slow speed and sways as it goes
      if (b.vy > b.fall) b.vy += (b.fall - b.vy) * (1 - Math.exp(-4 * dt));
      b.sway += dt * (b.strip ? 5 : 3);
      b.x += (b.vx + Math.sin(b.sway) * (b.strip ? 40 : 22)) * dt;
      b.y += b.vy * dt;
      b.a += b.spin * dt;
      b.turn += b.flip * dt;
      if (b.y > h + 30 || b.x < -60 || b.x > w + 60) { bits[i] = bits[bits.length - 1]; bits.pop(); }
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.save();
    // the card on screen keeps its words clear: nothing is drawn over it
    const card = document.querySelector('.overlay:not([hidden]) .card');
    if (card) {
      const r = card.getBoundingClientRect();
      ctx.beginPath();
      ctx.rect(0, 0, w, h);
      ctx.rect(r.left, r.top, r.width, r.height);
      ctx.clip('evenodd');
    }
    ctx.globalAlpha = Math.max(0, Math.min(1, (until - now) / CONFETTI_FADE));
    for (const b of bits) {
      // a strip flutters about its fall, a rectangle spins, and both turn over so they catch the light
      const a = b.strip ? b.a * 0.15 + Math.sin(b.sway * 1.3) * 0.9 : b.a;
      const cos = Math.cos(a) * dpr;
      const sin = Math.sin(a) * dpr;
      const thin = Math.cos(b.turn);
      ctx.setTransform(cos, sin, -sin * thin, cos * thin, b.x * dpr, b.y * dpr);
      ctx.fillStyle = b.tint;
      ctx.fillRect(-b.w / 2, -b.h / 2, b.w, b.h);
    }
    ctx.restore();
    if (now < until) raf = requestAnimationFrame(frame);
    else run.end();
  };
  raf = requestAnimationFrame(frame);
}

/* ────────────────────────────────────────────────────────── panels ── */

const show = (id) => { $(id).hidden = false; cardOpen($(id)); };
// Settings shut, and each app's screen behind drawn again where Settings changed it, Idiograph's after its
// timepoints changed (its `settingsShut`, tpAfter), and Idiograph's Project settings the same (settingsplit)
const hide = (id) => {
  $(id).hidden = true;
  if (id === 'settings') Object.values(FAMILY_APPS).forEach((a) => { if (a.settingsShut) a.settingsShut(); });
  if (id === 'projset') Object.values(FAMILY_APPS).forEach((a) => { if (a.projsetShut) a.projsetShut(); });
  cardClose($(id));
};

/* ── the cards, for the keyboard and a screen reader (a11yfix, 8 November 2026) ──

   Every card of the three apps, each overlay and the Search card, opens and closes one way. To a screen reader it
   is a dialog, modal, named by its title. Opened from the keyboard the focus goes to its first field, or to Done, or
   else to the card itself, and opened by the pointer to the card itself, so nothing new shows. Tab and Shift + Tab
   go round inside it. Closed by Esc or by its buttons, the focus goes back to what opened it, unless the app's own
   script has put the focus somewhere already. `show` and `hide` say so at once, and a watch on the cards hears the
   ones an app's script shows and hides itself. */
const CARDS = { open: [], from: new Map(), seen: [], keyed: false };
const CARD_SELECTOR = '.overlay, #search';
const CARD_STOPS = 'a[href], button, input, select, textarea, summary, [tabindex], [contenteditable="true"]';
const CARD_FIELDS = 'input:not([type="button"]):not([type="submit"]):not([type="hidden"]), textarea, select, [role="tab"][aria-selected="true"]';

const cardBox = (o) => (o.classList.contains('card') ? o : o.querySelector(':scope > .card') || o.querySelector('.card') || o);
const cardShown = (o) => !!o && o.isConnected && !o.hidden;
const cardTop = () => [...CARDS.open].reverse().find(cardShown) || null;

/* the dialog's role, modal, and its name: its one heading, or with several, the line above them that names the card */
function cardLabel(o) {
  const box = cardBox(o);
  if (!box.hasAttribute('role')) box.setAttribute('role', 'dialog');
  if (!box.hasAttribute('aria-modal')) box.setAttribute('aria-modal', 'true');
  if (box.hasAttribute('aria-labelledby') || box.hasAttribute('aria-label')) return;
  const heads = box.querySelectorAll('h1, h2');
  const head = (heads.length === 1 ? heads[0] : box.querySelector('.kicker')) || heads[0] || box.querySelector('h3');
  if (!head) return;
  if (!head.id) {
    let id = `${o.id || 'card'}-head`;
    while (document.getElementById(id)) id += '-';
    head.id = id;
  }
  box.setAttribute('aria-labelledby', head.id);
}

/* what Tab stops at inside a card, in order: shown, enabled, and of a group of radios the checked one alone, or its
   first, as the browser's own Tab takes them */
function cardStops(box) {
  return [...box.querySelectorAll(CARD_STOPS)].filter((el) => {
    if (el.disabled || el.tabIndex < 0 || el.closest('[hidden], [inert]') || !el.getClientRects().length) return false;
    if (getComputedStyle(el).visibility === 'hidden') return false;
    if (el.type === 'radio' && el.name) {
      const group = [...box.querySelectorAll('input[type="radio"]')].filter((r) => r.name === el.name && !r.disabled);
      return el === (group.find((r) => r.checked) || group[0]);
    }
    return true;
  });
}

/* the focus into a card that does not hold it: from the keyboard its first field or Done, else the card itself */
function cardFocusIn(o) {
  const box = cardBox(o);
  if (!cardShown(o) || box.contains(document.activeElement)) return;
  const stops = CARDS.keyed ? cardStops(box) : [];
  const done = t('page.done');
  const to = stops.find((el) => el.matches(CARD_FIELDS))
    || stops.find((el) => el.tagName === 'BUTTON' && el.textContent.trim() === done);
  if (to) { to.focus({ preventScroll: true }); return; }
  if (!box.hasAttribute('tabindex')) box.tabIndex = -1;
  box.focus({ preventScroll: true });
}

function cardOpen(o) {
  if (!cardShown(o) || CARDS.open.includes(o)) return;
  cardLabel(o);
  const box = cardBox(o);
  const now = document.activeElement;
  const from = now && now !== document.body && !box.contains(now) ? now
    : [...CARDS.seen].reverse().find((el) => el.isConnected && !box.contains(el)) || null;
  CARDS.from.set(o, from);
  CARDS.open.push(o);
  // after the script that opened it, which may put the focus in it itself
  queueMicrotask(() => cardFocusIn(o));
}

function cardClose(o) {
  const at = o ? CARDS.open.indexOf(o) : -1;
  if (at < 0 || cardShown(o)) return;
  CARDS.open.splice(at, 1);
  const from = CARDS.from.get(o);
  CARDS.from.delete(o);
  const now = document.activeElement;
  if (now && now !== document.body && !cardBox(o).contains(now)) return;
  const top = cardTop();
  const back = from && from.isConnected && from.getClientRects().length && !from.closest('[hidden]')
    && (!top || cardBox(top).contains(from)) ? from : null;
  if (back) back.focus({ preventScroll: true });
  else if (top) cardFocusIn(top);
}

/* Tab and Shift + Tab go round the card in front, and a Tab from outside it comes into it */
function cardTab(e) {
  if (e.key !== 'Tab' || e.altKey || e.ctrlKey || e.metaKey || e.defaultPrevented) return;
  const o = cardTop();
  if (!o) return;
  const box = cardBox(o);
  const now = document.activeElement;
  // a menu of the card's own that stands outside it keeps its own keys
  if (now && !box.contains(now) && now.closest && now.closest('.row-menu:not([hidden]), [role="menu"]:not([hidden]), [role="listbox"]')) return;
  e.preventDefault();
  e.stopPropagation();
  const stops = cardStops(box);
  if (!stops.length) { if (!box.contains(now)) cardFocusIn(o); return; }
  const at = stops.indexOf(now);
  let to;
  if (at >= 0) to = stops[(at + (e.shiftKey ? -1 : 1) + stops.length) % stops.length];
  else if (box.contains(now) && now !== box) {
    // from a part that takes no Tab of its own, the next stop after it or the last before it
    const after = (el) => !!(now.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING);
    to = e.shiftKey ? [...stops].reverse().find((el) => !after(el)) || stops[stops.length - 1] : stops.find(after) || stops[0];
  } else to = e.shiftKey ? stops[stops.length - 1] : stops[0];
  to.focus();
}

/* each card as it shows and hides, and the focus's last places, for the way back */
function cardsWatch() {
  for (const o of document.querySelectorAll(CARD_SELECTOR)) cardLabel(o);
  document.addEventListener('focusin', (e) => {
    CARDS.seen.push(e.target);
    if (CARDS.seen.length > 12) CARDS.seen.shift();
  }, true);
  window.addEventListener('keydown', (e) => { CARDS.keyed = true; cardTab(e); }, true);
  window.addEventListener('pointerdown', () => { CARDS.keyed = false; }, true);
  if (!window.MutationObserver) return;
  const look = (el) => {
    if (!(el instanceof Element) || !el.matches(CARD_SELECTOR)) return;
    if (cardShown(el)) cardOpen(el);
    else cardClose(el);
  };
  new MutationObserver((records) => {
    for (const r of records) look(r.target);
  }).observe(document.body, { attributes: true, attributeFilter: ['hidden'], subtree: true });
  new MutationObserver((records) => {
    for (const r of records) r.addedNodes.forEach(look);
    for (const o of [...CARDS.open]) if (!o.isConnected) { CARDS.open.splice(CARDS.open.indexOf(o), 1); CARDS.from.delete(o); }
  }).observe(document.body, { childList: true });
  for (const o of document.querySelectorAll(CARD_SELECTOR)) if (cardShown(o)) cardOpen(o);
}

/* Send feedback. The bug in either bar opens one card: a box for the note, a line for a reply
   address, and Send beside Cancel. The page sends the note, the address, the screen it came from
   as one word and the browser's user agent, and the server adds the version, the system and the
   time. Nothing from the case goes, no file, no path and nothing else on the page. The words stay
   in the box while the app is open, so a card closed by mistake loses nothing, and only a note
   sent clears it. The bug shows only when the server says the build carries the collector's
   address, and a server from before it says nothing, so the bug stays hidden. */
const FEEDBACK = { on: false, screen: 'statements', busy: false };

function drawFeedback(on) {
  FEEDBACK.on = !!on;
  for (const bug of document.querySelectorAll('.rail-feedback')) bug.hidden = !FEEDBACK.on;
}

/* `screen` is the bar's own short word: home on the first screen, project on a project's page,
   statements, pets, gets, sift, searches or trace. The server and the collector keep those words
   alone, FEEDBACK_SCREENS in server.py and SCREENS in the collector, and take any other as none. */
function openFeedback(screen) {
  if (!FEEDBACK.on) return;
  FEEDBACK.screen = String(screen || '');
  $('feedback-said').hidden = true;
  feedbackReady();
  show('feedback');
  $('feedback-text').focus();
}

/* Send is on only with something to send: the note holds a character that is not a space, and no note is on its way.
   Run as the box takes a character, as the card opens, since the words stay in the box across opens, and as a send
   ends, a note sent leaving the box empty and a failure leaving its words (29 October, fbcard) */
function feedbackReady() {
  const send = $('feedback-send');
  send.disabled = FEEDBACK.busy || !$('feedback-text').value.trim();
}

function closeFeedback() {
  hide('feedback');
  // the focus back where the screen in front keeps it, Idiograph's statements screen's field
  Object.values(FAMILY_APPS).forEach((a) => { if (a.refocus) a.refocus(); });
}

/* An empty box sends nothing, and Send is disabled while it is empty, so no key does it either. While the note is on
   its way the button says Sending, a note sent closes the card with one quiet line, and a failure says why in the
   card with the words still in the box, or in the line at the foot when the card was closed meanwhile. */
async function sendFeedback() {
  const text = $('feedback-text').value.trim();
  if (!text || FEEDBACK.busy) return;
  FEEDBACK.busy = true;
  const send = $('feedback-send');
  send.textContent = t('shell.feedback.sending');
  send.classList.add('busy');
  send.disabled = true;
  $('feedback-said').hidden = true;
  try {
    await api('/api/feedback', {
      text, contact: $('feedback-contact').value.trim(), screen: FEEDBACK.screen, agent: navigator.userAgent,
    });
    $('feedback-text').value = '';
    if (!$('feedback').hidden) closeFeedback();
    say(t('shell.feedback.sent'));
  } catch (err) {
    const line = needsRestart(err) ? RESTART_LINE : err.message;
    $('feedback-said').textContent = line;
    $('feedback-said').hidden = false;
    if ($('feedback').hidden) say(line, 9000);
  } finally {
    FEEDBACK.busy = false;
    send.textContent = t('shell.feedback.send');
    send.classList.remove('busy');
    feedbackReady();
  }
}

/* Settings opens over the home screen, the turn screen, the PETs screen or Sift, and takes its case
   from the one in front of him: the settings it opens with, its project under Projects, the
   workbook its exports write and the GETs its PETs category holds. Over the home screen there is no
   case, and a project's page gives its project and its GETs. */
function settingsCase() {
  // an app's own answer, Idiograph's case, PETs or GETs screen or project's page (distil.js)
  const said = appsSay('settingsCase');
  if (said) return said;
  if (!$('library').hidden) return { path: null, gets: null, themes: false, project: null, config: S.libConfig || (S.data && S.data.config) || {} };
  return { path: null, themes: false, project: null, config: {} };
}
const OVERLAYS = ['round-done', 'help', 'settings', 'ai-confirm', 'projset', 'create', 'import', 'newproject', 'rv-card', 'trim', 'th-confirm', 'th-aicard', 'assign', 'feedback', 'whatsnew', 'rename', 'complete', 'about', 'support', 'skip-confirm', 'hold-card', 'holds-batch', 'remove-card'];
// the cards this page holds, its own app's and the family's, never another app's since each ships alone (panefix)
const overlaysHere = () => OVERLAYS.filter((id) => $(id));
const anyOverlayOpen = () => overlaysHere().some((id) => !$(id).hidden);

/* Settings carries its categories down the left of the card with the chosen one on the right (9
   October). General comes first: AI features, the one switch for every AI part of the app, and
   under it the provider, the model, the key, the prompt and the test bench, then Celebrations.
   The parts follow in the order a study does them (15 October, later): Sift, its databases and the
   AI proposals of a screening, then Distil with its three parts set in under its name, Experiential
   statements, what the turn screen uses, PETs, what the PETs screen uses, its own model under AI and
   GETs among it, and Export, then Trace, its projects' names, and Projects last. The arrow keys walk
   them in this order, as they stand in the list. The home
   screen's Settings opens on General and each screen's own settings on its part: the turn screen's
   cog on Experiential statements, the PETs screen's on PETs, the GETs screen's on PETs with GETs in
   view, Sift's cog and the searches' Settings on Sift. The category chosen holds while the card is
   open, and the next open goes to the screen's own category again. */
// Idiograph's GETs, Export and Projects left Settings on 5 November 2026 (settingsplit, Adam): a project's own
// settings are its Project settings sheet's, and the exports the boards' Export menus'
const PANES_BY_APP = {
  idiograph: ['general', 'formats', 'statements', 'pets', 'ai'],
  sift: ['general', 'formats', 'databases', 'sift', 'zotero', 'ai'],
  trace: ['general', 'formats', 'trace', 'ai'],
};
// every category the card holds, and the ones this app's Settings show, in their order
const PANES_ALL = ['general', 'formats', 'statements', 'pets', 'databases', 'sift', 'zotero', 'trace', 'ai'];
const PANES = PANES_BY_APP[APP];
let paneHeld = 'general';

const onScreen = (id) => !!$(id) && !$(id).hidden;

/* the category a screen's own settings open on: Sift's over Sift and its searches, the PETs
   screen's over the PETs screen, the turn screen's over a case, and General over the home screen */
function screenPane() {
  if (onScreen('sift-search')) return 'databases';
  if (onScreen('sift')) return 'sift';
  if (onScreen('trace')) return 'trace';
  // an app's own screen's, Idiograph's PETs, GETs and statements screens'
  return appsSay('screenPane') || 'general';
}

/* The names a caller may give: a category, or `proposals`, Sift's AI proposals under its Projects, each its
   category. A category of another app's is General. */
const PANE_OF = { proposals: 'sift' };

function showPane(name, focus = false) {
  const asked = PANES.includes(name) ? name : PANE_OF[name] || screenPane();
  const pane = PANES.includes(asked) ? asked : 'general';
  paneHeld = pane;
  document.querySelectorAll('#settings-nav [data-pane]').forEach((tab) => {
    const on = tab.dataset.pane === pane;
    tab.classList.toggle('on', on);
    tab.setAttribute('aria-selected', String(on));
    tab.tabIndex = on ? 0 : -1;
    if (on && focus) tab.focus();
  });
  // each app ships alone since train 53, so a page holds its own app's panes and the family's, never
  // another app's, and a pane the page does not hold is passed over (panefix, 26 October 2026)
  for (const p of PANES_ALL) if ($(`pane-${p}`)) $(`pane-${p}`).hidden = p !== pane;
  $('settings-panes').scrollTop = 0;
}

/* the arrow keys walk the categories, the way a row or a column of tabs answers them */
function paneKeys(e) {
  const step = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key];
  if (!step) return;
  e.preventDefault();
  showPane(PANES[(PANES.indexOf(paneHeld) + step + PANES.length) % PANES.length], true);
}

/* `pane` opens the card on that category: the home screen's Settings on General, the PETs and GETs
   screens' cogs on PETs, and `ai`, the Review tab's link to the switch, on
   General with the switch at the top. With none it opens on the category of the screen it was
   opened over, never where it was left the time before. */
function openSettings(pane) {
  const ctx = settingsCase();
  const c = ctx.config || {};
  // an app's own parts of the card first, Idiograph's projects, statements, view, nudges and PETs limit
  Object.values(FAMILY_APPS).forEach((a) => { if (a.settingsOpen) a.settingsOpen(ctx, c); });
  drawAgentStart();
  // and the agent log's line under it, each app's own (agentlog.js, siftlog, 3 November 2026)
  if (typeof agentLogLine === 'function') agentLogLine();
  $('set-ai').checked = aiOn(c);
  // each of this app's AI features ticked unless the settings turned it off
  const off = Array.isArray(c[AI_OFF_KEY]) ? c[AI_OFF_KEY] : [];
  document.querySelectorAll('[data-ai-feature]').forEach((box) => { box.checked = !off.includes(box.dataset.aiFeature); });
  aiSetDraw();
  drawAppearance();
  drawLanguage();
  drawFormats();
  textSizeOpen();
  // Celebrations on for each screen and Sound off unless the settings say otherwise, as a server from
  // before says neither, and Sound waits on a Celebrations switch being on
  cheerDraw(c);
  $('set-sound').checked = c.sound === true;
  cheerSoundGate();
  // and it quits a few minutes after its last tab closes unless the settings say otherwise
  $('set-quit-closed').checked = c.quit_when_closed !== false;
  // and in Idiograph's own window its updates, the ticks as the window holds them (see updOpen)
  updOpen();
  saidIn('key-said', '');
  $('set-key').value = '';
  S.models = null;
  S.petsOpened = petsValue(c);
  aiHeldOpen(c);
  showPane(pane || screenPane());
  // the key, the models, the bench's turn and Sift's AI proposals are asked for only with the switch
  // on, so a card opened with it off asks nothing about the AI. An app's own parts, a Sift project's
  // with its PDFs whatever the switch says, are drawn first, so the AI proposals have their project, and
  // what follows the AI's, Sift's Zotero and its databases, after it, each by its own script
  Object.values(FAMILY_APPS).forEach((a) => { if (a.settingsReset) a.settingsReset(); });
  const own = FAMILY_APPS[APP];
  if (own && own.settingsLoad) own.settingsLoad();
  if (aiOn(c)) aiSetLoad();
  if (own && own.settingsLater) own.settingsLater();
  // and last an app's parts asked of its server, Idiograph's GETs
  Object.values(FAMILY_APPS).forEach((a) => { if (a.settingsLast) a.settingsLast(ctx); });
  show('settings');
}



/* A line beside a control in Settings, one that says something failed in the one warning tint, `.said-failed`,
   as every failure line is, where Settings' stood in the small print's grey (17 October, later). A server from
   before a change asks for a restart, which is no failure. */
function saidIn(id, text, failed = false) {
  $(id).textContent = text;
  $(id).classList.toggle('said-failed', !!(failed && text));
}
const saidErr = (id, err) => saidIn(id, needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));



/* ─────────────────────────────────────────────────── AI features ── */

/* In Settings the switch and its warning always show, first under General, and every other part about
   the AI, each marked data-ai-set, follows the box as it stands, saved or not: the provider, the
   model, the key, the prompt and the bench under it, the PETs model and limit, under Sift the AI
   proposals, and under Projects the agents' tick, their guide and Add Idiograph to Claude Desktop. */
function aiSetDraw() {
  const on = aiOn({ ai_suggest: $('set-ai').checked });
  document.querySelectorAll('#settings [data-ai-set]').forEach((el) => { el.hidden = !on; });
}

/* the parts under the switch that ask the server: the key's status, the models, the bench's turn and
   Sift's AI proposals */
function aiSetLoad() {
  keyStatus();
  loadModels();
  // the app's own AI parts, Idiograph's test bench's passage and Sift's AI proposals
  if (FAMILY_APPS[APP] && FAMILY_APPS[APP].aiLoad) FAMILY_APPS[APP].aiLoad();
}

/* Ticking the box asks first, in a small card over Settings with a fuller warning: I understand the
   risks, turn on ticks it and shows what sits under it, and Back to safety (keep off), the default and
   in focus, leaves it off (22 October). Unticking asks nothing. Either way it is saved with Save, as
   every setting is. */
function aiSwitch() {
  const box = $('set-ai');
  if (!box.checked) { aiSetDraw(); return; }
  box.checked = false;
  show('ai-confirm');
  $('ai-confirm-cancel').focus();
}

function aiConfirm(yes) {
  hide('ai-confirm');
  const box = $('set-ai');
  box.checked = yes;
  aiSetDraw();
  if (yes && !S.models) aiSetLoad();
  box.focus();
}

/* A server from before an update has none of the new endpoints. Each part of the AI section that
   finds one missing says so through the same quiet line, and the rest of the panel goes on
   working: a server with the key endpoints and no model list keeps the key and the prompt. */
const stale = { key: false, models: false };
const drawRestart = () => { $('ai-restart').hidden = !(stale.key || stale.models); };

/* The providers (aiprov's drawing, built by aipage, 8 November 2026): what each shows under the list. `key`
   whether it asks for one, `address` which address its Address row holds (`shared` is Azure's and Another
   service's, `ai_address`, `local` Ollama's, `local_url`, and `lmstudio` LM Studio's, `lmstudio_url`),
   `deployment` Azure's name in place of a Model list, `where` the line saying where its passages go, its key
   in the catalogue, or `host` and `local` for the lines drawWhere words itself. Every
   provider but Anthropic and Ollama has its Model row in #ai-other, from the OpenAI-style list the server sends. */
const PROVIDER_ROWS = {
  anthropic: { key: true, where: 'shell.ai.where_anthropic' },
  mistral: { key: true, where: 'shell.ai.where_mistral' },
  gemini: { key: true, where: 'shell.ai.where_gemini' },
  openai: { key: true, where: 'shell.ai.where_openai' },
  azure: { key: true, address: 'shared', deployment: true, where: 'shell.ai.where_azure' },
  other: { key: true, address: 'shared', where: 'host' },
  local: { address: 'local', where: 'local' },
  lmstudio: { address: 'lmstudio', where: 'local' },
};
// the usual addresses the two local ones are filled with, as the server's defaults
const LOCAL_AT = { local: 'http://127.0.0.1:11434', lmstudio: 'http://127.0.0.1:1234/v1' };
// the providers' own names, which no language changes, for the PETs list's labels
const PROVIDER_NAMES = { mistral: 'Mistral', gemini: 'Google Gemini', openai: 'OpenAI', azure: 'Azure OpenAI',
  lmstudio: 'LM Studio' };
const LOOPBACK = ['127.0.0.1', 'localhost', '[::1]', '::1'];

const providerNow = () => (PROVIDER_ROWS[$('set-provider').value] ? $('set-provider').value : 'anthropic');
const rowsOf = (provider) => PROVIDER_ROWS[provider] || PROVIDER_ROWS.anthropic;
const openaiShaped = (provider) => provider in PROVIDER_ROWS && provider !== 'anthropic' && provider !== 'local';
const hostOf = (address) => { try { return new URL(String(address || '').trim()).host; } catch (_) { return ''; } };
const hostLocal = (address) => { try { return LOOPBACK.includes(new URL(String(address).trim()).hostname); } catch (_) { return false; } };

/* What Settings holds for the AI while it is open, read from the settings when it opens and kept as he
   changes it, so moving between providers loses nothing he typed: each address, each provider's model and
   Azure's deployment. Saved with Save. */
function aiHeldOpen(c) {
  S.aiAt = {
    shared: String(c.ai_address || ''),
    local: String(c.local_url || '') || LOCAL_AT.local,
    lmstudio: String(c.lmstudio_url || '') || LOCAL_AT.lmstudio,
  };
  S.aiPick = { ...(c.ai_models && typeof c.ai_models === 'object' ? c.ai_models : {}) };
  if (c.other_model) S.aiPick.other = String(c.other_model);
  S.aiModel = String(c.model || '').replace(/-\d{8}$/, '');
  S.aiShown = null;
  $('set-deployment').value = String(c.ai_deployment || '');
}

// the address the chosen provider's calls go to, as the Address row holds it
const aiAddress = (provider) => {
  const slot = rowsOf(provider).address;
  return slot && S.aiAt ? S.aiAt[slot] || '' : '';
};

/* the provider whose key the key row is about: the chosen one, or Anthropic's while the row stands under
   PETs for an Anthropic model there (drawKeyPlace) */
const keyProvider = () => (rowsOf(providerNow()).key ? providerNow() : 'anthropic');
const keyAsk = () => ({ provider: keyProvider(), ai_address: S.aiAt ? S.aiAt.shared : '' });

/* The key itself never comes back from the server: the status says only whether one is stored and
   where it sits, each provider's from its own keychain item. A server that has not been restarted has no
   such endpoint, and the whole block stands down behind one line rather than half working. */
async function keyStatus() {
  try {
    const data = await api('/api/key-status', keyAsk());
    stale.key = false;
    $('ai-settings').hidden = false;
    saidIn('key-said', data.set
      ? t(data.source === 'file' ? 'shell.key.saved_file' : 'shell.key.saved')
      : t('shell.key.none'));
    $('btn-key-clear').hidden = !data.set || data.source === 'file';
  } catch (err) {
    if (!needsRestart(err)) { saidIn('key-said', err.message, true); return; }
    stale.key = true;
    $('ai-settings').hidden = true;
  }
  drawRestart();
}

/* The provider and its models. The Anthropic list comes live from the account when a key is
   stored, cut to the current models in their order, and from the built-in table when it cannot.
   The local list is what Ollama has pulled, or a line saying it is not there and what to do. Every other
   provider's is its own service's list, asked only while it is the chosen one. A reload of the lists
   after a key is saved keeps whatever is chosen in the panel. */
let modelsAsk = 0;

/* A model with a price is listed by its name alone, and the chosen one's price stands on its own line
   under the list, so neither is cut short in a narrow list (21 October) */
function fillModels(id, list, chosen) {
  const options = (list || []).slice();
  if (chosen && !options.some((m) => m.id === chosen)) {
    options.push({ id: chosen, name: chosen, hint: t('shell.models.stored', { model: chosen }) });
  }
  const select = $(id);
  select.innerHTML = options.map((m) => `<option value="${escAttr(m.id)}">${esc(m.price ? m.name : (m.hint || m.name))}</option>`).join('');
  if (chosen) select.value = chosen;
  select.disabled = !options.length;
  if (id === 'set-model') drawModelPrice();
}

function drawModelPrice() {
  const found = S.models && (S.models.anthropic.models || []).find((m) => m.id === $('set-model').value);
  $('model-price').textContent = (found && found.price) || '';
  $('model-price').hidden = !(found && found.price);
}

/* An OpenAI-style provider's Model row: its service's list by the models' own names, or where it lists none a
   name typed in the same row, and the line under it only when the list could not be had */
function drawOtherModels(listed) {
  const provider = providerNow();
  const models = (listed && listed.models) || [];
  const chosen = (S.aiPick && S.aiPick[provider]) || (S.models && S.models.model) || '';
  const named = models.map((m) => ({ id: m.id, name: m.id }));
  if (models.length) fillModels('set-other-model', named, chosen);
  $('set-other-model').hidden = !models.length;
  $('set-other-name').hidden = !!models.length;
  if (!models.length) $('set-other-name').value = chosen;
  saidIn('other-note', listed && listed.failed ? listed.note || '' : '', !!(listed && listed.failed));
  $('other-note').hidden = !(listed && listed.failed && listed.note);
}

// the model the chosen OpenAI-style provider is asked, as its row holds it
const otherModel = () => ($('set-other-name').hidden ? $('set-other-model').value : $('set-other-name').value.trim());

function pickOther() {
  if (S.aiPick && openaiShaped(providerNow())) S.aiPick[providerNow()] = otherModel();
  drawPetsNote();
}

/* the line saying where passages go: the provider's own fact, Another service's host, and for the two
   local ones this machine, or the host when the address names another */
function drawWhere() {
  const provider = providerNow();
  const rows = rowsOf(provider);
  const address = aiAddress(provider);
  let where = '';
  if (rows.where === 'host') where = hostOf(address) ? t('shell.ai.where_host', { host: hostOf(address) }) : '';
  else if (rows.where === 'local') {
    where = !address || hostLocal(address) ? t('shell.ai.where_local') : t('shell.ai.where_host', { host: hostOf(address) });
  } else where = t(rows.where);
  $('ai-where').textContent = where;
  $('ai-where').hidden = !where;
}

/* The chosen provider's rows, the rest hidden: Anthropic's model and price, Ollama's model, every other
   provider's model or Azure's deployment, the Address for those that ask for one, and the where line */
function drawProvider() {
  const provider = providerNow();
  const rows = rowsOf(provider);
  $('ai-anthropic').hidden = provider !== 'anthropic';
  $('ai-local').hidden = provider !== 'local';
  $('ai-other').hidden = !openaiShaped(provider);
  $('ai-address').hidden = !rows.address;
  if (rows.address) $('set-address').value = aiAddress(provider);
  $('deployment-row').hidden = !rows.deployment;
  $('other-model-row').hidden = !!rows.deployment;
  drawWhere();
  drawPetsNote();
}

/* Another provider chosen: its rows at once, then its key's status and its list, each asked afresh, since
   each provider has its own key and its own models */
function chooseProvider() {
  drawProvider();
  if (!S.models) return;
  if (!$('ai-key').hidden) keyStatus();
  loadModels();
}

/* The Address typed: the where line follows each key, and leaving the field asks again for the key's status
   (Another service's key is filed by its host) and the list at the new address */
function typeAddress() {
  const slot = rowsOf(providerNow()).address;
  if (slot && S.aiAt) S.aiAt[slot] = $('set-address').value.trim();
  drawWhere();
}

function leaveAddress() {
  typeAddress();
  if (!S.models) return;
  if (rowsOf(providerNow()).key) keyStatus();
  loadModels();
}

/* The key row sits under the statements' model while that provider takes a key. With a local one there
   and an Anthropic model for PETs, the same row, the same field and the same keychain item, stands in the
   PETs category instead, and with a local one for both it stands aside, since nothing about the key
   applies to a local model. */
function drawKeyPlace() {
  const keyless = !rowsOf(providerNow()).key;
  const pets = keyless && petsProvider() === 'anthropic';
  if (pets && $('pets-key-slot')) $('pets-key-slot').appendChild($('ai-key'));
  else keyHome();
  $('ai-key').hidden = keyless && !pets;
}

const keyHome = () => { if ($('ai-key').parentNode !== $('ai-settings')) $('ai-choice').before($('ai-key')); };

/* The PETs screen's own model, as the select holds it: `<provider>:<id>`, and empty for the Experiential
   statements one. The settings keep it as `pets_provider` and `pets_model`. */
function petsValue(c) {
  const provider = c && c.pets_provider;
  const model = String((c && c.pets_model) || '').trim();
  return PROVIDER_ROWS[provider] && model ? `${provider}:${model}` : '';
}

function petsChoice() {
  const value = $('set-pets-model') ? $('set-pets-model').value : '';
  const at = value.indexOf(':');
  return value && at > 0 ? { provider: value.slice(0, at), model: value.slice(at + 1) } : null;
}

const petsProvider = () => (petsChoice() || { provider: providerNow() }).provider;

// who an OpenAI-style provider is, by its name, or Another service by its address's host
const whoOf = (provider) => PROVIDER_NAMES[provider] || hostOf(S.aiAt && S.aiAt.shared) || provider;

/* a model by its plain name, as the lists the server sent name it */
function modelLabel(provider, id) {
  if (provider === 'local') return id ? t('shell.models.local', { model: id }) : t('shell.models.a_local');
  if (openaiShaped(provider)) return t('shell.models.from_who', { model: id, who: whoOf(provider) });
  const found = S.models && (S.models.anthropic.models || []).find((m) => m.id === id);
  return found ? found.name : id;
}

// the statements' model as the card holds it now, by its label
function statementsLabel() {
  const provider = providerNow();
  if (provider === 'local') return modelLabel('local', $('set-local-model').value);
  if (provider === 'azure') return modelLabel('azure', $('set-deployment').value.trim());
  if (openaiShaped(provider)) return modelLabel(provider, otherModel());
  return modelLabel('anthropic', $('set-model').value);
}

/* the line under the PETs model, following both selects as they stand in the card */
function drawPetsNote() {
  const own = petsChoice();
  if ($('pets-model-note')) {
    $('pets-model-note').textContent = own
      ? t('shell.models.uses', { model: modelLabel(own.provider, own.model) })
      : t('shell.models.uses_statements', { model: statementsLabel() });
  }
  drawKeyPlace();
}

/* Same as Experiential statements first, then every Anthropic model the statements' select offers,
   then the local models when Ollama answers, then the models of the OpenAI-style provider chosen for the
   statements, each labelled as those selects label it. A stored choice the lists no longer carry is kept
   and said to be. */
function fillPetsModels(data, chosen) {
  const listed = data.openai && data.openai.provider ? data.openai : null;
  const options = [{ value: '', label: t('shell.models.same_as_statements') }]
    .concat((data.anthropic.models || []).map((m) => ({ value: `anthropic:${m.id}`, label: m.hint || m.name })))
    .concat(data.local.running ? (data.local.models || []).map((m) => ({ value: `local:${m.id}`, label: m.hint || m.name })) : [])
    .concat(listed ? (listed.models || []).map((m) => ({ value: `${listed.provider}:${m.id}`, label: modelLabel(listed.provider, m.id) })) : []);
  if (chosen && !options.some((o) => o.value === chosen)) {
    options.push({ value: chosen, label: t('shell.models.stored', { model: chosen.slice(chosen.indexOf(':') + 1) }) });
  }
  const select = $('set-pets-model');
  if (!select) return;
  select.innerHTML = options.map((o) => `<option value="${escAttr(o.value)}">${esc(o.label)}</option>`).join('');
  select.value = chosen || '';
}

/* The lists, for the provider the card holds: the server is told which, with the addresses as typed and the
   switch as the card holds it, so a provider can be tried before Save. Never asked with the switch off
   (aiSetLoad and aiConfirm). */
async function loadModels(fresh = false) {
  const ask = ++modelsAsk;
  const keep = S.models
    ? { provider: providerNow(), model: $('set-model').value, local: $('set-local-model').value,
      pets: $('set-pets-model') ? $('set-pets-model').value : '' }
    : null;
  saidIn('model-note', t('shell.models.checking'));
  const at = S.aiAt || {};
  const body = { provider: keep ? keep.provider : undefined, ai_address: at.shared || '', local_url: at.local || '',
    lmstudio_url: at.lmstudio || '', ai_suggest: $('set-ai').checked, fresh: !!fresh };
  try {
    const data = await api('/api/models', body);
    if (ask !== modelsAsk) return;
    if (!data.anthropic || !data.local || !data.provider) throw olderServer();
    S.models = data;
    stale.models = false;
    $('ai-choice').hidden = false;
    $('ai-provider-row').hidden = false;
    for (const id of ['pets-choice', 'bench']) if ($(id)) $(id).hidden = false;
    // Anthropic's model as the card or else the settings hold it, never another provider's
    const anthropicModel = data.openai ? S.aiModel : data.model;
    fillModels('set-model', data.anthropic.models, (keep && keep.model) || anthropicModel);
    fillModels('set-local-model', data.local.models, (keep && keep.local) || data.local_model);
    fillPetsModels(data, keep ? keep.pets : S.petsOpened);
    const provider = keep ? keep.provider : data.provider;
    $('set-provider').value = PROVIDER_ROWS[provider] ? provider : 'anthropic';
    saidIn('model-note', data.anthropic.note || '', !!data.anthropic.failed);
    $('local-note').innerHTML = withCode(data.local.note || '');
    $('local-note').hidden = !data.local.note;
    $('local-model-row').hidden = !(data.local.running && data.local.models.length);
    drawProvider();
    if (data.openai) drawOtherModels(data.openai);
    drawPetsNote();
  } catch (err) {
    if (ask !== modelsAsk) return;
    S.models = null;
    if (needsRestart(err)) {
      stale.models = true;
      $('ai-choice').hidden = true;
      $('ai-provider-row').hidden = true;
      for (const id of ['pets-choice', 'bench']) if ($(id)) $(id).hidden = true;
      keyHome();
      $('ai-key').hidden = false;
      saidIn('model-note', '');
    } else { saidIn('model-note', err.message, true); }
  }
  drawRestart();
}

/* Check key (Adam, 21 October): the server asks the provider which models the key can call, the key in
   the field or else the one stored, each provider's under its own keychain item. The field is emptied as
   soon as the value is on its way, so the key is not left sitting in the page. An accepted key is stored,
   "This key works.", and the Model list takes the models it can call. A refused one is not stored, and the
   line says who refused it and why, in the warning tint, and the list stays as it was. Nothing about the
   key comes back. */
async function checkKey() {
  const field = $('set-key');
  const value = field.value;
  field.value = '';
  saidIn('key-said', t('shell.key.checking'));
  try {
    const data = await api('/api/check-key', { ...keyAsk(), ...(value.trim() ? { key: value } : {}) });
    if (!data.ok) { saidIn('key-said', data.said || '', true); $('btn-key-clear').hidden = true; return; }
    saidIn('key-said', data.said || '');
    $('btn-key-clear').hidden = data.source === 'file';
    if (S.models && data.anthropic) {
      S.models.anthropic = data.anthropic;
      fillModels('set-model', data.anthropic.models, $('set-model').value);
      fillPetsModels(S.models, $('set-pets-model') ? $('set-pets-model').value : '');
      saidIn('model-note', data.anthropic.note || '', !!data.anthropic.failed);
      drawPetsNote();
    } else if (S.models && data.openai && data.openai.provider === providerNow()) {
      S.models.openai = data.openai;
      drawOtherModels(data.openai);
      fillPetsModels(S.models, $('set-pets-model') ? $('set-pets-model').value : '');
      drawPetsNote();
    } else loadModels(true);
  } catch (err) {
    saidErr('key-said', err);
  }
}

// Remove: the chosen provider's key alone, from its own keychain item
async function clearKey() {
  try {
    const data = await api('/api/key', { ...keyAsk(), clear: true });
    saidIn('key-said', t(data.cleared ? 'shell.key.removed' : 'shell.key.nothing_to_remove'));
    keyStatus();
    if (S.models) loadModels(true);
  } catch (err) {
    saidErr('key-said', err);
  }
}

/* A choice tried before it is saved, the test bench's: the provider, its model and its address as the card
   holds them, which the server's ai_route takes from a body before the settings */
function aiTryBody(body) {
  const provider = providerNow();
  body.provider = provider;
  if (provider === 'anthropic' && $('set-model').value) body.model = $('set-model').value;
  if (provider === 'local' && $('set-local-model').value) body.local_model = $('set-local-model').value;
  if (openaiShaped(provider) && provider !== 'azure' && otherModel()) body.model = otherModel();
  if (provider === 'azure') body.ai_deployment = $('set-deployment').value.trim();
  if (S.aiAt && provider === 'lmstudio') body.lmstudio_url = S.aiAt.lmstudio;
  else if (S.aiAt && rowsOf(provider).address === 'shared') body.ai_address = S.aiAt.shared;
  return body;
}

/* What Save sends of the AI's settings, only to a server that sent the lists: the provider, each model,
   the addresses (Azure's and Another service's, Ollama's and LM Studio's, an emptied local one its usual
   one again), Azure's deployment, and the PETs model, or two empty keys for the Experiential statements
   one. A server from before a key leaves it out of the file, and nothing else changes. */
function aiSaveBody(body) {
  body.ai_provider = providerNow();
  if ($('set-model').value) body.model = $('set-model').value;
  if ($('set-local-model').value) body.local_model = $('set-local-model').value;
  if (S.aiAt) {
    body.ai_address = S.aiAt.shared || '';
    body.local_url = S.aiAt.local || LOCAL_AT.local;
    body.lmstudio_url = S.aiAt.lmstudio || LOCAL_AT.lmstudio;
  }
  body.ai_deployment = $('set-deployment').value.trim();
  if (openaiShaped(providerNow()) && !$('ai-other').hidden && providerNow() !== 'azure') pickOther();
  const picks = { ...(S.aiPick || {}) };
  if ('other' in picks) body.other_model = picks.other || '';
  delete picks.other;
  body.ai_models = picks;
  const own = petsChoice();
  body.pets_provider = own ? own.provider : '';
  body.pets_model = own ? own.model : '';
}

/* The provider and the model go only to a server that sent the lists. One from before them would
   drop the fields anyway, and the saved model is left as it was. */
async function saveSettings() {
  const body = {
    ai_suggest: $('set-ai').checked,
    ...cheerBody(),
    sound: $('set-sound').checked,
    quit_when_closed: $('set-quit-closed').checked,
    appearance: storedTheme(),
  };
  // this app's AI features turned off, each unticked under AI features
  body[AI_OFF_KEY] = [...document.querySelectorAll('[data-ai-feature]')]
    .filter((box) => AI_FEATURES[APP].includes(box.dataset.aiFeature) && !box.checked).map((box) => box.dataset.aiFeature);
  // an app's own keys, Idiograph's statements, rounds, nudges, prompt, view and PETs limit, Sift's databases
  // and its Zotero library, each from its own script
  Object.values(FAMILY_APPS).forEach((a) => { if (a.settingsBody) a.settingsBody(body); });
  if (S.models) aiSaveBody(body);
  // each app's own, from its own script: Idiograph's GETs and its projects, each to its own file, Sift's AI
  // proposals, each screening's to its own sift.json, after the switch is saved, and each Sift project's name
  // and question, to the app's own list and never its folder (12 October), and a Trace project's name the same
  // way (15 October)
  const appSends = Object.values(FAMILY_APPS).filter((a) => a.settingsSends).map((a) => [a, a.settingsSends()]);
  const overHome = !$('library').hidden;
  // an app's refusal before anything is sent, Idiograph's while a participant out of its GETs has no reason
  if (appSends.some(([a, sends]) => a.settingsRefuse && a.settingsRefuse(sends))) return;
  try {
    const data = await api('/api/settings', body);
    // the window's two update ticks, each only once it has moved
    await updSave();
    for (const [own, sends] of appSends) await own.settingsSend(sends);
    hide('settings');
    if (data.config) S.libConfig = data.config;
    if (data.config) aiPage(data.config);
    // over an app's own screen the settings as they now stand, each by its own script: Idiograph's PETs screen's
    // bar the switch and the model and its band the question, Sift's searches their databases and its screening
    // its own AI settings, or a read afresh, and Trace's the AI switch (15 October)
    for (const a of Object.values(FAMILY_APPS)) if (a.settingsSaved) await a.settingsSaved(data);
    // over the home screen the cards and a project's page take the name and the question at once
    if (overHome) { loadLibrary().catch((err) => say(err.message, 9000)); return; }
    // the screen behind as the settings now stand, Idiograph's case
    for (const a of Object.values(FAMILY_APPS)) if (a.settingsAfter) await a.settingsAfter(data);
  } catch (err) { say(err.message, 9000); }
}

/* ── Using your own AI agent ── */

/* The box at the end of AI features (21 October 2026): the words to paste into an agent, this install's
   command line, MCP server and guide, as the server knows them, asked each time Settings opens. A server
   from before the route leaves the section hidden. Copy says Copied for a moment, as the MCP card's does. */
async function drawAgentStart() {
  try {
    const data = await api('/api/agent-start');
    $('agent-text').textContent = data.text || '';
    $('agent-start').hidden = !data.text;
  } catch { $('agent-start').hidden = true; }
}

async function agentCopy(button) {
  $('agent-said').hidden = true;
  try {
    await navigator.clipboard.writeText($('agent-text').textContent);
    button.textContent = t('shell.agent.copied');
    setTimeout(() => { button.textContent = t('shell.agent.copy'); }, 1600);
  } catch {
    saidIn('agent-said', t('shell.agent.clipboard_refused'), true);
    $('agent-said').hidden = false;
  }
}

/* ── Restart and Quit ── */

/* Restart Idiograph and Quit Idiograph, at the foot of Settings, and a Restart after the restart
   line wherever it shows, since a new page in front of an old server is when he needs one. The
   page asks /api/server at boot. A server from before the route has no such endpoint: the restart
   line then stays as it was, with no button, and the foot shows it in place of the two. Both save
   what is pending first. Restart shows Restarting and reloads the page once the server answers
   from its new start, which then comes back to the screen it was on (see `spotKeep`). Quit says
   Idiograph is closed and how to open it again. A way of running that cannot restart itself says
   so in one line, and nothing else happens. */
const SERVER = { info: null, old: false, busy: false, watch: null };
const RESTART_NOW = 'restart-now';

async function serverBoot() {
  try {
    SERVER.info = await api('/api/server');
  } catch (err) { SERVER.old = needsRestart(err); }
  drawServerOps();
  if (SERVER.info) restartButtons();
}

function drawServerOps() {
  $('server-restart').hidden = !SERVER.info;
  $('server-quit').hidden = !SERVER.info;
  $('server-old').hidden = !SERVER.old;
  // in Idiograph's own window the app quits as its last window closes, so General's Closing and its
  // one tick, which speak of tabs, are not there (17 October)
  const own = !!(SERVER.info && SERVER.info.window);
  $('close-sub').hidden = own;
  $('set-quit-closed').closest('.switches').hidden = own;
  // and the button in the system's word, which the server gives: Exit Idiograph in the window on
  // Windows, whose File menu says Exit, and Quit Idiograph everywhere else (17 October, the third
  // Tauri build)
  $('server-quit').textContent = (SERVER.info && SERVER.info.quit) || t('shell.server.quit', { app: APP_NAME });
}

/* what is typed and not saved, each app's by its own script, Idiograph's turn's fields, interviewer note and
   canvas, as any move saves them. The answer is whether all of it is kept. */
async function savePending() {
  for (const own of Object.values(FAMILY_APPS)) if (own.savePending && !(await own.savePending())) return false;
  return true;
}

async function serverOp(op) {
  if (SERVER.busy) return;
  const cannot = op === 'restart' && SERVER.info && SERVER.info.restart;
  if (cannot) { say(cannot, 9000); return; }
  SERVER.busy = true;
  try {
    if (!(await savePending())) {
      say(t(op === 'restart' ? 'shell.server.not_saved_restart' : 'shell.server.not_saved_quit', { app: APP_NAME }), 9000);
      return;
    }
    if (op === 'restart') spotKeep();
    const data = await api('/api/server', { op });
    if (op === 'quit') { serverGone(t('shell.server.closed', { app: APP_NAME }), data.reopen || ''); beatQuiet(); return; }
    serverGone(t('shell.server.restarting'), '');
    await serverBack(data.started, data.reopen || '');
  } catch (err) {
    spotDrop();
    say(err.message, 9000);
  } finally { SERVER.busy = false; }
}

/* Where the page is when Restart is pressed, or as the page goes on a reload, kept in this tab alone
   for the start that follows, so it comes back there: the turn screen on its case and turn, PETs on
   its case and board, with the way back to Experiential statements when it was opened from there,
   GETs on its board, Sift on its screening or a Sift project's searches, or a Trace project. The home screen keeps
   its own place, the picker or a project's page, in `S.home`. It is read once, at the page's next
   start, and only within ten minutes. A case or a board gone by then is the home screen. */
const RETURN_KEY = 'idiograph-return';
const RETURN_FOR = 10 * 60 * 1000;

function spotNow() {
  // the screen in front, each app's by its own script: Idiograph's statements on their case and turn, PETs or GETs
  // on its board and the Trajectories board, Sift on its screening, kept as the folder alone, since the record it
  // was on is kept in the browser, or a review on its searches by the review's folder, and a Trace project by its
  // folder, the manuscript open kept in this browser (15 October)
  for (const own of Object.values(FAMILY_APPS)) { const at = own.spot && own.spot(); if (at) return at; }
  return null;
}

function spotKeep() {
  const spot = spotNow();
  try {
    if (spot) sessionStorage.setItem(RETURN_KEY, JSON.stringify(Object.assign({ at: Date.now() }, spot)));
    else sessionStorage.removeItem(RETURN_KEY);
  } catch { /* private window */ }
}

function spotDrop() {
  try { sessionStorage.removeItem(RETURN_KEY); } catch { /* private window */ }
}

/* the place kept, taken once, or null for none, one of another shape, or one older than ten minutes */
function spotTaken() {
  let spot = null;
  try {
    spot = JSON.parse(sessionStorage.getItem(RETURN_KEY) || 'null');
  } catch { spot = null; }
  spotDrop();
  if (!spot || typeof spot !== 'object' || typeof spot.path !== 'string' || !spot.path) return null;
  if (!['work', 'pets', 'gets', 'trajectories', 'trace', 'searches', 'sift'].includes(spot.screen)) return null;
  return Date.now() - Number(spot.at || 0) < RETURN_FOR ? spot : null;
}

/* Open in a new window (20 October, Adam's way C, for two screens): a participant's statements, from the
   participant switcher, or a board, from its menu, in a window of its own, the Mac app's window or the
   browser's, as File, New Window opens one on the home screen. The place goes in the new window's address
   after its #, so it never reaches the server, and the window opens there as a restart comes back. */
const OPEN_HASH = '#open=';

function openInWindow(spot) {
  if (!spot || !spot.path) return;
  const hash = `${OPEN_HASH}${encodeURIComponent(JSON.stringify(spot))}`;
  // in the Mac and Windows app a window.open shares its opener's handler, so closing it could close the
  // window that opened it: there the app's window file gives a hook that opens it through the app's own
  // window command, as File, New Window does, and window.open stays the browser's way
  if (typeof window.__idiographOpenWindow === 'function') {
    window.__idiographOpenWindow(spot, hash);
    return;
  }
  const url = `${location.origin}/${hash}`;
  const w = Math.min(1280, (typeof screen !== 'undefined' && screen.availWidth) || 1280);
  const h = Math.min(800, (typeof screen !== 'undefined' && screen.availHeight) || 800);
  const made = window.open(url, '_blank', `popup,width=${w},height=${h}`);
  if (!made) say(t('shell.window_blocked'), 8000);
}

/* the place a new window was opened on, read once from its address and taken off it, and kept as a restart
   keeps its place, so the page's start comes back to it the same way */
function spotFromAddress() {
  const spot = spotOpened();
  if (!spot) return;
  try { sessionStorage.setItem(RETURN_KEY, JSON.stringify(Object.assign({}, spot, { at: Date.now() }))); } catch { /* private window */ }
}

/* the place a new window was opened on, read once from its address and taken off it, or null */
function spotOpened() {
  const hash = String(location.hash || '');
  if (!hash.startsWith(OPEN_HASH)) return null;
  let spot = null;
  try { spot = JSON.parse(decodeURIComponent(hash.slice(OPEN_HASH.length))); } catch { spot = null; }
  try { history.replaceState(history.state, '', location.pathname + location.search); } catch { /* no history */ }
  if (!spot || typeof spot !== 'object' || typeof spot.path !== 'string' || !spot.path) return null;
  if (!['work', 'pets', 'gets'].includes(spot.screen)) return null;
  return spot;
}
window.openInWindow = openInWindow;

/* The screen kept, opened as he opened it: the case on its turn, then over it PETs when they were
   opened from there, or PETs or GETs on their board with the way back to the case list. A case that
   will not open, or a board the file no longer holds, is the home screen instead. */
async function comeBack(spot) {
  const home = () => {
    loadLibrary().catch((err) => say(err.message, 9000));
  };
  const own = familyApp(spot.screen);
  // Idiograph's screens by its own `comeBack`, Sift's and Trace's by their `open`
  if (own && own.comeBack) { await own.comeBack(spot, home); return; }
  if (own) { own.open(spot.path, home, spot.screen); return; }
  home();
}

/* The page over everything, its keys going nowhere behind it. */
function serverGone(head, line) {
  $('server-gone-head').textContent = head;
  $('server-gone-line').textContent = line;
  if ($('server-gone').hidden) window.addEventListener('keydown', (e) => { e.preventDefault(); e.stopImmediatePropagation(); }, true);
  $('server-gone').hidden = false;
}

/* The beat's word that the server has not answered for forty seconds (see `static/beat.js`), as when
   it quit by itself while this tab slept: Idiograph is closed and how to open it again, as after
   Quit, and the beat goes quiet. While a Restart from this page is under way the beat goes on. */
window.idiographClosed = () => {
  if (SERVER.busy) return false;
  if ($('server-gone').hidden) serverGone(t('shell.server.closed', { app: APP_NAME }), (SERVER.info && SERVER.info.reopen) || '');
  return true;
};

/* and once Quit has closed it, or a restart has not come back, the beat goes quiet, so this tab never
   holds the next start open */
function beatQuiet() {
  if (typeof window.idiographQuiet === 'function') window.idiographQuiet();
}

/* Asked every 400ms until the server answers from a new start, then the page reloads. One that is
   not back in forty seconds is said to be closed, with how to open it again. */
async function serverBack(started, reopen) {
  const until = Date.now() + 40 * 1000;
  while (Date.now() < until) {
    await new Promise((done) => setTimeout(done, 400));
    try {
      const res = await fetch('/api/server', { cache: 'no-store' });
      const data = res.ok ? await res.json() : null;
      if (data && data.started && data.started !== started) { location.reload(); return; }
    } catch { /* not listening yet */ }
  }
  serverGone(t('shell.server.not_back', { app: APP_NAME }), reopen);
  beatQuiet();
}

/* ──────────────────────────────── Idiograph's own updates, and What's new ── */

/* Idiograph's own updates, in its window alone (18 October, the fourth Tauri build): the window checks,
   downloads and installs them through Tauri's updater, and holds what he chose, and the page asks it
   through `idiographUpdate`, the window's own script's, and hears each change as `idiograph-update`. A
   browser's tab, a copy run from source among them, has no such bridge, so nothing of it shows. The
   line at the head of the home screen, in its flow so it covers no control: at the first start the
   question whether to check, asked once with two plain buttons, then a newer version offered when it
   does not download by itself, its download, and once it is ready Relaunch now and Later, which hides
   the line until the next start and lets the update install as Idiograph quits. Settings, General
   holds the version with What's new, the two ticks, written on Save each only once it has moved, and
   Check now with the last check's time and what it found. Every word of it Adam's (18 October, the
   fifth and sixth Tauri builds): Relaunch, the normal word, as the fourth build had it, where the fifth
   said Restart, which stays the word of Settings' Restart Idiograph, a different act. */
const UPD = { view: null, opened: null, relaunching: false };
const UPD_PRIVACY = t('shell.updates.privacy', { app: APP_NAME });

const updBridge = () => (typeof window.idiographUpdate === 'function' ? window.idiographUpdate : null);

/* one ask of the window, `read` by default, and what it answers taken */
async function updAsk(op = 'read', more = {}) {
  const bridge = updBridge();
  if (!bridge) return null;
  const view = await bridge(op, more);
  if (view) updTake(view);
  return view;
}

/* how the updates stand, from an answer or the window's own word, drawn */
function updTake(view) {
  UPD.view = view && view.here ? view : null;
  // Settings opened before the first answer came takes the ticks from it now
  if (UPD.view && !UPD.opened && !$('settings').hidden) updTicks();
  if (UPD.relaunching && UPD.view && UPD.view.state === 'failed') {
    UPD.relaunching = false;
    say(UPD.view.reason || t('shell.updates.not_relaunched', { app: APP_NAME }), 9000);
  }
  updDraw();
  wnFoot();
}

/* what the home screen's line says, its two buttons and what each does, or null for no line */
function updLine(v) {
  if (!v) return null;
  if (v.check !== true && v.check !== false) {
    return { said: t('shell.updates.ask'), more: UPD_PRIVACY, yes: t('shell.updates.check'), no: t('shell.updates.dont_check'),
      onYes: () => updAsk('choose', { check: true }), onNo: () => updAsk('choose', { check: false }) };
  }
  if (v.later) return null;
  const later = () => updAsk('later');
  if (v.state === 'ready') {
    return { said: t('shell.updates.ready', { app: APP_NAME, version: v.version }), yes: t('shell.updates.relaunch_now'),
      no: t('shell.updates.later'),
      onYes: () => updRelaunch(), onNo: later };
  }
  if (v.state === 'available' && !v.download) {
    return { said: t('shell.updates.available', { app: APP_NAME, version: v.version }), yes: t('shell.updates.download'),
      no: t('shell.updates.later'),
      onYes: () => updAsk('download'), onNo: later };
  }
  if (v.state === 'downloading' && !v.download) return { said: updDownloading(v) };
  return null;
}

function updDownloading(v) {
  const part = v.size ? Math.min(99, Math.floor((100 * (v.got || 0)) / v.size)) : 0;
  return t('shell.updates.downloading', { app: APP_NAME, version: v.version, percent: part });
}

/* the last check's time, today's by the hour alone */
function updWhen(iso) {
  const at = new Date(iso);
  if (Number.isNaN(at.getTime())) return '';
  const time = tTime(at);
  if (at.toDateString() === new Date().toDateString()) return t('shell.updates.today_at', { time });
  return t('shell.updates.day_at', { day: tDate(at, { day: 'numeric', month: 'long' }), time });
}

function updDraw() {
  const v = UPD.view;
  const line = updLine(v);
  $('update-line').hidden = !line;
  if (line) {
    $('update-said').textContent = line.said;
    $('update-more').textContent = line.more || '';
    $('update-more').hidden = !line.more;
    $('update-acts').hidden = !line.yes;
    $('update-yes').textContent = line.yes || '';
    $('update-no').textContent = line.no || '';
    $('update-yes').onclick = line.onYes || null;
    $('update-no').onclick = line.onNo || null;
  }
  // Settings, General: the rows only in the window, the ticks set as the card opens (updTicks)
  $('update-set').hidden = !v;
  if (!v) return;
  $('update-running').textContent = t('shell.app_version', { app: APP_NAME, version: v.running });
  $('update-checked').textContent = v.checked ? t('shell.updates.last_checked', { when: updWhen(v.checked) }) : '';
  const said = {
    checking: t('shell.updates.checking'),
    none: v.checked ? t('shell.updates.newest', { app: APP_NAME, version: v.running }) : '',
    available: t('shell.updates.available', { app: APP_NAME, version: v.version }),
    downloading: updDownloading(v),
    ready: t('shell.updates.ready', { app: APP_NAME, version: v.version }),
  }[v.state] || '';
  $('update-state').textContent = said;
  $('update-state').hidden = !said;
  $('update-failed').textContent = v.state === 'failed' ? v.reason || '' : '';
  $('update-failed').hidden = v.state !== 'failed' || !v.reason;
  $('update-check-now').disabled = v.state === 'checking' || v.state === 'downloading';
  $('update-get').hidden = v.state !== 'available';
  $('update-relaunch').hidden = v.state !== 'ready';
}

/* Settings opening: the two ticks as the window holds them, Check for updates unticked until the home
   screen's question is answered, and what they were, so Save sends one only once it has moved */
function updOpen() {
  updTicks();
  updAsk();
}

function updTicks() {
  const v = UPD.view;
  UPD.opened = v ? { check: v.check === true, download: v.download === true } : null;
  if (!v) return;
  $('set-update-check').checked = UPD.opened.check;
  $('set-update-download').checked = UPD.opened.download;
  // downloading by itself waits on checking, as Sound waits on Celebrations
  $('set-update-download').disabled = !UPD.opened.check;
}

/* after Settings' Save: the two ticks, each only once it has moved since the card opened */
async function updSave() {
  if (!UPD.view || !UPD.opened) return;
  const check = $('set-update-check').checked;
  const download = $('set-update-download').checked;
  const more = {};
  if (check !== UPD.opened.check) more.check = check;
  if (download !== UPD.opened.download) more.download = download;
  if (!Object.keys(more).length) return;
  UPD.opened = { check, download };
  await updAsk('set', more);
}

/* Relaunch now: what is typed saved first, as Restart saves it, the place kept and handed to the
   window, which installs the update and starts the new version there */
async function updRelaunch() {
  if (SERVER.busy || UPD.relaunching) return;
  SERVER.busy = true;
  try {
    if (!(await savePending())) {
      say(t('shell.updates.not_saved', { app: APP_NAME }), 9000);
      return;
    }
    spotKeep();
    const place = {};
    try {
      for (const key of [RETURN_KEY, HOME_KEY]) if (sessionStorage.getItem(key) !== null) place[key] = sessionStorage.getItem(key);
    } catch { /* no place to keep */ }
    UPD.relaunching = true;
    say(t('shell.updates.relaunching', { app: APP_NAME }), 20000);
    await updAsk('relaunch', { place });
  } finally { SERVER.busy = false; }
}

/* What's new, as the design note's choice (b) has it (17 October): once after an update, a line at the
   foot, "Updated to Idiograph 0.9.2." with What's new, which opens the sheet of notes, docs/whats-new.md as
   the app carries it (/api/whats-new). The line shows once and goes with Close or What's new, and the sheet
   is reached again from Settings, General and the Help menu. In the window alone, as the version's number
   comes from it. Since wnspan (29 October 2026, Sparkle's way on a Mac) the line's sheet holds every version
   since the one that ran before, the window's `before`, kept here as the line shows, since the window lets it
   go once told the line was seen. `earlier` holds what Earlier versions adds. */
const WN = { shown: false, before: '', earlier: [] };

function wnFoot() {
  const v = UPD.view;
  if (!v || !v.updated || WN.shown) return;
  WN.shown = true;
  WN.before = v.before || '';
  // the name and the number kept together, never broken over two lines at 360 (Adam, 18 October)
  $('whatsnew-said').textContent = t('shell.whatsnew.updated', { app: APP_NAME, version: v.updated });
  $('whatsnew-line').hidden = false;
  document.body.classList.add('foot-on');
  wnFootRoom();
  window.addEventListener('resize', wnFootRoom);
  // shown once, so the window is told at once
  updAsk('seen');
}

/* The line's height, kept on the page as --foot-h while it shows, so the home screen's last line scrolls
   clear above it and a toast stands over it (18 October, where at 360 Add transcripts stayed partly under
   it even scrolled to the end, and the toast's place took it as one row). Measured again as the window
   changes its width, since the line wraps on a phone. */
function wnFootRoom() {
  const line = $('whatsnew-line');
  if (line.hidden) return;
  document.body.style.setProperty('--foot-h', `${Math.ceil(line.offsetHeight)}px`);
}

function wnFootClose() {
  $('whatsnew-line').hidden = true;
  document.body.classList.remove('foot-on');
  window.removeEventListener('resize', wnFootRoom);
}

/* a version's three numbers, so 0.9.10 comes after 0.9.9 as text would not have it, read as update.rs's
   `numbers` reads them */
function wnNumbers(version) {
  return String(version || '').trim().split(/[.+-]/).slice(0, 3).map((n) => parseInt(n, 10) || 0);
}

/* below 0 when version a is older than b, above 0 when it is newer, 0 when they are the same */
function wnCompare(a, b) {
  const x = wnNumbers(a);
  const y = wnNumbers(b);
  for (let i = 0; i < 3; i += 1) if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) - (y[i] || 0);
  return 0;
}

/* Which of the file's versions the sheet shows (wnspan, 29 October 2026). After an update, with `before` the
   version that ran before it, every version newer than that up to `running`, newest first, so 0.9.10 to 0.9.13
   is 0.9.13 then 0.9.12 where the file has no 0.9.11. Otherwise the running version alone, or the file's
   newest where none is known. `earlier` is every version older than those, newest first, for Earlier versions,
   and `top` the version the sheet starts at. */
function wnSpan(versions, running, before) {
  const all = [...(versions || [])].sort((a, b) => wnCompare(b.version, a.version));
  const top = running || (all[0] ? all[0].version : '');
  const from = before && wnCompare(top, before) > 0 ? before : '';
  const shown = all.filter((x) => wnCompare(x.version, top) <= 0
    && (from ? wnCompare(x.version, from) > 0 : wnCompare(x.version, top) === 0));
  const earlier = all.filter((x) => wnCompare(x.version, from || top) <= 0 && !shown.includes(x));
  return { top, shown, earlier };
}

/* The update found and not yet installed, as the window has it from the update's own manifest: its version, its
   day and its notes, a line each, or null when there is none. Settings' What's new shows it first while it
   waits, as the running copy's file cannot hold its notes yet */
function wnIncoming() {
  const v = UPD.view;
  if (!v || !['available', 'downloading', 'ready'].includes(v.state) || !v.version || wnCompare(v.version, v.running) <= 0) return null;
  const lines = String(v.notes || '').split('\n').map((line) => line.trim()).filter(Boolean);
  if (!lines.length) return null;
  const date = v.date ? tDate(v.date, { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }) : '';
  return { version: v.version, date, lines };
}

/* one version's heading, its date and its lines, into the parts given */
function wnFill(head, date, notes, v) {
  head.textContent = t('shell.app_version', { app: APP_NAME, version: v.version });
  date.textContent = v.date || '';
  date.hidden = !v.date;
  notes.textContent = '';
  for (const line of v.lines) {
    const p = document.createElement('p');
    // a part's name before its colon in the part's own weight, Sift, Distil or Trace
    const part = /^(Sift|Distil|Trace):\s/.exec(line);
    if (part) {
      const b = document.createElement('strong');
      b.textContent = part[1];
      p.append(b, line.slice(part[1].length));
    } else p.textContent = line;
    notes.appendChild(p);
  }
}

/* a version after the sheet's first, in a section of its own in the first's look */
function wnSection(v) {
  const section = document.createElement('section');
  section.className = 'whatsnew-version';
  const head = document.createElement('h2');
  head.tabIndex = -1;
  const date = document.createElement('p');
  date.className = 'fineprint whatsnew-date';
  const notes = document.createElement('div');
  notes.className = 'whatsnew-notes';
  section.append(head, date, notes);
  wnFill(head, date, notes, v);
  return section;
}

/* The sheet. From the foot line after an update, `since` the version that ran before, every version after it up
   to the one running, newest first, in one scrolling sheet. From Settings, General and the Help menu the running
   version, and from Settings' What's new while an update waits (`incoming`) the update's own notes before it.
   Under the last, Earlier versions while the file holds older ones. */
async function openWhatsNew(from = {}) {
  const running = (UPD.view && UPD.view.running) || '';
  wnFootClose();
  let versions = [];
  try {
    versions = (await api('/api/whats-new')).versions || [];
  } catch { versions = []; }
  const span = wnSpan(versions, running, (from && from.since) || '');
  const shown = span.shown.length ? [...span.shown]
    : [{ version: span.top, date: '', lines: [t('shell.whatsnew.no_notes', { app: APP_NAME, version: span.top })] }];
  const coming = from && from.incoming ? wnIncoming() : null;
  if (coming) shown.unshift(coming);
  wnFill($('whatsnew-title'), $('whatsnew-date'), $('whatsnew-notes'), shown[0]);
  const rest = $('whatsnew-rest');
  rest.textContent = '';
  for (const v of shown.slice(1)) rest.appendChild(wnSection(v));
  WN.earlier = span.earlier;
  $('whatsnew-earlier').hidden = !WN.earlier.length;
  $('whatsnew-body').scrollTop = 0;
  show('whatsnew');
  doneAtFoot('whatsnew');
}

/* A card of words with Done at its foot opens at its top, Done taking Enter all the same: focused plainly, a
   card taller than the window opened scrolled to its foot, its heading and close out of sight above (zoomsweep,
   30 October: What's new at Text size Large in a short window, Support at Large in any) */
function doneAtFoot(id) {
  $(`${id}-done`).focus({ preventScroll: true });
  const card = $(id).querySelector('.card');
  if (card) card.scrollTop = 0;
}
window.openWhatsNew = openWhatsNew;

/* Earlier versions: the rest of the file's versions added below the last shown, newest first, and the button
   goes. The sheet stays where it is, the first of them where the button was, and takes the focus */
function wnEarlier() {
  const rest = $('whatsnew-rest');
  const added = WN.earlier.map((v) => rest.appendChild(wnSection(v)));
  WN.earlier = [];
  $('whatsnew-earlier').hidden = true;
  if (added.length) added[0].querySelector('h2').focus({ preventScroll: true });
}

/* About Idiograph (20 October): the name, the version, the author, the licence and the acknowledgements,
   from the Mac's Idiograph menu, Windows's Help menu and the foot of Settings. The version is the
   window's where there is one, else the server's, as the home screen had it. Over Settings it stands
   over the card, which is still there after Done or Esc. A copy built on Adam's Mac each day names the commit
   it was built from after the version (macdaily, 9 November 2026), so it is told apart from the week's release */
function openAbout() {
  const v = runningVersion();
  const build = (S.lib && S.lib.build) || '';
  $('about-version').textContent = !v ? '' : build ? t('shell.about.version_build', { version: v, build })
    : t('shell.about.version', { version: v });
  $('about-version').hidden = !v;
  show('about');
  doneAtFoot('about');
}
window.openAbout = openAbout;

/* the version running: the window's where there is one, else the server's, as About and the citation say it */
function runningVersion() {
  return (UPD.view && UPD.view.running) || (S.lib && S.lib.version) || '';
}

/* Support Idiograph (supportcard, 28 October 2026, Adam's wording 1 of that day): a card in About's look, opened
   from Home's link after Ko-fi, Settings' link beside About and the line after the first Word export of PETs
   (themes.js). Cite it gives the APA citation with the version running and Copy, which puts it on the clipboard
   as plain text. In Sift and Trace the citation names the app itself, and all three give idiograph.app (Adam,
   29 October, once he had registered it). A citation is never translated, so it is written here and not in the
   catalogue. Send feedback and "ask me how" (supportcard2, 29 October) open the app's own Send feedback card, and
   are left out where the build has no collector to send to, as the bars' feedback button is: a build with no
   collector is someone's own build, made from the code. Contribute code links the code on GitHub since the
   repository went public (pubreadme, 10 November 2026), so it stays in every build */
const SUPPORT_ADDRESS = 'https://idiograph.app';

function supportCitation(version, html = false) {
  const name = html ? `<i>${esc(APP_NAME)}</i>` : APP_NAME;
  const edition = version ? ` (Version ${html ? esc(version) : version})` : '';
  return `Knowles, A. (2026). ${name}${edition} [Computer software]. ${SUPPORT_ADDRESS}`;
}

function openSupport() {
  $('support-ref').innerHTML = supportCitation(runningVersion(), true);
  $('support-feedback').hidden = !FEEDBACK.on;
  $('support-grant').hidden = !FEEDBACK.on;
  show('support');
  doneAtFoot('support');
}
window.openSupport = openSupport;

async function supportCopy() {
  try {
    await navigator.clipboard.writeText(supportCitation(runningVersion()));
    say(t('shell.support.copied'));
  } catch { say(t('shell.agent.clipboard_refused'), 9000); }
}

/* the card's ways in and its own controls, the Send feedback card taking its place */
function supportWire() {
  $('lib-support').onclick = () => openSupport();
  $('settings-support').onclick = () => openSupport();
  $('support-done').onclick = () => hide('support');
  $('support-x').onclick = () => hide('support');
  $('support-copy').onclick = () => supportCopy();
  $('support').addEventListener('click', (e) => {
    if (!(e.target && e.target.closest && e.target.closest('[data-support-feedback]'))) return;
    e.preventDefault();
    hide('support');
    // a word no list of screens holds, so the note goes naming no screen
    openFeedback('support');
  });
}

/* The Restart after the restart line: every text that carries the line, there at boot or written
   later, toast, pane or canvas, gets the button after it, once. A text written again loses its
   button with its old words and gets a new one. */
function restartButtons() {
  if (SERVER.watch || typeof MutationObserver === 'undefined') return;
  const place = (text) => {
    if (!text.nodeValue || !text.nodeValue.includes(RESTART_LINE)) return;
    const el = text.parentElement;
    if (!el || el.closest(`.${RESTART_NOW}, #server-gone, #server-old, script, style, textarea, option, title`)) return;
    if ([...el.children].some((c) => c.classList.contains(RESTART_NOW))) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `ghost small ${RESTART_NOW}`;
    button.textContent = t('shell.server.restart_button');
    el.appendChild(button);
  };
  const mark = (root) => {
    if (root.nodeType === Node.TEXT_NODE) { place(root); return; }
    if (root.nodeType !== Node.ELEMENT_NODE || !(root.textContent || '').includes(RESTART_LINE)) return;
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = walk.nextNode(); n; n = walk.nextNode()) place(n);
  };
  mark(document.body);
  SERVER.watch = new MutationObserver((records) => {
    for (const r of records) {
      if (r.type === 'characterData') place(r.target);
      else r.addedNodes.forEach(mark);
    }
  });
  SERVER.watch.observe(document.body, { childList: true, subtree: true, characterData: true });
}

/* ────────────────────────────────────────────────────────── wiring ── */

/* Appearance, three states, not two. `system` follows the appearance set in macOS and changes with
   it, with no reload, because the stylesheet carries the media query. A store from before this held
   only light or dark, and either one is still honoured. Since 16 October it is chosen under
   Settings, General, Light, Dark or Same as this computer, applied at once, where until then a button
   on every bar cycled it. The store keeps its key and its values. */
const THEMES = ['system', 'light', 'dark'];

function storedTheme() {
  let saved = null;
  try { saved = localStorage.getItem('idiograph-theme'); } catch { /* private window */ }
  return saved === 'light' || saved === 'dark' ? saved : 'system';
}

function theme(next) {
  const name = THEMES.includes(next) ? next : 'system';
  document.documentElement.dataset.theme = name;
  try { localStorage.setItem('idiograph-theme', name); } catch { /* private window */ }
  drawAppearance();
  // what draws its own colours, Sift's PRISMA flow, draws again
  document.dispatchEvent(new CustomEvent('idiograph-theme', { detail: name }));
}

/* Appearance kept in the app's own settings too (the split's third build), so Sift's and Trace's first start
   copy it from Idiograph's: sent the moment a row is ticked, and read at boot, where the browser's own
   store gave the first paint. Opening the page only reads: the file is written when a row is ticked, and
   then with that one key */
function themeKeep(name) {
  api('/api/settings', { appearance: name }).then((data) => {
    if (data && data.config && S.libConfig) S.libConfig.appearance = data.config.appearance;
  }).catch(() => {});
}

async function themeFromSettings() {
  let data = null;
  try { data = await api('/api/settings', { op: 'read' }); } catch { return; }
  const held = data && data.config ? data.config.appearance : null;
  if (THEMES.includes(held) && held !== storedTheme()) theme(held);
  // and the language as the settings hold it, "" for the computer's own, which the Language row ticks
  LANGUAGE_ROW.set = data && data.config && typeof data.config.language === 'string' ? data.config.language : '';
  drawLanguage();
  // and the formats beside it, each "" for the computer's own
  const chosen = data && data.config && data.config.formats && typeof data.config.formats === 'object' ? data.config.formats : {};
  FORMATS_ROW.set = Object.fromEntries(Object.keys(FORMAT_CHOICES).map((k) => [k, typeof chosen[k] === 'string' ? chosen[k] : '']));
  drawFormats();
}

/* the three rows under Settings, General, the one on ticked */
function drawAppearance() {
  const now = storedTheme();
  for (const name of THEMES) {
    const row = $(`set-appearance-${name}`);
    if (row) row.checked = now === name;
  }
}

/* Language (i18nus, 28 October 2026), under Language and formats since fmtcore: Same as this computer, named as
   the app reads it, "English, UK" on a computer in a language the app has no words for, then English (UK) and
   English (US). Ticking a row saves `language` at once and loads the page again in it, back on the screen it was
   on (the reload keeps its place as a restart does) with Settings open again on Language and formats, so it needs
   no restart. What is typed and not
   saved is kept first, and when it cannot be, nothing changes. The window's own menus take a language at its
   next start, and en-US's menus are English's. */
const LANGUAGE_ROW = { set: null, busy: false };
const LANGUAGE_AGAIN = 'idiograph-language-settings';

/* the computer's row named, and the row the settings hold ticked, before the read the one the page is in */
function drawLanguage() {
  const names = { 'en-GB': t('page.language.in_en_gb'), 'en-US': t('page.language.in_en_us') };
  const computer = I18N_DATA.computer || 'en-GB';
  if ($('language-computer-word')) {
    $('language-computer-word').textContent = t('page.language.computer', { language: names[computer] || computer });
  }
  const held = LANGUAGE_ROW.set === null ? '' : LANGUAGE_ROW.set;
  const now = held === '' ? '' : (held === 'en' ? 'en-GB' : held);
  for (const row of document.querySelectorAll('input[name="set-language"]')) row.checked = row.value === now;
}

async function languageSet(tag) {
  if (LANGUAGE_ROW.busy) return;
  LANGUAGE_ROW.busy = true;
  try {
    if (!(await savePending())) { say(t('shell.language.not_saved'), 9000); drawLanguage(); return; }
    await api('/api/settings', { language: tag });
    LANGUAGE_ROW.set = tag;
    try { sessionStorage.setItem(LANGUAGE_AGAIN, String(Date.now())); } catch { /* private window */ }
    location.reload();
  } catch (err) {
    say(err.message, 9000);
    drawLanguage();
  } finally { LANGUAGE_ROW.busy = false; }
}

/* after the reload a Language or a format row asked for, Settings open again on Language and formats, taken once
   and only within a minute */
function languageAgain() {
  let at = 0;
  try {
    at = Number(sessionStorage.getItem(LANGUAGE_AGAIN) || 0);
    sessionStorage.removeItem(LANGUAGE_AGAIN);
  } catch { at = 0; }
  if (at && Date.now() - at < 60 * 1000) openSettings('formats');
}

/* Dates, Times of day and Numbers under Language and formats (fmtcore, 28 October 2026, Adam's B of that day),
   each first Same as this computer, named by what the computer gives (I18N.computer_formats, from the window, or
   the language's own in a browser), then each choice written as an example of itself, 28 Oct 2026, Oct 28, 2026
   and 2026-10-28, 14:05 and 2:05 pm, 1,234.5, 1.234,5, 1 234,5 and 1'234.5, the month's name and am and pm the
   language's. Ticking a row saves that key of `formats` alone and loads the page again in it, as Language does,
   so every date, time and number the page writes through tDate, tTime and tNum follows at once. */
const FORMATS_ROW = { set: null, busy: false };
const FORMAT_SAMPLE = new Date(2026, 9, 28, 14, 5);

/* each row's example, and the row the settings hold ticked, before the read the ones the page is in */
function drawFormats() {
  const comp = I18N_DATA.computer_formats || {};
  const said = {
    dates: (order) => tDate(FORMAT_SAMPLE, { day: 'numeric', month: 'short', year: 'numeric' }, { dates: order }),
    time: (clock) => tTime(FORMAT_SAMPLE, { time: clock }),
    numbers: (marks) => tNum(1234.5, { maximumFractionDigits: 1 }, { numbers: marks }),
  };
  for (const kind of Object.keys(FORMAT_CHOICES)) {
    const held = FORMATS_ROW.set ? FORMATS_ROW.set[kind] : (I18N_DATA.formats || {})[kind] || '';
    for (const box of document.querySelectorAll(`input[name="set-${kind}"]`)) {
      box.checked = box.value === (held || '');
      const word = box.parentElement.querySelector('[data-format-word]');
      if (!word) continue;
      word.textContent = box.value ? said[kind](box.value)
        : t('page.formats.computer', { example: said[kind](comp[kind] || '') });
    }
  }
}

async function formatsSet(kind, value) {
  if (FORMATS_ROW.busy) return;
  FORMATS_ROW.busy = true;
  try {
    if (!(await savePending())) { say(t('shell.formats.not_saved'), 9000); drawFormats(); return; }
    await api('/api/settings', { formats: { [kind]: value } });
    try { sessionStorage.setItem(LANGUAGE_AGAIN, String(Date.now())); } catch { /* private window */ }
    location.reload();
  } catch (err) {
    say(err.message, 9000);
    drawFormats();
  } finally { FORMATS_ROW.busy = false; }
}

/* Text size under General (Adam, 20 October, Settled 12), in Idiograph's own window alone: Small, Medium or
   Large, the window's zoom at 90%, 100% and 125%, which View's Bigger Text, Smaller Text and Actual Size
   move too, the two in step. The row on is the one the zoom stands at. Where the keys have left it between
   the three, at 110% say, no row is on and the heading says the size, "Text size: 110%" (30 October, drawn
   for Adam as option A). The window keeps it for the next run. A browser's tab has no `idiographTextSize`,
   and its own zoom, so the rows stay hidden. */
const TEXT_SIZES = { small: 0.9, medium: 1, large: 1.25 };
const textSizeOf = (zoom) => Object.keys(TEXT_SIZES).find((k) => Math.abs(zoom - TEXT_SIZES[k]) < 0.005) || '';
const textPercent = (zoom) => tNum(zoom, { style: 'percent', maximumFractionDigits: 0 });

function textSizeDraw(zoom) {
  const known = typeof zoom === 'number';
  const size = known ? textSizeOf(zoom) : '';
  document.querySelectorAll('input[name="set-text-size"]').forEach((row) => { row.checked = row.value === size; });
  const sub = $('text-size-sub');
  if (sub) sub.textContent = known && !size ? t('page.text_size.title_at', { size: textPercent(zoom) }) : t('page.text_size.title');
}

async function textSizeOpen() {
  const there = typeof window.idiographTextSize === 'function';
  $('text-size-block').hidden = !there;
  if (there) textSizeDraw(await window.idiographTextSize());
}

/* the row he last picked in Settings and when, so the size is not said for a change he is looking at */
let textSizePick = null;
async function textSizeSet(size) {
  if (typeof window.idiographTextSize !== 'function' || !(size in TEXT_SIZES)) return;
  textSizePick = { to: TEXT_SIZES[size], at: Date.now() };
  textSizeDraw(await window.idiographTextSize(TEXT_SIZES[size]));
}

/* The size said at the foot when the keys or View's items change it (Adam, 30 October: his window had been
   zoomed and he never knew), "Text size 110%", the line replaced at each step, the percent written by the
   Numbers format. Not for a row picked in Settings, which he sees, and not in a browser's tab, which has no
   `idiographTextSize` and so no event. The window tells the page twice for a change (its own event and the
   answer to the command), one line either way. */
function textSizeSay(zoom) {
  if (typeof zoom !== 'number' || typeof window.idiographTextSize !== 'function') return;
  if (textSizePick && Math.abs(zoom - textSizePick.to) < 0.001 && Date.now() - textSizePick.at < 1500) return;
  say(t('shell.text_size.said', { size: textPercent(zoom) }), 3000);
}

/* the keys and View's items tell the page, so the rows follow them while Settings is open */
window.addEventListener('idiograph-zoom', (e) => { textSizeDraw(e.detail); textSizeSay(e.detail); });

/* The notes could be shut under their own heading in the panel at the right until 17 October, which
   the browser kept as `idiograph-disclosures`. In the three columns they stand open in their own
   column on every passage, so nothing shuts them and the key is no longer read. */

/* The page's title, which a browser's tab and the app's own window both take, so two windows on two
   cases tell apart in the Dock, the taskbar and Alt+Tab (17 October): the app first and then what is open,
   its project, its participant where the screen is one's, and its screen, as in "Idiograph - Living with a dog -
   Juno - Experiential statements" (headroom, 6 November 2026, Adam: the app's name leads, as the
   window of any other app names itself, then the project). Home is the app's name alone, a project's page the
   app and its project, and Sift's and Trace's screens the app and the project. A part left out is a part the
   screen has none of, so no dash is ever left standing. Read from the bar's own name twice a second, since
   every screen draws its name its own way. */
const titleShown = (id) => !!$(id) && !$(id).hidden;
const titleText = (id) => ($(id) ? $(id).textContent.trim() : '');
const titled = (app, ...parts) => [app, ...parts.filter(Boolean)].join(' - ');

function pageTitle() {
  // an app's own screen by its own script, Idiograph's case, board or project's page
  const said = appsSay('title');
  if (said) return said;
  if (titleShown('sift')) return titled('Sift', titleText('sf-name'));
  if (titleShown('sift-search')) return titled('Sift', titleText('sfs-name'));
  if (titleShown('trace')) return titled('Trace', titleText('tr-name'));
  return APP_NAME;
}

/* The bars above every screen of the three apps (option C of Adam's bars, 26 October 2026): the app's lockup at
   the left of each title bar, its mark and its name, Home from every screen, drawn in from Home's own so the two
   never part, the Preview Edition's stamp left to Home and About. Run as the page starts and again by Sift and
   Trace once they build their screens. */
function barLockups() {
  if (typeof document === 'undefined' || !document.querySelectorAll) return;
  const lockup = document.querySelector(`#library .wordmark [data-only="${APP}"] svg.lockup`);
  for (const b of document.querySelectorAll('.bar-brand')) {
    if (!lockup || b.querySelector('svg.lockup')) continue;
    const own = lockup.cloneNode(true);
    own.setAttribute('aria-hidden', 'true');
    own.removeAttribute('role');
    b.prepend(own);
  }
  for (const bar of document.querySelectorAll('.screen > .rail')) barFitWatch(bar);
  // and Home's head, whose top row's tools give way by the same rule (homehead, 5 November 2026)
  for (const top of document.querySelectorAll('#library .lib-top')) barFitWatch(top);
}

/* A title bar's words give way to its room: every tool keeps its word where the bar holds it, and where it runs
   short the tools lose their words first, then a tab its long name for its short one, Experiential statements
   for ES (option C of the bars). A phone's width takes two rows and the icons alone by the stylesheet. */
const BAR_FIT_STEPS = ['bar-fit-words', 'bar-fit-tabs'];
function barFit(bar) {
  if (!bar || !bar.classList) return;
  bar.classList.remove(...BAR_FIT_STEPS);
  if (!bar.clientWidth) return;
  const over = () => bar.scrollWidth > bar.clientWidth + 1;
  for (const step of BAR_FIT_STEPS) {
    if (!over()) return;
    bar.classList.add(step);
  }
}

const BAR_FIT_WATCHED = new WeakSet();
function barFitWatch(bar) {
  if (!bar || BAR_FIT_WATCHED.has(bar) || typeof ResizeObserver === 'undefined') return;
  BAR_FIT_WATCHED.add(bar);
  new ResizeObserver(() => barFit(bar)).observe(bar);
}

/* The app's own name wherever the page names it in its markup: Settings' kicker, its foot's Restart and
   About, Updates' line and the Closing tick (the split's third build) */
function appWords() {
  $('settings-kicker').textContent = APP_NAME;
  $('server-ops').setAttribute('aria-label', APP_NAME);
  $('server-restart').textContent = t('shell.server.restart', { app: APP_NAME });
  for (const el of document.querySelectorAll('.app-name')) el.textContent = APP_NAME;
  $('update-privacy').textContent = UPD_PRIVACY;
  $('quit-closed-word').textContent = t('shell.closing.quit_when_closed', { app: APP_NAME });
}

function titleKeep() {
  const now = pageTitle();
  if (document.title !== now) document.title = now;
  screenHeads();
}

/* Each screen's heading for a screen reader (a11yfix, 8 November 2026): a screen that shows no heading of the first
   rank, the statements screen, the boards, Coding, the codes and Sift's and Trace's tables among them, has one out
   of sight, in the words of its tab in the bar, or the app's name on Home's picker. A screen that shows its own,
   a project's page with the project's name or a Sift record's title, keeps that alone. */
function screenHeads() {
  if (typeof document === 'undefined' || !document.querySelectorAll) return;
  for (const screen of document.querySelectorAll('.screen')) {
    if (screen.hidden) continue;
    let head = screen.querySelector(':scope > h1.screen-head');
    const own = [...screen.querySelectorAll('h1:not(.screen-head)')]
      .some((h) => h.textContent.trim() && h.getClientRects().length);
    if (own && !head) continue;
    const tab = screen.querySelector('.rail [aria-current="page"], .rail [aria-current="step"]');
    const words = own ? '' : (tab && (tab.getAttribute('aria-label')
      || (tab.querySelector('.tab-w') || tab).textContent.trim())) || APP_NAME;
    if (!head) {
      head = document.createElement('h1');
      head.className = 'sr-only screen-head';
      screen.prepend(head);
    }
    head.hidden = own;
    if (head.textContent !== words) head.textContent = words;
  }
}

function boot() {
  theme(storedTheme());
  themeFromSettings();
  appWords();
  barLockups();
  // the project's name in every screen's band opens its menu (barsD)
  bandMenuBoot();
  // every card a dialog that keeps Tab and gives the focus back (a11yfix)
  cardsWatch();
  setInterval(titleKeep, 500);
  $('btn-key-check').onclick = () => checkKey();
  // Enter in the key's field is Check key
  $('set-key').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); checkKey(); } });
  $('btn-key-clear').onclick = () => clearKey();
  // the tooltips written with Cmd name Ctrl on Windows and Linux
  for (const el of document.querySelectorAll(`[title*="${t('shell.keys.cmd')} + "]`)) el.title = keyName(el.title);
  $('lib-feedback').onclick = () => openFeedback(!$('home-project') || $('home-project').hidden ? 'home' : 'project');
  $('feedback-cancel').onclick = () => closeFeedback();
  $('feedback-send').onclick = () => sendFeedback();
  $('feedback-text').addEventListener('input', feedbackReady);
  $('settings-close').onclick = () => hide('settings');
  $('settings-save').onclick = () => saveSettings();
  $('settings-nav').addEventListener('click', (e) => {
    const tab = e.target.closest('[data-pane]');
    if (tab) showPane(tab.dataset.pane);
  });
  $('settings-nav').addEventListener('keydown', paneKeys);
  $('set-provider').onchange = () => chooseProvider();
  // the Address row: the where line follows each key, and leaving it asks for the key and the list there
  $('set-address').oninput = () => typeAddress();
  $('set-address').onchange = () => leaveAddress();
  // an OpenAI-style provider's model, from its list or typed, and Azure's deployment, kept as he changes them
  $('set-other-model').onchange = () => pickOther();
  $('set-other-name').oninput = () => pickOther();
  $('set-deployment').oninput = () => drawPetsNote();
  // AI features: ticking it asks first in its own card, and unticking hides what sits under it
  $('set-ai').onchange = () => aiSwitch();
  $('ai-confirm-go').onclick = () => aiConfirm(true);
  $('ai-confirm-cancel').onclick = () => aiConfirm(false);
  // Sound waits on Celebrations, and ticking it plays the tick once, so its loudness is known
  $('cheer-set').onchange = () => cheerSoundGate();
  // Text size, the window's zoom, applied the moment a row is ticked
  $('text-size-set').onchange = (e) => { if (e.target && e.target.name === 'set-text-size') textSizeSet(e.target.value); };
  $('set-sound').onchange = () => { if ($('set-sound').checked) playSound('tick'); };
  // the PETs model's line follows both screens' selects, and the key follows the line
  for (const id of ['set-model', 'set-local-model', 'set-pets-model']) if ($(id)) $(id).onchange = () => drawPetsNote();
  $('set-model').addEventListener('change', drawModelPrice);
  $('lib-settings').onclick = () => openSettings('general');
  // the New project and Open project folder card, Sift's and Trace's
  $('rv-cancel').onclick = () => hide('rv-card');
  $('rv-go').onclick = () => rvMake();
  $('rv-choose').onclick = () => rvFolder();
  const rvTyped = () => {
    const typed = $('rv-folder').value.trim();
    if (typed && typed !== RVC.folder) rvFolder(typed);
  };
  $('rv-folder').addEventListener('change', rvTyped);
  $('rv-folder').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); rvTyped(); } });
  $('rv-name').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); rvMake(); } });
  // a line the card said goes as soon as he changes what it was about
  ['rv-folder', 'rv-name', 'rv-question'].forEach((id) => $(id).addEventListener('input', () => rvSaid('')));
  // Appearance under Settings, General, applied the moment a row is ticked, with no Save
  $('appearance-set').addEventListener('change', (e) => {
    if (e.target && e.target.name === 'set-appearance' && e.target.checked) { theme(e.target.value); themeKeep(e.target.value); }
  });
  // Language under General, saved and applied the moment a row is ticked, by loading the page again in it
  $('language-set').addEventListener('change', (e) => {
    if (e.target && e.target.name === 'set-language' && e.target.checked) languageSet(e.target.value);
  });
  // and Dates, Times of day and Numbers beside it, the same way (fmtcore)
  for (const kind of Object.keys(FORMAT_CHOICES)) {
    $(`${kind}-set`).addEventListener('change', (e) => {
      if (e.target && e.target.name === `set-${kind}` && e.target.checked) formatsSet(kind, e.target.value);
    });
  }
  $('agent-copy').onclick = (e) => agentCopy(e.currentTarget);
  // Restart and Quit at the foot of Settings, and the Restart after the restart line, caught before
  // the click reaches whatever holds the line
  $('server-restart').onclick = () => serverOp('restart');
  $('server-quit').onclick = () => serverOp('quit');
  document.addEventListener('click', (e) => {
    if (!(e.target && e.target.closest && e.target.closest(`.${RESTART_NOW}`))) return;
    e.preventDefault();
    e.stopPropagation();
    serverOp('restart');
  }, true);
  serverBoot();
  // Idiograph's own updates and What's new, in its window alone: Check now, Download and Relaunch now
  // under Updates in Settings, the home screen's line and the foot's, the window's word heard as it
  // comes and asked for once here
  window.addEventListener('idiograph-update', (e) => updTake(e.detail));
  $('update-check-now').onclick = () => updAsk('check');
  $('update-get').onclick = () => updAsk('download');
  $('update-relaunch').onclick = () => updRelaunch();
  // Settings' What's new: the update's own notes first while one waits, then the running version's
  $('update-notes').onclick = () => openWhatsNew({ incoming: true });
  $('set-update-check').onchange = () => { $('set-update-download').disabled = !$('set-update-check').checked; };
  // the foot line's What's new: every version since the one that ran before the update
  $('whatsnew-open').onclick = () => openWhatsNew({ since: WN.before });
  $('whatsnew-earlier').onclick = () => wnEarlier();
  $('whatsnew-close').onclick = () => wnFootClose();
  $('whatsnew-done').onclick = () => hide('whatsnew');
  $('whatsnew-x').onclick = () => hide('whatsnew');
  $('about-done').onclick = () => hide('about');
  $('about-x').onclick = () => hide('about');
  $('settings-about').onclick = () => openAbout();
  supportWire();
  rmWire();
  updAsk();

  document.addEventListener('keydown', (e) => {
    // Send feedback's card keeps its keys on either screen: Esc cancels, Cmd + Enter sends, so
    // does Enter in the reply line, and every other key types
    // About closes alone on Esc, and Settings under it stays
    if (!$('about').hidden && e.key === 'Escape') { e.preventDefault(); hide('about'); return; }
    // Remove's card over Settings or Home: Esc removes nothing, and its own buttons and tick take the rest
    if (!$('remove-card').hidden) {
      if (e.key === 'Escape') { e.preventDefault(); rmAnswer(false); }
      return;
    }
    // and so does the Support card
    if (!$('support').hidden && e.key === 'Escape') { e.preventDefault(); hide('support'); return; }
    // and the agent log's sheet over Settings, every app's (agentlog.js)
    if (typeof agentLogKeys === 'function' && agentLogKeys(e)) return;
    if (!$('feedback').hidden) {
      if (e.key === 'Escape') { e.preventDefault(); closeFeedback(); }
      else if (e.key === 'Enter' && (MOD(e) || e.target === $('feedback-contact'))) { e.preventDefault(); sendFeedback(); }
      return;
    }
    // AI features' confirm card over Settings: Esc and Enter both keep it off, Back to safety, unless
    // I understand the risks has the focus, when Enter presses it, and Settings stays open behind it
    if (!$('ai-confirm').hidden) {
      if (e.key === 'Escape') { e.preventDefault(); aiConfirm(false); }
      else if (e.key === 'Enter') { e.preventDefault(); aiConfirm(e.target === $('ai-confirm-go')); }
      return;
    }
    if (e.key === 'Escape') {
      // an app's own first, Idiograph's menus, a timecode or a turn open for correction, the quote candidate
      // and its find card, then the panels, then the app's way back, and only then leaving the field
      if (appsKeys('keysEscape', e)) return;
      if (anyOverlayOpen()) { overlaysHere().forEach(hide); return; }
      if (appsKeys('keysEscapeLast', e)) return;
      if (document.activeElement && document.activeElement.tagName === 'TEXTAREA') document.activeElement.blur();
      return;
    }
    // an app's cards' own keys, Idiograph's, then nothing more under a card, then the app's screen's keys
    if (appsKeys('keysCards', e)) return;
    if (anyOverlayOpen()) return;
    appsKeys('keys', e);
  });
  // a reload keeps where he was, as a restart does: the screen in front of him, kept as the page goes
  window.addEventListener('pagehide', () => { if (!SERVER.busy && !S.noSpot) spotKeep(); });
  // Home and the screen kept, once every app's script has registered its part (FAMILY_APPS), so each
  // app's own Home and screens answer (the family codebase's fifth build, 23 October 2026)
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', homeStart, { once: true });
  else homeStart();
}

/* the page's start on Home, or back on the screen kept from a restart or a reload */
function homeStart() {

  // the home screen's own place in this tab, the picker or a project's page
  S.home = homeHeld();
  // back from a restart or a reload, the screen it was on, the home screen drawn out of sight
  // meanwhile. The PETs screen's script comes after this one, so the way back waits for every
  // script of the page
  // and a window opened by Open in a new window on the place it was opened for, from its address (20 October)
  spotFromAddress();
  const spot = spotTaken();
  if (spot) $('library').hidden = true;
  // and Settings open again over the screen once it is back, after a Language row's reload (languageAgain)
  const drawn = loadLibrary(!spot).then(() => { if (!spot) languageAgain(); }).catch((err) => say(err.message, 9000));
  // the mark comes in when the app opens on Home, once a window (homeMarkPlay), and opened on any other
  // screen it stays still
  if (!spot) homeMarkPlay();
  else {
    document.documentElement.classList.remove('home-mark-due');
    try { sessionStorage.setItem(HOME_MARK_KEY, '1'); } catch { /* private window */ }
  }
  // the start done, Home drawn and the screen kept opened again, which a shared copy the window hands Idiograph's
  // page waits for (fileassoc, 6 November 2026)
  let backed = () => {};
  S.started = Promise.all([drawn, spot ? new Promise((done) => { backed = done; }) : null]);
  if (spot) {
    const back = () => comeBack(spot).then(languageAgain, languageAgain).finally(backed);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', back, { once: true });
    else back();
  }
}

boot();
