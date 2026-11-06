/* ============================================
   API Call - robust fetch wrapper
   ============================================ */
/* One in-flight request per key. A filter typed twice, a tab clicked twice, a
   poll that overlaps its own previous tick - all of them fire a second request
   before the first has answered, and whichever lands LAST wins the DOM. That is
   the same bug everywhere and it needs the same answer everywhere, so it lives
   in the transport: pass `key` and the previous call under that key is aborted
   before this one starts. The superseded promise rejects with `superseded`
   set, which callers ignore rather than surface as an error. */
const _inflightByKey = new Map();

async function _request(url, method = 'GET', data = null, options = null) {
  const normalizedMethod = _normalizeMethod(method);
  const opts = options || {};

  const config = {
    timeoutMs: typeof opts.timeoutMs === 'number' ? opts.timeoutMs : 20000,
    maxRetries: typeof opts.maxRetries === 'number' ? _clamp(opts.maxRetries, 0, 5) : 2,
    retryDelayMs: typeof opts.retryDelayMs === 'number' ? Math.max(50, opts.retryDelayMs) : 350,
    headers: opts.headers && typeof opts.headers === 'object' ? opts.headers : {},
    signal: opts.signal || null,
    abortMessage: opts.abortMessage || '',
    allowRetryUnsafe: opts.allowRetryUnsafe === true,
  };

  let _keyCtl = null;
  let _unlinkKeySignal = null;
  if (opts.key) {
    const prev = _inflightByKey.get(opts.key);
    if (prev) {
      prev.superseded = true;
      try { prev.abort(); } catch (_) { /* already settled */ }
    }
    _keyCtl = new AbortController();
    _inflightByKey.set(opts.key, _keyCtl);
    if (config.signal) {
      /* Honour a caller's own signal as well as the key. */
      if (config.signal.aborted) _keyCtl.abort();
      else {
        const signal = config.signal;
        const onAbort = () => _keyCtl.abort();
        signal.addEventListener('abort', onAbort, { once: true });
        _unlinkKeySignal = () => signal.removeEventListener('abort', onAbort);
      }
    }
    config.signal = _keyCtl.signal;
  }

  async function _attempt(attempt) {
    const headers = {
      Accept: 'application/json',
      ...config.headers,
    };

    const requestOptions = {
      method: normalizedMethod,
      credentials: 'same-origin',
      headers,
      cache: opts.cache || 'no-store',
      redirect: opts.redirect || 'follow',
    };

    if (normalizedMethod !== 'GET' && normalizedMethod !== 'HEAD') {
      if (data instanceof FormData) {
        if (_csrfToken && !data.has('csrf_token')) {
          data.append('csrf_token', _csrfToken);
        }
        requestOptions.body = data;
        delete requestOptions.headers['Content-Type'];
      } else if (normalizedMethod === 'DELETE' && !data) {
        requestOptions.headers['X-CSRF-Token'] = _csrfToken;
      } else {
        // JSON body: send CSRF via header only.  Embedding it in the payload
        // breaks Pydantic schemas with extra="forbid" (e.g. WebhookConfigUpdate).
        // Server reads X-CSRF-Token first, then falls back to body for
        // legacy form posts.
        if (_csrfToken) requestOptions.headers['X-CSRF-Token'] = _csrfToken;
        requestOptions.headers['Content-Type'] = requestOptions.headers['Content-Type'] || 'application/json';
        requestOptions.body = JSON.stringify(data && typeof data === 'object' ? data : {});
      }
    }

    const timeoutInfo = _createTimeoutSignal(config.timeoutMs, config.signal);
    if (timeoutInfo.signal) {
      requestOptions.signal = timeoutInfo.signal;
    }

    try {
      const response = await fetch(url, requestOptions);
      const contentType = (response.headers.get('content-type') || '').toLowerCase();
      const isJson = contentType.includes('application/json');

      // Detect server redeploy - triggers toast + auto-reload
      _checkVersionHeader(response.headers);

      if (response.redirected && response.url.includes('/dashboard/login')) {
        const authErr = new Error(_translateUiText('Session expired. Please sign in again.'));
        authErr.status = 401;
        throw authErr;
      }

      if (!response.ok) {
        const genericMessage = `Error: ${response.status} ${response.statusText}`;
        let message = genericMessage;

        if (isJson) {
          const errorData = await response.json().catch(() => ({}));
          message = errorData.detail || errorData.message || errorData.error || message;
          if (response.status === 422 && errorData && errorData.fields && typeof errorData.fields === 'object') {
            const parts = Object.entries(errorData.fields)
              .map(([k, v]) => `${k}: ${v}`)
              .slice(0, 5);
            if (parts.length > 0) {
              message = `${message} (${parts.join('; ')})`;
            }
          }
        } else {
          const text = await response.text().catch(() => '');
          if (text && text.trim()) {
            message = text.trim().slice(0, 400);
          }
        }

        // User-friendly fallbacks when the server didn't provide a specific message
        if (message === genericMessage) {
          if (response.status === 429) {
            const retryAfter = response.headers.get('Retry-After');
            message = retryAfter
              ? _translateUiText('Too many requests. Please wait') + ' ' + retryAfter + 's.'
              : _translateUiText('Too many requests. Please wait a moment.');
          } else if (response.status === 403) {
            message = _translateUiText('Access denied. You do not have permission for this action.');
          } else if (response.status === 404) {
            message = _translateUiText('The requested resource was not found.');
          } else if (response.status === 409) {
            message = _translateUiText('Conflict: the resource was modified by another request.');
          } else if (response.status === 422) {
            message = _translateUiText('Validation error. Please check your input.');
          }
        }

        const error = new Error(message);
        error.status = response.status;

        const canRetry =
          attempt < config.maxRetries &&
          _shouldAutoRetry(normalizedMethod, response.status, config.allowRetryUnsafe);

        if (canRetry) {
          const delay = _retryDelay(config.retryDelayMs, attempt);
          await _sleep(delay);
          return _attempt(attempt + 1);
        }

        throw error;
      }

      if (response.status === 204) {
        return null;
      }

      // Return raw Response when requested (e.g. for blob downloads)
      if (opts.raw === true) {
        return response;
      }

      // Keep timeout and cancellation active until an HTML body is consumed.
      if (opts.responseType === 'text') {
        return await response.text();
      }

      return await response.json();
    } catch (err) {
      const isAbort = timeoutInfo.signal?.aborted || (err && err.name === 'AbortError');
      const isNetwork = err && err.name === 'TypeError';
      const canRetryUnsafe = config.allowRetryUnsafe === true;
      // HTTP failures have already passed the status retry policy above.
      // Only a transport failure belongs to this second retry path.
      const canRetryNetwork =
        attempt < config.maxRetries &&
        !isAbort &&
        isNetwork &&
        (canRetryUnsafe || ['GET', 'HEAD', 'OPTIONS'].includes(normalizedMethod));

      if (canRetryNetwork) {
        const delay = _retryDelay(config.retryDelayMs, attempt);
        await _sleep(delay);
        return _attempt(attempt + 1);
      }

      // Replace generic messages with user-friendly labels
      if (isAbort) {
        const externalAbort = config.signal && config.signal.aborted;
        const reason = externalAbort ? config.signal.reason : null;
        // DOMException.message is read-only in browsers. Wrap it rather than
        // silently keeping the browser's untranslated cancellation message.
        const abortError = new Error(config.abortMessage
          || (reason && reason.name !== 'AbortError' && reason.message)
          || (externalAbort
            ? _translateUiText('Request cancelled.')
            : _translateUiText('Request timed out. Please try again.')));
        abortError.name = 'AbortError';
        abortError.cause = err;
        err = abortError;
      } else if (isNetwork) {
        err.message = _translateUiText('Network error. Please check your connection.');
      }

      throw err;
    } finally {
      timeoutInfo.cleanup();
    }
  }

  try {
    return await _attempt(0);
  } catch (err) {
    if (_keyCtl && _keyCtl.superseded) {
      err.superseded = true;
    }
    throw err;
  } finally {
    if (_unlinkKeySignal) _unlinkKeySignal();
    if (_keyCtl && _inflightByKey.get(opts.key) === _keyCtl) {
      _inflightByKey.delete(opts.key);
    }
  }
}

/* Anti-spam: one in-flight mutation per endpoint. A second identical write
   while the first still runs is refused with `code: 'LOCKED'` - the code
   withUiLock() uses, so the callers' `if (err.code !== 'LOCKED')` guards
   swallow it - and one throttled "please wait" toast instead of the
   caller's failure toast. Reads are not throttled; `key` supersedes them. */
const _inflightMutations = new Set();
let _apiThrottleToastAt = 0;

async function apiCall(url, method = 'GET', data = null, options = null) {
  const m = _normalizeMethod(method);
  if (m === 'GET' || m === 'HEAD' || m === 'OPTIONS') return _request(url, method, data, options);

  const throttleKey = m + ':' + url.split('?')[0];
  if (_inflightMutations.has(throttleKey)) {
    const now = Date.now();
    if (now - _apiThrottleToastAt > 1500 && typeof window.showToast === 'function') {
      _apiThrottleToastAt = now;
      window.showToast(_translateUiText('Please wait - the previous action is still running.'), 'info', 1800);
    }
    const err = new Error(_translateUiText('Request already in progress'));
    err.code = 'LOCKED';
    throw err;
  }
  _inflightMutations.add(throttleKey);
  const finishProgress = GP.beginTopProgress();
  try {
    return await _request(url, method, data, options);
  } finally {
    finishProgress();
    _inflightMutations.delete(throttleKey);
  }
}

GP.apiCall = apiCall;

/* Abandon everything still in flight. An internal navigation swaps
   #main-content, so a request started on the page being left answers into a
   DOM that no longer belongs to it - at best writing nothing, at worst
   painting the previous page's rows, counts or error into the new one. The SPA
   calls this on the way out; the rejections carry `superseded`, which callers
   already ignore. Only keyed calls are tracked, which is the point: an
   unkeyed one-shot POST should finish. */
function abortInflight() {
  _inflightByKey.forEach(function (ctl) {
    ctl.superseded = true;
    try { ctl.abort(); } catch (_) { /* already settled */ }
  });
  _inflightByKey.clear();
}
GP.abortInflight = abortInflight;

/* The OTHER half of the race mechanic, for refreshes that must not be dropped.

   `apiCall({key})` supersedes: the newest read wins and the older is abandoned.
   That is right for a read the user re-triggers (a filter, a page, a sort) -
   only the latest answer is wanted.

   A live refresh driven by events is the opposite case. Three SSE messages in
   one second must not fire three overlapping fetches, but the LAST one still
   has to be honoured, or the page settles on state that is one event stale.
   So: while a run is in flight, later calls join it, and exactly one trailing
   re-run follows if any arrived.

   This was hand-rolled three times in the dashboard alone (stats, attention
   items, activity feed), each with its own pair of module-level flags. One
   mechanic, one place. `fn` owns its own error handling - the returned promise
   never rejects, so callers may fire and forget.

   The promise resolves to what `fn` returned (or to the trailing re-run's
   result, which is the newer answer). It used to resolve to `undefined`, so a
   loader that answered `true` for "it worked" was read as a failure by every
   caller that checked - the System page's "Refresh stats" ran the reload and
   then said nothing, because its success toast waited on a `true` that never
   arrived. A rejected `fn` resolves to `false`. */
function coalesce(fn) {
  let inFlight = null;
  let pending = false;
  return function run() {
    if (inFlight) { pending = true; return inFlight; }
    inFlight = Promise.resolve().then(fn).catch(function (e) {
      console.debug('coalesced refresh:', e);
      return false;
    });
    inFlight = inFlight.then(function (result) {
      inFlight = null;
      if (pending) { pending = false; return run(); }
      return result;
    });
    return inFlight;
  };
}
GP.coalesce = coalesce;

/* Share concurrent event refreshes by key, replacing the loader on navigation.
   Retain its page closure only while the coalesced run is pending. */
const _coalescedByKey = new Map();
function coalesced(key, fn) {
  let entry = _coalescedByKey.get(key);
  if (!entry) {
    entry = { fn: fn };
    entry.run = coalesce(function () { return entry.fn(); });
    _coalescedByKey.set(key, entry);
  }
  entry.fn = fn;
  return entry.run().then(function (result) {
    if (_coalescedByKey.get(key) === entry) _coalescedByKey.delete(key);
    return result;
  });
}
GP.coalesced = coalesced;

window.apiCall = apiCall;
