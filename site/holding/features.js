(() => {
  document.documentElement.classList.add('js');
  const box = document.getElementById('find');
  const said = document.getElementById('find-said');
  const none = document.getElementById('find-none');
  const list = document.querySelector('.list');
  const rows = [...document.querySelectorAll('.list .fr')];
  const fold = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  const textOf = (r, sel) => [...r.querySelectorAll(sel)].map((e) => e.textContent).join(' ');
  const seen = new Map(rows.map((r) => [r, fold(textOf(r, '.fr-name, .fr-line'))]));
  const sentences = new Map(rows.map((r) => {
    const d = r.querySelector('.fr-detail');
    return [r, d ? d.textContent.trim().split(/(?<=[.!?])\s+(?=[A-Z0-9"“(])/) : []];
  }));
  const text = new Map(rows.map((r) => [r, seen.get(r) + ' ' + fold(sentences.get(r).join(' '))]));
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const html = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const matcher = (asked, whole) => asked.map((w) => new RegExp(`(^|[^a-z0-9])${esc(w)}${whole ? '($|[^a-z0-9])' : ''}`, 'g'));
  const has = (re, s) => { re.lastIndex = 0; return re.test(s); };
  const marked = (sentence, res) => {
    const f = fold(sentence);
    if (f.length !== sentence.length) return html(sentence);
    const spans = [];
    for (const re of res) {
      re.lastIndex = 0;
      let m;
      while ((m = re.exec(f))) {
        const at = m.index + m[1].length;
        const word = m[0].slice(m[1].length, m[0].length - (m[2] ? m[2].length : 0));
        spans.push([at, at + word.length]);
        re.lastIndex = at + Math.max(1, word.length);
      }
    }
    spans.sort((a, b) => a[0] - b[0]);
    let out = '';
    let i = 0;
    for (const [a, b] of spans) {
      if (a < i) continue;
      out += html(sentence.slice(i, a)) + '<mark>' + html(sentence.slice(a, b)) + '</mark>';
      i = b;
    }
    return out + html(sentence.slice(i));
  };
  const run = () => {
    if (!box) return;
    const asked = fold(box.value).split(/\s+/).filter(Boolean);
    let res = matcher(asked, true);
    if (!rows.some((r) => res.every((re) => has(re, text.get(r))))) res = matcher(asked, false);
    let shown = 0;
    for (const r of rows) {
      const hit = res.every((re) => has(re, text.get(r)));
      r.hidden = !hit;
      if (hit) shown += 1;
      const slot = r.querySelector('.fr-hit');
      if (!slot) continue;
      const rest = asked.length && hit ? res.filter((re) => !has(re, seen.get(r))) : [];
      const found = rest.length ? sentences.get(r).filter((s) => rest.some((re) => has(re, fold(s)))).slice(0, 2) : [];
      slot.hidden = !found.length;
      slot.innerHTML = found.map((s) => marked(s, rest)).join(' ');
    }
    for (const cat of document.querySelectorAll('.list .cat')) {
      cat.hidden = !cat.querySelector('.fr:not([hidden])');
    }
    list.classList.toggle('finding', asked.length > 0);
    if (!asked.length) { said.textContent = ''; none.hidden = true; return; }
    said.textContent = shown === 1 ? '1 feature' : `${shown} features`;
    none.hidden = shown > 0;
    none.textContent = `Nothing here matches "${box.value.trim()}".`;
  };
  const openHash = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    const el = id && document.getElementById(id);
    if (!el || el.tagName !== 'DETAILS') return;
    if (box && box.value && el.hidden) { box.value = ''; run(); }
    el.open = true;
    el.scrollIntoView({ block: 'start' });
  };
  window.addEventListener('hashchange', openHash);
  if (box && list) {
    box.addEventListener('input', run);
    run();
  }
  openHash();
})();
