  const GP = window.GP || {};
  const { escapeHtml: _escHtml, showToast, flashToast, withUiLock: _lock } = GP;
  const { t } = GP;

  // Cleanup prior page context if it exists to avoid leak/races
  GP.runPageCleanup();

  const _pageConfig = JSON.parse(document.getElementById('gp-dashboard-config')?.textContent || '{}');
  const _canEdit = _pageConfig.canEdit === true;
  const _isAdmin = _pageConfig.isAdmin === true;
  const _DESC_MAX_LEN = 120;

  // Variables for cleanup
  let onVisibilityChangeGreeting = null;
  let onKeydownShortcuts = null;

  // Initialize import modal lifecycle (from import_helpers.html)
  if (typeof initImportModals === 'function') {
    initImportModals();
  }

  // -- Time-of-day greeting word --
  (function _initGreeting() {
    const h1 = document.querySelector('.gl-home-title[data-greeting]');
    const wordEl = h1 && h1.querySelector('[data-greeting-word]');
    if (!wordEl) return;
    function _pickGreeting() {
      const hr = new Date().getHours();
      let key = 'evening';
      if (hr >= 5 && hr < 12) key = 'morning';
      else if (hr >= 12 && hr < 18) key = 'afternoon';
      const word = h1.getAttribute('data-greeting-' + key);
      if (word && wordEl.textContent !== word) wordEl.textContent = word;
    }
    _pickGreeting();
    onVisibilityChangeGreeting = function () {
      if (document.visibilityState === 'visible') _pickGreeting();
    };
    document.addEventListener('visibilitychange', onVisibilityChangeGreeting);
  })();

  // -- Disabled quick-link toast --
  document.querySelectorAll('.gl-quicklink-disabled').forEach(function (el) {
    el.addEventListener('click', function (e) {
      e.preventDefault();
      const msg = el.getAttribute('data-toast-msg') || GP.t('You are not enrolled in any courses yet.');
      if (typeof showToast === 'function') { showToast(msg, 'warning'); }
    });
  });

  // -- URL filter/hash handling --
  function _handleDashboardNavigation() {
    const params = new URLSearchParams(window.location.search);
    const filter = params.get('filter');
    const hash = window.location.hash.replace('#', '');

    const cfg = _pageConfig;

    // Role-appropriate "no courses" message
    function _noCourseMsg() {
      return cfg.isStudent
        ? GP.t('You are not enrolled in any courses yet. Your teacher will add you soon.')
        : GP.t('You have no active courses yet. Create or import one to get started.');
    }

    // If user has no courses and tries to use a filter, show toast but still scroll
    if (filter && !cfg.hasCourses) {
      if (typeof showToast === 'function') {
        showToast(_noCourseMsg(), 'warning');
      }
    }

    // Map filter values to scroll-to targets and highlight actions
    const filterTargets = {
      'flagged': { panelSelector: '.attention-panel, .gl-home-card', highlight: true },
      'deadlines': { panelSelector: '.attention-panel, .gl-home-card', highlight: true },
      'teams': { sectionId: 'my-courses', highlight: true },
      'compliance': { panelSelector: '.gl-student-progress', fallbackId: 'my-courses', highlight: true },
      'mrs': { panelSelector: '.gl-student-progress', fallbackId: 'my-courses', highlight: true },
    };

    let targetEl = null;

    // Hash-based navigation (e.g. #my-courses)
    if (hash) {
      if (hash === 'my-courses' && !cfg.hasCourses) {
        if (typeof showToast === 'function') {
          showToast(_noCourseMsg(), 'warning');
        }
      }
      targetEl = document.getElementById(hash);
    } else if (filter && filterTargets[filter]) {
      const target = filterTargets[filter];
      if (target.sectionId) {
        targetEl = document.getElementById(target.sectionId);
      } else if (target.panelSelector) {
        targetEl = document.querySelector(target.panelSelector);
      }
      // Fallback when primary target doesn't exist (e.g. student progress panel hidden)
      if (!targetEl && target.fallbackId) {
        targetEl = document.getElementById(target.fallbackId);
      }
    }

    if (targetEl) {
      // Small delay to ensure DOM is fully painted
      setTimeout(function () {
        GP.scrollWithinPageContent(targetEl, { block: 'start' });
        /* THE "here is the thing you asked for" mark - GP.motion.highlight.
           This was a sixth copy of the pattern that helper exists to replace: a
           class plus a setTimeout to take it off again (2500ms here, 1400 /
           1600 / 2000 in the five it already absorbed), backed by a keyframe of
           its own. */
        GP.motion.highlight(targetEl);
      }, 300);
    }
  }

  // Run on initial page load
  _handleDashboardNavigation();

  // Re-run on hash change (e.g. clicking sidebar #my-courses link while already on dashboard)
  window.addEventListener('hashchange', _handleDashboardNavigation);

  // Auto-open search palette when arriving from an error page with ?search=...
  (function _handleErrorPageSearch() {
    const params = new URLSearchParams(window.location.search);
    const q = (params.get('search') || '').trim();
    if (!q) return;
    function _open() {
      if (typeof window.GP?.openSearchPalette === 'function') {
        window.GP.openSearchPalette(q);
      } else {
        setTimeout(_open, 200);
      }
    }
    setTimeout(_open, 250);
    // Clean the URL so a refresh doesn't keep re-opening the palette
    try {
      params.delete('search');
      const qs = params.toString();
      const url = window.location.pathname + (qs ? '?' + qs : '') + window.location.hash;
      window.history.replaceState({}, '', url);
    } catch (_) { /* ignore */ }
  })();
  
  // Course search/filter functionality
  function filterCourses(query) {
    const q = query.toLowerCase().trim();
    const cards = document.querySelectorAll('.course-card');
    const grids = document.querySelectorAll('.courses-grid');
    const headers = document.querySelectorAll('.section-header');

    cards.forEach(card => {
      const searchText = card.dataset.search || '';
      card.classList.toggle('d-none', q !== '' && !searchText.includes(q));
    });

    // Hide empty course groups
    grids.forEach((grid, i) => {
      const visibleCards = grid.querySelectorAll('.course-card:not(.d-none)').length;
      grid.classList.toggle('d-none', visibleCards === 0);
      if (headers[i]) headers[i].classList.toggle('d-none', visibleCards === 0);
    });

    // Show a "no matching courses" empty state when a non-empty query hides
    // every card; hide it again when the query is cleared or matches resume.
    const emptyEl = document.getElementById('courseSearchEmpty');
    if (emptyEl) {
      const anyVisible = document.querySelectorAll('.course-card:not(.d-none)').length > 0;
      emptyEl.classList.toggle('d-none', q === '' || anyVisible);
    }
  }

  // Attach course search filter via vanilla JS (no Alpine)
  const _searchInput = document.getElementById('courseSearchInput');
  if (_searchInput) {
    _searchInput.addEventListener('input', function () {
      filterCourses(this.value);
    });
  }
  
  // Page-specific keyboard shortcuts (only for users who can edit)
  if (_canEdit) {
    onKeydownShortcuts = e => {
      if (e.shiftKey && e.key === 'N' && !e.target.matches('input, textarea, select')) {
        e.preventDefault();
        openModal('createCourseModal');
      }
      if (e.shiftKey && e.key === 'I' && !e.target.matches('input, textarea, select')) {
        e.preventDefault();
        if (GP.guardProcessAction && !GP.guardProcessAction(['import'])) return;
        openModal('importGitlabCourseModal');
      }
    };
    document.addEventListener('keydown', onKeydownShortcuts);
  }
  
