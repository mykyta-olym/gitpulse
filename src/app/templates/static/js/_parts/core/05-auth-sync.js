/* ============================================
   Auth Cross-Tab Sync
   ============================================
   Keeps every open GitPulse tab in lockstep with the user's auth state.

   Scenarios covered:
   - Login in tab A while tab B sits on /dashboard/login   -> B navigates to /dashboard/
     (handled inside pages/login.js, but we still surface the channel here so
     non-login pages stay silent rather than crash).
   - Logout in tab A (click on /dashboard/logout link)     -> every other tab
     navigates to /dashboard/login so we never leave a stale, "ghost-authed"
     surface that will 401 on its next XHR.
   - Server-driven session expiry (any 401 response)        -> broadcast the
     same logout signal so siblings join the redirect rather than each
     discovering the dead session independently.

   Mechanism: BroadcastChannel('gitpulse-auth-v1') with a localStorage
   `storage` event fallback for Safari private mode / older WebViews. The
   localStorage key is wiped right after writing so a future setItem with
   the same payload still fires the event in other tabs.
*/
const _AUTH_CHANNEL = 'gitpulse-auth-v1';
const _LOGIN_PATH = '/dashboard/login';
let _authBC = null;
try {
  if (typeof BroadcastChannel !== 'undefined') {
    _authBC = new BroadcastChannel(_AUTH_CHANNEL);
  }
} catch (_) { /* private mode / unsupported */ }

function _isOnLoginPage() {
  try { return window.location.pathname.startsWith(_LOGIN_PATH); }
  catch (_) { return false; }
}

function _broadcastAuthEvent(type) {
  const payload = { type: type, at: Date.now() };
  try { localStorage.setItem(_AUTH_CHANNEL, JSON.stringify(payload)); } catch (_) {}
  try { localStorage.removeItem(_AUTH_CHANNEL); } catch (_) {}
  if (_authBC) { try { _authBC.postMessage(payload); } catch (_) {} }
}

let _authRedirectScheduled = false;
/* Unified redirect-to-login helper.
   - Idempotent: only ever schedules one redirect.
   - Adds ?next=<current path+query> so the user lands back where they were.
   - Uses location.replace() to avoid back-button trapping the user on the
     dead page (which would just bounce them back to /login again).
   - Broadcasts session-expired so sibling tabs redirect too.
   - Skips when the user is already on /dashboard/login.
   - When `silent` is true, no toast is shown (used for cross-tab events
     where the originating tab already showed one). */
function _redirectToLogin(opts) {
  if (_authRedirectScheduled) return;
  if (_isOnLoginPage()) return;
  _authRedirectScheduled = true;
  const o = opts || {};
  if (!o.silent) {
    try { showToast(GP.t('Session expired. Redirecting to login...'), 'warning', 3000); } catch (_) {}
  }
  try { _broadcastAuthEvent('session-expired'); } catch (_) {}
  let target = _LOGIN_PATH;
  try {
    const here = window.location.pathname + window.location.search;
    // Don't redirect-loop through /login as the next target.
    if (here && !here.startsWith(_LOGIN_PATH)) {
      target = _LOGIN_PATH + '?next=' + encodeURIComponent(here);
    }
  } catch (_) {}
  setTimeout(function () {
    try { window.skipBeforeunload && window.skipBeforeunload(); } catch (_) {}
    try { window.location.replace(target); }
    catch (_) { window.location.href = target; }
  }, o.delay != null ? o.delay : 1500);
}

function _handleRemoteAuth(payload) {
  if (!payload || typeof payload !== 'object') return;
  if (payload.type === 'logout' || payload.type === 'session-expired') {
    if (_isOnLoginPage() || _authRedirectScheduled) return;
    _authRedirectScheduled = true;
    try { window.skipBeforeunload && window.skipBeforeunload(); } catch (_) {}
    // Reload via login redirect so the server can render its own state.
    window.location.replace(_LOGIN_PATH);
  } else if (payload.type === 'login') {
    // Non-login pages don't react to remote login events - they are
    // already authenticated. Only the /dashboard/login page cares,
    // and pages/login.js installs its own handler.
  }
}

if (_authBC) {
  _authBC.onmessage = function (ev) { _handleRemoteAuth(ev && ev.data); };
}
window.addEventListener('storage', function (ev) {
  if (!ev || ev.key !== _AUTH_CHANNEL || !ev.newValue) return;
  try { _handleRemoteAuth(JSON.parse(ev.newValue)); } catch (_) {}
});
