/* ============================================
   Declarative Data Actions
   ============================================ */
function _resolveGlobalFunction(path) {
  if (!path) {
    return null;
  }
  const parts = String(path).split('.');
  let ctx = window;
  for (let i = 0; i < parts.length; i += 1) {
    const key = parts[i];
    if (!ctx || !(key in ctx)) {
      return null;
    }
    ctx = ctx[key];
  }
  return typeof ctx === 'function' ? ctx : null;
}

function _parseActionArgs(raw) {
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch (_) {
    return [];
  }
}

function _mapActionToken(arg, event, el) {
  if (arg === '$event') {
    return event;
  }
  if (arg === '$el') {
    return el;
  }
  if (arg === '$value') {
    return 'value' in el ? el.value : el.textContent;
  }
  if (arg === '$checked') {
    return Boolean(el.checked);
  }
  if (arg === '$dataset') {
    return { ...el.dataset };
  }
  return arg;
}


function _runDataAction(el, event, actionNameKey = 'action', actionArgsKey = 'actionArgs') {
  const actionName = el.dataset[actionNameKey];
  if (!actionName) {
    return false;
  }
  const fn = _resolveGlobalFunction(actionName);
  if (!fn) {
    console.debug(`Action function "${actionName}" was not found on window (may be handled by page script)`);
    return false;
  }

  const rawArgs = _parseActionArgs(el.dataset[actionArgsKey] || '');
  const args = rawArgs.map((value) => _mapActionToken(value, event, el));
  if (args.length === 0) {
    args.push(event);
  }

  fn.apply(window, args);
  return true;
}

/* Optimistic sidebar active highlight. Navigation uses a cross-document view
   transition (@view-transition: navigation auto), which snapshots the OUTGOING
   page - including its CURRENT sidebar highlight - and crossfades it into the new
   page. That made a freshly-clicked item look un-highlighted while the PREVIOUS
   page's highlight lingered through the crossfade ("I clicked one section but a
   different one is highlighted"). Moving `.active` to the clicked item here, on
   the capture phase BEFORE the snapshot is taken, makes the transition show the
   correct highlight from the first frame. The destination page re-renders the
   authoritative state server-side, so this is purely a transition-time hint. */
document.addEventListener('click', (event) => {
  if (event.defaultPrevented || event.button !== 0 ||
      event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const item = event.target.closest('.gl-sidebar-item[href]');
  if (!item || item.getAttribute('target') === '_blank') return;
  const list = item.closest('.gl-sidebar');
  if (!list) return;
  list.querySelectorAll('.gl-sidebar-item.active').forEach((el) => el.classList.remove('active'));
  item.classList.add('active');
}, true);

document.addEventListener('click', (event) => {
  const openTrigger = event.target.closest('[data-modal-open]');
  if (openTrigger) {
    event.preventDefault();
    openModal(openTrigger.dataset.modalOpen, openTrigger);
    return;
  }

  const closeTrigger = event.target.closest('[data-modal-close]');
  if (closeTrigger) {
    event.preventDefault();
    // data-modal-close may carry an explicit modal id, otherwise walk up to the parent backdrop
    const targetId = closeTrigger.dataset.modalClose || closeTrigger.closest('.modal-backdrop')?.id;
    if (targetId) closeModal(targetId);
    return;
  }

  const copyTrigger = event.target.closest('[data-copy-text]');
  if (copyTrigger) {
    event.preventDefault();
    copyToClipboard(copyTrigger.dataset.copyText || '', copyTrigger.dataset.copySuccess || _translateUiText('Copied!'));
    return;
  }

  const removeTrigger = event.target.closest('[data-remove-closest]');
  if (removeTrigger) {
    event.preventDefault();
    const selector = removeTrigger.dataset.removeClosest || '';
    const node = selector ? removeTrigger.closest(selector) : null;
    if (node) {
      node.remove();
    }
    return;
  }

  const nextClassToggleTrigger = event.target.closest('[data-toggle-next-class]');
  if (nextClassToggleTrigger) {
    const className = nextClassToggleTrigger.dataset.toggleNextClass || '';
    if (!className) {
      return;
    }
    const next = nextClassToggleTrigger.nextElementSibling;
    if (next && next.classList) {
      next.classList.toggle(className);
    }
    return;
  }

  const backTrigger = event.target.closest('[data-nav-back]');
  if (backTrigger) {
    event.preventDefault();
    if (document.referrer && document.referrer !== window.location.href) {
      window.history.back();
    } else if (backTrigger.getAttribute('href')) {
      const backHref = backTrigger.getAttribute('href');
      if (!GP.navigateTo?.(backHref, backTrigger)) {
        window.location.href = backHref;
      }
    }
    return;
  }

  const actionTrigger = event.target.closest('[data-action]');
  if (actionTrigger) {
    if (actionTrigger.tagName === 'A' || actionTrigger.dataset.preventDefault === 'true') {
      event.preventDefault();
    }
    _runDataAction(actionTrigger, event, 'action', 'actionArgs');
    return;
  }
});

// Dismissible info-card banners: the X button removes its card. Delegated so it
// works for server-rendered AND dynamically-inserted cards (CSP-safe, no inline).
// When the card carries a [data-dismiss-key], the dismissal is persisted in
// localStorage so the banner does NOT reappear when the user navigates away and
// back, RELOADS the page, or has the app open in ANOTHER tab (the reported
// "banner keeps coming back after I closed it"). Persistence is keyed by
// data-dismiss-key: state-embedding keys (e.g. failed count) still re-surface a
// genuinely NEW condition, while stable keys (e.g. "data may be outdated") stay
// dismissed. A 'storage' listener below prunes the banner live in other tabs.
const _DISMISS_STORE_KEY = 'gp:dismissedBanners';
function _readDismissedBanners() {
  try {
    const raw = window.localStorage.getItem(_DISMISS_STORE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (_) { return {}; }
}
function _rememberDismissed(key) {
  if (!key) return;
  try {
    const store = _readDismissedBanners();
    store[key] = 1;
    window.localStorage.setItem(_DISMISS_STORE_KEY, JSON.stringify(store));
  } catch (_) { /* storage disabled/full - dismissal is best-effort */ }
}
function _isBannerDismissed(key) {
  if (!key) return false;
  return !!_readDismissedBanners()[key];
}
/* Hide any already-dismissed banners immediately on (re)render so they never
   flash back in after a navigation. Idempotent - safe to call repeatedly. */
function _hideDismissedBanners(root) {
  const scope = root || document;
  // Any element carrying a persisted dismiss key - info-card banners AND the
  // unified .gp-top-banner strips (archived, data-outdated, stale-data, ...).
  scope.querySelectorAll('[data-dismiss-key]').forEach((el) => {
    if (_isBannerDismissed(el.getAttribute('data-dismiss-key'))) el.remove();
  });
}
GP.isBannerDismissed = _isBannerDismissed;
