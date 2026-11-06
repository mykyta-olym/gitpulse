/**
 * Search Command Palette - GitLab-style global search
 *
 * Every part is a shared component, the way GitLab's palette is GlSearchBoxByType,
 * GlCollapsibleListbox and GlDisclosureDropdownGroup:
 *   - the field is `search_input(borderless)`; a handle typed first scopes it:
 *     ">" pages, "@" users, ":" courses, "#" students
 *   - the filters are a `gl-dropdown` in the field whose items type that handle
 *   - results are `gl-dropdown-item`s under `gl-dropdown-header`s, with the
 *     shared avatar (`GP.avatarHtml`) and role badge (`GP.roleBadgeHtml`)
 *   - pages come from the sidebar; users/courses/teams/students from
 *     /dashboard/search, behind the shared loading mark
 *   - ↓ moves focus into the results and ↑ from the first one back to the
 *     field, Esc closes, "/" opens
 */
(function () {
  'use strict';

  /* -- DOM refs -- */
  const backdrop = document.getElementById('searchModalBackdrop');
  const input    = document.getElementById('searchModalInput');
  const body     = document.getElementById('searchModalResults');
  const trigger  = document.getElementById('globalSearchBtn');
  const filters  = document.getElementById('searchFilters');
  const closeBtn = document.getElementById('searchCloseBtn');

  if (!backdrop || !input || !body) return;

  /* -- Role config from base template -- */
  let _baseConfig = {};
  try {
    const _cfgEl = document.getElementById('gp-base-config');
    if (_cfgEl) _baseConfig = JSON.parse(_cfgEl.textContent);
  } catch (_) { /* ignore */ }
  const _isAdmin = !!_baseConfig.isAdmin;
  const _isTeacher = !!(_baseConfig.isAdmin || _baseConfig.isTeacher);
  const _canSearchUsers = _isTeacher;

  /* -- State -- */
  let abortCtrl      = null;
  let _searchGen     = 0;
  let debounceTimer  = null;
  let allPages       = [];
  let isOpen         = false;
  const _t = GP.t;
  const esc = GP.escapeHtml;

  const HANDLES = { '>': 'pages', '@': 'users', ':': 'courses', '#': 'students' };

  /* -- Collect all navigable pages from the sidebar + known routes -- */
  function buildPageList() {
    const pages = [];
    const seen = {};

    const sidebarSections = document.querySelectorAll('.gl-sidebar-body .gl-sidebar-section');
    sidebarSections.forEach(function (sec) {
      let label = '';
      const labelEl = sec.querySelector('.gl-sidebar-section-label');
      if (labelEl) label = labelEl.textContent.trim();

      sec.querySelectorAll('.gl-sidebar-item').forEach(function (el) {
        const href = el.getAttribute('href');
        if (!href || href === '#' || seen[href]) return;
        seen[href] = true;
        const textEl = el.querySelector('.gl-sidebar-item-text');
        const name = textEl ? textEl.textContent.trim() : el.textContent.trim();
        const iconEl = el.querySelector('svg');
        pages.push({ href: href, text: name, section: label, iconSvg: iconEl ? iconEl.outerHTML : null, type: 'page' });
      });
    });

    document.querySelectorAll('.gl-sidebar-bottom .gl-sidebar-bottom-item').forEach(function (el) {
      const href = el.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript') || seen[href]) return;
      if (el.classList.contains('gl-sidebar-toggle')) return;
      seen[href] = true;
      const textEl = el.querySelector('.gl-sidebar-item-text');
      const name = textEl ? textEl.textContent.trim() : el.textContent.trim();
      const iconEl = el.querySelector('svg');
      pages.push({ href: href, text: name, section: '', iconSvg: iconEl ? iconEl.outerHTML : null, type: 'page' });
    });

    return pages;
  }

  /* -- Open / Close -- */
  function cancelRead() {
    ++_searchGen;
    if (abortCtrl) { abortCtrl.abort(); abortCtrl = null; }
    clearTimeout(debounceTimer);
    debounceTimer = null;
    body.removeAttribute('aria-busy');
  }

  function open(prefill) {
    cancelRead();
    allPages = buildPageList();
    isOpen = true;
    backdrop.classList.remove('closing');
    backdrop.hidden = false;
    backdrop.classList.add('active');
    trigger?.setAttribute('aria-expanded', 'true');
    input.value = '';
    renderDefault();
    GP.motion.searchPalette(backdrop, trigger, true);
    input.focus({ preventScroll: true });
    if (typeof prefill === 'string' && prefill) {
      input.value = prefill;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }

  function close(instant) {
    if (!isOpen) return;
    isOpen = false;
    cancelRead();
    if (filters) GP.dropdown.close(filters);
    const returnFocus = backdrop.contains(document.activeElement);
    trigger?.setAttribute('aria-expanded', 'false');
    backdrop.classList.remove('active');
    backdrop.classList.add('closing');
    const _finalize = function () {
      if (isOpen) return;
      backdrop.classList.remove('closing');
      backdrop.hidden = true;
      input.value = '';
      body.innerHTML = '';
      if (returnFocus) trigger?.focus({ preventScroll: true });
    };
    GP.motion.searchPalette(backdrop, trigger, false, _finalize, instant === true);
  }

  function navigateTo(href) {
    close(true); /* at once: the page swap is a jump's one motion */
    /* The app's own navigation, like every link in the sidebar: the progress
       bar runs, the page it is leaving stays put and inert, and the content is
       swapped instead of the whole document being loaded again. A jump from the
       palette used to be the one navigation in the app that reported nothing at
       all and paid for a full page load. Falls back when the URL is not ours. */
    if (GP.navigateTo(href)) return;
    window.location.href = href;
  }

  /* -- Rendering: dropdown items under group headers -- */
  function itemHtml(item) {
    const lead = item.type === 'page'
      ? (item.iconSvg || '')
      : GP.avatarHtml(item.avatarUrl, item.text, 16, { entity: item.type === 'course' || item.type === 'team' });
    const note = item.detail
      ? '<span class="gl-dropdown-item-note gl-dropdown-item-note--muted">' + esc(item.detail) + '</span>'
      : '';
    return '<a class="gl-dropdown-item" href="' + esc(item.href) + '">' + lead +
      '<span class="gl-dropdown-item-content"><span class="gl-dropdown-item-title">' + esc(item.text) +
      '</span></span>' + note + (item.role ? GP.roleBadgeHtml(item.role) : '') + '</a>';
  }

  function appendGroup(label, items) {
    if (!items || !items.length) return;
    body.insertAdjacentHTML('beforeend',
      (body.querySelector('.gl-dropdown-item') ? '<div class="gl-dropdown-divider"></div>' : '') +
      '<div class="gl-dropdown-header">' + esc(label) + '</div>' + items.map(itemHtml).join(''));
    GP.scanAvatars(body);
  }

  /* -- Default view (no query) - the sidebar's pages, in its groups -- */
  function renderDefault() {
    body.innerHTML = '';
    const groups = {};
    const order = [];
    allPages.forEach(function (p) {
      const key = p.section || _t('Pages');
      if (!groups[key]) { groups[key] = []; order.push(key); }
      groups[key].push(p);
    });
    order.forEach(function (label) { appendGroup(label, groups[label]); });
  }

  function renderEmpty(message) {
    body.innerHTML = '<div class="gl-dropdown-empty">' + esc(message) + '</div>';
  }

  /* -- Filter pages client-side -- */
  function filterPages(query) {
    const q = query.toLowerCase();
    return allPages.filter(function (p) {
      return p.text.toLowerCase().indexOf(q) !== -1 ||
             p.href.toLowerCase().indexOf(q) !== -1 ||
             (p.section && p.section.toLowerCase().indexOf(q) !== -1);
    });
  }

  /* -- API search -- */
  function searchAPI(query, scope) {
    abortCtrl = new AbortController();
    return GP.apiCall('/dashboard/search?q=' + encodeURIComponent(query) + '&scope=' + scope,
      'GET', null, { signal: abortCtrl.signal, timeoutMs: 10000, maxRetries: 0 });
  }

  /* -- The handle typed first decides the scope -- */
  function parseInput(raw) {
    const val = raw.trim();
    const scope = HANDLES[val.charAt(0)];
    if (!scope || (scope === 'users' && !_canSearchUsers)) return { scope: 'all', query: val };
    return { scope: scope, query: val.substring(1).trim() };
  }

  /* -- Build display items from API data -- */
  function buildUserItems(data) {
    return (data || []).map(function (u) {
      /* An admin lands on User Management with the person already found. */
      const href = _isAdmin ? '/dashboard/admin/users?q=' + encodeURIComponent(u.username) : (u.href || '/dashboard');
      return { href: href, text: u.name, detail: '@' + u.username, role: u.role, type: 'user', avatarUrl: u.avatar_url || '' };
    });
  }
  function buildCourseItems(data) {
    return (data || []).map(function (c) {
      return { href: c.href || ('/dashboard/courses/' + c.id), text: c.name, detail: c.code + (c.year ? ' · ' + GP.periodLabel(c.year, c.semester) : ''), type: 'course' };
    });
  }
  function buildTeamItems(data) {
    return (data || []).map(function (t) {
      const term = t.course_year ? ' · ' + GP.periodLabel(t.course_year, t.course_semester) : '';
      return { href: t.href || ('/dashboard/teams/' + t.id), text: t.name, detail: (t.course_name || _t('Group')) + term, type: 'team' };
    });
  }
  function buildStudentItems(data) {
    return (data || []).map(function (s) {
      return { href: s.href || '/dashboard', text: s.name, detail: '@' + s.username + (s.team ? ' · ' + s.team : ''), type: 'student' };
    });
  }

  /* -- Main search handler -- */
  async function doSearch() {
    cancelRead();
    const gen = _searchGen;
    const { query, scope } = parseInput(input.value);
    if (!query) {
      if (scope === 'all') renderDefault();
      else {
        const hints = { users: _t('Type a name to search users'), courses: _t('Type a name to search courses'), students: _t('Type a name to search students'), pages: _t('Type to search pages') };
        renderEmpty(hints[scope]);
      }
      return;
    }

    const pages = scope === 'all' || scope === 'pages' ? filterPages(query) : [];
    body.innerHTML = '';
    appendGroup(_t('Pages'), scope === 'all' ? pages.slice(0, 5) : pages);
    if (scope === 'pages') {
      if (!pages.length) renderEmpty(_t('No pages found for') + ' “' + query + '”');
      return;
    }

    body.insertAdjacentHTML('beforeend', GP.renderLoaderHtml('', 'lg'));
    body.setAttribute('aria-busy', 'true');
    try {
      const data = await searchAPI(query, scope);
      if (!isOpen || gen !== _searchGen) return;
      body.querySelector('.gp-block-loading')?.remove();
      const groups = [
        [_t('Users'), _canSearchUsers && (scope === 'all' || scope === 'users') ? buildUserItems(data.users) : []],
        [_t('Courses'), scope === 'all' || scope === 'courses' ? buildCourseItems(data.courses) : []],
        [_t('Groups'), scope !== 'students' ? buildTeamItems(data.teams) : []],
        [_t('Students'), scope === 'all' || scope === 'students' ? buildStudentItems(data.students) : []],
      ];
      groups.forEach(function ([label, items]) {
        appendGroup(label, scope === 'all' ? items.slice(0, 5) : items);
      });
      if (!body.querySelector('.gl-dropdown-item')) {
        const empty = { users: 'No users found for', courses: 'No courses found for', students: 'No students found for', all: 'No results found for' };
        renderEmpty(_t(empty[scope]) + ' “' + query + '”');
      }
    } catch (err) {
      if (!isOpen || gen !== _searchGen || err?.superseded) return;
      body.querySelector('.gp-block-loading')?.remove();
      body.insertAdjacentHTML('beforeend', GP.errorStateHtml(err.message, _t('Retry')));
      GP.bindRetry(body, doSearch);
    } finally {
      if (gen === _searchGen) {
        abortCtrl = null;
        body.removeAttribute('aria-busy');
      }
    }
  }

  /* -- Keyboard navigation: focus moves through the results, as in GitLab -- */
  function getAllResultItems() { return Array.from(body.querySelectorAll('.gl-dropdown-item')); }

  function scrollResultIntoBody(item) {
    if (!item || !body) return;
    try {
      const itemRect = item.getBoundingClientRect();
      const bodyRect = body.getBoundingClientRect();
      const pad = 8;
      let nextTop = null;
      if (itemRect.top < bodyRect.top + pad) {
        nextTop = body.scrollTop + itemRect.top - bodyRect.top - pad;
      } else if (itemRect.bottom > bodyRect.bottom - pad) {
        nextTop = body.scrollTop + itemRect.bottom - bodyRect.bottom + pad;
      }
      if (nextTop !== null) {
        if (typeof body.scrollTo === 'function') {
          body.scrollTo({ top: Math.max(0, nextTop), behavior: 'smooth' });
        } else {
          body.scrollTop = Math.max(0, nextTop);
        }
      }
    } catch (_) {}
  }

  function focusResult(item) {
    item.focus({ preventScroll: true });
    scrollResultIntoBody(item);
  }

  /* -- Filters: an item types its handle into the field -- */
  if (filters) {
    filters.querySelectorAll('[data-search-handle]').forEach(function (item) {
      item.addEventListener('click', function () {
        const value = input.value;
        input.value = item.getAttribute('data-search-handle') + (HANDLES[value.charAt(0)] ? value.slice(1) : value);
        input.focus({ preventScroll: true });
        doSearch();
      });
    });
  }

  /* -- Events -- */
  if (trigger) trigger.addEventListener('click', function (e) { e.preventDefault(); open(); });
  if (closeBtn) closeBtn.addEventListener('click', function () { close(); });
  backdrop.addEventListener('click', function (e) { if (e.target === backdrop) close(); });

  body.addEventListener('click', function (e) {
    const item = e.target.closest('.gl-dropdown-item');
    if (!item || e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    navigateTo(item.getAttribute('href'));
  });

  input.addEventListener('input', function () {
    cancelRead();
    const { query, scope } = parseInput(input.value);
    if (!query || scope === 'pages') doSearch();
    else debounceTimer = setTimeout(doSearch, 150);
  });

  input.addEventListener('keydown', function (e) {
    if (e.key !== 'ArrowDown') return;
    const items = getAllResultItems();
    if (!items.length) return;
    e.preventDefault();
    focusResult(items[0]);
  });

  body.addEventListener('keydown', function (e) {
    const items = getAllResultItems();
    const idx = items.indexOf(document.activeElement);
    if (idx === -1) return;
    let next = null;
    if (e.key === 'ArrowDown') next = items[Math.min(idx + 1, items.length - 1)];
    else if (e.key === 'ArrowUp') next = idx === 0 ? input : items[idx - 1];
    else if (e.key === 'Home') next = items[0];
    else if (e.key === 'End') next = items[items.length - 1];
    if (!next) return;
    e.preventDefault();
    if (next === input) input.focus({ preventScroll: true });
    else focusResult(next);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA' || document.activeElement.isContentEditable)) return;
    if (e.key === '/' && backdrop.hidden) { e.preventDefault(); open(); }
    if (e.key === 'Escape' && !backdrop.hidden) close();
  });

  GP.openSearchPalette = open;
})();
