/* ============================================
   Mobile: swipe-down-to-dismiss the bottom sheet
   The mobile modal renders a drag-handle pill (.modal::before on <=640px).
   Make it real: a downward drag that STARTS on the sheet's top region (the
   handle + header) closes the modal, mirroring the iOS / GitLab bottom-sheet
   gesture. It engages ONLY from the top region, so it never competes with
   scrolling the modal body, and the non-passive touchmove listener is attached
   only for the duration of an actual drag.
   ============================================ */
const _SHEET_DRAG = {
  modal: null,
  backdropId: null,
  startY: 0,
  startX: 0,
  active: false, // passed the engage threshold; we now own the gesture
};

function _sheetDragTeardown() {
  document.removeEventListener('touchmove', _sheetDragMove, { passive: false });
  document.removeEventListener('touchend', _sheetDragEnd);
  document.removeEventListener('touchcancel', _sheetDragCancel);
}

function _sheetDragReset() {
  if (_SHEET_DRAG.modal) {
    _SHEET_DRAG.modal.style.transition = '';
    _SHEET_DRAG.modal.style.transform = '';
  }
  _SHEET_DRAG.modal = null;
  _SHEET_DRAG.backdropId = null;
  _SHEET_DRAG.active = false;
}

function _sheetDragStart(event) {
  if (!event.touches || event.touches.length !== 1) {
    return;
  }
  // Only the bottom-sheet form factor has the handle - match the CSS breakpoint.
  if (!window.matchMedia('(max-width: 640px)').matches) {
    return;
  }
  // The gesture belongs to the dialog actually touched. DOM order does not
  // match paint order when the shared confirmation sits above a page modal.
  const backdrop = event.target.closest('.modal-backdrop.active');
  if (!backdrop || !backdrop.id) {
    return;
  }
  const modal = backdrop.querySelector('.modal');
  if (!modal || !modal.contains(event.target)) {
    return;
  }
  const touch = event.touches[0];
  const rect = modal.getBoundingClientRect();
  // Engage only from the top region: handle pill + header (~64px). Below that
  // the gesture belongs to body content, where a drag means scroll.
  const inHandleZone = (touch.clientY - rect.top) <= 64;
  const onHeader = !!event.target.closest('.modal-header');
  if (!inHandleZone && !onHeader) {
    return;
  }
  // Never hijack a drag that begins on an interactive control.
  if (event.target.closest('button, a, input, select, textarea, [role="button"]')) {
    return;
  }
  _SHEET_DRAG.modal = modal;
  _SHEET_DRAG.backdropId = backdrop.id;
  _SHEET_DRAG.startY = touch.clientY;
  _SHEET_DRAG.startX = touch.clientX;
  _SHEET_DRAG.active = false;
  document.addEventListener('touchmove', _sheetDragMove, { passive: false });
  document.addEventListener('touchend', _sheetDragEnd);
  document.addEventListener('touchcancel', _sheetDragCancel);
}

function _sheetDragMove(event) {
  if (!_SHEET_DRAG.modal) {
    return;
  }
  const touch = event.touches[0];
  const dy = touch.clientY - _SHEET_DRAG.startY;
  const dx = touch.clientX - _SHEET_DRAG.startX;
  if (!_SHEET_DRAG.active) {
    // Decide intent: only a clear downward pull captures the gesture.
    if (dy > 8 && dy > Math.abs(dx)) {
      _SHEET_DRAG.active = true;
      _SHEET_DRAG.modal.style.transition = 'none';
    } else if (dy < -4 || Math.abs(dx) > 10) {
      _sheetDragTeardown();
      _sheetDragReset();
      return;
    } else {
      return;
    }
  }
  if (dy <= 0) {
    _SHEET_DRAG.modal.style.transform = '';
    return;
  }
  if (!event.cancelable) {
    _sheetDragCancel(); // The browser already owns this scroll gesture.
    return;
  }
  event.preventDefault(); // stop the page rubber-banding behind the sheet
  // Mild resistance so the sheet trails the finger without feeling 1:1 sticky.
  _SHEET_DRAG.modal.style.transform = 'translateY(' + dy + 'px)';
}

function _sheetDragEnd(event) {
  const modal = _SHEET_DRAG.modal;
  const id = _SHEET_DRAG.backdropId;
  const wasActive = _SHEET_DRAG.active;
  const endY = (event.changedTouches && event.changedTouches[0]
    ? event.changedTouches[0].clientY
    : _SHEET_DRAG.startY);
  const dy = endY - _SHEET_DRAG.startY;
  _sheetDragTeardown();
  if (!modal || !wasActive) {
    _sheetDragReset();
    return;
  }
  // Close past 25% of the sheet height (capped at 120px), else snap back.
  const threshold = Math.min(modal.getBoundingClientRect().height * 0.25, 120);
  _SHEET_DRAG.modal = null;
  _SHEET_DRAG.backdropId = null;
  _SHEET_DRAG.active = false;
  if (dy > threshold && id) {
    // Continue the sheet DOWN off-screen from where the finger left it, with
    // inertia - instead of snapping back to 0 and replaying a canned slide
    // (the reported "blink / disappear"). Nothing has to be suppressed any more:
    // dismissing a modal is opacity-only now, as GitLab's is, so this inline
    // transition is the only thing moving the sheet.
    const vh = window.innerHeight || (modal.getBoundingClientRect().bottom + 300);
    /* GP.motion owns the release - see sheetDismiss. This used to be an inline
       transition string plus a 400ms setTimeout that restated its duration. */
    if (closeModal(id)) { // Check unsaved-change guards before leaving the screen.
      GP.motion.sheetDismiss(modal, vh);
    } else {
      GP.motion.sheetSettle(modal);
    }
    return;
  }
  // Did not pass the threshold: settle back where it came from.
  GP.motion.sheetSettle(modal);
}

function _sheetDragCancel() {
  _sheetDragTeardown();
  _sheetDragReset();
}

document.addEventListener('touchstart', _sheetDragStart, { passive: true });

GP.openModal = openModal;
GP.closeModal = closeModal;
GP.forceCloseModal = forceCloseModal;
GP.registerModalGuard = registerModalGuard;
GP.enableFormDirtyGuard = enableFormDirtyGuard;
GP.clearModalDirty = clearModalDirty;
GP.closeAllModals = closeAllModals;
GP.setButtonLoading = setButtonLoading;
/* Exposed for the one other owner of a button's loading chrome: the cooldown in
   process-action-guards.js, which has to take the button over mid-flight. */
GP.clearButtonLoadingChrome = clearButtonLoadingChrome;
GP.copyToClipboard = copyToClipboard;
