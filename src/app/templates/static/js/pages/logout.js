/* Broadcast logout only after the user explicitly submits confirmation. */
(function initLogoutConfirmation() {
  'use strict';

  const form = document.querySelector('form[action="/dashboard/logout"]');
  if (!form) return;

  form.addEventListener('submit', function (event) {
    if (form.dataset.submitting === '1') return;
    event.preventDefault();
    form.dataset.submitting = '1';
    const submit = form.querySelector('button[type="submit"]');
    if (submit) {
      submit.disabled = true;
      submit.setAttribute('aria-busy', 'true');
    }
    const payload = JSON.stringify({ type: 'logout', at: Date.now() });
    try {
      window.localStorage.setItem('gitpulse-auth-v1', payload);
    } catch (_) {
      // Storage can be unavailable in private browsing; the POST still works.
    }
    try {
      if ('BroadcastChannel' in window) {
        const channel = new BroadcastChannel('gitpulse-auth-v1');
        channel.postMessage(JSON.parse(payload));
        channel.close();
      }
    } catch (_) {
      // Cross-tab notification is best-effort.
    }
    /* One macrotask, not 140ms: the delay existed only to play an exit
       animation that has been removed. Yielding once still lets the
       BroadcastChannel message above dispatch before the navigation - which is
       exactly what the reduced-motion path always did. */
    setTimeout(function () {
      form.submit();
    }, 0);
  });
})();
