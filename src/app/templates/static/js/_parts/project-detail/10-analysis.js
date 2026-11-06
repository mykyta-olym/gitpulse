  // Reuse the server projection for intelligence and optional AI cards.
  function refreshProjectCards() {
    const owner = pageOwner;
    const revision = analysisRevision;
    if (!owner.isConnected || (!CAN_EDIT && !document.getElementById('projectAnalysisResults'))) {
      return Promise.resolve(false);
    }
    return GP.coalesced('project-cards:' + PROJECT_ID + ':' + revision, async function () {
      if (!owner.isConnected || revision !== analysisRevision) return false;
      try {
        const html = await apiCall('/dashboard/projects/' + PROJECT_ID, 'GET', null,
          { responseType: 'text', timeoutMs: 10000, maxRetries: 0, key: 'project-cards' });
        if (!owner.isConnected || revision !== analysisRevision) return false;
        const doc = new DOMParser().parseFromString(html, 'text/html');
        if (!doc.getElementById(pageOwner.id)) return false;
        const grid = document.getElementById('glIntelligenceGrid');
        const nextGrid = doc.getElementById('glIntelligenceGrid');
        if (grid && nextGrid) {
          grid.replaceChildren(...nextGrid.childNodes);
          GP.applyDataDrivenStyles(grid);
          GP.initTippy(grid);
          window.localizeTimes(grid);
        }

        const results = document.getElementById('projectAnalysisResults');
        const nextResults = doc.getElementById('projectAnalysisResults');
        if (results && nextResults) {
          const search = document.getElementById('mrSearchInput')?.value || '';
          const risk = document.getElementById('mrRiskFilter')?.value || '';
          const currentPage = _mrPaginator?.currentPage || 1;
          results.replaceChildren(...nextResults.childNodes);
          Alpine.initTree(results);
          const searchInput = document.getElementById('mrSearchInput');
          const riskFilter = document.getElementById('mrRiskFilter');
          if (searchInput) searchInput.value = search;
          if (riskFilter) riskFilter.value = risk;
          _mrPaginator = null;
          bindFilters();
          renderMrPagination();
          if (_mrPaginator) {
            _mrPaginator.currentPage = currentPage;
            filterMrAnalyses();
          }
          GP.applyDataDrivenStyles(results);
          GP.initTippy(results);
          window.localizeTimes(results);
        }
        return true;
      } catch (_) {
        return false; // Background reads retain the last server-rendered state.
      }
    });
  }

  async function dismissLlmError(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    try {
      await _lock('dismissLlmError:' + PROJECT_ID, async () => {
        if (submitBtn) {
          setButtonLoading(submitBtn, true);
        }

        // Form POST with redirect:manual - cannot use apiCall (throws on non-2xx/opaque redirect)
        const csrfToken = window.GP?.csrfToken || form.querySelector('[name="csrf_token"]')?.value || '';
        const response = await fetch(form.action, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRF-Token': csrfToken,
          },
          body: `csrf_token=${encodeURIComponent(csrfToken)}`,
          redirect: 'manual',
        });

        if (response.ok || response.status === 303 || response.type === 'opaqueredirect') {
          const card = form.closest('.llm-error-card, .info-card, .card');
          if (card) {
            GP.collapseAndRemove(card, function() {
              // If no analysis results exist, restore the empty state
              const analysisList = document.getElementById('mrAnalysisList');
              if (!analysisList || !analysisList.children.length) {
                document.querySelector('.empty-state')?.classList.remove('d-none');
              }
            });
          }
          showToast(t('LLM error dismissed!'), 'success');
        } else {
          showToast(t('Failed to dismiss error'), 'danger');
        }
      });
    } catch (error) {
      if (error.code !== 'LOCKED') showToast(error.message || t('Failed to dismiss error'), 'danger');
    } finally {
      if (submitBtn) {
        setButtonLoading(submitBtn, false);
      }
    }

    return false;
  }

  function setAnalysisButtonState(isRunning) {
    setButtonLoading(document.getElementById('runAnalysisBtn'), isRunning);
  }

  async function refreshAnalysisResult() {
    const revision = analysisRevision;
    const refreshed = await refreshProjectCards();
    if (!pageOwner.isConnected || revision !== analysisRevision) return false;
    const progress = document.getElementById('analysisProgress');
    const retry = document.getElementById('refreshAnalysisBtn');
    if (refreshed) {
      if (progress?.classList.contains('gitlab-alert-success') || document.querySelector('.llm-error-card')) {
        progress?.classList.add('d-none');
      }
      retry?.classList.add('d-none');
    } else {
      const subtitle = document.getElementById('analysisSubtitle');
      if (subtitle) subtitle.textContent = t('Failed to refresh project data');
      retry?.classList.remove('d-none');
    }
    return refreshed;
  }

  window.refreshProjectAnalysis = function() {
    return GP.refreshRegion({
      button: document.getElementById('refreshAnalysisBtn'),
      region: document.getElementById('analysisProgress'),
      load: refreshAnalysisResult,
    });
  };

  function updateAnalysisUI(data) {
    const progress = document.getElementById('analysisProgress');
    if (!progress || !pageOwner.isConnected) return false;

    // Normalize SSE pubsub format (progress=object, percent=int) -> REST format
    if (data && typeof data.progress === 'object' && data.progress !== null) {
      const nested = data.progress;
      data = Object.assign({}, data, nested);
      data.progress = data.percent;
    }

    const statusText = progress.querySelector('#analysisStatusText');
    const subtitle = progress.querySelector('#analysisSubtitle');
    const spinner = progress.querySelector('#analysisSpinner');
    const progressInner = progress.querySelector('#analysisProgressBar .progress-bar');

    const status = String(data?.status || '').toLowerCase();
    if (!['running', 'completed', 'failed', 'cancelled', 'none'].includes(status)) return false;
    if (analysisCompletionHandled) return true;
    document.getElementById('refreshAnalysisBtn')?.classList.add('d-none');

    if (status === 'running') {
      progress.classList.remove('d-none', 'gitlab-alert-success', 'gitlab-alert-danger');
      progress.classList.add('gitlab-alert-info');
      progress.querySelector('#analysisProgressBar')?.classList.remove('d-none');

      // Hide old error card - new analysis in progress
      const oldErrorCard = document.querySelector('.llm-error-card');
      if (oldErrorCard) oldErrorCard.remove();

      // Hide empty-state placeholder as soon as analysis starts
      const emptyEl = progress.closest('.card-body')?.querySelector('.empty-state');
      if (emptyEl) emptyEl.classList.add('d-none');

      const total = data?.total || 0;
      const analyzed = data?.analyzed || 0;
      const failedCount = data?.failed || 0;
      const skippedCount = data?.skipped || 0;
      const pct = typeof data.progress === 'number' && Number.isFinite(data.progress)
        ? Math.max(0, Math.min(100, data.progress)) : null;
      const currentMr = data?.current_mr;
      const done = analyzed + failedCount + skippedCount;

      if (statusText) {
        if (currentMr && total) {
          if (GITLAB_URL && PROJECT_PATH) {
            const mrUrl = GITLAB_URL + '/' + PROJECT_PATH + '/-/merge_requests/' + currentMr;
            statusText.innerHTML = `${_escapeHtml(t('Analyzing MR'))} <a href="${_escapeHtml(mrUrl)}" target="_blank" rel="noopener noreferrer">!${currentMr}</a>  (${done}/${total})`;
          } else {
            statusText.textContent = `${t('Analyzing MR')} !${currentMr}...  (${done}/${total})`;
          }
        } else {
          statusText.textContent = data?.message || t('Analyzing merge requests with AI...');
        }
      }
      if (subtitle) {
        if (total) {
          const parts = [];
          if (analyzed) parts.push(`${analyzed} ${t('analyzed')}`);
          if (failedCount) parts.push(`${failedCount} ${t('failed')}`);
          if (skippedCount) parts.push(`${skippedCount} ${t('cached')}`);
          subtitle.textContent = parts.length ? parts.join(', ') : t('Starting analysis...');
        } else {
          subtitle.textContent = t('Preparing merge requests...');
        }
      }
      if (spinner) {
        if (!spinner.querySelector('.gp-spinner')) spinner.innerHTML = GP.renderSpinnerHtml('sm');
      }
      if (progressInner) {
        if (total && pct !== null) {
          progressInner.style.setProperty('--progress', pct + '%');
          progressInner.classList.remove('is-indeterminate');
          progressInner.parentElement.setAttribute('aria-valuenow', pct);
        } else {
          progressInner.style.removeProperty('--progress');
          progressInner.classList.add('is-indeterminate');
          progressInner.parentElement.removeAttribute('aria-valuenow');
        }
      }
      setAnalysisButtonState(true);

      updateGlobalJob(t('Analyzing...'), 'analysis');
      if (pct !== null) updateGlobalJobProgress('analysis', pct);
      return true;
    }

    if (status !== 'none') {
      analysisCompletionHandled = true;
      stopPolling();
      _lastAnalysisRefreshAt = Date.now();
    }

    if (status === 'completed') {
      progress.classList.remove('d-none', 'gitlab-alert-danger', 'gitlab-alert-info');
      progress.classList.add('gitlab-alert-success');
      if (statusText) {
        statusText.textContent = t('Analysis complete!');
      }
      if (subtitle) {
        subtitle.textContent = t('Refreshing metrics...');
      }
      if (spinner) spinner.innerHTML = GP.iconSvg('check-circle', 'md');
      if (progressInner) {
        progressInner.classList.remove('is-indeterminate');
        progressInner.style.setProperty('--progress', '100%');
        progressInner.parentElement.setAttribute('aria-valuenow', '100');
      }
      refreshProjectData();
      window.refreshProjectAnalysis();
      const doneMsg = t('AI analysis completed successfully');
      GP.finishGlobalJobOrToast('analysis', doneMsg, 'done', { flash: true });
      setAnalysisButtonState(false);
      return true;
    }

    if (status === 'failed' || status === 'cancelled') {
      progress.classList.remove('d-none', 'gitlab-alert-success');
      progress.classList.toggle('gitlab-alert-info', status === 'cancelled');
      progress.classList.toggle('gitlab-alert-danger', status === 'failed');
      if (statusText) {
        statusText.textContent = status === 'cancelled'
          ? t('Analysis cancelled')
          : t('Analysis failed');
      }
      if (subtitle) {
        subtitle.textContent = data?.message || t('Please try again.');
      }
      if (spinner) spinner.innerHTML = GP.iconSvg(status === 'cancelled' ? 'minus' : 'x-circle', 'md');
      // A failure or cancellation has no completed percentage.
      progress.querySelector('#analysisProgressBar')?.classList.add('d-none');
      completeGlobalJob('analysis', data?.message || (status === 'cancelled'
        ? t('Analysis cancelled') : t('Analysis failed')), 'error');
      window.refreshProjectAnalysis();
      setAnalysisButtonState(false);
      return true;
    }

    // Only an explicit idle response can clear an unconfirmed pending state.
    if (!analysisCompletionHandled) {
      hideGlobalJob('analysis');
      progress.classList.add('d-none');
      setAnalysisButtonState(false);
    }
    stopPolling();
    return true;
  }

  async function checkAnalysisStatus() {
    if (_sseDelivering || analysisReading || !pageOwner.isConnected) return;
    const read = {};
    analysisReading = read;
    const revision = analysisRevision;
    try {
      const data = await apiCall(`/dashboard/projects/${PROJECT_ID}/llm-analysis-status`, 'GET', null, {
        key: 'analysis-status:' + PROJECT_ID,
        timeoutMs: 12000,
        maxRetries: 1,
      });
      if (!pageOwner.isConnected || revision !== analysisRevision || _sseDelivering) return;
      updateAnalysisUI(data);
    } catch (error) {
      if (!pageOwner.isConnected || revision !== analysisRevision || error?.superseded) return;
      const subtitle = document.getElementById('analysisSubtitle');
      if (subtitle) subtitle.textContent = t('Reconnecting...');
    } finally {
      if (analysisReading === read) analysisReading = null;
    }
  }

  function stopPolling() {
    analysisRevision++;
    analysisGeneration++;
    analysisReading = null;
    analysisPoller?.close();
    analysisPoller = null;
    _sseDelivering = false;
    if (analysisFallbackTimerId) {
      clearInterval(analysisFallbackTimerId);
      analysisFallbackTimerId = null;
    }
  }

  function startPolling() {
    if (!MAY_SEE_ANALYSIS || analysisPoller || analysisFallbackTimerId || !pageOwner.isConnected) return;
    analysisCompletionHandled = false;
    const generation = analysisGeneration;

    function fallback() {
      if (generation !== analysisGeneration) return;
      stopPolling();
      _startFallbackPolling();
    }
    function receive(event) {
      if (generation !== analysisGeneration || analysisCompletionHandled) return;
      if (!pageOwner.isConnected) { stopPolling(); return; }
      let data;
      try { data = JSON.parse(event.data); } catch (_) { fallback(); return; }
      analysisRevision++;
      _sseDelivering = true;
      if (!updateAnalysisUI(data)) fallback();
    }
    const stream = GP.sse({
      url: `/dashboard/projects/${PROJECT_ID}/llm-analysis-stream`,
      withCredentials: true,
      events: { message: receive, complete: receive },
      onFailure() { if (generation === analysisGeneration) _sseDelivering = false; },
      onGiveUp: fallback,
      onBlocked: fallback,
    });
    if (stream.active) analysisPoller = stream;
    else stream.close();
    checkAnalysisStatus();
  }

  function _startFallbackPolling() {
    if (analysisPoller || analysisFallbackTimerId || !pageOwner.isConnected) return;
    analysisFallbackTimerId = setInterval(checkAnalysisStatus, 3000);
    checkAnalysisStatus();
  }

  function retryProjectAnalysis() {
    const button = document.getElementById('runAnalysisBtn');
    if (button && !button.disabled) {
      button.click();
    }
  }

  function bindAnalysisForm() {
    const form = document.getElementById('llmAnalysisForm');
    if (!form || form.dataset.bound === '1') {
      return;
    }

    form.dataset.bound = '1';

    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      if (typeof isGlobalJobRunning === 'function' && typeof confirmProcessRestart === 'function') {
        if (isGlobalJobRunning('analysis') && !await confirmProcessRestart('analysis', 'AI Analysis')) {
          return;
        }
      }

      try {
        await _lock('llmAnalysis:' + PROJECT_ID, async () => {
          setAnalysisButtonState(true);

          await apiCall(`/dashboard/projects/${PROJECT_ID}/llm-analyze`, 'POST');
          showToast(t('Analysis started'), 'success');
          if (typeof deferGlobalJob === 'function') {
            deferGlobalJob(
              t('Analyzing: %name').replace('%name', PROJECT_NAME),
              'analysis',
              { courseId: COURSE_ID, teamId: TEAM_ID, projectId: PROJECT_ID, pollUrl: `/dashboard/projects/${PROJECT_ID}/llm-analysis-status`, localIndicatorSelector: '#analysisProgress', cancelUrl: `/dashboard/projects/${PROJECT_ID}/llm-analysis-cancel` }
            );
          }
          stopPolling();
          startPolling();
        });
      } catch (err) {
        if (err.code !== 'LOCKED') {
          showToast(err.message || t('Failed to start analysis'), 'danger');
          setAnalysisButtonState(false);
        }
      }
    });
  }

  function filterMrAnalyses() {
    const searchInput = document.getElementById('mrSearchInput');
    const riskFilter = document.getElementById('mrRiskFilter');
    if (!searchInput || !riskFilter || !_mrPaginator) return;

    const query = searchInput.value.trim().toLowerCase();
    const risk = riskFilter.value;

    const filtered = _mrPaginator._allRows.filter((el) => {
      const mrRisk = el.dataset.mrRisk || '';
      const mrSearchText = el.dataset.mrSearch || '';

      const matchesRisk = !risk || mrRisk === risk;
      const matchesQuery = !query || mrSearchText.includes(query);

      return matchesRisk && matchesQuery;
    });

    _mrPaginator.setFilteredRows(filtered);

    const emptyState = document.getElementById('mrAnalysisFiltersEmpty');
    if (emptyState) {
      if (filtered.length === 0 && _mrPaginator._allRows.length > 0) {
        emptyState.classList.remove('d-none');
      } else {
        emptyState.classList.add('d-none');
      }
    }

    const countDiv = document.getElementById('mrFilteredCount');
    if (countDiv) {
      if (query || risk) {
        countDiv.textContent = t('Found %n matching merge requests').replace('%n', filtered.length);
        countDiv.classList.remove('d-none');
      } else {
        countDiv.classList.add('d-none');
      }
    }

  }

  function bindFilters() {
    const searchInput = document.getElementById('mrSearchInput');
    const riskFilter = document.getElementById('mrRiskFilter');

    if (searchInput && !searchInput.dataset.bound) {
      searchInput.dataset.bound = '1';
      searchInput.addEventListener('input', filterMrAnalyses);
    }
    if (riskFilter && !riskFilter.dataset.bound) {
      riskFilter.dataset.bound = '1';
      riskFilter.addEventListener('change', filterMrAnalyses);
    }
  }

  function onReady() {
    bindAnalysisForm();
    bindFilters();

    if (ANALYSIS_STARTED && MAY_SEE_ANALYSIS) {
      setAnalysisButtonState(true);
      if (typeof deferGlobalJob === 'function') {
        deferGlobalJob(
          t('Analyzing: %name').replace('%name', PROJECT_NAME),
          'analysis',
          { courseId: COURSE_ID, teamId: TEAM_ID, projectId: PROJECT_ID, pollUrl: `/dashboard/projects/${PROJECT_ID}/llm-analysis-status`, localIndicatorSelector: '#analysisProgress', cancelUrl: `/dashboard/projects/${PROJECT_ID}/llm-analysis-cancel` }
        );
      }
      startPolling();
    }
  }

  window.dismissLlmError = dismissLlmError;
  window.retryProjectAnalysis = retryProjectAnalysis;

  // Run checks - calls the selective run-checks endpoint with selected checks
  async function runSelectedChecks() {
    if (!CAN_EDIT || !TEAM_ID) return;

    await (window.GP?.runScopedChecksProcess || window.runScopedChecksProcess)?.({
      endpoint: `/api/v1/teams/${TEAM_ID}/run-checks`,
      jobKey: 'run_checks:team:' + TEAM_ID,
      lockKey: 'runChecks:' + TEAM_ID,
      guardScopes: scoringScope('project:' + PROJECT_ID),
      label: document.querySelector('#runChecksModal .rcm-scope-name')?.textContent.trim(),
      button: document.getElementById('btnRunChecks'),
      courseId: COURSE_ID,
      teamId: TEAM_ID,
      projectId: PROJECT_ID,
      onComplete(detail) {
        if (detail.status === 'done') refreshProjectData();
      },
    });
  }
  window.runSelectedChecks = runSelectedChecks;

  // -- Run Checks modal: select/deselect/reset/search are handled by the
  // shared partial's inline init (`partials/_run_checks_modal.html`).
  // We only wire the submit button here.
  document.getElementById('btnRunChecks')?.addEventListener('click', () => { runSelectedChecks(); });
