  /* -- Load Background Jobs (with filters & pagination) -- */
  const _jobsPaginator = new ClientPaginator({
    tbodySelector: '#jobsTableBody',
    controlsSelector: '#jobsPagination',
    pageSizes: [25, 50, 100],
    pageSize: 50,
    storageKey: 'jobs',
    onFetch: function () {
      loadBackgroundJobs();
    }
  });

  // Refreshes can introduce types absent from the initial page.
  let _jobTypesRetries = 0;
  let _jobsRead = 0;
  function _populateJobTypes(jobTypes) {
    if (_disposed) return;
    const typeFilter = document.getElementById('jobTypeFilter');
    if (!typeFilter || !jobTypes || !jobTypes.length) return;
    if (typeof typeFilter.addOptions !== 'function') {
      if (_jobTypesRetries++ < 60) requestAnimationFrame(function () { _populateJobTypes(jobTypes); });
      return;
    }
    typeFilter.addOptions(jobTypes.map(function (jt) { return [jt, _jobTypeLabel(jt)]; }));
  }

  function _appendUnseenJobRows(existingHtml, nextHtml, unseenIds) {
    if (!nextHtml || !unseenIds.size) return existingHtml;
    const tpl = document.createElement('template');
    tpl.innerHTML = nextHtml;
    const kept = [];
    Array.from(tpl.content.children).forEach(function (el) {
      const jobId = el.getAttribute('data-job-id');
      if (jobId) {
        if (unseenIds.has(jobId)) kept.push(el.outerHTML);
        return;
      }
      const id = el.id || '';
      if (id.startsWith('jobDetail-') && unseenIds.has(id.slice('jobDetail-'.length))) {
        kept.push(el.outerHTML);
      }
    });
    return existingHtml + kept.join('');
  }

  /** @returns {Promise<boolean>} whether the jobs were actually loaded. */
  async function loadBackgroundJobs(options = {}) {
    const read = ++_jobsRead;
    const tbody = document.getElementById('jobsTableBody');
    if (!tbody) return false;

    GP.tableLoading(tbody, 7);

    const all = _jobsPaginator.pageSize === 'all';
    const ps = all ? 500 : _jobsPaginator.pageSize;
    const offset = ((_jobsPaginator.currentPage || 1) - 1) * ps;

    try {
      const typeFilter = document.getElementById('jobTypeFilter');
      let data;
      {
        let url = '/dashboard/api/v1/admin/system/jobs?limit=' + ps;
        const statusFilter = document.getElementById('jobStatusFilter');
        if (statusFilter && statusFilter.value) url += '&status=' + encodeURIComponent(statusFilter.value);
        if (typeFilter && typeFilter.value) url += '&type=' + encodeURIComponent(typeFilter.value);
        data = await apiCall(url + '&offset=' + offset, 'GET', null, { maxRetries: 1, timeoutMs: 10000, ...options, key: 'admin-jobs' });
        data.jobs = Array.isArray(data.jobs) ? data.jobs : [];
        let cursor = data.jobs.length;
        const seenIds = new Set(data.jobs.map(function (j) { return String(j.id); }));
        while (all && cursor < (data.total || 0)) {
          if (_disposed || read !== _jobsRead) return false;
          const next = await apiCall(url + '&offset=' + cursor, 'GET', null, { maxRetries: 1, timeoutMs: 10000, ...options, key: 'admin-jobs' });
          const nextJobs = Array.isArray(next.jobs) ? next.jobs : [];
          if (!nextJobs.length) break;
          cursor += nextJobs.length;
          const unseenIds = new Set();
          nextJobs.forEach(function (j) {
            const jid = String(j.id);
            if (!seenIds.has(jid)) {
              seenIds.add(jid);
              unseenIds.add(jid);
              data.jobs.push(j);
            }
          });
          if (typeof data.rows_html === 'string' && typeof next.rows_html === 'string') {
            data.rows_html = _appendUnseenJobRows(data.rows_html, next.rows_html, unseenIds);
          }
          data.total = next.total;
        }
      }
      if (_disposed || read !== _jobsRead) return false;
      if (!all && offset >= data.total && data.total > 0) {
        _jobsPaginator.currentPage = Math.ceil(data.total / ps);
        return loadBackgroundJobs(options);
      }

      if (data.job_types) _populateJobTypes(data.job_types);
      const historyEl = document.getElementById('jobsFailureHistory');
      if (historyEl && typeof data.history_html === 'string') {
        historyEl.innerHTML = data.history_html;
      }

      if (_disposed || read !== _jobsRead) return false;

      if (typeof data.rows_html === 'string') {
        tbody.innerHTML = data.rows_html;
      } else if (!data.jobs.length) {
        tbody.innerHTML = GP.emptyStateRow(7, t('No background jobs found'));
      }
      GP.tableLoaded(tbody);
      localizeTimes(tbody);
      restripeTable(tbody);
      GP.initTippy(tbody);
      _jobsPaginator.setServerTotal(data.total || 0);
      _bindJobActions(tbody);
      _resetJobSelection();
      if (options.quiet && data.failure_history && data.failure_history.available === false) {
        throw new Error(t('Failure history is unavailable. Refresh to try again.'));
      }
    } catch (err) {
      if (err?.superseded || _disposed || read !== _jobsRead) return false;
      if (!options.quiet || !tbody.children.length || tbody.querySelector('.table-loading-state')) {
        tbody.innerHTML = GP.errorStateRow(7, t('Failed to load jobs'), t('Retry'));
        GP.bindRetry(tbody, () => loadBackgroundJobs());
      }
      GP.tableLoaded(tbody);
      if (options.quiet) throw err;
      showToast(t('Failed to load jobs'), 'danger');
      return false;
    }
    return true;
  }

  function _bindJobActions(tbody) {
    if (!tbody) return;
    tbody.querySelectorAll('.btn-cancel-job').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        _cancelJob(btn.dataset.jobId, btn);
      });
    });
  }

  async function _cancelJob(jobId, btn) {
    if (!jobId) return;
    if (!await GP.confirmDialog({ message: t('Cancel this process?'), confirmText: t('Confirm') })) return;
    try {
      await _lock('cancelJob:' + jobId, async () => {
        setButtonLoading(btn, true);
        await apiCall('/api/v1/jobs/' + encodeURIComponent(jobId) + '/cancel', 'POST', { reason: t('Cancelled by admin') }, { maxRetries: 0 });
        showToast(t('Process cancelled'), 'warning');
        await loadBackgroundJobs();
      });
    } catch (err) {
      if (err.code !== 'LOCKED') showToast(t('Cancellation failed') + ': ' + err.message, 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  }
