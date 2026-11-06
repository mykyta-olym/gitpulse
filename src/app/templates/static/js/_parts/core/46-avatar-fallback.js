/* ============================================
   Avatar / image fallback (CSP-safe replacement for inline onerror)
   - Avatars: auto-retry once before showing letter fallback.
   - Resilient to laptop sleep / network drop: when the browser is offline
     (or the page was just resumed from BFCache / sleep), we DEFER the
     fallback decision and retry the original image once connectivity
     returns. Otherwise every avatar across the app would silently degrade
     to a letter placeholder after even a brief network glitch.
   - Generic images with data-img-fallback: hide on error.
   The picture lies over its initial inside one `.gl-avatar` box
   (components/avatar.html), so falling back is hiding the picture.
   ============================================ */
function _gpAvatarShowFallback(img) {
  if (!img || img.tagName !== 'IMG') return;
  if (!img.hasAttribute('data-avatar-fallback')) return;
  img.classList.add('gl-hidden');
  delete img.dataset.avatarPending;
}

/* GlAvatar's identicon colour for a key, 1-7: the sum of its character codes,
   exactly as `identicon()` in app/template_helpers.py - so the server and a
   script give one person or group the same colour. */
function identicon(key) {
  const s = String(key || '');
  let sum = 0;
  for (let i = 0; i < s.length; i++) sum += s.charCodeAt(i);
  return sum % 7 + 1;
}
GP.identicon = identicon;

/* THE avatar, in JS - the `avatar` macro (components/avatar.html): the
   initial as an identicon, the picture laid over it. No url, no picture: the
   initial alone is the resting state. `opts.key` colours the identicon
   (default: the name); `opts.entity` draws a course, group or project as
   GitLab's square. */
function avatarHtml(url, name, size, opts) {
  const o = opts || {};
  const label = String(name || '?');
  const px = size || 24;
  const img = url
    ? '<img src="' + escapeHtml(url) + '" alt="" class="gl-avatar-img" width="' + px + '" height="' + px +
      '" loading="lazy" decoding="async" referrerpolicy="no-referrer" data-avatar-fallback>'
    : '';
  return '<span class="gl-avatar gl-avatar-s' + px + (o.entity ? ' gl-avatar-rect' : '') +
    ' gl-avatar-identicon-bg' + identicon(o.key || label) + '" aria-hidden="true">' +
    escapeHtml(label.charAt(0).toUpperCase()) + img + '</span>';
}
GP.avatarHtml = avatarHtml;

function _gpAvatarRestore(img) {
  // Re-show the picture over its initial, then trigger a fresh load.
  if (!img || img.tagName !== 'IMG') return;
  if (!img.hasAttribute('data-avatar-fallback')) return;
  const orig = img.dataset.avatarOriginalSrc;
  if (!orig) return;
  img.classList.remove('gl-hidden');
  delete img.dataset.avatarRetried;
  delete img.dataset.avatarPending;
  // Cache-bust to bypass any stale negative cache from when we were offline.
  const sep = orig.indexOf('?') === -1 ? '?' : '&';
  img.src = orig + sep + '_r=' + Date.now();
}

/* `everything` is for the `online` event ONLY: connectivity genuinely came back,
   so every avatar that degraded while it was gone deserves another try.

   A tab merely regaining focus means nothing of the sort, and treating it the
   same way is what made the default avatars blink on every alt-tab. Most images
   sitting on their letter are not failures at all - they are users with no
   picture - and restoring one un-hides an empty <img>, hides the letter, and
   cache-busts a URL already known to 404. The letter vanished, two doomed
   requests went out (the error handler retries once before falling back), and
   the letter came back. Every single time the window was focused.

   An avatar that fell back WHILE offline is the one case a resume can actually
   fix, and it is already marked `data-avatar-pending` for exactly that. */
function _gpAvatarRetryAll(everything) {
  // Don't bother if we're still offline.
  if (typeof navigator !== 'undefined' && navigator.onLine === false) return;
  const nodes = document.querySelectorAll(
    everything
      ? 'img[data-avatar-fallback].gl-hidden, img[data-avatar-fallback][data-avatar-pending="1"]'
      : 'img[data-avatar-fallback][data-avatar-pending="1"]'
  );
  nodes.forEach(_gpAvatarRestore);
}

document.addEventListener('error', function (e) {
  const img = e.target;
  if (!img || img.tagName !== 'IMG') return;
  if (!img.hasAttribute('data-avatar-fallback')) return;
  // Save original src on first error so we can restore later (the retry
  // appends a cache-buster, and the fallback path replaces src entirely).
  if (!img.dataset.avatarOriginalSrc && img.getAttribute('src')) {
    img.dataset.avatarOriginalSrc = img.getAttribute('src');
  }
  // If we lost network (laptop sleep, Wi-Fi drop, server hiccup) defer the
  // fallback decision: don't show the letter yet - instead mark the img
  // as pending so the next online/visibility event can retry.
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    img.dataset.avatarPending = '1';
    return;
  }
  // Auto-retry once with cache-buster before falling back.
  const retried = img.dataset.avatarRetried;
  if (!retried && img.dataset.avatarOriginalSrc) {
    img.dataset.avatarRetried = '1';
    const sep = img.dataset.avatarOriginalSrc.indexOf('?') === -1 ? '?' : '&';
    img.src = img.dataset.avatarOriginalSrc + sep + '_r=' + Date.now();
    return;
  }
  _gpAvatarShowFallback(img);
}, true);

// Also detect "loaded but empty" responses (some GitLab proxies return a
// 0×0 / 1×1 transparent PNG instead of a 404 for users without a custom
// upload, so the `error` event never fires and the user sees an empty
// grey circle).  When that happens, fall back to the initials div.
document.addEventListener('load', function (e) {
  const img = e.target;
  if (!img || img.tagName !== 'IMG') return;
  if (!img.hasAttribute('data-avatar-fallback')) return;
  if (!img.dataset.avatarOriginalSrc && img.getAttribute('src')) {
    img.dataset.avatarOriginalSrc = img.getAttribute('src');
  }
  // naturalWidth/Height are 0 for broken images and ≤2px for the transparent
  // pixel placeholders some servers return.
  if ((img.naturalWidth || 0) <= 2 || (img.naturalHeight || 0) <= 2) {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      img.dataset.avatarPending = '1';
      return;
    }
    _gpAvatarShowFallback(img);
  }
}, true);

// Resume avatars on connectivity / visibility / BFCache restore.
window.addEventListener('online', _gpAvatarRetryAll);
window.addEventListener('pageshow', function (e) {
  // pageshow.persisted === true means the page came back from BFCache (e.g.
  // mobile Safari resume, browser back-button). Retry just to be safe.
  if (e && e.persisted) _gpAvatarRetryAll();
});
document.addEventListener('visibilitychange', function () {
  if (document.visibilityState === 'visible') {
    // Slight defer: give DNS/Wi-Fi a moment to settle after wake-from-sleep.
    setTimeout(_gpAvatarRetryAll, 250);
  }
});

/* -- Avatar load watchdog --
   The error/load listeners above only fire when the request RESOLVES. If an
   avatar host black-holes the TCP connection (TUKE VPN down, GitLab
   unreachable), the <img> fires NEITHER event and stays pending forever - the
   browser tab keeps its loading spinner spinning even though the whole page is
   already rendered ("content is all there but it still looks like it's
   loading"). Give every actually-fetching avatar a bounded window; on expiry
   abort the hung request (so the tab spinner clears) and show the initials.
   Off-screen lazy avatars are NOT fetching yet, so they are only armed once
   they scroll into view - we never degrade an avatar that would have loaded. */
(function _avatarLoadWatchdog() {
  'use strict';
  const TIMEOUT_MS = 8000;

  function _isDone(img) {
    return img.complete && (img.naturalWidth || 0) > 2;
  }

  function _arm(img) {
    if (!img || img.tagName !== 'IMG') return;
    if (!img.hasAttribute('data-avatar-fallback')) return;
    if (img.dataset.avatarWatch === '1' || _isDone(img)) return;
    img.dataset.avatarWatch = '1';
    const timer = setTimeout(function () {
      if (_isDone(img)) return; // resolved in the meantime
      if (!img.dataset.avatarOriginalSrc && img.getAttribute('src')) {
        img.dataset.avatarOriginalSrc = img.getAttribute('src');
      }
      // Offline: keep it pending for the online/visibility retry instead of
      // permanently degrading (matches the error handler's deferral).
      if (typeof navigator !== 'undefined' && navigator.onLine === false) {
        img.dataset.avatarPending = '1';
      }
      // Mark as already-retried FIRST: clearing src can fire an 'error', and
      // the global error handler would otherwise re-issue the original (hung)
      // request. _gpAvatarRestore resets this flag on reconnect.
      img.dataset.avatarRetried = '1';
      // Abort the hung request so the browser stops "loading", then fall back.
      try { img.src = ''; } catch (_) { /* noop */ }
      _gpAvatarShowFallback(img);
    }, TIMEOUT_MS);
    const clear = function () {
      clearTimeout(timer);
      delete img.dataset.avatarWatch;
    };
    img.addEventListener('load', clear, { once: true });
    img.addEventListener('error', clear, { once: true });
  }

  const io = ('IntersectionObserver' in window)
    ? new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { io.unobserve(en.target); _arm(en.target); }
        });
      }, { rootMargin: '200px' })
    : null;

  function _scan(root) {
    const scope = (root && root.querySelectorAll) ? root : document;
    scope.querySelectorAll('img[data-avatar-fallback]').forEach(function (img) {
      if (img.dataset.avatarWatch === '1' || _isDone(img)) return;
      // Already failed before this script was listening - a quick 404, a
      // source the img-src policy refuses: its error event is gone, and the
      // watchdog would leave the broken picture (and its alt text) on screen
      // for eight seconds after it scrolled in. A lazy image not yet fetched
      // is not `complete`, so it is left to load.
      if (img.complete && img.getAttribute('src')) { _gpAvatarShowFallback(img); return; }
      // Lazy + off-screen: defer arming until it actually starts fetching.
      if (img.loading === 'lazy' && io) { io.observe(img); }
      else { _arm(img); }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { _scan(document); }, { once: true });
  } else {
    _scan(document);
  }
  // New avatars arriving via HTMX fragment swaps (lazy page content, modals).
  document.body.addEventListener('htmx:afterSwap', function (e) {
    _scan(e && e.detail && e.detail.target ? e.detail.target : document);
  });
  // ...and via a page's own redraw of a server-rendered region.
  GP.scanAvatars = _scan;
})();
