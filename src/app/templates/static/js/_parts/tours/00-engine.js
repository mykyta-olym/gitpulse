/* ------------------------------------------------------------------
 *  The guided-tour engine (js/tours.js, with the tours in 20-50).
 *
 *  Wraps the Driver.js library (vendor/driver.js/) with app conventions:
 *    * Role-aware (student / teacher / admin)
 *    * Multi-language (English + Slovak via window.GP.t)
 *    * Per-page automatic detection from `location.pathname`
 *    * Persistence of "completed" / "skipped" state in localStorage
 *    * Graceful handling of missing target elements
 *    * Smooth scroll, animated stage, custom theming via CSS vars
 *    * First-visit auto-prompt with subtle non-blocking toast
 *    * Public API: GP.tour.{run, runIfEligible, list, reset, isAvailable}
 *
 *  Tour content lives in the modules after 10-render.js and registers via
 *  `GP.tour.register(slug, definition)`.  Definitions are NOT pre-localized
 *  - each step provides `title_en`, `title_sk`, `body_en`, `body_sk` and the
 *  engine picks the active locale at runtime.  This keeps a single source of
 *  truth and means the user can switch language mid-tour.
 *
 *  Step shape:
 *    {
 *      element:   '#selector' | () => HTMLElement | null,    // optional -> centered popover
 *      side:      'top'|'right'|'bottom'|'left'|'over',
 *      align:     'start'|'center'|'end',
 *      title_en:  string,
 *      title_sk:  string,
 *      body_en:   string  (HTML allowed; simple <strong>/<kbd>/<em>),
 *      body_sk:   string,
 *      onBefore:  (ctx) => void,    // e.g. open a modal/menu before highlighting
 *      onAfter:   (ctx) => void,    // e.g. close it after step
 *      requires:  () => boolean,    // skip step if returns false
 *      role:      'student'|'teacher'|'admin'|undefined,  // restrict step to a role
 *    }
 *
 *  Tour shape:
 *    {
 *      slug:       string,
 *      title_en:   string,
 *      title_sk:   string,
 *      pages:      [string, ...],     // pageSlugs where this tour offers itself
 *      roles:      ['student', 'teacher', 'admin'],
 *      autoPrompt: boolean,         // offer on first visit
 *      steps:      [step, ...],
 *    }
 * ------------------------------------------------------------------ */
;(function() {
  'use strict';
  // v2 (2026-05-09): per-stage fingerprint became authoritative for the
  // tour-completed signal. Bumping the prefix from v1 -> v2 cleanly clears
  // any stale bare `<slug>@<role>:completed` keys that v1 wrote on every
  // tour finish - under v1 those bare keys permanently suppressed the
  // welcome card on multi-stage pages (e.g. /dashboard/support) the
  // moment the first stage was completed. Under v2 the bare key is only
  // written on EXPLICIT user dismissal of the welcome card itself.
  const STORAGE_PREFIX = 'gp_tour_v2:';
  const COMPLETED_SUFFIX = ':completed';
  const SKIPPED_SUFFIX = ':skipped';
  const PROMPTED_SUFFIX = ':prompted';

  /** Build a role-scoped storage key so the same slug can be re-prompted
   *  if the user's role changes (e.g. student -> teacher mid-semester). */
  const scopedKey = (slug, suffix, role) => `${slug}@${role || getRole()}${suffix}`;

  /** Stage fingerprint - cheap 32-bit hash of the compiled step element
   *  selectors. Stable across reloads, changes when the available step set
   *  changes (e.g. /dashboard/support stages: course-picker -> category ->
   *  form). Used to scope COMPLETED / SKIPPED / PROMPTED keys per-stage so
   *  the welcome card re-appears on each new sub-page even though the slug
   *  is the same. Returns string like "fp=12345678". */
  const stageFingerprint = (steps) => {
    const sig = (steps || []).map((s) => s.element || s.title_en || '').join('|');
    let h = 0;
    for (let i = 0; i < sig.length; i++) {
      h = ((h << 5) - h + sig.charCodeAt(i)) | 0;
    }
    return 'fp=' + (h >>> 0);
  };

  /** Active locale from <html data-locale="..."> with fallback to 'en'. */
  const getLocale = () => (document.documentElement.getAttribute('data-locale') || 'en').toLowerCase().startsWith('sk') ? 'sk' : 'en';

  /** Translate UI string via window.GP.t (the JSON i18n catalog) with English fallback.
   *  Single source of truth - Slovak translations live in src/app/i18n/catalogs/sk.json. */
  const tx = (en) => GP.t(en);

  /** Resolve role from `gp-base-config` JSON inserted in base.html. */
  const getRole = () => {
    try {
      const cfg = JSON.parse(document.getElementById('gp-base-config')?.textContent || '{}');
      if (cfg.isAdmin) return 'admin';
      if (cfg.isTeacher) return 'teacher';
      if (cfg.isStudent) return 'student';
      return cfg.userRole || 'student';
    } catch {
      return 'student';
    }
  };

  /** Map `location.pathname` -> page slug used to look up tours. */
  const getPageSlug = () => {
    const p = location.pathname;
    if (p === '/dashboard' || p === '/dashboard/' || p === '/') return 'dashboard';
    if (/^\/dashboard\/courses\/[^/]+\/settings\/?$/.test(p)) return 'course_settings';
    if (/^\/dashboard\/courses\/[^/]+\/roster\/?$/.test(p)) return 'course_roster';
    if (/^\/dashboard\/courses\/[^/]+\/teachers\/?$/.test(p)) return 'course_teachers';
    if (/^\/dashboard\/courses\/[^/]+\/assistant\/?$/.test(p)) return 'course_assistant';
    if (/^\/dashboard\/courses\/[^/]+\/analytics\/?$/.test(p)) return 'course_analytics';
    if (/^\/dashboard\/courses\/[^/]+\/activity\/?$/.test(p)) return 'course_activity';
    // Activity Monitor is mounted under /projects (the route handler is course_activity_page).
    if (/^\/dashboard\/courses\/[^/]+\/projects\/?$/.test(p)) return 'course_activity';
    if (/^\/dashboard\/courses\/[^/]+\/?$/.test(p)) return 'course_detail';
    if (/^\/dashboard\/students\/[^/]+(?:\/team\/[^/]+)?\/?$/.test(p)) return 'student_detail';
    if (/^\/dashboard\/projects\/[^/]+\/?$/.test(p)) return 'project_detail';
    if (/^\/dashboard\/teams\/[^/]+\/students\/[^/]+\/?$/.test(p)) return 'student_detail';
    if (/^\/dashboard\/teams\/[^/]+\/projects\/[^/]+\/?$/.test(p)) return 'project_detail';
    if (/^\/dashboard\/teams\/[^/]+\/?$/.test(p)) return 'team_detail';
    if (/^\/dashboard\/admin\/users\/?$/.test(p)) return 'admin_users';
    if (/^\/dashboard\/admin\/courses\/?$/.test(p)) return 'admin_courses';
    if (/^\/dashboard\/admin\/system\/?$/.test(p)) return 'admin_system';
    if (/^\/dashboard\/admin\/events\/?$/.test(p)) return 'admin_events';
    if (/^\/dashboard\/support\/?$/.test(p)) return 'support_form';
    if (/^\/dashboard\/support\/tickets\/?$/.test(p)) return 'support_tickets';
    if (/^\/dashboard\/support\/tickets\/[^/]+\/?$/.test(p)) return 'support_ticket_detail';
    if (/^\/dashboard\/preferences\/?$/.test(p)) return 'preferences';
    return '';
  };

  /** localStorage helpers (tolerant of disabled storage). */
  const lsGet = (key) => {
    try { return localStorage.getItem(STORAGE_PREFIX + key); } catch { return null; }
  };
  const lsSet = (key, value) => {
    try { localStorage.setItem(STORAGE_PREFIX + key, value); } catch { /* noop */ }
  };
  const lsDel = (key) => {
    try { localStorage.removeItem(STORAGE_PREFIX + key); } catch { /* noop */ }
  };

  // -- Server-side tour persistence (cross-device sync) ------------------

  // Per-session dedup: keys already POSTed this session are skipped so a
  // double lsSet call (e.g. stage + global dismiss) never fires twice.
  const _syncedKeys = new Set();

  // sessionStorage flag so seedFromServer only fires once per browser tab.
  const _SEED_SESSION_KEY = '_gp_tour_seeded';

  /**
   * Fire-and-forget: persist `key` (WITHOUT the STORAGE_PREFIX) to the
   * server so the user's completion/dismiss state survives across devices.
   *
   * Security: X-CSRF-Token is attached so the endpoint's CSRFCheck passes.
   * The token is placed on window.GP.csrfToken by core.js at init time;
   * fallback reads the <meta name="csrf-token"> directly.
   */
  const syncToServer = (key) => {
    if (_syncedKeys.has(key)) return;
    _syncedKeys.add(key);
    try {
      const csrf = window.GP?.csrfToken
        || document.querySelector('meta[name="csrf-token"]')?.content
        || '';
      fetch('/dashboard/api/tour/seen', {
        method: 'POST',
        credentials: 'same-origin',
        keepalive: true,
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
        body: JSON.stringify({ key }),
      }).then((response) => {
        if (!response.ok) _syncedKeys.delete(key);
      }).catch(() => {
        _syncedKeys.delete(key);
      });
    } catch {
      _syncedKeys.delete(key);
    }
  };

  /**
   * On first tab load, pull the list of already-seen keys from the server
   * and seed them into localStorage so tours dismissed on another device
   * are not re-shown here.  Guarded by sessionStorage so subsequent HTMX
   * navigations (same tab) do not re-fire the GET.  Any key not already in
   * localStorage is written as '1' - presence gates future prompts, not the
   * original timestamp.
   *
   * If any new keys are seeded and the welcome card is already visible for
   * one of those tours, dismiss it immediately (handles the rare race where
   * autoPrompt fires before the seed resolves on a slow connection).
   */
  // Module-level promise so autoPromptIfFirstVisit can await the seed.
  // Without this, the welcome card may appear on a new device before the
  // cross-device completed/skipped keys finish loading (user reported:
  // "completed tour on PC, opened on phone, welcome card appears again").
  let _seedPromise = null;
  const seedFromServer = () => {
    try {
      if (sessionStorage.getItem(_SEED_SESSION_KEY)) {
        _seedPromise = Promise.resolve();
        return _seedPromise;
      }
    } catch { /* noop - sessionStorage disabled */ }
    _seedPromise = (async () => {
      try {
        const r = await fetch('/dashboard/api/tour/seen', { credentials: 'same-origin' });
        const data = r.ok ? await r.json() : null;
        try { sessionStorage.setItem(_SEED_SESSION_KEY, '1'); } catch { /* noop */ }
        if (!Array.isArray(data?.keys) || !data.keys.length) return;
        let anyNew = false;
        for (const key of data.keys) {
          try {
            if (!localStorage.getItem(STORAGE_PREFIX + key)) {
              localStorage.setItem(STORAGE_PREFIX + key, '1');
              anyNew = true;
            }
          } catch { /* noop */ }
        }
        // If the welcome card is already on screen (rare race where seed
        // resolved after autoPrompt despite the await below), dismiss it.
        if (anyNew) {
          try { dismissWelcomeCard(); } catch { /* noop */ }
        }
      } catch {
        try { sessionStorage.setItem(_SEED_SESSION_KEY, '1'); } catch { /* noop */ }
      }
    })();
    return _seedPromise;
  };
  seedFromServer();

  /** Tour registry. */
  const tours = new Map();
  const sharedStepGroups = new Map();

  /** Mobile-aware sidebar opener. The app's sidebar is off-canvas on
   *  viewports ≤ 768px (see sidebar.js: `mobile-open` class on
   *  `#appSidebar`). When a tour step targets an element that lives
   *  inside the sidebar we must open the drawer first, otherwise the
   *  highlight cut-out lands on a 0×0 hidden node and the popover
   *  appears with no visible target. We track which elements caused
   *  the open so the close in `onDeselected` only fires when this step
   *  was the one to open it (avoids closing a sidebar the user opened
   *  manually before launching the tour). */
  // Form-factor detection. We treat anything ≤ 768px as the mobile
  // bottom-sheet form factor. Tablets in landscape (≥ 769px) keep
  // the desktop corner popover but with reduced height (handled
  // entirely in CSS). The CSS bottom-sheet breakpoint is aligned
  // with this JS check (see tour.css `@media (max-width: 768px)`).
  const _isMobile = () => window.innerWidth <= 768;
  // Landscape phones use compact cards even when wider than the sidebar's
  // mobile breakpoint. Card placement still follows the visible target.
  const _isLandscapePhone = () =>
    window.innerHeight <= 480 && window.innerWidth > window.innerHeight;
  const _isInsideSidebar = (el) => {
    if (!el || !(el instanceof Element)) return false;
    return !!el.closest?.('#appSidebar, .gl-sidebar, [data-sidebar]');
  };
  /** Heuristic: does this step's `element` selector target the sidebar?
   *  Used for the defensive rescue path in `onHighlightStarted` when
   *  Driver.js falls back to its dummy element because the sidebar
   *  was off-canvas at element() time. */
  const _selectorTargetsSidebar = (sel) => {
    if (typeof sel !== 'string') return false;
    return /(^|[\s,])(#appSidebar|\.gl-sidebar|\[data-sidebar)/.test(sel);
  };
  const _mobileSidebarOpenedByTour = { v: false };
  const _openMobileSidebarForTour = () => {
    const sidebar = document.getElementById('appSidebar');
    if (!sidebar) return;
    if (sidebar.classList.contains('mobile-open')) return; // user already opened it
    window.GP?.sidebar?.open();
    sidebar.classList.add('mobile-open');
    document.body.classList.add('sidebar-mobile-open');
    _mobileSidebarOpenedByTour.v = true;
  };
  const _closeMobileSidebarFromTour = () => {
    if (!_mobileSidebarOpenedByTour.v) return;
    window.GP?.sidebar?.close();
    document.getElementById('appSidebar')?.classList.remove('mobile-open');
    document.getElementById('sidebarOverlay')?.classList.remove('visible');
    document.body.classList.remove('sidebar-mobile-open');
    _mobileSidebarOpenedByTour.v = false;
  };

  /** Resolve a step's element selector, accepting string or function.
   *  Returns null for loading, hidden, or disabled elements
   *  so the engine can fall back to a centred popover instead of pointing
   *  at a loading state or a feature-flagged-off button. */
  const isLoadingOrHidden = (el) => {
    if (!el || !(el instanceof Element)) return true;
    if (el.closest?.('[aria-busy="true"]')) return true;
    if (el.hasAttribute?.('disabled') || el.getAttribute?.('aria-disabled') === 'true') return true;
    if (el.hidden) return true;
    const cs = window.getComputedStyle?.(el);
    if (cs && (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05)) return true;
    const r = el.getBoundingClientRect?.();
    if (!r || r.width < 2 || r.height < 2) return true;
    return false;
  };
  /** True when the element is hidden ONLY because it (or an ancestor) is a
   *  collapsed <details>. Such elements are still valid tour targets - we open
   *  the section when the tour actually navigates to the step, not during the
   *  eligibility scan (which would auto-expand the page on load). */
  const insideClosedDetails = (el) => {
    if (!el || !(el instanceof Element)) return false;
    let p = el.tagName === 'DETAILS' ? el : el.parentElement;
    while (p && p !== document.body) {
      if (p.tagName === 'DETAILS' && !p.open) return true;
      p = p.parentElement;
    }
    return false;
  };
  /** Open any <details> the target lives inside (and the target itself when it
   *  IS a <details>) so a tour step can highlight content the user left
   *  collapsed - the changed-file tree, an MR diff section, an inline code
   *  context. Called only when DRIVING a step (element()/onHighlightStarted),
   *  never during eligibility checks, so loading a page never auto-expands it. */
  const openAncestorDetails = (el) => {
    if (!el || !(el instanceof Element)) return;
    let p = el.tagName === 'DETAILS' ? el : el.parentElement;
    while (p && p !== document.body) {
      if (p.tagName === 'DETAILS' && !p.open) {
        try { p.open = true; } catch { /* noop */ }
      }
      p = p.parentElement;
    }
  };
  const resolveElement = (step) => {
    const sel = step.element;
    if (!sel) return null;
    let el = null;
    if (typeof sel === 'function') {
      try { el = sel(); } catch { el = null; }
    } else {
      try { el = document.querySelector(sel); } catch { el = null; }
    }
    if (!el || !(el instanceof Element)) return null;
    // Loading / disabled / feature-flagged-off elements are never valid targets.
    if (el.closest?.('[aria-busy="true"]')) return null;
    if (el.hasAttribute?.('disabled') || el.getAttribute?.('aria-disabled') === 'true' || el.hidden) return null;
    // Keep an element that is hidden ONLY because it sits in a collapsed
    // <details> - the driver opens that section when it navigates to the step.
    // Otherwise apply the normal visibility test.
    if (!insideClosedDetails(el) && isLoadingOrHidden(el)) return null;
    // Chart canvases have flaky bounding boxes - Chart.js delays its
    // first paint by an animation frame, so the rect is sometimes
    // measured before the canvas reaches its final width/height.
    // Always prefer the .chart-canvas-wrap parent (fixed pixel height,
    // 100% width) for a clean rectangular highlight.
    if (el && el.tagName === 'CANVAS') {
      const wrap = el.closest('.chart-canvas-wrap, .issues-chart-canvas-wrap');
      if (wrap) return wrap;
    }
    return el;
  };

  /** Wait until the page is fully loaded - dynamically.
   *
   *  Resolves only when ALL of the following are true for a sustained
   *  quiet window (default 600 ms with no DOM mutations):
   *    - no `[aria-busy="true"]` element
   *    - no in-flight `fetch` / `XMLHttpRequest` started since page load
   *    - no in-flight HTMX request (htmx:beforeRequest open)
   *    - `document.readyState === 'complete'`
   *
   *  A hard cap (default 20 s) prevents indefinite waits on a stuck
   *  page; the tour starts anyway after it elapses. */
  let _inFlightRequests = 0;
  if (!window.__tourReqHook) {
    window.__tourReqHook = true;
    const _origFetch = window.fetch?.bind(window);
    if (_origFetch) {
      window.fetch = function (...args) {
        // Exclude the tour-sync API calls and all background-monitor
        // endpoints from the page-loading signal.  These requests run
        // continuously in the background (health polling, badge refresh,
        // sync-watchdog, session check) and must never delay
        // waitForStableDom or prevent the auto-prompt idle check.
        const _url = typeof args[0] === 'string' ? args[0] : (args[0]?.url || '');
        if (
          _url.includes('/api/tour/') ||
          _url.includes('/health') ||               // /health + /health/gitlab
          _url.includes('/dashboard/sidebar-badges') ||
          _url.includes('/api/v1/sync/active') ||
          _url.includes('/dashboard/session-check')
        ) return _origFetch(...args);
        _inFlightRequests++;
        return _origFetch(...args).finally(() => { _inFlightRequests = Math.max(0, _inFlightRequests - 1); });
      };
    }
    const _OrigXHR = window.XMLHttpRequest;
    if (_OrigXHR) {
      const open = _OrigXHR.prototype.open;
      const send = _OrigXHR.prototype.send;
      _OrigXHR.prototype.open = function (...a) { this.__tourTracked = true; return open.apply(this, a); };
      _OrigXHR.prototype.send = function (...a) {
        if (this.__tourTracked) {
          _inFlightRequests++;
          const dec = () => { _inFlightRequests = Math.max(0, _inFlightRequests - 1); };
          this.addEventListener('loadend', dec);
        }
        return send.apply(this, a);
      };
    }
    document.addEventListener('htmx:beforeRequest', () => { _inFlightRequests++; });
    document.addEventListener('htmx:afterRequest', () => { _inFlightRequests = Math.max(0, _inFlightRequests - 1); });
    document.addEventListener('htmx:sendError', () => { _inFlightRequests = Math.max(0, _inFlightRequests - 1); });
    document.addEventListener('htmx:responseError', () => { _inFlightRequests = Math.max(0, _inFlightRequests - 1); });
    document.addEventListener('htmx:timeout', () => { _inFlightRequests = Math.max(0, _inFlightRequests - 1); });
  }

  const isPageLoading = () => {
    if (document.readyState !== 'complete') return true;
    if (_inFlightRequests > 0) return true;
    // Every loading state in the app (block loader, busy table) carries
    // aria-busy, so that one check is the whole test.
    return !!document.querySelector('[aria-busy="true"]');
  };

  const waitForStableDom = (cap = 20000, quietMs = 250) => new Promise((resolve) => {
    const start = performance.now();
    let lastMutation = performance.now();
    const mo = new MutationObserver(() => { lastMutation = performance.now(); });
    mo.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['aria-busy', 'hidden', 'class'] });

    const finish = () => { try { mo.disconnect(); } catch (_) {} resolve(); };
    const tick = () => {
      const now = performance.now();
      if (now - start > cap) return finish();
      if (!isPageLoading() && (now - lastMutation) > quietMs) return finish();
      // Re-check on next animation frame; cheap and naturally throttled.
      requestAnimationFrame(tick);
    };
    // Kick off once initial paint settles.
    requestAnimationFrame(tick);
  });

  /** Filter steps for the current role and `requires`. Steps whose
   *  `element` selector resolves to nothing at runtime are SKIPPED
   *  entirely (e.g. optional AI-analysis cards when the course has them
   *  disabled, or admin-only buttons hidden from teachers). Steps with no `element`
   *  at all (welcome / intro / closing) always pass through. */
  const compileSteps = (tour, role) => {
    const out = [];
    // Shared steps (e.g. the appearance/account menu) are OPT-IN: only tours
    // that set ``includeSharedSteps: true`` get them, so the appearance step no
    // longer tags onto every page's tour - only the dashboard's.
    const sharedSteps = tour.includeSharedSteps === true
      ? Array.from(sharedStepGroups.values()).flat()
      : [];
    for (const step of [...(tour.steps || []), ...sharedSteps]) {
      if (step.role && step.role !== role) continue;
      if (step.requires) {
        try { if (!step.requires()) continue; } catch { continue; }
      }
      // If a step targets a specific element, drop it when the target is
      // not present in the DOM (disabled feature, role-gated UI, etc.).
      // Steps without an `element` (welcome / outro / power-tip) keep.
      if (step.element && !step.keepIfMissing) {
        if (!resolveElement(step)) continue;
      }
      out.push(step);
    }
    return out;
  };

  const scrollTourTarget = (el, ctx, popover) => {
    if (el && el.id !== 'driver-dummy-element') {
      try {
        // Walk up to the nearest TRULY scrollable ancestor by computed
        // style. Stop BEFORE document.documentElement / body - we never
        // touch the window scroller.
        const findInnerScroller = (start) => {
          let p = start && start.parentElement;
          while (p && p !== document.documentElement && p !== document.body) {
            const cs = getComputedStyle(p);
            const oy = cs.overflowY;
            if ((oy === 'auto' || oy === 'scroll') && p.scrollHeight - p.clientHeight > 40) {
              return p;
            }
            p = p.parentElement;
          }
          return null;
        };
        const vh = window.innerHeight || document.documentElement.clientHeight;
        const isMobile = _isMobile() || _isLandscapePhone();
        const scrollIntoViewRecursive = (target) => {
          const scroller = findInnerScroller(target);
          if (!scroller || typeof scroller.scrollTo !== 'function') return;

          const sr = scroller.getBoundingClientRect();
          const rr = target.getBoundingClientRect();
          // Reserve only the measured card height on a compact screen.
          const padTop = sr.top + 16;
          const padBottom = isMobile
            ? vh - popover.getBoundingClientRect().height - 16
            : (sr.bottom - 16);
          const bandHeight = Math.max(0, padBottom - padTop);
          // Target viewport-y for the element TOP:
          let targetTopY;
          if (rr.height <= bandHeight - 8) {
            targetTopY = Math.round(padTop + (bandHeight - rr.height) / 2);
          } else {
            targetTopY = padTop;
          }
          // Required delta (positive = scroll DOWN, i.e. scrollTop
          // increases, so element moves UP in the viewport).
          const wantedDelta = rr.top - targetTopY;
          // Clamp to the scroller's achievable scroll range.
          const maxUp   = scroller.scrollTop;
          const maxDown = scroller.scrollHeight - scroller.clientHeight
                        - scroller.scrollTop;
          const delta = wantedDelta > 0
            ? Math.min(wantedDelta,  maxDown)
            : Math.max(wantedDelta, -maxUp);
          // Only scroll when the element is meaningfully out of
          // place (a 4 px wobble is invisible and not worth animating).
          if (Math.abs(delta) > 4) {
            const startTop = scroller.scrollTop;
            const targetTop = startTop + delta;
            ctx.scrollTargets.push({ scroller, top: targetTop });
            GP.motion.tourScroll(scroller, { scrollTop: targetTop });
          }
          // Propagate scroll up to the next ancestor!
          scrollIntoViewRecursive(scroller);
        };

        scrollIntoViewRecursive(el);
        // Notify Driver.js so the SVG cut-out tracks the new rect.
        try { window.dispatchEvent(new Event('scroll')); } catch { /* noop */ }
        // Horizontal scroll-into-view for tab bars / overflow-x:auto
        // containers (e.g. .tabs-nav on mobile where the last tab -
        // "Teachers" - sits offscreen-right). Smooth as well.
        try {
          let p = el.parentElement;
          while (p && p !== document.body) {
            const cs = getComputedStyle(p);
            const ox = cs.overflowX;
            if ((ox === 'auto' || ox === 'scroll') && p.scrollWidth > p.clientWidth + 1) {
              const rr2 = el.getBoundingClientRect();
              const pr  = p.getBoundingClientRect();
              if (rr2.right > pr.right - 16 || rr2.left < pr.left + 16) {
                const delta = (rr2.left - pr.left) - (pr.width - rr2.width) / 2;
                const targetLeft = Math.max(0, Math.min(p.scrollWidth - p.clientWidth, p.scrollLeft + delta));
                ctx.scrollTargets.push({ scroller: p, left: targetLeft });
                GP.motion.tourScroll(p, { scrollLeft: targetLeft });
              }
              break;
            }
            p = p.parentElement;
          }
        } catch { /* noop */ }
      } catch { /* ignore */ }
    }
  };

  /** Build a Driver.js step from one of our step descriptors. */
  const toDriverStep = (step, ctx, driverRef) => {
    const title = step['title_' + getLocale()] || step.title_en || '';
    const body = step['body_' + getLocale()] || step.body_en || '';
    // Resolve at runtime so HTMX swaps after step.onBefore are picked up.
    // Steps without an `element` (or with a missing target) become
    // centred modal-style popovers - see the onPopoverRender hook in run()
    // which forces the centred CSS class so positioning works regardless
    // of how Driver.js placed the popover internally.
    const driverStep = {
      onHighlightStarted: (el) => {
        ctx.previousTarget = driverRef.current?.getActiveElement();
        // Capture the visible position before Driver.js replaces this card.
        // Its next step can have a different height at the same bottom anchor.
        const previousPopover = document.querySelector('.driver-popover.gp-tour-popover');
        ctx.popoverRect = previousPopover?.getBoundingClientRect();
        ctx.scrollTargets?.forEach((target) => GP.motion.tourScroll(target.scroller));
        ctx.scrollTargets = [];
        try { step.onBefore?.(ctx); } catch (e) { console.warn('[tour] onBefore failed', e); }
        // Defensive: ensure any collapsed <details> around the target is open
        // (covers the re-drive / refresh path where element() ran while a
        // section was still closed).
        if (el && el.id !== 'driver-dummy-element') openAncestorDetails(el);
        // -- Defensive sidebar fallback --
        // If Driver.js fell back to the dummy element even though this step
        // targets a sidebar selector, the most common cause on mobile is
        // that the sidebar was off-canvas at element() time and the rect
        // collapsed. Open the drawer NOW and re-drive the same index so
        // the next pass measures the on-screen rect. The early return
        // guards against infinite recursion (we only attempt the rescue
        // once per step transition by checking for a stable on-screen rect).
        if (
          _isMobile()
          && el && el.id === 'driver-dummy-element'
          && step.element
          && _selectorTargetsSidebar(step.element)
        ) {
          try {
            _openMobileSidebarForTour();
            const drv = driverRef && driverRef.current;
            if (drv && typeof drv.getActiveIndex === 'function') {
              const idx = drv.getActiveIndex();
              requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                  try { drv.drive(idx); } catch { /* noop */ }
                });
              });
            }
          } catch { /* noop */ }
        }
      },
      onDeselected: (_el) => {
        try { step.onAfter?.(ctx); } catch (e) { console.warn('[tour] onAfter failed', e); }
        // NOTE: do NOT close the mobile sidebar here. Driver.js fires
        // onDeselected for the previous step AFTER our element() of the
        // NEW step has already opened the drawer for a sidebar-targeted
        // step (the call order is: G(step) -> element() -> xe() ->
        // prevStep.onDeselected -> newStep.onHighlightStarted). Closing
        // here would slam shut the sidebar we just opened. The close is
        // handled in `element()` of the next step (if it doesn't target
        // the sidebar) and unconditionally in `onDestroyed`.
      },
      popover: {
        title,
        description: body,
        side: step.side || 'bottom',
        align: step.align || 'start',
      },
    };
    if (step.element) {
      driverStep.element = () => {
        let raw = null;
        const sel = step.element;
        if (typeof sel === 'function') {
          try { raw = sel(); } catch { raw = null; }
        } else {
          try { raw = document.querySelector(sel); } catch { raw = null; }
        }
        if (_isMobile()) {
          if (_isInsideSidebar(raw)) {
            _openMobileSidebarForTour();
          } else if (_mobileSidebarOpenedByTour.v) {
            // Previous step opened the drawer; this one targets the
            // page body, so close it now (before Driver.js measures)
            // so the highlight isn't occluded.
            _closeMobileSidebarFromTour();
          }
        }
        const resolved = resolveElement(step);
        // Reveal a collapsed <details> the target lives in NOW (at navigation
        // time, synchronously before Driver.js measures the rect) so the
        // cut-out lands on the real element and not a 0x0 box.
        if (resolved) openAncestorDetails(resolved);
        return resolved || undefined;
      };
    } else {
      driverStep.element = () => {
        if (_isMobile()) _closeMobileSidebarFromTour();
        return undefined;
      };
    }
    // Stash original step on the descriptor so onPopoverRender can decide
    // whether to centre this popover.
    driverStep.__gpStep = step;
    return driverStep;
  };

  /** Public: register a tour definition. */
  const register = (definition) => {
    if (!definition?.slug) throw new Error('tour.register: slug required');
    tours.set(definition.slug, definition);
  };

  /** Register shell-level steps once and append them to every page tour. */
  const registerSharedSteps = (key, steps) => {
    if (!key || !Array.isArray(steps)) {
      throw new Error('tour.registerSharedSteps: key and steps required');
    }
    sharedStepGroups.set(key, steps);
  };

  /** Stage-aware completion check: a tour counts as completed when EITHER
   *  the bare slug+role key is set (explicit user dismissal) OR the
   *  per-stage fingerprinted `:completed:fp=...` key matches the current
   *  stage. This lets multi-stage pages (e.g. /dashboard/support) advertise
   *  the tour again on subsequent stages without losing the "already seen"
   *  signal for stages the user actually finished. */
  const isStageCompleted = (tour, role) => {
    if (lsGet(scopedKey(tour.slug, COMPLETED_SUFFIX, role))) return true;
    try {
      const compiled = compileSteps(tour, role);
      if (!compiled.length) return false;
      const fp = stageFingerprint(compiled);
      const exact = lsGet(scopedKey(tour.slug, COMPLETED_SUFFIX, role) + ':' + fp);
      if (exact) return true;
      // Persisted fingerprint completion also completes a single-stage tour.
      // Multi-stage tours must retain their independent stage prompts.
      if (tour.multiStage) return false;
      try {
        const prefix = STORAGE_PREFIX + scopedKey(tour.slug, COMPLETED_SUFFIX, role) + ':fp=';
        for (let i = 0; i < localStorage.length; i++) {
          const k = localStorage.key(i);
          if (k && k.indexOf(prefix) === 0) return true;
        }
      } catch { /* localStorage disabled - fall through */ }
      return false;
    } catch {
      return false;
    }
  };

  /** Public: list tours available on the current page for current role. */
  const list = () => {
    const page = getPageSlug();
    const role = getRole();
    const out = [];
    for (const tour of tours.values()) {
      if (tour.pages && !tour.pages.includes(page)) continue;
      if (tour.roles && !tour.roles.includes(role)) continue;
      out.push({
        slug: tour.slug,
        title: tour['title_' + getLocale()] || tour.title_en,
        completed: isStageCompleted(tour, role),
      });
    }
    return out;
  };

  /** Public: are any tours available right here right now? */
  const isAvailable = () => list().length > 0;

  /** Close any UI that would compete with the tour for clicks / focus.
   *  Called BEFORE we start a tour or render a welcome card, never on
   *  arbitrary DOM mutations (the previous MutationObserver-based
   *  approach destroyed the tour mid-render and broke positioning).
   *  Safe to call repeatedly; every step is wrapped in try/catch. */
  const closeCompetingOverlays = (reason) => {
    try {
      // 0. Dismiss visible toasts - but only on mobile where they visually
      //    overlap the bottom-sheet welcome card / tour popover.  On desktop
      //    and tablets the toast stack sits in a corner and does not compete
      //    with either the welcome card or the Driver.js overlay.
      if (_isMobile()) {
        window.GP.dismissAllToasts();
      }
      // 1. App-managed modals (`window.GP.closeAllModals` closes every
      //    `.modal-backdrop.active`).
      //    These genuinely cover the full viewport on all screen sizes.
      window.GP.closeAllModals();
      // 2. Mobile sidebar - only close on mobile (≤768px) where the sidebar
      //    slides over the content and would sit on top of the welcome card or
      //    tour popover.  On desktop/tablet the sidebar is always visible in
      //    the layout and does not cover the tour.  Also skip if *we* opened
      //    the sidebar for a tour step (`_mobileSidebarOpenedByTour.v = true`).
      if (_isMobile() && !_mobileSidebarOpenedByTour?.v) {
        const sb = document.getElementById('appSidebar');
        if (sb && sb.classList.contains('mobile-open')) {
          sb.classList.remove('mobile-open');
          document.body.classList.remove('sidebar-mobile-open');
          const ov = document.getElementById('sidebarOverlay');
          if (ov) ov.style.removeProperty('opacity');
        }
      }
      // 3. Native <details> / <dialog> popouts that opened from a click
      //    elsewhere - close only those that are NOT the tour target.
      //    We don't know the next step's selector here, so be cautious:
      //    only close header/menu dropdowns marked with a known class.
      document.querySelectorAll('details.gp-menu[open], details.dropdown[open], details.user-menu[open]').forEach((d) => {
        try { d.removeAttribute('open'); } catch { /* noop */ }
      });
      // 4. Tippy tooltips currently visible - Driver.js overlay covers
      //    them visually but they keep stealing pointer events.
      try {
        document.querySelectorAll('[data-tippy-root]').forEach((n) => {
          const inst = n._tippy;
          if (inst && typeof inst.hide === 'function') inst.hide();
        });
      } catch { /* noop */ }
    } catch { /* noop */ }
    if (GP.debug) console.debug('[tour] closed competing overlays:', reason);
  };

  /** Public: run a tour by slug. */
  const run = (slug) => {
    const tour = tours.get(slug);
    if (!tour) {
      console.warn('[tour] unknown tour:', slug);
      return false;
    }
    if (!window.driver?.js?.driver) {
      console.warn('[tour] driver.js not loaded');
      return false;
    }
    // Always dismiss any visible welcome card and lock auto-prompts for
    // this page load - a tour is starting, no need to pop a competing
    // welcome on top of the Driver.js overlay.
    dismissWelcomeCard();
    _welcomePromptedThisLoad = true;
    // Pre-emptively close anything that would float on top of the tour
    // overlay. Driver.js owns focus / scroll once it starts, so a stale
    // modal / drawer / open dropdown sitting in front of the highlighted
    // target produces visual chaos and hijacks clicks.
    closeCompetingOverlays('tour-start');
    const role = getRole();
    // Hard role guard: refuse to run a tour the current role is not in.
    if (tour.roles && !tour.roles.includes(role)) {
      console.info('[tour] role', role, 'not eligible for', slug);
      return false;
    }
    const steps = compileSteps(tour, role);
    if (steps.length === 0) {
      window.showToast(tx('No tour steps available on this page yet.'), 'info');
      return false;
    }

    const ctx = { role, locale: getLocale(), tour, slug };
    // Shared mutable reference so per-step callbacks (onHighlightStarted)
    // can call back into the driver instance for the rescue re-drive
    // path when Driver.js falls back to its dummy element.
    const driverRef = { current: null };
    const driverSteps = steps.map((s) => toDriverStep(s, ctx, driverRef));
    // Animate the first card once; subsequent steps move from its last position.
    let _entranceShown = false;
    // Until a real target renders, reveal its highlight in place rather than
    // morphing from Driver.js' zero-size, centred placeholder.
    let _highlightReady = false;
    // Highest step index the user actually saw. Driver.js'
    // `getActiveIndex()` returns -1/undefined inside `onDestroyed`
    // (state is already torn down by then), so relying on it caused
    // the very last \"Done\" click to be classified as \"skipped\"
    // instead of \"completed\" \u2014 the per-stage `:skipped` key is
    // fingerprint-scoped and dies as soon as the page DOM shifts
    // (e.g. lazy webhook config table renders), so the welcome card
    // popped back up on the next visit. Tracking max index ourselves
    // via onPopoverRender (and the per-step onHighlightStarted) keeps
    // a stable, reliable signal of \"how far did the user get\".
    let _maxIndex = -1;

    // -- Inner-scroll-container bridge ----------------------------
    // Driver.js v1.3.6 only listens to `window.scroll` to refresh the
    // SVG cut-out overlay. This app's layout has body{overflow:hidden}
    // and a single inner scroller `.gl-page-content` - when *that*
    // element scrolls, Driver.js never redraws and the overlay stays
    // pinned to the wrong viewport coordinates (cut-out drifts off the
    // highlighted element). Bridge inner scroll -> window scroll for
    // the duration of the tour and tear down on destroy.
    const scrollContainers = Array.from(
      document.querySelectorAll('.gl-page-content, [data-tour-scroll-root]')
    );
    let scrollRaf = 0;
    const bridgeScroll = () => {
      // Refresh the live destination; GP.motion keeps the visible transition
      // separate so this refresh cannot interrupt a step's highlight morph.
      if (scrollRaf) return;
      scrollRaf = requestAnimationFrame(() => {
        scrollRaf = 0;
        try { window.dispatchEvent(new Event('scroll')); } catch { /* noop */ }
      });
    };
    scrollContainers.forEach((c) => c.addEventListener('scroll', bridgeScroll, { passive: true }));
    // Catch every nested scroller too (table-responsive, tabs-nav, etc.)
    // so the SVG cut-out tracks the highlighted element when the user
    // scrolls a table sideways or a tab strip horizontally.
    document.addEventListener('scroll', bridgeScroll, { passive: true, capture: true });
    const detachScrollBridge = () => {
      scrollContainers.forEach((c) => c.removeEventListener('scroll', bridgeScroll));
      document.removeEventListener('scroll', bridgeScroll, { capture: true });
      if (scrollRaf) cancelAnimationFrame(scrollRaf);
    };

    let _leaving = false;
    const closeTour = () => {
      if (_leaving || !driverInstance.isActive()) return;
      _leaving = true;
      ctx.scrollTargets?.forEach((target) => GP.motion.tourScroll(target.scroller));
      driverInstance.setConfig({ ...driverInstance.getConfig(), allowKeyboardControl: false });
      const root = document.querySelector('.driver-popover.gp-tour-popover');
      const active = driverInstance.getActiveElement();
      const track = _isInsideSidebar(active) ? () => active.getBoundingClientRect() : undefined;
      if (_isMobile()) _closeMobileSidebarFromTour();
      if (root) {
        root.classList.add('gp-tour-popover--leaving');
        root.inert = true;
      }
      // Keep the overlay alive until the reverse reveal and card exit finish.
      let pending = 2;
      const done = () => {
        if (--pending === 0) {
          try { driverInstance.destroy(); } catch { /* noop */ }
        }
      };
      GP.motion.tourPopover(root, false, done);
      GP.motion.tourHighlight(document.querySelector('.driver-overlay'), true, null,
        { collapse: true, track: track, onComplete: done });
    };
    const escHandler = (e) => {
      if (e.key === 'Escape') closeTour();
    };

    const driverInstance = window.driver.js.driver({
      // GP.motion owns the highlight and popover transitions; Driver.js'
      // animation would recreate the popover halfway through that movement.
      animate: false,
      // IMPORTANT: keep this false. Driver.js' internal scroll uses
      // `element.scrollIntoView({behavior:'smooth', block:'center'})`
      // which bubbles up the ancestor chain and ALSO scrolls the
      // window - that drags the fixed topbar/sidebar and breaks the
      // layout. We do our own container-only scroll in
      // `onPopoverRender`, once the card can be measured. Setting smoothScroll:false makes Driver pass
      // `behavior:'auto'` AND only scroll if not already in viewport,
      // which on this layout (body{overflow:hidden}) is a no-op.
      smoothScroll: false,
      // Allow closing so users always have an escape hatch (X button + ESC
      // key). Without this the user can get stuck on a dark overlay with no
      // way out if a popover positions itself off-screen for any reason.
      allowClose: true,
      disableActiveInteraction: false,
      stagePadding: 6,
      stageRadius: 6,
      popoverOffset: 0,
      overlayOpacity: 0.5,
      overlayColor: '#000',
      showProgress: true,
      progressText: tx('Step {{current}} of {{total}}'),
      nextBtnText: tx('Next'),
      prevBtnText: tx('Back'),
      doneBtnText: tx('Done'),
      popoverClass: 'gp-tour-popover',
      steps: driverSteps,
      onPopoverRender: (popover, opts) => {
        // The popover lives at one of two fixed anchor points:
        //   * centred in the viewport - for steps with no SVG cut-out
        //     (welcome step, or any step whose target isn't found)
        //   * bottom-right corner - whenever a real element is
        //     highlighted, so the popover never covers the cut-out
        //     and the (visually hidden) Driver.js arrow tucks under
        //     the popover instead of floating beside the target.
        // Driver.js recreates the wrapper each step. The motion component
        // preserves its visible box while resizing at the new anchor.
        const root = popover?.wrapper || document.querySelector('.driver-popover');
        if (!root) return;
        root.style.removeProperty('display');
        popover.previousButton.classList.add('btn', 'btn-default');
        popover.nextButton.classList.add('btn', 'btn-confirm');
        popover.closeButton.classList.add('btn', 'btn-tertiary', 'btn-sm', 'btn-icon-only', 'btn-touch-target');

        // Driver.js' positioning code inlines `top/left/right/bottom`
        // and `transform: translateY(...)` on the wrapper. Wipe them
        // so our class-based transforms win cleanly.
        root.style.top = '';
        root.style.left = '';
        root.style.right = '';
        root.style.bottom = '';
        root.style.transform = '';

        const state = opts?.state || {};
        // Track furthest step reached (see _maxIndex declaration above).
        if (typeof state.activeIndex === 'number' && state.activeIndex > _maxIndex) {
          _maxIndex = state.activeIndex;
        }
        const activeEl =
          state.activeElement || state.__activeElement || state['activeElement'];
        // Driver.js commits its previous element on the next frame. Multiple
        // clicks within that frame can otherwise leave earlier targets active.
        document.querySelectorAll('.driver-active-element').forEach((el) => {
          if (el === activeEl) return;
          el.classList.remove('driver-active-element', 'driver-no-interaction');
          ['aria-haspopup', 'aria-expanded', 'aria-controls'].forEach((name) => el.removeAttribute(name));
        });
        const isDummy =
          !activeEl ||
          activeEl.id === 'driver-dummy-element' ||
          (activeEl.classList && activeEl.classList.contains('driver-dummy-element'));
        // Padding around Driver.js' zero-size dummy makes a circular hole
        // at the viewport centre. Intro/outro steps need a solid backdrop.
        opts.driver.setConfig({ ...opts.config, stagePadding: isDummy ? 0 : 6 });
        scrollTourTarget(activeEl, ctx, root);
        // Compare the usable target area on each side of the measured card.
        // This also handles bottom-of-drawer controls and short landscape views.
        let wantsMobileTop = false;
        if ((_isMobile() || _isLandscapePhone()) && !isDummy) {
          const rect = activeEl.getBoundingClientRect();
          const remaining = (ctx.scrollTargets || []).reduce((y, target) =>
            y + (typeof target.top === 'number' ? target.top - target.scroller.scrollTop : 0), 0);
          const top = rect.top - remaining, bottom = top + rect.height;
          const height = root.getBoundingClientRect().height;
          const visibleBelow = Math.max(0, Math.min(bottom, innerHeight - height - 16) - Math.max(top, 0));
          const visibleAbove = Math.max(0, Math.min(bottom, innerHeight) - Math.max(top, height + 16));
          wantsMobileTop = visibleAbove > visibleBelow + 4;
        }
        const next = isDummy ? 'centered' : (wantsMobileTop ? 'mobileTop' : 'corner');
        const prev = document.documentElement.dataset.gpTourPos || next;
        const remainingScroll = () => (ctx.scrollTargets || []).reduce((offset, target) => {
          if (typeof target.left === 'number') offset.x += target.left - target.scroller.scrollLeft;
          if (typeof target.top === 'number') offset.y += target.top - target.scroller.scrollTop;
          return offset;
        }, { x: 0, y: 0 });
        let reveal;
        if (!isDummy && (prev === 'centered' || !_highlightReady)) {
          const rect = activeEl.getBoundingClientRect();
          const offset = remainingScroll();
          reveal = { x: rect.left - offset.x - 6, y: rect.top - offset.y + rect.height / 2,
            width: rect.width + 12 };
        }
        const highlight = () => GP.motion.tourHighlight(
          document.querySelector('.driver-overlay'), true, remainingScroll,
          { reveal: reveal, collapse: isDummy,
            track: _isInsideSidebar(isDummy ? ctx.previousTarget : activeEl)
              ? () => (isDummy ? ctx.previousTarget : activeEl).getBoundingClientRect() : undefined },
        );
        if (document.querySelector('.driver-overlay')) highlight();
        else if (!isDummy) requestAnimationFrame(() => {
          if (root.isConnected) highlight();
        });
        _highlightReady = false;
        document.documentElement.dataset.gpTourPos = next;

        document.documentElement.classList.add('gp-tour-pinned-active');

        const setAnchor = (position) => {
          root.classList.remove(
            'gp-tour-popover--centered',
            'gp-tour-popover--corner',
            'gp-tour-popover--mobile-top',
          );
          if (position === 'mobileTop') root.classList.add('gp-tour-popover--corner', 'gp-tour-popover--mobile-top');
          else root.classList.add(`gp-tour-popover--${position}`);
        };
        setAnchor(next);
        requestAnimationFrame(() => {
          if (!root.isConnected) return;
          _highlightReady = !isDummy;
        });
        if (!_entranceShown) {
          _entranceShown = true;
          GP.motion.tourPopover(root, true);
        } else GP.motion.tourStep(root, ctx.popoverRect);

        // -- Mobile swipe navigation --------------------------------------
        // Swipe left  -> next step
        // Swipe right -> previous step
        // Swipe down  -> dismiss tour (bottom-sheet only, mirrors ESC)
        // Only wired on touch devices at mobile breakpoints to avoid
        // interfering with text selection or horizontal scroll on desktop.
        if ((_isMobile() || _isLandscapePhone()) && 'ontouchstart' in window) {
          let _swipeX = 0, _swipeY = 0;
          const _swipeStart = (e) => {
            _swipeX = e.touches[0].clientX;
            _swipeY = e.touches[0].clientY;
          };
          const _swipeEnd = (e) => {
            const dx = e.changedTouches[0].clientX - _swipeX;
            const dy = e.changedTouches[0].clientY - _swipeY;
            const adx = Math.abs(dx), ady = Math.abs(dy);
            if (Math.max(adx, ady) < 40) return; // too small - ignore
            const drv = driverRef.current;
            if (!drv) return;
            if (adx > ady) {
              // Horizontal swipe - navigate steps
              if (dx < -40) {
                if (e.cancelable) e.preventDefault();
                try { navigator.vibrate?.(8); } catch { /* noop */ }
                try { drv.moveNext(); } catch { /* noop */ }
              } else if (dx > 40) {
                if (e.cancelable) e.preventDefault();
                try { navigator.vibrate?.(8); } catch { /* noop */ }
                try { drv.movePrevious(); } catch { /* noop */ }
              }
            } else if (!e.target.closest('.driver-popover-description') &&
              ((dy > 60 && !root.classList.contains('gp-tour-popover--mobile-top')) ||
               (dy < -60 && root.classList.contains('gp-tour-popover--mobile-top')))) {
              // Swipe down on bottom-sheet -> dismiss (same as pressing ×)
              if (e.cancelable) e.preventDefault();
              try { navigator.vibrate?.(12); } catch { /* noop */ }
              closeTour();
            }
          };
          root.addEventListener('touchstart', _swipeStart, { passive: true });
          root.addEventListener('touchend', _swipeEnd, { passive: false });
          // Clean up listeners when this popover instance is destroyed.
          // Driver.js recreates the DOM node each step, so each render
          // registers its own pair - no persistent references needed.
        }
      },
      onDestroyStarted: closeTour,
      onDestroyed: () => {
        document.removeEventListener('keydown', escHandler, true);
        ctx.scrollTargets?.forEach((target) => GP.motion.tourScroll(target.scroller));
        GP.motion.tourHighlight(document.querySelector('.driver-overlay'), false);
        document.documentElement.classList.remove('gp-tour-pinned-active');
        const tourMenu = document.querySelector(
          '[data-user-menu][data-dropdown-owner="tour"]'
        );
        window.GP?.dropdown?.close(tourMenu);
        delete document.documentElement.dataset.gpTourPos;
        detachScrollBridge();
        // If the tour left the mobile sidebar open, restore the original state.
        if (_isMobile()) _closeMobileSidebarFromTour();
        if (window.__gpTourActiveDriver === driverInstance) {
          window.__gpTourActiveDriver = null;
        }
        // Allow auto-prompt to fire again for OTHER tours after this one
        // ends. Without this reset, run() set the flag to true and any
        // subsequent page (htmx swap or in-page nav) would silently
        // skip its own welcome card. The per-tour ':prompted' lsKey
        // still prevents the SAME tour from re-prompting.
        _welcomePromptedThisLoad = false;
        // Mark completed only if the user reached the last step.
        // Stage-aware: write BOTH the legacy global key AND a per-stage
        // fingerprinted key, so multi-stage pages (e.g. /dashboard/support)
        // can re-prompt on subsequent stages while a fully-seen stage stays
        // remembered.
        // IMPORTANT: prefer the locally-tracked `_maxIndex` (updated in
        // onPopoverRender) over `driverInstance.getActiveIndex()`. The
        // latter is unreliable inside onDestroyed  -  driver.js may
        // have already cleared its internal state, returning -1, which
        // would mis-classify a fully-completed tour as "skipped".
        const liveIdx = driverInstance.getActiveIndex?.();
        const idx = (typeof liveIdx === 'number' && liveIdx >= 0)
          ? Math.max(liveIdx, _maxIndex)
          : _maxIndex;
        const total = steps.length;
        const fp = stageFingerprint(steps);
        // IMPORTANT: write only the per-stage fingerprinted key, NOT the
        // bare global slug+role key. Multi-stage pages (e.g. /dashboard/support:
        // course-picker -> category -> form) share the same slug, so writing the
        // bare `:completed` key on the first stage permanently suppressed the
        // welcome card on every subsequent stage. The bare key is reserved
        // for *explicit* user dismissals (× / "Maybe later" on the welcome
        // card - see persistDismiss below), which legitimately should be
        // final across the whole slug.
        if (typeof idx === 'number' && idx >= total - 1) {
          // Full completion: write per-stage fingerprinted key.
          const ts = String(Date.now());
          const _completedKey = scopedKey(slug, COMPLETED_SUFFIX, role) + ':' + fp;
          lsSet(_completedKey, ts);
          syncToServer(_completedKey);
          if (tour && tour.multiStage) {
            // Multi-stage flow (e.g. /dashboard/support course-picker -> form):
            // clear the global :prompted key so the welcome card can re-appear
            // on the NEXT stage (different fingerprint, same slug).
            // Per-stage `:prompted:fp=` is left intact for SAME-stage refreshes.
            lsDel(scopedKey(slug, PROMPTED_SUFFIX, role));
          } else {
            // Single-stage tour: once completed, never re-prompt for THIS
            // slug+role even on page variants that yield a different DOM
            // fingerprint (e.g. different students on student_detail).
            // Write the bare global :completed key in addition to the
            // per-stage one, then clear :prompted (otherwise the global
            // check would still pass it through on next page load).
            const _completedGlobalKey = scopedKey(slug, COMPLETED_SUFFIX, role);
            lsSet(_completedGlobalKey, ts);
            syncToServer(_completedGlobalKey);
            lsDel(scopedKey(slug, PROMPTED_SUFFIX, role));
          }
          window.showToast(
            `${tx('Tour complete')}: ${tour['title_' + getLocale()] || tour.title_en}`,
            'success',
          );
        } else {
          // Mark skipped per-stage only - see comment above.
          const _skippedStageKey = scopedKey(slug, SKIPPED_SUFFIX, role) + ':' + fp;
          lsSet(_skippedStageKey, String(Date.now()));
          syncToServer(_skippedStageKey);
          // Same multi-stage clear as full completion: user already engaged
          // with this tour on this stage; let the next stage re-prompt.
          // Per-stage `:prompted:fp=` is left intact for SAME-stage refreshes.
          lsDel(scopedKey(slug, PROMPTED_SUFFIX, role));
        }
      },
    });

    driverRef.current = driverInstance;
    // Expose globally so the mobile-sidebar open helper (module scope,
    // no closure access to driverInstance) can call refresh() after
    // its slide-in transition completes.
    window.__gpTourActiveDriver = driverInstance;

    driverInstance.drive(0);

    // If a loader is still on screen, the very first step often
    // ends up centred because its target hasn't rendered yet. Re-evaluate
    // the current step once the DOM is stable so highlighting "kicks in"
    // as soon as the real content arrives.
    waitForStableDom(20000).then(() => {
      try {
        if (_leaving || !driverInstance.isActive()) return;
        const idx = driverInstance.getActiveIndex?.() ?? 0;
        const active = driverInstance.getActiveElement?.();
        if (active?.isConnected && active.id !== 'driver-dummy-element') {
          driverInstance.refresh();
          return;
        }
        // Re-driving the same index forces Driver.js to re-resolve the
        // element() function, which now returns the freshly-rendered node.
        if (typeof idx === 'number' && driverSteps[idx]?.element) driverInstance.drive(idx);
      } catch { /* noop */ }
    });

    // Global ESC rescue - guarantees the user can never get stuck on a
    // dark overlay even if Driver.js' own keyboard handler fails or is
    // suppressed by some other listener.
    document.addEventListener('keydown', escHandler, true);
    return true;
  };
