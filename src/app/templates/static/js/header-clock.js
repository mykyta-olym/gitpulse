/**
 * Top-bar clock: updates the time display every 30 seconds.
 * Updates every element carrying [data-clock-text] (the inline desktop bar
 * plus the mobile "+" dropdown), so both stay in sync.
 */
(function () {
  const els = document.querySelectorAll('[data-clock-text]');
  if (!els.length) return;
  /* The clock half goes through the shared formatter, which is what reads
     Preferences > "Time format". Building it here with getHours() made this the
     most visible hardcode in the app: a reader who chose 12-hour saw 18:12 in
     the top bar of EVERY page, while the same moment in a table read 6:12 PM.
     A live clock cannot be a `<time data-localize-time>` element - that is for
     a fixed instant - so it asks the same formatter those elements use. */
  function clock(d) {
    if (typeof window.formatClock === 'function') return window.formatClock(d);
    return String(d.getHours()).padStart(2, '0') + ':' +
           String(d.getMinutes()).padStart(2, '0');
  }
  function u() {
    const d = new Date(),
      day = String(d.getDate()).padStart(2, '0'),
      mon = String(d.getMonth() + 1).padStart(2, '0'),
      text = day + '.' + mon + '. ' + clock(d);
    els.forEach((el) => { el.textContent = text; });
  }
  let timerId = null;
  function startClock() {
    if (timerId) return;
    u();
    timerId = setInterval(u, 30000);
  }
  function stopClock() {
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
  }

  startClock();

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') {
      stopClock();
    } else {
      startClock();
    }
  });
})();
