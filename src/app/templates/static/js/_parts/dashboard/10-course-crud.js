  const csrfToken = window._csrfToken || '';
  const _COURSE_WRITE_PROCESSES = ['sync', 'import', 'run_checks'];

  function _courseScope(courseId) {
    const id = String(courseId || '').trim();
    return id ? `course:${id}` : '';
  }

  function _guardCourseWrite(courseId) {
    const scope = _courseScope(courseId);
    if (!scope || !GP.guardProcessAction) return true;
    return GP.guardProcessAction(_COURSE_WRITE_PROCESSES, { scope });
  }

  function _setCourseProcessLock(el, courseId, processes) {
    const scope = _courseScope(courseId);
    if (!el || !scope) return;
    el.dataset.processLockWhen = (processes || _COURSE_WRITE_PROCESSES).join(' ');
    el.dataset.processLockScope = scope;
  }

  async function createCourse(e) {
    if (!_canEdit) { showToast(GP.t('No permission'), 'warning'); return; }
    return submitModalForm(e, {
      url: '/api/v1/courses/',
      modalId: 'createCourseModal',
      btnSelector: '#createCourseBtn',
      loadingText: GP.t('Creating...'),
      getData: () => {
        const startVal = document.getElementById('courseSemesterStart')?.value?.trim() || '';
        const endVal = document.getElementById('courseSemesterEnd')?.value?.trim() || '';
        const payload = {
          code: document.getElementById('courseCode')?.value?.trim() || '',
          name: document.getElementById('courseName')?.value?.trim() || '',
          description: document.getElementById('courseDescription')?.value?.trim() || '',
          academic_year: document.getElementById('academicYear')?.value?.trim() || '',
          semester: document.getElementById('semester')?.value || 'winter'
        };
        if (startVal) payload.semester_start_date = startVal;
        if (endVal) payload.semester_end_date = endVal;
        return payload;
      },
      successMsg: GP.t('Course created!'),
      reload: false,
      onSuccess: (result) => {
        // Refresh sidebar badge counts
        if (typeof GP.refreshSidebarBadges === 'function') GP.refreshSidebarBadges();
        // Redirect to the new course page
        if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
        window.location.href = '/dashboard/courses/' + result.id;
      }
    });
  }

  async function importGitlabCourse(e) {
    e.preventDefault();
    if (GP.guardProcessAction && !GP.guardProcessAction(['import'])) return;
    if (typeof importInProgress !== 'undefined' && importInProgress) {
      showToast(GP.t('Import is already in progress. Please wait for it to complete.'), 'warning');
      return;
    }
    const form = document.getElementById('importGitlabCourseForm');
    const targetCourseId = form.target_course_id.value || null;
    if (targetCourseId && !_guardCourseWrite(targetCourseId)) return;
    // Optional dates: omit when blank so the schema's date-or-null accepts
    // them. flatpickr leaves the visible input as ISO yyyy-mm-dd.
    const startEl = document.getElementById('importCourseSemesterStart');
    const endEl = document.getElementById('importCourseSemesterEnd');
    const startVal = startEl && startEl.value ? startEl.value : null;
    const endVal = endEl && endEl.value ? endEl.value : null;
    await submitGitLabImport({
      target_course_id: targetCourseId,
      course_code: form.course_code.value,
      course_name: form.course_name.value,
      academic_year: form.academic_year.value,
      semester: form.semester.value,
      semester_start_date: startVal,
      semester_end_date: endVal,
    }, (result) => {
      // Toast already shown by finalizeImportSuccess. Show the course where it
      // landed: a page scoped to another term goes to the course's term,
      // otherwise the page reloads in place.
      if (GP.followPeriod && result && GP.followPeriod(result.course_academic_year, result.course_semester)) return;
      if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
      reloadKeepScroll();
    });
  }

  function toggleImportCourseFields() {
    const targetSelect = document.getElementById('importTargetCourseId');
    const newCourseFields = document.getElementById('importNewCourseFields');
    if (!targetSelect || !newCourseFields) return;
    const importingToExisting = Boolean(targetSelect.value);
    newCourseFields.classList.toggle('d-none', importingToExisting);
  }
  
  function openAddTeamModal(courseId, courseName) {
    if (!_guardCourseWrite(courseId)) return;
    const el = document.getElementById('teamCourseId');
    const nameEl = document.getElementById('teamModalCourseName');
    if (el) el.value = courseId;
    if (nameEl) nameEl.textContent = courseName;
    _setCourseProcessLock(document.getElementById('addTeamBtn'), courseId);
    GP.refreshProcessActionGuards(document.getElementById('addTeamModal'));
    openModal('addTeamModal');
  }
  
  async function addTeam(e) {
    const courseId = document.getElementById('teamCourseId')?.value;
    if (!_guardCourseWrite(courseId)) {
      e.preventDefault();
      return;
    }
    return submitModalForm(e, {
      url: '/api/v1/teams/',
      modalId: 'addTeamModal',
      btnSelector: '#addTeamBtn',
      getData: (f) => {
        const data = { name: f.name.value, course_id: f.course_id.value };
        if (f.gitlab_namespace.value) data.gitlab_group_path = f.gitlab_namespace.value;
        return data;
      },
      successMsg: GP.t('Group added!'),
      reload: false,
      flash: false,
      onSuccess: () => refreshDashboardStats()
    });
  }
  
  function openCourseMenu(courseId, code, name, year, semester, description, start, end) {
    const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
    setVal('menuCourseId', courseId);
    setVal('menuCourseCode', code);
    setVal('menuCourseName', name);
    setVal('menuCourseYear', year);
    setVal('menuCourseSemester', semester);
    setVal('menuCourseStart', start || '');
    setVal('menuCourseEnd', end || '');
    setVal('menuCourseDescription', description || '');
    const modal = document.getElementById('courseMenuModal');
    modal?.querySelectorAll('[data-action="openEditCourseModal"], [data-action="archiveCourse"]').forEach((btn) => {
      _setCourseProcessLock(btn, courseId);
    });
    GP.refreshProcessActionGuards(modal);
    openModal('courseMenuModal'); 
  }
  
  function openEditCourseModal() {
    const getVal = (id) => { const el = document.getElementById(id); return el ? el.value : ''; };
    if (!_guardCourseWrite(getVal('menuCourseId'))) return;
    const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
    setVal('editCourseId', getVal('menuCourseId'));
    setVal('editCourseCode', getVal('menuCourseCode'));
    setVal('editCourseName', getVal('menuCourseName'));
    // The period and its dates as ONE set - the same fields, and the same
    // rules, as Create Course: move the course to another term here and its
    // dates move with it, unless they are the teacher's own.
    const periodFields = GP.periodFields?.of(document.getElementById('editCourseForm'));
    const loaded = {
      academic_year: getVal('menuCourseYear'),
      semester: getVal('menuCourseSemester'),
      start: getVal('menuCourseStart'),
      end: getVal('menuCourseEnd'),
    };
    if (periodFields) periodFields.fill(loaded);
    else {
      setVal('editCourseYear', loaded.academic_year);
      setVal('editCourseSemester', loaded.semester);
    }
    const descEl = document.getElementById('editCourseDescription');
    if (descEl) descEl.value = getVal('menuCourseDescription');
    _setCourseProcessLock(document.getElementById('editCourseBtn'), getVal('menuCourseId'));
    GP.refreshProcessActionGuards(document.getElementById('editCourseModal'));
    closeModal('courseMenuModal');
    openModal('editCourseModal');
  }
  
  async function updateCourse(e) {
    const courseId = document.getElementById('editCourseId')?.value;
    if (!courseId) return;
    if (!_guardCourseWrite(courseId)) {
      e.preventDefault();
      return;
    }
    return submitModalForm(e, {
      url: `/api/v1/courses/${courseId}`,
      method: 'PUT',
      modalId: 'editCourseModal',
      btnSelector: '#editCourseBtn',
      getData: () => ({
        code: document.getElementById('editCourseCode')?.value || '',
        name: document.getElementById('editCourseName')?.value || '',
        academic_year: document.getElementById('editCourseYear')?.value || '',
        semester: document.getElementById('editCourseSemester')?.value || '',
        // Sent every time, empty as null: the dates are saved with the period
        // they belong to, never left behind in the old term.
        semester_start_date: document.getElementById('editCourseStart')?.value || null,
        semester_end_date: document.getElementById('editCourseEnd')?.value || null,
        description: document.getElementById('editCourseDescription')?.value || ''
      }),
      successMsg: GP.t('Course updated!'),
      reload: false,
      flash: false,
      onSuccess: () => {
        const newYear = document.getElementById('editCourseYear')?.value || '';
        const newSemester = document.getElementById('editCourseSemester')?.value || '';
        // Moved to a term other than the one on screen: follow the course there
        // rather than leave its card in a list it no longer belongs to.
        if (GP.followPeriod && GP.followPeriod(newYear, newSemester)) return;
        // Update course card in the DOM
        const card = document.querySelector(`a[href="/dashboard/courses/${courseId}"]`)?.closest('.course-card');
        if (card) {
          const codeEl = card.querySelector('.course-card-code');
          const titleEl = card.querySelector('.course-card-title');
          const termEl = card.querySelector('.course-card-semester');
          const descEl = card.querySelector('.course-card-description');
          const newDesc = (document.getElementById('editCourseDescription')?.value || '').trim();
          if (codeEl) codeEl.textContent = document.getElementById('editCourseCode')?.value || '';
          if (titleEl) titleEl.textContent = document.getElementById('editCourseName')?.value || '';
          if (termEl && GP.periodLabel) termEl.textContent = GP.periodLabel(newYear, newSemester);
          if (descEl) {
            if (newDesc) { descEl.textContent = newDesc.length > _DESC_MAX_LEN ? newDesc.substring(0, _DESC_MAX_LEN - 3) + '...' : newDesc; descEl.classList.remove('d-none'); }
            else { descEl.textContent = ''; descEl.classList.add('d-none'); }
          } else if (newDesc) {
            const d = document.createElement('div'); d.className = 'course-card-description muted'; d.textContent = newDesc.length > _DESC_MAX_LEN ? newDesc.substring(0, _DESC_MAX_LEN - 3) + '...' : newDesc;
            titleEl?.insertAdjacentElement('afterend', d);
          }
          card.setAttribute('data-search', `${(document.getElementById('editCourseCode')?.value || '').toLowerCase()} ${(document.getElementById('editCourseName')?.value || '').toLowerCase()} ${document.getElementById('editCourseYear')?.value || ''}`);
          // Keep the menu button's action args in step, so the next Edit opens
          // on what was just saved.
          const menuBtn = card.querySelector('[data-action="openCourseMenu"]');
          if (menuBtn) {
            const args = JSON.parse(menuBtn.dataset.actionArgs || '[]');
            if (args.length >= 6) {
              args[1] = document.getElementById('editCourseCode')?.value || args[1];
              args[2] = document.getElementById('editCourseName')?.value || args[2];
              args[3] = newYear;
              args[4] = newSemester;
              args[5] = newDesc;
              args[6] = document.getElementById('editCourseStart')?.value || '';
              args[7] = document.getElementById('editCourseEnd')?.value || '';
              menuBtn.dataset.actionArgs = JSON.stringify(args);
            }
          }
        }
      }
    });
  }
  
  function goToSettings() { const id = document.getElementById('menuCourseId')?.value; if (id) window.location.href = `/dashboard/courses/${id}/settings`; }
  /* One transfer flow for the whole app: the full wizard lives in course
     settings (Danger Zone) - the old duplicate dashboard clone modal and its
     /clone call were removed with the bare-clone API. */
  function transferCourse() { const id = document.getElementById('menuCourseId')?.value; closeModal('courseMenuModal'); if (id) window.location.href = `/dashboard/courses/${id}/settings#transfer`; }
  
  function _removeCourseCard(courseId) {
    const card = document.querySelector(`a[href="/dashboard/courses/${courseId}"]`)?.closest('.course-card');
    if (!card) return;
    /* update visible card count on active filter, after the card is gone */
    const afterRemove = () => {
      document.querySelectorAll('.courses-grid').forEach(grid => {
        if (!grid.children.length) {
          grid.innerHTML = GP.emptyStateHtml(GP.t('No courses in this section'));
        }
      });
    };
    // Collapse smoothly (fade, then height) instead of fade-then-snap-gap.
    GP.collapseAndRemove(card, afterRemove);
  }

  const _ca = GP.courseActions || {};
  const _notFoundFallback = (url) => (err) => {
    if ((err.message || '').toLowerCase().includes('not found')) {
      submitDashboardPost(url);
      return true;
    }
    return false;
  };

  async function archiveCourse(actionEvent) {
    if (!_canEdit) return;
    const courseId = document.getElementById('menuCourseId')?.value;
    if (!courseId) {
      showToast(GP.t('Please open the course menu first'), 'danger');
      return;
    }
    const btn = actionEvent?.target?.closest?.('button, a') || null;
    _ca.archive(courseId, btn, {
      onSuccess: () => { closeModal('courseMenuModal'); _removeCourseCard(courseId); },
      onError: _notFoundFallback(`/dashboard/courses/${courseId}/archive`),
    });
  }
  
  async function activateCourse(courseId, actionEvent) {
    if (!_canEdit) return;
    const btn = actionEvent?.target?.closest?.('button, a') || null;
    _ca.activate(courseId, btn, {
      onSuccess: () => { _removeCourseCard(courseId); },
      onError: _notFoundFallback(`/dashboard/courses/${courseId}/activate`),
    });
  }

  async function deleteCourse(courseId, courseCode, actionEvent) {
    if (!_isAdmin) { showToast(GP.t('Admin access required'), 'warning'); return; }
    const btn = actionEvent?.target?.closest?.('button, a') || null;
    _ca.deletePermanent(courseId, courseCode, btn, {
      onSuccess: () => { _removeCourseCard(courseId); },
    });
  }

  function submitDashboardPost(url) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;

    const csrf = document.createElement('input');
    csrf.type = 'hidden';
    csrf.name = 'csrf_token';
    csrf.value = csrfToken;
    form.appendChild(csrf);

    document.body.appendChild(form);
    form.submit();
  }

  // Initialise Flatpickr on every `.date-picker` input rendered into the
  // dashboard modals (Create / Edit / Clone Course, Import-from-GitLab).
  // Idempotent: `initFlatpickr` skips elements that already have a
  // `_flatpickr` instance attached, so it is safe to call after every
  // HTMX swap.
  function _wireDatePickers() {
    if (typeof initFlatpickr === 'function') initFlatpickr('.date-picker');
  }

  function _registerCourseCardSyncs() {
    // Register global sync jobs for courses with active syncs.
    // Called on initial boot AND after HTMX swaps (dashboard content is
    // lazy-loaded, so `.course-card-sync` nodes don't exist yet at _boot).
    if (typeof deferGlobalJob !== 'function') return;
    document.querySelectorAll('.course-card-sync[data-course-id]').forEach(el => {
      const cid = el.dataset.courseId;
      const running = parseInt(el.dataset.syncRunning, 10) || 0;
      const queued = parseInt(el.dataset.syncQueued, 10) || 0;
      const total = parseInt(el.dataset.syncTotal, 10) || 0;
      const synced = parseInt(el.dataset.syncSynced, 10) || 0;
      if ((running + queued) > 0) {
        // Defer the global bar to the inline badge so the user sees only
        // ONE indicator (the inline card badge), not two showing the
        // same numeric text simultaneously.  `passive: true` signals
        // this is a page-load reconcile, not a user click, so a prior
        // dismissal is honoured.  The localIndicatorSelector tells
        // global-job-bar to suppress the bottom bar whenever this badge
        // is in the viewport.
        const _msg = (typeof window._courseSyncMsg === 'function')
          ? window._courseSyncMsg('', running, queued, total > 0 ? synced : null, total > 0 ? total : null)
          : t('Syncing data: %r running, %q queued').replace('%r', running).replace('%q', queued);
        deferGlobalJob(
          _msg,
          cid,
          { jobKind: 'course_sync', localIndicatorSelector: `.course-card-sync[data-course-id="${cid}"]`, passive: true }
        );
        if (typeof startCourseSyncPolling === 'function') {
          startCourseSyncPolling(cid);
        }
      }
    });

    // Second pass: any in-flight course-sync job that the global-job-bar
    // is already tracking (e.g. user clicked Sync All on the course page,
    // hit Back to dashboard before the first SSE tick - the server may
    // not yet show running>0 because BackgroundJob rows are still being
    // committed, so the template emitted NO inline .course-card-sync
    // element).  Inject the badge ourselves so the user sees a per-course
    // local indicator instead of only the global bar.
    if (window._globalJobs) {
      Object.keys(window._globalJobs).forEach((jobType) => {
        const job = window._globalJobs[jobType];
        if (!job) return;
        if (job.status === 'done' || job.status === 'error') return;
        if (job.meta && job.meta.jobKind && job.meta.jobKind !== 'course_sync') return;
        // Heuristic: course-sync ids are UUID or numeric, and there must
        // be a matching .course-card on the dashboard.
        if (!document.querySelector(`.course-card[data-course-id="${CSS.escape(jobType)}"]`)) return;
        _ensureCourseCardSyncBadge(jobType);
      });
    }
  }

  function _bootAutofill() {
    if (typeof setupGitLabAutofill !== 'function') return;
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
  }

  function _boot() {
    toggleImportCourseFields();
    const _impSel = document.getElementById('importTargetCourseId');
    if (_impSel) _impSel.dataset.changeAction = 'toggleImportCourseFields';
    _registerCourseCardSyncs();
    _wireDatePickers();
    _bootAutofill();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _boot);
  } else {
    _boot();
  }
  // Dashboard body is HTMX lazy-loaded - re-register dedup for course cards
  // after the content swap so the global bar defers to the inline badges.
  document.body.addEventListener('htmx:afterSettle', _registerCourseCardSyncs);
  document.body.addEventListener('htmx:afterSettle', _wireDatePickers);
  document.body.addEventListener('htmx:afterSettle', _bootAutofill);
