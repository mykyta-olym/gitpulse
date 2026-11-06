  // -- SSE-first live dashboard updates (polling is fallback) --
  let _dashSSE = null;
  let _dashPollTimer = null;
  // Fix G: track whether this is the first SSE connection on this page load.
  // The page was just rendered by the server so the initial `connected` event
  // carries no new data - skip the redundant refresh on first connect only.
  let _dashConnectedOnce = false;
  const _DASH_SSE_MAX_ERRORS = GP.SSE_MAX_ERRORS || 5;
  const _DASH_POLL_INTERVAL = 30000;

  function _handBadgesBack() {
    // Permanent fallback - hand badge SSE back to sidebar.js.
    window.GP?._sidebar?.release();
    _startDashboardPolling();
  }

  function _connectDashboardSSE() {
    _disconnectDashboardSSE();
    _dashSSE = GP.sse({
      url: '/api/v1/dashboard/stream',
      maxErrors: _DASH_SSE_MAX_ERRORS,
      beforeConnect: function () {
        // sidebar.js also connects to the same /api/v1/dashboard/stream
        // endpoint for badge updates. On the dashboard page we manage that
        // single SSE and drive badge polls from it, so we ask sidebar to
        // release its own connection first.
        window.GP?._sidebar?.takeover();
      },
      events: {
        connected: function () {
          // Fix G: first connect after page render - server just gave us fresh
          // data, so skip the duplicate refresh.  All reconnects DO refresh
          // because data may have changed while the SSE was disconnected.
          if (!_dashConnectedOnce) {
            _dashConnectedOnce = true;
            return;
          }
          refreshDashboardLive({ includeSidebar: true });
        },
        update: function (ev) {
          // Any dashboard SSE update means data changed - refresh everything
          refreshDashboardLive({ includeSidebar: true });
          GP.announceLiveUpdate?.(ev);
          // Notify other components via the
          // same event that badge SSE would have dispatched.
          window.dispatchEvent(new CustomEvent('gp:data-changed'));
        },
      },
      onGiveUp: _handBadgesBack,
      onBlocked: _handBadgesBack,
    });
  }

  function _disconnectDashboardSSE() {
    if (_dashSSE) { _dashSSE.close(); _dashSSE = null; }
  }

  function _startDashboardPolling() {
    if (_dashPollTimer) return;
    _dashPollTimer = setInterval(() => {
      if (document.visibilityState === 'visible') {
        refreshDashboardLive();
      }
    }, _DASH_POLL_INTERVAL);
  }

  if (_pageConfig.hasCourses) {
    _connectDashboardSSE();
  }

  const onTabVisible = () => {
    if (!_dashSSE?.active && !_dashPollTimer && _pageConfig.hasCourses) {
      _connectDashboardSSE();
    }
  };

  const onVisibilityChange = () => {
    if (document.visibilityState === 'hidden') {
      _disconnectDashboardSSE();
      if (_dashPollTimer) {
        clearInterval(_dashPollTimer);
        _dashPollTimer = null;
      }
      return;
    }
    const _needsReconnect = !_dashSSE?.active && !_dashPollTimer && _pageConfig.hasCourses;
    if (!_needsReconnect) {
      refreshDashboardLive({ includeSidebar: Boolean(_dashSSE?.active) });
    }
    if (_needsReconnect) {
      _connectDashboardSSE();
    }
  };

  let _dashHealthDown = false;
  const onHealthChange = (e) => {
    if (e.detail?.current === 'down' && !_dashHealthDown) {
      _dashHealthDown = true;
      _disconnectDashboardSSE();
      if (_dashPollTimer) { clearInterval(_dashPollTimer); _dashPollTimer = null; }
    } else if (e.detail?.current !== 'down' && _dashHealthDown) {
      _dashHealthDown = false;
      if (_pageConfig.hasCourses) _connectDashboardSSE();
    }
  };

  const onBeforeUnload = () => {
    _disconnectDashboardSSE();
    if (_dashPollTimer) clearInterval(_dashPollTimer);
  };

  const onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.classList.contains('gl-page-content') || target.querySelector('#gp-dashboard-config') || target.id === 'gp-dashboard-config')) {
      GP.dashboardCleanup();
    }
  };

  document.addEventListener('gp-tab-visible', onTabVisible);
  document.addEventListener('visibilitychange', onVisibilityChange);
  document.addEventListener('gp-health-change', onHealthChange);
  window.addEventListener('beforeunload', onBeforeUnload);
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.dashboardCleanup = function () {
    _importHandle.destroy();
    _disconnectDashboardSSE();
    if (_dashPollTimer) { clearInterval(_dashPollTimer); _dashPollTimer = null; }
    window.GP?._sidebar?.release();

    document.removeEventListener('gp-tab-visible', onTabVisible);
    document.removeEventListener('visibilitychange', onVisibilityChange);
    document.removeEventListener('gp-health-change', onHealthChange);
    window.removeEventListener('beforeunload', onBeforeUnload);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);

    // From 00-core.js
    if (onVisibilityChangeGreeting) {
      document.removeEventListener('visibilitychange', onVisibilityChangeGreeting);
    }
    if (onKeydownShortcuts) {
      document.removeEventListener('keydown', onKeydownShortcuts);
    }
    window.removeEventListener('hashchange', _handleDashboardNavigation);

    // From 10-course-crud.js
    document.body.removeEventListener('htmx:afterSettle', _registerCourseCardSyncs);
    document.body.removeEventListener('htmx:afterSettle', _wireDatePickers);
    document.body.removeEventListener('htmx:afterSettle', _bootAutofill);

    // From 20-live-updates.js
    if (onJobUpdateLive) {
      window.removeEventListener('gp:job-update', onJobUpdateLive);
    }
    if (onJobCompleteLive) {
      window.removeEventListener('gp:job-complete', onJobCompleteLive);
    }
    if (onVisibilityChangeLive) {
      document.removeEventListener('visibilitychange', onVisibilityChangeLive);
    }
  };

  GP.activePageCleanup = GP.dashboardCleanup;
