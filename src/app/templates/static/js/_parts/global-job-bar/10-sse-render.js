
function _ensureJob(jobType, message, meta) {
  if (!_globalJobs[jobType]) {
    // New run starting -> drop any stale dedup entries so the next
    // completion produces a fresh toast even if an older run of the
    // same jobType already showed one in this tab session.
    _clearCompletionDedup(jobType);
    _globalJobs[jobType] = {
      message: message || t('Processing...'),
      startedAt: _now(),
      status: 'running',
      progress: null,      // 0-100 determinate progress
      meta: meta || {},
      pollTimerId: null,
      poller: null,
      hideTimerId: null,
    };
  }
  return _globalJobs[jobType];
}

function _courseSyncTerminalStateFromData(data, courseName) {
  const name = courseName ? String(courseName) + ': ' : '';
  const failed = Number(data?.sync_failed_count || 0);
  const cancelled = Number(data?.sync_cancelled_count || 0);
  if (failed > 0) {
    return {
      status: 'error',
      message: name + t('Sync finished with problems') + ' - ' + failed + ' ' + t('group(s) failed') + '.',
    };
  }
  if (cancelled > 0) {
    return {
      status: 'error',
      message: name + t('Sync cancelled') + ' - ' + cancelled + ' ' + t('group(s) cancelled') + '.',
    };
  }
  return { status: 'done', message: t('Sync completed!') };
}

function _autoStartPolling(jobType) {
  if (document.hidden) {
    return;
  }
  // Cross-tab: only the elected leader tab runs the network pollers; followers
  // mirror job state via 'storage' events. Fail-open (a lone tab always leads),
  // so this never stops a single tab from polling. See _isPollLeader().
  if (typeof _isPollLeader === 'function' && !_isPollLeader()) {
    return;
  }
  const job = _globalJobs[jobType];
  if (!job) {
    return;
  }

  // Course-sync job types are either a UUID or a plain numeric course ID
  // (both are used across the codebase - dashboard passes numeric IDs,
  // discovery may return UUIDs). On any page where a course-sync job is
  // restored from localStorage (e.g. Admin -> Users during an active sync
  // started elsewhere) we must resume the SSE stream so the bar updates
  // and eventually completes - otherwise it flashes on load then goes stale.
  if (jobType !== 'sync' && (UUID_LIKE_REGEX.test(jobType) || /^\d+$/.test(jobType) || job.meta?.jobKind === 'course_sync')) {
    startCourseSyncPolling(jobType);
    return;
  }

  if (job.meta?.jobKind === 'team_sync' || job.meta?.jobKind === 'project_sync') {
    const jobId = job.meta?.jobId;
    if (jobId) {
      startGenericStatusPolling(jobType, `/api/v1/jobs/${jobId}`, {
        messageRunning(data) {
          const pct = data?.progress != null ? ` (${Math.round(data.progress)}%)` : '';
          return (data?.message || t('Syncing...')) + pct;
        },
        messageDone(data) {
          return data?.result_summary || t('Sync completed');
        },
        messageFailed(data) {
          return data?.error_message || t('Sync failed');
        },
      });
    }
    return;
  }

  if (jobType === 'enrichment') {
    startGenericStatusPolling('enrichment', '/dashboard/admin/users/enrich-gitlab/status', {
      messageRunning(data) {
        const total = Number(data?.total || 0);
        const processed = Number(data?.processed || 0);
        const pct = total > 0 ? Math.round((processed / total) * 100) : 0;
        // Update determinate progress
        if (_globalJobs.enrichment && pct >= 0) {
          _globalJobs.enrichment.progress = Math.min(pct, 100);
        }
        // Use the backend message directly (shows per-phase details)
        return data?.message || `Enriching: ${processed}/${total || '?'}`;
      },
      messageDone(data) {
        return data?.message || 'Enrichment complete!';
      },
      messageFailed(data) {
        return data?.message || 'Enrichment failed';
      },
    });
    return;
  }

  if (jobType === 'analysis') {
    const pollUrl = job.meta?.pollUrl;
    if (pollUrl) {
      startGenericStatusPolling('analysis', pollUrl, {
        messageRunning(data) {
          // Project publications carry an object plus percent; group snapshots carry a number.
          const raw = typeof data?.progress === 'number' ? data.progress : data?.percent;
          const pct = Number.isFinite(raw) ? Math.max(0, Math.min(100, Math.round(raw))) : null;
          _globalJobs.analysis.progress = pct;
          const progress = pct != null ? ` (${pct}%)` : '';
          const baseMsg = _globalJobs.analysis.meta?.baseMessage || t('Analyzing...');
          return `${baseMsg}${progress}`;
        },
        messageDone() {
          return t('AI Analysis completed!');
        },
        messageFailed(data) {
          return data?.message || t('AI Analysis failed');
        },
      });
    } else {
      updateGlobalJob('Analysis may still be running - check the project page', 'analysis');
    }
    return;
  }

  if (job.meta?.jobKind === 'run_checks' || jobType === 'run_checks') {
    // Prefer pollUrl (from meta) over jobId-based URL for run_checks
    const checkUrl = job.meta?.pollUrl || (job.meta?.jobId ? `/api/v1/jobs/${job.meta.jobId}` : null);
    if (checkUrl) {
      startGenericStatusPolling(jobType, checkUrl, {
        messageRunning(data) {
          if (_globalJobs[jobType] && data?.progress != null) {
            _globalJobs[jobType].progress = Number(data.progress);
          }
          return data?.result_summary || data?.message || t('Running compliance checks...');
        },
        messageDone(data) {
          return data?.result_summary || t('Checks completed!');
        },
        messageFailed(data) {
          return data?.error_message || data?.message || t('Checks failed');
        },
      });
    }
    return;
  }

  if (jobType === 'recheck' || jobType === 'recheck_student') {
    const jobId = job.meta?.jobId;
    if (jobId) {
      startGenericStatusPolling(jobType, `/api/v1/jobs/${jobId}`, {
        messageRunning(data) {
          const pct = data?.progress != null ? ` (${Math.round(data.progress)}%)` : '';
          return (_globalJobs[jobType]?.message || t('Running compliance checks...')) + pct;
        },
        messageDone(data) {
          return data?.result_summary || 'Recheck completed!';
        },
        messageFailed(data) {
          return data?.error_message || 'Recheck failed';
        },
      });
    }
    return;
  }

  if (jobType === 'export') {
    const jobId = job.meta?.jobId;
    if (jobId) {
      startGenericStatusPolling('export', `/api/v1/jobs/${jobId}`, {
        messageRunning(data) {
          const pct = data?.progress != null ? ` (${Math.round(data.progress)}%)` : '';
          return (_globalJobs.export?.message || t('Exporting data...')) + pct;
        },
        messageDone(data) {
          return data?.message || 'Export complete!';
        },
        messageFailed(data) {
          return data?.message || 'Export failed';
        },
      });
    }
    return;
  }

  // -- scheduled_job: manually-triggered sweep jobs from admin panel --
  if (jobType === 'scheduled_job') {
    const jobId = job.meta?.jobId;
    if (jobId) {
      startGenericStatusPolling('scheduled_job', `/api/v1/jobs/${jobId}`, {
        messageRunning(data) {
          return data?.message || _globalJobs.scheduled_job?.message || t('Running scheduled job...');
        },
        messageDone(data) {
          return data?.result_summary || t('Job completed!');
        },
        messageFailed(data) {
          return data?.error_message || t('Job failed');
        },
      });
    }
  }
}

/* ============================================
   Public API
   ============================================ */
function showGlobalJob(message, jobType = 'default', meta = null) {
  // Respect an active dismissal using the startedAt-aware check so we
  // correctly distinguish between a user clicking a button to start a
  // NEW job (startedAt = now, dismissal auto-clears) and the restore /
  // reconcile path re-registering an already-running job after page
  // navigation (startedAt = server enqueued_at <= dismissal time ->
  // dismissal holds).
  //
  // IMPORTANT: on a fresh page load `_globalJobs` is always empty so
  // the previous `!_existing` heuristic treated every restore/reconcile
  // call as a "fresh start" and silently wiped the dismissal, causing
  // the dismissed bar to resurrect on every navigation. Trust the
  // startedAt metadata instead.
  //
  // Passive reconcile callers (e.g. dashboard._registerCourseCardSyncs
  // runs on every dashboard visit for every in-progress course sync)
  // don't know the real startedAt. Treat them as startedAt=0 so
  // `_isDismissed` cannot auto-clear via the `startedAt > timestamp`
  // rule - a dismissed run must stay dismissed across navigation, even
  // if the user returns to a page that re-registers it.
  const incomingStartedAt = (meta && typeof meta.startedAt === 'number')
    ? meta.startedAt
    : (meta?.passive ? 0 : _now());
  if (_isDismissed(jobType, incomingStartedAt)) {
    return;
  }

  // If the job already exists but was completed/errored or reached 100%,
  // reset it for a fresh run - otherwise stale progress is preserved and
  // the monotonic guard prevents it from ever going back down.
  const prev = _globalJobs[jobType];
  if (prev && (prev.status === 'done' || prev.status === 'error' || prev.progress >= 100)) {
    prev.progress = null;
    // Do NOT blindly bump startedAt to now(): a long-running sync-all
    // transiently flips to "done"/100% between batches, and passive
    // reconcilers (dashboard card re-scan, /sync/active poll) then
    // re-register the SAME run via this path. Bumping startedAt restarted
    // the elapsed counter on every such tick ("time constantly resets").
    // Prefer an authoritative server start time (meta.startedAt from
    // /sync/active) when present, but never move the start forward; only
    // fall back to now() when we have no prior start at all. A genuine new
    // user-initiated run sets its own startedAt via connectGlobalJob().
    if (typeof incomingStartedAt === 'number' && incomingStartedAt > 0) {
      prev.startedAt = prev.startedAt
        ? Math.min(prev.startedAt, incomingStartedAt)
        : incomingStartedAt;
    } else {
      prev.startedAt = prev.startedAt || _now();
    }
  }

  const job = _ensureJob(jobType, message, meta || {});
  // Anchor the elapsed timer to the server-authoritative start time when
  // one is supplied (meta.startedAt from /sync/active's started_at_ms).
  // _ensureJob stamps startedAt=now() for a freshly created bar, so on a
  // page navigation the reconcile that recreates a course-sync bar would
  // otherwise reset the elapsed counter to ~0 on every navigation. Never
  // move the start forward - keep the earliest known start so the timer
  // stays monotonic across navigations and between-batch re-registrations.
  if (meta && typeof meta.startedAt === 'number' && meta.startedAt > 0) {
    job.startedAt = job.startedAt
      ? Math.min(job.startedAt, meta.startedAt)
      : meta.startedAt;
  }
  job.message = message || job.message || t('Processing...');
  job.status = 'running';
  // Promotion out of the optimistic "connecting" phase (connectGlobalJob):
  // a real server-confirmed run is now starting, so drop the placeholder
  // phase and cancel its safety-net timeout.
  delete job.phase;

  _clearConnectingTimer(jobType);
  _restoredJobs.delete(jobType);  // no longer a restored-from-storage job
  // A freshly started job (user clicked a button) is, by definition, active
  // - mark as server-confirmed so any subsequent racy 'complete' event
  // during the initial restore window can't silently kill the bar.
  job.serverConfirmedRunning = true;
  if (meta) {
    job.meta = { ...(job.meta || {}), ...meta };
  }

  _clearHideTimer(jobType);

  // Deduplication: watch for a local progress indicator and defer if visible
  const localSel = meta?.localIndicatorSelector || _DEFAULT_LOCAL_SELECTORS[jobType];
  if (localSel) {
    _watchLocalIndicator(jobType, localSel);
  }

  _renderGlobalBar();
  _saveGlobalJobs();

  // Notify listeners (e.g. dashboard.js injects an inline course-card
  // badge so the global bar can be deferred to it without flashing on
  // screen first).  Mirrors the gp:job-update event but fires on the
  // initial show too, where updateGlobalJob has not yet been called.
  window.dispatchEvent(new CustomEvent('gp:job-update', {
    detail: { jobType, message: job.message, progress: job.progress },
  }));

  if (!job.pollTimerId && !job.poller) {
    _autoStartPolling(jobType);
  }
}

/**
 * Show an INSTANT, indeterminate "connecting" bar the moment a user clicks
 * a trigger button - BEFORE the backend POST resolves.
 *
 * Why: the bar previously appeared only AFTER the POST returned. With the
 * GitLab reachability pre-flight (which retries and can take several
 * seconds), the user saw nothing during that window and could re-click the
 * button. This surfaces immediate feedback ("Connecting...") and, crucially,
 * makes isGlobalJobRunning(jobType) true right away so the existing
 * re-click guards (confirmProcessRestart / guardProcessAction) block double
 * submits while the request is in flight.
 *
 * The connecting job:
 *   - renders an indeterminate spinner (progress = null, no %)
 *   - does NOT start polling (there is no server job yet)
 *   - auto-fails after a timeout if the caller never promotes/cancels it,
 *     so an unexpected throw can never leave a phantom spinner hanging
 *
 * Lifecycle from the caller:
 *   connectGlobalJob(jobKey, t('Connecting...'), meta)   // on click
 *   -> on success: showGlobalJob()/deferGlobalJob()     // promote
 *   -> nothing to do: hideGlobalJob(jobKey)             // cancel
 *   -> on failure: failGlobalJob(jobKey, msg)           // error in bar
 */
function connectGlobalJob(jobType = 'default', message = '', meta = null) {
  const startedAt = _now();
  // A fresh user-initiated click always starts a new run: clear any stale
  // dismissal so the bar is allowed to appear...
  if (_dismissedJobs[jobType]) {
    delete _dismissedJobs[jobType];
    _saveDismissedJobs();
  }
  // ...and clear the completion dedup so the next success/error toast fires
  // even if a prior run already showed one for this jobType this session.
  _clearCompletionDedup(jobType);

  const label = message || t('Connecting...');
  const job = _ensureJob(jobType, label, meta || {});
  job.message = label;
  job.status = 'running';
  job.phase = 'connecting';
  job.progress = null;            // indeterminate spinner, no %
  job.startedAt = startedAt;
  // Deliberately leave serverConfirmedRunning falsy: the job is NOT yet
  // enqueued server-side, so the /sync/active reconciler must NOT treat it
  // as a confirmed run (otherwise a course missing from /sync/active for
  // 10s would be finalized as "Sync completed" before the POST returns).
  // showGlobalJob()/updateGlobalJob() set it true once the run is real.
  job.serverConfirmedRunning = false;
  if (meta) {
    job.meta = { ...(job.meta || {}), ...meta };
  }

  _clearHideTimer(jobType);
  _clearConnectingTimer(jobType);

  // Safety net: if the caller never promotes or cancels this connecting job
  // (e.g. an unexpected throw before failGlobalJob), auto-surface an error
  // so the spinner can't hang forever.
  const timeoutMs = (meta && typeof meta.connectTimeoutMs === 'number')
    ? meta.connectTimeoutMs
    : 30000;
  _connectingTimers[jobType] = setTimeout(() => {
    const j = _globalJobs[jobType];
    if (j && j.phase === 'connecting' && j.status === 'running') {
      completeGlobalJob(jobType, t('Request timed out - please retry'), 'error');
    }
  }, timeoutMs);

  _renderGlobalBar();
  _saveGlobalJobs();

  window.dispatchEvent(new CustomEvent('gp:job-update', {
    detail: { jobType, message: job.message, progress: null },
  }));
}

/**
 * Surface an error for a job IN THE BAR (works whether it is still in the
 * connecting phase or already running). Thin wrapper over
 * completeGlobalJob(..., 'error') so trigger sites can report failures in
 * the global bar, not only via a transient toast.
 */
function failGlobalJob(jobType = 'default', message = '') {
  _clearConnectingTimer(jobType);
  if (!_globalJobs[jobType]) {
    return;
  }
  completeGlobalJob(jobType, message || t('Failed'), 'error');
}

function updateGlobalJob(message, jobType = 'default') {
  if (!_globalJobs[jobType]) {
    return;
  }

  // Never reset a completed/failed job back to running - that causes race
  // conditions where a late-arriving poll response resurrects a finished bar.
  const _st = _globalJobs[jobType].status;
  if (_st === 'done' || _st === 'error') {
    return;
  }

  _globalJobs[jobType].message = message || _globalJobs[jobType].message;
  _globalJobs[jobType].lastUpdate = _now();

  // Real progress arrived: promote out of the optimistic "connecting" phase
  // and cancel its safety-net timeout so it can't false-error a long run.
  if (_globalJobs[jobType].phase === 'connecting') {
    delete _globalJobs[jobType].phase;
    _clearConnectingTimer(jobType);
  }

  _clearHideTimer(jobType);
  _renderGlobalBar();
  _saveGlobalJobs();

  window.dispatchEvent(new CustomEvent('gp:job-update', {
    detail: {
      jobType,
      message: _globalJobs[jobType].message,
      progress: _globalJobs[jobType].progress,
    },
  }));
}

/**
 * Update determinate progress (0-100) and optionally message/ETA.
 */
function updateGlobalJobProgress(jobType, progress, message) {
  const job = _globalJobs[jobType];
  if (!job) return;
  if (job.status === 'done' || job.status === 'error') return;

  const pct = Math.max(0, Math.min(100, Number(progress) || 0));
  job.progress = pct;
  if (message) job.message = message;
  if (job.phase === 'connecting') {
    delete job.phase;
    _clearConnectingTimer(jobType);
  }
  _renderGlobalBar();
  _saveGlobalJobs();
}

/**
 * Attach metadata (viewUrl, retryFn, etc.) to a running job.
 */
function setGlobalJobMeta(jobType, meta) {
  const job = _globalJobs[jobType];
  if (!job) return;
  job.meta = { ...(job.meta || {}), ...meta };
  _renderGlobalBar();
  _saveGlobalJobs();
}

function completeGlobalJob(jobType = 'default', message = '', status = 'done') {
  const job = _globalJobs[jobType];
  if (!job) {
    return false;
  }

  // Idempotency guard: prevent duplicate toasts when both SSE and polling
  // (or cross-tab storage events) detect the same completion.
  if (job.status === 'done' || job.status === 'error') {
    return true;
  }

  delete _dismissedJobs[jobType];
  _saveDismissedJobs();

  _stopPoller(jobType);
  _clearHideTimer(jobType);

  _clearConnectingTimer(jobType);
  _restoredJobs.delete(jobType);

  // Capture whether a local inline indicator is currently visible BEFORE
  // _renderGlobalBar may re-defer this job. Used to route completion toast
  // and control auto-hide.
  const _localSel = job.meta?.localIndicatorSelector || _DEFAULT_LOCAL_SELECTORS[jobType];
  let _hasVisibleLocal = false;
  if (_localSel) {
    const _el = document.querySelector(_localSel);
    _hasVisibleLocal = !!(_el && !_el.hidden && _el.offsetParent !== null);
  }

  job.status = status === 'error' ? 'error' : 'done';
  job.progress = status === 'error' ? job.progress : 100;
  job.completedAt = _now();
  _lastCompletionAt = job.completedAt;
  if (message) {
    job.message = message;
  }

  _renderGlobalBar();
  _saveGlobalJobs();

  // Always force the completion toast - _renderGlobalBar() may have
  // re-deferred the job via the synchronous local-indicator recheck,
  // which would incorrectly suppress the toast.
  _showCompletionToast(jobType, message, job.status, _hasVisibleLocal, true);
  if (!_hasVisibleLocal) {
    _scheduleAutoHide(jobType, job.status);
  }

  window.dispatchEvent(new CustomEvent('gp:job-complete', {
    detail: { jobType, message, status: job.status, meta: job.meta || {} },
  }));

  // Synchronously refresh process-action guards so buttons that were locked
  // for this job are unlocked IMMEDIATELY  -  before any caller's subsequent
  // setButtonLoading(btn, false) runs. The previous flow deferred this via
  // setTimeout(fn, 0) (from the gp:job-complete listener), which created a
  // race: setButtonLoading(false) saw processLocked=1 (set by the deferred
  // guard refresh from the earlier gp:job-update) and kept the button
  // permanently disabled.
  if (typeof GP.refreshProcessActionGuards === 'function') {
    GP.refreshProcessActionGuards();
  }

  return true;
}

function hideGlobalJob(jobType = null) {
  if (!jobType) {
    _stopAllPollers();
    Object.keys(_globalJobs).forEach((key) => {
      _clearConnectingTimer(key);

      _unwatchLocalIndicator(key);
      _clearHardSuppress(key);
      delete _globalJobs[key];
    });
    _deferredJobs.clear();
    _renderGlobalBar();
    _saveGlobalJobs();
    return;
  }

  if (!_globalJobs[jobType]) {
    return;
  }

  _stopPoller(jobType);
  _clearHideTimer(jobType);

  _clearConnectingTimer(jobType);
  _unwatchLocalIndicator(jobType);
  _clearHardSuppress(jobType);
  delete _globalJobs[jobType];
  _deferredJobs.delete(jobType);

  _renderGlobalBar();
  _saveGlobalJobs();
}

function dismissGlobalJob(jobType) {
  if (jobType) {
    _dismissedJobs[jobType] = _now();
    _saveDismissedJobs();
  }

  // If the sync is STILL RUNNING, the X only hides the progress UI - the
  // job keeps running on the server.  Deleting it from _globalJobs (via
  // hideGlobalJob) would release the process-action locks and wrongly
  // re-enable the Sync / Run Checks / Unlink / Delete buttons mid-sync,
  // and would stop the poller so completion is never observed.  Instead
  // keep the job active (locks stay on, poller keeps tracking) but
  // suppress it from the bar.  It is removed normally once it finishes.
  // Finishing remains active until the server confirms its terminal state.
  const _dismissed = jobType ? _globalJobs[jobType] : null;
  if (_dismissed && _dismissed.status !== 'done' && _dismissed.status !== 'error') {
    _hardSuppressedJobs.set(jobType, null);
    const { content } = _barElements();
    const item = content
      ? content.querySelector(`[data-job-id="${CSS.escape(jobType)}"]`)
      : null;
    if (item && item.parentNode) item.remove();
    _renderGlobalBar();
    return;
  }

  // Completed / errored job: animate the item out and remove it entirely.
  const { content } = _barElements();
  if (content && jobType) {
    const item = content.querySelector(`[data-job-id="${CSS.escape(jobType)}"]`);
    if (item) {
      _animateJobExit(item, jobType);
      // Fallback if animation event doesn't fire
      return;
    }
  }

  hideGlobalJob(jobType);
}

function isGlobalJobRunning(jobType) {
  const job = _globalJobs[jobType];
  return Boolean(job && job.status !== 'done' && job.status !== 'error');
}

/* Async because it asks on the app's own dialog now, not the browser's blocking
   `window.confirm`. Every call site already sits in an async function, so they
   just `await` it. */
async function confirmProcessRestart(jobType, processLabel = 'A process') {
  if (!isGlobalJobRunning(jobType)) {
    return true;
  }

  const elapsed = _fmtElapsed(_now() - _globalJobs[jobType].startedAt);
  const ok = await GP.confirmDialog({
    title: t('Process already running'),
    message: t('{label} is already running ({elapsed}). Do you want to cancel it? Start the new process after it stops.')
      .replace('{label}', processLabel).replace('{elapsed}', elapsed),
    confirmText: t('Confirm'),
    variant: 'warning',
  });
  if (ok) {
    const job = _globalJobs[jobType];
    if (typeof _cancelGlobalJob === 'function' && _isJobCancellable(jobType, job)) {
      _cancelGlobalJob(jobType, { confirm: false });
    } else {
      updateGlobalJob(t('Cancellation is not available for this process.'), jobType);
      if (typeof showToast === 'function') {
        showToast(t('Cancellation is not available for this process.'), 'warning');
      }
    }
  }
  return false;
}

function deferGlobalJob(message, jobType = 'default', meta = null) {
  // Explicitly clear any stale dismissal - the caller is starting a new
  // job (user clicked a button).  Without this, closing a previous bar
  // for the same jobType silently suppresses every future start for 15 min.
  //
  // EXCEPTION: passive reconcilers (dashboard course-card sync registry,
  // team-detail analysis-on-reload probe) re-call deferGlobalJob on every
  // page load for already-running jobs.  They must NOT clear a dismissal
  // set by the user on a previous page - otherwise the bar resurrects on
  // every navigation that touches those pages.
  if (!meta?.passive && _dismissedJobs[jobType]) {
    delete _dismissedJobs[jobType];
    _saveDismissedJobs();
  }

  // When a caller explicitly specifies a `localIndicatorSelector`, it is
  // asserting "this page owns the UI for this job - defer the global bar".
  // Previously we only deferred if the selector matched an already-visible
  // element, which caused a micro-flash of the global bar whenever the
  // indicator was created asynchronously (e.g. SSE card rendered a few
  // frames after the API call returned).  Trust the caller: defer
  // immediately and rely on MutationObserver / a safety timeout to un-defer
  // if the indicator truly never appears.
  const localSel = (meta && meta.localIndicatorSelector) || _DEFAULT_LOCAL_SELECTORS[jobType] || null;
  const localEl = localSel ? document.querySelector(localSel) : null;

  if (localSel) {
    _deferredJobs.add(jobType);
    // Page JS has taken ownership - drop the meta pre-defer flag so the
    // normal revalidator can take over from here on.
    _metaDeferredJobs.delete(jobType);
    if (localEl) {
      // Local indicator already rendered - no suppression needed,
      // defer alone is sufficient.
      _clearHardSuppress(jobType);
      // Already in DOM - hand off to IntersectionObserver for
      // scroll-based un-defer when it leaves the viewport.
      _watchLocalIndicator(jobType, localSel);
    } else {
      // Local indicator not yet rendered (typical case: the user just
      // clicked a button and the page JS will insert the inline card
      // on the next SSE tick or POST response).  Hard-suppress the bar
      // for up to 5 s so the user NEVER sees a transient global bar
      // flash while the local card is being created.  If the local
      // card appears sooner, the normal defer + IntersectionObserver
      // takes over without any visual change.
      _hardSuppress(jobType, 5000);
      _watchForLocalIndicatorAppearance(jobType, localSel);
      setTimeout(() => {
        if (!_globalJobs[jobType]) return;
        if (_globalJobs[jobType].status === 'done' || _globalJobs[jobType].status === 'error') return;
        if (document.querySelector(localSel)) return;  // indicator arrived
        if (_localIndicators[jobType]) return;  // already handed off to IntersectionObserver
        // Indicator never appeared - un-defer so the global bar surfaces.
        _deferredJobs.delete(jobType);
        _renderGlobalBar();
      }, 15000);
    }
  }

  // Passive reconcilers (dashboard re-scans for already-running syncs on
  // every boot tick + htmx:afterSettle + gp:job-update) must NOT overwrite
  // the live SSE-driven message on the existing job - that caused a
  // flicker where the badge text flipped between the stale page-render
  // string ("Syncing data: 4 running, 1 queued") and the real SSE
  // string ("Syncing: 4/9 groups done (4 active, 1 queued)") several
  // times per second.  When passive, only refresh meta and re-render;
  // the defer flag + IntersectionObserver were already set above.
  const existing = _globalJobs[jobType];
  if (meta?.passive && existing && existing.status === 'running' && existing.message) {
    if (meta) {
      existing.meta = { ...(existing.meta || {}), ...meta };
    }
    // CRITICAL: passive reconcilers skip showGlobalJob -> which means
    // _autoStartPolling is never called for an SSE-restored job.
    // Without an active SSE/poller, `job.lastUpdate` stops being
    // refreshed and the 1 s staleness guard fires "Process timed
    // out - check results manually" after _jobMaxAge - even though
    // the server is still actively syncing.  Kick off polling here
    // if it isn't already running.
    if (!existing.pollTimerId && !existing.poller) {
      _autoStartPolling(jobType);
    }
    _renderGlobalBar();
    return;
  }

  const enrichedMeta = { ...(meta || {}), baseMessage: message };
  showGlobalJob(message, jobType, enrichedMeta);
}

function _watchForLocalIndicatorAppearance(jobType, selector) {
  // Cancel any previous watcher for this jobType
  if (_pendingLocalWatchers[jobType]) {
    try { _pendingLocalWatchers[jobType].disconnect(); } catch (_) { /* noop */ }
    delete _pendingLocalWatchers[jobType];
  }
  if (!document.body) return;
  const mo = new MutationObserver(() => {
    // If the job has ended, stop watching
    if (!_globalJobs[jobType]) {
      try { mo.disconnect(); } catch (_) { /* noop */ }
      delete _pendingLocalWatchers[jobType];
      return;
    }
    const el = document.querySelector(selector);
    if (el) {
      try { mo.disconnect(); } catch (_) { /* noop */ }
      delete _pendingLocalWatchers[jobType];
      // Local indicator is now in DOM - clear the hard-suppression
      // (defer alone is enough) and hand off to the regular
      // IntersectionObserver for scroll-based un-defer.
      _clearHardSuppress(jobType);
      _watchLocalIndicator(jobType, selector);
    }
  });
  mo.observe(document.body, { childList: true, subtree: true });
  _pendingLocalWatchers[jobType] = mo;
  // Safety timeout - stop watching after 2 minutes
  setTimeout(() => {
    if (_pendingLocalWatchers[jobType] === mo) {
      try { mo.disconnect(); } catch (_) { /* noop */ }
      delete _pendingLocalWatchers[jobType];
    }
  }, 120000);
}

function promoteGlobalJob(jobType) {
  if (!jobType) {
    return;
  }

  _deferredJobs.delete(jobType);
  _renderGlobalBar();

  if (_globalJobs[jobType] && !_globalJobs[jobType].pollTimerId && !_globalJobs[jobType].poller) {
    _autoStartPolling(jobType);
  }
}

/**
 * Build a single, consistent course-sync status message.
 * One format for every code path (SSE, legacy poll, page-load reconciler,
 * watchdog reconciler) so the global job bar never flickers between
 * "Syncing CODE: R running, Q queued" and "NAME: Syncing X/Y groups done".
 *
 * Format: "<name>: Syncing X/Y groups done (R active, Q queued)"
 *  - name prefix is optional
 *  - "X/Y groups done" only included when synced/total are known (>0)
 *  - "(R active, Q queued)" only included when there is work in flight
 * @private
 */
function _courseSyncMsg(name, running, queued, synced, total) {
  const r = Number(running) || 0;
  const q = Number(queued) || 0;
  const s = synced != null ? Number(synced) : null;
  const tot = total != null ? Number(total) : null;
  const prefix = name ? (name + ': ') : '';
  // When we have no numbers at all yet (page-load placeholder, modal
  // close before SSE has fired) emit a clean unified "<name>: Syncing..."
  // line instead of the older "Syncing data..." literal - this avoids
  // the visual flicker where the bar showed "Syncing data..." and was
  // then immediately overridden by the real "Syncing: X/Y groups done".
  const hasProgress = (s != null && tot != null && tot > 0);
  const hasFlight = (r > 0 || q > 0);
  if (!hasProgress && !hasFlight) {
    return prefix + t('Syncing...');
  }
  let msg = prefix + t('Syncing:');
  if (hasProgress) {
    msg += ` ${s}/${tot} ` + t('groups done');
  }
  if (hasFlight) {
    msg += ` (${r} ` + t('active') + `, ${q} ` + t('queued') + ')';
  }
  return msg;
}

function _courseFinishingMsg(name) {
  return (name ? name + ': ' : '') + t('Finishing...');
}

function _markCourseSyncRunning(jobType) {
  const job = _globalJobs[jobType];
  if (!job) {
    return;
  }
  if (job.status === 'finishing') {
    job.status = 'running';
  }

}

/* All groups may be idle while the server verifies the course run.
   Keep tracking it until a terminal snapshot/event; elapsed time is not proof. */
function _markCourseSyncFinishing(jobType, message) {
  const job = _globalJobs[jobType];
  if (!job || _isUiTerminalStatus(job.status)) return;
  job.status = 'finishing';
  job.progress = null;
  job.message = message || t('Finishing...');
  job.lastUpdate = _now();
  job.serverConfirmedRunning = true;
  _renderGlobalBar();
  _saveGlobalJobs();
  window.dispatchEvent(new CustomEvent('gp:job-update', {
    detail: { jobType, message: job.message, progress: job.progress, status: job.status },
  }));
}

function startCourseSyncPolling(courseId) {
  if (!_globalJobs[courseId]) {
    return;
  }

  // Idempotency guard: dashboard.js calls _registerCourseCardSyncs from
  // _boot, three setTimeout retries (100/500/1500 ms), and on every
  // htmx:afterSettle.  Without this guard each call would tear down the
  // active EventSource and open a fresh one, producing N-1 (canceled)
  // network requests per page load.  If we already have a live poller,
  // leave it running.
  if (_globalJobs[courseId].poller) {
    return;
  }

  _stopPoller(courseId);

  // Open SSE directly - the stream is the authoritative source of
  // sync state.  A previous design did an HTTP /sync-status probe
  // here first, but that doubled the request count on every page
  // load and added latency; the stream's first data frame gives us
  // the same information and the server's debounced `complete`
  // event handles the terminal case correctly.
  _beginCourseSyncSse(courseId);
}

function _beginCourseSyncSse(courseId) {
  if (!_globalJobs[courseId]) return;

  // Use SSE stream for course sync status (replaces old setInterval polling)
  const sseUrl = `/api/v1/courses/${courseId}/sync-stream`;
  let sseSource = null;
  const trackedJob = _globalJobs[courseId];

  function _openSse() {
    if (!_globalJobs[courseId]) return;
    sseSource = GP.sse({
      url: sseUrl,
      maxErrors: MAX_SSE_ERRORS,
      // Exponential-ish backoff: 4s, 8s, 12s, 16s, 20s. Prevents tight
      // reconnect loops when the server closes streams quickly (visible
      // as 25ms/14ms stream entries in the network tab).
      reconnectMs: (n) => Math.min(4000 * n, 20000),
      onGiveUp: () => {
        // SSE unavailable - fall back to polling instead of showing error.
        // The sync may still be running; don't remove the progress bar.
        console.warn('[global-job-bar] SSE max errors for course sync, falling back to polling');
        _startLegacyCoursePoll(courseId);
      },
      onBlocked: () => {
        // EventSource not available - fall back to legacy polling
        _startLegacyCoursePoll(courseId);
      },
      events: {
      message: (ev) => {
      if (_globalJobs[courseId] !== trackedJob || _isUiTerminalStatus(trackedJob.status)) return;
      if (!_globalJobs[courseId]) { _closeSse(); return; }
      try {
        const data = JSON.parse(ev.data);
        if (data?.has_active_sync) {
          const running = data.sync_running_count || 0;
          const queued = data.sync_queued_count || 0;
          const job = _globalJobs[courseId];
          if (!job?.meta) { if (job) job.meta = {}; }

          // Group-level progress from DB (completed_groups / total_groups)
          let pct = null;
          const synced = data.synced_groups;
          const total = data.total_groups;
          if (data.progress != null) {
            pct = Math.round(data.progress);
          } else if (synced != null && total > 0) {
            pct = Math.round((synced / total) * 100);
          }
          if (job && pct != null) {
            job.progress = pct;
            _saveGlobalJobs();
          }
          // Track last update so the staleness guard doesn't expire active
          // jobs, and mark server-confirmed so the restore silent-remove
          // guard can't kill the bar on a subsequent stale complete event.
          if (job) {
            job.lastUpdate = _now();
            job.serverConfirmedRunning = true;
          }

          // Per-group completion toast
          if (data.completed_group && typeof flashToast === 'function') {
            flashToast(
              (t('Group synced:') + ' ' + data.completed_group),
              'success',
              4000
            );
          }

          // Build descriptive sync status message - uses the unified
          // _courseSyncMsg helper so SSE, polling, and reconciler paths
          // never flip the bar text between different formats.
          const _name = job?.meta?.courseName || '';
          let msg;
          if (running === 0 && queued === 0) {
            // Server still reports has_active_sync=true but no work left
            // - we're inside the post-batch grace window. Surface a
            // clearer "Finishing..." state instead of "0 running, 0 queued"
            // which looks like the bar is stuck.
            msg = _courseFinishingMsg(_name);
            _markCourseSyncFinishing(courseId, msg);
          } else {
            _markCourseSyncRunning(courseId);
            msg = _courseSyncMsg(_name, running, queued, synced, total);
            updateGlobalJob(msg, courseId);
          }
        }
        // If has_active_sync is false, do NOT complete here - the server
        // debounces and sends an explicit named 'complete' event after
        // N consecutive inactive snapshots (see
        // /api/v1/courses/{id}/sync-stream backend).
      } catch (e) {
        console.debug('[global-job-bar] SSE parse error', e);
      }
      },
      complete: (ev) => {
      if (_globalJobs[courseId] !== trackedJob || _isUiTerminalStatus(trackedJob.status)) return;
      let completedGroupName = null;
      let terminalData = null;
      try {
        const data = JSON.parse(ev.data);
        terminalData = data;
        if (data?.completed_group) completedGroupName = data.completed_group;
      } catch (_) { /* ignore parse errors */ }
      _closeSse();
      if (terminalData?.has_active_sync !== false) {
        _startLegacyCoursePoll(courseId);
        return;
      }

      const job = _globalJobs[courseId];
      if (!job) return;

      // Trust the SSE terminal event - the server debounces 6 s of
      // consecutive inactivity AND keeps `has_active_sync=true` for a
      // 15 s grace window after the last team completes, so by the time
      // `complete` is emitted the sync is truly done.  A previous design
      // did an extra /sync/active verify here; it added network noise
      // and was racy (the grace window already covers the same case).
      if (completedGroupName && typeof flashToast === 'function') {
        flashToast(
          (t('Group synced:') + ' ' + completedGroupName),
          'success',
          4000,
        );
      }
      const term = _courseSyncTerminalStateFromData(
        terminalData,
        job?.meta?.courseName || '',
      );
      completeGlobalJob(courseId, term.message, term.status);
      },
      },
    });
  }

  function _closeSse() {
    if (sseSource) { sseSource.close(); sseSource = null; }
  }

  _globalJobs[courseId].pollTimerId = null;
  _globalJobs[courseId].poller = {
    stop: _closeSse,
    close: _closeSse,
  };

  _openSse();
}

/**
 * Legacy fallback polling for course sync when SSE is unavailable.
 * @private
 */
function _startLegacyCoursePoll(courseId) {
  if (!_globalJobs[courseId]) return;
  _stopPoller(courseId);
  const trackedJob = _globalJobs[courseId];
  let reading = false;
  let pollErrors = 0;
  let consecutiveInactive = 0;
  const maxPollErrors = 10;

  const poll = async () => {
    if (reading || _globalJobs[courseId] !== trackedJob || _isUiTerminalStatus(trackedJob.status)) return;
    reading = true;
    try {
      const data = await GP.apiCall(`/api/v1/courses/${courseId}/sync-status`, 'GET', null, {
        maxRetries: 0, timeoutMs: 10000,
      });
      if (_globalJobs[courseId] !== trackedJob || trackedJob.pollTimerId !== intervalId) return;
      if (typeof data?.has_active_sync !== 'boolean') throw new Error('Missing sync status');
      pollErrors = 0;
      if (data.has_active_sync) {
        consecutiveInactive = 0;
        const running = data.sync_running_count || 0;
        const queued = data.sync_queued_count || 0;
        const job = _globalJobs[courseId];
        // Group-level progress from DB
        let pct = null;
        if (data.progress != null) {
          pct = Math.round(data.progress);
        } else if (data.synced_groups != null && data.total_groups > 0) {
          pct = Math.round((data.synced_groups / data.total_groups) * 100);
        }
        if (job) {
          if (pct != null) {
            job.progress = pct;
          }
          // Server confirmed the sync is still active - protect from stale
          // silent-removal on the next (possibly racy) status response.
          job.serverConfirmedRunning = true;
        }
        const _name = job?.meta?.courseName || '';
        let msg;
        if (running === 0 && queued === 0) {
          msg = _courseFinishingMsg(_name);
          _markCourseSyncFinishing(courseId, msg);
        } else {
          _markCourseSyncRunning(courseId);
          msg = _courseSyncMsg(_name, running, queued, data.synced_groups, data.total_groups);
          updateGlobalJob(msg, courseId);
        }
      } else {
        // Require 2 consecutive inactive polls before declaring complete -
        // a single false is routinely a brief DB race between groups.
        consecutiveInactive += 1;
        if (consecutiveInactive >= 2) {
          const term = _courseSyncTerminalStateFromData(
            data,
            _globalJobs[courseId]?.meta?.courseName || '',
          );
          completeGlobalJob(courseId, term.message, term.status);
        }
      }
    } catch (err) {
      if (_globalJobs[courseId] !== trackedJob || trackedJob.pollTimerId !== intervalId) return;
      consecutiveInactive = 0;
      pollErrors++;
      if (err?.status === 404) {
        // Course no longer exists (e.g. DB wiped) - remove stale job silently
        hideGlobalJob(courseId);
        GP.refreshProcessActionGuards();
        return;
      }
      if (err?.status === 401 || err?.status === 403) {
        completeGlobalJob(courseId, t('Session expired - refresh the page'), 'error');
        return;
      }
      if (pollErrors >= maxPollErrors) {
        updateGlobalJob(t('Network error checking status'), courseId);
      }
    } finally {
      reading = false;
    }
  };
  const intervalId = setInterval(poll, 3000);
  _globalJobs[courseId].pollTimerId = intervalId;
  setTimeout(() => { if (_globalJobs[courseId]?.pollTimerId === intervalId) poll(); }, 500);
}

function startGenericStatusPolling(jobType, url, opts = {}) {
  if (!_globalJobs[jobType]) {
    return;
  }

  _stopPoller(jobType);
  const trackedJob = _globalJobs[jobType];

  const onRunning = typeof opts.messageRunning === 'function'
    ? opts.messageRunning
    : (data) => data?.message || t('Processing...');

  const onDone = typeof opts.messageDone === 'function'
    ? opts.messageDone
    : () => 'Completed!';

  const onFailed = typeof opts.messageFailed === 'function'
    ? opts.messageFailed
    : (data) => data?.message || 'Process failed';

  // Check if the URL is a job endpoint - if so, use SSE via streamJobProgress
  const jobIdMatch = url.match(/\/api\/v1\/jobs\/([0-9a-f-]{36})$/i);

  if (jobIdMatch && typeof window.streamJobProgress === 'function') {
    // -- SSE path: use streamJobProgress for individual job tracking --
    const jobId = jobIdMatch[1];
    const ctrl = window.streamJobProgress(jobId, {
      onUpdate(data) {
        if (_globalJobs[jobType] !== trackedJob || _isUiTerminalStatus(trackedJob.status)) return;
        const status = String(data?.status || '').toLowerCase();
        if (status === 'enqueued' || status === 'queued') {
          updateGlobalJob(t('Waiting in queue...'), jobType);
        } else if (status === 'running' || status === 'started') {
          // Auto-update progress from API response
          const job = _globalJobs[jobType];
          if (job && data?.progress != null) {
            job.progress = Number(data.progress);
          }
          updateGlobalJob(onRunning(data), jobType);
        } else if (!['completed', 'failed', 'cancelled'].includes(status)) {
          updateGlobalJob(t('Status unavailable - the process may still be running.'), jobType);
        }
      },
      onComplete(data) {
        if (_globalJobs[jobType] !== trackedJob || _isUiTerminalStatus(trackedJob.status)) return;
        if (!_completeStatusJob(jobType, data, onDone, onFailed)) {
          _startLegacyGenericPoll(jobType, url, opts);
        }
      },
      onError() {
        if (_globalJobs[jobType] === trackedJob && !_isUiTerminalStatus(trackedJob.status)) {
          updateGlobalJob(t('Network error checking status'), jobType);
        }
      },
      // streamJobProgress owns the SSE -> polling fallback. Starting the
      // legacy poller here as well creates duplicate timers and can close
      // the helper while it is still switching modes.
    });

    _globalJobs[jobType].pollTimerId = null;
    _globalJobs[jobType].poller = ctrl;
    return;
  }

  // -- Non-job URL (e.g. enrichment, analysis status) - try SSE stream, fall back to polling --
  const SSE_STREAM_MAP = {
    'enrichment': '/dashboard/admin/users/enrich-gitlab/stream',
  };
  // Analysis: derive SSE stream URL from poll URL
  if (jobType === 'analysis' && url.includes('/llm-analysis-status')) {
    SSE_STREAM_MAP['analysis'] = url.replace('/llm-analysis-status', '/llm-analysis-stream');
  }

  const sseStreamUrl = SSE_STREAM_MAP[jobType];

  if (sseStreamUrl) {
    const isCurrent = () => _globalJobs[jobType] === trackedJob && !_isUiTerminalStatus(trackedJob.status);
    const fallback = () => {
      if (isCurrent()) _startLegacyGenericPoll(jobType, url, opts);
    };
    const stream = GP.sse({
      url: sseStreamUrl,
      withCredentials: true,
      maxErrors: MAX_SSE_ERRORS,
      onGiveUp: fallback,
      onBlocked: fallback,
      events: {
        message(event) {
          if (!isCurrent()) return;
          let data;
          try { data = JSON.parse(event.data); } catch (_) { return; }
          // A group stream also relays individual projects. Only its aggregate
          // snapshot can advance group progress or complete the whole run.
          if (jobType === 'analysis' && url.startsWith('/dashboard/teams/') && data?.job_id) return;
          if (_completeStatusJob(jobType, data, onDone, onFailed)) return;
          const status = String(data?.status || '').toLowerCase();
          if (status === 'running' || status === 'started') {
            const progress = data.progress ?? data.percent;
            if (typeof progress === 'number') trackedJob.progress = progress;
            updateGlobalJob(onRunning(data), jobType);
          } else if (status === 'enqueued' || status === 'queued') {
            updateGlobalJob(t('Waiting in queue...'), jobType);
          } else {
            updateGlobalJob(t('Status unavailable - the process may still be running.'), jobType);
            fallback();
          }
        },
        complete(event) {
          if (!isCurrent()) return;
          let data;
          try { data = JSON.parse(event.data); } catch (_) { /* Verify through polling. */ }
          if (!_completeStatusJob(jobType, data, onDone, onFailed)) fallback();
        },
      },
    });
    // A blocked EventSource starts polling synchronously; preserve that timer.
    if (stream.active && isCurrent()) {
      trackedJob.pollTimerId = null;
      trackedJob.poller = stream;
    } else {
      stream.close();
    }
    return;
  }

  _startLegacyGenericPoll(jobType, url, opts);
}
