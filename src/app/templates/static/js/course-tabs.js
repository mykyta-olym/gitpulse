/* Keyboard navigation for course tab bars. */
;(function initCourseTabs() {
  'use strict';

  function courseTabFromEvent(event) {
    if (!event.target || typeof event.target.closest !== 'function') return null;
    return event.target.closest('.tabs-nav[role="tablist"] [role="tab"]');
  }

  function nextTabIndex(key, currentIndex, tabCount) {
    if (key === 'ArrowRight' || key === 'ArrowDown') return (currentIndex + 1) % tabCount;
    if (key === 'ArrowLeft' || key === 'ArrowUp') return (currentIndex - 1 + tabCount) % tabCount;
    if (key === 'Home') return 0;
    if (key === 'End') return tabCount - 1;
    return -1;
  }

  document.addEventListener('keydown', function onCourseTabKeydown(event) {
    const current = courseTabFromEvent(event);
    if (!current) return;

    const nav = current.closest('.tabs-nav[role="tablist"]');
    if (!nav) return;

    const tabs = Array.from(nav.querySelectorAll('[role="tab"]'));
    const currentIndex = tabs.indexOf(current);
    if (currentIndex < 0 || tabs.length < 2) return;

    const targetIndex = nextTabIndex(event.key, currentIndex, tabs.length);
    if (targetIndex < 0) return;

    event.preventDefault();
    tabs[currentIndex].setAttribute('tabindex', '-1');
    tabs[targetIndex].setAttribute('tabindex', '0');
    tabs[targetIndex].focus();
  });
})();
