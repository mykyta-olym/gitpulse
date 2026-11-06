/* ============================================
   THE badge, in JS
   ============================================
   `components/badges.html` renders every badge the server draws; eight JS files
   were assembling the same span by hand, so the class order, the size suffix and
   the escaping were decided per call site (several interpolated untrusted text
   straight into the string). Same signature as the Jinja macro - text, variant,
   size - so a badge written in a template and one written in a renderer are the
   same component.

   @param {string} text        already-translated; escaped here
   @param {string} [variant]   gray | info | success | warning | danger | muted ...
   @param {{size?: string, class?: string, tooltip?: string, icon?: string}} [opts] */
function badgeHtml(text, variant, opts) {
  const o = opts || {};
  const size = o.size === 'sm' ? ' badge-sm' : o.size === 'lg' ? ' badge-lg' : '';
  const extra = o.class ? ' ' + o.class : '';
  const tip = o.tooltip ? ' data-tippy-content="' + escapeHtml(o.tooltip) + '"' : '';
  return '<span class="badge badge-' + (variant || 'gray') + size + extra + '"' + tip + '>' +
         (o.icon ? GP.iconSvg(o.icon, 'xs') : '') +
         escapeHtml(String(text == null ? '' : text)) + '</span>';
}
GP.badgeHtml = badgeHtml;

// The text form of components/badges.html's traffic_light macro.
function trafficLightHtml(status) {
  const value = String(status || 'GRAY').toUpperCase();
  const parts = {
    GREEN: ['success', 'All compliance checks are passing'],
    AMBER: ['warning', 'Some compliance checks need attention'],
    YELLOW: ['warning', 'Some compliance checks need attention'],
    RED: ['danger', 'Critical compliance checks are failing'],
    GRAY: ['gray', 'No compliance data available'],
    GREY: ['gray', 'No compliance data available'],
  }[value] || ['gray', ''];
  return badgeHtml(GP.t(value), parts[0], { tooltip: GP.t(parts[1]) });
}
GP.trafficLightHtml = trafficLightHtml;

function updateScoreCell(cell, score, greenPct, yellowPct) {
  const hasScore = score !== null && score !== undefined;
  if (!cell.classList.contains('member-badge-cell')) cell.classList.add('member-badge-cell');
  cell.classList.toggle('text-muted', !hasScore);
  const sortValue = hasScore ? String(score) : '-1';
  if (cell.dataset.sortValue !== sortValue) cell.dataset.sortValue = sortValue;
  const variant = score >= greenPct ? 'green' : score >= yellowPct ? 'amber' : 'red';
  const html = hasScore ? GP.badgeHtml(score + '%', variant) : '-';
  if (cell.innerHTML.trim() !== html) cell.innerHTML = html;
}
GP.updateScoreCell = updateScoreCell;

/* THE role badge, in JS - the `role_badge` macro's colour and translated word.
   `tests/unit/test_role_badge_colours.py` pins this map to the macro's. */
const ROLE_BADGE_VARIANTS = { admin: 'warning', teacher: 'purple', ta: 'info', mentor: 'teal', student: 'secondary' };
function roleBadgeParts(role) {
  const key = String(role || '').toLowerCase();
  const label = { admin: GP.t('Admin'), teacher: GP.t('Teacher'), ta: 'TA', student: GP.t('Student') }[key]
    || key.charAt(0).toUpperCase() + key.slice(1);
  return { variant: ROLE_BADGE_VARIANTS[key] || 'secondary', label: label };
}
function roleBadgeHtml(role) {
  const r = roleBadgeParts(role);
  return badgeHtml(r.label, r.variant, { size: 'sm' });
}
GP.roleBadgeParts = roleBadgeParts;
GP.roleBadgeHtml = roleBadgeHtml;

/* THE alert, in JS - the `alert` macro (components/alerts.html), GitLab's
   GlAlert. `bodyHtml` is markup the caller has already escaped.
   @param {{title?: string, icon?: string, class?: string}} [opts] */
const ALERT_ICONS = { info: 'info', success: 'check-circle', warning: 'alert-triangle', danger: 'alert-circle', error: 'alert-circle' };
function alertHtml(bodyHtml, variant, opts) {
  const o = opts || {};
  const v = variant || 'info';
  return '<div class="gitlab-alert gitlab-alert-' + v + (o.class ? ' ' + o.class : '') + '" role="alert">' +
    '<div class="gitlab-alert-icon" aria-hidden="true">' + GP.iconSvg(o.icon || ALERT_ICONS[v] || 'info', 'sm') + '</div>' +
    '<div class="gitlab-alert-content">' +
    (o.title ? '<p class="gitlab-alert-title">' + escapeHtml(o.title) + '</p>' : '') +
    '<div class="gitlab-alert-message">' + bodyHtml + '</div></div></div>';
}
GP.alertHtml = alertHtml;

/* ============================================
   THE timestamp, in JS
   ============================================
   Mirror of the `localized_time` macro (components/time.html), for markup that
   JS builds. Preferences offers "Time format" and "Use relative times", and
   `localize-time.js` applies both to `time[data-localize-time]` and to nothing
   else - so a stamp written with `new Date(x).toLocaleString()` silently
   ignores whatever the reader chose. Ten call sites did exactly that, which is
   most of why those two settings looked decorative.

   The element is inert until `localizeTimes()` runs over it, so the text passed
   here is what shows in the meantime; callers that insert into the live DOM
   should call `window.localizeTimes(container)` afterwards, exactly as the
   progress banner does.

   @param {string} iso        UTC ISO stamp from the server
   @param {string} [format]   '' | 'date' | 'time' | 'monthday-time' | 'relative'
   @param {string} [fallback] shown when `iso` is missing */
function timeHtml(iso, format, fallback) {
  const empty = fallback === undefined ? '-' : fallback;
  if (!iso) return escapeHtml(empty);
  const d = new Date(iso);
  if (isNaN(d.getTime())) return escapeHtml(String(iso));
  const pad = (n) => (n < 10 ? '0' + n : String(n));
  const day = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  const shown = format === 'date' ? day : day + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  return '<time datetime="' + escapeHtml(String(iso)) + '" data-localize-time'
    + (format ? ' data-localize-format="' + escapeHtml(format) + '"' : '')
    + '>' + escapeHtml(shown) + '</time>';
}
GP.timeHtml = timeHtml;

document.addEventListener('click', function (event) {
  const button = event.target.closest('[data-table-detail-toggle]');
  if (!button) return;
  const row = document.getElementById(button.getAttribute('aria-controls'));
  if (!row || row.closest('table') !== button.closest('table')) return;
  const expanded = button.getAttribute('aria-expanded') !== 'true';
  button.setAttribute('aria-expanded', String(expanded));
  row.classList.toggle('d-none', !expanded);
  button.closest('tr').classList.toggle('expanded', expanded);
  if (expanded) {
    const scroller = button.closest('.table-responsive');
    if (scroller) scroller.scrollLeft = 0;
  }
});

/* ============================================
   THE empty state, in JS
   ============================================
   The server has `empty_state()` / `table_empty()`; four places built the same
   markup by hand instead - core's own table loader, the compliance-checks error
   branch, the paginator's filtered-to-zero state and the member filters - each
   with its own idea of whether there is an icon, which icon, and whether the
   message is escaped. One shape and one escaping rule, so a JS-rendered empty
   state and a server-rendered one are the same thing. The shape is
   GlEmptyState's at its sm size: a GitLab illustration, then the message.

   @param {string} message         already-translated text; escaped here
   @param {string} [illustration]  'status-nothing-sm' (default), 'search-sm'
                                   for a filter that matched nothing,
                                   'chart-bar-sm' for a chart with no data
   @returns {string} HTML for the inside of a container or a full-width cell */
function emptyStateHtml(message, illustration) {
  return '<div class="table-empty-state">' + illustrationSlot(illustration || 'status-nothing-sm') +
         '<p class="table-empty-message">' + escapeHtml(String(message || '')) + '</p></div>';
}
GP.emptyStateHtml = emptyStateHtml;

/* The illustration slot, filled from base.html's #gpStateIllustrations - the
   vendored @gitlab/svgs files the Jinja macros include. */
function illustrationSlot(name) {
  const tpl = document.getElementById('gpStateIllustrations');
  const art = tpl && tpl.content.querySelector('[data-illustration="' + name + '"]');
  return '<div class="table-empty-icon" aria-hidden="true">' + (art ? art.innerHTML : '') + '</div>';
}

/* -- Selected rows --
   A ticked row checkbox marks its <tr> `is-selected` (tables.css paints it in
   the selected tint), so a reader sees WHICH rows a "Delete selected" will
   act on. One delegated listener for every table: Job History, the event
   queues and Support Tickets each wired their own count and select-all and
   none of them marked the row. A select-all in the <thead> sets the row
   boxes programmatically (no change events), so it re-syncs every row from
   the box's state instead. Only `*-select` boxes: a checkbox that is itself
   the row's data (a check's Active toggle) is not a selection. */
document.addEventListener('change', function (evt) {
  const cb = evt.target;
  if (!cb || cb.type !== 'checkbox') return;
  const table = cb.closest('table.data-table');
  if (!table) return;
  if (cb.closest('thead')) {
    table.querySelectorAll('tbody > tr').forEach(function (tr) {
      const box = tr.querySelector('input[type="checkbox"][class*="-select"]');
      tr.classList.toggle('is-selected', !!(box && box.checked));
    });
    return;
  }
  if (!/-select(\s|$)/.test(cb.className)) return;
  const row = cb.closest('tr');
  if (row) row.classList.toggle('is-selected', cb.checked);
});

/** The same thing as a full-width table row, for a tbody that has to say it is
 *  empty without changing the table's shape. */
function emptyStateRow(cols, message, illustration) {
  return '<tr class="table-empty-row"><td colspan="' + (cols || 1) + '">' +
         emptyStateHtml(message, illustration) + '</td></tr>';
}
GP.emptyStateRow = emptyStateRow;

/** The FAILURE twin of the two above. "Nothing here" and "this could not be
 *  loaded" are different answers and must not look the same, but each of them
 *  has to look the same wherever it appears - and the error half did not: a
 *  table row in one place, a bare `<p class="text-danger p-4">` in two others,
 *  a red span inside a button in a fourth, each with its own words and none
 *  with a way to retry. */
function errorStateHtml(message, retryLabel) {
  const retry = retryLabel
    ? '<button type="button" class="btn btn-sm btn-secondary gp-retry-btn">' +
      escapeHtml(String(retryLabel)) + '</button>'
    : '';
  return '<div class="table-empty-state table-empty-state--error" role="alert">' +
         illustrationSlot('status-fail-sm') +
         '<p class="table-empty-message">' + escapeHtml(String(message || '')) + '</p>' +
         retry + '</div>';
}
GP.errorStateHtml = errorStateHtml;

/* Wire the Retry button an error state was rendered with.
   The retry is a button like any other, so it carries the loading state while
   the work it kicked off runs - it used to be the one control in the app that
   went dead silent on click, which reads as "nothing happened" on exactly the
   slow connection that produced the error. Bound here, not at each call site,
   so it cannot be wired one way in one place and another way in the next.

   @param {HTMLElement} container - whatever errorStateHtml was rendered into
   @param {Function} onRetry - may return a promise; the state lasts as long as it */
function bindRetry(container, onRetry) {
  const btn = container && container.querySelector('.gp-retry-btn');
  if (!btn) return;
  btn.addEventListener('click', function () {
    GP.setButtonLoading(btn, true);
    Promise.resolve().then(onRetry).catch(function () {
      /* The retried call renders its own error state; nothing to add here. */
    }).finally(function () {
      // A successful retry replaces this very node - only a survivor needs reset.
      if (btn.isConnected) GP.setButtonLoading(btn, false);
    });
  });
}
GP.bindRetry = bindRetry;

/** The same thing as a full-width table row. */
function errorStateRow(cols, message, retryLabel) {
  return '<tr class="table-empty-row"><td colspan="' + (cols || 1) + '">' +
         errorStateHtml(message, retryLabel) + '</td></tr>';
}
GP.errorStateRow = errorStateRow;

/* ============================================
   THE refresh contract
   ============================================
   A "reload this region" control owes the reader four things, and every call
   site was assembling them by hand:

     1. the CONTROL shows it is working            (setButtonLoading)
     2. the REGION shows it is working             (the loader's own state)
     3. the outcome is reported, and reported ONCE (success XOR failure)
     4. it ENDS.

   (3) is where this came from: a loader that caught its own error, toasted it
   and returned normally left its caller unable to tell failure from success, so
   the caller toasted "reloaded" on top of the error. A failed refresh said both
   "failed" and "OK" - the reported bug. Here the loader either resolves or
   throws, and exactly one toast is emitted.

   (4) is the other half of the same report ("it refreshes for a very long
   time"): apiCall defaults to a 20s timeout with 2 retries, so a wedged
   endpoint can hold a button spinning for over a minute. A person is watching
   THIS request, so an interactive refresh gets one attempt on a 10s cap and
   fails visibly instead - the reader can press it again, which is faster than
   any retry ladder and tells them the truth in the meantime.

   A loader may resolve false when its result was superseded or deferred;
   that ends the control's state without announcing an unapplied result.

   @param {{button?: Element, region?: Element, load: (opts: object) => Promise<any>,
            successMessage?: string, errorMessage?: string}} options
   @returns {Promise<boolean>} whether the refresh succeeded
*/
const REFRESH_REQUEST_OPTS = { timeoutMs: 10000, maxRetries: 0 };
const _refreshOwners = new WeakSet();

async function refreshRegion(options) {
  const opts = options || {};
  if (typeof opts.load !== 'function') return false;
  const button = opts.button && opts.button.nodeType === 1 ? opts.button : null;
  const region = opts.region && opts.region.nodeType === 1 ? opts.region : null;
  const owners = [button, region].filter(Boolean);
  if (owners.some(owner => _refreshOwners.has(owner))) return false;
  owners.forEach(owner => _refreshOwners.add(owner));
  const finishProgress = GP.beginTopProgress();
  const previousBusy = region?.getAttribute('aria-busy');
  const previousInert = region?.inert;
  const wasRefreshing = region?.classList.contains('is-refreshing');
  if (region) {
    region.setAttribute('aria-busy', 'true');
    region.inert = true;
  }

  if (button) {
    setButtonLoading(button, true);
  }
  // A form's own button shows pending work without a second spinner over other fields.
  const busyTimer = region && button?.form !== region && !wasRefreshing
    ? setTimeout(() => region.classList.add('is-refreshing'), _BUSY_DELAY_MS) : 0;
  let success = false;
  try {
    const updated = await opts.load(REFRESH_REQUEST_OPTS);
    if (updated === false || (button && !button.isConnected) || (region && !region.isConnected)) return false;
    if (opts.successMessage) showToast(opts.successMessage, 'success', 5000, { button });
    success = true;
  } catch (err) {
    if (err?.superseded || (button && !button.isConnected) || (region && !region.isConnected)) return false;
    showToast(
      (err && err.message) || opts.errorMessage || _translateUiText('Refresh failed'),
      'danger', 5000, { button });
    success = false;
  } finally {
    finishProgress();
    clearTimeout(busyTimer);
    owners.forEach(owner => _refreshOwners.delete(owner));
    if (region) {
      region.classList.toggle('is-refreshing', !!wasRefreshing);
      if (previousBusy === null) region.removeAttribute('aria-busy');
      else region.setAttribute('aria-busy', previousBusy);
      region.inert = previousInert;
    }
    if (button && !success) GP._releaseActiveAction(button);
    if (button?.isConnected) {
      setButtonLoading(button, false);
    }
    if (region?.isConnected) region.dispatchEvent(new Event('gp:region-settled'));
  }
  return success;
}
GP.refreshRegion = refreshRegion;

/* A table keeps its rows and geometry while a read is pending. The semantic
   state starts immediately; the spinner waits briefly to avoid flashing for
   local filters and cache hits. Replacing the rows completes the read. */
const _BUSY_DELAY_MS = 180;

function tableLoading(tbody, cols) {
  if (!tbody || _refreshOwners.has(tbody) || tbody.parentElement?.closest('[aria-busy="true"]')) return;
  if (tbody._busyObserver) return;
  if (typeof window.tippy?.hideAll === 'function') window.tippy.hideAll({ duration: 0 });

  tbody._busyInert = tbody.inert;
  tbody._busyAria = tbody.getAttribute('aria-busy');
  tbody.inert = true;
  tbody.setAttribute('aria-busy', 'true');
  const box = tbody.closest('.table-responsive') || tbody.closest('table');
  if (box) {
    tbody._busyMinHeight = box.style.minHeight;
    const height = box.getBoundingClientRect().height;
    if (height > 40) box.style.minHeight = height + 'px';
  }

  const observer = new MutationObserver(function () { tableLoaded(tbody); });
  tbody._busyObserver = observer;
  observer.observe(tbody, { childList: true });
  const show = function () {
    tbody._busyTimer = 0;
    if (tbody.children.length) {
      tbody.classList.add('is-refreshing');
    } else {
      observer.disconnect();
      tbody.innerHTML =
        '<tr class="table-empty-row table-loading-row"><td colspan="' + cols + '">' +
        '<div class="table-empty-state table-loading-state">' +
        '<div class="table-empty-icon">' + GP.renderSpinnerHtml('md') + '</div>' +
        '<p class="table-empty-message">' + escapeHtml(GP.t('Loading...')) + '</p>' +
        '</div></td></tr>';
      observer.observe(tbody, { childList: true });
    }
  };
  tbody._busyTimer = setTimeout(show, _BUSY_DELAY_MS);
}
GP.tableLoading = tableLoading;

/** Finish after writing rows, including empty and error states. Call explicitly
 *  in finally when a refresh keeps the existing rows instead. */
function tableLoaded(tbody) {
  if (!tbody || _refreshOwners.has(tbody) || !tbody._busyObserver) return;
  clearTimeout(tbody._busyTimer);
  tbody._busyTimer = 0;
  tbody._busyObserver.disconnect();
  delete tbody._busyObserver;
  const box = tbody.closest('.table-responsive') || tbody.closest('table');
  if (box) box.style.minHeight = tbody._busyMinHeight;
  delete tbody._busyMinHeight;
  tbody.classList.remove('is-refreshing');
  if (tbody._busyAria === null) tbody.removeAttribute('aria-busy');
  else tbody.setAttribute('aria-busy', tbody._busyAria);
  tbody.inert = tbody._busyInert;
  delete tbody._busyAria;
  delete tbody._busyInert;
}
GP.tableLoaded = tableLoaded;
