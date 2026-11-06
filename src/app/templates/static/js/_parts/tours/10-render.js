  /** Public: run only if not previously completed/skipped (used by auto-prompt). */
  const runIfEligible = (slug) => {
    const role = getRole();
    if (lsGet(scopedKey(slug, COMPLETED_SUFFIX, role)) || lsGet(scopedKey(slug, SKIPPED_SUFFIX, role))) return false;
    return run(slug);
  };

  /** Public: reset persisted state (one slug or all). */
  const reset = (slug) => {
    try {
      const keys = [];
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (!k?.startsWith(STORAGE_PREFIX)) continue;
        if (slug && !k.includes(slug + '@')) continue;
        keys.push(k);
      }
      keys.forEach((k) => localStorage.removeItem(k));
    } catch { /* noop */ }
    // Clear session-level sync guards so a reset -> re-complete cycle
    // in the same tab works correctly (keys can be re-POSTed, and seed
    // will re-run to reflect the now-cleared server state).
    _syncedKeys.clear();
    try { sessionStorage.removeItem(_SEED_SESSION_KEY); } catch { /* noop */ }
    // Drop the stale seed promise: it resolved with the pre-reset key list
    // and would suppress autoPromptIfFirstVisit on the same page load.
    _seedPromise = null;
    // Propagate reset to server so other devices are unblocked.
    try {
      const csrf = window.GP?.csrfToken
        || document.querySelector('meta[name="csrf-token"]')?.content
        || '';
      const url = slug
        ? `/dashboard/api/tour/seen?slug=${encodeURIComponent(slug)}`
        : '/dashboard/api/tour/seen';
      fetch(url, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: { 'X-CSRF-Token': csrf },
      }).catch(() => { /* noop */ });
    } catch { /* noop */ }
    // Do NOT call seedFromServer() here. The DELETE above is fire-and-
    // forget - if we immediately GET /seen, the request can arrive at the
    // server before the DELETE is processed and we would re-seed the very
    // keys we just cleared, which would prevent autoPromptIfFirstVisit from
    // showing the welcome card on the same page load.
    // On the next page load, seedFromServer() runs normally and will fetch
    // the by-then-empty server state.
  };

  /** Render a small floating welcome card (bottom-right) inviting the tour. */
  let _welcomePromptedThisLoad = false;
  /** Dismiss any visible welcome card immediately (used when run() is
   *  invoked from another path - user-menu launcher or programmatic). */
  const dismissWelcomeCard = () => {
    const card = document.getElementById('gpTourWelcome');
    if (!card) return;
    // Guard against double-dismiss (e.g. modal-open + sidebar-open events
    // firing back-to-back) - the second call would restart the timer and
    // could interrupt the in-flight transition mid-way, making it look
    // instant. Mark the card so subsequent calls become no-ops.
    if (card.dataset.gpDismissing === '1') return;
    card.dataset.gpDismissing = '1';
    card.classList.remove('is-visible');
    // CSS transition is 260ms (transform/opacity); use 320ms for headroom
    // so the node is removed only after the slide-down fully finishes.
    setTimeout(() => {
      try { card.remove(); } catch (_) {}
      try {
        window.dispatchEvent(new CustomEvent('gp:tour:welcome:dismissed'));
      } catch (_) {}
    }, 320);
  };
  const renderWelcomeCard = (tour) => {
    if (_welcomePromptedThisLoad) return;
    if (document.getElementById('gpTourWelcome')) return;
    // Never prompt while another tour is actually running - the welcome
    // card would float over the dimmed Driver.js overlay and confuse
    // users into thinking two tours are competing.
    if (window.__gpTourActiveDriver) return;
    _welcomePromptedThisLoad = true;
    // Close anything that would visually compete with the welcome card
    // (open mobile sidebar from earlier user interaction, lingering
    // modal, dropdown menu, tooltip...). Done once at render time so we
    // never re-trigger on subsequent DOM mutations.
    closeCompetingOverlays('welcome-card');
    const card = document.createElement('div');
    card.id = 'gpTourWelcome';
    card.className = 'gp-tour-welcome';
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    card.setAttribute('aria-labelledby', 'gpTourWelcomeTitle');
    const title = tour['title_' + getLocale()] || tour.title_en;
    const subtitle = tour['subtitle_' + getLocale()] || tour.subtitle_en || '';
    // Use the COMPILED step count (after dropping role-mismatched, requires-false,
    // and missing-element steps). Otherwise we advertise '5 steps' when only 2
    // will actually run, which the user notices and complains about.
    let stepCount = 0;
    try { stepCount = compileSteps(tour, getRole()).length; } catch { stepCount = tour.steps?.length ?? 0; }
    if (!stepCount) stepCount = tour.steps?.length ?? 0;
    const minutes = Math.max(1, Math.round(stepCount / 8));
    card.innerHTML = `
      ${GP.closeButtonHtml(tx('Dismiss'), 'gp-tour-welcome-close')}
      <div class="gp-tour-welcome-hat">${GP.badgeHtml(tx('New here?'), 'info')}</div>
      <div class="gp-tour-welcome-title" id="gpTourWelcomeTitle">${title}</div>
      ${subtitle ? `<div class="gp-tour-welcome-sub">${subtitle}</div>` : ''}
      <div class="gp-tour-welcome-meta">
        ${GP.badgeHtml(tx('Steps:') + ' ' + stepCount, 'gray', { icon: 'list' })}
        ${GP.badgeHtml('~' + minutes + ' ' + tx('min'), 'gray', { icon: 'clock' })}
      </div>
      <div class="gp-tour-welcome-actions">
        <button type="button" class="btn btn-primary btn-sm gp-tour-welcome-start" data-tour-action="start">${tx('Take the tour')}</button>
        <button type="button" class="btn btn-secondary btn-sm gp-tour-welcome-skip" data-tour-action="later">${tx('Maybe later')}</button>
      </div>
    `;
    document.body.appendChild(card);
    requestAnimationFrame(() => {
      card.classList.add('is-visible');
      // Move focus to the Start button after the slide-in animation begins
      // so screen readers announce the dialog and its primary action.
      // The second rAF ensures the element is visible/painted before focus.
      requestAnimationFrame(() => {
        if (_userIsBusy()) {
          dismissWelcomeCard();
          return;
        }
        try { card.querySelector('[data-tour-action="start"]')?.focus(); } catch { /* noop */ }
      });
    });

    // Track whether the user explicitly chose to dismiss vs the auto-
    // dismiss timeout firing. Explicit dismissals are persisted so the
    // welcome card cannot pop back on a subsequent htmx:afterSwap or
    // even on the next page reload until the user clears tour history.
    const role = getRole();
    let _stageFp = '';
    try { _stageFp = stageFingerprint(compileSteps(tour, role)); } catch { _stageFp = ''; }
    const persistDismiss = () => {
      try {
        const now = String(Date.now());
        // Global slug+role key - survives htmx swaps and fingerprint
        // drift, so closing once is final until tour-reset clears it.
        const _dismissKey = scopedKey(tour.slug, SKIPPED_SUFFIX, role);
        lsSet(_dismissKey, now);
        syncToServer(_dismissKey);
        // Per-stage key for parity with the existing autoPrompt check.
        if (_stageFp) {
          const _dismissStageKey = _dismissKey + ':' + _stageFp;
          lsSet(_dismissStageKey, now);
          syncToServer(_dismissStageKey);
        }
      } catch { /* noop */ }
    };

    const close = (userInitiated) => {
      if (userInitiated) persistDismiss();
      card.classList.remove('is-visible');
      setTimeout(() => card.remove(), 220);
    };
    card.querySelector('.gp-tour-welcome-close')?.addEventListener('click', () => close(true));
    card.querySelector('[data-tour-action="later"]')?.addEventListener('click', () => close(true));
    card.querySelector('[data-tour-action="start"]')?.addEventListener('click', () => {
      close(false);
      run(tour.slug);
    });

    // Auto-dismiss after 25s if ignored. We do NOT persist a SKIPPED
    // marker here - the user didn't make an active choice - but the
    // per-stage `:prompted` key already written by autoPromptIfFirstVisit
    // prevents re-nagging within the same fingerprint.
    setTimeout(() => {
      if (document.body.contains(card)) {
        close(false);
      }
    }, 25000);
  };

  const _userIsBusy = () => GP.hasUnsavedState()
    || document.activeElement?.isContentEditable
    || document.activeElement?.matches('input, textarea, select')
    || !!document.querySelector(
      '.modal-backdrop.active, .flatpickr-calendar.open, .gl-dropdown.open, #searchModalBackdrop.active, #appSidebar.mobile-open',
    );

  /** Auto-prompt: offer the most relevant un-seen tour shortly after page idle.
   *  Pass immediate=true to skip the waitForStableDom + isPageLoading guards
   *  (used when the user explicitly clicks "Clear tours" - in that case the
   *  page is already rendered and we must not wait up to 20 s). */
  const autoPromptIfFirstVisit = async (immediate = false) => {
    if (_welcomePromptedThisLoad) return;
    // If a tour is currently running, don't pop a competing welcome card.
    if (window.__gpTourActiveDriver) return;
    if (!immediate && _userIsBusy()) return;
    const page = getPageSlug();
    const role = getRole();
    if (!page) return;

    // Stage-1 candidate filter: must be autoPrompt-eligible for this page/role.
    const candidates = [...tours.values()].filter((t) =>
      t.autoPrompt && t.pages?.includes(page) && t.roles?.includes(role),
    );
    if (!candidates.length) return;

    // One-time auto-prompt per device/role: once ANY tour has been offered
    // automatically, never pop the welcome card again while navigating. Tours
    // stay available on demand from the launcher (the "?" help control). Without
    // this the card appeared on EVERY page's first visit as the user moved
    // through the app (re-armed on each htmx:afterSwap), which read as the tour
    // "appearing everywhere by mistake".
    const globalAutoKey = scopedKey('_auto', PROMPTED_SUFFIX, role);
    if (lsGet(globalAutoKey)) return;

    // Wait for the cross-device seed to finish before deciding whether to
    // prompt. Otherwise a user who completed/dismissed the tour on another
    // device sees the welcome card here while the server response is still
    // in flight. Cap the wait at 4 s so a hung / offline backend cannot
    // permanently suppress the welcome card.
    if (_seedPromise) {
      try {
        await Promise.race([
          _seedPromise,
          new Promise((res) => setTimeout(res, 4000)),
        ]);
      } catch { /* noop */ }
    }

    // Claim the slot BEFORE awaiting so concurrent triggers (initial
    // armAutoPrompt + htmx:afterSwap) cannot race past this guard and
    // both end up in renderWelcomeCard - which previously caused the
    // card to flash on screen for a single frame and then be wiped
    // by the duplicate-id check in the second call.
    _welcomePromptedThisLoad = true;
    // Track whether we actually got far enough to render. Every early
    // exit below MUST release the optimistic lock - otherwise the
    // welcome card silently never appears for the rest of the page
    // load (this was the "sometimes shows, sometimes doesn't" flake
    // where a candidate compiled to 0 steps and the lock stayed set).
    let rendered = false;
    try {
      // Wait until loaders / busy regions have settled so the welcome card
      // and the first highlighted step don't end up pointing at a loading
      // state that the page is about to replace.
      if (!immediate) await waitForStableDom(20000);

      // Re-check post-await: a tour may have started during the wait,
      // or the timeout may have elapsed and the page is STILL loading.
      // Skip these guards when called in immediate mode (explicit user
      // action - the page is already rendered, polling must not block).
      if (!immediate && isPageLoading()) return;
      if (window.__gpTourActiveDriver) return;
      // A delayed first-visit prompt must yield to edits and open controls.
      if (!immediate && _userIsBusy()) return;

      for (const tour of candidates) {
        let compiled;
        try { compiled = compileSteps(tour, role); } catch { compiled = []; }
        if (!compiled.length) continue;
        // Global slug+role keys: an explicit user dismiss (× / "Maybe
        // later") writes these. They survive fingerprint drift so the
        // welcome card cannot pop back on the next htmx:afterSwap with
        // a slightly different DOM snapshot.
        const completedGlobal = scopedKey(tour.slug, COMPLETED_SUFFIX, role);
        const skippedGlobal = scopedKey(tour.slug, SKIPPED_SUFFIX, role);
        // promptedGlobal: set when the welcome card has been shown for this
        // tour at least once (any stage/fingerprint). Prevents re-prompting
        // when navigating between pages that share a slug but differ in
        // rendered content (e.g. different students on student_detail page
        // produce different DOM fingerprints, making each student look like
        // a new "stage" without this guard).
        const promptedGlobal = scopedKey(tour.slug, PROMPTED_SUFFIX, role);
        // Backfill global completion from persisted fingerprint keys for a
        // single-stage tour. DOM changes must not reopen a completed tour.
        if (!tour.multiStage && !lsGet(completedGlobal)) {
          let _legacyHit = false;
          try {
            const _prefix = STORAGE_PREFIX + completedGlobal + ':fp=';
            for (let i = 0; i < localStorage.length; i++) {
              const k = localStorage.key(i);
              if (k && k.indexOf(_prefix) === 0) { _legacyHit = true; break; }
            }
          } catch { /* localStorage disabled / quota - give up quietly */ }
          if (_legacyHit) {
            const _ts = String(Date.now());
            lsSet(completedGlobal, _ts);
            try { syncToServer(completedGlobal); } catch { /* noop */ }
          }
        }
        if (lsGet(completedGlobal) || lsGet(skippedGlobal) || lsGet(promptedGlobal)) continue;
        const fp = stageFingerprint(compiled);
        const completedStage = completedGlobal + ':' + fp;
        const skippedStage = skippedGlobal + ':' + fp;
        const promptedStage = promptedGlobal + ':' + fp;
        // Stage-level memory: also check per-fingerprint keys in case they
        // were written by a prior session before this global guard existed.
        if (lsGet(completedStage) || lsGet(skippedStage) || lsGet(promptedStage)) continue;
        lsSet(promptedStage, String(Date.now()));
        // Set the global prompted key so that subsequent navigations to any
        // page with the same slug (different students, etc.) don't re-show
        // the welcome card even when the DOM fingerprint differs.
        lsSet(promptedGlobal, String(Date.now()));
        // One-time global gate: after the first auto-prompt on this device, no
        // more welcome cards pop automatically on any page (they can still be
        // launched by hand).
        lsSet(globalAutoKey, String(Date.now()));
        // Note: prompted keys are intentionally NOT synced to the server.
        // They represent "the welcome card was shown on this device" -
        // syncing them would prevent the card from appearing on a new device
        // that has never seen the tour, which defeats the feature's purpose.
        // Reset the slot so renderWelcomeCard sees a fresh state -
        // it sets the lock again itself in its own duplicate-render
        // guard, so we won't double-fire.
        _welcomePromptedThisLoad = false;
        renderWelcomeCard(tour);
        rendered = true;
        return;
      }
    } finally {
      // Universal release: if we exited without rendering for ANY
      // reason (active driver, no compiled steps, all stages already
      // seen, exception), free the lock so a later htmx:afterSwap or
      // tour-reset can legitimately re-trigger.
      if (!rendered) _welcomePromptedThisLoad = false;
    }
  };

  // -- Bootstrap --
  // Run auto-prompt after first idle (or 1.2s, whichever first) so the page
  // has a chance to settle.  Also re-check after HTMX swaps the lazy content
  // in (some pages render their target elements only after the swap).
  const armAutoPrompt = () => {
    const fire = () => autoPromptIfFirstVisit();
    // If the page is already idle the moment we arm, fire on the next
    // animation frame - no need to wait a full second on a fast page.
    if (!isPageLoading()) {
      requestAnimationFrame(fire);
      return;
    }
    if (typeof window.requestIdleCallback === 'function') {
      window.requestIdleCallback(fire, { timeout: 800 });
    } else {
      setTimeout(fire, 400);
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', armAutoPrompt);
  } else {
    armAutoPrompt();
  }
  document.body?.addEventListener?.('htmx:afterSwap', () => {
    // A page swap counts as a fresh chance to prompt: reset the
    // module-level lock so the new page's autoPrompt-eligible tour
    // (if any, and not yet prompted) can render its welcome card.
    _welcomePromptedThisLoad = false;
    setTimeout(autoPromptIfFirstVisit, 400);
  });

  // -- Orientation / resize refresh --
  // When the user rotates their phone or resizes the window mid-tour,
  // Driver.js' SVG overlay and popover anchor become stale (they were
  // measured against the old viewport dimensions). A debounced refresh()
  // call re-measures the active element and repaints the cut-out.
  // 150 ms covers the ~300 ms CSS rotation transition on iOS / Android
  // without triggering on every pixel of a desktop resize drag.
  //
  // Skip refresh when ONLY window.innerHeight changes (Chrome on Android
  // shows/hides the address bar on scroll - this fires resize but the
  // layout viewport width is unchanged and driver.js repositioning causes
  // the popover to visibly jump up then fall back down).
  let _resizeTimer = 0;
  let _lastResizeWidth = window.innerWidth;
  window.addEventListener('resize', () => {
    if (!window.__gpTourActiveDriver) return;
    const currentWidth = window.innerWidth;
    if (currentWidth === _lastResizeWidth) return; // toolbar-only height change - skip
    _lastResizeWidth = currentWidth;
    clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(() => {
      try { window.__gpTourActiveDriver?.refresh(); } catch { /* noop */ }
    }, 150);
  });

  // Public API
  window.GP = window.GP ?? {};
  window.GP.tour = {
    register,
    registerSharedSteps,
    run,
    runIfEligible,
    list,
    reset,
    isAvailable,
    getRole,
    getLocale,
    getPageSlug,
  };

  // -- Cross-tab coordination --
  // When the user finishes / dismisses a tour in one tab, tear down any
  // visible welcome card or active driver in OTHER open tabs of the same
  // app so they don't keep advertising a tour that was just consumed.
  // Browsers fire `storage` events on every OTHER tab when localStorage
  // changes - never on the tab that wrote the value, so this is always
  // safe. We filter to our own prefix to avoid reacting to unrelated keys.
  try {
    window.addEventListener('storage', (e) => {
      if (!e || !e.key || !e.key.startsWith(STORAGE_PREFIX)) return;
      // React only to completion / skip writes (the meaningful signals).
      // PROMPTED keys also fire, but those don't need cross-tab cleanup.
      if (!e.key.includes(COMPLETED_SUFFIX) && !e.key.includes(SKIPPED_SUFFIX)) return;
      try { dismissWelcomeCard(); } catch { /* noop */ }
      try {
        const drv = window.__gpTourActiveDriver;
        if (drv && typeof drv.destroy === 'function') drv.destroy();
      } catch { /* noop */ }
    });
  } catch { /* noop */ }

  // -- Ongoing overlay suppression while a tour is active --
  // The earlier MutationObserver approach broke popover positioning by
  // calling driver.destroy() during step transitions. Instead, attach
  // narrowly-scoped listeners that fire AFTER the user's interaction
  // (a click that opens a sidebar/modal/dropdown) and run a single
  // microtask later, so the driver popover position is already
  // committed for the current step.
  try {
    const isDriverActive = () => !!window.__gpTourActiveDriver
      || document.documentElement.classList.contains('gp-tour-pinned-active');
    const isWelcomeVisible = () => !!document.getElementById('gpTourWelcome');
    const scheduleDismiss = (reason) => {
      // Defer one frame so DOM mutations from the triggering action settle
      // before we dismiss the welcome card / close competing driver overlays.
      requestAnimationFrame(() => {
        // 1) Always dismiss the floating welcome card if visible - it is
        //    a non-modal CTA that must yield to anything the user just
        //    chose to open (sidebar, modal, dropdown, drawer, ...).
        if (isWelcomeVisible()) {
          try { dismissWelcomeCard(); } catch { /* noop */ }
        }
        // 2) During an actual driver tour, also close the competing
        //    overlay so the highlighted target stays visible.
        if (isDriverActive()) {
          try { closeCompetingOverlays(reason); } catch { /* noop */ }
        }
      });
    };
    const shouldHandle = () => isWelcomeVisible() || isDriverActive();
    document.addEventListener('click', (ev) => {
      if (!shouldHandle()) return;
      const t = ev.target;
      if (!t || !(t instanceof Element)) return;
      // Don't react to clicks inside the welcome card itself or on the
      // driver popover - those are tour-owned surfaces.
      if (t.closest('#gpTourWelcome, .driver-popover')) return;
      // On desktop/tablet the sidebar is a permanent layout column - any
      // interaction inside it (nav links, collapse/expand, language switcher,
      // collapsible sub-sections) must never dismiss the welcome card or tour.
      // On mobile the sidebar slides over content, so dismiss IS correct there.
      if (!_isMobile() && t.closest('#appSidebar, .gl-sidebar')) return;
      // Sidebar toggles (mobile hamburger, collapsible rail, custom).
      // Only dismiss on mobile - on desktop/tablet the sidebar sits in the
      // layout and does not overlap the welcome card or tour popover.
      if (_isMobile() && t.closest('.gl-mobile-menu-btn, [data-action="toggle-sidebar"], .gl-sidebar-toggle, [data-toggle="sidebar"]')) {
        scheduleDismiss('sidebar-toggle-click');
        return;
      }
      // Anything that opens a modal via data-attribute.
      if (t.closest('[data-modal-open], [data-open-modal], [data-toggle="modal"]')) {
        scheduleDismiss('modal-trigger-click');
        return;
      }
      // Header dropdowns / details elements - scoped to known dropdown containers
      // (NOT the bare `summary` tag) so collapsible panels elsewhere on the page,
      // e.g. code-reference sections in Course Settings, don't trigger dismiss.
      if (t.closest('details.gp-menu, details.dropdown, details.user-menu')) {
        scheduleDismiss('details-click');
      }
    }, true);
    // App-managed modal events.
    document.addEventListener('gp:modal-open', dismissWelcomeCard);
    // Sidebar open event: only relevant on mobile where it covers the viewport.
    document.addEventListener('gp:sidebar:open', () => { if (_isMobile()) scheduleDismiss('gp:sidebar:open'); });
    // The mobile sidebar can also open without a click on its toggle.
    const bodyObserver = new MutationObserver(() => {
      if (!shouldHandle()) return;
      const hasMobileOverlay = _isMobile() && document.body.classList.contains('sidebar-mobile-open');
      if (hasMobileOverlay) {
        scheduleDismiss('body-class-overlay-open');
      }
    });
    bodyObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  } catch { /* noop */ }

  // -- Header launcher (in user dropdown) --
  const wireLauncher = () => {
    document.addEventListener('click', async (ev) => {
      const launcher = ev.target?.closest?.('[data-action="tour-launch"]');
      if (launcher) {
        ev.preventDefault();
        const available = list();
        if (available.length === 0) {
          window.showToast(
            tx('No tour available on this page yet.'),
            'info',
          );
          return;
        }
        // Run the first available tour for this page right away. The
        // engine already handles missing/late-arriving DOM nodes via the
        // post-start `waitForStableDom` re-drive in run() - no need to
        // block the user behind a "page is still loading" toast that may
        // never clear (e.g. an open SSE connection on the dashboard
        // counts as in-flight forever).
        run(available[0].slug);
        return;
      }
      const resetBtn = ev.target?.closest?.('[data-action="tour-reset"]');
      if (resetBtn) {
        ev.preventDefault();
        reset();
        _welcomePromptedThisLoad = false;
        window.showToast(
          tx('Tour history cleared.'),
          'success',
        );
        // Fire a fresh auto-prompt immediately - the user explicitly asked
        // to clear history and wants to see the card right now.  Skip
        // waitForStableDom and the isPageLoading guard (dashboard polling
        // could keep _inFlightRequests > 0 indefinitely).
        setTimeout(() => autoPromptIfFirstVisit(true), 200);
      }
    });
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireLauncher);
  } else {
    wireLauncher();
  }

  // -- Navigation-synced exit animation ----------------------------
  // When the welcome card is on screen and the user clicks a link or
  // submits a form that triggers a same-tab navigation, play the slide-
  // down/fade-out animation BEFORE navigating away. Browsers paint the
  // dismiss on this page, then the next page renders and its own
  // welcome card slides in - the transition feels synchronized end to
  // end. Without this hook the card vanished instantly (the new page
  // simply replaced it), which was jarring.
  //
  // We use capture phase so the listener wins over app routers. The
  // anchor's default action is suppressed and re-issued via
  // `location.assign(href)` after the animation duration. New-tab
  // semantics (target=_blank, Ctrl/Meta/Shift+click), hash/mailto/tel
  // links and cross-origin links bypass the delay so the OS/browser
  // behaviour is preserved. The same hook fires htmx swaps via
  // `htmx:beforeRequest` - in that case the dismiss runs in parallel
  // because htmx asynchronously fetches and swaps; the durations are
  // comparable so it still feels synchronized.
  try {
    // Per-navigation re-entry guard - set on the anchor when we re-fire
    // the original click after the animation, so the second pass falls
    // through to the browser's default handler.
    const _navInFlight = new WeakSet();
    document.addEventListener('click', (ev) => {
      const card = document.getElementById('gpTourWelcome');
      if (!card || !card.classList.contains('is-visible')) return;
      // Skip if dismiss is already in flight - the card is leaving.
      if (card.dataset.gpDismissing === '1') return;
      // Find the navigating anchor. We deliberately do NOT intercept
      // clicks inside the welcome card itself (Start / Maybe later / ×).
      const a = ev.target?.closest?.('a[href]');
      if (!a) return;
      if (a.closest('#gpTourWelcome')) return;
      if (_navInFlight.has(a)) return;
      if (ev.defaultPrevented) return;
      // Honour modifier keys / target=_blank - they open in a new tab,
      // so the current page stays put and the card is irrelevant.
      if (ev.button !== 0) return; // only left-click
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
      const target = a.getAttribute('target');
      if (target && target !== '' && target !== '_self') return;
      const href = a.getAttribute('href');
      if (!href) return;
      if (href.startsWith('#') || href.startsWith('javascript:')
          || href.startsWith('mailto:') || href.startsWith('tel:')) return;
      // Only intercept same-origin navigations - leave external links
      // to the browser's normal flow (we cannot guarantee the next page
      // belongs to us, and any redirect could feel laggy with a 260ms
      // delay).
      let url;
      try { url = new URL(a.href, location.href); } catch { return; }
      if (url.origin !== location.origin) return;
      // Skip downloads - no navigation happens, so no page transition.
      if (a.hasAttribute('download')) return;
      // OK - play the exit animation, then navigate.
      ev.preventDefault();
      ev.stopPropagation();
      _navInFlight.add(a);
      // 260ms matches the CSS transition for transform/opacity on
      // `.gp-tour-welcome` (see tour.css). dismissWelcomeCard() already
      // schedules removal of the DOM node at 320ms; we proceed with
      // navigation slightly earlier (at 240ms) so the new page begins
      // loading just before the slide-down fully completes - feels
      // continuous instead of "wait, then go".
      try { dismissWelcomeCard(); } catch { /* noop */ }
      setTimeout(() => {
        try { location.assign(url.href); } catch { window.location.href = url.href; }
      }, 240);
    }, true);

    // Form submissions that cause a full navigation - same idea.
    document.addEventListener('submit', (ev) => {
      const card = document.getElementById('gpTourWelcome');
      if (!card || !card.classList.contains('is-visible')) return;
      if (card.dataset.gpDismissing === '1') return;
      const form = ev.target;
      if (!form || form.tagName !== 'FORM') return;
      // Forms inside the card or with htmx attributes are handled below
      // (htmx:beforeRequest) or are tour-internal.
      if (form.closest('#gpTourWelcome')) return;
      if (form.hasAttribute('hx-post') || form.hasAttribute('hx-get')
          || form.hasAttribute('hx-put') || form.hasAttribute('hx-delete')) return;
      // Best-effort: dismiss in parallel with the submit. We do NOT
      // delay form submission because intercepting form.submit() and
      // re-firing is fragile (validation state, file inputs, custom
      // submit handlers all break). The 260ms slide animation runs
      // while the browser is already requesting the next page -
      // perceived latency is identical.
      try { dismissWelcomeCard(); } catch { /* noop */ }
    }, true);

    // HTMX-driven swaps (in-page navigation): dismiss in parallel -
    // htmx fetches and swaps asynchronously, so the dismiss animation
    // runs while the response is in flight. Times line up well in
    // practice (~150ms swap, 260ms dismiss).
    document.addEventListener('htmx:beforeRequest', () => {
      const card = document.getElementById('gpTourWelcome');
      if (!card || !card.classList.contains('is-visible')) return;
      if (card.dataset.gpDismissing === '1') return;
      try { dismissWelcomeCard(); } catch { /* noop */ }
    });
  } catch { /* noop */ }
})();
