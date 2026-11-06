/* Login page logic - cookie consent handled by /static/js/cookie-consent.js */
(function initLoginPage() {
  // Language switcher uses Alpine.js (loaded via script tag in login.html)

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () {});
  }

  function _removeLoginAlert(el) {
    if (!el || !el.parentNode) return;
    el.remove();
  }

  document.addEventListener('click', function (event) {
    const removeTrigger = event.target.closest('[data-remove-closest]');
    if (!removeTrigger) return;
    event.preventDefault();
    const selector = removeTrigger.dataset.removeClosest || '';
    const node = selector ? removeTrigger.closest(selector) : null;
    if (!node) return;
    const alertWrapper = node.classList.contains('login-auth-alert')
      ? node
      : node.closest('.login-auth-alert');
    if (alertWrapper && alertWrapper.closest('.login-alert-region')) {
      /* Leaves upward, the way it arrived. GP.motion honours reduced motion
         itself and calls back exactly once, replacing the manual media-query
         branch plus an `animationend` listener AND a 260 ms fallback that
         could both fire. */
      GP.motion.edgeOut(alertWrapper, -8, function () {
        _removeLoginAlert(alertWrapper);
      });
    } else {
      node.remove();
    }
  });

  function _ensureLoginAlertRegion() {
    let region = document.querySelector('.login-alert-region');
    if (region) return region;
    region = document.createElement('div');
    region.className = 'login-alert-region';
    region.setAttribute('aria-live', 'polite');
    // Insert inside the login card, above the heading - matches the
    // server-rendered placement in login.html so the alert layout is
    // identical regardless of trigger path.
    const card = document.querySelector('.login-card');
    const heading = card ? card.querySelector('.login-heading') : null;
    if (card && heading) {
      card.insertBefore(region, heading);
    } else if (card) {
      card.prepend(region);
    } else {
      document.body.prepend(region);
    }
    return region;
  }

  /** Show a GitLab-style login error without relying on the app toast bundle. */
  function _showLoginError(msg) {
    const existing = document.getElementById('loginInlineError') || document.getElementById('loginAuthError');
    if (existing) {
      existing.querySelector('.gitlab-alert-message').textContent = msg;
      // Shake to draw attention on re-trigger. One shared shake for the whole
      // app - restarting it needed a force-reflow and a self-removing listener.
      GP.motion.shake(existing);
      return;
    }

    const region = _ensureLoginAlertRegion();
    const alert = document.getElementById('loginErrorTemplate').content.firstElementChild.cloneNode(true);
    alert.querySelector('.gitlab-alert-message').textContent = msg;
    region.appendChild(alert);
    /* Same entrance as a server-rendered alert. This one used to arrive with no
       motion at all: the entrance lived on the `.login-auth-alert` class, and a
       CSS animation on a base selector only fires on first paint. */
    GP.motion.edgeIn(alert, -8);
  }

  // -- Role -> default username auto-fill --
  const _defaultUsernames = { admin: 'admin', teacher: 'teacher', student: 'student' };
  const _usernameInput = document.getElementById('username');
  const _roleRadios = document.querySelectorAll('input[name="role"]');
  let _userEdited = false;
  if (_usernameInput) {
    _usernameInput.addEventListener('input', function () {
      // Mark as manually edited if value doesn't match any default
      const val = _usernameInput.value.trim();
      const isDefault = Object.values(_defaultUsernames).indexOf(val) !== -1;
      _userEdited = !isDefault;
    });
  }
  _roleRadios.forEach(function (radio) {
    radio.addEventListener('change', function () {
      if (_usernameInput && !_userEdited) {
        _usernameInput.value = _defaultUsernames[radio.value] || radio.value;
      }
    });
  });

  // -- Login form validation + loading state --
  const loginForm = document.querySelector('form[action*="login"], form[action*="auth"], form.login-form');
  /** Status-code-aware error message resolver. */
  function _errorForStatus(status) {
    const t = (k, fb) => (window.GP?.t?.(k) || fb);
    if (status === 401 || status === 403) {
      return t('Invalid username or password.', 'Invalid username or password.');
    }
    if (status === 422) {
      return t('Please check the form and try again.', 'Please check the form and try again.');
    }
    if (status === 429) {
      return t('Too many requests. Please wait a moment and try again.', 'Too many requests. Please wait a moment and try again.');
    }
    if (status >= 500) {
      return t('Server error. Please try again in a moment.', 'Server error. Please try again in a moment.');
    }
    return t('Sign in failed. Please try again.', 'Sign in failed. Please try again.');
  }

  let _submitInFlight = false;
  /** Toggle the submit button between idle and loading state. */
  /* The auth pages do not load core.bundle.js, so they cannot call
     GP.setButtonLoading - but the STATE must still look the same as everywhere
     else: a spinner in front of the label, and the label left alone. This used to
     replace the text with "Signing in..." and drop the button to opacity .75,
     which is the deformation the app-wide loading state just stopped doing. */
  function _setSubmitLoading(btn, loading) {
    if (!btn) return;
    if (window.GP && typeof GP.setButtonLoading === 'function') {
      GP.setButtonLoading(btn, loading);
      return;
    }
    const existing = btn.querySelector(':scope > .gp-spinner');
    if (loading) {
      btn.disabled = true;
      btn.setAttribute('aria-busy', 'true');
      btn.classList.add('loading');
      /* The same mark as everywhere else. The auth pages load logo.min.css, so
         the ring and the tanuki are both already there. */
      if (!existing && window.GP && typeof GP.renderSpinnerHtml === 'function') {
        btn.insertAdjacentHTML('afterbegin', GP.renderSpinnerHtml('xs'));
      }
    } else {
      btn.disabled = false;
      btn.removeAttribute('aria-busy');
      btn.classList.remove('loading');
      if (existing) existing.remove();
    }
  }

  /* ============================================
     Cross-tab auth sync - if the user signs in
     successfully in another tab, this tab will
     immediately navigate to the dashboard so they
     don't see a stale login form.  Uses both
     BroadcastChannel (modern) and the storage
     event (universal fallback).
     ============================================ */
  const AUTH_CHANNEL = 'gitpulse-auth-v1';
  let _authBC = null;
  try {
    if ('BroadcastChannel' in window) {
      _authBC = new BroadcastChannel(AUTH_CHANNEL);
    }
  } catch (_) { /* ignored */ }

  function _broadcastLogin() {
    const payload = { type: 'login', at: Date.now() };
    try { localStorage.setItem(AUTH_CHANNEL, JSON.stringify(payload)); } catch (_) { /* private mode */ }
    if (_authBC) {
      try { _authBC.postMessage(payload); } catch (_) { /* closed */ }
    }
  }

  function _handleRemoteAuth(payload) {
    if (!payload || payload.type !== 'login') return;
    // Another tab signed in - go to the dashboard rather than stay on
    // an obsolete login form.  Stop any pending submit first.
    _submitInFlight = true;
    window.location.href = '/dashboard/';
  }

  if (_authBC) {
    _authBC.onmessage = function (ev) { _handleRemoteAuth(ev.data); };
  }
  window.addEventListener('storage', function (ev) {
    if (ev.key !== AUTH_CHANNEL || !ev.newValue) return;
    try { _handleRemoteAuth(JSON.parse(ev.newValue)); } catch (_) { /* ignored */ }
  });

  if (loginForm) {
    loginForm.addEventListener('submit', function (e) {
      e.preventDefault();
      // Idempotent: ignore further submits while one is in flight
      // (covers double-click, Enter-spam, and accessibility submit-twice).
      if (_submitInFlight) return;

      // Block submit when health-banner has flagged the server as down.
      if (document.body.classList.contains('is-offline')) {
        _showLoginError(window.GP?.t?.('Server is unreachable. Retrying...') || 'Server is unreachable. Retrying...');
        return;
      }

      const username = loginForm.querySelector('input[name="username"], input[type="text"]');
      const password = loginForm.querySelector('input[name="password"], input[type="password"]');
      let hasError = false;
      let firstInvalid = null;
      [username, password].forEach(function (field) {
        if (field && !field.value.trim()) {
          field.classList.add('is-invalid');
          field.setAttribute('aria-invalid', 'true');
          if (!firstInvalid) firstInvalid = field;
          hasError = true;
        } else if (field) {
          field.classList.remove('is-invalid');
          field.removeAttribute('aria-invalid');
        }
      });
      if (hasError) {
        if (firstInvalid) { try { firstInvalid.focus(); } catch (_) { /* ignored */ } }
        return;
      }

      const submitBtn = loginForm.querySelector('button[type="submit"], input[type="submit"]');
      _submitInFlight = true;
      _setSubmitLoading(submitBtn, true);

      const formData = new FormData(loginForm);
      fetch(loginForm.action || '/dashboard/login', {
        method: 'POST',
        credentials: 'same-origin',
        body: formData,
        redirect: 'manual',
        headers: { 'X-Requested-With': 'fetch' },
      }).then(function (resp) {
        // Server responds with 303 -> opaque redirect. The session cookie is
        // set on this response and committed by the browser before we navigate.
        if (resp.type === 'opaqueredirect') {
          _broadcastLogin();
          window.location.href = '/dashboard/';
          return;
        }
        if (resp.ok && resp.redirected) {
          _broadcastLogin();
          window.location.href = resp.url || '/dashboard/';
          return;
        }
        _showLoginError(_errorForStatus(resp.status));
        _submitInFlight = false;
        _setSubmitLoading(submitBtn, false);
      }).catch(function () {
        _showLoginError(window.GP?.t?.('Network error. Please check your connection.') || 'Network error. Please check your connection.');
        _submitInFlight = false;
        _setSubmitLoading(submitBtn, false);
      });
    });
    // Clear validation error on input
    loginForm.querySelectorAll('input').forEach(function (input) {
      input.addEventListener('input', function () {
        this.classList.remove('is-invalid');
        this.removeAttribute('aria-invalid');
      });
    });
  }

  /* ============================================
     BFCache / pageshow recovery - when the user
     navigates back to login via the browser back
     button, the persisted DOM may still have a
     disabled "Signing in..." button.  Reset state.
     ============================================ */
  window.addEventListener('pageshow', function (ev) {
    if (!ev.persisted) return;
    _submitInFlight = false;
    const submitBtn = document.querySelector('.btn-signin');
    _setSubmitLoading(submitBtn, false);
  });

  /* ============================================
     Server Health Check (login-page lightweight heartbeat)
     - Only checks /health/live - no session/token validation
     - Shows inline banner when server is unreachable
     - Disables login buttons while offline
     ============================================ */
  const POLL_OK_MS  = 25000;   // 25 s when healthy
  const POLL_FAIL_MS = 5000;   // 5 s when failing
  const FAIL_THRESHOLD = 2;    // show banner after 2 consecutive failures
  const INITIAL_DELAY = 1500;  // first check 1.5 s after page loads

  let _failCount = 0;
  let _timerId = null;
  let _bannerEl = null;
  const _statusDot = document.getElementById('loginServerStatus');
  let _wasDown = false;

  function _ensureBanner() {
    if (_bannerEl) return _bannerEl;
    const banner = document.createElement('div');
    banner.id = 'loginHealthBanner';
    banner.className = 'login-health-banner';
    banner.setAttribute('role', 'alert');
    banner.hidden = true;
    banner.innerHTML =
      /* Pajamas `warning` (@gitlab/svgs); the auth pages load no icon registry. */
      '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" class="login-health-icon" aria-hidden="true">' +
        '<path fill-rule="evenodd" clip-rule="evenodd" d="M8.429 2.746a.5.5 0 00-.858 0L1.58 12.743a.5.5 0 00.429.757h11.984a.5.5 0 00.43-.757L8.428 2.746zm-2.144-.77C7.06.68 8.939.68 9.715 1.975l5.993 9.996c.799 1.333-.161 3.028-1.716 3.028H2.008C.453 15-.507 13.305.292 11.972l5.993-9.997zM9 11.5a1 1 0 11-2 0 1 1 0 012 0zm-.25-5.75a.75.75 0 00-1.5 0v3a.75.75 0 001.5 0v-3z"/>' +
      '</svg>' +
      '<span class="login-health-text">' + (window.GP?.t?.('Server is unreachable. Retrying...') || 'Server is unreachable. Retrying...') + '</span>';
    const card = document.querySelector('.login-card');
    if (card) {
      card.parentNode.insertBefore(banner, card);
    } else {
      document.body.prepend(banner);
    }
    _bannerEl = banner;
    return banner;
  }

  function _showBanner() {
    const b = _ensureBanner();
    if (!b.hidden) return;
    b.hidden = false;
    /* Drops in from above the card, on the shared edge contract. The keyframe
       this replaces sat on the `.login-health-banner` class and so only ever
       ran on first paint - this banner is created hidden and revealed later,
       so it never animated at all. */
    GP.motion.edgeIn(b, '-100%');
  }
  function _hideBanner() {
    if (!_bannerEl || _bannerEl.hidden) return;
    GP.motion.edgeOut(_bannerEl, '-100%', function () {
      _bannerEl.hidden = true;
      GP.motion.settle(_bannerEl, 'opacity,transform');
    });
  }

  /** Update the small dot indicator + disable/enable login controls */
  function _setOnlineState(online) {
    document.body.classList.toggle('is-offline', !online);
    if (_statusDot) {
      _statusDot.classList.toggle('status-online', online);
      _statusDot.classList.toggle('status-offline', !online);
      // Component (tippy) tooltip only - never a native title=.
      const _tip = online ? (window.GP?.t?.('Server online') || 'Server online') : (window.GP?.t?.('Server unreachable') || 'Server unreachable');
      _statusDot.setAttribute('data-tippy-content', _tip);
      _statusDot.removeAttribute('title');
      if (_statusDot._tippy && typeof _statusDot._tippy.setContent === 'function') _statusDot._tippy.setContent(_tip);
      else window.GP?.initTippy?.(_statusDot.parentNode || document);
    }
    // Disable / enable login buttons while server is down
    const oauthBtn = document.querySelector('.btn-gitlab');
    const signInBtn = document.querySelector('.btn-signin');
    [oauthBtn, signInBtn].forEach(function (btn) {
      if (!btn) return;
      if (!online) {
        btn.classList.add('btn-disabled-offline');
        btn.setAttribute('data-offline', '1');
        if (btn.tagName === 'A') { btn.dataset.href = btn.href; btn.removeAttribute('href'); }
        else btn.disabled = true;
      } else {
        btn.classList.remove('btn-disabled-offline');
        btn.removeAttribute('data-offline');
        if (btn.tagName === 'A' && btn.dataset.href) { btn.href = btn.dataset.href; delete btn.dataset.href; }
        else btn.disabled = false;
      }
    });
  }

  function _heartbeat() {
    let controller = null;
    let timeoutId = null;
    try { controller = new AbortController(); } catch (_) { /* IE fallback: no abort */ }
    const signal = controller ? controller.signal : undefined;

    // 8s timeout
    if (controller) {
      timeoutId = setTimeout(function () { controller.abort(); }, 8000);
    }

    const online = navigator.onLine !== false;
    if (!online) {
      _failCount++;
      _afterHeartbeat();
      return;
    }

    fetch('/health/live', { method: 'GET', credentials: 'same-origin', cache: 'no-store', signal: signal })
      .then(function (resp) {
        if (timeoutId) clearTimeout(timeoutId);
        if (!resp.ok) {
          _failCount++;
        } else {
          const hadFailure = _failCount >= FAIL_THRESHOLD;
          _failCount = 0;
          _hideBanner();
          _setOnlineState(true);
          if (hadFailure && _wasDown) {
            _wasDown = false;
            // Brief green flash on the card
            const card = document.querySelector('.login-card');
            if (card) { card.classList.add('login-card-restored'); setTimeout(function () { card.classList.remove('login-card-restored'); }, 2000); }
          }
        }
        _afterHeartbeat();
      })
      .catch(function () {
        if (timeoutId) clearTimeout(timeoutId);
        _failCount++;
        _afterHeartbeat();
      });
  }

  function _afterHeartbeat() {
    if (_failCount >= FAIL_THRESHOLD) {
      _showBanner();
      _setOnlineState(false);
      _wasDown = true;
    }
    _schedule(_failCount >= FAIL_THRESHOLD ? POLL_FAIL_MS : POLL_OK_MS);
  }

  function _schedule(delayMs) {
    if (_timerId) clearTimeout(_timerId);
    _timerId = setTimeout(_heartbeat, delayMs);
  }

  // Start after short initial delay
  _schedule(INITIAL_DELAY);

  // Immediate re-check when browser comes back online
  window.addEventListener('online', function () { _schedule(500); });
  // Mark offline immediately when browser loses connectivity
  window.addEventListener('offline', function () { _failCount = FAIL_THRESHOLD; _afterHeartbeat(); });

  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) _schedule(800);
  });

  window.addEventListener('beforeunload', function () {
    if (_timerId) { clearTimeout(_timerId); _timerId = null; }
  });

})();
