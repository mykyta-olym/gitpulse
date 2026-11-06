  function _showJobCleanupResult(result) {
    let message = t('Deleted {database} PostgreSQL records and {redis} Redis/RQ job records.')
      .replace('{database}', result.database_deleted)
      .replace('{redis}', result.redis_deleted);
    if (result.skipped) message += ' ' + t('{count} active or changed jobs were retained. Refresh and try again.').replace('{count}', result.skipped);
    showToast(message, result.skipped ? 'warning' : 'success');
  }

  /* -- Purge finished jobs by age -- */
  async function purgeOldJobs(hours) {
    if (!_isAdmin) { showToast(t('Admin access required'), 'warning'); return; }
    hours = parseInt(hours, 10) || 24;
    const purgeBtn = document.getElementById('btnPurgeJobs');
    const ageLabels = {
      24: t('older than 24 hours'),
      168: t('older than 7 days'),
      720: t('older than 30 days'),
      87600: t('- everything'),
    };
    const ageLabel = ageLabels[hours] || (t('older than') + ' ' + hours + 'h');
    const confirmMsg = hours >= 87600
      ? t('Delete all finished jobs from PostgreSQL and Redis/RQ? Active jobs, sessions and the activity audit will be retained.')
      : t('Delete finished jobs {age} from PostgreSQL and Redis/RQ? Active jobs, sessions and the activity audit will be retained.').replace('{age}', ageLabel);
    confirmDangerousAction(t('purge finished jobs'), async function () {
      try {
        await _lock('purgeJobs', async () => {
          setButtonLoading(purgeBtn, true);
          const result = await apiCall('/dashboard/api/v1/admin/system/jobs/purge', 'POST', { hours: hours, status: 'both', scope: 'jobs' }, { maxRetries: 0 });
          _showJobCleanupResult(result);
          await loadBackgroundJobs();
        });
      } catch (err) {
        if (err.code !== 'LOCKED') showToast(t('Purge failed') + ': ' + err.message, 'danger');
      } finally {
        setButtonLoading(purgeBtn, false);
      }
    }, { confirmText: confirmMsg, singleConfirm: hours < 87600 });
  }

  /* -- Selective cleanup of finished jobs -- */
  function _updateJobSelectionCount() {
    const checked = document.querySelectorAll('#jobsTableBody .job-select:not(:disabled):checked');
    const countEl = document.getElementById('jobsSelectedCount');
    const delBtn = document.getElementById('btnDeleteSelectedJobs');
    if (countEl) countEl.textContent = checked.length;
    if (delBtn) delBtn.disabled = checked.length === 0;
    const selectAll = document.getElementById('jobsSelectAll');
    const all = document.querySelectorAll('#jobsTableBody .job-select:not(:disabled)');
    if (selectAll) {
      selectAll.disabled = all.length === 0;
      selectAll.checked = all.length > 0 && all.length === checked.length;
      selectAll.indeterminate = checked.length > 0 && checked.length < all.length;
    }
  }

  function _resetJobSelection() {
    const selectAll = document.getElementById('jobsSelectAll');
    if (selectAll) { selectAll.checked = false; selectAll.indeterminate = false; }
    _updateJobSelectionCount();
  }

  async function deleteSelectedJobs() {
    if (!_isAdmin) { showToast(t('Admin access required'), 'warning'); return; }
    const ids = Array.from(document.querySelectorAll('#jobsTableBody .job-select:not(:disabled):checked'))
      .map(function (cb) { return cb.dataset.jobId; }).filter(Boolean);
    if (!ids.length) return;
    const delBtn = document.getElementById('btnDeleteSelectedJobs');
    confirmDangerousAction(t('the selected finished jobs'), async function () {
      try {
        await _lock('deleteJobs', async () => {
          setButtonLoading(delBtn, true);
          const result = await apiCall('/dashboard/api/v1/admin/system/jobs/delete', 'POST', { ids: ids }, { maxRetries: 0 });
          _showJobCleanupResult(result);
          await loadBackgroundJobs();
        });
      } catch (err) {
        if (err.code !== 'LOCKED') showToast(t('Delete failed') + ': ' + err.message, 'danger');
      } finally {
        setButtonLoading(delBtn, false);
      }
    }, { confirmText: t('Delete the selected finished jobs from PostgreSQL and Redis/RQ? This cannot be undone.'), singleConfirm: true });
  }

  /* -- System Health & Monitoring (server-rendered partials) -- */
  const _healthSig = function (raw) {
    const comps = (raw && raw.components) || {};
    const parts = Object.keys(comps).sort().map(function (k) {
      const c = comps[k] || {};
      return k + ':' + (c.status || '') + ':' + (c.error || '');
    });
    return String((raw && raw.status) || '') + '|' + parts.join('|');
  };
  let _lastHealthSig = document.getElementById('systemHealthContent')?.dataset.healthSig || '';

  async function _fetchHealthPartial(fresh) {
    const body = document.querySelector('#systemHealth > .card-body');
    if (!body || _disposed) return null;
    const controller = new AbortController();
    const timer = setTimeout(function () { controller.abort(); }, 10000);
    try {
      const resp = await fetch('/dashboard/api/v1/admin/system/health' + (fresh ? '?fresh=1' : ''), {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { Accept: 'text/html' },
        signal: controller.signal,
      });
      if (!resp.ok) throw new Error(t('Health check failed'));
      const html = await resp.text();
      if (_disposed) return null;
      const current = document.getElementById('systemHealthContent');
      if (current) current.outerHTML = html;
      else body.innerHTML = html;
      const freshEl = document.getElementById('systemHealthContent');
      if (freshEl) {
        _lastHealthSig = freshEl.dataset.healthSig || '';
        window.localizeTimes?.(freshEl);
        GP.initTippy?.(freshEl);
      }
      return resp.headers.get('X-Health-Status') || 'ok';
    } finally {
      clearTimeout(timer);
    }
  }

  async function checkSystemHealth(arg) {
    if (_disposed) return;
    const silent = !!(arg && arg.silent === true);
    if (silent) {
      try { await _fetchHealthPartial(false); } catch (_) { /* noop */ }
      return;
    }
    if (!healthBtn) return;
    let status = 'ok';
    const updated = await GP.refreshRegion({
      button: healthBtn,
      region: document.querySelector('#systemHealth > .card-body'),
      errorMessage: t('Health check failed'),
      load: async () => {
        const res = await _fetchHealthPartial(true);
        if (!res) return false;
        status = res;
        return true;
      },
    });
    if (!updated || _disposed) return;
    showToast(
      t(status === 'ok'
        ? 'All systems operational'
        : status === 'degraded'
          ? 'Some components are degraded'
          : 'System is unavailable'),
      status === 'ok' ? 'success' : status === 'degraded' ? 'warning' : 'danger',
      5000,
      { button: healthBtn }
    );
  }

  async function _fetchMonitoringPartial(fresh) {
    const region = document.getElementById('systemMonitoringResults');
    if (!region || _disposed) return null;
    const controller = new AbortController();
    const timer = setTimeout(function () { controller.abort(); }, 10000);
    try {
      const resp = await fetch('/dashboard/api/v1/admin/system/monitoring' + (fresh ? '?fresh=1' : ''), {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { Accept: 'text/html' },
        signal: controller.signal,
      });
      const ctype = resp.headers.get('content-type') || '';
      if (!resp.ok && !(resp.status === 503 && ctype.includes('text/html'))) {
        throw new Error(t('Failed to refresh monitoring'));
      }
      const html = await resp.text();
      if (_disposed) return null;
      region.innerHTML = html;
      window.localizeTimes?.(region);
      GP.initTippy?.(region);
      return resp.status;
    } finally {
      clearTimeout(timer);
    }
  }

  async function refreshMonitoring(arg) {
    if (_disposed) return;
    const silent = !!(arg && arg.silent === true);
    if (silent) {
      try { await _fetchMonitoringPartial(false); } catch (_) { /* noop */ }
      return;
    }
    if (!refreshMonitoringBtn) return;
    let httpStatus = 200;
    const updated = await GP.refreshRegion({
      button: refreshMonitoringBtn,
      region: document.querySelector('#systemMonitoring > .card-body'),
      errorMessage: t('Failed to refresh monitoring'),
      load: async () => {
        const res = await _fetchMonitoringPartial(true);
        if (!res) return false;
        httpStatus = res;
        return true;
      },
    });
    if (!updated || _disposed) return;
    if (httpStatus === 503) {
      showToast(t('Monitoring is unavailable'), 'warning', 5000, { button: refreshMonitoringBtn });
    } else {
      showToast(t('Monitoring refreshed'), 'success', 5000, { button: refreshMonitoringBtn });
    }
  }

  /* -- Clear Cache -- */
  async function clearSystemCache() {
    if (!_isAdmin) { showToast(t('Admin access required'), 'warning'); return; }
    if (!cacheBtn) return;
    confirmDangerousAction(t('clear cache'), async () => {
      try {
        await _lock('clearCache', async () => {
          setButtonLoading(cacheBtn, true);
          const result = await apiCall('/dashboard/api/v1/admin/cache/clear', 'POST', null, { maxRetries: 0, timeoutMs: 10000 });
          if (!_disposed) showToast(t('Cache cleared') + ': ' + result.cleared.join(', '), 'success');
        });
      } catch (err) {
        if (err.code !== 'LOCKED') {
          showToast(t('Failed to clear cache') + ': ' + err.message, 'danger');
        }
      } finally {
        setButtonLoading(cacheBtn, false);
      }
    }, { confirmText: t('Clear cached pages and GitLab responses? Sessions, queues, locks and job history will be retained.') });
  }

  /* -- Refresh All -- */
  async function refreshAll() {
    const results = await Promise.all([loadSystemStats(), loadBackgroundJobs()]);
    return results.every(Boolean);
  }

  /* -- Bind event listeners -- */
  if (healthBtn) healthBtn.addEventListener('click', checkSystemHealth);
  if (refreshMonitoringBtn) refreshMonitoringBtn.addEventListener('click', refreshMonitoring);
  if (cacheBtn) cacheBtn.addEventListener('click', clearSystemCache);
  if (refreshJobsBtn) {
    refreshJobsBtn.addEventListener('click', async function () {
      await GP.refreshRegion({
        button: refreshJobsBtn,
        region: document.querySelector('#jobQueue > .card-body'),
        load: async options => {
          const [stats, jobs] = await Promise.all([
            loadSystemStats(), loadBackgroundJobs({ ...options, quiet: true }),
          ]);
          if (_disposed || !jobs) return false;
          if (!stats) throw new Error(t('Queue status is temporarily unavailable.'));
        },
        successMessage: t('Jobs refreshed'),
      });
    });
  }

  document.querySelectorAll('[data-purge-hours]').forEach(function (item) {
    item.addEventListener('click', function () {
      purgeOldJobs(this.dataset.purgeHours);
    });
  });

  const delSelBtn = document.getElementById('btnDeleteSelectedJobs');
  if (delSelBtn) delSelBtn.addEventListener('click', deleteSelectedJobs);

  document.getElementById('jobsSelectAll')?.addEventListener('change', function () {
    document.querySelectorAll('#jobsTableBody .job-select:not(:disabled)').forEach(function (cb) { cb.checked = this.checked; }, this);
    _updateJobSelectionCount();
  });

  const onJobSelectionChange = function (e) {
    if (e.target && e.target.classList && e.target.classList.contains('job-select')) {
      _updateJobSelectionCount();
    }
  };
  document.addEventListener('change', onJobSelectionChange);

  const jobStatusFilter = document.getElementById('jobStatusFilter');
  const jobTypeFilter = document.getElementById('jobTypeFilter');
  function _filterReloadJobs() {
    _jobsPaginator.currentPage = 1;
    loadBackgroundJobs();
  }
  if (jobStatusFilter) jobStatusFilter.addEventListener('change', _filterReloadJobs);
  if (jobTypeFilter) jobTypeFilter.addEventListener('change', _filterReloadJobs);

  onHealthChangeMaintenance = function (e) {
    const detail = e.detail || {};
    const state = detail.state;
    if (state && state.raw && document.getElementById('systemHealthContent')) {
      const sig = _healthSig(state.raw);
      if (sig === _lastHealthSig) return;
      _lastHealthSig = sig;
      checkSystemHealth({ silent: true });
      if (document.getElementById('systemMonitoringResults')) {
        refreshMonitoring({ silent: true });
      }
    }
  };
  document.addEventListener('gp-health-change', onHealthChangeMaintenance);

  // Rows, health, monitoring, and queue status are already rendered by the server.
  _jobsPaginator.setServerTotal(_cfg.jobsTotal);
  _bindJobActions(document.getElementById('jobsTableBody'));
  _resetJobSelection();
  loadSystemStats();
  if (_jobsPaginator.pageSize !== _cfg.jobsPageSize || (_cfg.jobsPageSize === 'all' && _cfg.jobsTotal > 500)) loadBackgroundJobs();

  /* -- LLM Status Check -- */
  const llmStatusBtn = document.getElementById('btnLlmStatus');
  const llmStatusDiv = document.getElementById('llmStatusResult');
  if (llmStatusBtn) {
    llmStatusBtn.addEventListener('click', async function () {
      try {
        await _lock('llmStatus', async () => {
          setButtonLoading(llmStatusBtn, true);
          const data = await apiCall('/dashboard/api/v1/admin/system/llm-status', 'GET', null, { maxRetries: 0, timeoutMs: 15000 });
          const statusCls = data.status === 'ok' ? 'success' : data.status === 'warning' ? 'warning' : data.status === 'disabled' ? 'info' : 'danger';
          if (llmStatusDiv) {
            llmStatusDiv.classList.remove('d-none');
            let html = '<strong>' + escapeHtml(t(data.message) || data.message) + '</strong>';
            if (data.available_models != null) {
              html += '<br><span class="text-sm">' + t('Available models') + ': ' + data.available_models + '</span>';
            }
            if (data.model_available === true) {
              html += ', <span class="text-sm text-success">' + escapeHtml(data.model) + ' ' + _icon('check', 12) + '</span>';
            } else if (data.model_available === false) {
              html += ', <span class="text-sm text-danger">' + escapeHtml(data.model) + ' ' + _icon('x', 12) + ' ' + t('not available') + '</span>';
            }
            llmStatusDiv.innerHTML = GP.alertHtml(html, statusCls);
          }
          showToast(t(data.message) || data.message, statusCls === 'success' ? 'success' : statusCls);
        });
      } catch (err) {
        if (err.code !== 'LOCKED') {
          showToast(t('Status check failed') + ': ' + err.message, 'danger');
          if (llmStatusDiv) {
            llmStatusDiv.classList.remove('d-none');
            llmStatusDiv.innerHTML = GP.alertHtml(escapeHtml(t('Status check failed') + ': ' + err.message), 'danger');
          }
        }
      } finally {
        setButtonLoading(llmStatusBtn, false);
      }
    });
  }

  onTabVisibleMaintenance = () => {
    refreshAll().catch(() => {});
  };
  document.addEventListener('gp-tab-visible', onTabVisibleMaintenance);

  onJobCompleteMaintenance = function (e) {
    const detail = e.detail || {};
    if (detail.status === 'done' || detail.status === 'error') {
      refreshAll().catch(function () {});
    }
  };
  window.addEventListener('gp:job-complete', onJobCompleteMaintenance);

  onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-page-config') || target.id === 'gp-page-config')) {
      GP.adminSystemCleanup();
    }
  };
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.adminSystemCleanup = () => {
    _disposed = true;
    document.removeEventListener('change', onJobSelectionChange);
    document.removeEventListener('gp-health-change', onHealthChangeMaintenance);
    document.removeEventListener('gp-tab-visible', onTabVisibleMaintenance);
    window.removeEventListener('gp:job-complete', onJobCompleteMaintenance);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };
  GP.activePageCleanup = GP.adminSystemCleanup;
