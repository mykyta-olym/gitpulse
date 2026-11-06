/**
 * Project detail page controller.
 */
  const GP = window.GP;
  GP.runPageCleanup();

  const { apiCall, showToast, flashToast, t, ClientPaginator, escapeHtml: _escapeHtml, withUiLock: _lock } = GP;
  const pageOwner = document.getElementById('gp-project-detail-config');
  const config = JSON.parse(pageOwner?.textContent || 'null');
  if (!config || !config.projectId) {
    return;
  }

  // Scoped variables for cleanable listeners and timers across files
  let _ciPollTimer = null;
  let onBeforeUnload = null;
  let onTabVisible = null;
  let onVisibilityChangeIntel = null;
  let onHealthChange = null;
  let onJobCompleteProject = null;
  let onDocumentClickScrollToMember = null;
  let onDocumentClickCloseIssueDetail = null;
  let onMrHistoryClick = null;
  let onBeforeSwap = null;

  const PROJECT_ID = String(config.projectId);
  const TEAM_ID = String(config.teamId || '');
  const COURSE_ID = String(config.courseId || '');
  const CHECK_CODES = Array.isArray(config.checkCodes) ? config.checkCodes.map((code) => String(code)) : [];
  const PROJECT_NAME = String(config.projectName || 'project');
  const CAN_EDIT = config.canEdit === true || config.canEdit === 'true';
  const MAY_SEE_ANALYSIS = config.llmEnabled === true
    && (config.isTeacher === true || config.isAdmin === true);
  const ANALYSIS_STARTED = config.analysisStarted === true || config.analysisStarted === 'true';
  const GITLAB_URL = String(config.gitlabUrl || '');
  const PROJECT_PATH = String(config.projectPath || '');

  let analysisPoller = null;
  let analysisFallbackTimerId = null;
  let analysisCompletionHandled = false;
  let analysisRevision = 0;
  let analysisGeneration = 0;
  let analysisReading = null;
  let _sseDelivering = false;  // true once SSE delivers its first message
  let _checksFallbackPollId = null;  // run-checks fallback poll interval (module-scoped for cleanup)
  let _mrPaginator = null;

  function scoringScope(extra) {
    return [
      COURSE_ID ? `course:${COURSE_ID}` : '',
      TEAM_ID ? `team:${TEAM_ID}` : '',
      extra || '',
    ].filter(Boolean).join(' ');
  }

  function getMembersTbody() {
    return document.querySelector('#projectMembersTable tbody');
  }

  function normalizeStudent(student) {
    return {
      id: String(student?.id || ''),
      name: String(student?.name || student?.gitlab_username || 'Unknown'),
      gitlab: String(student?.gitlab_username || ''),
      checks: student?.checks && typeof student.checks === 'object' ? student.checks : {},
      score: student?.score,
      excludedFromScoring: student?.excluded_from_scoring === true,
      memberCategory: String(student?.member_category || ''),
      memberBaseCategory: String(student?.member_base_category || ''),
    };
  }

  let _lastStudentsHash = '';
  function updateMembersTable(studentsRaw) {
    const students = Array.isArray(studentsRaw) ? studentsRaw.map(normalizeStudent) : [];

    // Nothing to render - leave the page as-is.
    if (students.length === 0) return;

    // Fast-path guard: if incoming student metrics have not changed, avoid DOM churn and pagination resync
    let currentHash = '';
    try {
      currentHash = JSON.stringify(studentsRaw);
    } catch (_) {}
    if (currentHash && currentHash === _lastStudentsHash) {
      return;
    }
    _lastStudentsHash = currentHash;

    const tbody = getMembersTbody();
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr[data-student-id]'));
    const rowById = new Map(rows.map((row) => [String(row.dataset.studentId || ''), row]));

    // Do NOT create new rows here - the server template uses a GitLab
    // API intersection to decide which members belong in this project.
    // Adding rows for every live-data student would re-add members that
    // the template intentionally excluded (e.g. students from other
    // projects in the same team).  Only update existing rows below.

    // Never remove server-rendered rows - the member filter bar
    // controls visibility for all categories (direct/inherited/
    // teacher/excluded).  Only the server template decides which
    // rows exist; the live-data endpoint only supplies fresh metrics.

    students.forEach((student) => {
      const row = rowById.get(student.id);
      if (!row) {
        return;
      }

      row.dataset.studentId = student.id;
      if (student.memberBaseCategory) {
        row.dataset.memberBaseCategory = student.memberBaseCategory;
      }
      if (student.memberCategory) {
        row.dataset.memberCategory = student.memberCategory;
      }
      row.classList.toggle('member-excluded', student.excludedFromScoring);
      if (student.excludedFromScoring) {
        row.setAttribute('data-member-excluded', '1');
      } else {
        row.removeAttribute('data-member-excluded');
      }

      const cells = row.querySelectorAll('td');
      if (cells.length === 0) {
        return;
      }

      const nameStrong = cells[0].querySelector('strong');
      if (nameStrong) {
        nameStrong.textContent = student.name;
      }

      const usernameLabel = cells[0].querySelector('span.muted.font-08');
      if (usernameLabel) {
        usernameLabel.textContent = `@${student.gitlab}`;
      }

      const showMetrics = student.score != null && !row.hasAttribute('data-member-teacher')
        && !row.hasAttribute('data-member-mentor');
      CHECK_CODES.forEach((code, index) => {
        const cell = cells[index + 1];
        if (!cell) {
          return;
        }
        if (!showMetrics) {
          cell.className = 'check-na';
          cell.removeAttribute('aria-label');
          cell.removeAttribute('data-tippy-content');
          cell.textContent = '-';
          return;
        }

        const raw = student.checks[code];
        const val = raw && typeof raw === 'object' ? raw.pass : raw;
        const expected = raw && typeof raw === 'object' ? raw.expected : true;
        const name = row.closest('table').tHead.rows[0].cells[index + 1].dataset.tippyContent;
        const label = expected === false ? t('Not yet required')
          : val === true ? t('Pass') : val === false ? t('Fail') : t('N/A');
        cell.dataset.tippyContent = name + ': ' + (expected === false ? t('not yet required') : label);
        cell.setAttribute('aria-label', label);
        if (expected === false) {
          cell.className = 'check-na';
          cell.textContent = '-';
        } else if (val === true) {
          cell.className = 'check-pass';
          cell.innerHTML = GP.iconSvg('check-circle', 'sm');
        } else if (val === false) {
          cell.className = 'check-fail';
          cell.innerHTML = GP.iconSvg('x-circle', 'sm');
        } else {
          cell.className = 'check-na';
          cell.textContent = '-';
        }
      });

      // Score column is cells[CHECK_CODES.length + 1] (immediately after all checks)
      const scoreCell = cells[CHECK_CODES.length + 1];
      if (scoreCell) {
        GP.updateScoreCell(scoreCell, showMetrics ? student.score : null, config.greenPct, config.yellowPct);
      }

    });

    // Re-sync pagination after row changes
    const membersPag = _tablePaginators['projectMembersBody'];
    if (membersPag) { membersPag.resync(); }

    // Re-apply member filters so the count badge stays in sync
    if (window.GP && window.GP.initMemberFilters) {
      window.GP.initMemberFilters();
    }
  }

  function updateBottlenecks(bottlenecksRaw, issuesHtml) {
    // Preferred path: swap the full pre-rendered "Issues to Address" partial.
    // This keeps the card structure, severity badges, affected-student lists
    // and scored-cohort count in sync with the live data on every refresh
    // (exclude / include student, demote teacher, run checks, etc.).
    if (typeof issuesHtml === 'string' && issuesHtml.length > 0) {
      const container = document.getElementById('issuesToAddressContainer');
      if (container) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(issuesHtml, 'text/html');
        const next = doc.getElementById('issuesToAddressContainer');
        if (next) {
          // Skip the swap (and the chart destroy/rebuild "blink") when the data
          // is byte-identical - e.g. the SSE reconnect after an alt-tab/tab-focus
          // re-pushes the same snapshot. Only rebuild when the data truly changed.
          const _cur = container.querySelector('#issuesToAddressData');
          const _next = next.querySelector('#issuesToAddressData');
          if (_cur && _next && _cur.textContent === _next.textContent &&
              container.getAttribute('data-scored-count') === next.getAttribute('data-scored-count')) {
            return;
          }
          container.replaceWith(next);
          // Re-run any enhancements on newly injected nodes.
          window.GP.initTippy(next);
          // Re-render the Issues chart against the freshly-injected JSON.
          if (typeof initIssuesChart === 'function') {
            // The IntersectionObserver re-arms on the new canvas (the previous
            // one was discarded with the replaced container). Pass animate:false
            // so the entrance animation plays only on the first page reveal,
            // never on every live-data refresh.
            initIssuesChart({ animate: false });
          }
          return;
        }
      }
    }

    // No fresh issues_html this poll (the server returns "" when it could not
    // determine the repo-empty state, e.g. GitLab unreachable / no token). LEAVE
    // the existing server-rendered card exactly as-is - never hide it. The old
    // legacy path used to `d-none` the card on empty, which made the empty-state
    // ("No repository data yet" / "No scored members yet") vanish a second after
    // load. The persistent server-rendered empty-state is the correct display.
  }

  function refreshProjectData() {
    /* Coalesced: SSE, the reconnect handler and the visibility handler can
       all ask for this within a few ms. Overlapping reads made the older
       answer paint last, settling the page one event behind. */
    return GP.coalesced('project-live-data', async () => {
    if (!pageOwner.isConnected) return false;
    try {
      const data = await apiCall(`/dashboard/projects/${PROJECT_ID}/live-data`, 'GET', null, {
        key: 'project-live-data',
        timeoutMs: 15000,
        maxRetries: 1,
      });
      if (!pageOwner.isConnected) return false;
      updateMembersTable(data?.students || []);
      updateBottlenecks(data?.bottlenecks || [], data?.issues_html);
    } catch (error) {
      /* Abandoned by abortInflight() as the user navigated away. The page
         this was going to paint is already gone; a failure toast here would
         land on the NEXT page. */
      if (!pageOwner.isConnected || error?.superseded) return;
      console.error('Failed to refresh project data:', error);
      showToast(t('Failed to refresh project data'), 'danger');
    }
    });
  }
