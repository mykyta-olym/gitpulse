/* ============================================
   Anti-Spam: Global click lock (capture phase)

   A single capture-phase guard that lets the first click on any action
   button/link through, then swallows further clicks on the SAME element
   for a short window. This is handler-independent: it works even for
   buttons whose handlers forget to call setButtonLoading, use raw fetch(),
   or trigger non-apiCall actions. Pure UI toggles (dropdowns, modal
   open/close, tabs, checkboxes) are excluded so they stay snappy.

   When a click is swallowed we surface a single throttled "please wait"
   toast so the user always knows the system registered the click and is
   busy - addressing the "tell me even when nothing changes" requirement.
   Opt out per element with data-no-click-lock="true".
   ============================================ */
const _CLICK_LOCK_MS = 350;

// Instant, client-only actions that do no network I/O - they must never be
// debounced/locked (and certainly never toast), so copy/expand/filter stay
// snappy on rapid repeat.
const _INSTANT_ACTIONS = new Set([
  'copyToClipboard',
  'clickElementById',
  'closeModal',
  'openModal',
  'toggleNextClass',
  'toggleClass',
  'dismiss',
  'scrollToTop',
  'closeModalOnBackdrop',
]);

function _isClickLockExempt(el) {
  if (!el || el.dataset.noClickLock === 'true') return true;
  if (el.type === 'checkbox' || el.type === 'radio') return true;
  const tagName = el.tagName;
  if (tagName === 'INPUT' || tagName === 'SELECT' || tagName === 'TEXTAREA' || tagName === 'LABEL') return true;
  if (el.hasAttribute('contenteditable') || el.closest('[contenteditable="true"], [contenteditable=""]')) return true;
  // Copy buttons + other instant client-only actions.
  if (el.hasAttribute('data-copy') || el.hasAttribute('data-clipboard-text')) return true;
  const act = el.getAttribute('data-action');
  if (act && _INSTANT_ACTIONS.has(act)) return true;
  // Toggles / navigation that rely on rapid repeat interaction.
  if (el.closest('.gl-dropdown-toggle, .gl-tab, [role="tab"], [data-page], .gp-deleted-toggle, .card-header-info-tip')) {
    return true;
  }
  return el.hasAttribute('data-modal-open')
    || el.hasAttribute('data-modal-close')
    || el.hasAttribute('data-toggle-next-class')
    || el.hasAttribute('aria-expanded')
    // Toggle buttons (e.g. the "Deleted" show/hide) carry aria-pressed and are
    // pure client-side state flips - they must respond to every click, not be
    // locked out for the cooldown after the first.
    || el.hasAttribute('aria-pressed');
}

document.addEventListener('click', function _antiSpamClickLock(event) {
  // Resolve the actual interactive control the user clicked. CRITICAL: never
  // lock on a large container that merely carries a passthrough [data-action]
  // (e.g. the modal backdrop's closeModalOnBackdrop, or a [data-submit-action]
  // <form>). Locking a container would freeze EVERY control inside it for the
  // cooldown window after the first click - which is exactly the "almost
  // everything needs two clicks, everywhere" bug inside modals.
  let el = event.target.closest('button, input[type="submit"], a.btn, .btn');
  if (!el) {
    const action = event.target.closest('[data-action]');
    // A [data-action] element is only a real control when it is itself a
    // button / link / role=button - not a wrapping <div> container.
    if (action && (action.tagName === 'BUTTON' || action.tagName === 'A'
        || action.getAttribute('role') === 'button')) {
      el = action;
    }
  }
  if (!el || _isClickLockExempt(el)) return;

  const now = Date.now();
  if (el._gpClickLockUntil && now < el._gpClickLockUntil) {
    // Silent debounce: swallowing an accidental rapid double-click is normal
    // UX and must be invisible. The meaningful "please wait, something is
    // actually running" feedback is surfaced ONLY by the apiCall mutation
    // throttle below, which fires only when a real network mutation to the
    // same endpoint is genuinely in flight - not on every quick re-click.
    event.preventDefault();
    event.stopImmediatePropagation();
    return;
  }
  el._gpClickLockUntil = now + _CLICK_LOCK_MS;
}, true);

/* ============================================
   Anti-Spam: Form Submit Debounce
   Prevents double-submission of standard forms
   by disabling the submit button during submission.
   ============================================ */
document.addEventListener('submit', function _antiSpamSubmit(event) {
  const form = event.target.closest('form');
  if (
    !form ||
    form.dataset.noAntiSpam === 'true' ||
    form.dataset.saveGuard === '1' ||
    form.hasAttribute('data-preferences-form') ||
    form.hasAttribute('data-save-guard') ||
    form.querySelector('.btn-save-guard')
  ) {
    return;
  }

  // Registered in the CAPTURE phase, so this runs BEFORE the form's own
  // bubble-phase submit handler (validation, [data-submit-action], etc.).
  // At this instant `event.defaultPrevented` is still false even for a
  // submit that is about to be cancelled. If we disabled the button now we
  // would lock it for the full 5s fallback whenever:
  //   - client validation aborts the submit (e.g. a 1-char group name), or
  //   - a [data-submit-action] AJAX form handles its own button-loading
  //     state via submitModalForm()/setButtonLoading (double-management).
  // Defer past the dispatch: by then the bubble handler has run and
  // defaultPrevented accurately reflects whether a real navigation submit
  // is happening. Only guard genuine page-navigation submits against
  // double-clicks; leave prevented/AJAX submits to their own handlers.
  // A macrotask, not a microtask: the browser runs a microtask checkpoint
  // between the listeners of a user-fired event, so a queueMicrotask here
  // ran BEFORE the form's own handler and saw defaultPrevented=false for
  // every AJAX form - the submit button of every modal form went dead for
  // five seconds with no loading state to show for it.
  setTimeout(function () {
    if (event.defaultPrevented) return;
    const btns = form.querySelectorAll('button[type="submit"], input[type="submit"], button:not([type])');
    btns.forEach(btn => {
      if (btn.disabled || btn.classList.contains('btn-save-guard')) return;
      // Disabled at once (the point of the guard), and the app's one loading
      // state on top of it, so a navigating submit looks like every other
      // working button instead of a greyed-out one.
      btn.disabled = true;
      setButtonLoading(btn, true);
      // Re-enable after 5s as a safety fallback
      setTimeout(() => {
        setButtonLoading(btn, false);
      }, 5000);
    });
  }, 0);
}, true);
