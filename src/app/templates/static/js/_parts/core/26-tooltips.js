/* ============================================
   Tooltips (Tippy)
   ============================================ */
/* How many tooltips are on screen. A visible tooltip makes Popper recompute its
   position on every scroll frame, and that was the single most expensive thing
   the main thread did while scrolling: profiled on System Health at 4x CPU
   throttle, popper + tippy accounted for ~430ms of a 5s scroll and 12 long
   tasks (worst 208ms). A tooltip that follows the content is also wrong - the
   pointer has left the thing it describes. It hides instead, and the counter
   keeps the scroll listener free when nothing is up. */
/* Scrolling with the pointer parked over the page drags element after element
   under a stationary cursor, and each `mouseenter` opens a tooltip: measured 12
   mounts into <body> during a single 2.5s wheel scroll on System Health, each
   one a Popper layout pass. Suppress them while the wheel is moving - a tooltip
   describes what the pointer is ON, and during a scroll it is on nothing in
   particular. */
let _scrollingUntil = 0;
const _SCROLL_QUIET_MS = 160;

let _tippyScrollQueued = false;
document.addEventListener('scroll', function _hideTippyOnScroll() {
  /* Kept synchronous and cheap: `_scrollingUntil` gates the hover re-arm below,
     so it has to be current the instant a scroll fires. */
  _scrollingUntil = Date.now() + _SCROLL_QUIET_MS;
  if (_tippyScrollQueued) return;
  if (typeof window.tippy !== 'function' || !window.tippy.hideAll) return;
  /* Coalesce the actual tooltip check to ONE rAF per frame, off the scroll path.
     This listener is capture-phase on `document`, so it fires for every scroller
     (page, tables, dropdowns, the sidebar) and can run several times per frame;
     doing a whole-document `querySelector('[data-tippy-root]')` inline on each of
     those put an O(n) DOM scan on the scroll path every frame. `[data-tippy-root]`
     still covers tooltips mounted anywhere - the scan just no longer blocks the
     scroll, and once queued it runs at most once until the frame paints. */
  _tippyScrollQueued = true;
  requestAnimationFrame(function () {
    _tippyScrollQueued = false;
    const roots = document.querySelectorAll('[data-tippy-root]');
    if (!roots.length) return;
    roots.forEach(function (root) {
      const inst = root._tippy;
      if (!inst) return;
      const ref = inst.reference;
      // Do not hide persistent info tips on scroll - users need to read them on mobile
      if (ref && ref.closest('.card-header-info-tip')) {
        return;
      }
      inst.hide(0);
    });
  });
}, { capture: true, passive: true });

/* ONE delegated tooltip for the whole document, not one instance per element.

   Tooltips used to be instantiated eagerly: every `[data-tippy-content]` on the
   page got its own tippy at boot, and every later `initTippy(scope)` call -
   after each HTMX swap, after every `localizeTimes()` pass - re-walked the
   scope and called `setContent` on all of them. Profiled on User Management
   with 574 rows (production's size): 822ms in initTippy plus 524ms in
   localizeTimes, of a 1.4s main-thread block on load - the page "hangs" - for
   thousands of tooltips of which the reader can hover one, on the 25 rows
   that are visible.

   `tippy.delegate` listens on <body> and creates an element's instance the
   first time the pointer (or keyboard focus) reaches it, showing it at once.
   Nothing is created for a row nobody hovers; a row added later by a swap or
   by Alpine needs no init call at all; and `el._tippy` still exists for any
   element that HAS been hovered, so callers that update a live tooltip with
   `setContent` keep working. Content is re-read from the attribute at every
   show, so a caller that only rewrites `data-tippy-content` is enough.
   Native `title` is dropped when the instance is made - before the browser's
   own tooltip delay - so nothing shows twice. */
const _TIPPY_TARGET = '[data-tippy-content]:not(.card-header-info-tip), [data-tooltip]:not(.card-header-info-tip)';
let _tippyDelegate = null;
const _tooltipInstances = new Set();
let _tooltipRemovalObserver = null;

function _tippyContent(reference) {
  return reference.dataset.tippyContent || reference.dataset.tooltip || '';
}

function _prepareTooltip(instance) {
  if (typeof window.tippy.hideAll === 'function') window.tippy.hideAll({ exclude: instance, duration: 0 });
  // Tippy's hideAll list only includes mounted popups. A popup shown earlier
  // in this frame can still be waiting for its first Popper layout.
  _tooltipInstances.forEach(function (other) {
    if (other !== instance && other.state.isVisible) other.hide(0);
  });
  const live = _tippyContent(instance.reference);
  if (live !== instance.props.content) instance.setContent(live);
}

function initCardInfoTips(container = document) {
  if (typeof window.tippy !== 'function') return;
  const scope = container || document;
  const tips = scope.querySelectorAll ? scope.querySelectorAll('.card-header-info-tip') : [];
  const isTouch = Boolean(
    (window.matchMedia && window.matchMedia('(pointer: coarse)').matches)
    || ('ontouchstart' in window)
    || (navigator.maxTouchPoints > 0)
  );

  tips.forEach(function (btn) {
    if (btn._tippy) return;
    const content = _tippyContent(btn);
    if (!content) return;
    window.tippy(btn, {
      content: content,
      trigger: isTouch ? 'click' : 'mouseenter focus',
      touch: true,
      interactive: true,
      arrow: true,
      placement: btn.dataset.tippyPlacement || 'bottom-end',
      offset: [0, 8],
      delay: isTouch ? 0 : [80, 120],
      duration: [160, 120],
      hideOnClick: true,
      appendTo: () => document.body,
      onCreate(instance) { _tooltipInstances.add(instance); },
      onDestroy(instance) { _tooltipInstances.delete(instance); },
      onShow: _prepareTooltip,
      popperOptions: {
        strategy: 'fixed',
        modifiers: [
          { name: 'preventOverflow', options: { padding: 12 } },
          { name: 'flip', options: { padding: 12 } },
        ],
      },
    });
  });
}

function initTippy(container = document) {
  initCardInfoTips(container);
  if (typeof window.tippy !== 'function' || typeof window.tippy.delegate !== 'function') return;
  if (_tippyDelegate || !document.body) return;
  _tippyDelegate = window.tippy.delegate(document.body, {
    target: _TIPPY_TARGET,
    content: _tippyContent,
    duration: [180, 120],
    touch: false,
    /* Popper's scroll/resize listeners are what make an open tooltip cost
       main-thread time on every scroll frame. The tooltip hides on scroll
       (see _hideTippyOnScroll), so it has nothing to follow. */
    popperOptions: {
      modifiers: [{ name: 'eventListeners', options: { scroll: false, resize: false } }],
    },
    onCreate(instance) {
      _tooltipInstances.add(instance);
      const ref = instance.reference;
      // Remove native title to prevent double-tooltip
      if (ref.hasAttribute('title')) ref.removeAttribute('title');
      if (ref.dataset.tippyPlacement) instance.setProps({ placement: ref.dataset.tippyPlacement });
    },
    onDestroy(instance) { _tooltipInstances.delete(instance); },
    // Record what triggered the show (hover vs focus) so onShow can decide
    // whether to suppress it.
    onTrigger(instance, event) {
      instance._gpTriggerType = event.type;
    },
    onShow(instance) {
      if (Date.now() < _scrollingUntil) return false;
      const ref = instance.reference;
      /* ONE tooltip at a time. A cell with its own tooltip holding a <time>
         with another (the job table's Enqueued column) showed both, stacked:
         the inner one wins while the pointer is on it, and showing any
         tooltip hides whatever else is up - the tooltip twin of one open
         menu at a time. */
      if (ref && typeof ref.querySelector === 'function'
          && ref.querySelector('[data-tippy-content]:hover, [data-tooltip]:hover')) {
        return false;
      }
      /* Tippy's default trigger is "mouseenter focus". A modal focus-trap (or
         a plain mouse click) programmatically focuses buttons such as the
         modal close (X), which would otherwise pop the tooltip open with no
         hover. Only allow focus-triggered tooltips when the focus is from the
         keyboard (:focus-visible); always allow hover. The very first show
         comes from the delegate's own listener and records no trigger, so it
         is judged by where the pointer is. */
      const type = instance._gpTriggerType;
      const fromFocus = type === 'focus' || type === 'focusin'
        || (!type && ref && typeof ref.matches === 'function' && !ref.matches(':hover'));
      if (fromFocus && ref && typeof ref.matches === 'function' && !ref.matches(':focus-visible')) {
        return false;
      }
      /* Content is whatever the attribute says NOW: a label driven by state
         (a count, an Alpine binding, a job's progress) is rewritten on the
         element, and the instance follows it at display time. */
      _prepareTooltip(instance);
      return undefined;
    },
  });
  document.documentElement.classList.add('js-tooltips');
}

/* Fallback click support for dynamic .card-header-info-tip elements.
   If Tippy is attached, Tippy natively handles click, touch, and outside-clicks.
   Never manually toggle an existing Tippy instance here, as that creates a
   race condition where Tippy shows and this handler immediately hides it. */
document.addEventListener('click', function (e) {
  const btn = e.target.closest ? e.target.closest('.card-header-info-tip') : null;
  if (!btn) return;

  // Let Tippy's own click/touch listener handle it if initialized:
  if (btn._tippy) return;

  e.preventDefault();
  e.stopPropagation();

  if (typeof window.tippy === 'function') {
    initCardInfoTips(btn.ownerDocument || document);
    if (btn._tippy) {
      btn._tippy.show();
      return;
    }
  }

  const tipText = _tippyContent(btn);
  if (tipText) {
    GP.showToast(tipText, 'info', 4000);
  }
});

function initTooltips() {
  initTippy(document);
  initCardInfoTips(document);
  if (_tooltipRemovalObserver || !document.body || typeof MutationObserver !== 'function') return;
  // Popups live under body, outside their page/row. Destroy their instances
  // when a swap removes the reference, including pending or hidden tooltips.
  // Check only created instances; never scan every tooltip target on a swap.
  // isConnected preserves references moved by sorting or modal teleportation.
  _tooltipRemovalObserver = new MutationObserver(function (mutations) {
    if (!mutations.some((mutation) => mutation.removedNodes.length)) return;
    _tooltipInstances.forEach(function (instance) {
      if (!instance.reference.isConnected) instance.destroy();
    });
  });
  _tooltipRemovalObserver.observe(document.body, { childList: true, subtree: true });
}
