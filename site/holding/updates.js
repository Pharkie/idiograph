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
  // an answer that went wrong reads as the field's own: the line straight under it. Only a bad address marks the field
  // (its border and aria-invalid), since a sign-up that did not go through is not the field's fault
  const show = (text, bad, fieldAtFault) => {
    said.textContent = text;
    said.classList.toggle('bad', Boolean(bad));
    if (bad && fieldAtFault !== false) email.setAttribute('aria-invalid', 'true');
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
      // done: the address as plain words in place of the field and its button, and the line saying what comes next
      box.classList.add('up-done');
      form.querySelector('.up-row').hidden = true;
      form.querySelector('.up-label').hidden = true;
      const sent = document.createElement('p');
      sent.className = 'up-sent';
      sent.textContent = address;
      sent.tabIndex = -1;
      said.before(sent);
      show('Check your email to confirm.', false);
      // focus goes to the address line, outside the status region, so the confirmation is announced once, by the status
      sent.focus();
    } else if (status === 400 && error === 'email') {
      show('That is not an email address.', true);
      email.focus();
    } else {
      show('Your sign-up did not go through. Try again later.', true, false);
      send.focus();
    }
  });
})();
