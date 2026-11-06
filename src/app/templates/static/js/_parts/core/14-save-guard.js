/* ============================================
   Save-button guard - disable submit until form is dirty
   ============================================ */

const _saveGuardRegistry = {};

/**
 * Snapshot all form field values inside a container.
 * Skips descendants that belong to a nested modal or a different
 * form, so an inline-rendered modal does not pollute the parent form's
 * dirty-state snapshot (e.g. webhookConfigEditModal lives inside
 * #courseSettingsForm but its inputs must NOT enable Save Settings).
 * @param {HTMLElement} container
 * @returns {Object} key->value map
 */
function _snapshotFormFields(container) {
  const snap = {};
  container.querySelectorAll('input, select, textarea').forEach(function (el) {
    const key = el.type === 'checkbox' && el.name
      ? el.name + ':' + (el.id || el.value) : el.name || el.id;
    if (!key || el.hasAttribute('data-dirty-ignore')) return;
    // Skip fields that belong to a nested modal.
    if (el.closest('.modal-backdrop')) return;
    // Skip fields that belong to a different form than the container
    // (when the container is itself a form).
    if (container.tagName === 'FORM') {
      const ownerForm = el.form || el.closest('form');
      if (ownerForm && ownerForm !== container) return;
    }
    if (el.type === 'radio') {
      /* A radio GROUP shares one name, so keying on `checked` made the snapshot
         hold whichever button happened to come LAST - normally unchecked, and
         still unchecked after the reader picks a different option. The value
         never changed, so the Save button never armed: picking an accent, a
         layout width, a syntax scheme or a time format all looked like no edit
         at all. Record the SELECTED VALUE, which is what a group actually has. */
      if (el.checked) snap[key] = el.value;
      else if (!(key in snap)) snap[key] = '';
    } else if (el.type === 'checkbox') {
      snap[key] = el.checked;
    } else {
      snap[key] = el.value;
    }
  });
  return snap;
}

/**
 * Check if form has changed relative to snapshot.
 * @param {HTMLElement} container
 * @param {Object} snap - snapshot from _snapshotFormFields
 * @returns {boolean}
 */
function _isFormDirtyGuard(container, snap) {
  if (!snap) return true;
  const current = _snapshotFormFields(container);
  const keys = new Set(Object.keys(snap).concat(Object.keys(current)));
  for (const k of keys) {
    if (String(snap[k] ?? '') !== String(current[k] ?? '')) return true;
  }
  return false;
}

/**
 * Initialise save-button guard for a standard HTML form.
 * Disables the save button initially and enables it when form content changes.
 *
 * @param {string} formSelector - CSS selector for the form element
 * @param {string} btnSelector  - CSS selector for the save button
 * @param {Object} [opts]
 * @param {string} [opts.dirtyKey] - key for addDirtyReason / clearDirtyReason
 */
function initSaveGuard(formSelector, btnSelector, opts) {
  const _opts = opts || {};
  const dirtyKey = _opts.dirtyKey || btnSelector;
  const form = document.querySelector(formSelector);
  const btn = document.querySelector(btnSelector);
  if (!form || !btn) return;

  btn.disabled = true;
  btn.classList.add('btn-save-guard');
  form.dataset.saveGuard = '1';

  /* A disabled control has to say why - the app's own rule, and the reason the
     guard reads as "the button is broken" otherwise. Both guarded forms broke
     it: #btnSaveTeachers and #btnSaveSettings were the only disabled controls
     in the app with no reason attached. Set here, in the one place that owns
     the disabling, rather than per form. */
  const _whyDisabled = _opts.disabledReason
    || GP.t('Change something first - there is nothing to save yet.');
  function _explain(disabled) {
    if (disabled) {
      if (typeof GP.setDisabledReason === 'function') GP.setDisabledReason(btn, _whyDisabled);
    } else if (typeof GP.clearDisabledReason === 'function') {
      GP.clearDisabledReason(btn);
    }
  }
  _explain(true);

  // Snapshot SYNCHRONOUSLY. `_isFormDirtyGuard` treats a missing snapshot as
  // "dirty", so taking the first one in a timeout meant every event fired
  // before it landed evaluated against `undefined` and armed the button. That
  // is the "Save changes flashes enabled for a moment when a modal opens"
  // flicker: opening a modal initialises its guard and populates its fields in
  // the same tick, so the population events hit the empty-snapshot window.
  let snap = _snapshotFormFields(form);
  let submitted = null;
  let userEdited = false;
  _trackFormUserEdits(form, () => { userEdited = true; });

  // Alpine's gl-dropdown components bind their initial value silently (they
  // assign, they do not always emit), so re-baseline once after boot - but only
  // while the user has not interacted with a field or custom control.
  const _SETTLE_MS = 600;
  const settleUntil = Date.now() + _SETTLE_MS;
  setTimeout(function () {
    if (!userEdited) snap = _snapshotFormFields(form);
  }, _SETTLE_MS);

  function check(event) {
    if (!form.isConnected) return;
    // Async initialisation dispatches SYNTHETIC events (Alpine re-emitting a
    // bound value, page JS filling a modal). Only untouched forms may adopt
    // these as setup: date pickers, dropdowns and steppers also emit synthetic
    // events for real edits, as can follow-up formatting after native input.
    if (event && !event.isTrusted && !userEdited && Date.now() < settleUntil) {
      snap = _snapshotFormFields(form);
      btn.disabled = true;
      _explain(true);
      clearDirtyReason(dirtyKey);
      return;
    }
    const dirty = _isFormDirtyGuard(form, snap);
    const locked = btn._loadingArmed || btn.classList.contains('loading')
      || ['archivedLocked', 'processLocked', 'syncLocked', 'cooldownActive']
        .some(key => btn.dataset[key] === '1');
    btn.disabled = !dirty || !!locked;
    if (!locked) _explain(!dirty);
    if (dirty) {
      addDirtyReason(dirtyKey);
    } else {
      clearDirtyReason(dirtyKey);
    }
  }

  form.addEventListener('input', check);
  form.addEventListener('change', check);

  /* For non-AJAX forms: re-snapshot after submit.
     `defaultPrevented` has to be read INSIDE the timeout. Listeners run in
     registration order and the guard is initialised BEFORE the page's own
     submit handler, so at dispatch time an AJAX form has not called
     preventDefault() yet - reading it here treated every AJAX form as a full
     page submit and re-baselined it 200ms later regardless of what the server
     said. On a save that FAILED that was destructive twice over: the pending
     edits were recorded as the new pristine state, so Save greyed out with the
     changes still unsaved and the unsaved-changes warning was withdrawn. */
  form.addEventListener('submit', function (e) {
    // The response acknowledges these values, not edits made while it waits.
    if (!btn._loadingArmed && !btn.classList.contains('loading')) {
      submitted = _snapshotFormFields(form);
    }
    setTimeout(function () {
      if (e.defaultPrevented || !form.isConnected) return;
      snap = submitted || _snapshotFormFields(form);
      submitted = null;
      check();
    }, 200);
  });

  // Store for programmatic reset (AJAX forms call resetSaveGuard after save)
  _saveGuardRegistry[formSelector] = {
    form: form,
    btn: btn,
    /* Re-derive the button from the form, without touching the baseline. A save
       that FAILED changed nothing, so the answer is "still dirty, arm it". */
    recheck: function () { check(); },
    reset: function () {
      snap = submitted || _snapshotFormFields(form);
      submitted = null;
      check();
    }
  };
}

/**
 * Acknowledge the last submitted fields after a successful AJAX save.
 * Later edits remain dirty. The owner prevents resetting a replacement form.
 *
 * @param {string} formSelector - same selector passed to initSaveGuard
 * @param {HTMLFormElement} [ownerForm] - form that submitted the request
 */
function resetSaveGuard(formSelector, ownerForm) {
  const guard = _saveGuardRegistry[formSelector];
  if (guard && (!ownerForm || guard.form === ownerForm)) guard.reset();
}

/**
 * Re-evaluate the guard that owns this button, if any.
 *
 * A guarded Save is deliberately the one control a loading reset will not
 * re-enable (`btn-save-guard`, `_applyButtonLoadingReset`): the guard owns that
 * state, so a finished save cannot be allowed to arm a button with nothing left
 * to save. The cost was that a save which FAILED left the button disabled for
 * good - the form was still dirty, but nothing ever asked the guard again, so
 * the user could not retry and their edits were stranded on the page.
 *
 * @param {Element} btn - the button that just reported an outcome
 */
function recheckSaveGuardFor(btn) {
  if (!btn) return;
  for (const key of Object.keys(_saveGuardRegistry)) {
    const guard = _saveGuardRegistry[key];
    if (guard && guard.btn === btn && typeof guard.recheck === 'function') {
      guard.recheck();
      return;
    }
  }
}

GP.initSaveGuard = initSaveGuard;
GP.resetSaveGuard = resetSaveGuard;
GP.recheckSaveGuardFor = recheckSaveGuardFor;
