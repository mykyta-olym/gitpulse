/**
 * Course Analytics page - Chart.js interactive charts, report generation,
 * data refresh, intervention flags, support management.
 */

  const GP = window.GP || {};
  GP.runPageCleanup();

  // Scoped variables for cleanable listeners and timers across files
  let onLoadCharts = null;

  const { t, withUiLock: _lock } = GP;

  /* -- Config from JSON block -- */
  const _cfgEl = document.getElementById('gp-analytics-config');
  const _cfg = _cfgEl ? JSON.parse(_cfgEl.textContent) : {};
  const courseId = _cfg.courseId;
  if (!courseId) return;

  /* -- Role config -- */
  const _canEdit = !!_cfg.canEdit;
  const greenPct = _cfg.greenPct ?? 80;
  const yellowPct = _cfg.yellowPct ?? 50;

  /* -- Chart colors from the shared semantic theme -- */
  const chartColors = (GP.chartTheme && GP.chartTheme.colors) || {};

  /* -- SVG icon helper for dynamic stat cards (uses GP icon system) -- */
  /* ==========================================
   *  CHART INSTANCES - stored for updates
   * ========================================== */
  let checklistChart = null;

  /* ==========================================
   *  TEACHER'S CHECKLIST - Horizontal Bar (dynamic: R01-R13 + custom)
   * ========================================== */
  /* One colour per category, from the theme's palette (tokens.css
     --chart-cat-*), read at draw time so a mode switch redraws in the mode's
     own steps. */
  function categoryColors() {
    const c = (GP.chartTheme && GP.chartTheme.colors) || {};
    const a = (GP.chartTheme && GP.chartTheme.alpha) || function (x) { return x; };
    const mk = function (bar) { return { bar: bar, bg: a(bar, 0.8) }; };
    return {
      issue:   mk(c.catIssue || '#9475db'),
      mr:      mk(c.catMr || '#428fdc'),
      review:  mk(c.catReview || '#d99530'),
      ci:      mk(c.catCi || '#0094b6'),
      commit:  mk(c.catQuality || '#ec4899'),
      custom:  mk(c.catCustom || '#a855f7'),
    };
  }

  function initChecklistChart(data) {
    const _cat = categoryColors();
    const canvas = document.getElementById('checklistCanvas');
    if (!canvas || typeof Chart === 'undefined' || !data || !data.length) return;

    const _loading = document.getElementById('checklistLoading');
    const _body = document.getElementById('checklistBody');

    // Wait for both visibility and the loading hand-off before measuring.
    if (canvas.dataset.gpEntered !== '1') {
      const _watch = (_loading && !_loading.classList.contains('d-none')) ? _loading : canvas;
      GP.drawOnEntry(canvas, function () {
        GP.revealAfterLoading(_loading, _body, function () {
          if (canvas.isConnected) initChecklistChart(data);
        });
      }, _watch);
      return;
    }

    if (checklistChart) { checklistChart.destroy(); checklistChart = null; }

    // Filter to only show checks that are expected in the current week
    const filtered = data.filter(d => d.expected !== false);
    if (!filtered.length) {
      // All checks are not yet expected - show message
      const wrap = canvas.closest('.chart-canvas-wrap');
      if (wrap) {
        wrap.style.minHeight = '';
        wrap.innerHTML = GP.emptyStateHtml(
          t('No checks are expected yet for the current week.'),
          'chart-bar-sm');
      }
      return;
    }

    /* On a phone the axis has room for about twenty characters, and Chart.js
       clips a longer label at the canvas edge ("7 Recenzia kódu poskytnutá"
       lost its "R0"). A two-line label - the code, then the name - keeps the
       whole text on screen; the tooltip carries the full title either way. */
    const narrow = ((canvas.closest('.chart-canvas-wrap') || canvas).clientWidth || window.innerWidth) < 480;
    const labels = filtered.map(d => (narrow ? [d.code, d.label] : d.code + ' ' + d.label));
    const pcts = filtered.map(d => d.pct);
    const barColors = filtered.map(d => {
      if (d.pct >= greenPct) return chartColors.green;
      if (d.pct >= yellowPct) return chartColors.yellow;
      return chartColors.red;
    });

    // Category indicator stripe on the left
    const catStripe = {
      id: 'checklistCatStripe',
      beforeDraw(chart) {
        const { ctx: c, chartArea, scales } = chart;
        if (!chartArea || !scales.y) return;
        c.save();
        filtered.forEach((d, i) => {
          const cat = _cat[d.category] || _cat.custom;
          const y = scales.y.getPixelForValue(i);
          const barH = Math.max(scales.y.getPixelForValue(0) - scales.y.getPixelForValue(1), 20) * 0.55;
          c.fillStyle = cat.bar;
          c.fillRect(chartArea.left - 6, y - barH / 2, 4, barH);
        });
        c.restore();
      },
    };

    const ctx = canvas.getContext('2d');
    const canvasH = Math.max(340, filtered.length * 34);
    canvas.parentElement.style.minHeight = canvasH + 'px';

    checklistChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: t('Students %'),
          data: pcts,
          backgroundColor: barColors.map(c => (GP.chartTheme && GP.chartTheme.alpha) ? GP.chartTheme.alpha(c, 0.8) : c),
          borderColor: barColors,
          borderWidth: 2,
          borderRadius: 4,
          borderSkipped: false,
          barPercentage: 0.7,
          categoryPercentage: 0.85,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        animation: GP.barsEntrance(canvas),
        layout: { padding: { left: 8 } },
        scales: {
          x: {
            beginAtZero: true,
            max: 100,
            grid: { color: chartColors.grid },
            ticks: { callback: v => v + '%', stepSize: 20 },
          },
          y: {
            grid: { display: false },
            ticks: {
              font: { size: 12, weight: '500' },
              color: chartColors.text,
              /* Every check keeps its label: with two-line labels Chart.js
                 would otherwise skip every other tick and leave bars unnamed. */
              autoSkip: false,
            },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            // Theme-aware surface comes from Chart.defaults (GP.chartTheme).
            titleFont: { size: 13, weight: '600' },
            bodyFont: { size: 12 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              title: (items) => {
                const idx = items[0]?.dataIndex;
                if (idx == null) return '';
                const d = filtered[idx];
                return d.code + ' - ' + d.label + (d.category ? ' [' + d.category + ']' : '');
              },
              label: (item) => {
                const d = filtered[item.dataIndex];
                return ' ' + d.passed + '/' + d.total + ' (' + d.pct.toFixed(1) + '%)';
              },
            },
          },
        },
      },
      plugins: [catStripe],
    });
  }

  function initCharts() {
    if (_cfg.checklistData) initChecklistChart(_cfg.checklistData);
  }

  if (typeof Chart !== 'undefined') {
    initCharts();
  } else {
    onLoadCharts = initCharts;
    window.addEventListener('load', onLoadCharts);
  }
