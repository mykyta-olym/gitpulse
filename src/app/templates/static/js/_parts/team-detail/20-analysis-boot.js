  const analysisPageOwner = document.getElementById('gp-team-detail-config');
  let analysisProbe = null;
  let analysisProbeRevision = 0;

  function invalidateAnalysisProbe() {
    analysisProbeRevision++;
    analysisProbe = null;
  }

  function resumeTeamAnalysis() {
    if (!MAY_SEE_ANALYSIS || document.hidden || !analysisPageOwner.isConnected
        || analysisProbe || isGlobalJobRunning('analysis')) return;
    const revision = analysisProbeRevision;
    const read = GP.apiCall(`/dashboard/teams/${TEAM_ID}/llm-analysis-status`, 'GET', null, { maxRetries: 0 });
    analysisProbe = read;
    read.then(data => {
      if (revision !== analysisProbeRevision || !analysisPageOwner.isConnected || document.hidden) return;
      if (!['running', 'queued', 'enqueued'].includes(data?.status) || isGlobalJobRunning('analysis')) return;
      const message = t('Analyzing: %name').replace('%name', TEAM_NAME);
      // The shared job bar owns progress, cancellation, reconnects and completion.
      showGlobalJob(message, 'analysis', {
        courseId: COURSE_ID, teamId: TEAM_ID, passive: true, baseMessage: message,
        pollUrl: `/dashboard/teams/${TEAM_ID}/llm-analysis-status`,
        cancelUrl: `/dashboard/teams/${TEAM_ID}/llm-analysis-cancel`,
      });
      if (Number.isFinite(data.progress)) updateGlobalJobProgress('analysis', data.progress);
    }).catch(() => { /* Retry discovery on return to this page; transport failure is not completion. */ })
      .finally(() => { if (analysisProbe === read) analysisProbe = null; });
  }

  function _boot() {
    const url = new URL(window.location.href);
    if (url.searchParams.has('analysis_started')) {
      url.searchParams.delete('analysis_started');
      window.history.replaceState(window.history.state, '', url);
    }
    resumeTeamAnalysis();

    const csrfToken = window._csrfToken || '';

    if (typeof setupGitLabAutofill === 'function') {
      setupGitLabAutofill('#projectGitLabUrl', {
        project: {
          '#projectGitlabId': 'gitlab_id',
          '#projectPath': 'path',
          '#projectDisplayName': 'name'
        }
      }, csrfToken);
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _boot);
  } else {
    _boot();
  }
  
  // Cleanup pollers on page unload
  const onBeforeUnload = () => {
    invalidateAnalysisProbe();
    if (syncStreamCtrl) { syncStreamCtrl.close(); syncStreamCtrl = null; }
    if (_checksPollId) { clearInterval(_checksPollId); _checksPollId = null; }
    _disconnectTeamSSE();
    _stopFallbackPolling();
  };
  window.addEventListener('beforeunload', onBeforeUnload);
