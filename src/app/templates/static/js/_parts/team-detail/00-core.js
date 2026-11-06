  const GP = window.GP;
  const { t, showToast, flashToast, withUiLock: _lock } = GP;

  GP.runPageCleanup();
const _pageConfig = JSON.parse(document.getElementById('gp-team-detail-config')?.textContent || '{}');
const TEAM_ID = String(_pageConfig.teamId || '');
  const TEAM_NAME = String(_pageConfig.teamName || 'group');
  const COURSE_ID = String(_pageConfig.courseId || '');
  const CAN_EDIT = !!_pageConfig.canEdit;
  const IS_ADMIN = !!_pageConfig.isAdmin;
  // Observe optional analysis only when enabled and accessible to this role.
  const MAY_SEE_ANALYSIS = !!_pageConfig.llmEnabled && (!!_pageConfig.isTeacher || !!_pageConfig.isAdmin);
  const GREEN_PCT = _pageConfig.greenPct;
  const YELLOW_PCT = _pageConfig.yellowPct;
if (!TEAM_ID) { console.warn('[team-detail] No teamId found'); return; }
  let syncStreamCtrl = null;
  
  // -- Live data refresh (replaces location.reload) --
  function refreshTeamData() {
    /* Coalesced: SSE, the reconnect handler and the visibility handler can
       all ask for this within a few ms. Overlapping reads made the older
       answer paint last, settling the page one event behind. */
    return GP.coalesced('team-live-data', async () => {
    try {
      const data = await window.GP.apiCall(`/dashboard/teams/${TEAM_ID}/live-data`, 'GET', null, { key: 'team-live-data', maxRetries: 0 });
      
      // Update member rows (score, traffic light, checks, MRs, issues, pipelines)
      if (Array.isArray(data.students)) {
        document.querySelectorAll('tr[data-student-id]').forEach(row => {
          const student = data.students.find(s => String(s.id) === row.dataset.studentId);
          if (!student) return;
          if (student.member_base_category) row.dataset.memberBaseCategory = student.member_base_category;
          if (student.member_category) row.dataset.memberCategory = student.member_category;
          row.classList.toggle('member-excluded', student.excluded_from_scoring === true);
          if (student.excluded_from_scoring === true) {
            row.setAttribute('data-member-excluded', '1');
          } else {
            row.removeAttribute('data-member-excluded');
          }
          // Teachers/mentors with no activity keep their dashes
          const isTeacherOrMentor = row.hasAttribute('data-member-teacher') || row.hasAttribute('data-member-mentor');
          const hasActivity = student.mrs_created || student.issues_assigned || student.pipeline_total || student.checks_passed;
          const showMetrics = student.score != null && (!isTeacherOrMentor || hasActivity);
          const cells = row.querySelectorAll('td');
          if (cells.length < 6) return;
          // cells[0] = name, [1] = score, [2] = checks, [3] = MRs, [4] = issues, [5] = pipelines
          GP.updateScoreCell(cells[1], showMetrics ? student.score : null, GREEN_PCT, YELLOW_PCT);
          const _setCell = function (cell, value) {
            cell.classList.toggle('text-muted', !showMetrics);
            if (cell.textContent !== value) {
              cell.textContent = value;
            }
          };
          _setCell(cells[2], showMetrics ? student.checks_passed + '/' + student.checks_total : '-');
          _setCell(cells[3], showMetrics ? String(student.mrs_created) : '-');
          _setCell(cells[4], showMetrics ? String(student.issues_assigned) : '-');

          const pipeCell = cells[5];
          let pipeHtml;
          if (!showMetrics) {
            pipeHtml = '-';
          } else if (student.pipeline_total > 0) {
            const success = student.pipeline_success || 0;
            const total = student.pipeline_total || 0;
            if (success === total) {
              pipeHtml = `<span class="text-success" data-tippy-content="${t('All pipelines completed successfully')}">${success}/${total}</span>`;
            } else {
              pipeHtml = `<span class="text-danger font-semibold" data-tippy-content="${t('Some pipelines failed')}">${success}/${total}</span>`;
            }
          } else {
            pipeHtml = '<span class="text-muted">-</span>';
          }
          if (pipeCell.innerHTML !== pipeHtml) {
            pipeCell.classList.toggle('text-muted', !showMetrics);
            pipeCell.innerHTML = pipeHtml;
          }
        });
        GP.initTippy();
      }

    } catch (e) {
      /* Abandoned by abortInflight() as the user navigated away. The page
         this was going to paint is already gone; a failure toast here would
         land on the NEXT page. */
      if (e && e.superseded) return;
      console.error('Failed to refresh team data:', e);
      showToast(t('Failed to refresh group data'), 'danger');
    }
    });
  }
  
  async function linkProject(e) {
    if (!CAN_EDIT) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + TEAM_ID })) {
      e.preventDefault();
      return;
    }
    return submitModalForm(e, {
      url: `/api/v1/projects/${TEAM_ID}/projects`,
      modalId: 'linkProjectModal',
      btnSelector: '#linkProjectBtn',
      getData: (f) => ({
        gitlab_project_id: parseInt(f.gitlab_project_id.value),
        gitlab_project_path: f.gitlab_project_path.value,
        gitlab_project_name: f.gitlab_project_name.value || f.gitlab_project_path.value
      }),
      successMsg: t('Project linked!'),
    });
  }

  async function deleteTeam() {
    if (!IS_ADMIN) { showToast(t('Only administrators can delete groups'), 'warning'); return; }
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'run_checks'], { scope: 'course:' + COURSE_ID + ' team:' + TEAM_ID })) return;
    const deleteBtn = document.querySelector('[data-action="deleteTeam"]');
    confirmDangerousAction('this group', async () => {
      try {
        await _lock(`deleteTeam:${TEAM_ID}`, async () => {
          if (deleteBtn) setButtonLoading(deleteBtn, true);
          await apiCall(`/api/v1/teams/${TEAM_ID}`, 'DELETE');
          flashToast(t('Group deleted!'), 'success');
          if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
          // Soft-delete: stay on this page and reload in place so the
          // archived banner + Restore action appear, instead of ejecting
          // the user back to the course page ("kicked out").
          setTimeout(() => { reloadKeepScroll(); }, 500);
        });
      } catch (err) {
        if (err.code !== 'LOCKED') showToast(err.message, 'danger');
      } finally {
        if (deleteBtn) setButtonLoading(deleteBtn, false);
      }
    }, { confirmText: t('This group exists in GitLab. It will be re-created on next sync if the GitLab subgroup still exists. Continue?') });
  }
  
  // -- Per-row SYNCING badge on the Projects table --
