/* Working together's comments and review (wtreview, 8 November 2026, build 4 of the spec, drawn in wtshots 06, 08,
   10 and 11 and approved as drawn). Nothing here shows while Working together is off: every call answers
   `{on: false}` and every part stays hidden.

   The owner asks for a review from a participant's menu on the project's page (Ask for review, after Rename). A
   teammate on a participant he does not own comments on a passage (its words selected, Comment by the selection),
   a statement (Comment under it) or a PET or a GET (Comment in its menu), each kept as a draft on his machine, and
   the tray, a row under the toolbar, says "Review for Adam: 2 comments" with Send review. When a review comes, the owner sees
   the line where held changes stand, "Curt's review of Juno: 2 comments." with Review, which opens the review card:
   each comment with what it is on, Reply and Resolve, and Done, which keeps every thread he left open as
   unresolved, still on view under its passage on both machines. Replies and Resolve go at once. A board the
   teammate sent stands on the same line and card, "Curt's board of Juno's PETs", waiting for Decline or Add as
   next board (/api/team-board's answer), a board sent on its own a review holding only a board (wtreview2, 9
   November 2026).

   Suggestions (wtsuggest, 10 November 2026, drawn in wtshots 08, 09 and 11 and approved as drawn): the reviewer's
   Suggest a wording beside Comment under a statement, and Suggest a title in a PET's or a GET's menu, each a small
   box with today's words in it and an optional reason, kept as a draft in his tray until Send review. The owner's
   card shows each with Now and the reviewer's words, Decline and Accept, a changed one marked and still accepted,
   one whose statement is gone Decline only. Under the passage the reviewer sees his own and their answers.

   Every write is `/api/team-review`, the op the command line's `team` commands run (review.py). */

const RVW = {
  st: null,          // the state for the screen on view, as /api/team-review answered it
  ask: 0,            // the state in flight, so a slow answer never lands on a newer one
  busy: false,
  editor: null,      // the comment or suggestion being written, { kind, key, words, time, label, line, board, suggest }
  reply: null,       // the reply box open on the card, by thread id
  decline: null,     // the suggestion whose Decline asks why, on the card, by id
  review: null,      // the review open on the card
  rows: new Map(),   // each project's state on Home, by its id
  rowAsk: new Map(),
  askFor: null,      // the Ask for review card's participant, { root, case, members }
  at: { x: 0, y: 0 }, // where the last menu was asked for, for a PET's comment box
};
const RVW_EVERY = 4 * 1000;
const RVW_BUBBLE = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v8a1.5 1.5 0 0 1-1.5 1.5h-8l-4.5 3.5v-3.5H5A1.5 1.5 0 0 1 3.5 15V7A1.5 1.5 0 0 1 5 5.5Z"/></svg>';
const RVW_PEN = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M4.5 19.5l1-4 10-10 3 3-10 10-4 1Z"/><path d="M13.5 7.5l3 3"/></svg>';

/* a pseudonym from a case as its row names it, "P1 - Juno" or "P1 Juno" being Juno */
const rvwWho = (c) => String(c || '').replace(/^P\d+\s*-?\s*/, '').trim();

async function rvwCall(body) {
  return api('/api/team-review', body);
}

/* ── the project's page: Ask for review in a participant's menu, on one he owns ── */

/* each row of a project, as drawCards draws it, asks once for its project's state, and gets Ask for review */
function rvwRow(li, p, where) {
  if (!li || !where || !where.id || p.demo || !p.path) return;
  li.dataset.wtRoot = where.id;
  if (RVW.rowAsk.has(where.id)) return;
  RVW.rowAsk.set(where.id, setTimeout(async () => {
    RVW.rowAsk.delete(where.id);
    let st;
    try { st = await rvwCall({ op: 'state', root: where.id }); } catch { st = { on: false }; }
    RVW.rows.set(where.id, st);
    rvwRowsDraw(where.id);
  }, 30));
}

function rvwRowsDraw(root) {
  const st = RVW.rows.get(root) || { on: false };
  for (const li of document.querySelectorAll('li.pcard')) {
    if (li.dataset.wtRoot !== root) continue;
    const menu = li.querySelector('.pc-menu');
    if (!menu) continue;
    const old = menu.querySelector('[data-act="wtask"]');
    if (old) old.remove();
    const own = st.on && (st.owners || {})[rvwWho(li.dataset.case)];
    if (!own || !own.mine || !(st.members || []).length) continue;
    menu.insertAdjacentHTML('beforeend', `<button type="button" class="ghost" role="menuitem" data-act="wtask">${esc(t('review.page.ask'))}</button>`);
  }
}

/* Ask for review (shot 06): who, each a tick by its whole row, and a line for them */
function rvwAskOpen(root, p) {
  const st = RVW.rows.get(root) || { members: [] };
  RVW.askFor = { root, case: p.case, members: st.members || [] };
  $('wt-ask-kicker').textContent = rvwWho(p.case);
  $('wt-ask-who').innerHTML = RVW.askFor.members.map((m, i) => `<label><input type="checkbox" data-wt-member="${i}" checked> ${esc(m)}</label>`).join('');
  $('wt-ask-line').value = '';
  rvwAskSaid('');
  rvwAskLabel();
  $('wt-ask-go').disabled = false;
  show('wt-ask');
  $('wt-ask-line').focus();
}

const rvwAskTicked = () => [...$('wt-ask-who').querySelectorAll('input[data-wt-member]')]
  .filter((x) => x.checked).map((x) => RVW.askFor.members[Number(x.dataset.wtMember)]);

function rvwAskLabel() {
  const names = rvwAskTicked();
  $('wt-ask-for').textContent = t('review.page.line_for', { names: tList(names.length ? names : RVW.askFor.members) });
  $('wt-ask-go').disabled = !names.length;
}

function rvwAskSaid(line) {
  $('wt-ask-said').textContent = line;
  $('wt-ask-said').hidden = !line;
}

async function rvwAskGo() {
  if (RVW.busy || !RVW.askFor) return;
  RVW.busy = true;
  $('wt-ask-go').disabled = true;
  try {
    const done = await rvwCall({ op: 'ask', root: RVW.askFor.root, case: RVW.askFor.case, to: rvwAskTicked(),
      line: $('wt-ask-line').value });
    hide('wt-ask');
    say((done.changes || [])[0] || '');
  } catch (err) {
    rvwAskSaid(err.message);
  } finally {
    RVW.busy = false;
    $('wt-ask-go').disabled = !rvwAskTicked().length;
  }
}

/* ── the screen on view: which participant, and its state ── */

function rvwScreen() {
  if ($('work') && !$('work').hidden && typeof S !== 'undefined' && S.data) return 'work';
  if ($('themes') && !$('themes').hidden && typeof TH !== 'undefined' && TH.path) return 'themes';
  return null;
}

/* the body naming the screen's participant, or on GETs the GETs board, and asking for every review that came */
function rvwBody() {
  const screen = rvwScreen();
  if (screen === 'work') return { path: S.data.path, all: true };
  if (screen === 'themes') return TH.mode === 'gets' ? { path: TH.path, case: '', all: true } : { path: TH.path, all: true };
  return null;
}

async function rvwTick() {
  const body = rvwBody();
  if (!body || document.hidden) { if (!body) { RVW.st = null; rvwDraw(); } return; }
  const ask = ++RVW.ask;
  let st;
  try { st = await rvwCall(Object.assign({ op: 'state' }, body)); } catch { st = { on: false }; }
  if (ask !== RVW.ask) return;
  RVW.st = st;
  rvwDraw();
}

const rvwOn = () => !!(RVW.st && RVW.st.on);
// a reviewer here: Working together on and the participant on view someone else's
const rvwReviewer = () => rvwOn() && RVW.st.mine === false;

function rvwDraw() {
  rvwTrayDraw();
  rvwLineDraw();
  rvwEsDraw();
  rvwPairsDrawn();
  if ($('sel-wtcomment')) $('sel-wtcomment').hidden = !(rvwReviewer() && rvwScreen() === 'work');
  if (RVW.review && !$('wt-review').hidden) rvwReviewDraw();
}

/* ── the reviewer's tray, top right (shot 08): his drafts on this participant, and Send review ── */

/* where the line and the tray stand: under the screen's toolbar at its right, below an agent's held line */
function rvwTop() {
  const th = $('th-undo');
  const undo = th && th.getBoundingClientRect().width ? th : $('es-undo');
  let top = undo && undo.parentElement ? undo.parentElement.getBoundingClientRect().bottom + 16 : 54;
  for (const id of ['hold-line', 'es-outside', 'th-outside']) {
    const el = $(id);
    if (el && !el.hidden && el.getBoundingClientRect().height) top = Math.max(top, el.getBoundingClientRect().bottom + 8);
  }
  return Math.round(top);
}

/* the reviewer's tray stands in the screen's own flow, a row under the toolbar's dock, right-aligned, where it hides
   nothing: Columns, the notes column's grip, the board's cards. Its height goes into the screen's --band with the
   dock's (measureBand on the statements screen, thBandMeasure on the boards), so the columns and the canvas take
   the room off their own (trayfix, 10 November 2026, from the drawing's top right, which stood over them). */
function rvwTrayDraw() {
  const tray = $('wt-tray');
  if (!tray) return;
  const screen = rvwScreen();
  const dock = screen === 'work' ? $('es-dock') : screen === 'themes' ? $('th-dock') : null;
  const drafts = rvwReviewer() ? (RVW.st.drafts || []).filter((d) => d.case === RVW.st.case) : [];
  const offered = rvwReviewer() ? (RVW.st.suggested || []).filter((s) => s.case === RVW.st.case) : [];
  if ((!drafts.length && !offered.length) || !dock) {
    tray.hidden = true;
  } else {
    $('wt-tray-for').textContent = t('review.page.tray', { owner: RVW.st.owner });
    $('wt-tray-counts').textContent = rvwCountsOf(drafts.length, offered.length);
    if (tray.previousElementSibling !== dock) dock.after(tray);
    tray.hidden = false;
  }
  if (typeof measureBand === 'function') measureBand();
  if (typeof thBandMeasure === 'function' && $('th-band')) thBandMeasure();
}

async function rvwSend() {
  if (RVW.busy || !rvwReviewer()) return;
  RVW.busy = true;
  $('wt-tray-send').disabled = true;
  try {
    const done = await rvwCall(Object.assign({ op: 'send' }, rvwBody(), { case: RVW.st.case }));
    say((done.changes || [])[0] || '');
  } catch (err) {
    say(err.message, 9000);
  } finally {
    RVW.busy = false;
    $('wt-tray-send').disabled = false;
    rvwTick();
  }
}

/* ── comments: the editor, under a statement, by the selection for a passage, or by a PET's or GET's menu ── */

const rvwRow0 = () => (typeof current === 'function' ? current() : null);

/* Comment under each statement of the passage being worked on, for a reviewer alone */
function rvwPairsDrawn() {
  const pairs = $('pairs');
  if (!pairs) return;
  const on = rvwReviewer() && rvwScreen() === 'work';
  [...pairs.querySelectorAll('.pair')].forEach((el, i) => {
    let tools = el.querySelector('.wt-tools');
    // a statement with no words yet has nothing to comment on
    if (!on || !el.querySelector('.pair-es').value.trim()) { if (tools) tools.remove(); return; }
    if (!tools) {
      el.querySelector('.pair-body').insertAdjacentHTML('beforeend', `<div class="wt-tools"><button type="button" class="ghost small" data-wt-line="${i}">${RVW_BUBBLE}${esc(t('review.page.comment'))}</button>`
        + `<button type="button" class="ghost small" data-wt-sline="${i}">${RVW_PEN}${esc(t('review.page.suggest_wording'))}</button></div>`);
      tools = el.querySelector('.wt-tools');
    } else {
      tools.querySelector('[data-wt-line]').dataset.wtLine = String(i);
      tools.querySelector('[data-wt-sline]').dataset.wtSline = String(i);
    }
    const ed = RVW.editor && RVW.editor.kind === 'statement' && RVW.editor.line === i ? RVW.editor : null;
    const box = tools.querySelector('.wt-draft');
    // a box of the other kind open here gives way to the one asked for
    if (box && (!ed || box.dataset.suggest !== String(!!ed.suggest))) box.remove();
    if (ed && !tools.querySelector('.wt-draft')) tools.insertAdjacentHTML('beforeend', ed.suggest ? rvwSuggestHtml('review.page.your_wording', ed.words, '') : rvwEditorHtml());
  });
}

function rvwEditorHtml(value = '') {
  return `<div class="wt-draft" data-suggest="false"><label class="wt-d-label" for="wt-text">${esc(t('review.page.your_comment'))}</label>`
    + `<textarea id="wt-text" rows="2">${esc(value)}</textarea>`
    + `<div class="wt-d-acts"><button type="button" class="ghost small" data-wt="cancel">${esc(t('review.page.cancel'))}</button>`
    + `<button type="button" class="ghost small" data-wt="add">${esc(t('review.page.add'))}</button></div></div>`;
}

/* a suggestion's box (shots 08 and 09): Your wording or Your title, Now under a title's head, today's words in the
   field to be changed, and an optional line for why */
function rvwSuggestHtml(labelKey, value, now) {
  const field = labelKey === 'review.page.your_title'
    ? `<input type="text" id="wt-text" value="${escAttr(value)}" spellcheck="true">`
    : `<textarea id="wt-text" rows="2">${esc(value)}</textarea>`;
  return `<div class="wt-draft wt-suggest" data-suggest="true"><label class="wt-d-label" for="wt-text">${esc(t(labelKey))}</label>`
    + (now ? `<p class="wt-now-is">${esc(t('review.page.now_is', { words: now }))}</p>` : '')
    + field
    + `<label class="wt-d-why" for="wt-why">${esc(t('review.page.why'))}</label><textarea id="wt-why" rows="1"></textarea>`
    + `<div class="wt-d-acts"><button type="button" class="ghost small" data-wt="cancel">${esc(t('review.page.cancel'))}</button>`
    + `<button type="button" class="ghost small" data-wt="add">${esc(t('review.page.add'))}</button></div></div>`;
}

function rvwCommentStatement(i, suggest = false) {
  const row = rvwRow0();
  const field = $('pairs').querySelectorAll('.pair .pair-es')[i];
  if (!row || !field) return;
  RVW.editor = { kind: 'statement', line: i, key: `${row.key}:${i}`, words: field.value, time: row.time || '', suggest };
  rvwPairsDrawn();
  rvwEsDraw();
  const box = $('wt-text');
  if (box) { box.focus(); if (suggest) box.select(); }
}

/* the comment's box over the screen, beside what it is on: the words selected, or a PET's or GET's label, and a
   title's suggestion in its own box */
function rvwPop(title, x, y, inner = null) {
  document.querySelectorAll('.wt-pop').forEach((e) => e.remove());
  const pop = document.createElement('div');
  pop.className = 'wt-pop';
  pop.innerHTML = inner || `<p class="wt-was">${esc(title)}</p>${rvwEditorHtml()}`;
  document.body.appendChild(pop);
  pop.style.left = `${Math.round(Math.max(8, Math.min(x, window.innerWidth - pop.offsetWidth - 8)))}px`;
  pop.style.top = `${Math.round(Math.max(8, Math.min(y, window.innerHeight - pop.offsetHeight - 8)))}px`;
  pop.addEventListener('click', rvwClick);
  $('wt-text').focus();
}

/* Comment by the selection: the words selected in a passage, its box under them */
function rvwCommentPassage() {
  const pick = typeof selBarPick === 'function' ? selBarPick() : null;
  const sel = window.getSelection();
  if (!pick || !sel) return;
  const words = sel.toString().replace(/\s+/g, ' ').trim();
  RVW.editor = { kind: 'passage', key: pick.row.key, words, time: pick.row.time || '' };
  if (typeof selBarHide === 'function') selBarHide();
  sel.removeAllRanges();
  rvwPop(`"${words}"`, pick.first.left, pick.bottom + 10);
}

/* Comment in a PET's or GET's menu, its box where the menu stood */
function rvwLabelItems(v, item) {
  if (!rvwReviewer() || rvwScreen() !== 'themes' || item.kind !== 'group') return [];
  return [{ label: t('review.page.comment'), act: 'wtcomment', rule: true },
    { label: t('review.page.suggest_title'), act: 'wtsuggest' }];
}

function rvwLabelComment(id) {
  const g = typeof thGroup === 'function' ? thGroup(TH.v, id) : null;
  if (!g) return;
  const title = typeof thLabelShown === 'function' ? thLabelShown(g.label) : String(g.label || '');
  RVW.editor = { kind: TH.mode === 'gets' ? 'get' : 'pet', key: id, words: title, label: '' };
  rvwPop(title, RVW.at.x, RVW.at.y + 6);
}

/* Suggest a title in a PET's or GET's menu (shot 09): its box where the menu stood, Now and the title to change */
function rvwLabelSuggest(id) {
  const g = typeof thGroup === 'function' ? thGroup(TH.v, id) : null;
  if (!g) return;
  const title = typeof thLabelShown === 'function' ? thLabelShown(g.label) : String(g.label || '');
  RVW.editor = { kind: TH.mode === 'gets' ? 'get' : 'pet', key: id, words: title, label: '', suggest: true,
    board: TH.meta && TH.meta.id ? TH.meta.id : '' };
  rvwPop(title, RVW.at.x, RVW.at.y + 6, rvwSuggestHtml('review.page.your_title', title, title));
  $('wt-text').select();
}

/* a passage left takes its statement's box with it */
function rvwTurnMoved() {
  if (RVW.editor && RVW.editor.kind === 'statement') RVW.editor = null;
  rvwPairsDrawn();
  rvwEsDraw();
}

function rvwEditorClose() {
  RVW.editor = null;
  document.querySelectorAll('.wt-pop').forEach((e) => e.remove());
  rvwPairsDrawn();
  rvwEsDraw();
}

async function rvwAdd() {
  const ed = RVW.editor;
  const box = $('wt-text');
  if (!ed || !box || RVW.busy) return;
  const text = box.value.trim();
  if (!text) { box.focus(); return; }
  RVW.busy = true;
  try {
    const why = ed.suggest && $('wt-why') ? $('wt-why').value.trim() : '';
    await rvwCall(Object.assign({ op: ed.suggest ? 'suggest' : 'comment' }, rvwBody(),
      ed.kind === 'get' ? { case: '' } : { case: RVW.st.case }, ed.suggest ? { reason: why } : {},
      { text, on: { kind: ed.kind, key: ed.key, words: ed.words, time: ed.time || '', label: ed.label || '', board: ed.board || '' } }));
    rvwEditorClose();
  } catch (err) {
    say(err.message, 9000);
  } finally {
    RVW.busy = false;
    rvwTick();
  }
}

/* ── under the passage: the editor for a passage, his drafts, and the threads not resolved ── */

function rvwWhen(at) {
  const d = new Date(at);
  if (Number.isNaN(d.getTime())) return '';
  return d.toDateString() === new Date().toDateString() ? t('review.page.sent_today', { time: tTime(d) })
    : t('review.page.sent_on', { date: tDate(d, { day: 'numeric', month: 'short' }), time: tTime(d) });
}

/* what a comment is on, "Comment on a passage, 21:45" */
function rvwHead(th) {
  const kind = th.on;
  if (kind === 'pet' || kind === 'get') {
    return th.label ? t('review.page.head.label', { label: th.label }) : t(kind === 'pet' ? 'review.page.head.pet' : 'review.page.head.get');
  }
  if (kind === 'passage') return th.time ? t('review.page.head.passage', { time: th.time }) : t('review.page.head.passage_untimed');
  return th.time ? t('review.page.head.statement', { time: th.time }) : t('review.page.head.statement_untimed');
}

/* one thread: what it is on, each comment by its author, You for his own, and its acts or where it stands */
function rvwThreadHtml(th, card) {
  const lines = th.comments.map((c) => `<p class="wt-said"><b>${esc(c.mine ? t('review.page.you') : c.by)}:</b> ${esc(c.text)}</p>`).join('');
  const own = !rvwOn() ? null : th.case === '' ? RVW.st.gets_owner : (RVW.st.owners || {})[th.case];
  const owner = !!(own && own.mine);
  const mayAnswer = owner || th.began_here;
  let foot = '';
  if (RVW.reply === th.id) {
    foot = `<div class="wt-draft"><label class="wt-d-label" for="wt-reply">${esc(t('review.page.your_reply'))}</label><textarea id="wt-reply" rows="2"></textarea>`
      + `<div class="wt-d-acts"><button type="button" class="ghost small" data-wt="reply-cancel">${esc(t('review.page.cancel'))}</button>`
      + `<button type="button" class="ghost small" data-wt="reply-send" data-thread="${escAttr(th.id)}">${esc(t('review.page.reply'))}</button></div></div>`;
  } else if (th.status === 'resolved') {
    foot = `<div class="wt-i-acts"><span class="wt-state">${esc(t('review.page.resolved'))}</span>`
      + (mayAnswer ? `<button type="button" class="ghost small" data-wt="reopen" data-thread="${escAttr(th.id)}">${esc(t('review.page.reopen'))}</button>` : '') + '</div>';
  } else if (mayAnswer) {
    foot = `<div class="wt-i-acts">${th.status === 'unresolved' && !owner ? `<span class="wt-state">${esc(t('review.page.kept'))}</span>` : ''}`
      + `<button type="button" class="ghost small" data-wt="reply" data-thread="${escAttr(th.id)}">${esc(t('review.page.reply'))}</button>`
      + (owner ? `<button type="button" class="ghost small" data-wt="resolve" data-thread="${escAttr(th.id)}">${esc(t('review.page.resolve'))}</button>` : '')
      + '</div>';
  }
  const quote = th.quote ? `<span class="wt-on">${esc(th.on === 'passage' ? `"${th.quote}"` : th.quote)}</span>` : '';
  return card
    ? `<div class="wt-item" data-thread="${escAttr(th.id)}"><span class="wt-k">${esc(rvwHead(th))}</span>${quote}${lines}${foot}</div>`
    : `<div class="wt-note" data-thread="${escAttr(th.id)}">${quote}${lines}${foot}</div>`;
}

function rvwEsDraw() {
  const box = $('wt-es');
  if (!box) return;
  const row = rvwRow0();
  if (!rvwOn() || rvwScreen() !== 'work' || !row) { box.hidden = true; box.innerHTML = ''; return; }
  const here = (key) => key === row.key || String(key).startsWith(`${row.key}:`);
  const drafts = (RVW.st.drafts || []).filter((d) => d.case === RVW.st.case && (d.on === 'passage' || d.on === 'statement') && here(d.key));
  const threads = (RVW.st.threads || []).filter((th) => th.case === RVW.st.case && here(th.key) && th.status !== 'resolved');
  let html = '';
  html += drafts.map((d) => `<div class="wt-note">${d.quote ? `<span class="wt-on">${esc(d.on === 'passage' ? `"${d.quote}"` : d.quote)}</span>` : ''}`
    + `<p class="wt-said"><b>${esc(t('review.page.you'))}:</b> ${esc(d.text)}</p></div>`).join('');
  html += threads.map((th) => rvwThreadHtml(th, false)).join('');
  // his own suggestions on this passage's statements: a draft, then sent with its answer once it comes, a
  // declined one staying
  const mine = (RVW.st.suggested || []).concat(RVW.st.suggestions || [])
    .filter((s) => s.case === RVW.st.case && s.on === 'statement' && here(s.key));
  html += mine.map((s) => `<div class="wt-note"><span class="wt-on">${esc(s.seen)}</span>`
    + `<p class="wt-said"><b>${esc(t('review.page.your_wording'))}:</b> ${esc(s.suggested)}</p>`
    + (s.status === 'draft' ? '' : `<p class="wt-said wt-answer">${esc(rvwMineSaid(s))}</p>`) + '</div>').join('');
  // the box keeps what is typed in it while the screen asks again
  const typing = box.contains(document.activeElement) && /TEXTAREA/.test(document.activeElement.tagName);
  if (typing && box.innerHTML && html.includes('<textarea')) return;
  box.innerHTML = html;
  box.hidden = !html;
}

/* ── the owner's line (shot 10), where held changes stand, and the review card (shot 11) ── */

function rvwLineDraw() {
  const line = $('wt-line');
  if (!line) return;
  // a review read with a suggestion still waiting stays on the line, as a board waiting does
  const reviews = rvwOn() ? (RVW.st.reviews || []).filter((r) => !r.seen || r.waiting) : [];
  // the participant on view first
  reviews.sort((a, b) => (b.case === RVW.st.case) - (a.case === RVW.st.case));
  const r = reviews[0];
  if (!r) { line.hidden = true; return; }
  $('wt-line-words').textContent = t('review.page.line', { who: r.from, name: r.case || t('review.gets_board'), counts: rvwCounts(r) });
  line.dataset.review = r.id;
  line.hidden = false;
  line.style.top = `${rvwTop()}px`;
}

/* "2 comments", "1 suggestion" or "2 comments, 1 suggestion" */
function rvwCountsOf(comments, suggestions) {
  const c = t('review.n.comments', { n: comments });
  if (!suggestions) return c;
  const s = t('review.n.suggestions', { n: suggestions });
  return comments ? t('review.n.pair', { comments: c, suggestions: s }) : s;
}

/* what a review holds, "2 comments", "2 comments, 1 suggestion and a board" or "a board" */
function rvwCounts(r) {
  const n = (r.suggestions || []).length;
  const counts = rvwCountsOf(r.comments, n);
  if (!(r.boards || []).length) return counts;
  return r.comments || n ? t('review.n.and_board', { counts }) : t('review.n.board');
}

/* his own suggestion's answer, as the reviewer sees it under the passage */
function rvwMineSaid(s) {
  if (s.status === 'accepted') return t('review.page.your_s_accepted', { owner: s.owner });
  if (s.status === 'declined') {
    return s.answer_reason ? t('review.page.your_s_declined_why', { owner: s.owner, reason: s.answer_reason })
      : t('review.page.your_s_declined', { owner: s.owner });
  }
  return t('review.page.your_s_waiting', { owner: s.owner });
}

/* what a suggestion is on, "New wording for a statement, 21:45" or "New title for PET B" */
function rvwSuggestHead(s) {
  if (s.on === 'statement') return s.time ? t('review.page.head.wording', { time: s.time }) : t('review.page.head.wording_untimed');
  if (s.label) return t('review.page.head.title_label', { label: s.label });
  return t(s.on === 'get' ? 'review.page.head.title_get' : 'review.page.head.title_pet');
}

/* a suggestion on the card (shot 11): Now and the teammate's words, why, a changed one marked, and Decline and
   Accept, or its answer. One whose statement is gone is Decline only. */
function rvwSuggestItem(s) {
  const who = s.from_name;
  const rows = (s.status === 'waiting' ? `<p class="wt-row"><span>${esc(t('review.page.now'))}</span><span>${esc(s.gone ? s.seen : s.now)}</span></p>` : '')
    + `<p class="wt-row wt-row-new"><span>${esc(who)}</span><span>${esc(s.suggested)}</span></p>`
    + (s.reason ? `<p class="wt-said"><b>${esc(s.by)}:</b> ${esc(s.reason)}</p>` : '');
  let foot;
  if (s.status === 'accepted') foot = `<div class="wt-i-acts"><span class="wt-state">${esc(t('review.page.accepted', { who }))}</span></div>`;
  else if (s.status === 'declined') foot = `<div class="wt-i-acts"><span class="wt-state">${esc(t('review.page.declined'))}</span></div>`;
  else if (RVW.decline === s.id) {
    foot = `<div class="wt-draft"><label class="wt-d-label" for="wt-no-why">${esc(t('review.page.why'))}</label><textarea id="wt-no-why" rows="2"></textarea>`
      + `<div class="wt-d-acts"><button type="button" class="ghost small" data-wt="no-cancel">${esc(t('review.page.cancel'))}</button>`
      + `<button type="button" class="ghost small" data-wt="s-no" data-sid="${escAttr(s.id)}">${esc(t('review.page.decline'))}</button></div></div>`;
  } else {
    foot = (s.gone ? `<p class="wt-stale">${esc(t('review.page.gone', { who, seen: s.seen }))}</p>`
      : s.stale ? `<p class="wt-stale">${esc(t('review.page.stale', { who, seen: s.seen }))}</p>` : '')
      + `<div class="wt-i-acts"><button type="button" class="ghost small" data-wt="s-decline" data-sid="${escAttr(s.id)}">${esc(t('review.page.decline'))}</button>`
      + (s.gone ? '' : `<button type="button" class="primary small" data-wt="s-yes" data-sid="${escAttr(s.id)}">${esc(t('review.page.accept'))}</button>`)
      + '</div>';
  }
  return `<div class="wt-item wt-sg" data-sid="${escAttr(s.id)}"><span class="wt-k">${esc(rvwSuggestHead(s))}</span>${rows}${foot}</div>`;
}

/* Accept or Decline: the op runs on what stands now, or nothing is written, and the answer goes back. On the PETs or
   GETs screen the board on view is saved first and read again after, so the new title shows at once. */
async function rvwSuggestAnswer(sid, accept, reason = '') {
  if (RVW.busy || !sid) return;
  RVW.busy = true;
  const board = rvwScreen() === 'themes';
  try {
    if (board && typeof thFlush === 'function') await thFlush();
    const done = await rvwCall(Object.assign({ op: 'answer', suggestion: sid, accept, reason }, rvwBody()));
    RVW.decline = null;
    if (board && accept && typeof thOwnLoad === 'function') await thOwnLoad({ changed: true });
    say((done.changes || [])[0] || '');
  } catch (err) {
    say(err.message, 9000);
  } finally {
    RVW.busy = false;
    await rvwTick();
  }
}

/* a teammate's name as whose board it is, Curt's, or Jess', from the catalogue as distil.js has it */
function rvwWhose(name) {
  const n = String(name || '').trim();
  return /s$/i.test(n) ? t('distil.copy.whose_s', { name: n }) : t('distil.copy.whose', { name: n });
}

/* a board the teammate sent: whose and of whom, where it comes in, and Decline and Add as next board, or its answer */
function rvwBoardHtml(b) {
  const said = b.answer === 'accepted' ? t('review.page.board_added', { name: b.name })
    : b.answer === 'declined' ? t('review.page.board_declined') : '';
  const where = b.beside ? t('review.page.board_next', { board: b.beside }) : t('review.page.board_first');
  const acts = said ? `<div class="wt-i-acts"><span class="wt-state">${esc(said)}</span></div>`
    : `<div class="wt-i-acts"><button type="button" class="ghost small" data-wt="board-no" data-ref="${escAttr(b.ref)}">${esc(t('review.page.decline'))}</button>`
      + `<button type="button" class="primary small" data-wt="board-yes" data-ref="${escAttr(b.ref)}">${esc(t('review.page.add_board'))}</button></div>`;
  return `<div class="wt-item" data-ref="${escAttr(b.ref)}"><span class="wt-k">${esc(t('review.page.board_head', { whose: rvwWhose(b.from), name: b.case }))}</span>`
    + `${said ? '' : `<p class="wt-said">${esc(where)}</p>`}${acts}</div>`;
}

/* Add as next board or Decline: the answer goes back to the teammate, and on that participant's PETs screen the
   new board shows in the board menu at once */
async function rvwBoardAnswer(ref, accept) {
  if (RVW.busy || !ref) return;
  RVW.busy = true;
  const body = { op: 'answer', ref, accept };
  const pets = rvwScreen() === 'themes' && TH.mode === 'pets';
  if (pets) Object.assign(body, { workbook: TH.path }, TH.tp ? { timepoint: TH.tp } : {});
  else Object.assign(body, rvwBody());
  try {
    if (pets && typeof thFlush === 'function') await thFlush();
    const data = await api('/api/team-board', body);
    if (pets && data.state && !TH.dirty && typeof thTakeBoards === 'function') thTakeBoards(data.state);
    say((data.changes || [])[0] || '');
  } catch (err) {
    say(err.message, 9000);
  } finally {
    RVW.busy = false;
    await rvwTick();
  }
  // a review that held only this board is answered whole
  const r = (RVW.st && RVW.st.reviews || []).find((x) => x.id === RVW.review);
  if (!r && RVW.review) rvwReviewClose();
}

function rvwReviewOpen(id) {
  RVW.review = id;
  RVW.reply = null;
  rvwReviewDraw();
  show('wt-review');
}

function rvwReviewDraw() {
  const r = (RVW.st && RVW.st.reviews || []).find((x) => x.id === RVW.review);
  if (!r) return;
  $('wt-rv-kicker').textContent = `${r.case || t('review.gets_board')} · ${rvwWhen(r.sent)}`;
  $('wt-rv-title').textContent = t('review.page.title', { who: r.from });
  $('wt-rv-asked').textContent = r.asked ? t('review.page.you_asked', { line: r.asked }) : '';
  $('wt-rv-asked').hidden = !r.asked;
  const threads = r.items.map((id) => (RVW.st.threads || []).find((th) => th.id === id)).filter(Boolean);
  const list = $('wt-rv-list');
  const typing = list.contains(document.activeElement) && /TEXTAREA/.test(document.activeElement.tagName);
  if (typing) return;
  list.innerHTML = threads.map((th) => rvwThreadHtml(th, true)).join('') + (r.suggestions || []).map(rvwSuggestItem).join('')
    + (r.boards || []).map(rvwBoardHtml).join('');
}

function rvwReviewClose() {
  RVW.review = null;
  RVW.reply = null;
  RVW.decline = null;
  hide('wt-review');
}

async function rvwDone() {
  const id = RVW.review;
  if (!id || RVW.busy) return;
  // a review holding only a board has nothing to mark read: the board waits on the line until it is answered
  if (id.startsWith('board-')) { rvwReviewClose(); return; }
  RVW.busy = true;
  try {
    await rvwCall(Object.assign({ op: 'done', review: id }, rvwBody()));
    rvwReviewClose();
  } catch (err) {
    say(err.message, 9000);
  } finally {
    RVW.busy = false;
    rvwTick();
  }
}

async function rvwThreadAct(op, tid, extra = {}) {
  if (RVW.busy) return;
  RVW.busy = true;
  try {
    await rvwCall(Object.assign({ op, thread: tid }, rvwBody(), extra));
    RVW.reply = null;
  } catch (err) {
    say(err.message, 9000);
  } finally {
    RVW.busy = false;
    await rvwTick();
  }
}

/* every press inside the comments' boxes, the card's, the passage's and the canvas's */
function rvwClick(e) {
  const b = e.target.closest('[data-wt], [data-wt-line], [data-wt-sline]');
  if (!b) return;
  if (b.dataset.wtLine !== undefined) { rvwCommentStatement(Number(b.dataset.wtLine)); return; }
  if (b.dataset.wtSline !== undefined) { rvwCommentStatement(Number(b.dataset.wtSline), true); return; }
  const act = b.dataset.wt;
  if (act === 'cancel') rvwEditorClose();
  else if (act === 'add') rvwAdd();
  else if (act === 'reply') { RVW.reply = b.dataset.thread; rvwDraw(); rvwReviewDraw(); const box = $('wt-reply'); if (box) box.focus(); }
  else if (act === 'reply-cancel') { RVW.reply = null; if (document.activeElement) document.activeElement.blur(); rvwEsDraw(); rvwReviewDraw(); }
  else if (act === 'reply-send') {
    const text = ($('wt-reply') || {}).value || '';
    if (!text.trim()) { $('wt-reply').focus(); return; }
    if (document.activeElement) document.activeElement.blur();
    rvwThreadAct('reply', b.dataset.thread, { text });
  } else if (act === 'resolve') rvwThreadAct('thread', b.dataset.thread, { state: 'resolved' });
  else if (act === 'board-yes') rvwBoardAnswer(b.dataset.ref, true);
  else if (act === 'board-no') rvwBoardAnswer(b.dataset.ref, false);
  else if (act === 'reopen') rvwThreadAct('thread', b.dataset.thread, { state: 'reopened' });
  else if (act === 's-yes') rvwSuggestAnswer(b.dataset.sid, true);
  else if (act === 's-decline') { RVW.decline = b.dataset.sid; rvwReviewDraw(); const box = $('wt-no-why'); if (box) box.focus(); }
  else if (act === 'no-cancel') { RVW.decline = null; if (document.activeElement) document.activeElement.blur(); rvwReviewDraw(); }
  else if (act === 's-no') {
    const reason = ($('wt-no-why') || {}).value || '';
    if (document.activeElement) document.activeElement.blur();
    rvwSuggestAnswer(b.dataset.sid, false, reason.trim());
  }
}

/* Esc: the editor or the reply box first, then the review card, kept unread */
function rvwKeys(e) {
  if (e.key !== 'Escape') return false;
  if (RVW.reply && document.activeElement && document.activeElement.id === 'wt-reply') {
    e.preventDefault(); RVW.reply = null; document.activeElement.blur(); rvwEsDraw(); rvwReviewDraw(); return true;
  }
  if (RVW.decline && document.activeElement && document.activeElement.id === 'wt-no-why') {
    e.preventDefault(); RVW.decline = null; document.activeElement.blur(); rvwReviewDraw(); return true;
  }
  if ($('wt-review') && !$('wt-review').hidden) { e.preventDefault(); rvwReviewClose(); return true; }
  if ($('wt-ask') && !$('wt-ask').hidden) { e.preventDefault(); hide('wt-ask'); return true; }
  if (RVW.editor) { e.preventDefault(); rvwEditorClose(); return true; }
  return false;
}

function rvwBoot() {
  if (!$('wt-line')) return;
  $('wt-ask-cancel').onclick = () => hide('wt-ask');
  $('wt-ask-go').onclick = () => rvwAskGo();
  $('wt-ask-who').addEventListener('change', rvwAskLabel);
  $('wt-tray-send').onclick = () => rvwSend();
  $('wt-line-review').onclick = () => rvwReviewOpen($('wt-line').dataset.review);
  $('wt-rv-close').onclick = () => rvwReviewClose();
  $('wt-rv-done').onclick = () => rvwDone();
  $('wt-rv-list').addEventListener('click', rvwClick);
  $('wt-es').addEventListener('click', rvwClick);
  $('pairs').addEventListener('click', rvwClick);
  if ($('sel-wtcomment')) $('sel-wtcomment').onclick = () => rvwCommentPassage();
  window.addEventListener('focus', () => rvwTick());
  document.addEventListener('contextmenu', (e) => { RVW.at = { x: e.clientX, y: e.clientY }; }, true);
  window.addEventListener('resize', () => rvwDraw());
  setInterval(rvwTick, RVW_EVERY);
  rvwTick();
}

if (typeof document !== 'undefined' && document.readyState !== 'loading') rvwBoot();
else if (typeof document !== 'undefined') document.addEventListener('DOMContentLoaded', rvwBoot);
