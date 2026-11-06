/* ============================================
   Smooth banner enter / exit
   ============================================
   Banners inserted AFTER the page settles (GitLab-token warning, the live
   "sync failed" card, or any dynamically-added .info-card) otherwise pop into
   place and shove the content below in one jarring jump. These helpers ease
   the height + opacity + margin so the surrounding layout opens and closes
   smoothly. Banners that arrive as part of a lazy-content swap are already
   animated by the stagger reveal (_revealSwapped), so a MutationObserver below
   deliberately skips anything added within the swap window to avoid the
   documented double-animation regression. */
/** Ease a freshly-inserted banner open (height 0 -> natural). Idempotent.
 *  Shares the disclosure contract with <details> and collapsible card bodies:
 *  height, opacity, margin and padding open together, so the layout below eases
 *  down instead of being shoved. */
function revealBanner(el) {
  if (!el || el.nodeType !== 1 || el.dataset.bannerRevealed === '1') return;
  el.dataset.bannerRevealed = '1';
  if (!el.getBoundingClientRect().height) return;
  GP.motion.disclose(el, true);
}

/** Collapse an element closed (fade, then height -> 0) and remove it.
 *  THE removal animation for the whole app - banners, cards, table rows. There
 *  used to be four: this one, `.fade-out` + a 300 ms timer, `.card-dismissing`
 *  + a 300 ms timer, and a bare `.remove()`, so the same "delete" felt
 *  different depending on which list you were looking at. GP.motion owns the
 *  timing and reports back when the node is really gone, which removes the
 *  hand-written transitionend-plus-fallback pair that could both fire. */
function collapseBanner(el, cb) {
  if (!el || el.nodeType !== 1) { if (cb) cb(); return; }
  if (el.dataset.bannerCollapsing === '1') return;
  el.dataset.bannerCollapsing = '1';
  GP.motion.dismiss(el, cb);
}
GP.revealBanner = revealBanner;
GP.collapseBanner = collapseBanner;
// Generic alias: any single element (card / list row) removed WITHOUT a full
// list re-render should collapse smoothly instead of vanishing. Reduced-motion
// removes instantly. (Full-list reloads are already animated by the reveal.)
GP.collapseAndRemove = collapseBanner;

// Auto-reveal genuinely dynamic banner insertions. Swap-driven insertions are
// owned by the stagger reveal, so we only animate banners added OUTSIDE the
// short window after an htmx swap (tracked by _lastSwapAt below).
let _lastSwapAt = 0;
try {
  const _bannerObserver = new MutationObserver((mutations) => {
    if (Date.now() - _lastSwapAt < 700) return; // swap-driven -> reveal owns it
    for (const m of mutations) {
      m.addedNodes.forEach((node) => {
        if (node.nodeType !== 1) return;
        const card = node.classList && node.classList.contains('info-card')
          ? node
          : (node.querySelector && node.querySelector('.info-card'));
        if (card && card.dataset.bannerRevealed !== '1') {
          revealBanner(card);
        }
      });
    }
  });
  const _startObserving = () => {
    if (document.body) _bannerObserver.observe(document.body, { childList: true, subtree: true });
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _startObserving, { once: true });
  } else {
    _startObserving();
  }
} catch (_) { /* MutationObserver unavailable - banners simply appear instantly */ }

document.addEventListener('click', (event) => {
  const dismissBtn = event.target.closest('.info-card-dismiss, .gp-top-banner-dismiss');
  if (dismissBtn) {
    const banner = dismissBtn.closest('[data-dismiss-key]')
      || dismissBtn.closest('.info-card, .gp-top-banner');
    if (banner) {
      _rememberDismissed(banner.getAttribute('data-dismiss-key'));
      collapseBanner(banner);
    }
  }
});

// Prune already-dismissed banners on first paint and after HTMX swaps re-inject them.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => _hideDismissedBanners(), { once: true });
} else {
  _hideDismissedBanners();
}
document.body?.addEventListener('htmx:afterSwap', (evt) => {
  _lastSwapAt = Date.now();
  try { _hideDismissedBanners(evt.target); } catch (_) { /* noop */ }
  try { initCardInfoTips(evt.target); } catch (_) { /* noop */ }
});
// Cross-tab: dismissing a banner in one tab prunes it live in the others.
window.addEventListener('storage', (evt) => {
  if (evt.key === _DISMISS_STORE_KEY) {
    try { _hideDismissedBanners(); } catch (_) { /* noop */ }
  }
});

document.addEventListener('submit', (event) => {
  const form = event.target.closest('form');
  if (!form) {
    return;
  }

  /* `data-confirm` on a form: ask on the app's dialog, not the browser's.
     A submit handler cannot await, so stop this submit, ask, and re-submit on
     confirm - marking the form so the second pass runs straight through. */
  const confirmMessage = form.dataset.confirm || '';
  if (confirmMessage && form.dataset.confirmed !== '1') {
    event.preventDefault();
    GP.confirmDialog({ message: _translateUiText(confirmMessage) }).then(function (ok) {
      if (!ok) return;
      form.dataset.confirmed = '1';
      if (typeof form.requestSubmit === 'function') form.requestSubmit();
      else form.submit();
      delete form.dataset.confirmed;
    });
    return;
  }

  if (form.dataset.submitAction) {
    event.preventDefault();
    _runDataAction(form, event, 'submitAction', 'submitArgs');
    return;
  }

});

document.addEventListener('change', (event) => {
  const target = event.target.closest('[data-change-action]');
  if (!target) {
    return;
  }
  _runDataAction(target, event, 'changeAction', 'changeArgs');
});

document.addEventListener('keyup', (event) => {
  const target = event.target.closest('[data-keyup-action]');
  if (!target) {
    return;
  }
  _runDataAction(target, event, 'keyupAction', 'keyupArgs');
});
