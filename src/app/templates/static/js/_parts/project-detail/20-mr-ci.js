  function renderMrPagination() {
    const list = document.getElementById('mrAnalysisList');
    const pagDiv = document.getElementById('mrPaginationBottom');
    if (!list || !pagDiv) return;

    if (!_mrPaginator) {
      _mrPaginator = new ClientPaginator({
        tbodySelector: '#mrAnalysisList',
        controlsSelector: '#mrPaginationBottom',
        itemSelector: ':scope > [data-mr-item]',
        scrollOnChange: false,
      });
    } else {
      _mrPaginator.resync();
    }
    _mrPaginator.render();

    if (typeof filterMrAnalyses === 'function') {
      filterMrAnalyses();
    }
  }

  /* -- Sync project (delegates to team-level sync) --
   *
   * Behaviour matches the group-level Sync button on course/team pages:
   *   * Defer global job-bar slot before the POST so the bar shows
   *     immediately and there is no flash between click and response.
   *   * Inspect the API response and branch on every status:
   *       - skipped_fresh -> info toast, hide bar, unlock button.
   *       - failed        -> danger toast (real error), complete bar
   *                          with error, unlock button.
   *       - running       -> info toast "Sync already in progress"
   *                          (does NOT lie about starting a new run),
   *                          attach SSE to the existing job, keep
   *                          button locked until completion.
   *       - enqueued      -> success toast "Sync started!", attach
   *                          SSE, keep button locked until completion.
   *   * SSE onComplete / onError finalises the global bar and unlocks
   *     the button - this prevents the previous bug where the button
   *     unlocked after the POST and the deferred bar slot stayed
   *     forever even though no new sync started.
   */
  const btnSync = document.getElementById('btnSyncProject');
  let _projectSyncStreamCtrl = null;
  if (btnSync) {
    const projectSyncJobKey = 'sync:project:' + PROJECT_ID;
    const {
      connectGlobalJob,
      deferGlobalJob,
      completeGlobalJob,
      hideGlobalJob,
    } = window.GP?.globalJobs || window.GP || {};

    function _finishProjectSync(messageKind, bannerText) {
      // Release button + bar exactly once, regardless of which SSE
      // event we land on (complete / error).
      if (_projectSyncStreamCtrl) {
        try { _projectSyncStreamCtrl.close(); } catch (_) { /* ignore */ }
        _projectSyncStreamCtrl = null;
      }
      setButtonLoading(btnSync, false);
      // Anti-spam cooldown whenever the sync FAILS  -  regardless of which SSE
      // event we landed on (streamed failure / onError / start-failure catch).
      // Centralised here so the countdown is consistent for every failure path.
      if (messageKind === 'error' && btnSync) {
        GP.applyCooldown(btnSync);
      }
      if (typeof completeGlobalJob === 'function') {
        return completeGlobalJob(projectSyncJobKey, bannerText, messageKind);
      } else if (typeof hideGlobalJob === 'function') {
        hideGlobalJob(projectSyncJobKey);
      }
      return false;
    }

    btnSync.addEventListener('click', async () => {
      if (!CAN_EDIT) return;
      if (!PROJECT_ID) return;
      if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: scoringScope('project:' + PROJECT_ID) })) return;
      const label = t('Syncing project:') + ' ' + (PROJECT_NAME || t('project'));
      try {
        await _lock('sync:project:' + PROJECT_ID, async () => {
          setButtonLoading(btnSync, true);
          if (typeof connectGlobalJob === 'function') {
            connectGlobalJob(projectSyncJobKey, label, { courseId: String(COURSE_ID || ''), teamId: String(TEAM_ID || ''), projectId: String(PROJECT_ID || ''), projectName: PROJECT_NAME || '', jobKind: 'project_sync' });
          }
          const result = await apiCall(`/api/v1/projects/${PROJECT_ID}/sync`, 'POST');
          const status = (result && result.status) ? String(result.status).toLowerCase() : '';

          // -- 1. Server short-circuit: data already fresh --
          if (status === 'skipped_fresh') {
            const msg = result.message || t('Already up-to-date');
            const handledByGlobal = _finishProjectSync('done', msg);
            if (!handledByGlobal) showToast(msg, 'info');
            return;
          }

          // -- 2. Backend failed to enqueue (Redis down etc.) --
          if (status === 'failed' || status === 'cancelled' || !result || !result.job_id) {
            const msg = (result && result.message) || t('Sync failed');
            const handledByGlobal = _finishProjectSync('error', msg);
            if (!handledByGlobal) showToast(msg, 'danger');
            return;
          }

          // -- 3. Existing job already running/enqueued for this team --
          if (status === 'running' || status === 'enqueued') {
            // Was this a fresh enqueue or an existing job? Server
            // returns the same shape; we use the message as the
            // signal (the existing-job branch sets it to
            // "Sync already <status> for group ...").
            const isExisting = typeof result.message === 'string' && /already\s+(enqueued|running)/i.test(result.message);
            if (isExisting) {
              showToast(result.message || t('Sync already in progress'), 'info');
            } else {
              showToast(t('Sync started!'), 'success');
            }
          }

          if (typeof deferGlobalJob === 'function') {
            deferGlobalJob(label, projectSyncJobKey, { courseId: String(COURSE_ID || ''), teamId: String(TEAM_ID || ''), projectId: String(PROJECT_ID || ''), jobKind: 'project_sync', jobId: result.job_id });
          } else if (typeof setGlobalJobMeta === 'function') {
            setGlobalJobMeta(projectSyncJobKey, { jobId: result.job_id });
          }

          // -- 4. Attach SSE so the button stays locked until the
          //       backend job actually finishes, and the global bar
          //       reflects real progress (not a phantom deferred
          //       slot that never resolves). --
          if (typeof streamJobProgress !== 'function') {
            // No SSE helper - the scoped global bar job has a jobId now,
            // so restore/polling can finish it if the user navigates.
            setButtonLoading(btnSync, false);
            return;
          }
          _projectSyncStreamCtrl = streamJobProgress(result.job_id, {
            onComplete(data) {
              const s = String((data && data.status) || '').toLowerCase();
              if (s === 'failed' || s === 'cancelled') {
                const msg = (data && data.error_message) || t('Sync failed');
                const handledByGlobal = _finishProjectSync('error', msg);
                if (!handledByGlobal) showToast(msg, 'danger');
              } else {
                // Was wrongly "Group sync completed" on a PROJECT sync; use the
                // generic (already-translated) wording so the message matches
                // the entity being synced.
                const msg = t('Sync completed');
                const handledByGlobal = _finishProjectSync('done', msg);
                if (!handledByGlobal) showToast(msg, 'success');
                // Reload to surface freshly synced members / pipelines / MRs.
                // Delay slightly so the toast renders before the
                // navigation tears it down.
                setTimeout(() => { reloadKeepScroll(); }, 1200);
              }
            },
            onError() {
              _finishProjectSync('error', t('Sync status unknown'));
            },
          });
        });
      } catch (err) {
        if (err.code !== 'LOCKED') {
          // Shared message so group / project / course syncs read identically
          // (esp. the 401 expired-token case).
          const msg = (GP.syncErrorMessage || ((e) => (e && e.message) || 'Sync failed'))(err);
          const handledByGlobal = _finishProjectSync('error', msg);
          if (!handledByGlobal) showToast(msg, 'danger');
          // Apply anti-spam cooldown to prevent permanent lock and discourage
          // rapid re-clicking on a failing endpoint.
          if (btnSync) {
            GP.applyCooldown(btnSync);
          }
        }
      }
    });
  }

  /* -- Unlink Project -- */
  const btnUnlink = document.getElementById('btnUnlinkProject');
  if (btnUnlink) {
    btnUnlink.addEventListener('click', async () => {
      if (!CAN_EDIT) { showToast(t('You do not have permission to unlink this project.'), 'warning'); return; }
      if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: scoringScope('project:' + PROJECT_ID) })) return;
      confirmDangerousAction(t('unlink this project'), async () => {
        try {
          await _lock(`unlinkProject:${PROJECT_ID}`, async () => {
            setButtonLoading(btnUnlink, true);
            await apiCall(`/api/v1/projects/${PROJECT_ID}`, 'DELETE');
            flashToast(t ? t('Project unlinked') : 'Project unlinked', 'success');
            if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
            // Stay on this page and reload in place so the teacher/admin
            // sees the "unlinked" banner + Restore button, instead of
            // being ejected to the group page ("kicked out").
            setTimeout(() => { reloadKeepScroll(); }, 500);
          });
        } catch (err) {
          if (err.code !== 'LOCKED') showToast(err.message || t('Failed to unlink project'), 'danger');
        } finally {
          setButtonLoading(btnUnlink, false);
        }
      }, { confirmText: t('Unlink this project? Its history stays in the database but it will be hidden from the group and skipped by sync. It will NOT come back automatically on next sync - a teacher or admin must restore it.') });
    });
  }

  /* -- Restore (reactivate) an unlinked project from its detail page -- */
  const btnReactivateProject = document.querySelector('[data-action="reactivateProject"]');
  if (btnReactivateProject) {
    btnReactivateProject.addEventListener('click', async () => {
      if (!CAN_EDIT) { showToast(t('You do not have permission to restore this project.'), 'warning'); return; }
      if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: scoringScope('project:' + PROJECT_ID) })) return;
      /* THE dialog, never window.confirm - see components/modals. */
      const _ok = await GP.confirmDialog({
        title: t('Restore this project?'),
        message: t('Reactivate this project? A background sync will be enqueued.'),
        confirmText: t('Restore'),
      });
      if (!_ok) return;
      try {
        await _lock(`reactivateProject:${PROJECT_ID}`, async () => {
          setButtonLoading(btnReactivateProject, true);
          const result = await apiCall(`/api/v1/projects/${PROJECT_ID}/reactivate`, 'POST');
          flashToast(t ? t('Project restored') : 'Project restored', 'success');
          if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
          // Register the enqueued refresh in the global job bar with its
          // jobId/jobKind. The bar persists to localStorage and, after the
          // reload below, reconnects and polls /api/v1/jobs/<id> to
          // completion on its own. We do NOT block the reload on the sync
          // finishing - the project becomes active immediately, so the
          // page must show the restored state right away instead of
          // freezing on "Restoring..." for the whole sync (which can hang
          // for tens of seconds on an empty/slow repo).
          const reactivateJobKey = 'sync:project:' + PROJECT_ID;
          const jobId = result && result.job_id;
          if (jobId && typeof window.deferGlobalJob === 'function') {
            const label = t('Syncing project:') + ' ' + (PROJECT_NAME || t('project'));
            window.deferGlobalJob(label, reactivateJobKey, { courseId: String(COURSE_ID || ''), teamId: String(TEAM_ID || ''), projectId: String(PROJECT_ID || ''), jobKind: 'project_sync', jobId });
          }
          setTimeout(() => { reloadKeepScroll(); }, 600);
        });
      } catch (err) {
        if (err.code !== 'LOCKED') showToast(err.message || t('Failed to reactivate project'), 'danger');
        setButtonLoading(btnReactivateProject, false);
      }
    });
  }

  /* -- MR Analysis History Viewer -- */
  function createHistoryModal() {
    let modal = document.getElementById('mrHistoryModal');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'mrHistoryModal';
    modal.className = 'modal-backdrop';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-hidden', 'true');
    modal.setAttribute('data-action', 'closeModalOnBackdrop');
    const _tplModal = document.getElementById('tplMrHistoryModal');
    if (_tplModal) {
      modal.appendChild(_tplModal.content.cloneNode(true));
      const _title = modal.querySelector('#mrHistoryTitle');
      if (_title) _title.textContent = t('MR Analysis History');
    }
    document.body.appendChild(modal);
    return modal;
  }

  async function showMrHistory(mrIid) {
    const modal = createHistoryModal();
    const title = modal.querySelector('#mrHistoryTitle');
    const body = modal.querySelector('#mrHistoryBody');
    if (title) title.textContent = `MR !${mrIid} - ${t('Analysis History')}`;
    if (body) body.innerHTML = GP.renderLoaderHtml('Loading history...', 'md');
    openModal('mrHistoryModal');

    try {
      const data = await apiCall(`/api/v1/llm/mr/${PROJECT_ID}/${mrIid}/history`);
      if (!data || !data.length) {
        body.innerHTML = GP.emptyStateHtml(
          t('No analysis history found for this MR.'));
        return;
      }
      const esc = _escapeHtml;
      body.innerHTML = data.map((entry, i) => {
        const ts = GP.timeHtml(entry.analysis_timestamp);
        const r = entry.structured_result || {};
        const risk = entry.risk_score != null ? entry.risk_score : '-';
        const conf = r.confidence_score != null ? Math.round(r.confidence_score * 100) + '%' : '-';
        return `<details class="mr-card mr-history-card" ${i === 0 ? 'open' : ''}>
          <summary class="mr-card-header mr-history-card-header">
            <div class="mr-history-card-header-inner">
              <span><strong>${ts}</strong> &bull; ${esc(entry.model_used || '?')}</span>
              ${GP.badgeHtml(t('Risk') + ': ' + risk + ' \u2022 ' + t('Conf') + ': ' + conf, 'gray')}
            </div>
          </summary>
          <div class="mr-history-card-body">
            ${r.summary ? `<p class="mb-2">${esc(r.summary)}</p>` : ''}
            ${r.strengths?.length ? `<p><strong>${t('Strengths')}:</strong> ${r.strengths.map(s => esc(s.category || s.description || '')).join(', ')}</p>` : ''}
            ${r.risk_flags?.length ? `<p><strong>${t('Risk Flags')}:</strong> ${r.risk_flags.map(f => esc(f.flag || f.description || '')).join(', ')}</p>` : ''}
            ${r.improvements?.length ? `<p><strong>${t('Improvements')}:</strong> ${r.improvements.map(im => esc(im.area || im.suggestion || '')).join(', ')}</p>` : ''}
            ${r.grading_suggestion ? `<p><strong>${t('Grading')}:</strong> ${esc(r.grading_suggestion)}</p>` : ''}
          </div>
        </details>`;
      }).join('');
    } catch (err) {
      /* With a retry: the modal is already open on a failed fetch, and the only
         way back used to be closing it and finding the row again. */
      body.innerHTML = GP.errorStateHtml(err.message || t('Failed to load history'), t('Retry'));
      GP.bindRetry(body, function () { return showMrHistory(mrIid); });
    }
  }

  async function triggerSingleMrAnalysis(mrIid, actionBtn) {
    if (!CAN_EDIT) return;
    if (isGlobalJobRunning('analysis') && !await confirmProcessRestart('analysis', t('MR Analysis'))) return;
    confirmDangerousAction(t('MR re-analysis'), async () => {
      try {
        await _lock('mrAnalysis:' + PROJECT_ID + ':' + mrIid, async () => {
          if (actionBtn) setButtonLoading(actionBtn, true);

          // Enqueue background job via dashboard endpoint (SSE-based progress)
          await apiCall(`/dashboard/projects/${PROJECT_ID}/llm-analyze-mr/${mrIid}`, 'POST');
          showToast(t('Analysis started'), 'success');

          deferGlobalJob(t('Analyzing MR !%mr: %name').replace('%mr', mrIid).replace('%name', PROJECT_NAME), 'analysis',
            { courseId: COURSE_ID, teamId: TEAM_ID, projectId: PROJECT_ID, pollUrl: `/dashboard/projects/${PROJECT_ID}/llm-analysis-status`, localIndicatorSelector: '.analysis-progress', cancelUrl: `/dashboard/projects/${PROJECT_ID}/llm-analysis-cancel` });
          stopPolling();
          startPolling();
        });
      } catch (err) {
        if (err.code !== 'LOCKED') {
          showToast(err.message || t('Failed to start analysis'), 'danger');
        }
      } finally {
        if (actionBtn) setButtonLoading(actionBtn, false);
      }
    }, { confirmText: t('Re-analyze this MR? This will consume LLM tokens.'), singleConfirm: true });
  }

  // Delegate clicks on MR history/reanalyze buttons
  onMrHistoryClick = (e) => {
    const histBtn = e.target.closest('[data-mr-history]');
    if (histBtn) {
      e.preventDefault();
      e.stopPropagation();
      showMrHistory(histBtn.dataset.mrHistory);
      return;
    }
    const reanalBtn = e.target.closest('[data-mr-reanalyze]');
    if (reanalBtn) {
      e.preventDefault();
      e.stopPropagation();
      triggerSingleMrAnalysis(reanalBtn.dataset.mrReanalyze, reanalBtn);
    }
  };
  document.addEventListener('click', onMrHistoryClick);
