/* Student detail page logic - Chart.js compliance history + skill radar + diff highlighting */
(function initStudentDetailPage() {
  const GP = window.GP || {};
  const { apiCall, showToast, flashToast, t, escapeHtml, ClientPaginator } = GP;

  GP.runPageCleanup();

  const chartColors = GP.chartTheme.colors;
  const chartAlpha = GP.chartTheme.alpha;

  /* -- Score thresholds for traffic-light colors --
     The course's own (course settings -> green_pct / yellow_pct, on the
     Compliance Progress card). They were fixed at 70/40 here while the pills
     under the chart printed the course's 80/50, so the dashed lines, the
     point colours and the legend disagreed on the same canvas. */
  const _thresholdPanel = document.getElementById('complianceHistoryPanel');
  const _pct = (v, dflt) => { const n = parseFloat(v); return Number.isFinite(n) ? n / 100 : dflt; };
  const _SCORE_GREEN = _pct(_thresholdPanel?.dataset.greenPct, 0.8);
  const _SCORE_YELLOW = _pct(_thresholdPanel?.dataset.yellowPct, 0.5);

  /* -- Chart instances -- */
  let historyChart = null;
  let skillRadarChart = null;
  let lastHistoryData = null;
  let _historyLoaded = false;
  let _historyRead = 0;
  let _studentDisposed = false;
  let _commitsPaginator = null;

  function clearComplianceCharts() {
    if (historyChart) historyChart.destroy();
    if (skillRadarChart) skillRadarChart.destroy();
    historyChart = skillRadarChart = lastHistoryData = null;
    ['historyCanvas', 'skillRadarCanvas'].forEach(function (id) {
      const canvas = document.getElementById(id);
      const entry = canvas?._gpEntry;
      if (entry) {
        entry.io?.disconnect();
        clearTimeout(entry.timer);
        canvas._gpEntry = null;
      }
    });
    const weekLabel = document.getElementById('radarWeekLabel');
    if (weekLabel) weekLabel.textContent = '';
  }

  /* -- Diff Highlighting (with line numbers) -- */
  function highlightDiffBlocks() {
    const blocks = document.querySelectorAll('.diff-pre');
    blocks.forEach((block) => {
      if (block.dataset.highlighted === 'true') return;
      const rawText = block.textContent || '';
      if (!rawText) return;
      const lines = rawText.split('\n');
      // Remove trailing empty line from split
      if (lines.length && lines[lines.length - 1] === '') lines.pop();
      let html = '';
      lines.forEach((line) => {
        let cls = '';
        if (line.startsWith('+') && !line.startsWith('+++')) cls = 'diff-line-add';
        else if (line.startsWith('-') && !line.startsWith('---')) cls = 'diff-line-del';
        else if (line.startsWith('@@')) cls = 'diff-line-hunk';
        html += `<div class="diff-line ${cls}"><span class="diff-line-num"></span><span class="diff-line-content">${escapeHtml(line) || ' '}</span></div>`;
      });
      block.innerHTML = html;
      block.dataset.highlighted = 'true';
    });
  }

  /* -- Diff toggle: highlight diff blocks the first time their <details> opens.
     The diff content lives inside the MR card's <details> (no separate row), so
     we just lazily highlight when revealed. -- */
  function initDiffToggles() {
    document.querySelectorAll('.mr-diff-details').forEach(function (det) {
      det.addEventListener('toggle', function () {
        if (this.open) highlightDiffBlocks();
      });
    });
  }

  /* -- Diff file tree: clicking a file in the (multi-file) tree expands its
     block and smooth-scrolls to it WITHOUT an anchor jump. A bare `#id` link (or
     default scrollIntoView) walks up and scrolls every scrollable ancestor -
     which nudges the window and shifts the fixed topbar / page chrome ("layout
     breaks"). Instead we scroll the page-content container directly to the
     computed offset, like the member-row jump on the project page. The entry
     stays active and tracks the file scrolled into view. -- */
  function _scrollToDiff(target) {
    if (!target) return;
    const parentDetails = target.closest('.mr-diff-details');
    if (parentDetails && !parentDetails.open) parentDetails.open = true;
    if (!target.open) target.open = true;
    highlightDiffBlocks();
    GP.scrollWithinPageContent(target, { block: 'center' });
    GP.motion.highlight(target);
  }

  function _scrollDiffTreeItemIntoView(item) {
    const scroller = item?.closest?.('.diff-file-tree');
    if (!scroller || scroller.scrollHeight <= scroller.clientHeight) return;
    try {
      const itemRect = item.getBoundingClientRect();
      const scrollerRect = scroller.getBoundingClientRect();
      const pad = 8;
      if (itemRect.top < scrollerRect.top + pad) {
        scroller.scrollTo({
          top: Math.max(0, scroller.scrollTop + itemRect.top - scrollerRect.top - pad),
          behavior: 'smooth',
        });
      } else if (itemRect.bottom > scrollerRect.bottom - pad) {
        scroller.scrollTo({
          top: Math.max(0, scroller.scrollTop + itemRect.bottom - scrollerRect.bottom + pad),
          behavior: 'smooth',
        });
      }
    } catch (_) {}
  }

  function _queryScopedId(scope, id) {
    if (!id) return null;
    const esc = window.CSS && CSS.escape
      ? CSS.escape(id)
      : String(id).replace(/([^\w-])/g, '\\$1');
    if (scope && scope.querySelector) {
      const scoped = scope.querySelector('#' + esc);
      if (scoped) return scoped;
    }
    return document.getElementById(id);
  }

  function _markManualDiffScroll(layout) {
    if (layout) {
      layout.dataset.manualDiffScrollUntil = String(Date.now() + 900);
    }
  }

  function initDiffFileTree() {
    document.querySelectorAll('.diff-layout').forEach(function (layout) {
      const items = Array.from(layout.querySelectorAll('[data-diff-target]'));
      if (!items.length) return;
      const setActive = function (id, options) {
        const opts = options || {};
        items.forEach((it) => {
          const active = it.dataset.diffTarget === id;
          it.setAttribute('aria-current', String(active));
          if (active && opts.scrollTree !== false) {
            _scrollDiffTreeItemIntoView(it);
          }
        });
      };
      items.forEach(function (item) {
        if (item.dataset.diffBound === '1') return;
        item.dataset.diffBound = '1';
        item.addEventListener('click', function () {
          _markManualDiffScroll(layout);
          _scrollToDiff(_queryScopedId(layout, this.dataset.diffTarget));
          setActive(this.dataset.diffTarget, { scrollTree: false });
        });
      });
      if ('IntersectionObserver' in window) {
        const visibleBlocks = new Set();
        const root = layout.closest('.gl-page-content') || null;
        const obs = new IntersectionObserver(
          function (entries) {
            entries.forEach(function (e) {
              if (e.isIntersecting) {
                visibleBlocks.add(e.target);
              } else {
                visibleBlocks.delete(e.target);
              }
            });
            if (Number(layout.dataset.manualDiffScrollUntil || 0) > Date.now()) {
              return;
            }
            if (visibleBlocks.size > 0) {
              const sorted = Array.from(visibleBlocks).sort((a, b) => {
                return a.getBoundingClientRect().top - b.getBoundingClientRect().top;
              });
              setActive(sorted[0].id);
            }
          },
          { root, rootMargin: '-84px 0px -50% 0px', threshold: 0 },
        );
        layout.querySelectorAll('.diff-block').forEach((b) => {
          obs.observe(b);
        });
        layout._diffObserver = obs;
      }
    });
    document.querySelectorAll('[data-diff-jump]').forEach(function (trigger) {
      if (trigger.dataset.diffJumpBound === '1') return;
      trigger.dataset.diffJumpBound = '1';
      trigger.addEventListener('click', function (event) {
        event.preventDefault();
        const targetId = this.dataset.diffJump;
        const scope = this.closest('[data-mr-card], .rg-card') || document;
        const target = _queryScopedId(scope, targetId);
        if (!target) return;
        const targetLayout = target.closest('.diff-layout');
        _markManualDiffScroll(targetLayout);
        _scrollToDiff(target);
        if (!targetLayout) return;
        targetLayout.querySelectorAll('[data-diff-target]').forEach(function (item) {
          const active = item.dataset.diffTarget === targetId;
          item.setAttribute('aria-current', String(active));
          if (active) _scrollDiffTreeItemIntoView(item);
        });
      });
    });
  }

  function _scrollToMergeRequestCard(target) {
    if (!target) return;
    GP.scrollWithinPageContent(target, { block: 'center' });
    GP.motion.highlight(target);
  }

  const onDocumentClickScrollToMr = function (event) {
    const link = event.target.closest?.('[data-scroll-to-mr]');
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    const iid = link.getAttribute('data-scroll-to-mr');
    const target = iid ? document.getElementById('mr-' + iid) : null;
    if (!target) {
      showToast(t('Merge request is not visible on this page'), 'info');
      return;
    }
    _scrollToMergeRequestCard(target);
    try {
      history.replaceState(null, '', '#mr-' + encodeURIComponent(iid));
    } catch (_) {}
  };

  const onDocumentClickCopyCodeContext = function (event) {
    const btn = event.target.closest?.('[data-copy-code-context]');
    if (!btn) return;
    // The copy button lives inside the code-context <summary>; preventDefault +
    // stopPropagation keep the click from toggling the <details> open/closed.
    event.preventDefault();
    event.stopPropagation();
    const root = btn.closest('[data-code-context]');
    const lines = Array.from(root?.querySelectorAll('[data-code-line] .dn-code-text code') || [])
      .map((el) => el.textContent || '');
    if (!lines.length) return;
    GP.copyToClipboard(lines.join('\n'), t('Code context copied'));
  };

  /* -- Compliance History -- */

  function scoreCell(val) {
    if (val == null) return '<span class="muted">-</span>';
    const pct = (val * 100).toFixed(0);
    const cls = val >= _SCORE_GREEN ? 'text-success' : val >= _SCORE_YELLOW ? 'text-warning' : 'text-danger';
    return `<span class="${cls}">${pct}%</span>`;
  }

  function deltaCell(val) {
    if (val == null) return '<span class="muted">-</span>';
    const pct = (val * 100).toFixed(1);
    if (val > 0) return GP.badgeHtml('+' + pct + '%', 'success', { icon: 'trending-up' });
    if (val < 0) return GP.badgeHtml(pct + '%', 'danger', { icon: 'trending-down' });
    return '<span class="muted">0%</span>';
  }

  function progressBarFill(val) {
    if (val == null) return '';
    const pct = (val * 100).toFixed(0);
    return `<div class="progress history-score-progress" aria-hidden="true"><div class="progress-bar" data-progress="${pct}"></div></div>`;
  }

  /* -- Score Trend Line Chart -- */
  function initHistoryChart(data) {
    if (_studentDisposed) return;
    const canvas = document.getElementById('historyCanvas');
    const emptyMsg = document.getElementById('historyEmpty');
    if (!canvas || typeof Chart === 'undefined') return;

    // The first draw waits until the canvas scrolls in (GP.drawOnEntry, the
    // one every chart uses).
    if (canvas.dataset.gpEntered !== '1') {
      GP.drawOnEntry(canvas, function () { initHistoryChart(data); });
      return;
    }

    if (emptyMsg) emptyMsg.classList.add('d-none');

    if (historyChart) historyChart.destroy();
    historyChart = null;
    const labels = data.map(d => `W${d.week_number}`);
    const scores = data.map(d => d.overall_score != null ? +(d.overall_score * 100).toFixed(1) : null);

    const ctx = canvas.getContext('2d');

    // Create gradient fill for the area under the line - in the brand colour
    // the line itself is drawn in, so an accent theme fills under its accent
    // rather than under a blue that belongs to no theme.
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.parentElement?.clientHeight || 300);
    gradient.addColorStop(0, chartAlpha(chartColors.brand, 0.19));
    gradient.addColorStop(0.6, chartAlpha(chartColors.brand, 0.03));
    gradient.addColorStop(1, chartAlpha(chartColors.brand, 0));

    historyChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: t('Overall Score'),
          data: scores,
          borderColor: chartColors.brand,
          backgroundColor: gradient,
          borderWidth: 2.5,
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBackgroundColor: scores.map(v =>
            v == null ? 'transparent' :
            v >= _SCORE_GREEN * 100 ? chartColors.green :
            v >= _SCORE_YELLOW * 100 ? chartColors.yellow : chartColors.red
          ),
          /* Live theme colours: a ring cut from the current background, so a
             mode switch does not leave white rings on a dark chart. */
          pointBorderColor: () => (GP.chartTheme?.colors?.background) || chartColors.background,
          pointBorderWidth: 2,
          pointHoverBorderWidth: 3,
          pointHoverBorderColor: () => (GP.chartTheme?.colors?.tooltipBg) || chartColors.tooltipBg,
          fill: true,
          tension: 0.35,
          spanGaps: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 8 } },
        interaction: { mode: 'index', intersect: false },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { size: 12 } },
          },
          y: {
            beginAtZero: true,
            suggestedMax: 100,
            ticks: {
              font: { size: 12 },
              callback: (v) => v + '%',
              stepSize: 25,
            },
            grid: { color: chartColors.grid },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            // No backgroundColor here: Chart.defaults carries the theme-aware
            // tooltip surface (GP.chartTheme). Hardcoding a dark box left the
            // light theme with dark-on-dark text until the user toggled themes.
            titleFont: { size: 13, weight: '600' },
            bodyFont: { size: 12 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              title: (items) => {
                const d = data[items[0]?.dataIndex];
                if (!d) return items[0]?.label || '';
                return `${items[0].label} - ${d.snapshot_date || ''}`;
              },
              label: (item) => {
                if (item.raw == null) return t('No data');
                const d = data[item.dataIndex];
                const delta = d && d.improvement_delta != null
                  ? ` (${d.improvement_delta > 0 ? '+' : ''}${(d.improvement_delta * 100).toFixed(1)}%)`
                  : '';
                return `  ${t('Score')}: ${item.raw.toFixed(0)}%${delta}`;
              },
              afterLabel: (item) => {
                const d = data[item.dataIndex];
                if (!d) return '';
                const parts = [];
                if (d.issue_score != null)  parts.push(`  ${t('Issues')}: ${(d.issue_score * 100).toFixed(0)}%`);
                if (d.mr_score != null)     parts.push(`  ${t('MRs')}: ${(d.mr_score * 100).toFixed(0)}%`);
                if (d.review_score != null) parts.push(`  ${t('Review')}: ${(d.review_score * 100).toFixed(0)}%`);
                if (d.ci_score != null)     parts.push(`  ${t('CI/CD')}: ${(d.ci_score * 100).toFixed(0)}%`);
                return parts.join('\n');
              },
            },
          },
        },
        animation: GP.chartEntrance(canvas, {
          duration: 800,
          easing: 'easeOutQuart',
        }),
      },
      plugins: [{
        id: 'thresholdBands',
        /* The three zones the pills below the chart name, drawn from the
           theme's LIVE colours on every frame (a mode switch repaints them),
           and each threshold line labelled with its value at the right edge so
           the dashed lines read as "80 %" and "50 %" rather than as two more
           grid lines. */
        beforeDraw(chart) {
          const { ctx: c, chartArea: { left, right }, scales: { y } } = chart;
          if (!y) return;
          const live = (GP.chartTheme && GP.chartTheme.colors) || {};
          const alpha = (GP.chartTheme && GP.chartTheme.alpha) || ((col, a) => col);
          const green = live.green || chartColors.green;
          const yellow = live.yellow || chartColors.yellow;
          const red = live.red || chartColors.red;
          const greenY = y.getPixelForValue(_SCORE_GREEN * 100);
          const yellowY = y.getPixelForValue(_SCORE_YELLOW * 100);
          const topY = y.getPixelForValue(100);
          const bottomY = y.getPixelForValue(0);
          c.save();
          c.fillStyle = alpha(green, 0.07);
          c.fillRect(left, topY, right - left, greenY - topY);
          c.fillStyle = alpha(yellow, 0.07);
          c.fillRect(left, greenY, right - left, yellowY - greenY);
          c.fillStyle = alpha(red, 0.07);
          c.fillRect(left, yellowY, right - left, bottomY - yellowY);
          c.setLineDash([6, 4]);
          c.lineWidth = 1;
          c.font = '600 12px ' + (Chart.defaults.font.family || 'sans-serif');
          c.textAlign = 'right';
          c.textBaseline = 'bottom';
          [[greenY, green, _SCORE_GREEN], [yellowY, yellow, _SCORE_YELLOW]].forEach(([py, col, v]) => {
            c.strokeStyle = alpha(col, 0.55);
            c.beginPath(); c.moveTo(left, py); c.lineTo(right, py); c.stroke();
            c.fillStyle = col;
            c.fillText(Math.round(v * 100) + ' %', right - 4, py - 2);
          });
          c.restore();
        },
      }],
    });
  }

  /* -- Skill Profile Radar Chart -- */
  function initSkillRadar(data) {
    if (_studentDisposed) return;
    const canvas = document.getElementById('skillRadarCanvas');
    if (!canvas || typeof Chart === 'undefined' || !data.length) return;
    if (skillRadarChart) skillRadarChart.destroy();
    skillRadarChart = null;

    // Use latest week that has actual data
    const dataWithScores = data.filter(d => d.overall_score != null);
    if (!dataWithScores.length) {
      canvas.classList.add('d-none');
      const empty = document.getElementById('skillRadarEmpty');
      if (empty) {
        empty.innerHTML = GP.emptyStateHtml(t('No skill profile yet'));
        empty.classList.remove('d-none');
      }
      document.getElementById('weekSummaryStats')?.classList.add('d-none');
      return;
    }
    const latest = dataWithScores[dataWithScores.length - 1];
    const weekLabel = document.getElementById('radarWeekLabel');
    if (weekLabel) weekLabel.textContent = `W${latest.week_number}`;

    /* The theme's category colours (tokens.css --chart-cat-*), the same ones
       the course checklist and the team charts use for these four categories -
       not a blue/green/yellow/purple picked here, which read as a traffic
       light (green MRs = good?) rather than as categories. */
    const categories = [
      { key: 'issue_score', label: t('Issues'), color: chartColors.catIssue || chartColors.blue },
      { key: 'mr_score', label: t('MRs'), color: chartColors.catMr || chartColors.green },
      { key: 'review_score', label: t('Review'), color: chartColors.catReview || chartColors.yellow },
      { key: 'ci_score', label: t('CI/CD'), color: chartColors.catCi || chartColors.purple },
    ];
    _populateWeekSummary(dataWithScores, categories);
    if (canvas.dataset.gpEntered !== '1') {
      GP.drawOnEntry(canvas, function () { initSkillRadar(data); });
      return;
    }
    const _liveBg = () => (GP.chartTheme?.colors?.background) || chartColors.background;
    const _liveGrid = () => (GP.chartTheme?.colors?.grid) || chartColors.grid;

    const labels = categories.map(c => c.label);
    const values = categories.map(c => {
      const v = latest[c.key];
      return v != null ? +(v * 100).toFixed(1) : 0;
    });

    // Point colors - one per axis, matching the stacked bar colors
    const pointColors = categories.map(c => c.color);

    // If we have data from previous week, show comparison
    const datasets = [{
      label: `W${latest.week_number}`,
      data: values,
      borderColor: chartColors.brand,
      backgroundColor: chartAlpha(chartColors.brand, 0.15),
      borderWidth: 2,
      pointRadius: 5,
      pointBackgroundColor: pointColors,
      pointBorderColor: _liveBg,
      pointBorderWidth: 2,
      pointHoverRadius: 7,
    }];

    if (dataWithScores.length >= 2) {
      const prev = dataWithScores[dataWithScores.length - 2];
      const prevValues = categories.map(c => {
        const v = prev[c.key];
        return v != null ? +(v * 100).toFixed(1) : 0;
      });
      datasets.push({
        label: `W${prev.week_number}`,
        data: prevValues,
        borderColor: chartAlpha(chartColors.text, 0.25),
        backgroundColor: chartAlpha(chartColors.text, 0.03),
        borderWidth: 1.5,
        borderDash: [4, 4],
        pointRadius: 3,
        pointBackgroundColor: chartAlpha(chartColors.text, 0.25),
        pointBorderColor: _liveBg,
        pointBorderWidth: 1,
      });
    }

    const ctx = canvas.getContext('2d');
    skillRadarChart = new Chart(ctx, {
      type: 'radar',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: datasets.length > 1,
            position: 'bottom',
            labels: {
              boxWidth: 10,
              padding: 8,
              font: { size: 12 },
            },
          },
          tooltip: {
            // Theme-aware surface comes from Chart.defaults (GP.chartTheme).
            titleFont: { size: 13, weight: '600' },
            bodyFont: { size: 12 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (item) => ` ${item.dataset.label} - ${item.label}: ${item.raw}%`,
            },
          },
        },
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            ticks: {
              display: false,
              stepSize: 25,
            },
            grid: { color: _liveGrid },
            angleLines: { color: _liveGrid },
            pointLabels: {
              font: { size: 12, weight: '600' },
              color: pointColors,
            },
          },
        },
        animation: GP.chartEntrance(canvas, {
          duration: 700,
          easing: 'easeOutQuart',
        }),
      },
    });

  }

  /** Fill the summary stat boxes below the radar chart. */
  function _populateWeekSummary(dataWithScores, categories) {
    const panel = document.getElementById('weekSummaryStats');
    if (!panel) return;

    const latest = dataWithScores[dataWithScores.length - 1];
    const currentEl = document.getElementById('summaryCurrentScore');
    const deltaEl = document.getElementById('summaryDelta');
    const weakestEl = document.getElementById('summaryWeakest');

    // Current overall score
    if (currentEl && latest.overall_score != null) {
      const pct = (latest.overall_score * 100).toFixed(0);
      const cls = latest.overall_score >= _SCORE_GREEN ? 'text-success' : latest.overall_score >= _SCORE_YELLOW ? 'text-warning' : 'text-danger';
      currentEl.className = 'summary-stat-value ' + cls;
      currentEl.textContent = pct + '%';
    }

    // Delta vs last week
    if (deltaEl && latest.improvement_delta != null) {
      const d = (latest.improvement_delta * 100).toFixed(1);
      if (latest.improvement_delta > 0) {
        deltaEl.className = 'summary-stat-value text-success';
        deltaEl.innerHTML = GP.iconSvg('trending-up', 'sm') + ' +' + d + '%';
      } else if (latest.improvement_delta < 0) {
        deltaEl.className = 'summary-stat-value text-danger';
        deltaEl.innerHTML = GP.iconSvg('trending-down', 'sm') + ' ' + d + '%';
      } else {
        deltaEl.className = 'summary-stat-value muted';
        deltaEl.textContent = '- 0%';
      }
    }

    // Weakest area
    if (weakestEl) {
      let worstVal = Infinity;
      let worstLabel = '-';
      categories.forEach(function(c) {
        const v = latest[c.key];
        if (v != null && v < worstVal) {
          worstVal = v;
          worstLabel = c.label;
        }
      });
      weakestEl.textContent = worstVal < Infinity ? worstLabel : '-';
      weakestEl.className = 'summary-stat-value ' + (worstVal < _SCORE_YELLOW ? 'text-danger' : worstVal < _SCORE_GREEN ? 'text-warning' : 'text-success');
    }

    panel.classList.remove('d-none');
  }

  /* -- Check Progress Heatmap -- */
  function renderCheckHeatmap(data) {
    const heatPanel = document.getElementById('checkHeatmapPanel');
    const head = document.getElementById('checkHeatmapHead');
    const body = document.getElementById('checkHeatmapBody');
    if (!heatPanel || !head || !body) return;
    const wrap = document.getElementById('checkHeatmapBody-wrap');
    if (wrap) wrap.style.minHeight = '';

    // Collect all check codes across all weeks
    const codeSet = {};
    const weeksWithChecks = [];
    data.forEach(function(d) {
      if (!d.checks_detail) return;
      weeksWithChecks.push(d.week_number);
      Object.keys(d.checks_detail).forEach(function(code) {
        if (!codeSet[code]) {
          const info = d.checks_detail[code];
          codeSet[code] = info.name || code;
        }
      });
    });

    if (!weeksWithChecks.length || !Object.keys(codeSet).length) {
      heatPanel.classList.add('d-none');
      head.replaceChildren();
      body.replaceChildren();
      return;
    }

    // Sort check codes: R01-R12 first (natural sort), then custom
    const codes = Object.keys(codeSet).sort(function(a, b) {
      const aR = a.match(/^R(\d+)$/), bR = b.match(/^R(\d+)$/);
      if (aR && bR) return parseInt(aR[1]) - parseInt(bR[1]);
      if (aR) return -1;
      if (bR) return 1;
      return a.localeCompare(b);
    });

    // Build header: Check | W1 | W2 | ...
    const esc = escapeHtml;
    const weeks = data.map(function(d) { return d.week_number; });
    head.innerHTML = '<tr><th class="hm-check-col">' + esc(t('Check')) + '</th>' +
      weeks.map(function(w) { return '<th class="hm-week-col">W' + w + '</th>'; }).join('') +
      '</tr>';

    // Build body rows
    body.innerHTML = codes.map(function(code) {
      const label = codeSet[code];
      const cells = data.map(function(d) {
        const cd = d.checks_detail && d.checks_detail[code];
        if (!cd) return '<td><span class="hm-cell hm-cell--empty">-</span></td>';
        const expected = cd.expected !== false;
        // Component tooltips, not native title= (which this project bans).
        if (!expected) return '<td><span class="hm-cell hm-cell--na" data-tippy-content="' + esc(t('Not expected')) + '">' + GP.iconSvg('slash', 'sm') + '</span></td>';
        if (cd.pass) return '<td><span class="hm-cell hm-cell--pass" data-tippy-content="' + esc(t('Pass')) + '">' + GP.iconSvg('check-circle', 'sm') + '</span></td>';
        return '<td><span class="hm-cell hm-cell--fail" data-tippy-content="' + esc(t('Fail')) + '">' + GP.iconSvg('x-circle', 'sm') + '</span></td>';
      }).join('');
      return '<tr><td class="hm-check-col"><span class="hm-code">' + esc(code) + '</span> <span class="hm-name muted">' + esc(label) + '</span></td>' + cells + '</tr>';
    }).join('');

    GP.initTippy(body);
    heatPanel.classList.remove('d-none');
    const _loading = document.getElementById('checkHeatmapLoading');
    if (wrap) GP.revealAfterLoading(_loading, wrap);
  }

  /* -- Render enhanced weekly table -- */
  function renderHistoryTable(data, body) {
    const esc = escapeHtml;
    body.innerHTML = data.map(d => {
      const isEmpty = d.overall_score == null;
      return `<tr${isEmpty ? ' class="trend-row--empty"' : ''}>
      <td>${GP.badgeHtml('W' + d.week_number, isEmpty ? 'muted' : 'gray')}</td>
      <td class="muted">${esc(String(d.snapshot_date || '-'))}</td>
      <td>
        <div class="d-flex items-center gap-2">
          ${scoreCell(d.overall_score)}
          ${progressBarFill(d.overall_score)}
        </div>
      </td>
      <td>${scoreCell(d.mr_score)}</td>
      <td>${scoreCell(d.review_score)}</td>
      <td>${scoreCell(d.ci_score)}</td>
      <td>${scoreCell(d.issue_score)}</td>
      <td>${deltaCell(d.improvement_delta)}</td>
    </tr>`;
    }).join('');
    GP.applyDataDrivenStyles(body);
  }

  /* preData = the first payload inlined into the page (#gp-student-history),
     painted on boot with no fetch - the instant-rows behaviour every
     server-rendered table has. A Reload or a live refresh passes nothing and
     fetches. */
  async function loadHistory(preData, opts) {
    const read = ++_historyRead;
    const _quiet = !!(opts && opts.quiet);
    const _panel = document.getElementById('complianceHistoryPanel');
    if (!_panel) return;
    const courseId = _panel.dataset.courseId;
    const studentId = _panel.dataset.studentId;
    if (!courseId || !studentId) return;
    const emptyMsg = document.getElementById('historyEmpty');
    const body = document.getElementById('historyBody');

    if (emptyMsg && !_historyLoaded && !preData) {
      emptyMsg.classList.remove('d-none');
      emptyMsg.innerHTML = GP.renderLoaderHtml('Loading compliance data...');
    }
    /* The table mechanic every reloading table uses: what is on screen stays
       and is marked busy until the new rows land in its place. */
    if (body && !preData) GP.tableLoading(body, 8);

    try {
      // Request the full history window (API max), not just the teaching-week
      // count. The exam period (skuskove obdobie) extends past the teaching
      // weeks, and the backend already trims to the first/last week that has
      // data and caps at the current academic week, so this never over-pads.
      // Passing only semesterWeeks (13) clipped exam-period snapshots.
      const resp = (preData && Array.isArray(preData.history)) ? preData.history
        : await apiCall(`/api/v1/compliance/${courseId}/student/${studentId}?weeks=52`, 'GET', null,
          { timeoutMs: 10000, maxRetries: 0, ...opts, key: 'student-compliance-history' });
      const data = Array.isArray(resp) ? resp : (resp?.data || resp?.items || []);
      if (_studentDisposed || read !== _historyRead) return false;
      _historyLoaded = true;
      clearComplianceCharts();
      renderCheckHeatmap(data);
      const radarEmpty = document.getElementById('skillRadarEmpty');
      if (!data || !data.length) {
        document.getElementById('weekSummaryStats')?.classList.add('d-none');
        ['historyCanvas', 'skillRadarCanvas'].forEach(function (id) { document.getElementById(id)?.classList.add('d-none'); });
        const none = t('No compliance snapshots recorded yet. Data appears after the first weekly compliance run.');
        // Both charts say so in the box every empty table shows - the score
        // trend in place of its line, the radar in place of its web.
        if (emptyMsg) {
          emptyMsg.classList.remove('d-none');
          emptyMsg.innerHTML = GP.emptyStateHtml(none);
        }
        if (radarEmpty) {
          radarEmpty.classList.remove('d-none');
          radarEmpty.innerHTML = GP.emptyStateHtml(t('No skill profile yet'));
        }
        // ...and the TABLE says it too, in its own body. It used to stay
        // `d-none` and simply never appear, so the card ended at the charts and
        // a reader had no way to tell an empty history from a table that failed
        // to load. Every other table in the app says which it is.
        if (body) body.innerHTML = GP.emptyStateRow(8, none);
        return true;
      }

      lastHistoryData = data;
      ['historyCanvas', 'skillRadarCanvas'].forEach(function (id) { document.getElementById(id)?.classList.remove('d-none'); });
      radarEmpty?.classList.add('d-none');
      // Init Chart.js charts
      initHistoryChart(data);
      initSkillRadar(data);

      // Render table
      if (body) renderHistoryTable(data, body);
      if (emptyMsg) emptyMsg.classList.add('d-none');
      return true;
    } catch (err) {
      if (_studentDisposed || read !== _historyRead || err?.superseded) return false;
      if (_quiet && _historyLoaded) throw err;
      const status = err?.status;
      let why;
      if (status === 403) {
        why = t('Access denied - you may not have permission to view this data.');
      } else if (status === 404) {
        why = t('Compliance history endpoint not available.');
      } else {
        why = t('Failed to load compliance history.');
      }
      if (emptyMsg) {
        emptyMsg.classList.remove('d-none');
        emptyMsg.innerHTML = GP.errorStateHtml(why, t('Retry'));
        GP.bindRetry(emptyMsg, () => loadHistory());
      }
      // The table's own body carries the failure, with a Retry, instead of
      // spinning for the life of the page behind a message meant for the chart.
      if (body) {
        body.innerHTML = GP.errorStateRow(8, why);
        GP.tableLoaded(body);
      }
      // The refresh runner reports manual failures; background loads report here.
      if (!_quiet && typeof showToast === 'function') showToast(why, 'danger');
      if (_quiet) throw new Error(why);
      return false;
    }
  }

  /* The Reload button goes through the refresh contract (GP.refreshRegion):
     the control shows it is working, the region does too (tableLoading in
     loadHistory), the outcome is reported exactly once, and it ends - the
     same behaviour as "Check now" on System Health. Not
     `addEventListener('click', loadHistory)`: that hands the click event in as
     `preData`, and a Reload would try to paint the event instead of fetching. */
  document.getElementById('btnRefreshHistory')?.addEventListener('click', function () {
    GP.refreshRegion({
      button: this,
      region: document.querySelector('#complianceHistoryPanel > .card-body'),
      load: options => loadHistory(undefined, { ...options, quiet: true }),
      successMessage: t('Compliance history reloaded'),
    });
  });

  /* -- Export Compliance Data -- */
  function initExportButton() {
    const btn = document.getElementById('btnExportStudentData');
    if (!btn) return;

    btn.addEventListener('click', function () {
      const studentName = btn.dataset.studentName || 'student';
      const studentUsername = btn.dataset.studentUsername || '';
      const courseCode = btn.dataset.courseCode || '';

      const exportData = {
        student: { name: studentName, username: studentUsername, course: courseCode },
        exported_at: new Date().toISOString(),
      };

      const statCards = document.querySelectorAll('.stat-card');
      if (statCards.length) {
        exportData.activity_summary = {};
        statCards.forEach(card => {
          const value = card.querySelector('.stat-card-value')?.textContent?.trim();
          const label = card.querySelector('.stat-card-label')?.textContent?.trim();
          if (label && value) exportData.activity_summary[label] = value;
        });
      }

      const checksTable = document.querySelector('.data-table tbody');
      if (checksTable) {
        const checksRows = checksTable.querySelectorAll('tr');
        if (checksRows.length) {
          exportData.compliance_checks = [];
          checksRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 3) {
              exportData.compliance_checks.push({
                code: cells[0]?.textContent?.trim(),
                check: cells[1]?.textContent?.trim(),
                result: cells[2]?.textContent?.trim(),
              });
            }
          });
        }
      }

      const commTable = document.querySelectorAll('.data-table');
      commTable.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
          const indicator = row.querySelector('td:first-child')?.textContent?.trim();
          const value = row.querySelector('td:last-child strong')?.textContent?.trim();
          if (indicator && value) {
            if (!exportData.communication_indicators) exportData.communication_indicators = {};
            exportData.communication_indicators[indicator] = value;
          }
        });
      });

      const historyBody = document.getElementById('historyBody');
      if (historyBody && historyBody.children.length) {
        exportData.compliance_history = [];
        Array.from(historyBody.children).forEach(row => {
          const cells = row.querySelectorAll('td');
          if (cells.length >= 8) {
            exportData.compliance_history.push({
              week: cells[0]?.textContent?.trim(),
              date: cells[1]?.textContent?.trim(),
              overall: cells[2]?.textContent?.trim(),
              mrs: cells[3]?.textContent?.trim(),
              review: cells[4]?.textContent?.trim(),
              ci: cells[5]?.textContent?.trim(),
              issues: cells[6]?.textContent?.trim(),
              delta: cells[7]?.textContent?.trim(),
            });
          }
        });
      }

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const filename = `${studentUsername || 'student'}-compliance-${new Date().toISOString().slice(0, 10)}.json`;
      GP.downloadBlob(blob, filename);
      showToast(t('Data exported'), 'success');
    });
  }

  /* -- Generic Client-side Pagination (delegates to ClientPaginator) -- */
  function initPagination(containerId, paginationId, pageSize, itemSelector, opts) {
    const container = document.getElementById(containerId);
    const pagDiv = document.getElementById(paginationId);
    if (!container || !pagDiv) return null;

    const o = opts || {};
    const paginator = new ClientPaginator({
      tbodySelector: '#' + containerId,
      controlsSelector: '#' + paginationId,
      pageSize: pageSize,
      itemSelector: itemSelector,
      scrollOnChange: o.scroll === true,
      pageSizes: [25, 50, 100],
    });
    paginator.render();
    return paginator;
  }

  function filterCommits() {
    const branchFilter = document.getElementById('commitBranchFilter');
    if (!branchFilter || !_commitsPaginator) return;

    const branch = branchFilter.value;
    const filtered = _commitsPaginator._allRows.filter((el) => {
      const rowBranch = el.dataset.branch || '';
      return !branch || rowBranch === branch;
    });

    _commitsPaginator.setFilteredRows(filtered);

    // The count is the paginator's to write, into the card header's `table_count`
    // slot, in the one wording every other table uses ("Showing 1-50 of 120").
    // This wrote a second wording into the same span a frame later, so the same
    // table said "Showing 12 of 120" here and "Showing 1-12 of 12" everywhere else.
  }

  function initAllPagination() {
    // MR discussions now live inside per-MR cards (a student has at most a
    // couple of MRs), so only the long flat tables still paginate.
    _commitsPaginator = initPagination('commitsBody', 'commitsPagination', 50, ':scope > tr');
    _issuesPaginator = initPagination('issuesBody', 'issuesPagination', 10, ':scope > tr');
    _initIssueSideFilter();
  }

  // The issues table holds every issue this member is on, either side of it.
  // These pills are what the Authored / Assigned tabs used to be - a row can
  // match both, which is exactly the case the two tabs listed twice.
  let _issuesPaginator;
  let _issueSidePills;
  function _initIssueSideFilter() {
    const group = document.querySelector('.issues-side-filter');
    const body = document.getElementById('issuesBody');
    if (!group || !body || group._bound) return;
    group._bound = true;
    const label = document.getElementById('issuesFilterCount');
    const apply = (side) => {
      const rows = Array.from(body.querySelectorAll(':scope > tr'));
      const matching = side === 'all'
        ? rows
        : rows.filter((r) => (r.dataset.side || '').split(' ').includes(side));
      if (_issuesPaginator && typeof _issuesPaginator.setFilteredRows === 'function') {
        _issuesPaginator.setFilteredRows(matching);
      } else {
        rows.forEach((r) => r.classList.toggle('d-none', !matching.includes(r)));
      }
      if (label) {
        label.textContent = side === 'all'
          ? ''
          : t('Showing %n of %t')
              .replace('%n', matching.length).replace('%t', rows.length);
      }
    };
    _issueSidePills = new FilterPills('.issues-side-filter', 'data-value', apply);
  }

  // -- SSE-first live updates (polling fallback) --
  const _sdCfg = JSON.parse(document.getElementById('gp-student-detail-config')?.textContent || '{}');
  let _sdSSE = null;
  let _sseToastTimer = null;

  let _reloadTimer = null;
  let _suppressReload = false;
  try {
    if (sessionStorage.getItem('_gp_job_reload_done')) {
      sessionStorage.removeItem('_gp_job_reload_done');
      _suppressReload = true;
    }
  } catch (_) {}
  function _refreshStudentData() {
    // Debounced full-page reload so that all server-rendered sections
    // (commits, issues, MRs, notes, stat cards, compliance checks) pick
    // up fresh data after sync or metrics computation.
    if (_studentDisposed || _reloadTimer) return;
    loadHistory();
    if (_suppressReload) return;
    _reloadTimer = setTimeout(function () {
      _reloadTimer = null;
      try { sessionStorage.setItem('_gp_job_reload_done', '1'); } catch (_) {}
      if (typeof flashToast === 'function') flashToast(t('Data updated'), 'info');
      reloadKeepScroll();
    }, 1200);
  }

  function _connectStudentSSE() {
    _disconnectStudentSSE();
    const streamId = _sdCfg.teamId || _sdCfg.courseId;
    const streamType = _sdCfg.teamId ? 'teams' : 'courses';
    if (!streamId) return;
    _sdSSE = GP.sse({
      url: '/api/v1/' + streamType + '/' + streamId + '/stream',
      events: {
        update: function (e) {
          try {
            const data = JSON.parse(e.data);
            if (data?.event === 'settings_changed') { reloadKeepScroll(); return; }
          } catch (_) {}
          _refreshStudentData();
          clearTimeout(_sseToastTimer);
          _sseToastTimer = setTimeout(function () {
            if (!_studentDisposed) showToast(t('Data updated'), 'success');
          }, 600);
        },
      },
    });
  }

  function _disconnectStudentSSE() {
    if (_sdSSE) { _sdSSE.close(); _sdSSE = null; }
  }

  /* -- Init -- */
  function init() {
    initDiffToggles();
    initDiffFileTree();
    let _historyFirst = null;
    try {
      const _el = document.getElementById('gp-student-history');
      _historyFirst = _el ? JSON.parse(_el.textContent || 'null') : null;
    } catch (_) { _historyFirst = null; }
    loadHistory(_historyFirst && Array.isArray(_historyFirst.history) ? _historyFirst : undefined);
    initExportButton();
    initAllPagination();
    initRunChecksButton();
    _connectStudentSSE();

    const branchFilter = document.getElementById('commitBranchFilter');
    if (branchFilter) {
      branchFilter.addEventListener('change', filterCommits);
    }
  }

  // Checks recompute the whole group, including this student's snapshot.
  function initRunChecksButton() {
    const btn = document.getElementById('btnRunChecks');
    if (!btn) return;
    btn.addEventListener('click', async () => {
      if (!_sdCfg.canEdit) return;
      const teamId = btn.dataset.teamId || _sdCfg.teamId;
      if (!teamId) {
        showToast(t('Missing group context.'), 'danger');
        return;
      }
      await GP.runScopedChecksProcess({
        endpoint: `/api/v1/teams/${teamId}/run-checks`,
        jobKey: 'run_checks:team:' + teamId,
        lockKey: 'runChecks:' + teamId,
        guardScopes: 'course:' + _sdCfg.courseId + ' team:' + teamId,
        label: document.querySelector('#runChecksModal .rcm-scope-name')?.textContent.trim(),
        button: btn,
        courseId: _sdCfg.courseId,
        teamId,
      });
    });
  }

  const onVisibilityChange = function () {
    if (document.visibilityState === 'hidden') {
      _disconnectStudentSSE();
      return;
    }
    // visible
    if (!_sdSSE?.active) {
      _connectStudentSSE();
    }
    if (_pendingRefresh) {
      _pendingRefresh = false;
      _refreshStudentData();
    }
  };

  // Auto-refresh student data when relevant jobs complete
  let _pendingRefresh = false;
  const onJobComplete = function(e) {
    const detail = e.detail || {};
    if (detail.status !== 'done') return;
    if (!GP.jobAffectsScope(detail, { courseId: _sdCfg.courseId, teamId: _sdCfg.teamId })) return;
    if (document.visibilityState === 'visible') {
      _refreshStudentData();
    } else {
      _pendingRefresh = true;
    }
  };

  // Pause SSE when backend is unreachable
  let _sdHealthDown = false;
  const onHealthChange = function (e) {
    if (e.detail?.current === 'down' && !_sdHealthDown) {
      _sdHealthDown = true;
      _disconnectStudentSSE();
    } else if (e.detail?.current !== 'down' && _sdHealthDown) {
      _sdHealthDown = false;
      _connectStudentSSE();
    }
  };

  const onBeforeUnload = function () { _disconnectStudentSSE(); };
  const onChartThemeChange = function () {
    if (!lastHistoryData) return;
    if (historyChart) initHistoryChart(lastHistoryData);
    if (skillRadarChart) initSkillRadar(lastHistoryData);
  };

  const onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gp-student-detail-config') || target.id === 'gp-student-detail-config')) {
      GP.studentDetailCleanup();
    }
  };

  document.addEventListener('visibilitychange', onVisibilityChange);
  document.addEventListener('click', onDocumentClickScrollToMr, true);
  document.addEventListener('click', onDocumentClickCopyCodeContext);
  window.addEventListener('gp:job-complete', onJobComplete);
  document.addEventListener('gp-health-change', onHealthChange);
  window.addEventListener('beforeunload', onBeforeUnload);
  window.addEventListener('gp:themechange', onChartThemeChange);
  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  // Global cleanup register to remove listeners and SSE connections
  GP.studentDetailCleanup = function () {
    if (_studentDisposed) return;
    _studentDisposed = true;
    clearTimeout(_sseToastTimer);
    clearTimeout(_reloadTimer);
    _disconnectStudentSSE();
    clearComplianceCharts();
    
    // Disconnect IntersectionObservers on any diff layouts
    document.querySelectorAll('.diff-layout').forEach(function (layout) {
      if (layout._diffObserver) {
        try { layout._diffObserver.disconnect(); } catch (_) {}
        delete layout._diffObserver;
      }
    });

    document.removeEventListener('visibilitychange', onVisibilityChange);
    document.removeEventListener('click', onDocumentClickScrollToMr, true);
    document.removeEventListener('click', onDocumentClickCopyCodeContext);
    window.removeEventListener('gp:job-complete', onJobComplete);
    document.removeEventListener('gp-health-change', onHealthChange);
    window.removeEventListener('beforeunload', onBeforeUnload);
    window.removeEventListener('gp:themechange', onChartThemeChange);
    document.removeEventListener('DOMContentLoaded', init);
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };
  GP.activePageCleanup = GP.studentDetailCleanup;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
