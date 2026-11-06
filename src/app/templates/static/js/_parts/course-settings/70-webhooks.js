  /* ==================================================================
   * Webhook configurations - multi-scope CRUD (group / sub-group /
   * project list / whole course). One row per server-generated secret
   * with rotate (24 h grace), revoke, edit metadata, and last-delivery
   * audit. Plain text is shown exactly once on create / rotate.
   * ================================================================== */
  (function initWebhookConfigs() {
    const container = document.getElementById('webhookConfigsContainer');
    if (!container) return;

    const courseIdWh = container.dataset.courseId;
    const tbody = document.getElementById('webhookConfigsTbody');
    const tableEl = document.getElementById('webhookConfigsTable');
    const emptyEl = document.getElementById('webhookConfigsEmpty');
    if (!courseIdWh || !tbody || !tableEl || !emptyEl) return;

    async function loadWebhookConfigs(opts) {
      GP.tableLoading(tbody, 6);
      try {
        const html = await apiCall('/dashboard/courses/' + courseIdWh + '/webhooks/table', 'GET', null,
          Object.assign({}, opts || {}, { responseType: 'text' }));
        const fragment = document.createElement('template');
        fragment.innerHTML = html;
        tbody.replaceChildren(fragment.content);
        const empty = !tbody.children.length;
        tableEl.classList.toggle('d-none', empty);
        emptyEl.classList.toggle('d-none', !empty);
        const sorter = GP.SortableTable.getInstance(tableEl);
        if (sorter) sorter.refresh();
        else GP.SortableTable.initTable(tableEl);
        GP.refreshProcessActionGuards(tbody);
        GP.initTippy(tbody);
      } finally {
        GP.tableLoaded(tbody);
      }
    }

    /* Report post-mutation reload failures without rejecting the action callback. */
    function loadWebhookConfigsQuietly() {
      return loadWebhookConfigs().catch(function (err) {
        showToast(err?.message || t('Failed to load webhook configurations'), 'danger');
      });
    }

    function applyScopeVisibility() {
      const sel = document.getElementById('wcf_scope_type');
      const groupBox = document.getElementById('wcf_group_fields');
      const projectsBox = document.getElementById('wcf_projects_fields');
      if (!sel || !groupBox || !projectsBox) return;
      const v = sel.value;
      const showGroup = v === 'group' || v === 'subgroup';
      const showProjects = v === 'projects';
      groupBox.classList.toggle('d-none', !showGroup);
      projectsBox.classList.toggle('d-none', !showProjects);
      const help = sel.closest('.form-group')?.querySelector('.form-help');
      if (help) {
        const map = {
          group: t('A "group" scope accepts deliveries from any project whose path starts with the group path (including all sub-groups).'),
          subgroup: t('A "sub-group" scope accepts only that exact sub-tree - narrower than "group".'),
          projects: t('A "projects" scope only authenticates the listed numeric project IDs - best blast-radius isolation.'),
          course: t('A "course" scope authenticates any project that resolves to this course - useful as a fallback shared secret.'),
        };
        help.textContent = map[v] || '';
      }
    }

    document.getElementById('wcf_scope_type')?.addEventListener('change', applyScopeVisibility);

    function resetForm() {
      document.getElementById('wcfConfigId').value = '';
      const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
      setVal('wcf_name', '');
      setVal('wcf_description', '');
      setVal('wcf_group_path', '');
      setVal('wcf_group_id', '');
      setVal('wcf_project_ids', '');
      const sel = document.getElementById('wcf_scope_type');
      if (sel) {
        sel.value = 'group';
        const tgl = sel.closest('.gl-dropdown')?.querySelector('.gl-dropdown-toggle');
        if (tgl) tgl.disabled = false;
      }
      const active = document.getElementById('wcf_is_active');
      if (active) active.checked = true;
      const hint = document.getElementById('wcf_create_hint');
      if (hint) hint.classList.remove('d-none');
      // Active checkbox is visible in both create and edit - defaults to checked for new ones.
      const activeField = document.getElementById('wcf_active_field');
      if (activeField) activeField.classList.remove('d-none');
      applyScopeVisibility();
    }

    function openCreateWebhookConfigModal() {
      resetForm();
      const titleEl = document.querySelector('#webhookConfigEditModal .modal-title');
      if (titleEl) titleEl.textContent = t('New webhook configuration');
      openModal('webhookConfigEditModal');
    }

    async function openEditWebhookConfigModal(configId) {
      try {
        const cfg = await apiCall('/api/v1/webhook-configs/' + encodeURIComponent(configId), 'GET');
        resetForm();
        document.getElementById('wcfConfigId').value = cfg.id;
        document.getElementById('wcf_name').value = cfg.name || '';
        document.getElementById('wcf_description').value = cfg.description || '';
        const sel = document.getElementById('wcf_scope_type');
        if (sel) {
          sel.value = cfg.scope_type || 'group';
          const tgl = sel.closest('.gl-dropdown')?.querySelector('.gl-dropdown-toggle');
          if (tgl) tgl.disabled = true;
        }
        document.getElementById('wcf_group_path').value = cfg.gitlab_group_path || '';
        document.getElementById('wcf_group_id').value = cfg.gitlab_group_id || '';
        document.getElementById('wcf_project_ids').value = (cfg.gitlab_project_ids || []).join(', ');
        const active = document.getElementById('wcf_is_active');
        if (active) active.checked = !!cfg.is_active;
        const activeField = document.getElementById('wcf_active_field');
        if (activeField) activeField.classList.remove('d-none');
        const hint = document.getElementById('wcf_create_hint');
        if (hint) hint.classList.add('d-none');
        const titleEl = document.querySelector('#webhookConfigEditModal .modal-title');
        if (titleEl) titleEl.textContent = t('Edit webhook configuration');
        applyScopeVisibility();
        openModal('webhookConfigEditModal');
      } catch (err) {
        showToast(err.message || t('Failed to load configuration'), 'danger');
      }
    }

    function parseProjectIds(raw) {
      if (!raw) return [];
      return String(raw)
        .split(/[\s,;\n]+/)
        .map(s => s.trim())
        .filter(s => s.length > 0)
        .map(s => parseInt(s, 10))
        .filter(n => Number.isFinite(n) && n > 0);
    }

    function buildPayload() {
      const scope = document.getElementById('wcf_scope_type').value;
      const name = document.getElementById('wcf_name').value.trim();
      if (!name) throw new Error(t('Name is required'));
      const payload = {
        name: name,
        scope_type: scope,
        description: document.getElementById('wcf_description').value.trim() || null,
      };
      if (scope === 'group' || scope === 'subgroup') {
        const path = document.getElementById('wcf_group_path').value.trim();
        if (!path) throw new Error(t('GitLab group path is required for this scope'));
        payload.gitlab_group_path = path;
        const gid = document.getElementById('wcf_group_id').value.trim();
        if (gid) payload.gitlab_group_id = parseInt(gid, 10);
      } else if (scope === 'projects') {
        const ids = parseProjectIds(document.getElementById('wcf_project_ids').value);
        if (ids.length === 0) throw new Error(t('At least one project ID is required'));
        payload.gitlab_project_ids = ids;
      }
      return payload;
    }

    async function submitWebhookConfigForm() {
      const btn = document.getElementById('wcfSubmitBtn');
      const configId = document.getElementById('wcfConfigId').value;
      let payload;
      try { payload = buildPayload(); }
      catch (err) { showToast(err.message, 'warning'); return; }
      try {
        setButtonLoading(btn, true);
        if (configId) {
          const updatePayload = { name: payload.name, description: payload.description };
          if ('gitlab_group_path' in payload) updatePayload.gitlab_group_path = payload.gitlab_group_path;
          if ('gitlab_group_id' in payload) updatePayload.gitlab_group_id = payload.gitlab_group_id;
          if ('gitlab_project_ids' in payload) updatePayload.gitlab_project_ids = payload.gitlab_project_ids;
          const active = document.getElementById('wcf_is_active');
          if (active) updatePayload.is_active = !!active.checked;
          await apiCall('/api/v1/webhook-configs/' + encodeURIComponent(configId), 'PATCH', updatePayload);
          showToast(t('Webhook configuration updated'), 'success');
          clearModalDirty('webhookConfigEditModal');
          closeModal('webhookConfigEditModal');
          await loadWebhookConfigsQuietly();
        } else {
          const reveal = await apiCall('/api/v1/courses/' + courseIdWh + '/webhook-configs', 'POST', payload);
          showSecretReveal(reveal);
          clearModalDirty('webhookConfigEditModal');
          closeModal('webhookConfigEditModal');
          await loadWebhookConfigsQuietly();
        }
      } catch (err) {
        showToast(err.message || t('Failed to save webhook configuration'), 'danger');
      } finally {
        setButtonLoading(btn, false);
      }
    }

    async function rotateWebhookConfig(configId, btn) {
      if (!configId) return;
      if (!await GP.confirmDialog({ message: t('Rotate secret? The current secret will be replaced. Both old and new secrets accept deliveries during a 24 h grace window.'), confirmText: t('Confirm'), variant: 'warning' })) return;
      /* The row button spins while the server rotates; the reveal modal that
         follows is the success signal, so no success toast on top of it. */
      setButtonLoading(btn, true);
      try {
        const reveal = await apiCall('/api/v1/webhook-configs/' + encodeURIComponent(configId) + '/rotate', 'POST');
        showSecretReveal(reveal);
        await loadWebhookConfigsQuietly();
      } catch (err) {
        showToast(err.message || t('Failed to rotate secret'), 'danger');
      } finally {
        setButtonLoading(btn, false);
      }
    }

    function requestRevokeWebhookConfig(configId, name) {
      if (!configId) return;
      document.getElementById('wcfRevokeConfigId').value = configId;
      document.getElementById('wcfRevokeConfigName').value = name || '';
      const hard = document.getElementById('wcf_revoke_hard');
      if (hard) hard.checked = false;
      openModal('webhookConfigRevokeModal');
    }

    async function confirmRevokeWebhookConfig() {
      const btn = document.getElementById('wcfConfirmRevokeBtn');
      const configId = document.getElementById('wcfRevokeConfigId').value;
      const hard = !!document.getElementById('wcf_revoke_hard')?.checked;
      if (!configId) return;
      try {
        setButtonLoading(btn, true);
        const url = '/api/v1/webhook-configs/' + encodeURIComponent(configId) + (hard ? '?hard=true' : '');
        await apiCall(url, 'DELETE');
        showToast(hard ? t('Webhook configuration deleted') : t('Webhook configuration revoked'), 'success');
        closeModal('webhookConfigRevokeModal');
        await loadWebhookConfigsQuietly();
      } catch (err) {
        showToast(err.message || t('Failed to revoke configuration'), 'danger');
      } finally {
        setButtonLoading(btn, false);
      }
    }

    function showSecretReveal(payload) {
      const secret = payload?.webhook_secret || '';
      const cfg = payload?.config || {};
      const secretInput = document.getElementById('webhookRevealSecret');
      if (secretInput) secretInput.value = secret;
      const nameEl = document.getElementById('webhookRevealName');
      if (nameEl) nameEl.textContent = cfg.name || '-';
      const scopeEl = document.getElementById('webhookRevealScope');
      if (scopeEl) scopeEl.textContent = (cfg.scope_type || '') + (cfg.scope_summary ? ' - ' + cfg.scope_summary : '');
      const graceRow = document.getElementById('webhookRevealGraceRow');
      const graceEl = document.getElementById('webhookRevealGrace');
      if (graceRow && graceEl) {
        if (payload?.previous_expires_at) {
          graceEl.innerHTML = GP.timeHtml(payload.previous_expires_at);
          graceRow.classList.remove('d-none');
        } else {
          graceRow.classList.add('d-none');
        }
      }
      openModal('webhookSecretRevealModal');
      setTimeout(() => { secretInput?.focus(); secretInput?.select(); }, 80);
    }

    function copyRevealedSecret() {
      const el = document.getElementById('webhookRevealSecret');
      if (!el || !el.value) return;
      copyToClipboard(el.value, t('Secret copied to clipboard'));
    }

    onDocumentClickAdvanced = function (e) {
      const trg = e.target.closest('[data-action]');
      if (!trg) return;
      const action = trg.getAttribute('data-action');
      switch (action) {
        // THE refresh contract (GP.refreshRegion): the button reports it is
        // working, the table dims in place, and exactly one toast follows -
        // "reloaded" or the actual error, never both.
        case 'reloadWebhookConfigs':
          GP.refreshRegion({
            button: trg,
            region: container,
            load: loadWebhookConfigs,
            successMessage: t('Webhook configurations reloaded'),
            errorMessage: t('Failed to load webhook configurations'),
          });
          break;
        case 'openCreateWebhookConfigModal': openCreateWebhookConfigModal(); break;
        case 'editWebhookConfig': openEditWebhookConfigModal(trg.dataset.configId); break;
        case 'rotateWebhookConfig': rotateWebhookConfig(trg.dataset.configId, trg); break;
        case 'requestRevokeWebhookConfig':
          requestRevokeWebhookConfig(trg.dataset.configId, trg.dataset.configName);
          break;
        case 'confirmRevokeWebhookConfig': confirmRevokeWebhookConfig(); break;
        case 'submitWebhookConfigForm': submitWebhookConfigForm(); break;
        case 'copyRevealedSecret': copyRevealedSecret(); break;
        default: return;
      }
    };
    document.addEventListener('click', onDocumentClickAdvanced);

    /* No `GP.webhookConfigs` facade: all five of these are driven from the
       delegated click handler above and nothing ever called them through the
       object, so it was a public API with no consumers. */

  })();

  onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-page-config') || target.id === 'gp-page-config')) {
      GP.courseSettingsCleanup();
    }
  };
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.courseSettingsCleanup = () => {
    _fullConfigImportHandle.destroy();
    _checksImportHandle.destroy();
    _disconnectSettingsSSE();
    if (_syncLockPoller) { clearInterval(_syncLockPoller); _syncLockPoller = null; }

    document.removeEventListener('DOMContentLoaded', onDOMContentLoadedCore);
    document.removeEventListener('alpine:initialized', onAlpineInitialized);
    document.removeEventListener('DOMContentLoaded', onDOMContentLoadedScoring);
    document.removeEventListener('click', onDocumentClickSection);
    document.removeEventListener('change', onDocumentChangeSection);
    document.removeEventListener('click', onDocumentClickCheck);
    document.removeEventListener('click', onDocumentClickPatternPreset);
    document.removeEventListener('modal-closed', onModalClosed);
    document.removeEventListener('change', onDocumentChangeAdvanced);
    document.removeEventListener('gp-health-change', onHealthChange);
    document.removeEventListener('visibilitychange', onVisibilityChange);
    window.removeEventListener('beforeunload', onBeforeUnload);
    window.removeEventListener('gp:global-job-start', onGlobalJobStart);
    window.removeEventListener('gp:job-complete', onJobComplete);
    document.removeEventListener('click', onDocumentClickAdvanced);
    document.removeEventListener('click', onWeeklyDeadlineClick);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };

