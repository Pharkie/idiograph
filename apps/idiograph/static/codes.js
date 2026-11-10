/* The code list (codes, 2 November 2026, Adam's choice of the drawings on 2 November: the code list as its own
   tab between Coding and Themes, shot 08, Merge as shot 09, a code with no extracts and the row's menu as shot 10).

   A thematic analysis project's codes, each a label many extracts share, each extract still one quote. The list
   on the left, sorted by name, with its extracts and participants counted, and the open code on the right with
   Rename, Merge into another code, Delete this code for a code with no extracts, its description and its
   extracts by participant, each with Go to the passage. Every change goes through /api/codes-ops with the same
   operations an agent's command line sends (codes.py on the server), and the list is drawn again from the
   answer. A rename and a merge reach every workbook and every board, all or nothing, and each change is one step
   of the list's undo, Cmd + Z on this screen and the Undo beside the list. Nothing is kept in the browser. */

const CD = { path: '', back: null, to: 'statements', data: null, ask: 0, busy: false, open: null, project: null,
  find: '', menu: null, merging: null };

const cdNorm = (s) => String(s || '').split(/\s+/).filter(Boolean).join(' ').toLowerCase();
const cdCode = (id) => ((CD.data && CD.data.codes) || []).find((c) => c.id === id) || null;
const cdWho = (cs) => ((CD.data && CD.data.participants) || []).find((p) => p.case === cs) || null;

/* the list opened for the project a workbook belongs to, `how` as trajOpen takes it */
async function codesOpen(path, how = {}) {
  const ask = ++CD.ask;
  let data;
  try {
    data = await api('/api/codes', { workbook: path });
  } catch (err) {
    if (ask !== CD.ask) return false;
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    return false;
  }
  if (ask !== CD.ask) return false;
  if (how.leave) how.leave();
  CD.path = path;
  CD.back = how.back || null;
  CD.to = how.to || 'statements';
  if (how.open) CD.open = how.open;
  $('codes-screen').hidden = false;
  codesLoad(data);
  return true;
}

function codesLoad(data) {
  CD.data = data;
  CD.project = data.project || null;
  tMethod('ta');
  pathProjectDraw('cd-project', CD.project);
  dsTabsDraw('cd-steps', CD.project, 'codes');
  const question = CD.project && CD.project.research_question;
  $('cd-band').classList.toggle('band-unasked', !question);
  $('cd-band-question').textContent = question || '';
  $('cd-feedback').hidden = !data.feedback;
  if (!cdCode(CD.open)) CD.open = ((data.codes || [])[0] || {}).id || null;
  codesDraw();
}

/* ── drawing ── */

function codesShown() {
  const find = cdNorm(CD.find);
  const all = (CD.data && CD.data.codes) || [];
  if (!find) return all;
  return all.filter((c) => find.split(' ').every((w) => cdNorm(`${c.name} ${c.description}`).includes(w)));
}

function codesDraw() {
  const d = CD.data;
  if (!d) return;
  const total = d.total || { codes: 0, extracts: 0, participants: 0 };
  $('cd-total').textContent = t('codes.total', { codes: t('codes.n.codes', { n: total.codes }), extracts: t('codes.n.extracts', { n: total.extracts }) });
  const shown = codesShown();
  let html = '';
  for (const c of shown) {
    const on = c.id === CD.open;
    html += `<li class="cd-row${on ? ' on' : ''}${c.extracts ? '' : ' none'}" role="option" aria-selected="${on}" tabindex="${on ? 0 : -1}" data-code="${escAttr(c.id)}">`
      // the counts in their columns, and under the name where the window is too narrow for the columns
      + `<span class="cd-row-name">${esc(c.name)}<span class="cd-row-sub">${esc(c.extracts ? t('codes.counts', {
        extracts: t('codes.n.extracts', { n: c.extracts }), participants: t('codes.n.participants', { n: c.participants }) }) : t('codes.no_extracts'))}</span></span>`
      + `<span class="cd-row-n">${c.extracts}</span><span class="cd-row-n">${c.participants}</span>`
      + `<button type="button" class="cd-row-more" tabindex="-1" data-more="${escAttr(c.id)}" aria-haspopup="menu" `
      + `aria-label="${escAttr(t('codes.menu_label', { name: c.name }))}" title="${escAttr(t('codes.menu_label', { name: c.name }))}">&#8943;</button></li>`;
  }
  if (!shown.length) html = `<li class="cd-row-empty">${esc((d.codes || []).length ? t('codes.none_found') : t('codes.empty'))}</li>`;
  $('cd-rows').innerHTML = html;
  codesOpenDraw();
  // the counts at the left, and Undo and Redo at the right while the list has a change to put back or make again
  const step = (act, what, word) => (what ? `<button type="button" class="ghost small cd-step" data-step="${act}" title="${escAttr(what)}">${esc(word)}</button>` : '');
  $('cd-status').innerHTML = [t('codes.n.codes', { n: total.codes }), t('codes.n.extracts', { n: total.extracts }),
    t('codes.n.participants', { n: total.participants })].map((x) => `<span class="cd-count">${esc(x)}</span>`).join('')
    + `<span class="cd-grow"></span>${step('undo', d.undo, t('codes.undo'))}${step('redo', d.redo, t('codes.redo'))}`;
}

function cdBadge(cs) {
  const p = cdWho(cs);
  const colour = p ? (Number(p.colour) || 0) % 25 : 0;
  return `<span class="gt-badge case-${colour} cd-badge" aria-hidden="true">${esc((p && p.badge) || whoName(cs).slice(0, 1))}</span>`;
}

function codesOpenDraw() {
  const c = cdCode(CD.open);
  const box = $('cd-open');
  if (!c) { box.innerHTML = ''; return; }
  const counts = c.extracts ? t('codes.counts', { extracts: t('codes.n.extracts', { n: c.extracts }), participants: t('codes.n.participants', { n: c.participants }) })
    : t('codes.no_extracts');
  let html = `<p class="kicker cd-kicker">${esc(t('codes.kicker'))}</p>`
    + `<h2 class="cd-name" id="cd-name">${esc(c.name)}</h2>`
    + `<p class="cd-counts">${esc(counts)}</p>`
    + '<div class="cd-acts">'
    + `<button type="button" class="ghost small" data-act="rename">${esc(t('codes.rename'))}</button>`
    + `<button type="button" class="ghost small" data-act="merge"${(CD.data.codes || []).length < 2 ? ' disabled' : ''}>${esc(t('codes.merge'))}</button>`
    + (c.extracts ? '' : `<button type="button" class="ghost small" data-act="delete">${esc(t('codes.delete'))}</button>`)
    + '</div>'
    + `<label class="field-label cd-desc-label" for="cd-desc">${esc(t('codes.description'))}</label>`
    + `<textarea class="cd-desc" id="cd-desc" rows="1" maxlength="2000" spellcheck="true">${esc(c.description || '')}</textarea>`;
  if (!c.extracts) html += `<p class="cd-none">${esc(t('codes.none_yet'))}</p>`;
  for (const by of c.by || []) {
    html += `<section class="cd-who"><h3 class="cd-who-head">${cdBadge(by.case)}<span>${esc(by.who)}</span>`
      + `<span class="cd-who-n">${esc(t('codes.n.extracts', { n: by.extracts.length }))}</span></h3><ul class="cd-xs">`;
    by.extracts.forEach((x, i) => {
      html += `<li class="cd-x"><span class="th-time cd-time">${esc(x.time || '')}</span><span class="cd-q">${esc(x.quote)}</span>`
        + `<button type="button" class="ghost small cd-go" data-go="${escAttr(by.case)}" data-i="${i}">${esc(t('codes.go'))}</button></li>`;
    });
    html += '</ul></section>';
  }
  box.innerHTML = html;
  cdDescFit();
}

function cdDescFit() {
  const el = $('cd-desc');
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${el.scrollHeight + 2}px`;
}

/* ── changes, each through the list's operations ── */

async function codesOps(ops) {
  if (!ops.length || CD.busy) return null;
  CD.busy = true;
  $('cd-save').hidden = false;
  $('cd-save').textContent = t('codes.saving');
  try {
    const data = await api('/api/codes-ops', { workbook: CD.path, ops, v: CD.data && CD.data.v });
    codesLoad(data);
    $('cd-save').hidden = true;
    if ((data.changes || []).length) say(data.changes.join(' '), 5000);
    return data;
  } catch (err) {
    $('cd-save').hidden = true;
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
    // a list changed since this screen read it is drawn again as it is now
    if (err.data && err.data.stale) await codesReload();
    else codesDraw();
    return null;
  } finally {
    CD.busy = false;
  }
}

async function codesReload() {
  try { codesLoad(await api('/api/codes', { workbook: CD.path })); } catch (err) { say(err.message, 9000); }
}

/* Undo and Redo on this screen, the list's last change put back or made again, every file it wrote */
async function codesUndo(redo) {
  if (CD.busy) return;
  CD.busy = true;
  try {
    const data = await api('/api/codes-undo', { workbook: CD.path, redo: !!redo });
    codesLoad(data);
    say((data.changes || []).join(' '), 5000);
  } catch (err) {
    say(needsRestart(err) ? RESTART_LINE : err.message, 9000);
  } finally {
    CD.busy = false;
  }
}

/* Rename: the name becomes a field in place, Enter keeps it, Escape leaves it */
function codesRename(id) {
  const c = cdCode(id);
  if (!c) return;
  if (CD.open !== id) { CD.open = id; codesDraw(); }
  const h = $('cd-name');
  if (!h) return;
  h.innerHTML = `<input class="cd-name-field" id="cd-name-field" type="text" maxlength="200" aria-label="${escAttr(t('codes.rename_label'))}" value="${escAttr(c.name)}">`;
  const input = $('cd-name-field');
  let done = false;
  const finish = (keep) => {
    if (done) return;
    done = true;
    const name = input.value.split(/\s+/).filter(Boolean).join(' ');
    if (keep && name && name !== c.name) codesOps([{ op: 'rename', code: c.id, name }]);
    else codesOpenDraw();
  };
  input.onkeydown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); finish(true); } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); finish(false); }
  };
  input.onblur = () => finish(true);
  input.focus();
  input.select();
}

/* New code: a field at the head of the list, its name added on Enter */
function codesNew() {
  const tools = document.querySelector('.cd-tools');
  if (!tools || $('cd-new-field')) return;
  const box = document.createElement('div');
  box.className = 'cd-new-box';
  box.innerHTML = `<input class="cd-find cd-new-field" id="cd-new-field" type="text" maxlength="200" aria-label="${escAttr(t('codes.new_label'))}">`;
  tools.after(box);
  const input = $('cd-new-field');
  let done = false;
  const finish = async (keep) => {
    if (done) return;
    done = true;
    const name = input.value.split(/\s+/).filter(Boolean).join(' ');
    box.remove();
    if (keep && name) {
      const made = await codesOps([{ op: 'new', name }]);
      const c = made && (made.codes || []).find((x) => cdNorm(x.name) === cdNorm(name));
      if (c) { CD.open = c.id; codesDraw(); }
    }
  };
  input.onkeydown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); finish(true); } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); finish(false); }
  };
  input.onblur = () => finish(true);
  input.focus();
}

/* Merge two codes: the other code chosen, the line under it saying what the merge will do before it is done */
function codesMerge(id) {
  const c = cdCode(id);
  const others = ((CD.data && CD.data.codes) || []).filter((x) => x.id !== id);
  if (!c || !others.length) return;
  CD.merging = id;
  $('cd-merge-line').textContent = t('codes.merge_line', { code: c.name, extracts: t('codes.n.extracts', { n: c.extracts }) });
  $('cd-merge-into').innerHTML = others.map((x) => `<option value="${escAttr(x.id)}">${esc(x.name)}</option>`).join('');
  codesMergeSaid();
  $('cd-merge').hidden = false;
  $('cd-merge-into').focus();
}

/* what a merge will do: the extracts and participants the kept code will have, an extract both had counted once */
function codesMergeSaid() {
  const a = cdCode(CD.merging);
  const b = cdCode($('cd-merge-into').value);
  if (!a || !b) return;
  const places = new Map();
  for (const c of [a, b]) for (const by of c.by || []) for (const x of by.extracts) places.set(`${by.case}|${x.sheet}|${x.row}|${x.quote}`, by.case);
  // an extract both codes have is kept once, which the line says, so the count adds up
  const both = a.extracts + b.extracts - places.size;
  $('cd-merge-will').textContent = t('codes.merge_will', { into: b.name, code: a.name,
    extracts: t('codes.n.extracts', { n: places.size }), participants: t('codes.n.participants', { n: new Set(places.values()).size }) })
    + (both > 0 ? ` ${t('codes.merge_both', { n: both })}` : '');
}

function codesMergeShut() {
  $('cd-merge').hidden = true;
  CD.merging = null;
}

async function codesMergeGo() {
  const id = CD.merging;
  const into = $('cd-merge-into').value;
  codesMergeShut();
  if (!id || !into) return;
  const done = await codesOps([{ op: 'merge', code: id, into }]);
  if (done) { CD.open = into; codesDraw(); }
}

async function codesDelete(id) {
  const c = cdCode(id);
  if (!c || c.extracts) return;
  const at = codesShown().findIndex((x) => x.id === id);
  const done = await codesOps([{ op: 'delete', code: id }]);
  if (done) {
    const left = codesShown();
    CD.open = (left[Math.min(at, left.length - 1)] || {}).id || null;
    codesDraw();
  }
}

/* the row's menu: Rename, Merge into another code, and Delete this code for a code with no extracts */
function codesMenu(id, anchor) {
  const menu = $('cd-menu');
  const c = cdCode(id);
  if (!c || !anchor) { menu.hidden = true; CD.menu = null; return; }
  CD.menu = id;
  menu.innerHTML = `<button type="button" class="ghost" role="menuitem" data-act="rename">${esc(t('codes.rename'))}</button>`
    + `<button type="button" class="ghost" role="menuitem" data-act="merge"${(CD.data.codes || []).length < 2 ? ' disabled' : ''}>${esc(t('codes.merge'))}</button>`
    + (c.extracts ? '' : `<span class="cd-menu-rule" aria-hidden="true"></span><button type="button" class="ghost" role="menuitem" data-act="delete">${esc(t('codes.delete'))}</button>`);
  menu.hidden = false;
  const box = anchor.getBoundingClientRect();
  const host = $('codes-screen').getBoundingClientRect();
  menu.style.left = `${Math.max(8, Math.min(box.left - host.left - 8, host.width - menu.offsetWidth - 8))}px`;
  menu.style.top = `${box.bottom - host.top + 4}px`;
  const first = menu.querySelector('button:not(:disabled)');
  if (first) first.focus();
}

function codesAct(act, id) {
  codesMenu(null);
  if (act === 'rename') codesRename(id);
  else if (act === 'merge') codesMerge(id);
  else if (act === 'delete') codesDelete(id);
}

/* Go to the passage: the participant's passage opened on the Coding screen, the way back this list */
async function codesGo(cs, i) {
  const c = cdCode(CD.open);
  const by = c && (c.by || []).find((b) => b.case === cs);
  const x = by && by.extracts[i];
  const p = cdWho(cs);
  if (!x || !p) return;
  const open = CD.open;
  const back = () => codesOpen(x.workbook || p.path, { back: CD.back, to: CD.to, open });
  const leave = () => { $('codes-screen').hidden = true; CD.ask += 1; };
  await navGo(() => codesGo(cs, i), () => openPassage(x.workbook || p.path, { sheet: x.sheet, row: x.row, line: x.line },
    { leave, back, to: 'codes' }));
}

/* ── the way out ── */

async function codesIdle() {
  const el = document.activeElement;
  if (el && $('codes-screen').contains(el) && el.blur) el.blur();
  for (let i = 0; CD.busy && i < 50; i += 1) await new Promise((r) => setTimeout(r, 40));
}

async function codesLeave() {
  await codesIdle();
  $('codes-screen').hidden = true;
  CD.ask += 1;
  if (CD.back) await CD.back();
  else loadLibrary().catch((err) => say(err.message, 9000));
  return true;
}

async function codesHome() {
  await codesIdle();
  $('codes-screen').hidden = true;
  CD.ask += 1;
  S.backTo = null;
  if (typeof homeKeep === 'function') homeKeep('');
  try { await loadLibrary(); } catch (err) { say(err.message, 9000); }
  window.scrollTo(0, 0);
}

/* a tab of the bar: the participant's Coding screen, or the Themes board, or the way back where it goes there */
async function codesStep(step) {
  if (step === 'codes') return;
  if (step === CD.to && CD.back) { if (typeof navBackNow === 'function' && navBackNow()) return; await codesLeave(); return; }
  await codesIdle();
  const path = CD.path;
  const kept = { back: CD.back, to: CD.to, open: CD.open };
  const again = () => codesOpen(path, kept);
  const leave = () => { $('codes-screen').hidden = true; CD.ask += 1; };
  if (step === 'statements') {
    await navGo(() => codesStep(step), () => openStatements(path, { leave, back: again, to: 'codes' }));
    return;
  }
  leave();
  await navGo(() => codesStep(step), () => getsOpen(path, { back: again, label: '', to: 'codes' }));
}

function codesWire() {
  $('cd-home').onclick = () => codesHome();
  $('cd-feedback').onclick = () => openFeedback('gets');
  $('cd-settings').onclick = () => openSettings('pets');
  for (const [id, step] of [['cd-step-es', 'statements'], ['cd-step-codes', 'codes'], ['cd-step-gets', 'gets']]) {
    $(id).onclick = () => codesStep(step);
  }
  dsTabsWatch('cd-steps');
  $('cd-find').addEventListener('input', () => { CD.find = $('cd-find').value; codesDraw(); });
  $('cd-status').addEventListener('click', (e) => {
    const b = e.target.closest('[data-step]');
    if (b) codesUndo(b.dataset.step === 'redo');
  });
  $('cd-new').onclick = () => codesNew();
  const rows = $('cd-rows');
  rows.addEventListener('click', (e) => {
    const more = e.target.closest('[data-more]');
    if (more) { e.stopPropagation(); codesMenu(CD.menu === more.dataset.more ? null : more.dataset.more, more); return; }
    const row = e.target.closest('.cd-row');
    if (row) { CD.open = row.dataset.code; codesDraw(); row.focus && $('cd-rows').querySelector('.cd-row.on').focus(); }
  });
  rows.addEventListener('keydown', (e) => {
    const list = codesShown();
    const at = list.findIndex((c) => c.id === CD.open);
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const to = list[Math.max(0, Math.min(list.length - 1, at + (e.key === 'ArrowDown' ? 1 : -1)))];
      if (to) { CD.open = to.id; codesDraw(); const on = rows.querySelector('.cd-row.on'); if (on) { on.focus(); on.scrollIntoView({ block: 'nearest' }); } }
    } else if (e.key === 'F2' || (e.key === 'Enter' && !MOD(e))) {
      e.preventDefault();
      if (CD.open) codesRename(CD.open);
    }
  });
  $('cd-open').addEventListener('click', (e) => {
    const act = e.target.closest('[data-act]');
    if (act && !act.disabled) { codesAct(act.dataset.act, CD.open); return; }
    const go = e.target.closest('[data-go]');
    if (go) codesGo(go.dataset.go, Number(go.dataset.i));
  });
  $('cd-open').addEventListener('input', (e) => { if (e.target.id === 'cd-desc') cdDescFit(); });
  $('cd-open').addEventListener('focusout', (e) => {
    if (e.target.id !== 'cd-desc') return;
    const c = cdCode(CD.open);
    const text = e.target.value.trim();
    if (c && text !== (c.description || '')) codesOps([{ op: 'describe', code: c.id, description: text }]);
  });
  $('cd-menu').addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]');
    if (b && !b.disabled) codesAct(b.dataset.act, CD.menu);
  });
  $('cd-menu').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.stopPropagation(); const id = CD.menu; codesMenu(null); const row = rows.querySelector(`[data-code="${CSS.escape(id || '')}"]`); if (row) row.focus(); }
  });
  document.addEventListener('click', (e) => {
    if (!$('cd-menu').hidden && !e.target.closest('#cd-menu') && !e.target.closest('[data-more]')) codesMenu(null);
  });
  $('cd-merge-into').addEventListener('change', codesMergeSaid);
  $('cd-merge-cancel').onclick = () => codesMergeShut();
  $('cd-merge-go').onclick = () => codesMergeGo();
  $('cd-merge').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); codesMergeShut(); }
  });
  // Cmd + Z and Shift + Cmd + Z on this screen, the list's own undo, never inside a field
  document.addEventListener('keydown', (e) => {
    if ($('codes-screen').hidden || !$('cd-merge').hidden || !MOD(e) || e.altKey || (e.key !== 'z' && e.key !== 'Z')) return;
    const el = document.activeElement;
    if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) return;
    e.preventDefault();
    codesUndo(e.shiftKey);
  });
  // the Coding screen's quick keys on the selection's toolbar (quickkeysB)
  cxQuickWire();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', codesWire);
else codesWire();

/* ───────────────────────────────── coding: each extract a box, its codes as chips (coding A) ── */

/* On the Coding screen of a thematic analysis project (Adam's choice of the drawings, shots 02 and 05): each
   extract of the passage one box, numbered as the passage numbers it, its codes as chips under it, the x on a
   chip taking the code off, and Add a code with the project's codes suggested as he types, each with its extracts
   and participants counted, or New code "..." for a name the list lacks. The passage's pairs stay what the page
   saves, a code on an extract a statement with the extract as its quote, so two codes on one extract are two
   pairs with the same quote: the boxes are drawn over them (`cxDraw`, after every change to the pairs) and every
   act changes them, one step of undo each. */

const CX = { codes: [], path: '', ask: 0, ai: new Map(), aiRow: '', aiAsk: 0, recent: [], used: [] };

const cxOn = () => typeof tMethodNow === 'function' && tMethodNow() === 'ta' && !!S.data;
const cxWords = (s) => String(s || '').split(/\s+/).filter(Boolean).join(' ');

/* the project's codes for the suggestions, asked for as a passage opens and after each save */
async function cxCodesRead(path) {
  if (!path) return;
  const ask = ++CX.ask;
  const asked = Date.now();
  try {
    const data = await api('/api/codes', { workbook: path });
    if (ask !== CX.ask) return;
    CX.codes = data.codes || [];
    CX.path = path;
    // the codes used last as the project keeps them, and those put on here since the read was asked first (quickkeysB)
    CX.recent = Array.isArray(data.recent) ? data.recent : [];
    CX.used = CX.used.filter((u) => u.at > asked);
    if (typeof selBarOn === 'function' && selBarOn()) cxQuickBar();
  } catch { /* the suggestions wait for the next read */ }
}

/* the passage's extracts in the order they first stand among its pairs, each with its pairs' elements */
function cxExtracts() {
  const out = [];
  const by = new Map();
  pairEls().forEach((el) => {
    const p = pairOf(el);
    const quote = cxWords(p.kq);
    if (!quote && !cxWords(p.es)) return;
    const key = quote || `\u0000${el.dataset.pid}`;
    if (!by.has(key)) { by.set(key, { quote: p.kq, words: quote, els: [] }); out.push(by.get(key)); }
    by.get(key).els.push(el);
  });
  return out;
}

/* each pair's extract by its place among the passage's extracts, the first one standing first, from a passage's
   pairs as the page holds them, for the passage's marks and numbers */
function cxPlaces(pairs) {
  const seen = new Map();
  return (pairs || []).map((p, n) => {
    // an empty pair, the one a passage with none opens with, is no extract (as cxExtracts reads them)
    if (!cxWords(p.kq) && !cxWords(p.es)) return -1;
    const key = cxWords(p.kq) || `\u0000${n}`;
    if (!seen.has(key)) seen.set(key, seen.size);
    return seen.get(key);
  });
}

function cxDraw() {
  const card = $('es-card');
  const on = cxOn();
  card.classList.toggle('ta-codes', on);
  let list = $('cx-list');
  if (!on) { if (list) list.remove(); return; }
  if (!list) {
    list = document.createElement('div');
    list.id = 'cx-list';
    list.className = 'cx-list';
    $('pairs').after(list);
    cxWire(list);
  }
  const active = document.activeElement;
  const held = active && list.contains(active) && active.classList.contains('cx-field')
    ? { at: Number(active.dataset.x), value: active.value } : null;
  const ai = cxAiOn();
  cxAiFresh();
  list.innerHTML = cxExtracts().map((x, i) => {
    const chips = x.els.filter((el) => cxWords(pairOf(el).es)).map((el) => {
      const name = cxWords(pairOf(el).es);
      return `<span class="cx-chip"><span class="cx-chip-name">${esc(name)}</span><button type="button" class="cx-chip-x" data-off="${escAttr(el.dataset.pid)}"`
        + ` aria-label="${escAttr(t('codes.take_off', { name }))}" title="${escAttr(t('codes.take_off', { name }))}">&#215;</button></span>`;
    }).join('');
    return `<div class="cx" data-x="${i}" data-es-colour="${i % 6}"><span class="pair-num cx-num" aria-hidden="true">${i + 1}</span><div class="cx-body">`
      + `<span class="field-label cx-label">${esc(t('codes.extract'))}</span>`
      + `<p class="cx-quote">${esc(x.quote || '')}</p>`
      // AI suggest beside the extract's Codes, with AI features on in a thematic analysis project (taaibuild)
      + (ai ? `<div class="cx-codes-row"><span class="field-label cx-codes-label">${esc(t('codes.codes'))}</span>${cxAiButton(x, i)}</div>`
        : `<span class="field-label cx-codes-label">${esc(t('codes.codes'))}</span>`)
      + `<div class="cx-chips">${chips}</div>`
      + `<div class="cx-add"><input type="text" class="cx-field" id="cx-f-${i}" data-x="${i}" placeholder="${escAttr(t('codes.add'))}" aria-label="${escAttr(t('codes.add'))}"`
      + ' autocomplete="off" spellcheck="false" maxlength="200" role="combobox" aria-expanded="false" aria-autocomplete="list">'
      + `<ul class="cx-sugg" role="listbox" hidden></ul></div>${ai ? cxAiHtml(x, i) : ''}</div></div>`;
  }).join('');
  if (held) {
    const field = list.querySelector(`.cx-field[data-x="${held.at}"]`);
    if (field) { field.value = held.value; field.focus(); }
  }
}

/* ── AI suggest on an extract's codes (taaibuild, 3 November 2026, Adam's Coding A, taai's shot 02) ──

   With AI features on, and the Experiential statements' switch, in a thematic analysis project: AI suggest beside
   the extract's Codes asks for codes for that extract alone, and the answer stands under Add a code in the list Add
   a code shows as he types, the project's codes that fit first with their counts, then New code "..." for a name
   none holds. Each is a click to take, which does what Add a code does with that name, one step of undo, and the
   code taken is an ordinary code with no mark of the AI. Nothing is written until then, nothing of it is kept, and
   the next passage starts with none. */

const CX_SPARK = '<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 3.2c.95 4.2 2.65 5.9 6.85 6.85-4.2.95-5.9 2.65-6.85 6.85-.95-4.2-2.65-5.9-6.85-6.85C9.35 9.1 11.05 7.4 12 3.2Z"/><path d="M18.4 14.6c.42 1.85 1.17 2.6 3.02 3.02-1.85.42-2.6 1.17-3.02 3.02-.42-1.85-1.17-2.6-3.02-3.02 1.85-.42 2.6-1.17 3.02-3.02Z"/></svg>';
const CX_CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M5 5l14 14M19 5L5 19"/></svg>';

const cxAiOn = () => cxOn() && typeof aiTaFor === 'function' && aiTaFor(S.data.config, 'statements');

/* the answers of the passage before set aside when another passage is in front */
function cxAiFresh() {
  const row = typeof current === 'function' ? current() : null;
  const key = row ? `${S.data && S.data.path}|${row.key}` : '';
  if (CX.aiRow === key) return;
  CX.aiRow = key;
  CX.ai = new Map();
}

function cxAiButton(x, i) {
  const held = CX.ai.get(x.words);
  return `<button type="button" class="ghost small cx-ai-ask${held ? ' on' : ''}" data-cx-ask="${i}" aria-pressed="${!!held}"`
    + `${held && held.busy ? ' disabled' : ''} title="${escAttr(t('codes.ai.tip'))}">`
    + `${CX_SPARK}${esc(t('codes.ai.go'))}</button>`;
}

/* a code's counts as Add a code's list gives them, from the list as it stands now, else as the answer gave them */
function cxAiCounts(c) {
  const now = CX.codes.find((k) => cdNorm(k.name) === cdNorm(c.name)) || c;
  return now.extracts
    ? t('codes.counts', { extracts: t('codes.n.extracts', { n: now.extracts }), participants: t('codes.n.participants', { n: now.participants }) })
    : t('codes.no_extracts');
}

function cxAiHtml(x, i) {
  const held = CX.ai.get(x.words);
  if (!held) return '';
  const here = new Set(x.els.map((el) => cdNorm(pairOf(el).es)));
  let body;
  if (held.busy) body = `<p class="cx-ai-note">${esc(t('codes.ai.asking'))}</p>`;
  else if (held.said) body = `<p class="cx-ai-note failed">${esc(held.said)}</p>`;
  else {
    const old = held.existing.filter((c) => !here.has(cdNorm(c.name)));
    const fresh = held.fresh.filter((n) => !here.has(cdNorm(n)));
    const pick = (name, inner, isNew) => `<li><button type="button" class="cx-sugg-row cx-ai-pick" data-aix="${i}" data-pick="${escAttr(name)}"${isNew ? ' data-new="1"' : ''}>${inner}</button></li>`;
    const rows = old.map((c) => pick(c.name, `<span class="cx-sugg-name">${esc(c.name)}</span><span class="cx-sugg-n">${esc(cxAiCounts(c))}</span>`))
      .concat(old.length && fresh.length ? ['<li class="cx-sugg-rule" aria-hidden="true"></li>'] : [])
      .concat(fresh.map((n) => pick(n, `<span class="cx-sugg-new">${esc(t('codes.add_new', { name: n }))}</span>`, true)));
    body = rows.length ? `<ul class="cx-sugg cx-ai-list">${rows.join('')}</ul>`
      : `<p class="cx-ai-note">${esc(held.existing.length || held.fresh.length ? t('codes.ai.all_taken') : t('codes.ai.none'))}</p>`;
  }
  return `<div class="cx-ai" data-x="${i}"><div class="cx-ai-head"><span class="field-label">${esc(t('codes.ai.head'))}</span>`
    + `<button type="button" class="ai-close cx-ai-close" data-cx-ai-close="${i}" aria-label="${escAttr(t('codes.ai.close'))}" title="${escAttr(t('codes.ai.close'))}">${CX_CLOSE}</button></div>`
    + `${body}</div>`;
}

/* AI suggest: the passage, the interviewer's before it, the extract and the codes on it go in one call, and the
   answer stands under the extract's Add a code. A second press while it is open puts it away. */
async function cxAiAsk(xi) {
  const row = current();
  const x = cxExtracts()[xi];
  if (!row || !x || !cxAiOn()) return;
  const held = CX.ai.get(x.words);
  if (held && held.busy) return;
  if (held) { CX.ai.delete(x.words); cxDraw(); return; }
  const ask = ++CX.aiAsk;
  const passage = CX.aiRow;
  CX.ai.set(x.words, { busy: true, ask });
  cxDraw();
  const before = S.flat[row.i - 1];
  const on = x.els.map((el) => cxWords(pairOf(el).es)).filter(Boolean);
  let data = null;
  let said = '';
  try {
    data = await api('/api/codes-suggest', { workbook: S.data.path, turn: row.text, prior: before ? before.text : '',
      time: row.time, name: row.name, quote: x.quote, on });
  } catch (err) {
    said = needsRestart(err) ? RESTART_LINE : err.message;
  }
  const now = CX.ai.get(x.words);
  if (CX.aiRow !== passage || !now || now.ask !== ask) return;
  if (!said && (!data || !Array.isArray(data.existing))) said = RESTART_LINE;
  CX.ai.set(x.words, said ? { said } : { existing: data.existing, fresh: Array.isArray(data.new) ? data.new : [] });
  cxDraw();
}

/* the suggestions under a field: the project's codes holding what he typed, those on this extract left out, the
   matched words in bold, each with its counts, then New code "..." while no code has that name */
function cxSuggest(field) {
  const box = field.parentElement.querySelector('.cx-sugg');
  const x = cxExtracts()[Number(field.dataset.x)];
  const typed = cxWords(field.value);
  if (!x || !typed) { box.hidden = true; field.setAttribute('aria-expanded', 'false'); return; }
  const low = typed.toLowerCase();
  const here = new Set(x.els.map((el) => cdNorm(pairOf(el).es)));
  const found = CX.codes.filter((c) => !here.has(cdNorm(c.name)) && c.name.toLowerCase().includes(low)).slice(0, 4);
  const same = CX.codes.some((c) => cdNorm(c.name) === cdNorm(typed));
  const bold = (name) => {
    const at = name.toLowerCase().indexOf(low);
    return at < 0 ? esc(name) : `${esc(name.slice(0, at))}<b>${esc(name.slice(at, at + low.length))}</b>${esc(name.slice(at + low.length))}`;
  };
  let html = found.map((c, i) => `<li class="cx-sugg-row${i === 0 ? ' on' : ''}" role="option" data-pick="${escAttr(c.name)}">`
    + `<span class="cx-sugg-name">${bold(c.name)}</span><span class="cx-sugg-n">${esc(c.extracts
      ? t('codes.counts', { extracts: t('codes.n.extracts', { n: c.extracts }), participants: t('codes.n.participants', { n: c.participants }) })
      : t('codes.no_extracts'))}</span></li>`).join('');
  if (!same && !here.has(cdNorm(typed))) {
    html += `${found.length ? '<li class="cx-sugg-rule" aria-hidden="true"></li>' : ''}<li class="cx-sugg-row${found.length ? '' : ' on'}" role="option" data-pick="${escAttr(typed)}" data-new="1">`
      + `<span class="cx-sugg-new">${esc(t('codes.add_new', { name: typed }))}</span></li>`;
  }
  box.innerHTML = html;
  box.hidden = !html;
  field.setAttribute('aria-expanded', String(!!html));
  // the list whole in view, its last row clear of the screen's foot, the column moving no more than it takes
  if (html && box.scrollIntoView) box.scrollIntoView({ block: 'nearest' });
}

function cxMove(field, by) {
  const rows = [...field.parentElement.querySelectorAll('.cx-sugg-row')];
  if (!rows.length) return;
  const at = rows.findIndex((r) => r.classList.contains('on'));
  rows.forEach((r) => r.classList.remove('on'));
  rows[(at + by + rows.length) % rows.length].classList.add('on');
}

/* a code put on an extract: into its pair with no code when it has one, else a pair of its own after the last,
   one step of undo */
function cxPut(xi, given) {
  const row = current();
  const x = cxExtracts()[xi];
  let name = cxWords(given);
  if (!row || !x || !name) return;
  if (x.els.some((el) => cdNorm(pairOf(el).es) === cdNorm(name))) return;
  const kept = CX.codes.find((c) => cdNorm(c.name) === cdNorm(name));
  if (kept) name = kept.name;
  else CX.codes.push({ id: '', name, description: '', extracts: 0, participants: 0, by: [] });
  cxUsed(name);
  const bare = x.els.find((el) => !cxWords(pairOf(el).es));
  if (bare) {
    bare.querySelector('.pair-es').value = name;
    pairsChanged();
    undoPush({ key: row.key, what: 'the code', quote: x.quote, name,
      undo: (e) => cxSet(e, ''), redo: (e) => cxSet(e, e.name) });
  } else {
    insertPair({ es: name, kq: x.quote });
    pairsChanged();
    undoPush({ key: row.key, what: 'the code', quote: x.quote, name,
      undo: (e) => cxPairOut(e), redo: (e) => { insertPair({ es: e.name, kq: e.quote }); pairsChanged(); } });
  }
  cxFocus(xi);
}

/* the extract's pair with no code takes `name`, or its pair of `e.name` loses it, for undo and redo */
function cxSet(e, name) {
  const el = pairEls().find((p) => pairOf(p).kq === e.quote && (name ? !cxWords(pairOf(p).es) : cdNorm(pairOf(p).es) === cdNorm(e.name)));
  if (el) { el.querySelector('.pair-es').value = name; pairsChanged(); }
}

function cxPairOut(e) {
  const el = pairEls().find((p) => pairOf(p).kq === e.quote && cdNorm(pairOf(p).es) === cdNorm(e.name));
  if (!el) return;
  el.remove();
  if (!pairEls().length) insertPair({ es: '', kq: '' });
  pairsChanged();
}

/* the x on a chip: the code off the extract, and the extract kept with no code when it was its last */
function cxOff(pid) {
  const row = current();
  const el = pairEls().find((p) => p.dataset.pid === pid);
  if (!row || !el) return;
  const { es, kq } = pairOf(el);
  const xi = cxExtracts().findIndex((x) => x.els.includes(el));
  const others = pairEls().filter((p) => p !== el && pairOf(p).kq === kq && cxWords(pairOf(p).es));
  if (others.length) {
    removePair(el);
  } else {
    el.querySelector('.pair-es').value = '';
    pairsChanged();
    undoPush({ key: row.key, what: 'the code', quote: kq, name: es, undo: (e) => cxSet(e, e.name), redo: (e) => cxSet(e, '') });
  }
  cxFocus(xi);
}

function cxFocus(xi) {
  const field = $('cx-list') && $('cx-list').querySelector(`.cx-field[data-x="${xi}"]`);
  if (field) { field.value = ''; field.focus(); }
}

/* after Q or the arrow took the words as a new extract, its Add a code takes the caret */
function cxFocusPair(el) {
  const xi = cxExtracts().findIndex((x) => x.els.includes(el));
  if (xi >= 0) cxFocus(xi);
}

function cxWire(list) {
  list.addEventListener('input', (e) => {
    if (!e.target.classList.contains('cx-field')) return;
    S.lastInput[e.target.id] = Date.now();
    cxSuggest(e.target);
  });
  list.addEventListener('focusin', (e) => {
    if (!e.target.classList.contains('cx-field')) return;
    const x = cxExtracts()[Number(e.target.dataset.x)];
    // Q from here makes a new extract, never writing into this one
    if (x) S.pairFocus = x.els[0].dataset.pid;
  });
  list.addEventListener('focusout', (e) => {
    if (!e.target.classList.contains('cx-field')) return;
    setTimeout(() => {
      const box = e.target.parentElement && e.target.parentElement.querySelector('.cx-sugg');
      if (box && document.activeElement !== e.target) { box.hidden = true; e.target.setAttribute('aria-expanded', 'false'); }
    }, 120);
  });
  list.addEventListener('keydown', (e) => {
    const field = e.target.classList && e.target.classList.contains('cx-field') ? e.target : null;
    if (!field) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); e.stopPropagation(); cxMove(field, e.key === 'ArrowDown' ? 1 : -1); return; }
    if (e.key === 'Escape') {
      const box = field.parentElement.querySelector('.cx-sugg');
      if (!box.hidden) { e.preventDefault(); e.stopPropagation(); box.hidden = true; field.setAttribute('aria-expanded', 'false'); }
      return;
    }
    if (e.key === 'Enter' && !MOD(e)) {
      const on = field.parentElement.querySelector('.cx-sugg:not([hidden]) .cx-sugg-row.on');
      const name = on ? on.dataset.pick : cxWords(field.value);
      if (!name) return;
      e.preventDefault();
      e.stopPropagation();
      cxPut(Number(field.dataset.x), name);
    }
  });
  list.addEventListener('pointerdown', (e) => {
    const pick = e.target.closest('.cx-sugg-row');
    if (!pick || pick.classList.contains('cx-ai-pick')) return;
    e.preventDefault();
    const field = pick.closest('.cx-add').querySelector('.cx-field');
    cxPut(Number(field.dataset.x), pick.dataset.pick);
  });
  list.addEventListener('click', (e) => {
    const off = e.target.closest('[data-off]');
    if (off) { cxOff(off.dataset.off); return; }
    // AI suggest, its list put away, and a code of it taken as Add a code takes one (taaibuild)
    const ask = e.target.closest('[data-cx-ask]');
    if (ask) { cxAiAsk(Number(ask.dataset.cxAsk)); return; }
    const shut = e.target.closest('[data-cx-ai-close]');
    if (shut) {
      const x = cxExtracts()[Number(shut.dataset.cxAiClose)];
      if (x) { CX.ai.delete(x.words); cxDraw(); }
      return;
    }
    const take = e.target.closest('.cx-ai-pick');
    if (take) cxPut(Number(take.dataset.aix), take.dataset.pick);
  });
}

/* ─────────────────── the quick keys: R, V and 1 to 5 on words selected (quickkeysB, 9 November 2026) ──

   Adam's choice of option B with A's keys (9 November): with words selected in a thematic analysis project, the
   selection's toolbar gains In vivo code and a second line of the five codes used last in the project, the last one
   first, and the right-click menu lists the same with their keys. R puts the code used last on the words as a new
   extract, 1 to 5 that one of the five, V makes the words a code of their own, an in vivo code, and Q makes the
   extract with no code as ever. Plain keys, only while words are selected and no field has the caret. Each is one
   step of undo and goes to the workbook with the passage's save, which keeps the codes used last in the project's
   code list (codes.py, `note_used`), so they are there after a restart. An agent has the same as `codes apply-last`
   and `codes in-vivo`. IPA's statements screen keeps its keys and its toolbar as they are. */

const CX_RECENT_MAX = 5;
const CX_STOPS = /[\s.,;:!?…]+$/;

/* a code put on an extract here, the code used last until the next read says otherwise */
function cxUsed(name) {
  const n = cdNorm(name);
  CX.used = [{ name: cxWords(name), at: Date.now() }, ...CX.used.filter((u) => cdNorm(u.name) !== n)];
}

/* the five codes used last, the last one first, by name as the list spells them */
function cxRecent() {
  const out = [];
  const seen = new Set();
  for (const name of [...CX.used.map((u) => u.name), ...CX.recent]) {
    const n = cdNorm(name);
    if (!n || seen.has(n)) continue;
    seen.add(n);
    const kept = CX.codes.find((c) => cdNorm(c.name) === n);
    out.push(kept ? kept.name : name);
  }
  return out.slice(0, CX_RECENT_MAX);
}

/* an in vivo code's name: the extract's words, the inverted commas round them set aside, trimmed of the stop at
   their end and of any dots at their start, as codes.py's `vivo_name` trims them */
function cxVivoName(quote) {
  let name = cxWords(quote);
  while (name.length >= 2 && /^["“'‘]/.test(name) && /["”'’]$/.test(name)) name = cxWords(name.slice(1, -1));
  return cxWords(name.replace(CX_STOPS, '').replace(/^[\s.…]+/, ''));
}

const cxShort = (s, most = 40) => (s.length > most ? `${s.slice(0, most).replace(/\s+\S*$/, '')}…` : s);

/* The words become a new extract with `opts.code`, or with the words as a code of their own (`opts.vivo`), as Q
   then Add a code would make it, one step of undo, called by commitQuote with the quote it put together. Words the
   passage holds as an extract already take the code on that extract. */
function cxQuickPut(row, quote, opts) {
  let name = opts.vivo ? cxVivoName(quote) : cxWords(opts.code);
  if (!name) { say(t('distil.pair.nothing_selected')); return; }
  if (name.length > 200) { say(t('codes.name_long', { most: 200 })); return; }
  const kept = CX.codes.find((c) => cdNorm(c.name) === cdNorm(name));
  if (kept) name = kept.name;
  const x = cxExtracts().find((e) => e.words === cxWords(quote));
  clearPending(true);
  window.getSelection().removeAllRanges();
  if (x && x.els.some((el) => cdNorm(pairOf(el).es) === cdNorm(name))) { say(t('codes.has_it', { name })); return; }
  if (!kept) CX.codes.push({ id: '', name, description: '', extracts: 0, participants: 0, by: [] });
  cxUsed(name);
  const kq = x ? x.quote : quote;
  const bare = x ? x.els.find((el) => !cxWords(pairOf(el).es)) : null;
  // the one empty pair a passage with none opens with takes the new extract
  const blank = x ? null : pairEls().find((el) => !cxWords(pairOf(el).es) && !cxWords(pairOf(el).kq));
  if (bare) {
    bare.querySelector('.pair-es').value = name;
    pairsChanged();
    undoPush({ key: row.key, what: 'the code', quote: kq, name, undo: (e) => cxSet(e, ''), redo: (e) => cxSet(e, e.name) });
  } else {
    if (blank) {
      blank.querySelector('.pair-es').value = name;
      blank.querySelector('.pair-kq').value = kq;
    } else insertPair({ es: name, kq });
    pairsChanged();
    undoPush({ key: row.key, what: 'the code', quote: kq, name,
      undo: (e) => cxPairOut(e), redo: (e) => { insertPair({ es: e.name, kq: e.quote }); pairsChanged(); } });
  }
  // the keyboard stays with the transcript, so the next words selected take the next key
  $('transcript').focus({ preventScroll: true });
}

/* R, V and 1 to 5 on the Coding screen, from the statements screen's keys: only in a thematic analysis project and
   only while words are selected in one of her passages or pieces are held, else nothing, the key left alone */
function cxQuickKey(key) {
  if (!cxOn()) return false;
  // with the right-click menu open on words, its key chooses its row
  if (S.rowMenu && S.rowMenu.pick) {
    const open = S.rowMenu;
    S.rowMenu = null;
    open.el.remove();
    cxQuickChosen({ quick: key }, open.pick);
    return true;
  }
  if (!(selBarPick() || S.pending.length)) return false;
  if (key === 'v') { commitQuote({ vivo: true }); return true; }
  const n = key === 'r' ? 1 : Number(key);
  if (!(n >= 1 && n <= CX_RECENT_MAX)) return false;
  const name = cxRecent()[n - 1];
  if (!name) {
    say(n === 1 ? t('codes.quick_none_used') : t('codes.quick.none_at', { n }));
    return true;
  }
  commitQuote({ code: name });
  return true;
}

/* the toolbar's In vivo code and its second line, drawn as it shows, in a thematic analysis project alone */
function cxQuickBar() {
  const vivo = $('sel-vivo');
  const line = $('sel-recent');
  if (!vivo || !line) return;
  const on = cxOn();
  vivo.hidden = !on;
  const recent = on ? cxRecent() : [];
  line.hidden = !recent.length;
  if (!on) { line.innerHTML = ''; return; }
  $('sel-vivo-label').textContent = t('codes.quick.in_vivo');
  vivo.title = t('codes.quick.in_vivo_tip');
  line.setAttribute('aria-label', t('codes.quick.recent'));
  line.innerHTML = recent.map((name, i) => `<button type="button" class="sel-chip${i === 0 ? ' last' : ''}" tabindex="-1" data-quick="${i + 1}"`
    + ` title="${escAttr(i === 0 ? t('codes.quick.chip_tip_first', { name }) : t('codes.quick.chip_tip', { name, n: i + 1 }))}">${esc(name)}</button>`).join('');
}

/* the right-click menu's first group on words selected, a thematic analysis project's alone: Extract, Extract with
   the last code, In vivo code with the words, then the codes used last numbered 1 to 5, each with its key */
function cxQuickMenu(pick) {
  if (!cxOn() || !pick) return [];
  const words = cxShort(cxVivoName(rowText(pick.row).slice(pick.start, pick.end)));
  const recent = cxRecent();
  const first = [{ label: t('page_idiograph.work.quote'), key: 'Q', quick: 'q' }];
  if (recent.length) first.push({ label: t('codes.quick.last'), key: 'R', quick: 'r' });
  first.push({ label: t('codes.quick.in_vivo_words', { words }), key: 'V', quick: 'v' });
  const groups = [first];
  if (recent.length) {
    groups.push([{ head: t('codes.quick.recent') },
      ...recent.map((name, i) => ({ label: name, key: String(i + 1), quick: String(i + 1) }))]);
  }
  return groups;
}

/* a quick act chosen from the menu, the words it was opened on selected again first, as the key would take them */
function cxQuickChosen(item, pick) {
  const box = $('transcript-rows').querySelector(`.turn[data-i="${pick.row.i}"] .turn-text`);
  if (box && typeof restoreSelection === 'function') restoreSelection(box, pick.start, pick.end);
  if (item.quick === 'q') { commitQuote(); return; }
  cxQuickKey(item.quick);
}

function cxQuickWire() {
  const vivo = $('sel-vivo');
  const line = $('sel-recent');
  if (!vivo || !line) return;
  vivo.onclick = () => cxQuickKey('v');
  line.addEventListener('click', (e) => {
    const chip = e.target.closest('[data-quick]');
    if (chip) cxQuickKey(chip.dataset.quick);
  });
}
