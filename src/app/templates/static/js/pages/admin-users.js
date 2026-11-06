/* Admin users page logic */;(function() {
'use strict';
  const GP = window.GP || {};
  GP.runPageCleanup();
  const { apiCall, showToast, t, escapeHtml: _escHtml, withUiLock: _lock } = GP;
  let _disposed = false;
  /* -- Role config -- */
  let _cfg = {};
  try { const _ce = document.getElementById('gp-page-config'); if (_ce) _cfg = JSON.parse(_ce.textContent); } catch (_) { /* */ }
  const _isAdmin = !!_cfg.isAdmin;

  const _REFRESH_DEBOUNCE_MS = 2000;

  function statusIndicatorHtml(isActive) {
    const variant = isActive ? 'success' : 'muted';
    const label = _escHtml(t(isActive ? 'Active' : 'Inactive'));
    return `<span class="status-indicator status-indicator--${variant}"><span class="status-dot status-dot--sm"></span><span class="status-label">${label}</span></span>`;
  }

  // Live reads and edits must update the row and its next Edit together.
  function updateUserRowState(row, user) {
    const isBot = row.dataset.bot === '1';
    if (user.role && row.dataset.role !== user.role) {
      const roleCell = row.querySelector('td.col-role');
      if (roleCell && !isBot) roleCell.innerHTML = GP.roleBadgeHtml(user.role);
      row.dataset.role = user.role;
    }
    if (user.is_active !== undefined) {
      const statusCell = row.querySelector('td.col-status');
      if (statusCell) statusCell.innerHTML = statusIndicatorHtml(user.is_active);
      row.classList.toggle('row-inactive', !user.is_active);
    }
    const editBtn = row.querySelector('button[data-action="openEditUserModal"]');
    if (editBtn) {
      const args = JSON.parse(editBtn.dataset.actionArgs);
      args[2] = user.role || args[2];
      args[3] = user.is_active ?? args[3];
      args[4] = isBot;
      editBtn.dataset.actionArgs = JSON.stringify(args);
    }
  }
// -- Live table refresh (replaces location.reload) --
  let _lastRefreshTs = 0;
  let _tableReadId = 0;

  async function refreshUserTable() {
    // Debounce: skip if called within 2s of last successful refresh
    const now = Date.now();
    if (_disposed || now - _lastRefreshTs < _REFRESH_DEBOUNCE_MS) return;
    const tbody = document.querySelector('.users-table tbody');
    if (!tbody) return;
    const readId = ++_tableReadId;
    try {
      /* Keyed: the list reloads on refresh, after an enrich, and from the
         filter toolbar - three triggers that can overlap. */
      const data = await apiCall('/dashboard/admin/users/list', 'GET', null,
                                 { key: 'admin:users:list' });
      
      if (_disposed || readId !== _tableReadId || !tbody.isConnected || !data.users) return;
      
      _lastRefreshTs = Date.now();
      
      data.users.forEach(user => {
        // Find row by username in data-search or by the username cell
        const rows = tbody.querySelectorAll('tr');
        for (const row of rows) {
          const usernameCell = row.querySelector('td:first-child strong');
          if (!usernameCell || usernameCell.textContent.trim() !== user.username) continue;
          
          const cells = row.querySelectorAll('td');
          // GitLab User ID (2nd column, index 1)
          if (cells[1] && user.gitlab_user_id) {
            const valEl = cells[1].querySelector('.users-cell-value');
            const oldId = (valEl ? valEl.textContent : cells[1].textContent).trim();
            const newId = String(user.gitlab_user_id);
            if (oldId !== newId && oldId === '-') {
              if (valEl) {
                valEl.textContent = newId;
              } else {
                cells[1].innerHTML = `<span class="users-cell-value">${_escHtml(newId)}</span>`;
              }
            }
          }
          // Full Name (3rd column, index 2)
          if (cells[2]) {
            const valEl = cells[2].querySelector('.users-cell-value');
            const oldText = (valEl ? valEl.textContent : cells[2].textContent).trim();
            const newText = user.full_name || '-';
            if (oldText !== newText) {
              if (valEl) {
                valEl.textContent = newText;
                valEl.setAttribute('data-tippy-content', newText);
              } else {
                cells[2].innerHTML = `<span class="users-cell-value" data-tippy-content="${_escHtml(newText)}">${_escHtml(newText)}</span>`;
              }
            }
          }
          // Email (4th column, index 3) - compare using textContent only
          if (cells[3]) {
            const valEl = cells[3].querySelector('.users-cell-value');
            const oldEmail = (valEl ? valEl.textContent : cells[3].textContent).trim();
            const newEmailText = user.email || '-';
            // Compare plain text values (PRIVATE textContent stays "PRIVATE")
            if (oldEmail !== newEmailText) {
              if (user.email === 'PRIVATE') {
                const privHtml = '<span class="muted">' + _escHtml(t('PRIVATE')) + '</span>';
                if (valEl) {
                  valEl.innerHTML = privHtml;
                  valEl.removeAttribute('data-tippy-content');
                } else {
                  cells[3].innerHTML = '<span class="users-cell-value">' + privHtml + '</span>';
                }
              } else {
                if (valEl) {
                  valEl.textContent = newEmailText;
                  if (newEmailText && newEmailText !== '-') {
                    valEl.setAttribute('data-tippy-content', newEmailText);
                  } else {
                    valEl.removeAttribute('data-tippy-content');
                  }
                } else {
                  const tipAttr = (newEmailText && newEmailText !== '-') ? ` data-tippy-content="${_escHtml(newEmailText)}"` : '';
                  cells[3].innerHTML = `<span class="users-cell-value"${tipAttr}>${_escHtml(newEmailText)}</span>`;
                }
              }
            }
          }
          updateUserRowState(row, user);
          
          // Update data-search for filtering
          const searchStr = `${user.username.toLowerCase()} ${(user.full_name || '').toLowerCase()} ${(user.email || '').toLowerCase()}`;
          row.setAttribute('data-search', searchStr);
          break;
        }
      });
      _userFilter?.apply();
    } catch (e) {
      if (_disposed || readId !== _tableReadId || e?.superseded) return;
      console.error('Failed to refresh user table:', e);
      showToast(t('Failed to refresh user data'), 'danger');
    }
  }
  
  // -- Edit User Modal --
  function openEditUserModal(id, username, role, isActive, isBot) {
    if (!_isAdmin) return;
    const setVal = (elId, v) => { const el = document.getElementById(elId); if (el) el.value = v; };
    const setChk = (elId, v) => { const el = document.getElementById(elId); if (el) el.checked = v; };
    setVal('editUserId', id);
    setVal('editUsername', username);
    setVal('editRole', role);
    setChk('editIsActive', isActive);
    setChk('editIsBot', !!isBot);
    openModal('editUserModal');
  }

  async function updateUser(e) {
    if (!_isAdmin) { showToast(t('Admin access required'), 'warning'); return; }
    const form = e.target;
    const userId = form.user_id.value;
    return submitModalForm(e, {
      url: `/api/v1/users/${userId}`,
      method: 'PUT',
      modalId: 'editUserModal',
      btnSelector: '#editUserBtn',
      reload: false,
      getData: (f) => ({
        role: f.role.value,
        is_active: f.is_active.checked,
        is_bot: f.is_bot ? f.is_bot.checked : undefined,
      }),
      successMsg: t('User updated!') + ' - ' + (form.username?.value || ''),
      onSuccess(result) {
        // Show warning if user is a course owner being demoted
        if (result && result._warning) {
          showToast(result._warning, 'warning', 8000);
        }

        // Bot toggle changes which table the row belongs to -> reload the
        // whole content fragment so the row moves into / out of the
        // Service Accounts panel.
        const newIsBot = !!form.is_bot?.checked;
        // result.is_bot is the persisted value AFTER the update; if it
        // differs from any row in the current "humans" table that has the
        // same username, the row needs to switch panels.
        const formUsername = form.querySelector('[name="username"]')?.value || document.getElementById('editUsername')?.value;
        let oldIsBot = false;
        const allRows = document.querySelectorAll('.users-table tbody tr');
        for (const r of allRows) {
          const u = r.querySelector('td:first-child strong');
          if (u && u.textContent.trim() === formUsername) {
            oldIsBot = r.getAttribute('data-bot') === '1';
            break;
          }
        }
        if (oldIsBot !== newIsBot) {
          const lazy = document.querySelector('.gl-lazy-content');
          if (lazy && window.htmx) {
            window.htmx.trigger(lazy, 'load');
          } else {
            if (typeof reloadKeepScroll === 'function') {
              reloadKeepScroll();
            } else {
              const freshUrl = GP.cacheBustedCurrentUrl() || window.location.href;
              window.location.assign(freshUrl);
            }
          }
          return;
        }

        // Update the table row in-place
        const newRole = form.role.value;
        const newActive = form.is_active.checked;
        const username = form.querySelector('[name="username"]')?.value || document.getElementById('editUsername')?.value;
        
        // Find row by username
        const rows = document.querySelectorAll('.data-table tbody tr');
        for (const row of rows) {
          const usernameCell = row.querySelector('td:first-child strong');
          if (!usernameCell || usernameCell.textContent.trim() !== username) continue;
          
          updateUserRowState(row, { role: newRole, is_active: newActive });

          // Refresh sidebar badge counts
          if (typeof GP.refreshSidebarBadges === 'function') GP.refreshSidebarBadges();
          break;
        }

        // Re-apply filters so the table reflects the new role immediately
        if (typeof _userFilter?.apply === 'function') _userFilter.apply();
      }
    });
  }

  // -- Table Filtering + Pagination (using component library) --
  // Deferred: the table may not exist yet if using lazy-shell loading.
  let _rolePills;
  let _userPaginator;
  let _userFilter;

  function _initTableComponents() {
    const table = document.querySelector('.users-table');
    const controls = document.getElementById('paginationControls');
    if (!table || !controls) return;

    if (table._clientPaginator && document.body.contains(table._clientPaginator.controls)) {
      _userPaginator = table._clientPaginator;
      return;
    }

    _userPaginator = new ClientPaginator({
      tbodySelector: '.users-table tbody',
      controlsSelector: '#paginationControls',
      storageKey: 'users',
      showPerPage: true,
      pageSizes: [25, 50, 100]
    }).register('userTable');

    _rolePills = new FilterPills('.users-role-filter', 'data-value', function() {
      _userFilter.apply();
    });
    const roleParam = (new URLSearchParams(window.location.search).get('role') || '').toLowerCase();
    if (roleParam) _rolePills.setActive(roleParam);

    _userFilter = new TableFilter({
      inputSelector: '#userSearch',
      tbodySelector: '.users-table tbody',
      paginator: _userPaginator,
      urlParams: () => ({ role: _rolePills.activeValue }),
      rowFilter: function (row) {
        const pill = _rolePills.activeValue;
        const isBot = row.dataset.bot === '1';
        // "All" is all the PEOPLE. A service account is a different kind of row,
        // not a fourth role, and a reader opening this page is here for the
        // people - the accounts have their own view, set apart in the strip.
        return pill === 'all' ? !isBot : pill === 'bot' ? isBot : !isBot && row.dataset.role === pill;
      },
    });
    _userFilter.apply();

    // Bind enrich form submit (form is inside content partial)
    const _ef = document.getElementById('enrichForm');
    if (_ef && !_ef._bound) {
      _ef._bound = true;
      _ef.addEventListener('submit', _handleEnrichSubmit);
    }
  }

  // Try immediately (works when page is rendered without lazy shell)
  _initTableComponents();

  // Also listen for HTMX swap (lazy shell loads content asynchronously)
  const onAfterSwap = function (evt) {
    if (document.querySelector('.users-table')) {
      _initTableComponents();
    }
  };
  document.body.addEventListener('htmx:afterSwap', onAfterSwap);

  // -- GitLab Enrichment - global-job-bar.js handles all polling/SSE --
  let _enrichDone = false;
  let _lastEnrichPct = -1;

  // Named handler for enrich form submit - bound inside _initTableComponents
  async function _handleEnrichSubmit(e) {
      e.preventDefault();
      if (!_isAdmin) { showToast(t('Admin access required'), 'warning'); return; }
      if (typeof isGlobalJobRunning === 'function' && isGlobalJobRunning('enrichment') && typeof confirmProcessRestart === 'function' && !confirmProcessRestart('enrichment', 'GitLab enrichment')) return;
      _enrichDone = false;
      _lastEnrichPct = -1;
      try {
        await _lock('enrichGitlab', async () => {
          setButtonLoading(document.getElementById('enrichBtn'), true);
          const data = await apiCall('/dashboard/admin/users/enrich-gitlab', 'POST', {}, { maxRetries: 0 });
          if (data.started) {
            if (typeof showGlobalJob === 'function') showGlobalJob(data.message || t('Enriching users...'), 'enrichment', { localIndicatorSelector: '#enrichBtn', cancelUrl: data.cancel_url || '/dashboard/admin/users/enrich-gitlab/cancel' });
            _setEnrichBtnProgress();
          } else if (data.reason === 'already_running') {
            if (typeof showGlobalJob === 'function') showGlobalJob(data.message || t('Enriching users...'), 'enrichment', { localIndicatorSelector: '#enrichBtn', cancelUrl: '/dashboard/admin/users/enrich-gitlab/cancel' });
            _setEnrichBtnProgress();
            showToast(data.message || t('Enrichment already in progress'), 'info');
          } else {
            const btn = document.getElementById('enrichBtn');
            if (data.reason === 'not_needed') {
              _resetEnrichBtn();
              (window.flashToast || showToast)?.(data.message || t('No users need enrichment'), 'success', 5000);
            } else {
              if (btn) GP.setButtonError(btn, t('Failed'));
              else _resetEnrichBtn();
              (window.flashToast || showToast)?.(data.message || t('Enrichment could not start'), 'warning', 5000);
            }
          }
        });
      } catch (err) {
        if (err.code !== 'LOCKED') {
          const btn = document.getElementById('enrichBtn');
          const headline = t('Failed to start enrichment');
          const reason = err.message || t('Network error');
          if (btn) {
            const errLabel = err.status ? `${err.status}` : t('Failed');
            GP.setButtonError(btn, errLabel);
            if (btn._tippy) {
              btn._tippy.setContent(reason);
            } else {
              btn.setAttribute('data-tippy-content', reason);
            }
          } else {
            _resetEnrichBtn();
          }
          showToast(headline + ': ' + reason, 'danger');
        }
      }
  }

  /* Both of these are now the shared mechanic, which is idempotent (a second
     call while loading is a no-op) - so the `btn-in-progress` guard that used to
     stand in for that is gone with the class, and so is the stashed original
     innerHTML: setButtonLoading never replaces the button's content, it puts the
     spinner where the leading icon was and keeps the label and the width. */
  function _setEnrichBtnProgress() {
    setButtonLoading(document.getElementById('enrichBtn'), true);
  }

  function _resetEnrichBtn() {
    setButtonLoading(document.getElementById('enrichBtn'), false);
  }

  // Listen for progress updates from the global job bar
  const onJobUpdate = function(e) {
    if (e.detail?.jobType !== 'enrichment' || _enrichDone) return;
    _setEnrichBtnProgress();
    // Refresh table every ~5% progress
    const pct = e.detail.progress || 0;
    if (pct - _lastEnrichPct >= 5) {
      _lastEnrichPct = pct;
      refreshUserTable();
    }
  };

  // Listen for completion from the global job bar
  const onJobComplete = function(e) {
    if (e.detail?.jobType !== 'enrichment' || _enrichDone) return;
    _enrichDone = true;
    _lastEnrichPct = -1;
    const failed = e.detail.status === 'error';
    const btn = document.getElementById('enrichBtn');
    if (btn) {
      /* THE done state, which draws its own check, keeps its own 2s timer and
         restores the resting label itself - instead of two hand-built terminal
         states with their own SVGs and a setTimeout to undo them. A failure is
         reported by the job bar's own toast, so the button just stops loading:
         reporting it twice is what the refresh contract in core rules out. */
      if (failed) GP.setButtonError(btn, t('Failed'));
      else GP.setButtonDone(btn, t('Done'));
    }
    if (!failed) refreshUserTable();
  };

  // enrichForm submit handler is now bound inside _initTableComponents

  // Check if enrichment is already running on page load
  (async function() {
    try {
      const data = await apiCall('/dashboard/admin/users/enrich-gitlab/status');
      const status = String(data.status || '').toLowerCase();
      if (status === 'running') {
        _setEnrichBtnProgress();
        // Only show global job if not already tracked (avoids duplicate SSE)
        if (typeof isGlobalJobRunning === 'function' && !isGlobalJobRunning('enrichment')) {
          if (typeof showGlobalJob === 'function') showGlobalJob(data.message || t('Enriching users...'), 'enrichment', { localIndicatorSelector: '#enrichBtn', cancelUrl: '/dashboard/admin/users/enrich-gitlab/cancel' });
        }
      }
    } catch(e) { console.debug('Enrichment status check:', e); }
  })();

  // Resume button state if enrichment was restored from localStorage
  const onEnrichmentRestored = function() {
    if (!_enrichDone) _setEnrichBtnProgress();
  };

  // Expose functions for data-action delegation
  window.openEditUserModal = openEditUserModal;
  window.updateUser = updateUser;
  window.openUserInfoModal = openUserInfoModal;

  // -- User Info Modal (uses shared UserInfoModal renderer) --
  /* THE button loading state (setButtonLoading) and THE done state
     (GP.setButtonDone), not a hand-built one. This used to stash the button's
     innerHTML, replace it with `<span class="spinner spinner-sm">` - the OTHER
     spinner, a plain ring rather than the app's brand mark - and put the label
     back on a timer. That is the arrangement core/21-buttons.js was rewritten
     to replace: it deforms the button from its resting size, and the restore
     races anything else that touches the button meanwhile. */
  async function _enrichSingleUser(btn) {
    const userId = btn.getAttribute('data-user-id');
    if (!userId) return;
    setButtonLoading(btn, true);
    GP.showToast(t('Updating user from GitLab...'), 'info');
    try {
      const data = await apiCall('/dashboard/admin/users/' + userId + '/enrich', 'POST');
      if (data.ok) {
        GP.setButtonDone(btn, t('Saved'));
        if (data.updated_fields && data.updated_fields.length) {
          GP.showToast(t('User updated: ') + data.updated_fields.join(', '), 'success');
          refreshUserTable();
          // Refresh only the profile that is still open, never reopen a
          // dismissed dialog or replace a person selected in the meantime.
          setTimeout(function() {
            const modal = btn.closest('.modal-backdrop');
            if (!_disposed && btn.isConnected && modal?.classList.contains('active')
                && !modal.classList.contains('closing')) openUserInfoModal(userId);
          }, 1500);
        } else {
          GP.showToast(t('No changes found'), 'info');
        }
      } else {
        /* The toast is the report. Writing the same failure into the button
           as well said it twice, and the 3s timer that undid it raced anything
           that touched the button in between - the shape the refresh contract
           in core/22-content-states.js exists to prevent (report it ONCE). */
        GP.showToast(data.detail || t('Enrichment failed'), 'error');
        setButtonLoading(btn, false);
      }
    } catch (err) {
      GP.showToast(err.message || t('Enrichment failed'), 'error');
      setButtonLoading(btn, false);
    }
  }

  /* Proper error STATE with a retry, instead of a dead-end message - so a
     timeout on slow internet is recoverable without closing and reopening.
     One copy, reached from both the module-missing and the request-failed
     paths. */
  async function _showInfoError(container, message, userId, username, current) {
    // The app's one error state, and a Retry that shows its loading state.
    if (!await GP.swapModalBodyAnimated(container, GP.errorStateHtml(message, t('Retry')), current)) return;
    GP.bindRetry(container, function () {
      return openUserInfoModal(userId, username);
    });
  }

  async function openUserInfoModal(userId, username) {
    if (_disposed || !userId) return;
    const container = document.getElementById('userInfoContent');
    if (!container) return;
    const read = GP.beginUserInfoRead(container.closest('.modal-backdrop'), userId);
    if (!read) return;
    /* Fetch the card renderer first (memoised in core/12-user-info.js). This
       page used to be the only one that loaded it eagerly; it is on demand for
       everyone now. */
    /* Loader first, module second: fetching the card renderer is itself a
       network round trip, and awaiting it before painting left the click with
       no answer at all until it landed. */
    container.innerHTML = GP.renderLoaderHtml('Loading user info...');
    openModal('userInfoModal');
    try {
      const ready = await GP.ensureUserInfoModule();
      if (!read.current()) return;
      if (!ready) {
        await _showInfoError(container, t('Failed to load user info'), userId, username, read.current);
        return;
      }
      const data = await apiCall('/dashboard/admin/users/' + userId + '/info', 'GET', null,
        { key: 'admin:user-info', signal: read.controller.signal, timeoutMs: 12000, maxRetries: 0 });
      if (!read.current()) return;
      if (data.detail) {
        await GP.swapModalBodyAnimated(container, GP.emptyStateHtml(data.detail), read.current);
        return;
      }
      data._userId = userId;
      /* The renderer is guaranteed by the await above, so the "component not
         loaded" dead end is gone - it was an untranslated developer string
         shown to a teacher, with nothing to do about it. */
      if (!await GP.swapModalBodyAnimated(container, window.UserInfoModal.render(data), read.current)) return;
      // Bind enrich button inside the rendered modal
      const enrichBtn = document.getElementById('enrichSingleUserBtn');
      if (enrichBtn) {
        enrichBtn.addEventListener('click', function() {
          _enrichSingleUser(enrichBtn);
        });
      }
    } catch (err) {
      if (!read.current() || err?.superseded) return;
      const errMsg = err.message || t('Failed to load user info');
      await _showInfoError(container, errMsg, userId, username, read.current);
    } finally {
      read.finish();
    }
  }

  /* -- Modal Dirty-State Guards -- */
  if (typeof enableFormDirtyGuard === 'function') {
    enableFormDirtyGuard('editUserModal');
  }
  if (typeof GP !== 'undefined' && GP.initModalSaveGuard) {
    GP.initModalSaveGuard('editUserModal', '#editUserBtn');
  }

  // Auto-refresh user table when enrichment or any user-related job completes
  const onJobCompleteSync = function(e) {
    if ((e.detail?.status === 'done' || e.detail?.status === 'error') && e.detail?.jobType === 'enrichment') {
      refreshUserTable().catch(() => {});
    }
  };

  // Auto-refresh user table when returning to this tab
  const onTabVisible = () => {
    refreshUserTable().catch(() => {});
  };

  const onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-page-config') || target.id === 'gp-page-config')) {
      GP.adminUsersCleanup();
    }
  };

  window.addEventListener('gp:job-update', onJobUpdate);
  window.addEventListener('gp:job-complete', onJobComplete);
  document.addEventListener('enrichment-restored', onEnrichmentRestored);
  window.addEventListener('gp:job-complete', onJobCompleteSync);
  document.addEventListener('gp-tab-visible', onTabVisible);
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.adminUsersCleanup = function() {
    _disposed = true;
    GP.cancelUserInfoRead('userInfoModal');
    document.body.removeEventListener('htmx:afterSwap', onAfterSwap);
    window.removeEventListener('gp:job-update', onJobUpdate);
    window.removeEventListener('gp:job-complete', onJobComplete);
    document.removeEventListener('enrichment-restored', onEnrichmentRestored);
    window.removeEventListener('gp:job-complete', onJobCompleteSync);
    document.removeEventListener('gp-tab-visible', onTabVisible);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);

    delete window.openEditUserModal;
    delete window.updateUser;
    delete window.openUserInfoModal;
  };
  GP.activePageCleanup = GP.adminUsersCleanup;

})();
