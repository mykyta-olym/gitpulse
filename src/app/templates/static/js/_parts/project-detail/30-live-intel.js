  // -- Generic table pagination (delegates to ClientPaginator) --
  const _tablePaginators = {};
  function initTablePagination(bodyId, paginationId, pageSize) {
    const tbody = document.getElementById(bodyId);
    const pagDiv = document.getElementById(paginationId);
    if (!tbody || !pagDiv) return null;

    const paginator = new ClientPaginator({
      tbodySelector: '#' + bodyId,
      controlsSelector: '#' + paginationId,
      pageSize,
      scrollOnChange: false,
      pageSizes: [25, 50, 100],
    });
    paginator.render();
    _tablePaginators[bodyId] = paginator;
    return paginator;
  }

  // Init table pagination for members
  initTablePagination('projectMembersBody', 'projectMembersPagination', 50);

  /* -- Page unload - cleanup pollers, warn if analysis running -- */
  onBeforeUnload = function (e) {
    stopPolling();
    if (_checksFallbackPollId) { clearInterval(_checksFallbackPollId); _checksFallbackPollId = null; }
    _disconnectProjectSSE();
    _stopProjectPolling();
    if (_ciPollTimer) { clearInterval(_ciPollTimer); _ciPollTimer = null; }
    // Global job bar auto-detected by core.js hasUnsavedState()
  };
  window.addEventListener('beforeunload', onBeforeUnload);

  // Auto-refresh project data when returning to this tab
  onTabVisible = () => {
    refreshProjectData().catch(() => {});
  };
  document.addEventListener('gp-tab-visible', onTabVisible);

  // -- SSE-first live data stream (polling is fallback only) --
  let _projSSE = null;
  // The server already rendered fresh member rows, bottlenecks and the GitLab
  // Intelligence cards (protected branches / contributors /
  // repository stats) for this page, so the FIRST SSE `connected` (fired right
  // after the page loads) must NOT trigger any /live-data fetch or intel
  // repaint - that is the blank-then-JS flicker. Only reconnects (after a
  // dropout) and real change events refresh.
  let _projConnectedOnce = false;
  let _projPollTimer = null;
  const _PROJ_SSE_MAX = GP.SSE_MAX_ERRORS || 5;
  const _PROJ_POLL_MS = 60000;

  function _connectProjectSSE() {
    _disconnectProjectSSE();
    if (!TEAM_ID) { _startProjectPolling(); return; }
    _projSSE = GP.sse({
      url: '/api/v1/teams/' + TEAM_ID + '/stream',
      maxErrors: _PROJ_SSE_MAX,
      events: {
        connected: function() {
          // First connect: the server already rendered project data AND the
          // GitLab Intelligence cards, so skip every repaint to avoid the
          // blank-then-JS flicker. Only genuine reconnects refresh.
          if (_projConnectedOnce) {
            refreshProjectData().catch(function() {});
            refreshProjectCards();
          } else {
            _projConnectedOnce = true;
          }
        },
        update: function(e) {
          try {
            const d = JSON.parse(e.data);
            if (d && d.event === 'settings_changed') { reloadKeepScroll(); return; }
          } catch (_) {}
          refreshProjectData().catch(function() {});
          refreshProjectCards();
        },
      },
      onGiveUp: _startProjectPolling,
      onBlocked: _startProjectPolling,
    });
  }
  function _disconnectProjectSSE() {
    if (_projSSE) { _projSSE.close(); _projSSE = null; }
  }
  function _startProjectPolling() {
    if (_projPollTimer) return;
    _projPollTimer = setInterval(function() {
      if (document.visibilityState === 'visible') refreshProjectData().catch(function() {});
    }, _PROJ_POLL_MS);
  }
  function _stopProjectPolling() {
    if (_projPollTimer) { clearInterval(_projPollTimer); _projPollTimer = null; }
  }
  _connectProjectSSE();

  let _pendingRefresh = false;
  onVisibilityChangeIntel = function() {
    if (document.visibilityState === 'hidden') {
      _disconnectProjectSSE();
      _stopProjectPolling();
      stopPolling();
      if (_checksFallbackPollId) {
        clearInterval(_checksFallbackPollId);
        _checksFallbackPollId = null;
      }
      return;
    }
    // Re-establish SSE or polling
    if (!_projSSE?.active && !_projPollTimer) {
      _projSSE?.resetErrors();
      _connectProjectSSE();
    }
    // Restart analysis polling if it was dropped while tab was in background
    if (!analysisPoller && !analysisFallbackTimerId && MAY_SEE_ANALYSIS) {
      const generation = analysisGeneration;
      apiCall('/dashboard/projects/' + PROJECT_ID + '/llm-analysis-status', 'GET', null,
        { key: 'analysis-discovery:' + PROJECT_ID, maxRetries: 0 })
        .then(function(data) {
          if (pageOwner.isConnected && generation === analysisGeneration && data?.status === 'running') startPolling();
        })
        .catch(function() {});
    }
    // If a job completed while we were hidden, refresh now
    if (_pendingRefresh) {
      _pendingRefresh = false;
      refreshProjectData();
      refreshProjectCards();
    }
  };
  document.addEventListener('visibilitychange', onVisibilityChangeIntel);

  // Pause SSE & polling when backend is unreachable
  let _projHealthDown = false;
  onHealthChange = function (e) {
    if (e.detail?.current === 'down' && !_projHealthDown) {
      _projHealthDown = true;
      _disconnectProjectSSE();
      _stopProjectPolling();
    } else if (e.detail?.current !== 'down' && _projHealthDown) {
      _projHealthDown = false;
      _projSSE?.resetErrors();
      _connectProjectSSE();
    }
  };
  document.addEventListener('gp-health-change', onHealthChange);

  // Auto-refresh project data when any relevant job completes
  let _lastAnalysisRefreshAt = 0;
  onJobCompleteProject = function(e) {
    const jt = e.detail?.jobType || '';
    const st = e.detail?.status;
    if (st !== 'done' && st !== 'error') return;
    if (!GP.jobAffectsScope(e.detail, {
      courseId: COURSE_ID, teamId: TEAM_ID, projectId: PROJECT_ID,
    })) return;
    // Skip duplicate refresh if analysis completion already triggered one recently
    if (jt === 'analysis' && Date.now() - _lastAnalysisRefreshAt < 5000) return;
    if (jt === 'analysis') _lastAnalysisRefreshAt = Date.now();
    if (document.visibilityState === 'visible') {
      refreshProjectData();
      refreshProjectCards();
    } else {
      _pendingRefresh = true;
    }
  };
  window.addEventListener('gp:job-complete', onJobCompleteProject);


  // -- Toggle Member Exclusion (project page) --
  async function toggleExclusion(studentId, teamId) {
    if (!CAN_EDIT) { showToast(t('Not authorized'), 'warning'); return; }
    await GP.toggleMemberExclusion({
      studentId,
      teamId,
      scope: scoringScope('project:' + PROJECT_ID),
      onRefresh: refreshProjectData,
    });
  }
  window.toggleExclusion = toggleExclusion;

  // Issues-to-Address -> scroll to affected student row in members table
  onDocumentClickScrollToMember = (e) => {
    const link = e.target.closest?.('[data-scroll-to-member]');
    if (!link) return;
    // Always cancel the navigation - the href is purely a fallback anchor and
    // if the row is filtered out (e.g. Direct-only filter) following #member-{id}
    // just scrolls the page to the top.
    e.preventDefault();
    const sid = link.getAttribute('data-scroll-to-member');
    if (!sid) return;
    const row = document.querySelector(`tr[data-student-id="${sid}"]`);
    if (!row) {
      try {
        showToast(
          t('Member is hidden by an active filter'),
          'info',
        );
      } catch (_) {}
      return;
    }

    // If client pagination is active on the members table and the row is on another page, navigate there first
    const paginator = _tablePaginators && _tablePaginators['projectMembersBody'];
    if (paginator && paginator.filteredRows) {
      const idx = paginator.filteredRows.indexOf(row);
      if (idx !== -1 && paginator.pageSize !== 'all') {
        const targetPage = Math.floor(idx / paginator.pageSize) + 1;
        if (paginator.currentPage !== targetPage) {
          paginator.goToPage(targetPage, false);
        }
      }
    }

    // Scroll ONLY the .gl-page-content container (not window/body). Default
    // scrollIntoView walks up every scrollable ancestor and shifts app chrome.
    GP.scrollWithinPageContent(row, { block: 'center' });
    GP.motion.highlight(row);
  };
  document.addEventListener('click', onDocumentClickScrollToMember);

  /* ==========================================
   *  ISSUES TO ADDRESS - Horizontal Bar Chart
   *  Reads #issuesToAddressData JSON, renders a Chart.js horizontal bar
   *  (% of group affected per check), colored by severity. Click a bar to
   *  expand the affected-students panel below.
   * ========================================== */
  let issuesChart = null;

  function _severityColor(sev) {
    const colors = (window.GP && window.GP.chartTheme && window.GP.chartTheme.colors) || {};
    if (sev === 'high') return colors.red || '#ec5941';
    if (sev === 'med')  return colors.yellow || '#c17d10';
    return colors.brand || colors.blue || '#428fdc';
  }

  function _renderIssueDetail(issue) {
    const el = document.getElementById('issuesChartDetail');
    if (!el) return;
    if (!issue) {
      el.hidden = true;
      el.innerHTML = '';
      el.className = 'issues-chart-detail';
      return;
    }
    const sev = issue.severity === 'high' || issue.severity === 'med' || issue.severity === 'low' ? issue.severity : 'low';
    el.className = `issues-chart-detail issues-chart-detail--${sev}`;
    const students = Array.isArray(issue.students) ? issue.students : [];
    const title = `${issue.check_id} - ${issue.name}`;
    const closeLabel = t('Close');
    let html = '';
    html += GP.closeButtonHtml(closeLabel, 'issues-chart-detail__close', { 'issues-detail-close': '' });
    html += '<div class="issues-chart-detail__header">';
    html += GP.badgeHtml(issue.severity_label || '', { high: 'danger', med: 'warning' }[sev] || 'info');
    html += `<h4 class="issues-chart-detail__title">${_escapeHtml(title)}</h4>`;
    html += `<span class="issues-chart-detail__stat">${issue.affected}/${issue.total} · ${issue.share_pct}%`;
    if (issue.weight_pct > 0) html += ` · ${issue.weight_pct}% ${_escapeHtml(t('weight'))}`;
    html += '</span></div>';
    if (students.length) {
      html += '<ul class="issues-chart-detail__list">';
      students.forEach((st) => {
        const name = _escapeHtml(st.name || st.username || 'Unknown');
        const handle = st.username && st.username !== st.name
          ? ` <span class="muted">@${_escapeHtml(st.username)}</span>`
          : '';
        const detail = st.detail
          ? `<p class="issues-chart-detail__note">${_escapeHtml(st.detail)}</p>`
          : '';
        html += `<li><a href="#" data-scroll-to-member="${_escapeHtml(String(st.id))}">${name}${handle}</a>${detail}</li>`;
      });
      html += '</ul>';
    }
    el.innerHTML = html;
    el.hidden = false;
    /* Fades in on every re-render, not only the first. As a keyframe on the
       base class it fired once per element lifetime, so picking a second issue
       swapped the panel's contents with no motion at all. */
    GP.motion.panelIn(el);
    // Scroll ONLY the scrollable page container; nearest keeps already-visible
    // details stable and avoids touching the browser viewport.
    GP.scrollWithinPageContent(el, { block: 'nearest', offset: 24 });
  }

  function initIssuesChart(opts) {
    if (!pageOwner.isConnected) return;
    const canvas = document.getElementById('issuesChart');
    const dataEl = document.getElementById('issuesToAddressData');
    if (!canvas || !dataEl || typeof Chart === 'undefined') return;
    // Entrance animation plays on the FIRST reveal only. Live-data re-renders
    // (exclude/include, run-checks, role change) replace the whole container -
    // they pass { animate: false } so the bars never replay on every refresh.
    const _animate = !(opts && opts.animate === false);

    let issues = [];
    try { issues = JSON.parse(dataEl.textContent || '[]'); } catch (_) { return; }
    // Guard: if payload is empty or malformed, tear down any prior chart and
    // collapse the canvas wrap so the card doesn't hold a 280px empty frame.
    if (!Array.isArray(issues) || !issues.length) {
      if (issuesChart) { try { issuesChart.destroy(); } catch (_) {} issuesChart = null; }
      if (canvas.parentElement) canvas.parentElement.style.height = '0px';
      return;
    }

    // The first draw waits until the canvas scrolls in (GP.drawOnEntry, the
    // one every chart uses); a later re-render on the same canvas is drawn at
    // once.
    if (canvas.dataset.gpEntered !== '1') {
      GP.drawOnEntry(canvas, function () { initIssuesChart({ animate: _animate }); });
      return;
    }

    if (issuesChart) { try { issuesChart.destroy(); } catch (_) {} issuesChart = null; }

    const chartColors = (window.GP && window.GP.chartTheme && window.GP.chartTheme.colors) || {};
    const labels = issues.map((i) => `${i.check_id}  ${i.name}`);
    const pcts = issues.map((i) => i.share_pct);
    const _alpha = (window.GP && window.GP.chartTheme && window.GP.chartTheme.alpha) || function (c) { return c; };
    const fills = issues.map((i) => _alpha(_severityColor(i.severity), 0.8));
    const borders = issues.map((i) => _severityColor(i.severity));
    // Scale the x-axis to the data: if the worst bar is 30%, showing 0-100 makes
    // every bar look tiny and leaves a lot of empty space. Round up to the next
    // 10% above the max (min 20%, max 100%).
    const maxPct = pcts.reduce((m, v) => Math.max(m, v), 0);
    const xMax = Math.min(100, Math.max(20, Math.ceil((maxPct + 5) / 10) * 10));

    // Cap overall chart height and bar thickness so 3 bars look fine and 12 bars don't scroll forever.
    const barH = issues.length <= 4 ? 36 : issues.length <= 8 ? 28 : 24;
    const canvasH = Math.min(380, issues.length * barH + 40);
    if (canvas.parentElement) {
      canvas.parentElement.style.height = canvasH + 'px';
      canvas.parentElement.style.minHeight = '';
    }

    const _chartCfg = {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: t('% of group affected'),
          data: pcts,
          backgroundColor: fills,
          borderColor: borders,
          borderWidth: 2,
          borderRadius: 6,
          borderSkipped: false,
          barPercentage: 0.72,
          categoryPercentage: 0.85,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        // Debounce resize-driven re-layouts so rapid viewport changes (e.g.
        // sidebar collapse, window resize) don't thrash the page layout.
        resizeDelay: 120,
        // The bar charts' one entrance (GP.barsEntrance), on the first reveal
        // only: live-data re-renders pass `animate: false`, so the bars never
        // replay on every refresh.
        animation: _animate ? GP.barsEntrance(canvas) : false,
        layout: { padding: { left: 4, right: 16 } },
        scales: {
          x: {
            beginAtZero: true,
            max: xMax,
            // Neutral fallback readable on both themes (white-6% was invisible
            // on the light card if chartColors had not resolved yet).
            grid: { color: chartColors.grid || 'rgba(128,128,128,0.15)' },
            ticks: { callback: (v) => v + '%', stepSize: xMax <= 40 ? 10 : 20 },
          },
          y: {
            grid: { display: false },
            ticks: { font: { size: 12, weight: '500' }, color: chartColors.text || '#999' },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) => {
                const i = items[0]?.dataIndex;
                if (i == null) return '';
                const iss = issues[i];
                return `${iss.check_id} - ${iss.name}`;
              },
              label: (ctx) => {
                const iss = issues[ctx.dataIndex];
                const lines = [
                  `${iss.share_pct}% ${t('of group')} (${iss.affected}/${iss.total})`,
                ];
                if (iss.weight_pct > 0) {
                  lines.push(`${t('Weight')}: ${iss.weight_pct}%`);
                }
                lines.push(`${t('Severity')}: ${iss.severity_label || iss.severity}`);
                lines.push(t('Click for affected students'));
                return lines;
              },
            },
          },
        },
        onClick: (_evt, elements) => {
          if (!elements || !elements.length) return;
          const idx = elements[0].index;
          _renderIssueDetail(issues[idx]);
        },
        onHover: (evt, elements) => {
          if (evt.native && evt.native.target) {
            evt.native.target.style.cursor = elements.length ? 'pointer' : 'default';
          }
        },
      },
    };
    try {
      issuesChart = new Chart(canvas.getContext('2d'), _chartCfg);
    } catch (err) {
      // Never let a Chart.js init failure break the rest of the page layout.
      try { console.error('[issues-chart] init failed:', err); } catch (_) {}
      if (canvas.parentElement) canvas.parentElement.style.height = '0px';
      issuesChart = null;
    }
  }

  function _boot() {
    onReady();
    renderMrPagination();
    initIssuesChart();
    // Delegated close for Issues-to-Address detail panel.
    onDocumentClickCloseIssueDetail = (e) => {
      if (e.target.closest && e.target.closest('[data-issues-detail-close]')) {
        _renderIssueDetail(null);
      }
    };
    document.addEventListener('click', onDocumentClickCloseIssueDetail);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _boot);
  } else {
    _boot();
  }

  onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-project-detail-config') || target.id === 'gp-project-detail-config')) {
      GP.projectDetailCleanup();
    }
  };
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.projectDetailCleanup = () => {
    if (_checksFallbackPollId) { clearInterval(_checksFallbackPollId); _checksFallbackPollId = null; }
    if (_ciPollTimer) { clearInterval(_ciPollTimer); _ciPollTimer = null; }
    _disconnectProjectSSE();
    _stopProjectPolling();
    stopPolling();

    if (issuesChart) { issuesChart.destroy(); issuesChart = null; }

    window.removeEventListener('beforeunload', onBeforeUnload);
    document.removeEventListener('gp-tab-visible', onTabVisible);
    document.removeEventListener('visibilitychange', onVisibilityChangeIntel);
    document.removeEventListener('gp-health-change', onHealthChange);
    window.removeEventListener('gp:job-complete', onJobCompleteProject);
    document.removeEventListener('click', onDocumentClickScrollToMember);
    document.removeEventListener('click', onDocumentClickCloseIssueDetail);
    document.removeEventListener('click', onMrHistoryClick);
    document.removeEventListener('DOMContentLoaded', _boot);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };
  GP.activePageCleanup = GP.projectDetailCleanup;
