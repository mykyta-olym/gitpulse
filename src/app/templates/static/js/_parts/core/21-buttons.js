/* Disable and announce pending work immediately. Only the spinner is delayed;
   completion never waits for a decorative loading minimum. */
/* Use a monotonic clock to expire the button's association with an action. */
function _now() {
  return typeof performance !== 'undefined' && performance.now
    ? performance.now()
    : Date.now();
}

/* Releasing one temporary lock must preserve the other owners. Once they all
   finish, a Save follows the current draft, rather than its pre-lock state. */
function refreshButtonDisabledState(btn, wasDisabled = false) {
  if (!btn) return;
  const locked = btn._loadingArmed || btn.classList.contains('loading')
    || ['archivedLocked', 'processLocked', 'syncLocked', 'cooldownActive']
      .some(key => btn.dataset[key] === '1');
  if (locked) {
    btn.disabled = true;
    btn.classList.add('is-disabled');
    btn.setAttribute('aria-disabled', 'true');
    return;
  }
  btn.classList.remove('is-disabled');
  btn.removeAttribute('aria-disabled');
  if (btn.classList.contains('btn-save-guard')) {
    GP.recheckSaveGuardFor(btn);
  } else {
    btn.disabled = wasDisabled;
  }
}
GP.refreshButtonDisabledState = refreshButtonDisabledState;

/* ============================================
   The loading chrome
   ============================================
   A loading button keeps its label and its box; a spinner takes the LEADING
   ICON's place. That is GlButton's own contract (@gitlab/ui 136.2.0
   src/components/base/button/button.vue:418-421):

     <gl-loading-icon v-if="loading" inline class="gl-button-icon ..." />
     <gl-icon v-if="hasIcon && !(hasIconOnly && loading)" class="gl-button-icon" />
     <span v-if="!hasIconOnly" class="gl-button-text"><slot/></span>

   - the label is never touched, and the icon is only dropped when the button is
   icon-only (i.e. when the spinner is standing in for it).

   What was here before replaced `innerHTML` with a loading label, or - with no
   label to show - let CSS set `color: transparent`, hide every child and drop
   the button to `opacity: .7`. A "Reload" button became an empty washed-out box
   with a spinner in it, which is the "buttons deform badly from their resting
   state" report. It also meant TWO loading mechanisms (`.loading` and
   `.btn-loading-text`) for one state; there is now one.

   Insert and teardown live in these two functions because THREE owners tear the
   state down - request completion, the done state, and the cooldown in
   process-action-guards.js - and each used to carry its own copy of the class
   list, which is how they drifted. */
/* Use the same spinner as block and table loading states. */
function _buttonSpinner(btn) {
  return btn.querySelector(':scope > .gp-spinner');
}

/** Immediate, unconditional teardown of the loading chrome: pending timers, the
 *  class, aria-busy and the spinner element. Says nothing about `disabled` -
 *  that belongs to whoever is holding the button (reset / cooldown / lock). */
function clearButtonLoadingChrome(btn) {
  if (!btn) return;
  if (btn._loadingArmed) {
    clearTimeout(btn._loadingArmed);
    btn._loadingArmed = 0;
  }
  btn.classList.remove('loading');
  btn.removeAttribute('aria-busy');
  // The request ended; a retry must not inherit the click's fallback debounce.
  btn._gpClickLockUntil = 0;
  const spinner = _buttonSpinner(btn);
  if (spinner) spinner.remove();
}

function _applyButtonLoadingReset(btn) {
  clearButtonLoadingChrome(btn);
  // Use the process guard's own teardown; a loading reset must never cancel
  // a cooldown or discard the tooltip saved by that guard.
  if (btn.dataset.processLockActive === '1') GP.refreshProcessActionGuards?.();
  refreshButtonDisabledState(btn);
}

/* `loadingText` is gone on purpose. It was the second of two loading
   mechanisms - one swapped the label for "Checking..." while the other hid the
   label behind a spinner - so the same state looked different depending on which
   call site you clicked, and the text-swap variant resized the control (and with
   it the toolbar around it) every time. GitLab shows a spinner and keeps the
   label; that is now the only path. */
/* Preferences > Localization > "First day of the week". Flatpickr wants
   0=Sunday..6=Saturday; the calendar was pinned to Monday regardless, which is
   right for sk/en-GB but wrong for anyone who reads a week as starting Sunday.
   "system" keeps Monday, so an untouched account sees exactly what it did. */
function firstDayOfWeek() {
  const pref = document.documentElement.getAttribute('data-first-day');
  if (pref === 'sunday') return 0;
  if (pref === 'saturday') return 6;
  return 1; // 'monday' and 'system'
}

function setButtonLoading(btn, loading = true) {
  if (!btn) {
    return;
  }

  // A cooldown countdown owns the button while active - never let a loading
  // toggle restore/clobber it, or the
  // button freezes on the last painted "Wait Ns". The cooldown clears itself
  // and re-enables the button when it ends.
  if (btn.dataset.cooldownActive === '1') {
    return;
  }

  if (loading) {
    if (btn._loadingArmed || btn.classList.contains('loading')) return;
    _clearButtonOutcome(btn);
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    btn._loadingArmed = setTimeout(function () {
      btn._loadingArmed = 0;
      _paintButtonLoading(btn);
    }, _BUSY_DELAY_MS);
  } else {
    _setButtonLoadingState(btn, false);
  }
}

/** Paint the loading state. Split out so arming it can be deferred. */
function _paintButtonLoading(btn) {
  _setButtonLoadingState(btn, true);
}

function _setButtonLoadingState(btn, loading) {
  if (loading) {
    // A new click supersedes an outcome still on screen. Tear it down FIRST, so
    // the label it restores is the resting one, not "Done" / "Failed".
    _clearButtonOutcome(btn);
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');

    /* The spinner is a real element rather than a `::after`, so it can sit in
       the flex row where the leading icon was (CSS hides that icon while
       `.loading` is on) - which is what keeps the button exactly its resting
       width while it works. */
    if (!_buttonSpinner(btn)) {
      btn.insertAdjacentHTML('afterbegin', GP.renderSpinnerHtml('xs'));
    }
    btn.classList.add('loading');
    return;
  }

  // An outcome already consumed the pending state and owns its markup.
  if (!btn._outcomeTimer) _applyButtonLoadingReset(btn);
}

/* ============================================
   Outcome states
   ============================================
   Every action in this app owed the user three states and only ever shipped
   two: loading, then a toast. The toast says the SYSTEM did something; it never
   says THIS BUTTON finished. `setButtonDone` is the missing third state - the
   control that was clicked reports its own completion, in place, before going
   back to normal.

   A finish has two answers, and only one of them was painted. A button whose
   action FAILED said nothing at all: it came back to its resting label, and the
   toast in the corner was the only evidence anything had gone wrong. Worse, the
   pairing below was armed by a click and disarmed only by a success, so a
   failed action stayed on the hook - the next success toast from anywhere (a
   poll, a background sync, another widget) handed the button that had just
   failed a green tick. `setButtonError` is the same state with the other
   answer, and a failure now consumes the pairing exactly as a success does.

   It is deliberately ONE mechanism (see the "one pattern per interaction" rule):
   `_runDataAction` remembers which control started the current operation, and
   the toast - the signal every finished action already emits - hands that
   control its outcome. No call site has to opt in. */
const _DONE_VISIBLE_MS = 1600;
/* A failure has to be read, not merely noticed, so it stays a little longer
   than the confirmation does. */
const _ERROR_VISIBLE_MS = 2600;
let _activeActionButton = null;
let _activeActionButtonAt = 0;

/* Retire an outcome and put the button's resting label back. One teardown,
   shared by the timer that ends it and by a new click that supersedes it. */
function _clearButtonOutcome(btn) {
  if (!btn) return;
  if (!btn._outcomeTimer) return;
  clearTimeout(btn._outcomeTimer);
  btn._outcomeTimer = null;
  btn.classList.remove('btn-done', 'btn-error');
  btn.removeAttribute('aria-live');
  if (btn.dataset.outcomeRestore) {
    btn.innerHTML = btn.dataset.outcomeRestore;
    delete btn.dataset.outcomeRestore;
  }
  if (btn.dataset.outcomeLockedWidth === '1') {
    btn.style.minWidth = '';
    delete btn.dataset.outcomeLockedWidth;
  }
}

/* The two marks are the app's own icons for these two meanings - the tick, and
   `alert-triangle` from components/icons.html - so a button reports an outcome
   with the same symbol as everything else on the page. */
/* `icon` is a NAME into GP.icons, the app's one icon table - not a glyph
   inlined here. Both marks were already Pajamas, but a copied path is a copy
   that can drift, and the done mark had in fact drifted: a hand-drawn tick
   rather than the `check` every other confirmation in the product uses. */
const _OUTCOME = {
  done: {
    cls: 'btn-done',
    ms: _DONE_VISIBLE_MS,
    live: 'polite',
    word: 'Done',
    icon: 'check',
  },
  error: {
    cls: 'btn-error',
    ms: _ERROR_VISIBLE_MS,
    live: 'assertive',
    word: 'Failed',
    icon: 'alert-triangle',
  },
};

/* The two outcomes are ONE function. The handover from the loading state, the
   ownership rules and the teardown are identical - only the colour, the mark,
   the default word and how long it stays differ. Writing them as two separate
   routines is exactly how the app came to have a done state and no error state
   at all. */
function _setButtonOutcome(btn, kind, label) {
  if (!btn || btn.nodeType !== 1 || btn.dataset.cooldownActive === '1') return;
  // A form dropdown's label is its selected value, not an action caption.
  // Replacing its children would also detach Alpine's value binding.
  if (btn.closest('.gl-form-dropdown')) { _applyButtonLoadingReset(btn); return; }
  const spec = _OUTCOME[kind];
  if (!spec) return;

  // Clear pending timers and the spinner before snapshotting the resting label.
  _applyButtonLoadingReset(btn);

  if (btn._outcomeTimer) clearTimeout(btn._outcomeTimer);
  else if (!btn.dataset.outcomeRestore) {
    btn.dataset.outcomeRestore = btn.innerHTML;
    const rect = btn.getBoundingClientRect();
    if (rect.width > 0 && !btn.style.minWidth) {
      btn.dataset.outcomeLockedWidth = '1';
      btn.style.minWidth = Math.round(rect.width) + 'px';
    }
  }

  const text = label || _translateUiText(spec.word);
  /* An icon-only control has no room for the word: in a 24px square the label
     shrank to a 2px sliver of its first letter beside the mark, and pushed the
     mark off centre - the "strip on the right of the tick". The word stays in
     the accessible name only, at every width; a labelled button keeps it. */
  const _probe = document.createElement('div');
  _probe.innerHTML = btn.dataset.outcomeRestore || '';
  const labelClass = (_probe.textContent || '').trim()
    ? 'btn-outcome-label sr-only-sm'
    : 'btn-outcome-label sr-only';
  btn.classList.remove('btn-done', 'btn-error');
  btn.classList.add(spec.cls);
  btn.innerHTML = GP.icons.get(spec.icon, 16, 'icon btn-outcome-icon')
    + '<span class="' + labelClass + '">' + text + '</span>';
  btn.setAttribute('aria-live', spec.live);

  btn._outcomeTimer = setTimeout(function () { _clearButtonOutcome(btn); }, spec.ms);
}

function setButtonDone(btn, label) { _setButtonOutcome(btn, 'done', label); }
function setButtonError(btn, label) { _setButtonOutcome(btn, 'error', label); }

/* Called by showToast when an action ends. The pairing is time-boxed so a toast
   that arrives long after its click (a background job, another tab) never
   decorates an unrelated button the user has since moved on from - and it is
   consumed by EITHER answer, so a failure can no longer leave the button armed
   to collect whichever success happens along next. */
function _markActiveActionOutcome(kind) {
  if (!_activeActionButton) return;
  const btn = _activeActionButton;
  const startedAt = _activeActionButtonAt;
  _activeActionButton = null;
  if (_now() - startedAt > 30000) return;
  if (btn.isConnected) _setButtonOutcome(btn, kind);
}

GP.setButtonDone = setButtonDone;
GP.setButtonError = setButtonError;
/* For the cooldown in process-action-guards.js, which takes the button over
   right after a failure and must not snapshot the outcome as the label. */
GP.clearButtonOutcome = _clearButtonOutcome;
GP._markActiveActionDone = function () { _markActiveActionOutcome('done'); };
GP._markActiveActionFailed = function () { _markActiveActionOutcome('error'); };
/* A warning is neither answer: the action ended, but calling it a failure would
   overstate what happened. Release the pairing without painting anything - the
   button returns to rest, and cannot be handed a later, unrelated tick.
   (`_setButtonOutcome` has no spec for this kind, so nothing is drawn.) */
GP._releaseActiveAction = function (button) {
  if (!button || _activeActionButton === button) _markActiveActionOutcome(null);
};

/* ONE capture-phase listener owns "which control is the user waiting on". It has
   to be here rather than inside _runDataAction: Refresh, Sync and a pile of
   other buttons bind their own handlers and never route through [data-action],
   which is exactly why Refresh showed no done state. Capture phase so it still
   records the control when a handler stops propagation.

   Passive controls (tabs, filter pills) are excluded - they change a view, they
   do not complete an operation. */
document.addEventListener('click', function _rememberActionSource(event) {
  const el = event.target.closest('button, input[type="submit"], a.btn, .btn, [role="button"]');
  if (!el || el.disabled) return;
  if (el.closest('.gl-form-dropdown')) return;
  // GP's, not a bare name: the helper lives in process-action-guards.js's
  // closure, where a bare `isPassiveUiControl` never resolved.
  if (typeof GP.isPassiveUiControl === 'function' && GP.isPassiveUiControl(el)) return;
  if (el.closest('[data-modal-close], .modal-close, [data-dismiss]')) return;
  _activeActionButton = el;
  _activeActionButtonAt = _now();
  // A new press deserves fresh feedback even when it repeats the last message.
  GP.resetToastDedup();
}, true);

/* Brief success / error feedback flash on any button (component-level, used
   app-wide). Adds a one-shot animation class that self-clears. Reduced-motion
   is handled in CSS (the animation is disabled there), so it degrades cleanly. */
function flashButton(btn, type) {
  if (!btn || btn.nodeType !== 1) return;
  /* Success grows, failure shakes - the same two gestures the app uses for a
     badge that changed and an input that was rejected. As CSS classes this
     needed a force-reflow to replay, an `animationend` listener AND a 600 ms
     fallback that could both fire. */
  if (type === 'error') GP.motion.shake(btn);
  else GP.motion.pop(btn);
}
GP.flashButton = flashButton;

/* THE close button, in JS - the `close_button` macro (components/buttons.html),
   GitLab's CloseButton. `hookClass` is what code listens to or a surface
   places; it never decides how the button looks. `data` becomes data-*
   attributes, like the macro's `data_attrs`. */
function closeButtonHtml(label, hookClass, data) {
  const attrs = Object.keys(data || {}).map(function (k) {
    return ' data-' + k + '="' + escapeHtml(String(data[k])) + '"';
  }).join('');
  return '<button type="button" class="btn btn-icon-only btn-tertiary btn-sm btn-touch-target' +
    (hookClass ? ' ' + hookClass : '') + '" aria-label="' + escapeHtml(label || GP.t('Close')) + '"' + attrs + '>' +
    GP.iconSvg('x', 'sm') + '</button>';
}
GP.closeButtonHtml = closeButtonHtml;

/* JS mirror of btn / btn_icon. Text and attribute values are escaped here. */
function buttonHtml(text, opts = {}) {
  const classes = ['btn', opts.icon ? 'btn-icon' : '', 'btn-' + (opts.variant || 'primary'),
    opts.size === 'sm' ? 'btn-sm' : '', opts.class || ''].filter(Boolean).join(' ');
  const data = Object.entries(opts.data || {}).map(([key, value]) =>
    ' data-' + key + '="' + escapeHtml(String(value)) + '"').join('');
  const id = opts.id ? ' id="' + escapeHtml(opts.id) + '"' : '';
  const expanded = opts.expanded === undefined ? '' : ' aria-expanded="' + String(!!opts.expanded) + '"';
  return '<button class="' + escapeHtml(classes) + '" type="button"' + id + data + expanded + '>'
    + (opts.icon ? GP.iconSvg(opts.icon, 'sm') : '')
    + '<span class="btn-text">' + escapeHtml(String(text)) + '</span></button>';
}
GP.buttonHtml = buttonHtml;
