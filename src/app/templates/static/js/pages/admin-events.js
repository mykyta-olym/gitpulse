/**
 * Admin Events page - DLQ management with batch resurrect, detail viewer, event replay, sortable columns.
 */
(function () {
  'use strict';

  const GP = window.GP;
  GP.runPageCleanup();

  const {
    apiCall,
    showToast,
    escapeHtml,
    t,
    withUiLock: _lock
  } = GP;
  const _DLQ_FETCH_LIMIT = 500;
  const _pageReads = new AbortController();
  let _disposed = false;
  let _eventDetailRead = 0;
  let _recentRead = 0;
  let _dlqRead = 0;

  /* -- Role config -- */
  let _cfg = {};
  try { const _ce = document.getElementById('gp-page-config'); if (_ce) _cfg = JSON.parse(_ce.textContent); } catch (_) { /* */ }
  const _canMutate = !!(_cfg.canReplay || _cfg.canResurrect || _cfg.isAdmin);
  const _canReplay = !!(_cfg.canReplay || _cfg.isAdmin);
  /* Resurrect used to live only on the dead-letter tab, so its own
     capability was never read here. The failed rows are in this table. */
  const _canResurrect = !!(_cfg.canResurrect || _cfg.isAdmin);

  const _startupWarning = _cfg && _cfg.startupWarning && typeof _cfg.startupWarning === 'object'
    ? _cfg.startupWarning
    : null;

  /* -- Selection management -- */
  /* Every bulk button over a selection follows the same rule: it is available
     exactly when something is ticked. Listing them keeps a new one from being
     added without its enabling, which is how Delete arrived beside a Resurrect
     that already had it. */
  function _armBulk(ids, count) {
    ids.forEach(function (id) {
      const btn = document.getElementById(id);
      if (btn) GP.refreshButtonDisabledState(btn, count === 0);
    });
  }

  /* Recent-events selection. Replay acts on ticked rows, so the same
     select-all / count / disabled-button contract the DLQ table already uses. */
  function updateRecentSelection() {
    const checked = document.querySelectorAll('.recent-select:checked');
    const countEl = document.getElementById('recentSelectedCount');
    if (countEl) countEl.textContent = checked.length;
    _armBulk(['btnReplaySelected', 'btnDeleteSelectedRecent', 'btnBatchResurrect'],
             checked.length);
  }

  /* -- Load DLQ events -- */
  /* The Details button has always called this, but it was never defined - so
     every click threw "viewEventDetail is not defined" and the payload viewer
     could not open, on the dead-letter rows just as much as anywhere else. */
  /* The endpoint returns the event's FACTS alongside the delivery, and the
     viewer used to stringify the lot into one <pre> - so "what arrived, was it
     handled, and why not" had to be read out of a dump. The facts are a
     property list now (the same component the webhook panel uses) and the raw
     delivery keeps the code viewer under it. */
  function syntaxHighlightJson(json) {
    if (typeof json !== 'string') {
      json = JSON.stringify(json, null, 2);
    }
    const escaped = escapeHtml(json);
    return escaped.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, function (match) {
      let cls = 'syntax-number';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'syntax-key';
        } else {
          cls = 'syntax-string';
        }
      } else if (/true|false/.test(match)) {
        cls = 'syntax-bool';
      } else if (/null/.test(match)) {
        cls = 'syntax-null';
      }
      return '<span class="' + cls + '">' + match + '</span>';
    });
  }

  function _fact(iconName, label, value, opts) {
    const o = opts || {};
    if (value === null || value === undefined || value === '') return '';
    const iconSvg = iconName ? `<span class="gl-kv-icon">${GP.iconSvg(iconName, 'xs')}</span>` : '';
    const valHtml = o.html ? value : `<span class="${o.class || ''}">${escapeHtml(String(value))}</span>`;
    return `<div class="gl-kv-row">
      <div class="gl-kv-label">${iconSvg}<span>${escapeHtml(label)}</span></div>
      <div class="gl-kv-value">${valHtml}</div>
    </div>`;
  }

  async function viewEventDetail(eventId) {
    if (_disposed) return;
    const read = ++_eventDetailRead;
    const modal = document.getElementById('eventDetailModal');
    if (!modal) return;
    const facts = document.getElementById('eventDetailFacts');
    const errEl = document.getElementById('eventDetailError');
    const copyBtn = document.getElementById('eventDetailCopyBtn');
    const payloadWrapper = document.getElementById('eventDetailPayloadContainer');

    if (errEl) errEl.innerHTML = '';
    if (copyBtn) copyBtn.classList.add('d-none');
    if (facts) facts.innerHTML = '';
    if (payloadWrapper) {
      // The app's one loading block, not a row of utility classes around a spinner.
      payloadWrapper.innerHTML = GP.renderLoaderHtml('Loading payload...');
    }

    GP.openModal('eventDetailModal');
    const version = modal._gpOpenVersion;
    const isCurrent = () => !_disposed && read === _eventDetailRead && modal.isConnected
      && modal._gpOpenVersion === version && modal.classList.contains('active')
      && !modal.classList.contains('closing');

    try {
      const data = await apiCall(`/api/v1/events/${encodeURIComponent(eventId)}/payload`,
        'GET', null, { key: 'events:detail', signal: _pageReads.signal });
      if (!isCurrent()) return;
      
      // Error message callout if present
      if (errEl) {
        if (data.processing_error) {
          /* The event's OWN stored error - data about the event, shown in the
             alert component (components/alerts.html), not a load failure. */
          errEl.innerHTML = GP.alertHtml(escapeHtml(String(data.processing_error)), 'danger',
            { title: t('Processing Error'), class: 'mb-4' });
        } else {
          errEl.innerHTML = '';
        }
      }

      // Metadata facts with icons
      if (facts) {
        const isFailed = !!data.processing_error || (!data.processed && !!data.dead_letter_at);
        let statusBadge;
        if (isFailed) {
          statusBadge = GP.badgeHtml(t('Failed'), 'danger', { icon: 'alert-circle' });
        } else if (data.processed) {
          statusBadge = GP.badgeHtml(t('Processed'), 'success', { icon: 'check-circle' });
        } else {
          statusBadge = GP.badgeHtml(t('Pending'), 'warning', { icon: 'clock' });
        }

        const actor = data.actor ||
          (data.payload && typeof data.payload === 'object'
            ? (data.payload.user_name || data.payload.user_username || data.payload.user?.name)
            : '');
        const message = data.summary || data.event_message || data.title ||
          (data.payload && typeof data.payload === 'object'
            ? (data.payload.object_attributes?.title || data.payload.object_attributes?.note || data.payload.message)
            : '');

        facts.innerHTML =
          _fact('tag', t('Type'), GP.badgeHtml(data.event_type || '', 'info'), {html: true})
          + _fact('shield', t('Status'), statusBadge, {html: true})
          + _fact('calendar', t('Received'), GP.timeHtml(data.received_at), {html: true})
          + (data.processed_at ? _fact('check-circle', t('Processed at'), GP.timeHtml(data.processed_at), {html: true}) : '')
          + _fact('folder', t('GitLab project'), data.gitlab_project_id)
          + (actor ? _fact('user', t('Who'), actor) : '')
          + (message ? _fact('message-square', t('What happened'), message) : '')
          + (data.action ? _fact('play', t('Action'), data.action) : '')
          + _fact('repeat', t('Retries'), data.retry_count != null ? data.retry_count : 0)
          + _fact('hash', t('Event ID'), `<code>${escapeHtml(data.id || '')}</code>`, {html: true});
      }

      // Payload handling: check for empty payload
      const payload = data.payload ?? data;
      const isEmpty = !payload || (typeof payload === 'object' && Object.keys(payload).length === 0);

      if (isEmpty) {
        if (copyBtn) copyBtn.classList.add('d-none');
        if (payloadWrapper) {
          payloadWrapper.innerHTML = GP.emptyStateHtml(t('GitLab sent an empty payload with this event.'));
        }
      } else {
        const jsonFormatted = JSON.stringify(payload, null, 2);
        if (payloadWrapper) {
          payloadWrapper.innerHTML = `<pre class="event-code-viewer" id="eventDetailJson"><code>${syntaxHighlightJson(jsonFormatted)}</code></pre>`;
        }
        if (copyBtn) {
          copyBtn.classList.remove('d-none');
          copyBtn.onclick = async function () {
            try {
              await navigator.clipboard.writeText(jsonFormatted);
              const label = copyBtn.querySelector('span');
              if (label) {
                const prev = label.textContent;
                label.textContent = t('Copied!');
                setTimeout(() => { label.textContent = prev; }, 2000);
              }
            } catch (_) {}
          };
        }
      }
    } catch (err) {
      if (!isCurrent() || err?.superseded) return;
      if (errEl) errEl.innerHTML = '';
      if (facts) facts.innerHTML = '';
      if (payloadWrapper) {
        /* With a retry. The modal is already open when the fetch fails, so
           without one the only way to try again was to close it and find the
           row again - the same dead end the User Info modal had. */
        payloadWrapper.innerHTML = GP.errorStateHtml(t('Could not load this event.'), t('Retry'));
        GP.bindRetry(payloadWrapper, function () { return viewEventDetail(eventId); });
      }
    }
  }

  /* The page only ever listed the dead-letter queue, so a healthy pipeline was
     indistinguishable from one receiving nothing. This is the normal flow. */
  /* Fetch is for REFRESH / type-filter / paging only. The first window is
     inlined into the page (#gp-recent-events) and rendered on load with no fetch
     and no loader - the instant-rows behaviour every server-rendered table has.
     See the init block below. */
  async function loadRecentEvents(eventType, options = {}) {
    if (_disposed) return false;
    const read = ++_recentRead;
    const tbody = document.getElementById('recentEventsTableBody');
    if (!tbody) return false;
    const isCurrent = () => !_disposed && read === _recentRead && tbody.isConnected;
    /* The loading state inherits the row count the table already has, so a
       refresh does not change its height at all. */
    GP.tableLoading(tbody, 9);

    let data;
    try {
      // A 200-row window gives the status filter something to filter over; the
      // paginator keeps the rendered page readable.
      let url = '/api/v1/events/recent?limit=200';
      if (eventType) url += '&event_type=' + encodeURIComponent(eventType);
      /* Keyed: changing the type filter twice in quick succession fired two
         requests and whichever answered LAST painted the table, which is not
         necessarily the one the reader asked for. */
      data = await apiCall(url, 'GET', null, { ...options, key: 'events:recent', signal: _pageReads.signal });
    } catch (err) {
      if (!isCurrent() || err?.superseded) return false;
      if (options.quiet) throw err;
      tbody.innerHTML = GP.errorStateRow(9, t('Could not load recent events.'), t('Retry'));
      GP.bindRetry(tbody, () => loadRecentEvents(_recentType()));
      GP.tableLoaded(tbody);
      return false;
    }
    if (!isCurrent()) return false;
    _renderRecentEvents(data.events || [], read, !options.keepView);
    return true;
  }

  /* Paint a recent-events window - from the fetch above OR the inlined first
     page. Computes the health counters, applies the client-side status filter,
     then renders the rows. */
  function _renderRecentEvents(all, read = _recentRead, resetPage = true) {
    const tbody = document.getElementById('recentEventsTableBody');
    if (!tbody) return;
    if (!_disposed && read === _recentRead && tbody.isConnected) _paintRecentEvents(tbody, all || [], resetPage);
  }

  function _paintRecentEvents(tbody, all, resetPage) {
    const selected = new Set(Array.from(tbody.querySelectorAll('.recent-select:checked'), cb => cb.value));
    /* Counters describe the whole window, not the filtered view - otherwise
       narrowing to "Failed" would make the health row read 0 processed. */
    const counts = { processed: 0, pending: 0, failed: 0 };
    all.forEach(function (ev) {
      if (ev.dead_letter_at) counts.failed += 1;
      else if (ev.processed) counts.processed += 1;
      else counts.pending += 1;
    });
    [['recentProcessed', counts.processed],
     ['recentPending', counts.pending],
     ['recentFailed', counts.failed]].forEach(function (pair) {
      const el = document.getElementById(pair[0]);
      if (el && el.textContent !== String(pair[1])) {
        el.textContent = String(pair[1]);
      }
    });

    // Status is filtered client-side over the fetched window, so the counters
    // above keep describing all of it.
    const wanted = (document.getElementById('recentStatusFilter') || {}).value || '';
    const events = !wanted ? all : all.filter(function (ev) {
      if (wanted === 'failed') return !!ev.dead_letter_at;
      if (wanted === 'processed') return !ev.dead_letter_at && ev.processed;
      return !ev.dead_letter_at && !ev.processed;
    });

    if (!events.length) {
      tbody.innerHTML = GP.emptyStateRow(9,
        all.length ? t('No events match these filters.') : t('No events received yet.'),
        all.length ? 'search-sm' : 'status-nothing-sm');
      const recentAll = document.getElementById('recentSelectAll');
      if (recentAll) recentAll.checked = false;
      updateRecentSelection();
      _initRecentPaginator(resetPage);
      return;
    }

    tbody.innerHTML = events.map(function (ev) {
      /* Through the shared element, so Preferences > Time format and Use
         relative times reach this column like every other stamp. */
      const when = GP.timeHtml(ev.received_at);
      // Each badge carries its own explanation, so a reader never has to infer
      // what a state means from its colour alone.
      let status;
      const isFailed = !!ev.dead_letter_at || (!!ev.processing_error && !ev.processed);
      if (isFailed) {
        status = GP.badgeHtml(t('Failed'), 'danger', { icon: 'alert-circle',
          tooltip: t('Could not be processed - the reason is shown beside the badge.') });
        if (ev.processing_error) {
          status += ' <span class="muted font-sm">' +
            escapeHtml(String(ev.processing_error).slice(0, 80)) + '</span>';
        }
      } else if (ev.processed) {
        status = GP.badgeHtml(t('Processed'), 'success', { icon: 'check-circle',
          tooltip: t('Handled successfully - the data is already reflected on the course pages.') });
      } else {
        status = GP.badgeHtml(t('Pending'), 'warning', { icon: 'clock',
          tooltip: t('Received and queued, waiting for a worker to pick it up.') });
      }
      const safeId = escapeHtml(ev.id);
      // The shared detail handler reads the id off the ROW, so keep it there.
      // Where: course and group first, the GitLab path as the technical detail,
      // and the raw project id only in the tooltip - it means nothing on sight.
      const course = ev.course_code || ev.course_name;
      /* The course's term beside its code - the same code runs every year. */
      const term = ev.course_academic_year
        ? ' ' + GP.periodBadgeHtml(ev.course_academic_year, ev.course_semester)
        : '';
      const where = course
        ? `<strong>${escapeHtml(course)}</strong>` + term +
          (ev.team_name ? ' <span class="muted">/ ' + escapeHtml(ev.team_name) + '</span>' : '')
        : `<span class="muted">${escapeHtml(t('Unlinked project'))}</span>`;
      const wherePath = ev.project_path
        ? `<div class="muted font-sm text-truncate">${escapeHtml(ev.project_path)}</div>` : '';
      const whereTip = escapeHtml(
        (ev.project_path || t('Not linked to any course in this platform')) +
        ' (GitLab id ' + (ev.gitlab_project_id || '-') + ')'
      );

      const recentCheckbox = _canReplay
        ? `<input type="checkbox" id="event-select-${safeId}" class="form-check-input recent-select" value="${safeId}"${selected.has(ev.id) ? ' checked' : ''} aria-label="${escapeHtml(t('Select event'))}">`
        : '';
      // Row actions as in every other table - btn_icon_only squares: the eye
      // for "look at it", Restore's green arrows for bringing a dead event
      // back. They were the only worded buttons in a table row.
      return `<tr data-event-id="${safeId}">
        <td>${recentCheckbox}</td>
        <td data-label="${escapeHtml(t('Type'))}">${GP.badgeHtml(ev.event_type || '-', 'gray')}</td>
        <td data-label="${escapeHtml(t('What happened'))}">${
          ev.summary ? escapeHtml(ev.summary) : '<span class="muted">-</span>'}</td>
        <td data-label="${escapeHtml(t('Where'))}" data-tippy-content="${whereTip}">${where}${wherePath}</td>
        <td data-label="${escapeHtml(t('Who'))}">${
          ev.actor ? escapeHtml(ev.actor) : '<span class="muted">-</span>'}</td>
        <td data-label="${escapeHtml(t('Status'))}">${status}</td>
        <td class="text-center" data-label="${escapeHtml(t('Retries'))}">${ev.retry_count || 0}</td>
        <td class="muted" data-label="${escapeHtml(t('Received'))}">${when}</td>
        <td class="text-right" data-label="${escapeHtml(t('Actions'))}">
          ${ev.dead_letter_at && _canResurrect
            ? `<button type="button" class="btn btn-icon-only btn-success btn-sm resurrect-btn" data-resurrect="${safeId}"
                  aria-label="${escapeHtml(t('Resurrect'))}"
                  data-tippy-content="${escapeHtml(t('Put it back in the queue and try again'))}">${GP.iconSvg('refresh-cw', 'sm')}</button> `
            : ''}
          <button type="button" class="btn btn-icon-only btn-secondary btn-sm dlq-view-detail"
                  aria-label="${escapeHtml(t('Details'))}"
                  data-tippy-content="${escapeHtml(t('What GitLab sent, and what happened to it'))}">${GP.iconSvg('eye', 'sm')}</button>
        </td>
      </tr>`;
    }).join('');

    GP.initTippy(tbody);
    const recentAll = document.getElementById('recentSelectAll');
    if (recentAll) recentAll.checked = tbody.querySelectorAll('.recent-select:checked').length === events.length;
    updateRecentSelection();
    _initRecentPaginator(resetPage);
  }

  /* Same paginator component the dead-letter table uses, so both behave alike. */
  let _recentPaginator = null;
  function _initRecentPaginator(resetPage) {
    if (_recentPaginator) {
      _recentPaginator.resync();
      if (resetPage) _recentPaginator.goToPage(1);
      return;
    }
    _recentPaginator = new ClientPaginator({
      tbodySelector: '#recentEventsTableBody',
      controlsSelector: '#recentPagination',
      pageSize: 50,
      showPerPage: true,
      pageSizes: [25, 50, 100]
    });
    _recentPaginator.render();
  }

  /* preData = the DLQ first page inlined into the HTML, rendered on load with NO
     fetch and NO loader. A normal call (Refresh / type-filter) passes nothing and
     fetches as before. */
  async function loadDLQ(eventType, preData, options = {}) {
    if (_disposed) return false;
    const read = ++_dlqRead;
    const setStat = (id, value) => {
      const el = document.getElementById(id);
      if (el && el.textContent !== String(value)) el.textContent = value;
    };

    try {
      let data = preData;
      if (!data) {
        let url = '/api/v1/events/dlq?limit=' + _DLQ_FETCH_LIMIT;
        if (eventType) url += '&event_type=' + encodeURIComponent(eventType);
        data = await apiCall(url, 'GET', null, { ...options, key: 'events:dlq', signal: _pageReads.signal });
      }
      if (_disposed || read !== _dlqRead) return false;
      const allEvents = data.events || [];

      setStat('dlqCount', data.count);

      /* Derived from the parked events themselves. An empty queue is the good
         case and reads as a dash and a zero, not as a spinner. */
      const dates = allEvents.filter(e => e.dead_letter_at).map(e => new Date(e.dead_letter_at));
      if (dates.length) {
        const diffH = Math.floor((Date.now() - Math.min.apply(null, dates)) / 3600000);
        setStat('dlqOldest', diffH < 1 ? '<1h' : diffH < 24 ? diffH + 'h' : Math.floor(diffH / 24) + 'd');
      } else {
        setStat('dlqOldest', '-');
      }

      if (allEvents.length > 0) {
        const totalRetries = allEvents.reduce(function (sum, e) { return sum + (e.retry_count || 0); }, 0);
        setStat('dlqAvgRetries', (totalRetries / allEvents.length).toFixed(1));
      } else {
        setStat('dlqAvgRetries', '0');
      }

      return true;
    } catch (err) {
      if (_disposed || read !== _dlqRead || err?.superseded) return false;
      if (options.quiet) throw err;
      ['dlqCount', 'dlqOldest', 'dlqAvgRetries'].forEach(id => setStat(id, '?'));
      return false;
    }
  }

  async function loadEventData(options = {}) {
    // Wait for both reads: a fast failure must not unlock a still-pending read.
    const results = await Promise.allSettled([
      loadRecentEvents(_recentType(), options), loadDLQ('', null, options)
    ]);
    const failed = results.find(result => result.status === 'rejected');
    if (failed) throw failed.reason;
    return results.every(result => result.value === true);
  }

  /* -- Select all checkbox -- */
  document.getElementById('recentSelectAll')?.addEventListener('change', function () {
    document.querySelectorAll('.recent-select').forEach(cb => { cb.checked = this.checked; });
    updateRecentSelection();
  });

  /* -- Individual checkbox change -- */
  const onDocumentChange = function (e) {
    if (e.target.classList.contains('recent-select')) {
      updateRecentSelection();
      const selectAll = document.getElementById('recentSelectAll');
      const all = document.querySelectorAll('.recent-select');
      const checked = document.querySelectorAll('.recent-select:checked');
      if (selectAll) selectAll.checked = all.length > 0 && all.length === checked.length;
    }
  };

  /* -- Event delegation -- */
  const onDocumentClick = async (e) => {
    const btn = e.target.closest('[data-resurrect]');
    if (btn) {
      if (!_canMutate) return;
      try {
        await _lock(`resurrect:${btn.dataset.resurrect}`, async () => {
          setButtonLoading(btn, true, '...');
          await apiCall(`/api/v1/events/dlq/${btn.dataset.resurrect}/resurrect`, 'POST');
          showToast(t('Event resurrected'), 'success');
          /* It is pending again, not gone: this table lists every event, so the
             row stays and changes state. (The dead-letter tab removed it,
             because there it no longer belonged.) */
          await loadEventData();
        });
      } catch (err) {
        if (err.code !== 'LOCKED') showToast(err.message || t('Resurrect failed'), 'danger');
      } finally {
        setButtonLoading(btn, false);
      }
      return;
    }
    const detailBtn = e.target.closest('.dlq-view-detail');
    if (detailBtn) {
      const row = detailBtn.closest('tr');
      const eventId = row?.dataset.eventId;
      if (eventId) viewEventDetail(eventId);
    }
  };

  // Shared bounded reconnects; Refresh is also the retry after giving up.
  let _dlqSSE = null;
  let _connectedOnce = false;
  let _evtHealthDown = GP.health.isDown;
  const canReadLive = () => !_disposed && document.visibilityState !== 'hidden'
    && navigator.onLine && !_evtHealthDown;

  function _connectDlqSSE() {
    if (!canReadLive() || _dlqSSE?.active) return;
    _dlqSSE?.close();
    _dlqSSE = GP.sse({
      url: '/api/v1/dashboard/stream',
      events: {
        connected: function () {
          if (!canReadLive()) return;
          if (_connectedOnce) loadEventData({ keepView: true });
          _connectedOnce = true;
        },
        update: function () { if (canReadLive()) loadEventData({ keepView: true }); },
      },
    });
  }

  function _disconnectDlqSSE() {
    if (_dlqSSE) { _dlqSSE.close(); _dlqSSE = null; }
  }

  const onVisibilityChange = function () {
    if (canReadLive()) _connectDlqSSE();
    else _disconnectDlqSSE();
  };

  // Auto-refresh DLQ when batch operations complete
  const onJobComplete = function(e) {
    const st = e.detail?.status;
    if (st !== 'done' && st !== 'error') return;
    const jt = e.detail?.jobType;
    if (jt === 'batch_resurrect' || jt === 'event_replay') {
      loadEventData({ keepView: true });
    }
  };

  // Pause SSE when backend is unreachable
  const onHealthChange = function (e) {
    const wasDown = _evtHealthDown;
    _evtHealthDown = ['down', 'offline'].includes(e.detail?.current);
    if (_evtHealthDown) _disconnectDlqSSE();
    else if (wasDown) _connectDlqSSE();
  };

  const onBeforeSwap = function (evt) {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-page-config') || target.id === 'gp-page-config')) {
      GP.adminEventsCleanup();
    }
  };

  document.addEventListener('change', onDocumentChange);
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('visibilitychange', onVisibilityChange);
  window.addEventListener('gp:job-complete', onJobComplete);
  document.addEventListener('gp-health-change', onHealthChange);
  window.addEventListener('online', onVisibilityChange);
  window.addEventListener('offline', onVisibilityChange);
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.adminEventsCleanup = function () {
    _disposed = true;
    _pageReads.abort();
    _disconnectDlqSSE();
    document.removeEventListener('change', onDocumentChange);
    document.removeEventListener('click', onDocumentClick);
    document.removeEventListener('visibilitychange', onVisibilityChange);
    window.removeEventListener('gp:job-complete', onJobComplete);
    document.removeEventListener('gp-health-change', onHealthChange);
    window.removeEventListener('online', onVisibilityChange);
    window.removeEventListener('offline', onVisibilityChange);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };
  GP.activePageCleanup = GP.adminEventsCleanup;

  /* -- Init -- */
  if (_startupWarning && _startupWarning.message) {
    GP.showToast(_startupWarning.message, 'warning', Number(_startupWarning.durationMs || 12000), { once: true });
  }
  // Initialize the table and counters from the server's existing payloads.
  (function () {
    const _readIsland = function (id) {
      try {
        const el = document.getElementById(id);
        return el ? JSON.parse(el.textContent || 'null') : null;
      } catch (_) { return null; }
    };
    const recent = _readIsland('gp-recent-events');
    if (recent && Array.isArray(recent.events)) _renderRecentEvents(recent.events);
    else loadRecentEvents('');

    const dlq = _readIsland('gp-dlq');
    if (dlq && Array.isArray(dlq.events)) loadDLQ('', dlq);
    else loadDLQ('');
  })();
  _connectDlqSSE();

  // Type narrows the query server-side; status filters the fetched window.
  const _recentType = () => (document.getElementById('recentTypeFilter') || {}).value || '';

  document.getElementById('recentTypeFilter')?.addEventListener('change', function () {
    loadRecentEvents(_recentType());
  });
  document.getElementById('recentStatusFilter')?.addEventListener('change', function () {
    loadRecentEvents(_recentType());
  });
  const _dlqBtn = document.getElementById('btnRefreshDLQ');
  _dlqBtn?.addEventListener('click', async function () {
    const updated = await GP.refreshRegion({
      button: _dlqBtn,
      region: document.getElementById('eventPipelineRegion'),
      load: options => loadEventData({ ...options, quiet: true, keepView: true }),
      successMessage: t('Events refreshed'),
      errorMessage: t('Could not load recent events.'),
    });
    if (updated && !_disposed) _connectDlqSSE();
  });
  /* -- Replay the ticked events --
     Replay used to live in a modal that asked for a start and an end date: it
     named the events only indirectly, swept in everything else inside that
     window, and its own selects were clipped by the dialog. Acting on the rows
     you can see is both safer and simpler - and it reuses the selection
     pattern the dead-letter table already had. */
  document.getElementById('btnReplaySelected')?.addEventListener('click', async function () {
    if (!_canReplay) return;
    const btn = this;
    const ids = Array.from(document.querySelectorAll('.recent-select:checked')).map(cb => cb.value);
    if (!ids.length) return;

    /* `GP.confirmDialog` already falls back to the browser's own confirm when
       no dialog element is in the DOM (core/19-confirm-dialog.js), so re-declaring
       that fallback here was a second copy of the same decision - and the only
       place in the app that reached for `window.confirm` directly. */
    const ok = await GP.confirmDialog({
      title: t('Replay events'),
      message: t('Re-process {n} selected event(s)? Each one is queued again as a fresh copy.')
        .replace('{n}', String(ids.length)),
      confirmText: t('Replay'),
      variant: 'warning',
    });
    if (!ok) return;

    try {
      await _lock('replayEvents', async () => {
        setButtonLoading(btn, true, t('Replaying...'));
        const res = await apiCall('/api/v1/events/replay', 'POST', { event_ids: ids });
        showToast(t('{n} event(s) queued for replay').replace('{n}', String(res.replayed ?? ids.length)), 'success');
        await loadEventData();
      });
    } catch (err) {
      if (err && err.code === 'LOCKED') return;
      showToast((err && err.message) || t('Could not replay the selected events'), 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  });

  /* -- Purge old events (admin only) --
     Job History has cleared itself by age since it was built; this table
     collects the same kind of rows and had no way to, so it only ever grew.
     A PENDING event is never removed, whatever the age: it has not been dealt
     with yet, and dropping it would lose work rather than tidy up after it -
     which is why the server decides that, not this menu. */
  const _PURGE_LABELS = {
    24: t('older than 24 hours'),
    168: t('older than 7 days'),
    720: t('older than 30 days'),
    87600: t('- everything handled'),
  };

  async function purgeOldEvents(hours) {
    if (!_cfg.isAdmin) { showToast(t('Admin access required'), 'warning'); return; }
    hours = parseInt(hours, 10) || 24;
    const label = _PURGE_LABELS[hours] || (t('older than') + ' ' + hours + 'h');
    const ok = await GP.confirmDialog({
      title: t('Purge events'),
      message: hours >= 87600
        ? t('Remove every handled event from the pipeline? Pending events are kept. This cannot be undone.')
        : t('Remove handled events {age}? This cannot be undone.').replace('{age}', label),
      confirmText: t('Purge'),
      variant: 'danger',
    });
    if (!ok) return;

    const btn = document.getElementById('btnPurgeEvents');
    try {
      await _lock('purgeEvents', async () => {
        setButtonLoading(btn, true);
        const res = await apiCall('/api/v1/events/purge', 'POST',
          { hours: hours, scope: 'all' }, { maxRetries: 0 });
        showToast(t('Removed {n} event(s)').replace('{n}', String(res.deleted || 0)), 'success');
        await loadEventData();
      });
    } catch (err) {
      if (err && err.code === 'LOCKED') return;
      showToast((err && err.message) || t('Could not purge the events'), 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  }

  /* -- Delete the ticked events (admin only) --
     One handler for both tables: they differ only in which checkbox class they
     use and which list they reload afterwards. */
  async function deleteSelectedEvents(selector, btnId, reload) {
    const ids = Array.from(document.querySelectorAll(selector + ':checked')).map(cb => cb.value);
    if (!ids.length) return;

    const ok = await GP.confirmDialog({
      title: t('Delete events'),
      message: t('Delete {n} selected event(s)? A pending event is kept - it has not been handled yet.')
        .replace('{n}', String(ids.length)),
      confirmText: t('Delete'),
      variant: 'danger',
    });
    if (!ok) return;

    const btn = document.getElementById(btnId);
    try {
      await _lock('deleteEvents', async () => {
        setButtonLoading(btn, true);
        const res = await apiCall('/api/v1/events/delete', 'POST', { ids: ids }, { maxRetries: 0 });
        const gone = res.deleted || 0;
        /* Say when fewer went than were ticked, so a reader who selected a
           pending row is told it was kept rather than left wondering. */
        showToast(gone < ids.length
          ? t('Removed {n} of {total} - pending events are kept')
              .replace('{n}', String(gone)).replace('{total}', String(ids.length))
          : t('Removed {n} event(s)').replace('{n}', String(gone)), 'success');
        await reload();
      });
    } catch (err) {
      if (err && err.code === 'LOCKED') return;
      showToast((err && err.message) || t('Could not delete the selected events'), 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  }

  /* -- Resurrect the ticked failed events --
     The dead-letter tab rendered this button and armed it, and nothing was ever
     bound to it: clicking did nothing. It applies to the ticked rows that
     actually failed - the others are already in the queue or already done. */
  document.getElementById('btnBatchResurrect')?.addEventListener('click', async function () {
    /* Read the state off the ROW, not out of `allEvents`: the first paint comes
       from the inlined window and leaves that array empty, so filtering through
       it found nothing and the button quietly did nothing at all. A row carries
       a Resurrect control exactly when it failed. */
    const ids = Array.from(document.querySelectorAll('.recent-select:checked'))
      .filter(cb => cb.closest('tr')?.querySelector('[data-resurrect]'))
      .map(cb => cb.value);
    if (!ids.length) {
      showToast(t('None of the ticked events failed - only a failed one can be resurrected.'), 'warning');
      return;
    }
    const ok = await GP.confirmDialog({
      title: t('Resurrect events'),
      message: t('Put {n} failed event(s) back in the queue?').replace('{n}', String(ids.length)),
      confirmText: t('Resurrect'),
      variant: 'warning',
    });
    if (!ok) return;

    const btn = this;
    try {
      await _lock('batchResurrect', async () => {
        setButtonLoading(btn, true);
        let done = 0;
        for (const id of ids) {
          await apiCall(`/api/v1/events/dlq/${encodeURIComponent(id)}/resurrect`, 'POST');
          done++;
        }
        showToast(t('{n} event(s) put back in the queue').replace('{n}', String(done)), 'success');
        await loadEventData();
      });
    } catch (err) {
      if (err && err.code === 'LOCKED') return;
      showToast((err && err.message) || t('Could not resurrect the selected events'), 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  });

  document.getElementById('btnDeleteSelectedRecent')?.addEventListener('click', function () {
    deleteSelectedEvents('.recent-select', 'btnDeleteSelectedRecent',
      () => loadEventData());
  });

  document.querySelectorAll('[data-purge-events-hours]').forEach(function (item) {
    item.addEventListener('click', function () {
      purgeOldEvents(this.dataset.purgeEventsHours);
    });
  });
})();
