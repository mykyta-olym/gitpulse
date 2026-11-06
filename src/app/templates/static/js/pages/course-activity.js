/* Course Activity uses the same server-rendered components on arrival and refresh. */
(function initCourseActivityPage() {
  GP.runPageCleanup();
  const owner = document.getElementById('gp-course-activity-config');
  if (!owner) return;
  let cfg = JSON.parse(owner.textContent);
  const courseId = String(cfg.courseId);
  const region = owner.closest('.gl-tab-content');
  let chart = null, stream = null, pollTimer = 0, refreshTimer = 0;
  let controller = null, reading = false, pending = false, disposed = false, healthDown = false;
  const current = () => !disposed && owner.isConnected;

  function clearChart() {
    if (chart) chart.destroy();
    chart = null;
    const canvas = region.querySelector('#pipelineDoughnut');
    const entry = canvas?._gpEntry;
    if (entry) {
      entry.io?.disconnect();
      clearTimeout(entry.timer);
      canvas._gpEntry = null;
    }
  }

  function drawChart() {
    const canvas = region.querySelector('#pipelineDoughnut');
    if (!canvas) return;
    if (typeof Chart === 'undefined') {
      const error = document.createElement('div');
      error.innerHTML = GP.errorStateHtml(GP.t('Failed to load chart'), GP.t('Retry'));
      canvas.parentElement.replaceWith(error);
      GP.bindRetry(error, () => GP.reloadKeepScroll());
      return;
    }
    GP.drawOnEntry(canvas, function () {
      if (!current() || !canvas.isConnected) return;
      if (chart) chart.destroy();
      const stats = cfg.pipelineStats;
      chart = new Chart(canvas, {
        type: 'doughnut',
        data: {
          labels: ['Passed', 'Failed', 'Running', 'Pending', 'Other'].map(label => GP.t(label)),
          datasets: [{
            data: [stats.passed, stats.failed, stats.running, stats.pending, stats.other],
            backgroundColor: ctx => {
              const c = GP.chartTheme.colors;
              return [c.green, c.red, c.blue, c.yellow, c.surface][ctx.dataIndex];
            },
            borderColor: () => GP.chartTheme.colors.background,
            hoverBorderColor: () => GP.chartTheme.colors.background,
            borderWidth: 2, hoverOffset: 0, hoverBorderWidth: 2,
          }],
        },
        options: {
          cutout: '68%', responsive: true, maintainAspectRatio: true,
          animation: GP.ringEntrance(canvas),
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: ctx => {
              const total = ctx.dataset.data.reduce((sum, value) => sum + value, 0);
              return ctx.label + ': ' + ctx.parsed + ' (' + Math.round(ctx.parsed / total * 100) + '%)';
            } } },
          },
        },
      });
    });
  }

  function swapContent(next) {
    const health = region.querySelector('#activityHealthCard > .card-body');
    const nextHealth = next.querySelector('#activityHealthCard > .card-body');
    const config = next.querySelector('#gp-course-activity-config');
    const panels = Array.from(region.querySelectorAll('#activityViews > [data-tab-panel]'));
    if (!nextHealth || !config || panels.some(panel => !next.getElementById(panel.id))) {
      throw new Error(GP.t('Failed to refresh'));
    }
    const nextConfig = JSON.parse(config.textContent);
    if (String(nextConfig.courseId) !== courseId) throw new Error(GP.t('Failed to refresh'));
    const entered = region.querySelector('#pipelineDoughnut')?.dataset.gpEntered;
    clearChart();
    cfg = nextConfig;
    GP.motion.resize(health, () => health.replaceChildren(...nextHealth.childNodes));
    const canvas = region.querySelector('#pipelineDoughnut');
    if (canvas && entered === '1') canvas.dataset.gpEntered = canvas.dataset.gpDrawn = '1';
    panels.forEach(function (panel) {
      const paginator = panel.querySelector('tbody')?._clientPaginator;
      const page = paginator?.currentPage || 1;
      const scrollLeft = panel.querySelector('.table-responsive')?.scrollLeft || 0;
      GP.motion.resize(panel, function () {
        panel.replaceChildren(...next.getElementById(panel.id).childNodes);
        GP.initDataComponents(panel);
        panel.querySelectorAll('table[data-sortable]').forEach(GP.SortableTable.initTable);
        panel.querySelector('tbody')?._clientPaginator?.goToPage(page);
        const scroller = panel.querySelector('.table-responsive');
        if (scroller) scroller.scrollLeft = scrollLeft;
      });
    });
    region.querySelectorAll('.activity-view-filter [data-value]').forEach(function (tab) {
      const badge = tab.querySelector('.badge');
      const nextBadge = next.querySelector('.activity-view-filter [data-value="' + tab.dataset.value + '"] .badge');
      if (badge && nextBadge) badge.replaceWith(nextBadge);
    });
    GP.applyDataDrivenStyles(region);
    GP.initResponsiveTableLabels(region);
    GP.initTippy(region);
    GP.initTableScroll(region);
    window.localizeTimes(region);
    drawChart();
  }

  function queueRefresh() {
    if (!current()) return;
    pending = true;
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => refresh(), 350);
  }

  async function refresh(button) {
    clearTimeout(refreshTimer);
    refreshTimer = 0;
    if (!current() || document.visibilityState !== 'visible' || healthDown) return;
    if (reading || (!button && region.querySelector('.card-body:focus-within'))) {
      queueRefresh();
      return;
    }
    pending = false;
    reading = true;
    controller = new AbortController();
    const query = location.search;
    try {
      await GP.refreshRegion({
        button, region,
        successMessage: button ? GP.t('Data updated') : '',
        errorMessage: GP.t('Failed to refresh'),
        load: async options => {
          const html = await GP.apiCall(location.pathname + query, 'GET', null, {
            ...options, signal: controller.signal, key: 'course-activity:' + courseId,
            responseType: 'text', headers: { Accept: 'text/html', 'Cache-Control': 'no-cache' },
          });
          if (!current()) return false;
          if (query !== location.search) { queueRefresh(); return false; }
          swapContent(new DOMParser().parseFromString(html, 'text/html'));
        },
      });
    } finally {
      reading = false;
      controller = null;
      if (pending && current()) queueRefresh();
    }
  }

  function stopLive() {
    if (stream) stream.close();
    stream = null;
    clearInterval(pollTimer);
    pollTimer = 0;
  }
  function connect() {
    stopLive();
    if (!current() || healthDown || document.visibilityState !== 'visible') return;
    stream = GP.sse({
      url: '/api/v1/courses/' + courseId + '/stream',
      events: { update: function (event) {
        let data;
        try { data = JSON.parse(event.data); } catch (_) { /* An update still refreshes. */ }
        if (data?.event === 'settings_changed' && !GP.hasUnsavedState()) {
          GP.reloadKeepScroll();
          return;
        }
        queueRefresh();
      } },
      onGiveUp: function () { pollTimer = setInterval(queueRefresh, 60000); },
    });
  }
  function visibility() {
    if (document.visibilityState === 'hidden') stopLive();
    else { connect(); queueRefresh(); }
  }
  function healthChange(event) {
    const wasDown = healthDown;
    healthDown = ['down', 'offline'].includes(event.detail?.current);
    if (healthDown) stopLive();
    else if (wasDown) { connect(); queueRefresh(); }
  }
  function jobComplete(event) {
    const d = event.detail || {};
    if ((d.status === 'done' || d.status === 'error') && GP.jobAffectsScope(d, { courseId })) queueRefresh();
  }
  function click(event) {
    const button = event.target.closest('#btnRefreshActivity');
    if (button) refresh(button);
  }
  GP.courseActivityCleanup = function () {
    disposed = true;
    stopLive();
    clearTimeout(refreshTimer);
    controller?.abort();
    clearChart();
    document.removeEventListener('visibilitychange', visibility);
    document.removeEventListener('gp-health-change', healthChange);
    region.removeEventListener('click', click);
    window.removeEventListener('gp:job-complete', jobComplete);
  };
  GP.activePageCleanup = GP.courseActivityCleanup;
  document.addEventListener('visibilitychange', visibility);
  document.addEventListener('gp-health-change', healthChange);
  window.addEventListener('gp:job-complete', jobComplete);
  region.addEventListener('click', click);
  drawChart();
  connect();
})();
