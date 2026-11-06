/* ============================================
   In-place page reload
   The app's one "load this page again" primitive: a cache-busted navigation to
   the same URL, flagged so the next load comes up without the entrance
   animation. The name is historical - a reload deliberately lands at the TOP
   (see _resetScrollOnLoad below), and the scroll offset it used to save was
   read back by nothing; saving it cost a forced layout on every reload.
   ============================================ */
const _REFRESH_PARAM = '_gp_refresh';

function _cacheBustedCurrentUrl() {
  const url = new URL(window.location.href);
  url.searchParams.set(_REFRESH_PARAM, String(Date.now()));
  return url.toString();
}

let _reloadInFlight = false;
function reloadKeepScroll() {
  // Guard against double reloads: a single settings save can fan out more than
  // one SSE 'settings_changed' (course + team streams, plus the recompute
  // follow-up). Each listener calls this, and two near-simultaneous reloads
  // made the page visibly flash twice. The first call wins; later ones within
  // the same tick are no-ops because navigation is already under way.
  if (_reloadInFlight) return;
  _reloadInFlight = true;
  // Flag the next load as a silent in-place reload: theme-bootstrap reads this
  // before first paint and suppresses the entrance animation, so the page comes
  // back without replaying it.
  try { sessionStorage.setItem('_gp_silent_reload', '1'); } catch (_) { /* storage */ }
  GP.skipBeforeunload();
  _preserveFlashToast();
  window.location.assign(_cacheBustedCurrentUrl());
}

/* Refresh / reload lands at the TOP of the page, YouTube-style. The old code
   restored the previous scroll position by re-writing scrollTop every 120ms for
   5 seconds, fighting the lazy data that grows the page - which read as the page
   "jumping around for seconds" after every refresh. Simpler and predictable:
   turn OFF the browser's own restoration, strip the reload cache-buster, drop
   any saved offsets (incl. those left by an older build), and start every load
   at the top of the shell scroller. */
(function _resetScrollOnLoad() {
  try {
    if ('scrollRestoration' in window.history) window.history.scrollRestoration = 'manual';
  } catch (_) { /* history unavailable */ }

  try {
    const url = new URL(window.location.href);
    if (url.searchParams.has(_REFRESH_PARAM)) {
      url.searchParams.delete(_REFRESH_PARAM);
      const clean = url.pathname + url.search + url.hash;
      window.history.replaceState(window.history.state, '', clean || url.pathname);
    }
  } catch (_) { /* URL/history unavailable */ }

  // Consume the silent-reload flag (set by reloadKeepScroll, read pre-paint by
  // theme-bootstrap).
  try {
    sessionStorage.removeItem('_gp_silent_reload');
  } catch (_) { /* storage unavailable */ }

  const _toTop = function () {
    const el = document.querySelector('.gl-page-content');
    if (el) el.scrollTop = 0; else window.scrollTo(0, 0);
  };
  _toTop();
  document.addEventListener('DOMContentLoaded', _toTop);
})();

window.reloadKeepScroll = reloadKeepScroll;
GP.reloadKeepScroll = reloadKeepScroll;
GP.cacheBustedCurrentUrl = _cacheBustedCurrentUrl;

document.addEventListener('click', function _handleDeclarativeReload(event) {
  const target = event.target instanceof Element ? event.target : event.target?.parentElement || null;
  const trigger = target ? target.closest('[data-action="reload-keep-scroll"]') : null;
  if (!trigger) return;
  event.preventDefault();
  reloadKeepScroll();
});

/* ============================================
   Auto-reload on background job completion
   Centralised handler so page-level scripts don't have to
   duplicate the _suppressReload / sessionStorage guard pattern.

   Usage:  GP.autoReloadOnJob(['sync*', 'import']);
   Patterns ending in '*' match any jobType that starts with that prefix.

   The registration is PAGE-SCOPED. core.bundle.js survives SPA navigation, so
   patterns registered by (say) Admin > Courses used to outlive that page: a sync
   finishing while the reader sat on the Dashboard then hard-reloaded THAT page
   via window.location.assign - a page that never opted in, with the URL visibly
   gaining ?_gp_refresh=. Navigation clears the list (see GP.clearJobReload);
   each page re-registers on arrival because its bundle re-runs.
   ============================================ */
let _jobReloadRegistered = false;
let _jobReloadTimer = null;
const _jobReloadPatterns = [];
let _jobReloadSuppressed = false;
const _JOB_RELOAD_KEY = '_gp_job_reload_done';

try {
  if (sessionStorage.getItem(_JOB_RELOAD_KEY)) {
    sessionStorage.removeItem(_JOB_RELOAD_KEY);
    _jobReloadSuppressed = true;
  }
} catch (_) { /* storage unavailable */ }

function _matchesJobPattern(jobType) {
  for (let i = 0; i < _jobReloadPatterns.length; i++) {
    const p = _jobReloadPatterns[i];
    if (p.charAt(p.length - 1) === '*') {
      if (jobType.indexOf(p.slice(0, -1)) === 0) return true;
    } else {
      if (jobType === p) return true;
    }
  }
  return false;
}

function _onJobComplete(ev) {
  if (_jobReloadSuppressed) return;
  const d = ev.detail || {};
  if (d.status !== 'done') return;
  const jt = d.jobType || '';
  if (!_matchesJobPattern(jt)) return;
  if (_jobReloadTimer) return;
  _jobReloadTimer = setTimeout(function () {
    _jobReloadTimer = null;
    try { sessionStorage.setItem(_JOB_RELOAD_KEY, '1'); } catch (_) {}
    // No toast here: the global job bar already showed the terminal
    // "Sync completed!" / "Checks completed" toast. A second "Data updated"
    // info toast just stacked a duplicate on every sync/import/run-checks.
    reloadKeepScroll();
  }, 1200);
}

/**
 * Register job types that should trigger an automatic page reload.
 * Can be called multiple times - patterns are merged.
 * @param {string[]} patterns  e.g. ['sync*', 'import']
 */
GP.autoReloadOnJob = function autoReloadOnJob(patterns) {
  for (let i = 0; i < patterns.length; i++) {
    if (_jobReloadPatterns.indexOf(patterns[i]) === -1) {
      _jobReloadPatterns.push(patterns[i]);
    }
  }
  if (!_jobReloadRegistered) {
    _jobReloadRegistered = true;
    window.addEventListener('gp:job-complete', _onJobComplete);
  }
};

/* Drop every registration - called when navigation leaves the page that opted
   in. With an empty list _onJobComplete matches nothing, so the listener stays
   attached but inert until the next page registers. */
GP.clearJobReload = function clearJobReload() {
  _jobReloadPatterns.length = 0;
  if (_jobReloadTimer) { clearTimeout(_jobReloadTimer); _jobReloadTimer = null; }
};
