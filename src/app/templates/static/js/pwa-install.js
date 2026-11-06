/* ------------------------------------------------------------------
 *  pwa-install.js - Progressive Web App install prompt (GitLab-style)
 *
 *  Features:
 *    * Captures beforeinstallprompt and renders a polished card
 *    * Smooth fade+lift enter/exit animations (respects prefers-reduced-motion)
 *    * Multi-tab synchronisation via BroadcastChannel + localStorage fallback
 *    * Conflict-aware: hides while cookie banner, tour welcome card, modal
 *      overlays, or app loader are visible; auto-reshow once they go away
 *    * Pauses scheduling while the tab is hidden (visibilitychange)
 *    * Escape key dismisses without persisting (so user can re-trigger)
 * ------------------------------------------------------------------ */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  // -- Constants -----------------------------------------------------
  const DISMISS_KEY        = 'gp_pwa_install_dismissed_until';
  const INSTALLED_KEY      = 'gp_pwa_installed';
  const SYNC_KEY           = 'gp_pwa_install_sync';
  const CHANNEL_NAME       = 'gp_pwa_install';
  const DISMISS_DAYS       = 90;
  const SHOW_DELAY_MS      = 4000;
  const CONFLICT_POLL_MS   = 800;
  const HIDE_TRANSITION_MS = 220;
  const PRM = (() => {
    try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; }
    catch (_) { return false; }
  })();

  // -- State ---------------------------------------------------------
  let deferredPrompt = null;
  let rootEl         = null;
  let shownOnce      = false;
  let _hideTimer     = null;
  let _showTimer     = null;
  let _conflictTimer = null;
  let bc             = null;
  let listenersBound = false;
  let installedKnown = false;

  // -- Helpers -------------------------------------------------------
  const _isStandalone = () => {
    try {
      if (window.matchMedia?.('(display-mode: standalone)').matches) return true;
      if (window.matchMedia?.('(display-mode: minimal-ui)').matches) return true;
      if (window.navigator?.standalone === true) return true;
    } catch (_) { /* noop */ }
    return false;
  };

  const _hasInstalledMarker = () => {
    try { return localStorage.getItem(INSTALLED_KEY) === '1'; }
    catch (_) { return false; }
  };

  const _markInstalled = () => {
    installedKnown = true;
    try { localStorage.setItem(INSTALLED_KEY, '1'); } catch (_) { /* noop */ }
  };

  const _clearInstalledMarker = () => {
    installedKnown = false;
    try { localStorage.removeItem(INSTALLED_KEY); } catch (_) { /* noop */ }
  };

  const _isInstalled = () => installedKnown || _isStandalone() || _hasInstalledMarker();
  const _customPromptEnabled = () => {
    try {
      return window.GP?.config?.customPwaInstallPrompt === true
        || document.documentElement?.dataset?.customPwaInstall === 'true';
    } catch (_) {
      return false;
    }
  };

  const _detectInstalled = async () => {
    if (_isStandalone()) {
      _markInstalled();
      return true;
    }
    if (typeof navigator.getInstalledRelatedApps !== 'function') {
      return _hasInstalledMarker();
    }
    try {
      const apps = await navigator.getInstalledRelatedApps();
      const installed = Array.isArray(apps) && apps.some((app) => app?.platform === 'webapp');
      if (installed) {
        _markInstalled();
      } else {
        _clearInstalledMarker();
      }
      return installed;
    } catch (_) {
      return _hasInstalledMarker();
    }
  };

  let installedCheck = _detectInstalled();

  const _isDismissed = () => {
    try {
      const until = parseInt(localStorage.getItem(DISMISS_KEY) || '0', 10);
      return Number.isFinite(until) && until > Date.now();
    } catch (_) {
      return false;
    }
  };

  const _markDismissed = (days = DISMISS_DAYS) => {
    try {
      const ms = days * 24 * 60 * 60 * 1000;
      localStorage.setItem(DISMISS_KEY, String(Date.now() + ms));
    } catch (_) { /* noop */ }
  };

  const _clearDismissed = () => {
    try { localStorage.removeItem(DISMISS_KEY); } catch (_) { /* noop */ }
  };

  /* The catalogue is keyed by the English source text, like every other
     string in the app - the dotted keys this used to look up never matched,
     so the card was English on a Slovak page. */
  const _t = (text) => {
    try {
      const t = window.GP?.i18n?.t || window.GP?.t;
      if (typeof t === 'function') {
        const v = t(text);
        if (v) return v;
      }
    } catch (_) { /* noop */ }
    return text;
  };

  /**
   * Detect overlay/onboarding conflicts. We deliberately *defer* showing
   * the install card when something more important is on-screen so the
   * UI never stacks two attention-grabbing prompts.
   */
  const _conflictPresent = () => {
    const cookie = document.getElementById('cookieConsent');
    if (cookie && !cookie.classList.contains('d-none') && cookie.offsetParent !== null) return true;
    if (document.querySelector('.gp-tour-welcome')) return true;
    if (document.querySelector('.driver-active, .driver-popover')) return true;
    if (document.querySelector('.modal.show, .gl-modal-overlay:not([hidden])')) return true;
    if (document.querySelector('.gp-app-loader.is-visible')) return true;
    return false;
  };

  // -- Card DOM factory ----------------------------------------------
  const _createCard = () => {
    const card = document.createElement('div');
    card.className = 'gp-pwa-install';
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'false');
    card.setAttribute('aria-labelledby', 'gp-pwa-install-title');
    card.setAttribute('aria-describedby', 'gp-pwa-install-desc');
    card.hidden = true;

    const icon = document.createElement('div');
    icon.className = 'gp-pwa-install__icon';
    const iconImg = document.createElement('img');
    iconImg.src = '/static/img/icons/icon-96x96.png';
    iconImg.alt = '';
    iconImg.width = 48;
    iconImg.height = 48;
    iconImg.loading = 'lazy';
    iconImg.decoding = 'async';
    icon.appendChild(iconImg);

    const body = document.createElement('div');
    body.className = 'gp-pwa-install__body';

    const title = document.createElement('div');
    title.id = 'gp-pwa-install-title';
    title.className = 'gp-pwa-install__title';
    title.textContent = _t('Install GitPulse');

    const desc = document.createElement('div');
    desc.id = 'gp-pwa-install-desc';
    desc.className = 'gp-pwa-install__desc';
    desc.textContent = _t(
      'Install this app on your device for a faster, full-screen experience with quick access from your home screen.'
    );

    body.appendChild(title);
    body.appendChild(desc);

    const actions = document.createElement('div');
    actions.className = 'gp-pwa-install__actions';

    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'gp-pwa-install__btn gp-pwa-install__btn--ghost';
    cancelBtn.textContent = _t('Not now');

    const installBtn = document.createElement('button');
    installBtn.type = 'button';
    installBtn.className = 'gp-pwa-install__btn gp-pwa-install__btn--primary';
    installBtn.textContent = _t('Install');

    actions.appendChild(cancelBtn);
    actions.appendChild(installBtn);

    const closeHolder = document.createElement('template');
    closeHolder.innerHTML = GP.closeButtonHtml(_t('Close'), 'gp-pwa-install__close');
    const closeBtn = closeHolder.content.firstElementChild;

    card.appendChild(closeBtn);
    card.appendChild(icon);
    card.appendChild(body);
    card.appendChild(actions);

    cancelBtn.addEventListener('click', () => _dismissAndBroadcast(true));
    closeBtn.addEventListener('click',  () => _dismissAndBroadcast(true));
    installBtn.addEventListener('click', _triggerInstall);

    return card;
  };

  const _ensureRoot = () => {
    if (rootEl && document.body.contains(rootEl)) return rootEl;
    rootEl = _createCard();
    document.body.appendChild(rootEl);
    return rootEl;
  };

  // -- Show / Hide ---------------------------------------------------
  const _show = () => {
    if (_isInstalled() || _isDismissed() || !deferredPrompt) return;
    if (_conflictPresent()) {
      if (_conflictTimer === null) {
        _conflictTimer = setTimeout(() => {
          _conflictTimer = null;
          _show();
        }, CONFLICT_POLL_MS);
      }
      return;
    }
    if (_hideTimer !== null) {
      clearTimeout(_hideTimer);
      _hideTimer = null;
    }
    const el = _ensureRoot();
    el.hidden = false;
    void el.offsetHeight; // force reflow for transition
    el.classList.add('is-visible');
    shownOnce = true;
  };

  const _hide = (persistDismiss) => {
    if (!rootEl) return;
    rootEl.classList.remove('is-visible');
    clearTimeout(_hideTimer);
    _hideTimer = setTimeout(() => {
      if (rootEl) rootEl.hidden = true;
      _hideTimer = null;
    }, PRM ? 0 : HIDE_TRANSITION_MS);
    if (persistDismiss) _markDismissed();
  };

  const _dismissAndBroadcast = (persist) => {
    _hide(persist);
    _broadcast(persist ? 'dismiss' : 'hide');
  };

  // -- Cross-tab synchronisation -------------------------------------
  const _broadcast = (kind) => {
    try { bc?.postMessage({ kind, t: Date.now() }); } catch (_) { /* noop */ }
    try {
      localStorage.setItem(SYNC_KEY, JSON.stringify({ kind, t: Date.now() }));
    } catch (_) { /* noop */ }
  };

  const _onPeerMessage = (kind) => {
    if (kind === 'dismiss' || kind === 'hide' || kind === 'installed') {
      if (kind === 'installed') {
        deferredPrompt = null;
        _markInstalled();
      }
      _hide(false);
    } else if (kind === 'reset') {
      _clearDismissed();
    }
  };

  // -- Native install trigger ----------------------------------------
  const _triggerInstall = async () => {
    if (!deferredPrompt) { _hide(false); return; }
    const prompt = deferredPrompt;
    deferredPrompt = null;
    try {
      const result = await prompt.prompt();
      const outcome = result?.outcome
        ?? (await prompt.userChoice?.catch(() => null))?.outcome;
      if (outcome === 'dismissed') {
        _markDismissed();
        _broadcast('dismiss');
      } else if (outcome === 'accepted') {
        _broadcast('installed');
      }
    } catch (_) { /* user may have already been prompted */ }
    _hide(false);
  };

  // -- Wire-up event listeners (idempotent) --------------------------
  const _bindListeners = () => {
    if (listenersBound) return;
    listenersBound = true;

    window.addEventListener('beforeinstallprompt', async (ev) => {
      if (!_customPromptEnabled()) {
        deferredPrompt = null;
        return;
      }
      // Keep the browser's install promotion available; the saved event can
      // still open the native dialog from the card's Install button.
      if (await installedCheck) return;
      installedCheck = _detectInstalled();
      if (await installedCheck) return;
      deferredPrompt = ev;
      ev.userChoice?.then(() => {
        // The browser can complete its own prompt before our card is used.
        if (deferredPrompt !== ev) return;
        deferredPrompt = null;
        clearTimeout(_showTimer);
        _hide(false);
      }).catch(() => {});
      if (_isInstalled() || _isDismissed()) return;
      clearTimeout(_showTimer);
      _showTimer = setTimeout(_show, shownOnce ? 0 : SHOW_DELAY_MS);
    });

    window.addEventListener('appinstalled', () => {
      deferredPrompt = null;
      _markInstalled();
      _clearDismissed();
      _hide(false);
      _broadcast('installed');
    });

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        clearTimeout(_showTimer);
      } else if (deferredPrompt && !_isInstalled() && !_isDismissed()) {
        clearTimeout(_showTimer);
        _showTimer = setTimeout(_show, 600);
      }
    });

    // Re-evaluate after overlay components emit their close events.
    window.addEventListener('gp:cookie-consent',          () => deferredPrompt && _show());
    window.addEventListener('gp:tour:welcome:dismissed',  () => deferredPrompt && _show());
    window.addEventListener('gp:modal:close',             () => deferredPrompt && _show());

    document.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape' && rootEl && rootEl.classList.contains('is-visible')) {
        _hide(false);
      }
    });

    try {
      bc = new BroadcastChannel(CHANNEL_NAME);
      bc.addEventListener('message', (ev) => {
        if (ev?.data?.kind) _onPeerMessage(ev.data.kind);
      });
    } catch (_) { /* BroadcastChannel unsupported - storage event still works */ }

    window.addEventListener('storage', (ev) => {
      if (ev.key === SYNC_KEY && ev.newValue) {
        try {
          const payload = JSON.parse(ev.newValue);
          if (payload?.kind) _onPeerMessage(payload.kind);
        } catch (_) { /* noop */ }
      }
      if (ev.key === DISMISS_KEY && rootEl?.classList.contains('is-visible')) {
        if (_isDismissed()) _hide(false);
      }
    });

    window.addEventListener('pagehide', () => {
      try { bc?.close(); } catch (_) { /* noop */ }
    });
  };

  _bindListeners();

})();
