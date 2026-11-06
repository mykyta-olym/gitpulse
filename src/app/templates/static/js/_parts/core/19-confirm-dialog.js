/* ============================================
   Shared confirmation dialog
   ============================================
   ONE styled "are you sure?" for the whole app (markup: #gpConfirmDialog in
   base.html). It replaces the raw `window.confirm` / `window.prompt` the
   destructive actions used to call: browser dialogs cannot be themed, ignore
   dark mode, carry no danger accent and read as if the page broke - and they
   sat next to the app's own modals doing the same job, which is two patterns
   for one interaction.

   Promise-based, because that is the only faithful way to model a dialog that
   does not block the thread:

     if (await GP.confirmDialog({ message: '...' })) { ... }

   `requireTyping` reproduces the "type the course code" safeguard the prompt
   used to provide, with the confirm button disabled until the text matches. */
(function _confirmDialog() {
  'use strict';
  let _resolve = null;
  let _lastFocus = null;

  function _el() { return document.getElementById('gpConfirmDialog'); }

  function _finish(result, alreadyClosed = false) {
    /* Close through the app's own modal machinery - the exit animation, the
       body scroll lock and the open-stack all live there. Rolling our own
       show/hide here was the very duplication this dialog exists to remove
       (and it did not work: the backdrop never became visible). */
    const r = _resolve;
    _resolve = null;
    if (!alreadyClosed) closeModal('gpConfirmDialog');
    if (_lastFocus && typeof _lastFocus.focus === 'function') {
      try { _lastFocus.focus(); } catch (_) { /* element may be gone */ }
    }
    _lastFocus = null;
    if (r) r(result);
  }

  function confirmDialog(options) {
    const opts = options || {};
    const root = _el();
    /* No dialog in the DOM (a standalone page, an error template): fall back to
       the browser's so a destructive action still asks rather than just firing. */
    if (!root) {
      return Promise.resolve(window.confirm(opts.message || GP.t('Are you sure you want to continue?')));
    }
    if (_resolve) _finish(false);          /* never stack two dialogs */

    const title = root.querySelector('.modal-title');
    const message = root.querySelector('.gp-confirm-message');
    const okBtn = root.querySelector('[data-gp-confirm="ok"]');
    const typingWrap = root.querySelector('.gp-confirm-typing');
    const typingLabel = typingWrap ? typingWrap.querySelector('label') : null;
    const typingInput = typingWrap ? typingWrap.querySelector('input') : null;

    if (title) title.textContent = opts.title || GP.t('Are you sure?');
    if (message) message.textContent = opts.message || '';
    if (okBtn) {
      okBtn.textContent = opts.confirmText || GP.t('Confirm');
      okBtn.className = 'btn btn-' + (opts.variant || 'danger');
      okBtn.disabled = false;
    }

    const expected = opts.requireTyping ? String(opts.expectedValue || '') : '';
    if (typingWrap) {
      if (expected) {
        typingWrap.classList.remove('d-none');
        if (typingLabel) {
          typingLabel.textContent = opts.typingPrompt
            || GP.t('Type "{expected}" to confirm:').replace('{expected}', expected);
        }
        if (typingInput) {
          typingInput.value = '';
          if (okBtn) okBtn.disabled = true;
        }
      } else {
        typingWrap.classList.add('d-none');
      }
    }

    _lastFocus = document.activeElement;
    openModal('gpConfirmDialog');
    const openVersion = root._gpOpenVersion;
    /* Focus the safe control, not the destructive one: Enter must not delete. */
    window.requestAnimationFrame(function () {
      if (!root.isConnected || root._gpOpenVersion !== openVersion
        || !root.classList.contains('active') || root.classList.contains('closing')
        || _modalState.openStack[_modalState.openStack.length - 1] !== root.id) return;
      const target = expected && typingInput
        ? typingInput
        : root.querySelector('[data-gp-confirm="cancel"]');
      if (target && typeof target.focus === 'function') target.focus();
    });

    return new Promise(function (resolve) {
      _resolve = resolve;
      if (expected && typingInput && okBtn) {
        typingInput.oninput = function () {
          okBtn.disabled = typingInput.value.trim() !== expected;
        };
      }
    });
  }

  document.addEventListener('click', function (evt) {
    const root = _el();
    if (!root || !_resolve) return;
    const btn = evt.target.closest ? evt.target.closest('[data-gp-confirm]') : null;
    if (btn && root.contains(btn)) {
      evt.preventDefault();
      _finish(btn.getAttribute('data-gp-confirm') === 'ok');
      return;
    }
    /* Backdrop click cancels, like every other modal in the app. */
    if (evt.target === root) _finish(false);
  }, true);

  // Keyboard, swiping and programmatic closing use the shared controller.
  // Those paths must cancel the pending confirmation just like Escape.
  document.addEventListener('modal-closed', function (evt) {
    if (evt.detail?.id === 'gpConfirmDialog' && _resolve) _finish(false, true);
  });

  GP.confirmDialog = confirmDialog;
  window.gpConfirm = confirmDialog;
})();
