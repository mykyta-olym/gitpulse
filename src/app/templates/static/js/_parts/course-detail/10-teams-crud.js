  
  // Initialize import modal lifecycle (from import_helpers.html)
  if (typeof initImportModals === 'function') initImportModals();
  
  // -- Team Pagination & Filter (using component library) --
  let _teamPaginator = null;
  let _teamFilter = null;

  function initCourseTeamPagination() {
    const table = document.getElementById('teamsTable');
    const controls = document.getElementById('teamPaginationControls');
    if (!table || !controls) return;

    if (table._clientPaginator && document.body.contains(table._clientPaginator.controls)) {
      _teamPaginator = table._clientPaginator;
      return;
    }

    _teamPaginator = new ClientPaginator({
      tbodySelector: '#teamsTable tbody',
      controlsSelector: '#teamPaginationControls',
      pageSize: 50,
      showPerPage: true,
      pageSizes: [25, 50, 100],
      itemSelector: 'tr[data-team-id]'
    }).register('teamTable');

    // After paginator renders, sync child row visibility with parent rows
    _teamPaginator.render = function() {
      ClientPaginator.prototype.render.call(_teamPaginator);
      _syncTreeChildRows();
    };

    _teamFilter = new TableFilter({
      inputSelector: '#teamSearchInput',
      tbodySelector: '#teamsTable tbody',
      paginator: _teamPaginator
    });

    _teamPaginator.render();
  }

  function _syncTreeChildRows() {
    if (!_teamPaginator) return;
    const tbody = _teamPaginator.tbody;
    if (!tbody) return;
    // A parent hidden by the current page/filter hides its whole subtree;
    // otherwise _paintTreeRows decides, so the "View all" cap survives a
    // re-render instead of dumping every child row back on screen.
    tbody.querySelectorAll('tr[data-team-id]').forEach(function(parent) {
      if (parent.classList.contains('d-none')) {
        tbody.querySelectorAll('tr[data-parent-team="' + _cssEscape(parent.dataset.teamId) + '"]')
          .forEach(function(child) { child.classList.add('d-none'); });
      } else {
        _paintTreeRows(parent);
      }
    });
  }

  // Rebind after the course table is replaced by an HTMX response.
  initCourseTeamPagination();
  document.body.addEventListener('htmx:afterSwap', initCourseTeamPagination);

  function _jsonAttr(args) {
    return _escHtml(JSON.stringify(Array.isArray(args) ? args : []));
  }

  function _cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === 'function') {
      return window.CSS.escape(String(value));
    }
    return String(value).replace(/([^\w-])/g, '\\$1');
  }

  const csrfToken = window._csrfToken || '';

  async function addTeam(e) {
    if (!GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID })) {
      e.preventDefault();
      return;
    }
    const form = e.target;
    // Client-side guard: reject blank / single-char names (e.g. a stray "ф")
    // before the request so the user gets immediate feedback, not a 422.
    const _nameVal = (form.name?.value || '').trim();
    if (_nameVal.length < 2) {
      e.preventDefault();
      const _msg = t('Group name must be at least 2 non-space characters.');
      if (form.name) showFieldError(form.name, _msg);
      else showToast(_msg, 'warning');
      return;
    }
    return submitModalForm(e, {
      url: '/api/v1/teams/',
      modalId: 'addTeamModal',
      btnSelector: '#addTeamBtn',
      reload: false,
      getData: (f) => {
        const data = { name: f.name.value, course_id: COURSE_ID };
        if (f.gitlab_namespace.value) data.gitlab_group_path = f.gitlab_namespace.value;
        return data;
      },
      successMsg: t('Group added!'),
      onSuccess(result) {
        const tbody = document.querySelector('.data-table tbody');
        // First group in the course: the table doesn't exist yet (empty state
        // was showing). Hand-building the full sortable/tree table + <colgroup>
        // here drifts from the server macro (teams_table_head) - the columns
        // and their responsive hide-breakpoints (col-hide-sm/md) end up
        // mismatched, which is exactly what shifts the cells out of alignment.
        // Reload once so the server renders the canonical table.
        if (!tbody && result && result.id) {
          // Scroll-preserving, consistent with every other reload in this file.
          reloadKeepScroll();
          return;
        }
        if (tbody && result && result.id) {
          const tr = document.createElement('tr');
          tr.setAttribute('data-search', (result.name || '').toLowerCase());
          tr.setAttribute('data-team-id', result.id);
          const canEdit = _pageConfig.canEdit === true;
          const teamId = String(result.id || '');
          const teamName = String(result.name || '');
          const safeTeamName = _escHtml ? _escHtml(teamName) : teamName;
          const safeTeamId = encodeURIComponent(teamId);
          // The server row's buttons exactly (btn_icon_only, 16px glyphs): this
          // row had 14px glyphs in padded `btn-icon` boxes and a FILLED delete.
          const _icn = (n) => GP.iconSvg(n, 'sm') || '';
          const viewTip = t('Open the group: members, projects and their checks');
          // Component (tippy) tooltips via data-tippy-content - never native title=.
          const actionsHtml = canEdit
            ? `<button class="btn btn-icon-only btn-secondary btn-sm" data-action="openLinkProjectModal" data-action-args='${_jsonAttr([teamId, teamName])}' data-process-lock-when="sync import run_checks" data-process-lock-scope="course:${COURSE_ID} team:${teamId}" data-tippy-content="${t('Link Project')}" aria-label="${t('Link Project')}">${_icn('link')}</button>
               <button class="btn btn-icon-only btn-secondary btn-sm" data-action="triggerSync" data-action-args='${_jsonAttr([teamId, teamName, '$event'])}' data-process-lock-when="sync run_checks" data-process-lock-scope="course:${COURSE_ID} team:${teamId}" data-tippy-content="${t('Sync')}" aria-label="${t('Sync')}">${_icn('refresh')}</button>
               <button class="btn btn-icon-only btn-danger btn-sm" data-action="deleteTeam" data-action-args='${_jsonAttr([teamId, teamName, '$event'])}' data-process-lock-when="sync import run_checks" data-process-lock-scope="course:${COURSE_ID} team:${teamId}" data-tippy-content="${t('Delete Group')}" aria-label="${t('Delete Group')}">${_icn('trash')}</button>`
            : '';
          // Cell classes MUST mirror the server row (partials/course/_detail_content.html)
          // and the <colgroup> in teams_table_head - especially col-hide-sm on the
          // tree-toggle cell, text-center on Status, and col-hide-md on Last Updated -
          // otherwise this row keeps cells the header hides on narrow viewports and
          // the whole row shifts out of column alignment.
          tr.innerHTML = `
            <td class="col-tree-toggle col-hide-sm"></td>
            <td><a href="/dashboard/teams/${safeTeamId}" class="text-bold">${safeTeamName}</a></td>
            <td>0</td>
            <td>-</td>
            <td class="text-center" data-sort-value="3">${GP.badgeHtml(t('N/A'), 'gray')}</td>
            <td class="muted col-hide-md">-</td>
            <td class="text-right"><div class="gl-row-actions">${actionsHtml}<a href="/dashboard/teams/${safeTeamId}" class="btn btn-icon-only btn-secondary btn-sm" aria-label="${viewTip}" data-tippy-content="${viewTip}">${_icn('eye')}</a></div></td>`;
          tbody.appendChild(tr);
          // Bind tippy to the freshly-inserted action buttons (component tooltips).
          GP.initTippy(tr);
          // Resync paginator and filter with new row (also updates match count)
          _teamPaginator.resync();
          _teamFilter.resync();
        }
      }
    });
  }

  async function importGitlabIntoCourse(e) {
    e.preventDefault();
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID })) return;
    await submitGitLabImport({ target_course_id: COURSE_ID }, () => {
      // Toast already shown by finalizeImportSuccess - reload the page so
      // newly imported groups appear in the table.  The importJustCompleted
      // flag prevents a second reload when the SSE complete event fires.
      // Small delay lets flashToast persist properly to sessionStorage
      // before navigation begins.
      if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
      setTimeout(() => { reloadKeepScroll(); }, 300);
    });
  }
  
  function openLinkProjectModal(teamId, teamName) {
    const scope = 'course:' + COURSE_ID + ' team:' + teamId;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope })) return;
    document.getElementById('projectTeamId').value = teamId;
    document.getElementById('projectTeamName').textContent = teamName;
    const submitBtn = document.getElementById('linkProjectBtn');
    if (submitBtn) submitBtn.dataset.processLockScope = scope;
    GP.refreshProcessActionGuards();
    openModal('linkProjectModal');
  }
  
  async function linkProject(e) {
    const form = e.target;
    const teamId = form.team_id.value;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + teamId })) {
      e.preventDefault();
      return;
    }
    // Guard: require project ID and path
    const projId = (form.gitlab_project_id.value || '').trim();
    const projPath = (form.gitlab_project_path.value || '').trim();
    if (!projId) {
      showToast(t('GitLab Project ID is required'), 'warning');
      e.preventDefault();
      return;
    }
    if (!projPath) {
      showToast(t('Project path is required'), 'warning');
      e.preventDefault();
      return;
    }
    return submitModalForm(e, {
      url: `/api/v1/projects/${teamId}/projects`,
      modalId: 'linkProjectModal',
      btnSelector: '#linkProjectBtn',
      reload: false,
      getData: (f) => ({
        gitlab_project_id: parseInt(f.gitlab_project_id.value),
        gitlab_project_path: f.gitlab_project_path.value,
        gitlab_project_name: f.gitlab_project_name.value || f.gitlab_project_path.value
      }),
      successMsg: t('Project linked!')
    });
  }
  
  async function deleteTeam(teamId, teamName, event) {
    if (!CAN_EDIT) { showToast(t('You do not have permission to delete this group.'), 'warning'); return; }
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + teamId })) return;
    const teamRow = document.querySelector(`tr[data-team-id="${_cssEscape(teamId)}"]`);
    const deleteBtn = event?.target?.closest?.('button[data-action="deleteTeam"]')
      || teamRow?.querySelector('button[data-action="deleteTeam"]')
      || null;
    confirmDangerousAction(teamName || 'this group', async () => {
      try {
        await _lock(`deleteTeam:${teamId}`, async () => {
          if (deleteBtn) setButtonLoading(deleteBtn, true);
          await apiCall(`/api/v1/teams/${teamId}`, 'DELETE');
          showToast(t('Group deleted!'), 'success');
          // Soft-delete: the group stays in the table (dimmed, restorable).
          // Reload from the server so the dimmed row, the "Deleted" toggle,
          // the Restore action and the recomputed course stat cards all
          // reflect the authoritative server state - no client/server drift.
          if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
          setTimeout(() => { reloadKeepScroll(); }, 500);
        }); // end withUiLock
      } catch (err) {
        if (err.code !== 'LOCKED') showToast(err.message, 'danger');
        if (deleteBtn) setButtonLoading(deleteBtn, false);
      }
    }, { confirmText: t('This group exists in GitLab. It will be re-created on next sync if the GitLab subgroup still exists. Continue?') });
  }

  // -- Restore a soft-deleted group (teacher/admin) --
  async function reactivateTeam(event) {
    const btn = event?.target?.closest?.('[data-action="reactivateTeam"]');
    if (!btn) return;
    if (!CAN_EDIT) { showToast(t('You do not have permission to restore this group.'), 'warning'); return; }
    const teamId = btn.dataset.teamId;
    const teamName = btn.dataset.teamName || '';
    if (!teamId) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + teamId })) return;
    confirmDangerousAction(
      teamName || 'this group',
      async () => {
        try {
          await _lock(`reactivateTeam:${teamId}`, async () => {
            setButtonLoading(btn, true);
            await apiCall(`/api/v1/teams/${teamId}/reactivate`, 'POST');
            showToast(t('Group restored'), 'success');
            if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
            setTimeout(() => { reloadKeepScroll(); }, 500);
          });
        } catch (err) {
          if (err.code !== 'LOCKED') showToast(err.message || t('Failed to restore group'), 'danger');
          setButtonLoading(btn, false);
        }
      },
      {
        confirmText: t('Restore this group? It will become active again and can be synced and checked.'),
        singleConfirm: true,
      }
    );
  }

  // -- Permanent delete a group (teacher/admin) --
  async function deleteTeamPermanent(event) {
    const btn = event?.target?.closest?.('[data-action="deleteTeamPermanent"]');
    if (!btn) return;
    if (!CAN_EDIT) { showToast(t('You do not have permission to delete this group.'), 'warning'); return; }
    const teamId = btn.dataset.teamId;
    const teamName = btn.dataset.teamName || '';
    if (!teamId) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + teamId })) return;
    confirmDangerousAction(
      teamName || 'this group',
      async () => {
        try {
          await _lock(`deleteTeamPermanent:${teamId}`, async () => {
            setButtonLoading(btn, true);
            await apiCall(`/api/v1/teams/${teamId}/permanent`, 'DELETE');
            showToast(t('Group permanently deleted'), 'success');
            if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
            setTimeout(() => { reloadKeepScroll(); }, 500);
          });
        } catch (err) {
          if (err.code !== 'LOCKED') showToast(err.message || t('Failed to delete group'), 'danger');
          setButtonLoading(btn, false);
        }
      },
      {
        confirmText: t('Are you sure you want to permanently delete "%s" and all its projects, members, and data? This action cannot be undone.').replace('%s', teamName),
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
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: btn.dataset.processLockScope || ('project:' + projectId) })) return;
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

  // -- Restore a soft-deleted (unlinked) project from the course tree --
  async function reactivateProject(event) {
    const btn = event?.target?.closest?.('[data-action="reactivateProject"]');
    if (!btn) return;
    if (!CAN_EDIT) { showToast(t('You do not have permission to restore this project.'), 'warning'); return; }
    const projectId = btn.dataset.projectId;
    if (!projectId) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: btn.dataset.processLockScope || ('project:' + projectId) })) return;
    try {
      await _lock(`reactivateProject:${projectId}`, async () => {
        setButtonLoading(btn, true);
        await apiCall(`/api/v1/projects/${projectId}/reactivate`, 'POST');
        showToast(t('Project restored'), 'success');
        if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
        setTimeout(() => { reloadKeepScroll(); }, 500);
      });
    } catch (err) {
      if (err.code !== 'LOCKED') showToast(err.message || t('Failed to reactivate project'), 'danger');
      setButtonLoading(btn, false);
    }
  }

  // -- Toggle visibility of dimmed soft-deleted group rows --
  function toggleDeletedTeams(event) {
    const btn = event?.target?.closest?.('[data-action="toggleDeletedTeams"]');
    const table = document.getElementById('teamsTable') || document.querySelector('.data-table');
    if (!table) return;
    const hidden = table.classList.toggle('gp-hide-deleted');
    if (btn) btn.setAttribute('aria-pressed', hidden ? 'false' : 'true');
    // Keep tree child rows consistent with their (possibly hidden) parents.
    if (typeof _syncTreeChildRows === 'function') _syncTreeChildRows();
  }
  
  async function triggerSync(teamId, teamName, event) {
    if (!CAN_EDIT) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + teamId })) return;
    const jobKey = 'sync:team:' + teamId;
    const syncBtn = event?.target?.closest?.('button[data-action="triggerSync"]') || null;
    let syncStreamSuspended = false;
    const resumeCourseSyncStream = (options) => {
      if (!syncStreamSuspended) return;
      syncStreamSuspended = false;
      _resumeCourseSyncStreamAfterTeamSync(options);
    };
    try {
      await _lock('sync:' + teamId, async () => {
        if (syncBtn) setButtonLoading(syncBtn, true);
    
        const syncMessage = document.getElementById('syncMessage');
        const syncDetails = document.getElementById('syncDetails');
        const syncSpinner = document.getElementById('syncSpinner');

        if (syncMessage) { syncMessage.classList.remove('text-success', 'text-danger', 'text-warning'); syncMessage.textContent = t('Syncing') + ' ' + teamName + '...'; }
        if (syncDetails) syncDetails.textContent = t('This may take a few seconds.');
        if (syncSpinner) syncSpinner.classList.remove('d-none');
        // syncStatusModal removed: progress now shown only in the persistent
        // top-of-page global job bar (avoids duplicate UI). The modal markup
        // is gone, so any getElementById hits below silently no-op.

        const syncLabel = t('Syncing group:') + ' ' + (teamName || t('group'));
        const syncMeta = { teamId: String(teamId || ''), courseId: String(COURSE_ID || ''), teamName: teamName || '', jobKind: 'team_sync' };
        if (typeof connectGlobalJob === 'function') {
          connectGlobalJob(jobKey, syncLabel, syncMeta);
        } else if (typeof deferGlobalJob === 'function') {
          deferGlobalJob(syncLabel, jobKey, syncMeta);
        }

        // Suspend course-level SSE while this single-team sync is tracked by
        // the job-level SSE. Multiple row syncs may run in parallel, so use a
        // counter instead of clearing the suppression window on the first
        // completion.
        _suspendCourseSyncStreamForTeamSync();
        syncStreamSuspended = true;

        const result = await apiCall(`/api/v1/teams/${teamId}/sync`, 'POST');

        // Freshness short-circuit: server reports data is already up-to-date.
        if (result && result.status === 'skipped_fresh') {
          if (syncSpinner) syncSpinner.classList.add('d-none');
          if (syncMessage) { syncMessage.textContent = t('Already up-to-date'); syncMessage.classList.add('text-success'); }
          if (syncDetails) syncDetails.textContent = result.message || '';
          const msg = result.message || t('Already up-to-date');
          if (typeof completeGlobalJob === 'function') completeGlobalJob(jobKey, msg, 'done');
          else showToast(msg, 'info');
          resumeCourseSyncStream({ delay: 1000 });
          _resetSyncButtons(syncBtn);
          return;
        }

        if (!result || result.status === 'failed' || result.status === 'cancelled' || !result.job_id) {
          const message = result?.message || t('Sync failed');
          if (syncSpinner) syncSpinner.classList.add('d-none');
          if (syncMessage) { syncMessage.textContent = message; syncMessage.classList.add('text-danger'); }
          if (syncDetails) syncDetails.textContent = message;
          const handledByGlobal = typeof completeGlobalJob === 'function'
            && completeGlobalJob(jobKey, message, 'error');
          if (!handledByGlobal) showToast(message, 'danger');
          resumeCourseSyncStream({ delay: 0 });
          _resetSyncButtons(syncBtn);
          return;
        }

        if (syncMessage) syncMessage.textContent = t('Sync started!');
        if (syncDetails) syncDetails.textContent = `${t('Job ID')}: ${result.job_id}`;

        if (typeof deferGlobalJob === 'function') {
          deferGlobalJob(
            syncLabel,
            jobKey,
            { ...syncMeta, jobId: result.job_id },
          );
        }
        if (typeof setGlobalJobMeta === 'function') {
          setGlobalJobMeta(jobKey, { jobId: result.job_id });
        }

        const startedAt = Date.now();
        if (typeof streamJobProgress !== 'function') {
          showToast(t('Sync started. Refresh to see results.'), 'info');
          if (syncBtn) setButtonLoading(syncBtn, false);
          resumeCourseSyncStream({ delay: 1000 });
          return;
        }
        streamJobProgress(result.job_id, {
          onUpdate(data) {
            const s = (data.status || '').toLowerCase();
            const elapsedSec = Math.floor((Date.now() - startedAt) / 1000);
            if (syncMessage) syncMessage.textContent = s === 'running'
              ? (data.message || t('Sync in progress...'))
              : t('Waiting for worker...');
            if (syncDetails) syncDetails.textContent = data.result_summary || `${t('Job ID')}: ${result.job_id} * ${elapsedSec}s ${t('elapsed')}`;
          },
          onComplete(data) {
            _resetSyncButtons(syncBtn);
            const s = (data.status || '').toLowerCase();
            if (syncSpinner) syncSpinner.classList.add('d-none');
            if (s === 'failed' || s === 'cancelled') {
              const failedLabel = s === 'cancelled'
                ? t('Sync cancelled')
                : t('Sync failed');
              if (syncMessage) { syncMessage.textContent = failedLabel; syncMessage.classList.add('text-danger'); }
              if (syncDetails) syncDetails.textContent = data.error_message
                || t('Unknown error');
              const failMsg = data.error_message || (s === 'cancelled' ? t('Group sync cancelled') : t('Group sync failed'));
              const handledByGlobal = typeof completeGlobalJob === 'function'
                && completeGlobalJob(jobKey, failMsg, 'error');
              if (!handledByGlobal) showToast(failMsg, 'danger');
              // Anti-spam cooldown on a genuine failure (not a user cancel).
              if (s === 'failed' && syncBtn) {
                GP.applyCooldown(syncBtn);
              }
              resumeCourseSyncStream({ delay: 1200 });
            } else {
              if (syncMessage) { syncMessage.textContent = t('Sync completed!'); syncMessage.classList.add('text-success'); }
              if (syncDetails) syncDetails.textContent = data.result_summary || '';
              const doneMsg = t('Group sync completed');
              const handledByGlobal = typeof completeGlobalJob === 'function'
                && completeGlobalJob(jobKey, doneMsg, 'done');
              if (!handledByGlobal) showToast(doneMsg, 'success');
              resumeCourseSyncStream({ delay: 1200, refresh: true });
            }
          },
          onError() {
            resumeCourseSyncStream({ delay: 0 });
            _resetSyncButtons(syncBtn);
            if (syncSpinner) syncSpinner.classList.add('d-none');
            if (syncMessage) { syncMessage.textContent = t('Sync status unknown'); syncMessage.classList.add('text-warning'); }
            if (syncDetails) syncDetails.textContent = `${t('Job ID')}: ${result.job_id}. ${t('It will keep running in the background.')}`;
            if (typeof completeGlobalJob === 'function') completeGlobalJob(jobKey, t('Sync status unknown'), 'error');
          },
        });
      });
    } catch (err) {
      resumeCourseSyncStream({ delay: 0 });
      if (err.code !== 'LOCKED') {
        const syncSpinner = document.getElementById('syncSpinner');
        const syncMessage = document.getElementById('syncMessage');
        const syncDetails = document.getElementById('syncDetails');
        if (syncSpinner) syncSpinner.classList.add('d-none');
        if (syncMessage) { syncMessage.textContent = t('Failed to start sync'); syncMessage.classList.add('text-danger'); }
        if (syncDetails) syncDetails.textContent = err.message;
        const msg = (err && err.message) || t('Failed to start sync');
        if (typeof completeGlobalJob === 'function') completeGlobalJob(jobKey, msg, 'error');
        else showToast(msg, 'danger');
        if (syncBtn) {
          setButtonLoading(syncBtn, false);
          GP.applyCooldown(syncBtn);
        }
      }
    }
  }
  
