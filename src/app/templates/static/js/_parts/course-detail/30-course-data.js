  // GitLab URL auto-fill setup
  function _bootAutofill() {
    if (typeof setupGitLabAutofill !== 'function') return;
    // Team modal - auto-fill from group URL
    setupGitLabAutofill('#teamGitLabUrl', {
      group: {
        '#teamName': 'name',
        '#gitlabNamespace': 'path'
      },
      project: {
        '#teamName': (r) => r.name || r.path?.split('/').pop(),
        '#gitlabNamespace': 'namespace'
      }
    }, csrfToken);
    
    // Project modal - auto-fill from project URL
    setupGitLabAutofill('#projectGitLabUrl', {
      project: {
        '#projectGitlabId': 'gitlab_id',
        '#projectPath': 'path',
        '#projectDisplayName': 'name'
      }
    }, csrfToken);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _bootAutofill);
  } else {
    _bootAutofill();
  }

  // -- Visibility change: recover SSE after tab was in background --
  // Browsers throttle EventSource in background tabs. When the user
  // returns, force-reconnect SSE and poll once for immediate data.
  const onVisibilityChangeSSE = () => {
    if (document.visibilityState === 'hidden') {
      disconnectSyncStream();
      _disconnectCourseDataSSE();
      if (_courseAutoRefresh) {
        clearInterval(_courseAutoRefresh);
        _courseAutoRefresh = null;
      }
      return;
    }
    // Force one poll for immediate data freshness
    if (typeof _pollSyncStatusOnce === 'function') _pollSyncStatusOnce();
    _refreshCourseData();
    // Re-establish sync SSE if it was lost (e.g., timed out in background)
    if (!_sseSource?.active && !_sseFallbackTimer) {
      connectSyncStream();
    }
    // Re-establish course data SSE if lost
    if (!_courseSSE?.active && !_courseAutoRefresh) {
      _connectCourseDataSSE();
    }
  };
  document.addEventListener('visibilitychange', onVisibilityChangeSSE);

  // -- SSE-first live data stream for course stats (polling is fallback) --
  let _courseSSE = null;            // EventSource for course data updates
  // The server already rendered fresh stat cards and team rows for this page,
  // so the FIRST SSE `connected` (which fires right after the page loads) must
  // NOT trigger a redundant /live-data fetch + repaint - that is the
  // blank-then-JS flicker. Only reconnects (after a dropout) refresh.
  let _courseConnectedOnce = false;
  const _COURSE_SSE_MAX_ERRORS = GP.SSE_MAX_ERRORS || 5;

  function _refreshCourseData() {
    /* Coalesced: SSE, the reconnect handler and the visibility handler can
       all ask for this within a few ms. Overlapping reads made the older
       answer paint last, settling the page one event behind. */
    return GP.coalesced('course-live-data', async () => {
    try {
      const data = await window.GP.apiCall(`/dashboard/courses/${COURSE_ID}/live-data`, 'GET', null, { key: 'course-live-data', maxRetries: 0 });
      if (Array.isArray(data.teams)) {
        data.teams.forEach(team => updateTeamRow({
          ...team,
          team_id: team.id,
          team_name: team.name,
          member_count: team.members,
          avg_score: team.avg_score == null ? null : team.avg_score / 100,
        }));
      }
    } catch (_) { /* ignore poll errors */ }
    });
  }

  // Friendly labels for the teacher webhook toast (keyed by GitLab object_kind).
  const _WEBHOOK_LABELS = {
    merge_request: 'Merge request', push: 'Push', pipeline: 'Pipeline',
    issue: 'Issue', note: 'Comment', tag_push: 'Tag push', wiki_page: 'Wiki',
  };
  let _lastWebhookToastAt = 0;
  /**
   * Teacher-only toast when a webhook lands for a group in this course. Designed
   * to interact cleanly with the rest of the app:
   *   - staff only (CAN_EDIT);
   *   - only the VISIBLE leader tab decides, then broadcasts to sibling visible
   *     tabs (GP.broadcastToast) - so N open course tabs = one toast, and
   *     background tabs stay silent (same pattern as every other cross-tab toast);
   *   - stays quiet while THIS course is mid-sync - the global sync bar already
   *     signals data is updating, so per-event toasts would just be noise on top
   *     of the user's own Sync All;
   *   - throttled to one per 4s so a burst of pushes/pipelines can't spam the
   *     corner (the data still refreshes silently on every event).
   */
  function _maybeWebhookToast(d) {
    if (!CAN_EDIT) return;
    if (!GP.isPollLeader()) return;
    if (typeof _syncWasActive !== 'undefined' && _syncWasActive) return;
    const now = Date.now();
    if (now - _lastWebhookToastAt < 4000) return;
    _lastWebhookToastAt = now;
    const kind = String(d.event).replace('webhook_', '');
    const label = t(_WEBHOOK_LABELS[kind] || 'Activity');
    const group = d.team_name ? ' — ' + d.team_name : '';
    const msg = t('Webhook received') + ': ' + label + group;
    if (typeof window.showToast === 'function') window.showToast(msg, 'info');
    GP.broadcastToast(msg, 'info');
  }

  /** Connect to the course dashboard SSE stream for live-data updates. */
  function _connectCourseDataSSE() {
    _disconnectCourseDataSSE();
    const previous = window.GP?.courseDetailDataSSE;
    if (previous && previous.courseId === String(COURSE_ID) && typeof previous.close === 'function') {
      previous.close();
    }
    _courseSSE = GP.sse({
      url: `/api/v1/courses/${COURSE_ID}/stream`,
      maxErrors: _COURSE_SSE_MAX_ERRORS,
      events: {
        connected: () => {
          if (window.GP?.debug) console.debug('[course-detail] Course data SSE connected');
          // Skip the first connect: trust the server render. Reconnects refresh.
          if (!_courseConnectedOnce) { _courseConnectedOnce = true; return; }
          _refreshCourseData();
        },
        update: (e) => {
          try {
            const d = JSON.parse(e.data);
            if (d && d.event === 'settings_changed') { reloadKeepScroll(); return; }
            // Structural project changes roll up into per-group project counts
            // and the course totals; re-render server-side so the counts and
            // any affected group rows reflect the committed state.
            if (d && typeof d.event === 'string'
                && (d.event === 'project_unlinked'
                  || d.event === 'project_reactivated'
                  || d.event === 'project_linked'
                  || d.event === 'team_deleted'
                  || d.event === 'team_reactivated')) {
              reloadKeepScroll();
              return;
            }
            // A GitLab webhook was just processed for a group in THIS course. The
            // data refresh below picks up the change; additionally surface a
            // teacher-only toast so staff watching the page see activity land live.
            if (d && typeof d.event === 'string' && d.event.indexOf('webhook_') === 0) {
              _maybeWebhookToast(d);
            }
          } catch (_) {}
          _refreshCourseData();
        },
      },
      onFailure: (n) => {
        if (window.GP?.debug) console.debug('[course-detail] Course data SSE error #' + n);
      },
      onGiveUp: () => {
        console.warn('[course-detail] Course data SSE max errors, using polling fallback');
        _startCoursePollingFallback();
      },
      onBlocked: () => {
        console.warn('[course-detail] Course data SSE unavailable, using polling fallback');
        _startCoursePollingFallback();
      },
    });
    window.GP = window.GP || {};
    window.GP.courseDetailDataSSE = {
      courseId: String(COURSE_ID),
      source: _courseSSE,
      close: _disconnectCourseDataSSE,
    };
  }

  function _disconnectCourseDataSSE() {
    if (_courseSSE) {
      const current = window.GP?.courseDetailDataSSE;
      if (current?.source === _courseSSE) delete window.GP.courseDetailDataSSE;
      _courseSSE.close();
      _courseSSE = null;
    }
  }

  let _courseAutoRefresh = null;
  function _startCoursePollingFallback() {
    if (_courseAutoRefresh) return;
    _courseAutoRefresh = setInterval(() => {
      if (document.visibilityState === 'visible') _refreshCourseData();
    }, 30000);
  }

  // Start SSE as primary mechanism for course data
  _connectCourseDataSSE();

  // Pause all SSE streams & polling when backend is unreachable
  let _courseHealthDown = false;
  const onHealthChange = (e) => {
    if (e.detail?.current === 'down' && !_courseHealthDown) {
      _courseHealthDown = true;
      disconnectSyncStream();
      _disconnectCourseDataSSE();
      if (_courseAutoRefresh) { clearInterval(_courseAutoRefresh); _courseAutoRefresh = null; }
    } else if (e.detail?.current !== 'down' && _courseHealthDown) {
      _courseHealthDown = false;
      connectSyncStream();
      _connectCourseDataSSE();
    }
  };
  document.addEventListener('gp-health-change', onHealthChange);

  /* -- Refresh after a job in this course completes -- */
  let _pendingRefresh = false;
  const onJobComplete = (ev) => {
    const d = ev.detail || {};
    if (d.status !== 'done' && d.status !== 'error') return;
    if (!GP.jobAffectsScope(d, { courseId: COURSE_ID })) return;
    if (document.visibilityState === 'visible') {
      _refreshCourseData();
    } else {
      _pendingRefresh = true;
    }
  };
  window.addEventListener('gp:job-complete', onJobComplete);

  const onVisibilityChangeJob = () => {
    if (_pendingRefresh && document.visibilityState === 'visible') {
      _pendingRefresh = false;
      _refreshCourseData();
    }
  };
  document.addEventListener('visibilitychange', onVisibilityChangeJob);

  const onBeforeUnload = () => {
    disconnectSyncStream();
    _disconnectCourseDataSSE();
    if (_courseAutoRefresh) { clearInterval(_courseAutoRefresh); _courseAutoRefresh = null; }
  };
  window.addEventListener('beforeunload', onBeforeUnload);

  // Expose functions for data-action delegation
  window.triggerSyncAll = triggerSyncAll;
  window.triggerSync = triggerSync;
  window.openLinkProjectModal = openLinkProjectModal;
  window.importGitlabIntoCourse = importGitlabIntoCourse;
  window.addTeam = addTeam;
  window.linkProject = linkProject;
  window.deleteTeam = deleteTeam;
  window.reactivateTeam = reactivateTeam;
  window.reactivateProject = reactivateProject;
  window.toggleDeletedTeams = toggleDeletedTeams;
  window.deleteTeamPermanent = deleteTeamPermanent;
  window.deleteProjectPermanent = deleteProjectPermanent;

  // Per-group "Recomputing..." badge so a Run Checks (all groups) run shows
  // visible per-row state (like a sync), not just the global bar. Clear these
  // badges when the process completes or the launch is declined.
  function _setGroupsRecomputing(on) {
    document.querySelectorAll('tr[data-team-id]').forEach(function (tr) {
      const nameCell = tr.querySelector('td:nth-child(2)');
      if (!nameCell) return;
      let badge = nameCell.querySelector('.group-recompute-badge');
      if (on) {
        if (!badge) {
          badge = document.createElement('span');
          badge.className = 'group-recompute-badge badge badge-info ml-2';
          badge.innerHTML =
            GP.renderSpinnerHtml('sm') + ' ' +
            t('Recomputing...');
          nameCell.appendChild(badge);
        }
      } else if (badge) {
        badge.remove();
      }
    });
  }

  // -- Run Checks (course scope, fan-out to all active groups) --
  (function initCourseRunChecks() {
    const btn = document.getElementById('btnRunChecks');
    if (!btn || !CAN_EDIT) return;
    btn.addEventListener('click', async () => {
      const courseId = btn.dataset.courseId || COURSE_ID;
      if (!courseId) return;
      const jobKey = 'run_checks:course:' + courseId;
      if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: 'course:' + courseId })) return;
      const boxes = document.querySelectorAll('#runChecksGrid input[name="check_codes"]:checked');
      const checkCodes = Array.from(boxes).map(cb => cb.value);
      if (!checkCodes.length) {
        showToast(t('Please select at least one check to run, or use Select all.'), 'warning');
        return;
      }
      const courseLabel = COURSE_NAME || t('this course');
      const confirmMsg = t('Recompute %d checks for every active group in %s? Each group will get its own background job.')
        .replace('%d', String(checkCodes.length)).replace('%s', courseLabel);
      const enqueueChecks = async () => {
        _setGroupsRecomputing(true);
        try {
          const result = await (window.GP?.runScopedChecksProcess || window.runScopedChecksProcess)?.({
            endpoint: `/api/v1/courses/${courseId}/run-checks`,
            statusUrl: `/api/v1/courses/${courseId}/run-checks-status`,
            jobKey,
            lockKey: 'runChecks:' + courseId,
            guardScopes: 'course:' + courseId,
            label: courseLabel,
            button: btn,
            courseId,
            runningMessage: t('Running checks for all groups in %s...').replace('%s', courseLabel),
            onComplete() {
              _setGroupsRecomputing(false);
              _refreshCourseData();
            },
          });
          if (!result || !Number(result.enqueued)) {
            _setGroupsRecomputing(false);
          }
        } catch (_) {
          _setGroupsRecomputing(false);
        }
      };
      if (typeof confirmDangerousAction === 'function') {
        await confirmDangerousAction(
          t('Run Checks'),
          enqueueChecks,
          { confirmText: confirmMsg, singleConfirm: true },
        );
        return;
      }
      await enqueueChecks();
    });
  })();

  /* -- Group tree rows -----------------------------------------------------
     Two states per group, both painted from the parent row's classes so that
     re-rendering (pagination, filtering, sort) can restore them without
     tracking anything of its own:
       .tree-row-expanded  - children are visible at all,
       .tree-row-show-all  - "View all" was used, so the extras are out too.
     The server marks the rows past the limit `.tree-row-extra` and appends one
     `.tree-row-more` row, so the cap lives in the template alone. */
  function _treeChildRows(parentRow) {
    const teamId = parentRow.dataset.teamId;
    const scope = parentRow.closest('tbody');
    if (!teamId || !scope) return [];
    return Array.from(scope.querySelectorAll(`tr[data-parent-team="${_cssEscape(teamId)}"]`));
  }

  function _paintTreeRows(parentRow) {
    const expanded = parentRow.classList.contains('tree-row-expanded');
    const showAll = parentRow.classList.contains('tree-row-show-all');
    _treeChildRows(parentRow).forEach(function(row) {
      const visible = expanded && (row.classList.contains('tree-row-more')
        ? !showAll
        : showAll || !row.classList.contains('tree-row-extra'));
      row.classList.toggle('d-none', !visible);
    });
  }

  function toggleTreeRow(evt) {
    const btn = evt instanceof Event
      ? (evt.target.closest ? evt.target.closest('.tree-toggle-btn') : null)
      : evt;
    if (!btn) return;
    const parentRow = btn.closest('tr');
    if (!parentRow || !parentRow.dataset.teamId) return;
    const expand = btn.getAttribute('aria-expanded') !== 'true';
    btn.setAttribute('aria-expanded', expand ? 'true' : 'false');
    /* The name and the tooltip follow the state. They used to say "Expand"
       whichever way the row was pointing - the button was also the only
       icon-only control on this page with no tooltip at all. */
    const _label = expand ? GP.t('Collapse') : GP.t('Expand');
    btn.setAttribute('aria-label', _label);
    btn.setAttribute('data-tippy-content', _label);
    if (btn._tippy && typeof btn._tippy.setContent === 'function') {
      btn._tippy.setContent(_label);
    }
    parentRow.classList.toggle('tree-row-expanded', expand);
    // Collapsing resets the disclosure, so re-expanding starts capped again.
    if (!expand) parentRow.classList.remove('tree-row-show-all');
    _paintTreeRows(parentRow);
  }
  window.toggleTreeRow = toggleTreeRow;

  function expandTreeRow(evt) {
    const moreRow = evt?.target?.closest?.('tr.tree-row-more');
    if (!moreRow) return;
    const parentRow = moreRow.closest('tbody')
      ?.querySelector(`tr[data-team-id="${_cssEscape(moreRow.dataset.parentTeam || '')}"]`);
    if (!parentRow) return;
    parentRow.classList.add('tree-row-show-all');
    _paintTreeRows(parentRow);
  }
  window.expandTreeRow = expandTreeRow;

  /* -- Modal Dirty-State Guards -- */
  if (typeof enableFormDirtyGuard === 'function') {
    enableFormDirtyGuard('addTeamModal');
    enableFormDirtyGuard('linkProjectModal');
  }

  const onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-course-detail-config') || target.id === 'gp-course-detail-config')) {
      GP.courseDetailCleanup();
    }
  };
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.courseDetailCleanup = () => {
    disconnectSyncStream();
    _disconnectCourseDataSSE();
    if (_courseAutoRefresh) { clearInterval(_courseAutoRefresh); _courseAutoRefresh = null; }
    if (_resumeTeamSyncTimer) { clearTimeout(_resumeTeamSyncTimer); _resumeTeamSyncTimer = null; }

    document.removeEventListener('DOMContentLoaded', _bootAutofill);
    window.removeEventListener('beforeunload', onBeforeUnload);
    document.removeEventListener('visibilitychange', onVisibilityChangeSSE);
    document.removeEventListener('gp-health-change', onHealthChange);
    window.removeEventListener('gp:job-complete', onJobComplete);
    document.removeEventListener('visibilitychange', onVisibilityChangeJob);
    document.body.removeEventListener('htmx:afterSwap', initCourseTeamPagination);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };
  GP.activePageCleanup = GP.courseDetailCleanup;
