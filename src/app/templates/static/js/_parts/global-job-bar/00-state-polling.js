/**
 * GitPulse - Global Job Bar
 *
 * Tracks long-running jobs across page navigation.
 * Features: determinate progress, ETA, job-type icons,
 * staggered auto-hide, hover-pause, local indicator
 * deduplication (hides global bar when a local progress
 * element is visible on screen).
 */
const GP = window.GP || (window.GP = {});
const { t } = GP;

const GLOBAL_JOB_KEY = 'gitpulse_global_job';
const DISMISSED_KEY = 'gitpulse_dismissed_jobs';
const _MIN = 60_000;
const DISMISS_TTL_MS = 15 * _MIN;
const UUID_LIKE_REGEX = /^[0-9a-f-]{36}$/i;
const AUTO_HIDE_STAGGER_MS = 800;
const AUTO_HIDE_MAX_STAGGER_MS = 3200;
const AUTO_HIDE_ERROR_MS = 10000;
const AUTO_HIDE_SUCCESS_MS = 8000;
const ANIMATION_EXIT_FALLBACK_MS = 250;
const MAX_SSE_ERRORS = 5;

const _globalJobs = {};
const _deferredJobs = new Set();
const _dismissedJobs = {};
let _lastSyncActiveAt = 0;
// Stamp of the most recent local completeGlobalJob/SSE-complete call.
// Periodic /sync/active reconciliation and htmx:load reconcile skip
// work for ~3 s after a completion to avoid flicker:
// SSE finishes -> bar enters auto-hide animation -> a stale /sync/active
// (or htmx:load) snapshot would otherwise re-add the bar momentarily.
let _lastCompletionAt = 0;
const POST_COMPLETION_RECONCILE_SUPPRESS_MS = 3000;
const _restoredJobs = new Set();  // jobs restored from localStorage on page load
const _pendingLocalWatchers = {};  // jobType -> MutationObserver waiting for selector to appear
const _metaDeferredJobs = new Set();  // jobType pre-deferred via <meta name="defer-global-job">;
                                      // kept deferred until explicit deferGlobalJob() from page JS,
                                      // so revalidator doesn't strip them while lazy content loads.
const _hardSuppressedJobs = new Map(); // jobType -> timeoutId. While the jobType is here, _jobEntries
                                       // forcibly filters it out no matter what - used for the
                                       // short "wait for local indicator" window right after a
                                       // button click so the user never sees a transient global
                                       // bar between click and local card creation.
let _elapsedTimerId = null;
let _suppressToasts = false;
const _queuedToasts = [];
let _barEventsBound = false;
let _autoHideStagger = 0;

function _now() {
  return Date.now();
}

function _fmtElapsed(ms) {
  const sec = Math.max(0, Math.floor(ms / 1000));
  if (sec < 60) {
    return `${sec}s`;
  }
  const min = Math.floor(sec / 60);
  return `${min}m ${sec % 60}s`;
}

// NOTE: The ETA / "time left" indicator was removed (2026-05-21) because the
// rate-based extrapolation produced misleading labels that counted down to 0
// and then snapped back to ~1m 30s on the next sample window. The elapsed
// timer is shown instead. The old ETA calculation, storage key, DOM hook,
// and CSS class were removed at the same time.

/* -- Job-type icons --
   Names into the app's one icon set (GP.iconSvg, the mirror of
   components/icons.html), not ten inline SVGs of their own: these were the
   24x24 stroked Feather glyphs, so the job bar - the strip the reader watches
   for minutes at a time - drew a different icon family from the page under it. */
const _JOB_ICONS = {
  sync: 'refresh',
  import: 'download',
  analysis: 'search',
  enrichment: 'users',
  export: 'upload',
  llm_generate: 'layers',
  recheck: 'refresh-cw',
  recheck_student: 'user-check',
  scheduled_job: 'clock',
  default: 'clock',
};

/* Scoped keys ("sync:team:<id>", "run_checks:course:<id>", a course sync keyed
   by its course id) are not in the table, so every finished sync and check run
   ended on the default clock instead of its own mark. Resolve by the job's
   kind, then by the key's first segment. Answers with an icon NAME. */
function _iconForJob(jobType, job) {
  const key = String(jobType || '');
  if (_JOB_ICONS[key]) return _JOB_ICONS[key];
  const kind = String(job?.meta?.jobKind || '').toLowerCase();
  if (kind === 'run_checks' || /^run_checks(?::|$)/.test(key)) return _JOB_ICONS.recheck;
  if (kind === 'course_sync' || kind === 'team_sync' || kind === 'project_sync'
      || /^sync(?::|$)/.test(key) || /^[0-9a-f-]{36}$/i.test(key) || /^\d+$/.test(key)) {
    return _JOB_ICONS.sync;
  }
  return _JOB_ICONS[key.split(':')[0]] || _JOB_ICONS.default;
}

/* -- Local indicator deduplication --
 * Maps jobType -> { selector, observer }.
 * When a local progress element (button spinner, in-page progress bar)
 * is visible on screen, the global bar item for that job is suppressed
 * (deferred).  As soon as the element scrolls out of view or is removed,
 * the global bar item becomes visible again.
 */
const _localIndicators = {};

// When a page-level indicator (button / inline progress bar) is visible
// for one of these job types, the global bar defers to it.  As soon as
// the element scrolls out of view or the user navigates away, the
// global bar takes over automatically.
const _DEFAULT_LOCAL_SELECTORS = {
  import:          '#importStatusBox',
  // sync: no page-level indicator any more (modal was removed because
  // it duplicated the global bar) - global bar owns sync UI.
  analysis:        '#analysisProgress',
  llm_generate:    '#btnRunLLM',
  batch_resurrect: '#btnBatchResurrect',
  event_replay:    '#btnReplaySelected',
  enrichment:      '#enrichBtn',
  // run_checks: its button lives in a modal that closes the moment the run
  // starts, so it can never stand in for the bar - the bar owns check runs.
};

function _watchLocalIndicator(jobType, selector) {
  if (_localIndicators[jobType]) return;            // already watching
  const el = document.querySelector(selector);
  if (!el) return;

  const observer = new IntersectionObserver(([entry]) => {
    if (!_globalJobs[jobType]) { observer.disconnect(); delete _localIndicators[jobType]; return; }
    if (entry.isIntersecting) {
      if (!_deferredJobs.has(jobType)) { _deferredJobs.add(jobType); _renderGlobalBar(); }
    } else {
      if (_deferredJobs.has(jobType)) {
        // Element removed from DOM (HTMX navigation) - clean up defer state
        if (!document.body.contains(entry.target)) {
          observer.disconnect();
          delete _localIndicators[jobType];
          _deferredJobs.delete(jobType);
          // If the job already completed while deferred, silently remove it
          // instead of flashing the global bar for a finished job.
          const _jr = _globalJobs[jobType];
          if (_jr && (_jr.status === 'done' || _jr.status === 'error')) {
            delete _globalJobs[jobType];
            _saveGlobalJobs();
          }
          _renderGlobalBar();
          return;
        }
        _deferredJobs.delete(jobType);
        // If the job already completed while deferred (badge handled it),
        // silently remove - don't flash the global bar for a finished job.
        const _j = _globalJobs[jobType];
        if (_j && (_j.status === 'done' || _j.status === 'error')) {
          observer.disconnect();
          delete _localIndicators[jobType];
          delete _globalJobs[jobType];
          _saveGlobalJobs();
          _renderGlobalBar();
          return;
        }
        _renderGlobalBar();
      }
    }
  }, { threshold: 0.1 });

  observer.observe(el);
  _localIndicators[jobType] = { selector, observer };

  // Initial: if element is visible now, defer immediately
  const rect = el.getBoundingClientRect();
  if (rect.top < window.innerHeight && rect.bottom > 0 && el.offsetParent !== null) {
    _deferredJobs.add(jobType);
  }
}

function _unwatchLocalIndicator(jobType) {
  const info = _localIndicators[jobType];
  if (info?.observer) info.observer.disconnect();
  delete _localIndicators[jobType];
}

/**
 * Clear all deferral state.  Called on every HTMX page navigation so
 * that the global bar is visible on the destination page regardless of
 * which page the sync was started from.  Any page-specific JS that
 * wants to hide the global bar behind an inline indicator on the newly
 * loaded page will re-register its own `deferGlobalJob` call on that
 * page's init.
 */
function _jobMaxAge(jobType) {
  const map = {
    import: 15 * _MIN,
    sync: 5 * _MIN,
    analysis: 10 * _MIN,
    enrichment: 30 * _MIN,
    export: 10 * _MIN,
    llm_generate: 2 * _MIN,
    recheck: 3 * _MIN,
    recheck_student: 3 * _MIN,
    run_checks: 5 * _MIN,
    aggregate: 3 * _MIN,
    event_replay: 5 * _MIN,
    batch_resurrect: 5 * _MIN,
    default: 10 * _MIN,
  };
  // Team-/project-scoped syncs ("sync:team:<uuid>" / "sync:project:<uuid>")
  // merely CONTAIN a UUID; they are single-scope and finish in minutes, so
  // they must NOT inherit the 45-min course cap below (that left a stuck
  // team/project ghost locking the Sync button for up to 45 min).
  if (/^sync:(team|project):/.test(String(jobType))) {
    return map.sync;
  }
  // Course-sync jobs (bare UUID-like or numeric course IDs) routinely take
  // 15-25 min for large courses (8 groups × ~6-8 min each, batched
  // across 4 workers).  A 10-min cap caused the staleness guard to
  // mark them as "Process timed out" mid-sync.  Use 45 min instead.
  if (UUID_LIKE_REGEX.test(jobType) || /^\d+$/.test(jobType)) {
    return 45 * _MIN;
  }
  return map[jobType] || map.default;
}

function _animateJobExit(item, jobType) {
  hideGlobalJob(jobType);
}


function _loadDismissedJobs() {
  try {
    const raw = sessionStorage.getItem(DISMISSED_KEY);
    if (!raw) {
      return;
    }
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') {
      return;
    }

    const now = _now();
    Object.entries(parsed).forEach(([key, ts]) => {
      if (typeof ts === 'number' && now - ts < DISMISS_TTL_MS) {
        _dismissedJobs[key] = ts;
      }
    });
  } catch (_) {
    // ignore parse/storage errors
  }
}

function _saveDismissedJobs() {
  try {
    const keys = Object.keys(_dismissedJobs);
    if (!keys.length) {
      sessionStorage.removeItem(DISMISSED_KEY);
      return;
    }
    sessionStorage.setItem(DISMISSED_KEY, JSON.stringify(_dismissedJobs));
  } catch (_) {
    // ignore storage errors
  }
}

function _isDismissed(jobType, startedAt) {
  const timestamp = _dismissedJobs[jobType];
  if (!timestamp) {
    return false;
  }
  if (_now() - timestamp > DISMISS_TTL_MS) {
    delete _dismissedJobs[jobType];
    _saveDismissedJobs();
    return false;
  }
  // Dismissal only suppresses the SPECIFIC occurrence that was dismissed.
  // If we can see that the incoming job started AFTER the dismissal was
  // recorded, it's a different run and should be shown.  Without this,
  // closing the bar once silently blocks every future job of the same
  // jobType for 15 minutes (very confusing UX - "the bar just stopped
  // working").
  if (typeof startedAt === 'number' && startedAt > timestamp) {
    delete _dismissedJobs[jobType];
    _saveDismissedJobs();
    return false;
  }
  return true;
}

function _barElements() {
  return {
    bar: document.getElementById('globalJobBar'),
    content: document.getElementById('globalJobContent'),
  };
}

function _bindBarEvents() {
  if (_barEventsBound) {
    return;
  }

  const { content } = _barElements();
  if (!content) {
    return;
  }

  content.addEventListener('click', (event) => {
    const cancelButton = event.target.closest('[data-job-cancel]');
    if (cancelButton) {
      event.preventDefault();
      event.stopPropagation();
      const jobType = cancelButton.dataset.jobCancel;
      if (jobType) {
        _cancelGlobalJob(jobType);
      }
      return;
    }

    const dismissButton = event.target.closest('[data-job-dismiss]');
    if (!dismissButton) {
      return;
    }
    const jobType = dismissButton.dataset.jobDismiss;
    if (jobType) {
      dismissGlobalJob(jobType);
    }
  });

  _barEventsBound = true;
}

function _isUiTerminalStatus(status) {
  return status === 'done' || status === 'error';
}

function _cancelEndpointForJob(jobType, job) {
  const meta = job?.meta || {};
  if (meta.cancelUrl) {
    return { url: meta.cancelUrl, body: meta.cancelPayload || { reason: t('Cancelled by user') } };
  }
  if (meta.jobId) {
    return {
      url: `/api/v1/jobs/${encodeURIComponent(meta.jobId)}/cancel`,
      body: { reason: t('Cancelled by user') },
    };
  }

  const scope = _scopeOfJob(jobType, job);
  if (scope.isCourse && scope.courseId) {
    const kind = String(meta.jobKind || '').toLowerCase();
    const key = String(jobType || '').toLowerCase();
    const jobTypes = [];
    if (kind === 'run_checks' || key.startsWith('run_checks')) {
      jobTypes.push('run_checks');
    } else {
      jobTypes.push('sync');
    }
    return {
      url: `/api/v1/courses/${encodeURIComponent(scope.courseId)}/jobs/cancel`,
      body: { reason: t('Cancelled by user'), job_types: jobTypes },
    };
  }

  return null;
}

function _isJobCancellable(jobType, job) {
  if (!job || _isUiTerminalStatus(job.status) || job.status === 'finishing') {
    return false;
  }
  if (jobType === 'import' && typeof window.cancelActiveImport === 'function') {
    return true;
  }
  if (jobType === 'llm_generate' && typeof window.cancelActiveLLMGeneration === 'function') {
    return true;
  }
  return Boolean(_cancelEndpointForJob(jobType, job));
}

/* The bar's controls are built in JS, so they have to opt into the tooltip
   component the same way markup does - a native title= would render the
   browser's own tooltip instead of the app's. initTippy() looks at
   descendants, so it is called on the container once the button is in it. */
function _setJobTooltip(el, content, jobType) {
  el.dataset.tippyContent = content;
  el.setAttribute('aria-label', content + ' ' + jobType);
  el.removeAttribute('title');
  if (el._tippy && typeof el._tippy.setContent === 'function') {
    el._tippy.setContent(content);
  } else if (el.parentNode && window.GP && typeof GP.initTippy === 'function') {
    GP.initTippy(el.parentNode);
  }
}

function _createCancelButton(jobType, job) {
  const cancel = document.createElement('button');
  cancel.type = 'button';
  cancel.className = 'btn btn-icon-only btn-tertiary btn-sm btn-touch-target btn-on-filled global-job-cancel';
  cancel.dataset.jobCancel = jobType;
  cancel.dataset.tippyContent = t('Cancel process');
  cancel.setAttribute('aria-label', t('Cancel process') + ' ' + jobType);
  cancel.disabled = job?.cancelRequested === true;
  cancel.innerHTML = GP.iconSvg('x-circle', 'sm');
  return cancel;
}

// A finished/failed job is not cancellable, so it gets a plain dismiss-X to close
// the bar. A running job never shows this (it shows the cancel-X instead), so the
// bar always has exactly one trailing control - never two ambiguous X's.
function _createDismissButton(jobType) {
  const holder = document.createElement('template');
  holder.innerHTML = GP.closeButtonHtml(t('Dismiss') + ' ' + jobType, 'btn-on-filled global-job-dismiss',
    { 'job-dismiss': jobType, 'tippy-content': t('Dismiss') });
  return holder.content.firstElementChild;
}

async function _cancelGlobalJob(jobType, options = {}) {
  const job = _globalJobs[jobType];
  if (!_isJobCancellable(jobType, job) || job.cancelRequested) {
    return;
  }

  if (options.confirm !== false) {
    const ok = await GP.confirmDialog({ message: t('Cancel this process?'), confirmText: t('Confirm') });
    if (!ok) {
      return;
    }
  }

  job.cancelRequested = true;
  job.message = t('Cancelling...');
  job.lastUpdate = _now();
  _renderGlobalBar();
  _saveGlobalJobs();

  if (jobType === 'import' && typeof window.cancelActiveImport === 'function') {
    window.cancelActiveImport({ confirm: false });
    return;
  }
  if (jobType === 'llm_generate' && typeof window.cancelActiveLLMGeneration === 'function') {
    window.cancelActiveLLMGeneration({ confirm: false });
    return;
  }

  const endpoint = _cancelEndpointForJob(jobType, job);
  if (!endpoint) {
    completeGlobalJob(jobType, t('Cancellation is not available for this process.'), 'error');
    return;
  }

  try {
    const call = GP.apiCall || window.apiCall;
    if (typeof call !== 'function') throw new Error(t('API client unavailable'));
    const result = await call(endpoint.url, 'POST', endpoint.body || {}, { maxRetries: 0 });
    completeGlobalJob(jobType, result?.message || t('Process cancelled.'), 'error');
  } catch (err) {
    job.cancelRequested = false;
    updateGlobalJob(t('Cancellation failed') + ': ' + (err?.message || t('Unknown error')), jobType);
    if (typeof showToast === 'function') showToast(t('Cancellation failed') + ': ' + (err?.message || ''), 'danger');
  }
}

function _jobEntries(includeDeferred = false) {
  const base = Object.entries(_globalJobs).filter(([jobType]) => {
    if (_hardSuppressedJobs.has(jobType)) return false;
    return includeDeferred ? true : !_deferredJobs.has(jobType);
  });
  return _dedupSyncScopes(base);
}

/**
 * Classify a job entry's sync scope from its key + meta.
 * @private
 */
function _scopeOfJob(jobType, job) {
  const key = String(jobType || '');
  const meta = (job && job.meta) || {};
  const parts = key.split(':');
  const keyKind = parts.length >= 3 ? parts[1] : '';
  const keyId = parts.length >= 3 ? parts.slice(2).join(':') : '';
  const isCourse = meta.jobKind === 'course_sync'
    || /^[0-9a-f-]{36}$/i.test(key)
    || /^\d+$/.test(key)
    || keyKind === 'course';
  const isProjectOrTeam = meta.jobKind === 'project_sync'
    || meta.jobKind === 'team_sync'
    || keyKind === 'project'
    || keyKind === 'team';
  const courseId = String(
    meta.courseId
    || meta.scopeCourseId
    || meta.targetCourseId
    || (isCourse ? (keyKind === 'course' ? keyId : key) : '')
    || ''
  );
  return { isCourse, isProjectOrTeam, courseId };
}

/**
 * Collapse duplicate sync entries that represent the same work.
 *
 * Restoring or syncing a single project registers a per-project
 * `project_sync` entry ("Syncing project..."), but the same work is *also*
 * surfaced as a course-level aggregate sync ("DEVOPS: Syncing") because
 * `/sync/active` counts running jobs per course. Both carry the same
 * courseId, so the global bar would show two rows for one operation.
 *
 * The course-level aggregate is the authoritative representation (it is
 * server-confirmed and auto-completes via `/sync/active` reconciliation),
 * so whenever a course-sync entry exists for a course we collapse every
 * project-/team-scoped sync entry belonging to that same course into it -
 * regardless of whether either side has finished yet. Without the
 * state-agnostic match, a per-project sync that completes *before* the
 * course aggregate (common on tiny/empty repos) leaves a second
 * "Sync completed" row behind. This only filters what is *displayed* -
 * the underlying job state, polling and completion toasts are untouched.
 * @private
 */
function _dedupSyncScopes(entries) {
  // Group every sync-scope entry (course / project / team) by its courseId
  // and render AT MOST ONE row per course. A single user action frequently
  // surfaces several rows for the same course (a course-level aggregate from
  // `/sync/active`, a per-project `project_sync`, and sometimes a fast
  // optimistic/deferred row that finishes instantly), which the user sees as
  // duplicate progress bars. Forcibly collapse them.
  //
  // Winner selection within a course group:
  //   1. the course-level aggregate entry (server-confirmed, auto-completes
  //      via `/sync/active` reconciliation), else
  //   2. the still-running entry with the LEAST progress (most work left), so
  //      the visible bar reflects the operation that is actually ongoing and
  //      a sibling that already finished is hidden rather than left behind,
  //      else
  //   3. the first entry.
  //
  // Entries without a courseId are never grouped (they cannot be proven to be
  // the same work). This only filters what is *displayed* - underlying job
  // state, polling and completion toasts are untouched.
  const groups = new Map(); // courseId -> [[jobType, job, scope], ...]
  const scopes = new Map(); // jobType -> scope
  entries.forEach(([jt, job]) => {
    if (!job) return;
    const s = _scopeOfJob(jt, job);
    scopes.set(jt, s);
    if ((s.isCourse || s.isProjectOrTeam) && s.courseId) {
      if (!groups.has(s.courseId)) groups.set(s.courseId, []);
      groups.get(s.courseId).push([jt, job, s]);
    }
  });

  if (!groups.size) return entries;

  const winners = new Map(); // courseId -> winning jobType
  groups.forEach((arr, courseId) => {
    if (arr.length <= 1) {
      winners.set(courseId, arr[0][0]);
      return;
    }
    const course = arr.find(([, , s]) => s.isCourse);
    if (course) {
      winners.set(courseId, course[0]);
      return;
    }
    let best = null;
    arr.forEach(([jt, job]) => {
      const done = job.status === 'done' || job.status === 'error';
      const prog = typeof job.progress === 'number' ? job.progress : 0;
      // Running jobs rank ahead of finished ones; within each tier the
      // lower progress (more work remaining) wins.
      const rank = (done ? 100000 : 0) + prog;
      if (best === null || rank < best.rank) best = { rank, jt };
    });
    winners.set(courseId, best.jt);
  });

  return entries.filter(([jt, job]) => {
    if (!job) return true;
    const s = scopes.get(jt);
    if (!s) return true;
    if ((s.isCourse || s.isProjectOrTeam) && s.courseId) {
      return winners.get(s.courseId) === jt;
    }
    return true;
  });
}

/**
 * Hard-suppress a job from rendering in the global bar for `ms`
 * milliseconds.  While a jobType is hard-suppressed the bar is
 * guaranteed never to show it, regardless of defer/un-defer state.
 * Used to wait for a page-level local indicator to appear after a
 * click so the user never sees the global bar flash before the local
 * card is created.  If a local indicator appears sooner, the normal
 * defer mechanism takes over seamlessly once suppression clears.
 */
function _hardSuppress(jobType, ms) {
  const prev = _hardSuppressedJobs.get(jobType);
  if (prev) clearTimeout(prev);
  const tid = setTimeout(() => {
    _hardSuppressedJobs.delete(jobType);
    _renderGlobalBar();
  }, ms);
  _hardSuppressedJobs.set(jobType, tid);
}

function _clearHardSuppress(jobType) {
  const tid = _hardSuppressedJobs.get(jobType);
  if (tid) {
    clearTimeout(tid);
    _hardSuppressedJobs.delete(jobType);
  }
}

function _syncElapsedTimer() {
  const visibleCount = _jobEntries(false).length;

  // Keep the ticker - and the staleness/ghost-expiry guard it hosts - alive
  // whenever ANY job exists in _globalJobs, even a HIDDEN one: a ghost deduped
  // by _dedupSyncScopes, or one that locks the Sync / Run Checks button via
  // process-guards without ever being rendered. Gating this on VISIBLE jobs
  // meant a hidden ghost was never auto-expired, so the button stayed locked
  // until a manual page refresh (the "have to refresh for the fix to work" bug).
  const hasAnyJob = visibleCount > 0 || Object.keys(_globalJobs).length > 0;
  if (!hasAnyJob) {
    if (_elapsedTimerId) {
      clearInterval(_elapsedTimerId);
      _elapsedTimerId = null;
    }
    return;
  }

  if (_elapsedTimerId) {
    return;
  }

  _elapsedTimerId = setInterval(() => {
    const { content } = _barElements();
    if (!content) {
      return;
    }

    const now = _now();

    content.querySelectorAll('[data-job-elapsed]').forEach((node) => {
      const jobType = node.getAttribute('data-job-elapsed');
      if (!jobType || !_globalJobs[jobType]) {
        return;
      }
      const _job = _globalJobs[jobType];
      // Freeze elapsed time once the job reaches a terminal state - otherwise
      // a completed banner that sits on screen (e.g. user is on another tab,
      // background-tab throttling delays auto-hide) keeps ticking up and
      // eventually shows nonsense like "97m 23s" for a 30-second sync.
      const elapsedMs = (_job.completedAt || now) - _job.startedAt;
      node.textContent = _fmtElapsed(elapsedMs);
    });

    // -- Staleness guard: auto-expire jobs that exceed their maxAge --
    Object.entries(_globalJobs).forEach(([jobType, job]) => {
      if (job.status === 'done' || job.status === 'error') {
        // Belt-and-suspenders: a terminal "Sync completed!" / error banner must
        // never outlive its auto-hide window. A background tab that throttles
        // setTimeout, a lost hide timer, or an SSE / /sync/active replay can
        // leave it on screen long after completion (users saw it hang around an
        // hour later). On the next 1s tick, retire anything past the hide
        // window + buffer regardless of how it got there.
        const terminalAge = now - (job.completedAt || job.startedAt);
        const cap = (job.status === 'error' ? AUTO_HIDE_ERROR_MS : AUTO_HIDE_SUCCESS_MS) + 6000;
        if (terminalAge > cap) hideGlobalJob(jobType);
        return;
      }
      // Fast-path: retire a GHOST job that has no real backend work behind it,
      // so it can't keep the Sync / Run Checks button process-locked. A ghost
      // is any non-terminal job that (a) never got a real backend job_id (the
      // POST was refused - 401 / invalid token - or the page restored a stale
      // pre-POST snapshot from local/sessionStorage) AND (b) was not confirmed
      // running by /sync/active, AND (c) has had no update for >15 s. A genuine
      // run is exempt on all three counts: it carries meta.jobId the moment its
      // POST returns, or is a server-confirmed course aggregate, and sends SSE
      // heartbeats that keep lastUpdate fresh. Without this, a team-/project-
      // scoped ghost sat locked for its whole maxAge and survived refreshes
      // (localStorage persists) - the recurring "button won't re-enable" bug.
      const _isBackedByRealJob = !!(
        job.jobId
        || (job.meta && job.meta.jobId)
        || job.serverConfirmedRunning
      );
      const _sinceUpdate = now - (job.lastUpdate || job.startedAt || 0);
      if (!_isBackedByRealJob && (now - job.startedAt) > 15000 && _sinceUpdate > 15000) {
        hideGlobalJob(jobType);
        return;
      }
      // If SSE/polling recently confirmed the job is still running, skip expiration.
      if (job.lastUpdate && (now - job.lastUpdate) < 60000) return;
      const age = now - job.startedAt;
      if (age > _jobMaxAge(jobType)) {
        completeGlobalJob(jobType, t('Process timed out - check results manually'), 'error');
      }
    });
  }, 1000);
}

function _createJobItem(jobType, job) {
  const item = document.createElement('div');
  item.className = 'global-job-item';
  item.setAttribute('data-job-id', jobType);

  if (job.status === 'error') {
    item.classList.add('global-job-error');
  } else if (job.status === 'done') {
    item.classList.add('global-job-done');
  }

  // Job-type icon
  const iconWrap = document.createElement('span');
  iconWrap.className = 'gjb-icon-wrap';
  if (job.status !== 'done' && job.status !== 'error') {
    const spinner = document.createElement('div');
    spinner.className = 'global-job-spinner gp-spinner gp-spinner--sm';
          spinner.innerHTML = GP.tanukiMarkHtml();
    iconWrap.appendChild(spinner);
  } else {
    iconWrap.innerHTML = GP.iconSvg(_iconForJob(jobType, job), 'sm');
  }
  item.appendChild(iconWrap);

  const message = document.createElement('span');
  message.className = 'global-job-msg';
  message.textContent = (window.GP && GP.formatJobMessage) ? GP.formatJobMessage(job.message) : job.message;

  // Progress percentage display
  const pctSpan = document.createElement('span');
  pctSpan.className = 'gjb-progress-pct';
  pctSpan.setAttribute('data-job-pct', jobType);
  if (job.progress != null && job.progress >= 0) {
    pctSpan.textContent = Math.round(job.progress) + '%';
  }

  const elapsed = document.createElement('span');
  elapsed.className = 'global-job-elapsed';
  elapsed.setAttribute('data-job-elapsed', jobType);
  elapsed.textContent = _fmtElapsed(_now() - job.startedAt);

  item.appendChild(message);
  item.appendChild(pctSpan);
  item.appendChild(elapsed);
  // Show exactly ONE trailing control (never two X's, which read as ambiguous):
  //  - a running job gets the cancel-X (with a confirm() before it stops the process);
  //  - a finished/failed job gets the dismiss-X to close the bar (nothing to cancel).
  if (_isJobCancellable(jobType, job)) {
    const cancel = _createCancelButton(jobType, job);
    item.appendChild(cancel);
    _setJobTooltip(cancel, t('Cancel process'), jobType);
  } else {
    const dismiss = _createDismissButton(jobType);
    item.appendChild(dismiss);
    _setJobTooltip(dismiss, t('Dismiss'), jobType);
  }

  // Determinate progress track
  const track = document.createElement('div');
  track.className = 'gjb-progress-track';
  const fill = document.createElement('div');
  fill.className = 'gjb-progress-fill';
  if (job.progress != null && job.progress >= 0) {
    fill.style.setProperty('--gjb-fill', Math.min(100, Math.round(job.progress)) + '%');
  } else if (job.status === 'done') {
    fill.style.setProperty('--gjb-fill', '100%');
  }
  track.appendChild(fill);
  item.appendChild(track);
  // Enable transitions AFTER the initial paint so restored progress
  // doesn't animate from 0% -> current value on page load.
  requestAnimationFrame(() => { fill.classList.add('gjb-animated'); });

  // Hover-to-pause auto-hide
  item.addEventListener('mouseenter', () => {
    item.dataset.hovered = '1';
    _clearHideTimer(jobType);
  });
  item.addEventListener('mouseleave', () => {
    delete item.dataset.hovered;
    const j = _globalJobs[jobType];
    if (j && (j.status === 'done' || j.status === 'error')) {
      _scheduleAutoHide(jobType, j.status);
    }
  });

  return item;
}

function _renderGlobalBar() {
  _bindBarEvents();

  const { bar, content } = _barElements();
  if (!bar || !content) {
    return;
  }

  // Prune redundant project/team scoped sync jobs from _globalJobs when a course-level sync is active
  const activeCourseSyncs = new Set();
  Object.entries(_globalJobs).forEach(([jt, job]) => {
    if (!job) return;
    const s = _scopeOfJob(jt, job);
    if (s.isCourse && s.courseId && job.status !== 'done' && job.status !== 'error') {
      activeCourseSyncs.add(s.courseId);
    }
  });

  if (activeCourseSyncs.size > 0) {
    let pruned = false;
    Object.keys(_globalJobs).forEach((jt) => {
      const job = _globalJobs[jt];
      if (!job) return;
      const s = _scopeOfJob(jt, job);
      if (s.isProjectOrTeam && s.courseId && activeCourseSyncs.has(s.courseId)) {
        _stopPoller(jt);
        _clearHideTimer(jt);

        _clearConnectingTimer(jt);
        _unwatchLocalIndicator(jt);
        _clearHardSuppress(jt);
        delete _globalJobs[jt];
        _deferredJobs.delete(jt);
        pruned = true;
      }
    });
    if (pruned) {
      _saveGlobalJobs();
    }
  }

  // Revalidate existing deferrals first: if the local indicator element
  // is no longer in the DOM or no longer visible (e.g. user navigated
  // via HTMX to a page without that indicator), undefer the job so the
  // global bar takes over again.  Without this step, _deferredJobs
  // persists stale entries across page swaps and the bar stays hidden
  // on pages where it should be visible.
  //
  // NOTE: We deliberately do NOT re-add to _deferredJobs here based on
  // the current DOM state.  Deferral is added only at two moments:
  //   (1) explicitly inside deferGlobalJob() when the caller signals
  //       a local indicator is already visible, and
  //   (2) by the IntersectionObserver in _watchLocalIndicator() once
  //       the indicator scrolls into view.
  // Re-adding here from a synchronous DOM check caused the global bar
  // to vanish on pages that happened to contain a matching element in
  // a transient (loader) state during HTMX swaps.
  Array.from(_deferredJobs).forEach((jt) => {
    const job = _globalJobs[jt];
    if (!job) {
      // No job entry yet - this is a pre-emptive defer (click happened
      // but POST hasn't returned and the watchdog/SSE hasn't created the
      // job record yet).  Keep the deferral so the bar cannot flash
      // during the network round-trip.  It will be garbage-collected by
      // the 2-minute safety timeout in _watchForLocalIndicatorAppearance
      // or cleaned up by hideGlobalJob on error.
      if (_metaDeferredJobs.has(jt)) return;
      if (_pendingLocalWatchers[jt]) return;
      _deferredJobs.delete(jt);
      return;
    }
    const sel = job.meta?.localIndicatorSelector
      || _DEFAULT_LOCAL_SELECTORS[jt];
    if (!sel) {
      // No selector known yet - if this is a meta-pre-deferred job,
      // keep it deferred until the page JS wires up deferGlobalJob().
      // Otherwise it's truly orphaned.
      if (_metaDeferredJobs.has(jt)) return;
      _deferredJobs.delete(jt);
      return;
    }
    const el = document.querySelector(sel);
    const visible = !!(el && !el.hidden && el.offsetParent !== null);
    if (!visible) {
      // Don't un-defer if the page JS is still waiting for the indicator
      // to appear (deferGlobalJob's MutationObserver) or has explicitly
      // marked this job as owner-managed.  This prevents a flash where
      // the bar briefly shows between the call to deferGlobalJob and the
      // indicator arriving in the DOM a few frames later.
      if (_pendingLocalWatchers[jt]) return;
      if (_metaDeferredJobs.has(jt)) return;
      _deferredJobs.delete(jt);
      _unwatchLocalIndicator(jt);
    }
  });

  // Pre-scan: before any render pass, auto-defer jobs whose page-level
  // indicator is already in the DOM and visible.  This eliminates the
  // "flash" where the bar briefly renders on the dashboard / course page
  // between the HTMX content swap and the page JS's explicit deferGlobalJob
  // call.  Conventions:
  //   * `[data-defer-job-id]` -> job type matches the attribute value.
  //   * Dashboard course cards: `.course-card-sync[data-course-id]`.
  Object.keys(_globalJobs).forEach((jt) => {
    if (_deferredJobs.has(jt)) return;
    const job = _globalJobs[jt];
    if (!job) return;
    const candidateSelectors = [
      job.meta?.localIndicatorSelector,
      _DEFAULT_LOCAL_SELECTORS[jt],
      `[data-defer-job-id="${CSS.escape(jt)}"]`,
      `.course-card-sync[data-course-id="${CSS.escape(jt)}"]`,
    ].filter(Boolean);
    for (const sel of candidateSelectors) {
      let el = null;
      try { el = document.querySelector(sel); } catch (_) { /* bad selector */ }
      if (!el) continue;
      const visible = !el.hidden && el.offsetParent !== null;
      if (visible) {
        _deferredJobs.add(jt);
        break;
      }
    }
  });

  const entries = _jobEntries(false);
  if (!entries.length) {
    bar.classList.remove('gjb-leaving');
    bar.hidden = true;
    content.innerHTML = '';
    bar.classList.remove('bar-state-done', 'bar-state-error', 'bar-state-mixed');
    _syncElapsedTimer();
    return;
  }

  // Cancel a pending exit if new work arrives.
  if (bar.classList.contains('gjb-leaving')) {
    bar.classList.remove('gjb-leaving');
  }
  bar.hidden = false;

  // Build set of current job types for diffing
  const currentJobTypes = new Set(entries.map(([jt]) => jt));

  // Remove items that are no longer in the entries
  content.querySelectorAll('[data-job-id]').forEach((el) => {
    if (!currentJobTypes.has(el.getAttribute('data-job-id'))) {
      el.remove();
    }
  });

  // Add or update each job item IN-PLACE (no innerHTML wipe)
  entries.forEach(([jobType, job]) => {
    const item = content.querySelector(`[data-job-id="${CSS.escape(jobType)}"]`);
    if (item) {
      // Update existing item in-place (no DOM rebuild -> spinner keeps running)
      const msg = item.querySelector('.global-job-msg');
      if (msg && msg.textContent !== job.message) {
        // Plain in-place update - the unified _courseSyncMsg format
        // keeps the prefix stable so only the digits change, which is
        // imperceptible without a transition.  An earlier opacity-fade
        // attempt actually *introduced* a blink because hiding the
        // text to 0 and back was visible to the user.
        msg.textContent = job.message;
      }

      // Elapsed is updated solely by the 1-second timer - skip here

      // Update status classes without recreating
      const isDone = job.status === 'done';
      const isError = job.status === 'error';
      item.classList.toggle('global-job-done', isDone);
      item.classList.toggle('global-job-error', isError);

      // Keep exactly one trailing control in sync as the job transitions between
      // running (cancel-X) and finished/failed (dismiss-X) - never both, never none.
      const existingCancel = item.querySelector('[data-job-cancel]');
      const existingDismiss = item.querySelector('[data-job-dismiss]');
      if (isDone || isError || !_isJobCancellable(jobType, job)) {
        if (existingCancel) existingCancel.remove();
        if (!existingDismiss) {
          const dismiss = _createDismissButton(jobType);
          item.appendChild(dismiss);
          _setJobTooltip(dismiss, t('Dismiss'), jobType);
        }
      } else {
        if (existingDismiss) existingDismiss.remove();
        if (!existingCancel) {
          const cancel = _createCancelButton(jobType, job);
          item.appendChild(cancel);
          _setJobTooltip(cancel, t('Cancel process'), jobType);
        } else {
          existingCancel.disabled = job.cancelRequested === true;
          _setJobTooltip(
            existingCancel,
            job.cancelRequested ? t('Cancelling...') : t('Cancel process'),
            jobType
          );
        }
      }

      // Update icon wrap: spinner <-> type-icon
      const iconWrap = item.querySelector('.gjb-icon-wrap');
      if (iconWrap) {
        if (isDone || isError) {
          if (iconWrap.querySelector('.global-job-spinner')) {
            iconWrap.innerHTML = GP.iconSvg(_iconForJob(jobType, job), 'sm');
          }
        } else if (!iconWrap.querySelector('.global-job-spinner')) {
          iconWrap.innerHTML = '';
          const spinner = document.createElement('div');
          spinner.className = 'global-job-spinner gp-spinner gp-spinner--sm';
          spinner.innerHTML = GP.tanukiMarkHtml();
          iconWrap.appendChild(spinner);
        }
      }

      // Update progress percentage
      const pctNode = item.querySelector('[data-job-pct]');
      if (pctNode) {
        const pctText = (job.progress != null && job.progress >= 0) ? Math.round(job.progress) + '%' : '';
        if (pctNode.textContent !== pctText) pctNode.textContent = pctText;
      }

      // Update determinate progress track
      const fillNode = item.querySelector('.gjb-progress-fill');
      if (fillNode) {
        let targetW = '';
        if (job.progress != null && job.progress >= 0) {
          targetW = Math.min(100, Math.round(job.progress)) + '%';
        } else if (isDone) {
          targetW = '100%';
        }
        const curW = fillNode.style.getPropertyValue('--gjb-fill');
        if (curW !== targetW) fillNode.style.setProperty('--gjb-fill', targetW);
      }
    } else {
      // New job - create fresh item
      content.appendChild(_createJobItem(jobType, job));
    }
  });

  const statuses = entries.map(([, job]) => job.status);
  const allDone = statuses.every((status) => status === 'done');
  const allError = statuses.every((status) => status === 'error');
  const allTerminal = statuses.every((status) => status === 'done' || status === 'error');
  const runningCount = statuses.filter((s) => s !== 'done' && s !== 'error').length;

  bar.classList.toggle('bar-state-done', allDone);
  bar.classList.toggle('bar-state-error', allError);
  bar.classList.toggle('bar-state-mixed', allTerminal && !allDone && !allError);
  if (!allTerminal) {
    bar.classList.remove('bar-state-done', 'bar-state-error', 'bar-state-mixed');
  }

  // Show multi-job count badge
  let countBadge = bar.querySelector('.gjb-count-badge');
  if (entries.length > 1) {
    if (!countBadge) {
      countBadge = document.createElement('span');
      countBadge.className = 'gjb-count-badge';
      // Insert at top so it never overlaps with per-item dismiss
      // buttons or ETA text on narrow viewports (e.g. Opera).
      bar.insertBefore(countBadge, bar.firstChild);
    }
    countBadge.textContent = runningCount > 0
      ? `${runningCount}/${entries.length} ${t('running')}`
      : `${entries.length} ${t('jobs')}`;
    countBadge.hidden = false;
  } else if (countBadge) {
    countBadge.hidden = true;
  }

  _syncElapsedTimer();
}

function _saveGlobalJobs() {
  try {
    const payload = {};

    Object.entries(_globalJobs).forEach(([jobType, job]) => {
      payload[jobType] = {
        message: job.message,
        startedAt: job.startedAt,
        jobType,
        status: job.status || 'running',
      };
      if (job.progress != null) {
        payload[jobType].progress = job.progress;
      }
      if (job.completedAt != null) {
        payload[jobType].completedAt = job.completedAt;
      }
      if (job.lastUpdate != null) {
        payload[jobType].lastUpdate = job.lastUpdate;
      }
      if (job.cancelRequested === true) {
        payload[jobType].cancelRequested = true;
      }
      if (job.meta && Object.keys(job.meta).length) {
        payload[jobType].meta = job.meta;
      }
    });

    if (Object.keys(payload).length > 0) {
      localStorage.setItem(GLOBAL_JOB_KEY, JSON.stringify(payload));
    } else {
      localStorage.removeItem(GLOBAL_JOB_KEY);
    }
  } catch (_) {
    // ignore storage errors
  }

  // Update snapshot so tab-visible only fires when something actually changed
  if (typeof _lastVisibleSnapshot !== 'undefined') {
    _lastVisibleSnapshot = _jobSnapshot();
  }
}

function _clearHideTimer(jobType) {
  const job = _globalJobs[jobType];
  if (job?.hideTimerId) {
    clearTimeout(job.hideTimerId);
    job.hideTimerId = null;
  }
}

// Safety-net timers for the optimistic "connecting" phase (see
// connectGlobalJob): jobType -> timeoutId.  Cleared the moment the job is
// promoted to a real running job, completed, or hidden.
const _connectingTimers = {};

function _clearConnectingTimer(jobType) {
  const tid = _connectingTimers[jobType];
  if (tid) {
    clearTimeout(tid);
    delete _connectingTimers[jobType];
  }
}

function _stopPoller(jobType) {
  const job = _globalJobs[jobType];
  if (!job) {
    return;
  }

  if (job.pollTimerId) {
    clearInterval(job.pollTimerId);
    job.pollTimerId = null;
  }

  if (job.poller) {
    if (typeof job.poller.stop === 'function') {
      job.poller.stop();
    } else if (typeof job.poller.close === 'function') {
      job.poller.close();
    }
    job.poller = null;
  }
}

function _stopAllPollers() {
  Object.keys(_globalJobs).forEach((jobType) => {
    _stopPoller(jobType);
    _clearHideTimer(jobType);
  });
}

/**
 * Per-tab session-scoped guard so a completion toast for jobType X fires
 * AT MOST ONCE per browser tab session.  Without this, the following
 * scenario re-shows a toast the user has already dismissed:
 *   1. Sync finishes -> toast shown -> user clicks X.
 *   2. User navigates -> page reload -> _restoreJobs sees status='done',
 *      auto-polling restarts SSE (or watchdog hits /sync/active).
 *   3. SSE re-emits 'complete' OR the watchdog reconciler decides the
 *      job is gone -> completeGlobalJob() fires again.
 *   4. The 5 s text-based dedup window in showToast() has long expired
 *      -> toast appears a second time.
 * The flag lives in sessionStorage so it's wiped automatically when the
 * tab is closed but survives in-tab navigation.
 */
const _COMPLETION_DEDUP_KEY = 'gp_job_completion_dedup_v2';
const _PAGE_LOAD_COUNTER_KEY = 'gp_job_page_load_counter_v1';
// Window during which a toast fired on a previous page is allowed to
// re-fire on the next page load.  Captures the "user clicked a link the
// moment the toast appeared and never actually saw it" case (issue 2).
// Anything older than this is assumed to have been seen. Widened from 3s
// to 8s because slow navigations (heavy pages / HTMX swaps / cold cache)
// can easily eat the entire window before the new page boots and shows
// the replay toast - leaving the user with zero feedback that their
// sync actually finished.
const _NAV_REPLAY_WINDOW_MS = 8000;
let _pageLoadCounter = 1;
const _TAB_ID_KEY = 'gp_job_tab_id_v1';
let _tabId = '';
try {
  const _raw = sessionStorage.getItem(_PAGE_LOAD_COUNTER_KEY);
  _pageLoadCounter = (_raw ? parseInt(_raw, 10) || 0 : 0) + 1;
  sessionStorage.setItem(_PAGE_LOAD_COUNTER_KEY, String(_pageLoadCounter));

  let tid = sessionStorage.getItem(_TAB_ID_KEY);
  if (!tid) {
    tid = Math.random().toString(36).slice(2, 11);
    sessionStorage.setItem(_TAB_ID_KEY, tid);
  }
  _tabId = tid;
} catch (_) {
  _tabId = 'fallback-' + Date.now();
}

/* ============================================
   Cross-tab poll leadership (localStorage lease)
   ============================================
   With the app open in several tabs, EVERY tab used to run its own SSE
   streams and /sync/active pollers - N tabs = N× the requests, N progress
   bars advancing out of step, and duplicate completion toasts. This lease
   elects a single VISIBLE "leader" tab that owns the network pollers; the
   other tabs mirror job state through the 'storage' events already wired in
   20-listeners-api.js, so their bars stay in sync without hitting the server.

   Design is deliberately FAIL-OPEN so a single tab can NEVER stall:
     - No fresh lease (lone tab, private-mode/no-storage, or the leader
       closed) => this visible tab claims leadership and polls.
     - The leader renews the lease on a heartbeat; it stops renewing the
       moment it is hidden, so a visible tab takes over within the TTL.
     - We only ever START pollers, never forcibly stop a follower's existing
       ones, so a mis-election degrades to today's behaviour (a little extra
       polling) rather than a frozen bar. */
const _LEADER_LEASE_KEY = 'gp:jobLeaderLease_v1';
const _LEADER_TTL_MS = 6000;
const _LEADER_HEARTBEAT_MS = 2000;
let _leaderHeartbeatId = null;
let _wasLeader = false;

function _readLeaderLease() {
  try {
    const raw = localStorage.getItem(_LEADER_LEASE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (_) { return null; }
}
function _writeLeaderLease() {
  try {
    localStorage.setItem(_LEADER_LEASE_KEY, JSON.stringify({ tab: _tabId, at: Date.now() }));
  } catch (_) { /* storage disabled - fail open (every tab leads) */ }
}
function _leaseFresh(lease) {
  return !!(lease && typeof lease.at === 'number' && (Date.now() - lease.at) < _LEADER_TTL_MS);
}

/* True if THIS visible tab may run the network pollers. Claims the lease when
   none is fresh (fail-open). Hidden tabs never lead - their pollers are already
   suppressed by the document.hidden guards + the visibilitychange handler. */
function _isPollLeader() {
  if (document.hidden) return false;
  const lease = _readLeaderLease();
  if (!_leaseFresh(lease)) { _writeLeaderLease(); return true; }
  return lease.tab === _tabId;
}
GP.isPollLeader = _isPollLeader;

/* (Re)start pollers for every still-running job - used when this tab first
   becomes leader or takes over from a closed leader. Each poller-start is
   idempotent (guards on job.poller / job.pollTimerId), so this is safe to run
   on every heartbeat and never opens a duplicate stream. */
function _resumeLeaderPollers() {
  Object.entries(_globalJobs).forEach(([jobType, job]) => {
    if (!job || job.status === 'done' || job.status === 'error') return;
    if (job.pollTimerId || job.poller) return;
    if (typeof _autoStartPolling === 'function') _autoStartPolling(jobType);
  });
}

function _releaseLeaderLease() {
  const lease = _readLeaderLease();
  if (lease && lease.tab === _tabId) {
    try { localStorage.removeItem(_LEADER_LEASE_KEY); } catch (_) { /* noop */ }
  }
}

function _leaderHeartbeat() {
  if (document.hidden) {
    // Step back cleanly: drop our lease so a VISIBLE tab takes over at once
    // (the storage event wakes it) instead of waiting out the TTL.
    if (_wasLeader) { _wasLeader = false; _releaseLeaderLease(); }
    return;
  }
  const lease = _readLeaderLease();
  const iLead = !_leaseFresh(lease) || lease.tab === _tabId;
  if (iLead) {
    _writeLeaderLease();
    // Resume pollers only on the transition INTO leadership (fresh start or
    // taking over from a closed tab) - never on every heartbeat, so we don't
    // churn pollers for jobs a page owns via its own SSE (e.g. the course
    // page's _stopGlobalBarTracking). Mirrors the visibilitychange restart.
    if (!_wasLeader) {
      _wasLeader = true;
      _resumeLeaderPollers();
    }
  } else {
    _wasLeader = false;
  }
}

// Release leadership when the tab is closed/navigated away so a sibling tab
// resumes polling immediately rather than after the lease expires.
window.addEventListener('pagehide', () => { try { _releaseLeaderLease(); } catch (_) { /* noop */ } });

function _startLeaderHeartbeat() {
  if (_leaderHeartbeatId) return;
  try { _leaderHeartbeat(); } catch (_) { /* noop */ }
  _leaderHeartbeatId = setInterval(() => {
    try { _leaderHeartbeat(); } catch (_) { /* noop */ }
  }, _LEADER_HEARTBEAT_MS);
}

// Re-evaluate leadership the instant a tab is shown/hidden so takeover from a
// backgrounded leader is near-immediate rather than waiting a full heartbeat.
document.addEventListener('visibilitychange', () => {
  try { _leaderHeartbeat(); } catch (_) { /* noop */ }
});
// Another tab dropping/renewing the lease should prompt a re-check here too.
window.addEventListener('storage', (evt) => {
  if (evt.key === _LEADER_LEASE_KEY) {
    try { _leaderHeartbeat(); } catch (_) { /* noop */ }
  }
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', _startLeaderHeartbeat, { once: true });
} else {
  _startLeaderHeartbeat();
}

function _completionDedupRead() {
  try {
    const raw = localStorage.getItem(_COMPLETION_DEDUP_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return (parsed && typeof parsed === 'object') ? parsed : {};
  } catch (_) { return {}; }
}
function _completionDedupWrite(map) {
  try {
    localStorage.setItem(_COMPLETION_DEDUP_KEY, JSON.stringify(map));
  } catch (_) { /* noop */ }
}
function _completionAlreadyShown(jobType, status) {
  const map = _completionDedupRead();
  const entry = map[jobType + ':' + status];
  if (!entry) return false;
  // Legacy schema (plain number) -> treat as confirmed-shown.
  if (typeof entry === 'number') return true;
  const at = entry.at || 0;
  const pl = entry.pl || 0;
  const tab = entry.tab;
  // If shown in a different tab, we do not want to show it again in this tab.
  if (tab && tab !== _tabId) return true;
  // Same page-load: hard block (prevents same-page duplicate toasts).
  if (pl === _pageLoadCounter) return true;
  // Different page-load but stale: user already saw it on a previous page.
  if (Date.now() - at >= _NAV_REPLAY_WINDOW_MS) return true;
  // Different page-load AND within the replay window: the user probably
  // navigated away before the toast was visible -> allow re-fire.
  return false;
}
function _markCompletionShown(jobType, status) {
  const map = _completionDedupRead();
  map[jobType + ':' + status] = { at: Date.now(), pl: _pageLoadCounter, tab: _tabId };
  // Cap to last 30 entries to bound storage growth.
  const keys = Object.keys(map);
  if (keys.length > 30) {
    keys.sort((a, b) => {
      const ax = (typeof map[a] === 'object' ? map[a].at : map[a]) || 0;
      const bx = (typeof map[b] === 'object' ? map[b].at : map[b]) || 0;
      return ax - bx;
    });
    keys.slice(0, keys.length - 30).forEach((k) => { delete map[k]; });
  }
  _completionDedupWrite(map);
}
function _clearCompletionDedup(jobType) {
  // Called when a NEW run starts for jobType so that the next completion
  // (success or error) is always shown even if an earlier run already
  // produced a toast in this tab session (issue 3: error toasts going
  // missing across repeated failures of the same course).
  if (!jobType) return;
  const map = _completionDedupRead();
  let changed = false;
  ['done', 'error'].forEach((s) => {
    const k = jobType + ':' + s;
    if (k in map) { delete map[k]; changed = true; }
  });
  if (changed) _completionDedupWrite(map);
}

function _showCompletionToast(jobType, message, status, _skipBroadcast, _force) {
  if (!_force && _deferredJobs.has(jobType)) {
    return;
  }

  // Collapse per-project / per-team sync completion toasts into the
  // course-level aggregate toast for the same course. Restoring or syncing
  // a single project completes BOTH a project_sync job ("Sync completed")
  // and the course_sync aggregate ("Sync completed!"); their wording differs
  // so the 5s text-based dedup in showToast misses them, and their jobTypes
  // differ so the session dedup misses them too - producing two toasts, the
  // faster project one firing early (before the aggregate finishes). The
  // course aggregate is authoritative, so whenever a course-sync entry for
  // the same course exists we suppress the project/team completion toast and
  // let only the aggregate toast fire. Mirrors _dedupSyncScopes for the bar.
  const _scopedJob = _globalJobs[jobType];
  if (_scopedJob) {
    const _s = _scopeOfJob(jobType, _scopedJob);
    if (_s.isProjectOrTeam && _s.courseId) {
      const _hasCourseSync = Object.entries(_globalJobs).some(([jt, j]) => {
        if (!j || jt === jobType) return false;
        const cs = _scopeOfJob(jt, j);
        return cs.isCourse && cs.courseId === _s.courseId;
      });
      if (_hasCourseSync) {
        return;
      }
    }
  }

  // Session-scoped dedup - see _completionAlreadyShown JSDoc.
  if (_completionAlreadyShown(jobType, status)) {
    return;
  }

  const _rawMsg = message || (status === 'error' ? t('Process failed') : t('Process completed'));
  // Normalise worker-stored English summaries ("Synced N issues, ...") into
  // the friendly translated wording so the toast never leaks raw text.
  const msg = (window.GP && GP.formatJobMessage) ? GP.formatJobMessage(_rawMsg) : _rawMsg;
  const type = status === 'error' ? 'error' : 'success';

  if (_suppressToasts) {
    _queuedToasts.push({ msg, type, status, jobType, _skipBroadcast });
    return;
  }

  /* Defer toast display while tab is hidden so it doesn't auto-dismiss
     before the user can see it. */
  if (document.hidden) {
    _queuedToasts.push({ msg, type, status, jobType, _skipBroadcast });
    return;
  }

  if (typeof flashToast !== 'function') return;

  flashToast(msg, type, status === 'error' ? 10000 : 5000);
  _markCompletionShown(jobType, status);

  // Broadcast to other tabs (but not if WE received this from another tab,
  // or if the user is looking at a local inline indicator on this page -
  // other tabs may not be on a relevant page and would receive a noisy toast).
  if (!_skipBroadcast && typeof broadcastToast === 'function') {
    broadcastToast(msg, type);
  }
}

function _scheduleAutoHide(jobType, status) {
  const job = _globalJobs[jobType];
  if (!job) {
    return;
  }

  _clearHideTimer(jobType);

  // Stagger auto-hide when multiple jobs complete simultaneously
  _autoHideStagger += 1;
  const staggerIndex = _autoHideStagger;
  const staggerDelay = Math.min(staggerIndex * AUTO_HIDE_STAGGER_MS, AUTO_HIDE_MAX_STAGGER_MS);
  const baseDelay = status === 'error' ? AUTO_HIDE_ERROR_MS : AUTO_HIDE_SUCCESS_MS;
  const delay = baseDelay + staggerDelay;

  // Anchor the deadline to wall-clock time so a backgrounded tab (where
  // setTimeout is throttled to ~1 minute) doesn't leave a "Sync completed"
  // banner hanging for ages - the visibilitychange handler below force-hides
  // anything past its deadline as soon as the tab regains focus.
  job.hideAt = Date.now() + delay;

  // Reset stagger counter after a bit
  setTimeout(() => { if (_autoHideStagger === staggerIndex) _autoHideStagger = 0; }, delay + 1000);

  job.hideTimerId = setTimeout(() => {
    const current = _globalJobs[jobType];
    if (!current) {
      return;
    }

    // Don't hide if user is hovering over the item
    const { content } = _barElements();
    if (content) {
      const item = content.querySelector(`[data-job-id="${CSS.escape(jobType)}"]`);
      if (item && item.dataset.hovered === '1') {
        // Re-schedule when user stops hovering
        return;
      }
    }

    if (current.status === 'done' || current.status === 'error') {
      // Animate the item out before fully removing
      if (content) {
        const item = content.querySelector(`[data-job-id="${CSS.escape(jobType)}"]`);
        if (item) {
          _animateJobExit(item, jobType);
          return;
        }
      }
      hideGlobalJob(jobType);
    }
  }, delay);
}
