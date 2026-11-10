/* The beat (16 October): every page the app serves tells the server it is open, so the server can
   quit by itself a few minutes after its last tab closes (see Quitting after the last tab, in
   docs/internals.md). A light beat about every thirty seconds, in view or hidden, and a last word as
   the page goes, where the browser sends one. A page that comes back into view, or back from the
   browser's cache, beats at once. A beat with no answer is asked again every two seconds, so a
   restart or a moment's pause is never taken for a close, and after forty seconds with none the
   page's own `idiographClosed`, the main page's, says Idiograph is closed and how to open it again.
   The beat then goes quiet, as it does after Quit (`idiographQuiet`), so an old tab never holds a
   later start open.
   Each beat names the page, `page`, an id of its own, and the project it is in front of, `at`, from the app's
   own `idiographAt`, so the server never moves a project open in another window to the Trash (removetrash, 10
   November 2026). A change of project beats at once, looked for every few seconds. */
(() => {
  const BEAT = '/api/beat';
  const EVERY = 30 * 1000;
  const AGAIN = 2 * 1000;
  const WAIT = 40 * 1000;
  const LOOK = 3 * 1000;
  let asking = null;
  let timer = null;
  const page = (window.crypto && typeof crypto.randomUUID === 'function') ? crypto.randomUUID()
    : `p${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
  window.idiographPageId = page;
  let lastAt = '';

  /* the project this page is in front of, as the app says it, or none */
  function at() {
    try { return typeof window.idiographAt === 'function' ? String(window.idiographAt() || '') : ''; } catch { return ''; }
  }

  /* whether the server answered, a 503 being its word that it is closing */
  async function answers() {
    try {
      const res = await fetch(BEAT, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ page, at: (lastAt = at()) }),
        cache: 'no-store',
      });
      return res.status !== 503;
    } catch {
      return false;
    }
  }

  function quiet() {
    clearInterval(timer);
    timer = null;
  }

  function closed() {
    const hook = window.idiographClosed;
    if (typeof hook === 'function' && hook() === false) return;
    quiet();
  }

  function check() {
    if (asking) return asking;
    asking = (async () => {
      const until = Date.now() + WAIT;
      while (timer !== null && !(await answers())) {
        if (Date.now() >= until) { closed(); return; }
        await new Promise((done) => setTimeout(done, AGAIN));
      }
    })().finally(() => { asking = null; });
    return asking;
  }

  async function beat() {
    if (timer !== null && !asking && !(await answers())) check();
  }

  // the main page's own word, once Quit has closed the app or a restart has not come back
  window.idiographQuiet = quiet;
  timer = setInterval(beat, EVERY);
  beat();
  setInterval(() => { if (timer !== null && !asking && at() !== lastAt) beat(); }, LOOK);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') beat(); });
  document.addEventListener('resume', beat);
  window.addEventListener('pageshow', (e) => { if (e.persisted) beat(); });
  window.addEventListener('pagehide', () => {
    if (timer === null || !navigator.sendBeacon) return;
    try {
      navigator.sendBeacon(BEAT, JSON.stringify({ gone: true, page }));
    } catch { /* the browser sent nothing, and the last beat stands */ }
  });
})();
