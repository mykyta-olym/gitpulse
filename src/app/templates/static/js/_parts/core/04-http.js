/* ============================================
   Shared timing constants
   ============================================ */
const _RETRY_JITTER_MAX_MS = 120;

function _retryDelay(baseMs, attempt) {
  return baseMs * Math.pow(2, attempt) + Math.floor(Math.random() * _RETRY_JITTER_MAX_MS);
}

function _httpErrorLabel(statusCode) {
  const _labels = {
    401: _translateUiText('Session expired - please sign in again'),
    403: _translateUiText('Access denied'),
    404: _translateUiText('Not found'),
    409: _translateUiText('Conflict - please refresh'),
    422: _translateUiText('Validation error'),
    429: _translateUiText('Too many requests - please wait'),
    500: _translateUiText('Server error - please try again'),
  };
  return _labels[statusCode] || _translateUiText('Request failed');
}

/* ============================================
   CSRF
   ============================================ */
const _csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
window._csrfToken = _csrfToken;
GP.csrfToken = _csrfToken;
