/* ============================================
   Chart entrance
   ============================================
   A chart's entrance animation plays ONCE per canvas. Every refresh path in
   the app - an SSE tick, a finished job, a returning tab, the Refresh button -
   re-runs the page's chart init, which destroys the chart and builds it
   again, and the bars grew out of nothing a second time ("the chart's
   appearance animation plays twice"). The first draw on a canvas gets the
   entrance it asked for; every later draw on the same canvas gets none, so a
   refresh replaces the numbers in place.

   @param {HTMLCanvasElement} canvas
   @param {object} entrance  the Chart.js `animation` config for the first draw
   @returns {object|false}   the config to put in `options.animation` */
function chartEntrance(canvas, entrance) {
  if (!canvas || !canvas.dataset) return entrance;
  if (canvas.dataset.gpDrawn === '1') return false;
  canvas.dataset.gpDrawn = '1';
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
  return entrance;
}
GP.chartEntrance = chartEntrance;

/* A chart's first draw waits until it is on screen. One below the fold that
   animated on load had finished before anyone scrolled to it - Analytics'
   compliance ring was drawn 300-700 ms in and seen standing still. Admin >
   System's role chart waited for its canvas to scroll in; every chart does it
   that way now, through this one function.

   `draw` runs once `watch` (the canvas, or the loader standing in for it) is
   at least 10% visible. A call before that only replaces what will be drawn
   (a refresh with fresher data); after the first draw a call runs at once.

   @param {HTMLCanvasElement} canvas  carries the "entered" mark
   @param {Function} draw
   @param {Element} [watch]           what to watch instead of the canvas */
function drawOnEntry(canvas, draw, watch) {
  const target = watch || canvas;
  if (!canvas || !target || canvas.dataset.gpEntered === '1' || !('IntersectionObserver' in window)) {
    if (canvas && canvas.dataset) canvas.dataset.gpEntered = '1';
    draw();
    return;
  }
  if (canvas._gpEntry) { canvas._gpEntry.draw = draw; return; }
  const entry = { draw: draw, io: null, timer: 0 };
  canvas._gpEntry = entry;
  const go = function () {
    if (canvas._gpEntry !== entry) return;
    canvas._gpEntry = null;
    canvas.dataset.gpEntered = '1';
    if (entry.io) entry.io.disconnect();
    clearTimeout(entry.timer);
    entry.draw();
  };
  // Watched a frame later: a canvas a loading hand-off reveals in this very
  // tick still measures zero, and a zero-sized box never intersects.
  requestAnimationFrame(function () {
    if (canvas._gpEntry !== entry) return;
    entry.io = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) go();
    }, { threshold: 0.1 });
    entry.io.observe(target);
    // Safety net for a target that never gets a box: drawn anyway. One that
    // is merely below the fold waits for the reader.
    entry.timer = setTimeout(function () {
      const r = target.getBoundingClientRect();
      if (!r.width || !r.height) go();
    }, 1200);
  });
}
GP.drawOnEntry = drawOnEntry;

/* Shared bar-chart entrance: 900 ms ease-out with an 80 ms stagger. */
function barsEntrance(canvas) {
  return chartEntrance(canvas, {
    duration: 900,
    easing: 'easeOutQuart',
    // The bars of the first draw only - not a later update's.
    delay: function (ctx) { return ctx.type === 'data' && ctx.mode === 'default' ? ctx.dataIndex * 80 : 0; },
  });
}
GP.barsEntrance = barsEntrance;

/* ...and a ring's: the arc sweeps round in the same 900 ms. */
function ringEntrance(canvas) {
  return chartEntrance(canvas, { animateRotate: true, duration: 900, easing: 'easeOutQuart' });
}
GP.ringEntrance = ringEntrance;

/* ============================================
   Clipboard
   ============================================ */
async function copyToClipboard(text, successMessage = null) {
  const value = String(text || '');
  if (!value) {
    showToast(_translateUiText('Nothing to copy'), 'warning');
    return false;
  }

  try {
    await navigator.clipboard.writeText(value);
    showToast(_translateUiText(successMessage || 'Copied to clipboard'), 'success');
    return true;
  } catch (_) {
    showToast(_translateUiText('Failed to copy'), 'danger');
    return false;
  }
}

/* ============================================
   Debounce / Throttle
   ============================================ */
function debounce(fn, wait) {
  let timeoutId = null;
  return function debounced(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), wait);
  };
}


GP.debounce = debounce;

/* ============================================
   Global Job Terminal Ownership
   ============================================ */
function finishGlobalJobOrToast(jobType, message = '', status = 'done', options = {}) {
  const opts = options || {};
  const jobs = GP.globalJobs || GP;
  const completeFn = jobs.completeGlobalJob || window.completeGlobalJob;
  const hideFn = jobs.hideGlobalJob || window.hideGlobalJob;

  const handledByGlobal = typeof completeFn === 'function'
    && completeFn(jobType, message, status);
  if (handledByGlobal) {
    return true;
  }

  if (typeof hideFn === 'function') {
    hideFn(jobType);
  }

  if (opts.toast === false) {
    return false;
  }

  const toastFn = opts.flash
    ? (window.flashToast || GP.flashToast)
    : (window.showToast || GP.showToast);
  const fallbackType = opts.type || (status === 'error' ? 'danger' : 'success');
  if (typeof toastFn === 'function') {
    toastFn(message, fallbackType);
  }
  return false;
}

GP.finishGlobalJobOrToast = finishGlobalJobOrToast;
