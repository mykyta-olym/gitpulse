/**
 * Horizontal-scroll affordance for data tables.
 *
 * Every responsive table is `.table-scroll > .table-responsive > table`
 * (see components/tables.html). `.table-responsive` is the scroll viewport;
 * `.table-scroll` is a non-scrolling wrapper that paints a right-edge fade
 * (tables.css) so users can see a table scrolls sideways instead of thinking
 * the columns are cut off.
 *
 * This module only TOGGLES CLASSES on the wrapper - no DOM mutation, no inline
 * styles:
 *   .is-scrollable-x  -> the viewport overflows horizontally
 *   .at-scroll-end    -> scrolled to (or past) the far right; fade hidden
 *
 * Re-runs on load, HTMX swaps, viewport resize, and content resize
 * (ResizeObserver), so the affordance stays correct as rows load in.
 *
 * A tab strip (`.tabs-nav`) is its own scroll viewport and gets the same two
 * classes, so a strip that runs off a phone's edge fades at that edge instead
 * of cutting the last tab in half with nothing to say more follow.
 */
(function () {
  'use strict';

  const ROW_MIN_PX = 190;
  const tableBindings = new WeakMap();

  function update(wrap) {
    const sc = wrap.querySelector(':scope > .table-responsive');
    if (!sc) return;
    const max = sc.scrollWidth - sc.clientWidth;
    const scrollable = max > 1;
    /* A pinned actions column only helps while it leaves the row room for its
       own columns. On a small phone the admin Courses table's four buttons
       pinned 200px of a 309px viewport, so the course code was the only column
       ever visible and everything else scrolled under the buttons. The column
       stays pinned while at least ROW_MIN_PX remain beside it - one identity
       column's worth - and otherwise lets go and scrolls with the row, the way
       a GitLab table simply scrolls. Measured, not guessed: a one- or two-button
       column pins on every phone (198px beside it at 360px), three buttons
       pin from ~430px, four from ~450px. Re-evaluated on every resize. */
    // The first body row may be hidden by a filter or pagination. Its width
    // would be zero; the header still measures the rendered actions column.
    const pinned = sc.querySelector(':scope > .table-sticky-actions > thead > tr > th:last-child:not([colspan])')
      || sc.querySelector(':scope > .table-sticky-actions > tbody > tr > td:last-child:not([colspan])');
    const tooWide = !!(pinned && scrollable && sc.clientWidth - pinned.getBoundingClientRect().width < ROW_MIN_PX);
    // Measure before writing classes. Pinning depends on geometry, not on the
    // finger's position, and must not be re-evaluated on every scroll event.
    wrap.classList.toggle('is-scrollable-x', scrollable);
    wrap.classList.toggle('at-scroll-end', !scrollable || sc.scrollLeft >= max - 1);
    wrap.classList.toggle('sticky-column-off', tooWide);
  }

  function bind(wrap) {
    const sc = wrap.querySelector(':scope > .table-responsive');
    const tbl = sc && sc.querySelector('table');
    const previous = tableBindings.get(wrap);
    if (previous && previous.sc === sc && previous.tbl === tbl) {
      update(wrap);
      return;
    }
    // An inner HTMX swap can keep the wrapper but replace its viewport/table.
    // Stop watching the old nodes before binding the current ones.
    if (previous) {
      previous.sc?.removeEventListener('scroll', previous.onScroll);
      previous.observer?.disconnect();
    }
    wrap.__tableScrollBound = true;
    const onScroll = function () {
      const max = sc.scrollWidth - sc.clientWidth;
      wrap.classList.toggle('at-scroll-end', max <= 1 || sc.scrollLeft >= max - 1);
    };
    if (sc) {
      sc.addEventListener('scroll', onScroll, { passive: true });
    }
    let observer = null;
    if (window.ResizeObserver) {
      observer = new ResizeObserver(function () { update(wrap); });
      observer.observe(wrap);
      if (tbl) observer.observe(tbl);
      const actions = tbl?.querySelector('thead > tr > th:last-child:not([colspan])');
      if (actions) observer.observe(actions);
    }
    tableBindings.set(wrap, { sc, tbl, onScroll, observer });
    update(wrap);
  }

  function updateStrip(el) {
    const max = el.scrollWidth - el.clientWidth;
    const scrollable = max > 1;
    el.classList.toggle('is-scrollable-x', scrollable);
    el.classList.toggle('at-scroll-end', !scrollable || el.scrollLeft >= max - 1);
  }

  function bindStrip(el) {
    if (el.__stripScrollBound) {
      updateStrip(el);
      return;
    }
    el.__stripScrollBound = true;
    el.addEventListener('scroll', function () { updateStrip(el); }, { passive: true });
    if (window.ResizeObserver) {
      new ResizeObserver(function () { updateStrip(el); }).observe(el);
    }
    updateStrip(el);
  }

  function init(root) {
    const scope = root && root.querySelectorAll ? root : document;
    // Swaps can target the component itself or just a region inside it.
    const tableRoot = scope.closest?.('.table-scroll');
    if (tableRoot) bind(tableRoot);
    const wraps = scope.querySelectorAll('.table-scroll');
    for (let i = 0; i < wraps.length; i++) bind(wraps[i]);
    const stripRoot = scope.closest?.('.tabs-nav');
    if (stripRoot) bindStrip(stripRoot);
    const strips = scope.querySelectorAll('.tabs-nav');
    for (let j = 0; j < strips.length; j++) bindStrip(strips[j]);
  }

  if (document.readyState !== 'loading') {
    init(document);
  } else {
    document.addEventListener('DOMContentLoaded', function () { init(document); });
  }
  // HTMX lazy regions / re-renders bring new tables in.
  document.addEventListener('htmx:afterSwap', function (e) { init(e.target || document); });
  window.addEventListener('resize', function () { init(document); }, { passive: true });

  window.GP = window.GP || {};
  window.GP.initTableScroll = init;
})();
