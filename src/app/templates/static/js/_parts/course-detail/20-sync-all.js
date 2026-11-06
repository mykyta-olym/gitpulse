  function _resetSyncButtons(syncBtn) {
    if (syncBtn) {
      setButtonLoading(syncBtn, false);
      return;
    }
    document.querySelectorAll('button[data-action="triggerSync"]').forEach(b => setButtonLoading(b, false));
  }

  async function triggerSyncAll(opts) {
    if (!CAN_EDIT) return;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: 'course:' + COURSE_ID })) return;
    // Token is known-bad: the server will refuse this. Give the reason plainly
    // instead of flashing a "Connecting..." bar that vanishes a second later.
    if (_tokenOk === false || document.getElementById('gitlabTokenBanner')) {
      const msg = t('The GitLab API token is invalid or expired (401). Sync, import and other GitLab actions are blocked until the token is updated.');
      if (typeof connectGlobalJob === 'function') {
        connectGlobalJob(COURSE_ID, msg, { jobKind: 'course_sync', courseName: COURSE_NAME, courseId: String(COURSE_ID || '') });
      }
      if (typeof failGlobalJob === 'function') failGlobalJob(COURSE_ID, msg);
      else showToast(msg, 'danger', 8000);
      // Apply anti-spam cooldown so the button doesn't stay permanently
      // disabled but also can't be spam-clicked on a known-bad token.
      const _syncAllBtn = document.querySelector('[data-action="triggerSyncAll"]');
      if (_syncAllBtn) {
        GP.applyCooldown(_syncAllBtn);
      }
      return;
    }
    const force = !!(opts && opts.force);
    // Guard: no teams to sync
    if (_renderedTeamCount === 0) {
      showToast(t('No groups to sync'), 'warning');
      return;
    }
    // Dedup guard: prevent re-trigger while sync-all is already running
    if (typeof isGlobalJobRunning === 'function' && isGlobalJobRunning(COURSE_ID) && typeof confirmProcessRestart === 'function' && !await confirmProcessRestart(COURSE_ID, t('Sync All'))) return;
    const syncBtn = document.querySelector('[data-action="triggerSyncAll"]');
    try {
      await _lock('syncAll:' + COURSE_ID, async () => {
        if (syncBtn) setButtonLoading(syncBtn, true);

        // Instant "Connecting..." bar before the POST. The GitLab pre-flight
        // can take several seconds; without this the bar surfaced only once
        // the POST returned, so the user saw it jump straight to
        // "Syncing: 0/N groups done" with no connecting feedback.
        // connectGlobalJob() renders an INDETERMINATE spinner (no progress
        // %, phase='connecting'), which sidesteps the two bugs the old
        // optimistic pre-show caused:
        //   1) Flicker - there is no placeholder progress number to flip.
        //   2) Stale `done` race - the connecting phase carries no progress,
        //      so a leftover localStorage `done` entry can't bleed through.
        // showGlobalJob() below promotes it to the real running message;
        // the enqueued===0 / error paths call hideGlobalJob() to cancel it.
        if (typeof connectGlobalJob === 'function') {
          connectGlobalJob(
            COURSE_ID,
            (COURSE_NAME ? COURSE_NAME + ': ' : '')
              + t('Connecting to GitLab...'),
            { jobKind: 'course_sync', courseName: COURSE_NAME, courseId: String(COURSE_ID || '') },
          );
        }

        let syncEnqueued = false;
        try {
          // NOTE: no optimistic "Sync started..." toast here. It fired BEFORE the
          // POST resolved, so a refused sync (e.g. 401 invalid token) showed a
          // green "Sync started" AND a red "Failed to start sync" at the same
          // time - the exact contradictory double-state the user reported. The
          // "Connecting to GitLab..." global-job bar above already signals that
          // the action began, and it resolves cleanly to either real progress or
          // the error path - one state, not two.
          const url = `/api/v1/courses/${COURSE_ID}/sync-all` + (force ? '?force=true' : '');
          const result = await apiCall(url, 'POST');
          if (result.enqueued > 0) {
            syncEnqueued = true;
            // No second toast here - the synchronous "Sync started..." toast
            // above already confirmed the action; adding another one would
            // just be noise.
            // Register in global bar so sync persists across page navigation
            _syncWasActive = true;
            if (typeof showGlobalJob === 'function') {
              // Use the SAME message format as the SSE handler in
              // global-job-bar.js so the user does not see one text
              // ("Syncing data: 8 groups queued...") flip to a different
              // one ("Syncing: 0/8 groups done (0 active, 8 queued)") a
              // second later.  Treat the freshly-enqueued count as queued
              // until the first SSE tick reports running/queued breakdown.
              const _cn = COURSE_NAME ? COURSE_NAME + ': ' : '';
              const _initMsg = _cn
                + t('Syncing:')
                + ` 0/${result.enqueued} `
                + t('groups done')
                + ` (0 ` + t('active') + `, ${result.enqueued} ` + t('queued') + ')';
              showGlobalJob(_initMsg, COURSE_ID, { jobKind: 'course_sync', courseName: COURSE_NAME, courseId: String(COURSE_ID || '') });
              // Set initial _syncTotal from the enqueued count
              if (typeof _globalJobs !== 'undefined' && _globalJobs[COURSE_ID]) {
                if (!_globalJobs[COURSE_ID].meta) _globalJobs[COURSE_ID].meta = {};
                _globalJobs[COURSE_ID].meta._syncTotal = result.enqueued;
              }
              // Stop global bar's SSE/polling - this page handles sync updates inline
              _stopGlobalBarTracking();
            }
            // Optimistically flip every visible team row's Status pill to
            // QUEUED so the user sees per-team feedback immediately -
            // without this they'd stare at stale RED/GREEN badges until
            // the next /sync-stream tick (typically 2-5 s) overwrites
            // them.  updateTeamRow() will repaint each row to SYNCING
            // when the worker actually starts processing it.
            try {
              document.querySelectorAll('table tbody tr').forEach((row) => {
                const link = row.querySelector('a[href^="/dashboard/teams/"]');
                if (!link) return;
                const statusCell = row.cells && row.cells[4];
                if (!statusCell) return;
                const curBadge = statusCell.querySelector('.badge');
                // Don't clobber an already-running indicator from a
                // previous overlapping click.
                if (curBadge && curBadge.textContent === 'SYNCING') return;
                statusCell.innerHTML = GP.badgeHtml('QUEUED', 'info');
                if (row.cells && row.cells[5]) {
                  // Preserve col-hide-md so the cell stays hidden on
                  // tablets/phones where the column is collapsed.
                  row.cells[5].className = 'muted col-hide-md';
                  row.cells[5].textContent = t('Sync queued...');
                }
              });
            } catch (_) { /* defensive - never block the sync flow */ }
          } else {
            // No work enqueued - roll back the pre-defer so the bar
            // doesn't linger with a stale "Starting sync..." message.
            // If everything is fresh, offer the user a force re-sync option.
            if (!force && (result.already_fresh || 0) > 0 && result.enqueued === 0 && result.skipped === 0) {
              const ask = t('All groups are already up-to-date. Force re-sync anyway?');
              if (await GP.confirmDialog({ message: ask, confirmText: t('Confirm'), variant: 'warning' })) {
                if (syncBtn) setButtonLoading(syncBtn, false);
                return triggerSyncAll({ force: true });
              }
              const msg = result.message || t('All groups already up to date');
              if (typeof completeGlobalJob === 'function') completeGlobalJob(COURSE_ID, msg, 'done');
              else showToast(msg, 'info');
            } else {
              const msg = result.message || t('All groups already up to date');
              if (typeof completeGlobalJob === 'function') completeGlobalJob(COURSE_ID, msg, 'done');
              else showToast(msg, 'info');
            }
          }
          // Reconnect SSE stream so updates flow immediately
          setTimeout(() => connectSyncStream(), 1500);
        } catch (err) {
          const msg = t('Failed to start sync') + ': ' + (err?.message || err);
          if (typeof failGlobalJob === 'function') failGlobalJob(COURSE_ID, msg);
          else {
            if (typeof hideGlobalJob === 'function') hideGlobalJob(COURSE_ID);
            showToast(msg, 'danger');
          }
          // Apply anti-spam cooldown on error to prevent rapid re-clicking
          // on a failing endpoint (e.g. invalid GitLab token → repeated 401s).
          if (syncBtn) {
            GP.applyCooldown(syncBtn);
          }
        } finally {
          // Only re-enable button if no sync was enqueued (error or 0 teams)
          if (!syncEnqueued && syncBtn) setButtonLoading(syncBtn, false);
        }
      }); // end withUiLock
    } catch (lockErr) {
      if (lockErr.code !== 'LOCKED') throw lockErr;
    }
  }
  
