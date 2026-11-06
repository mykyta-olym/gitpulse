/* import-stream.js - Shared SSE-driven GitLab import progress helpers */
/* Extracted from components/import_helpers.html macro */

const _t = GP.t;
const _MAX_LOG_ENTRIES = 200;

let importStatusTimer = null;
let importStatusStartedAt = 0;
let importInProgress = false;
let importCompleted = false;          // eslint-disable-line no-unused-vars
let _importCounts = { teams: 0, students: 0, teachers: 0, projects: 0 };
let _importSeen  = { students: new Set(), teachers: new Set() };
let _activeImportAbortController = null;
let _importCancelRequested = false;
let _importModalsInitialized = false;
const _GITLAB_IMPORT_PATH_RE = /^[A-Za-z0-9][A-Za-z0-9._-]*(\/[A-Za-z0-9][A-Za-z0-9._-]*)*$/;

function _setImportCancelButtonState(isBusy) {
  const cancelBtn = document.getElementById('importGitlabCourseCancelBtn');
  if (!cancelBtn) return;
  if (!cancelBtn.dataset.idleLabel) cancelBtn.dataset.idleLabel = cancelBtn.textContent.trim() || _t('Cancel');
  cancelBtn.disabled = false;
  cancelBtn.textContent = isBusy
    ? (_importCancelRequested ? _t('Cancelling...') : _t('Cancel import'))
    : cancelBtn.dataset.idleLabel;
  cancelBtn.setAttribute('aria-disabled', _importCancelRequested ? 'true' : 'false');
}

function setImportModalBusy(isBusy) {  // eslint-disable-line no-unused-vars
  importInProgress = isBusy;
  // GitLab import is a cancellable process, not unsaved form data. Do not
  // register it with the beforeunload dirty guard; that browser prompt made
  // "Cancel" look like it would abort the import while actually just keeping
  // the page open. Real cancellation is handled by the cancel button/global bar.
  if (typeof GP !== 'undefined' && GP.clearDirtyReason) GP.clearDirtyReason('import_running');
  if (isBusy) GP.clearModalDirty?.('importGitlabCourseModal');
  const submitBtn = document.getElementById('importGitlabCourseBtn');
  if (submitBtn) {
    if (typeof setButtonLoading === 'function') {
      setButtonLoading(submitBtn, isBusy);
    } else {
      submitBtn.disabled = isBusy;
    }
  }
  _setImportCancelButtonState(isBusy);
}

function resetImportStatus() {  // eslint-disable-line no-unused-vars
  const box = document.getElementById('importStatusBox');
  const text = document.getElementById('importStatusText');
  const meta = document.getElementById('importStatusMeta');
  const spinner = document.getElementById('importStatusSpinner');
  const counters = document.getElementById('importCounters');
  const log = document.getElementById('importLog');
  if (!box) return;
  box.hidden = true;
  box.classList.remove('success', 'error');
  if (text) text.textContent = _t('Starting import...');
  if (meta) meta.textContent = '';
  if (spinner) spinner.hidden = false;
  if (counters) counters.hidden = true;
  if (log) { log.hidden = true; log.innerHTML = ''; }
  _importCounts = { teams: 0, students: 0, teachers: 0, projects: 0 };
  _importSeen  = { students: new Set(), teachers: new Set() };
}

function showImportStage(message) {  // eslint-disable-line no-unused-vars
  const box = document.getElementById('importStatusBox');
  const text = document.getElementById('importStatusText');
  if (box) box.hidden = false;
  if (text) text.textContent = message;
}

function appendImportLog(icon, label) {  // eslint-disable-line no-unused-vars
  const log = document.getElementById('importLog');
  if (!log) return;
  log.hidden = false;
  const entry = document.createElement('div');
  entry.className = 'import-log-entry';
  entry.textContent = icon + ' ' + label;
  log.appendChild(entry);
  while (log.children.length > _MAX_LOG_ENTRIES) log.removeChild(log.firstChild);
  log.scrollTop = log.scrollHeight;
}

function updateImportCounters() {  // eslint-disable-line no-unused-vars
  const el = document.getElementById('importCounters');
  if (el) { el.hidden = false; el.classList.add('import-counters-active'); }
  const t = document.getElementById('importCntTeams');
  const s = document.getElementById('importCntStudents');
  const p = document.getElementById('importCntProjects');
  if (t && t.textContent !== String(_importCounts.teams)) { t.textContent = _importCounts.teams; }
  if (s && s.textContent !== String(_importCounts.students)) { s.textContent = _importCounts.students; }
  if (p && p.textContent !== String(_importCounts.projects)) { p.textContent = _importCounts.projects; }
  const ic = document.getElementById('importCntTeachers');
  if (ic && ic.textContent !== String(_importCounts.teachers)) { ic.textContent = _importCounts.teachers; }
}

function _globalBarImportProgress() {
  if (typeof updateGlobalJob !== 'function') return;
  const parts = [];
  if (_importCounts.teams) parts.push(_importCounts.teams + ' ' + _t('groups'));
  if (_importCounts.students || _importCounts.teachers) {
    parts.push(_importCounts.students + ' ' + _t('students'));
    let instrPart = _importCounts.teachers + ' ' + _t('teachers');
    if (_importSeen.teachers.size) instrPart += ' (' + Array.from(_importSeen.teachers).join(', ') + ')';
    parts.push(instrPart);
  }
  if (_importCounts.projects) parts.push(_importCounts.projects + ' ' + _t('projects'));
  if (parts.length) {
    updateGlobalJob(_t('Importing:') + ' ' + parts.join(', ') + '...', 'import');
  }
}

function _extractGitLabImportPath(rawValue) {
  const raw = String(rawValue || '').trim();
  if (!raw) return '';
  let path = raw;
  if (/^https?:\/\//i.test(raw)) {
    try {
      const url = new URL(raw);
      path = decodeURIComponent(url.pathname.replace(/^\/+|\/+$/g, ''));
    } catch (_) {
      return '';
    }
  } else {
    path = raw.replace(/^\/+|\/+$/g, '');
  }
  path = path.replace(/^groups\//, '');
  if (path.includes('/-/')) path = path.split('/-/')[0];
  path = path.replace(/\.git$/, '').replace(/^\/+|\/+$/g, '');
  return path;
}

function validateGitLabImportUrl(rawValue) {  // eslint-disable-line no-unused-vars
  const raw = String(rawValue || '').trim();
  if (!raw) return _t('GitLab URL is required.');
  const path = _extractGitLabImportPath(raw);
  if (!path || !_GITLAB_IMPORT_PATH_RE.test(path) || path.split('/').some((part) => part === '.' || part === '..')) {
    return _t('Enter a valid GitLab group or project URL/path.');
  }
  return '';
}

function _resetImportAbortState() {
  _activeImportAbortController = null;
  _importCancelRequested = false;
  _setImportCancelButtonState(importInProgress);
}

/* Async: the confirmation runs on the app's dialog now. Callers that pass
   `{confirm:false}` (the job bar) never await anything, so they are unaffected. */
async function cancelActiveImport(options) {  // eslint-disable-line no-unused-vars
  if (!importInProgress) return false;
  if (_importCancelRequested) return true;
  const opts = options || {};
  if (opts.confirm !== false) {
    const ok = await GP.confirmDialog({
      message: _t('Cancel this import? Data already saved on the server will remain.'),
      confirmText: _t('Confirm'), variant: 'warning',
    });
    if (!ok) return false;
  }

  _importCancelRequested = true;
  _setImportCancelButtonState(true);
  showImportStage(_t('Cancelling import...'));
  if (typeof GP !== 'undefined' && GP.clearDirtyReason) GP.clearDirtyReason('import_running');
  if (typeof updateGlobalJob === 'function') updateGlobalJob(_t('Cancelling import...'), 'import');
  if (_activeImportAbortController) {
    try {
      _activeImportAbortController.abort(new DOMException(_t('Import cancelled.'), 'AbortError'));
    } catch (_) {
      _activeImportAbortController.abort();
    }
  }
  return true;
}

function handleImportEvent(event) {  // eslint-disable-line no-unused-vars
  switch (event.type) {
    case 'stage':
      showImportStage(event.message);
      if (typeof updateGlobalJob === 'function') updateGlobalJob(event.message, 'import');
      break;
    case 'course':
      showImportStage(event.created
        ? _t('Created course:') + ' ' + event.name
        : _t('Found course:') + ' ' + event.name);
      appendImportLog(event.created ? '+' : '=', _t('Course:') + ' ' + event.code + ' \u2014 ' + event.name);
      break;
    case 'team':
      _importCounts.teams++;
      updateImportCounters();
      showImportStage(_t('Importing groups...') + ' (' + _importCounts.teams + ')');
      appendImportLog(event.created ? '+' : '~', _t('Group:') + ' ' + event.name);
      _globalBarImportProgress();
      break;
    case 'student':
      _importSeen.students.add(event.username);
      _importCounts.students = _importSeen.students.size;
      updateImportCounters();
      showImportStage(_t('Importing students...') + ' (' + _importCounts.students + ')');
      appendImportLog(event.created ? '+' : '~',
        _t('Student:') + ' ' + event.username + (event.name ? ' (' + event.name + ')' : ''));
      _globalBarImportProgress();
      break;
    case 'teacher': {
      const isNewTeacher = !_importSeen.teachers.has(event.username);
      _importSeen.teachers.add(event.username);
      _importCounts.teachers = _importSeen.teachers.size;
      updateImportCounters();
      showImportStage(_t('Importing members...') + ' (' + (_importCounts.students + _importCounts.teachers) + ')');
      if (isNewTeacher) {
        appendImportLog(event.created ? '+' : '~',
          _t('Teacher:') + ' ' + event.username + (event.name ? ' (' + event.name + ')' : ''));
      }
      _globalBarImportProgress();
      break;
    }
    case 'project':
      _importCounts.projects++;
      updateImportCounters();
      showImportStage(_t('Importing projects...') + ' (' + _importCounts.projects + ')');
      appendImportLog(event.created ? '+' : '~', _t('Project:') + ' ' + event.name);
      _globalBarImportProgress();
      break;
  }
}

function stopImportStatus(type, message, courseId) {  // eslint-disable-line no-unused-vars
  if (importStatusTimer) {
    clearInterval(importStatusTimer);
    importStatusTimer = null;
  }
  // Stop counter pulse animation
  const countersEl = document.getElementById('importCounters');
  if (countersEl) countersEl.classList.remove('import-counters-active');
  const box = document.getElementById('importStatusBox');
  const text = document.getElementById('importStatusText');
  const meta = document.getElementById('importStatusMeta');
  const spinner = document.getElementById('importStatusSpinner');
  if (!box || !text || !meta || !spinner) return;
  box.hidden = false;
  box.classList.remove('success', 'error');
  if (type === 'success') box.classList.add('success');
  if (type === 'error') box.classList.add('error');
  text.textContent = message;
  spinner.hidden = true;
  const elapsed = Math.floor((Date.now() - importStatusStartedAt) / 1000);
  meta.textContent = _t('Completed in') + ' ' + Math.max(elapsed, 0) + 's';
  if (courseId && type === 'success') {
    window._pendingSyncCourseId = courseId;
  }
}

/** Start elapsed-time timer for import status meta display. */
function startImportElapsedTimer() {  // eslint-disable-line no-unused-vars
  importStatusStartedAt = Date.now();
  importStatusTimer = setInterval(function() {
    const elapsed = Math.floor((Date.now() - importStatusStartedAt) / 1000);
    const meta = document.getElementById('importStatusMeta');
    if (meta) meta.textContent = _t('Elapsed:') + ' ' + elapsed + 's';
  }, 1000);
}

// -- Edge case: network offline during import --
window.addEventListener('offline', function() {
  if (importInProgress) {
    showImportStage(_t('Warning: Network disconnected - import may still be running on server...'));
  }
});

window.addEventListener('online', function() {
  if (importInProgress) {
    showImportStage(_t('Network reconnected - waiting for import stream...'));
  }
});

/**
 * Read an SSE response stream and dispatch events via handleImportEvent().
 * Returns the final 'done' event object, or throws on error.
 */
async function readImportSSEStream(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let sseBuffer = '';
  let result = null;

  while (true) {  // eslint-disable-line no-constant-condition
    const { done, value } = await reader.read();
    if (done) break;
    const rawChunk = decoder.decode(value, { stream: true });
    sseBuffer += rawChunk;
    const parts = sseBuffer.split('\n\n');
    sseBuffer = parts.pop();
    for (const part of parts) {
      for (const line of part.split('\n')) {
        if (!line.startsWith('data: ')) continue;
        try {
          const evt = JSON.parse(line.slice(6));
          if (evt.type === 'done') {
            // Safety net: if server sent teachers_list in done but
            // individual teacher SSE events never arrived, inject them
            // now so counters and import log are populated.
            if (evt.teachers_list && evt.teachers_list.length && _importSeen.teachers.size === 0) {
              for (const uname of evt.teachers_list) {
                handleImportEvent({ type: 'teacher', username: uname, name: '', created: false, role_label: 'teacher' });
              }
            }
            result = evt;
          } else if (evt.type === 'error') {
            throw new Error(evt.message);
          } else {
            handleImportEvent(evt);
          }
        } catch (parseErr) {
          if (parseErr.message && !parseErr.message.includes('JSON')) throw parseErr;
        }
      }
      // Break immediately after receiving done - don't wait for
      // reader.read() which may throw if the server closes the
      // connection before the client reads again.
      if (result) break;
    }
    if (result) break;
  }

  if (!result) throw new Error('Import stream ended without result');
  return result;
}

/** Format import result into a human-readable summary string. */
function formatImportResult(result) {  // eslint-disable-line no-unused-vars
  const totalStudents = result.students_total != null ? result.students_total : (result.students_created || 0);
  const totalTeachers = result.teachers_total != null ? result.teachers_total : (result.teachers_created || 0);
  const syncInfo = result.sync_jobs_enqueued
    ? ' \u2022 ' + _t('Sync queued:') + ' ' + result.sync_jobs_enqueued
    : '';
  const cleanupInfo = result.projects_deactivated
    ? ' \u2022 ' + _t('Deactivated stale projects:') + ' ' + result.projects_deactivated
    : '';
  let instrInfo = ', ' + totalTeachers + ' ' + _t('teachers');
  if (totalTeachers && result.teachers_list && result.teachers_list.length) {
    instrInfo += ' (' + result.teachers_list.join(', ') + ')';
  }
  return result.teams_created + ' ' + _t('groups') + ', ' + totalStudents + ' ' + _t('students') + instrInfo + ', ' + result.projects_created + ' ' + _t('projects') + cleanupInfo + syncInfo;
}

function _finishImportGlobalJob(message, status, fallbackType, fallbackDuration) {
  const handledByGlobal = typeof completeGlobalJob === 'function'
    && completeGlobalJob('import', message, status);
  if (!handledByGlobal) {
    if (typeof flashToast === 'function') {
      flashToast(message, fallbackType, fallbackDuration);
    } else if (typeof showToast === 'function') {
      showToast(message, fallbackType, fallbackDuration);
    } else if (typeof hideGlobalJob === 'function') {
      hideGlobalJob('import');
    }
  }
  return handledByGlobal;
}

function _isImportCancelError(err) {
  return Boolean(
    _importCancelRequested
    || err?.name === 'AbortError'
    || /cancelled|canceled/i.test(err?.message || '')
  );
}

/** Common import-done handling: stop status, set flags, transition global bar. */
function finalizeImportSuccess(result) {  // eslint-disable-line no-unused-vars
  const summary = formatImportResult(result);
  const completionMsg = _t('Imported:') + ' ' + summary;
  stopImportStatus(
    'success',
    _t('Done:') + ' ' + summary,
    result.sync_jobs_enqueued > 0 ? result.course_id : null
  );
  sessionStorage.removeItem('activeImport');
  importCompleted = true;

  _finishImportGlobalJob(completionMsg, 'done', 'success', 10000);
  if (window._pendingSyncCourseId) {
    const syncCount = result.sync_jobs_enqueued || 0;
    const toastMsg = syncCount > 0
      ? _t('Sync started for') + ' ' + syncCount + ' ' + _t('groups') + '...'
      : _t('Syncing data...');
    // Use flashToast so the sync-start toast survives page navigation.
    if (typeof flashToast === 'function') flashToast(toastMsg, 'info', 8000);
    else if (typeof showToast === 'function') showToast(toastMsg, 'info', 8000);
    // Global bar uses the unified _courseSyncMsg format (queued only at
    // this point - running ramps up as workers pick the jobs) so the
    // bar never flashes a generic "Syncing data..." placeholder that
    // gets overridden by the SSE-driven "Syncing: X/Y groups done" line.
    const barMsg = (typeof window._courseSyncMsg === 'function')
      ? window._courseSyncMsg('', 0, syncCount)
      : toastMsg;
    if (typeof deferGlobalJob === 'function') deferGlobalJob(barMsg, window._pendingSyncCourseId);
    window._pendingSyncCourseId = null;
  }

  sessionStorage.setItem('importJustCompleted', '1');
  // Ensure all toasts are persisted before the impending page navigation.
  if (typeof _preserveFlashToast === 'function') _preserveFlashToast();
}

/** Common import-error handling. */
function finalizeImportError(err) {  // eslint-disable-line no-unused-vars
  const isCancel = _isImportCancelError(err);
  if (isCancel) {
    const msg = _t('Import cancelled.');
    stopImportStatus('error', msg);
    sessionStorage.removeItem('activeImport');
    _finishImportGlobalJob(msg, 'error', 'warning', 5000);
    return;
  }

  const isNetworkError = /network|fetch|abort|timeout/i.test(err.message || '');
  const hasProgress = Boolean(
    _importCounts.teams > 0
    || _importCounts.students > 0
    || _importCounts.teachers > 0
    || _importCounts.projects > 0
    || (_importSeen?.students?.size || 0) > 0
    || (_importSeen?.teachers?.size || 0) > 0
  );
  if (isNetworkError && hasProgress) {
    // Import data was likely committed server-side; the SSE stream
    // just closed before the "done" event arrived.  Show a softer
    // warning instead of a scary red error.
    const msg = _t('Connection lost during import - data was likely saved. Reloading...');
    stopImportStatus('success', msg);
    flashToast(msg, 'warning', 6000);
    sessionStorage.removeItem('activeImport');
    sessionStorage.setItem('importJustCompleted', '1');
    if (typeof _preserveFlashToast === 'function') _preserveFlashToast();
    setTimeout(() => {
      if (typeof reloadKeepScroll === 'function') {
        reloadKeepScroll();
      } else {
        const freshUrl = window.GP?.cacheBustedCurrentUrl?.() || window.location.href;
        window.location.assign(freshUrl);
      }
    }, 1500);
    return;
  }
  stopImportStatus('error', _t('Import failed:') + ' ' + err.message);
  sessionStorage.removeItem('activeImport');
  _finishImportGlobalJob(err.message || _t('Import failed'), 'error', 'danger', 7000);
}

/**
 * Bind the shared modal lifecycle to import progress without replacing it.
 * Call once from DOMContentLoaded or inline on pages that use import.
 */
function initImportModals() {  // eslint-disable-line no-unused-vars
  GP.enableFormDirtyGuard?.('importGitlabCourseModal');
  const cancelBtn = document.getElementById('importGitlabCourseCancelBtn');
  if (cancelBtn && !cancelBtn._importCancelBound) {
    cancelBtn.addEventListener('click', (event) => {
      if (!importInProgress) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      cancelActiveImport();
    });
    cancelBtn._importCancelBound = true;
  }

  const form = document.getElementById('importGitlabCourseForm');
  const urlField = form?.group_url || form?.querySelector('[name="group_url"]');
  if (urlField && !urlField._importValidationBound) {
    urlField.addEventListener('input', () => {
      if (typeof clearFieldError === 'function') clearFieldError(urlField);
    });
    urlField._importValidationBound = true;
  }

  if (_importModalsInitialized) return;
  _importModalsInitialized = true;

  document.addEventListener('gp:modal-open', (event) => {
    if (event.detail?.id === 'importGitlabCourseModal' && !importInProgress) resetImportStatus();
  });
  document.addEventListener('modal-closed', (event) => {
    if (event.detail?.id === 'importGitlabCourseModal') {
      if (window._pendingSyncCourseId) {
        hideGlobalJob('import');
        const _barMsg = (typeof window._courseSyncMsg === 'function')
          ? window._courseSyncMsg('', 0, 0)
          : _t('Syncing:');
        deferGlobalJob(_barMsg, window._pendingSyncCourseId);
        window._pendingSyncCourseId = null;
        sessionStorage.removeItem('activeImport');
      } else if (importCompleted) {
        hideGlobalJob('import');
        sessionStorage.removeItem('activeImport');
      } else if (importInProgress && !importCompleted) {
        promoteGlobalJob('import');
      }
    }
  });
}

/**
 * Build the import payload from the standard import form and submit via SSE.
 * @param {Object} extraPayload - page-specific fields (e.g. target_course_id, course_code)
 * @param {Function} onSuccess  - (result) => void, called after successful import
 */
async function submitGitLabImport(extraPayload, onSuccess) {  // eslint-disable-line no-unused-vars
  const { t } = GP;
  const _lock = window.GP?.withUiLock || (async (_k, fn) => fn());
  try {
    await _lock('gitlab:import', async () => {
      if (isGlobalJobRunning('import') && !confirmProcessRestart('import', 'GitLab import')) return;

      const form = document.getElementById('importGitlabCourseForm');
      if (!form) return;
      const groupUrlField = form.group_url || form.querySelector('[name="group_url"]');
      const validationMessage = validateGitLabImportUrl(groupUrlField?.value || '');
      if (validationMessage) {
        if (typeof showFieldError === 'function' && groupUrlField) showFieldError(groupUrlField, validationMessage);
        if (typeof showToast === 'function') showToast(validationMessage, 'warning');
        return;
      }
      if (typeof clearFieldError === 'function' && groupUrlField) clearFieldError(groupUrlField);

      const autoSyncField = form.auto_sync || form.querySelector('input[name="auto_sync"]');
      const autoSync = autoSyncField ? autoSyncField.checked : true;
      const oneTeamPerProjectField = form.one_team_per_project || form.querySelector('input[name="one_team_per_project"]');
      const oneTeamPerProject = oneTeamPerProjectField
        ? (oneTeamPerProjectField.type === 'checkbox' ? oneTeamPerProjectField.checked : oneTeamPerProjectField.value === 'true')
        : false;
      const includeSubgroupsField = form.include_subgroups || form.querySelector('[name="include_subgroups"]');
      const includeSubgroups = includeSubgroupsField
        ? (includeSubgroupsField.tagName === 'SELECT' ? includeSubgroupsField.value === 'true' : includeSubgroupsField.value === 'true')
        : true;
      const payload = Object.assign({
        group_url: groupUrlField.value,
        include_subgroups: includeSubgroups,
        one_team_per_project: oneTeamPerProject,
        auto_sync: autoSync,
        csrf_token: _csrfToken
      }, extraPayload || {});

      _activeImportAbortController = new AbortController();
      _importCancelRequested = false;
      setImportModalBusy(true);
      try {
        showImportStage(t('Checking for existing data...'));
        const box = document.getElementById('importStatusBox');
        if (box) box.hidden = false;
        const dupInfo = await checkImportDuplicate(payload, _activeImportAbortController.signal);
        if (dupInfo && dupInfo.has_duplicate) {
          const choice = await showDuplicateWarning(dupInfo);
          if (choice === 'cancel') { resetImportStatus(); return; }
        }
        sessionStorage.setItem('activeImport', JSON.stringify({ started: Date.now() }));
        resetImportStatus();
        showImportStage(t('Starting import...'));
        if (typeof deferGlobalJob === 'function') deferGlobalJob(t('Importing course from GitLab...'), 'import', { localIndicatorSelector: '#importStatusBox' });
        startImportElapsedTimer();

        const response = await apiCall('/api/v1/courses/import/gitlab-group/stream', 'POST', payload, {
          raw: true,
          timeoutMs: 0,
          maxRetries: 0,
          signal: _activeImportAbortController.signal,
          abortMessage: t('Import cancelled.'),
        });
        const result = await readImportSSEStream(response);
        finalizeImportSuccess(result);
        try { if (onSuccess) { onSuccess(result); return; } } catch (cbErr) { console.warn('Import onSuccess callback error:', cbErr); }
      } catch (err) {
        finalizeImportError(err);
      } finally {
        setImportModalBusy(false);
        _resetImportAbortState();
      }
    });
  } catch (lockErr) {
    if (lockErr.code !== 'LOCKED') throw lockErr;
  }
}

/* -- Import duplicate check -- */
async function checkImportDuplicate(payload, signal) {  // eslint-disable-line no-unused-vars
  try {
    const body = { group_url: payload.group_url || '' };
    if (payload.course_code) body.course_code = payload.course_code;
    if (payload.academic_year) body.academic_year = payload.academic_year;
    if (payload.semester) body.semester = payload.semester;
    if (payload.target_course_id) body.target_course_id = payload.target_course_id;
    return await apiCall('/api/v1/courses/check-import-duplicate', 'POST', body, {
      maxRetries: 0,
      signal: signal || null,
      abortMessage: _t('Import cancelled.'),
    });
  } catch (e) {
    if (_isImportCancelError(e)) throw e;
    console.warn('Duplicate check failed:', e);
    return null;
  }
}

/* Async because it asks on THE dialog (GP.confirmDialog) rather than
   `window.confirm`, which cannot be themed, ignores dark mode, carries no danger
   accent and reads as if the page broke. Its one caller already sits in an async
   function, so the change stops there. `.gp-confirm-message` is
   `white-space: pre-line`, so the per-project list below still reads as a list. */
async function showDuplicateWarning(dupInfo) {  // eslint-disable-line no-unused-vars
  if (!dupInfo || !dupInfo.has_duplicate) return 'proceed';

  const msgs = [];

  if (dupInfo.matching_course) {
    const mc = dupInfo.matching_course;
    msgs.push(_t('A course with the same code/year/semester already exists:'));
    msgs.push('  ' + mc.code + ' - ' + mc.name + ' (' + GP.periodLabel(mc.academic_year, mc.semester) + ')');
    msgs.push('  ' + _t('Groups') + ': ' + mc.team_count + ', ' + _t('Students') + ': ' + mc.student_count + ', ' + _t('Projects') + ': ' + mc.project_count);
    msgs.push('');
    msgs.push(_t('Re-importing will UPDATE existing records (upsert), not create duplicates.'));
  }

  if (dupInfo.matching_teams && dupInfo.matching_teams.length > 0) {
    msgs.push('');
    msgs.push(_t('Groups that already exist') + ' (' + dupInfo.matching_teams.length + '):');
    dupInfo.matching_teams.slice(0, 5).forEach(function(team) {
      msgs.push('  \u2022 ' + team.name + (team.project_count ? ' (' + team.project_count + ' ' + _t('projects') + ')' : ''));
    });
    if (dupInfo.matching_teams.length > 5) {
      msgs.push('  \u2026' + _t('and') + ' ' + (dupInfo.matching_teams.length - 5) + ' ' + _t('more'));
    }
  }

  if (dupInfo.cross_course_projects && dupInfo.cross_course_projects.length > 0) {
    msgs.push('');
    msgs.push(_t('Projects already registered under OTHER courses') + ' (' + dupInfo.cross_course_projects.length + '):');
    dupInfo.cross_course_projects.slice(0, 5).forEach(function(p) {
      msgs.push('  \u2022 ' + (p.gitlab_project_name || p.gitlab_project_path) + ' \u2192 ' + _t('course') + ' "' + (p.current_course_code || '?') + '", ' + _t('group') + ' "' + (p.current_team_name || '?') + '"');
    });
    if (dupInfo.cross_course_projects.length > 5) {
      msgs.push('  \u2026' + _t('and') + ' ' + (dupInfo.cross_course_projects.length - 5) + ' ' + _t('more'));
    }
    msgs.push('');
    msgs.push(_t('These projects will be MOVED to the new course/group!'));
  }

  const ok = await GP.confirmDialog({
    title: _t('This data already exists'),
    message: msgs.join('\n'),
    confirmText: _t('Proceed (update existing)'),
    variant: 'danger',
  });
  return ok ? 'proceed' : 'cancel';
}

window.cancelActiveImport = cancelActiveImport;
if (typeof GP !== 'undefined') {
  GP.cancelActiveImport = cancelActiveImport;
}
