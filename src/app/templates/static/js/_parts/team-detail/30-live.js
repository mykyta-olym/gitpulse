  // -- Team Members Pagination (ClientPaginator) --
  function initTeamMembersPagination() {
    if (typeof ClientPaginator !== 'function') return;
    const table = document.getElementById('teamMembersTable');
    const controls = document.getElementById('tmPaginationControls');
    if (!table || !controls) return;

    // Avoid duplicate initialization if already bound and alive in DOM
    if (table._clientPaginator && document.body.contains(table._clientPaginator.controls)) {
      return;
    }

    const p = new ClientPaginator({
      tbodySelector: '#teamMembersTable tbody',
      controlsSelector: '#tmPaginationControls',
      pageSize: 50,
      pageSizes: [25, 50, 100],
    });
    p.render();
  }

  // Initialize on load/script evaluation
  initTeamMembersPagination();

  // Re-run on HTMX swaps so that elements loaded lazily/swapped dynamically get paginated!
  document.body.addEventListener('htmx:afterSwap', initTeamMembersPagination);

  // -- Toggle Member Exclusion --
  async function toggleExclusion(studentId, teamId) {
    if (!CAN_EDIT) { showToast(t('Not authorized'), 'warning'); return; }
    await GP.toggleMemberExclusion({
      studentId,
      teamId,
      scope: 'course:' + COURSE_ID + ' team:' + teamId,
      onRefresh: refreshTeamData,
    });
  }

  // -- Reactivate soft-deleted project --
  async function reactivateProject(event) {
    const btn = event?.target?.closest?.('[data-action="reactivateProject"]');
    if (!btn) return;
    if (!CAN_EDIT) { showToast(t('You do not have permission to restore this project.'), 'warning'); return; }
    const projectId = btn.dataset.projectId;
    if (!projectId) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + TEAM_ID + ' project:' + projectId })) return;
    /* THE dialog, never window.confirm; and THE loading state, not a hand-rolled
       label swap - `setButtonLoading` keeps the button's size and label and puts
       the shared spinner where its icon was. */
    const _okProject = await GP.confirmDialog({
      title: t('Restore this project?'),
      message: t('Reactivate this project? A background sync will be enqueued.'),
      confirmText: t('Restore'),
    });
    if (!_okProject) return;
    setButtonLoading(btn, true);
    try {
      const resp = await fetch(`/api/v1/projects/${projectId}/reactivate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      showToast(t('Project restored'), 'success');
      // Reload so the projects table re-renders the row as active and the
      // recomputed metrics / rankings reflect the restored project.
      if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
      setTimeout(() => { reloadKeepScroll(); }, 500);
    } catch (err) {
      /* setButtonLoading restores the button's own label - the hand-rolled
         `textContent = 'Reactivate'` that used to sit here had to repeat that
         label, so it drifted from the markup the moment either changed. */
      setButtonLoading(btn, false);
      showToast(t('Failed to reactivate project'), 'danger');
    }
  }

  // -- Restore this whole group from the archived-group banner --
  async function reactivateTeam(event) {
    const btn = event?.target?.closest?.('[data-action="reactivateTeam"]');
    if (!btn) return;
    if (!CAN_EDIT) { showToast(t('You do not have permission to restore this group.'), 'warning'); return; }
    const teamId = btn.dataset.teamId || TEAM_ID;
    if (!teamId) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + teamId })) return;
    const _okTeam = await GP.confirmDialog({
      title: t('Restore this group?'),
      message: t('Restore this group? Its members and projects will be re-enabled and a background sync will be enqueued.'),
      confirmText: t('Restore'),
    });
    if (!_okTeam) return;
    setButtonLoading(btn, true);
    try {
      await apiCall(`/api/v1/teams/${teamId}/reactivate`, 'POST');
      showToast(t('Group restored'), 'success');
      if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
      setTimeout(() => { reloadKeepScroll(); }, 500);
    } catch (err) {
      setButtonLoading(btn, false);
      if (err.code !== 'LOCKED') showToast(err.message || t('Failed to restore group'), 'danger');
    }
  }

  // -- Hard delete this group permanently --
  async function deleteTeamPermanent(event) {
    const btn = event?.target?.closest?.('[data-action="deleteTeamPermanent"]');
    if (!btn) return;
    if (!CAN_EDIT) { showToast(t('You do not have permission to delete this group.'), 'warning'); return; }
    const teamId = btn.dataset.teamId || TEAM_ID;
    if (!teamId) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + teamId })) return;
    
    confirmDangerousAction(
      btn.dataset.teamName || 'this group',
      async () => {
        try {
          await _lock(`deleteTeamPermanent:${teamId}`, async () => {
            setButtonLoading(btn, true);
            await apiCall(`/api/v1/teams/${teamId}/permanent`, 'DELETE');
            flashToast(t('Group permanently deleted'), 'success');
            if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
            setTimeout(() => {
              window.location.href = `/dashboard/courses/${COURSE_ID}`;
            }, 500);
          });
        } catch (err) {
          if (err.code !== 'LOCKED') showToast(err.message || t('Failed to delete group'), 'danger');
          setButtonLoading(btn, false);
        }
      },
      {
        confirmText: t('Are you sure you want to permanently delete this group and all its projects, members, and data? This action cannot be undone.'),
      }
    );
  }

  // -- Permanent delete a project (teacher/admin) --
  async function deleteProjectPermanent(event) {
    const btn = event?.target?.closest?.('[data-action="deleteProjectPermanent"]');
    if (!btn) return;
    if (!CAN_EDIT) { showToast(t('You do not have permission to delete this project.'), 'warning'); return; }
    const projectId = btn.dataset.projectId;
    if (!projectId) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + TEAM_ID + ' project:' + projectId })) return;
    confirmDangerousAction(
      t('this project'),
      async () => {
        try {
          await _lock(`deleteProjectPermanent:${projectId}`, async () => {
            setButtonLoading(btn, true);
            await apiCall(`/api/v1/projects/${projectId}/permanent`, 'DELETE');
            showToast(t('Project permanently deleted'), 'success');
            if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
            setTimeout(() => { reloadKeepScroll(); }, 500);
          });
        } catch (err) {
          if (err.code !== 'LOCKED') showToast(err.message || t('Failed to delete project'), 'danger');
          setButtonLoading(btn, false);
        }
      },
      {
        confirmText: t('Are you sure you want to permanently delete this project and all its pipelines, MRs, commits, and data? This action cannot be undone.'),
      }
    );
  }

  // -- Toggle visibility of dimmed unlinked project rows --
  function toggleDeletedProjects(event) {
    const btn = event?.target?.closest?.('[data-action="toggleDeletedProjects"]');
    const table = document.getElementById('projectsTable');
    if (!table) return;
    const hidden = table.classList.toggle('gp-hide-deleted');
    if (btn) btn.setAttribute('aria-pressed', hidden ? 'false' : 'true');
  }


  // Expose functions for data-action delegation
  window.linkProject = linkProject;
  window.reactivateProject = reactivateProject;
  window.reactivateTeam = reactivateTeam;
  window.toggleDeletedProjects = toggleDeletedProjects;
  window.deleteTeam = deleteTeam;
  window.deleteTeamPermanent = deleteTeamPermanent;
  window.deleteProjectPermanent = deleteProjectPermanent;
  window.triggerSync = triggerSync;
  window.runSelectedChecks = runSelectedChecks;
  window.closeSyncModal = closeSyncModal;
  window.toggleExclusion = toggleExclusion;

  /* -- Modal Dirty-State Guards -- */
  if (typeof enableFormDirtyGuard === 'function') {
    enableFormDirtyGuard('linkProjectModal');
  }

  /* syncStatusModal - ensure X / Escape properly stops SSE stream */
  if (typeof registerModalGuard === 'function') {
    registerModalGuard('syncStatusModal', function () {
      // Clean up SSE stream before allowing close
      if (typeof syncStreamCtrl !== 'undefined' && syncStreamCtrl) {
        syncStreamCtrl.close();
        syncStreamCtrl = null;
      }
      return true;  // allow close after cleanup
    });
  }

  let _lastVisibleRefreshAt = 0;

  function _refreshTeamDataVisible() {
    const now = Date.now();
    if (now - _lastVisibleRefreshAt < 800) return Promise.resolve();
    _lastVisibleRefreshAt = now;
    return refreshTeamData().catch(() => {});
  }

  // Auto-refresh team data when returning to this tab
  const onTabVisible = () => {
    _refreshTeamDataVisible();
    resumeTeamAnalysis();
  };
  document.addEventListener('gp-tab-visible', onTabVisible);

  // -- SSE-first live data stream (polling is fallback only) --
  let _teamSSE = null;           // EventSource instance
  // The server already rendered fresh member rows, so the
  // FIRST SSE `connected` (fired right after the page loads) must NOT trigger
  // a redundant /live-data fetch + repaint. Only reconnects refresh.
  let _teamConnectedOnce = false;
  let _autoRefreshTimer = null;  // fallback polling timer
  let _checksPollId = null;      // run-checks fallback poll interval
  const _SSE_MAX_ERRORS = GP.SSE_MAX_ERRORS || 5;     // switch to polling after N SSE failures
  const _POLL_INTERVAL = 30000;  // fallback polling interval (30s)

  /** Connect to the team dashboard SSE stream. */
  function _connectTeamSSE() {
    _disconnectTeamSSE();
    _teamSSE = GP.sse({
      url: `/api/v1/teams/${TEAM_ID}/stream`,
      maxErrors: _SSE_MAX_ERRORS,
      events: {
        connected: () => {
          if (GP.debug) console.debug('[team-detail] SSE connected');
          // Skip the first connect: trust the server render. Reconnects refresh.
          if (!_teamConnectedOnce) { _teamConnectedOnce = true; return; }
          refreshTeamData().catch(() => {});
        },
        update: (e) => {
          try {
            const d = JSON.parse(e.data);
            if (d && d.event === 'settings_changed') { reloadKeepScroll(); return; }
            // Structural project changes (unlink / restore / link) add or
            // remove rows in the server-rendered "Subgroups and Projects"
            // list and flip the Deleted toggle count - neither of which the
            // fine-grained refreshTeamData() DOM patch covers. Re-render the
            // page server-side (scroll preserved) so the list, the Deleted
            // count and the summary cards all reflect the committed truth.
            if (d && typeof d.event === 'string'
                && (d.event === 'project_unlinked'
                  || d.event === 'project_reactivated'
                  || d.event === 'project_linked'
                  || d.event === 'team_deleted'
                  || d.event === 'team_reactivated')) {
              reloadKeepScroll();
              return;
            }
          } catch (_) {}
          refreshTeamData().catch(() => {});
          showToast(t('Data updated'), 'success');
        },
      },
      onFailure: (n) => { if (GP.debug) console.debug('[team-detail] SSE error #' + n); },
      onGiveUp: () => {
        console.warn('[team-detail] SSE max errors reached, using polling fallback');
        _startFallbackPolling();
      },
      onBlocked: () => {
        console.warn('[team-detail] EventSource unavailable, falling back to polling');
        _startFallbackPolling();
      },
    });
  }

  /** Close the team SSE stream. */
  function _disconnectTeamSSE() {
    if (_teamSSE) { _teamSSE.close(); _teamSSE = null; }
  }

  /** Start fallback polling (only used when SSE is unavailable). */
  function _startFallbackPolling() {
    if (_autoRefreshTimer) return;
    _autoRefreshTimer = setInterval(() => {
      if (document.visibilityState === 'visible') {
        refreshTeamData().catch(() => {});
      }
    }, _POLL_INTERVAL);
  }

  /** Stop fallback polling. */
  function _stopFallbackPolling() {
    if (_autoRefreshTimer) { clearInterval(_autoRefreshTimer); _autoRefreshTimer = null; }
  }

  // Start SSE as primary mechanism
  _connectTeamSSE();

  // Pause SSE / polling when backend is unreachable - prevents console flood
  let _healthWasDown = false;
  const onHealthChange = (e) => {
    const detail = e.detail || {};
    if (detail.current === 'down' && !_healthWasDown) {
      _healthWasDown = true;
      _disconnectTeamSSE();
      _stopFallbackPolling();
      if (_checksPollId) { clearInterval(_checksPollId); _checksPollId = null; }
    } else if (detail.current !== 'down' && _healthWasDown) {
      _healthWasDown = false;
      _teamSSE?.resetErrors();
      _connectTeamSSE();
    }
  };

  // Visibility change: reconnect SSE when tab becomes visible, pause when hidden
  const onVisibilityChangeSSE = () => {
    if (document.visibilityState === 'hidden') {
      _disconnectTeamSSE();
      _stopFallbackPolling();
      invalidateAnalysisProbe();
      _stopSyncStatusPoller();
      if (_checksPollId) {
        clearInterval(_checksPollId);
        _checksPollId = null;
      }
      return;
    }
    // Force one immediate refresh for data freshness, debounced with gp-tab-visible.
    _refreshTeamDataVisible();
    // Re-establish SSE if it was lost in background
    if (!_teamSSE?.active && !_autoRefreshTimer) {
      _teamSSE?.resetErrors();
      _connectTeamSSE();
    }
    resumeTeamAnalysis();
    // Restart sync status poller if sync is active
    _pollTeamSyncStatusOnce().then(st => {
      if (st === 'running' || st === 'enqueued') {
        _startSyncStatusPoller();
      }
    });
  };

  // -- Run Checks modal: select/deselect/reset/search are handled by the
  // shared partial's inline init (`partials/_run_checks_modal.html`).
  // We only wire the submit button here.
  document.getElementById('btnRunChecks')?.addEventListener('click', () => { runSelectedChecks(); });

  // On page load: detect an in-flight sync triggered elsewhere (e.g.
  // course-level Sync All) and paint the project rows accordingly +
  // start the lightweight poller until it clears.
  _pollTeamSyncStatusOnce().then(st => {
    if (st === 'running' || st === 'enqueued') {
      _startSyncStatusPoller();
    }
  });

  // Auto-refresh team data when relevant jobs complete
  let _pendingRefresh = false;
  const onJobComplete = function(e) {
    const st = e.detail?.status;
    if (st !== 'done' && st !== 'error') return;
    if (!GP.jobAffectsScope(e.detail, { courseId: COURSE_ID, teamId: TEAM_ID })) return;
    if (document.visibilityState === 'visible') {
      _refreshTeamDataVisible();
    } else {
      _pendingRefresh = true;
    }
  };

  const onVisibilityChangeJob = function() {
    if (_pendingRefresh && document.visibilityState === 'visible') {
      _pendingRefresh = false;
      _refreshTeamDataVisible();
    }
  };

  const onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-team-detail-config') || target.id === 'gp-team-detail-config')) {
      GP.teamDetailCleanup();
    }
  };

  // Register all event listeners
  document.addEventListener('gp-health-change', onHealthChange);
  document.addEventListener('visibilitychange', onVisibilityChangeSSE);
  document.addEventListener('visibilitychange', onVisibilityChangeJob);
  window.addEventListener('gp:job-complete', onJobComplete);
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  // Global cleanup register to remove listeners and SSE connections
  GP.teamDetailCleanup = function () {
    invalidateAnalysisProbe();
    document.removeEventListener('DOMContentLoaded', _boot);
    if (syncStreamCtrl) { syncStreamCtrl.close(); syncStreamCtrl = null; }
    if (_checksPollId) { clearInterval(_checksPollId); _checksPollId = null; }
    _disconnectTeamSSE();
    _stopFallbackPolling();

    document.removeEventListener('gp-health-change', onHealthChange);
    document.removeEventListener('visibilitychange', onVisibilityChangeSSE);
    document.removeEventListener('visibilitychange', onVisibilityChangeJob);
    document.removeEventListener('gp-tab-visible', onTabVisible);
    window.removeEventListener('gp:job-complete', onJobComplete);
    window.removeEventListener('beforeunload', onBeforeUnload);
    document.body.removeEventListener('htmx:afterSwap', initTeamMembersPagination);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };
  GP.activePageCleanup = GP.teamDetailCleanup;
