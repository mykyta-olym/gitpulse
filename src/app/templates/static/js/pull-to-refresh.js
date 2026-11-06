/**
 * Pull-to-Refresh - GitLab Pajamas style, zero-lag.
 *
 * ALL listeners are { passive: true } so the browser scroll-compositor
 * thread is never blocked.  overscroll-behavior-y: contain (in CSS)
 * suppresses the native pull-to-refresh / rubber-band.
 * Visual updates are batched in requestAnimationFrame.
 */
(function () {
  'use strict';

  function initPtr() {
    const isTouch = ('ontouchstart' in window) ||
                    (navigator.maxTouchPoints > 0) ||
                    (window.matchMedia && matchMedia('(pointer:coarse)').matches);
    if (!isTouch) return;

    const scroller = document.querySelector('.gl-page-content') ||
                     document.querySelector('.gl-main-content') ||
                     document.documentElement;
    if (!scroller) return;

  /* -- Config -- */
  const THRESHOLD = 48;
  const MAX_PULL  = 64;
  const DAMPING   = 0.35;
  const R = 9, C = 2 * Math.PI * R;          /* ≈ 56.55 */

  /* -- DOM (built once) -- */
  const el = document.createElement('div');
  el.className = 'ptr';
  el.setAttribute('aria-hidden', 'true');
  el.innerHTML =
    '<svg class="ptr-svg" viewBox="0 0 24 24">' +
      '<circle class="ptr-track" cx="12" cy="12" r="' + R + '"/>' +
      '<circle class="ptr-arc"   cx="12" cy="12" r="' + R + '"' +
        ' stroke-dasharray="' + C + '" stroke-dashoffset="' + C + '"/>' +
    '</svg>';

  /* Appended to <body> rather than the scroller so `overflow: hidden auto`
     on .gl-page-content never clips the indicator. Position: fixed in CSS
     keeps it viewport-anchored; JS computes the centre from the scroller's
     bounding rect. */
  document.body.appendChild(el);

  const arc = el.querySelector('.ptr-arc');

  /* -- State -- */
  let startY = 0, startX = 0, pulling = false, busy = false, dist = 0, raf = 0;
  let locked = false;  /* locked = horizontal gesture detected, ignore until touchend */

  function reset() {
    el.className = 'ptr';
    el.style.cssText = '';
    arc.style.cssText = '';
    dist = 0;
  }
  reset();

  /* -- Render (called only inside rAF) -- */
  function scrollerCenter() {
    const r = scroller.getBoundingClientRect();
    return { cx: r.left + r.width / 2, top: r.top };
  }
  function render() {
    raf = 0;
    const sc = scrollerCenter();
    const p = Math.min(dist / THRESHOLD, 1);
    el.style.opacity = '1';
    el.style.left = sc.cx + 'px';
    el.style.top = sc.top + 'px';
    el.style.transform = 'translate(-50%,' + (dist - 44) + 'px)' +
      (p >= 1 ? ' scale(1.05)' : '');
    arc.style.strokeDashoffset = C * (1 - p);
    arc.style.transform = 'rotate(' + (p * 270 - 90) + 'deg)';
  }

  /* -- Touch (all passive - zero scroll-blocking) -- */
  scroller.addEventListener('touchstart', function (e) {
    if (busy || scroller.scrollTop > 1) return;
    /* Ignore touches starting inside horizontally scrollable containers */
    let target = e.target;
    while (target && target !== scroller) {
      if (target.scrollWidth > target.clientWidth + 2 && target.scrollLeft !== undefined) {
        const ov = getComputedStyle(target).overflowX;
        if (ov === 'auto' || ov === 'scroll') return;
      }
      target = target.parentElement;
    }
    startY = e.touches[0].clientY;
    startX = e.touches[0].clientX;
    pulling = true;
    locked = false;
    dist = 0;
  }, { passive: true });

  scroller.addEventListener('touchmove', function (e) {
    if (!pulling || busy || locked) return;
    const dy = e.touches[0].clientY - startY;
    const dx = Math.abs(e.touches[0].clientX - startX);
    /* If horizontal displacement exceeds vertical, this is a scroll gesture */
    if (dx > Math.abs(dy) + 4) {
      locked = true;
      if (dist > 0) snapBack();
      return;
    }
    if (dy <= 0 || scroller.scrollTop > 1) {
      pulling = false;
      if (dist > 0) snapBack();
      return;
    }
    dist = Math.min(dy * DAMPING, MAX_PULL);
    if (!raf) raf = requestAnimationFrame(render);
  }, { passive: true });

  scroller.addEventListener('touchend', end, { passive: true });
  scroller.addEventListener('touchcancel', end, { passive: true });

  function end() {
    if (locked) { locked = false; pulling = false; return; }
    if (!pulling || busy) return;
    pulling = false;
    if (raf) { cancelAnimationFrame(raf); raf = 0; }

    if (dist >= THRESHOLD) {
      busy = true;
      const sc = scrollerCenter();
      el.className = 'ptr ptr--load';
      el.style.left = sc.cx + 'px';
      el.style.top = sc.top + 'px';
      el.style.transform = 'translate(-50%, 8px)';
      el.style.opacity = '1';
      arc.style.strokeDashoffset = C * 0.25;
      arc.style.transform = '';
      try { navigator.vibrate(10); } catch (_) {}
      setTimeout(function () {
        if (typeof reloadKeepScroll === 'function') {
          reloadKeepScroll();
          return;
        }
        const freshUrl = window.GP?.cacheBustedCurrentUrl?.() || window.location.href;
        window.location.assign(freshUrl);
      }, 280);
    } else {
      snapBack();
    }
  }

    function snapBack() {
      el.style.transition = 'transform var(--transition-normal), opacity var(--transition-fast)';
      el.style.transform = 'translate(-50%, -48px)';
      el.style.opacity = '0';
      setTimeout(function () { el.style.transition = ''; reset(); }, 260);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPtr, { once: true });
  } else {
    initPtr();
  }
})();
