/* ============================================
   Modal System
   ============================================ */
const _modalState = {
  openStack: [],
  openVersion: 0,
};

function _refreshBodyScrollLock() {
  const hasOpenModal = document.querySelector('.modal-backdrop.active');
  // The body is already `overflow: hidden` and `.gl-page-content` keeps its
  // `scrollbar-gutter: stable` even under `overflow: hidden` (an overflow:hidden
  // box is still a scroll container per spec), so locking does NOT change the
  // content width - no scrollbar compensation needed.
  document.body.classList.toggle('scroll-locked', !!hasOpenModal);
}

function _getFocusableElements(container) {
  if (!container) {
    return [];
  }
  // Native controls also match the earlier selector branches when tabindex=-1.
  // Check every candidate, including disabled fieldsets and exiting inert menus.
  return Array.from(container.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )).filter((el) => el.tabIndex >= 0
    && !el.matches(':disabled')
    && !el.closest('[inert]')
    && el.offsetParent !== null);
}

/* Where focus lands when a modal opens: the first FIELD in its body, so a
   keyboard user starts typing; failing that the dialog itself (it carries
   tabindex=-1 so a screen reader announces the title). It used to land on the
   first focusable element in DOM order - the "x" in the header - so every
   modal opened with its close button highlighted, one Enter from closing. */
/* Does focusing this raise the on-screen keyboard? */
function _isTypable(el) {
  if (!el) return false;
  if (el.isContentEditable) return true;
  if (el.tagName === 'TEXTAREA') return true;
  if (el.tagName !== 'INPUT') return false;
  return ['checkbox', 'radio', 'button', 'submit', 'reset', 'file', 'range', 'color']
    .indexOf(el.type) === -1;
}

function _isTouchPointer() {
  try { return window.matchMedia('(pointer: coarse)').matches; } catch (_) { return false; }
}

function _focusFirstModalField(modalEl) {
  const modal = modalEl?.querySelector('.modal') || modalEl;
  const body = modal?.querySelector('.modal-body') || modal;
  const fields = _getFocusableElements(body).filter((el) =>
    !el.matches('[data-modal-close], .modal-close, a[href]'));
  let target = fields[0] || modal;
  if (!target) return;
  /* On a phone, focusing a text field raises the keyboard - over half the
     dialog, before the reader has decided to type anything. It happened on
     EVERY modal, including the ones with nothing to type into: Run Checks is
     tick-the-boxes-and-press-Run, and it opened with the keyboard up and its
     list of checks hidden behind it. Worse, a field that has focus collects
     whatever the keyboard then emits - a stray character, a predictive
     insertion - and closing the modal answers with "You have unsaved changes.
     Discard?" for something the reader never typed.
     Autofocus into a field is a hardware-keyboard affordance, so it is for
     hardware keyboards. On touch the dialog itself takes focus: Escape, the
     focus trap and the screen-reader announcement all still work. */
  if (target !== modal && _isTouchPointer() && _isTypable(target)) target = modal;
  if (target === modal && !modal.hasAttribute('tabindex')) modal.setAttribute('tabindex', '-1');
  // preventScroll: focusing must not yank the page to the top on mobile.
  target.focus({ preventScroll: true });
}

function _resetModalScroll(modalEl) {
  if (!modalEl) return;
  modalEl.querySelectorAll('.modal-body, .modal-content-scroll').forEach((node) => {
    node.scrollTop = 0;
    node.scrollLeft = 0;
  });
}

function openModal(id, trigger) {
  const modal = document.getElementById(id);
  if (!modal) {
    return;
  }
  /* Already open - do NOT replay the entrance. Re-entering this function on an
     open modal scrolled its body back to the top, restarted its entrance,
     faded the backdrop in a second time and pulled focus
     back to the first field: the modal visibly re-opened under the user, which
     is what "it jerks, like it opens again" describes. Every path that
     re-enters the open function to repaint the body hit it - Retry in an error
     state, a reload inside a modal, a second click on the opener. A modal
     mid-close is a different case and falls through to a real re-open. */
  if (modal.classList.contains('active') && !modal.classList.contains('closing')) {
    return;
  }
  _autoInitModalDirtyGuards(modal);
  /* Remember what opened it, so closing hands focus back there - a keyboard
     user was otherwise dropped at the top of the document after every modal. */
  const opener = trigger || document.activeElement;
  modal._gpOpener = (opener && opener !== document.body && !modal.contains(opener)) ? opener : null;

  modal.classList.remove('closing');
  _resetModalScroll(modal);
  modal.classList.add('active', 'modal-animating');
  modal.removeAttribute('hidden');
  modal.setAttribute('aria-hidden', 'false');

  // Keep each opening distinct even if navigation replaces the modal node.
  modal._gpOpenVersion = ++_modalState.openVersion;
  const openVersion = modal._gpOpenVersion;
  // Guard: ignore backdrop clicks for a brief window after open
  // to prevent the triggering click from propagating/racing into close.
  modal.dataset.openedAt = String(Date.now());

  if (!_modalState.openStack.includes(id)) {
    _modalState.openStack.push(id);
  }

  _refreshBodyScrollLock();
  document.dispatchEvent(new CustomEvent('gp:modal-open', { detail: { id, modal } }));

  /* Backdrop fades, dialog travels down into place - Bootstrap's modal motion,
     which GitLab keeps. The dialog deliberately does not fade: it is a child of
     the backdrop, and nested opacity multiplies, which double-exposed
     everything inside the modal. */
  GP.motion.overlayIn(modal, modal.querySelector('.modal'));

  // Enable pointer interaction only after this opening has settled.
  setTimeout(() => {
    if (modal._gpOpenVersion === openVersion) modal.classList.remove('modal-animating');
  }, 400);

  setTimeout(() => {
    if (!modal.isConnected || modal._gpOpenVersion !== openVersion
      || !modal.classList.contains('active') || modal.classList.contains('closing')
      || _modalState.openStack[_modalState.openStack.length - 1] !== id
      || modal.contains(document.activeElement)) return;
    _focusFirstModalField(modal);
  }, 50);
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) {
    return false;
  }

  // Check close guard - if a guard returns false, abort close.
  const guard = _modalGuards[id];
  if (guard && typeof guard === 'function') {
    const result = guard(id);
    if (result === false) {
      return false; // guard vetoed the close
    }
  }

  _animateModalClose(modal, id);
  return true;
}

/**
 * Force-close a modal bypassing any registered guard.
 * Used internally after the user confirms discarding unsaved work.
 */
function forceCloseModal(id) {
  const modal = document.getElementById(id);
  if (!modal) { return; }
  _animateModalClose(modal, id);
}

/** Shared close-with-animation helper. */
function _animateModalClose(modal, id) {
  if (modal.classList.contains('closing')) return; // already closing
  const openVersion = modal._gpOpenVersion;
  modal.classList.add('closing');
  document.dispatchEvent(new CustomEvent('gp:modal-closing', { detail: { id, modal } }));
  // Close any open flatpickr calendar owned by an input inside this modal.
  // Flatpickr appends its popup to <body>, so it stays open (orphaned, floating
  // over the page) after the modal is hidden - the "modal closed but the
  // calendar didn't" bug. Closing here covers every close path (button,
  // backdrop, Escape, programmatic).
  modal.querySelectorAll('input').forEach(function (inp) {
    if (inp._flatpickr) { try { inp._flatpickr.close(); } catch (_e) { /* noop */ } }
  });
  // Move focus out before hiding to avoid "Blocked aria-hidden" browser warning
  if (modal.contains(document.activeElement)) { document.activeElement.blur(); }

  function _cleanup() {
    modal.classList.remove('active', 'closing');
    modal.setAttribute('aria-hidden', 'true');
    _modalState.openStack = _modalState.openStack.filter((v) => v !== id);
    _refreshBodyScrollLock();
    document.dispatchEvent(new CustomEvent('modal-closed', { detail: { id } }));
    /* Focus goes back to the control that opened the modal - unless another
       modal is still open (a confirm over a form) or the opener is gone. */
    const back = modal._gpOpener;
    modal._gpOpener = null;
    if (back && !_modalState.openStack.length && document.contains(back) && back.offsetParent !== null) {
      try { back.focus({ preventScroll: true }); } catch (_) { /* noop */ }
    }
  }

  /* GP.motion fades the backdrop and calls back exactly once when it is done -
     including under reduced motion, where it calls back immediately. The old
     `animationend` + 350 ms fallback pair could BOTH fire, and had to filter
     bubbled events from the inner dialog to avoid cleaning up mid-open. */
  GP.motion.overlayOut(modal, function () {
    if (modal._gpOpenVersion !== openVersion || document.getElementById(id) !== modal) return;
    if (modal.contains(document.activeElement)) { document.activeElement.blur(); }
    GP.motion.settle(modal, 'opacity');
    _cleanup();
  });
}

/** Retire a page modal before its DOM is removed or its id is reused. */
function _disposeModal(modal) {
  const id = modal.id;
  const wasOpen = modal.classList.contains('active') || modal.classList.contains('closing');
  modal._gpOpenVersion = ++_modalState.openVersion;
  GP.motion.settle(modal, 'opacity');
  GP.motion.settle(modal.querySelector('.modal'), 'transform');
  if (modal.contains(document.activeElement)) document.activeElement.blur();
  modal.classList.remove('active', 'closing', 'modal-animating');
  modal.setAttribute('aria-hidden', 'true');
  modal._gpOpener = null;
  _modalState.openStack = _modalState.openStack.filter((value) => value !== id);
  delete _modalGuards[id];
  delete _formDirtySnapshots[id];
  _refreshBodyScrollLock();
  if (wasOpen) document.dispatchEvent(new CustomEvent('modal-closed', { detail: { id } }));
}

/**
 * Register a close guard for a modal.
 * The guard function is called before closing - return false to prevent close.
 * @param {string} modalId
 * @param {function(string): boolean|void} guardFn - return false to prevent close
 */
const _modalGuards = {};
function registerModalGuard(modalId, guardFn) {
  _modalGuards[modalId] = guardFn;
}

/**
 * Snapshot all form field values inside a modal.
 * Returns a Map<element, value> for comparison later.
 */
function _snapshotModalFields(modalEl) {
  const snap = new Map();
  if (!modalEl) return snap;
  modalEl.querySelectorAll('input, textarea, select').forEach((el) => {
    // A custom select's validator only mirrors its hidden value, asynchronously.
    if (el.classList.contains('gl-form-dropdown-validator')) return;
    // Keep derived hidden values too, so discarding restores the whole form.
    snap.set(el, el.type === 'checkbox' || el.type === 'radio' ? el.checked : el.value);
  });
  return snap;
}

/**
 * Compare current field values to a snapshot.
 * Returns true if any field changed (the modal is "dirty").
 */
function _isModalDirty(modalEl, snapshot) {
  if (!modalEl || !snapshot || snapshot.size === 0) return false;
  for (const [el, orig] of snapshot) {
    if (el.hasAttribute('data-dirty-ignore')) continue;
    // Derived ids/tokens do not represent an edit by the reader.
    if (el.type === 'hidden' && !el.closest('.gl-form-dropdown')) continue;
    const cur = el.type === 'checkbox' || el.type === 'radio' ? el.checked : el.value;
    if (cur !== orig) return true;
  }
  return false;
}

/** Restore the opening values, including custom selects and date pickers. */
function _restoreModalFields(modalEl, snapshot) {
  const changed = [];
  for (const [el, value] of snapshot) {
    if (!modalEl.contains(el)) continue;
    const current = el.type === 'checkbox' || el.type === 'radio' ? el.checked : el.value;
    if (current !== value) changed.push(el);
    if (el.type === 'checkbox' || el.type === 'radio') el.checked = value;
    else if (el._flatpickr) el._flatpickr.setDate(value, false);
    else el.value = value;
    if (typeof clearFieldError === 'function') clearFieldError(el);
  }
  // Reconcile dependent dates before select watchers emit their change events.
  modalEl.querySelectorAll('[data-period-fields]').forEach(scope => GP.periodFields?.of(scope)?.reset());
  changed.forEach(el => el.dispatchEvent(new Event('change', { bubbles: true })));
}

const _formDirtySnapshots = {};

/** Track intent before custom controls emit their synthetic value events. */
function _trackFormUserEdits(container, onEdit) {
  const nativeEdit = event => {
    if (event.isTrusted && !event.target.closest('[data-dirty-ignore]')) onEdit();
  };
  const controlEdit = event => {
    if (event.isTrusted && event.target instanceof Element
        && event.target.closest('.gl-form-dropdown .gl-dropdown-item, [data-number-step], [data-dirty-action]')) {
      onEdit();
    }
  };
  ['input', 'change'].forEach(type => container.addEventListener(type, nativeEdit, true));
  container.addEventListener('click', controlEdit, true);
  // Body-mounted calendars forward their trusted interaction to the owning input.
  container.addEventListener('gp:user-edit', onEdit, true);
  return function () {
    ['input', 'change'].forEach(type => container.removeEventListener(type, nativeEdit, true));
    container.removeEventListener('click', controlEdit, true);
    container.removeEventListener('gp:user-edit', onEdit, true);
  };
}
GP.trackFormUserEdits = _trackFormUserEdits;

/**
 * Enable an automatic dirty-state guard for a form-based modal.
 * On every openModal(id), snapshots field values.
 * On close attempt, if dirty -> shows confirm dialog.
 * Call once during page init; works for the lifetime of the page.
 */
function enableFormDirtyGuard(modalId, options) {
  const el = document.getElementById(modalId);
  if (!el || el._gpDirtyGuardEnabled) return;
  el._gpDirtyGuardEnabled = true;

  // Capture the opening state immediately, then let untouched forms settle
  // after Alpine / gl-form-dropdown writes its initial hidden-input values.
  _trackFormUserEdits(el, () => { el._gpUserEdited = true; });

  function captureOpening() {
    const currentEl = document.getElementById(modalId);
    if (!currentEl?.classList.contains('active')) return;
    currentEl._gpUserEdited = false;
    _formDirtySnapshots[modalId] = _snapshotModalFields(currentEl);
    // Plain JSON editors have no async initial values. A file read is an edit,
    // including when drag/drop dispatches synthetic input events.
    (options?.settle === false ? [] : [80, 600]).forEach((delay) => setTimeout(() => {
      const cur = document.getElementById(modalId);
      if (cur === currentEl && cur.classList.contains('active') && !cur._gpUserEdited) {
        _formDirtySnapshots[modalId] = _snapshotModalFields(cur);
      }
    }, delay));
  }

  const observer = new MutationObserver((mutations) => {
    // Animation classes must not replace the baseline with the reader's edits.
    const opened = mutations.some((m) => {
      const old = String(m.oldValue || '').split(/\s+/);
      return !old.includes('active') || (old.includes('closing') && !el.classList.contains('closing'));
    });
    if (opened) captureOpening();
  });
  observer.observe(el, { attributes: true, attributeFilter: ['class'], attributeOldValue: true });
  // A programmatic opener can run before the incoming page registers its guard.
  captureOpening();

  registerModalGuard(modalId, () => {
    const modalEl = document.getElementById(modalId);
    const snap = _formDirtySnapshots[modalId];
    if (!_isModalDirty(modalEl, snap)) return; // clean -> allow close
    const openVersion = modalEl._gpOpenVersion;
    const { t } = GP;
    /* THE confirmation, not `window.confirm` - which cannot be themed, ignores
       dark mode and reads as if the page broke.
       The guard is synchronous and the dialog is not, so the close is vetoed
       NOW and re-issued through `forceCloseModal` (which bypasses guards, and
       exists for exactly this) once the reader answers. */
    GP.confirmDialog({
      title: t('Discard unsaved changes?'),
      message: t('You have unsaved changes. Discard?'),
      confirmText: t('Discard'),
      variant: 'danger',
    }).then(function (ok) {
      if (!ok || !modalEl.isConnected || modalEl._gpOpenVersion !== openVersion
          || !modalEl.classList.contains('active') || _formDirtySnapshots[modalId] !== snap) return;
      _formDirtySnapshots[modalId] = null;
      _restoreModalFields(modalEl, snap);
      forceCloseModal(modalId);
    });
    return false; // block this close; the answer re-issues it
  });
}

/**
 * Mark a form-based modal as intentionally clean (call before programmatic close
 * after a successful save so the guard does not trigger).
 */
function clearModalDirty(modalId) {
  _formDirtySnapshots[modalId] = null;
}

function closeModalOnBackdrop(event) {
  if (!event || !event.target) {
    return;
  }
  if (document.documentElement.classList.contains('theme-transitioning')) {
    return;
  }
  if (event.target.classList.contains('modal-backdrop') && event.target.id) {
    // Guard: ignore clicks within 200ms of modal open to prevent
    // the triggering click event from racing into a close.
    const openedAt = parseInt(event.target.dataset.openedAt || '0', 10);
    if (openedAt && (Date.now() - openedAt) < 200) {
      return;
    }
    closeModal(event.target.id);
  }
}

function closeAllModals(options) {
  document
    .querySelectorAll('.modal-backdrop.active')
    .forEach((node) => options?.force === true ? forceCloseModal(node.id) : closeModal(node.id));
}

// Focus trap and Escape for active modal.
document.addEventListener('keydown', (event) => {
  const activeBackdrop = document.getElementById(_modalState.openStack[_modalState.openStack.length - 1])
    || document.querySelector('.modal-backdrop.active');
  if (!activeBackdrop) {
    return;
  }

  if (event.key === 'Escape') {
    // Flatpickr handles keys from its popup before they reach the modal.
    if (event.target instanceof Element && event.target.closest('.flatpickr-calendar')) return;
    const pickerInput = Array.from(activeBackdrop.querySelectorAll('input')).find(
      input => input._flatpickr && input._flatpickr.isOpen
    );
    if (pickerInput) {
      event.preventDefault();
      event.stopImmediatePropagation();
      pickerInput._flatpickr.close();
      pickerInput.focus({ preventScroll: true });
      return;
    }
    // A dirty close may open a confirmation synchronously. This key belongs
    // only to the original dialog, not to that newly opened confirmation.
    event.preventDefault();
    event.stopImmediatePropagation();
    closeModal(activeBackdrop.id);
    return;
  }

  if (event.key !== 'Tab') {
    return;
  }

  const container = activeBackdrop.querySelector('.modal') || activeBackdrop;
  const focusables = _getFocusableElements(container);
  if (focusables.length === 0) {
    event.preventDefault();
    return;
  }

  const first = focusables[0];
  const last = focusables[focusables.length - 1];
  const current = document.activeElement;

  if (current === container) {
    event.preventDefault();
    (event.shiftKey ? last : first).focus({ preventScroll: true });
    return;
  }

  if (event.shiftKey && current === first) {
    event.preventDefault();
    last.focus({ preventScroll: true });
  } else if (!event.shiftKey && current === last) {
    event.preventDefault();
    first.focus({ preventScroll: true });
  }
});
