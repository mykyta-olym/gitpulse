/**
 * Global Health Monitor - production-grade system health tracking.
 *
 * Features:
 * - Periodic background health polling with adaptive intervals
 * - Sticky banner for degraded/down states with animated entry/exit
 * - Page-visibility-aware polling (pause when hidden, immediate check on return)
 * - Network online/offline awareness
 * - Exponential back-off on consecutive failures
 * - Broadcasts health state changes via custom events
 * - Provides global API for admin dashboard and other consumers
 *
 * Usage from other modules:
 *   window.GP.health.check()           - force an immediate check
 *   document.addEventListener('gp-health-change', e => { ... })
 */
(function initHealthMonitor() {
  'use strict';

  const GP = window.GP;
  const _serviceStatus = document.getElementById('serviceNoticeBanner');
  const _serviceTextEl = document.getElementById('serviceNoticeText');
  const _serviceActionEl = document.getElementById('serviceNoticeAction');
  let _serviceText = '';
  let _serviceActionHref = '';
  let _serviceActionLabel = '';
  let _serviceVisible = false;
  function _renderServiceNotice() {
    if (!_serviceStatus) return;
    const shouldShow = !!_serviceText && !document.getElementById('systemMonitoringResults');
    if (_serviceTextEl && _serviceTextEl.textContent !== _serviceText) {
      _serviceTextEl.textContent = _serviceText;
    }
    if (_serviceActionEl) {
      if (_serviceActionHref && _serviceActionLabel) {
        _serviceActionEl.href = _serviceActionHref;
        _serviceActionEl.textContent = _serviceActionLabel;
        _serviceActionEl.hidden = false;
      } else {
        _serviceActionEl.removeAttribute('href');
        _serviceActionEl.textContent = '';
        _serviceActionEl.hidden = true;
      }
    }
    if (shouldShow && !_serviceVisible) {
      _serviceStatus.hidden = false;
      _serviceVisible = true;
      GP.motion.disclose(_serviceStatus, true);
    } else if (!shouldShow && _serviceVisible) {
      _serviceVisible = false;
      if (document.getElementById('systemMonitoringResults')) {
        _serviceStatus.hidden = true;
        GP.motion.settle(_serviceStatus, 'display');
      } else {
        GP.motion.disclose(_serviceStatus, false, function () {
          if (!_serviceVisible && _serviceStatus) {
            _serviceStatus.hidden = true;
            GP.motion.settle(_serviceStatus, 'display');
          }
        });
      }
    }
  }
  window.addEventListener('gp:page-ready', _renderServiceNotice);
  const { t } = GP;

  /* -- Configuration -- */
  const POLL_OK_MS      = 30000;  // 30s when healthy
  const POLL_DEGRADED_MS = 10000; // 10s when degraded
  const POLL_DOWN_MS     = 3000;  // 3s when down
  const INITIAL_DELAY_MS = 500;   // First check 0.5s after page load
  const FAIL_THRESHOLD   = 3;     // Show banner after 3 consecutive failures
  const MAX_BACKOFF_MS   = 30000; // Max polling interval on repeated failures
  const CHECK_TIMEOUT_MS = 5000;  // Abort health check after 5s

  /* -- State -- */
  const _state = {
    status: 'unknown',    // 'ok' | 'degraded' | 'down' | 'unknown'
    version: '',
    environment: '',
    uptime: '',
    uptimeSeconds: 0,
    components: {},
    checksDuration: 0,
    lastCheck: null,      // Date
    lastOk: null,         // Date
    consecutiveFails: 0,
    raw: null,            // full API response
  };

  let _timerId = null;
  let _metaTimerId = null;  // refresh "Last healthy: Xs ago" text
  let _bannerDismissed = false;
  let _bannerVisible = false;

  /* -- DOM refs (lazy) -- */
  let _banner = null;
  let _bannerIcon = null;
  let _bannerText = null;
  let _bannerMeta = null;
  let _bannerDismissBtn = null;

  function _refs() {
    if (!_banner) {
      _banner = document.getElementById('healthGlobalBanner');
      _bannerIcon = document.getElementById('healthBannerIcon');
      _bannerText = document.getElementById('healthBannerText');
      _bannerMeta = document.getElementById('healthBannerMeta');
      _bannerDismissBtn = document.getElementById('healthBannerDismiss');
      if (_bannerDismissBtn) {
        if (!_bannerDismissBtn.innerHTML.trim()) {
          _bannerDismissBtn.innerHTML = _icon('x', 14);
        }
        _bannerDismissBtn.addEventListener('click', _dismissBanner);
      }
    }
  }

  /* -- Icons (from central registry) -- */
  function _icon(name, size) {
    return GP.icons.get(name, size || 16);
  }

  /* -- Banner management -- */
  function _showBanner(status) {
    _refs();
    if (!_banner) return;
    if (_bannerDismissed && status !== 'offline') return;

    // If the GitLab banner was visible, reset its flag - this banner takes precedence.
    if (_glBannerVisible) _glBannerVisible = false;

    let cls, icon, text;
    if (status === 'offline') {
      cls = 'health-global-banner--offline';
      icon = _icon('wifi-off', 16) || _icon('alert-triangle', 16);
      text = t("You're offline. Some features may be unavailable until your connection is restored.");
    } else if (status === 'degraded') {
      cls = 'health-global-banner--degraded';
      icon = _icon('alert-triangle', 16);
      text = t('System is experiencing degraded performance. Some services may be slow.');
    } else {
      cls = 'health-global-banner--down';
      icon = _icon('x-circle', 16);
      // navigator.onLine reports "online" on a Wi-Fi-without-internet network,
      // so a failed health check is often the user's own connection, not a
      // server outage. Keep the wording neutral instead of promising "we're
      // working to restore service" for something that may be on their end.
      text = t("Can't reach GitPulse - check your internet connection. We'll keep retrying.");
    }

    _banner.className = 'health-global-banner ' + cls;
    const _arriving = !_bannerVisible;
    _banner.hidden = false;

    if (_bannerIcon) _bannerIcon.innerHTML = icon;
    if (_bannerText) _bannerText.textContent = text;
    _updateBannerMeta();
    _startMetaRefresh();

    /* The strip pushes the page down, so it opens its HEIGHT rather than
       fading in place - the same disclosure contract as a collapsible card, so
       the content below eases down instead of being shoved. Only on arrival: a
       banner that is already up and merely changing its wording must not
       re-animate. */
    if (_arriving) GP.motion.disclose(_banner, true);
    _bannerVisible = true;
  }

  /** Refresh the "Last ...: Xs ago" text for whichever banner is on screen.
   *  The GitLab banner (shown only when the app-health banner is not) tracks
   *  its own "Last connected" time; the app-health banner tracks "Last healthy".
   *  Both need the same live-ticking refresh so the age never freezes. */
  function _updateBannerMeta() {
    _refs();
    if (!_bannerMeta) return;
    if (_glBannerVisible && !_bannerVisible) {
      _bannerMeta.textContent = _glState.lastOk
        ? t('Last connected') + ': ' + _formatAgo(_glState.lastOk)
        : '';
    } else if (_state.lastOk) {
      _bannerMeta.textContent = t('Last healthy') + ': ' + _formatAgo(_state.lastOk);
    } else {
      _bannerMeta.textContent = '';
    }
  }

  /** Keep refreshing the meta text every 5s while the banner is visible. */
  function _startMetaRefresh() {
    _stopMetaRefresh();
    _metaTimerId = setInterval(_updateBannerMeta, 5000);
  }

  function _stopMetaRefresh() {
    if (_metaTimerId) { clearInterval(_metaTimerId); _metaTimerId = null; }
  }

  function _hideBanner() {
    _refs();
    if (!_banner || !_bannerVisible) return;

    _stopMetaRefresh();
    GP.motion.disclose(_banner, false, function () {
      if (_banner) {
        _banner.hidden = true;
        GP.motion.settle(_banner, 'display');
      }
      _bannerVisible = false;
    });
  }

  function _dismissBanner() {
    // Dismiss ONLY the banner that is actually on screen, and remember that
    // choice per-banner. The app-health banner and the GitLab banner share
    // one DOM strip but have independent lifecycles: the app can be perfectly
    // healthy while GitLab is unreachable. A single shared "dismissed" flag
    // used to get cleared by the next successful /health poll (~30s), which
    // silently revived a GitLab banner the user had just closed.
    if (_glBannerVisible && !_bannerVisible) {
      _glBannerDismissed = true;
      _hideGlBanner(false);
    } else {
      _bannerDismissed = true;
      _hideBanner();
    }
  }

  /* -- Format helpers -- */
  function _formatAgo(date) {
    if (!date) return '';
    const secs = Math.floor((Date.now() - date.getTime()) / 1000);
    if (secs < 10) return t('just now');
    /* The whole phrase goes to t(), not `n + 's ' + t('ago')`. Slovak puts
       "pred" FIRST, so the concatenation rendered "11s pred" - the number was
       right and the sentence was not. A placeholder lets each locale put the
       number where its own grammar wants it. */
    if (secs < 60) return t('{n}s ago', { n: secs });
    if (secs < 3600) return t('{n}m ago', { n: Math.floor(secs / 60) });
    return t('{n}h ago', { n: Math.floor(secs / 3600) });
  }

  let _checking = false;  // Prevent concurrent /health fetches

  /* -- Health check -- */
  async function _performCheck() {
    if (_checking) return;
    if (document.hidden) {
      _schedule(_getInterval(_state.status));
      return;
    }
    let controller = null;
    let timeoutId = null;

    // Don't check if browser is offline - report as offline, not server-down
    if (navigator.onLine === false) {
      const prevStatus = _state.status;
      _state.status = 'offline';
      _state.lastCheck = new Date();
      _showBanner('offline');
      if (prevStatus !== 'offline') _dispatch(prevStatus, 'offline');
      _schedule(POLL_DEGRADED_MS);
      return;
    }

    try {
      controller = new AbortController();
    } catch (_) { /* no AbortController */ }

    if (controller) {
      timeoutId = setTimeout(function () { controller.abort(); }, CHECK_TIMEOUT_MS);
    }

    _checking = true;
    try {
      const resp = await fetch('/health', {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
        signal: controller ? controller.signal : undefined,
        headers: { 'Accept': 'application/json' },
      });

      if (timeoutId) clearTimeout(timeoutId);

      if (!resp.ok) {
        _handleFailure('HTTP ' + resp.status);
        return;
      }

      const data = await resp.json();
      _handleSuccess(data);
    } catch (err) {
      if (timeoutId) clearTimeout(timeoutId);
      _handleFailure(err.name === 'AbortError' ? 'Timeout' : err.message);
    } finally {
      _checking = false;
    }
  }

  function _handleSuccess(data) {
    const prevStatus = _state.status;
    const newStatus = data.status || 'ok';

    _state.status = newStatus;
    _state.version = data.version || '';
    _state.environment = data.environment || '';
    _state.uptime = data.uptime_human || '';
    _state.uptimeSeconds = data.uptime_seconds || 0;
    _state.checksDuration = data.checks_duration_ms || 0;
    _state.components = data.components || {};
    _state.lastCheck = new Date();
    _state.raw = data;

    if (newStatus === 'ok') {
      _state.consecutiveFails = 0;
      _state.lastOk = new Date();
      _bannerDismissed = false; // allow future banners now that health recovered
      if (prevStatus !== 'ok' && prevStatus !== 'unknown' && _state.lastOk) {
        // Recovered - hide banner and notify user (only if we had a baseline)
        _hideBanner();
        if (window.showToast) {
          showToast(t('Connection restored'), 'success', 2500);
        }
      } else if (_bannerVisible) {
        // Ensure banner is hidden if status is ok
        _hideBanner();
      }
    } else {
      // Degraded or down from API
      _state.consecutiveFails = 0; // API responded, it's not a network failure
      if (newStatus === 'degraded' || newStatus === 'down') {
        _showBanner(newStatus);
      }
    }

    _dispatch(prevStatus, newStatus);
    _schedule(_getInterval(newStatus));
  }

  function _handleFailure(reason) {
    const prevStatus = _state.status;
    _state.consecutiveFails++;
    _state.lastCheck = new Date();

    if (_state.consecutiveFails >= FAIL_THRESHOLD) {
      _state.status = 'down';
      _showBanner('down');
    }

    if (prevStatus !== _state.status) {
      _dispatch(prevStatus, _state.status);
    }

    // Exponential back-off (first retry is fast to confirm the failure)
    const delay = _state.consecutiveFails <= 1
      ? 1500
      : Math.min(POLL_DOWN_MS * Math.pow(1.5, _state.consecutiveFails - 2), MAX_BACKOFF_MS);
    _schedule(delay);
  }

  function _getInterval(status) {
    switch (status) {
      case 'ok': return POLL_OK_MS;
      case 'degraded': return POLL_DEGRADED_MS;
      case 'down': return POLL_DOWN_MS;
      default: return POLL_OK_MS;
    }
  }

  /* -- Scheduling -- */
  function _schedule(delayMs) {
    if (_timerId) clearTimeout(_timerId);
    _timerId = setTimeout(_performCheck, delayMs);
  }

  /* -- Event dispatch -- */
  function _dispatch(prevStatus, newStatus) {
    try {
      document.dispatchEvent(new CustomEvent('gp-health-change', {
        detail: {
          previous: prevStatus,
          current: newStatus,
          state: Object.assign({}, _state),
        },
      }));
    } catch (_) { /* CustomEvent not supported */ }
  }

  /* -- Visibility/Network handlers -- */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      _stopMetaRefresh();
    } else {
      // Immediate check when tab becomes visible
      _schedule(500);
      _scheduleGl(1000);
      if (_bannerVisible || _glBannerVisible) {
        _updateBannerMeta();
        _startMetaRefresh();
      }
    }
  });

  window.addEventListener('online', function () {
    // Network came back - clear dismissal so user sees "restored" toast,
    // hide any offline banner immediately, and force a fresh check.
    _bannerDismissed = false;
    if (_state.status === 'offline') {
      _hideBanner();
      _state.status = 'unknown';
    }
    _schedule(800);
    _scheduleGl(1500);
    if (window.showToast) {
      try { showToast(t('Connection restored'), 'success', 2200); } catch (_) {}
    }
  });

  window.addEventListener('offline', function () {
    const prevStatus = _state.status;
    _state.status = 'offline';
    _state.consecutiveFails = 0;
    _bannerDismissed = false;
    _showBanner('offline');
    _dispatch(prevStatus, 'offline');
  });

  window.addEventListener('beforeunload', function () {
    if (_timerId) { clearTimeout(_timerId); _timerId = null; }
    if (_glTimerId) { clearTimeout(_glTimerId); _glTimerId = null; }
    _stopMetaRefresh();
  });

  /* -- GitLab health check -- */
  const GL_POLL_OK_MS   = 60000;  // 60s when GitLab is healthy
  const GL_POLL_DOWN_MS = 15000;  // 15s when GitLab is down
  const GL_FAIL_THRESHOLD = 3;    // Show banner after 3 consecutive failures
                                  // (~45s of sustained downtime - avoids
                                  // false-positives from brief network blips
                                  // or transient GitLab 502s while the
                                  // server is actually reachable).
  const _glState = { status: 'unknown', consecutiveFails: 0, lastOk: null, lastCheck: null, hasBaseline: false };
  let _glTimerId = null;
  let _glBannerVisible = false;
  let _glBannerDismissed = false;  // sticky per-banner dismissal (see _dismissBanner)
  let _glChecking = false;  // Prevent concurrent connectivity-report fetches

  async function _checkGitLab() {
    if (_glChecking) return;
    if (navigator.onLine === false) return;
    if (document.hidden) {
      _scheduleGl(GL_POLL_OK_MS);
      return;
    }
    _glChecking = true;
    let timeoutId = null;
    try {
      const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
      timeoutId = controller ? setTimeout(function () { controller.abort(); }, 6000) : null;
      const options = {
        method: 'GET', credentials: 'same-origin', cache: 'no-store',
        signal: controller ? controller.signal : undefined,
        headers: { 'Accept': 'application/json' },
      };
      // One visibility-aware scheduler; connectivity and monitoring retain
      // independent meanings and display components.
      const [connection, service] = await Promise.allSettled([
        fetch('/health/gitlab/status', options),
        _serviceStatus ? fetch('/api/v1/observability/status', options)
          .then(function (r) { return r.ok ? r.json() : null; }) : null,
      ]);
      if (_serviceStatus) {
        const data = service.status === 'fulfilled' ? service.value : null;
        const notices = data && data.state === 'degraded' && Array.isArray(data.notices) ? data.notices : [];
        _serviceText = notices.map(function (n) { return n.text; }).filter(Boolean).join(' ');
        const actionable = notices.find(function (n) { return n.action_href && n.action_label; });
        _serviceActionHref = actionable ? actionable.action_href : '';
        _serviceActionLabel = actionable ? actionable.action_label : '';
        // System already shows full monitoring details. Other pages expose
        // only the role-filtered impact notice, never worker data or logs.
        _renderServiceNotice();
      }
      const resp = connection.status === 'fulfilled' ? connection.value : null;
      const report = resp && resp.ok ? await resp.json() : null;
      if (report && report.status === 'ok') {
        _glState.consecutiveFails = 0;
        _glState.status = 'ok';
        _glState.lastCheck = new Date();
        _glState.lastOk = new Date();
        _glState.hasBaseline = true;
        // GitLab recovered - clear any earlier dismissal so a *future* outage
        // is allowed to surface a fresh banner.
        _glBannerDismissed = false;
        if (_glBannerVisible) _hideGlBanner(true);
        _scheduleGl(GL_POLL_OK_MS);
      } else {
        _glHandleFail();
      }
    } catch (_e) {
      _glHandleFail();
    } finally {
      if (timeoutId) clearTimeout(timeoutId);
      _glChecking = false;
    }
  }

  function _glHandleFail() {
    _glState.lastCheck = new Date();
    _glState.consecutiveFails++;
    if (!_glState.hasBaseline && !_glState.lastOk) {
      _scheduleGl(GL_POLL_DOWN_MS);
      return;
    }
    _glState.status = 'down';
    if (_glState.consecutiveFails >= GL_FAIL_THRESHOLD) _showGlBanner();
    _scheduleGl(GL_POLL_DOWN_MS);
  }

  function _showGlBanner() {
    _refs();
    if (!_banner || _glBannerDismissed || _glBannerVisible) return;
    if (!_glState.hasBaseline || !_glState.lastOk) return;
    // Only show GitLab banner if the main app banner is not visible
    if (_bannerVisible) return;
    _banner.className = 'health-global-banner health-global-banner--degraded';
    _banner.hidden = false;
    if (_bannerIcon) _bannerIcon.innerHTML = _icon('alert-triangle', 16);
    if (_bannerText) _bannerText.textContent = t('GitLab server is currently unreachable. Some features may be unavailable.');
    _glBannerVisible = true;
    // Route the "Last connected" text through the shared meta updater + its
    // 5s refresh so the age ticks live instead of freezing at the value it
    // happened to have the instant the banner first appeared.
    _updateBannerMeta();
    _startMetaRefresh();
  }

  function _hideGlBanner(notify) {
    _refs();
    if (!_banner || !_glBannerVisible) return;
    // Only hide (and stop the meta ticker) if the banner is still showing
    // GitLab content - the main health banner may have overwritten it.
    if (!_bannerVisible) {
      _banner.hidden = true;
      _stopMetaRefresh();
    }
    _glBannerVisible = false;
    // Toast only on a genuine recovery (notify=true), never on a manual
    // dismiss - and never when the main backend-health banner took over,
    // since a GitLab-only "restored" toast would be misleading while the
    // application itself may still be unreachable.
    if (notify && !_bannerVisible && window.showToast) {
      showToast(t('GitLab connection restored'), 'success', 2500);
    }
  }

  function _scheduleGl(ms) {
    if (_glTimerId) clearTimeout(_glTimerId);
    _glTimerId = setTimeout(_checkGitLab, ms);
  }

  /* -- Public API -- */
  GP.health = {
    check: function () { return _performCheck(); },
    /** Global flag - true when backend is unreachable (used by SSE/polling code) */
    get isDown() { return _state.status === 'down'; },
    get isGitLabDown() { return _glState.status === 'down' && _glState.consecutiveFails >= GL_FAIL_THRESHOLD; },
  };
  window.GP = GP;

  /* -- Start -- */
  _schedule(INITIAL_DELAY_MS);
  _scheduleGl(INITIAL_DELAY_MS + 1000);  // stagger GitLab check
})();
