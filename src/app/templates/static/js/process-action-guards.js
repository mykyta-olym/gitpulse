/* Shared guards for UI actions that conflict with long-running jobs. */
;(function () {
  'use strict';

  const GP = window.GP || (window.GP = {});
  const { t } = GP;

  const PROCESS_LABELS = {
    sync: 'sync',
    import: 'import',
    run_checks: 'check run',
  };

  let guardTimer = null;
  let lastLockedCount = 0;

  /* ============================================
     Anti-spam cooldown system
     ============================================
     Instead of permanently disabling buttons after errors, apply a
     timed cooldown (e.g. 5 s) with a visible countdown, then
     automatically re-enable. This prevents users from spamming
     failing endpoints while never leaving the button stuck.
  */
  const COOLDOWN_MS = 5000;
  const COOLDOWN_TICK_MS = 200;
  /** @type {Map<HTMLElement, {timer: number, endTime: number, tickTimer: number}>} */
  const _cooldowns = new Map();

  function _applyCooldown(el) {
    if (!el) return;
    _clearCooldown(el);

    // Take exclusive ownership of the button away from setButtonLoading():
    // cancel any pending min-visible-duration reset timer and drop the loading
    // chrome. Without this, a reset scheduled BEFORE the cooldown (fast <400ms
    // failures  -  e.g. a 401 token rejection) fires mid-countdown, deletes the
    // saved label, and the button freezes on "Wait 1s" (the reported bug).
    // ONE teardown for the loading chrome (timers, class, aria-busy, spinner) -
    // core/21-buttons.js owns it, because the min-duration reset, the done
    // state and this cooldown all need exactly the same thing and used to carry
    // three copies of it.
    if (typeof GP !== 'undefined' && GP.clearButtonLoadingChrome) {
      GP.clearButtonLoadingChrome(el);
    }
    // The toast that announced the failure hands the button its red "Failed"
    // outcome BEFORE the handler gets round to this cooldown. Retire it first:
    // otherwise the outcome markup is what gets snapshotted below and restored
    // when the countdown ends, and the button rested on "Failed" (text inside
    // an icon-only control, the tick icon gone) with nothing left to undo it.
    if (typeof GP !== 'undefined' && GP.clearButtonOutcome) {
      GP.clearButtonOutcome(el);
    }

    const endTime = Date.now() + COOLDOWN_MS;
    el.disabled = true;
    el.classList.add('is-disabled', 'is-cooldown');
    el.setAttribute('aria-disabled', 'true');

    // Capture the REAL label into a cooldown-owned slot that setButtonLoading()
    // never touches, so the countdown can always restore it. The loading chrome
    // was torn down above, so innerHTML IS that label.
    const savedLabel = el.innerHTML;
    el.dataset.cooldownLabel = savedLabel;
    el.dataset.cooldownActive = '1';
    // The countdown borrows aria-label and the tooltip for "Wait Ns"; keep the
    // button's own so they come back with the label. An icon-only Sync used to
    // lose its accessible name and its tooltip for good after one failure.
    const ownAria = el.getAttribute('aria-label');
    if (ownAria != null) el.dataset.cooldownAria = ownAria;
    const ownTip = el.getAttribute('data-tippy-content');
    if (ownTip != null) el.dataset.cooldownTip = ownTip;

    // Render countdown ticks. Self-heals: when the time is up the tick itself
    // clears the cooldown, so the button can NEVER hang on "Wait 1s" if the
    // setTimeout below is lost/throttled (background tab, a swallowed timer, or
    // a re-render racing the timeout). The 200ms tick is the reliable clock; the
    // setTimeout is just a backstop.
    // Does the real label carry visible text? Stuffing "Wait 12s" into an
    // icon-only (or very narrow) control overflowed it and clipped against the
    // neighbouring cell. Those controls now show a clock icon instead and carry
    // the remaining time in the tooltip + aria-label, so the state stays
    // discoverable without truncating anything.
    const _probe = document.createElement('div');
    _probe.innerHTML = savedLabel || '';
    const _labelHasText = (_probe.textContent || '').trim().length > 0;
    // Freeze the pre-cooldown width so the countdown never reflows the row.
    const _preWidth = el.offsetWidth;
    if (_preWidth) {
      el.style.minWidth = _preWidth + 'px';
    }

    const _renderCooldownTick = () => {
      const remaining = Math.max(0, Math.ceil((endTime - Date.now()) / 1000));
      if (remaining > 0) {
        const label = t('Wait') + ' ' + remaining + 's';
        let content = label;
        if (!_labelHasText) {
          const ico = (window.GP && GP.icons && GP.icons.get) ? GP.icons.get('clock', 16) : '';
          content = ico || label; // never leave the button empty
        }
        el.innerHTML = content;
        el.setAttribute('aria-label', label);
        el.dataset.tippyContent = label;
        if (el._tippy && typeof el._tippy.setContent === 'function') el._tippy.setContent(label);
      } else {
        _clearCooldown(el);
      }
    };
    _renderCooldownTick();
    const tickTimer = setInterval(_renderCooldownTick, COOLDOWN_TICK_MS);

    const timer = setTimeout(() => {
      _clearCooldown(el);
    }, COOLDOWN_MS);

    _cooldowns.set(el, { timer, endTime, tickTimer });
  }

  function _clearCooldown(el) {
    if (!el) return;
    const cd = _cooldowns.get(el);
    if (cd) {
      clearTimeout(cd.timer);
      clearInterval(cd.tickTimer);
      _cooldowns.delete(el);
    }
    if (el.dataset.cooldownActive !== '1') return;
    delete el.dataset.cooldownActive;
    el.classList.remove('is-cooldown');

    // Restore original button content. Prefer the cooldown-owned label slot
    // (never clobbered by setButtonLoading) so the countdown ALWAYS restores
    // the real label and can never hang on "Wait 1s".
    const label = el.dataset.cooldownLabel;
    if (label != null) {
      el.innerHTML = label;
    }
    // Undo the countdown-only presentation (frozen width, countdown tooltip and
    // aria-label) so the button returns to exactly its pre-cooldown state.
    el.style.minWidth = '';
    if (el.dataset.cooldownAria != null) {
      el.setAttribute('aria-label', el.dataset.cooldownAria);
      delete el.dataset.cooldownAria;
    } else {
      el.removeAttribute('aria-label');
    }
    if (el.dataset.cooldownTip != null) {
      el.dataset.tippyContent = el.dataset.cooldownTip;
      if (el._tippy && typeof el._tippy.setContent === 'function') el._tippy.setContent(el.dataset.cooldownTip);
      delete el.dataset.cooldownTip;
    } else {
      delete el.dataset.tippyContent;
      if (el._tippy && typeof el._tippy.setContent === 'function') el._tippy.setContent('');
    }
    delete el.dataset.cooldownLabel;
    if (typeof GP !== 'undefined' && GP.clearButtonLoadingChrome) {
      GP.clearButtonLoadingChrome(el);
    }
    GP.refreshButtonDisabledState(el);
  }

  function tokenList(value) {
    if (Array.isArray(value)) {
      return value.map(String).map((item) => item.trim()).filter(Boolean);
    }
    return String(value || '')
      .split(/[\s,]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function isJobActive(job) {
    return Boolean(job && job.status !== 'done' && job.status !== 'error');
  }

  function isCourseSyncJob(jobType, job) {
    return (
      job?.meta?.jobKind === 'course_sync'
      || /^[0-9a-f-]{36}$/i.test(String(jobType || ''))
      || /^\d+$/.test(String(jobType || ''))
    );
  }

  // Parse "course:42 team:abc" -> [{kind:'course', id:'42'}, {kind:'team', id:'abc'}]
  function parseScope(scope) {
    if (!scope) return [];
    const tokens = Array.isArray(scope) ? scope : tokenList(scope);
    const out = [];
    for (const tok of tokens) {
      const idx = tok.indexOf(':');
      if (idx <= 0) continue;
      const kind = tok.slice(0, idx).trim().toLowerCase();
      const id = tok.slice(idx + 1).trim();
      if (!kind || !id) continue;
      if (kind === 'course' || kind === 'team' || kind === 'project') {
        out.push({ kind, id });
      }
    }
    return out;
  }

  function scopeMap(scopeTokens) {
    return scopeTokens.reduce((acc, tok) => {
      acc[tok.kind] = tok.id;
      return acc;
    }, {});
  }

  function firstString() {
    for (const value of arguments) {
      if (value !== undefined && value !== null && String(value).trim() !== '') {
        return String(value);
      }
    }
    return '';
  }

  function scopeFromJobKey(jobType) {
    const parts = String(jobType || '').split(':').map((part) => part.trim()).filter(Boolean);
    if (parts.length < 3) return {};
    const kind = parts[1];
    const id = parts.slice(2).join(':');
    if (!id) return {};
    if (kind === 'course') return { level: 'course', courseId: id };
    if (kind === 'team') return { level: 'team', teamId: id };
    if (kind === 'project') return { level: 'project', projectId: id };
    return {};
  }

  function jobScopeInfo(jobType, job) {
    const key = String(jobType || '');
    const meta = job?.meta || {};
    const keyed = scopeFromJobKey(key);
    const courseId = firstString(meta.courseId, meta.scopeCourseId, meta.targetCourseId, keyed.courseId);
    const teamId = firstString(meta.teamId, meta.scopeTeamId, keyed.teamId);
    const projectId = firstString(meta.projectId, meta.scopeProjectId, keyed.projectId);

    if (meta.jobKind === 'course_sync' || isCourseSyncJob(key, job)) {
      return { level: 'course', courseId: courseId || key, teamId, projectId };
    }
    if (projectId) {
      return { level: 'project', courseId, teamId, projectId };
    }
    if (teamId) {
      return { level: 'team', courseId, teamId, projectId };
    }
    if (courseId) {
      return { level: 'course', courseId, teamId, projectId };
    }
    return { level: 'global', courseId, teamId, projectId };
  }

  function sameId(left, right) {
    return left && right && String(left) === String(right);
  }

  // Does an active job in _globalJobs conflict with the target scope?
  // A team-level job in course A must not block team B in the same course;
  // only a course-wide job blocks every team in that course.
  function jobMatchesScope(jobType, job, scopeTokens) {
    if (!scopeTokens.length) return false;
    const target = scopeMap(scopeTokens);
    const active = jobScopeInfo(jobType, job);

    if (active.level === 'global') {
      return true;
    }

    if (active.level === 'course') {
      return sameId(active.courseId, target.course);
    }

    if (active.level === 'team') {
      if (target.team) return sameId(active.teamId, target.team);
      return sameId(active.courseId, target.course);
    }

    if (active.level === 'project') {
      if (target.project) return sameId(active.projectId, target.project) || sameId(active.teamId, target.team);
      if (target.team) return sameId(active.teamId, target.team);
      return sameId(active.courseId, target.course);
    }

    return false;
  }

  // Map UI process type -> set of _globalJobs keys / job-kind predicates.
  // Returns true if any active job of this type matches the given scope.
  function isProcessRunning(processType, scope) {
    const type = String(processType || '');
    if (!type) return false;
    const scopeTokens = parseScope(scope);
    const jobs = window._globalJobs || {};

    if (scopeTokens.length) {
      // Scope-restricted check: only an active job within the scope counts.
      for (const [jobType, job] of Object.entries(jobs)) {
        if (!isJobActive(job)) continue;
        if (!jobMatchesScope(jobType, job, scopeTokens)) continue;
        if (matchesType(jobType, job, type)) return true;
      }
      return false;
    }

    // Unscoped (legacy global) check - used by dashboard Import etc.
    if (type === 'sync') {
      if (typeof window.isGlobalJobRunning === 'function' && window.isGlobalJobRunning('sync')) {
        return true;
      }
      return Object.entries(jobs).some(([jobType, job]) => isJobActive(job) && matchesType(jobType, job, type));
    }
    if (typeof window.isGlobalJobRunning === 'function') {
      return window.isGlobalJobRunning(type);
    }
    return isJobActive(jobs[type]);
  }

  // Classify whether (jobType, job) represents a given UI process type.
  function matchesType(jobType, job, type) {
    const key = String(jobType || '');
    if (type === 'sync') {
      if (key === 'sync') return true;
      if (key.startsWith('sync:')) return true;
      if (isCourseSyncJob(key, job)) return true;
      if (job?.meta?.jobKind === 'project_sync' || job?.meta?.jobKind === 'team_sync') return true;
      return false;
    }
    if (type === 'run_checks') {
      if (key === 'run_checks') return true;
      if (key.startsWith('run_checks:')) return true;
      if (job?.meta?.jobKind === 'run_checks') return true;
      return false;
    }
    if (type === 'import') {
      if (key === 'import') return true;
      if (key.startsWith('import:')) return true;
      if (job?.meta?.jobKind === 'import') return true;
      return false;
    }
    return key === type;
  }

  function activeProcess(processes, scope) {
    const items = tokenList(processes);
    for (const type of items) {
      if (isProcessRunning(type, scope)) {
        return { type, label: t(PROCESS_LABELS[type] || type.replaceAll('_', ' ')) };
      }
    }
    return null;
  }

  function conflictMessage(processInfo, customMessage) {
    if (customMessage) return t(customMessage);
    if (!processInfo) {
      return t('Wait for the active process to finish before starting another action.');
    }
    return t('Wait for the active %process to finish before starting another action.')
      .replace('%process', processInfo.label);
  }

  function isPassiveUiControl(el) {
    if (!el || typeof el.closest !== 'function') return false;
    const passive = el.closest([
      '.check-filter-btn',
      '.tab-btn',
      '[role="tab"]',
      '[data-filter]',
      '[data-no-process-lock]',
    ].join(','));
    if (!passive) return false;
    // A passive child can still live inside a real destructive/action button.
    // In that case the explicit action wins and the guard must still apply.
    return !passive.closest([
      '[data-action]',
      '[data-modal-open]',
      '[data-sync-trigger]',
      '[data-process-write]',
    ].join(','));
  }

  function setTooltipContent(el, content) {
    if (!el) return;
    if (content) {
      el.title = content;
      el.setAttribute('data-tippy-content', content);
      if (el._tippy && typeof el._tippy.setContent === 'function') {
        el._tippy.setContent(content);
      }
      return;
    }

    el.removeAttribute('title');
    el.removeAttribute('data-tippy-content');
    if (el._tippy && typeof el._tippy.setContent === 'function') {
      el._tippy.setContent('');
    }
  }

  // Disabled form controls do not emit pointer events, so Tippy can never show
  // the "why is this disabled" reason on them. Wrap the control in an inline
  // span that DOES receive the hover and host the tooltip there. The wrapper
  // is removed again when the control is unlocked.
  function showDisabledReason(el, content) {
    /* A hidden input is never seen or hovered, so there is nothing to explain
       on it - and a wrapper around it is a VISIBLE box: in a grid row it took a
       column of its own. The archived course's Academic period field (a select
       plus two hidden inputs) shrank to a third of its row that way. */
    if (!el || (el.tagName === 'INPUT' && el.type === 'hidden')) return;
    if (typeof window.tippy !== 'function') {
      // No Tippy available - fall back to a native title so the reason is
      // still discoverable on hover.
      el.title = content;
      return;
    }
    // Destroy any tooltip the control owned while enabled - it can't fire now.
    if (el._tippy && typeof el._tippy.destroy === 'function') {
      el._tippy.destroy();
    }
    el.removeAttribute('title');
    let wrap = el.parentElement;
    if (!wrap || !wrap.classList.contains('gl-tip-wrap')) {
      wrap = document.createElement('span');
      wrap.className = 'gl-tip-wrap';
      // A bare inline <span> wrapper shrink-wraps to its content width, which
      // collapses a block, full-width control to its text width: a btn-block
      // button ended up narrower than its unlocked siblings, and on an archived
      // course EVERY input/textarea/select in the settings form shrank to a tiny
      // box (the reported deformation - a 890px Description textarea rendered at
      // 181px). Form controls and block buttons are laid out full-width by their
      // container, so the wrapper has to be block too or it changes their size.
      const tag = el.tagName;
      const inlineInput = tag === 'INPUT' && /^(checkbox|radio|button|submit|reset)$/.test(el.type);
      const isBlockControl =
        el.classList.contains('btn-block') ||
        tag === 'TEXTAREA' || tag === 'SELECT' ||
        (tag === 'INPUT' && !inlineInput);
      if (isBlockControl) {
        wrap.style.display = 'block';
        wrap.style.width = '100%';
      }
      el.parentNode.insertBefore(wrap, el);
      wrap.appendChild(el);
    }
    // The reason rides on the wrapper for the click below: the tooltip is
    // hover-only (`touch: false`), so on a phone a tap is the only way to ask.
    wrap.dataset.disabledReason = content;
    if (wrap._tippy && typeof wrap._tippy.setContent === 'function') {
      wrap._tippy.setContent(content);
    } else {
      window.tippy(wrap, {
        content,
        placement: el.dataset.tippyPlacement || 'top',
        duration: [180, 120],
        touch: false,
      });
    }
  }

  /* A click on a disabled control answers with its reason, as a toast. The
     control itself is `pointer-events: none` inside its .gl-tip-wrap, so the
     wrapper is what receives the click - on a phone, where the hover tooltip
     never shows, this is the only explanation the reader gets. */
  function explainDisabledClick(event) {
    const wrap = event.target?.closest?.('.gl-tip-wrap');
    if (!wrap) return;
    // Set here for a control disabled at runtime; the template's own
    // `disabled_reason` (components/buttons.html) rides on the tooltip attribute.
    const reason = wrap.dataset.disabledReason || wrap.getAttribute('data-tippy-content');
    const control = wrap.firstElementChild;
    if (!reason || !control || !(control.disabled || control.getAttribute('aria-disabled') === 'true')) return;
    event.preventDefault();
    GP.showToast?.(reason, 'warning');
  }

  function clearDisabledReason(el) {
    const wrap = el.parentElement;
    if (wrap && wrap.classList.contains('gl-tip-wrap')) {
      const parent = wrap.parentNode;
      if (wrap._tippy && typeof wrap._tippy.destroy === 'function') {
        wrap._tippy.destroy();
      }
      parent.insertBefore(el, wrap);
      wrap.remove();
      if (parent) {
        GP.initTippy(parent);
      }
    }
  }

  /* `data-disabled-reason` is how a control says why it may be disabled. While
     it IS disabled it sits in the .gl-tip-wrap above - the reason on hover, and
     on a tap (a phone has no hover) as a toast; enabled again, it is unwrapped.
     Whatever disables the control - a template, the paginator, a selection
     handler - only toggles `disabled`. A process lock's own reason wins while
     the lock holds. */
  function syncDisabledReason(el) {
    if (el.dataset.processLocked === '1') return;
    const off = el.disabled || el.getAttribute('aria-disabled') === 'true';
    const wrapped = el.parentElement?.classList.contains('gl-tip-wrap');
    if (off) showDisabledReason(el, el.dataset.disabledReason);
    else if (wrapped) clearDisabledReason(el);
  }

  function syncDisabledReasons(root) {
    if (root.matches?.('[data-disabled-reason]')) syncDisabledReason(root);
    root.querySelectorAll?.('[data-disabled-reason]').forEach(syncDisabledReason);
  }

  new MutationObserver((records) => {
    for (const record of records) {
      if (record.type === 'attributes') {
        if (record.target.dataset?.disabledReason) syncDisabledReason(record.target);
      } else {
        record.addedNodes.forEach((node) => {
          if (node.nodeType === 1) syncDisabledReasons(node);
        });
      }
    }
  }).observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ['disabled', 'aria-disabled', 'data-disabled-reason'],
  });

  function lockElement(el, processInfo) {
    if (!el || el.dataset.processLockActive === '1') return;
    el.dataset.processLockActive = '1';
    const temporarilyLocked = el._loadingArmed || el.classList.contains('loading')
      || ['syncLocked', 'cooldownActive'].some(key => el.dataset[key] === '1');
    el.dataset.processLockWasDisabled = el.disabled && !temporarilyLocked ? '1' : '0';
    el.dataset.processLockOriginalTooltip = el.getAttribute('data-tippy-content') || '';
    el.dataset.processLockOriginalTitle = el.getAttribute('title') || '';
    el.dataset.processLocked = '1';
    el.disabled = true;
    el.classList.add('is-disabled');
    el.setAttribute('aria-disabled', 'true');
    showDisabledReason(el, conflictMessage(processInfo, el.dataset.processLockMessage));
  }

  function unlockElement(el) {
    if (!el || el.dataset.processLockActive !== '1') return;
    const wasDisabled = el.dataset.processLockWasDisabled === '1';
    const originalTooltip = el.dataset.processLockOriginalTooltip || '';
    const originalTitle = el.dataset.processLockOriginalTitle || '';

    // Remove the disabled-reason wrapper before restoring the control state.
    clearDisabledReason(el);

    delete el.dataset.processLockActive;
    delete el.dataset.processLockWasDisabled;
    delete el.dataset.processLockOriginalTooltip;
    delete el.dataset.processLockOriginalTitle;
    delete el.dataset.processLocked;

    if (originalTooltip) {
      setTooltipContent(el, originalTooltip);
      // Enabled controls use the shared delegated tooltip, including its
      // scroll handling and keyboard-focus rules.
    } else if (originalTitle) {
      el.title = originalTitle;
      el.removeAttribute('data-tippy-content');
    } else {
      setTooltipContent(el, '');
    }
    GP.refreshButtonDisabledState(el, wasDisabled);
  }

  function refreshProcessActionGuards(scope) {
    const root = scope?.querySelectorAll ? scope : document;
    let lockedCount = 0;
    const candidates = Array.from(root.querySelectorAll('[data-process-lock-when]'));
    if (root.matches?.('[data-process-lock-when]')) {
      candidates.unshift(root);
    }
    candidates.forEach((el) => {
      if (!(el instanceof HTMLButtonElement) && !(el instanceof HTMLInputElement)) return;
      if (el.dataset.processBusy === '1') return;
      const elScope = el.dataset.processLockScope || '';
      const processInfo = activeProcess(el.dataset.processLockWhen, elScope);
      if (processInfo) {
        lockedCount += 1;
        lockElement(el, processInfo);
      } else {
        unlockElement(el);
      }
    });

    if (lastLockedCount > 0 && lockedCount === 0) {
      document.querySelectorAll('.rcm').forEach((rootEl) => {
        try { GP.runChecksModal?.refresh?.(rootEl); } catch (_) { /* noop */ }
      });
    }
    lastLockedCount = lockedCount;
    return lockedCount;
  }

  function guardProcessAction(processes, options) {
    const opts = typeof options === 'string' ? { message: options } : (options || {});
    /* `_globalJobs` is empty until /sync/active answers for the first time, and
       an empty object reads exactly like "nothing is running" - so for the first
       second of every page load this guard let through the very actions it
       exists to block. Not knowing is not the same as knowing there is nothing.
       `_globalJobsReady` is set by the job bar on the first answer OR the first
       failure, so an unreachable endpoint cannot block the page for good. */
    if (window._globalJobsReady === false) {
      if (opts.toast !== false) {
        GP.showToast?.(t('Checking for running processes - try again in a moment.'), 'warning');
      }
      return false;
    }
    const processInfo = activeProcess(processes, opts.scope);
    if (!processInfo) return true;
    const message = conflictMessage(processInfo, opts.message);
    if (opts.toast !== false) {
      GP.showToast?.(message, 'warning');
    }
    refreshProcessActionGuards();
    return false;
  }

  /**
   * Apply anti-spam cooldown to a button after a failed action.
   * Shows a countdown timer and auto-re-enables after COOLDOWN_MS.
   * Exposed as GP.applyCooldown(el) for use from page-level error handlers.
   */
  function applyCooldown(el) {
    _applyCooldown(el);
  }

  function interceptModalClick(event) {
    if (isPassiveUiControl(event.target)) return;
    const trigger = event.target?.closest?.('[data-modal-open]');
    if (!trigger) return;
    const lockWhen = trigger.dataset.processLockWhen;
    if (!lockWhen) return;
    const triggerScope = trigger.dataset.processLockScope || '';
    if (guardProcessAction(lockWhen, { message: trigger.dataset.processLockMessage, scope: triggerScope })) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation?.();
  }

  function interceptLockedActionClick(event) {
    if (isPassiveUiControl(event.target)) return;
    const trigger = event.target?.closest?.('[data-process-lock-when]');
    if (!trigger || trigger.dataset.modalOpen) return;
    if (trigger.disabled || trigger.dataset.processBusy === '1') return;
    const lockWhen = trigger.dataset.processLockWhen;
    if (!lockWhen) return;
    const triggerScope = trigger.dataset.processLockScope || '';
    if (guardProcessAction(lockWhen, { message: trigger.dataset.processLockMessage, scope: triggerScope })) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation?.();
  }

  function initProcessActionGuards() {
    syncDisabledReasons(document.body);
    refreshProcessActionGuards();
    if (guardTimer === null) {
      guardTimer = window.setInterval(refreshProcessActionGuards, 1500);
    }
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      if (guardTimer !== null) {
        window.clearInterval(guardTimer);
        guardTimer = null;
      }
    } else if (document.visibilityState === 'visible') {
      initProcessActionGuards();
    }
  });

  function scheduleGuardRefresh() {
    if (document.hidden) return;
    setTimeout(refreshProcessActionGuards, 0);
  }

  document.addEventListener('click', interceptModalClick, true);
  document.addEventListener('click', interceptLockedActionClick, true);
  document.addEventListener('click', explainDisabledClick);
  document.addEventListener('htmx:afterSwap', (event) => {
    // Clear all active cooldown timers on page navigation/swap to prevent leaks
    for (const [el] of _cooldowns.entries()) {
      _clearCooldown(el);
    }
    refreshProcessActionGuards(event.target);
  });
  window.addEventListener('gp:job-update', scheduleGuardRefresh);
  window.addEventListener('gp:job-complete', scheduleGuardRefresh);
  window.addEventListener('storage', (event) => {
    if (event.key === 'gitpulse_global_job') {
      scheduleGuardRefresh();
    }
  });

  GP.isProcessRunning = isProcessRunning;
  GP.isPassiveUiControl = isPassiveUiControl;
  GP.activeProcess = activeProcess;
  GP.guardProcessAction = guardProcessAction;
  GP.refreshProcessActionGuards = refreshProcessActionGuards;
  GP.initProcessActionGuards = initProcessActionGuards;
  GP.applyCooldown = applyCooldown;
  GP.clearCooldown = _clearCooldown;
  // Exposed so page-level code that disables its own controls (e.g. the
  // course-settings sync lock) can show a "why is this disabled" tooltip that
  // actually fires on the disabled control.
  GP.setDisabledReason = showDisabledReason;
  GP.clearDisabledReason = clearDisabledReason;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProcessActionGuards);
  } else {
    initProcessActionGuards();
  }
})();
