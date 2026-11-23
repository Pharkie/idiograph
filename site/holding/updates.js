(() => {
  const box = document.getElementById('up');
  const form = document.getElementById('up-form');
  const email = document.getElementById('up-email');
  const send = document.getElementById('up-send');
  const said = document.getElementById('up-said');
  const trap = document.getElementById('up-website');
  if (!box || !form || !email || !send || !said) return;
  box.hidden = false;
  const label = send.textContent;
  const looksRight = (v) => v.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  const show = (text, bad) => {
    said.textContent = text;
    said.classList.toggle('bad', Boolean(bad));
    if (bad) email.setAttribute('aria-invalid', 'true');
    else email.removeAttribute('aria-invalid');
  };
  const busy = (on) => {
    send.disabled = on;
    email.readOnly = on;
    send.textContent = on ? 'Sending…' : label;
  };
  email.addEventListener('input', () => { if (said.classList.contains('bad')) show('', false); });
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (send.disabled) return;
    const address = email.value.trim();
    if (!looksRight(address)) { show('That is not an email address.', true); email.focus(); return; }
    show('', false);
    busy(true);
    let status = 0, error = '';
    try {
      const r = await fetch('/api/updates/subscribe', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email: address, source: 'site', version: '', consent: form.dataset.consent || '',
          website: trap ? trap.value : '' }),
        credentials: 'omit',
        cache: 'no-store',
      });
      status = r.status;
      if (status === 400) { try { error = (await r.json()).error || ''; } catch (err) { error = ''; } }
    } catch (err) { status = 0; }
    busy(false);
    if (status === 200) {
      box.classList.add('up-done');
      form.querySelector('.up-row').hidden = true;
      form.querySelector('.up-label').hidden = true;
      show('Check your email to confirm.', false);
      said.focus();
    } else if (status === 400 && error === 'email') {
      show('That is not an email address.', true);
      email.focus();
    } else {
      show('Your sign-up did not go through. Try again later.', true);
      email.removeAttribute('aria-invalid');
    }
  });
})();
