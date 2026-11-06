
  // Multiple triggers (SSE connected, SSE update, visibilitychange,
  // gp:job-complete) can fire within a few ms of each other. Coalescing is
  // what keeps that from sending two concurrent /dashboard/stats and two
  // concurrent /dashboard/attention-items on every sync completion.

  // Live-update stat cards from role-based /dashboard/stats response
  /* Coalesced by GP.coalesce: SSE can deliver several updates in a second, and
     these three refreshers used to carry a hand-rolled in-flight/pending pair
     each - three copies of one mechanic in one file. */
  function refreshDashboardStats() {
    return GP.coalesced('dashboard-stats', async () => {
      try {
        /* All three refreshers ask for the period on screen (GP.withPagePeriod):
           the server scopes them with the same function as the page, and a
           refresh for "every term" beside a grid of one used to change the
           cards under the reader on the first SSE push or tab return. */
        const data = await apiCall(GP.withPagePeriod('/dashboard/stats'), 'GET', null, { key: 'dashboard-stats' });
      const courseHealth = data._course_health;
      const states = data._states;
      delete data._course_health;
      delete data._states;
      // Retone before the numbers change: the card carries the state, the
      // value element only carries the text.
      if (states) {
        for (const [id, state] of Object.entries(states)) {
          const card = document.getElementById(id)?.closest('.gl-home-stat');
          if (!card) continue;
          if (state) card.dataset.state = state;
          else delete card.dataset.state;
        }
      }
      for (const [id, val] of Object.entries(data)) {
        const el = document.getElementById(id);
        if (el && el.textContent !== String(val)) {
          el.textContent = val;
        }
      }
      // Update course card health badges
      if (courseHealth) {
        document.querySelectorAll('.course-card[data-course-id]').forEach(card => {
          const cid = card.dataset.courseId;
          const ch = courseHealth[cid];
          const redCount = ch?.red_teams || 0;
          const badge = card.querySelector('.course-card-at-risk');
          if (redCount > 0) {
            /* The server's badge (cards.html), redrawn with the new count. */
            const html = GP.badgeHtml(redCount + ' ' + t('at-risk'), 'danger',
              { icon: 'alert-triangle', class: 'course-card-at-risk' });
            if (badge) {
              if (badge.textContent !== redCount + ' ' + t('at-risk')) badge.outerHTML = html;
            } else {
              card.querySelector('.course-card-indicators')?.insertAdjacentHTML('beforeend', html);
            }
          } else if (badge) {
            badge.remove();
          }
        });
      }
    } catch (e) { console.debug('Stats refresh:', e); }
    });
  }

  /* A refresh that brings back the markup already on screen is a no-op. The
     comparison is made on a KEY, not the raw strings: after paint,
     localize-time rewrites every <time> (its text and tooltip) and Alpine
     writes inline display styles, so the DOM never equalled the server's
     string and each refresh - every tab return, every SSE tick - rebuilt the
     list and the feed for nothing, which read as the page replaying itself. */
  function _liveMarkupKey(html) {
    /* Through the browser's own serializer first: the server writes
       `<path .../>` where the DOM serializes `<path ...></path>`, so the raw
       strings never match even for identical markup. */
    const tpl = document.createElement('template');
    tpl.innerHTML = String(html || '');
    return tpl.innerHTML
      .replace(/<time\b[^>]*>[^<]*<\/time>/g, '<time>')
      .replace(/\s(?:style|data-localized|data-tippy-content)="[^"]*"/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function refreshAttentionItems() {
    return GP.coalesced('dashboard-attention', async () => {
    const container = document.getElementById('attention-items-body');
    if (!container) return;
      try {
        const resp = await fetch(GP.withPagePeriod('/dashboard/attention-items'), { credentials: 'same-origin' });
        if (resp.ok) {
          const html = (await resp.text()).trim();
          if (_liveMarkupKey(container.innerHTML) === _liveMarkupKey(html)) return;
          container.innerHTML = html;
        }
      } catch (e) { console.debug('Attention items refresh:', e); }
    });
  }

  // Live-refresh the "Follow the latest updates" feed so lifecycle events -
  // group/project deletion and restoration, syncs, pipeline runs - appear
  // without a full page reload.  Replaces the Alpine x-data wrapper and
  // re-inits Alpine on the new node so the show-more toggle keeps working.
  function refreshActivityFeed() {
    return GP.coalesced('dashboard-activity', async () => {
    const card = document.getElementById('activity');
    const current = card && card.querySelector('.gl-home-card-content');
    if (!current) return;
      try {
        const resp = await fetch(GP.withPagePeriod('/dashboard/activity'), { credentials: 'same-origin' });
        if (!resp.ok) return;
        const html = (await resp.text()).trim();
        if (!html || _liveMarkupKey(current.outerHTML) === _liveMarkupKey(html)) return;
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        const next = tmp.firstElementChild;
        if (!next) return;
        // Guard: NEVER replace a populated feed with an empty-state render.
        // A transient builder hiccup (DB blip) or a brief quiet window can make
        // /dashboard/activity return the "no activity yet" placeholder; swapping
        // it in would wipe every visible record ("entries lost completely").
        const _nextHasItems = next.querySelector('.gl-activity-item') !== null;
        const _currentHasItems = current.querySelector('.gl-activity-item') !== null;
        if (!_nextHasItems && _currentHasItems) return;
        // Preserve the user's expand state: a background refresh must NOT
        // collapse a "Show all" feed back to 5 (that also reads as records
        // vanishing). Capture the old Alpine limit/total, then re-apply after
        // the fresh node is initialised.
        let _prevLimit = 5;
        let _prevTotal = 5;
        try {
          const _d = window.Alpine && typeof window.Alpine.$data === 'function'
            ? window.Alpine.$data(current) : null;
          if (_d) { _prevLimit = _d.limit || 5; _prevTotal = _d.total || 5; }
        } catch (_) { /* Alpine not ready on this node */ }
        current.replaceWith(next);
        // Re-init Alpine on the freshly injected x-data node so the
        // show-more / show-less toggle is wired up again.
        if (window.Alpine && typeof window.Alpine.initTree === 'function') {
          window.Alpine.initTree(next);
        }
        try {
          const _nd = window.Alpine && typeof window.Alpine.$data === 'function'
            ? window.Alpine.$data(next) : null;
          if (_nd && typeof _nd.total === 'number' && _prevLimit > 5) {
            // Was fully expanded -> stay fully expanded even if new items arrived.
            _nd.limit = (_prevLimit >= _prevTotal) ? _nd.total : Math.min(_prevLimit, _nd.total);
          }
        } catch (_) { /* noop */ }
      } catch (e) { console.debug('Activity feed refresh:', e); }
    });
  }

  function refreshDashboardLive(options) {
    const includeSidebar = options && options.includeSidebar === true;
    const tasks = [
      refreshDashboardStats(),
      refreshAttentionItems(),
      refreshActivityFeed(),
    ];
    if (includeSidebar) {
      if (typeof window.GP?._sidebar?.pollBadges === 'function') {
        tasks.push(window.GP._sidebar.pollBadges());
      } else if (typeof window.GP?.refreshSidebarBadges === 'function') {
        tasks.push(window.GP.refreshSidebarBadges());
      }
    }
    return Promise.allSettled(tasks);
  }

  // Inject an inline .course-card-sync badge into the matching course card
  // when a sync starts AFTER the dashboard was rendered (the server-side
  // template only emits the badge if course_sync_info.running/queued > 0
  // at render time).  Without this, syncs started from another page or
  // tab show ONLY the global bar - the per-course inline indicator stays
  // missing until the user navigates and the page re-renders.  Returns
  // the badge element (existing or freshly injected), or null if no
  // course card on this dashboard matches the jobType.
  function _ensureCourseCardSyncBadge(jobType) {
    let badge = document.querySelector(`.course-card-sync[data-course-id="${CSS.escape(jobType)}"]`);
    if (badge) return badge;
    const card = document.querySelector(`.course-card[data-course-id="${CSS.escape(jobType)}"]`);
    if (!card) return null;
    const header = card.querySelector('.course-card-header');
    if (!header) return null;
    const template = document.createElement('template');
    template.innerHTML = GP.badgeHtml('', 'info', { class: 'course-card-sync' });
    badge = template.content.firstElementChild;
    badge.setAttribute('data-course-id', jobType);
    badge.setAttribute('data-sync-running', '1');
    badge.setAttribute('data-sync-queued', '0');
    badge.setAttribute('data-sync-total', '0');
    badge.setAttribute('data-sync-synced', '0');
    badge.setAttribute('data-created-at', String(Date.now()));
    /* Exactly what components/cards.html renders for this badge: the shared
       spinner and the text. The hand-drawn ring that stood between them was
       left behind when the shared spinner was added in front of it, so a
       JS-injected badge carried TWO spinners and an orphan </span>, while a
       server-rendered one carried the correct single mark. */
    badge.innerHTML = GP.renderSpinnerHtml('sm')
      + '<span class="course-sync-text">' + GP.escapeHtml(t('Syncing:') + ' 1 ' + t('running') + ', 0 ' + t('queued')) + '</span>';
    // Insert after the top row (code + semester), before the title - same
    // position the server-side template uses.
    const topRow = header.querySelector('.course-card-top-row');
    if (topRow && topRow.nextSibling) {
      header.insertBefore(badge, topRow.nextSibling);
    } else {
      header.appendChild(badge);
    }
    // Inline badge exists now - register it as a localIndicatorSelector
    // so the bottom global bar defers to it (no duplicated progress).
    if (typeof deferGlobalJob === 'function') {
      deferGlobalJob(
        badge.querySelector('.course-sync-text').textContent,
        jobType,
        { jobKind: 'course_sync', localIndicatorSelector: `.course-card-sync[data-course-id="${jobType}"]`, passive: true }
      );
    }
    return badge;
  }

  let onJobUpdateLive = null;
  let onJobCompleteLive = null;
  let onVisibilityChangeLive = null;

  // Listen for global-job-bar events to update inline course card badges
  onJobUpdateLive = function(e) {
    const { jobType, message } = e.detail;
    // Never let a late/straggling update resurrect or re-label a badge whose
    // job already finished: the global bar may emit a trailing `update` right
    // after `complete`, which would otherwise flip a "Sync completed!" pill
    // back to "Finishing..." and leave it stranded on the card.
    const _job = window._globalJobs?.[jobType];
    if (_job && (_job.status === 'done' || _job.status === 'error')) return;
    const _existing = document.querySelector(`.course-card-sync[data-course-id="${CSS.escape(jobType)}"]`);
    if (_existing && _existing.classList.contains('sync-done')) return;
    const badge = _ensureCourseCardSyncBadge(jobType);
    if (badge) {
      const textEl = badge.querySelector('.course-sync-text');
      if (textEl) {
        // Strip redundant course-name prefix - already shown on the card
        let cardMsg = message;
        const cn = window._globalJobs?.[jobType]?.meta?.courseName;
        if (cn && cardMsg.startsWith(cn + ': ')) {
          cardMsg = cardMsg.slice(cn.length + 2);
        }
        textEl.textContent = cardMsg;
      }
    }
  };
  window.addEventListener('gp:job-update', onJobUpdateLive);

  // Defensive sweep: a course-card sync badge must never outlive its job.
  // The exact-match `gp:job-complete` handler clears the badge for the
  // completing course, but a badge can still get stranded on a stale
  // "Finishing.../Syncing..." pill (e.g. an SSE/poll race re-spawns then
  // finalizes the job, or a completion fires before the badge text caught
  // up). Whenever the underlying global job is already terminal, drop the
  // orphaned badge so the card state always matches the global bar.
  // Grace window distinguishing a *just-created* badge whose global job has
  // not registered yet (creation race - keep it) from a *stranded* one whose
  // job was cleaned without a terminal event (remove it).
  const BADGE_STRANDED_GRACE_MS = 12000;

  function _reconcileCourseCardBadges() {
    const jobs = window._globalJobs || {};
    const deferred = window._deferredJobs || new Set();
    const now = Date.now();
    document.querySelectorAll('.course-card-sync[data-course-id]').forEach((badge) => {
      // Its own post-complete display timer / data-remove-at sweep owns this.
      if (badge.classList.contains('sync-done')) return;
      // Stamp first-seen time so we can age out stranded badges below.
      if (!badge.dataset.createdAt) badge.dataset.createdAt = String(now);
      const courseId = badge.dataset.courseId;
      const job = jobs[courseId];
      if (job) {
        if (job.status === 'done' || job.status === 'error') {
          badge.remove();
        }
      } else {
        // No backing global job. A badge registers itself as a deferred local
        // indicator on creation, so we normally keep it while deferred. But
        // the /sync/active reconcile can drop a completed job from _globalJobs
        // WITHOUT firing gp:job-complete, leaving the defer entry - and the
        // "Syncing..." pill - stranded forever. Past the creation-race grace
        // window, treat a jobless badge as stranded and clear both it and the
        // stale defer entry so the card always matches the global bar.
        const age = now - Number(badge.dataset.createdAt || now);
        if (!deferred.has(courseId)) {
          badge.remove();
        } else if (age > BADGE_STRANDED_GRACE_MS) {
          deferred.delete(courseId);
          badge.remove();
        }
      }
    });
  }

  let _pendingRefresh = false;
  onJobCompleteLive = function(e) {
    const { jobType, status } = e.detail;
    const badge = document.querySelector(`.course-card-sync[data-course-id="${CSS.escape(jobType)}"]`);
    if (badge) {
      if (status === 'done') {
        badge.classList.add('sync-done');
        badge.classList.replace('badge-info', 'badge-success');
        badge.querySelector('.gp-spinner')?.remove();
        const textEl = badge.querySelector('.course-sync-text');
        if (textEl) textEl.textContent = t('Sync completed!');
        // Wall-clock deadline so the badge does not linger forever when the
        // tab is backgrounded (Chromium throttles setTimeout to ~1/min in
        // hidden tabs - see visibilitychange handler at the bottom of this
        // file which sweeps any past-deadline badges on tab focus).
        badge.dataset.removeAt = String(Date.now() + 4000);
        setTimeout(() => badge.remove(), 4000);
      } else if (status === 'error') {
        badge.remove();
      }
    }
    // Any completion is a good moment to clear badges stranded by other
    // courses' terminal jobs.
    _reconcileCourseCardBadges();
    if (status !== 'done' && status !== 'error') return;
    if (document.visibilityState !== 'visible') { _pendingRefresh = true; return; }
    // Fix H: when the dashboard SSE is alive it will emit an `update` event
    // within milliseconds of the job completing (same Redis pub/sub push that
    // triggered the job-complete toast).  The `update` handler already calls
    // refreshDashboardStats + refreshAttentionItems AND dispatches
    // `gp:data-changed`.  We listen for that once with a 3 s safety-net
    // fallback so we don't duplicate the refresh in the common (SSE alive) path.
    if (_dashSSE?.active) {
      const _jobRefreshTimer = setTimeout(() => {
        // SSE update didn't arrive within 3 s - refresh now as a fallback.
        refreshDashboardLive({ includeSidebar: true });
      }, 3000);
      window.addEventListener('gp:data-changed', function _onDataChanged() {
        // SSE already handled it - cancel the fallback.
        clearTimeout(_jobRefreshTimer);
        window.removeEventListener('gp:data-changed', _onDataChanged);
      }, { once: true });
    } else {
      // No SSE - fall back to the original 800 ms debounce.
      setTimeout(() => {
        refreshDashboardLive();
      }, 800);
    }
  };
  window.addEventListener('gp:job-complete', onJobCompleteLive);

  onVisibilityChangeLive = function() {
    if (document.visibilityState !== 'visible') return;
    if (_pendingRefresh) {
      _pendingRefresh = false;
      refreshDashboardLive({ includeSidebar: Boolean(_dashSSE?.active) });
    }
    // Sweep any course-card sync badges whose removal deadline passed while
    // the tab was hidden (setTimeout is throttled to ~1/min in background tabs).
    const now = Date.now();
    document.querySelectorAll('.course-card-sync[data-remove-at]').forEach((badge) => {
      const due = Number(badge.dataset.removeAt || 0);
      if (due && now >= due) badge.remove();
    });
    // Also clear any badge stranded on a stale running/finishing pill while
    // its job already finished (e.g. completion fired while tab was hidden).
    _reconcileCourseCardBadges();
  };
  document.addEventListener('visibilitychange', onVisibilityChangeLive);

  /* ==========================================
   *  Import Course from JSON Config Modal
   *  (uses shared GP.ConfigImport module)
   * ========================================== */
  const _importHandle = GP.ConfigImport.init({
    modalId: 'importConfigCourseModal',
    previewId: 'importConfigPreview',
    summaryId: 'importConfigSummary',
    sectionsId: 'importConfigSections',
    applyBtnId: 'btnImportConfigApply',
    pasteInputId: 'import_config_paste_input',
    disabledFeatures: _pageConfig?.disabledFeatures || {},
    requireCourseCode: true,
    requireAcademicYear: true,
    onApply: async function (config, btn) {
      const cm = config.course || config.source_course || {};
      const lines = [];
      ['course', 'settings', 'builtin_checks', 'custom_checks', 'weekly_deadlines'].forEach(function (k) {
        if (config[k] == null) return;
        lines.push(k);
      });

      confirmDangerousAction(GP.t('course import'), async () => {
        if (GP.guardProcessAction && !GP.guardProcessAction(['import'])) return;
        try {
          await _lock('importConfig', async () => {
            setButtonLoading(btn, true, GP.t('Importing...'));
            const result = await apiCall('/dashboard/courses/import-config', 'POST', config);
            const appliedCount = (result.applied || []).length;
            const errCount = (result.errors || []).length;
            const actionLabel = result.created ? GP.t('Course created') : GP.t('Course updated');

            if (errCount === 0) {
              flashToast(actionLabel + ' - ' + appliedCount + ' ' + GP.t('sections applied'), 'success');
            } else {
              let errMsg = actionLabel + ' - ' + appliedCount + ' ' + GP.t('sections applied') + ', ' + errCount + ' ' + GP.t('warnings') + ':\n';
              (result.errors || []).slice(0, 5).forEach(function (e) { errMsg += '* ' + e + '\n'; });
              flashToast(errMsg, 'warning');
            }

            GP.clearDirtyReason('dashboard_import_config');
            setButtonLoading(btn, true, errCount === 0 ? GP.t('Done!') : GP.t('Done with warnings'));
            try { sessionStorage.setItem('importJustCompleted', '1'); } catch (_) {}
            _importHandle.reset();
            forceCloseModal('importConfigCourseModal');

            // Trigger user enrichment global progress bar if backend started it
            if (result.enrich_started && typeof showGlobalJob === 'function') {
              let enrichMsg = GP.t('Enriching user profiles from GitLab...');
              if (result.enrich_total) enrichMsg += ' (' + result.enrich_total + ')';
              showGlobalJob(enrichMsg, 'enrichment', { cancelUrl: '/dashboard/admin/users/enrich-gitlab/cancel' });
              showToast(enrichMsg, 'info');
            }

            if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
            if (result.course_id) {
              window.location.href = '/dashboard/courses/' + result.course_id;
            } else {
              reloadKeepScroll();
            }
          });
        } catch (err) {
          if (err.code !== 'LOCKED') showToast(err.message || GP.t('Import failed'), 'danger');
        } finally {
          setButtonLoading(btn, false);
        }
      }, {
        confirmText: GP.t('This will create or update course') + ' "' + (cm.code || '') + '" (' + GP.periodLabel(cm.academic_year || '', cm.semester || 'winter') + ')\n\n' + GP.t('Sections to apply') + ':\n* ' + lines.join('\n* '),
        singleConfirm: true
      });
    }
  });

  // -- Export action handlers for data-action dispatch and Alpine.js --
  window.createCourse = createCourse;
  window.importGitlabCourse = importGitlabCourse;
  window.toggleImportCourseFields = toggleImportCourseFields;
  window.openAddTeamModal = openAddTeamModal;
  window.addTeam = addTeam;
  window.openCourseMenu = openCourseMenu;
  window.openEditCourseModal = openEditCourseModal;
  window.updateCourse = updateCourse;
  window.goToSettings = goToSettings;
  window.transferCourse = transferCourse;
  window.archiveCourse = archiveCourse;
  window.activateCourse = activateCourse;
  window.deleteCourse = deleteCourse;

  /* -- Modal Dirty-State Guards -- */
  if (typeof enableFormDirtyGuard === 'function') {
    enableFormDirtyGuard('createCourseModal');
    enableFormDirtyGuard('addTeamModal');
    enableFormDirtyGuard('editCourseModal');
  }
  if (typeof GP !== 'undefined' && GP.initModalSaveGuard) {
    GP.initModalSaveGuard('editCourseModal', '#editCourseBtn');
  }

  /* Page-level import config guard - handled by shared GP.ConfigImport module */
