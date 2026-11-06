/**
 * GitPulse - Job Streaming
 *
 * Uses SSE with graceful fallback to polling.
 */
;(function() {
'use strict';

const GP = window.GP || (window.GP = {});

function streamJobProgress(jobId, callbacks = {}, options = {}) {
  const config = {
    sseUrl: options.sseUrl || `/api/v1/jobs/${encodeURIComponent(jobId)}/stream`,
    pollUrl: options.pollUrl || `/api/v1/jobs/${encodeURIComponent(jobId)}`,
    pollInterval: options.pollInterval || 2000,
    disableSse: options.disableSse === true,
  };

  const state = {
    closed: false,
    mode: 'idle',
    closeImpl: null,
  };

  const safeCallbacks = {
    onUpdate: typeof callbacks.onUpdate === 'function' ? callbacks.onUpdate : null,
    onComplete: typeof callbacks.onComplete === 'function' ? callbacks.onComplete : null,
    onError: typeof callbacks.onError === 'function' ? callbacks.onError : null,
  };

  function callCallback(callback, payload) {
    if (!callback) {
      return;
    }
    try {
      callback(payload);
    } catch (error) {
      // Job streams are infrastructure; one page callback must not leave
      // an EventSource open forever or break the polling fallback loop.
      console.error('[sse-stream] callback failed', error);
    }
  }

  function finishComplete(payload) {
    if (state.closed) {
      return;
    }
    try {
      callCallback(safeCallbacks.onComplete, payload);
    } finally {
      controller.close();
    }
  }

  function emitUpdate(payload) {
    if (state.closed) {
      return;
    }
    callCallback(safeCallbacks.onUpdate, payload);
  }

  function emitError(error) {
    if (state.closed) {
      return;
    }
    callCallback(safeCallbacks.onError, error);
  }

  function startPollingFallback(reasonError) {
    if (state.closed || state.mode === 'polling') {
      return;
    }
    if (state.closeImpl) state.closeImpl();

    if (reasonError) {
      emitError(reasonError);
    }

    // The error callback is allowed to close this controller (for example
    // a caller may replace it with its own poller). Do not start an internal
    // fallback after the controller was closed from that callback.
    if (state.closed) {
      return;
    }

    state.mode = 'polling';

    const poller = new GP.PollingController(config.pollUrl, {
      interval: config.pollInterval,
      // A read failure is not a worker failure; keep trying until closed.
      maxErrors: Infinity,
      onUpdate(data) {
        emitUpdate(data);
        const status = String(data?.status || '').toLowerCase();
        if (status === 'completed' || status === 'failed' || status === 'cancelled') {
          finishComplete({
            status,
            error_message: data.error_message || null,
            result_summary: data.result_summary || null,
          });
        }
      },
      onError(error) {
        emitError(error);
      },
      isComplete(data) {
        const status = String(data?.status || '').toLowerCase();
        return status === 'completed' || status === 'failed' || status === 'cancelled';
      },
    });

    poller.start();
    state.closeImpl = () => poller.stop();

  }

  function startSse() {
    if (!window.EventSource || config.disableSse) {
      startPollingFallback(null);
      return;
    }

    state.mode = 'sse';
    let source;
    try { source = new EventSource(config.sseUrl); } catch (error) {
      startPollingFallback(error);
      return;
    }
    let errorCount = 0;

    const handlePayload = (raw) => {
      if (state.closed) {
        return null;
      }
      try {
        return JSON.parse(raw);
      } catch (_) {
        return null;
      }
    };

    source.onmessage = (event) => {
      const payload = handlePayload(event.data);
      if (!payload) {
        return;
      }
      errorCount = 0;
      emitUpdate(payload);

      const status = String(payload.status || '').toLowerCase();
      if (status === 'completed' || status === 'failed' || status === 'cancelled') {
        finishComplete(payload);
      }
    };

    function handleTerminal(event) {
      if (state.closed) return;
      const payload = handlePayload(event.data);
      if (['completed', 'failed', 'cancelled'].includes(payload?.status)) {
        finishComplete(payload);
      } else {
        source.close();
        startPollingFallback(new Error('Terminal status missing, verifying through polling'));
      }
    }
    source.addEventListener('complete', handleTerminal);
    source.addEventListener('failed', handleTerminal);

    source.onerror = () => {
      errorCount += 1;
      // Trigger immediate health check on first SSE failure
      if (errorCount === 1 && window.GP?.health?.check) {
        window.GP.health.check();
      }
      // If backend is known to be down, close SSE and fall back to polling
      // (polling will retry periodically so the job isn't silently lost).
      if (window.GP?.health?.isDown) {
        source.close();
        startPollingFallback(new Error('Backend unreachable, switched to polling'));
        return;
      }
      if (errorCount < (GP.SSE_MAX_ERRORS || 5)) {
        return;
      }
      source.close();
      startPollingFallback(new Error('SSE connection lost, switched to polling'));
    };

    state.closeImpl = () => {
      source.close();
    };
  }

  const controller = {
    get mode() {
      return state.mode;
    },
    close() {
      if (state.closed) {
        return;
      }
      state.closed = true;
      if (typeof state.closeImpl === 'function') {
        state.closeImpl();
      }
      state.closeImpl = null;
    },
  };

  startSse();
  return controller;
}

window.streamJobProgress = streamJobProgress;
window.GP.streamJobProgress = streamJobProgress;

})();
