/* Shared member scoring-exclusion controls. */
;(function () {
  'use strict';

  const GP = window.GP;
  const { t, apiCall, withUiLock } = GP;

  let guardTimer = null;

  function scoringIcon(excluded) {
    const name = excluded ? 'user-plus' : 'user-minus';
    return GP.iconSvg(name, 'sm');
  }

  function escapeSelectorValue(value) {
    return CSS.escape(String(value));
  }

  function scoringScopeForButton(btn) {
    const explicit = btn?.dataset?.processLockScope || '';
    if (explicit) return explicit;
    const teamId = btn?.dataset?.teamId || btn?.closest('[data-team-id]')?.dataset?.teamId || '';
    return teamId ? `team:${teamId}` : '';
  }

  function activeScoringProcess(scope) {
    if (typeof GP.activeProcess === 'function') {
      return GP.activeProcess(['sync', 'import', 'run_checks'], scope);
    }
    const checks = [
      { type: 'sync', label: t('Sync') },
      { type: 'import', label: t('Import') },
      { type: 'run_checks', label: t('Run checks') },
    ];
    if (typeof window.isGlobalJobRunning !== 'function') return null;
    return checks.find((item) => window.isGlobalJobRunning(item.type)) || null;
  }

  function titleForExcluded(excluded) {
    return excluded ? t('Include in scoring') : t('Exclude from scoring');
  }

  function setTooltipContent(btn, content) {
    btn.setAttribute('data-tippy-content', content);
    if (btn._tippy && typeof btn._tippy.setContent === 'function') {
      btn._tippy.setContent(content);
      // A live Tippy instance already shows the tooltip; keeping the native
      // title attribute would surface a duplicate browser tooltip on hover.
      btn.removeAttribute('title');
    } else {
      btn.title = content;
    }
  }

  function pulseToggle(btn) {
    if (!btn) return;
    GP.motion.pop(btn.querySelector('svg') || btn);
  }

  function syncToggleButton(btn, excluded) {
    if (!btn) return;
    const title = titleForExcluded(excluded);
    setTooltipContent(btn, title);
    btn.setAttribute('aria-label', title);
    if (btn.dataset.memberToggleBusy !== '1') {
      btn.innerHTML = scoringIcon(excluded);
    }
  }

  function setToggleBusy(btn, busy) {
    if (!btn) return;
    btn.dataset.memberToggleBusy = busy ? '1' : '0';
    btn.disabled = busy;
    btn.classList.toggle('loading', busy);
    if (busy) {
      btn.setAttribute('aria-busy', 'true');
    } else {
      btn.removeAttribute('aria-busy');
      delete btn.dataset.memberToggleBusy;
    }
  }

  function applyMemberFilters() {
    GP.initMemberFilters(document);
  }

  function updateMemberRow(studentId, result) {
    const row = document.querySelector(
      `tr[data-student-id="${escapeSelectorValue(studentId)}"]`,
    );
    if (!row) return;

    const excluded = result?.excluded_from_scoring === true;
    const baseCategory =
      String(result?.member_base_category || row.dataset.memberBaseCategory || 'direct');
    const category = excluded
      ? 'excluded'
      : String(result?.member_category || baseCategory || 'direct');

    row.dataset.memberBaseCategory = baseCategory;
    row.dataset.memberCategory = category;
    row.classList.toggle('member-excluded', excluded);
    if (excluded) {
      row.setAttribute('data-member-excluded', '1');
    } else {
      row.removeAttribute('data-member-excluded');
    }

    const btn = row.querySelector('.btn-toggle-exclusion');
    syncToggleButton(btn, excluded);
    pulseToggle(btn);
    applyMemberFilters();
  }

  function setButtonsLocked(processInfo) {
    document.querySelectorAll('.btn-toggle-exclusion').forEach((btn) => {
      if (!(btn instanceof HTMLButtonElement)) return;
      if (btn.dataset.memberToggleBusy === '1') return;
      const scopedProcessInfo = processInfo || activeScoringProcess(scoringScopeForButton(btn));
      const locked = !!scopedProcessInfo;
      const reason = locked
        ? t('Wait for the active sync/import/check run to finish before changing scoring membership.')
        : '';

      if (locked) {
        btn.disabled = true;
        btn.classList.add('is-disabled');
        btn.dataset.processLocked = '1';
        btn.setAttribute('aria-disabled', 'true');
        setTooltipContent(btn, reason);
        return;
      }

      if (btn.dataset.processLocked === '1') {
        btn.disabled = false;
        btn.classList.remove('is-disabled');
        btn.removeAttribute('aria-disabled');
        delete btn.dataset.processLocked;
        const row = btn.closest('tr[data-student-id]');
        syncToggleButton(btn, row?.hasAttribute('data-member-excluded'));
      }
    });
  }

  function refreshMemberExclusionGuards() {
    setButtonsLocked(null);
    return null;
  }

  function initMemberExclusionGuards() {
    refreshMemberExclusionGuards();
    if (guardTimer !== null) return;
    guardTimer = window.setInterval(refreshMemberExclusionGuards, 1500);
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      if (guardTimer !== null) {
        window.clearInterval(guardTimer);
        guardTimer = null;
      }
    } else if (document.visibilityState === 'visible') {
      initMemberExclusionGuards();
    }
  });

  async function toggleMemberExclusion(options) {
    const studentId = String(options?.studentId || '');
    const teamId = String(options?.teamId || '');
    if (!studentId || !teamId || typeof apiCall !== 'function') return;

    const row = document.querySelector(
      `tr[data-student-id="${escapeSelectorValue(studentId)}"]`,
    );
    const btn = row?.querySelector('.btn-toggle-exclusion');
    const scope = options?.scope || scoringScopeForButton(btn) || `team:${teamId}`;
    const processInfo = activeScoringProcess(scope);
    refreshMemberExclusionGuards();
    if (processInfo) {
      GP.showToast?.(
        t('Wait for the active sync/import/check run to finish before changing scoring membership.'),
        'warning',
      );
      return;
    }

    try {
      await withUiLock(`toggleExclusion:${teamId}:${studentId}`, async () => {
        try {
          setToggleBusy(btn, true);
          const result = await apiCall(
            `/dashboard/teams/${encodeURIComponent(teamId)}/members/${encodeURIComponent(studentId)}/toggle-exclusion`,
            'POST',
            null,
            { maxRetries: 0, timeoutMs: 60000 },
          );

          updateMemberRow(studentId, result);
          GP.flashToast?.(
            result?.excluded_from_scoring
              ? t('Student excluded from scoring')
              : t('Student included in scoring'),
            'success',
          );
          if (typeof options?.onRefresh === 'function') {
            await Promise.resolve(options.onRefresh()).catch(() => {});
          }
        } catch (err) {
          GP.showToast?.(
            err?.message || t('Failed to toggle exclusion'),
            err?.status === 409 ? 'warning' : 'danger',
          );
        } finally {
          setToggleBusy(btn, false);
          const currentExcluded = row?.hasAttribute('data-member-excluded') || false;
          syncToggleButton(btn, currentExcluded);
          refreshMemberExclusionGuards();
        }
      });
    } catch (err) {
      if (err?.code !== 'LOCKED') {
        GP.showToast?.(err?.message || t('Failed to toggle exclusion'), 'danger');
      }
    }
  }

  GP.toggleMemberExclusion = toggleMemberExclusion;
  GP.initMemberExclusionGuards = initMemberExclusionGuards;
  GP.refreshMemberExclusionGuards = refreshMemberExclusionGuards;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMemberExclusionGuards);
  } else {
    initMemberExclusionGuards();
  }
})();
