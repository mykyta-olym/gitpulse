/**
 * Admin System page - health check, monitoring, background jobs, configuration.
 */
  const GP = window.GP;
  GP.runPageCleanup();

  let onHealthChangeMaintenance = null;
  let onTabVisibleMaintenance = null;
  let onJobCompleteMaintenance = null;
  let onBeforeSwap = null;
  let _disposed = false;

  const { apiCall, showToast, escapeHtml, t, withUiLock: _lock, jobTypeLabel: _jobTypeLabel } = GP;

  let _cfg = {};
  try {
    const _ce = document.getElementById('gp-page-config');
    if (_ce) _cfg = JSON.parse(_ce.textContent);
  } catch (_) { /* noop */ }
  const _isAdmin = _cfg.isAdmin !== false;

  const healthBtn = document.getElementById('btnHealthCheck');
  const refreshMonitoringBtn = document.getElementById('btnRefreshMonitoring');
  const cacheBtn = document.getElementById('btnClearCache');
  const refreshJobsBtn = document.getElementById('btnRefreshJobs');

  function _icon(name, size) {
    return GP.icons.get(name, size || 16);
  }
