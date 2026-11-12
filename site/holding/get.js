(() => {
  const FILES = 'https://github.com/Pharkie/idiograph/releases/latest/download/';
  const box = document.getElementById('get');
  const line = document.getElementById('get-line');
  const other = document.getElementById('get-other');
  if (!box || !line || !other) return;
  const ua = navigator.userAgent || '';
  const uad = navigator.userAgentData;
  const plat = (uad && uad.platform) || navigator.platform || '';
  const touchMac = /Mac/i.test(plat) && navigator.maxTouchPoints > 1;
  const phone = (uad && uad.mobile) || /iPhone|iPad|iPod|Android|Mobile/i.test(ua) || touchMac;
  let os = '';
  if (phone) os = 'phone';
  else if (/CrOS/.test(ua)) os = '';
  else if (/Win/i.test(plat) || /Windows/.test(ua)) os = 'windows';
  else if (/Mac/i.test(plat) || /Macintosh/.test(ua)) os = 'mac';
  else if (/Linux/i.test(plat) || /Linux|X11/.test(ua)) os = 'linux';

  const el = (tag, cls, text, href) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    if (href) e.href = href;
    return e;
  };
  const plain = (text) => { line.textContent = text; };
  const offer = (label, file, note, alt) => {
    const row = el('p', 'get-row');
    row.appendChild(el('a', 'dl', label, FILES + file));
    if (alt) row.appendChild(el('a', 'dl-alt', alt[0], FILES + alt[1]));
    line.replaceWith(row);
    if (note) row.after(el('p', 'get-note', note));
    other.textContent = 'Other downloads';
  };

  const firstOpen = (which) => {
    const own = document.getElementById('fo-' + which);
    if (!own) return;
    own.parentNode.prepend(own);
    own.open = true;
  };

  const intelMac = async () => {
    try {
      if (uad && uad.getHighEntropyValues) {
        const v = await uad.getHighEntropyValues(['architecture']);
        if (v && v.architecture) return v.architecture === 'x86';
      }
    } catch (e) { }
    try {
      const gl = document.createElement('canvas').getContext('webgl');
      if (!gl) return false;
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      const r = String(gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER) || '');
      return /Intel|AMD|Radeon|NVIDIA|GeForce/i.test(r);
    } catch (e) { return false; }
  };

  if (os === 'windows') offer('Download for Windows', 'Idiograph-Setup.exe');
  else if (os === 'linux') offer('Download for Linux', 'Idiograph-amd64.deb', 'The .deb is for Ubuntu, Debian and Mint.', ['Other Linux: AppImage', 'Idiograph-x86_64.AppImage']);
  else if (os === 'phone') plain('Idiograph is a desktop app for Mac, Windows and Linux. Visit this page on one of those computers to download it.');
  else if (os === 'mac') {
    intelMac().then((intel) => {
      if (intel) plain('Idiograph for Mac needs an Apple Silicon Mac (M1 or later), and this looks like an Intel Mac.');
      else offer('Download for Mac', 'Idiograph.dmg', 'For Apple Silicon Macs (M1 or later).');
      if (!intel) firstOpen('mac');
    });
  }
  if (os === 'windows') firstOpen('windows');
})();
