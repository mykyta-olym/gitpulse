  /* ==========================================
   *  Weekly Deadlines - form editor
   * ------------------------------------------
   *  Weekly deadlines used to be editable ONLY by hand-writing JSON into a
   *  textarea, which is unusable for a teacher and easy to corrupt. This adds
   *  an Add/Edit/Delete modal on top. The textarea stays the single source of
   *  truth (it is what the settings save posts), so no new endpoint was needed
   *  and the JSON path keeps working for power users.
   * ========================================== */

  function _wdTextarea() {
    return document.querySelector('textarea[name="weekly_deadlines"]');
  }

  /** Parse the textarea into an array; never throws. */
  function _wdRead() {
    const el = _wdTextarea();
    if (!el) return [];
    try {
      const parsed = JSON.parse(el.value || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  }

  /** Write back, keep the list ordered by week, refresh the table, mark dirty. */
  function _wdWrite(list) {
    const el = _wdTextarea();
    if (!el) return;
    list.sort(function (a, b) { return (Number(a.week) || 0) - (Number(b.week) || 0); });
    el.value = JSON.stringify(list, null, 2);
    _wdRender(list);
    GP.addDirtyReason('settings_form', t('Weekly deadlines changed'));
  }

  /** One row action, identical to the server's `btn_icon_only`: secondary,
      and the red trash for a delete, as in every other table. */
  function _wdRowAction(action, iconName, index, label, tip, variant) {
    const svg = GP.iconSvg(iconName, 'sm');
    const locked = !!document.querySelector('.is-course-archived');
    const tooltip = locked ? t('This course is archived and read-only. Reactivate it to make changes.') : tip;
    return '<button type="button" class="btn btn-icon-only btn-' + variant + ' btn-sm"'
      + (locked ? ' disabled data-archived-locked="1"' : '')
      + ' data-action="' + action + '" data-week-index="' + index + '"'
      + ' aria-label="' + _esc(label) + '"'
      + ' data-tippy-content="' + _esc(tooltip) + '">' + svg + '</button>';
  }

  /** Rebuild the summary table from the current JSON. */
  function _wdRender(list) {
    const body = document.getElementById('weeklyDeadlinesBody');
    const wrap = document.getElementById('weeklyDeadlinesSummary');
    const empty = document.getElementById('weeklyDeadlinesEmpty');
    if (!body) return;
    const rows = list || _wdRead();
    if (wrap) wrap.classList.toggle('d-none', rows.length === 0);
    if (empty) empty.classList.toggle('d-none', rows.length > 0);

    body.innerHTML = rows.map(function (wd, i) {
      const checks = Array.isArray(wd.expected_checks) ? wd.expected_checks : [];
      const chips = checks.length
        ? '<span class="weekly-check-chips">' + checks.map(function (c) {
            return GP.badgeHtml(c, 'gray', { size: 'sm' });
          }).join('') + '</span>'
        : '<span class="muted">-</span>';
      return '<tr>'
        + '<td>' + GP.badgeHtml(wd.week, 'primary') + '</td>'
        + '<td>' + _esc(wd.label || ('Week ' + wd.week)) + '</td>'
        + '<td>' + chips + '</td>'
        + '<td class="text-right text-nowrap">'
        /* The SAME icon buttons the server renders for this row (btn_icon_only,
           edit + trash). This used to emit text buttons, so adding a week
           silently changed every row's actions from two glyphs to two words. */
        + '<div class="gl-row-actions">'
        + _wdRowAction('editWeek', 'edit', i, t('Edit week'), t('Edit this week'), 'secondary')
        + _wdRowAction('deleteWeek', 'trash', i, t('Delete week'), t('Delete this week'), 'danger')
        + '</div></td></tr>';
    }).join('');
    if (window.GP && GP.initTippy) GP.initTippy(body);
  }

  /** Build the expected-checks picker from the course's OWN checks, so custom
   *  checks are selectable too (the JSON reference only ever showed R01-R12). */
  function _wdBuildCheckGrid(selected) {
    const grid = document.getElementById('wdCheckGrid');
    if (!grid) return;
    const sel = {};
    (selected || []).forEach(function (c) { sel[c] = true; });
    const fallback = ['R01', 'R02', 'R03', 'R04', 'R05', 'R06', 'R07', 'R08', 'R09', 'R10', 'R11', 'R12', 'R13'];
    const source = (Array.isArray(_allChecks) && _allChecks.length)
      ? _allChecks
      : fallback.map(function (c) { return { check_code: c, name: c, is_active: true }; });

    grid.innerHTML = source.map(function (c) {
      const code = c.check_code;
      const id = 'wdChk_' + code;
      return '<label class="wd-check-item" for="' + id + '">'
        + '<input type="checkbox" class="form-check-input" id="' + id + '" value="' + _esc(code) + '"' + (sel[code] ? ' checked' : '') + '>'
        + '<span class="wd-check-code">' + _esc(code) + '</span>'
        + '<span class="wd-check-name">' + _esc(c.name || '') + '</span>'
        + (c.is_active === false ? GP.badgeHtml(t('disabled'), 'gray', { size: 'sm' }) : '')
        + '</label>';
    }).join('');
  }

  function _wdSelectedChecks() {
    return Array.prototype.map.call(
      document.querySelectorAll('#wdCheckGrid input[type="checkbox"]:checked'),
      function (cb) { return cb.value; }
    );
  }

  /** Open the modal for a new week (index null) or an existing one. */
  function _wdOpen(index) {
    const list = _wdRead();
    const entry = (index === null || index === undefined) ? null : list[index];
    const idxEl = document.getElementById('wdEditIndex');
    if (idxEl) idxEl.value = entry ? String(index) : '';

    const weekEl = document.getElementById('wdWeek');
    const labelEl = document.getElementById('wdLabel');
    const mrEl = document.getElementById('wdMrDeadline');
    const mergeEl = document.getElementById('wdMergeDeadline');

    // Default a NEW entry to the next free week so the teacher rarely retypes.
    let nextWeek = 1;
    if (list.length) {
      const maxWeek = list.reduce(function (m, w) { return Math.max(m, Number(w.week) || 0); }, 0);
      nextWeek = Math.min(30, maxWeek + 1);
    }
    if (weekEl) weekEl.value = entry ? (entry.week || 1) : nextWeek;
    if (labelEl) labelEl.value = entry ? (entry.label || '') : '';
    [[mrEl, entry && entry.mr_deadline], [mergeEl, entry && entry.merge_deadline]].forEach(function (field) {
      const el = field[0], value = field[1] || '';
      if (!el) return;
      if (el._flatpickr) el._flatpickr.setDate(value || [], false);
      else el.value = String(value).slice(0, 16);
    });

    const loadingEl = document.getElementById('wdCheckGridLoading');
    if (loadingEl) loadingEl.remove();
    _wdBuildCheckGrid(entry ? entry.expected_checks : []);
    openModal('weeklyDeadlineModal');
  }

  function _wdSaveFromModal() {
    const list = _wdRead();
    const idxEl = document.getElementById('wdEditIndex');
    const rawIndex = idxEl ? idxEl.value : '';
    const weekEl = document.getElementById('wdWeek');
    const week = parseInt(weekEl ? weekEl.value : '', 10);
    if (!week || week < 1 || week > 30) {
      if (showToast) showToast(t('Week number must be between 1 and 30'), 'warning');
      return;
    }
    // A duplicate week silently shadows the other entry in the engine (it picks
    // the latest entry whose week is <= the current one), so reject it here.
    let dupIndex = -1;
    list.forEach(function (w, i) { if (Number(w.week) === week && dupIndex === -1) dupIndex = i; });
    if (dupIndex !== -1 && String(dupIndex) !== String(rawIndex)) {
      if (showToast) showToast(t('That week already exists - edit that entry instead.'), 'warning');
      return;
    }

    const entry = { week: week };
    const labelEl = document.getElementById('wdLabel');
    const label = labelEl ? labelEl.value.trim() : '';
    if (label) entry.label = label;
    const mrEl = document.getElementById('wdMrDeadline');
    if (mrEl && mrEl.value) entry.mr_deadline = mrEl.value;
    const mergeEl = document.getElementById('wdMergeDeadline');
    if (mergeEl && mergeEl.value) entry.merge_deadline = mergeEl.value;
    entry.expected_checks = _wdSelectedChecks();

    if (rawIndex === '') list.push(entry);
    else list[Number(rawIndex)] = entry;

    _wdWrite(list);
    if (typeof clearModalDirty === 'function') clearModalDirty('weeklyDeadlineModal');
    closeModal('weeklyDeadlineModal');
    if (showToast) showToast(t('Week saved - remember to press Update settings.'), 'success');
  }

  const onWeeklyDeadlineClick = async function (e) {
    if (!e.target.closest) return;
    if (e.target.closest('#btnAddWeeklyDeadline')) { e.preventDefault(); _wdOpen(null); return; }

    const editBtn = e.target.closest('[data-action="editWeek"]');
    if (editBtn) { e.preventDefault(); _wdOpen(Number(editBtn.dataset.weekIndex)); return; }

    const delBtn = e.target.closest('[data-action="deleteWeek"]');
    if (delBtn) {
      e.preventDefault();
      const idx = Number(delBtn.dataset.weekIndex);
      const list = _wdRead();
      const wk = list[idx];
      if (!wk) return;
      if (!await GP.confirmDialog({ message: t('Delete week') + ' ' + wk.week + '?',
                        confirmText: t('Confirm'), variant: 'danger' })) return;
      list.splice(idx, 1);
      _wdWrite(list);
      if (showToast) showToast(t('Week removed - remember to press Update settings.'), 'info');
      return;
    }

    if (e.target.closest('#btnSaveWeeklyDeadline')) { e.preventDefault(); _wdSaveFromModal(); return; }
    if (e.target.closest('#btnWdSelectAll')) {
      e.preventDefault();
      document.querySelectorAll('#wdCheckGrid input[type="checkbox"]').forEach(function (cb) { cb.checked = true; });
      return;
    }
    if (e.target.closest('#btnWdClearAll')) {
      e.preventDefault();
      document.querySelectorAll('#wdCheckGrid input[type="checkbox"]').forEach(function (cb) { cb.checked = false; });
    }
  };
  document.addEventListener('click', onWeeklyDeadlineClick);

  /* Import: the shared `json_drop` component loads a dropped or browsed file
     straight into this editor and fires a synthetic change, so there is no
     separate file input to read and no second copy of the FileReader logic.
     A trusted change is the teacher typing - leave their text exactly as
     written rather than reformatting it under the cursor. */
  const _wdEditor = _wdTextarea();
  if (_wdEditor) {
    _wdEditor.addEventListener('change', function (ev) {
      if (ev.isTrusted) return;
      const raw = String(this.value || '').trim();
      if (!raw) { _wdWrite([]); return; }
      let parsed;
      try {
        parsed = JSON.parse(raw);
      } catch (_) {
        if (showToast) showToast(t('That file is not valid JSON.'), 'danger');
        return;
      }
      if (!Array.isArray(parsed)) {
        if (showToast) showToast(t('Expected a JSON array of week objects.'), 'danger');
        return;
      }
      _wdWrite(parsed);
      if (showToast) showToast(t('Weekly deadlines imported - remember to press Update settings.'), 'success');
    });
  }

  GP.activePageCleanup = GP.courseSettingsCleanup;
