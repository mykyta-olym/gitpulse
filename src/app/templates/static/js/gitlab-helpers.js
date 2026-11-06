/**
 * GitPulse - GitLab URL Helpers
 */
;(function() {
'use strict';

window.GP = window.GP || {};

async function parseGitLabUrl(url, csrfToken, options = {}) {
  const trimmedUrl = String(url || '').trim();
  if (!trimmedUrl) {
    return null;
  }

  try {
    const payload = {
      url: trimmedUrl,
      csrf_token: csrfToken || window._csrfToken || '',
    };

    const result = await apiCall('/api/v1/gitlab/parse-url', 'POST', payload, {
      timeoutMs: options.timeoutMs || 12000,
      maxRetries: options.maxRetries || 1,
      signal: options.signal || null,
      allowRetryUnsafe: false,
    });

    return result || null;
  } catch (error) {
    if (error?.name !== 'AbortError') {
      console.warn('GitLab URL parse failed:', error);
    }
    return null;
  }
}

/**
 * Auto-fill form fields from GitLab URL.
 *
 * @param {string} inputSelector
 * @param {Object} fieldMappings
 * @param {string} [csrfToken]
 * @param {Object} [options]
 */
function setupGitLabAutofill(inputSelector, fieldMappings, csrfToken, options = {}) {
  if (!inputSelector || !fieldMappings) return;
  const input = document.querySelector(inputSelector);
  if (!input) {
    return;
  }

  let lastProcessedUrl = '';
  let abortController = null;

  const debounceDelay = options.debounceMs || 300;
  const debouncedRun = (window.GP?.debounce || ((fn) => fn))(async () => {
    const raw = String(input.value || '').trim();
    if (!raw || !raw.includes('/')) {
      return;
    }

    if (raw === lastProcessedUrl) {
      return;
    }

    if (abortController) {
      abortController.abort();
    }
    abortController = new AbortController();

    // Show loading indicator on the input
    input.classList.add('input-loading');

    const result = await parseGitLabUrl(raw, csrfToken, {
      signal: abortController.signal,
      timeoutMs: options.timeoutMs || 12000,
    });

    input.classList.remove('input-loading');

    if (!result) {
      return;
    }

    lastProcessedUrl = raw;
    const mappings = fieldMappings?.[result.resource_type] || null;
    if (!mappings) {
      return;
    }

    let filledCount = 0;

    Object.entries(mappings).forEach(([selector, getter]) => {
      const target = document.querySelector(selector);
      if (!target || target.value) {
        return;
      }

      const value = typeof getter === 'function' ? getter(result) : result[getter];
      if (value === null || value === undefined || value === '') {
        return;
      }

      target.value = String(value);
      target.dispatchEvent(new Event('input', { bubbles: true }));
      target.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount += 1;
    });

    if (filledCount > 0 && options.toast !== false) {
      const t = window.GP?.t;
      showToast(t('Auto-filled') + ` ${filledCount} ` + t('field(s) from GitLab'), 'success', 2600);
    }
  }, debounceDelay);

  input.addEventListener('paste', () => {
    setTimeout(() => debouncedRun(), 0);
  });

  input.addEventListener('blur', () => {
    debouncedRun();
  });

  if (options.watchInput === true) {
    input.addEventListener('input', () => {
      debouncedRun();
    });
  }

  return {
    destroy() {
      if (abortController) {
        abortController.abort();
      }
    },
  };
}

window.setupGitLabAutofill = setupGitLabAutofill;
window.GP.parseGitLabUrl = parseGitLabUrl;
window.GP.setupGitLabAutofill = setupGitLabAutofill;

})();
