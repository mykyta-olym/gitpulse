/**
 * Cookie Consent - GitLab js-cookie pattern.
 *
 * Works on ALL pages: login, dashboard, error pages.
 * Requires: cookies.js (must be loaded first).
 *
 * Uses the GitLab-standard Cookies API:
 *   Cookies.set(name, value, { expires })
 *   Cookies.get(name)
 *   Cookies.remove(name)
 *
 * Usage: <script src="/static/js/cookies.js"></script>
 *        <script src="/static/js/cookie-consent.js"></script>
 *        (must be loaded AFTER the #cookieConsent element)
 */
(function initCookieConsent() {
  'use strict';

  const COOKIE_NAME = 'gp_cookie_consent';
  const COOKIE_DAYS = 365;
  const SYNC_CHANNEL = 'gp_cookie_consent_sync';

  /* -- DOM refs -- */
  const banner       = document.getElementById('cookieConsent');
  const acceptBtn    = document.getElementById('cookieAcceptBtn');
  const essentialBtn = document.getElementById('cookieEssentialBtn');
  const dismissBtn   = document.getElementById('cookieDismissBtn');

  if (!banner) return;

  function dismiss() {
    if (banner.classList.contains('d-none')) return;
    banner.classList.add('cookie-banner-leaving');
    setTimeout(function() {
      banner.classList.add('d-none');
      banner.classList.remove('cookie-banner-leaving');
    }, 280);
  }

  /* -- cross-tab sync: hide the banner when another tab accepts -- */
  let bc = null;
  try {
    if ('BroadcastChannel' in window) {
      bc = new BroadcastChannel(SYNC_CHANNEL);
      bc.addEventListener('message', function (ev) {
        if (ev && ev.data && ev.data.kind === 'accepted') dismiss();
      });
      window.addEventListener('pagehide', function () {
        try { bc.close(); } catch (_) {}
      });
    }
  } catch (_) { /* noop */ }

  async function setConsent(level) {
    try { await Cookies.setAsync(COOKIE_NAME, level, { expires: COOKIE_DAYS }); } catch (_) {}
    dismiss();
    try {
      window.dispatchEvent(
        new CustomEvent('gp:cookie-consent', { detail: { level: level } })
      );
    } catch (_) { /* fallback - not critical */ }
    try { bc && bc.postMessage({ kind: 'accepted', level: level }); } catch (_) {}
  }

  /* -- init -- */
  if (!Cookies.getInitial(COOKIE_NAME)) {
    /* Authenticated users (on /dashboard/) have implicitly consented
       to essential cookies - auto-accept so the banner does not
       reappear on every new device / browser. */
    if (window.location.pathname.indexOf('/dashboard') === 0) {
      Cookies.setAsync(COOKIE_NAME, 'accepted', { expires: COOKIE_DAYS }).catch(() => {});
    } else {
      banner.classList.remove('d-none');
    }
  }

  if (acceptBtn) {
    acceptBtn.addEventListener('click', function () { setConsent('accepted'); });
  }
  if (essentialBtn) {
    essentialBtn.addEventListener('click', function () { setConsent('essential'); });
  }
  if (dismissBtn) {
    dismissBtn.addEventListener('click', function () { setConsent('accepted'); });
  }

})();
