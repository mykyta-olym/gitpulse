/* ============================================
   Restripe - maintain zebra striping on visible rows
   ============================================ */
/**
 * Backward-compatible stub - zebra striping is now handled entirely
 * by CSS :nth-child(even of :not(.d-none)...)
 * which the browser re-evaluates automatically when classes change.
 *
 * This function is kept so existing callers (Paginator, SortableTable)
 * don't break.  It intentionally does nothing.
 *
 * @param {HTMLElement} _tbody - unused
 */
function restripeTable(_tbody) { /* CSS-only - no JS needed */ }
GP.restripeTable = restripeTable;
window.restripeTable = restripeTable;

/* ============================================
   Small Utilities
   ============================================ */
function _sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function _clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function _normalizeMethod(method) {
  return String(method || 'GET').toUpperCase();
}

function _shouldAutoRetry(method, statusCode, allowRetryUnsafe = false) {
  const retryableMethods = ['GET', 'HEAD', 'OPTIONS'];
  const retryableStatus = [408, 425, 429, 500, 502, 503, 504];
  return (retryableMethods.includes(method) || allowRetryUnsafe) && retryableStatus.includes(statusCode);
}

function _createTimeoutSignal(timeoutMs, externalSignal) {
  if (!timeoutMs || timeoutMs <= 0) {
    return { signal: externalSignal || null, cleanup: () => {} };
  }

  const controller = new AbortController();
  const cleanupFns = [];

  const timeoutId = setTimeout(() => {
    try {
      controller.abort(new DOMException('Request timed out', 'AbortError'));
    } catch (_) {
      controller.abort();
    }
  }, timeoutMs);
  cleanupFns.push(() => clearTimeout(timeoutId));

  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort(externalSignal.reason);
    } else {
      const onAbort = () => {
        try {
          controller.abort(externalSignal.reason);
        } catch (_) {
          controller.abort();
        }
      };
      externalSignal.addEventListener('abort', onAbort, { once: true });
      cleanupFns.push(() => externalSignal.removeEventListener('abort', onAbort));
    }
  }

  return {
    signal: controller.signal,
    cleanup: () => {
      cleanupFns.forEach((fn) => fn());
    },
  };
}

/* ============================================
   Operation Locks (double-click prevention)
   ============================================ */
const _operationLocks = new Set();

async function withUiLock(lockKey, fn) {
  if (typeof fn !== 'function') {
    return undefined;
  }
  if (!lockKey) {
    return fn();
  }
  if (_operationLocks.has(lockKey)) {
    const err = new Error(_translateUiText('Operation already in progress'));
    err.code = 'LOCKED';
    throw err;
  }

  _operationLocks.add(lockKey);
  try {
    return await fn();
  } finally {
    _operationLocks.delete(lockKey);
  }
}


GP.withUiLock = withUiLock;

/* -- HTML escape utility -- */
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str ?? '');
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  return str.replace(/[&<>"']/g, c => map[c]);
}
GP.escapeHtml = escapeHtml;
