  function handleTeacherExpand(button) {
    const overflow = button.parentElement?.querySelector('.teacher-overflow');
    if (!overflow) return;
    overflow.classList.toggle('d-none');
    const isExpanded = !overflow.classList.contains('d-none');
    const label = isExpanded
      ? (button.dataset.labelLess || '')
      : (button.dataset.labelMore || '');
    button.setAttribute('aria-pressed', String(isExpanded));
    button.setAttribute('aria-label', label);
    button.setAttribute('data-tippy-content', label);
    button.innerHTML = GP.iconSvg(isExpanded ? 'chevron-up' : 'chevron-down', 'sm');
    button._tippy?.setContent(label);
  }

  function handleCourseActionClick(event, buttonClass, callback) {
    const target = event.target instanceof Element ? event.target : null;
    const button = target?.closest(`.${buttonClass}`);
    if (!button) return false;
    event.preventDefault();
    callback(button.dataset.courseId, button.dataset.courseCode, button);
    return true;
  }

  onDocumentClick = (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const expandButton = target?.closest('[data-expand-toggle]');
    if (expandButton) {
      event.preventDefault();
      handleTeacherExpand(expandButton);
      return;
    }
    if (handleCourseActionClick(event, 'btn-archive-course', archiveCourse)) return;
    if (handleCourseActionClick(event, 'btn-activate-course', activateCourse)) return;
    handleCourseActionClick(event, 'btn-delete-course', deleteCourse);
  };
  document.addEventListener('click', onDocumentClick);

  GP.autoReloadOnJob?.(['sync*', 'import']);

  onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-page-config') || target.id === 'gp-page-config')) {
      GP.adminCoursesCleanup();
    }
  };
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.adminCoursesCleanup = () => {
    document.removeEventListener('click', onDocumentClick);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };
  GP.activePageCleanup = GP.adminCoursesCleanup;
