  const GP = window.GP || {};
  const { t, escapeHtml: _escHtml, showToast, flashToast, withUiLock: _lock } = GP;

  // Cleanup prior page context if it exists to avoid leak/races
  GP.runPageCleanup();

  const _pageConfig = JSON.parse(document.getElementById('gp-course-detail-config')?.textContent || '{}');
const COURSE_ID = String(_pageConfig.courseId || '');
const COURSE_NAME = String(_pageConfig.courseName || '');
const CAN_EDIT = _pageConfig.canEdit === true;
if (!COURSE_ID) { console.warn('[course-detail] No courseId found'); return; }

  /** Toggle the Sync All button between loading (syncing) and idle. */
  function _setSyncAllBtn(syncing) {
    const btn = document.querySelector('[data-action="triggerSyncAll"]');
    if (!btn) return;
    if (typeof setButtonLoading === 'function') setButtonLoading(btn, syncing);
  }

  /** Stop global bar's SSE/polling for this course (this page owns sync tracking). */
  function _stopGlobalBarTracking() {
    if (typeof _globalJobs === 'undefined' || !_globalJobs[COURSE_ID]) return;
    const job = _globalJobs[COURSE_ID];
    if (job.poller) {
      if (typeof job.poller.close === 'function') job.poller.close();
      else if (typeof job.poller.stop === 'function') job.poller.stop();
      job.poller = null;
    }
    if (job.pollTimerId) { clearInterval(job.pollTimerId); job.pollTimerId = null; }
  }
  
  // =================== Live Sync Status (SSE Stream) ===================
  let _sseSource = null;          // EventSource instance
  let _sseFallbackTimer = null;   // fallback poll timer when SSE unavailable
  let _syncReadGeneration = 0;
  let _inactivePolls = 0;
  let _pollErrorCount = 0;        // consecutive failed fallback polls...
  const _POLL_MAX_ERRORS = 10;    // ...before the page says the connection is lost
  const _SSE_FALLBACK_INTERVAL = 2000;
  const _SSE_MAX_RETRIES = 5;
  let _resumeTeamSyncTimer = null;

  // -- SSE throttle: coalesce rapid messages into one DOM update per frame --
  let _pendingSyncData = null;
  let _syncRAFPending = false;

  // Latest snapshot - drives the terminal state (success vs "with problems").
  let _lastSyncData = null;
  // Mirror of the server's gitlab_token_ok so triggerSyncAll can short-circuit
  // even in the split second before _renderTokenBanner inserts the banner DOM.
  let _tokenOk = true;
  // Teams already shown as failed, so pre-existing failures on page load don't
  // toast en masse; only NEW failures during this session raise a toast. Null
  // until the first snapshot seeds it silently.
  let _seenFailedTeams = null;

  /**
   * Decide the terminal bar/toast state from the last snapshot.
   * A sync run that had ANY failed group must NOT report a green
   * "All syncs completed!" - it reports "finished with problems" (red),
   * names the failed groups, and points the user at Job History / support.
   */
  function _syncTerminalState() {
    const failed = (_lastSyncData && Number(_lastSyncData.sync_failed_count)) || 0;
    const cancelled = (_lastSyncData && Number(_lastSyncData.sync_cancelled_count)) || 0;
    if (failed > 0) {
      const names = ((_lastSyncData && _lastSyncData.teams) || [])
        .filter((x) => x.sync_status === 'failed')
        .map((x) => x.team_name);
      const list = names.length
        ? ': ' + names.slice(0, 3).join(', ') + (names.length > 3 ? '…' : '')
        : '';
      const msg = (COURSE_NAME ? COURSE_NAME + ': ' : '')
        + t('Sync finished with problems')
        + ' — ' + failed + ' '
        + t('group(s) failed') + list + '. '
        + t('See Job History or contact support.');
      return { status: 'error', message: msg };
    }
    if (cancelled > 0) {
      const names = ((_lastSyncData && _lastSyncData.teams) || [])
        .filter((x) => x.sync_status === 'cancelled')
        .map((x) => x.team_name);
      const list = names.length
        ? ': ' + names.slice(0, 3).join(', ') + (names.length > 3 ? '...' : '')
        : '';
      const msg = (COURSE_NAME ? COURSE_NAME + ': ' : '')
        + t('Sync cancelled')
        + ' - ' + cancelled + ' '
        + t('group(s) cancelled') + list + '.';
      return { status: 'error', message: msg };
    }
    return { status: 'done', message: t('All syncs completed!') };
  }

  // Check if there are active syncs initially
  const hasActiveSyncOnLoad = _pageConfig.hasActiveSyncOnLoad === true;
  let _syncWasActive = hasActiveSyncOnLoad;

  // After an import the page reloads; the sync-stream may immediately
  // fire a "complete" event (stale/reconciled job).  A second reload would
  // consume the sessionStorage toast and flash stale content.
  // Use a time-based approach: suppress reloads for N seconds after
  // import.  This prevents multiple code paths (SSE complete handler,
  // updateSyncStatusUI, polling) from racing to consume a one-shot flag.
  let _suppressSyncReloadUntil = 0;
  let _activeSingleTeamSyncs = 0;
  {
    const justImported = sessionStorage.getItem('importJustCompleted');
    if (justImported) {
      sessionStorage.removeItem('importJustCompleted');
      _suppressSyncReloadUntil = Date.now() + 15000;
    }
    // After a sync-completion reload, suppress the next SSE-driven reload
    // to prevent a reload loop that destroys the flash toast.
    const syncReloadDone = sessionStorage.getItem('_syncReloadDone');
    if (syncReloadDone) {
      sessionStorage.removeItem('_syncReloadDone');
      _suppressSyncReloadUntil = Date.now() + 5000;
    }
  }
  function _isSyncReloadSuppressed() {
    return Date.now() < _suppressSyncReloadUntil;
  }

  function _suspendCourseSyncStreamForTeamSync() {
    _activeSingleTeamSyncs += 1;
    _suppressSyncReloadUntil = Math.max(_suppressSyncReloadUntil, Date.now() + 30000);
    disconnectSyncStream();
  }

  function _resumeCourseSyncStreamAfterTeamSync(options = {}) {
    const delay = Number(options.delay || 0);
    const refresh = options.refresh === true;
    if (_resumeTeamSyncTimer) clearTimeout(_resumeTeamSyncTimer);
    _resumeTeamSyncTimer = setTimeout(() => {
      _resumeTeamSyncTimer = null;
      _activeSingleTeamSyncs = Math.max(0, _activeSingleTeamSyncs - 1);
      if (_activeSingleTeamSyncs > 0) {
        _suppressSyncReloadUntil = Math.max(_suppressSyncReloadUntil, Date.now() + 5000);
        return;
      }
      _suppressSyncReloadUntil = 0;
      connectSyncStream();
      if (refresh) _refreshCourseData();
    }, delay);
  }

  /** Prevent double-reload from SSE complete + polling detection firing simultaneously. */
  let _reloadScheduled = false;

  function _completeSyncWithoutReload() {

    _syncWasActive = false;
    const term = _syncTerminalState();
    let handledByGlobal = false;
    if (typeof completeGlobalJob === 'function') {
      handledByGlobal = completeGlobalJob(COURSE_ID, term.message, term.status);
    } else if (typeof hideGlobalJob === 'function') {
      hideGlobalJob(COURSE_ID);
    }
    _setSyncAllBtn(false);
    if (!handledByGlobal) showToast(term.message, term.status === 'error' ? 'danger' : 'success');
    _refreshCourseData();
  }

  function _completeCourseSync() {
    if (_isSyncReloadSuppressed()) {
      _completeSyncWithoutReload();
      return;
    }
    _scheduleReload();
  }

  /**
   * Centralized reload after sync completes.
   * Called from BOTH the SSE complete handler AND the polling path.
   * Uses _reloadScheduled flag to prevent double-invocation.
   */
  function _scheduleReload() {
    if (_reloadScheduled) return;
    _reloadScheduled = true;

    disconnectSyncStream();
    _syncWasActive = false;
    // Render the terminal bar state before the reload kicks in. A run with
    // failed groups ends red ("finished with problems"), not green.
    // completeGlobalJob owns the terminal toast; fall back to a direct
    // persisted toast only if no global job exists on this page.
    const term = _syncTerminalState();
    const _toastType = term.status === 'error' ? 'error' : 'success';
    const _toastMs = term.status === 'error' ? 10000 : 5000;
    let handledByGlobal = false;
    if (typeof completeGlobalJob === 'function') {
      handledByGlobal = completeGlobalJob(COURSE_ID, term.message, term.status);
    } else if (typeof hideGlobalJob === 'function') {
      hideGlobalJob(COURSE_ID);
    }
    _setSyncAllBtn(false);
    // If the global bar was not present, use flashToast so the user sees
    // the completion immediately and beforeunload can preserve it.
    if (!handledByGlobal) {
      if (typeof flashToast === 'function') {
        flashToast(term.message, _toastType, _toastMs);
      } else {
        try {
          sessionStorage.setItem('flash_toast', JSON.stringify({
            message: term.message,
            type: _toastType,
            duration: _toastMs,
            createdAt: Date.now(),
          }));
        } catch (_) {}
      }
    }
    // Mark that we already handled sync completion so the reloaded page
    // does not re-trigger _scheduleReload() if the server still reports
    // stale active-sync counts (race condition).
    try { sessionStorage.setItem('_syncReloadDone', '1'); } catch (_) {}
    reloadKeepScroll();
  }

  /** Open an SSE connection to the course sync stream endpoint. */
  function connectSyncStream() {
    disconnectSyncStream();  // close any prior connection
    if (!CAN_EDIT) return;
    _sseSource = GP.sse({
      url: `/api/v1/courses/${COURSE_ID}/sync-stream`,
      maxErrors: _SSE_MAX_RETRIES,
      // This stream retries on the fallback cadence, not the app default: a
      // sync is minutes long, so there is nothing to miss by waiting.
      reconnectMs: _SSE_FALLBACK_INTERVAL,
      events: {
        message: (ev) => {
          try {
            _pendingSyncData = JSON.parse(ev.data);
          } catch (e) {
            console.debug('[course-detail] SSE parse error', e);
            return;
          }
          // Coalesce rapid SSE messages - render only the latest data per frame
          if (!_syncRAFPending) {
            _syncRAFPending = true;
            requestAnimationFrame(() => {
              _syncRAFPending = false;
              if (_pendingSyncData) {
                updateSyncStatusUI(_pendingSyncData);
                _pendingSyncData = null;
              }
            });
          }
        },
        // Named "complete" event - sync finished, do a full reload for fresh data
        complete: (ev) => {
          let data;
          try { data = JSON.parse(ev.data); } catch (_) { /* Poll to verify. */ }
          if (data?.has_active_sync !== false) {
            disconnectSyncStream();
            _startFallbackPolling();
            return;
          }
          updateSyncStatusUI(data);
          disconnectSyncStream();
          if (_syncWasActive) _completeCourseSync();
        },
      },
      onFailure: (n) => {
        console.debug('[course-detail] SSE connection error #' + n);
        // Trigger immediate health check on first SSE failure
        if (n === 1 && window.GP?.health?.check) window.GP.health.check();
      },
      onGiveUp: () => {
        console.warn('[course-detail] SSE max retries reached, falling back to polling');
        _startFallbackPolling();
      },
      onBlocked: () => {
        console.warn('[course-detail] EventSource not available, falling back to polling');
        _startFallbackPolling();
      },
    });
  }

  /** Close SSE and stop any fallback/reconnect timers. */
  function disconnectSyncStream() {
    _syncReadGeneration += 1;
    _pendingSyncData = null;
    _inactivePolls = 0;
    if (_sseSource) { _sseSource.close(); _sseSource = null; }
    if (_sseFallbackTimer) { clearInterval(_sseFallbackTimer); _sseFallbackTimer = null; }
  }

  function _startFallbackPolling() {
    if (_sseFallbackTimer) return;
    _pollSyncStatusOnce();
    _sseFallbackTimer = setInterval(_pollSyncStatusOnce, _SSE_FALLBACK_INTERVAL);
  }

  function _pollSyncStatusOnce() {
    if (!CAN_EDIT) return;
    const generation = _syncReadGeneration;
    /* Coalesced, not superseded. Every tick asks the same question, so the
       right answer to an overlap is "join the one already in flight", not
       "cancel it and start again" - which also removes the abort accounting
       this used to need: an abandoned tick looked like a dropped connection
       and walked the poll to "Connection to server lost" while the server was
       answering fine. */
    return GP.coalesced('course-sync-status', async () => {
    try {
      const data = await apiCall(`/api/v1/courses/${COURSE_ID}/sync-status`, 'GET', null, { key: 'course-sync-status', maxRetries: 0, timeoutMs: 10000 });
      if (generation !== _syncReadGeneration) return;
      if (typeof data?.has_active_sync !== 'boolean') throw new Error('Missing sync status');
      _pollErrorCount = 0;
      updateSyncStatusUI(data);
      _inactivePolls = data.has_active_sync ? 0 : _inactivePolls + 1;
      if (_inactivePolls >= 2 && _syncWasActive) {
        _completeCourseSync();
      }
    } catch (err) {
      if (generation !== _syncReadGeneration) return;
      // Abandoned at navigation, not a dropped connection.
      if (err && err.superseded) return;
      _inactivePolls = 0;
      _pollErrorCount++;
      console.debug('Sync poll fallback error:', err);
      if (_pollErrorCount >= _POLL_MAX_ERRORS) {
        const infoCard = document.querySelector('.info-card-info .info-card-body') || document.querySelector('.info-card-info .sync-status-text');
        if (infoCard) {
          infoCard.innerHTML = GP.errorStateHtml(t('Connection to server lost. Sync status may be outdated.'), t('Retry'));
          GP.bindRetry(infoCard, _pollSyncStatusOnce);
        }
      }
    }
    });
  }
  
  let _renderedTeamCount = Number(_pageConfig.initialRenderedTeamCount || 0);

  function updateSyncStatusUI(data) {
    // If teams appeared but page was rendered with empty state - reload
    // BEFORE updating stat cards to avoid an inconsistent flash where
    // stats show N teams but the list still says "No Teams Yet".
    const teams = data.teams || [];
    // Remember the latest snapshot so the terminal state can tell success
    // from "finished with problems".
    _lastSyncData = data;
    if (teams.length > 0 && _renderedTeamCount === 0) {
      _renderedTeamCount = teams.length;  // prevent repeated reloads
      reloadKeepScroll();
      return;
    }

    // Group-level completion toast
    if (data.completed_group) {
      showToast(
        t('Group synced:') + ' ' + _escHtml(data.completed_group),
        'success',
        4000,
      );
    }

    // Per-group FAILURE toast: surface which groups failed AS they fail,
    // instead of silently swallowing the error and letting the bar flap.
    // Seed the set silently on the first snapshot so pre-existing failures
    // (page opened after a failed run) don't fire a burst of toasts.
    {
      const failedNow = new Set(
        teams.filter((x) => x.sync_status === 'failed').map((x) => x.team_id),
      );
      if (_seenFailedTeams === null) {
        _seenFailedTeams = failedNow;
      } else {
        teams.forEach((x) => {
          if (x.sync_status === 'failed' && !_seenFailedTeams.has(x.team_id)) {
            _seenFailedTeams.add(x.team_id);
            showToast(
              t('Group sync failed:') + ' ' + _escHtml(x.team_name),
              'danger',
              6000,
            );
          }
        });
        // Forget teams that recovered so a later failure can toast again.
        _seenFailedTeams.forEach((id) => { if (!failedNow.has(id)) _seenFailedTeams.delete(id); });
      }
    }

    // Update sync info card
    updateSyncInfoCard(data);

    // GitLab token health banner (shown only when the token is known-bad)
    _tokenOk = data.gitlab_token_ok !== false;
    _renderTokenBanner(data.gitlab_token_ok);

    _renderedTeamCount = teams.length;

    // Update each team row
    teams.forEach(team => {
      updateTeamRow(team);
    });
  }
  
  /**
   * Show/hide a persistent danger banner when the GitLab token is known-bad.
   * `ok === false` only when the server has actually seen a 401/403, so the
   * banner never flashes on a healthy token. The banner (not a disabled button)
   * is the single, clear explanation: buttons stay clickable and clicking Sync
   * All surfaces the same reason as a toast - consistent with Import and never
   * leaving the user wondering when a greyed-out button will re-enable.
   */
  function _renderTokenBanner(ok) {
    const existing = document.getElementById('gitlabTokenBanner');
    if (ok === false) {
      if (existing) return;
      // Portal into the global top strip (#globalBannerSlot) so it stacks with
      // the archived / data-outdated / sync banners - same unified .gp-top-banner
      // strip as the server-rendered ones. Fall back to the page body only if the
      // slot is somehow missing.
      const slot = document.getElementById('globalBannerSlot');
      const host = slot || document.querySelector('.info-card-info') || document.querySelector('.stats-grid');
      if (!host) return;
      const card = document.createElement('div');
      card.id = 'gitlabTokenBanner';
      card.className = 'gp-top-banner gp-top-banner--danger js-top-banner';
      card.setAttribute('role', 'alert');
      card.innerHTML =
        '<div class="gp-top-banner-inner">' +
        '<span class="gp-top-banner-icon">' + GP.iconSvg('alert-circle', 'sm') + '</span>' +
        '<span class="gp-top-banner-msg"><strong>' +
        _escHtml(t('GitLab token invalid')) + '</strong> · ' +
        _escHtml(
          t('The GitLab API token is invalid or expired (401). Sync, import and other GitLab actions are blocked until the token is updated.'),
        ) + '</span></div>';
      if (slot) host.appendChild(card);
      else host.insertAdjacentElement('beforebegin', card);
      // Ease it open so it doesn't shove the page content in one jump.
      if (window.GP?.revealBanner) window.GP.revealBanner(card);
    } else if (existing) {
      if (window.GP?.collapseBanner) window.GP.collapseBanner(existing);
      else existing.remove();
    }
  }

  function updateSyncInfoCard(data) {
    const syncRunning = data.sync_running_count;
    const syncQueued = data.sync_queued_count;
    const hasSyncWork = syncRunning > 0 || syncQueued > 0;
    const isFinishing = !hasSyncWork && data.has_active_sync === true;

    // Keep the global job in sync so it persists across page navigation
    if (hasSyncWork) {

      _syncWasActive = true;
      _setSyncAllBtn(true);
      // Progress is always at the GROUP level (completed_groups / total_groups)
      let pct = null;
      if (data.progress != null) {
        pct = Math.round(data.progress);
      } else if (data.synced_groups != null && data.total_groups > 0) {
        pct = Math.round((data.synced_groups / data.total_groups) * 100);
      }
      const synced = data.synced_groups;
      const total = data.total_groups;
      // Single shared message format - see window._courseSyncMsg in
      // global-job-bar.js. Avoids the dashboard banner flickering
      // between two separate templates on every poll tick.
      const msg = (typeof window._courseSyncMsg === 'function')
        ? window._courseSyncMsg(COURSE_NAME || '', syncRunning, syncQueued, synced, total)
        : ((COURSE_NAME ? COURSE_NAME + ': ' : '') + t('Syncing...'));
      // Authoritative server-side start of the run (ms since epoch). Anchor
      // the bar's elapsed timer to it so the timer stays stable across page
      // navigations instead of resetting to the new page's load time.
      const _serverStart = Number(data.started_at_ms) || 0;
      if (typeof _globalJobs !== 'undefined' && _globalJobs[COURSE_ID]) {
        const job = _globalJobs[COURSE_ID];
        if (!job.meta) job.meta = {};
        job.meta.jobKind = 'course_sync';
        if (COURSE_NAME) job.meta.courseName = COURSE_NAME;
        // Pull startedAt back to the server start when it is earlier than
        // the (possibly client-stamped) value - monotonic earliest wins.
        if (_serverStart > 0 && (!job.startedAt || _serverStart < job.startedAt)) {
          job.startedAt = _serverStart;
        }
        if (pct != null) {
          job.progress = pct;
        }
        if (typeof updateGlobalJob === 'function') updateGlobalJob(msg, COURSE_ID);
      } else {
        // No inline indicator anymore - surface directly in the global bar.
        // `passive: true` - this is a reconciliation call on every SSE
        // tick, not a user button click, so it must not clear a dismissal.
        if (typeof showGlobalJob === 'function') showGlobalJob(msg, COURSE_ID, { jobKind: 'course_sync', courseName: COURSE_NAME, courseId: String(COURSE_ID || ''), passive: true, startedAt: _serverStart || undefined });
      }
      // This page owns sync tracking - stop global bar's own SSE/polling
      _stopGlobalBarTracking();
    } else if (isFinishing && _syncWasActive) {
      _syncWasActive = true;
      _setSyncAllBtn(true);
      const msg = (typeof window._courseFinishingMsg === 'function')
        ? window._courseFinishingMsg(COURSE_NAME || '')
        : ((COURSE_NAME ? COURSE_NAME + ': ' : '') + t('Finishing...'));

      if (typeof _globalJobs !== 'undefined' && _globalJobs[COURSE_ID]) {
        const job = _globalJobs[COURSE_ID];
        if (!job.meta) job.meta = {};
        job.meta.jobKind = 'course_sync';
        if (COURSE_NAME) job.meta.courseName = COURSE_NAME;
      } else if (typeof showGlobalJob === 'function') {
        showGlobalJob(msg, COURSE_ID, {
          jobKind: 'course_sync',
          courseName: COURSE_NAME,
          courseId: String(COURSE_ID || ''),
          passive: true,
        });
      }

      if (typeof window.markCourseSyncFinishing === 'function') {
        window.markCourseSyncFinishing(COURSE_ID, msg);
      } else if (typeof updateGlobalJob === 'function') {
        updateGlobalJob(msg, COURSE_ID);
      }
      _stopGlobalBarTracking();

    }

    // Update failed jobs card. Manage ONLY the JS-created live card
    // (#jsSyncFailedCard). Never remove the server-rendered "Some sync jobs
    // failed" banner (.js-sync-failed-banner) - its count is computed at page
    // load over a different window than the SSE's 2h window, so an SSE tick
    // reporting 0 does NOT mean the server banner is wrong. It also must never
    // touch #gitlabTokenBanner (also .info-card-danger). This was the "8 groups
    // failed banner flashes and vanishes in a second" bug.
    const existingFailed = document.querySelector('.js-sync-failed-banner');
    const jsFailedCard = document.getElementById('jsSyncFailedCard');
    if (data.sync_failed_count > 0) {
      if (!existingFailed) {
        // Portal into the global top strip so the live "failed" banner sits with
        // the other page-level status strips (same unified .gp-top-banner style as
        // the server-rendered one). Body fallback only if the slot is missing.
        const slot = document.getElementById('globalBannerSlot');
        const host = slot || document.querySelector('.info-card-info') || document.querySelector('.stats-grid');
        if (host) {
          const titleTxt = t('Some sync jobs failed');
          const bodyTxt = t('group(s) failed to sync. You can retry using the Sync action for those groups.');
          const newCard = document.createElement('div');
          newCard.id = 'jsSyncFailedCard';
          newCard.className = 'gp-top-banner gp-top-banner--danger js-top-banner js-sync-failed-banner';
          newCard.setAttribute('role', 'status');
          newCard.setAttribute('aria-live', 'polite');
          newCard.innerHTML = `
            <div class="gp-top-banner-inner">
              <span class="gp-top-banner-icon">${GP.iconSvg('alert-circle', 'sm')}</span>
              <span class="gp-top-banner-msg"><strong>${titleTxt}</strong> · ${data.sync_failed_count} ${bodyTxt}</span>
            </div>
          `;
          if (slot) {
            host.appendChild(newCard);
          } else {
            host.insertAdjacentElement('afterend', newCard);
          }
        }
      }
    } else if (jsFailedCard) {
      jsFailedCard.remove();
    }
  }
  
  /**
   * Single source of truth for the "Last Updated" cell.
   *
   * The cell is fed by two independent SSE streams (/sync-stream and the
   * /live-data poll). Without a canonical key they fight every tick: one
   * writes a localized `<time>` (user-local 21:05) and the other stomps it
   * with the raw server UTC string (19:05), so the value visibly blinks
   * between the two. This helper makes the update idempotent and keyed off
   * the canonical UTC ISO timestamp, so once a value is rendered and
   * localized it is never rewritten until the underlying timestamp actually
   * changes.
   *
   * @param {HTMLTableCellElement} cell  - the Last Updated <td>
   * @param {string} text - server display fallback ("2026-06-01 19:05" or a
   *                        transient status like "Sync in progress...")
   * @param {?string} iso - canonical UTC ISO ("...Z") or null for status text
   */
  function _renderLastUpdated(cell, text, iso) {
    if (!cell) return;
    const display = text ? t(text) : '-';
    const sortValue = iso || '';
    if (cell.dataset.sortValue !== sortValue) cell.dataset.sortValue = sortValue;
    if (iso) {
      // Skip entirely when the same timestamp is already shown - this is
      // what keeps the localized value from bouncing back to raw UTC on
      // every SSE frame that carries an unchanged computed_at.
      const existing = cell.querySelector('time[datetime]');
      if (existing && existing.getAttribute('datetime') === iso) return;
      cell.className = 'muted col-hide-md';
      cell.innerHTML = GP.timeHtml(iso);
      window.localizeTimes(cell);
      return;
    }
    // Transient status text ("Sync in progress...", "Sync queued...").
    if (cell.textContent !== display) {
      cell.className = 'muted col-hide-md';
      cell.textContent = display;
    }
  }

  // Match the server's integer percentage rounding, including exact halves.
  const _scoreFormat = new Intl.NumberFormat(document.documentElement.lang, {
    maximumFractionDigits: 0, useGrouping: false, roundingMode: 'halfEven',
  });

  function updateTeamRow(team) {
    const row = document.querySelector(`#teamsTable tr[data-team-id="${CSS.escape(team.team_id)}"]`);
    if (!row) return;
    const setText = (cell, value) => { if (cell && cell.textContent !== value) cell.textContent = value; };
    setText(row.cells[2], String(team.member_count));
    setText(row.cells[3], team.avg_score != null ? _scoreFormat.format(team.avg_score * 100) + '%' : '-');

    // Live metric reads omit retry notes; keep the stream's note while that
    // same group is still running, then retire it with the terminal status.
    if ('sync_note' in team) row.dataset.syncNote = team.sync_note || '';
    if (team.sync_status !== 'running') delete row.dataset.syncNote;
    const retryNote = row.dataset.syncNote;
    const statusCell = row.cells[4];
    if (statusCell) {
      const light = String(team.traffic_light || '').toUpperCase();
      let html;
      let sortValue = '3';
      if (row.hasAttribute('data-team-inactive')) {
        html = GP.badgeHtml(t(CAN_EDIT ? 'Deleted' : 'Archived'), CAN_EDIT ? 'danger' : 'secondary');
      } else if (team.sync_status === 'running' || team.sync_status === 'enqueued') {
        const attempt = retryNote && /\((\d+)\/(\d+)\)/.exec(retryNote);
        const label = team.sync_status === 'enqueued' ? t('QUEUED')
          : attempt ? 'RETRY ' + attempt[1] + '/' + attempt[2] : retryNote ? t('RETRYING') : t('SYNCING');
        html = GP.badgeHtml(label, 'info');
        sortValue = '4';
      } else if (team.sync_status === 'cancelled') {
        html = GP.badgeHtml(t('CANCELLED'), 'warning');
      } else if (light) {
        html = GP.trafficLightHtml(light);
        sortValue = String({ RED: 0, YELLOW: 1, AMBER: 1, GREEN: 2 }[light] ?? 3);
      } else if (team.sync_status === 'failed') {
        html = GP.badgeHtml(t('FAILED'), 'danger');
      } else if (team.sync_status === 'completed') {
        html = GP.badgeHtml(t('DONE'), 'success');
      } else {
        html = GP.badgeHtml(t('N/A'), 'gray');
      }
      if (statusCell.dataset.sortValue !== sortValue) statusCell.dataset.sortValue = sortValue;
      if (statusCell.innerHTML.trim() !== html) statusCell.innerHTML = html;
    }
    _renderLastUpdated(row.cells[5], retryNote || team.last_updated, retryNote ? null : team.last_updated_iso);
    const search = `${team.team_name.toLowerCase()} ${(team.traffic_light || '').toLowerCase()}`;
    if (row.dataset.search !== search) row.dataset.search = search;
  }

  // Initialize SSE sync stream on page load
  function _bootSync() {
    if (!CAN_EDIT) return;
    // Keep the global bar in sync with server-reported state on arrival.
    if (hasActiveSyncOnLoad) {
      // `passive: true` - page-load registration, must respect existing dismissal.
      // Compose using the unified _courseSyncMsg helper so the bar never
      // flashes a duplicated placeholder "Syncing data..." before SSE
      // delivers the first frame and immediately overrides it.
      const _initMsg = (typeof window._courseSyncMsg === 'function')
        ? window._courseSyncMsg(COURSE_NAME || '', 0, 0)
        : t('Syncing:');
      if (typeof showGlobalJob === 'function') showGlobalJob(_initMsg, COURSE_ID, { jobKind: 'course_sync', courseName: COURSE_NAME, courseId: String(COURSE_ID || ''), passive: true });
      _setSyncAllBtn(true);
    } else if (typeof _globalJobs !== 'undefined' && _globalJobs[COURSE_ID]) {
      const job = _globalJobs[COURSE_ID];
      const terminal = job.status === 'done' || job.status === 'error';
      if (terminal) {
        _setSyncAllBtn(false);
      } else {
        _syncWasActive = true;
        _setSyncAllBtn(true);
      }
    }

    // Stop global bar's own SSE/polling - this page handles sync updates via SSE
    _stopGlobalBarTracking();

    // Open SSE stream for live sync status
    connectSyncStream();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _bootSync);
  } else {
    _bootSync();
  }
  // =================== End Live Sync Status ===================
