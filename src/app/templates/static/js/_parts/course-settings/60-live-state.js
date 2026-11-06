  /* ==========================================
   *  Modal Dirty-State Guards
   * ========================================== */
  if (typeof enableFormDirtyGuard === 'function') {
    enableFormDirtyGuard('checkEditorModal');
    enableFormDirtyGuard('transferCourseModal');
    enableFormDirtyGuard('webhookConfigEditModal');
  }
  if (window.GP && GP.initModalSaveGuard) {
    GP.initModalSaveGuard('webhookConfigEditModal', '#wcfSubmitBtn');
    GP.initModalSaveGuard('checkEditorModal', '#btnSaveCheck');
  }

  /* Import dialogs use the shared form guard in GP.ConfigImport. */
  if (typeof registerModalGuard === 'function') {
    /* Every guard below asks on THE dialog (GP.confirmDialog), never
       `window.confirm`. A guard has to answer synchronously, so the pattern is:
       veto this close, and re-issue it through `GP.forceCloseModal` - which
       bypasses guards, and exists for exactly this - once the reader answers. */
    const _guardAsk = function (modalId, opts, onDiscard) {
      GP.confirmDialog(opts).then(function (ok) {
        if (!ok) return;
        if (typeof onDiscard === 'function') onDiscard();
        GP.forceCloseModal(modalId);
      });
      return false;
    };

    /* LLM generate - warn when unsaved suggestions exist or generation in-flight */
    registerModalGuard('llmGenerateModal', function () {
      if (_llmRunning) {
        return _guardAsk('llmGenerateModal', {
          title: t('Close while AI generation is running?'),
          message: t('AI generation is in progress. Close anyway? You can reopen the modal later to see the results.'),
          confirmText: t('Close'),
        });
      }
      if (_llmSuggestions.length > 0) {
        return _guardAsk('llmGenerateModal', {
          title: t('Close with unsaved suggestions?'),
          message: t('You have unsaved AI suggestions. Close? They will be available when you reopen.'),
          confirmText: t('Close'),
        });
      }
      return true;  // clean - allow close
    });
  }

  /* -- SSE: listen for settings changes (e.g. from another user) -- */
  let _settingsSSE = null;
  const _SETTINGS_SSE_MAX = (typeof GP !== 'undefined' && GP.SSE_MAX_ERRORS) || 5;

  function handleSettingsEvent(event) {
    if (_settingsSaveInFlight) { _pendingSettingsEvent = event; return; }
    if (event.settings_updated_at && settingsFormAjax
        && event.settings_updated_at === settingsFormAjax.dataset.settingsUpdatedAt) return;
    if (!_isSettingsDirty()) { reloadKeepScroll(); return; }
    showToast(t('Settings were changed externally.') + ' <a href="" class="toast-action">'
      + t('Refresh') + '</a>', 'warning', 0);
  }

  function _connectSettingsSSE() {
    _disconnectSettingsSSE();
    if (!_courseId) return;
    _settingsSSE = GP.sse({
      url: '/api/v1/courses/' + _courseId + '/stream',
      maxErrors: _SETTINGS_SSE_MAX,
      events: {
        connected: function () {},
        update: function (e) {
          try {
            const d = JSON.parse(e.data);
            if (d && d.event === 'settings_changed') handleSettingsEvent(d);
          } catch (_) {}
        },
      },
      // No polling fallback here on purpose: this stream only tells the page
      // that SOMEONE ELSE edited these settings. Losing it costs a warning,
      // not data, and the save still checks the optimistic lock.
    });
  }
  function _disconnectSettingsSSE() {
    if (_settingsSSE) { _settingsSSE.close(); _settingsSSE = null; }
  }
  _connectSettingsSSE();

  // Pause SSE when backend is unreachable
  let _settingsHealthDown = false;
  onHealthChange = function (e) {
    if (e.detail?.current === 'down' && !_settingsHealthDown) {
      _settingsHealthDown = true;
      _disconnectSettingsSSE();
    } else if (e.detail?.current !== 'down' && _settingsHealthDown) {
      _settingsHealthDown = false;
      _connectSettingsSSE();
    }
  };
  document.addEventListener('gp-health-change', onHealthChange);

  /* -- Sync-lock: disable Save buttons while sync is in progress -- */
  let _syncLockActive = false;
  const _saveButtons = [
    document.getElementById('btnSaveSettings'),
  ].filter(Boolean);

  function _setSyncLock(locked) {
    _syncLockActive = locked;
    _saveButtons.forEach(function (btn) {
      if (locked) {
        btn.dataset.syncLocked = '1';
        btn.disabled = true;
        // Component tooltip on the disabled control (via .gl-tip-wrap wrapper) -
        // never a native title=. Tippy can't fire on a disabled button directly.
        GP.setDisabledReason(btn, t('Settings cannot be changed while sync is running'));
      } else {
        delete btn.dataset.syncLocked;
        GP.clearDisabledReason(btn);
        btn.removeAttribute('title');
        GP.refreshButtonDisabledState(btn);
      }
    });
  }

  // Check sync status periodically to activate/deactivate lock
  let _syncLockPoller = null;
  function _checkSyncLock() {
    if (!_courseId) return;
    (typeof apiCall === 'function'
      ? apiCall('/api/v1/courses/' + _courseId + '/sync-status')
      : fetch('/api/v1/courses/' + _courseId + '/sync-status', { credentials: 'same-origin' }).then(function (r) { return r.json(); })
    ).then(function (data) {
      if (data && data.has_active_sync) {
        if (!_syncLockActive) _setSyncLock(true);
      } else {
        if (_syncLockActive) _setSyncLock(false);
      }
    }).catch(function () {});
  }

  // Poll sync status every 5s, but only while visible
  function _startSyncLockPolling() {
    _checkSyncLock();
    _syncLockPoller = setInterval(function () {
      if (document.visibilityState !== 'hidden') _checkSyncLock();
    }, 5000);
  }
  _startSyncLockPolling();

  onVisibilityChange = () => {
    if (document.visibilityState === 'hidden') {
      _disconnectSettingsSSE();
      if (_syncLockPoller) {
        clearInterval(_syncLockPoller);
        _syncLockPoller = null;
      }
      return;
    }
    // visible
    if (!_settingsSSE?.active) {
      _connectSettingsSSE();
    }
    if (!_syncLockPoller) {
      _startSyncLockPolling();
    }
  };
  document.addEventListener('visibilitychange', onVisibilityChange);

  onBeforeUnload = () => {
    _disconnectSettingsSSE();
    if (_syncLockPoller) clearInterval(_syncLockPoller);
  };
  window.addEventListener('beforeunload', onBeforeUnload);

  // Also react to gp:global-job-start events to lock immediately
  onGlobalJobStart = function () {
    _checkSyncLock();
  };
  window.addEventListener('gp:global-job-start', onGlobalJobStart);

  /* -- Live update: show refresh prompt after sync/checks -- */
  let _refreshShown = false;
  onJobComplete = function (ev) {
    const d = ev.detail || {};
    if (d.status !== 'done' || _refreshShown) return;
    const jt = d.jobType || '';
    if (jt.startsWith('sync') || jt === 'run_checks' || jt === 'recheck') {
      // Release sync lock since the job is done
      if (_syncLockActive) _setSyncLock(false);
      if (!_isSettingsDirty()) {
        _refreshShown = true;
        showToast(
          t('Settings data updated.') +
          ' <a href="" class="toast-action">' +
          t('Refresh') + '</a>',
          'info', 0
        );
      }
    }
  };
  window.addEventListener('gp:job-complete', onJobComplete);

