/**
 * GitPulse - GSAP motion system.
 *
 * ONE owner for every animation in the app. Before this module the app had 67
 * hand-written `@keyframes` spread over 25 stylesheets, each with its own
 * duration, easing and lifecycle (some `animationend`, some `setTimeout`, some
 * neither) - the same interaction animated differently depending on which page
 * you were on. Every one of those is now a named contract here, so a component
 * animates the same way everywhere and the whole app shares one clock.
 *
 * Division of labour, deliberately:
 *
 *   - GSAP owns ORCHESTRATED motion: anything with a beginning and an end, a
 *     sequence, or a lifecycle that other code has to wait on. Overlays,
 *     toasts, disclosure, loading hand-off, flashes, dismissals, progress.
 *   - CSS owns STATE INTERPOLATION (hover/focus/active colour changes) and
 *     CONTINUOUS LOOPS (spinners, pulses). Hover targets live in the
 *     stylesheets - that is what a hover rule *is* - and the single baseline
 *     rule in animations.css eases all of them on this module's tokens. Loops
 *     stay in CSS because they run on the compositor thread: a spinner is shown
 *     exactly when the main thread is busy, and a rAF-driven one stutters
 *     precisely then. Several also live on `::after`, which no JS can target.
 *
 * Durations and easings are READ FROM tokens.css, never redeclared here, so
 * `--motion-duration-*` stays the one place timing is defined. The cubic-beziers
 * map onto GSAP core's equivalents (no CustomEase plugin needed):
 *   standard    cubic-bezier(0.22, 0.61, 0.36, 1) -> power2.out
 *   emphasized  cubic-bezier(0.16, 1, 0.3, 1)     -> expo.out
 *   loop        cubic-bezier(0.42, 0, 0.58, 1)    -> sine.inOut
 *
 * If GSAP fails to load, every entry point below still exists and applies the
 * FINAL state synchronously. The app is never left mid-animation with a hidden
 * modal or an undismissed toast just because a script 404'd.
 */
(function _gsapMotionInit() {
  'use strict';

  window.GP = window.GP || {};

  const gsap = window.gsap;

  /* ------------------------------------------------------------------ *
   * Tokens: read once from :root so tokens.css stays authoritative.
   * ------------------------------------------------------------------ */

  function _seconds(name, fallback) {
    try {
      const raw = getComputedStyle(document.documentElement)
        .getPropertyValue(name).trim();
      if (!raw) return fallback;
      if (raw.endsWith('ms')) return parseFloat(raw) / 1000;
      if (raw.endsWith('s')) return parseFloat(raw);
      return fallback;
    } catch (_) {
      return fallback;
    }
  }

  function _number(name, fallback) {
    try {
      const raw = getComputedStyle(document.documentElement)
        .getPropertyValue(name).trim();
      const val = parseFloat(raw);
      return Number.isFinite(val) ? val : fallback;
    } catch (_) {
      return fallback;
    }
  }

  const D = {
    fast: _seconds('--motion-duration-fast', 0.1),
    normal: _seconds('--motion-duration-normal', 0.2),
    slow: _seconds('--motion-duration-slow', 0.4),
    progress: _seconds('--gl-anim-progress', 0.6),
    tour: _seconds('--motion-duration-tour', 0.4),
    flash: _seconds('--gl-anim-flash', 0.6),
    highlight: _seconds('--gl-anim-highlight', 1.8)
  };

  /* The easing vocabulary is GitLab's, and it is three curves long.
     Ground truth, @gitlab/ui 136.2.0 `src/scss/variables.scss:203-205`:

       $gl-easing-linear:    linear
       $gl-easing-default:   ease
       $gl-easing-out-cubic: cubic-bezier(0.22, 0.61, 0.36, 1)

     and every transition in their built CSS uses one of those three. There is
     no spring, no overshoot and no elastic anywhere in the library.

     `power2.out` IS out-cubic: GSAP defines it as cubic-bezier(0.215, 0.61,
     0.355, 1), which is GitLab's curve to three decimals - so `standard` is a
     literal match rather than an approximation.

     The overshoot easings that used to live here (`back.out(1.4)` for
     entrances, `back.out(1.7)` for pops, `elastic.out` for the shake) are gone.
     An overshoot spends its last third travelling BACK to where it was already
     going, so a 0.42s entrance reads as slower than a 0.42s ease - which is the
     "animations feel sluggish" report - and on a scaled panel it also leaves
     text mis-scaled, and therefore re-rasterised, for those frames. */
  const E = {
    standard: 'power2.out',   /* = GitLab out-cubic */
    emphasized: 'expo.out',   /* draw-in for the compliance ring only */
    exit: 'power2.in',
    loop: 'sine.inOut',
    linear: 'none'
  };

  /* How far apart the members of a group start. Long enough to read as a
     sequence, short enough that the last item is not left waiting. */
  const STAGGER = 0.045;

  /* ------------------------------------------------------------------ *
   * Reduced motion. One switch, consulted by every helper via `dur()`.
   * ------------------------------------------------------------------ */

  let REDUCED = false;
  try {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    REDUCED = mq.matches;
    const _onChange = function (e) { REDUCED = e.matches; };
    if (mq.addEventListener) mq.addEventListener('change', _onChange);
    else if (mq.addListener) mq.addListener(_onChange);
  } catch (_) {
    REDUCED = false;
  }

  /** Duration for a tween, collapsed to ~0 when the user asked for less motion.
   *  Never exactly 0: GSAP still runs onComplete for a 0-duration tween, but a
   *  hair of time keeps `from` tweens from painting their start frame. */
  function dur(seconds) {
    return REDUCED ? 0.001 : seconds;
  }

  /* ------------------------------------------------------------------ *
   * No-GSAP shim
   *
   * If the vendored library ever fails to load, EVERY entry point below must
   * still work: a modal that will not close and a toast that never leaves are
   * far worse than an app without animation. Rather than a second copy of the
   * API that drifts from the real one, this shim implements the handful of
   * GSAP calls this module makes and lands each one on its END state
   * immediately. One code path, so there is nothing to keep in sync.
   * ------------------------------------------------------------------ */

  const G = gsap || (function _shim() {
    /* Apply final states when GSAP is unavailable, including the navigation fill. */
    const DIRECT = {
      opacity: 1, height: 1, width: 1, display: 1, overflow: 1, backgroundColor: 1,
      marginBottom: 1, marginTop: 1, paddingTop: 1, paddingBottom: 1,
      borderTopWidth: 1, borderBottomWidth: 1, strokeDashoffset: 1
    };

    const apply = function (target, vars) {
      if (!target || !vars) return;
      const els = target.length != null && !target.style ? target : [target];
      for (const el of els) {
        if (!el || !el.style) continue;
        if (vars.clearProps) {
          const names = String(vars.clearProps) === 'all'
            ? Object.keys(DIRECT).concat(['transform'])
            : String(vars.clearProps).split(',');
          names.forEach(function (n) { el.style.removeProperty(_dashed(n.trim())); });
          continue;
        }
        for (const key in vars) {
          if (!DIRECT[key]) continue;
          const v = vars[key];
          el.style[key] = typeof v === 'number' && key !== 'opacity' ? v + 'px' : v;
        }
      }
      if (typeof vars.onComplete === 'function') vars.onComplete();
    };

    const _dashed = function (n) { return n.replace(/[A-Z]/g, function (c) { return '-' + c.toLowerCase(); }); };

    const chain = {
      to: function (t, v) { apply(t, v); return chain; },
      from: function () { return chain; },
      fromTo: function (t, _f, v) { apply(t, v); return chain; }
    };

    return {
      defaults: function () {}, config: function () {},
      set: apply,
      to: apply,
      from: function (t, v) { apply(t, { clearProps: 'all', onComplete: v && v.onComplete }); },
      fromTo: function (t, _from, to) { apply(t, to); },
      killTweensOf: function () {},
      quickTo: function (t, prop) {
        return function (value) { apply(t, _one(prop, value)); };
      },
      timeline: function (vars) {
        const tl = Object.create(chain);
        if (vars && typeof vars.onComplete === 'function') {
          Promise.resolve().then(vars.onComplete);
        }
        return tl;
      }
    };

    function _one(prop, value) { const o = {}; o[prop] = value; return o; }
  })();

  G.defaults({ duration: D.normal, ease: E.standard, overwrite: 'auto' });
  /* Sub-pixel transforms on text produce visible re-rasterisation blur while a
     tween runs. Every transform in this module lands on a whole pixel. */
  G.config({ force3D: false });

  /* ------------------------------------------------------------------ *
   * Primitives
   * ------------------------------------------------------------------ */

  /** Kill any tween this module started on `el` and drop the inline styles it
   *  wrote, so CSS is authoritative again the moment motion ends. */
  function settle(el, props) {
    if (!el) return;
    G.killTweensOf(el);
    G.set(el, { clearProps: props || 'all' });
  }

  /* ------------------------------------------------------------------ *
   * Overlays - modal, backdrop, search palette, tour popover
   *
   * GitLab's modal is Bootstrap's: the backdrop fades (`opacity 0.15s linear`)
   * and the dialog travels 50px down into place (`transform 0.3s ease-out`).
   * The dialog deliberately does NOT fade: it is a child of the backdrop, and
   * nested opacity multiplies - fading both double-exposed everything inside.
   * ------------------------------------------------------------------ */

  function overlayIn(backdrop, dialog) {
    if (!backdrop) return;
    G.killTweensOf(backdrop);
    G.fromTo(backdrop, { opacity: 0 },
      { opacity: 1, duration: dur(0.15), ease: E.linear, clearProps: 'opacity' });
    if (dialog) {
      G.killTweensOf(dialog);
      /* GitLab's modal motion exactly: `.modal.fade .modal-dialog { transition:
         transform 0.3s ease-out }` with the dialog starting 50px above its
         resting place (@gitlab/ui 136.2.0 dist/index.css - Bootstrap's modal,
         which GitLab keeps). No scale: it was 0.985 -> 1 on an overshoot curve,
         which re-rasterises every glyph in the dialog for the length of the
         entrance. No opacity either - the dialog is a child of the backdrop and
         nested opacity multiplies, which double-exposed everything inside. */
      G.fromTo(dialog,
        { y: -50 },
        {
          y: 0,
          duration: dur(0.3), ease: E.standard,
          clearProps: 'transform'
        });
    }
  }

  function overlayOut(backdrop, onDone) {
    if (!backdrop) { if (onDone) onDone(); return; }
    G.killTweensOf(backdrop);
    G.to(backdrop, {
      opacity: 0,
      duration: dur(D.normal),
      ease: E.exit,
      onComplete: function () { if (onDone) onDone(); }
    });
  }

  /* Search grows from its top-bar field, then returns to it. On phones reveal
     a fixed-size layer with clipping/translation, avoiding per-frame layout.
     `instant` settles it at once - a jump to another page, whose own
     transition must not run under the palette's way back. */
  const SEARCH_MOTIONS = new WeakMap();
  const SEARCH_BOX = 'position,left,top,width,height,maxWidth,maxHeight,borderRadius,transform,clipPath,willChange';

  function searchPalette(backdrop, trigger, opening, onDone, instant) {
    if (!backdrop) { if (onDone) onDone(); return; }
    const panel = backdrop.querySelector('.gl-search-modal');
    const field = backdrop.querySelector('.gl-search-modal-input-wrap');
    const results = backdrop.querySelector('.gl-search-modal-body');
    let shade = backdrop.querySelector('.gl-search-modal-shade');
    const rows = [field, results];
    const previous = SEARCH_MOTIONS.get(backdrop);
    const current = previous && panel ? previous.bounds() : null;
    const currentClip = panel ? getComputedStyle(panel).clipPath : '';
    const currentRadius = panel ? getComputedStyle(panel).borderRadius : '';
    const currentOpacity = shade ? getComputedStyle(shade).opacity : 0;
    const visibility = previous ? previous.visibility : (trigger?.style.visibility || '');
    if (previous) previous.cancel();
    G.killTweensOf([panel, field, results, shade]);
    panel.classList.remove('is-morphing');
    G.set(panel, { clearProps: SEARCH_BOX });
    G.set(rows, { clearProps: 'width,height' });
    if (shade) G.set(shade, { clearProps: 'opacity' });

    const source = trigger?.getBoundingClientRect();
    if (instant || !gsap || REDUCED || !panel || !source?.width || !source.height) {
      SEARCH_MOTIONS.delete(backdrop);
      if (trigger) trigger.style.visibility = visibility;
      if (onDone) onDone();
      return;
    }

    const expanded = panel.getBoundingClientRect();
    const rowSizes = rows.map(function (row) { return row.getBoundingClientRect(); });
    const expandedRadius = getComputedStyle(panel).borderRadius;
    /* A pill can declare 9999px; interpolate its rendered radius instead. */
    const radius = Math.min(parseFloat(getComputedStyle(trigger).borderRadius) || 0,
      source.width / 2, source.height / 2) + 'px';
    const sourceRadius = [radius, radius, radius, radius].join(' ');
    const mobile = window.matchMedia('(max-width: 768px)').matches;
    const viewportWidth = window.innerWidth;
    const from = current || (opening ? source : expanded);
    const to = opening ? expanded : source;
    if (!shade) {
      shade = document.createElement('div');
      shade.className = 'gl-search-modal-shade';
      shade.setAttribute('aria-hidden', 'true');
      backdrop.prepend(shade);
      backdrop.classList.add('has-motion-shade');
    }
    const clip = function (box, radius) {
      const corners = radius.trim().split(/\s+/);
      radius = [corners[0], corners[1] || corners[0], corners[2] || corners[0],
        corners[3] || corners[1] || corners[0]].join(' ');
      return 'inset(0px ' + Math.max(0, expanded.width - box.width) + 'px ' +
        Math.max(0, expanded.height - box.height) + 'px 0px round ' + radius + ')';
    };
    const fromClip = clip(from, current && currentClip.includes('round') ?
      currentClip.split('round')[1].slice(0, -1).trim() : (opening ? sourceRadius : expandedRadius));
    const bounds = function () {
      const rect = panel.getBoundingClientRect();
      if (!mobile) return rect;
      const inset = getComputedStyle(panel).clipPath.split('round')[0].match(/[\d.]+/g);
      return { left: rect.left, top: rect.top,
        width: rect.width - (Number(inset?.[1]) || 0),
        height: rect.height - (Number(inset?.[2]) || 0) };
    };
    let timeline;
    let startFrame;
    let finished = false;
    const cancel = function () {
      if (timeline) timeline.kill();
      cancelAnimationFrame(startFrame);
      window.removeEventListener('resize', onResize);
    };
    const onResize = function () {
      /* Opening the phone keyboard changes height, not the source anchor. */
      if (!mobile || window.innerWidth !== viewportWidth) finish();
    };
    const finish = function () {
      if (finished) return;
      finished = true;
      cancel();
      const height = bounds().height;
      panel.classList.remove('is-morphing');
      G.set(panel, { clearProps: SEARCH_BOX });
      G.set(rows, { clearProps: 'width,height' });
      G.set(shade, { clearProps: 'opacity' });
      if (opening && !mobile) resizeFrom(panel, height);
      if (!opening) {
        trigger.style.visibility = visibility;
        SEARCH_MOTIONS.delete(backdrop);
      }
      if (onDone) onDone();
    };
    SEARCH_MOTIONS.set(backdrop, { cancel: cancel, visibility: visibility, bounds: bounds });
    trigger.style.visibility = 'hidden';
    panel.classList.add('is-morphing');
    G.set(panel, {
      position: 'fixed', left: mobile ? expanded.left : from.left, top: mobile ? expanded.top : from.top,
      width: mobile ? expanded.width : from.width, height: mobile ? expanded.height : from.height,
      maxWidth: 'none', maxHeight: 'none',
      borderRadius: mobile ? expandedRadius : (current ? currentRadius : (opening ? sourceRadius : expandedRadius))
    });
    if (mobile) G.set(panel, {
      x: from.left - expanded.left, y: from.top - expanded.top,
      clipPath: fromClip,
      willChange: 'transform, clip-path', force3D: true
    });
    /* Reveal full-size rows through the growing shell. Neither the input nor
       the results reflow or shrink into a temporary scroll container. */
    rows.forEach(function (row, i) {
      row.style.width = rowSizes[i].width + 'px';
      row.style.height = rowSizes[i].height + 'px';
    });
    G.set(shade, { opacity: previous ? currentOpacity : (opening ? 0 : 1) });
    timeline = G.timeline({ paused: true, onComplete: finish });
    const destination = mobile ? {
      x: to.left - expanded.left, y: to.top - expanded.top,
      clipPath: clip(to, opening ? expandedRadius : sourceRadius)
    } : {
      left: to.left, top: to.top, width: to.width, height: to.height,
      borderRadius: opening ? expandedRadius : sourceRadius
    };
    const timing = { duration: opening ? D.normal : D.fast, ease: E.standard };
    if (mobile) timeline.fromTo(panel, {
      x: from.left - expanded.left, y: from.top - expanded.top,
      clipPath: fromClip
    }, Object.assign(destination, timing), 0);
    else timeline.to(panel, Object.assign(destination, timing), 0);
    timeline.to(shade, {
      opacity: opening ? 1 : 0,
      duration: opening ? D.normal : D.fast, ease: E.standard
    }, 0);
    window.addEventListener('resize', onResize);
    /* Start after preparation and input focus, so slow devices still see the
       full transition rather than catching up to a stale GSAP ticker time. */
    startFrame = requestAnimationFrame(function () { timeline.play(0); });
  }

  /* ------------------------------------------------------------------ *
   * Popovers - dropdown panels, selects, flatpickr, tour
   *
   * Measured on GitLab: dropdowns have ZERO motion in either direction. Ours
   * keep a very short fade so the panel does not simply blink into existence,
   * but no travel and no scale - a panel that grows reads as a different
   * component from GitLab's.
   * ------------------------------------------------------------------ */

  /* Driver.js keeps measuring the live target while its scroll container moves.
     Interpolate a temporary copy towards that live path, so scroll refreshes
     cannot replace the visible highlight in the middle of a step transition. */
  const TOUR_HIGHLIGHTS = new WeakMap();

  function tourScroll(scroller, position) {
    if (!position) { G.killTweensOf(scroller, 'scrollTop,scrollLeft'); return; }
    if (!gsap || REDUCED) { Object.assign(scroller, position); return; }
    G.to(scroller, Object.assign({ duration: dur(D.tour), ease: E.standard }, position));
  }

  function tourHighlight(overlay, animate, remainingScroll, options = {}) {
    const { reveal, collapse, track, onComplete } = options;
    if (!overlay) { onComplete?.(); return; }
    const path = overlay.firstElementChild;
    const previous = TOUR_HIGHLIGHTS.get(overlay);
    let from = (previous?.copy || path)?.getAttribute('d');
    if (previous) previous.finish();
    if (!animate || !gsap || REDUCED || !from) { onComplete?.(); return; }
    const trackedOrigin = track?.();
    const movePath = (d, x, y) => d.replace(/(Z\s+M)([-\d.e+]+),([-\d.e+]+)/,
      (_match, move, px, py) => move + (Number(px) + x) + ',' + (Number(py) + y));
    const trackedPath = (rect) => {
      const r = Math.min(6, (rect.width + 12) / 2, (rect.height + 12) / 2);
      const w = rect.width + 12 - 2 * r, h = rect.height + 12 - 2 * r;
      return from.split('Z')[0] + `Z M${rect.left - 6 + r},${rect.top - 6}
        h${w} a${r},${r} 0 0 1 ${r},${r} v${h} a${r},${r} 0 0 1 -${r},${r}
        h-${w} a${r},${r} 0 0 1 -${r},-${r} v-${h} a${r},${r} 0 0 1 ${r},-${r} z`;
    };

    const slit = (rect) => from.split('Z')[0] + `Z M${rect.x},${rect.y}
      h${rect.width} a0,0 0 0 1 0,0 v0 a0,0 0 0 1 0,0
      h-${rect.width} a0,0 0 0 1 0,0 v0 a0,0 0 0 1 0,0 z`;
    let folded;
    if (collapse) {
      // Fold the currently visible cut-out, including an interrupted reveal,
      // towards its own centre rather than Driver.js' centred dummy element.
      const n = from.slice(from.indexOf('Z') + 1).match(/[+-]?\d*\.?\d+(?:e[+-]?\d+)?/ig)?.map(Number);
      if (!n || (n[10] === 0 && n[3] === 0)) { onComplete?.(); return; }
      folded = slit({ x: n[0] - n[3], y: n[1] + n[10] / 2 + n[3], width: n[2] + 2 * n[3] });
    } else if (reveal && !previous) {
      // Open a full-width slit at the target, never a rounded point at the
      // viewport centre. The zero-height cut-out starts with a solid backdrop.
      from = slit(reveal);
    }
    const copy = path.cloneNode();
    copy.setAttribute('d', from);
    copy.classList.add('gp-tour-highlight-path');
    overlay.append(copy);
    const visibility = path.style.visibility;
    path.style.visibility = 'hidden';
    const progress = { value: 0 };
    let startFrame;
    const finish = function () {
      cancelAnimationFrame(startFrame);
      G.killTweensOf(progress);
      copy.remove();
      path.style.visibility = visibility;
      TOUR_HIGHLIGHTS.delete(overlay);
    };
    TOUR_HIGHLIGHTS.set(overlay, { copy: copy, finish: finish });
    const tween = G.to(progress, {
      value: 1, paused: true, duration: dur(D.tour), ease: E.standard,
      onUpdate: function () {
        if (!overlay.isConnected) { finish(); onComplete?.(); return; }
        const offset = remainingScroll?.() || { x: 0, y: 0 };
        // Driver.js' path has a fixed viewport outline followed by a relative
        // rounded cut-out. Move only that cut-out to its post-scroll position.
        const rect = track?.();
        const to = folded || movePath(rect ? trackedPath(rect) : path.getAttribute('d'), -offset.x, -offset.y);
        const start = rect && reveal && !previous
          ? slit({ x: rect.left - 6, y: rect.top + rect.height / 2, width: rect.width + 12 }) : from;
        let d = gsap.utils.interpolate(start, to, progress.value);
        if (folded && rect) d = movePath(d, rect.left - trackedOrigin.left, rect.top - trackedOrigin.top);
        copy.setAttribute('d', d);
      },
      onComplete: function () {
        if (track && !collapse) path.setAttribute('d', copy.getAttribute('d'));
        finish(); onComplete?.();
      }
    });
    // Driver.js writes its new target on the next frame. Start after that
    // measurement so the first reveal never interpolates towards its dummy.
    startFrame = requestAnimationFrame(function () { tween.play(0); });
  }

  function tourStep(el, previous) {
    if (!el || !previous?.width || !gsap || REDUCED) return;
    const height = el.getBoundingClientRect().height;
    // Resize the box at its destination anchor before measuring the offset.
    // Preserving only the old top with the new height makes the footer jump.
    el.style.height = previous.height + 'px';
    const rect = el.getBoundingClientRect();
    el.classList.add('gp-tour-popover--moving');
    G.set(el, {
      '--gp-tour-x': (previous.left - rect.left) + 'px',
      '--gp-tour-offset': (previous.top - rect.top) + 'px'
    });
    G.to(el, {
      height: height, '--gp-tour-x': '0px', '--gp-tour-offset': '0px', autoRound: false,
      duration: dur(D.tour), ease: E.standard,
      onComplete: function () {
        el.style.removeProperty('height');
        el.style.removeProperty('--gp-tour-x');
        el.style.removeProperty('--gp-tour-offset');
        el.classList.remove('gp-tour-popover--moving');
      }
    });
  }

  function tourPopover(el, entering, onComplete) {
    if (!el) { onComplete?.(); return; }
    G.killTweensOf(el);
    if (!gsap || REDUCED) {
      el.style.setProperty('--gp-tour-offset', '0px');
      G.set(el, { opacity: entering ? 1 : 0 });
      onComplete?.();
      return;
    }
    const compact = matchMedia('(max-width: 768px), (max-height: 480px) and (orientation: landscape)').matches;
    // Step transitions use pixels. Mixing them with percentages on interruption
    // makes GSAP convert against the parent instead of the card's own height.
    const offset = (compact ? el.getBoundingClientRect().height *
      (el.classList.contains('gp-tour-popover--mobile-top') ? -1 : 1) : 12) + 'px';
    el.classList.add('gp-tour-popover--moving');
    if (entering) G.set(el, { '--gp-tour-offset': offset, opacity: compact ? 1 : 0 });
    G.to(el, {
      '--gp-tour-offset': entering ? '0px' : offset,
      opacity: entering ? 1 : 0,
      duration: dur(D.tour), ease: entering ? E.standard : E.exit,
      onComplete: function () {
        if (entering) el.classList.remove('gp-tour-popover--moving');
        onComplete?.();
      }
    });
  }

  function popIn(el) {
    if (!el) return;
    G.killTweensOf(el);
    /* Rises the last few pixels into place instead of blinking on. 4px is
       enough to give the panel a direction it came from; more and it reads as
       sliding, which fights the anchor it is pinned to. */
    G.fromTo(el,
      { opacity: 0, y: -4 },
      {
        opacity: 1, y: 0,
        duration: dur(D.fast), ease: E.standard,
        clearProps: 'opacity,transform'
      });
  }

  function popOut(el, onDone) {
    if (!el) { if (onDone) onDone(); return; }
    G.killTweensOf(el);
    G.to(el, {
      opacity: 0, y: -4,
      duration: dur(D.fast),
      ease: E.exit,
      onComplete: function () { if (onDone) onDone(); }
    });
  }

  /* ------------------------------------------------------------------ *
   * Edge strips - cookie banner, login banner, login auth alert
   *
   * One contract for "a strip that arrives from an edge and leaves the same
   * way". These were four near-identical keyframe pairs (cookieBannerIn/Out,
   * loginBannerIn, loginAlertIn/Out) differing only in direction and distance,
   * each on its own duration.
   *
   * @param {Element} el
   * @param {number|string} dy where it starts: px number, or '100%' / '-100%'
   *        for a full strip height off the bottom / top edge.
   * ------------------------------------------------------------------ */

  function edgeIn(el, dy) {
    if (!el) return;
    G.killTweensOf(el);
    G.fromTo(el,
      { opacity: 0, y: dy },
      {
        opacity: 1, y: 0,
        duration: dur(D.normal), ease: E.standard,
        clearProps: 'opacity,transform'
      });
  }

  function edgeOut(el, dy, onDone) {
    if (!el) { if (onDone) onDone(); return; }
    G.killTweensOf(el);
    G.to(el, {
      opacity: 0, y: dy,
      duration: dur(D.normal), ease: E.exit,
      onComplete: function () { if (onDone) onDone(); }
    });
  }

  /* ------------------------------------------------------------------ *
   * Toasts
   *
   * Grow in from their own position and shrink back into it, then the row
   * collapses so the stack reflows underneath. The collapse is a SEPARATE
   * phase: fading and collapsing at once made the remaining toasts jump while
   * the dismissed one was still legible.
   * ------------------------------------------------------------------ */

  function toastIn(el) {
    if (!el) return;
    /* Arrives from the edge it is docked to. Fade + a short travel, no scale:
       a toast that grows from 0.88 re-rasterises its text for the whole
       entrance and reads as a different component from the alert it replaces.
       0.2s is GitLab's medium token ($gl-transition-duration-medium).
       The stack staggers: when several land together they read as a queue
       rather than one block appearing. */
    const siblings = el.parentElement
      ? Array.prototype.indexOf.call(el.parentElement.children, el)
      : 0;
    G.fromTo(el,
      { opacity: 0, x: -12 },
      {
        opacity: 1, x: 0,
        duration: dur(D.normal), ease: E.standard,
        delay: REDUCED ? 0 : Math.min(siblings, 3) * STAGGER,
        clearProps: 'opacity,transform'
      });
  }

  function toastOut(el, onDone) {
    if (!el) { if (onDone) onDone(); return; }
    G.killTweensOf(el);
    const finish = function () { if (onDone) onDone(); };
    if (REDUCED) { finish(); return; }

    const tl = G.timeline({ onComplete: finish });
    tl.to(el, {
      opacity: 0, x: -16,
      duration: D.normal * 0.6, ease: E.exit
    })
      .to(el, {
        height: 0, marginBottom: -8, paddingTop: 0, paddingBottom: 0,
        borderTopWidth: 0, borderBottomWidth: 0,
        duration: D.normal * 0.55, ease: E.standard
      });
  }

  /** Run a change to the stack - an arrival - and slide the toasts that it
   *  displaced from where they were to where they now are, instead of letting
   *  them jump. The stack is pinned to the bottom edge, so every toast already
   *  on screen moves up by one slot the instant a new one is appended; with
   *  several landing a few hundred milliseconds apart that read as the pile
   *  "falling out". A toast still playing its own entrance or exit is left to
   *  that tween. */
  function toastReflow(container, mutate) {
    if (!container) { if (mutate) mutate(); return; }
    const before = new Map();
    Array.prototype.forEach.call(container.children, function (el) {
      before.set(el, el.getBoundingClientRect().top);
    });
    if (mutate) mutate();
    if (REDUCED) return;
    before.forEach(function (top, el) {
      if (!el.isConnected) return;
      if (typeof G.isTweening === 'function' && G.isTweening(el)) return;
      const dy = top - el.getBoundingClientRect().top;
      if (Math.abs(dy) < 0.5) return;
      G.fromTo(el, { y: dy }, {
        y: 0, duration: dur(D.normal), ease: E.standard, clearProps: 'transform'
      });
    });
  }

  /** The auto-dismiss countdown bar. Driven as a real tween so hover-to-pause
   *  is `.pause()` on the same object, instead of a second CSS rule toggling
   *  `animation-play-state` that could not be resumed from JS. */
  function toastCountdown(bar, ttlMs) {
    if (!bar || !ttlMs || ttlMs <= 0) return;
    /* A countdown can start over (toastAgain); the old tween must not keep
       pulling the same bar towards its own end. */
    if (bar._gpCountdown && typeof bar._gpCountdown.kill === 'function') bar._gpCountdown.kill();
    if (REDUCED) { G.set(bar, { scaleX: 0 }); return; }
    const tw = G.fromTo(bar,
      { scaleX: 1 },
      { scaleX: 0, duration: ttlMs / 1000, ease: E.linear });
    bar._gpCountdown = tw;
  }

  function toastPause(toast) {
    const bar = toast && toast.querySelector('.toast-progress-bar');
    if (bar && bar._gpCountdown) bar._gpCountdown.pause();
  }

  function toastResume(toast) {
    const bar = toast && toast.querySelector('.toast-progress-bar');
    if (bar && bar._gpCountdown) bar._gpCountdown.resume();
  }

  /** The same toast was raised again while it is still on screen. showToast
   *  does not stack a second copy; the one already up is SAID AGAIN instead:
   *  it replays the entrance every toast plays (toastIn), from where it
   *  stands, with a ring in its own accent and its repeat count ("x2") popping
   *  in. An 8px knock was tried first and read as "the toast did not come" -
   *  the entrance is the gesture a reader already knows means "new message".
   *  Under reduced motion only the ring fades, the way `highlight` does it:
   *  colour, no travel.
   *
   *  Raised again while it is still replaying: it starts over. Still playing
   *  its first ENTRANCE (or sliding to a new slot): left alone - it is where
   *  the eye is going anyway, and killing that tween would strand it half
   *  faded in. */
  function toastAgain(toast) {
    if (!toast) return;
    const running = toast._gpAgain;
    if (running && typeof running.isActive === 'function' && running.isActive()) {
      running.restart();
      return;
    }
    if (typeof G.isTweening === 'function' && G.isTweening(toast)) return;

    const accent = getComputedStyle(toast).getPropertyValue('--_toast-accent').trim()
      || _token('--primary', '#428fdc');
    const tl = G.timeline();
    tl.fromTo(toast,
      { boxShadow: '0 0 0 2px ' + accent },
      {
        boxShadow: '0 0 0 2px ' + _fadeTo(accent),
        duration: D.slow * 2, ease: E.standard, clearProps: 'boxShadow'
      }, 0);
    if (!REDUCED) {
      tl.fromTo(toast,
        { opacity: 0.2, x: -12 },
        { opacity: 1, x: 0, duration: dur(D.normal), ease: E.standard, clearProps: 'opacity,transform' }, 0);
      const count = toast.querySelector('.toast-repeat');
      if (count) {
        tl.fromTo(count,
          { scale: 1.4 },
          { scale: 1, duration: dur(D.normal), ease: E.standard, clearProps: 'transform' }, 0);
      }
    }
    toast._gpAgain = tl;
  }

  /* ------------------------------------------------------------------ *
   * Bottom sheet - the release of a drag
   *
   * The DRAG itself is a gesture: the sheet follows the finger, written straight
   * to `transform` by the handler that reads the touch. What happens when the
   * finger LIFTS is an animation, and it belongs here like every other one.
   *
   * It used to live in the modal code as two inline `style.transition` strings
   * plus two setTimeouts (400ms and 220ms) that restated those durations, and
   * one of the strings still asked for `--motion-ease-spring` - a token that no
   * longer exists, so it was silently falling back to a hard-coded overshoot
   * curve nothing else in the app uses.
   * ------------------------------------------------------------------ */

  /** Settle the sheet back to its resting place (the drag did not pass the
   *  dismiss threshold). */
  function sheetSettle(el, onDone) {
    if (!el) { if (onDone) onDone(); return; }
    G.killTweensOf(el);
    G.to(el, {
      y: 0,
      duration: dur(D.normal), ease: E.standard,
      clearProps: 'transform',
      onComplete: function () { if (onDone) onDone(); }
    });
  }

  /** Carry the sheet the rest of the way off-screen from wherever the finger
   *  left it, so the dismissal continues the gesture instead of snapping back
   *  and replaying a canned slide. */
  function sheetDismiss(el, distance, onDone) {
    if (!el) { if (onDone) onDone(); return; }
    G.killTweensOf(el);
    G.to(el, {
      y: distance,
      duration: dur(D.normal), ease: E.exit,
      onComplete: function () {
        G.set(el, { clearProps: 'transform' });
        if (onDone) onDone();
      }
    });
  }

  /* ------------------------------------------------------------------ *
   * Tab panels
   *
   * OPACITY ONLY. A tab panel wraps a whole data table; moving or scaling it
   * promotes the table to its own compositor layer and repaints it mid-switch,
   * which tore the table visibly. The outgoing panel leaves the layout at once
   * (it is `hidden`), so the incoming one fades over a layout already final -
   * nothing grows and snaps back.
   * ------------------------------------------------------------------ */

  function panelIn(el) {
    if (!el) return;
    G.fromTo(el, { opacity: 0 },
      { opacity: 1, duration: dur(D.fast), ease: E.standard, clearProps: 'opacity' });
  }

  /* Hold the last painted page while its replacement initialises. The copy is
     inert and stripped of behaviour; the incoming DOM can measure its layout
     behind it. Only this cover fades, so the content never fades from blank. */
  const _pageCovers = new WeakMap();
  const _coverSheets = new WeakMap();
  function coverStyleSheets() {
    return Array.from(document.styleSheets).flatMap(function (sheet) {
      try {
        if (!_coverSheets.has(sheet)) {
          const copy = new CSSStyleSheet();
          copy.replaceSync(Array.from(sheet.cssRules, rule => rule.cssText).join('\n'));
          _coverSheets.set(sheet, copy);
        }
        return [_coverSheets.get(sheet)];
      } catch (_) { return []; } // Cross-origin font sheets are already loaded by the document.
    });
  }
  function coverPage(el) {
    if (!el) return;
    const previous = _pageCovers.get(el);
    if (previous) {
      if (el.classList.contains('is-arriving')) return;
      G.killTweensOf(previous);
      previous.remove();
    }
    const scroller = el.closest('.gl-page-content');
    if (!scroller) return;
    const viewport = scroller.getBoundingClientRect();
    const box = el.getBoundingClientRect();
    const top = Math.max(viewport.top, box.top);
    if (top >= viewport.bottom) return;
    const copy = el.cloneNode(true);
    const nodes = [el, ...el.querySelectorAll('*')];
    const copies = [copy, ...copy.querySelectorAll('*')];
    const originals = el.querySelectorAll('canvas');
    copy.querySelectorAll('canvas').forEach(function (canvas, index) {
      try { canvas.getContext('2d').drawImage(originals[index], 0, 0); } catch (_) { /* empty canvas */ }
    });
    copy.querySelectorAll('script, iframe, .modal-backdrop').forEach(n => n.remove());
    copies.forEach(function (node) {
      Array.from(node.attributes).forEach(function (attr) {
        if (/^(autofocus$|on)/.test(attr.name)) node.removeAttribute(attr.name);
      });
    });
    copy.classList.remove('is-navigating', 'is-refining', 'is-arriving');
    Object.assign(copy.style, {
      position: 'absolute', margin: '0', width: box.width + 'px',
      left: (box.left - viewport.left) + 'px', top: (box.top - top) + 'px',
      opacity: getComputedStyle(el).opacity
    });
    const cover = document.createElement('div');
    cover.className = 'gp-page-cover';
    cover.setAttribute('aria-hidden', 'true');
    cover.setAttribute('x-ignore', '');
    cover.setAttribute('hx-disable', '');
    cover.inert = true;
    Object.assign(cover.style, {
      left: viewport.left + 'px', top: top + 'px', width: scroller.clientWidth + 'px',
      height: (viewport.bottom - top) + 'px'
    });
    // Shadow DOM keeps the original component selectors and label identities
    // without exposing duplicate IDs or declarative handlers to the live page.
    const shadow = cover.attachShadow({ mode: 'open' });
    shadow.adoptedStyleSheets = coverStyleSheets();
    let root = copy;
    for (let parent = el.parentElement; parent; parent = parent.parentElement) {
      const context = parent.cloneNode(false);
      context.style.setProperty('display', 'contents', 'important');
      context.appendChild(root);
      root = context;
    }
    shadow.appendChild(root);
    scroller.appendChild(cover);
    nodes.forEach(function (node, index) {
      copies[index].scrollLeft = node.scrollLeft;
      copies[index].scrollTop = node.scrollTop;
    });
    // Freeze sticky/fixed controls at the painted position, independent of the
    // incoming page's scroll range and the cover's clipped viewport.
    const pinned = nodes.flatMap(function (node, index) {
      if (!node.checkVisibility() || !/^(sticky|fixed)$/.test(getComputedStyle(node).position)) return [];
      const before = node.getBoundingClientRect(), after = copies[index].getBoundingClientRect();
      return [{ node: copies[index], x: before.left - after.left, y: before.top - after.top }];
    });
    pinned.forEach(item => { item.node.style.translate = item.x + 'px ' + item.y + 'px'; });
    _pageCovers.set(el, cover);
  }

  function uncoverPage(el, immediate = false) {
    const cover = el && _pageCovers.get(el);
    if (!cover) return;
    const remove = function () {
      cover.remove();
      if (_pageCovers.get(el) === cover) _pageCovers.delete(el);
    };
    G.killTweensOf(cover);
    if (immediate) { remove(); return; }
    G.to(cover, { opacity: 0, duration: dur(D.normal), ease: E.standard, onComplete: remove });
  }

  /* ------------------------------------------------------------------ *
   * Tab ink bar
   *
   * A single underline that TRAVELS from the old tab to the new one, instead of
   * each tab drawing and erasing its own bottom border. The travelling bar is
   * what makes a tab strip feel like one control rather than a row of separate
   * buttons - and it is the piece the user is looking at while the panel
   * underneath swaps, which covers the moment the content changes.
   *
   * One element per strip, positioned with transform only, so it composites and
   * costs nothing per frame.
   * ------------------------------------------------------------------ */

  const INK_CLASS = 'gp-tab-ink';

  function _inkBar(strip) {
    let bar = strip.querySelector(':scope > .' + INK_CLASS);
    if (!bar) {
      bar = document.createElement('span');
      bar.className = INK_CLASS;
      bar.setAttribute('aria-hidden', 'true');
      /* The strip has to be a positioning context. Setting it here rather than
         in CSS keeps the bar entirely opt-in: a strip that never activates a
         tab never gets one. */
      if (getComputedStyle(strip).position === 'static') {
        strip.style.position = 'relative';
      }
      strip.appendChild(bar);
    }
    return bar;
  }

  /** Move the ink bar under `tab`. Called on every activation, including the
   *  first, so the bar starts in the right place instead of sliding in from
   *  the left edge on page load. */
  function inkTo(tab) {
    if (!tab || !tab.offsetParent) return;
    const strip = tab.parentElement;
    if (!strip) return;

    const bar = _inkBar(strip);
    const x = tab.offsetLeft;
    const w = tab.offsetWidth;
    if (!w) return;

    const first = bar.dataset.placed !== '1';
    bar.dataset.placed = '1';

    if (first || REDUCED) {
      G.set(bar, {
        x: x,
        scaleX: w,
        opacity: 1
      });
      return;
    }

    /* Width travels as scaleX off a 1px base, so the bar never triggers layout
       while it moves. */
    G.to(bar, {
      x: x,
      scaleX: w,
      opacity: 1,
      duration: dur(D.normal),
      ease: E.standard
    });
  }

  /* ------------------------------------------------------------------ *
   * Disclosure (details / collapsible card bodies)
   *
   * Real height animation from 0 to the measured content height, then height is
   * cleared so the panel resizes naturally afterwards. This replaces the
   * `interpolate-size` + `::details-content` CSS, which only worked in Chromium
   * 129+ and silently did nothing everywhere else - the "archived courses slide
   * open smoothly, nothing else does" report.
   * ------------------------------------------------------------------ */

  const CLEAR_REDUCED =
    'height,overflow,marginTop,marginBottom,paddingTop,paddingBottom';

  function disclose(panel, open, onDone) {
    if (!panel) { if (onDone) onDone(); return; }
    G.killTweensOf(panel);

    if (REDUCED) {
      G.set(panel, { clearProps: CLEAR_REDUCED });
      if (!open) G.set(panel, { display: 'none' });
      else G.set(panel, { clearProps: 'display' });
      if (onDone) onDone();
      return;
    }

    /* Margins and padding collapse WITH the height. Animating height alone
       leaves the element's own spacing at full size, so a panel closing to
       zero height still occupies its margins and the layout below stops short
       of closing up - the jump this was meant to remove. */
    /* NO opacity. Fading the panel promotes it to its own compositor layer, and
       a layer holding a table paints its default surface for a frame before the
       content lands on it - a white flash INSIDE the card the instant it opens.
       The height clip already reveals the content, which is also all GitLab
       animates here; the fade bought nothing and cost that frame. */
    const BOX = {
      height: 0, overflow: 'hidden',
      marginTop: 0, marginBottom: 0, paddingTop: 0, paddingBottom: 0
    };
    const CLEAR = 'height,overflow,marginTop,marginBottom,paddingTop,paddingBottom';

    if (open) {
      /* Measure, collapse, then grow to the measured height. `from()` leaves
         the browser one frame in which to paint the expanded panel before
         GSAP's first render lands - measured as a single 265px frame ahead of
         the slide, which reads as a flash. Setting the collapsed box
         explicitly first means the very first painted frame is already
         closed. */
      G.set(panel, { display: '', clearProps: CLEAR });
      const target = panel.getBoundingClientRect().height;
      const style = getComputedStyle(panel);
      const box = {
        marginTop: style.marginTop, marginBottom: style.marginBottom,
        paddingTop: style.paddingTop, paddingBottom: style.paddingBottom,
      };
      G.set(panel, BOX);
      G.to(panel, Object.assign({ height: target }, box, {
        duration: dur(D.normal), ease: E.standard,
        clearProps: CLEAR,
        onComplete: function () { if (onDone) onDone(); }
      }));
    } else {
      G.to(panel, Object.assign({}, BOX, {
        duration: dur(D.normal), ease: E.exit,
        onComplete: function () {
          G.set(panel, { display: 'none', clearProps: CLEAR });
          if (onDone) onDone();
        }
      }));
    }
  }

  /* ------------------------------------------------------------------ *
   * Resize - the general fix for content that arrives late
   *
   * A container whose contents are replaced jumps from one height to the next
   * in a single frame, and everything below it jumps with it. That is the
   * "it compresses for a millisecond and comes back" report: the card renders
   * at its empty height, the data lands, and the page snaps.
   *
   * Measure, mutate, measure, then animate between the two. The DOM is already
   * final the whole time - only the box the user is looking at travels - so
   * nothing is delayed and no state is faked.
   *
   * `apply` must be synchronous. Anything async has already lost the old height
   * by the time it finishes, which is the whole quantity being preserved.
   * ------------------------------------------------------------------ */

  function resize(el, apply) {
    if (!el) { if (typeof apply === 'function') apply(); return; }
    const from = el.getBoundingClientRect().height;
    if (typeof apply === 'function') apply();
    resizeFrom(el, from);
  }

  /** The same, for callers that cannot wrap their mutation in a callback -
   *  they capture the height themselves and hand it back once the DOM settles. */
  function resizeFrom(el, from) {
    if (!el || from == null) return;
    // A newer result can arrive while the previous height transition is running.
    // Measure natural content height, rather than that transition's inline frame.
    G.killTweensOf(el, 'height,overflow');
    G.set(el, { clearProps: 'height,overflow' });
    const to = el.getBoundingClientRect().height;

    /* Under a few pixels the animation is less honest than the snap: it draws
       attention to a change nobody would have noticed. */
    if (REDUCED || Math.abs(to - from) < 6) return;

    G.fromTo(el,
      { height: from, overflow: 'hidden' },
      {
        height: to,
        duration: dur(D.normal),
        ease: E.standard,
        clearProps: 'height,overflow'
      });
  }

  /* There is deliberately no observer watching containers for growth.
     One was added here and removed the same day: it animated the height of any
     `.card-body` or `.table-responsive` that grew, which caught the late content
     it was meant for AND every legitimate resize the user had just asked for -
     expanding a tree row, changing the page size, closing a panel. Each of
     those became a lurch, and the chart inside the Issues panel jumped as its
     container eased shut underneath it.
     Late-arriving content is smoothed where the code KNOWS content is arriving
     (`resizeFrom`, called from the health dashboard), never by guessing from
     the outside. */

  /* ------------------------------------------------------------------ *
   * Change feedback - flash, pop, shake
   * ------------------------------------------------------------------ */

  /** Accept an element, a NodeList, or an array - so a caller with fifty
   *  changed cells hands them over once instead of calling fifty times. */
  function _targets(target) {
    if (!target) return [];
    if (target.nodeType === 1) return [target];
    return Array.prototype.filter.call(target, function (el) {
      return el && el.nodeType === 1;
    });
  }

  /** A theme token, read once and cached.
   *
   *  Every read is a `getComputedStyle` on the root, and the flash helpers used
   *  to do one (plus a probe element for `_fadeTo`) on EVERY call - so a
   *  fifty-cell refresh forced fifty synchronous style resolutions before a
   *  single frame had been drawn. Tokens only change when the theme changes,
   *  which the app announces. */
  const _TOKENS = new Map();

  function _token(name, fallback) {
    if (_TOKENS.has(name)) return _TOKENS.get(name);
    let value = '';
    try {
      value = getComputedStyle(document.documentElement)
        .getPropertyValue(name).trim();
    } catch (_) { /* fall through to the fallback */ }
    if (!value) value = fallback;
    _TOKENS.set(name, value);
    return value;
  }

  document.addEventListener('gp:theme-changed', function () { _TOKENS.clear(); });

  /** The same colour at alpha 0.
   *
   *  Fading a colour to `rgba(0,0,0,0)` interpolates towards BLACK on the way
   *  out, so a blue ring or a green wash turns muddy grey before it disappears.
   *  Ending on the colour's own transparent form keeps the hue constant and
   *  only the alpha moves. The browser normalises whatever the token holds
   *  (hex, hsl, oklch) into `rgb()/rgba()` for us.
   */
  const _RGB = new Map();

  /** The token's own red/green/blue, whatever notation it is written in. */
  function _rgbOf(colour) {
    if (_RGB.has(colour)) return _RGB.get(colour);
    let parts = null;
    try {
      if (typeof document !== 'undefined' && document.createElement) {
        // 1. Primary: 2D canvas normalises ANY valid CSS colour (color-mix, oklch, lab, color(srgb), hex, rgb) to 8-bit [0-255] RGB integers.
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        if (ctx) {
          ctx.fillStyle = colour;
          ctx.fillRect(0, 0, 1, 1);
          const data = ctx.getImageData(0, 0, 1, 1).data;
          if (data && data[3] > 0) {
            parts = [data[0], data[1], data[2]];
          }
        }
        // 2. Fallback: probe DOM element if canvas context is unavailable
        if (!parts && document.body) {
          const probe = document.createElement('span');
          probe.style.color = colour;
          document.body.appendChild(probe);
          const rgb = getComputedStyle(probe).color;
          probe.remove();
          const m = rgb.match(/-?[\d.]+/g);
          if (m && m.length >= 3) {
            if (rgb.startsWith('color(')) {
              // CSS Color 4 floats in 0..1 range
              parts = [
                Math.round(parseFloat(m[0]) * 255),
                Math.round(parseFloat(m[1]) * 255),
                Math.round(parseFloat(m[2]) * 255)
              ];
            } else {
              parts = [
                Math.round(parseFloat(m[0])),
                Math.round(parseFloat(m[1])),
                Math.round(parseFloat(m[2]))
              ];
            }
          }
        }
      }
    } catch (_) { /* leave null */ }
    _RGB.set(colour, parts);
    return parts;
  }

  function _withAlpha(colour, alpha) {
    const parts = _rgbOf(colour);
    if (!parts) return alpha ? colour : 'rgba(0,0,0,0)';
    return 'rgba(' + parts[0] + ',' + parts[1] + ',' + parts[2] + ',' + alpha + ')';
  }

  function _fadeTo(colour) {
    return _withAlpha(colour, 0);
  }

  /** "Here is the thing you asked for."
   *
   *  Used when the user is TAKEN somewhere - a jump-to-file click, an anchor in
   *  the URL, a row that just arrived over the live feed. Distinct from
   *  `flash`, which says "this number changed": this one draws a ring so the
   *  element is findable on a busy page, and deliberately does not move it - a
   *  table row that shifts while you are reading it is worse than no hint.
   *
   *  Replaced five separate implementations, each a class plus its own
   *  setTimeout to take the class off again (1400 / 1600 / 2000 ms), and three
   *  more written as `:target` rules that could not be triggered from JS at all.
   */
  function highlight(target) {
    const els = _targets(target);
    if (!els.length) return;

    /* The theme's selected colour - blue on the default theme, the accent under
       a Preferences theme - so the flash is the same colour as a selected row
       and the in-flight navigation tint (tokens.css), never a hard-coded hue. */
    const accent = _token('--gl-action-selected-border', _token('--primary', '#428fdc'));
    const faded = _fadeTo(accent);
    const dur = _seconds('--gl-anim-highlight', D.highlight || 1.8);
    const alpha = _number('--gl-highlight-opacity', 0.25);
    /* The token is a color-mix(); the canvas in _rgbOf resolves it to plain
       rgb so the tween has a colour it can interpolate. */
    const rowTint = _withAlpha(_token('--gl-table-row-selected-bg', _withAlpha(accent, alpha)), 1);

    /* A table row cannot be ringed at all. Every cell in these tables paints its
       own opaque background - tables.css puts the zebra and the hover on the
       <td>, never on the <tr>, so that containment and compositor layers cannot
       swallow them - which means a shadow on the row, inset or not, is drawn
       BEHIND the cells and the reader sees nothing. Measured on the project page
       while chasing "clicking a name scrolls but nothing lights up": the tween
       ran, the row's computed box-shadow went 0.675 -> 0 over 600ms, and not one
       pixel of it was visible.

       A row is marked by tinting its CELLS instead - the surface that is
       actually on top - so the whole row lights up and fades, which is what a
       reader means by "the row flashed". `clearProps` hands the zebra and the
       hover back when it is done. Everything else keeps the ring. */
    const rows = els.filter(function (el) { return el.tagName === 'TR'; });
    const boxed = els.filter(function (el) { return el.tagName !== 'TR'; });
    const cells = rows.reduce(function (acc, row) {
      return acc.concat(Array.prototype.slice.call(row.cells || []));
    }, []);

    G.killTweensOf(els.concat(cells));

    if (REDUCED) {
      if (cells.length) {
        G.set(cells, { backgroundColor: rowTint });
        G.to(cells, { backgroundColor: faded, duration: 0.8, ease: 'none', clearProps: 'backgroundColor' });
      } else if (boxed.length) {
        const inset = boxed.every(function (el) { return el.tagName === 'TD'; }) ? 'inset ' : '';
        G.set(boxed, { boxShadow: inset + '0 0 0 2px ' + accent });
        G.to(boxed, { boxShadow: inset + '0 0 0 2px ' + faded, duration: 0.8, ease: 'none', clearProps: 'boxShadow' });
      }
      return;
    }

    if (cells.length) {
      G.fromTo(cells,
        { backgroundColor: rowTint },
        {
          backgroundColor: faded,
          duration: dur, ease: E.standard,
          clearProps: 'backgroundColor'
        });
    }
    if (boxed.length) {
      /* A <td> on its own (a cell the live feed changed) still takes the ring on
         its inside edge - it has no children painting over it. */
      const inset = boxed.every(function (el) { return el.tagName === 'TD'; }) ? 'inset ' : '';
      G.fromTo(boxed,
        { boxShadow: inset + '0 0 0 2px ' + accent },
        {
          boxShadow: inset + '0 0 0 2px ' + faded,
          duration: dur, ease: E.standard,
          clearProps: 'boxShadow'
        });
    }
  }

  let _navigationTarget = null;
  let _navigationTargetId = '';
  let _navigationHref = '';
  function _revealNavigationParents(el) {
    const checks = [], regions = [];
    let expanded = false, alpineChanged = false;
    for (let parent = el.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === 'DETAILS') {
        if (!parent.open) { parent.open = true; expanded = true; }
        checks.push(() => parent.open);
      }
      if (/^glCollapse(?:\(|$)/.test(parent.getAttribute('x-data') || '') && window.Alpine?.$data) {
        const state = window.Alpine.$data(parent);
        if (state.open === false) { state.open = true; expanded = alpineChanged = true; }
        checks.push(() => state.open !== false);
      }
      if (parent.hasAttribute('x-collapse')) regions.push(parent);
      if (parent.matches('.gl-home-card.is-collapsed, .card.is-collapsed, .card.collapsed, [data-card-collapsible][data-collapsed="true"]')) {
        expanded = true;
        parent.classList.remove('is-collapsed', 'collapsed');
        parent.removeAttribute('data-collapsed');
        const body = parent.querySelector('.card-body, .gl-home-card-body');
        if (body) body.style.display = '';
        const toggle = parent.querySelector('[data-card-toggle], .gl-home-card-toggle, .card-collapse-toggle');
        if (toggle) toggle.setAttribute('aria-expanded', 'true');
      }
    }
    let ready = Promise.resolve();
    if ((alpineChanged || regions.length) && window.Alpine?.nextTick) {
      // x-collapse starts its height transition over two animation frames.
      // Wait for that transition, including its reduced-motion duration.
      ready = window.Alpine.nextTick()
        .then(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
        .then(() => Promise.allSettled(regions.flatMap(region =>
          region.getAnimations ? region.getAnimations()
            .filter(animation => animation.transitionProperty === 'height')
            .map(animation => animation.finished) : [])));
    }
    const obscured = (el.getClientRects && !el.getClientRects().length)
      || regions.some(region => region.clientHeight + 1 < region.scrollHeight);
    return { expanded, obscured, ready: ready.then(() => checks.every(check => check())) };
  }

  /** Follow a URL fragment or query parameter to its element and mark it. */
  function _highlightNavigationTarget() {
    const main = document.getElementById('main-content');
    if (main && (main.classList.contains('is-arriving') || (window.Alpine && main.hasAttribute('x-ignore')))) return;
    let rawId = '';
    const hash = window.location.hash;
    if (hash && hash.length > 1) {
      try {
        rawId = decodeURIComponent(hash.slice(1));
      } catch (_) {}
    }
    const fromHash = !!rawId;
    if (!rawId) {
      try {
        const params = new URLSearchParams(window.location.search);
        rawId = params.get('highlight') || params.get('row') || params.get('target') || '';
      } catch (_) {}
    }
    if (!rawId) { _navigationTarget = null; return; }

    let el = null;
    try {
      el = document.getElementById(rawId) || (fromHash ? document.getElementsByName(rawId)[0] : null);
    } catch (_) {}
    const fragmentAnchor = !!(fromHash && el);

    if (!el) {
      try {
        const cleanId = rawId.replace(/^(course|team|ticket|user|job)-/, '');
        el = document.querySelector(
          `#${CSS.escape(rawId)}, ` +
          `[data-course-id="${CSS.escape(rawId)}"], [data-course-id="${CSS.escape(cleanId)}"], ` +
          `[data-team-id="${CSS.escape(rawId)}"], [data-team-id="${CSS.escape(cleanId)}"], ` +
          `[data-ticket-id="${CSS.escape(rawId)}"], [data-ticket-id="${CSS.escape(cleanId)}"], ` +
          `[data-user-id="${CSS.escape(rawId)}"], [data-user-id="${CSS.escape(cleanId)}"], ` +
          `[data-job-id="${CSS.escape(rawId)}"], [data-job-id="${CSS.escape(cleanId)}"], ` +
          `[data-id="${CSS.escape(rawId)}"], [data-id="${CSS.escape(cleanId)}"]`
        );
      } catch (_) {}
    }

    if (!el) { _navigationTarget = null; return; }

    const { expanded, obscured, ready } = _revealNavigationParents(el);
    const href = window.location.href;
    if (!expanded && _navigationTarget === el && _navigationTargetId === rawId && _navigationHref === href) return;
    _navigationTarget = el;
    _navigationTargetId = rawId;
    _navigationHref = href;

    ready.then(function (open) {
      if (!open || !el.isConnected || window.location.href !== href || _navigationTarget !== el) return;
      // Existing fragment anchors are positioned by the scroll component.
      // A newly opened destination is positioned after its height settles.
      if (!fragmentAnchor || expanded || obscured) {
        try {
          if (typeof window.GP?.scrollWithinPageContent === 'function') {
            window.GP.scrollWithinPageContent(el, {
              block: fragmentAnchor ? 'start' : 'center', behavior: fragmentAnchor ? 'auto' : 'smooth'
            });
          } else {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        } catch (_) {}
      }
      highlight(el);
    });
  }

  /** Badge/count changed. Scale overshoot only - no colour, no glow ring: the
   *  badge already carries its own semantic colour and a second one read as an
   *  error state. */
  function pop(el) {
    if (!el || REDUCED) return;
    G.killTweensOf(el);
    /* One eased step up to its resting size, on GitLab's medium duration. It
       used to be 0.4s on back.out(1.7), whose overshoot took the badge 14% PAST
       full size and back - on a 20px pill that reads as a wobble, and it is
       also the frame budget where the number itself is unreadable. */
    G.fromTo(el,
      { scale: 0.9 },
      { scale: 1, duration: D.normal, ease: E.standard, clearProps: 'transform' });
  }

  /** Rejected input / failed action. */
  function shake(el) {
    if (!el || REDUCED) return;
    G.killTweensOf(el);
    /* One nudge back into place. The elastic version oscillated for 0.32s,
       which on a text input meant three frames where the caret was not where
       the user last saw it. */
    G.fromTo(el,
      { x: -6 },
      {
        x: 0, duration: dur(D.normal), ease: E.standard,
        clearProps: 'transform'
      });
  }

  /* ------------------------------------------------------------------ *
   * Continuous loops are NOT here, on purpose.
   *
   * Spinners and status pulses stay CSS `@keyframes`, for two
   * reasons that no amount of JS solves:
   *
   *   1. A CSS animation of `transform`/`opacity` runs on the compositor
   *      thread. A GSAP tween runs on the main thread, via rAF. A spinner is on
   *      screen precisely when the main thread is busy - so moving it to JS
   *      makes it stutter exactly when it is supposed to say "still working".
   *   2. Half of them live on `::after` (`.spinner::after`, `.btn.loading::after`,
   *      `.motion-status-pulse::after`). Pseudo-elements are not in the DOM, so
   *      no JS library can target them at all.
   *
   * What DID need fixing was the inconsistency: four near-identical rotation
   * keyframes (`spin`, `health-spin`, `gp-nav-spin` and a `spin-bg` that span no
   * one at all) with three different durations. There is now one `spin`
   * keyframe on one token, and the odd one out is renamed `gp-input-busy` for
   * what it actually does.
   * ------------------------------------------------------------------ */

  /* ------------------------------------------------------------------ *
   * Removal - dismissed cards, deleted rows
   * ------------------------------------------------------------------ */

  /** Fade the element out, then collapse the space it occupied so the list
   *  closes up instead of leaving a hole. */
  function dismiss(el, onDone) {
    if (!el) { if (onDone) onDone(); return; }
    const finish = function () {
      if (el.parentNode) el.remove();
      if (onDone) onDone();
    };
    if (REDUCED) { finish(); return; }

    G.killTweensOf(el);
    const isRow = el.tagName === 'TR';
    const tl = G.timeline({ onComplete: finish });
    tl.to(el, { opacity: 0, duration: D.normal, ease: E.exit });
    /* A <tr> cannot be collapsed by height - table layout ignores it. Fade
       only, and let the row removal do the reflow in one step. */
    if (!isRow) {
      tl.to(el, {
        height: 0, marginTop: 0, marginBottom: 0,
        paddingTop: 0, paddingBottom: 0, overflow: 'hidden',
        duration: D.normal, ease: E.standard
      });
    }
  }

  /* ------------------------------------------------------------------ *
   * Compliance rings
   *
   * Builds the SVG and draws the arc. Lives here rather than in its own module
   * because the draw IS the animation - splitting the two is what left the app
   * with a ring that animated on first paint and snapped on every htmx swap.
   * ------------------------------------------------------------------ */

  function ring(circle, circumference, pct) {
    if (!circle) return;
    const target = circumference - (pct / 100) * circumference;
    G.fromTo(circle,
      { strokeDashoffset: circumference },
      {
        strokeDashoffset: target,
        duration: dur(D.slow),
        ease: E.emphasized
      });
  }

  const SVG_NS = 'http://www.w3.org/2000/svg';

  function _buildRing(el) {
    const pct = Math.min(Math.max(
      parseFloat(el.getAttribute('data-compliance-ring') || '0'), 0), 100);
    const strokeWidth = parseFloat(el.getAttribute('data-ring-stroke') || '3.5');
    const size = parseFloat(el.getAttribute('data-ring-size') || '36');

    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;

    el.innerHTML = '';

    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'compliance-ring-svg');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    svg.setAttribute('viewBox', '0 0 ' + size + ' ' + size);
    svg.setAttribute('role', 'progressbar');
    svg.setAttribute('aria-valuenow', pct);
    svg.setAttribute('aria-valuemin', '0');
    svg.setAttribute('aria-valuemax', '100');

    const bg = document.createElementNS(SVG_NS, 'circle');
    bg.setAttribute('class', 'compliance-ring-bg');
    bg.setAttribute('cx', size / 2);
    bg.setAttribute('cy', size / 2);
    bg.setAttribute('r', radius);
    bg.style.setProperty('--ring-stroke-width', strokeWidth);

    const fill = document.createElementNS(SVG_NS, 'circle');
    fill.setAttribute('class', 'compliance-ring-fill');
    fill.setAttribute('cx', size / 2);
    fill.setAttribute('cy', size / 2);
    fill.setAttribute('r', radius);
    fill.style.setProperty('--ring-stroke-width', strokeWidth);
    fill.style.setProperty('stroke-dasharray', circumference);
    fill.style.setProperty('stroke-dashoffset', circumference);

    const root = document.documentElement;
    const greenTh = parseFloat(root.getAttribute('data-green-threshold') || '85');
    const yellowTh = parseFloat(root.getAttribute('data-yellow-threshold') || '50');
    let colour = 'var(--danger)';
    if (pct >= greenTh) colour = 'var(--success)';
    else if (pct >= yellowTh) colour = 'var(--warning)';
    fill.style.setProperty('--ring-color', colour);

    svg.appendChild(bg);
    svg.appendChild(fill);
    el.appendChild(svg);

    ring(fill, circumference, pct);
  }

  /* ------------------------------------------------------------------ *
   * Loading state -> content hand-off
   *
   * The block loader (spinner + label, `block_loading`) cross-fades into the
   * content that replaces it. A loader that is already hidden has nothing to
   * fade out, so the content simply appears.
   * ------------------------------------------------------------------ */

  function _loaderIsShown(loadingEl) {
    return !!loadingEl && !loadingEl.classList.contains('d-none');
  }

  function loadingHandoff(loadingEl, contentEl, onReveal) {
    if (!contentEl) {
      if (loadingEl) loadingEl.classList.add('d-none');
      return;
    }

    if (REDUCED || !_loaderIsShown(loadingEl)) {
      contentEl.classList.remove('d-none');
      if (loadingEl) loadingEl.classList.add('d-none');
      if (onReveal) onReveal();
      return;
    }

    /* Take the loader OUT OF FLOW before the content goes in, not after it
       has finished fading. Both used to occupy their full height for the whole
       fade: on the System page that put the card at 520px + 546px for ~100ms
       and then collapsed it - a visible bounce on every loader in the app,
       since this is the one hand-off they all use. Pinned over its own former
       box, the cross-fade looks the same and the height never changes. */
    /* Only when the two are in normal FLOW. A container that already stacks
       them - `.gl-chart-swap` puts both children in `grid-area: 1/1` - overlaps
       them by construction, so pinning adds nothing and getting the offset
       parent wrong throws the loader across the page: it moved the analytics
       checklist 240px right, which is a 0.062 CLS on a page that had none. */
    const _stackParent = loadingEl && loadingEl.parentElement;
    const _alreadyStacked = !!_stackParent
      && /grid/.test(getComputedStyle(_stackParent).display)
      && getComputedStyle(loadingEl).gridArea !== 'auto';

    if (loadingEl && !loadingEl.classList.contains('d-none') && !_alreadyStacked) {
      const parent = loadingEl.offsetParent || loadingEl.parentElement;
      if (parent && getComputedStyle(parent).position === 'static') {
        parent.style.position = 'relative';
      }
      /* offsetTop/offsetLeft, not a rect difference: they are already measured
         from the offset parent, which is the box `position: absolute` resolves
         against. Subtracting bounding rects gets the same answer only when that
         parent has no border and is not itself transformed - on the analytics
         chart swap it did not, and pinning the loader threw it 240px to the
         right, turning a 0.000 CLS page into 0.062. */
      G.set(loadingEl, {
        position: 'absolute',
        top: loadingEl.offsetTop,
        left: loadingEl.offsetLeft,
        width: loadingEl.offsetWidth,
        height: loadingEl.offsetHeight,
      });
      loadingEl.style.pointerEvents = 'none';
      contentEl.classList.remove('d-none');
      G.to(loadingEl, {
        opacity: 0,
        duration: D.fast,
        ease: E.exit,
        onComplete: function () {
          loadingEl.classList.add('d-none');
          loadingEl.style.pointerEvents = '';
          G.set(loadingEl, {
            clearProps: 'opacity,position,top,left,width,height',
          });
        }
      });
    } else {
      contentEl.classList.remove('d-none');
      /* Stacked: the loader can fade where it stands, it costs no height. */
      if (loadingEl && !loadingEl.classList.contains('d-none')) {
        loadingEl.style.pointerEvents = 'none';
        G.to(loadingEl, {
          opacity: 0,
          duration: D.fast,
          ease: E.exit,
          onComplete: function () {
            loadingEl.classList.add('d-none');
            loadingEl.style.pointerEvents = '';
            G.set(loadingEl, { clearProps: 'opacity' });
          }
        });
      }
    }

    // Canvas charts must measure their visible container before animating.
    if (onReveal) onReveal();
    G.fromTo(contentEl, { opacity: 0 },
      { opacity: 1, duration: D.normal, ease: E.standard, clearProps: 'opacity' });
  }

  /* ------------------------------------------------------------------ *
   * Mount / unmount
   *
   * Declarative hooks so a template can ask for motion without page JS.
   * `mount` is idempotent and runs on DCL, on every htmx swap, and on SPA
   * navigation; `unmount` kills what a departing subtree started.
   * ------------------------------------------------------------------ */

  const MOUNT_FLAG = 'data-gp-motion';

  /* Native <details> snaps. `card(collapsible=true)` glides, because it animates
     its height through Alpine. Same component, two behaviours - the "archived
     courses slide open, nothing else does" report.
     A CSS-only fix existed here before (`interpolate-size` + `::details-content`)
     but needed Chromium 129+ and did nothing at all in Firefox or Safari. This
     handler works everywhere: the browser owns `open`, we own the height of the
     panel after the <summary>, and the close is deferred until the panel has
     actually collapsed - otherwise `open` flips first and the content vanishes
     before it can animate. */
  function _bindDetails() {
    document.addEventListener('click', function (evt) {
      if (evt.defaultPrevented) return;
      const summary = evt.target.closest && evt.target.closest('summary');
      if (!summary) return;
      const control = evt.target.closest('a,button,input,select,textarea,label,[role="button"],[role="link"]');
      if (control && control !== summary && summary.contains(control)) return;
      const details = summary.parentElement;
      if (!details || details.tagName !== 'DETAILS') return;

      const panel = summary.nextElementSibling;
      if (!panel) return;

      if (details.open) {
        evt.preventDefault();
        disclose(panel, false, function () { details.open = false; });
      } else {
        /* Open it ourselves and collapse it in the SAME tick. Letting the
           browser toggle `open` and waiting a frame to measure meant the panel
           was painted at its full height first and only then snapped to zero to
           start sliding - measured at two frames of 265px, then 0, then the
           slide. That flash-then-slide is the jerk; GSAP's `from` applies its
           start values immediately, so opening synchronously never paints the
           expanded state at all. */
        evt.preventDefault();
        details.open = true;
        disclose(panel, true);
      }
    });
  }

  function mount(root) {
    const scope = root && root.nodeType === 1 ? root : document;

    const each = function (selector, fn) {
      let nodes;
      try {
        nodes = scope.querySelectorAll(selector);
      } catch (_) {
        return;
      }
      nodes.forEach(fn);
      if (scope.nodeType === 1 && scope.matches && scope.matches(selector)) fn(scope);
    };

    /* The claim attribute matters here: rebuilding a ring would restart its
       draw on every unrelated htmx swap on the page. */
    each('[data-compliance-ring]', function (el) {
      if (el.hasAttribute(MOUNT_FLAG)) return;
      el.setAttribute(MOUNT_FLAG, '1');
      _buildRing(el);
    });
  }

  /* There is deliberately no `unmount`. Every tween this module starts is
     finite and releases its target on completion, so a swapped-away subtree is
     collectable without help. The one thing that WOULD have leaked - an
     infinite repeat holding a removed node alive - is not here at all, because
     continuous loops stayed in CSS (see the note above). */

  /* ------------------------------------------------------------------ *
   * Public surface
   * ------------------------------------------------------------------ */

  /* Pending work grows one continuous fill; only the last release completes it.
     New work during completion keeps the visible width and cancels the fade. */
  function topProgress(bar, inner) {
    let fadeFrame = null;
    function cancelFade() {
      if (fadeFrame !== null) cancelAnimationFrame(fadeFrame);
      fadeFrame = null;
    }
    function reset() {
      cancelFade();
      G.killTweensOf([bar, inner]);
      G.set(bar, { clearProps: 'opacity' });
      G.set(inner, { clearProps: 'width' });
      bar.classList.remove('is-finishing');
    }
    function move(finishing) {
      const from = inner.getBoundingClientRect().width / bar.getBoundingClientRect().width;
      cancelFade();
      G.killTweensOf([bar, inner]);
      bar.classList.toggle('is-finishing', finishing);
      G.set(bar, { opacity: 1 });
      G.to(inner, {
        width: Math.max(from, finishing ? 1 : 0.9) * 100 + '%',
        duration: dur(finishing ? D.normal * (1 - from) : _seconds('--gl-anim-loop', D.progress)),
        ease: E.standard,
        onComplete: function () {
          if (!finishing) return;
          // Paint the complete fill before fading, including reduced
          // motion or the synchronous fallback when GSAP is unavailable.
          fadeFrame = requestAnimationFrame(function () {
            fadeFrame = requestAnimationFrame(function () {
              fadeFrame = null;
              G.to(bar, { opacity: 0, duration: dur(D.fast), ease: E.standard, onComplete: reset });
            });
          });
        }
      });
    }
    return {
      reset: reset,
      start: function () { move(false); },
      finish: function () { move(true); }
    };
  }

  window.GP.motion = {
    available: !!gsap,
    reduced: function () { return REDUCED; },
    tokens: { D: D, E: E },
    dur: dur,
    settle: settle,

    overlayIn: overlayIn,
    overlayOut: overlayOut,
    searchPalette: searchPalette,
    tourHighlight: tourHighlight,
    tourScroll: tourScroll,
    tourStep: tourStep,
    tourPopover: tourPopover,
    popIn: popIn,
    popOut: popOut,
    edgeIn: edgeIn,
    edgeOut: edgeOut,
    toastIn: toastIn,
    toastOut: toastOut,
    toastReflow: toastReflow,
    toastCountdown: toastCountdown,
    toastPause: toastPause,
    toastResume: toastResume,
    toastAgain: toastAgain,
    panelIn: panelIn,
    coverPage: coverPage,
    uncoverPage: uncoverPage,
    sheetSettle: sheetSettle,
    sheetDismiss: sheetDismiss,
    inkTo: inkTo,
    disclose: disclose,
    resize: resize,
    resizeFrom: resizeFrom,
    highlight: highlight,
    pop: pop,
    shake: shake,
    dismiss: dismiss,
    ring: ring,
    loadingHandoff: loadingHandoff,
    topProgress: topProgress,
    mount: mount
  };

  /* The one helper other bundles call by name. */
  window.GP.revealAfterLoading = loadingHandoff;

  function _boot() {
    mount(document);
    _bindDetails();
    _highlightNavigationTarget();
    window.addEventListener('hashchange', _highlightNavigationTarget);
    window.addEventListener('gp:hashnavigate', _highlightNavigationTarget);
    window.addEventListener('gp:page-ready', _highlightNavigationTarget);
    document.addEventListener('alpine:initialized', _highlightNavigationTarget);
    window.addEventListener('popstate', _highlightNavigationTarget);
    document.body.addEventListener('htmx:afterSwap', function (evt) {
      const target = evt.detail && evt.detail.target;
      if (target && target.nodeType === 1) mount(target);
      _highlightNavigationTarget();
    });
    document.body.addEventListener('htmx:afterSettle', function () {
      _highlightNavigationTarget();
    });
  }

  /* core.bundle.js is deferred, so by the time this runs readyState is already
     'interactive' - testing for 'loading' would silently never fire. */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _boot);
  } else {
    _boot();
  }
})();
