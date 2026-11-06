  /* ==========================================
   *  LLM Generate Modal
   * ========================================== */
  let _llmSuggestions = [];

  function _resetLLMModal() {
    _llmSuggestions = [];
    GP.clearDirtyReason('llm_suggestions');
    const promptEl = document.getElementById('llmPrompt');
    const countEl = document.getElementById('llmCount');
    if (promptEl) promptEl.value = '';
    if (countEl) {
      countEl.value = '3';
      countEl.dispatchEvent(new Event('input', { bubbles: true }));
    }
    const sugBox = document.getElementById('llmSuggestions');
    if (sugBox) sugBox.classList.add('d-none');
    const sugBody = document.getElementById('llmSuggestionsBody');
    if (sugBody) sugBody.innerHTML = '';
    const saveBtn = document.getElementById('btnSaveLLMChecks');
    if (saveBtn) saveBtn.classList.add('d-none');
    const runBtn = document.getElementById('btnRunLLM');
    if (runBtn) runBtn.classList.remove('d-none');
    const newBtn = document.getElementById('btnNewLLMGeneration');
    if (newBtn) newBtn.classList.add('d-none');
  }

  function _restoreLLMSuggestions() {
    renderLLMSuggestions();
    const sugBox = document.getElementById('llmSuggestions');
    if (sugBox) sugBox.classList.remove('d-none');
    const saveBtn = document.getElementById('btnSaveLLMChecks');
    if (saveBtn) saveBtn.classList.remove('d-none');
    const runBtn = document.getElementById('btnRunLLM');
    if (runBtn) runBtn.classList.add('d-none');
    const newBtn = document.getElementById('btnNewLLMGeneration');
    if (newBtn) newBtn.classList.remove('d-none');
  }

  document.getElementById('btnGenerateChecks')?.addEventListener('click', function () {
    if (!_guardCourseWrite()) return;
    // Guard: LLM feature must be enabled globally and API key configured
    if ((_cfg.disabledFeatures || {}).llm_suggestions) {
      showToast(t('LLM suggestions feature is disabled'), 'warning');
      return;
    }
    if (!_cfg.llmApiKeyConfigured) {
      showToast(t('LLM API key is not configured. Set LLM_API_KEY in environment.'), 'warning');
      return;
    }
    if (_llmSuggestions.length > 0) {
      // Restore previous suggestions instead of wiping
      _restoreLLMSuggestions();
    } else {
      _resetLLMModal();
    }
    openModal('llmGenerateModal');
  });

  /* "New Generation" button - explicitly resets the modal for a fresh run */
  document.getElementById('btnNewLLMGeneration')?.addEventListener('click', function () {
    _resetLLMModal();
  });

  let _llmRunning = false;
  let _llmAbortController = null;
  let _llmCancelRequested = false;

  /* Async: the confirmation runs on the app's dialog now. Callers that pass
     `{confirm:false}` never await anything, so they are unaffected. */
  async function cancelActiveLLMGeneration(options = {}) {
    if (!_llmRunning || !_llmAbortController) return false;
    if (options.confirm !== false) {
      const ok = await GP.confirmDialog({ message: t('Cancel AI generation?'), confirmText: t('Confirm'), variant: 'warning' });
      if (!ok) return false;
    }
    _llmCancelRequested = true;
    try {
      _llmAbortController.abort(new DOMException(t('AI generation cancelled.'), 'AbortError'));
    } catch (_) {
      _llmAbortController.abort();
    }
    GP.clearDirtyReason('llm_running');
    GP.finishGlobalJobOrToast('llm_generate', t('AI generation cancelled.'), 'error', { type: 'warning' });
    return true;
  }

  /* One export, not two. The global-job-bar calls this as
     `window.cancelActiveLLMGeneration`; the parallel `GP.` alias beside it was
     never read, so the function had two public names and one of them could
     drift out of use unnoticed - which it had. */
  window.cancelActiveLLMGeneration = cancelActiveLLMGeneration;

  document.getElementById('btnRunLLM')?.addEventListener('click', async function () {
    const count = parseInt(document.getElementById('llmCount')?.value, 10) || 3;
    const prompt = document.getElementById('llmPrompt')?.value?.trim() || '';

    if (count < 1 || count > 20) { showToast(t('Count must be between 1 and 20'), 'warning'); return; }
    if (typeof isGlobalJobRunning === 'function' && isGlobalJobRunning('llm_generate') && typeof confirmProcessRestart === 'function' && !await confirmProcessRestart('llm_generate', t('AI Generation'))) return;

    const btn = this;
    try {
      await _lock('llmGenerate:' + _courseId, async () => {
        const controller = new AbortController();
        _llmAbortController = controller;
        _llmCancelRequested = false;
        setButtonLoading(btn, true);
        _llmRunning = true;
        GP.addDirtyReason('llm_running');
        if (typeof deferGlobalJob === 'function') {
          deferGlobalJob(t('Generating checks with AI...'), 'llm_generate', { localIndicatorSelector: '#btnRunLLM' });
        }
        const result = await apiCall('/dashboard/courses/' + _courseId + '/custom-checks/generate', 'POST', {
          count: count, prompt: prompt,
        }, {
          signal: controller.signal,
          abortMessage: t('AI generation cancelled.'),
          maxRetries: 0,
        });

        _llmSuggestions = result.suggestions || [];
        if (!_llmSuggestions.length) {
          const message = t('No suggestions generated');
          GP.finishGlobalJobOrToast('llm_generate', message, 'done', { type: 'warning' });
          return;
        }

        renderLLMSuggestions();
        const sugBox = document.getElementById('llmSuggestions');
        if (sugBox) sugBox.classList.remove('d-none');
        const saveBtn = document.getElementById('btnSaveLLMChecks');
        if (saveBtn) saveBtn.classList.remove('d-none');
        // Switch to "New Generation" mode
        const runBtn = document.getElementById('btnRunLLM');
        if (runBtn) runBtn.classList.add('d-none');
        const newBtn = document.getElementById('btnNewLLMGeneration');
        if (newBtn) newBtn.classList.remove('d-none');

        GP.finishGlobalJobOrToast('llm_generate', _llmSuggestions.length + ' ' + t('AI suggestions ready'), 'done');
      });
    } catch (err) {
      if (err.code !== 'LOCKED') {
        const cancelled = _llmCancelRequested || err.name === 'AbortError';
        const message = cancelled ? t('AI generation cancelled.') : (err.message || t('Generation failed'));
        GP.finishGlobalJobOrToast('llm_generate', message, 'error', cancelled ? { type: 'warning' } : undefined);
      }
    } finally {
      _llmRunning = false;
      _llmAbortController = null;
      _llmCancelRequested = false;
      GP.clearDirtyReason('llm_running');
      if (_llmSuggestions.length > 0) GP.addDirtyReason('llm_suggestions');
      setButtonLoading(btn, false);
    }
  });

  /* Promote global bar if modal closed while LLM generation is still running */
  onModalClosed = function (e) {
    if (e.detail?.id === 'llmGenerateModal' && _llmRunning) {
      if (typeof promoteGlobalJob === 'function') promoteGlobalJob('llm_generate');
    }
  };
  document.addEventListener('modal-closed', onModalClosed);

  function renderLLMSuggestions() {
    const body = document.getElementById('llmSuggestionsBody');
    if (!body) return;
    body.innerHTML = '';

    // Mark suggestions that duplicate existing check names
    const existingNames = new Set(_allChecks.map(function (c) { return c.name.toLowerCase(); }));

    _llmSuggestions.forEach(function (s, i) {
      const isDuplicate = existingNames.has((s.name || '').toLowerCase());
      const div = document.createElement('div');
      div.className = 'llm-suggestion' + (isDuplicate ? ' llm-suggestion-duplicate' : '');
      div.innerHTML =
        '<label class="llm-suggestion-header">' +
          '<input type="checkbox" id="llm-suggestion-' + i + '" class="form-check-input llm-suggestion-cb" data-idx="' + i + '"' + (isDuplicate ? '' : ' checked') + '> ' +
          GP.badgeHtml(s.check_code, 'info', { size: 'sm' }) + ' ' +
          '<strong>' + _esc(s.name) + '</strong>' +
          (isDuplicate ? ' ' + GP.badgeHtml(t('Duplicate'), 'warning', { size: 'sm' }) : '') +
        '</label>' +
        '<p class="muted llm-suggestion-desc">' + _esc(s.description || '') + '</p>' +
        '<div class="llm-suggestion-meta">' +
          GP.badgeHtml(CATEGORY_LABELS[s.category] || s.category,
            (CATEGORY_BADGES[s.category] || 'badge-gray').replace(/^badge-/, ''), { size: 'sm' }) +
          ' <span class="muted">' + t('Weight') + ': ' + (s.weight || 0.05).toFixed(2) + '</span>' +
        '</div>';
      body.appendChild(div);
    });

    // Selection summary
    let summaryEl = document.getElementById('llmSelectionSummary');
    if (!summaryEl) {
      summaryEl = document.createElement('div');
      summaryEl.id = 'llmSelectionSummary';
      summaryEl.className = 'llm-selection-summary';
      body.parentNode.appendChild(summaryEl);
    }
    _updateLLMSelectionSummary();
  }

  function _updateLLMSelectionSummary() {
    const summaryEl = document.getElementById('llmSelectionSummary');
    if (!summaryEl) return;
    const total = _llmSuggestions.length;
    const checked = document.querySelectorAll('.llm-suggestion-cb:checked').length;
    summaryEl.innerHTML = '<strong>' + checked + '</strong> / ' + total + ' ' + t('selected');
    summaryEl.classList.toggle('d-none', total === 0);
  }

  /* Update count when user toggles checkboxes */
  onDocumentChangeAdvanced = function (e) {
    if (e.target.matches('.llm-suggestion-cb')) _updateLLMSelectionSummary();
  };
  document.addEventListener('change', onDocumentChangeAdvanced);

  document.getElementById('btnSaveLLMChecks')?.addEventListener('click', async function () {
    if (!_guardCourseWrite()) return;
    const selected = [];
    document.querySelectorAll('.llm-suggestion-cb:checked').forEach(function (cb) {
      const idx = parseInt(cb.dataset.idx, 10);
      if (_llmSuggestions[idx]) selected.push(_llmSuggestions[idx]);
    });

    if (!selected.length) { showToast(t('No checks selected'), 'warning'); return; }

    const btn = this;
    try {
      await _lock('saveLLMChecks:' + _courseId, async () => {
        setButtonLoading(btn, true);
        let saved = 0;
        const errors = [];
        for (let i = 0; i < selected.length; i++) {
          const s = selected[i];
          try {
            await apiCall('/dashboard/courses/' + _courseId + '/custom-checks', 'POST', {
              name: s.name,
              description: s.description || '',
              category: s.category || 'custom',
              evaluation_rule: s.evaluation_rule || {},
              weight: s.weight || 0.05,
              created_by: 'llm',
            });
            saved++;
          } catch (itemErr) {
            errors.push(_esc(s.name) + ': ' + (itemErr.message || t('Failed')));
          }
        }
        if (errors.length === 0) {
          showToast(saved + ' ' + t('checks created'), 'success');
          _llmSuggestions = [];
          GP.clearDirtyReason('llm_suggestions');
          forceCloseModal?.('llmGenerateModal');
        } else {
          showToast(saved + ' ' + t('saved') + ', ' + errors.length + ' ' + t('failed') + ': ' + errors.join('; '), saved > 0 ? 'warning' : 'danger');
        }
        if (saved > 0) await loadAllChecksQuietly();
      });
    } catch (err) {
      if (err.code !== 'LOCKED') showToast(err.message || t('Save failed'), 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  });

