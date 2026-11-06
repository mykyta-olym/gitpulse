/* Course Teachers page.

   The table is server-rendered and worked by the shared components, exactly as
   on the Users page: ClientPaginator, TableFilter (the search) and FilterPills
   (the role tabs), with sortable-table.js on the headers. What is this page's
   own is the change itself - a role picked, a teacher removed, a teacher added,
   every restriction cleared - and each one applies at once, as on GitLab's
   members page: the course's full list goes to the same endpoint the form
   always posted to, and the page comes back from the server as it now is. */

// Wrapped in an IIFE like every other page script: a top-level `const GP` here
// collides with the one core.bundle.js declares and aborts the whole file.
(function initCourseTeachersPage() {
  'use strict';
  const GP = window.GP || {};
  GP.runPageCleanup();

  const { t } = GP;

  function config() {
    try {
      const el = document.getElementById('gp-page-config');
      return el ? JSON.parse(el.textContent) : {};
    } catch (_) {
      return {};
    }
  }

  /** The course's full list as the server sent it - admins included, even when
      this reader is not shown them, so a change keeps their memberships. */
  function currentTeachers() {
    const list = config().currentTeachers;
    return Array.isArray(list) ? list.map(function (i) { return Object.assign({}, i); }) : [];
  }

  function roleLabel(role) {
    const labels = config().roleLabels || {};
    return labels[role] || role;
  }

  function nameOf(inst) {
    return (inst && (inst.name || inst.username)) || '';
  }

  function ownerCount(list) {
    return list.filter(function (i) { return i.role === 'owner'; }).length;
  }

  /* -- Sending a change -- */
  function save(list, message) {
    const form = document.getElementById('teacherForm');
    if (!form) return Promise.resolve();
    const body = new FormData(form);
    body.set('teachers_json', JSON.stringify(list));
    // JSON back, not the form's redirect: the outcome is all this needs.
    return fetch(form.action, {
      method: 'POST', body: body, credentials: 'same-origin', headers: { Accept: 'application/json' },
    })
      .then(function (resp) {
        return resp.json().catch(function () { return {}; }).then(function (data) {
          if (data.error === 'no_owner') {
            GP.showToast(t('A course must have at least one owner.'), 'danger');
            return;
          }
          if (data.error === 'conflict') {
            GP.flashToast(t('Someone else changed the teachers meanwhile - this is the list as it is now.'), 'warning');
          } else if (resp.ok && data.ok) {
            GP.flashToast(message, 'success');
          } else {
            throw new Error(String(resp.status));
          }
          GP.reloadKeepScroll();
        });
      })
      .catch(function () {
        GP.showToast(t('Could not save the change. Try again.'), 'danger');
      });
  }

  function confirmThen(opts, list, message) {
    GP.confirmDialog(Object.assign({ confirmText: t('Remove'), variant: 'danger' }, opts))
      .then(function (ok) { if (ok) save(list, message); });
  }

  /* -- The row's role menu, its remove button, and Remove all restrictions -- */
  function onClick(event) {
    const pick = event.target.closest('[data-teacher-role]');
    if (pick) {
      const username = pick.dataset.username;
      const role = pick.dataset.teacherRole;
      const list = currentTeachers();
      const inst = list.find(function (i) { return i.username === username; });
      if (!inst || inst.role === role) return;
      if (inst.role === 'owner' && ownerCount(list) <= 1) {
        GP.showToast(t('Cannot change role - this is the last owner. Transfer ownership first.'), 'danger');
        return;
      }
      inst.role = role;
      save(list, nameOf(inst) + ': ' + t('Role changed to') + ' ' + roleLabel(role));
      return;
    }

    const remove = event.target.closest('[data-teacher-remove]');
    if (remove) {
      const username = remove.dataset.teacherRemove;
      const list = currentTeachers();
      const inst = list.find(function (i) { return i.username === username; });
      if (!inst) return;
      if (inst.role === 'owner' && ownerCount(list) <= 1) {
        GP.showToast(t('Cannot remove the last owner. Transfer ownership first.'), 'danger');
        return;
      }
      confirmThen({
        title: t('Remove teacher?'),
        message: t('Remove') + ' ' + nameOf(inst) + ' ' + t('from this course? Their existing feedback and grades stay intact.'),
      }, list.filter(function (i) { return i.username !== username; }), nameOf(inst) + ' ' + t('removed from course'));
      return;
    }

    if (event.target.closest('#btnClearTeachers')) {
      // Owners and administrators stay: the course always keeps someone who
      // can manage it, and an admin has every course anyway.
      const kept = currentTeachers().filter(function (i) { return i.role === 'owner' || i.global_role === 'admin'; });
      confirmThen({
        title: t('Remove all non-owner teachers from this course?'),
        message: t('Their existing feedback and grades stay intact. Owners are kept so the course always has an administrator.'),
      }, kept, t('All teacher restrictions removed'));
    }
  }

  /* -- The table: the Users page's components, with this table's role tabs -- */
  function initTable() {
    const tbody = document.querySelector('#courseTeachersTable tbody');
    if (!tbody || tbody._clientPaginator) return;
    const paginator = new ClientPaginator({
      tbodySelector: '#courseTeachersTable tbody',
      controlsSelector: '#paginationControls',
      storageKey: 'course-teachers',
      showPerPage: true,
    }).register('courseTeachersTable');
    const tabs = new FilterPills('.teachers-role-filter', 'data-value', function () {
      filter.apply();
    });
    // A tab narrows by the course role (Course Owner) or by the account
    // (Teacher, Admin), as the page always did.
    const filter = new TableFilter({
      inputSelector: '#teacherSearch',
      tbodySelector: '#courseTeachersTable tbody',
      paginator: paginator,
      urlParams: () => ({ role: tabs.activeValue }),
      rowFilter: function (row) {
        const view = tabs.activeValue;
        return view === 'all'
          || (view === 'owner' ? row.dataset.role === 'owner' : row.dataset.account === view);
      },
    });
    filter.apply();
  }

  /* -- The Add teacher dialog (Alpine: the typeahead is an Alpine component) -- */
  function teacherInvite() {
    const cfg = config();
    const users = Array.isArray(cfg.availableUsers) ? cfg.availableUsers : [];
    return {
      search: '',
      showDropdown: false,
      picked: null,

      get filteredUsers() {
        const q = this.search.toLowerCase();
        return users.filter(function (u) {
          return !q || u.username.toLowerCase().includes(q) || (u.name && u.name.toLowerCase().includes(q));
        });
      },

      init() {
        const self = this;
        // Typing again after a pick means another person: the pick is undone.
        this.$watch('search', function (value) {
          if (self.picked && value !== nameOf(self.picked)) self.picked = null;
        });
      },

      pick(user) {
        this.picked = user;
        this.search = nameOf(user);
        this.showDropdown = false;
      },

      submit() {
        const user = this.picked;
        if (!user) return;
        const field = document.getElementById('addTeacherRole');
        const role = (field && field.value) || 'teacher';
        const list = currentTeachers();
        list.push({ username: user.username, name: user.name || '', role: role, global_role: user.role || 'student' });
        save(list, nameOf(user) + ' ' + t('added as') + ' ' + roleLabel(role));
      },
    };
  }

  window.teacherInvite = teacherInvite;
  const register = function () {
    if (window.Alpine && typeof window.Alpine.data === 'function') {
      try { window.Alpine.data('teacherInvite', teacherInvite); } catch (_) { /* already registered */ }
    }
  };
  if (window.Alpine && window.Alpine.version) register();
  else document.addEventListener('alpine:init', register, { once: true });

  document.addEventListener('click', onClick);
  GP.activePageCleanup = function () { document.removeEventListener('click', onClick); };
  initTable();
  GP.autoReloadOnJob(['sync*']);
})();
