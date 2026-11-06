  function markCheckDraft() {
    const revision = document.getElementById('check_edits_revision');
    revision.value = String(Number(revision.value) + 1);
    revision.dispatchEvent(new Event('input', { bubbles: true }));
  }

  /* Hydrate the server rows; refresh uses that same Jinja projection. */
  async function loadAllChecks(opts, preData) {
    const tbody = document.getElementById('checksBody');
    if (!tbody || !_courseId) return;
    if (!preData) GP.tableLoading(tbody, 7);
    try {
      let resp = preData;
      if (!resp) {
        const html = await apiCall('/dashboard/courses/' + _courseId + '/checks/table', 'GET', null,
          Object.assign({}, opts || {}, { responseType: 'text' }));
        const fragment = document.createElement('template');
        fragment.innerHTML = html;
        const state = fragment.content.querySelector('#gp-checks-refresh');
        resp = JSON.parse(state.textContent);
        state.remove();
        tbody.replaceChildren(fragment.content);
      }
      const previous = new Map(_allChecks.map(function (check) { return [check.check_code, check]; }));
      _allChecks = (resp.checks || []).map(function (check) {
        const code = check.check_code;
        const pending = _pendingCheckEdits[code];
        const activePending = Object.prototype.hasOwnProperty.call(_pendingCustomActive, code);
        if (pending) Object.assign(check, pending);
        if (activePending) check.is_active = _pendingCustomActive[code];
        if ((pending || activePending) && previous.has(code)) check.updated_at = previous.get(code).updated_at;
        return check;
      });
      _weightPresets = resp.presets || {};
      _patternPresets = resp.pattern_presets || {};
      renderChecks();
      GP.SortableTable.getInstance(tbody.closest('table'))?.refresh();
      updateWeightDisplay();
      GP.refreshProcessActionGuards(tbody);
      GP.initTippy(tbody);
    } catch (err) {
      if (!tbody.children.length) tbody.innerHTML = GP.emptyStateRow(7, t('Failed to load checks.'));
      throw err;
    } finally {
      GP.tableLoaded(tbody);
    }
  }

  /* Boot and post-mutation reloads must not throw at their call sites. */
  function loadAllChecksQuietly() {
    return loadAllChecks().catch(function (err) {
      showToast(err?.message || t('Failed to load checks.'), 'danger');
    });
  }

  function renderChecks() {
    const tbody = document.getElementById('checksBody');
    if (!tbody) return;
    let visible = 0;
    tbody.querySelectorAll('.table-empty-row').forEach(function (row) { row.remove(); });
    const rows = new Map(Array.from(tbody.rows).map(function (row) { return [row.dataset.checkCode, row]; }));
    for (const check of _allChecks) {
      const row = rows.get(check.check_code);
      if (!row) continue;
      const matches = _activeFilter === 'all' ? true : _activeFilter === 'builtin' ? check.is_builtin
        : _activeFilter === 'custom' ? !check.is_builtin : check.category === _activeFilter;
      row.hidden = !matches;
      if (!row.hidden) visible++;
      const toggle = row.querySelector('[data-action="toggleCheck"]');
      toggle.checked = check.is_active;
      toggle.setAttribute('aria-label', (check.is_active ? t('Disable') : t('Enable')) + ' ' + check.check_code);
      row.querySelector('.check-name').textContent = t(check.name);
      const description = row.querySelector('.check-desc');
      description.textContent = t(check.description || '');
      description.hidden = !check.description;
      row.querySelector('.check-weight-value').textContent = check.weight.toFixed(2);
      const category = row.querySelector('[data-check-category]');
      if (category.dataset.checkCategory !== check.category) {
        category.innerHTML = GP.badgeHtml(CATEGORY_LABELS[check.category] || check.category,
          (CATEGORY_BADGES[check.category] || 'badge-gray').replace(/^badge-/, ''), { size: 'sm' });
        category.dataset.checkCategory = check.category;
      }
    }
    if (!visible) tbody.insertAdjacentHTML('beforeend', GP.emptyStateRow(7, t('No checks match the current filter.'), 'search-sm'));
    GP.tableLoaded(tbody);
  }

  function updateWeightDisplay() {
    let totalActive = 0;
    _allChecks.forEach(function (c) {
      if (c.is_active) totalActive += c.weight || 0;
    });

    const headerTotal = document.getElementById('checkWeightTotal');
    const footerTotal = document.getElementById('checksFooterWeight');

    const text = totalActive.toFixed(2);
    // The score divides by this total, so only a weightless set is invalid.
    const isValid = totalActive > 0;

    if (headerTotal) {
      headerTotal.textContent = '\u2211 ' + text;
      headerTotal.classList.toggle('badge-success', isValid);
      headerTotal.classList.toggle('badge-danger', !isValid);
    }
    if (footerTotal) {
      footerTotal.textContent = text;
      footerTotal.classList.toggle('badge-success', isValid);
      footerTotal.classList.toggle('badge-danger', !isValid);
    }
  }

  /* -- Filter buttons -- */
  const filterContainer = document.getElementById('checkFilters');
  if (filterContainer) {
    try {
      const p = new URLSearchParams(window.location.search);
      const urlCheckFilter = p.get('check_filter');
      if (urlCheckFilter && ['all', 'builtin', 'custom', 'issue', 'mr', 'review', 'ci', 'commit'].includes(urlCheckFilter)) {
        _activeFilter = urlCheckFilter;
        filterContainer.querySelectorAll('.tab-btn, .check-filter-btn').forEach(function (b) {
          const isActive = (b.dataset.value || b.dataset.filter) === urlCheckFilter;
          b.classList.toggle('active', isActive);
          b.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });
      }
    } catch (_) {}

    filterContainer.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-value], [data-filter], .tab-btn');
      if (!btn) return;
      const val = btn.dataset.value || btn.dataset.filter;
      if (!val) return;
      filterContainer.querySelectorAll('.tab-btn, .check-filter-btn').forEach(function (b) {
        const isActive = b === btn;
        b.classList.toggle('active', isActive);
        b.setAttribute('aria-selected', isActive ? 'true' : 'false');
      });
      _activeFilter = val;
      try {
        const url = new URL(window.location.href);
        if (val && val !== 'all') {
          url.searchParams.set('check_filter', val);
        } else {
          url.searchParams.delete('check_filter');
        }
        window.history.replaceState(null, '', url.toString());
      } catch (_) {}
      renderChecks();
    });
  }

  /* ===========================================
   *  Weight Presets - server-driven, dynamic over the live check set
   *  (fetched in loadAllChecks into _weightPresets; see build_weight_presets
   *  on the backend). No weight distributions are hard-coded on the client.
   * =========================================== */
  onDocumentClickSection = function (e) {
    const btn = e.target.closest('[data-action="applyPreset"]');
    if (!btn) return;
    const presetName = btn.dataset.preset;
    const preset = _weightPresets[presetName];
    if (!preset) return;
    if (!_guardCourseWrite()) return;

    confirmDangerousAction(t('apply weight preset'), function () {
      // Staged, not sent - the whole page applies with one "Update settings".
      const activeSet = new Set(preset._active);
      let applied = 0;

      for (const c of _allChecks) {
        if (!c.is_builtin) continue;
        const newWeight = preset[c.check_code];
        if (newWeight == null) continue;
        c.weight = newWeight;
        c.is_active = activeSet.has(c.check_code);
        _pendingCheckEdits[c.check_code] = {
          name: c.name,
          description: c.description || '',
          category: c.category,
          weight: c.weight,
          is_active: c.is_active,
          check_config: c.check_config || {},
        };
        applied++;
      }

      renderChecks();
      updateWeightDisplay();
      markCheckDraft();
      showToast(t('Preset staged') + ' (' + applied + ') - ' + t('press Update settings to apply.'), 'info');
    }, { confirmText: t('Apply the "') + btn.textContent.trim() + t('" preset? This will update weights and active state for all built-in checks.'), singleConfirm: true });
  };
  document.addEventListener('click', onDocumentClickSection);

  /* -- Convention pattern presets --
     Writes the R02/R03/R05 check_config in one go. Each preset carries the
     strict-mode flags together with the patterns, so applying one can never
     leave a branch regex configured that nothing actually scores. Values come
     from the server (build_pattern_presets) - none are hard-coded here. */
  onDocumentClickPatternPreset = function (e) {
    const btn = e.target.closest('[data-action="applyPatternPreset"]');
    if (!btn) return;
    const preset = _patternPresets[btn.dataset.preset];
    if (!preset || !preset.configs) return;
    if (!_guardCourseWrite()) return;

    confirmDangerousAction(t('apply pattern preset'), function () {
      // Staged, not sent: the preset is a settings change like any other on
      // this page, so it applies when the user presses "Update settings".
      let applied = 0;
      for (const code of Object.keys(preset.configs)) {
        const check = _allChecks.find(function (x) { return x.check_code === code; });
        if (!check) continue;
        // Merge, so a preset that only speaks about patterns does not wipe
        // unrelated parameters (min_description_words, min_test_files).
        check.check_config = Object.assign({}, check.check_config || {}, preset.configs[code]);
        _pendingCheckEdits[code] = {
          name: check.name,
          description: check.description || '',
          category: check.category,
          weight: check.weight,
          is_active: check.is_active,
          check_config: check.check_config,
        };
        applied++;
      }
      renderChecks();
      markCheckDraft();
      showToast(t('Conventions staged') + ' (' + applied + ') - ' + t('press Update settings to apply.'), 'info');
    }, { confirmText: t('Apply the "') + preset.label + t('" conventions? This overwrites the branch pattern, test paths and MR template settings of R02, R03 and R05.'), singleConfirm: true });
  };
  document.addEventListener('click', onDocumentClickPatternPreset);

  /* -- Toggle check active state inline -- */
  onDocumentChangeSection = function (e) {
    if (!e.target.matches('[data-action="toggleCheck"]')) return;
    const cb = e.target;
    const code = cb.dataset.checkCode;
    cb.setAttribute('aria-label', (cb.checked ? t('Disable') : t('Enable')) + ' ' + code);
    const isActive = cb.checked;
    if (!_guardCourseWrite()) {
      cb.checked = !isActive;
      return;
    }

    // No per-toggle PUT any more. Enabling/disabling a check is a pending
    // edit like every other field on this page and is applied by "Update
    // Settings" - built-ins ride along in CourseSettings.enabled_checks,
    // custom checks are flushed from _pendingCustomActive. This is what the
    // page always claimed to do, and it removes the 409 trap: each built-in
    // check optimistic-locks against the SAME CourseSettings row, so saving
    // one silently invalidated the page's token and the next toggle failed
    // with "modified by another user" in a single-user session.
    const c = _allChecks.find(function (x) { return x.check_code === code; });
    if (c) c.is_active = isActive;
    if (!/^R/i.test(code)) {
      if (cb.defaultChecked === isActive) delete _pendingCustomActive[code];
      else _pendingCustomActive[code] = isActive;
    }
    if (_pendingCheckEdits[code]) {
      _pendingCheckEdits[code] = Object.assign({}, _pendingCheckEdits[code], { is_active: isActive });
      markCheckDraft();
    }

    const label = cb.closest('.check-active-toggle');
    if (label) {
      // Component (tippy) tooltip only - never a native title=.
      const _tip = isActive ? t('Disable') : t('Enable');
      label.setAttribute('data-tippy-content', _tip);
      label.removeAttribute('title');
      if (label._tippy && typeof label._tippy.setContent === 'function') label._tippy.setContent(_tip);
      else GP.initTippy(label.parentNode || document);
    }
    updateWeightDisplay();
  };
  document.addEventListener('change', onDocumentChangeSection);

  /* ==========================================
   *  Unified Check Editor Modal
   * ========================================== */
  function openCheckEditor(checkCode) {
    if (!_guardCourseWrite()) return;
    const c = _allChecks.find(function (x) { return x.check_code === checkCode; });
    if (!c) return;

    const _el = (id) => document.getElementById(id);
    const ceCheckCode = _el('ceCheckCode'); if (ceCheckCode) ceCheckCode.value = c.check_code;
    const ceIsBuiltin = _el('ceIsBuiltin'); if (ceIsBuiltin) ceIsBuiltin.value = c.is_builtin ? '1' : '';
    const ceCheckId = _el('ceCheckId'); if (ceCheckId) ceCheckId.value = c.id || '';
    const ceName = _el('ceName'); if (ceName) ceName.value = c.name || '';
    const ceDescription = _el('ceDescription'); if (ceDescription) ceDescription.value = c.description || '';
    const ceWeight = _el('ceWeight');
    if (ceWeight) {
      ceWeight.value = c.weight != null ? c.weight : 0.05;
      ceWeight.dispatchEvent(new Event('input', { bubbles: true }));
    }
    const ceActive = _el('ceActive'); if (ceActive) ceActive.checked = c.is_active;
    const activeLabel = document.querySelector('label[for="ceActive"]');
    if (activeLabel) activeLabel.textContent = c.is_active ? t('Active') : t('Disabled');

    // Category - setting .value on the hidden input triggers glFormSelect sync
    const catInput = document.getElementById('ceCategory');
    if (catInput) catInput.value = c.category || 'custom';

    // All checks are fully editable (name, category, description)
    if (ceName) ceName.readOnly = false;
    const catToggle = catInput?.closest('.gl-dropdown')?.querySelector('.gl-dropdown-toggle');
    if (catToggle) catToggle.disabled = false;

    // Show correct panel
    const builtinPanel = document.getElementById('ceBuiltinPanel');
    const customPanel = document.getElementById('ceCustomPanel');

    // Always show config params for built-in checks
    if (c.is_builtin) {
      builtinPanel?.classList.remove('d-none');
      renderConfigParams(c);
    } else {
      builtinPanel?.classList.add('d-none');
    }

    // Always show evaluation rule editor for all checks
    customPanel?.classList.remove('d-none');
    const ruleType = (c.evaluation_rule || {}).type || 'count';
    const rtInput = document.getElementById('ceRuleType');
    if (rtInput) rtInput.value = ruleType;
    const ceRule = document.getElementById('ceRule');
    if (ceRule) ceRule.value = JSON.stringify(c.evaluation_rule || {}, null, 2);

    const delBtn = document.getElementById('btnDeleteCheck');
    if (delBtn) delBtn.classList.toggle('d-none', c.is_builtin);

    openModal('checkEditorModal');
  }

  function renderConfigParams(check) {
    const container = document.getElementById('ceConfigParams');
    if (!container) return;
    container.innerHTML = '';

    // The container outlives every re-render, so bind the dependency listener
    // to it exactly once instead of once per rendered check.
    if (!container.dataset.depsBound) {
      container.dataset.depsBound = '1';
      container.addEventListener('change', function (e) {
        if (e.target && e.target.dataset && e.target.dataset.cfgType === 'boolean') {
          _syncParamDependencies();
        }
      });
    }

    const params = check.configurable_params || [];
    if (!params.length) {
      // The app's one empty state, not a grey paragraph of its own.
      container.innerHTML = GP.emptyStateHtml(t('This check has no configurable parameters.'));
      return;
    }

    const cfg = check.check_config || {};
    params.forEach(function (p) {
      const currentVal = cfg[p.key] != null ? cfg[p.key] : '';
      const controlId = 'cfg_' + p.key;
      let control;

      if (p.type === 'boolean') {
        control = document.createElement('input');
        control.type = 'checkbox';
        control.id = controlId;
        control.className = 'form-check-input ce-config-input';
        control.dataset.cfgKey = p.key;
        control.dataset.cfgType = 'boolean';
        control.checked = currentVal === true || currentVal === 'true' ||
          (currentVal === '' && p.default === 'true');
      } else if (p.type === 'string' || p.type === 'list') {
        // The convention patterns (R02 branch regex, R03 test globs, R05
        // template headings) live here now, beside the option that decides
        // whether each one is enforced.
        control = document.createElement('input');
        control.type = 'text';
        control.id = controlId;
        control.className = 'form-input ce-config-input';
        control.dataset.cfgKey = p.key;
        control.dataset.cfgType = p.type;
        control.placeholder = p.placeholder || p.default || '';
        control.value = Array.isArray(currentVal) ? currentVal.join(', ') : String(currentVal);
      } else {
        // Cloned from the page's canonical stepper template - the parameter
        // rows used to inline their own -/+ markup, which then collided with
        // the macro-rendered control's handler and double-stepped the value.
        control = GP.createNumberStepper({
          id: controlId,
          value: currentVal,
          placeholder: p.default,
          min: 0,
          dataset: { cfgKey: p.key, cfgType: 'number' },
          className: 'ce-config-input'
        });
      }

      // Free-text params carry their own explanation; a bare "Default: " with
      // nothing after it (their default is empty) would say nothing.
      const hint = p.help || (p.default ? t('Default') + ': ' + p.default : '');
      const row = GP.createSettingRow({
        label: p.label,
        hint: hint,
        controlId: controlId,
        control: control,
        wide: p.type === 'string' || p.type === 'list'
      });
      if (p.depends_on) row.dataset.dependsOn = p.depends_on;
      container.appendChild(row);
    });

    _syncParamDependencies();
  }

  /* A pattern is only enforced while its own switch is on (R02's branch regex
     follows require_branch_convention, R05's headings follow require_template).
     The field used to stay fully editable with the dependency stated only in
     grey help text, so there was no visible way to tell a pattern was off.
     Mirror the switch onto the field it governs instead. */
  function _syncParamDependencies() {
    const container = document.getElementById('ceConfigParams');
    if (!container) return;
    container.querySelectorAll('[data-depends-on]').forEach(function (row) {
      const master = container.querySelector(
        '.ce-config-input[data-cfg-key="' + row.dataset.dependsOn + '"]'
      );
      if (!master) return;
      const on = !!master.checked;
      row.classList.toggle('is-dependency-off', !on);
      row.querySelectorAll('.ce-config-input').forEach(function (field) {
        field.disabled = !on;
        if (!on) {
          GP.setDisabledReason(field, t('Turn on the option above to use this pattern'));
        } else {
          GP.clearDisabledReason(field);
        }
      });
    });
  }

  function collectConfigParams() {
    const cfg = {};
    document.querySelectorAll('#ceConfigParams .ce-config-input').forEach(function (el) {
      const key = el.dataset.cfgKey;
      const type = el.dataset.cfgType;
      if (type === 'boolean') {
        cfg[key] = el.checked;
      } else if (type === 'list') {
        // Stored as a real array so the engine does not have to re-split it.
        const items = el.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
        if (items.length) cfg[key] = items;
      } else if (type === 'string') {
        const val = el.value.trim();
        if (val !== '') cfg[key] = val;
      } else {
        const val = el.value.trim();
        if (val !== '') {
          const num = Number(val);
          cfg[key] = Number.isNaN(num) ? val : num;
        }
      }
    });
    // Drop entries left at their default - an override that matches the
    // default is noise. Array params compare by content, not by String().
    const check = _allChecks.find(function (x) { return x.check_code === document.getElementById('ceCheckCode')?.value; });
    if (check && check.configurable_params) {
      check.configurable_params.forEach(function (p) {
        if (Array.isArray(cfg[p.key])) return;
        if (String(cfg[p.key]) === p.default) delete cfg[p.key];
      });
    }
    return cfg;
  }

  /* -- Open new custom check -- */
  document.getElementById('btnAddCustomCheck')?.addEventListener('click', function () {
    if (!_guardCourseWrite()) return;
    const _el = (id) => document.getElementById(id);
    const ceCheckCode = _el('ceCheckCode'); if (ceCheckCode) ceCheckCode.value = '';
    const ceIsBuiltin = _el('ceIsBuiltin'); if (ceIsBuiltin) ceIsBuiltin.value = '';
    const ceCheckId = _el('ceCheckId'); if (ceCheckId) ceCheckId.value = '';
    const ceName = _el('ceName'); if (ceName) { ceName.value = ''; ceName.readOnly = false; }
    const ceDescription = _el('ceDescription'); if (ceDescription) ceDescription.value = '';
    const ceWeight = _el('ceWeight');
    if (ceWeight) {
      ceWeight.value = '0.05';
      ceWeight.dispatchEvent(new Event('input', { bubbles: true }));
    }
    const ceActive = _el('ceActive'); if (ceActive) ceActive.checked = true;
    const activeLabel = document.querySelector('label[for="ceActive"]');
    if (activeLabel) activeLabel.textContent = t('Active');

    const catInput = document.getElementById('ceCategory');
    if (catInput) catInput.value = 'custom';
    const catToggle = catInput?.closest('.gl-dropdown')?.querySelector('.gl-dropdown-toggle');
    if (catToggle) catToggle.disabled = false;

    document.getElementById('ceBuiltinPanel')?.classList.add('d-none');
    document.getElementById('ceCustomPanel')?.classList.remove('d-none');

    const rtInput = document.getElementById('ceRuleType');
    if (rtInput) rtInput.value = 'count';

    const ceRule = document.getElementById('ceRule');
    if (ceRule) ceRule.value = '{\n  "type": "count",\n  "entity": "merge_request",\n  "op": ">=",\n  "threshold": 1\n}';

    document.getElementById('btnDeleteCheck')?.classList.add('d-none');
    openModal('checkEditorModal');
  });

  /* -- Edit check button -- */
  onDocumentClickCheck = function (e) {
    const btn = e.target.closest('[data-action="editCheck"]');
    if (!btn) return;
    openCheckEditor(btn.dataset.checkCode);
  };
  document.addEventListener('click', onDocumentClickCheck);

  /* -- Active toggle in modal -- */
  document.getElementById('ceActive')?.addEventListener('change', function () {
    const activeLabel = document.querySelector('label[for="ceActive"]');
    if (activeLabel) activeLabel.textContent = this.checked ? t('Active') : t('Disabled');
  });

  /* -- Save check -- */
  document.getElementById('btnSaveCheck')?.addEventListener('click', async function () {
    if (!_guardCourseWrite()) return;
    const checkCode = document.getElementById('ceCheckCode')?.value;
    const isBuiltin = document.getElementById('ceIsBuiltin')?.value === '1';
    const name = document.getElementById('ceName')?.value?.trim();
    const weight = parseFloat(document.getElementById('ceWeight')?.value);
    const isActive = document.getElementById('ceActive')?.checked;

    if (!name) { showToast(t('Check name is required'), 'warning'); return; }
    if (name.length > 200) { showToast(t('Check name is too long (max 200 characters)'), 'warning'); return; }
    if (Number.isNaN(weight) || weight < 0 || weight > 1) { showToast(t('Weight must be between 0 and 1'), 'warning'); return; }

    // Check for duplicate names across all checks
    const duplicate = _allChecks.find(function (x) {
      return x.name.toLowerCase() === name.toLowerCase() && x.check_code !== checkCode;
    });
    if (duplicate) {
      showToast(t('A check named') + ' "' + name + '" ' + t('already exists') + ' (' + duplicate.check_code + ')', 'warning');
      return;
    }

    const payload = { weight: weight, is_active: isActive };
    const btn = this;

    // Always send name, description, category (both built-in and custom)
    payload.name = name;
    payload.description = document.getElementById('ceDescription')?.value?.trim() || '';
    if (payload.description.length > 500) { showToast(t('Description is too long (max 500 characters)'), 'warning'); return; }
    payload.category = document.getElementById('ceCategory')?.value || 'custom';

    if (isBuiltin) {
      payload.check_config = collectConfigParams();
    }

    // Always collect evaluation rule (both built-in overrides and custom checks)
    const ruleText = document.getElementById('ceRule')?.value?.trim() || '{}';
    if (ruleText && ruleText !== '{}') {
      try {
        const rule = JSON.parse(ruleText);
        const ruleType = document.getElementById('ceRuleType')?.value;
        if (ruleType) rule.type = ruleType;
        payload.evaluation_rule = rule;
      } catch (parseErr) {
        showToast(t('Invalid JSON in rule') + ': ' + parseErr.message, 'danger');
        return;
      }

      const validRuleTypes = ['count', 'field_check', 'ratio', 'word_count', 'avg_word_count'];
      if (payload.evaluation_rule.type && validRuleTypes.indexOf(payload.evaluation_rule.type) === -1) {
        showToast(t('Invalid rule type. Must be one of:') + ' ' + validRuleTypes.join(', '), 'warning');
        return;
      }
      if (payload.evaluation_rule.type && !payload.evaluation_rule.entity) {
        showToast(t('Evaluation rule must specify an entity type'), 'warning');
        return;
      }
    }

    /* Editing an existing check is a SETTING: hold it until "Update settings",
       like every other control on this page. Only creating a brand-new custom
       check still goes straight to the server - see _pendingCheckEdits. */
    if (checkCode) {
      _pendingCheckEdits[checkCode] = payload;
      const local = _allChecks.find(function (x) { return x.check_code === checkCode; });
      if (local) {
        local.name = payload.name;
        local.description = payload.description;
        local.category = payload.category;
        local.weight = payload.weight;
        local.is_active = payload.is_active;
        if (payload.check_config) local.check_config = payload.check_config;
        if (payload.evaluation_rule) local.evaluation_rule = payload.evaluation_rule;
      }
      renderChecks();
      updateWeightDisplay();
      markCheckDraft();
      clearModalDirty('checkEditorModal');
      closeModal('checkEditorModal');
      showToast(t('Check updated - press Update settings to apply.'), 'info');
      _warnOnWeightlessChecks();
      return;
    }

    setButtonLoading(btn, true);
    try {
      await _lock('saveCheck:new', async () => {
        await apiCall('/dashboard/courses/' + _courseId + '/custom-checks', 'POST', payload);
        showToast(t('Check created'), 'success');
        clearModalDirty('checkEditorModal');
        closeModal('checkEditorModal');
        await loadAllChecksQuietly();
        _warnOnWeightlessChecks();
      });
    } catch (err) {
      if (err.code !== 'LOCKED') {
        if (err.status === 409) {
          showToast(t('This page was modified by another user. Please reload.'), 'warning');
        } else {
          showToast(err.message || t('Save failed'), 'danger');
        }
      }
    } finally {
      setButtonLoading(btn, false);
    }
  });

  /** Warn when the active checks weigh nothing: the score divides by their
      total, so any positive total works and zero leaves no score. */
  function _warnOnWeightlessChecks() {
    let totalActive = 0;
    _allChecks.forEach(function (x) { if (x.is_active) totalActive += x.weight || 0; });
    if (totalActive <= 0) {
      showToast(t('The active checks have no weight, so no score can be computed.'), 'warning');
    }
  }

  /* -- Delete check -- */
  document.getElementById('btnDeleteCheck')?.addEventListener('click', function () {
    const checkId = document.getElementById('ceCheckId')?.value;
    if (!checkId) return;
    if (!_guardCourseWrite()) return;
    const btn = this;
    confirmDangerousAction(t('this check'), async () => {
      try {
        await _lock(`deleteCheck:${checkId}`, async () => {
          setButtonLoading(btn, true);
          await apiCall('/dashboard/courses/' + _courseId + '/custom-checks/' + checkId, 'DELETE');
          const code = document.getElementById('ceCheckCode').value;
          delete _pendingCustomActive[code];
          delete _pendingCheckEdits[code];
          showToast(t('Check deleted'), 'success');
          clearModalDirty('checkEditorModal');
          closeModal('checkEditorModal');
          await loadAllChecksQuietly();
        });
      } catch (err) {
        if (err.code !== 'LOCKED') showToast(err.message || t('Delete failed'), 'danger');
      } finally {
        setButtonLoading(btn, false);
      }
    }, { confirmText: t('Delete this custom check? This action cannot be undone.') });
  });

  /* ==========================================
   *  Export / Import Check Configuration
   * ========================================== */

  /* -- Export -- */
  document.getElementById('btnExportChecks')?.addEventListener('click', async function () {
    const btn = this;
    try {
      await _lock('exportChecks:' + _courseId, async () => {
        setButtonLoading(btn, true);
        const resp = await fetch('/dashboard/courses/' + _courseId + '/checks/export', {
          credentials: 'same-origin',
        });
        if (!resp.ok) throw new Error(t('Export failed'));
        const blob = await resp.blob();
        const disposition = resp.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?([^"]+)"?/);
        const filename = match ? match[1] : 'checks-config.json';
        GP.downloadBlob(blob, filename);
        showToast(t('Configuration exported'), 'success');
      });
    } catch (err) {
      if (err.code !== 'LOCKED') showToast(err.message || t('Export failed'), 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  });
