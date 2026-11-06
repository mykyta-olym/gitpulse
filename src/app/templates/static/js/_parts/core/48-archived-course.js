/* -- Archived-course read-only guard + live status poll --
   Any page belonging to a course announces it with `data-course-id`, plus
   `data-course-archived` once that course is archived: course pages put both on
   `.tabs-nav`, group / project pages on their content root. When archived,
   disable the guarded action buttons (the server already 409s them; this makes
   the read-only state visible - the CSS `.is-course-archived` dims them). Also
   poll the course status so a course archived in another tab or by another user
   flips THIS tab to read-only without a manual refresh: on flip we reload so the
   server re-renders the banner and the disabled state authoritatively.

   The marker used to be `.tabs-nav` alone, which only course pages render - so a
   GROUP or PROJECT page of an archived course showed no banner and left its
   controls live. Clicking "exclude from scoring" there only failed once the
   server answered 403. */
(function _courseArchivedGuard() {
  'use strict';
  function _nav() {
    return document.querySelector('.tabs-nav[data-course-id], [data-course-archived]');
  }

  // Move page-level status banners (marked .js-top-banner: archived,
  // data-outdated, stale-data, ...) - rendered inside the lazily-loaded content
  // with full context - up into the global top slot so they stack with the job +
  // health strips like GitLab's broadcast bar. Element-scoped empty states are
  // NOT marked, so they stay put. Banners carrying a data-banner-key replace any
  // older same-key copy in the slot (survives a content-only reload).
  function _portalTopBanners() {
    const slot = document.getElementById('globalBannerSlot');
    if (!slot) return;
    document.querySelectorAll('.js-top-banner').forEach(function (b) {
      if (slot.contains(b)) return;               // already portaled
      // Drop banners the user already dismissed (persisted) so they never flash
      // back in at the top after a navigation / re-entry.
      const dk = b.getAttribute('data-dismiss-key');
      if (dk && GP.isBannerDismissed(dk)) {
        b.remove();
        return;
      }
      const key = b.getAttribute('data-banner-key');
      if (key) {
        slot.querySelectorAll('[data-banner-key="' + key + '"]').forEach(function (o) {
          o.remove();
        });
      }
      b.setAttribute('data-portaled', '1'); // came from #main-content (see _dropPortaledBanners)
      slot.appendChild(b);
      /* Localise the timestamps INSIDE the banner, here, at the moment it lands
         in the slot. `time[data-localize-time]:not([data-localized="1"])` is
         `visibility: hidden` (utilities.css) so the server's UTC value never
         flashes before it is converted - which means an unvisited <time> stays
         invisible FOREVER while still occupying its box. The slot lives outside
         #main-content, so a navigation's scoped localize pass never reached these
         banners: "Most recent snapshot:" was followed by a timestamp-shaped hole
         and then "(7 day(s) ago)". */
      if (typeof window.localizeTimes === 'function') {
        try { window.localizeTimes(b); } catch (_) { /* keep the banner */ }
      }
    });
  }

  // Every portaled strip is PAGE-scoped (archived, data-outdated, stale-data,
  // sync-failed, dead-token). The slot lives outside #main-content, which a
  // navigation swap never touches, so without this the previous page's strips
  // stayed pinned to the top of the next one - the "I am on the Dashboard and it
  // tells me the course is archived" report.
  function _dropPortaledBanners() {
    const slot = document.getElementById('globalBannerSlot');
    if (!slot) return;
    // ONLY the strips that were portaled out of #main-content. The strips the
    // server rendered straight into the slot block (e.g. the archived-course
    // banner, course_detail.html top_banners) are reconciled by signature in
    // _adoptIncomingBanners - dropping them here removed the one the incoming
    // page had JUST re-added, and _portalTopBanners (which only looks in
    // #main-content) could not bring it back, so it vanished on every nav.
    slot.querySelectorAll('.js-top-banner[data-portaled]').forEach(function (b) { b.remove(); });
  }

  /* Strips the server rendered straight into the slot (base.html `top_banners`)
     never went through _portalTopBanners, so nothing had checked whether the
     reader already dismissed them - the archived notice came back on every
     load. One dismissal check for both routes. */
  function _pruneDismissedBanners() {
    const slot = document.getElementById('globalBannerSlot');
    if (!slot) return;
    slot.querySelectorAll('.js-top-banner[data-dismiss-key]').forEach(function (b) {
      const dk = b.getAttribute('data-dismiss-key');
      if (dk && GP.isBannerDismissed(dk)) b.remove();
    });
  }

  /* An SPA navigation swaps only #main-content, so a strip rendered into the slot
     by the INCOMING page has to be carried across explicitly - the same
     reconciliation the breadcrumb, the title and the modals block already get. */
  function _bannerSignature(b) {
    const variant = b.className.match(/gp-top-banner--([a-z]+)/)?.[1] || '';
    const key = b.getAttribute('data-banner-key') || '';
    return key + '|' + variant + '|' + (b.textContent || '').replace(/\s+/g, ' ').trim();
  }

  function _adoptIncomingBanners(doc) {
    const slot = document.getElementById('globalBannerSlot');
    if (!slot || !doc) return;
    const incoming = doc.querySelector('#globalBannerSlot');
    const incomingBanners = incoming
      ? Array.prototype.slice.call(incoming.querySelectorAll('.js-top-banner'))
      : [];
    const incomingSigs = {};
    incomingBanners.forEach(function (b) { incomingSigs[_bannerSignature(b)] = true; });

    /* Reconcile the SERVER-slot-block strips (the ones NOT portaled from
       #main-content) by signature: a strip the incoming page still carries -
       the archived-course banner across a course's tabs - is KEPT exactly where
       it is, so it never blinks off; only strips the incoming page dropped are
       removed. */
    const kept = {};
    slot.querySelectorAll('.js-top-banner:not([data-portaled])').forEach(function (b) {
      const s = _bannerSignature(b);
      if (incomingSigs[s]) { kept[s] = true; } else { b.remove(); }
    });
    /* Add the incoming slot-block strips that are not already kept. */
    incomingBanners.forEach(function (b) {
      if (kept[_bannerSignature(b)]) return;
      slot.appendChild(document.importNode(b, true));
    });
    _pruneDismissedBanners();
  }
  GP._adoptIncomingBanners = _adoptIncomingBanners;

  /* Read-only-safe controls: filters, disclosure toggles, export and reload read
     the course, they never change it, so they stay live while archived.

     The explicit attribute is the opt-out for a one-off. The classes beside it
     are components that are read-only BY CONSTRUCTION, and listing them here
     rather than tagging each use is what makes the rule hold everywhere: an
     archived course was locking every collapsible card header, so a reader
     could not fold a section to get through the page, and the Copy Token
     button, so they could not copy a secret they were allowed to see. Neither
     writes anything.

     `input[readonly]` is the same argument from the other direction: the
     browser already refuses to edit it, so the lock protects nothing and only
     stops the reader selecting the text.

     A DISCLOSURE - anything that carries `aria-expanded` and is not a listbox
     toggle - only reveals what is already on the page. Locking it made an
     archived course unreadable: "Edit JSON Configuration" on the settings page
     answered "this course is read-only" to a click that changed nothing, and
     the schedule behind it could not be looked at. The textarea inside it is
     still disabled by the same pass; only the fold is free. Listbox toggles
     (`aria-haspopup`) stay locked: opening one is the first half of a change.
     Alpine writes `aria-expanded` at init, so the raw `:aria-expanded` binding
     is matched too, for a lock pass that runs first. */
  const _READONLY_OK = [
    '[data-readonly-ok]',
    '[aria-expanded]:not([aria-haspopup])',     /* a disclosure, whoever renders it */
    '[\\:aria-expanded]:not([aria-haspopup])',
    '[data-modal-close]',            /* closes a dialog */
    '.card-collapse-btn',            /* folds a card open or shut */
    '.card-header-info-tip',         /* the "?" help mark - explains, changes nothing */
    '.tree-toggle-btn',              /* expands a table row */
    '.admin-toggle-btn',             /* reveals the admin list */
    '.tab-btn',                      /* filter tabs and navigation */
    '[role="tab"]',
    '.filter-tabs button',
    '.table-controls-filters button',
    '.teachers-role-filter button',
    'input[type="search"]',          /* searching / filtering tables */
    '.search-input',
    'input[id$="Search"]',
    'input[id$="SearchInput"]',
    '.sortable-header',              /* column sorting */
    '.sort-link',
    '[data-sort-key]',
    '.pagination-btn',               /* pagination */
    '[data-page]',
    '[data-action="page"]',
    '[data-modal]',                  /* read-only inspection modals */
    '[data-action="copyRevealedSecret"]',
    'input[readonly]',
  ].join(',');

  function _readOnlyHost() {
    // #main-content IS the region a navigation swap replaces, so the class can
    // never outlive the page that set it. (It used to land on <body>, which
    // survives navigation and left every guarded button on the NEXT page dimmed.)
    return document.getElementById('main-content') || document.body;
  }

  function _archivedReason() {
    const { t } = GP;
    return t('This course is archived and read-only. Reactivate it to make changes.');
  }

  /* A locked BUTTON stays clickable and answers with the reason; only fields are
     truly disabled.
     A greyed-out control that swallows the click tells the reader nothing - they
     cannot tell "not allowed" from "broken", which is the same complaint the
     dead-token banner already answers by leaving Sync clickable and toasting
     why. Form fields are the exception: an input that looks editable and
     silently refuses keystrokes is worse than a disabled one. */
  /* Pressing something unavailable answers with WHY.
     This used to fire only for the archived lock, so a control put out of reach
     by anything else - a running process, a permission - stayed mute: the
     tooltip carrying its reason is hover-only (`touch: false`), so on a phone
     there was no way to ask at all, and on a desktop you had to know to hover.
     Every such control is already wrapped by GP.setDisabledReason with the
     reason on the wrapper, so answer with whatever reason is actually there. */
  document.addEventListener('click', function (evt) {
    const target = evt.target && evt.target.closest ? evt.target : null;
    if (!target) return;
    let reason = null;
    if (target.closest('[data-archived-locked="1"]')) {
      reason = _archivedReason();
    } else {
      /* A disabled control emits no pointer events, so the click lands on the
         wrapper around it - which is exactly why the wrapper exists. */
      const wrap = target.closest('.gl-tip-wrap');
      if (wrap) {
        reason = wrap.querySelector('[data-archived-locked="1"]')
          ? _archivedReason()
          : (wrap.dataset.disabledReason || null);
      }
    }
    if (!reason) return;
    evt.preventDefault();
    evt.stopPropagation();
    if (evt.stopImmediatePropagation) evt.stopImmediatePropagation();
    if (window.showToast) showToast(reason, 'warning');
  }, true);

  /* `GP.setDisabledReason` is defined by process-action-guards.js, which runs
     AFTER core.bundle.js - core executes at readyState 'interactive', before
     the scripts that follow it. A plain `typeof === 'function'` check therefore
     failed silently on a first page load and the control stayed greyed out and
     mute; it only ever worked on a later navigation, when the helper happened
     to exist by then. That is why the archived Teachers page had a disabled
     search box that explained nothing. Retry until the helper arrives. */
  function _attachReason(el, reason) {
    let tries = 0;
    const attach = function () {
      if (typeof GP.setDisabledReason === 'function') {
        GP.setDisabledReason(el, reason);
        return;
      }
      if (++tries < 40) setTimeout(attach, 50);
    };
    attach();
  }

  function _lockControls() {
    const reason = _archivedReason();
    const _lock = function (el) {
      if (el.matches(_READONLY_OK)) return;
      if (el.tagName === 'BUTTON') {
        if (el.dataset.archivedLocked === '1') return;
        el.dataset.archivedLocked = '1';
        /* Deliberately NOT aria-disabled: the control is still operable - it
           answers with the reason. Marking it disabled would tell assistive tech
           (and Playwright) not to try, which is the dead-end this replaces. The
           reason rides on the tooltip for hover and on the toast for the click. */
        el.setAttribute('data-tippy-content', reason);
        return;
      }
      /* Keyed on our own marker, not on `el.disabled`. Bailing out when the
         control was ALREADY disabled meant it never got the reason: the
         Teachers page disables its search box itself, so on an archived course
         it sat greyed out and mute - the only disabled control in the app that
         explained nothing. Whatever disabled it first, on an archived course
         "this course is read-only" is the reason that governs. */
      if (el.dataset.archivedLocked === '1') return;
      el.dataset.archivedLocked = '1';
      el.disabled = true;
      _attachReason(el, reason);
    };
    document.querySelectorAll('[data-process-lock-when], .btn-save-guard').forEach(_lock);
    // The settings form carries `is-course-archived` from the server, so every
    // control inside it is an editing surface by definition. Marking only the
    // guarded action buttons left the whole weekly-deadlines editor (add / edit /
    // delete week, the schedule JSON) live on an archived course: the modal
    // opened, "Save week" wrote to the textarea, and the save the server would
    // have refused was disabled anyway - an edit with nowhere to go.
    document.querySelectorAll('form.is-course-archived').forEach(function (form) {
      form.querySelectorAll('input, select, textarea, button').forEach(_lock);
    });
  }

  function _applyReadOnly() {
    _readOnlyHost().classList.add('is-course-archived');
    _lockControls();
    _watchReadOnly();
  }

  /* Half the settings page is drawn by its own JS after the guard has run (the
     compliance-check rows arrive from loadAllChecks(), webhook rows from their
     fetch), so a one-shot pass leaves every "Edit R01" button and enabled-checkbox
     live on an archived course. Watch the content while archived and re-lock what
     appears; the observer only exists in the archived state and is disconnected
     the moment the page stops being one. */
  let _roObserver = null;
  function _watchReadOnly() {
    if (_roObserver || typeof MutationObserver !== 'function') return;
    const host = _readOnlyHost();
    let queued = false;
    _roObserver = new MutationObserver(function () {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; _lockControls(); });
    });
    _roObserver.observe(host, { childList: true, subtree: true });
  }
  function _unwatchReadOnly() {
    if (!_roObserver) return;
    _roObserver.disconnect();
    _roObserver = null;
  }

  function _clearReadOnly() {
    _unwatchReadOnly();
    _readOnlyHost().classList.remove('is-course-archived');
    // Left over from an older build that put the class on <body>; harmless to
    // clear unconditionally and it keeps a stale session from staying dimmed.
    document.body.classList.remove('is-course-archived');
  }

  let _pollId = 0;
  let _polledCourse = '';
  function _stopPoll() {
    if (_pollId) clearInterval(_pollId);
    _pollId = 0;
    _polledCourse = '';
  }
  function _startPoll(courseId) {
    const url = '/dashboard/courses/' + encodeURIComponent(courseId) + '/status';
    _polledCourse = courseId;
    _pollId = setInterval(function () {
      if (document.visibilityState === 'hidden') return;
      const polled = _polledCourse;
      fetch(url, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          // A navigation may have landed elsewhere while this was in flight;
          // reloading then would yank the user off an unrelated page.
          if (polled !== _polledCourse) return;
          if (d && d.is_active === false) {
            _stopPoll();
            const { t } = GP;
            if (window.showToast) showToast(t('This course has been archived.'), 'warning');
            // Scroll-preserving reload: a raw location.reload() slams the
            // reader back to the top of a long course page.
            setTimeout(function () { reloadKeepScroll(); }, 1200);
          }
        })
        .catch(function () { /* transient - try again next tick */ });
    }, 60000);
  }

  /* Bring the read-only state and the status poll in line with whatever page is
     on screen NOW. Called on load and after every swap, so leaving a course page
     clears both instead of leaking them into the next one. */
  function _sync() {
    const nav = _nav();
    if (!nav) { _clearReadOnly(); _stopPoll(); return; }
    if (nav.hasAttribute('data-course-archived')) {
      _applyReadOnly();
      _stopPoll();               // already archived - nothing left to watch for
      return;
    }
    _clearReadOnly();
    const id = nav.getAttribute('data-course-id');
    if (!id) { _stopPoll(); return; }
    if (id !== _polledCourse) { _stopPoll(); _startPoll(id); }
  }

  function _init() {
    _pruneDismissedBanners();
    _portalTopBanners();
    _sync();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _init, { once: true });
  } else { _init(); }
  // The action buttons arrive with the lazy content fragment, after init.
  if (document.body) {
    document.body.addEventListener('htmx:afterSwap', function (evt) {
      const tgt = evt.detail && evt.detail.target;
      // A navigation swap (target = #main-content) retires the outgoing page's
      // status strips; a lazy content swap within the same page must not.
      if (tgt && tgt.id === 'main-content') _dropPortaledBanners();
      _portalTopBanners();
      _sync();
    });
  }
})();
