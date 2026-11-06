/* Support tickets page - client-side filtering + sorting (matches admin-system pattern) */
;(function() {
'use strict';

  const GP = window.GP;
  const { t } = GP;
  GP.runPageCleanup();
  const owner = document.getElementById('gp-tickets-config');
  if (!owner) return;
  const _purgeCfg = JSON.parse(owner.textContent);
  let disposed = false;
  const current = () => !disposed && owner.isConnected;

  // Reset filters button
  const resetBtn = document.getElementById('resetFilters');
  if (resetBtn) {
    resetBtn.addEventListener('click', function() {
      // Clear search
      const search = document.getElementById('ticketSearch');
      if (search) search.value = '';

      // Reset dropdowns - setting .value on hidden input triggers glFormSelect sync
      ['statusFilter', 'priorityFilter', 'categoryFilter'].forEach(function(id) {
        const el = document.getElementById(id);
        if (el) {
          el.value = '';
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });

      if (search && search._tableFilter) {
        search._tableFilter.apply();
      }
    });
  }

  let stream = null, lastReload = 0;
  function resumeLive() {
    if (!current() || !_purgeCfg.courseId || document.visibilityState === 'hidden'
        || GP.health.isDown || stream?.active) return;
    stream?.close();
    stream = GP.sse({
      url: '/api/v1/courses/' + encodeURIComponent(_purgeCfg.courseId) + '/stream',
      events: { update: function (event) {
        let data;
        try { data = JSON.parse(event.data); } catch (_) { return; }
        if (!current() || typeof data?.event !== 'string'
            || !data.event.startsWith('ticket') || GP.hasUnsavedState()) return;
        const now = Date.now();
        if (now - lastReload < 1500) return;
        lastReload = now;
        GP.flashToast(t(data.event === 'ticket_created' ? 'New ticket received' : 'Ticket updated'), 'info');
        GP.reloadKeepScroll();
      } },
    });
  }
  document.addEventListener('visibilitychange', resumeLive);
  document.addEventListener('gp-health-change', resumeLive);
  resumeLive();
  GP.activePageCleanup = function () {
    disposed = true;
    stream?.close();
    document.removeEventListener('visibilitychange', resumeLive);
    document.removeEventListener('gp-health-change', resumeLive);
  };

  /* -- Purge finished tickets (admin only) --
     The menu is rendered only for an admin and the endpoint refuses anyone
     else, so this is the convenience half of the gate, not the gate. Only
     resolved and closed tickets are ever eligible - the server decides that,
     because an open ticket is somebody still waiting for an answer. */
  const _TICKET_PURGE_LABELS = {
    720: t('resolved over 30 days ago'),
    2160: t('resolved over 90 days ago'),
    8760: t('resolved over a year ago'),
    87600: t('- every finished ticket'),
  };

  async function purgeTickets(hours) {
    hours = parseInt(hours, 10) || 720;
    const label = _TICKET_PURGE_LABELS[hours] || (t('older than') + ' ' + hours + 'h');
    const course = _purgeCfg.courseLabel || '';
    const ok = await GP.confirmDialog({
      title: t('Purge tickets'),
      message: hours >= 87600
        ? t('Remove every resolved and closed ticket of {course}? Open tickets are kept. This cannot be undone.').replace('{course}', course)
        : t('Remove tickets of {course} {age}? This cannot be undone.').replace('{course}', course).replace('{age}', label),
      confirmText: t('Purge'),
      variant: 'danger',
    });
    if (!ok || !current()) return;

    const btn = document.getElementById('btnPurgeTickets');
    try {
      await GP.withUiLock('ticketsMutation:' + _purgeCfg.courseId, async () => {
        GP.setButtonLoading(btn, true);
        const res = await GP.apiCall('/api/v1/support/tickets/purge', 'POST',
          { hours: hours, course_id: _purgeCfg.courseId || null }, { maxRetries: 0 });
        if (!current()) return;
        GP.showToast(t('Removed {n} ticket(s)').replace('{n}', String(res.deleted || 0)), 'success');
        if (res.deleted) GP.reloadKeepScroll();
      });
    } catch (err) {
      if (current() && err.code !== 'LOCKED') GP.showToast(err.message || t('Could not purge the tickets'), 'danger');
    } finally {
      GP.setButtonLoading(btn, false);
    }
  }

  /* -- Select rows, then delete them (admin only) --
     The same pair Job History and the Event Pipeline offer: a menu that clears
     by age, and this, which clears what the reader actually ticked. */
  function updateTicketSelection() {
    const checked = document.querySelectorAll('.ticket-select:checked');
    const countEl = document.getElementById('ticketsSelectedCount');
    const btn = document.getElementById('btnDeleteSelectedTickets');
    if (countEl) countEl.textContent = checked.length;
    if (btn) btn.disabled = checked.length === 0;
  }

  document.getElementById('ticketsSelectAll')?.addEventListener('change', function () {
    document.querySelectorAll('.ticket-select').forEach(function (cb) {
      cb.checked = this.checked;
    }, this);
    updateTicketSelection();
  });

  document.getElementById('ticketsTable')?.addEventListener('change', function (e) {
    if (e.target && e.target.classList && e.target.classList.contains('ticket-select')) {
      updateTicketSelection();
    }
  });

  document.getElementById('btnDeleteSelectedTickets')?.addEventListener('click', async function () {
    const ids = Array.from(document.querySelectorAll('.ticket-select:checked')).map(cb => cb.value);
    if (!ids.length) return;
    const ok = await GP.confirmDialog({
      title: t('Delete tickets'),
      message: t('Delete {n} selected ticket(s)? An open ticket is kept - somebody is waiting on it.')
        .replace('{n}', String(ids.length)),
      confirmText: t('Delete'),
      variant: 'danger',
    });
    if (!ok || !current()) return;

    const btn = this;
    try {
      await GP.withUiLock('ticketsMutation:' + _purgeCfg.courseId, async () => {
        GP.setButtonLoading(btn, true);
        const res = await GP.apiCall('/api/v1/support/tickets/delete', 'POST',
          { ids: ids }, { maxRetries: 0 });
        if (!current()) return;
        const gone = res.deleted || 0;
        GP.showToast(gone < ids.length
          ? t('Removed {n} of {total} - open tickets are kept')
              .replace('{n}', String(gone)).replace('{total}', String(ids.length))
          : t('Removed {n} ticket(s)').replace('{n}', String(gone)), 'success');
        if (gone) GP.reloadKeepScroll();
      });
    } catch (err) {
      if (current() && err.code !== 'LOCKED') GP.showToast(err.message || t('Could not delete the selected tickets'), 'danger');
    } finally {
      GP.setButtonLoading(btn, false);
    }
  });

  document.querySelectorAll('[data-purge-tickets-hours]').forEach(function (item) {
    item.addEventListener('click', function () {
      purgeTickets(this.dataset.purgeTicketsHours);
    });
  });

})();
