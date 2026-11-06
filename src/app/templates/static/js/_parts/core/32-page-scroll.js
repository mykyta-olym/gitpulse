/* ============================================
   Local Page-Content Scrolling

   The app shell owns scrolling through `.gl-page-content`; scrolling the
   document/window or calling `scrollIntoView()` on page targets can move both
   the inner pane and browser viewport, which shifts fixed chrome. Keep every
   in-app jump on the same local scroller contract used by Issues to Address.
   ============================================ */
function _targetFromHash(hash) {
  const raw = String(hash || '').replace(/^#/, '');
  if (!raw) return null;
  let id = raw;
  try { id = decodeURIComponent(raw); } catch (_) {}
  if (id) {
    const byId = document.getElementById(id);
    if (byId) return byId;
  }
  if (window.CSS && typeof CSS.escape === 'function') {
    try {
      return document.querySelector('[name="' + CSS.escape(id) + '"]');
    } catch (_) {}
  }
  return null;
}

function scrollWithinPageContent(target, options = {}) {
  if (!target || !target.getBoundingClientRect) return false;
  if (target.getClientRects && !target.getClientRects().length) return false;
  const mode = options.block || 'center';
  const behavior = options.behavior || 'smooth';
  const offset = Number.isFinite(options.offset) ? options.offset : 16;
  const explicitRoot = options.root || null;
  const scroller = explicitRoot || target.closest?.('.gl-page-content') || document.querySelector('.gl-page-content');
  if (!scroller || typeof scroller.scrollTo !== 'function') return false;

  try {
    const targetRect = target.getBoundingClientRect();
    const scrollerRect = scroller.getBoundingClientRect();
    let top = scroller.scrollTop + (targetRect.top - scrollerRect.top);

    if (mode === 'center') {
      top -= scroller.clientHeight / 2 - targetRect.height / 2;
    } else if (mode === 'end') {
      top -= scroller.clientHeight - targetRect.height - offset;
    } else if (mode === 'nearest') {
      const above = targetRect.top < scrollerRect.top + offset;
      const below = targetRect.bottom > scrollerRect.bottom - offset;
      if (!above && !below) return true;
      if (below) top = scroller.scrollTop + (targetRect.bottom - scrollerRect.bottom) + offset;
      else top -= offset;
    } else {
      top -= offset;
    }

    scroller.scrollTo({ top: Math.max(0, top), behavior });
    return true;
  } catch (_) {
    return false;
  }
}

GP.scrollWithinPageContent = scrollWithinPageContent;
window.scrollWithinPageContent = scrollWithinPageContent;

function _scrollToHashTarget(hash, opts = {}) {
  const target = _targetFromHash(hash);
  if (!target) return false;
  return scrollWithinPageContent(target, {
    block: opts.block || 'start',
    behavior: opts.behavior || 'smooth',
    offset: Number.isFinite(opts.offset) ? opts.offset : 16,
  });
}


function _scheduleCurrentHashScroll() {
  if (!window.location.hash) return;
  requestAnimationFrame(function () {
    _scrollToHashTarget(window.location.hash, { block: 'start', behavior: 'auto' });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', _scheduleCurrentHashScroll, { once: true });
} else {
  _scheduleCurrentHashScroll();
}

window.addEventListener('hashchange', function () {
  _scrollToHashTarget(window.location.hash, { block: 'start' });
});

// Anchor smooth-scroll for same-page hashes only.
document.addEventListener('click', (event) => {
  const link = event.target.closest('a[href]');
  if (!link || event.defaultPrevented || link.hasAttribute('download')
      || (link.target && link.target !== '_self')) {
    return;
  }
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    return;
  }
  let url;
  try { url = new URL(link.href, window.location.href); } catch (_) { return; }
  if (url.origin !== window.location.origin || url.pathname !== window.location.pathname
      || url.search !== window.location.search || !url.hash) return;
  const href = url.hash;
  const target = _targetFromHash(href);
  if (!target) {
    return;
  }
  event.preventDefault();
  scrollWithinPageContent(target, { block: 'start' });
  try {
    if (window.location.hash !== href) {
      window.history.pushState(null, '', href);
    }
    window.dispatchEvent(new CustomEvent('gp:hashnavigate'));
  } catch (_) {}
}, true);

/* Switches the cut on once the content region has scrolled. GitLab drives the
   same pseudo-element from a `scroll-state` container query, which only Chrome
   supports; a scroll listener does it everywhere. */
function _initScrollScrim() {
  const scroller = document.querySelector('.gl-page-content');
  if (!scroller || scroller._scrimBound) return;
  scroller._scrimBound = true;
  let queued = false;
  const paint = () => {
    queued = false;
    scroller.classList.toggle('is-scrolled', scroller.scrollTop > 0);
  };
  scroller.addEventListener('scroll', () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(paint);
  }, { passive: true });
  paint();
}
