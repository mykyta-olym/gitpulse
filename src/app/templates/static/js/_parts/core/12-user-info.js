// -- Global User Info modal (available on every page) --
const _userInfoReads = new Map();

GP.cancelUserInfoRead = function (modalId) {
  const read = _userInfoReads.get(modalId);
  if (read) {
    read.finish();
    read.controller.abort();
  }
};

/* Both User Info dialogs own their read, including the lazy renderer load.
   Closing or choosing another person must release it immediately; a late
   response must never replace the newly selected profile. */
GP.beginUserInfoRead = function (modal, identity) {
  const previous = _userInfoReads.get(modal.id);
  if (previous && previous.identity === identity && previous.current()) return null;
  GP.cancelUserInfoRead(modal.id);
  const body = modal.querySelector('.modal-body');
  body.setAttribute('aria-busy', 'true');
  const read = {
    identity,
    controller: new AbortController(),
    current: function () {
      return _userInfoReads.get(modal.id) === read && !read.controller.signal.aborted
        && modal.isConnected && modal.classList.contains('active')
        && !modal.classList.contains('closing');
    },
    finish: function () {
      if (_userInfoReads.get(modal.id) === read) {
        _userInfoReads.delete(modal.id);
        body.removeAttribute('aria-busy');
      }
    },
  };
  _userInfoReads.set(modal.id, read);
  return read;
};

document.addEventListener('modal-closed', function (event) {
  GP.cancelUserInfoRead(event.detail.id);
});

/** Replace modal content using the shared height transition.
 * @param {HTMLElement} container
 * @param {string} html
 */
async function swapModalBodyAnimated(container, html, current = () => container.isConnected) {
  // Yield once so a close or a newer profile can supersede this hand-off.
  await Promise.resolve();
  if (!current()) return false;
  GP.motion.resize(container, function () {
    container.innerHTML = html;
  });
  return true;
}
GP.swapModalBodyAnimated = swapModalBodyAnimated;

/* Load and memoize the shared renderer on first open. A failed load shows
   the retryable error state instead of a second renderer. */
let _userInfoModulePromise = null;
function _ensureUserInfoModule() {
  if (window.UserInfoModal) return Promise.resolve(true);
  if (_userInfoModulePromise) return _userInfoModulePromise;
  /* The URL comes from the server: static_url() resolves it to the built,
     content-hashed file in dist/, a name this script cannot know. Same
     `gp-base-config` island the tour engine reads. */
  let src = '';
  try {
    src = JSON.parse(document.getElementById('gp-base-config')?.textContent || '{}').userInfoModalUrl || '';
  } catch (_) { /* island missing or malformed - handled below */ }
  if (!src) return Promise.resolve(false);
  _userInfoModulePromise = new Promise(function (resolve) {
    const s = document.createElement('script');
    s.src = src;
    s.async = false;
    /* Same nonce trick the navigation loader uses: the strict CSP rejects an
       injected script without one. */
    const carrier = document.querySelector('script[nonce]');
    const nonce = carrier ? (carrier.nonce || carrier.getAttribute('nonce') || '') : '';
    if (nonce) s.setAttribute('nonce', nonce);
    const timer = setTimeout(function () { finish(false); }, 10000);
    function finish(ready) {
      clearTimeout(timer);
      s.onload = s.onerror = null;
      if (!ready) {
        _userInfoModulePromise = null;
        s.remove();
      }
      resolve(ready);
    }
    s.onload = function () { finish(Boolean(window.UserInfoModal)); };
    s.onerror = function () { finish(false); };
    document.head.appendChild(s);
  });
  return _userInfoModulePromise;
}

/* Admin -> Users keeps a modal of its own (it looks the user up by id and binds
   the per-user "enrich from GitLab" button, which the global one has no business
   knowing about), but it renders the SAME card - so it shares this loader rather
   than carrying a second copy of the "is the module here?" question.
   pages/admin-users.js is the caller; a dead-code sweep that did not read the
   page scripts removed this line once and took the whole modal with it. */
GP.ensureUserInfoModule = _ensureUserInfoModule;

/* One error state, reached from three places (module missing, request failed,
   request timed out) instead of one copy per place. */
async function _showUserInfoError(container, message, username, current) {
  /* The app's one error state - alert mark, message, retry - the same block a
     failed table or chart shows. What stood here was a bare red paragraph with
     a hand-built button, so the same failure looked like two different things
     depending on which modal you were in. */
  if (!await swapModalBodyAnimated(container, GP.errorStateHtml(message, GP.t('Retry')), current)) return;
  GP.bindRetry(container, function () {
    return window.openUserInfo(username);
  });
}

window.openUserInfo = async function openUserInfo(username) {
  if (!username) return;
  // Ensure modal container exists in the DOM
  let modal = document.getElementById('globalUserInfoModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'globalUserInfoModal';
    modal.className = 'modal-backdrop';
    modal.setAttribute('data-action', 'closeModalOnBackdrop');
    modal.setAttribute('data-action-args', '["$event"]');
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.innerHTML =
      '<div class="modal modal-md" role="document">' +
      '<div class="modal-header"><h3 class="modal-title">' + escapeHtml(GP.t('User Info')) + '</h3>' +
      GP.closeButtonHtml(GP.t('Close'), 'modal-close', { 'modal-close': 'globalUserInfoModal' }) +
      '</div>' +
      '<div class="modal-body" id="globalUserInfoContent"></div></div>';
    document.body.appendChild(modal);
  }
  const read = GP.beginUserInfoRead(modal, username);
  if (!read) return;
  const container = document.getElementById('globalUserInfoContent');
  /* Loader first, module second. Fetching user-info-modal.js is itself a network
     round trip, and awaiting it before painting anything left the click with no
     answer at all until it landed - an empty modal on a fast line, nothing at
     all on a slow one. */
  container.innerHTML = GP.renderLoaderHtml('Loading user info...');
  openModal('globalUserInfoModal');
  try {
    const ready = await _ensureUserInfoModule();
    if (!read.current()) return;
    if (!ready) {
      await _showUserInfoError(container, GP.t('Failed to load user info'), username, read.current);
      return;
    }
    const data = await GP.apiCall('/dashboard/admin/users/by-username/' + encodeURIComponent(username) + '/info',
      'GET', null, { key: 'global:user-info', signal: read.controller.signal, timeoutMs: 12000, maxRetries: 0 });
    if (!read.current()) return;
    if (data.detail && !data.profile) {
      // Same empty state the page-level modal shows for the same answer.
      await swapModalBodyAnimated(container, GP.emptyStateHtml(data.detail), read.current);
      return;
    }
    /* ONE renderer. The `else` that stood here rebuilt a lesser version of the
       card inline - no avatar, its own badge colour map, and "Courses (n)" /
       "Groups (n)" hard-coded past t() so they never translated. It existed
       only because the real renderer might not be on the page; it now always
       is, so the copy that was free to drift is gone. */
    await swapModalBodyAnimated(container, window.UserInfoModal.render(data), read.current);
  } catch (err) {
    if (!read.current() || err?.superseded) return;
    const _msg = err?.message || GP.t('Failed to load user info');
    await _showUserInfoError(container, _msg, username, read.current);
  } finally {
    read.finish();
  }
};

/**
 * Enable save-button guard for a modal form.
 * Disables the save button when the modal opens and enables it only when
 * form content differs from the snapshot taken at open time.
 *
 * @param {string} modalId - the modal backdrop id
 * @param {string} btnSelector - CSS selector for the save button inside the modal
 */
function initModalSaveGuard(modalId, btnSelector) {
  const el = document.getElementById(modalId);
  if (!el || el._gpModalSaveGuardEnabled) return;
  el._gpModalSaveGuardEnabled = true;
  enableFormDirtyGuard(modalId);
  let settleUntil = 0;

  function checkDirtyHandler() {
    const btn = el.querySelector(btnSelector);
    if (!el.isConnected || !el.classList.contains('active') || !btn) return;
    if (btn._gpModalSubmission || btn.classList.contains('loading') || btn.dataset.archivedLocked === '1') return;
    // Save and the unsaved-changes warning use the same opening baseline.
    // Animation class changes and settling timers must never adopt an edit.
    const settling = performance.now() < settleUntil && !el._gpUserEdited;
    btn.disabled = settling || !_isModalDirty(el, _formDirtySnapshots[modalId]);
  }

  el.addEventListener('input', checkDirtyHandler);
  el.addEventListener('change', checkDirtyHandler);
  const observer = new MutationObserver(function (mutations) {
    const opened = mutations.some(m => !String(m.oldValue || '').split(/\s+/).includes('active'));
    if (opened && el.classList.contains('active')) settleUntil = performance.now() + 600;
    checkDirtyHandler();
    if (!opened || !el.classList.contains('active')) return;
    // Recheck after the shared dirty guard settles untouched Alpine fields.
    [100, 600].forEach(delay => setTimeout(checkDirtyHandler, delay));
  });
  observer.observe(el, { attributes: true, attributeFilter: ['class'], attributeOldValue: true });
}

GP.initModalSaveGuard = initModalSaveGuard;
