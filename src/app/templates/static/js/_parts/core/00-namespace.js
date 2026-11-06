/**
 * GitPulse - Frontend Core
 *
 * Provides stable, shared primitives used by all pages.
 * Backward compatible with existing global function names.
 */

/* ============================================
   Global Namespace
   ============================================ */
/* A property of window, not a second binding: a bare `GP` anywhere resolves
   to it, in every script. */
window.GP = window.GP || {};

/* ============================================
   Global error suppression - harmless browser noise
   ============================================ */
// Modern browsers abort an in-flight cross-document View Transition
// whenever the navigation terminates without a new document (file
// download, same-tab redirect to binary, or user-initiated cancel).
// That surfaces as an uncaught `AbortError: Transition was skipped`
// which is purely informational - swallow it so it doesn't pollute
// Sentry/console and confuse teachers exporting JSON/CSV.
window.addEventListener('unhandledrejection', (e) => {
  const r = e && e.reason;
  if (!r) return;
  const name = r.name || '';
  const msg = String(r.message || r || '');
  if (name === 'AbortError' && /transition was (skipped|aborted)/i.test(msg)) {
    e.preventDefault();
  }
});
// Same pattern for synchronous rethrows (some Chrome versions fire
// `error` instead of `unhandledrejection` for VT aborts).
window.addEventListener('error', (e) => {
  const r = e && e.error;
  if (!r) return;
  if (r.name === 'AbortError' && /transition was (skipped|aborted)/i.test(String(r.message || ''))) {
    e.preventDefault();
  }
});
// Root-cause handling for cross-document View Transitions.
// `@view-transition { navigation: auto }` (animations.css) drives the
// GPU crossfade between pages. When a transition is skipped - the user
// clicks a second tab/link before the first settles, re-clicks the
// already-active tab (a same-URL navigation), or the tab is hidden
// mid-navigation - the browser rejects the transition's `ready`,
// `finished` and `updateCallbackDone` promises with
// `AbortError: Transition was skipped`. Unless something observes those
// promises they surface as an uncaught "(in promise)" rejection. We
// attach inert handlers through the navigation lifecycle events so the
// skip is always handled at its source rather than relying only on the
// global unhandledrejection sweep above.
function _silenceViewTransition(vt) {
  if (!vt) return;
  ['finished', 'ready', 'updateCallbackDone'].forEach((key) => {
    const p = vt[key];
    if (p && typeof p.catch === 'function') {
      p.catch(() => { /* transition skipped/aborted - expected, ignore */ });
    }
  });
}
// `pageswap` fires on the OUTGOING document, `pagereveal` on the INCOMING
// one; each exposes the active cross-document ViewTransition (if any).
window.addEventListener('pageswap', (e) => _silenceViewTransition(e && e.viewTransition));
window.addEventListener('pagereveal', (e) => _silenceViewTransition(e && e.viewTransition));

function _translateUiText(text, params) {
  const value = text == null ? '' : String(text);
  if (GP.i18n && typeof GP.i18n.t === 'function') {
    return GP.i18n.t(value, params || null);
  }
  return value;
}

GP.t = _translateUiText;
