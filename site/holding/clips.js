(() => {
  const still = window.matchMedia('(prefers-reduced-motion: reduce)');
  const boxes = [...document.querySelectorAll('.clip-box')];
  const shown = new Set();
  const seen = 'IntersectionObserver' in window ? new IntersectionObserver((list) => {
    for (const e of list) {
      if (e.isIntersecting) shown.add(e.target); else shown.delete(e.target);
      run(e.target);
    }
  }, { threshold: 0.25 }) : null;
  const run = (box) => {
    const film = box.querySelector('video');
    if (still.matches) return;
    if (!seen || shown.has(box)) {
      film.play().then(() => box.classList.remove('clip-blocked')).catch((e) => {
        if (e && e.name === 'NotAllowedError') box.classList.add('clip-blocked');
      });
    } else film.pause();
  };
  const mode = () => {
    for (const box of boxes) {
      const film = box.querySelector('video');
      box.classList.toggle('clip-still', still.matches);
      box.classList.remove('clip-on');
      if (still.matches) {
        film.pause();
        film.removeAttribute('autoplay');
        film.load();
      } else run(box);
    }
  };
  for (const box of boxes) {
    const film = box.querySelector('video');
    film.autoplay = false;
    film.tabIndex = -1;
    film.removeAttribute('autoplay');
    box.classList.add('clip-ready');
    // a clip a browser could not decode (a media error, found in Brave on 23 November) is loaded again, and then
    // again from its mp4 alone, so it is never left standing still
    let tries = 0;
    film.addEventListener('error', () => {
      if (still.matches || ++tries > 2) return;
      if (tries === 2) {
        // the source that failed is the one playing now: that one goes, the other is tried
        const bad = film.currentSrc;
        const sources = [...film.querySelectorAll('source')];
        const gone = sources.find((s) => s.src === bad) || sources.find((s) => s.type === 'video/webm');
        if (gone && sources.length > 1) gone.remove();
      }
      film.load();
      run(box);
    });
    const toggle = () => {
      const blocked = box.classList.contains('clip-blocked');
      if (!still.matches && !blocked) return;
      if (film.paused) {
        box.classList.add('clip-on');
        if (document.activeElement === box.querySelector('.clip-play')) film.focus({ preventScroll: true });
        film.play().then(() => {
          // a click is the gesture a browser that blocks autoplay was waiting for: the others try again
          box.classList.remove('clip-blocked');
          for (const other of boxes) if (other !== box && other.classList.contains('clip-blocked')) { other.classList.remove('clip-blocked'); run(other); }
        }).catch(() => box.classList.remove('clip-on'));
      } else {
        film.pause();
        box.classList.remove('clip-on');
      }
    };
    box.querySelector('.clip-play').addEventListener('click', toggle);
    film.addEventListener('click', toggle);
    if (seen) seen.observe(box);
  }
  mode();
  if (still.addEventListener) still.addEventListener('change', mode);
})();
