/* academic-period.js - the academic period in the browser.

   One module for everything the browser does with a period, so no page and no
   dialog carries its own copy:

   * GP.periodLabel(year, semester) - "2026/2027 · Winter", translated. The one
     label, the same one components/academic_period.html prints; six scripts
     used to build "2026/2027 / winter" by hand, in English, on Slovak pages.
   * The period selector - its links are rebuilt from the live address bar at
     click time, so a search or a sort the page wrote into the URL without a
     reload survives switching the term.
   * GP.withPagePeriod(url) - a live refresher asks for the term on screen, not
     the default one.
   * GP.followPeriod(year, semester) - after a course lands in a term (created,
     imported, moved), take the reader to that term if the page shows another.
   * The period-and-dates fields (period_fields in academic_period.html): the
     term and its two dates kept together. See the macro for the rules; they
     are implemented once, here. */
(function () {
  'use strict';

  const GP = (window.GP = window.GP || {});
  const { t } = GP;

  /* ---------------------------------------------------------------- label */

  function periodLabel(academicYear, semester) {
    if (!academicYear && !semester) return '';
    const term = semester === 'winter' ? t('Winter')
      : semester === 'summer' ? t('Summer') : (semester || '');
    return (academicYear || '') + ' · ' + term;
  }
  GP.periodLabel = periodLabel;

  function periodKey(academicYear, semester) {
    return String(academicYear || '').replace('/', '-') + '-' + String(semester || '');
  }
  GP.periodKey = periodKey;

  /* The period as a BADGE - the markup period_badge() renders on the server,
     so a list drawn in the browser (the User Info card, a live table) shows a
     term exactly as the pages do: gray, and info-blue for the term the
     calendar is in. */
  GP.periodBadgeHtml = function (academicYear, semester) {
    if (!academicYear || !semester) return '';
    const meta = document.querySelector('meta[name="gp-current-period"]');
    const current = !!meta && meta.content === periodKey(academicYear, semester);
    return GP.badgeHtml(periodLabel(academicYear, semester), current ? 'info' : 'gray',
      { size: 'sm', class: 'gl-period-badge' });
  };

  /* ------------------------------------------------- the page's period */

  function pageSelector() {
    return document.querySelector('[data-period-selector]');
  }

  function periodParam() {
    const el = pageSelector();
    return (el && el.dataset.periodParam) || 'period';
  }

  /* The current address with the period set - every other parameter kept,
     the page number dropped (page 4 of one term is not page 4 of another). */
  function urlForPeriod(key) {
    const u = new URL(window.location.href);
    u.searchParams.set(periodParam(), key);
    u.searchParams.delete('page');
    u.searchParams.delete('_gp_refresh');
    u.hash = '';
    return u.pathname + u.search;
  }
  GP.urlForPeriod = urlForPeriod;

  /* A live refresher's URL, carrying the period the page is showing. Without
     it the server answers for its default term, and the refreshed card
     describes a different term than the grid beside it. */
  GP.withPagePeriod = function (url) {
    const value = new URLSearchParams(window.location.search).get(periodParam());
    if (!value) return url;
    const u = new URL(url, window.location.origin);
    u.searchParams.set(periodParam(), value);
    return u.pathname + u.search;
  };

  /* After a course lands in a term: if the page is scoped to ANOTHER term, go
     to the course's term (keeping the rest of the address) and return true;
     otherwise return false and let the caller refresh in place. An import
     into a term other than the one on screen used to "succeed" and leave the
     reader looking at a list without the course in it. */
  GP.followPeriod = function (academicYear, semester) {
    const sel = pageSelector();
    if (!sel || !academicYear || !semester) return false;
    const key = periodKey(academicYear, semester);
    const shown = sel.dataset.periodSelected || '';
    if (!shown || shown === key || shown === (sel.dataset.periodAll || 'all')) return false;
    GP.skipBeforeunload();
    window.location.href = urlForPeriod(key);
    return true;
  };

  /* -- Remembering the pick --------------------------------------------
     The way the interface language is remembered (locale-sync.js): the pick
     lives in localStorage, and a cookie mirrors it so the SERVER can draw the
     page already scoped - read from localStorage alone, the page would first
     render the default term and then jump. The value carries the calendar's
     term at the moment of the pick; once a new term starts the pick has
     lapsed (the server ignores it, and so is it cleared here), and the pages
     follow the calendar again. See services/academic_periods.requested_period. */
  const STORE_KEY = 'gp_period';

  function writeCookie(value) {
    document.cookie = STORE_KEY + '=' + (value ? encodeURIComponent(value) : '')
      + '; Max-Age=' + (value ? 31536000 : 0) + '; Path=/; SameSite=Lax';
  }

  function rememberPeriod(key, currentKey) {
    if (memoryOff()) { forgetPeriod(); return; }
    const value = key + '~' + (currentKey || '');
    try { window.localStorage.setItem(STORE_KEY, value); } catch (_) { /* private mode */ }
    writeCookie(value);
  }

  /* Preferences > Behavior > "Default period": only "The period I picked
     last" keeps a pick. With any other default nothing is stored, and what an
     earlier visit stored is forgotten - every page opens on that default. */
  function memoryOff() {
    return (document.documentElement.getAttribute('data-period-default') || 'remembered') !== 'remembered';
  }

  function forgetPeriod() {
    try { window.localStorage.removeItem(STORE_KEY); } catch (_) { /* ignore */ }
    if (Cookies.getInitial(STORE_KEY)) writeCookie('');
  }

  function reconcileRemembered() {
    if (memoryOff()) { forgetPeriod(); return; }
    const sel = pageSelector();
    let stored = '';
    try { stored = window.localStorage.getItem(STORE_KEY) || ''; } catch (_) { return; }
    if (!stored) return;
    const current = sel && sel.dataset.periodCurrent;
    if (current && stored.split('~')[1] !== current) {
      // A pick from an earlier term: gone, here and on the server.
      try { window.localStorage.removeItem(STORE_KEY); } catch (_) { /* ignore */ }
      writeCookie('');
      return;
    }
    if (!Cookies.getInitial(STORE_KEY)) writeCookie(stored);
  }

  /* The selector's links, rebuilt from the LIVE address at click time (capture
     phase, so the SPA navigator reading the href afterwards sees the new one). */
  function refreshSelectorLinks(root) {
    (root || document).querySelectorAll('[data-period-selector] a[data-period-key]').forEach(function (a) {
      a.setAttribute('href', urlForPeriod(a.dataset.periodKey));
    });
  }
  document.addEventListener('click', function (e) {
    const target = e.target && e.target.closest ? e.target : null;
    if (!target) return;
    const link = target.closest('[data-period-selector] a[data-period-key]');
    if (link) {
      link.setAttribute('href', urlForPeriod(link.dataset.periodKey));
      const sel = link.closest('[data-period-selector]');
      rememberPeriod(link.dataset.periodKey, sel && sel.dataset.periodCurrent);
      /* The box says the pick AT ONCE, the way a select does. It kept the old
         term until the page landed, so the choice looked undone while it
         loaded. Not for a click that opens a new tab: this page stays. */
      if (sel && e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) {
        const text = sel.querySelector('.gl-form-dropdown-text');
        const title = link.querySelector('.gl-dropdown-item-title');
        if (text && title) text.textContent = title.textContent.trim();
        sel.querySelectorAll('a[aria-selected]').forEach(function (a) { a.removeAttribute('aria-selected'); });
        link.setAttribute('aria-selected', 'true');
      }
      return;
    }
    const toggle = target.closest('[data-period-selector] [data-dropdown-toggle]');
    if (toggle) refreshSelectorLinks(toggle.closest('[data-period-selector]'));
  }, true);

  /* ------------------------------------- the period-and-dates fields */

  const ROLES = ['period', 'year', 'semester', 'start', 'end'];
  const GAP_LOOKAHEAD_DAYS = 120;

  function readJSON(el, attr, fallback) {
    try { return JSON.parse(el.getAttribute(attr) || ''); } catch (_) { return fallback; }
  }

  function addDays(iso, days) {
    const d = new Date(iso + 'T00:00:00Z');
    d.setUTCDate(d.getUTCDate() + days);
    return d.toISOString().slice(0, 10);
  }

  function parseKey(key) {
    const m = /^(\d{4})-(\d{4})-(winter|summer)$/.exec(String(key || ''));
    return m ? { academic_year: m[1] + '/' + m[2], semester: m[3] } : null;
  }

  /* The term a date belongs to. The same three steps as
     app.utils.academic_period.period_of_date, in the same order: the term
     containing it (the later-starting one where two overlap), else the term
     starting within 120 days, else the shape of the TUKE year. ISO dates
     compare correctly as strings. */
  function periodOfDate(windows, iso) {
    const containing = windows.filter(function (w) { return w.start <= iso && iso <= w.end; });
    if (containing.length) {
      const w = containing.reduce(function (a, b) { return b.start > a.start ? b : a; });
      return { academic_year: w.academic_year, semester: w.semester };
    }
    const horizon = addDays(iso, GAP_LOOKAHEAD_DAYS);
    const upcoming = windows.filter(function (w) { return w.start > iso && w.start <= horizon; });
    if (upcoming.length) {
      const w = upcoming.reduce(function (a, b) { return b.start < a.start ? b : a; });
      return { academic_year: w.academic_year, semester: w.semester };
    }
    const y = parseInt(iso.slice(0, 4), 10);
    const m = parseInt(iso.slice(5, 7), 10);
    if (m === 7 || m === 8) return { academic_year: y + '/' + (y + 1), semester: 'winter' };
    const startYear = m >= 8 ? y : y - 1;
    return {
      academic_year: startYear + '/' + (startYear + 1),
      semester: (m >= 2 && m <= 6) ? 'summer' : 'winter',
    };
  }
  GP.periodOfDate = periodOfDate;

  /* Set a field the way a person would have, so every listener (Alpine
     selects, the date picker's week column, the save guard) sees it. A select
     here is glFormSelect's hidden input: its value setter updates the control
     and announces the change itself. */
  function setField(el, value) {
    if (!el) return;
    const v = value == null ? '' : String(value);
    if (el.value === v) return;
    if (el._flatpickr) {
      if (v) el._flatpickr.setDate(v, false);
      else el._flatpickr.clear(false);
    }
    el.value = v;
    if (el.type !== 'hidden') {
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  function bind(scope) {
    if (!scope || scope.__gpPeriodFields) return scope && scope.__gpPeriodFields;
    const roles = readJSON(scope, 'data-period-roles', {});
    const windows = readJSON(scope, 'data-period-windows', []);
    const el = {};
    ROLES.forEach(function (r) {
      el[r] = roles[r] ? scope.querySelector('#' + CSS.escape(roles[r])) : null;
    });
    const hintWrap = scope.querySelector('[data-period-hint-wrap]');
    const hint = scope.querySelector('[data-period-hint]');
    const officialBtn = scope.querySelector('[data-period-official]');
    const emptyHint = scope.getAttribute('data-period-empty-hint') || '';

    const api = {
      scope: scope,
      el: el,
      windows: windows,
      /* Do the dates follow the calendar? True while they are empty or are the
         official dates of the term; false once the teacher types their own. */
      auto: true,
      applying: false,
      /* The term the dates were last settled for. The select is glFormSelect,
         which announces a change asynchronously; comparing against this -
         rather than trusting the event - keeps a term WE set (a course loaded
         into Edit) from being treated as the reader moving the course. */
      settled: '',
    };

    const val = function (r) { return (el[r] && el[r].value) || ''; };
    const term = function () { return { academic_year: val('year'), semester: val('semester') }; };
    const windowOf = function (p) {
      return windows.find(function (w) { return w.academic_year === p.academic_year && w.semester === p.semester; }) || null;
    };
    const datesAreOfficial = function (w) {
      return !!w && val('start') === w.start && val('end') === w.end;
    };

    function applyDates(start, end) {
      api.applying = true;
      try { setField(el.start, start); setField(el.end, end); } finally { api.applying = false; }
    }

    function render() {
      const p = term();
      const w = windowOf(p);
      const start = val('start');
      const end = val('end');
      let msg = '';
      let warn = false;
      if (start && end && end <= start) {
        msg = t('The semester end date must be after its start date.');
        warn = true;
      } else if (start && p.academic_year && p.semester) {
        const of = periodOfDate(windows, start);
        if (of.academic_year !== p.academic_year || of.semester !== p.semester) {
          msg = t('The start date falls in {period}, but the course is set to {course}.')
            .replace('{period}', periodLabel(of.academic_year, of.semester))
            .replace('{course}', periodLabel(p.academic_year, p.semester));
          warn = true;
        }
      }
      if (!msg && !start && !end && emptyHint) msg = emptyHint;
      if (!msg && !w && p.academic_year && p.semester && !start && !end) {
        msg = t('The TUKE calendar for {period} is not published yet - enter the dates when it is, or leave them empty.')
          .replace('{period}', periodLabel(p.academic_year, p.semester));
      }
      const offerOfficial = !!w && !datesAreOfficial(w);
      if (officialBtn) {
        officialBtn.hidden = !offerOfficial;
        if (offerOfficial) {
          officialBtn.textContent = t('Use the official TUKE dates') + ' (' + w.start + ' – ' + w.end + ')';
        }
      }
      if (hint) {
        hint.textContent = msg;
        hint.hidden = !msg;
        hint.classList.toggle('is-warning', warn);
      }
      if (hintWrap) hintWrap.hidden = !msg && !offerOfficial;
    }

    /* The term changed - by the reader in the select, or by us. */
    function onPeriodChange() {
      const picked = parseKey(val('period'));
      if (picked) {
        setField(el.year, picked.academic_year);
        setField(el.semester, picked.semester);
      }
      const now = periodKey(val('year'), val('semester'));
      if (now !== api.settled) {
        api.settled = now;
        if (api.auto) {
          const w = windowOf(term());
          applyDates(w ? w.start : '', w ? w.end : '');
        }
      }
      render();
    }

    function onDateChange() {
      if (api.applying) return;
      api.auto = (!val('start') && !val('end')) || datesAreOfficial(windowOf(term()));
      render();
    }

    scope.addEventListener('change', function (e) {
      const target = e.target;
      if (target === el.period) onPeriodChange();
      else if (target === el.start || target === el.end) onDateChange();
    });
    ['start', 'end'].forEach(function (r) {
      if (el[r]) el[r].addEventListener('input', function () { if (!api.applying) render(); });
    });
    if (officialBtn) {
      officialBtn.addEventListener('click', function () {
        const w = windowOf(term());
        if (!w) return;
        api.auto = true;
        applyDates(w.start, w.end);
        render();
      });
    }

    /* Recompute from what the fields hold now - after they were filled from
       outside. */
    api.reset = function () {
      api.auto = (!val('start') && !val('end')) || datesAreOfficial(windowOf(term()));
      api.settled = periodKey(val('year'), val('semester'));
      render();
    };

    /* Load a course into the fields: its term and its own dates. A term the
       select does not list (an old course) is added to it first, labelled like
       every other, rather than shown as a raw key. */
    api.fill = function (values) {
      values = values || {};
      const year = values.academic_year || '';
      const semester = values.semester || '';
      const key = year && semester ? periodKey(year, semester) : '';
      if (key && el.period && typeof el.period.addOptions === 'function') {
        el.period.addOptions([[key, periodLabel(year, semester)]]);
      }
      setField(el.year, year);
      setField(el.semester, semester);
      api.settled = key;
      setField(el.period, key);
      applyDates(values.start || '', values.end || '');
      api.reset();
    };

    scope.__gpPeriodFields = api;
    api.reset();
    return api;
  }

  function bindAll(root) {
    (root || document).querySelectorAll('[data-period-fields]').forEach(bind);
  }

  GP.periodFields = {
    bind: bind,
    bindAll: bindAll,
    /* The fields inside (or around) `node` - a form, a modal or the wrapper. */
    of: function (node) {
      if (!node) return null;
      const scope = node.matches && node.matches('[data-period-fields]')
        ? node
        : (node.querySelector && node.querySelector('[data-period-fields]'))
          || (node.closest && node.closest('[data-period-fields]'));
      return scope ? bind(scope) : null;
    },
  };

  function boot() {
    bindAll(document);
    reconcileRemembered();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  /* A swap can bring new fields (lazy content, SPA navigation); modals are
     teleported out of the swapped subtree, so look at the whole document -
     there are a handful of these elements at most. */
  document.addEventListener('htmx:afterSwap', function () { bindAll(document); });
})();
