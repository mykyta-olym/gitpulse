/* ============================================
   Auto-init
   ============================================ */
function _initCoreUi() {
  _teleportNestedModals();
  _initServiceWorker();
  initTooltips();
  initDatePickers(document);
  initResponsiveTableLabels(document);
  initDataDrivenStyles(document);
  _initScrollScrim();
}


function _initServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  /* When a deploy ships a new service worker (bumped CACHE_VERSION), it activates
     immediately (skipWaiting + clients.claim) and takes control of this tab -
     `controllerchange` fires. A tab that has been sitting open across that deploy
     is genuinely stale and has to reload once, or it keeps showing yesterday's
     JS/CSS until a hard refresh.

     But a page the user JUST loaded is not stale: its HTML already references
     the new content-hashed asset URLs, and the new worker claims control a
     moment after registration - so the old unconditional reload turned every
     manual refresh into two. A ten-second settle window was the first answer,
     and it held only while the server answered fast: right after a restart the
     worker's install runs past any window, `controllerchange` landed at
     fifteen seconds and the page reloaded itself out from under a reader who
     was scrolling - "I refresh, it refreshes again and hangs while I scroll".

     Taking control says nothing about whether THIS page is behind. The server
     does: its X-App-Version against the page's own is exactly what the version
     check reads on every response, and that path reloads once, at a quiet
     moment, with a notice. So a new worker asks that question instead of
     reloading on its own clock. */
  if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.addEventListener('controllerchange', function () {
      fetch('/dashboard/session-check', { method: 'GET', credentials: 'same-origin', cache: 'no-store' })
        .then(function (resp) {
          if (typeof _checkVersionHeader === 'function') _checkVersionHeader(resp.headers);
        })
        .catch(function () { /* offline or mid-restart: the next poll asks again */ });
    });
  }
  navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () {});
}

/* Fixed dialogs belong outside the page's CSS containment. Return moved roots
   so the caller can initialise them after they leave the swapped subtree. */
function _teleportNestedModals(root) {
  const scope = root || document;
  const moved = [];
  scope.querySelectorAll('.modal-backdrop').forEach(function (m) {
    // Keep page dialogs under the same Alpine gate until their factories load.
    if (m.closest('[x-ignore]')) return;
    if (m.parentElement && m.parentElement !== document.body) {
      // Navigation disposes page dialogs while global shell dialogs stay mounted.
      if (m.closest('#gp-modals') || m.closest('#main-content')) {
        m.setAttribute('data-gp-page-modal', '1');
      }
      document.body.appendChild(m);
      moved.push(m);
    }
  });
  return moved;
}

/* Remove the outgoing page's teleported modals. Only ones marked as page-scoped
   above: a modal that base.html renders outside the swapped regions must stay.

   Removing the modal is NOT enough on its own. flatpickr appends its calendar to
   <body>, beside the modal rather than inside it, so dropping the modal orphaned
   the calendar - and each calendar carries an id derived from its input
   (`courseSemesterStart-fp-0`). Every navigation minted another set, so after
   three laps around the sidebar the page held three copies of four ids and
   DevTools reported duplicate form field ids. Destroy the instance first: that
   is what removes the calendar and restores the original input. */
function _dropPageModals() {
  document.querySelectorAll('body > [data-gp-page-modal]').forEach(function (m) {
    _disposeModal(m);
    m.querySelectorAll('input, select, textarea').forEach(function (el) {
      if (el._flatpickr && typeof el._flatpickr.destroy === 'function') {
        try { el._flatpickr.destroy(); } catch (_) { /* already gone */ }
      }
    });
    m.remove();
  });
}
GP.dropPageModals = _dropPageModals;

/* Wait for DOMContentLoaded whenever the document is still being set up -
   'interactive' included. core.bundle.js is a <script defer>, so it EXECUTES at
   readyState 'interactive', i.e. before the deferred vendor libs that follow it
   in <head> have run. Taking the `else` branch there called _initCoreUi() while
   window.flatpickr was still undefined, and initFlatpickr's `typeof !==
   'function'` guard returned silently: no date input on any page ever got a
   picker on first paint (only a later htmx swap re-ran the init). DOMContentLoaded
   fires after every deferred script has executed, so the vendor libs are ready. */
if (document.readyState === 'loading' || document.readyState === 'interactive') {
  document.addEventListener('DOMContentLoaded', _initCoreUi, { once: true });
} else {
  _initCoreUi();
}
