  async function loadSystemStats() {
    return GP.coalesced('admin-system-stats', async function () {
      const status = document.getElementById('queueStatus');
      if (!status) return false;
      try {
        const data = await apiCall('/dashboard/api/v1/admin/system/stats', 'GET', null, { key: 'admin-system-stats', maxRetries: 0, timeoutMs: 5000 });
        if (_disposed) return false;
        const queues = data.queues || {};
        const names = ['high', 'default', 'low'];
        const extra = Object.keys(queues).filter(function (k) { return names.indexOf(k) === -1; });
        const summary = names.concat(extra).map(function (name) {
          return name + ': ' + (queues[name] != null ? queues[name] : 0);
        }).join(', ');
        const workers = data.workers;
        const base = t('Queued jobs') + ': ' + summary + '. ' + t('Workers online') + ': ' + (workers != null ? workers : '-') + '.';
        const next = workers === 0 ? base + ' ' + t('No active workers; queued jobs will wait.') : base;
        if (status.textContent !== next) status.textContent = next;
        status.classList.toggle('text-warning', workers === 0);
        return true;
      } catch (err) {
        if (err?.superseded || _disposed) return false;
        status.classList.remove('text-warning');
        status.textContent = t('Queue status is temporarily unavailable.');
        return false;
      }
    });
  }
