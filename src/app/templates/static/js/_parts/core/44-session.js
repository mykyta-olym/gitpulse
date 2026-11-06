/* ============================================
   App version mismatch detection
   Compares the initial build hash (from <meta name="app-version">)
   against the X-App-Version header on subsequent responses.
   When a new deploy is detected, show a toast and hard-reload
   on the next user navigation so stale JS/HTML never lingers.
   ============================================ */
const _APP_VERSION = (function () {
  const el = document.querySelector('meta[name="app-version"]');
  return el ? el.getAttribute('content') : '';
})();
let _versionMismatch = false;

function _checkVersionHeader(headers) {
  if (_versionMismatch || !_APP_VERSION) return;
  let serverVersion = null;
  if (typeof headers === 'object' && headers !== null) {
    if (typeof headers.get === 'function') {
      serverVersion = headers.get('x-app-version');
    }
  }
  if (!serverVersion) return;
  if (serverVersion !== _APP_VERSION) {
    _versionMismatch = true;

    // Guard against infinite reload loops - if we already reloaded for this
    // version, don't trigger another reload (stale cache edge case).
    const reloadKey = 'gitpulse_version_reload_v2';
    try {
      const prev = sessionStorage.getItem(reloadKey);
      if (prev === serverVersion) return;  // already reloaded for this version
      sessionStorage.setItem(reloadKey, serverVersion);
    } catch (_) { /* storage unavailable */ }

    showToast(GP.t('A new version is available. The page will refresh shortly.'), 'info', 7000);

    /* Wait for a QUIET moment, not just a fixed six seconds.
       `hasUnsavedState` only knows about dirty forms, so a reader who had just
       set a filter, opened a menu or started typing in a search box lost it
       mid-action and saw the page reset itself for no reason they could
       connect to anything - reported as "the filters sometimes reset and
       refresh the page on their own". Reloading is right; doing it out from
       under someone's hands is not. */
    const IDLE_MS = 6000;
    let _lastTouch = Date.now();
    const _mark = function () { _lastTouch = Date.now(); };
    ['pointerdown', 'keydown', 'input', 'change', 'scroll'].forEach(function (evt) {
      document.addEventListener(evt, _mark, { passive: true, capture: true });
    });

    const _reload = function () {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function (regs) {
          Promise.all(regs.map(r => r.unregister())).then(() => reloadKeepScroll());
        }).catch(() => reloadKeepScroll());
      } else {
        reloadKeepScroll();
      }
    };

    const _tryReload = function () {
      if (hasUnsavedState()) {
        showToast(GP.t('A new version is available. Please save your work and refresh the page.'), 'warning', 0);
        return;   // never nags again; the reader refreshes when they are ready
      }
      const quietFor = Date.now() - _lastTouch;
      if (quietFor < IDLE_MS) {
        /* Still working. Come back when the remaining quiet time has passed. */
        setTimeout(_tryReload, IDLE_MS - quietFor);
        return;
      }
      _reload();
    };
    setTimeout(_tryReload, IDLE_MS);
  }
}

/* ============================================
   Session validity check
   Piggy-backs on health-monitor state changes so we don't
   duplicate heartbeat requests.  Every 3rd "ok" health event
   triggers a lightweight session-check fetch.
   ============================================ */
(function _initSessionCheck() {
  const SESSION_CHECK_INTERVAL = 3;
  const isLoginPage = /\/login\b/.test(window.location.pathname);
  if (isLoginPage) return;

  let okCount = 0;
  let stopped = false;

  document.addEventListener('gp-health-change', async function (e) {
    if (stopped) return;
    const detail = e.detail || {};
    if (detail.current !== 'ok') return;
    okCount += 1;
    if (okCount % SESSION_CHECK_INTERVAL !== 0) return;

    try {
      const sessTimeout = _createTimeoutSignal(5000, null);
      const sessResp = await fetch('/dashboard/session-check', {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
        signal: sessTimeout.signal,
      });
      sessTimeout.cleanup();
      // Check version header from session-check response
      _checkVersionHeader(sessResp.headers);
      if (sessResp.status === 401) {
        // Stop polling so we don't fire repeated toasts while the redirect
        // settles (and to be safe if the redirect is somehow blocked).
        stopped = true;
        _redirectToLogin();
      }
    } catch (_e) {
      // Network error - handled by health-monitor banner
    }
  });
})();

/* ============================================
   One-time notification consumption
   Fetches pending notifications from the server (e.g. "you were
   assigned as teacher to ZSI by admin") and shows them as toasts.
   ============================================ */
(function _initNotificationCheck() {
  const isLoginPage = /\/login\b/.test(window.location.pathname);
  if (isLoginPage) return;

  setTimeout(async function () {
    try {
      const data = await apiCall('/dashboard/notifications', 'GET', null, { maxRetries: 0 });
      const items = data && data.notifications;
      if (!items || !items.length) return;
      items.forEach(function (n) {
        showToast(n.message || '', n.type || 'info', 8000);
      });
    } catch (_) { /* ignore */ }
  }, 1500);
})();

/* ============================================
   Post-login welcome toast
   Detects ?login=1 or ?welcome_back=1 query params added by
   the OAuth callback and shows an appropriate toast.
   ============================================ */
(function _initLoginToast() {
  const params = new URLSearchParams(window.location.search);
  if (params.has('login') || params.has('welcome_back')) {
    const msg = params.has('login')
      ? (GP.t('Welcome! You have been signed in successfully.'))
      : (GP.t('Welcome back! You have been signed in successfully.'));
    setTimeout(function () { showToast(msg, 'success', 5000); }, 300);
    // Clean up the URL
    try {
      params.delete('login');
      params.delete('welcome_back');
      const clean = params.toString();
      const newUrl = window.location.pathname + (clean ? '?' + clean : '') + window.location.hash;
      window.history.replaceState(null, '', newUrl);
    } catch (_) { /* ignore */ }
  }
})();



/* ============================================
   bfcache (Back-Forward Cache) reload
   When the browser serves a page from its bfcache on back/forward
   navigation, the DOM is stale (e.g. course lists, stats).  Detect
   this and trigger a fresh server load so data is always current.
   ============================================ */
window.addEventListener('pageshow', function (event) {
  if (event.persisted) {
    reloadKeepScroll();
  }
});
