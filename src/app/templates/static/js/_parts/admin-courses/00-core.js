/**
 * Admin courses page - teacher editing, search/filter, archive/activate/delete.
 */
  const GP = window.GP || {};
  GP.runPageCleanup();

  // Scoped variables for cleanable listeners and timers across files
  let onDocumentClick = null;
  let onBeforeSwap = null;

  const { t, escapeHtml: esc } = GP;
  const courseActions = GP.courseActions || {};

  const pageConfig = readPageConfig();
  const isAdmin = pageConfig.isAdmin === true;
  const canEdit = pageConfig.canEdit === true || isAdmin;

  const COURSE_LOCK_PROCESSES = 'sync import run_checks';
  const LIFECYCLE_ACTIONS = {
    archive: {
      buttonClass: 'btn-archive-course',
      icon: 'archive',
      label: 'Archive',
      variant: 'warning',
    },
    activate: {
      buttonClass: 'btn-activate-course',
      icon: 'check-circle',
      label: 'Activate',
      variant: 'success',
    },
    delete: {
      buttonClass: 'btn-delete-course',
      icon: 'trash',
      label: 'Delete permanently',
      variant: 'danger',
    },
  };

  function readPageConfig() {
    const element = document.getElementById('gp-page-config');
    if (!element) return {};
    try {
      return JSON.parse(element.textContent || '{}');
    } catch (_) {
      console.warn('[admin-courses] Invalid page config JSON');
      return {};
    }
  }

  function courseLockAttrs(courseId) {
    return (
      ` data-process-lock-when="${COURSE_LOCK_PROCESSES}"`
      + ` data-process-lock-scope="course:${esc(courseId)}"`
    );
  }

  function courseStatusHtml(isActive) {
    const variant = isActive ? 'success' : 'muted';
    const label = isActive ? t('Active') : t('Archived');
    return (
      `<span class="status-indicator status-indicator--${variant}">`
      + '<span class="status-dot status-dot--sm"></span>'
      + `<span class="status-label">${esc(label)}</span>`
      + '</span>'
    );
  }

  function renderLifecycleButton(actionName, courseId, courseCode) {
    const action = LIFECYCLE_ACTIONS[actionName];
    if (!action) return '';
    const label = t(action.label);
    return (
      `<button type="button" class="btn btn-icon-only btn-${action.variant} btn-sm ${action.buttonClass}"`
      + ` data-course-id="${esc(courseId)}"`
      + ` data-course-code="${esc(courseCode)}"`
      + courseLockAttrs(courseId)
      + ` data-tippy-content="${esc(label)}"`
      + ` aria-label="${esc(label)}">`
      + GP.iconSvg(action.icon, 'sm')
      + '</button>'
    );
  }

  function insertBeforeSettingsOrAppend(buttonGroup, html) {
    if (!buttonGroup || !html) return;
    const settingsBtn = buttonGroup.querySelector('a[href*="settings"]');
    if (settingsBtn) {
      settingsBtn.insertAdjacentHTML('beforebegin', html);
    } else {
      buttonGroup.insertAdjacentHTML('beforeend', html);
    }
    refreshDynamicControls(buttonGroup);
  }

  function refreshDynamicControls(scope) {
    if (typeof window.initTooltips === 'function') {
      window.initTooltips();
    }
    GP.refreshProcessActionGuards(scope || document);
  }

