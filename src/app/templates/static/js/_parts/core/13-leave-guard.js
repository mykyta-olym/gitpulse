/* ============================================
   Page Navigation Guard - beforeunload
   Centralized dirty-state detection for ALL pages.
   Pages register "reasons" why navigation is unsafe.
   Open dirty modals are also auto-detected.
   ============================================ */
const _pageDirtyReasons = {};

/**
 * Register a reason that prevents safe navigation.
 * @param {string} key   - unique identifier, e.g. 'llm_running', 'settings_form'
 * @param {string} [label] - human-readable label (optional, for debugging)
 */
function addDirtyReason(key, label) {
  _pageDirtyReasons[key] = label || key;
}

/**
 * Clear a previously registered dirty reason.
 */
function clearDirtyReason(key) {
  delete _pageDirtyReasons[key];
}

/**
 * Check if any dirty reason is registered.
 * Also auto-detects open modals with dirty form snapshots.
 */
function hasUnsavedState() {
  // Explicit dirty reasons
  if (Object.keys(_pageDirtyReasons).length > 0) return true;

  // Check open modals for dirty form fields
  const openModals = _modalState.openStack;
  for (let i = 0; i < openModals.length; i++) {
    const id = openModals[i];
    const snap = _formDirtySnapshots[id];
    const el = document.getElementById(id);
    if (snap && _isModalDirty(el, snap)) return true;
  }

  // NOTE: Server-side jobs (sync, analysis, docker verify, CI scenarios)
  // run on the server via RQ - they do NOT need beforeunload protection.
  // The global job bar tracks them across navigations via localStorage.

  return false;
}

/**
 * Mark that the next navigation/reload is intentional (programmatic).
 * Prevents the beforeunload guard from firing for JS-initiated reloads
 * and redirects (e.g. after a successful import, config apply, delete).
 */
let _skipBeforeunload = false;
function skipBeforeunload() {
  _skipBeforeunload = true;
  /* Re-arm after 2 s in case navigation was cancelled */
  setTimeout(() => { _skipBeforeunload = false; }, 2000);
}

window.addEventListener('beforeunload', function (e) {
  _preserveFlashToast();
  if (_skipBeforeunload) return;
  if (hasUnsavedState()) {
    e.preventDefault();
    e.returnValue = '';
    // If the user clicks "Cancel" (stay on page), the navigation is aborted
    // but page-transition may have already applied .page-leaving (fade-out)
    // to <body>. Remove it so the page content re-appears without a reload.
    setTimeout(function () {
      document.body.classList.remove('page-leaving');
      document.body.classList.remove('page-navigating');
    }, 200);
  }
});

/**
 * Drop every registered dirty reason at once. Dirty reasons describe unsaved
 * state in the CURRENT page's DOM, so leaving that page (an SPA content swap)
 * makes them all moot - the DOM they referred to is gone. _navigate() calls
 * this on every internal navigation. Without it a reason registered on one page
 * (e.g. 'settings_form' on Course Settings) survived the swap and then fired the
 * browser "Leave site?" prompt on a later page that had nothing unsaved.
 */
function clearAllDirtyReasons() {
  for (const k in _pageDirtyReasons) delete _pageDirtyReasons[k];
}

GP.addDirtyReason = addDirtyReason;
GP.clearDirtyReason = clearDirtyReason;
GP.clearAllDirtyReasons = clearAllDirtyReasons;
GP.hasDirtyReason = function (key) { return Object.prototype.hasOwnProperty.call(_pageDirtyReasons, key); };
GP.hasUnsavedState = hasUnsavedState;
GP.skipBeforeunload = skipBeforeunload;
