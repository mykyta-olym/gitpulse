/**
 * Shared User Info Modal renderer - used by admin-users.js and course-roster.js.
 * Eliminates duplication: badge helpers, SVG icons, and profile card HTML
 * are defined once and shared across pages.
 */
;(function () {
  'use strict';

  const GP = window.GP || {};
  const { t, escapeHtml: esc } = GP;

  /* "2026/2027 \u00B7 Winter" - GP.periodLabel, the label the period badges
     and the selector use. The card printed the raw column, "2026/2027 \u00B7
     winter": lowercase, and English on a Slovak page. */
  function periodLabel(academicYear, semester) {
    return esc(GP.periodLabel(academicYear, semester));
  }

  /* -- Badge colour maps. These mirror the server macros in
     components/badges.html, which render the same roles on every page the
     modal opens over; a role must not change colour just because you opened a
     dialog. `tests/unit/test_role_badge_colours.py` pins them to each other.

     THREE different things are called a "role" here and they are deliberately
     three badges, not one:
       GP.roleBadgeHtml - the global account role -> badges.html `role_badge`
       CROLE_BADGE      - the per-course role     -> badges.html `course_role_badge`
       ACCESS_BADGE     - GitLab's project access level, which is nobody's
                          account role and shares only the WORD "owner"

     The comment that stood here claimed lockstep with
     partials/project/_members_table.html, which carries no colours at all, and
     under it CROLE_BADGE had drifted: a course owner was `warning` and a course
     teacher `purple` - the ACCESS_BADGE and ROLE_BADGE values, evidently copied
     across. The server draws a course owner teal (badges.html and
     components/members.html both), so the same person's course role was orange
     in this dialog and teal on the page behind it. -- */
  const CROLE_BADGE = { owner: 'teal', teacher: 'info', admin: 'warning', mentor: 'teal', ta: 'info', student: 'secondary' };
  const ACCESS_BADGE = { owner: 'warning', maintainer: 'info', developer: 'secondary', reporter: 'grey', guest: 'grey' };

  function _badge(text, variant) {
    const label = (text || '').charAt(0).toUpperCase() + (text || '').slice(1);
    return GP.badgeHtml(label, variant, { size: 'sm' });
  }

  function roleBadge(role) {
    return GP.roleBadgeHtml(role);
  }

  function courseRoleBadge(role) {
    return _badge(role, CROLE_BADGE[(role || '').toLowerCase()] || 'secondary');
  }

  /** GitLab project/group access level (owner/maintainer/developer/...). */
  function accessRoleBadge(role) {
    return _badge(role, ACCESS_BADGE[(role || '').toLowerCase()] || 'secondary');
  }

  /** Muted "Archived" pill for an inactive course / group. */
  function archivedBadge() {
    return ' ' + GP.badgeHtml(t('Archived'), 'muted', { size: 'sm' });
  }

  /** Check if a user has a course_role entry for any course linked to a membership. */
  function hasCourseRole(courses, membership) {
    if (!courses || !courses.length) return false;
    for (let i = 0; i < courses.length; i++) {
      if (courses[i].course_id === membership.course_id) return true;
    }
    return false;
  }

  /* -- SVG icons (24×24 Feather icons) -- */
  /* The app's icons, not a private set. This file carried its own 8-glyph
     registry of 24x24 stroked Feather paths, so the card drew a different
     icon family from every other surface around it - including the table it
     opens from. GP.iconSvg is the mirror of components/icons.html; 'sm' is
     the 16px the card's CSS sizes these to anyway. */
  function ico(name) {
    return GP.iconSvg(name, 'sm');
  }

  /**
   * Render the user info profile card HTML from API data.
   * @param {object} data  - response from /admin/users/{id}/info
   * @returns {string} HTML string
   */
  function renderUserInfoCard(data) {
    const p = data.profile || {};
    let html = '';

    /* -- Header: Avatar + Identity -- */
    html += '<div class="user-info-header">';
    // The app's avatar (GP.avatarHtml), 64px as in GitLab's user popover.
    html += GP.avatarHtml(p.avatar_url, p.full_name || p.username, 64);

    html += '<div class="user-info-identity">';
    html += '<div class="user-info-name">' + esc(p.full_name || p.username || '\u2014') + ' ' + roleBadge(p.role || 'student');
    if (p.is_active === false) html += ' ' + GP.badgeHtml(t('Inactive'), 'danger', { size: 'sm' });
    if (p.is_bot) html += ' ' + GP.badgeHtml(t('Service Account'), 'muted', { size: 'sm', tooltip: t('GitLab service account / bot - not a human user') });
    if (p.no_user_account) html += ' ' + GP.badgeHtml(t('GitLab only'), 'gray', { size: 'sm', tooltip: t('This member has no GitPulse account - they were discovered via GitLab group membership') });
    html += '</div>';

    const mp = [];
    if (p.email && p.email !== 'PRIVATE') mp.push('<span class="user-info-meta-row">' + ico('mail') + esc(p.email) + '</span>');
    if (p.gitlab_username) mp.push('<span class="user-info-meta-row">' + ico('gitlab') + '@' + esc(p.gitlab_username) + '</span>');
    if (p.gitlab_user_id) mp.push('<span class="user-info-meta-row">' + ico('tag') + esc(String(p.gitlab_user_id)) + '</span>');
    if (p.created_at) {
      try { mp.push('<span class="user-info-meta-row">' + ico('calendar') + GP.timeHtml(p.created_at, 'date') + '</span>'); } catch (_) { /* */ }
    }
    if (mp.length) html += '<div class="user-info-meta">' + mp.join('') + '</div>';
    html += '</div></div>';

    /* -- Enrich from GitLab button -- */
    if (data._userId) {
      html += '<div class="user-info-enrich">';
      html += GP.buttonHtml(t('Update from GitLab'), {icon: 'refresh', variant: 'secondary',
        size: 'sm', id: 'enrichSingleUserBtn', data: {'user-id': data._userId}});
      html += '</div>';
    }

    /* -- Courses section -- */
    const courses = data.course_roles || [];
    const memberships = data.memberships || [];

    /* Derive unique course IDs from both direct course_roles and group memberships */
    const seenCourseIds = new Set();
    for (let ci = 0; ci < courses.length; ci++) {
      if (courses[ci].course_id) seenCourseIds.add(courses[ci].course_id);
    }
    for (let mi = 0; mi < memberships.length; mi++) {
      if (memberships[mi].course_id) seenCourseIds.add(memberships[mi].course_id);
    }
    const totalCourses = seenCourseIds.size;

    html += '<div class="user-info-section">';
    html += '<div class="user-info-section-title">' + ico('book') + ' ' + esc(t('Courses')) + ' <span class="user-info-section-count">' + totalCourses + '</span></div>';
    if (!courses.length && !memberships.length) {
      html += GP.emptyStateHtml(t('No course memberships'));
    } else {
      /* Show direct course_roles first */
      const shownCourseIds = new Set();
      for (let i = 0; i < courses.length; i++) {
        const c = courses[i];
        if (c.course_id) shownCourseIds.add(c.course_id);
        html += '<div class="user-info-card"><div class="user-info-card-main">';
        html += '<a href="' + esc(c.course_url) + '">' + esc(c.course_code) + ' \u2014 ' + esc(c.course_name) + '</a>';
        html += '<div class="user-info-card-sub">' + (GP.periodBadgeHtml(c.academic_year, c.semester) || periodLabel(c.academic_year, c.semester)) + '</div>';
        html += '</div><div class="user-info-card-badges">' + courseRoleBadge(c.role);
        if (c.is_active === false) html += archivedBadge();
        if (c.via_config) html += ' ' + GP.badgeHtml(t('config'), 'info', { size: 'sm', tooltip: t('Set via course config') });
        html += '</div></div>';
      }

      /* Derive courses from group memberships that aren't already shown */
      const derivedCourses = new Map();
      for (let di = 0; di < memberships.length; di++) {
        const dm = memberships[di];
        if (dm.course_id && !shownCourseIds.has(dm.course_id) && !derivedCourses.has(dm.course_id)) {
          derivedCourses.set(dm.course_id, dm);
        }
      }
      derivedCourses.forEach(function (dc) {
        const label = dc.course_code
          ? esc(dc.course_code) + ' \u2014 ' + esc(dc.course_name || '')
          : esc(dc.course_name || '');
        const sub = (dc.academic_year || dc.semester)
          ? (GP.periodBadgeHtml(dc.academic_year, dc.semester) || periodLabel(dc.academic_year, dc.semester))
          : esc(t('Via group membership'));
        html += '<div class="user-info-card"><div class="user-info-card-main">';
        html += '<a href="' + esc(dc.course_url) + '">' + label + '</a>';
        html += '<div class="user-info-card-sub">' + sub + '</div>';
        html += '</div><div class="user-info-card-badges">';
        const dcRole = dc.is_teacher ? 'teacher' : 'student';
        html += courseRoleBadge(dcRole);
        if (dc.course_active === false) html += archivedBadge();
        html += '</div></div>';
      });
    }
    html += '</div>';

    /* -- Groups section -- */
    html += '<div class="user-info-section">';
    html += '<div class="user-info-section-title">' + ico('users') + ' ' + esc(t('Groups')) + ' <span class="user-info-section-count">' + memberships.length + '</span></div>';
    if (!memberships.length) {
      html += GP.emptyStateHtml(t('No group memberships found'));
    } else {
      for (let j = 0; j < memberships.length; j++) {
        const m = memberships[j];
        html += '<div class="user-info-card"><div class="user-info-card-main">';
        html += '<a href="' + esc(m.team_url) + '">' + esc(m.team_name) + '</a>';
        /* The group's course WITH its term - a student in last summer's
           tim-03 and this summer's is in two different groups of that name. */
        html += '<div class="user-info-card-sub"><a href="' + esc(m.course_url) + '">' + esc(m.course_name || m.course_code) + '</a>'
          + (m.academic_year ? ' ' + GP.periodBadgeHtml(m.academic_year, m.semester) : '');
        if (m.projects && m.projects.length) {
          /* Cap the inline project list - a member of a 20-project group used to
             render a wall of blue links. Show a few, then a clickable "+N more"
             that reveals the rest in place (toggles back to "Show less"). */
          const MAX_PROJECTS = 3;
          const link = function (pr) { return '<a href="' + esc(pr.url) + '">' + esc(pr.name) + '</a>'; };
          const shown = m.projects.slice(0, MAX_PROJECTS).map(link).join(', ');
          let extra = '';
          if (m.projects.length > MAX_PROJECTS) {
            const rest = m.projects.slice(MAX_PROJECTS).map(link).join(', ');
            const moreN = m.projects.length - MAX_PROJECTS;
            extra =
              '<span data-projects-rest hidden>, ' + rest + '</span> '
              + GP.buttonHtml('+' + moreN + ' ' + t('more'), {
                variant: 'ghost', size: 'sm', expanded: false,
                data: { 'toggle-projects': '', 'more-n': moreN }
              });
          }
          html += ' \u00B7 ' + shown + extra;
        }
        html += '</div></div><div class="user-info-card-badges">';
        if (m.access_role) html += accessRoleBadge(m.access_role);
        if (m.team_active === false || m.course_active === false) html += archivedBadge();
        if (m.is_mentor && !hasCourseRole(courses, m)) html += ' ' + GP.badgeHtml(t('Mentor'), 'teal', { size: 'sm' });
        html += '</div></div>';
      }
    }
    html += '</div>';

    return html;
  }

  /* -- Expand / collapse the per-group "+N more" project list. Delegated once
     at module load so it works for any user-info modal rendered later. -- */
  document.addEventListener('click', function (e) {
    const btn = e.target.closest && e.target.closest('[data-toggle-projects]');
    if (!btn) return;
    e.preventDefault();
    const sub = btn.closest('.user-info-card-sub') || btn.parentElement;
    const rest = sub && sub.querySelector('[data-projects-rest]');
    if (!rest) return;
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    rest.hidden = expanded;
    btn.setAttribute('aria-expanded', String(!expanded));
    btn.querySelector('.btn-text').textContent = expanded
      ? ('+' + (btn.dataset.moreN || '') + ' ' + t('more'))
      : t('Show less');
  });

  /* -- Expose -- */
  window.UserInfoModal = {
    render: renderUserInfoCard,
    roleBadge: roleBadge,
    courseRoleBadge: courseRoleBadge,
    ico: ico
  };

})();
