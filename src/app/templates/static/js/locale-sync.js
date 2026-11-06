/**
 * Sync preferred locale: sets `lang` attribute, localStorage, and cookie.
 * Runs immediately (IIFE) - safe for <head> inclusion.
 *
 * Cross-tab: if the user changes locale in another tab, the `gp_lang`
 * localStorage write fires a `storage` event here - we reload so the
 * server re-renders all UI in the new language.
 */
(function syncPreferredLocale() {
  const el = document.documentElement;
  const locale = el.getAttribute('data-locale') || 'sk';

  function _freshUrl() {
    const shared = window.GP?.cacheBustedCurrentUrl;
    if (typeof shared === 'function') return shared();
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('_gp_refresh', String(Date.now()));
      return url.toString();
    } catch (_) {
      return window.location.href;
    }
  }

  function _reloadFresh() {
    if (typeof window.reloadKeepScroll === 'function') {
      window.reloadKeepScroll();
      return;
    }
    window.location.assign(_freshUrl());
  }

  el.setAttribute('lang', locale);
  try {
    window.localStorage.setItem('gp_lang', locale);
  } catch (_) {}
  if (Cookies.getInitial('gp_lang') !== locale) {
    Cookies.setAsync('gp_lang', locale, { expires: 365 }).catch(() => {});
  }

  try {
    window.addEventListener('storage', async function (ev) {
      if (ev.key !== 'gp_lang' || !ev.newValue) return;
      if (ev.newValue === locale) return;
      // Update cookie so the next request uses the new locale, then reload.
      try {
        await Cookies.setAsync('gp_lang', ev.newValue, { expires: 365 });
      } catch (_) {}
      // Defer slightly so any in-flight HTMX/SSE request can settle.
      setTimeout(function () {
        try { _reloadFresh(); } catch (_) {}
      }, 50);
    });
  } catch (_) { /* noop */ }

  // Soft language switch. The locale links point at /dashboard/language/<code>,
  // a full server navigation that 303-redirects back and loses scroll position
  // (jumps to the top, with a hard flash). That route does nothing but set the
  // gp_lang cookie - exactly what we already do client-side here - so intercept
  // the click, set the cookie/localStorage, and use the scroll-preserving reload
  // (the same "ideal" reload as the cross-tab sync above). Writing localStorage
  // also propagates the change to other open tabs via the storage listener.
  try {
    document.addEventListener('click', async function (ev) {
      const link = ev.target.closest && ev.target.closest('a[href*="/dashboard/language/"]');
      if (!link) return;
      // Let modified / non-primary clicks (open-in-new-tab) behave normally.
      if (ev.defaultPrevented || ev.button !== 0 ||
          ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
      const m = (link.getAttribute('href') || '').match(/\/dashboard\/language\/([A-Za-z_-]+)/);
      if (!m) return;
      ev.preventDefault();
      const next = m[1];
      if (next === locale) return; // already in this language - no reload
      try { window.localStorage.setItem('gp_lang', next); } catch (_) {}
      try {
        await Cookies.setAsync('gp_lang', next, { expires: 365 });
      } catch (_) {}
      _reloadFresh();
    });
  } catch (_) { /* noop */ }
})();
