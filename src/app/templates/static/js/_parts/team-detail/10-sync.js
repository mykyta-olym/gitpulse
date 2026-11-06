  // Projects don't sync individually; they inherit their parent team's
  // sync state. When this team is syncing (either triggered locally or
  // via course-level Sync All), repaint every active project row's
  // Status cell with a SYNCING / QUEUED / FAILED badge so the table
  // reflects what's actually happening at the group level.
  //
  // The original Status badge (Active / Template) is stashed on the
  // row dataset so we can restore it once the sync settles.
  function _paintProjectRowsSyncStatus(state, projectStatusMap) {
    const rows = document.querySelectorAll('#projectsTable tbody tr');
    const hasMap = projectStatusMap && typeof projectStatusMap === 'object'
                    && Object.keys(projectStatusMap).length > 0;
    rows.forEach(row => {
      if (row.dataset.projectInactive === 'true') return; // keep Inactive
      const cell = row.cells && row.cells[3]; // Status column (0=name,1=path,2=branch,3=status,4=actions)
      if (!cell) return;
      // Per-project map wins when present: only paint rows whose
      // project id has an active status. Team-wide `state` is used
      // either when no map is supplied OR (fallback) as the default
      // for rows missing from the map when the team itself is syncing.
      let rowState = state || null;
      if (hasMap) {
        const pid = row.dataset.projectId || '';
        rowState = pid && projectStatusMap[pid] ? projectStatusMap[pid] : null;
      }
      if (rowState) {
        if (!row.dataset.originalStatus) {
          row.dataset.originalStatus = cell.innerHTML;
        }
        let badgeClass = 'badge-info';
        let badgeText = t('SYNCING');
        if (rowState === 'enqueued') {
          badgeText = t('QUEUED');
        } else if (rowState === 'failed') {
          badgeClass = 'badge-danger';
          badgeText = t('FAILED');
        } else if (rowState === 'cancelled') {
          badgeClass = 'badge-warning';
          badgeText = t('CANCELLED');
        }
        cell.innerHTML = GP.badgeHtml(badgeText, badgeClass.replace(/^badge-/, ''));
      } else if (row.dataset.originalStatus) {
        cell.innerHTML = row.dataset.originalStatus;
        delete row.dataset.originalStatus;
      }
    });
  }

  let _syncStatusPoller = null;
  async function _pollTeamSyncStatusOnce() {
    if (!CAN_EDIT) return null;
    if (!COURSE_ID) return null;
    try {
      const data = await window.GP.apiCall(`/api/v1/courses/${COURSE_ID}/sync-status`, 'GET', null, { maxRetries: 0 });
      const me = (data && Array.isArray(data.teams) ? data.teams : []).find(team => String(team.team_id) === TEAM_ID);
      const teamSt = me && me.sync_status ? String(me.sync_status).toLowerCase() : '';
      const projMap = (data && data.sync_status_by_project && typeof data.sync_status_by_project === 'object')
                       ? data.sync_status_by_project
                       : {};
      // Filter the project map to only ids that actually appear in this
      // team's projects table - the API returns the whole course.
      const ownProjectMap = {};
      let hasOwnProj = false;
      document.querySelectorAll('#projectsTable tbody tr').forEach(row => {
        const pid = row.dataset.projectId;
        if (pid && projMap[pid]) {
          ownProjectMap[pid] = String(projMap[pid]).toLowerCase();
          hasOwnProj = true;
        }
      });
      if (teamSt === 'running' || teamSt === 'enqueued' || teamSt === 'failed' || teamSt === 'cancelled') {
        // Team-wide sync - paint all rows with team state.
        _paintProjectRowsSyncStatus(teamSt);
        return teamSt;
      }
      if (hasOwnProj) {
        // Project-scoped sync(s) only - paint specific rows.
        _paintProjectRowsSyncStatus(null, ownProjectMap);
        // Return a synthetic "running" so the poller keeps going.
        return Object.values(ownProjectMap).some(s => s === 'running' || s === 'enqueued')
                 ? 'running'
                 : null;
      }
      _paintProjectRowsSyncStatus(null);
      return null;
    } catch (_) {
      return null;
    }
  }
  function _startSyncStatusPoller() {
    if (_syncStatusPoller) return;
    _syncStatusPoller = setInterval(async () => {
      const st = await _pollTeamSyncStatusOnce();
      if (st !== 'running' && st !== 'enqueued') {
        _stopSyncStatusPoller();
      }
    }, 4000);
  }
  function _stopSyncStatusPoller() {
    if (_syncStatusPoller) { clearInterval(_syncStatusPoller); _syncStatusPoller = null; }
  }

  // Sync functions
  async function triggerSync() {
    if (!CAN_EDIT) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + TEAM_ID })) return;
    const jobKey = 'sync:team:' + TEAM_ID;
    const syncBtn = document.querySelector('button[data-sync-trigger="team"]');
    try {
      await _lock('sync:' + TEAM_ID, async () => {
        if (syncBtn) setButtonLoading(syncBtn, true);
        const _label = TEAM_NAME || t('group');
        const _syncingMsg = t('Syncing group:') + ' ' + _label;
        if (typeof connectGlobalJob === 'function') {
          connectGlobalJob(jobKey, _syncingMsg,
            { teamId: String(TEAM_ID || ''), courseId: String(COURSE_ID || ''), teamName: TEAM_NAME || '', jobKind: 'team_sync' });
        }

        const result = await apiCall(`/api/v1/teams/${TEAM_ID}/sync`, 'POST');
        if (result.job_id) {
          if (typeof deferGlobalJob === 'function') {
            deferGlobalJob(_syncingMsg, jobKey,
              { teamId: String(TEAM_ID || ''), courseId: String(COURSE_ID || ''), jobKind: 'team_sync', jobId: result.job_id });
          }
          _paintProjectRowsSyncStatus('running');
          _startSyncStatusPoller();
          streamSyncStatus(result.job_id, jobKey);
        } else {
          showSyncSuccess(jobKey);
          if (syncBtn) setButtonLoading(syncBtn, false);
        }
      });
    } catch (err) {
      if (err.code !== 'LOCKED') {
        // Shared message so group / project / course syncs read identically
        // (esp. the 401 expired-token case). showSyncError resets the button +
        // applies the anti-spam cooldown.
        const msg = (GP.syncErrorMessage || ((e) => (e && e.message) || 'Sync failed'))(err);
        const handledByGlobal = showSyncError(jobKey, msg);
        if (!handledByGlobal) showToast(msg, 'danger');
      }
    }
  }

  // -- Run selected compliance checks --
  async function runSelectedChecks() {
    if (!CAN_EDIT) return;

    const teamName = (window.GP_TEAM?.name) || (document.querySelector('.page-header__title')?.textContent || '').trim() || 'group';
    await (window.GP?.runScopedChecksProcess || window.runScopedChecksProcess)?.({
      endpoint: `/api/v1/teams/${TEAM_ID}/run-checks`,
      jobKey: 'run_checks:team:' + TEAM_ID,
      lockKey: 'runChecks:' + TEAM_ID,
      guardScopes: 'course:' + COURSE_ID + ' team:' + TEAM_ID,
      label: teamName,
      button: document.getElementById('btnRunChecks'),
      courseId: COURSE_ID,
      teamId: TEAM_ID,
      onComplete(detail) {
        if (detail.status === 'done') refreshTeamData().catch(() => {});
      },
    });
  }
  
  // The old sync MODAL (syncStatusModal + its spinner/success/error/footer
  // elements) was removed from the templates - the global job bar owns ALL sync
  // UI now. These helpers therefore only drive the bar + the per-project row
  // badges; the dead modal-DOM manipulation has been stripped. Messages are the
  // generic (translated) "Sync completed" / "Sync failed" so group and project
  // syncs read the same.
  function showSyncSuccess(jobKey = 'sync') {
    const syncBtn = document.querySelector('button[data-sync-trigger="team"]');
    if (syncBtn) setButtonLoading(syncBtn, false);
    const doneMsg = t('Sync completed');
    const handledByGlobal = typeof completeGlobalJob === 'function'
      && completeGlobalJob(jobKey, doneMsg, 'done');
    // Refresh data live so the group members table updates without a page blink.
    setTimeout(() => {
      if (syncStreamCtrl) { syncStreamCtrl.close(); syncStreamCtrl = null; }
      refreshTeamData().catch(() => {});
      if (!handledByGlobal) showToast(doneMsg, 'success');
    }, 1500);
    return handledByGlobal;
  }

  function showSyncError(jobKey = 'sync', message) {
    const syncBtn = document.querySelector('button[data-sync-trigger="team"]');
    if (syncBtn) {
      setButtonLoading(syncBtn, false);
      // Anti-spam cooldown so the countdown shows on streamed failures too.
      GP.applyCooldown(syncBtn);
    }
    const failMsg = message || t('Sync failed');
    return typeof completeGlobalJob === 'function'
      && completeGlobalJob(jobKey, failMsg, 'error');
  }

  function streamSyncStatus(jobId, jobKey = 'sync') {
    if (typeof streamJobProgress !== 'function') { console.warn('streamJobProgress not available'); return; }
    syncStreamCtrl = streamJobProgress(jobId, {
      onUpdate(data) {
        // Forward progress to the global job bar (the only sync UI now).
        if (typeof updateGlobalJobProgress === 'function' && data.progress != null) {
          updateGlobalJobProgress(jobKey, data.progress, data.message);
        } else if (typeof updateGlobalJob === 'function') {
          updateGlobalJob(data.message || t('Syncing...'), jobKey);
        }
      },
      onComplete(data) {
        const s = (data.status || '').toLowerCase();
        if (s === 'failed' || s === 'cancelled') {
          showSyncError(jobKey);
          _paintProjectRowsSyncStatus('failed');
          // Clear the FAILED badge after a few seconds so the original
          // Active/Template badge returns for actionable projects.
          setTimeout(() => _paintProjectRowsSyncStatus(null), 5000);
        } else {
          showSyncSuccess(jobKey);
          _paintProjectRowsSyncStatus(null);
        }
        _stopSyncStatusPoller();
        syncStreamCtrl = null;
      },
      onError() {
        showSyncError(jobKey);
        _paintProjectRowsSyncStatus(null);
        _stopSyncStatusPoller();
        syncStreamCtrl = null;
      },
    });
  }

  // Kept (exported as window.closeSyncModal in 30-live.js). The modal is gone,
  // so this just frees the button + closes any open status stream.
  function closeSyncModal() {
    const syncBtn = document.querySelector('button[data-sync-trigger="team"]');
    if (syncBtn) { setButtonLoading(syncBtn, false); }
    if (syncStreamCtrl) { syncStreamCtrl.close(); syncStreamCtrl = null; }
  }
  
