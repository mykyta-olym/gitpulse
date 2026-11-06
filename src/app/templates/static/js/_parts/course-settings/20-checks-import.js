  function parseImportConfig(text, showErrors) {
    try {
      const config = JSON.parse(text);
      if (!config || typeof config !== 'object' || Array.isArray(config)) {
        if (showErrors) showToast(t('Invalid config: expected a JSON object'), 'warning');
        return null;
      }
      // Auto-tag $schema for server compatibility
      if (!config.$schema) {
        config.$schema = 'gitpulse/check-config/v1';
      }
      if (config.builtin_checks && !Array.isArray(config.builtin_checks)) {
        if (showErrors) showToast(t('builtin_checks must be an array'), 'warning');
        return null;
      }
      if (config.custom_checks && !Array.isArray(config.custom_checks)) {
        if (showErrors) showToast(t('custom_checks must be an array'), 'warning');
        return null;
      }
      return config;
    } catch (e) {
      if (showErrors) showToast(t('Invalid JSON') + ': ' + e.message, 'danger');
      return null;
    }
  }

  function showImportPreview(config) {
    const preview = document.getElementById('importChecksPreview');
    const summary = document.getElementById('importChecksSummary');
    const applyBtn = document.getElementById('btnImportChecksApply');
    if (!preview || !summary) return;

    const builtinCount = (config.builtin_checks || []).length;
    const customCount = (config.custom_checks || []).length;
    const source = config.source_course || {};
    const exported = GP.timeHtml(config.exported_at);

    let html = '<ul class="prop-list">';
    if (source.code) html += '<li><strong>' + t('Source') + ':</strong> ' + _esc(source.code) + (source.academic_year ? ' (' + _esc(GP.periodLabel(source.academic_year, source.semester || 'winter')) + ')' : '') + '</li>';
    html += '<li><strong>' + t('Exported') + ':</strong> ' + _esc(exported) + '</li>';
    html += '<li><strong>' + t('Built-in checks') + ':</strong> ' + builtinCount + '</li>';
    html += '<li><strong>' + t('Custom checks') + ':</strong> ' + customCount + '</li>';

    // Show active/inactive counts
    const activeBuiltin = (config.builtin_checks || []).filter(function (c) { return c.is_active; }).length;
    const activeCustom = (config.custom_checks || []).filter(function (c) { return c.is_active; }).length;
    html += '<li><strong>' + t('Active') + ':</strong> ' + (activeBuiltin + activeCustom) + ' / ' + (builtinCount + customCount) + '</li>';

    // Total weight
    let totalWeight = 0;
    (config.builtin_checks || []).forEach(function (c) { if (c.is_active) totalWeight += c.weight || 0; });
    (config.custom_checks || []).forEach(function (c) { if (c.is_active) totalWeight += c.weight || 0; });
    html += '<li><strong>' + t('Total weight') + ':</strong> ' + totalWeight.toFixed(2) + '</li>';
    html += '</ul>';

    summary.innerHTML = html;
    preview.classList.remove('d-none');
    if (applyBtn) applyBtn.disabled = false;
    GP.refreshProcessActionGuards(document.getElementById('importChecksModal') || document);
  }

  const _checksImportHandle = GP.ConfigImport.init({
    modalId: 'importChecksModal',
    previewId: 'importChecksPreview',
    applyBtnId: 'btnImportChecksApply',
    pasteInputId: 'checks_config_paste_input',
    openBtnId: 'btnImportChecksOpen',
    canOpen: _guardCourseWrite,
    cancelBtnId: 'btnImportChecksCancel',
    parse: parseImportConfig,
    renderPreview: showImportPreview,
    onApply: function (config, btn) {
      if (!_guardCourseWrite()) return;
      confirmDangerousAction(t('overwrite check config'), async () => {
        try {
          await _lock('importChecks:' + _courseId, async () => {
            setButtonLoading(btn, true);
            const result = await apiCall('/dashboard/courses/' + _courseId + '/checks/import', 'POST', config);
            let msg = result.applied + ' ' + t('checks applied');
            if (result.skipped > 0) msg += ', ' + result.skipped + ' ' + t('skipped');
            if (result.errors && result.errors.length > 0) {
              msg += ', ' + result.errors.length + ' ' + t('errors') + ':\n';
              result.errors.slice(0, 5).forEach(function (e) { msg += '* ' + e + '\n'; });
              if (result.errors.length > 5) msg += '... ' + t('and') + ' ' + (result.errors.length - 5) + ' ' + t('more');
            }
            showToast(msg, result.errors?.length ? 'warning' : 'success');
            clearModalDirty('importChecksModal');
            GP.clearDirtyReason('import_config');
            closeModal('importChecksModal');
            await loadAllChecksQuietly();

            // Warn if the imported active checks weigh nothing (any positive
            // total is fine: the score divides by it).
            let totalActive = 0;
            _allChecks.forEach(function (x) { if (x.is_active) totalActive += x.weight || 0; });
            if (totalActive <= 0) {
              showToast(t('The active checks have no weight, so no score can be computed.'), 'warning');
            }
          });
        } catch (err) {
          if (err.code !== 'LOCKED') showToast(err.message || t('Import failed'), 'danger');
        } finally {
          setButtonLoading(btn, false);
        }
      }, { confirmText: t('This will overwrite current check configuration. Continue?'), singleConfirm: true });
    },
  });

