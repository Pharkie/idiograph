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
    if (!seen || shown.has(box)) film.play().catch(() => {});
    else film.pause();
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
    film.removeAttribute('autoplay');
    box.classList.add('clip-ready');
    const toggle = () => {
      if (!still.matches) return;
      if (film.paused) {
        box.classList.add('clip-on');
        film.play().catch(() => box.classList.remove('clip-on'));
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
