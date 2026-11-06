/* ============================================
   Toast Notification System
   ============================================ */
const _FLASH_QUEUE_KEY = 'flash_toasts';
let _toastIdCounter = 0;
let _pressCount = 0;

const _toastState = {
  queue: [],
  /* Three, a stack a reader can still take in. Five was a pile: one action
     narrating its steps put a column of cards up the side of the page. The
     rest wait, in order, and each takes a slot as one frees - nothing on
     screen is ever pushed out while someone may be reading it. */
  maxVisible: 3,
  /** Map<string, number>  key -> timestamp of last shown toast for dedup */
  _recentMap: new Map(),
  /* Collapses BURSTS from one operation (an SSE echo landing next to the
     fetch's own callback). It must never swallow the feedback for a SECOND
     press of the same button - GP.resetToastDedup() below clears the slate
     whenever the user starts a new action. */
  _dedupWindowMs: 5000,
};

/** Read the persisted toast queue from sessionStorage. */
function _readFlashQueue() {
  try {
    const raw = sessionStorage.getItem(_FLASH_QUEUE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch (_) { return []; }
}

/** Write the toast queue to sessionStorage. */
function _writeFlashQueue(arr) {
  try {
    if (!arr || arr.length === 0) {
      sessionStorage.removeItem(_FLASH_QUEUE_KEY);
    } else {
      sessionStorage.setItem(_FLASH_QUEUE_KEY, JSON.stringify(arr));
    }
  } catch (_) {}
}

/** Add a toast payload to the persisted queue. */
function _enqueueFlash(payload) {
  const q = _readFlashQueue();
  // Cap queue at 10 to prevent runaway storage
  if (q.length >= 10) q.shift();
  q.push(payload);
  _writeFlashQueue(q);
}

/** Remove a toast from the persisted queue by its unique id. */
function _dequeueFlash(toastUid) {
  if (!toastUid) return;
  const q = _readFlashQueue();
  const filtered = q.filter(function(p) { return p.uid !== toastUid; });
  _writeFlashQueue(filtered);
}

function createToastContainer() {
  let container = document.getElementById('toastContainer');

  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'true');
    document.body.appendChild(container);
  }

  if (!container._toastClickBound) {
    container.addEventListener('click', (event) => {
      const closeBtn = event.target.closest('.toast-close');
      if (!closeBtn) {
        return;
      }
      const toast = closeBtn.closest('.toast');
      if (toast) {
        _dismissToast(toast);
      }
    });
    container._toastClickBound = true;
  }

  return container;
}

/* Names into GP.icons, not a seventh private table of glyphs. These were
   hand-written 24x24 stroked Feather paths - the last icon family left in the
   product after the move to Pajamas, on the component every page shows most. */
const _TOAST_ICONS = {
  info: 'info',
  success: 'check-circle',
  warning: 'alert-triangle',
  error: 'x-circle',
  danger: 'x-circle',
  tip: 'info',
  neutral: 'info',
};
function _toastIconHtml(type) {
  const name = _TOAST_ICONS[type] || _TOAST_ICONS.info;
  return GP.icons.get(name, 24, 'toast-icon');
}

function _toastTitle(type) {
  const titles = {
    info: 'Info',
    success: 'Success',
    warning: 'Warning',
    error: 'Error',
    danger: 'Error',
    tip: 'Tip',
    neutral: 'Notice',
  };
  return _translateUiText(titles[type] || 'Notice');
}

function _dismissToast(toast) {
  if (!toast || toast.dataset.removing === '1') {
    return;
  }
  toast.dataset.removing = '1';
  // Clear any pending auto-dismiss timer
  const tid = toast.dataset.timerId;
  if (tid) clearTimeout(Number(tid));

  // Remove this specific toast from the persisted queue so it won't
  // reappear after navigation.
  _dequeueFlash(toast.dataset.toastUid);

  /* Shrink back into its own place, then collapse the row so the stack
     reflows. GP.motion owns the timing and calls back when the element is
     actually gone - no `animationend` listener and no safety timeout racing
     it, which is what used to leave a dismissed toast in the DOM whenever the
     tab was backgrounded mid-animation. */
  toast.classList.add('toast-dismissing');
  GP.motion.toastOut(toast, () => {
    toast.remove();
    _flushToastQueue();
  });
}

function _flushToastQueue() {
  const container = createToastContainer();
  const visible = container.querySelectorAll('.toast:not([data-removing="1"])').length;
  if (visible >= _toastState.maxVisible) {
    return;
  }
  const next = _toastState.queue.shift();
  if (!next) {
    return;
  }
  // Small delay so the new toast doesn't overlap with the dismiss animation
  setTimeout(() => {
    _mountToast(container, next.toast, next.duration);
  }, 120);
}

/** Put a toast on screen: append, play its entrance, start its countdown bar
 *  and its dismissal timer. One place, so a queued toast behaves exactly like
 *  an immediate one - they used to diverge, and the queued one appeared with
 *  no entrance at all. */
function _mountToast(container, toast, duration) {
  // The toasts already up slide to their new slot rather than jumping there.
  GP.motion.toastReflow(container, () => container.appendChild(toast));
  GP.motion.toastIn(toast);
  if (duration > 0) {
    GP.motion.toastCountdown(toast.querySelector('.toast-progress-bar'), duration);
  }
  _startToastTimer(toast, duration);
}

function _startToastTimer(toast, duration) {
  if (!duration || duration <= 0) {
    return;
  }
  const timer = setTimeout(() => _dismissToast(toast), duration + 120);
  toast.dataset.timerId = String(timer);
  toast.dataset.duration = String(duration);
  toast.dataset.startedAt = String(Date.now());
  // Wall-clock dismissal deadline.  In a backgrounded tab, Chromium throttles
  // setTimeout to ~once per minute, which can leave a 5s success toast on
  // screen for minutes after the user returns.  A document-level
  // visibilitychange handler (installed below) sweeps for any toast past
  // its dismissAt and removes it immediately on tab focus.
  toast.dataset.dismissAt = String(Date.now() + duration + 120);

  // Hover-to-pause: stop timer and freeze progress bar animation (bind once)
  if (toast._toastHoverBound) return;
  toast._toastHoverBound = true;

  toast.addEventListener('mouseenter', () => {
    const tid = toast.dataset.timerId;
    if (tid) {
      clearTimeout(Number(tid));
      toast.dataset.timerId = '';
    }
    const elapsed = Date.now() - Number(toast.dataset.startedAt || Date.now());
    const remaining = Math.max(500, Number(toast.dataset.duration || 5000) - elapsed);
    toast.dataset.remaining = String(remaining);
    // Pause means the dismissAt deadline no longer applies until mouseleave.
    delete toast.dataset.dismissAt;
    toast.classList.add('toast-paused');
    GP.motion.toastPause(toast);
  });
  toast.addEventListener('mouseleave', () => {
    if (toast.dataset.removing === '1') return;
    toast.classList.remove('toast-paused');
    GP.motion.toastResume(toast);
    const remaining = Number(toast.dataset.remaining || 2000);

    const newTimer = setTimeout(() => _dismissToast(toast), remaining + 120);
    toast.dataset.timerId = String(newTimer);
    toast.dataset.startedAt = String(Date.now());
    toast.dataset.duration = String(remaining);
    toast.dataset.dismissAt = String(Date.now() + remaining + 120);
  });
}

// Flush any toast whose wall-clock dismissal deadline already passed while
// the tab was hidden - see comment in _startToastTimer.  Hover-paused toasts
// have their dismissAt cleared, so they are correctly skipped.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'visible') return;
  const container = document.querySelector('.toast-container');
  if (!container) return;
  const now = Date.now();
  container.querySelectorAll('.toast').forEach((toast) => {
    if (toast.dataset.removing === '1') return;
    if (toast.classList.contains('toast-paused')) return;
    const due = Number(toast.dataset.dismissAt || 0);
    if (due && now >= due) _dismissToast(toast);
  });
});

/* How many times the reader has pressed something: a pointer going down
   (not on a toast - closing or holding one is not an action), or Enter /
   Space, the keys that press a focused control. A toast remembers the count
   it was last said at; see _toastAgain. */
document.addEventListener('pointerdown', function (e) {
  if (e.isTrusted && !e.target.closest?.('.toast-container')) _pressCount++;
}, true);
document.addEventListener('keydown', function (e) {
  if (e.isTrusted && (e.key === 'Enter' || e.key === ' ')) _pressCount++;
}, true);

/* A fresh user action is entitled to fresh feedback, even when it produces the
   same message as a moment ago. Called by the shared action runner. */
GP.resetToastDedup = function () { _toastState._recentMap.clear(); };

/* A toast is the app's universal "that finished" - and it already says WHICH way
   it finished. Hand the control the user actually pressed its matching outcome
   at the same moment, so the answer appears where they are looking instead of
   only in the corner.

   Forwarding the FAILURE matters as much as the success: it is what releases the
   button from the pairing. While only success was forwarded, a failed action
   stayed armed, and the next success toast from anywhere - a poll, a background
   sync, another widget - painted a green tick on the control that had just
   failed. An `info` toast is not an ending (actions narrate progress with one),
   so it passes through untouched. */
function _signalActionOutcome(normalizedType, button) {
  if (!window.GP) return;
  // Concurrent refreshes report to the control that started this request.
  if (button !== undefined) {
    if (!button?.isConnected) return;
    GP._releaseActiveAction(button);
    if (normalizedType === 'success') GP.setButtonDone(button);
    else if (normalizedType === 'danger') GP.setButtonError(button);
    return;
  }
  if (normalizedType === 'success') {
    if (typeof GP._markActiveActionDone === 'function') GP._markActiveActionDone();
  } else if (normalizedType === 'danger') {
    if (typeof GP._markActiveActionFailed === 'function') GP._markActiveActionFailed();
  } else if (normalizedType === 'warning') {
    if (typeof GP._releaseActiveAction === 'function') GP._releaseActiveAction();
  }
}

/* `_opts.once`: a toast the PAGE raises about its own state (the Events page's
   webhook warning), not one the reader asked for. Still on screen - carried
   over from the page before, or the page opened again - it is left exactly as
   it is: not said again, not counted. The reader did nothing new.
   A copy carried over from the page before (`_fromRestore`) that finds its
   twin already up is not an event either: it is dropped, from storage too,
   so it cannot come back on a later page. */
function showToast(message, type = 'info', duration = 5000, _opts = {}) {
  /* Normalize 'error' -> 'danger' for consistent CSS class mapping */
  const normalizedType = type === 'error' ? 'danger' : type;

  /* The same toast (type and message) already on screen, if it is. */
  const _sameAlreadyUp = function (t) {
    return t && t.dataset && t.dataset.toastType === normalizedType
      && t.dataset.toastMessage === String(message || '');
  };
  const _liveContainer = document.getElementById('toastContainer') || document.querySelector('.toast-container');
  const _liveSame = _liveContainer
    ? Array.from(_liveContainer.querySelectorAll('.toast:not([data-removing="1"])')).find(_sameAlreadyUp)
    : null;

  /* -- Deduplication: suppress identical toast within a short time window -- */
  const dedupKey = normalizedType + '::' + String(message || '');
  const now = Date.now();
  const lastShown = _toastState._recentMap.get(dedupKey);
  if (lastShown && now - lastShown < _toastState._dedupWindowMs) {
    /* Suppressed as a duplicate - but the ACTION still finished, so the control
       the user pressed must still report it. Without this, pressing Refresh
       twice showed feedback only the first time ("toasts work every other
       time"): the second call returned here before anything was signalled. */
    _signalActionOutcome(normalizedType, _opts.button);
    if (_opts._fromRestore) _dequeueFlash(_opts._uid);
    else if (!_opts.once) _toastAgain(_liveSame, duration);
    return null;
  }
  /* -- ...and the same toast while it is STILL ON SCREEN (or waiting for a
     slot), however long ago it was raised. The 5s window above only covers a
     burst; a 12s warning raised again at second 6 by a poll, a refresh or a
     page re-render stacked a second identical toast under the first - the
     "why show it again, it is already there". Not stacked: the one on
     screen answers instead (_toastAgain). */
  if (_liveSame || _toastState.queue.some(function (q) { return _sameAlreadyUp(q.toast); })) {
    _signalActionOutcome(normalizedType, _opts.button);
    if (_opts._fromRestore) _dequeueFlash(_opts._uid);
    else if (!_opts.once) _toastAgain(_liveSame, duration);
    return null;
  }
  _toastState._recentMap.set(dedupKey, now);
  // Prune old entries periodically to avoid memory leak
  if (_toastState._recentMap.size > 50) {
    for (const [k, ts] of _toastState._recentMap) {
      if (now - ts > _toastState._dedupWindowMs) _toastState._recentMap.delete(k);
    }
  }

  _signalActionOutcome(normalizedType, _opts.button);

  // Assign a unique ID for queue tracking
  const toastUid = _opts._uid || ('t' + (++_toastIdCounter) + '_' + now);

  const container = createToastContainer();
  const toast = document.createElement('div');

  /* Map duration -> CSS utility class, with inline override for exact sync */
  const ttlBuckets = [2000, 3000, 4000, 5000, 7000, 10000];
  const bucket = ttlBuckets.reduce((prev, cur) =>
    Math.abs(cur - duration) < Math.abs(prev - duration) ? cur : prev, 5000);
  const ttlClass = duration <= 0 ? 'toast-ttl-infinite' : `toast-ttl-${bucket}`;
  toast.className = `toast toast-${normalizedType} ${ttlClass}`;
  /* Progress bar finishes slightly before JS timer fires (120 ms headroom)
     so the bar always reaches 0 % before the dismiss animation starts. */
  if (duration > 0) {
    toast.style.setProperty('--_toast-ttl', duration + 'ms');
  }

  /* Parsed from the registry's markup rather than assembled attribute by
     attribute, so the toast carries exactly the glyph, viewBox and fill every
     other icon in the app does. */
  const iconHolder = document.createElement('template');
  iconHolder.innerHTML = _toastIconHtml(normalizedType);
  const icon = iconHolder.content.firstElementChild;

  const content = document.createElement('div');
  content.className = 'toast-content';

  const title = document.createElement('p');
  title.className = 'toast-title';
  title.textContent = _toastTitle(normalizedType);

  const body = document.createElement('p');
  body.className = 'toast-message';
  body.textContent = _translateUiText(String(message || ''));

  const closeHolder = document.createElement('template');
  closeHolder.innerHTML = GP.closeButtonHtml(_translateUiText('Close'), 'toast-close');
  const closeBtn = closeHolder.content.firstElementChild;

  const progress = document.createElement('div');
  progress.className = 'toast-progress';
  const progressBar = document.createElement('span');
  progressBar.className = 'toast-progress-bar';
  /* Animation duration driven entirely by --toast-ttl CSS custom property */
  progress.appendChild(progressBar);

  content.appendChild(title);
  content.appendChild(body);

  if (icon) toast.appendChild(icon);
  toast.appendChild(content);
  toast.appendChild(closeBtn);
  toast.appendChild(progress);

  // Tag with unique ID for queue tracking
  toast.dataset.toastUid = toastUid;
  toast.dataset.toastMessage = String(message || '');
  toast.dataset.toastType = normalizedType;
  toast.dataset.toastDuration = String(duration);
  toast.dataset.toastCreatedAt = String(now);
  toast.dataset.toastPress = String(_pressCount);

  // Persist to sessionStorage queue so toast survives page navigation
  if (!_opts._fromRestore) {
    _enqueueFlash({
      uid: toastUid,
      message: String(message || ''),
      type: normalizedType,
      duration: duration,
      createdAt: now,
    });
  }

  _admitToast(container, toast, duration);

  return toast;
}

/* The same toast asked for again while it is still up. It is not stacked a
   second time; the one on screen answers - it knocks and rings
   (GP.motion.toastAgain) - and its countdown starts over, so whoever raised it
   again gets the full time to read it. A toast still waiting in the queue has
   nothing on screen to point at, and will get its full time when it lands. */
function _toastAgain(toast, duration) {
  if (!toast || !toast.isConnected || toast.dataset.removing === '1') return;
  /* Only a new press makes it "said again". One press can raise the same
     message twice - the request's own answer and the server's event echoing
     it - and that echo read as "x2" after a single click. */
  if (Number(toast.dataset.toastPress) === _pressCount) return;
  toast.dataset.toastPress = String(_pressCount);
  /* How many times it has been said, beside its title: "x2", "x3" - the answer
     to "did my second click do anything?" that a copy used to give by piling
     up. The live region is atomic, so the change is announced as well. */
  const times = (Number(toast.dataset.toastRepeat) || 1) + 1;
  toast.dataset.toastRepeat = String(times);
  const title = toast.querySelector('.toast-title');
  if (title) {
    let chip = title.querySelector('.toast-repeat');
    if (!chip) {
      chip = document.createElement('span');
      chip.className = 'toast-repeat';
      title.appendChild(chip);
    }
    chip.textContent = '\u00d7' + times;
  }
  GP.motion.toastAgain(toast);

  const ttl = Math.max(Number(toast.dataset.toastDuration || 0), Number(duration) || 0);
  if (ttl <= 0) return;
  const bar = toast.querySelector('.toast-progress-bar');
  const now = Date.now();
  toast.dataset.toastDuration = String(ttl);
  toast.dataset.toastCreatedAt = String(now);
  const q = _readFlashQueue();
  q.forEach(function (p) {
    if (p.uid === toast.dataset.toastUid) { p.createdAt = now; p.duration = ttl; }
  });
  _writeFlashQueue(q);

  if (toast.classList.contains('toast-paused')) {
    /* The pointer is holding it: a full countdown, frozen until mouseleave
       resumes it from there. */
    toast.dataset.remaining = String(ttl);
    GP.motion.toastCountdown(bar, ttl);
    GP.motion.toastPause(toast);
    return;
  }
  const tid = toast.dataset.timerId;
  if (tid) clearTimeout(Number(tid));
  GP.motion.toastCountdown(bar, ttl);
  _startToastTimer(toast, ttl);
}

/* Put a toast on screen if there is a free slot and nobody is already waiting
   for one; otherwise it joins the line. The line is drained as toasts leave
   (see _dismissToast), so a queued toast is admitted by exactly this rule. */
function _admitToast(container, toast, duration) {
  const live = container.querySelectorAll('.toast:not([data-removing="1"])').length;
  if (live < _toastState.maxVisible && _toastState.queue.length === 0) {
    _mountToast(container, toast, duration);
  } else {
    _toastState.queue.push({ toast, duration });
  }
}

/** flashToast - convenience alias for showToast with reload-friendly defaults.
 *  Since showToast already persists every toast to sessionStorage,
 *  there is no separate persistence mechanism; flashToast simply
 *  picks sensible default durations when none is specified.            */
function flashToast(message, type = 'success', duration = 0) {
  let effectiveDuration = duration;
  if (!effectiveDuration) {
    effectiveDuration = (type === 'danger' || type === 'error') ? 7000 : 5000;
  }
  return _rawShowToast(message, type, effectiveDuration);
}

// Keep a direct reference to the raw showToast before we alias window.showToast
const _rawShowToast = showToast;

/* No per-variant wrappers. `showToast(message, variant)` already takes the
   variant, and the five `showSuccessToast` / `showErrorToast` / ... aliases were
   a second way to say the same thing that nothing ever called - 42 call sites
   in _parts/ all use showToast. The progress toast went with them: it was the
   only thing that built `.progress-toast`, and nothing built it. */

// showToast & flashToast - unified; both persist via sessionStorage queue
GP.showToast = _rawShowToast;
GP.flashToast = flashToast;
window.showToast = _rawShowToast;

/**
 * Immediately dismiss all currently visible (non-progress) toasts.
 * Called by the tour engine before showing the welcome card or starting
 * a tour so toasts don't overlap the highlighted area / welcome card.
 * Progress toasts (toast-ttl-infinite) are intentionally preserved.
 */
function dismissAllToasts() {
  try {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    container.querySelectorAll('.toast:not([data-removing="1"])').forEach((t) => {
      if (t.classList.contains('toast-ttl-infinite')) return;
      _dismissToast(t);
    });
    // Drain queued (not-yet-inserted) toasts too so they don't pop mid-tour
    _toastState.queue.length = 0;
  } catch (_) { /* noop */ }
}
GP.dismissAllToasts = dismissAllToasts;
window.dismissAllToasts = dismissAllToasts;

window.flashToast = flashToast;

/**
 * Broadcast a toast to ALL other open tabs via localStorage.
 * The originating tab should call showToast() directly; other tabs pick
 * it up through the 'storage' event.
 */
const CROSS_TOAST_KEY = 'gitpulse_cross_toast';
function broadcastToast(message, type, duration) {
  try {
    localStorage.setItem(CROSS_TOAST_KEY, JSON.stringify({
      message: String(message || ''),
      type: String(type || 'info'),
      duration: duration || 5000,
      ts: Date.now(),
    }));
    // Remove immediately - the storage event fires in other tabs even if key
    // is deleted right away. This prevents stale payloads on next load.
    localStorage.removeItem(CROSS_TOAST_KEY);
  } catch (_) {
    // ignore storage errors
  }
}
GP.broadcastToast = broadcastToast;
window.broadcastToast = broadcastToast;

// Listen for cross-tab toast broadcasts
window.addEventListener('storage', (e) => {
  if (e.key !== CROSS_TOAST_KEY || !e.newValue) return;
  if (document.hidden) return; // Do not show toasts in background tabs
  try {
    const payload = JSON.parse(e.newValue);
    if (payload && payload.message) {
      const dur = typeof payload.duration === 'number' ? payload.duration : 5000;
      _rawShowToast(payload.message, payload.type || 'info', dur);
    }
  } catch (_) {
    // ignore parse errors
  }
});



(function _restoreFlashToasts() {
  try {
    // Migrate legacy single-toast key if present
    const legacyRaw = sessionStorage.getItem('flash_toast');
    if (legacyRaw) {
      try {
        const legacy = JSON.parse(legacyRaw);
        if (legacy && legacy.message) {
          const uid = legacy.uid || ('t_legacy_' + Date.now());
          legacy.uid = uid;
          _enqueueFlash(legacy);
        }
      } catch (_) {}
      sessionStorage.removeItem('flash_toast');
    }

    const queue = _readFlashQueue();
    if (!queue.length) return;
    // Clear queue immediately to prevent double-showing on rapid reloads
    _writeFlashQueue([]);

    const now = Date.now();
    // A toast still on screen when the user navigated was cut short - it was
    // captured by _preserveFlashToast() on beforeunload precisely because it
    // was still visible.  Page-load time then eats into its remaining life,
    // and for short (4 s) toasts like "Group synced" / "Sync completed!" this
    // drove `remaining` negative, so the confirmation was silently dropped on
    // the destination page (the intermittent "toast disappears on navigation"
    // bug).  Guarantee a minimum visible window so the success message always
    // lands after a page transition.  Genuinely stale entries (left in
    // storage by a long-abandoned tab) are still discarded.
    const MIN_RESTORE_MS = 2500;
    const STALE_MS = 60000;
    for (let i = 0; i < queue.length; i++) {
      const payload = queue[i];
      const dur = typeof payload.duration === 'number' ? payload.duration : 5000;
      const elapsed = payload.createdAt ? Math.max(0, now - payload.createdAt) : 0;
      // Drop only genuinely stale toasts, not ones merely cut short by nav.
      if (elapsed > dur + STALE_MS) continue;
      const natural = dur - elapsed;
      const remaining = Math.max(natural, MIN_RESTORE_MS);
      // When we floor the lifetime, restart the progress bar from full so it
      // animates over `remaining` instead of showing an already-drained bar.
      const freshBar = natural < MIN_RESTORE_MS;

      // Stagger each toast by 150ms so they don't all appear simultaneously
      const staggerDelay = 80 + (i * 150);
      setTimeout(function() {
        const toast = _rawShowToast(
          payload.message || '',
          payload.type || 'success',
          remaining,
          { _uid: payload.uid, _fromRestore: true }
        );
        // Offset progress-bar animation so it continues from where it was,
        // but only when we're honouring the natural remaining time.
        if (toast && elapsed > 0 && !freshBar) {
          const bar = toast.querySelector('.toast-progress-bar');
          if (bar) {
            bar.style.animationDuration = dur + 'ms';
            bar.style.animationDelay = '-' + elapsed + 'ms';
          }
        }
      }, staggerDelay);
    }
  } catch (_) {
    try { sessionStorage.removeItem(_FLASH_QUEUE_KEY); } catch (_e) {}
  }
})();

/** Re-persist all currently visible toasts into sessionStorage so they
 *  survive an impending page navigation or browser reload.                  */
function _preserveFlashToast() {
  try {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const visible = container.querySelectorAll('.toast:not([data-removing="1"])');
    if (!visible.length) {
      _writeFlashQueue([]);
      return;
    }
    const now = Date.now();
    const queue = [];
    visible.forEach(function(el) {
      const msg = el.dataset.toastMessage;
      if (!msg) return;
      const dur = Number(el.dataset.toastDuration || 5000);
      const createdAt = Number(el.dataset.toastCreatedAt || now);
      const elapsed = now - createdAt;
      if (dur > 0 && elapsed >= dur) return; // already expired
      queue.push({
        uid: el.dataset.toastUid || ('t_preserve_' + (++_toastIdCounter)),
        message: msg,
        type: el.dataset.toastType || 'info',
        duration: dur,
        createdAt: createdAt,
      });
    });
    _writeFlashQueue(queue);
  } catch (_) {}
}

GP._preserveFlashToast = _preserveFlashToast;
window._preserveFlashToast = _preserveFlashToast;

/* The tanuki mark, flat-filled. No <defs>/gradient ids: a page can hold several
   spinners at once and duplicate ids resolve to whichever appeared first, so
   the rest would borrow another spinner's colours. */
const _TANUKI_MARK =
  '<svg viewBox="0 0 48 48" class="gp-spinner-mark" aria-hidden="true" focusable="false">' +
    '<path fill="#fca326" d="M6 27.4152L17.9932 18.9935L23.9627 42Z"/>' +
    '<path fill="#fca326" d="M42 27.4152L30.9661 18.9935L23.9627 42Z"/>' +
    '<path fill="#fc6d26" d="M11.0151 6L17.9932 18.9935L6 27.4152Z"/>' +
    '<path fill="#fc6d26" d="M36.9957 6L30.9661 18.9935L42 27.4152Z"/>' +
    '<path fill="#e24329" d="M17.9932 18.9935H30.9661L23.9627 42Z"/>' +
  '</svg>';

/** THE loading mark for the whole app: the brand tanuki inside the same conic
 *  ring the full-page navigation loader turns, scaled down. One indicator
 *  everywhere means a table waiting for rows and a page waiting to arrive read
 *  as the same event instead of two unrelated widgets. */
function renderSpinnerHtml(size = 'md') {
  const label = GP.t('Loading');
  const s = ['xs', 'sm', 'md', 'lg'].indexOf(size) === -1 ? 'md' : size;
  return `<span class="gp-spinner gp-spinner--${s}" role="status" aria-label="${escapeHtml(label)}">${_TANUKI_MARK}</span>`;
}

/* The block loading mark for JS-built content - the same box the
   `block_loading` macro renders (spinner over label, centred), so a modal or a card filled by script loads exactly like one
   filled by the server. It used to be a mark of its own (`.user-info-loading`,
   an italic caption) beside the shared one. */
function renderLoaderHtml(message = '', size = 'md') {
  const msgEscaped = message ? escapeHtml(GP.t(message)) : '';
  const spinner = renderSpinnerHtml(size);
  return `<div class="gp-block-loading" role="status" aria-live="polite">` +
    spinner +
    (msgEscaped ? `<p class="gp-block-loading-text">${msgEscaped}</p>` : '') +
  `</div>`;
}


GP.tanukiMarkHtml = function () { return _TANUKI_MARK; };
GP.renderSpinnerHtml = renderSpinnerHtml;
GP.renderLoaderHtml = renderLoaderHtml;
window.renderSpinnerHtml = renderSpinnerHtml;
window.renderLoaderHtml = renderLoaderHtml;
