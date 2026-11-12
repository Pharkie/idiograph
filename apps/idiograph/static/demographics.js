/* Participants' demographics (demobuild, 12 November 2026, Adam's option A of demodraw's proposal, "A, plus B's
   table"). A project keeps its own categories, each a list (one value each, from its values) or free words, each
   value with its colour from the participants' palette, and each participant's values in their own set (see
   demographics.py). Everything here goes through the API agents use: /api/demographics for the categories, which
   `demographics apply` and MCP's `demographics_apply` run, and /api/participant's `values` for a participant's,
   which `participant set --value` and `participant_set` run.

   Project settings, last in the sheet: each category with its grip, its name and kind, Show as a pill and its
   menu (Rename..., List or Free words, Remove), its values as pills, a click on one opening its colours, Rename...,
   Move to and Remove, a list's + Add, then Everyone's values with Edit the table, and Add category with the
   starting set. Edit the table (B's) is a card of everyone's values, a row each and a column each, a second way to
   fill them in. The profile's fields across a row gain a line for each category, a list's values to click and free
   words typed. The rows show the pills of the categories shown on one line under the label, the last giving way
   to "+2" past the line's end, the pickers on the label's line, Trajectories in place of its tags, and the GETs
   print card's Participants table chooses One row each or In sum and which categories go. */

'use strict';

const DM = {
  root: '', data: null, menu: '', value: null, editing: null, adding: '', adder: false, moveTo: false, busy: false,
  // each project's categories as its page's section sent them, for the profile's fields
  cats: new Map(), wired: false, table: null, drag: null, grip: false,
};

const DM_X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6L6 18"/></svg>';
const DM_GRIP = '<svg viewBox="0 0 12 18" aria-hidden="true" focusable="false"><circle cx="3" cy="3" r="1.4"/><circle cx="9" cy="3" r="1.4"/><circle cx="3" cy="9" r="1.4"/><circle cx="9" cy="9" r="1.4"/><circle cx="3" cy="15" r="1.4"/><circle cx="9" cy="15" r="1.4"/></svg>';
const DM_CARET = '<svg class="dm-caret" viewBox="0 0 10 6" aria-hidden="true" focusable="false"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const DM_COLOURS = 25;

const dmCase = (n) => `case-${(Number(n) || 0) % DM_COLOURS}`;
const dmWords = (held) => (Array.isArray(held) ? held : held ? [held] : []);
const dmSame = (a, b) => String(a).toLowerCase() === String(b).toLowerCase();

/* ───────────────────────────── the pills: the rows, the pickers, Trajectories ── */

function dmPill(p, more = '') {
  return `<span class="tf-pill dm-pill ${dmCase(p.colour)}" title="${escAttr(`${p.category}: ${p.word}`)}"${more}>${esc(p.word)}</span>`;
}

/* a row's line of pills under the label, nothing when there are none */
function dmPillsHtml(pills) {
  const list = Array.isArray(pills) ? pills : [];
  return list.length ? `<div class="dm-rowpills">${list.map((p) => dmPill(p)).join('')}</div>` : '';
}

/* a picker's pills, small, on the label's line */
function dmPillsInline(pills) {
  const list = Array.isArray(pills) ? pills : [];
  return list.length ? `<span class="dm-mini">${list.map((p) => dmPill(p)).join('')}</span>` : '';
}

/* the pills' words in a line, for a tooltip, "Female, 40 to 49, Spanish" */
function dmPillsWords(pills) {
  return (Array.isArray(pills) ? pills : []).map((p) => p.word).join(', ');
}

/* the pills past the line's end give way, the last first, to "+2", its tooltip naming them */
function dmFit(box) {
  if (!box || !box.isConnected) return;
  for (const m of box.querySelectorAll('.dm-more')) m.remove();
  const pills = [...box.querySelectorAll('.dm-pill')];
  for (const p of pills) p.hidden = false;
  if (box.scrollWidth <= box.clientWidth + 1) return;
  const more = document.createElement('span');
  more.className = 'tf-pill dm-pill dm-more';
  box.appendChild(more);
  const gone = [];
  for (let i = pills.length - 1; i > 0 && box.scrollWidth > box.clientWidth + 1; i -= 1) {
    pills[i].hidden = true;
    gone.unshift(pills[i].textContent);
    more.textContent = `+${gone.length}`;
    more.title = gone.join(', ');
  }
}

function dmFitAll(scope = document) {
  for (const box of scope.querySelectorAll('.dm-rowpills')) dmFit(box);
}

window.addEventListener('resize', () => {
  clearTimeout(DM.fitTimer);
  DM.fitTimer = setTimeout(() => dmFitAll(), 80);
});

/* the project page's section: its categories kept for the profile's fields, and its rows' pills fitted */
function dmPage(s) {
  if (s && s.id) DM.cats.set(s.id, Array.isArray(s.demographics) ? s.demographics : []);
  dmWire();
  requestAnimationFrame(() => dmFitAll($('hp-list')));
}

/* a row's pills drawn again as the participant's set now stands, hidden while their fields are open */
function dmRowFill(li, person) {
  if (!li) return;
  const was = li.querySelector('.dm-rowpills');
  if (was) was.remove();
  const box = document.createElement('div');
  box.innerHTML = dmPillsHtml(person && person.pills);
  const line = box.firstElementChild;
  if (!line) return;
  line.hidden = !!li.querySelector('.pp-edit');
  li.insertBefore(line, li.querySelector('.pp-portrait') || li.querySelector('.pp-edit') || li.querySelector('.pc-files'));
  requestAnimationFrame(() => dmFit(line));
}

/* ───────────────────────────── the profile's fields across a row ── */

/* a line for each category after the pen portrait: a list's values to click, the one chosen filled in its colour
   and the rest dashed, a click on it again clearing it, and free words as pills with Add for one more */
function dmFieldsHtml(p) {
  const cats = DM.cats.get(PP.root) || [];
  if (!cats.length || !p || !p.person) return '';
  const values = p.person.values || {};
  return '<div class="dm-fields">' + cats.map((c, ci) => {
    const have = dmWords(values[c.name]);
    if (c.kind === 'list') {
      return `<div class="pp-l dm-l"><span>${esc(c.name)}</span><span class="dm-choices" role="group" aria-label="${escAttr(c.name)}">`
        + c.values.map((v) => {
          const on = have.some((h) => dmSame(h, v.word));
          return `<button type="button" class="tf-pill dm-pill dm-choice ${dmCase(v.colour)}${on ? '' : ' dm-opt'}" data-dm-pick="${ci}"`
            + ` data-dm-word="${escAttr(v.word)}" aria-pressed="${on}">${esc(v.word)}</button>`;
        }).join('') + '</span></div>';
    }
    return `<div class="pp-l dm-l"><span>${esc(c.name)}</span><span class="dm-choices">`
      + have.map((w) => {
        const v = c.values.find((x) => dmSame(x.word, w));
        return `<span class="tf-pill tf-pill-x dm-pill ${dmCase(v ? v.colour : 0)}"><span class="dm-pw">${esc(w)}</span>`
          + `<button type="button" class="tf-x" data-dm-unword="${ci}" data-dm-word="${escAttr(w)}"`
          + ` aria-label="${escAttr(t('demographics.page.remove_word', { word: w }))}" title="${escAttr(t('demographics.page.remove_word', { word: w }))}">${DM_X}</button></span>`;
      }).join('')
      + `<input class="tf-edit-in dm-wordin" data-dm-add="${ci}" maxlength="40" spellcheck="false" autocomplete="off"`
      + ` placeholder="${escAttr(t('demographics.page.add'))}" aria-label="${escAttr(t('demographics.page.add_to', { name: c.name }))}"></span></div>`;
  }).join('') + '</div>';
}

/* one category's value saved for the participant whose fields are open, and the fields drawn again */
async function dmFieldSave(ci, value, refocus) {
  const cats = DM.cats.get(PP.root) || [];
  const c = cats[ci];
  if (!c || !PP.p) return;
  if (await ppSave({ values: { [c.name]: value } })) {
    // a free word new to the category joined it, so the page's copy is read again for the next line drawn
    if (c.kind === 'words') dmCatsAgain(PP.root);
    ppDraw();
    if (refocus) {
      const box = PP.li && PP.li.querySelector(`[data-dm-add="${ci}"]`);
      if (box) box.focus();
    }
  }
}

/* the project's categories read again for the profile's fields, a free word added having joined one */
async function dmCatsAgain(root) {
  try {
    const got = await api('/api/demographics', { root, op: 'show' });
    if (got && Array.isArray(got.demographics)) DM.cats.set(root, got.demographics);
  } catch { /* the fields keep the copy they have */ }
}

function dmFieldWords(ci) {
  const cats = DM.cats.get(PP.root) || [];
  const c = cats[ci];
  return c && PP.p && PP.p.person ? dmWords((PP.p.person.values || {})[c.name]) : [];
}

/* the words typed in a free words field added, a comma or Enter ending each */
function dmFieldAdd(box, refocus) {
  const ci = Number(box.dataset.dmAdd);
  const typed = box.value.split(',').map((w) => w.replace(/\s+/g, ' ').trim()).filter(Boolean);
  box.value = '';
  if (!typed.length) return;
  const now = dmFieldWords(ci);
  const more = typed.filter((w) => !now.some((h) => dmSame(h, w)));
  if (more.length) dmFieldSave(ci, [...now, ...more], refocus);
}

/* the fields' own clicks and keys, wired once on the rows' list beside the profile's own */
function dmWire() {
  const list = $('hp-list');
  if (!list || DM.wired) return;
  DM.wired = true;
  list.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-dm-pick], [data-dm-unword]');
    if (!b || !PP.li || !PP.li.contains(b)) return;
    e.stopPropagation();
    if (b.dataset.dmPick !== undefined) {
      const ci = Number(b.dataset.dmPick);
      const on = b.getAttribute('aria-pressed') === 'true';
      dmFieldSave(ci, on ? '' : b.dataset.dmWord);
      return;
    }
    const ci = Number(b.dataset.dmUnword);
    dmFieldSave(ci, dmFieldWords(ci).filter((w) => !dmSame(w, b.dataset.dmWord)));
  });
  list.addEventListener('keydown', (e) => {
    const box = e.target.closest && e.target.closest('[data-dm-add]');
    if (!box) return;
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); e.stopPropagation(); dmFieldAdd(box, true); }
    else if (e.key === 'Backspace' && !box.value) {
      const ci = Number(box.dataset.dmAdd);
      const now = dmFieldWords(ci);
      if (now.length) { e.preventDefault(); dmFieldSave(ci, now.slice(0, -1), true); }
    }
  });
  list.addEventListener('focusout', (e) => {
    const box = e.target.closest && e.target.closest('[data-dm-add]');
    if (box && box.value.trim()) dmFieldAdd(box, false);
  });
}

/* ───────────────────────────── Project settings' section ── */

/* the section for the project the sheet was opened for, none for a demo, read from the server */
async function dmOpen(p) {
  const block = $('dm-block');
  if (!block) return;
  Object.assign(DM, { root: p && p.id ? p.id : '', data: null, menu: '', value: null, editing: null, adding: '',
    adder: false, moveTo: false });
  block.hidden = !p || !!p.demo || !p.id;
  dmSaid('');
  if (block.hidden) return;
  $('dm-cats').innerHTML = '';
  try {
    const got = await api('/api/demographics', { root: DM.root, op: 'show' });
    if (DM.root !== (p.id || '')) return;
    DM.data = got;
  } catch (err) {
    dmSaid(needsRestart(err) ? RESTART_LINE : err.message, true);
    return;
  }
  dmDraw();
}

function dmSaid(text, failed = false) {
  const line = $('dm-said');
  if (!line) return;
  saidIn('dm-said', text || '', failed);
  line.hidden = !text;
}

const dmCats = () => (DM.data && DM.data.demographics) || [];

/* one category's row: its grip, name, kind, Show as a pill and menu, then its values as pills */
function dmCatHtml(c, i) {
  const kind = c.kind === 'list' ? t('demographics.page.list') : t('demographics.page.words');
  const renaming = DM.editing && DM.editing.cat === c.name && DM.editing.word === undefined;
  const name = renaming
    ? `<input class="tf-edit-in dm-rename" data-dm-rename="cat" maxlength="40" spellcheck="false" value="${escAttr(c.name)}" aria-label="${escAttr(t('demographics.page.rename_of', { name: c.name }))}">`
    : `<span class="dm-cname">${esc(c.name)}</span>`;
  const menu = DM.menu === c.name ? `<div class="row-menu dm-menu" role="menu">`
    + `<button type="button" class="ghost" role="menuitem" data-dm-act="rename">${esc(t('demographics.page.rename'))}</button>`
    + `<button type="button" class="ghost${c.kind === 'list' ? ' dm-on' : ''}" role="menuitemradio" aria-checked="${c.kind === 'list'}" data-dm-act="list">${esc(t('demographics.page.list'))}</button>`
    + `<button type="button" class="ghost${c.kind === 'words' ? ' dm-on' : ''}" role="menuitemradio" aria-checked="${c.kind === 'words'}" data-dm-act="words">${esc(t('demographics.page.words'))}</button>`
    + `<button type="button" class="ghost" role="menuitem" data-dm-act="remove">${esc(t('demographics.page.remove'))}</button></div>` : '';
  const open = DM.value && DM.value.cat === c.name ? DM.value.word : '';
  const values = c.values.map((v, vi) => {
    if (DM.editing && DM.editing.cat === c.name && DM.editing.word === v.word) {
      return `<input class="tf-edit-in dm-rename dm-vrename" data-dm-rename="value" maxlength="40" spellcheck="false" value="${escAttr(v.word)}"`
        + ` aria-label="${escAttr(t('demographics.page.rename_of', { name: v.word }))}">`;
    }
    return `<button type="button" class="tf-pill dm-pill dm-vpill ${dmCase(v.colour)}${dmSame(open, v.word) ? ' tf-pill-open' : ''}" data-dm-value="${vi}"`
      + ` draggable="true" aria-expanded="${dmSame(open, v.word)}" title="${escAttr(t('demographics.page.value_tip', { word: v.word }))}">${esc(v.word)}</button>`;
  }).join('');
  const add = c.kind !== 'list' ? '' : DM.adding === c.name
    ? `<input class="tf-edit-in dm-rename dm-vadd" data-dm-addvalue maxlength="40" spellcheck="false" aria-label="${escAttr(t('demographics.page.add_to', { name: c.name }))}">`
    : `<button type="button" class="dm-addv" data-dm-act="add-value">${esc(t('demographics.page.add_value'))}</button>`;
  return `<li class="dm-cat" data-cat="${i}">`
    + `<button type="button" class="dm-grip" data-dm-grip="${i}" title="${escAttr(t('demographics.page.move_tip', { name: c.name }))}"`
    + ` aria-label="${escAttr(t('demographics.page.move_tip', { name: c.name }))}">${DM_GRIP}</button>`
    + `<span class="dm-chead">${name}<span class="dm-kind">${esc(kind)}</span></span>`
    + `<label class="dm-tick"><input type="checkbox" data-dm-show="${i}"${c.show ? ' checked' : ''}> ${esc(t('demographics.page.show_pill'))}</label>`
    + `<span class="dm-menuwrap"><button type="button" class="dm-dots" data-dm-act="menu" aria-haspopup="menu" aria-expanded="${DM.menu === c.name}"`
    + ` title="${escAttr(t('demographics.page.menu_of', { name: c.name }))}" aria-label="${escAttr(t('demographics.page.menu_of', { name: c.name }))}">&#8943;</button>${menu}</span>`
    + `<div class="dm-vals">${values}${add}</div>`
    + (open ? dmValuePanel(c, c.values.find((v) => dmSame(v.word, open))) : '')
    + '</li>';
}

/* a value's colours and its menu, under its category's values: Rename..., Move to and Remove */
function dmValuePanel(c, v) {
  if (!v) return '';
  const dots = Array.from({ length: DM_COLOURS }, (_, n) => `<button type="button" class="tf-dot case-${n}${v.colour === n ? ' on' : ''}" data-dm-colour="${n}"`
    + ` aria-pressed="${v.colour === n}" aria-label="${escAttr(t('demographics.page.colour_n', { word: v.word, n: n + 1 }))}"></button>`).join('');
  const others = dmCats().filter((x) => x.name !== c.name);
  const moves = DM.moveTo && others.length ? `<div class="row-menu dm-menu dm-moveto" role="menu">${others.map((x) => `<button type="button" class="ghost" role="menuitem"`
    + ` data-dm-moveto="${escAttr(x.name)}">${esc(x.name)}</button>`).join('')}</div>` : '';
  return `<div class="dm-vpanel"><span class="tf-dots" role="group" aria-label="${escAttr(t('demographics.page.colour_of', { word: v.word }))}">`
    + `<span class="tf-dots-l">${esc(v.word)}</span>${dots}</span><span class="dm-vacts">`
    + `<button type="button" class="ghost small" data-dm-act="value-rename">${esc(t('demographics.page.rename'))}</button>`
    + (others.length ? `<span class="dm-menuwrap"><button type="button" class="ghost small" data-dm-act="value-move" aria-haspopup="menu" aria-expanded="${DM.moveTo}">${esc(t('demographics.page.move_to'))}${DM_CARET}</button>${moves}</span>` : '')
    + `<button type="button" class="ghost small" data-dm-act="value-remove">${esc(t('demographics.page.remove'))}</button></span></div>`;
}

/* the section drawn, the field in front kept in front */
function dmDraw() {
  const box = $('dm-cats');
  if (!box || !DM.data) return;
  const cats = dmCats();
  box.innerHTML = cats.map(dmCatHtml).join('');
  // Add category's starting set, each one there already greyed and ticked, then New category...
  const menu = $('dm-add-menu');
  menu.innerHTML = (DM.data.starters || []).map((s, i) => {
    const there = cats.some((c) => dmSame(c.name, s.name));
    return `<button type="button" class="ghost${there ? ' dm-had' : ''}" role="menuitem" data-dm-starter="${i}"${there ? ' disabled aria-disabled="true"' : ''}>`
      + `<span>${esc(s.name)}</span>${there ? '<span class="dm-check" aria-hidden="true">&#10003;</span>' : ''}</button>`;
  }).join('') + `<span class="dm-msep" role="separator"></span><button type="button" class="ghost" role="menuitem" data-dm-starter="new">${esc(t('demographics.page.new_category'))}</button>`;
  $('dm-new-row').hidden = !DM.adder;
  $('dm-table-open').disabled = !cats.length;
  const focus = box.querySelector('.dm-rename');
  if (focus) { focus.focus(); focus.select(); }
}

/* the operations sent, the section drawn from the answer, and the project's page behind it read again */
async function dmApply(ops) {
  if (!DM.root || DM.busy) return false;
  DM.busy = true;
  try {
    const got = await api('/api/demographics', { root: DM.root, op: 'apply', ops });
    DM.data = got;
    DM.cats.set(DM.root, got.demographics || []);
    dmSaid('');
    dmDraw();
    if (!$('library').hidden) loadLibrary().catch(() => {});
    return true;
  } catch (err) {
    dmSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));
    return false;
  } finally {
    DM.busy = false;
  }
}

/* Remove, of a category or a value: straight away when nobody has it, else after the card says who had what,
   from a dry run of the same operation */
async function dmRemove(op) {
  let dry;
  try {
    dry = await api('/api/demographics', { root: DM.root, op: 'apply', ops: [op], dry_run: true });
  } catch (err) {
    dmSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));
    return;
  }
  const line = (dry.changes || [])[0] || '';
  if (!/, (with|from) /.test(line)) { DM.value = null; dmApply([op]); return; }
  $('dm-confirm-title').textContent = t('demographics.page.confirm_title', { name: op.op === 'remove' ? op.category : op.value });
  $('dm-confirm-line').textContent = line;
  DM.confirm = op;
  show('dm-confirm');
  $('dm-confirm-go').focus();
}

function dmConfirmShut(go) {
  const op = DM.confirm;
  DM.confirm = null;
  hide('dm-confirm');
  if (go && op) { DM.value = null; dmApply([op]); }
}

/* a rename typed in place kept, or Esc putting the name back */
function dmRenameDone(input, keep) {
  const edit = DM.editing;
  DM.editing = null;
  const to = input.value.replace(/\s+/g, ' ').trim();
  if (!keep || !edit || !to) { dmDraw(); return; }
  if (edit.word === undefined) {
    if (to === edit.cat) { dmDraw(); return; }
    if (DM.value && DM.value.cat === edit.cat) DM.value.cat = to;
    dmApply([{ op: 'rename', category: edit.cat, name: to }]);
  } else {
    if (to === edit.word) { dmDraw(); return; }
    if (DM.value) DM.value.word = to;
    dmApply([{ op: 'value_rename', category: edit.cat, value: edit.word, to }]);
  }
}

function dmCatOf(el) {
  const li = el.closest('.dm-cat');
  return li ? dmCats()[Number(li.dataset.cat)] : null;
}

function dmClick(e) {
  const el = e.target.closest ? e.target.closest('button, input') : null;
  if (!el || !$('dm-block').contains(el)) return;
  const c = dmCatOf(el);
  if (el.dataset.dmStarter !== undefined) {
    $('dm-add-menu').hidden = true;
    $('dm-add').setAttribute('aria-expanded', 'false');
    if (el.dataset.dmStarter === 'new') {
      DM.adder = true;
      dmDraw();
      $('dm-new-name').value = '';
      $('dm-new-name').focus();
      return;
    }
    const s = (DM.data.starters || [])[Number(el.dataset.dmStarter)];
    if (s) dmApply([{ op: 'add', name: s.name, kind: s.kind, values: s.values }]);
    return;
  }
  if (el.id === 'dm-add') {
    const menu = $('dm-add-menu');
    menu.hidden = !menu.hidden;
    el.setAttribute('aria-expanded', String(!menu.hidden));
    if (!menu.hidden) menuFirst(menu);
    return;
  }
  if (el.id === 'dm-table-open') { dmTableOpen(); return; }
  if (!c) return;
  const act = el.dataset.dmAct;
  if (act === 'menu') { DM.menu = DM.menu === c.name ? '' : c.name; dmDraw(); const m = $('dm-cats').querySelector('.dm-menu'); if (m) menuFirst(m); return; }
  if (act === 'rename') { DM.menu = ''; DM.editing = { cat: c.name }; dmDraw(); return; }
  if (act === 'list' || act === 'words') { DM.menu = ''; if (c.kind !== act) dmApply([{ op: 'kind', category: c.name, kind: act }]); else dmDraw(); return; }
  if (act === 'remove') { DM.menu = ''; dmDraw(); dmRemove({ op: 'remove', category: c.name }); return; }
  if (act === 'add-value') { DM.adding = c.name; dmDraw(); const box = $('dm-cats').querySelector('[data-dm-addvalue]'); if (box) box.focus(); return; }
  if (el.dataset.dmValue !== undefined) {
    const v = c.values[Number(el.dataset.dmValue)];
    DM.value = DM.value && DM.value.cat === c.name && dmSame(DM.value.word, v.word) ? null : { cat: c.name, word: v.word };
    DM.moveTo = false;
    dmDraw();
    return;
  }
  const v = DM.value ? c.values.find((x) => dmSame(x.word, DM.value.word)) : null;
  if (!v) return;
  if (el.dataset.dmColour !== undefined) { dmApply([{ op: 'value_colour', category: c.name, value: v.word, colour: Number(el.dataset.dmColour) }]); return; }
  if (act === 'value-rename') { DM.editing = { cat: c.name, word: v.word }; dmDraw(); return; }
  if (act === 'value-move') { DM.moveTo = !DM.moveTo; dmDraw(); const m = $('dm-cats').querySelector('.dm-moveto'); if (m) menuFirst(m); return; }
  if (el.dataset.dmMoveto) { DM.moveTo = false; DM.value = null; dmApply([{ op: 'value_to', category: c.name, value: v.word, to: el.dataset.dmMoveto }]); return; }
  if (act === 'value-remove') dmRemove({ op: 'value_remove', category: c.name, value: v.word });
}

function dmKeys(e) {
  const el = e.target;
  if (!el || !el.closest || !$('dm-block').contains(el)) return;
  if (el.matches('[data-dm-rename]')) {
    if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); dmRenameDone(el, true); }
    else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); dmRenameDone(el, false); }
    return;
  }
  if (el.matches('[data-dm-addvalue]')) {
    const c = dmCatOf(el);
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      const word = el.value.replace(/\s+/g, ' ').trim();
      if (word && c) dmApply([{ op: 'value_add', category: c.name, value: word }]).then(() => {
        const box = $('dm-cats').querySelector('[data-dm-addvalue]');
        if (box) box.focus();
      });
    } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); DM.adding = ''; dmDraw(); }
    return;
  }
  if (el.id === 'dm-new-name') {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      const name = el.value.replace(/\s+/g, ' ').trim();
      if (name) dmApply([{ op: 'add', name, kind: 'words' }]).then((ok) => { if (ok) { DM.adder = false; dmDraw(); } });
    } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); DM.adder = false; dmDraw(); }
    return;
  }
  // a menu's arrows and Esc, the menu shut and its button given the focus back
  const menu = el.closest('.dm-menu, #dm-add-menu');
  if (menu) {
    menuKeys(e, menu, () => {
      if (menu.id === 'dm-add-menu') { menu.hidden = true; $('dm-add').focus(); return; }
      DM.menu = '';
      DM.moveTo = false;
      dmDraw();
    });
    return;
  }
  // Alt and an arrow move a category by its grip, or a value by its pill, one place
  if (!e.altKey) return;
  const c = dmCatOf(el);
  if (!c) return;
  const cats = dmCats();
  if (el.dataset.dmGrip !== undefined && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
    e.preventDefault();
    const at = cats.indexOf(c) + (e.key === 'ArrowUp' ? -1 : 1);
    if (at >= 0 && at < cats.length) dmApply([{ op: 'move', category: c.name, at }]).then(() => dmRefocus(`[data-dm-grip="${at}"]`));
  } else if (el.dataset.dmValue !== undefined && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
    e.preventDefault();
    const vi = Number(el.dataset.dmValue);
    const at = vi + (e.key === 'ArrowLeft' ? -1 : 1);
    if (at >= 0 && at < c.values.length) {
      const ci = cats.indexOf(c);
      dmApply([{ op: 'value_move', category: c.name, value: c.values[vi].word, at }])
        .then(() => dmRefocus(`.dm-cat[data-cat="${ci}"] [data-dm-value="${at}"]`));
    }
  }
}

function dmRefocus(selector) {
  const el = $('dm-cats').querySelector(selector);
  if (el) el.focus();
}

/* a category dragged by its grip to another's place, or a value along its own category */
function dmDragStart(e) {
  const pill = e.target.closest && e.target.closest('[data-dm-value]');
  const li = e.target.closest && e.target.closest('.dm-cat');
  if (!li) return;
  if (pill) {
    DM.drag = { kind: 'value', cat: Number(li.dataset.cat), at: Number(pill.dataset.dmValue) };
  } else if (DM.grip) {
    DM.drag = { kind: 'cat', at: Number(li.dataset.cat) };
  } else {
    e.preventDefault();
    return;
  }
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', '');
  li.classList.add('dm-dragging');
}

function dmDragOver(e) {
  if (!DM.drag) return;
  const li = e.target.closest && e.target.closest('.dm-cat');
  if (!li) return;
  if (DM.drag.kind === 'value' && Number(li.dataset.cat) !== DM.drag.cat) return;
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
}

function dmDrop(e) {
  const drag = DM.drag;
  DM.drag = null;
  DM.grip = false;
  for (const x of $('dm-cats').querySelectorAll('.dm-dragging')) x.classList.remove('dm-dragging');
  if (!drag) return;
  const li = e.target.closest && e.target.closest('.dm-cat');
  if (!li) return;
  e.preventDefault();
  const cats = dmCats();
  if (drag.kind === 'cat') {
    const to = Number(li.dataset.cat);
    if (to !== drag.at) dmApply([{ op: 'move', category: cats[drag.at].name, at: to }]);
    return;
  }
  const c = cats[drag.cat];
  const pill = e.target.closest('[data-dm-value]');
  const to = pill ? Number(pill.dataset.dmValue) : c.values.length - 1;
  if (c && to !== drag.at) dmApply([{ op: 'value_move', category: c.name, value: c.values[drag.at].word, at: to }]);
}

function dmBoot() {
  const block = $('dm-block');
  if (!block) return;
  block.addEventListener('click', dmClick);
  block.addEventListener('keydown', dmKeys);
  block.addEventListener('change', (e) => {
    const tick = e.target.closest && e.target.closest('[data-dm-show]');
    const c = tick ? dmCats()[Number(tick.dataset.dmShow)] : null;
    if (c) dmApply([{ op: 'show', category: c.name, show: tick.checked }]);
  });
  block.addEventListener('focusout', (e) => {
    const el = e.target;
    if (el && el.matches && el.matches('[data-dm-rename]') && DM.editing) setTimeout(() => { if (DM.editing && el.isConnected) dmRenameDone(el, true); }, 0);
  });
  block.addEventListener('pointerdown', (e) => { DM.grip = !!(e.target.closest && e.target.closest('[data-dm-grip]')); });
  block.addEventListener('dragstart', dmDragStart);
  block.addEventListener('dragover', dmDragOver);
  block.addEventListener('drop', dmDrop);
  block.addEventListener('dragend', () => { DM.drag = null; DM.grip = false; for (const x of block.querySelectorAll('.dm-dragging')) x.classList.remove('dm-dragging'); });
  // a click away from a menu shuts it
  document.addEventListener('click', (e) => {
    if (!e.target.closest) return;
    if (!e.target.closest('#dm-add, #dm-add-menu')) { const m = $('dm-add-menu'); if (m && !m.hidden) { m.hidden = true; $('dm-add').setAttribute('aria-expanded', 'false'); } }
    if ((DM.menu || DM.moveTo) && !e.target.closest('.dm-menuwrap')) { DM.menu = ''; DM.moveTo = false; dmDraw(); }
  });
  $('dm-confirm-go').onclick = () => dmConfirmShut(true);
  $('dm-confirm-cancel').onclick = () => dmConfirmShut(false);
  $('dm-confirm-close').onclick = () => dmConfirmShut(false);
  dmTableBoot();
  dmPrintBoot();
}

/* ───────────────────────────── Edit the table: everyone's values in one card ── */

function dmTableOpen() {
  if (!DM.data || !dmCats().length) return;
  DM.table = { focus: '' };
  $('dm-table-kicker').textContent = (PROJ && PROJ.p && PROJ.p.name) || '';
  dmTableSaid('');
  dmTableDraw();
  show('dm-table');
  const first = $('dm-table-grid').querySelector('select, input');
  if (first) first.focus();
}

function dmTableSaid(text) {
  saidIn('dm-table-said', text || '', true);
  $('dm-table-said').hidden = !text;
}

/* a row a participant, a column a category: a list's pick-list, free words as pills with Add */
function dmTableDraw() {
  const cats = dmCats();
  const people = (DM.data && DM.data.participants) || [];
  const head = `<thead><tr><th>${esc(t('demographics.page.participant'))}</th>${cats.map((c) => `<th>${esc(c.name)}</th>`).join('')}</tr></thead>`;
  const rows = people.map((p, pi) => `<tr><td class="dm-twho">${esc(p.who)}</td>${cats.map((c, ci) => {
    const have = dmWords((p.values || {})[c.name]);
    const key = `${pi}|${ci}`;
    if (c.kind === 'list') {
      return `<td><select class="dm-tsel" data-dm-cell="${key}" aria-label="${escAttr(t('demographics.page.cell_of', { name: c.name, who: p.who }))}">`
        + `<option value=""${have.length ? '' : ' selected'}></option>`
        + c.values.map((v) => `<option value="${escAttr(v.word)}"${have.some((h) => dmSame(h, v.word)) ? ' selected' : ''}>${esc(v.word)}</option>`).join('')
        + '</select></td>';
    }
    return `<td><span class="dm-twords">${have.map((w) => {
      const v = c.values.find((x) => dmSame(x.word, w));
      return `<span class="tf-pill tf-pill-x dm-pill ${dmCase(v ? v.colour : 0)}"><span class="dm-pw">${esc(w)}</span><button type="button" class="tf-x"`
        + ` data-dm-tunword="${key}" data-dm-word="${escAttr(w)}" aria-label="${escAttr(t('demographics.page.remove_word', { word: w }))}">${DM_X}</button></span>`;
    }).join('')}<input class="dm-tin" data-dm-tadd="${key}" maxlength="40" spellcheck="false" autocomplete="off" placeholder="${escAttr(t('demographics.page.add'))}"`
      + ` aria-label="${escAttr(t('demographics.page.cell_of', { name: c.name, who: p.who }))}"></span></td>`;
  }).join('')}</tr>`).join('');
  $('dm-table-grid').innerHTML = head + `<tbody>${rows}</tbody>`;
  if (DM.table && DM.table.focus) {
    const back = $('dm-table-grid').querySelector(DM.table.focus);
    if (back) back.focus();
  }
}

/* one cell saved through the participant's own route, the table drawn again from the answer */
async function dmTableSave(key, value, focus) {
  const [pi, ci] = key.split('|').map(Number);
  const p = DM.data.participants[pi];
  const c = dmCats()[ci];
  if (!p || !c) return;
  try {
    const got = await api('/api/participant', { root: DM.root, case: p.case, values: { [c.name]: value } });
    if (got && got.person) p.values = got.person.values || {};
    // a free word new to its category joined it with a colour of its own
    if (c.kind === 'words') {
      const again = await api('/api/demographics', { root: DM.root, op: 'show' });
      DM.data = Object.assign(again, { participants: again.participants });
    }
    DM.table.focus = focus || '';
    dmTableSaid('');
    dmTableDraw();
  } catch (err) {
    dmTableSaid(needsRestart(err) ? RESTART_LINE : err.message);
    dmTableDraw();
  }
}

function dmTableWords(key) {
  const [pi, ci] = key.split('|').map(Number);
  const p = DM.data.participants[pi];
  const c = dmCats()[ci];
  return p && c ? dmWords((p.values || {})[c.name]) : [];
}

function dmTableAdd(box, keep) {
  const key = box.dataset.dmTadd;
  const typed = box.value.split(',').map((w) => w.replace(/\s+/g, ' ').trim()).filter(Boolean);
  box.value = '';
  const now = dmTableWords(key);
  const more = typed.filter((w) => !now.some((h) => dmSame(h, w)));
  if (more.length) dmTableSave(key, [...now, ...more], keep ? `[data-dm-tadd="${key}"]` : '');
}

/* the card shut, Project settings' section and the project's page read again */
function dmTableShut() {
  hide('dm-table');
  DM.table = null;
  if (PROJ && PROJ.p && !$('projset').hidden) dmOpen(PROJ.p);
  if (!$('library').hidden) loadLibrary().catch(() => {});
  const back = $('dm-table-open');
  if (back && !$('projset').hidden) back.focus();
}

function dmTableBoot() {
  const grid = $('dm-table-grid');
  $('dm-table-close').onclick = dmTableShut;
  grid.addEventListener('change', (e) => {
    const sel = e.target.closest && e.target.closest('[data-dm-cell]');
    if (sel) dmTableSave(sel.dataset.dmCell, sel.value, `[data-dm-cell="${sel.dataset.dmCell}"]`);
  });
  grid.addEventListener('click', (e) => {
    const x = e.target.closest && e.target.closest('[data-dm-tunword]');
    if (!x) return;
    const key = x.dataset.dmTunword;
    dmTableSave(key, dmTableWords(key).filter((w) => !dmSame(w, x.dataset.dmWord)), `[data-dm-tadd="${key}"]`);
  });
  grid.addEventListener('keydown', (e) => {
    const box = e.target.closest && e.target.closest('[data-dm-tadd]');
    if (!box) return;
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); e.stopPropagation(); dmTableAdd(box, true); }
    else if (e.key === 'Backspace' && !box.value) {
      const now = dmTableWords(box.dataset.dmTadd);
      if (now.length) { e.preventDefault(); dmTableSave(box.dataset.dmTadd, now.slice(0, -1), `[data-dm-tadd="${box.dataset.dmTadd}"]`); }
    }
  });
  grid.addEventListener('focusout', (e) => {
    const box = e.target.closest && e.target.closest('[data-dm-tadd]');
    if (box && box.value.trim()) dmTableAdd(box, false);
  });
}

/* ───────────────────────────── the GETs print card: One row each or In sum, and which go ── */

const DMP = { root: '', data: null, ask: 0 };

/* under Participants table, while it is ticked and shown: One row each or In sum, and a tick for each category,
   the project's own, kept in its file as he leaves them */
async function dmPrintDraw(shown, root) {
  const box = $('gt-print-dm');
  if (!box) return;
  const on = !!shown && $('gt-print-people').checked;
  if (!on || !root) { box.hidden = true; return; }
  // read afresh each time the card draws, so a change in Project settings meanwhile shows
  const ask = ++DMP.ask;
  try {
    const got = await api('/api/demographics', { root, op: 'show' });
    if (ask !== DMP.ask) return;
    Object.assign(DMP, { root, data: got });
  } catch { box.hidden = true; return; }
  const cats = (DMP.data && DMP.data.demographics) || [];
  box.hidden = !cats.length;
  if (!cats.length) return;
  const how = DMP.data.table === 'sum' ? 'sum' : 'each';
  box.innerHTML = `<span class="dm-prow" role="radiogroup" aria-label="${escAttr(t('page_print.people.heading'))}">`
    + `<label class="gt-print-notes"><input type="radio" name="dm-print-how" value="each"${how === 'each' ? ' checked' : ''}> ${esc(t('demographics.page.one_row'))}</label>`
    + `<label class="gt-print-notes"><input type="radio" name="dm-print-how" value="sum"${how === 'sum' ? ' checked' : ''}> ${esc(t('demographics.page.in_sum'))}</label></span>`
    + `<span class="dm-prow">${cats.map((c, i) => `<label class="gt-print-notes"><input type="checkbox" data-dm-export="${i}"${c.export ? ' checked' : ''}> ${esc(c.name)}</label>`).join('')}</span>`;
}

async function dmPrintSave(ops) {
  if (!DMP.root) return;
  try {
    DMP.data = await api('/api/demographics', { root: DMP.root, op: 'apply', ops });
  } catch (err) { say(needsRestart(err) ? RESTART_LINE : err.message, 9000); }
}

function dmPrintBoot() {
  const box = $('gt-print-dm');
  if (!box) return;
  box.addEventListener('change', (e) => {
    const el = e.target;
    if (el.name === 'dm-print-how') { dmPrintSave([{ op: 'table', how: el.value }]); return; }
    const c = el.dataset && el.dataset.dmExport !== undefined ? ((DMP.data && DMP.data.demographics) || [])[Number(el.dataset.dmExport)] : null;
    if (c) dmPrintSave([{ op: 'export', category: c.name, export: el.checked }]);
  });
  const people = $('gt-print-people');
  if (people) people.addEventListener('change', () => { if (typeof TH !== 'undefined' && TH.printing) dmPrintDraw(gtPeopleShown(TH.printing), TH.root || ''); });
}

dmBoot();
