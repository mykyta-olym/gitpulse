function initFlatpickr(selector, options = {}) {
  if (typeof window.flatpickr !== 'function') {
    return;
  }
  // Semester context. Course pages expose it as <meta>; the create-course /
  // settings modals have no course yet, so the semester start/end date fields
  // anchor to their own live value instead (see resolveAnchor below).
  const metaContent = function (name) {
    const m = document.querySelector('meta[name="' + name + '"]');
    return m ? m.getAttribute('content') : null;
  };
  const metaStart = metaContent('semester-start');
  const defaultTeachingWeeks = parseInt(metaContent('semester-weeks') || '', 10) || 13;

  document.querySelectorAll(selector).forEach((el) => {
    try {
      if (el._flatpickr || el.closest('[x-ignore]')) {
        return;
      }
      const fieldKey = (el.name || el.id || '').toLowerCase();
      const isStartField =
        fieldKey.indexOf('semester_start') !== -1 ||
        fieldKey.indexOf('semesterstart') !== -1 ||
        el.dataset.semesterAnchor === 'self';
      const isEndField =
        fieldKey.indexOf('semester_end') !== -1 || fieldKey.indexOf('semesterend') !== -1;
      const teachingWeeks = parseInt(el.dataset.semesterWeeks, 10) || defaultTeachingWeeks;

      // The semester start this field's week column numbers from, resolved LIVE
      // so the create-course pickers renumber as a date is chosen. Priority:
      // explicit data attr > the start field's own value > a sibling start
      // field (for the end field) > the course <meta>.
      const resolveAnchor = function () {
        if (el.dataset.semesterStart) {
          return el.dataset.semesterStart;
        }
        if (isStartField && el.value) {
          return el.value;
        }
        if (isEndField) {
          // Period groups also live in form-less modals (e.g. Transfer).
          // Prefer this pair's wrapper when one form contains multiple periods.
          const scope = el.closest('[data-period-fields]') || el.form || el.closest('form');
          const sib = scope
            ? scope.querySelector('[name*="semester_start"], [id*="emesterStart"]')
            : null;
          if (sib && sib.value) {
            return sib.value;
          }
        }
        return metaStart;
      };

      // Standard ISO-8601 week number - the neutral fallback when there is no
      // semester anchor yet (e.g. the create-course modal before a start date is
      // picked), so the Wk column is never a blank, broken-looking column.
      const isoWeek = function (date) {
        const t = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const day = t.getUTCDay() || 7;
        t.setUTCDate(t.getUTCDate() + 4 - day);
        const yearStart = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
        return String(Math.ceil(((t - yearStart) / 86400000 + 1) / 7));
      };

      // Semester week label: teaching weeks are plain numbers (1..N), the exam
      // period ("skuskove obdobie") that follows is S1, S2, ...; dates before
      // the semester get a blank cell. With no anchor at all we fall back to the
      // ISO week number so the column always means something.
      const semesterWeekLabel = function (date) {
        const anchor = resolveAnchor();
        if (!anchor) {
          return isoWeek(date);
        }
        // Semester dates are local calendar days, not UTC timestamps.
        const start = window.flatpickr.parseDate(anchor, 'Y-m-d');
        if (!start) {
          return '';
        }
        const startUTC = Date.UTC(start.getFullYear(), start.getMonth(), start.getDate());
        const dateUTC = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate());
        const startDay = new Date(startUTC).getUTCDay() || 7;
        const startMondayUTC = startUTC - (startDay - 1) * 86400000;
        const dateDay = new Date(dateUTC).getUTCDay() || 7;
        const dateMondayUTC = dateUTC - (dateDay - 1) * 86400000;
        const weekNum = Math.floor(Math.round((dateMondayUTC - startMondayUTC) / 86400000) / 7) + 1;
        if (weekNum < 1) {
          /* Before the semester starts. This used to return '' and the whole
             column went blank - open the picker on any month before the start
             date and you get a "Wk" header over six empty cells, which reads as
             a broken calendar rather than as "these weeks are outside the
             semester". The ISO week is the honest answer here, and it is what
             the fallback above already does when there is no anchor at all. */
          return isoWeek(date);
        }
        if (weekNum <= teachingWeeks) {
          return String(weekNum);
        }
        return 'S' + (weekNum - teachingWeeks);
      };

      // Show the Wk column only when it is meaningful (a semester anchor exists
      // or can be derived from this field). Otherwise the ISO-week numbers
      // (W9..W14) are just noise on a plain date field.
      const showWeeks = isStartField || isEndField || !!resolveAnchor();

      window.flatpickr(el, {
        dateFormat: 'Y-m-d',
        weekNumbers: showWeeks,
        // 'static' renders the month as a styled text label with arrow nav
        // instead of an unstyled native <select>, matching the app's theme.
        monthSelectorType: 'static',
        // Month arrows are GlDatepicker's: @gitlab/ui $gl-icon-chevron-left /
        // $gl-icon-chevron-right, not flatpickr's own thin chevrons.
        prevArrow: '<svg viewBox="0 0 16 16" aria-hidden="true"><path fill-rule="evenodd" d="M5.293 7.293a1 1 0 0 0 0 1.414l3 3a1 1 0 0 0 1.414-1.414L7.414 8l2.293-2.293a1 1 0 0 0-1.414-1.414l-3 3z"/></svg>',
        nextArrow: '<svg viewBox="0 0 16 16" aria-hidden="true"><path fill-rule="evenodd" d="M10.707 7.293a1 1 0 0 1 0 1.414l-3 3a1 1 0 0 1-1.414-1.414L8.586 8 6.293 5.707a1 1 0 0 1 1.414-1.414l3 3z"/></svg>',
        locale: { firstDayOfWeek: firstDayOfWeek() },
        allowInput: true,
        // Old desktop offsets can expand a phone's layout viewport as soon as
        // the popup opens. Clear them before Flatpickr measures that viewport.
        onPreCalendarPosition: function (selectedDates, dateStr, instance) {
          instance.calendarContainer.style.left = '0px';
          instance.calendarContainer.style.right = 'auto';
        },
        // Flatpickr injects nameless helper inputs (hour / minute / year),
        // flagged by browsers as "form field should have an id or name".
        // Give each a stable id + aria-label so the page stays clean.
        onReady: function (selectedDates, dateStr, instance) {
          // The popup lives outside the form. Forward user intent before
          // Flatpickr changes the input through synthetic input/change events.
          ['click', 'keydown', 'input', 'change'].forEach(function (type) {
            instance.calendarContainer?.addEventListener(type, function (event) {
              if (event.isTrusted) instance.input.dispatchEvent(new Event('gp:user-edit', { bubbles: true }));
            }, true);
          });
          try {
            const base = (instance.input && instance.input.id) || 'fp';
            const labels = { 'flatpickr-hour': 'Hour', 'flatpickr-minute': 'Minute', 'cur-year': 'Year' };
            instance.calendarContainer
              .querySelectorAll('input:not([id]):not([name])')
              .forEach(function (inp, i) {
                inp.id = base + '-fp-' + i;
                if (!inp.getAttribute('aria-label')) {
                  let lbl = 'Date';
                  Object.keys(labels).forEach(function (cls) { if (inp.classList.contains(cls)) lbl = labels[cls]; });
                  inp.setAttribute('aria-label', lbl);
                }
              });
          } catch (_e) { /* non-fatal */ }
        },
        getWeek: semesterWeekLabel,
        // An empty deadline field opens on the CURRENT month, which outside term
        // time is entirely before the semester - so every cell of the week column
        // is blank and the calendar looks like it has no week numbers at all
        // (the "the picker should show semester weeks" report). Start on the
        // semester instead, where the numbers mean something. Only for fields
        // that read the anchor; the start/end fields ARE the anchor.
        onOpen: function (selectedDates, dateStr, instance) {
          if (isStartField || isEndField) return;
          if (selectedDates && selectedDates.length) return;
          const anchor = resolveAnchor();
          if (!anchor) return;
          const start = window.flatpickr.parseDate(anchor, 'Y-m-d');
          if (!start || start <= new Date()) return;
          try {
            instance.jumpToDate(start, true);
          } catch (_e) {
            /* non-fatal */
          }
        },
        onChange: function (selectedDates, dateStr, instance) {
          // Picking a semester start/end date shifts every week label, so
          // redraw the visible month to renumber it live.
          if (isStartField || isEndField) {
            try {
              instance.redraw();
            } catch (_e) {
              /* non-fatal */
            }
          }
        },
        ...options,
      });
    } catch (err) {
      console.warn('Flatpickr init failed for element:', el, err);
    }
  });
}

function initDateTimePicker(selector, options = {}) {
  initFlatpickr(selector, {
    enableTime: true,
    dateFormat: 'Y-m-d H:i',
    time_24hr: true,
    ...options,
  });
}

/* System-wide date-input upgrade: every date field rendered through the shared
   macros (.datetime-picker = date+time, .date-picker = date-only) gets the same
   themed, semester-week-aware Flatpickr - automatically, on first paint AND on
   every HTMX swap - so no page has to wire its own picker and none are left as
   raw inputs. Idempotent: initFlatpickr skips elements that already have one. */
function initDatePickers(root) {
  const scope = root && root.querySelectorAll ? root : document;
  // Progressive enhancement: promote ANY raw native date / datetime-local input
  // anywhere in the app to the shared themed, semester-week-aware calendar.
  // Convert to type=text first (Flatpickr keeps the same Y-m-d / Y-m-d H:i wire
  // value) and tag it with the picker class so the class-based init below wires
  // it. Idempotent: an upgraded input is type=text + already has the class, so
  // it is not re-matched, and initFlatpickr skips elements that already have one.
  scope
    .querySelectorAll(
      'input[type="date"]:not(.date-picker), input[type="datetime-local"]:not(.datetime-picker)'
    )
    .forEach((el) => {
      const withTime = el.getAttribute('type') === 'datetime-local';
      el.setAttribute('type', 'text');
      el.classList.add(withTime ? 'datetime-picker' : 'date-picker');
    });
  initDateTimePicker('.datetime-picker');
  initFlatpickr('.date-picker');
}
window.GP.initDatePickers = initDatePickers;

// HTMX cleans each outgoing element before removing it. Destroy the picker,
// including its body-mounted popup and document/window event listeners.
document.body.addEventListener('htmx:beforeCleanupElement', function (event) {
  event.detail?.elt?._flatpickr?.destroy();
});

// Flatpickr handles window resize; its body-mounted popup also needs to follow
// inputs inside scrolling pages and modal bodies. Reuse the pinned vendor's
// positioning helper instead of maintaining another geometry implementation.
document.addEventListener('scroll', function (event) {
  document.querySelectorAll('.flatpickr-input').forEach(function (input) {
    const picker = input._flatpickr;
    if (picker?.isOpen && event.target?.contains?.(input)) picker._positionCalendar();
  });
}, { capture: true, passive: true });

// A popup left open across a width change can itself enlarge the mobile
// viewport before the vendor repositions it. Keep the date and reopen cleanly.
// Height-only changes from a phone keyboard do not dismiss the calendar.
let _datepickerViewportWidth = document.documentElement.clientWidth;
window.addEventListener('resize', function () {
  const width = document.documentElement.clientWidth;
  if (width === _datepickerViewportWidth) return;
  _datepickerViewportWidth = width;
  document.querySelectorAll('.flatpickr-input').forEach(function (input) {
    const picker = input._flatpickr;
    if (!picker?.isOpen) return;
    if (picker.calendarContainer.contains(document.activeElement)) input.focus({ preventScroll: true });
    picker.close();
  });
}, { passive: true });
