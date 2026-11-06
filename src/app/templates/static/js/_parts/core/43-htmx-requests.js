/* -- HTMX request indicators: disable trigger element during request -- */
document.body.addEventListener('htmx:beforeRequest', (evt) => {
  const elt = evt.detail.elt;
  if (elt?.tagName === 'BUTTON') GP.setButtonLoading(elt, true);
});
document.body.addEventListener('htmx:afterRequest', (evt) => {
  const elt = evt.detail.elt;
  if (elt?.tagName === 'BUTTON') {
    GP._releaseActiveAction(elt);
    if (evt.detail.successful) GP.setButtonDone(elt);
    else GP.setButtonError(elt);
    GP.setButtonLoading(elt, false);
  }
  // Check server version on every HTMX response
  const xhr = evt.detail.xhr;
  if (xhr && typeof xhr.getResponseHeader === 'function') {
    const sv = xhr.getResponseHeader('x-app-version');
    if (sv) _checkVersionHeader({ get: function () { return sv; } });
  }
});
document.body.addEventListener('htmx:responseError', (evt) => {
  const xhr = evt.detail.xhr;
  const code = xhr ? xhr.status : 0;
  /* 401 with HX-Redirect is handled by htmx natively - skip toast */
  if (code === 401) return;
  const msg = _httpErrorLabel(code);
  showToast(msg, code === 429 ? 'warning' : 'danger', 5000, { button: null });
});
/* Prevent HTMX from swapping error responses into the page - show toast instead */
document.body.addEventListener('htmx:beforeSwap', (evt) => {
  const code = evt.detail.xhr ? evt.detail.xhr.status : 0;
  if (code >= 400) {
    evt.detail.shouldSwap = false;
    evt.detail.isError = true;
    /* On 401, redirect to login immediately */
    if (code === 401) {
      _redirectToLogin();
    }
  }
});
/* Network-level HTMX failures (connection refused, DNS) surface a toast. */
document.body.addEventListener('htmx:sendError', function () {
  showToast(_translateUiText('Network error - check your connection'), 'danger', 5000, { button: null });
});

/* Request hit the global htmx.config.timeout. */
document.body.addEventListener('htmx:timeout', function () {
  showToast(_translateUiText('Request timed out - server is taking too long'), 'warning', 5000, { button: null });
});

/* -- Global form error interception --
   Intercept traditional <form method="post"> submissions (not HTMX, not
   already handled by JS) and submit via fetch so we can show a toast on
   4xx/5xx instead of rendering a raw JSON black-screen. */
document.addEventListener('submit', function (evt) {
  if (evt.defaultPrevented) return;
  const form = evt.target;
  if (!form || form.tagName !== 'FORM') return;
  // Skip forms already handled by HTMX, Alpine, or page-level JS handlers.
  // Page handlers run first on the form. An enhanced save owns its transport;
  // this fallback handles only submits they did not prevent.
  if (form.hasAttribute('hx-post') || form.hasAttribute('hx-put') ||
      form.hasAttribute('hx-patch') || form.hasAttribute('hx-delete')) return;
  if (form.dataset.noBoundary === '1') return;
  if (form.hasAttribute('data-submit-action')) return;  // page-level handler owns this
  if (form.hasAttribute('@submit') || form.hasAttribute('@submit.prevent')) return;  // Alpine
  const method = (form.method || 'GET').toUpperCase();
  if (method !== 'POST') return;

  evt.preventDefault();
  const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
  if (submitBtn?._loadingArmed || submitBtn?.classList.contains('loading')) return;
  if (submitBtn) GP.setButtonLoading(submitBtn, true);
  const finishProgress = GP.beginTopProgress();

  fetch(form.action || window.location.href, {
    method: 'POST',
    credentials: 'same-origin',
    body: new FormData(form),
    redirect: 'follow',
    signal: AbortSignal.timeout(15000),
  }).then(function (resp) {
    if (!form.isConnected) return;
    if (resp.ok && submitBtn) {
      GP._releaseActiveAction(submitBtn);
      GP.setButtonDone(submitBtn);
    }
    if (resp.redirected) { skipBeforeunload(); window.location.href = resp.url; return; }
    if (resp.ok) { reloadKeepScroll(); return; }
    // Error - show toast instead of replacing page with raw JSON
    showToast(_httpErrorLabel(resp.status) || _translateUiText('Request failed (') + resp.status + ')',
      resp.status === 429 ? 'warning' : 'danger', 5000, { button: submitBtn });
  }).catch(function (err) {
    if (!form.isConnected) return;
    const message = err.name === 'TimeoutError' ? 'Request timed out - server is taking too long'
      : 'Network error - check your connection';
    showToast(_translateUiText(message), 'danger', 5000, { button: submitBtn });
  }).finally(function () {
    finishProgress();
    if (submitBtn?.isConnected) GP.setButtonLoading(submitBtn, false);
  });
});
