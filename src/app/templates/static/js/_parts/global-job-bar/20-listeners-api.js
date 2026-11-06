/* Only an explicit terminal status can end tracking. Empty, idle or malformed
   responses do not prove success; retry the read without releasing job locks. */
function _completeStatusJob(jobType, data, onDone, onFailed) {
  const status = String(data?.status || '').toLowerCase();
  if (status === 'completed') return completeGlobalJob(jobType, onDone(data), 'done');
  if (status === 'failed') return completeGlobalJob(jobType, onFailed(data), 'error');
  if (status === 'cancelled') return completeGlobalJob(jobType, data?.message || t('Cancelled'), 'error');
  return false;
}

function _startLegacyGenericPoll(jobType, url, opts = {}) {
  if (!_globalJobs[jobType]) return;
  _stopPoller(jobType);
  const trackedJob = _globalJobs[jobType];
  let reading = false;
  let pollErrors = 0;
  const maxErrors = opts.maxErrors || 10;

  const onRunning = typeof opts.messageRunning === 'function'
    ? opts.messageRunning
    : (data) => data?.message || t('Processing...');

  const onDone = typeof opts.messageDone === 'function'
    ? opts.messageDone
    : () => 'Completed!';

  const onFailed = typeof opts.messageFailed === 'function'
    ? opts.messageFailed
    : (data) => data?.message || 'Process failed';

  const poll = async () => {
    if (reading || _globalJobs[jobType] !== trackedJob || _isUiTerminalStatus(trackedJob.status)) return;
    reading = true;
    try {
      const data = await GP.apiCall(url, 'GET', null, { maxRetries: 0, timeoutMs: 10000 });
      if (_globalJobs[jobType] !== trackedJob || trackedJob.pollTimerId !== intervalId) return;
      pollErrors = 0;
      const status = String(data?.status || '').toLowerCase();
      if (status === 'enqueued' || status === 'queued') {
        updateGlobalJob(t('Waiting in queue...'), jobType);
      } else if (status === 'running' || status === 'started') {
        const job = _globalJobs[jobType];
        if (job && data?.progress != null) {
          job.progress = Number(data.progress);
        }
        if (job && data?.percent != null) {
          job.progress = Number(data.percent);
        }
        updateGlobalJob(onRunning(data), jobType);
      } else if (!_completeStatusJob(jobType, data, onDone, onFailed)) {
        updateGlobalJob(t('Status unavailable - the process may still be running.'), jobType);
      }
    } catch (err) {
      if (_globalJobs[jobType] !== trackedJob || trackedJob.pollTimerId !== intervalId) return;
      pollErrors++;
      if (err?.status === 404) {
        // Resource gone (e.g. DB wiped) - remove stale job silently
        hideGlobalJob(jobType);
        GP.refreshProcessActionGuards();
        return;
      }
      if (err?.status === 401 || err?.status === 403) {
        completeGlobalJob(jobType, t('Session expired - refresh the page'), 'error');
        return;
      }
      if (pollErrors >= maxErrors) {
        updateGlobalJob(t('Network error checking status'), jobType);
      }
    } finally {
      reading = false;
    }
  };

  const intervalId = setInterval(poll, opts.interval || 3000);
  _globalJobs[jobType].pollTimerId = intervalId;
  setTimeout(() => { if (_globalJobs[jobType]?.pollTimerId === intervalId) poll(); }, 1000);
}

function _restoreJobs(jobsObj) {
  const now = _now();

  Object.entries(jobsObj).forEach(([jobType, value]) => {
    // Discovery can finish after a live tracker starts. Keep its poller and
    // object identity instead of orphaning its connection with a stored copy.
    if (_globalJobs[jobType]) return;
    if (!value || typeof value.startedAt !== 'number') {
      return;
    }

    // Preserve recently-completed bars across navigation so the user
    // actually sees the "100% / Sync completed!" terminal state they
    // deserve - otherwise a completion that fires ~1 s before the user
    // clicks a link vanishes mid-transition and they never see the bar
    // reach 100 %. Anything older than AUTO_HIDE_SUCCESS_MS + a small
    // animation buffer is genuinely stale and dropped as before.
    if (value.status === 'done' || value.status === 'error') {
      const completedAt = value.completedAt || value.startedAt;
      const ttl = value.status === 'error'
        ? AUTO_HIDE_ERROR_MS + ANIMATION_EXIT_FALLBACK_MS
        : AUTO_HIDE_SUCCESS_MS + ANIMATION_EXIT_FALLBACK_MS;
      if (now - completedAt > ttl) {
        return;
      }
      _globalJobs[jobType] = {
        message: value.message || 'Processing...',
        startedAt: value.startedAt,
        completedAt,
        status: value.status,
        progress: value.status === 'done' ? 100 : (value.progress ?? null),
        meta: value.meta || {},
        cancelRequested: value.cancelRequested === true,
        lastUpdate: now,
        pollTimerId: null,
        poller: null,
        hideTimerId: null,
      };
      // Re-schedule auto-hide for the remaining window.
      const remaining = Math.max(0, ttl - (now - completedAt));
      _globalJobs[jobType].hideTimerId = setTimeout(() => {
        const j = _globalJobs[jobType];
        if (!j || (j.status !== 'done' && j.status !== 'error')) return;
        const { content } = _barElements();
        if (content) {
          const item = content.querySelector(`[data-job-id="${CSS.escape(jobType)}"]`);
          if (item) { _animateJobExit(item, jobType); return; }
        }
        hideGlobalJob(jobType);
      }, remaining);
      // Replay completion toast: if the original completion fired during
      // a navigation (SSE delivered `complete` between beforeunload and
      // actual unload), the toast was never persisted by
      // _preserveFlashToast and the user saw nothing despite the count
      // increasing server-side.  Queue a replay - _completionAlreadyShown
      // will block it inside the same page-load or beyond the nav-replay
      // window, so this is safe across normal cases.
      _queuedToasts.push({
        msg: value.message || (value.status === 'error' ? t('Process failed') : t('Process completed')),
        type: value.status === 'error' ? 'error' : 'success',
        status: value.status,
        jobType,
        _skipBroadcast: true,
      });
      return;
    }

    if (_isDismissed(jobType, value.startedAt)) {
      return;
    }

    const age = now - value.startedAt;
    if (age > _jobMaxAge(jobType)) {
      return;
    }

    _globalJobs[jobType] = {
      message: value.message || 'Processing...',
      startedAt: value.startedAt,
      status: value.status === 'finishing' ? 'running' : (value.status || 'running'),
      progress: value.status === 'finishing' ? null : (value.progress ?? null),
      meta: value.meta || {},
      cancelRequested: value.cancelRequested === true,
      lastUpdate: now, // Grace period so staleness guard waits for SSE to reconnect
      pollTimerId: null,
      poller: null,
      hideTimerId: null,
    };
    _restoredJobs.add(jobType);
  });

  if (!Object.keys(_globalJobs).length) {
    try {
      localStorage.removeItem(GLOBAL_JOB_KEY);
    } catch (_) {
      // ignore storage errors
    }
    return;
  }

  // Watch local indicators for restored jobs (defer/promote like fresh starts).
  // If a local selector is configured but the element doesn't exist yet
  // (lazy HTMX content), set up a MutationObserver that hands off to the
  // IntersectionObserver once the element appears - this is the ONLY way
  // the bar defers correctly on the course page where #inlineSyncStatus
  // arrives via HTMX swap, while still showing the bar on unrelated pages
  // (admin/users, admin/system, home dashboard) where the element never
  // appears.  No pre-deferral: bar renders immediately with CSS slide-in.
  Object.entries(_globalJobs).forEach(([jobType, job]) => {
    const localSel = job.meta?.localIndicatorSelector || _DEFAULT_LOCAL_SELECTORS[jobType];
    if (!localSel) return;
    _watchLocalIndicator(jobType, localSel);
    if (!_localIndicators[jobType]) {
      _watchForLocalIndicatorAppearance(jobType, localSel);
    }
  });

  // Defer initial render to the next frame so other DOMContentLoaded handlers
  // (e.g., course-detail _bootSync) can register their deferrals first.
  // This prevents the global bar from flashing briefly on pages that show
  // sync status inline.
  requestAnimationFrame(() => {
    _renderGlobalBar();
  });
  _suppressToasts = true;

  Object.keys(_globalJobs).forEach((jobType) => {
    const job = _globalJobs[jobType];
    // Don't restart polling/SSE for jobs that already finished - they are
    // only being kept around so the user sees the terminal "100%" frame
    // and the auto-hide timer can complete the slide-out. Re-opening the
    // SSE stream here used to cause the server's 15 s post-completion
    // grace window to re-emit a `complete` event, which in turn called
    // completeGlobalJob() a second time. Idempotency catches the second
    // call now, but the network/CPU cost was pure waste.
    if (job && (job.status === 'done' || job.status === 'error')) {
      return;
    }
    _autoStartPolling(jobType);
    if (jobType === 'enrichment') {
      document.dispatchEvent(new CustomEvent('enrichment-restored'));
    }
    window.dispatchEvent(new CustomEvent('gp:job-update', {
      detail: {
        jobType,
        message: job.message,
        progress: job.progress,
      },
    }));
  });

  if (_globalJobs.import) {
    completeGlobalJob('import', t('Import was interrupted - please restart'), 'error');
    try {
      sessionStorage.removeItem('activeImport');
    } catch (_) {
      // ignore storage errors
    }
  }

  setTimeout(() => {
    _suppressToasts = false;
    _restoredJobs.clear();
    const pending = _queuedToasts.splice(0);
    pending.forEach(({ msg, type, status: s, jobType: jt, _skipBroadcast: sb }) => {
      // Honour the same session-scoped dedup that _showCompletionToast uses
      // so a completion that was already shown earlier in this tab session
      // (e.g. on a previous page, persisted in sessionStorage) doesn't pop
      // again here.
      if (jt && _completionAlreadyShown(jt, s)) return;
      if (typeof flashToast === 'function') flashToast(msg, type, s === 'error' ? 10000 : 5000);
      if (jt) _markCompletionShown(jt, s);
      if (!sb && typeof broadcastToast === 'function') broadcastToast(msg, type);
    });
  }, 2000);

  _saveGlobalJobs();
}

function restoreGlobalJobBar() {
  // Support multiple <meta name="defer-global-job"> tags AND a
  // comma-separated content value - so pages like the dashboard can
  // pre-defer every active course sync before any bar render happens.
  document.querySelectorAll('meta[name="defer-global-job"]').forEach((m) => {
    const val = (m.content || '').trim();
    if (!val) return;
    val.split(',').map((s) => s.trim()).filter(Boolean).forEach((id) => {
      _deferredJobs.add(id);
      _metaDeferredJobs.add(id);
    });
  });

  // Best-practice two-phase init:
  //   1. Ask the server what sync jobs are actually running (/sync/active).
  //   2. Restore localStorage entries, but DROP any course-sync entry that
  //      the server does not confirm as running - that's stale cache from
  //      a previous sync that completed in another tab.
  //
  // This is the single authoritative source of truth and eliminates:
  //   - stale-cache flash (bar appears for work that already finished)
  //   - mid-sync vanishing (bar flickered when SSE hit zero-window)
  // without needing a pendingConfirmation flag, delayed render, or
  // post-complete re-verification round-trip.
  //
  // If /sync/active fails (offline, 5xx), we fall back to the old
  // optimistic restore so the bar still appears for connectivity
  // blips during an active sync.
  // Stamp the timestamp so the htmx:load -> _onHtmxNavigated path skips
  // a duplicate /sync/active fetch that would otherwise fire 250ms later
  // (because _lastSyncActiveAt was still 0 when htmx:load fires after init).
  _lastSyncActiveAt = Date.now();
  _fetchActiveSyncs().then((activeSet) => {
    _restoreAndReconcile(activeSet);
    _startSyncWatchdog();
  }).catch(() => {
    // Fallback: server unreachable - restore optimistically.
    _restoreAndReconcile(null);
  });
}

let _syncWatchdogId = null;

function _startSyncWatchdog() {
  if (_syncWatchdogId) { clearInterval(_syncWatchdogId); }
  _syncWatchdogId = setInterval(() => {
    if (document.visibilityState === 'hidden') return;
    // Only the leader tab reconciles against /sync/active - followers mirror
    // via 'storage'. Fail-open so a lone tab always reconciles.
    if (typeof _isPollLeader === 'function' && !_isPollLeader()) return;
    if (_lastCompletionAt
      && (Date.now() - _lastCompletionAt) < POST_COMPLETION_RECONCILE_SUPPRESS_MS) {
      return;
    }
    _fetchActiveSyncs().then(_reconcileCourseJobs).catch(() => { });
  }, 30000);
}

/**
 * True when a non-terminal project-/team-scoped sync row for `courseId`
 * is already being tracked. The `/sync/active` reconciler must NOT spawn a
 * second course-level aggregate row for the same work - that is the source
 * of the duplicate progress bars (one "Syncing project..." row + one
 * "COURSE: Syncing" row for a single user action). The scoped row already
 * represents this course's in-flight sync, so we suppress the aggregate at
 * creation time rather than hiding it after the fact.
 * @private
 */
function _hasScopedSyncForCourse(courseId) {
  const cid = String(courseId || '');
  if (!cid) return false;
  return Object.keys(_globalJobs).some((jt) => {
    const job = _globalJobs[jt];
    if (!job) return false;
    if (job.status === 'done' || job.status === 'error') return false;
    const kind = job.meta?.jobKind;
    if (kind !== 'project_sync' && kind !== 'team_sync') return false;
    return String(job.meta?.courseId || '') === cid;
  });
}

/* Until this has answered once, the page does not know whether anything is
   running - and the process guard, which reads `_globalJobs`, sees an empty
   object and lets every locked action through. That is the window in which a
   button that should be blocked is clickable, on every page that has one.
   `window._globalJobsReady` closes it: false until the first answer (or the
   first failure), and the guard refuses locked actions while it is false. */
window._globalJobsReady = false;
function _markJobStateKnown() {
  if (window._globalJobsReady) return;
  window._globalJobsReady = true;
  try { window.GP?.refreshProcessActionGuards?.(); } catch (_) { /* noop */ }
}

/** Fetch /sync/active and return a Map<course_id, course_data>. */
function _fetchActiveSyncs() {
  const controller = (typeof AbortController === 'function') ? new AbortController() : null;
  const timeoutId = controller ? setTimeout(() => controller.abort(), 5000) : null;
  return fetch('/api/v1/sync/active', {
    method: 'GET',
    credentials: 'same-origin',
    headers: { 'Accept': 'application/json' },
    signal: controller ? controller.signal : undefined,
  }).then((resp) => {
    if (timeoutId) clearTimeout(timeoutId);
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    return resp.json();
  }).then((data) => {
    const map = new Map();
    if (data && Array.isArray(data.courses)) {
      data.courses.forEach((c) => {
        if (c && c.course_id) map.set(String(c.course_id), c);
      });
    }
    return map;
  }).finally(() => {
    /* Both paths: an unreachable endpoint must not leave the UI blocked for
       good, so a failure counts as "known" too. */
    _markJobStateKnown();
  });
}

/**
 * Phase-2 restore: apply the authoritative active-sync set to
 * localStorage-restored jobs and to any fresh server-side syncs that
 * weren't yet tracked locally.
 *
 * @param {Map|null} activeSet map of course_id -> {name,code,running,queued};
 *   pass null when the server was unreachable (fallback: show cache).
 */
function _restoreAndReconcile(activeSet) {
  // 1. Load localStorage and register jobs in memory.
  let parsed = null;
  try {
    const raw = localStorage.getItem(GLOBAL_JOB_KEY);
    if (raw) {
      parsed = JSON.parse(raw);
      if (parsed && parsed.startedAt && parsed.message) {
        // Legacy single-job format.
        const legacyType = parsed.jobType || 'default';
        parsed = { [legacyType]: parsed };
      }
    }
  } catch (_) {
    parsed = null;
  }

  if (parsed && typeof parsed === 'object') {
    // 2. If server responded, drop course-sync entries NOT in active set.
    //    Identified as course_sync by meta.jobKind or by an ID shape that
    //    /sync/active would have returned (UUID or numeric).
    //
    //    Protect against the between-batch zero-window race: if the
    //    localStorage entry is YOUNG (< 2 min since startedAt) and its
    //    last update was recent, keep it even if /sync/active
    //    momentarily doesn't list it - the SSE stream will either
    //    re-confirm activity or fire a debounced `complete`.
    if (activeSet) {
      const ZERO_WINDOW_GRACE_MS = 120000; // 2 minutes
      const now = _now();
      Object.keys(parsed).forEach((jobType) => {
        const v = parsed[jobType];
        if (!v || typeof v !== 'object') return;
        // Reconcile ANY sync-scope job against /sync/active - course-level AND
        // team-/project-scoped. Previously only course syncs were checked, so a
        // team/project ghost ("sync:team:<id>" / "sync:project:<id>") restored
        // from localStorage was skipped entirely: it lingered in _globalJobs and
        // kept the Sync / Run Checks button process-locked for its full maxAge
        // (up to 45 min) even though the server reported nothing active - and it
        // survived page refreshes because localStorage persists. It now checks
        // the job's OWNING COURSE (activeSet is keyed by course_id; team/project
        // jobs carry it in meta.courseId) so stale ghosts are dropped everywhere.
        const isSyncJob = (
          v.meta?.jobKind === 'course_sync'
          || v.meta?.jobKind === 'team_sync'
          || v.meta?.jobKind === 'project_sync'
          || /^sync(:|$)/.test(String(jobType))
          || UUID_LIKE_REGEX.test(jobType)
          || /^\d+$/.test(jobType)
        );
        if (!isSyncJob) return;
        // Scoped jobs have their own authoritative /jobs/{id} status.
        // Course discovery deliberately excludes project-only work.
        if (v.meta?.jobId) return;
        // A course-level jobType IS the course id; team/project jobs carry it in
        // meta.courseId. Fall back to the raw key (which then won't be in the
        // course-keyed activeSet, so a ghost with no courseId is treated stale).
        const courseKey = String((v.meta && v.meta.courseId) || jobType);
        // Recently-terminal entries are intentionally restored by
        // _restoreJobs for their remaining auto-hide window. Older ones
        // are dropped there by completedAt TTL, so do not delete them
        // here just because /sync/active responded: that swallowed the
        // "done" frame and toast during navigation.
        if (v.status === 'done' || v.status === 'error') {
          return;
        }
        // Owning course still has running/queued work (incl. the server's
        // post-completion grace window) - keep it.
        if (activeSet.has(courseKey)) return;
        // Not active and not terminal - decide whether stale or just
        // between-batches.
        const age = now - (v.startedAt || 0);
        const sinceUpdate = now - (v.lastUpdate || v.startedAt || 0);
        if (age < ZERO_WINDOW_GRACE_MS && sinceUpdate < 60000) {
          // Recent sync - keep it.  SSE will confirm either way.
          return;
        }
        // Old/stale - truly finished elsewhere (or never really started).
        delete parsed[jobType];
      });
      // Persist the cleaned-up state immediately so other tabs don't
      // re-resurrect truly-stale entries.
      try {
        if (Object.keys(parsed).length) {
          localStorage.setItem(GLOBAL_JOB_KEY, JSON.stringify(parsed));
        } else {
          localStorage.removeItem(GLOBAL_JOB_KEY);
        }
      } catch (_) { /* ignore storage errors */ }
    }
    _restoreJobs(parsed);
  }

  // 3. Register server syncs that aren't yet in localStorage (e.g. sync
  //    triggered in another tab/device).
  if (activeSet) {
    activeSet.forEach((c, courseId) => {
      // Skip courses currently in the server's post-completion grace
      // window (running=0, queued=0).  /sync/active keeps a course
      // visible for ~15 s after the last group finished so SSE can
      // deliver a final `complete` event - registering them here would
      // spawn a fresh bar AND set serverConfirmedRunning=true, which
      // the 5 s watchdog would then immediately finalize, causing a
      // ghost "Sync completed" bar + toast on every page navigation.
      const hasWork = (Number(c.running) || 0) + (Number(c.queued) || 0) > 0;
      if (!hasWork && !_globalJobs[courseId]) return;
      // Suppress the course-level aggregate when a project/team sync row
      // for this same course is already tracked - otherwise the user sees
      // two bars for one operation.
      if (!_globalJobs[courseId] && _hasScopedSyncForCourse(courseId)) return;
      // Respect an active client-side dismissal: if the user closed this
      // bar for the CURRENT run, do not re-create it on every page
      // navigation. `_isDismissed` auto-clears when the server reports a
      // run that started AFTER the dismissal timestamp (genuinely fresh
      // work), so new syncs after a dismiss still appear.
      if (_isDismissed(String(courseId), Number(c.started_at_ms) || 0)) {
        return;
      }
      const label = c.code || c.name || t('Course');
      const msg = _courseSyncMsg(label, c.running, c.queued, c.synced_groups, c.total_groups);
      const existing = _globalJobs[courseId];
      if (!hasWork && existing) {
        if (existing.status === 'done' || existing.status === 'error' || existing.status === 'finishing') {
          return;
        }
        _markCourseSyncFinishing(courseId, _courseFinishingMsg(label));
        return;
      }
      // If localStorage restored a `done`/`error` entry from a previous
      // run but the server reports the course as freshly active, drop
      // the stale terminal entry so showGlobalJob() resets it to
      // running.  Otherwise updateGlobalJob() short-circuits on the
      // monotonic-status guard and the dashboard shows a phantom
      // "Sync completed!" bar with progress=100 for an in-flight sync.
      if (existing && (existing.status === 'done' || existing.status === 'error')) {
        if (existing.hideTimerId) clearTimeout(existing.hideTimerId);
        delete _globalJobs[courseId];
      } else if (existing) {
        _markCourseSyncRunning(courseId);
        existing.serverConfirmedRunning = true;
        existing.lastUpdate = _now();
        // Do NOT overwrite the message here. If an SSE/poll handler
        // is already producing the detailed "Syncing: X/Y groups done
        // (R active, Q queued)" string, calling updateGlobalJob with
        // the simpler "Syncing CODE: R running, Q queued" placeholder
        // causes a per-page-tick flicker between the two formats.
        // SSE remains the authoritative source for the visible text.
        if (!existing.message) {
          updateGlobalJob(msg, courseId);
        }
        return;
      }
      showGlobalJob(msg, courseId, {
        jobKind: 'course_sync',
        courseName: label,
        // Pass server's enqueued_at so showGlobalJob can correctly tell
        // this is an already-running job (not a fresh user click) and
        // honour an existing dismissal instead of wiping it.
        startedAt: Number(c.started_at_ms) || undefined,
      });
      if (_globalJobs[courseId]) {
        _globalJobs[courseId].serverConfirmedRunning = true;
      }
    });
  }
}

/**
 * Watchdog callback: reconcile current course-sync jobs against a fresh
 * /sync/active response.  Adds newly-started syncs.  Does NOT remove
 * existing bars - SSE is the authoritative source for removal (via its
 * 6 s inactive debounce + final /sync/active verify on the `complete`
 * event). A naïve remove here would race with the brief between-batch
 * zero-windows where /sync/active momentarily returns no jobs.
 *
 * Called every 30 s while tab is visible, and on visibilitychange.
 */
function _reconcileCourseJobs(activeSet) {
  if (!activeSet) return;

  // Add any newly-started server syncs not yet in the bar.
  activeSet.forEach((c, courseId) => {
    const hasWork = (Number(c.running) || 0) + (Number(c.queued) || 0) > 0;
    const existing = _globalJobs[courseId];
    if (existing) {
      if (!hasWork) {
        if (existing.status !== 'done' && existing.status !== 'error' && existing.status !== 'finishing') {
          const label = c.code || c.name || existing.meta?.courseName || t('Course');
          _markCourseSyncFinishing(courseId, _courseFinishingMsg(label));
        }
        return;
      }
      // Server says this course is actively syncing - but the local
      // entry is in a terminal state (e.g. SSE delivered a stale
      // `complete` during a between-batch zero-window, or localStorage
      // carried a previous run's done-state into this page).  Drop it
      // so the showGlobalJob() path below recreates a fresh running
      // bar.  Without this, updateGlobalJob() refuses to reset the
      // status and the dashboard shows "Sync completed!" while the
      // server is still working through queued teams.
      if (hasWork && (existing.status === 'done' || existing.status === 'error')) {
        if (existing.hideTimerId) clearTimeout(existing.hideTimerId);
        delete _globalJobs[courseId];
      } else {
        _markCourseSyncRunning(courseId);
        existing.serverConfirmedRunning = true;
        existing.lastUpdate = _now();
        return;
      }
    }
    // Don't spawn a brand-new bar for a course already in the server's
    // post-complete 15 s grace window (running=0 && queued=0).
    if (!hasWork) return;
    // Suppress the course-level aggregate when a project/team sync row for
    // this same course is already tracked (avoids duplicate bars).
    if (_hasScopedSyncForCourse(courseId)) return;
    // Respect an active dismissal for the current run; `_isDismissed`
    // auto-clears when the server reports a fresher start_at.
    if (_isDismissed(String(courseId), Number(c.started_at_ms) || 0)) {
      return;
    }
    const label = c.code || c.name || t('Course');
    const msg = _courseSyncMsg(label, c.running, c.queued, c.synced_groups, c.total_groups);
    showGlobalJob(msg, courseId, {
      jobKind: 'course_sync',
      courseName: label,
      startedAt: Number(c.started_at_ms) || undefined,
    });
    if (_globalJobs[courseId]) {
      _globalJobs[courseId].serverConfirmedRunning = true;
    }
  });

  // Finalize course-sync jobs that the server reports as idle.
  // The server only keeps a course in /sync/active when it has running,
  // queued, OR very-recently-completed (<15 s) jobs.  When the client
  // sees entry.running=0 AND entry.queued=0, every tracked job already
  // completed - the course is only still in the list due to the server's
  // 15 s grace window.  Finalize immediately so the bar doesn't linger
  // stuck at e.g. 89 % showing "0 running, 0 queued".  If a new batch
  // gets enqueued after this, the next reconcile creates a fresh bar.
  const now = _now();
  Object.keys(_globalJobs).forEach((jt) => {
    const job = _globalJobs[jt];
    if (!job || job.meta?.jobKind !== 'course_sync') return;
    if (job.status === 'done' || job.status === 'error') return;
    const entry = activeSet.get(String(jt));
    const entryHasWork = entry
      && ((Number(entry.running) || 0) + (Number(entry.queued) || 0) > 0);
    if (entryHasWork) {
      job.serverMissingSince = 0;
      return;
    }
    // Server reports idle or missing - only finalize if we previously
    // confirmed the sync was actually running (avoids killing an
    // optimistic bar for a job that hasn't shown up server-side yet).
    if (!job.serverConfirmedRunning) return;
    if (job.cancelRequested === true) {
      completeGlobalJob(jt, t('Process cancelled.'), 'error');
      return;
    }
    if (entry) {
      // Present but idle -> inside server's 15 s grace window.  DO NOT
      // finalize here - this races with a fresh user-initiated sync:
      // if the user clicks "Sync All" while a previous run is still in
      // its 15 s grace window, /sync/active reports running=0,queued=0
      // for ~1 s until the new BackgroundJob rows are committed, and
      // an early watchdog tick would fire a phantom "Sync completed!"
      // toast right after the click.  The per-bar SSE stream handles
      // real completion via its own 6 s inactive debounce, which
      // correctly waits past both the grace window and any fresh
      // enqueue race.  Just keep `serverMissingSince` cleared so the
      // missing-from-active branch below doesn't fire prematurely.
      job.serverMissingSince = 0;
      return;
    }
    // Missing from active set: small client-side grace in case of a
    // transient /sync/active hiccup.
    const MISSING_GRACE_MS = 10000;
    if (!job.serverMissingSince) {
      job.serverMissingSince = now;
      return;
    }
    if (now - job.serverMissingSince >= MISSING_GRACE_MS) {
      completeGlobalJob(jt, t('Sync completed'), 'done');
    }
  });
}

window.addEventListener('beforeunload', () => {
  _deferredJobs.clear();

  // Clean up timers to prevent leaks in SPA-like scenarios
  if (_elapsedTimerId) { clearInterval(_elapsedTimerId); _elapsedTimerId = null; }
  if (_syncWatchdogId) { clearInterval(_syncWatchdogId); _syncWatchdogId = null; }

  // Drop finished jobs whose completion-display window has already
  // elapsed - they shouldn't reappear as stale "running" bars on the
  // next page. Recently-completed bars (still within the auto-hide
  // window) are preserved so that a navigation during the 5 s grace
  // shows the terminal 100 % state on the next page instead of
  // disappearing mid-transition.
  const _now_ = _now();
  Object.entries(_globalJobs).forEach(([jobType, job]) => {
    if (job.status !== 'done' && job.status !== 'error') return;
    const completedAt = job.completedAt || job.startedAt || 0;
    const ttl = job.status === 'error'
      ? AUTO_HIDE_ERROR_MS + ANIMATION_EXIT_FALLBACK_MS
      : AUTO_HIDE_SUCCESS_MS + ANIMATION_EXIT_FALLBACK_MS;
    if (_now_ - completedAt > ttl) {
      delete _globalJobs[jobType];
    }
  });

  _saveGlobalJobs();
});

_loadDismissedJobs();

// Initialize as early as possible - restoreGlobalJobBar() itself awaits
// /sync/active before rendering any course-sync bar, so there's no risk
// of flashing stale cache before the server confirms.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', restoreGlobalJobBar);
} else {
  restoreGlobalJobBar();
}



// After HTMX finishes settling the new page (post-transition, post-
// loader), re-render the bar so it reflects the new
// DOM context.  Coalesce bursts: htmx:afterSettle fires for the outer
// swap and htmx:load fires once per swapped element (including nested
// lazy-loaded fragments) - without throttling that could fire
// /sync/active 5+ times per navigation.  We listen on both events
// (htmx:load handles nested lazy loads) but keep a 1.5s debounce so
// only one network round-trip is issued per logical page change.
let _htmxSettleTimer = null;
const _SYNC_ACTIVE_MIN_INTERVAL_MS = 1500;
function _onHtmxNavigated() {
  if (_htmxSettleTimer) clearTimeout(_htmxSettleTimer);
  _htmxSettleTimer = setTimeout(() => {
    _htmxSettleTimer = null;
    _renderGlobalBar();
    const now = Date.now();
    if (now - _lastSyncActiveAt < _SYNC_ACTIVE_MIN_INTERVAL_MS) return;
    // Same flicker guard as the periodic watchdog: a navigation right
    // after a completion shouldn't re-add the just-faded bar.
    if (_lastCompletionAt
      && (now - _lastCompletionAt) < POST_COMPLETION_RECONCILE_SUPPRESS_MS) {
      return;
    }
    _lastSyncActiveAt = now;
    _fetchActiveSyncs().then(_reconcileCourseJobs).catch(() => { /* ignore */ });
  }, 250);
}
document.addEventListener('htmx:afterSettle', _onHtmxNavigated);
document.addEventListener('htmx:load', _onHtmxNavigated);

/* Storage events and focus restoration use the same transition rules.
   A missing storage row means dismissed/expired, never successful execution. */
function _mergeStoredJobs(remote) {
  Object.entries(remote).forEach(([jobType, value]) => {
    if (!value || !Number.isFinite(value.startedAt)
        || !['running', 'finishing', 'done', 'error'].includes(value.status)) return;
    let job = _globalJobs[jobType];
    const sameId = job?.meta?.jobId && job.meta.jobId === value.meta?.jobId;
    if (job && value.startedAt < job.startedAt && !sameId) return;
    if (job && value.startedAt > job.startedAt && !sameId) {
      _stopPoller(jobType);
      _clearHideTimer(jobType);
      _clearConnectingTimer(jobType);
      delete _globalJobs[jobType];
      job = null;
    }
    if (!job) {
      if (_isUiTerminalStatus(value.status)) return;
      job = _ensureJob(jobType, value.message, value.meta);
      job.startedAt = value.startedAt;
    }
    job.meta = { ...(job.meta || {}), ...(value.meta || {}) };
    if (_isUiTerminalStatus(value.status)) {
      completeGlobalJob(jobType, value.message || job.message, value.status);
      return;
    }
    if (_isUiTerminalStatus(job.status)) return;
    job.status = value.status;
    job.message = value.message || job.message;
    job.progress = value.status === 'finishing' ? null : (value.progress ?? null);
    job.cancelRequested = value.cancelRequested === true;
    job.lastUpdate = value.lastUpdate || _now();
    if (!job.pollTimerId && !job.poller) _autoStartPolling(jobType);
  });
  Object.entries(_globalJobs).forEach(([jobType, job]) => {
    if (!remote[jobType] && _isUiTerminalStatus(job.status)) hideGlobalJob(jobType);
  });
  _renderGlobalBar();
}

window.addEventListener('storage', (event) => {
  if (event.key !== GLOBAL_JOB_KEY) return;
  try {
    const remote = event.newValue ? JSON.parse(event.newValue) : {};
    if (remote && typeof remote === 'object' && !Array.isArray(remote)) _mergeStoredJobs(remote);
  } catch (_) { /* Invalid storage does not change running work. */ }
});

// -- Auto-refresh and Reconcile on tab re-focus --
// When user returns to a tab, flush auto-hidden jobs, flush queued toasts,
// re-check job status, restart lost polling, and dispatch tab-visibility event.
let _lastVisibleSnapshot = '';

function _jobSnapshot() {
  // Create a lightweight fingerprint of current job states
  const parts = Object.entries(_globalJobs)
    .map(([k, j]) => k + ':' + (j.status || 'running'))
    .sort();
  return parts.join(',');
}

_lastVisibleSnapshot = _jobSnapshot();

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    _stopAllPollers();
    if (_syncWatchdogId) {
      clearInterval(_syncWatchdogId);
      _syncWatchdogId = null;
    }
    return;
  }

  // 1. Flush any completed jobs whose auto-hide deadline elapsed while the tab
  // was hidden (background-tab setTimeout throttling can delay the original
  // hide timer by minutes). Without this the user comes back to a stale
  // "Sync completed" banner with a runaway elapsed counter.
  const now = Date.now();
  Object.entries(_globalJobs).forEach(([jobType, job]) => {
    if (!job) return;
    const terminal = job.status === 'done' || job.status === 'error';
    if (!terminal) return;
    if (typeof job.hideAt === 'number' && now >= job.hideAt) {
      _clearHideTimer(jobType);
      const { content } = _barElements();
      const item = content ? content.querySelector(`[data-job-id="${CSS.escape(jobType)}"]`) : null;
      if (item) {
        _animateJobExit(item, jobType);
      } else {
        hideGlobalJob(jobType);
      }
    }
  });

  // 2. Flush any toasts that were queued while the tab was hidden
  if (_queuedToasts.length && !_suppressToasts) {
    const pending = _queuedToasts.splice(0);
    pending.forEach(({ msg, type, status: s, jobType: jt, _skipBroadcast: sb }) => {
      if (jt && _completionAlreadyShown(jt, s)) return;
      if (typeof flashToast === 'function') flashToast(msg, type, s === 'error' ? 10000 : 5000);
      if (jt) _markCompletionShown(jt, s);
      if (!sb && typeof broadcastToast === 'function') broadcastToast(msg, type);
    });
  }

  // Recover changes missed while the tab was suspended through the same path.
  try {
    const stored = JSON.parse(localStorage.getItem(GLOBAL_JOB_KEY) || '{}');
    if (stored && typeof stored === 'object' && !Array.isArray(stored)) _mergeStoredJobs(stored);
  } catch (_) { /* Keep the last verified state. */ }

  // 4. Restart polling for jobs that lost their connection while hidden.
  // Only restart if there is no active poller - preserve healthy SSE connections.
  Object.entries(_globalJobs).forEach(([jobType, job]) => {
    if (job.status && job.status !== 'done' && job.status !== 'error') {
      if (!job.pollTimerId && !job.poller) {
        _autoStartPolling(jobType);
      }
    }
  });

  // 5. Only dispatch refresh event if job states actually changed
  const newSnapshot = _jobSnapshot();
  if (newSnapshot !== _lastVisibleSnapshot) {
    _lastVisibleSnapshot = newSnapshot;
    document.dispatchEvent(new CustomEvent('gp-tab-visible', { detail: { changed: true } }));
  }

  // 6. Verify active syncs and update the bar without waiting for the 30s watchdog.
  _fetchActiveSyncs().then(_reconcileCourseJobs).catch(() => { /* ignore */ });
  _startSyncWatchdog();
});

// Compatibility for page scripts that read these internals directly.
window._globalJobs = _globalJobs;
window._deferredJobs = _deferredJobs;

window.showGlobalJob = showGlobalJob;
window.connectGlobalJob = connectGlobalJob;
window.failGlobalJob = failGlobalJob;
window.updateGlobalJob = updateGlobalJob;
window.updateGlobalJobProgress = updateGlobalJobProgress;
window.setGlobalJobMeta = setGlobalJobMeta;
window.completeGlobalJob = completeGlobalJob;
window.cancelGlobalJob = _cancelGlobalJob;
window.hideGlobalJob = hideGlobalJob;
window.isGlobalJobRunning = isGlobalJobRunning;
window.confirmProcessRestart = confirmProcessRestart;
window.deferGlobalJob = deferGlobalJob;
window.promoteGlobalJob = promoteGlobalJob;
window.startCourseSyncPolling = startCourseSyncPolling;
window.startGenericStatusPolling = startGenericStatusPolling;
window.restoreGlobalJobBar = restoreGlobalJobBar;
window.markCourseSyncFinishing = _markCourseSyncFinishing;
// Exposed so page scripts (dashboard.js, course-detail.js) build the
// SAME message format as the SSE/poll loops here. Avoids per-tick
// flicker between "Syncing CODE: R running, Q queued" and
// "NAME: Syncing X/Y groups done (R active, Q queued)".
window._courseSyncMsg = _courseSyncMsg;
window._courseFinishingMsg = _courseFinishingMsg;

window.GP.globalJobs = {
  showGlobalJob,
  connectGlobalJob,
  failGlobalJob,
  updateGlobalJob,
  updateGlobalJobProgress,
  setGlobalJobMeta,
  completeGlobalJob,
  cancelGlobalJob: _cancelGlobalJob,
  hideGlobalJob,
  dismissGlobalJob,
  isGlobalJobRunning,
  confirmProcessRestart,
  deferGlobalJob,
  promoteGlobalJob,
  startCourseSyncPolling,
  startGenericStatusPolling,
  restoreGlobalJobBar,
  markCourseSyncFinishing: _markCourseSyncFinishing,
};

/* -- React to health-monitor status changes -- */
let _healthPaused = false;

document.addEventListener('gp-health-change', function (e) {
  const detail = e.detail || {};
  const bar = document.getElementById('globalJobBar');
  if (!bar) return;

  if (detail.current === 'down' && !_healthPaused) {
    _healthPaused = true;
    bar.classList.add('gjb-health-down');
    // Pause all active pollers to stop flooding ERR_CONNECTION_REFUSED
    Object.keys(_globalJobs).forEach(function (jt) {
      const job = _globalJobs[jt];
      if (!job || job.status === 'done' || job.status === 'error') return;
      _stopPoller(jt);
      // Append connection-lost indicator to message
      if (!job._savedMessage) {
        job._savedMessage = job.message;
      }
      updateGlobalJob(job._savedMessage + ' - ' + t('connection lost'), jt);
    });
  } else if (detail.current !== 'down' && _healthPaused) {
    _healthPaused = false;
    bar.classList.remove('gjb-health-down');
    // Restore messages and restart polling
    Object.keys(_globalJobs).forEach(function (jt) {
      const job = _globalJobs[jt];
      if (!job || job.status === 'done' || job.status === 'error') return;
      if (job._savedMessage) {
        updateGlobalJob(job._savedMessage, jt);
        delete job._savedMessage;
      }
      _autoStartPolling(jt);
    });
  }
});
