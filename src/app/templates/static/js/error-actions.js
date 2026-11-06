/* Error-page action delegate.
   Kept outside the template so CSP can stay nonce-based without inline JS. */
(function initErrorActions() {
  'use strict';

  const cleanupTimers = [];

  function _seconds(value, fallback) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
  }

  function _freshUrl() {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('_gp_refresh', String(Date.now()));
      return url.toString();
    } catch (_) {
      return window.location.href;
    }
  }

  function _reloadFresh() {
    window.location.assign(_freshUrl());
  }

  function _initTimedRedirect() {
    const el = document.querySelector('[data-redirect-after-seconds][data-redirect-url]');
    if (!el) return;
    const delaySeconds = _seconds(el.dataset.redirectAfterSeconds, 5);
    const target = el.dataset.redirectUrl || '/dashboard/login';
    const timer = window.setTimeout(function () {
      window.location.href = target;
    }, delaySeconds * 1000);
    cleanupTimers.push(function () { window.clearTimeout(timer); });
  }

  function _initCountdownReload() {
    const el = document.querySelector('[data-countdown-seconds]');
    if (!el) return;
    const valueEl = el.querySelector('[data-countdown-value]') || el.querySelector('#cd');
    if (!valueEl) return;

    let remaining = _seconds(el.dataset.countdownSeconds || valueEl.textContent, 60);
    valueEl.textContent = String(remaining);

    const timer = window.setInterval(function () {
      remaining -= 1;
      valueEl.textContent = String(Math.max(remaining, 0));
      if (remaining <= 0) {
        window.clearInterval(timer);
        if (el.dataset.reloadWhenDone === 'true') {
          _reloadFresh();
        }
      }
    }, 1000);
    cleanupTimers.push(function () { window.clearInterval(timer); });
  }

  /* Back-navigation can hand the page back from the bfcache exactly as it was
     left - with the pressed button still busy and disabled, which is the "the
     button is dead after I used it" report in its purest form. Clear it on
     restore; a fresh load has nothing to clear. */
  window.addEventListener('pageshow', function (event) {
    if (!event.persisted) return;
    document.querySelectorAll('.error-btn[aria-busy="true"]').forEach(function (btn) {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    });
  });

  /* The search on these pages navigates too, and on the connection that produced
     the error that is not instant either - so its submit gets the same state as
     Retry. Nothing clears either one: the page is on its way out. */
  document.addEventListener('submit', function (event) {
    const form = event.target.closest('.error-search');
    if (!form) return;
    const btn = form.querySelector('.error-btn');
    if (!btn) return;
    btn.setAttribute('aria-busy', 'true');
    /* Deferred past the dispatch, the way the app's own submit guard does it:
       a button disabled inside the submit event can drop out of serialisation
       in some engines, and a cancelled submit would otherwise leave it dead. */
    setTimeout(function () {
      if (!event.defaultPrevented) btn.disabled = true;
      else btn.removeAttribute('aria-busy');
    }, 0);
  });

  document.addEventListener('click', function (event) {
    const trigger = event.target.closest('[data-action]');
    if (!trigger) return;

    const action = trigger.dataset.action;
    if (action === 'reloadPage') {
      event.preventDefault();
      /* A navigation is not instant - on the connection that produced this page
         it can take seconds - so Retry carries a loading state like every other
         button in the app. `aria-busy` is what error.css paints and what a
         screen reader announces; nothing resets it because the page is leaving. */
      trigger.setAttribute('aria-busy', 'true');
      trigger.disabled = true;
      _reloadFresh();
    } else if (action === 'historyBack') {
      event.preventDefault();
      if (document.referrer && document.referrer !== window.location.href) {
        window.history.back();
      } else {
        window.location.href = '/dashboard/';
      }
    }
  });

  /* GitLab's error pages show "Go back" only when there is somewhere to go
     back to (`history.length > 1`); a first-visit landing on an error page
     hides it. Match that - the link falls back to the dashboard when clicked,
     but if there is no history AND no referrer, going "back" would do nothing
     the reader expects, so it is hidden. */
  function _gateGoBack() {
    const link = document.querySelector('[data-action="historyBack"]');
    if (!link) return;
    const hasReferrer = document.referrer && document.referrer !== window.location.href;
    if (window.history.length <= 1 && !hasReferrer) {
      link.style.display = 'none';
      // the separator that follows it, if any, goes too
      const sep = link.nextElementSibling;
      if (sep && sep.classList.contains('error-footer-sep')) sep.style.display = 'none';
    }
  }

  _gateGoBack();
  _initTimedRedirect();
  _initCountdownReload();

  window.addEventListener('pagehide', function () {
    cleanupTimers.splice(0).forEach(function (cleanup) { cleanup(); });
  });
})();
