  const GP = window.GP;
  GP.runPageCleanup();

  // Scoped variables for cleanable listeners and timers across files
  let onDOMContentLoadedCore = null;
  let onAlpineInitialized = null;
  let onDOMContentLoadedScoring = null;
  let onDocumentClickSection = null;
  let onDocumentChangeSection = null;
  let onDocumentClickCheck = null;
  let onDocumentClickPatternPreset = null;
  let onModalClosed = null;
  let onDocumentChangeAdvanced = null;
  let onHealthChange = null;
  let onVisibilityChange = null;
  let onBeforeUnload = null;
  let onGlobalJobStart = null;
  let onJobComplete = null;
  let onDocumentClickAdvanced = null;
  let onBeforeSwap = null;

  const { apiCall, showToast, setButtonLoading, copyToClipboard, escapeHtml, withUiLock: _lock } = GP;
  const { t } = GP;
  const { openModal, closeModal } = window;
  const forceCloseModal = window.forceCloseModal;
  const clearModalDirty = window.clearModalDirty;

  /* -- Role config -- */
  let _cfg = {};
  try { const _ce = document.getElementById('gp-page-config'); if (_ce) _cfg = JSON.parse(_ce.textContent); } catch (_) { /* */ }
  const _canEdit = !!_cfg.canEdit;
  const _isAdmin = !!_cfg.isAdmin;
  const _courseId = _cfg.courseId;
  const _COURSE_WRITE_PROCESSES = ['sync', 'import', 'run_checks'];
  const _courseProcessScope = _courseId ? 'course:' + _courseId : '';

  function _guardCourseWrite() {
    if (!_courseProcessScope) return true;
    return GP.guardProcessAction(_COURSE_WRITE_PROCESSES, { scope: _courseProcessScope });
  }

  const _esc = escapeHtml;

  /* Alpine.js component for LLM resource URL list.
     Registered as a global factory so it is available before Alpine starts. */
  window.llmResourceUrls = function llmResourceUrls() {
    const el = document.getElementById('llm-resource-urls-data');
    let initial = [];
    try { initial = JSON.parse(el ? el.textContent : '[]'); } catch (_) { initial = []; }
    return {
      entries: (initial && initial.length) ? initial : [],
      get entriesJson() {
        try { return JSON.stringify(this.entries); } catch (_) { return '[]'; }
      },
      addEntry() { this.entries.push({ url: '', label: '' }); },
      removeEntry(idx) { this.entries.splice(idx, 1); }
    };
  };

  function initLlmPromptPresets() {
    const presetsEl = document.getElementById('llm-prompt-presets-data');
    let presets = {};
    try { presets = JSON.parse(presetsEl ? presetsEl.textContent : '{}'); } catch (_) { presets = {}; }

    function getSelectedType() {
      return document.getElementById('llm_course_type')?.value || 'default';
    }

    function loadPresetIntoTextarea(withFeedback) {
      const ta = document.getElementById('llm_custom_prompt');
      if (!ta) return;
      const text = presets[getSelectedType()] || presets.default || '';
      ta.value = text;
      ta.dispatchEvent(new Event('input', { bubbles: true }));
      if (withFeedback === true) {
        showToast(t('Preset loaded into the prompt editor'), 'success');
      }
    }

    document.getElementById('btnLoadPreset')?.addEventListener('click', function () {
      loadPresetIntoTextarea(true);
    });

    document.getElementById('llm_course_type')?.addEventListener('change', function () {
      const ta = document.getElementById('llm_custom_prompt');
      if (!ta) return;
      const current = ta.value.trim();
      const matchesPreset = Object.values(presets).some(function (preset) {
        return String(preset || '').trim() === current;
      });
      if (!current || matchesPreset) {
        loadPresetIntoTextarea();
      }
    });
  }

  /* -- Trigger full sync from settings page -- */
  async function _triggerSyncFromSettings(courseId) {
    const syncScope = 'course:' + courseId;
    if (window.GP?.guardProcessAction && !window.GP.guardProcessAction(['sync', 'import', 'run_checks'], { scope: syncScope })) return;
    // Instant "Connecting..." bar before the POST (the GitLab pre-flight can
    // take several seconds; the bar used to surface only via the delayed
    // /sync/active reconciler).
    if (typeof connectGlobalJob === 'function') {
      connectGlobalJob(courseId, t('Connecting to GitLab...') || 'Connecting to GitLab...', { jobKind: 'course_sync', courseId: String(courseId || '') });
    }
    try {
      const result = await apiCall('/api/v1/courses/' + courseId + '/sync-all', 'POST');
      if (result.enqueued > 0) {
        showToast(t('Sync started for all groups'), 'info');
        const _msg = (t('Syncing data:') || 'Syncing data:') + ' ' + result.enqueued + ' ' + (t('groups queued...') || 'groups queued...');
        // Promote the connecting bar to the real running message.
        if (typeof showGlobalJob === 'function') {
          showGlobalJob(_msg, courseId, { jobKind: 'course_sync', courseId: String(courseId || '') });
        } else if (typeof deferGlobalJob === 'function') {
          deferGlobalJob(_msg, courseId, { jobKind: 'course_sync', courseId: String(courseId || '') });
        }
      } else {
        if (typeof hideGlobalJob === 'function') hideGlobalJob(courseId);
        showToast(result.message || t('No groups to sync'), 'info');
      }
    } catch (err) {
      const _emsg = err.message || t('Failed to start sync') || 'Failed to start sync';
      if (typeof failGlobalJob === 'function') {
        failGlobalJob(courseId, _emsg);
      } else {
        showToast(_emsg, 'danger');
      }
    }
  }

  /* ==========================================
   *  Unsaved changes guard
   *  Source-of-truth: GP.initSaveGuard tracks each form's dirty state
   *  via snapshot diff and toggles GP.addDirtyReason / clearDirtyReason
   *  accordingly. Reading dirty state goes through GP.hasDirtyReason -
   *  no separate boolean, no duplicate input listeners that would
   *  mark the form dirty even when values revert to original.
   * ========================================== */
  function _isSettingsDirty() {
    return GP.hasDirtyReason('settings_form');
  }

  /* Save-button guards - disable until form is dirty */
  GP.initSaveGuard('#courseSettingsForm', '#btnSaveSettings', { dirtyKey: 'settings_form' });

  /* ==========================================
   *  Collect form data -> API payloads
   * ========================================== */
  // Snapshot of identity fields at page load - used to detect changes to
  // code / academic_year / semester, which are rarely edited intentionally
  // after a course is live (they drive the uq_courses_code_year_semester
  // constraint, historical report headers, and archive-sweep matching).
  // A single confirm() keeps accidental mid-semester tweaks from silently
  // breaking dashboards or triggering 409 duplicates.
  //
  // course_semester is rendered via the `select_field` macro as a hidden
  // input whose `value` is bound to Alpine (`:value="selected"`), so at
  // module-evaluation time the DOM value is still empty. We defer the
  // snapshot until after Alpine has initialised the x-data component.
  const _identitySnapshot = { code: '', academic_year: '', semester: '', semester_start_date: '', semester_end_date: '' };
  let _identitySnapshotReady = false;
  function _captureIdentitySnapshot() {
    _identitySnapshot.code = document.getElementById('course_code')?.value?.trim() || '';
    _identitySnapshot.academic_year = document.getElementById('course_academic_year')?.value?.trim() || '';
    _identitySnapshot.semester = document.getElementById('course_semester')?.value || '';
    _identitySnapshot.semester_start_date = document.getElementById('semester_start_date')?.value || '';
    _identitySnapshot.semester_end_date = document.getElementById('semester_end_date')?.value || '';
    _identitySnapshotReady = true;
  }
  if (document.readyState === 'loading') {
    onDOMContentLoadedCore = () => {
      // One more tick for Alpine to evaluate x-data and propagate :value="selected".
      setTimeout(_captureIdentitySnapshot, 0);
    };
    document.addEventListener('DOMContentLoaded', onDOMContentLoadedCore, { once: true });
  } else {
    setTimeout(_captureIdentitySnapshot, 0);
  }
  // Re-capture on alpine:initialized as a safety net (fires once per page).
  onAlpineInitialized = () => {
    if (!_identitySnapshotReady) _captureIdentitySnapshot();
  };
  document.addEventListener('alpine:initialized', onAlpineInitialized, { once: true });

  function collectCourseMetadata() {
    return {
      code: document.getElementById('course_code')?.value?.trim() || '',
      name: document.getElementById('course_name')?.value?.trim() || '',
      academic_year: document.getElementById('course_academic_year')?.value?.trim() || '',
      semester: document.getElementById('course_semester')?.value || 'winter',
      description: document.getElementById('course_description')?.value?.trim() || '',
    };
  }

  function collectSettings() {
    const data = {};

    // No `gitlab_group_path` here: the settings page has no such input (the
    // server derives the value from the teams' GitLab paths), so the lookup
    // this used to do always returned null.

    // Thresholds
    const greenEl = document.getElementById('green_threshold');
    const yellowEl = document.getElementById('yellow_threshold');
    if (greenEl) data.green_threshold = parseFloat(greenEl.value) || 0;
    if (yellowEl) data.yellow_threshold = parseFloat(yellowEl.value) || 0;

    // The convention patterns are no longer collected here: they live in each
    // check's own configuration (R02 branch regex, R03 test globs, R05 template
    // headings) and are persisted with that check, so there are no top-level
    // pattern inputs on this form to read.

    // Merge deadline is configured per-week in Weekly Deadlines & Expected
    // Checks (course-wide default removed - redundant with per-week overrides).
    // MR creation deadline stays JSON-import only.

    // Semester start date
    const startDate = document.getElementById('semester_start_date');
    if (startDate) data.semester_start_date = startDate.value || null;
    const endDate = document.getElementById('semester_end_date');
    if (endDate) data.semester_end_date = endDate.value || null;

    // Skip auto-archive checkbox (per-course override)
    const skipArchive = document.getElementById('skip_auto_archive');
    if (skipArchive) data.skip_auto_archive = !!skipArchive.checked;

    // Weekly deadlines (JSON)
    const weeklyEl = document.querySelector('textarea[name="weekly_deadlines"]');
    if (weeklyEl) {
      try {
        data.weekly_deadlines = JSON.parse(weeklyEl.value || '[]');
      } catch (e) {
        // Will be caught in validation
        data.weekly_deadlines = weeklyEl.value; // send raw, server will validate
      }
    }

    // AI analysis configuration - previously never collected, so the whole
    // "AI Analysis Configuration" card silently failed to save.
    const llmType = document.getElementById('llm_course_type');
    if (llmType) data.llm_course_type = llmType.value || 'default';
    const llmPrompt = document.getElementById('llm_custom_prompt');
    if (llmPrompt) data.llm_custom_prompt = llmPrompt.value;
    const llmUrlsJson = document.getElementById('llm_resource_urls_json');
    if (llmUrlsJson) {
      try { data.llm_resource_urls = JSON.parse(llmUrlsJson.value || '[]'); }
      catch (_) { data.llm_resource_urls = []; }
    }

    // Built-in check enable/disable now travels WITH the settings save instead
    // of firing its own PUT per checkbox. Besides matching "everything on this
    // page is applied by Update Settings", it removes the 409 trap: every
    // built-in check optimistic-locks against the one CourseSettings row, so a
    // per-toggle PUT invalidated the page's own token mid-edit.
    // Only sent once the checks table has actually loaded, so a save that
    // happens before load can never blank enabled_checks.
    if (Array.isArray(_allChecks) && _allChecks.length) {
      data.enabled_checks = _allChecks
        .filter(function (c) { return /^R/i.test(c.check_code || '') && c.is_active; })
        .map(function (c) { return c.check_code; });
    }

    return data;
  }

  /* ==========================================
   *  Client-side validation
   * ========================================== */
  function validateSettings(metadata) {
    const errors = [];

    if (!metadata.code) errors.push(t('Course code is required'));
    if (!metadata.name) errors.push(t('Course name is required'));
    if (!metadata.academic_year) errors.push(t('Academic year is required'));

    // Validate weekly deadlines JSON
    const weeklyEl = document.querySelector('textarea[name="weekly_deadlines"]');
    if (weeklyEl && weeklyEl.value.trim()) {
      try {
        const parsed = JSON.parse(weeklyEl.value);
        if (!Array.isArray(parsed)) {
          errors.push(t('Weekly deadlines must be a JSON array'));
        }
      } catch (e) {
        errors.push(t('Invalid JSON in weekly deadlines') + ': ' + e.message);
      }
    }

    return errors;
  }

  /* ==========================================
   *  Main settings form - AJAX submit
   * ========================================== */
  const settingsFormAjax = document.getElementById('courseSettingsForm');
  let _settingsSaveInFlight = false;
  let _pendingSettingsEvent = null;
  if (settingsFormAjax) {
    settingsFormAjax.addEventListener('submit', async function (e) {
      e.preventDefault();
      const courseId = this.dataset.courseId;
      const btn = document.getElementById('btnSaveSettings');

      if (!_isSettingsDirty()) { showToast(t('No changes to save'), 'info'); return; }

      const metadata = collectCourseMetadata();
      const settings = collectSettings();

      if (!_canEdit) { showToast(t('You do not have permission to save settings'), 'warning'); return; }
      if (!_guardCourseWrite()) return;
      const errors = validateSettings(metadata);
      if (errors.length) {
        errors.forEach(function (err) { showToast(err, 'warning'); });
        return;
      }

      // Guard against accidental changes to identity fields on an existing
      // course.  These drive the unique constraint + historical reports,
      // so a single confirm() is enough to stop fat-finger mistakes while
      // still allowing legitimate fixes (typos, semester type correction).
      // Skip the check entirely if the snapshot never got captured (e.g.
      // user clicked Save before Alpine finished booting) - in that case
      // we cannot trust the comparison, and a false positive is worse than
      // a missed warning.
      const idChanges = [];
      if (_identitySnapshotReady) {
        if (metadata.code !== _identitySnapshot.code) {
          idChanges.push(t('Course Code') + ': ' + _identitySnapshot.code + ' -> ' + metadata.code);
        }
        /* The year and the semester are one fact - the term - so a change to
           either reads as one line, in the words the rest of the app uses:
           "2025/2026 · Summer -> 2026/2027 · Summer", not "summer -> winter". */
        if (metadata.academic_year !== _identitySnapshot.academic_year
            || metadata.semester !== _identitySnapshot.semester) {
          idChanges.push(t('Academic period') + ': '
            + GP.periodLabel(_identitySnapshot.academic_year, _identitySnapshot.semester)
            + ' -> ' + GP.periodLabel(metadata.academic_year, metadata.semester));
        }
      }
      if (idChanges.length) {
        const msg = t('You are changing the course identity fields:') + '\n\n' +
          idChanges.join('\n') + '\n\n' +
          t('This affects historical reports, dashboards, and the uniqueness check. Continue?');
        if (!await GP.confirmDialog({ message: msg, confirmText: t('Confirm'), variant: 'warning' })) { return; }
      }

      // Warn loudly when the semester start/end window is being changed.
      // The semester floor is the lower bound for every dashboard query,
      // compliance scoring, and GitLab sync `since=` parameter; moving it
      // re-scopes the entire course view in one click. We only prompt when
      // a value was already present (i.e. the teacher is *changing* a
      // configured window, not setting one for the first time).
      if (_identitySnapshotReady) {
        const oldStart = _identitySnapshot.semester_start_date || '';
        const newStart = (settings.semester_start_date || '');
        const oldEnd = _identitySnapshot.semester_end_date || '';
        const newEnd = (settings.semester_end_date || '');
        const semChanges = [];
        if (oldStart && oldStart !== newStart) {
          semChanges.push(t('Semester Start Date') + ': ' + oldStart + ' -> ' + (newStart || t('(cleared)')));
        }
        if (oldEnd && oldEnd !== newEnd) {
          semChanges.push(t('Semester End Date') + ': ' + oldEnd + ' -> ' + (newEnd || t('(cleared)')));
        }
        if (semChanges.length) {
          const semMsg = t('You are changing the active semester window:') + '\n\n' +
            semChanges.join('\n') + '\n\n' +
            /* Two catalogue keys, not one with the line breaks inside: that key
               matched nothing, so this warning was the one English paragraph
               in the Slovak save flow. */
            t('All dashboards, compliance scoring, and the next GitLab sync will use the NEW window. Older GitLab activity (commits, MRs, issues, pipelines) will be hidden from current-semester views and excluded from compliance checks. Existing data is NOT deleted - reverting the date restores the old view.') + '\n\n' + t('Continue?');
          if (!await GP.confirmDialog({ message: semMsg, confirmText: t('Confirm'), variant: 'warning' })) { return; }
        }
      }

      try {
        await _lock('saveSettings:' + courseId, async () => {
          if (btn) setButtonLoading(btn, true);
          const courseUpdatedAt = settingsFormAjax.dataset.courseUpdatedAt || undefined;
          const settingsUpdatedAt = settingsFormAjax.dataset.settingsUpdatedAt || undefined;
          if (courseUpdatedAt) metadata.expected_updated_at = courseUpdatedAt;
          if (settingsUpdatedAt) settings.expected_updated_at = settingsUpdatedAt;
          const pendingEdits = Object.assign({}, _pendingCheckEdits);
          const pendingActive = Object.assign({}, _pendingCustomActive);
          const checks = {};
          for (const code of new Set(Object.keys(pendingActive).concat(Object.keys(pendingEdits)))) {
            const check = _allChecks.find(function (x) { return x.check_code === code; });
            checks[code] = Object.assign({}, pendingEdits[code] || {});
            if (Object.prototype.hasOwnProperty.call(pendingActive, code)) {
              checks[code].is_active = pendingActive[code];
            }
            if (check && check.updated_at) checks[code].expected_updated_at = check.updated_at;
          }
          _settingsSaveInFlight = true;
          const result = await apiCall('/dashboard/courses/' + courseId + '/settings', 'POST', {
            course: metadata, settings: settings, checks: checks,
          });
          settingsFormAjax.dataset.courseUpdatedAt = result.course_updated_at || '';
          settingsFormAjax.dataset.settingsUpdatedAt = result.settings_updated_at || '';
          document.getElementById('expected_course_updated_at').value = result.course_updated_at || '';
          document.getElementById('expected_settings_updated_at').value = result.settings_updated_at || '';
          _allChecks.forEach(function (check) {
            check.updated_at = check.is_builtin ? result.settings_updated_at
              : ((result.check_updated_at || {})[check.check_code] || check.updated_at);
            const token = document.getElementById('check-updated-at-' + check.check_code);
            if (token) token.value = check.updated_at || '';
          });
          Object.keys(pendingActive).forEach(function (code) {
            if (_pendingCustomActive[code] === pendingActive[code]) delete _pendingCustomActive[code];
          });
          Object.keys(pendingEdits).forEach(function (code) {
            if (_pendingCheckEdits[code] === pendingEdits[code]) delete _pendingCheckEdits[code];
          });
          for (const key of ['code', 'academic_year', 'semester']) _identitySnapshot[key] = metadata[key];
          for (const key of ['semester_start_date', 'semester_end_date']) {
            if (Object.prototype.hasOwnProperty.call(settings, key)) _identitySnapshot[key] = settings[key] || '';
          }

          if (!settingsFormAjax.isConnected) return;
          GP.resetSaveGuard('#courseSettingsForm', settingsFormAjax);
          showToast(t('Settings saved successfully'), 'success');

          // Offer full sync so GitLab data is re-evaluated with new settings
          setTimeout(async () => {
            if (!settingsFormAjax.isConnected || GP.hasUnsavedState()) return;
            if (await GP.confirmDialog({
              title: t('Run a full sync?'),
              /* One catalogue key per sentence - a key with line breaks inside
                 matched nothing and the prompt came up in English. */
              message: t('Settings saved. Scores will be recalculated automatically.') + '\n\n'
                + t('Would you also like to run a full sync to re-fetch data from GitLab?') + '\n'
                + t('(Recommended after changing branch patterns, test paths, or Docker settings)'),
              confirmText: t('Confirm'),
              variant: 'confirm',
            })) {
              _triggerSyncFromSettings(courseId);
            }
          }, 400);
        });
      } catch (err) {
        if (!settingsFormAjax.isConnected) return;
        if (err.code !== 'LOCKED') {
          if (err.status === 409) {
            showToast(t('This page was modified by another user. Please reload.'), 'warning');
          } else {
            showToast(err.message || t('Failed to save settings'), 'danger');
          }
        }
      } finally {
        _settingsSaveInFlight = false;
        if (_pendingSettingsEvent) {
          const pending = _pendingSettingsEvent;
          _pendingSettingsEvent = null;
          handleSettingsEvent(pending);
        }
        if (btn) setButtonLoading(btn, false);
      }
    });
  }

  /* ==========================================
   *  Init helpers
   * ========================================== */
  function initSettingsForm() {
    if (_courseId) {
      /* Hydrate the initial server-rendered checks without replacing their rows. */
      let _checksInline = null;
      try {
        const _el = document.getElementById('gp-checks-first');
        if (_el) _checksInline = JSON.parse(_el.textContent || 'null');
      } catch (_) { /* fall through to fetch */ }
      if (_checksInline && Array.isArray(_checksInline.checks)) {
        /* Defer one microtask: initSettingsForm() runs synchronously (line ~559)
           BEFORE this file's _allChecks / _activeFilter / CATEGORY_* bindings
           below are initialized, so rendering inline right here would touch them
           in their temporal dead zone. The fetch path is safe only because its
           await already yields past those declarations; the inline path has no
           await, so it must yield explicitly. */
        Promise.resolve().then(function () {
          loadAllChecks(null, _checksInline).catch(function () {});
        });
      } else {
        loadAllChecksQuietly();
      }
    }
    initThresholdPreview();
    initLlmPromptPresets();
  }

  /* -- Threshold live preview -- */
  function initThresholdPreview() {
    const greenEl = document.getElementById('green_threshold');
    const yellowEl = document.getElementById('yellow_threshold');
    const redSeg = document.getElementById('thresholdRed');
    const yellowSeg = document.getElementById('thresholdYellow');
    const greenSeg = document.getElementById('thresholdGreen');
    const yellowLabel = document.getElementById('thresholdYellowLabel');
    const greenLabel = document.getElementById('thresholdGreenLabel');
    if (!greenEl || !yellowEl || !redSeg) return;

    function update() {
      const g = Math.min(1, Math.max(0, parseFloat(greenEl.value) || 0));
      const y = Math.min(g, Math.max(0, parseFloat(yellowEl.value) || 0));
      redSeg.style.flex = y;
      yellowSeg.style.flex = g - y;
      greenSeg.style.flex = 1 - g;
      if (yellowLabel) {
        yellowLabel.textContent = Math.round(y * 100) + '%';
        yellowLabel.style.left = Math.round(y * 100) + '%';
      }
      if (greenLabel) {
        greenLabel.textContent = Math.round(g * 100) + '%';
        greenLabel.style.left = Math.round(g * 100) + '%';
      }
    }
    greenEl.addEventListener('input', update);
    yellowEl.addEventListener('input', update);
    update();
  }

  if (document.readyState === 'loading') {
    onDOMContentLoadedScoring = function () {
      initSettingsForm();
      // Reset dirty flag after Alpine select_field components fire initial change events
      requestAnimationFrame(function () { GP.clearDirtyReason('settings_form'); });
    };
    document.addEventListener('DOMContentLoaded', onDOMContentLoadedScoring);
  } else {
    initSettingsForm();
    requestAnimationFrame(function () { GP.clearDirtyReason('settings_form'); });
  }

  /* ==========================================
   *  Unified Compliance Checks - load, render, edit, filter
   * ========================================== */
  let _allChecks = [];
  let _weightPresets = {};
  let _patternPresets = {};
  let _activeFilter = 'all';

  /* Custom state and editor changes are part of the same settings draft.
     Creating a new custom check is a separate, explicit modal action. */
  const _pendingCustomActive = Object.create(null);
  const _pendingCheckEdits = Object.create(null);

  const CATEGORY_BADGES = {
    issue: 'badge-success', mr: 'badge-primary', review: 'badge-warning',
    ci: 'badge-info', commit: 'badge-purple', custom: 'badge-gray',
  };
  const CATEGORY_LABELS = {
    issue: t('Issue'), mr: t('MR'), review: t('Review'), ci: t('CI/CD'),
    commit: t('Commit'), custom: t('Custom'),
  };
