/**
 * Sidebar - collapse/expand, mobile toggle, tooltips, badge polling
 * GitLab Pajamas-style left navigation behavior.
 */
(function () {
  'use strict';

  const sidebar = document.getElementById('appSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('sidebarToggle');
  const mobileBtn = document.getElementById('mobileMenuBtn');
  const closeBtn = document.getElementById('sidebarCloseBtn');
  if (!sidebar) return;

  /* -- Mobile detection helper -- */
  function _isMobile() {
    return window.innerWidth <= 768;
  }

  /* -- Restore collapsed state (default = expanded) -- */
  /* Preferences > Behavior > "Start with the sidebar collapsed" is the ACCOUNT
     default, used only on a device that has no stored state yet - collapsing it
     here still wins locally afterwards. */
  let savedState = localStorage.getItem('sidebar-collapsed');
  if (savedState === null && document.documentElement.hasAttribute('data-sidebar-collapsed')) {
    savedState = 'true';
  }
  if (savedState === 'true') {
    sidebar.classList.add('collapsed');
  } else if (savedState === 'false' || savedState === null) {
    sidebar.classList.remove('collapsed');
    /* Nothing is written here. Seeding 'false' on the first visit is what made
       the preference impossible to use: after ANY page load the key existed, so
       `savedState` was never null again and the branch above that consults the
       account default became unreachable. Turning "Start with the sidebar
       collapsed" on then did nothing at all, for the life of the browser
       profile. The key is written when the reader TOGGLES the sidebar - which
       is the only thing that should out-rank their account default. */
  }

  /* -- Sidebar tooltips (only visible when collapsed) -- */
  function initSidebarTooltips() {
    if (typeof window.tippy !== 'function') return;

    const items = sidebar.querySelectorAll('.gl-sidebar-item, .gl-sidebar-bottom-item');
    items.forEach(function (el) {
      const textEl = el.querySelector('.gl-sidebar-item-text');
      if (!textEl) return;
      const text = textEl.textContent.trim();
      if (!text) return;

      // Destroy any existing instance (from global init)
      if (el._tippy) el._tippy.destroy();

      window.tippy(el, {
        content: text,
        placement: 'right',
        delay: [300, 0],
        offset: [0, 8],
        touch: false,
        appendTo: document.body,
      });

      // Disable when sidebar is expanded (text is visible)
      if (!sidebar.classList.contains('collapsed')) {
        el._tippy.disable();
      }
    });
  }

  function updateTooltipState() {
    const isCollapsed = sidebar.classList.contains('collapsed');
    const items = sidebar.querySelectorAll('.gl-sidebar-item, .gl-sidebar-bottom-item');
    items.forEach(function (el) {
      if (el._tippy) {
        isCollapsed ? el._tippy.enable() : el._tippy.disable();
      }
    });
  }

  /* -- Desktop: collapse / expand toggle; Mobile: close sidebar -- */
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      if (_isMobile()) {
        closeMobileSidebar();
      } else {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
        updateTooltipState();
      }
    });
  }

  /* -- Cross-tab: mirror collapsed state when another tab toggles -- */
  try {
    window.addEventListener('storage', function (ev) {
      if (ev.key !== 'sidebar-collapsed' || _isMobile()) return;
      const shouldCollapse = ev.newValue === 'true';
      if (sidebar.classList.contains('collapsed') === shouldCollapse) return;
      sidebar.classList.toggle('collapsed', shouldCollapse);
      updateTooltipState();
    });
  } catch (_) { /* noop */ }

  /* -- Mobile: open / close sidebar overlay -- */
  function openMobileSidebar() {
    sidebar.classList.add('mobile-open');
    if (overlay) overlay.classList.add('visible');
    document.body.classList.add('sidebar-mobile-open');
  }

  function closeMobileSidebar() {
    sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('visible');
    document.body.classList.remove('sidebar-mobile-open');
  }

  GP.sidebar = { open: openMobileSidebar, close: closeMobileSidebar };
  sidebar.addEventListener('transitionend', function (event) {
    if (event.target === sidebar && event.propertyName === 'transform') {
      window.__gpTourActiveDriver?.refresh();
    }
  });

  if (mobileBtn) {
    mobileBtn.addEventListener('click', openMobileSidebar);
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', closeMobileSidebar);
  }

  if (overlay) {
    overlay.addEventListener('click', closeMobileSidebar);
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && sidebar.classList.contains('mobile-open')) {
      closeMobileSidebar();
    }
  });

  /* -- Mobile: touch swipe-to-close gesture (mobile only) -- */
  let _touchStartX = 0;
  let _touchStartY = 0;
  let _isSwipingSidebar = false;

  function _handleTouchStart(e) {
    if (!_isMobile() || !sidebar.classList.contains('mobile-open')) return;
    const touch = e.touches && e.touches[0];
    if (!touch) return;
    _touchStartX = touch.clientX;
    _touchStartY = touch.clientY;
    _isSwipingSidebar = true;
  }

  function _handleTouchMove(e) {
    if (!_isSwipingSidebar || !_isMobile() || !sidebar.classList.contains('mobile-open')) return;
    const touch = e.touches && e.touches[0];
    if (!touch) return;
    const deltaX = touch.clientX - _touchStartX;
    const deltaY = touch.clientY - _touchStartY;
    // Dismiss when user swipes left by at least 40px, predominantly horizontal
    if (deltaX < -40 && Math.abs(deltaX) > Math.abs(deltaY) * 1.1) {
      _isSwipingSidebar = false;
      closeMobileSidebar();
    }
  }

  function _handleTouchEnd() {
    _isSwipingSidebar = false;
  }

  sidebar.addEventListener('touchstart', _handleTouchStart, { passive: true });
  sidebar.addEventListener('touchmove', _handleTouchMove, { passive: true });
  sidebar.addEventListener('touchend', _handleTouchEnd, { passive: true });
  sidebar.addEventListener('touchcancel', _handleTouchEnd, { passive: true });
  if (overlay) {
    overlay.addEventListener('touchstart', _handleTouchStart, { passive: true });
    overlay.addEventListener('touchmove', _handleTouchMove, { passive: true });
    overlay.addEventListener('touchend', _handleTouchEnd, { passive: true });
  }


  /* Navigating closes it. On a phone the sidebar is a full-screen overlay, and
     internal navigation only swaps the content BEHIND it - so tapping a link
     loaded the new page and left the user staring at the menu it was opened
     from, with no indication anything had happened. Delegated on the sidebar so
     it covers every link, including the ones rendered later. */
  sidebar.addEventListener('click', function (e) {
    const link = e.target.closest && e.target.closest('a[href]');
    if (!link || !sidebar.contains(link)) return;
    /* Not for a link that only toggles a section open. */
    const href = link.getAttribute('href') || '';
    if (!href || href === '#' || href.startsWith('#')) return;
    closeMobileSidebar();
  });

  /* -- Init tooltips after a micro-tick (ensure tippy CDN is loaded) -- */
  requestAnimationFrame(function () {
    requestAnimationFrame(initSidebarTooltips);
  });

  /* ============================================================
     SidebarBadgeController - SSE-first with polling fallback
     ============================================================

     Connects to /api/v1/dashboard/stream for real-time updates.
     On SSE event -> immediate badge refresh via _pollBadges().
     Falls back to 60 s polling only after 5 SSE failures.
     ============================================================ */
  const BADGE_POLL_INTERVAL = 60000; // 60 seconds
  const _badgeCache = {};
  let _badgePollTimer = null;
  let _badgePollFailCount = 0;
  const MAX_BADGE_POLL_FAILURES = 5;
  let _badgeSSE = null;
  const _BADGE_SSE_MAX_ERRORS = GP.SSE_MAX_ERRORS || 5;

  /** Build list of badge-eligible sidebar items */
  function _initBadgeCache() {
    sidebar.querySelectorAll('[data-sidebar-badge-slot]').forEach(function (el) {
      const key = el.dataset.sidebarBadgeSlot;
      const existing = el.querySelector('.gl-sidebar-badge');
      _badgeCache[key] = existing ? parseInt(existing.textContent.trim(), 10) || 0 : 0;
    });
  }

  /** The count, as the app's badge (GitLab's nav item pill: GlBadge, muted). */
  function _createBadgeEl(count) {
    const holder = document.createElement('template');
    holder.innerHTML = GP.badgeHtml(count > 999 ? '999+' : String(count), 'muted', { size: 'sm', class: 'gl-sidebar-badge' });
    return holder.content.firstElementChild;
  }

  /** Update a single badge: create, update, or remove */
  function _updateBadge(key, newCount) {
    const slot = sidebar.querySelector('[data-sidebar-badge-slot="' + key + '"]');
    if (!slot) return;

    const oldCount = _badgeCache[key] || 0;
    if (oldCount === newCount) return;

    _badgeCache[key] = newCount;
    let el = slot.querySelector('.gl-sidebar-badge');

    if (newCount > 0) {
      if (!el) {
        // Create badge element - it didn't exist in the DOM
        el = _createBadgeEl(newCount);
        slot.appendChild(el);
      } else {
        el.textContent = newCount > 999 ? '999+' : String(newCount);
      }

      /* One pop for every badge in the app. As a CSS class this needed the
         remove / reflow / re-add dance to replay, an `animationend` listener to
         clean up after itself, and it ran on a different easing here than the
         identical rule in animations.css - the same badge popped differently
         depending on which one won. */
      GP.motion.pop(el);

      // Update tooltip if sidebar collapsed
      if (slot._tippy && sidebar.classList.contains('collapsed')) {
        const textEl = slot.querySelector('.gl-sidebar-item-text');
        const label = textEl ? textEl.textContent.trim() : '';
        slot._tippy.setContent(label + ' (' + newCount + ')');
      }
    } else if (el) {
      // Remove badge entirely - no element, no circle, nothing
      el.remove();
    }
  }

  /** Fetch sidebar badges from API and update */
  let _pollBadgesLastAt = 0;
  let _pollBadgesThrottleTimer = null;
  const _POLL_BADGES_MIN_INTERVAL_MS = 500;
  async function _pollBadges() {
    // Skip polling when tab is hidden to save network/battery
    if (document.visibilityState === 'hidden') return;
    // Coalescing (the burst of duplicate /dashboard/sidebar-badges calls when
    // the dashboard SSE emits an update right after the load-time fetch) is
    // GP.coalesce's job below. The throttle in front of it is this poller's
    // own, and gates only NEW calls - a coalesced trailing run is already a
    // round-trip behind the one it followed.
    // Throttle: enforce a minimum interval between fetches so bursts
    // from SSE update + htmx swap + visibilitychange collapse into one.
    const sinceLast = Date.now() - _pollBadgesLastAt;
    if (sinceLast < _POLL_BADGES_MIN_INTERVAL_MS) {
      if (_pollBadgesThrottleTimer) return;
      _pollBadgesThrottleTimer = setTimeout(() => {
        _pollBadgesThrottleTimer = null;
        _pollBadges();
      }, _POLL_BADGES_MIN_INTERVAL_MS - sinceLast);
      return;
    }
    _pollBadgesLastAt = Date.now();
    return GP.coalesced('sidebar-badges', async () => {
      try {
        const data = await GP.apiCall('/dashboard/sidebar-badges', 'GET', null, { key: 'sidebar-badges', maxRetries: 0 });
        _badgePollFailCount = 0;

        // Update every known badge key
        Object.keys(data).forEach(function (key) {
          _updateBadge(key, data[key] || 0);
        });

        // Also hide badges that were removed from the response
        Object.keys(_badgeCache).forEach(function (key) {
          if (!(key in data)) {
            _updateBadge(key, 0);
          }
        });
      } catch (err) {
        _badgePollFailCount++;
        if (_badgePollFailCount >= MAX_BADGE_POLL_FAILURES) {
          _stopBadgePolling();
        }
      }
    });
  }

  /** Connect to SSE for real-time badge updates */
  function _connectBadgeSSE() {
    _disconnectBadgeSSE();
    _badgeSSE = GP.sse({
      url: '/api/v1/dashboard/stream',
      maxErrors: _BADGE_SSE_MAX_ERRORS,
      events: {
        connected: function () {},
        update: function (ev) {
          _pollBadges();
          // This connection is live on every page except the dashboard (which
          // takes it over), so announcing here is what gives the rest of the
          // app the same "why did this just change" feedback.
          GP.announceLiveUpdate(ev);
          // Notify all pages that backend data changed (sync, webhook, metrics).
          window.dispatchEvent(new CustomEvent('gp:data-changed'));
        },
      },
      onFailure: function (n) {
        // Trigger immediate health check on first SSE failure
        if (n === 1 && window.GP?.health?.check) window.GP.health.check();
      },
      onGiveUp: _startBadgePolling,
      onBlocked: _startBadgePolling,
    });
  }

  function _disconnectBadgeSSE() {
    if (_badgeSSE) { _badgeSSE.close(); _badgeSSE = null; }
  }

  /** Start badge polling - fallback only when SSE unavailable */
  function _startBadgePolling() {
    if (_badgePollTimer) return;
    _initBadgeCache();
    _pollBadges();
    _badgePollTimer = setInterval(_pollBadges, BADGE_POLL_INTERVAL);
  }

  /** Stop badge polling */
  function _stopBadgePolling() {
    if (_badgePollTimer) {
      clearInterval(_badgePollTimer);
      _badgePollTimer = null;
    }
  }

  /** Visibility API: pause polling and disconnect SSE when hidden */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      _stopBadgePolling();
      _disconnectBadgeSSE();
    } else {
      _badgePollFailCount = 0;
      _badgeSSE?.resetErrors();
      _initBadgeCache();
      _pollBadges();
      // Reconnect only if the connection was lost (e.g. server idle-timeout).
      if (!_badgeSSE) _connectBadgeSSE();
    }
  });

  // Start SSE-first on page load
  if (sidebar.querySelectorAll('[data-sidebar-badge-slot]').length > 0) {
    _initBadgeCache();
    _pollBadges();
    _connectBadgeSSE();
  }

  window.addEventListener('beforeunload', function () {
    _disconnectBadgeSSE();
    _stopBadgePolling();
  });

  // Pause SSE & polling when backend is unreachable
  let _sidebarHealthDown = false;
  document.addEventListener('gp-health-change', function (e) {
    const detail = e.detail || {};
    if (detail.current === 'down' && !_sidebarHealthDown) {
      _sidebarHealthDown = true;
      _disconnectBadgeSSE();
      _stopBadgePolling();
    } else if (detail.current !== 'down' && _sidebarHealthDown) {
      _sidebarHealthDown = false;
      _badgeSSE?.resetErrors();
      _badgePollFailCount = 0;
      _connectBadgeSSE();
    }
  });

  // Auto-refresh sidebar badges when any global job completes or fails
  window.addEventListener('gp:job-complete', function(e) {
    if (e.detail?.status === 'done' || e.detail?.status === 'error') {
      _pollBadges();
    }
  });

  /* -- Public API -- */
  window.GP = window.GP || {};
  GP.refreshSidebarBadges = _pollBadges;

  // Internal API used by dashboard.js to avoid opening a duplicate SSE
  // connection to the same /api/v1/dashboard/stream endpoint.
  // When the dashboard page is loaded, dashboard.js calls
  // GP._sidebar.takeover() to close our SSE and drive badge polls itself.
  // When dashboard SSE falls back to polling or is destroyed, it calls
  // GP._sidebar.release() to hand control back here.
  GP._sidebar = {
    pollBadges: _pollBadges,
    takeover: function () {
      _disconnectBadgeSSE();
      _stopBadgePolling();
    },
    release: function () {
      _badgeSSE?.resetErrors();
      _badgePollFailCount = 0;
      _connectBadgeSSE();
    },
  };
})();
