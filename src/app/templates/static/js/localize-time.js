/* localize-time.js
 *
 * Convert any `<time data-localize-time datetime="...">` element on the
 * page from the server-rendered UTC string into the user's local
 * timezone.  Server templates emit a UTC ISO timestamp inside `datetime`
 * and a display fallback as the visible textContent (so the page is
 * still readable before JS runs / for SSR scrapers).
 *
 * Public API:
 *   window.localizeTimes(rootEl?)   - convert all matching <time>
 *                                     descendants of rootEl (default
 *                                     document).  Idempotent.
 *
 * Auto-runs on DOMContentLoaded and after every htmx:afterSwap so any
 * partial-rendered fragment also picks up the conversion.
 */
(function () {
  'use strict';

  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  function timeAgo(d) {
    const seconds = Math.floor((new Date() - d) / 1000);
    const lang = document.documentElement.lang || 'en';

    let interval = Math.floor(seconds / 31536000);
    if (interval >= 1) {
      if (lang === 'sk') {
        return interval === 1 ? 'pred rokom' : 'pred ' + interval + ' rokmi';
      }
      return interval === 1 ? '1 year ago' : interval + ' years ago';
    }
    interval = Math.floor(seconds / 2592000);
    if (interval >= 1) {
      if (lang === 'sk') {
        return interval === 1 ? 'pred mesiacom' : 'pred ' + interval + ' mesiacmi';
      }
      return interval === 1 ? '1 month ago' : interval + ' months ago';
    }
    interval = Math.floor(seconds / 604800);
    if (interval >= 1) {
      if (lang === 'sk') {
        return interval === 1 ? 'pred týždňom' : 'pred ' + interval + ' týždňami';
      }
      return interval === 1 ? '1 week ago' : interval + ' weeks ago';
    }
    interval = Math.floor(seconds / 86400);
    if (interval >= 1) {
      if (lang === 'sk') {
        return interval === 1 ? 'pred dňom' : 'pred ' + interval + ' dňami';
      }
      return interval === 1 ? '1 day ago' : interval + ' days ago';
    }
    interval = Math.floor(seconds / 3600);
    if (interval >= 1) {
      if (lang === 'sk') {
        return interval === 1 ? 'pred hodinou' : 'pred ' + interval + ' hodinami';
      }
      return interval === 1 ? '1 hour ago' : interval + ' hours ago';
    }
    interval = Math.floor(seconds / 60);
    if (interval >= 1) {
      if (lang === 'sk') {
        return interval === 1 ? 'pred minútou' : 'pred ' + interval + ' minútami';
      }
      return interval === 1 ? '1 minute ago' : interval + ' minutes ago';
    }
    return lang === 'sk' ? 'teraz' : 'just now';
  }

  /* Preferences > Time preferences. Both live on <html>, set server-side in
     base.html, so the very first paint already honours them - reading them
     from an API would format every stamp twice in front of the reader. */
  function absoluteTimesForced() {
    return document.documentElement.hasAttribute('data-absolute-times');
  }

  function hourCycle() {
    return document.documentElement.getAttribute('data-time-format') || 'system';
  }

  /* Returns "2:34 PM" / "14:34" honouring the preference. "system" keeps the
     24h pair the server-side strftime emits, so the two agree by default. */
  function fmtClock(d) {
    const mode = hourCycle();
    if (mode === '12h') {
      const h24 = d.getHours();
      const suffix = h24 < 12 ? 'AM' : 'PM';
      const h12 = h24 % 12 === 0 ? 12 : h24 % 12;
      return h12 + ':' + pad(d.getMinutes()) + ' ' + suffix;
    }
    return pad(d.getHours()) + ':' + pad(d.getMinutes());
  }

  function fmtLocal(d, mode) {
    if (mode === 'relative') {
      /* "Use relative times" off: fall through to the absolute rendering
         rather than returning "3 days ago". The element keeps its UTC tooltip
         either way, so nothing is lost. */
      if (!absoluteTimesForced()) return timeAgo(d);
      return (
        d.getFullYear() +
        '-' + pad(d.getMonth() + 1) +
        '-' + pad(d.getDate()) +
        ' ' + fmtClock(d)
      );
    }
    // 'date'          -> 2026-04-28
    // 'time'          -> 18:11
    // 'monthday-time' -> Apr 28, 18:11
    // default         -> 2026-04-28 18:11
    // User's timezone, and 24h by default so the result matches the
    // server-side strftime and the UI does not shift visually. The clock half
    // goes through fmtClock, which is where "Time format" turns it into 6:11 PM.
    if (mode === 'time') {
      return fmtClock(d);
    }
    /* A cell that shows only a day must not grow a clock when the client takes
       over - it still moves to the reader's timezone, which can shift the date
       itself by one. */
    if (mode === 'date') {
      return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
    }
    if (mode === 'monthday-time') {
      const mon = d.toLocaleString(undefined, { month: 'short' });
      return mon + ' ' + pad(d.getDate()) + ', ' + fmtClock(d);
    }
    return (
      d.getFullYear() +
      '-' + pad(d.getMonth() + 1) +
      '-' + pad(d.getDate()) +
      ' ' + fmtClock(d)
    );
  }

  function localizeOne(el) {
    if (!el || el.dataset.localized === '1') return;
    const iso = el.getAttribute('datetime');
    if (!iso) return;
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return;
    const local = fmtLocal(d, el.dataset.localizeFormat);
    if (el.textContent !== local) el.textContent = local;
    // Show the original UTC stamp on hover so power users can still see the
    // canonical server time when needed. Component (tippy) tooltip ONLY - the
    // native title= is deliberately not set (no unstyled/native tooltips).
    // Built from the parsed instant, not the attribute's spelling: a job's
    // stamp arrives as "2026-09-25 16:55:17.605651+00:00" and read that way.
    const utc = d.toISOString().slice(0, 19).replace('T', ' ') + ' UTC';
    if (!el.dataset.tippyContent) el.dataset.tippyContent = utc;
    if (el.hasAttribute('title')) el.removeAttribute('title');
    el.dataset.localized = '1';
  }

  function localizeTimes(root) {
    const scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll('time[data-localize-time]').forEach(localizeOne);
    // The UTC hover needs no per-element binding: tooltips are delegated
    // (GP.initTippy) and an instance is made the first time a <time> is
    // hovered, reading `data-tippy-content` then. The old batched pass here
    // re-walked every tooltip on the page - 524ms of the Users page's load.
  }

  window.localizeTimes = localizeTimes;
  /* For plain text, where a `<time>` element cannot go - a toast, an aria-label.
     Same "Time format" preference, so a clock in a message and a clock in a
     table do not disagree with each other. */
  window.formatClock = fmtClock;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => localizeTimes());
  } else {
    localizeTimes();
  }

  // HTMX swaps replace partial DOM - re-run the conversion against the
  // freshly inserted fragment so newly arrived <time> elements localize
  // without a full page refresh.
  document.addEventListener('htmx:afterSwap', (ev) => {
    localizeTimes(ev && ev.target ? ev.target : document);
  });

  /* Page JS builds rows and cards from fetched JSON, and that markup arrives
     through neither of the two paths above. Every such call site would have to
     remember to localize what it just inserted - and none of them did, which is
     precisely why ten of them gave up and called `toLocaleString()` instead,
     silently ignoring the reader's Time format and Use relative times.
     Watching for the element makes `GP.timeHtml()` safe to use anywhere.

     The work is proportional to what was inserted, not to the document: only
     added subtrees are scanned, and `localizeOne` skips anything already done. */
  const pending = new Set();
  let scheduled = 0;
  const observer = new MutationObserver((records) => {
    for (const rec of records) {
      for (const node of rec.addedNodes) {
        if (node.nodeType === 1) pending.add(node);
      }
    }
    if (!pending.size || scheduled) return;
    scheduled = requestAnimationFrame(() => {
      scheduled = 0;
      const batch = [...pending];
      pending.clear();
      for (const node of batch) {
        if (!node.isConnected) continue;
        if (node.matches && node.matches('time[data-localize-time]')) localizeOne(node);
        else localizeTimes(node);
      }
    });
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
