  function updateCourseStatus(row, isActive) {
    if (!row) return;
    row.dataset.isActive = isActive ? 'true' : 'false';
    // ...and the Status filter's attribute, so the row it just moved stays
    // under the right filter.
    row.dataset.status = isActive ? 'active' : 'archived';
    const statusCell = row.querySelector('.status-cell');
    if (statusCell) {
      statusCell.innerHTML = courseStatusHtml(isActive);
    }
  }

  function archiveCourse(courseId, courseCode, button) {
    if (!canEdit || typeof courseActions.archive !== 'function') return;
    courseActions.archive(courseId, button, {
      confirmText: `${t('Archive course')} ${courseCode}?`,
      onSuccess: () => {
        const row = button.closest('tr');
        const buttonGroup = button.closest('.gl-row-actions');
        updateCourseStatus(row, false);
        if (window.GP?.motion?.highlight && row) window.GP.motion.highlight(row);
        button.remove();
        if (buttonGroup) {
          insertBeforeSettingsOrAppend(
            buttonGroup,
            renderLifecycleButton('activate', courseId, courseCode)
              + (isAdmin ? renderLifecycleButton('delete', courseId, courseCode) : ''),
          );
        }
      },
    });
  }

  function activateCourse(courseId, courseCode, button) {
    if (!canEdit || typeof courseActions.activate !== 'function') return;
    courseActions.activate(courseId, button, {
      confirmText: `${t('Activate course')} ${courseCode}?`,
      onSuccess: () => {
        const row = button.closest('tr');
        const buttonGroup = button.closest('.gl-row-actions');
        updateCourseStatus(row, true);
        if (window.GP?.motion?.highlight && row) window.GP.motion.highlight(row);
        buttonGroup?.querySelector('.btn-delete-course')?.remove();
        button.remove();
        insertBeforeSettingsOrAppend(
          buttonGroup,
          renderLifecycleButton('archive', courseId, courseCode),
        );
      },
    });
  }

  function deleteCourse(courseId, courseCode, button) {
    if (!isAdmin || typeof courseActions.deletePermanent !== 'function') return;
    courseActions.deletePermanent(courseId, courseCode, button, {
      onSuccess: () => {
        const row = button.closest('tr');
        if (!row) return;
        GP.collapseAndRemove(row);
      },
    });
  }

