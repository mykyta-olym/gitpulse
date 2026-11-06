/* -- SSE shared constants -- */
GP.SSE_MAX_ERRORS = 5;
GP.SSE_RECONNECT_MS = 2000;

/* ONE page-level SSE client.

   Five pages had written this out by hand - dashboard, sidebar badges, course,
   team, project - and the five copies were the same twenty lines: construct in
   a try/catch because a blocked EventSource throws synchronously, zero the
   error count on any event, and on failure close, count, and either reconnect
   after GP.SSE_RECONNECT_MS or give up to a polling fallback. Only the event
   names and what to do on give-up ever differed, and those are the arguments.

     const stream = GP.sse({
       url: '/api/v1/...',
       events: { connected() {...}, update(ev) {...} },
       onGiveUp() { startPolling(); },   // N failures in a row: stop trying
       onFailure(n) {...},               // optional, every failure
       onBlocked() {...},                // optional, EventSource threw
     });
     stream.close();

   The per-JOB stream is a different thing and stays where it is: it ends when
   its job does. See GP.streamJobProgress in sse-stream.js. */
GP.sse = function (opts) {
  const maxErrors = opts.maxErrors || GP.SSE_MAX_ERRORS;
  /* A number for a fixed delay, or a function of the failure count for
     backoff - the global job bar needs the second kind, because the server
     closes a finished sync's stream promptly and a fixed delay turns that
     into a tight reconnect loop. */
  const reconnectMs = opts.reconnectMs || function (n) { return Math.min(GP.SSE_RECONNECT_MS * Math.pow(2, n - 1), 30000); };
  let source = null;
  let timer = null;
  let stableTimer = null;
  let errors = 0;
  let closed = false;

  function drop() {
    if (timer) { clearTimeout(timer); timer = null; }
    if (stableTimer) { clearTimeout(stableTimer); stableTimer = null; }
    if (source) { source.close(); source = null; }
  }

  function connect() {
    if (closed) return;
    drop();
    if (opts.beforeConnect) opts.beforeConnect();
    try {
      source = new EventSource(opts.url, opts.withCredentials ? { withCredentials: true } : undefined);
    } catch (_) {
      // Blocked outright (an extension, a proxy): retrying will not help.
      if (opts.onBlocked) opts.onBlocked();
      else if (opts.onGiveUp) opts.onGiveUp();
      return;
    }
    source.onopen = function () {
      stableTimer = setTimeout(function () { errors = 0; stableTimer = null; }, 20000);
    };
    Object.keys(opts.events || {}).forEach(function (name) {
      source.addEventListener(name, function (ev) {
        // An immediate greeting followed by a disconnect is not recovery.
        // Reset after useful data, or after the connection survives a heartbeat.
        if (name !== 'connected') errors = 0;
        opts.events[name](ev);
      });
    });
    source.onerror = function () {
      errors++;
      drop();
      if (opts.onFailure) opts.onFailure(errors);
      if (closed) return;
      if (errors >= maxErrors) {
        if (opts.onGiveUp) opts.onGiveUp();
        return;
      }
      timer = setTimeout(connect, typeof reconnectMs === 'function' ? reconnectMs(errors) : reconnectMs);
    };
  }

  connect();
  return {
    close: function () { closed = true; drop(); },
    reopen: function () { closed = false; errors = 0; connect(); },
    /* The pages that reset this do it when something else proves the server is
       reachable (a tab came back, a fetch answered), so the next hiccup starts
       a fresh count instead of tipping an old one over the edge. */
    resetErrors: function () { errors = 0; },
    get errors() { return errors; },
    /* Live OR waiting to reconnect. The hand-rolled copies each needed a
       three-way test - no source AND no poll timer AND no reconnect timer -
       because the reconnect timer lived outside the connection it belonged to.
       Here it does not, so "is this stream still trying?" is one question. */
    get active() { return !closed && (source !== null || timer !== null); },
  };
};
