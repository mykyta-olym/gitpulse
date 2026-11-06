  /* ==========================================
   *  Full Course Configuration Import / Export
   * ========================================== */

  /* -- Export full config -- */
  document.getElementById('btnExportFullConfig')?.addEventListener('click', async function () {
    const btn = this;
    try {
      await _lock('exportFullConfig:' + _courseId, async () => {
        setButtonLoading(btn, true);
        const resp = await fetch('/dashboard/courses/' + _courseId + '/settings/full-config', {
          credentials: 'same-origin',
        });
        if (!resp.ok) throw new Error(t('Export failed'));
        const blob = await resp.blob();
        const disposition = resp.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?([^"]+)"?/);
        const filename = match ? match[1] : 'full-config.json';
        GP.downloadBlob(blob, filename);
        showToast(t('Full configuration exported'), 'success');
      });
    } catch (err) {
      if (err.code !== 'LOCKED') showToast(err.message || t('Export failed'), 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  });

  const FULL_CONFIG_SECTION_KEYS = [
    'course',
    'settings',
    'builtin_checks',
    'custom_checks',
    'weekly_deadlines',
  ];

  /* -- Import full config (uses shared GP.ConfigImport module) -- */
  const _fullConfigImportHandle = GP.ConfigImport.init({
    modalId: 'fullConfigModal',
    previewId: 'fullConfigPreview',
    summaryId: 'fullConfigSummary',
    sectionsId: 'fullConfigSections',
    applyBtnId: 'btnFullConfigApply',
    cancelBtnId: 'btnFullConfigCancel',
    openBtnId: 'btnImportFullConfigOpen',
    canOpen: _guardCourseWrite,
    pasteInputId: 'full_config_paste_input',
    disabledFeatures: _cfg.disabledFeatures || {},
    onApply: async function (config, btn) {
      if (!_guardCourseWrite()) return;
      const sections = [];
      FULL_CONFIG_SECTION_KEYS.forEach(function (k) {
        if (config[k] != null) sections.push(k);
      });

      confirmDangerousAction(t('overwrite course config'), async () => {
        try {
          await _lock('fullConfig:' + _courseId, async () => {
            setButtonLoading(btn, true);
            const result = await apiCall('/dashboard/courses/' + _courseId + '/settings/full-config', 'POST', config);
            const appliedCount = (result.applied || []).length;
            const errCount = (result.errors || []).length;

            if (errCount === 0) {
              flashToast(appliedCount + ' ' + t('sections applied successfully'), 'success');
            } else {
              let errMsg = appliedCount + ' ' + t('sections applied') + ', ' + errCount + ' ' + t('warnings') + ':\n';
              (result.errors || []).slice(0, 5).forEach(function (e) { errMsg += '* ' + e + '\n'; });
              if (errCount > 5) errMsg += '... ' + t('and') + ' ' + (errCount - 5) + ' ' + t('more');
              flashToast(errMsg, 'warning');
              console.warn('Full config import warnings:', result.errors);
            }

            clearModalDirty('fullConfigModal');
            GP.clearDirtyReason('full_config');
            forceCloseModal('fullConfigModal');

            if (typeof loadAllChecksQuietly === 'function') await loadAllChecksQuietly();
            reloadKeepScroll();
          });
        } catch (err) {
          if (err.code !== 'LOCKED') showToast(err.message || t('Import failed'), 'danger');
        } finally {
          setButtonLoading(btn, false);
        }
      }, { confirmText: t('This will overwrite the following sections:') + ' ' + sections.join(', ') + '. ' + t('Continue?'), singleConfirm: true });
    }
  });

