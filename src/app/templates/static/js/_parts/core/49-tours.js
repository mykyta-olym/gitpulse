/* -- Guided tours, fetched when the page is idle --
   The tour engine, its tours and Driver.js are some 270 KB - they were a
   third of this bundle, which blocks the first paint of every page, though a
   tour only runs on a first visit or from the user menu. base.html names
   them in <meta name="gp-tour-scripts"> (Driver.js first, then
   tours.js), and they load once the page is idle; the engine then arms
   its own first-visit prompt, which waited for an idle page anyway. "Take a
   tour" / "Replay tours" clicked before that fetches them at once and hands
   the click over. */
(function () {
  'use strict';
  const meta = document.querySelector('meta[name="gp-tour-scripts"]');
  if (!meta) return;
  const scripts = meta.content.split(/\s+/).filter(Boolean);
  const nonce = document.currentScript?.nonce || '';
  let loading = null;

  const load = () => {
    if (!loading) {
      loading = new Promise((resolve) => {
        let left = scripts.length;
        scripts.forEach((src) => {
          const s = document.createElement('script');
          s.src = src;
          s.async = false; /* in order: Driver.js before the engine */
          if (nonce) s.setAttribute('nonce', nonce);
          s.onload = s.onerror = () => { if (--left === 0) resolve(); };
          document.head.appendChild(s);
        });
      });
    }
    return loading;
  };

  document.addEventListener('click', (ev) => {
    if (GP.tour) return; /* the engine handles its own items */
    const item = ev.target?.closest?.('[data-action="tour-launch"], [data-action="tour-reset"]');
    if (!item) return;
    ev.preventDefault();
    load().then(() => item.click());
  }, true);

  const whenIdle = () => {
    if (typeof window.requestIdleCallback === 'function') {
      window.requestIdleCallback(load, { timeout: 3000 });
    } else {
      setTimeout(load, 1500);
    }
  };
  if (document.readyState === 'complete') whenIdle();
  else window.addEventListener('load', whenIdle, { once: true });
})();
