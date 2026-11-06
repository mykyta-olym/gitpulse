/* ============================================
   Keyboard Shortcuts
   ============================================ */
const _shortcuts = new Map();

function _normalizeShortcut(combo) {
  return String(combo || '').trim().toLowerCase().replace(/\s+/g, '');
}

function registerShortcut(combo, handler, opts = {}) {
  const key = _normalizeShortcut(combo);
  if (!key || typeof handler !== 'function') {
    return () => {};
  }
  _shortcuts.set(key, {
    handler,
    ignoreInputs: opts.ignoreInputs !== false,
  });
  return () => _shortcuts.delete(key);
}

document.addEventListener('keydown', (event) => {
  /* Preferences > Behavior > "Enable keyboard shortcuts". Gated HERE, at the
     single dispatcher, rather than inside each handler: this is the only place
     that has to know, and search, save and help all pass through it.
     Escape and the modal keys are NOT registered
     shortcuts, so dismissing a dialog keeps working with shortcuts turned off -
     which is what makes gating the whole dispatcher safe. */
  if (document.documentElement.hasAttribute('data-no-shortcuts')) {
    return;
  }

  const parts = [];
  if (event.ctrlKey || event.metaKey) {
    parts.push('ctrl');
  }
  if (event.shiftKey) {
    parts.push('shift');
  }
  if (event.altKey) {
    parts.push('alt');
  }
  parts.push(String(event.key || '').toLowerCase());
  const combo = parts.join('+');

  const shortcut = _shortcuts.get(combo);
  if (!shortcut) {
    return;
  }

  const target = event.target;
  if (
    shortcut.ignoreInputs &&
    target &&
    target.matches &&
    target.matches('input, textarea, select, [contenteditable="true"], [contenteditable=""]')
  ) {
    return;
  }

  event.preventDefault();
  shortcut.handler(event);
});

registerShortcut('ctrl+k', () => {
  if (typeof GP.openSearchPalette === 'function') {
    window.GP.openSearchPalette();
  } else {
    const searchInput = document.querySelector('.search-box input, input[type="search"]');
    if (searchInput) searchInput.focus();
  }
});

/* GitLab: pressing / focuses the search box (same as Ctrl+K) */
registerShortcut('/', () => {
  if (typeof GP.openSearchPalette === 'function') {
    window.GP.openSearchPalette();
  } else {
    const searchInput = document.querySelector('.search-box input, input[type="search"]');
    if (searchInput) searchInput.focus();
  }
});

/* Escape is handled by the modal keydown handler (stack-based close) -
   no need for a separate shortcut that would bypass the close guard. */

/* "?" - show keyboard shortcut help toast */
const _showShortcutHelp = () => {
  const shortcuts = [
    'Ctrl+K / - ' + GP.t('Search'),
    '? - ' + GP.t('Keyboard shortcuts'),
    'Ctrl+S - ' + GP.t('Save current form'),
  ];
  const msg = shortcuts.join('<br>');
  GP.showToast(msg, 'info', 6000);
};
// KeyboardEvent.key already contains the shifted character. Some layouts
// produce '?' without Shift, so both combinations invoke the same help.
registerShortcut('shift+?', _showShortcutHelp);
registerShortcut('?', _showShortcutHelp);

/* Ctrl+S - save current form (prevents browser save-page) */
registerShortcut('ctrl+s', () => {
  const scope = document.querySelector('.modal-backdrop.active') || document;
  const form = scope.querySelector('form[data-autosave], form[data-save-guard], #courseSettingsForm');
  if (form) {
    const submitBtn = form.querySelector('button[type="submit"], [data-action="save"]');
    if (submitBtn && !submitBtn.disabled) {
      submitBtn.click();
    }
  }
}, { ignoreInputs: false });
