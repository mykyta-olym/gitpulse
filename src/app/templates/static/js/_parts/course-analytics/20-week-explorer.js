  /* ==========================================
   *  Week Analytics - interactive week explorer
   * ========================================== */
  const weekPills = document.getElementById('weekPills');
  const weekDetail = document.getElementById('weekDetail');
  const waDetailHead = document.getElementById('waDetailHead');
  const waSideStats = document.getElementById('waSideStats');
  const waRingCenter = document.getElementById('waRingCenter');
  const waPrev = document.getElementById('waPrev');
  const waNext = document.getElementById('waNext');

  let _waBarChart = null;
  let _waRingChart = null;
  let _waSelectedWeek = 0;

  /* Click handler */
  if (weekPills) {
    weekPills.addEventListener('click', (e) => {
      const pill = e.target.closest('.tab-btn');
      if (!pill) return;
      pill.blur();
      const week = parseInt(pill.dataset.value, 10);
      if (!week) return;
      /* Clicking the active pill used to DESELECT it and hide the whole detail
         panel - the card collapsed to the toolbar and the pills, with nothing
         under them and no word about why. A week explorer always shows a week
         (the same rule the auto-select follows), so the active pill is a
         no-op, as it is on every other pill strip in the app. */
      if (pill.classList.contains('active')) return;
      selectWeek(week);
    });
  }

  /* Arrow navigation */
  if (waPrev) waPrev.addEventListener('click', () => {
    const target = (_waSelectedWeek || 1) - 1;
    if (target >= 1) selectWeek(target);
  });
  if (waNext) waNext.addEventListener('click', () => {
    const pills = weekPills ? weekPills.querySelectorAll('.tab-btn') : [];
    const max = pills.length;
    const target = (_waSelectedWeek || 0) + 1;
    if (target <= max) selectWeek(target);
  });

  if (weekPills) {
    const initial = weekPills.querySelector('.tab-btn.active');
    const week = Number(initial?.dataset.value);
    if (week) selectWeek(week, { scrollPill: false });
    else _renderEmptyWeek('', t('No weeks to show yet - this course has no teaching weeks configured.'));
  }

  /* The ONE empty state of the detail panel: head (may be empty), the
     shared empty-state box (GP.emptyStateHtml - the box every empty table
     uses) in place of the charts. Used both for "no week at all" and for a
     selected week that carries no data. */
  function _renderEmptyWeek(headHtml, message) {
    if (!weekDetail) return;
    weekDetail.classList.remove('d-none');
    if (waDetailHead) waDetailHead.innerHTML = headHtml || '';
    const body = weekDetail.querySelector('.wa-detail-body');
    if (body) body.classList.add('d-none');
    let placeholder = weekDetail.querySelector('.wa-empty-placeholder');
    if (!placeholder) {
      placeholder = document.createElement('div');
      placeholder.className = 'wa-empty-placeholder';
      weekDetail.appendChild(placeholder);
    }
    placeholder.innerHTML = GP.emptyStateHtml(message);
    placeholder.classList.remove('d-none');
  }

  function selectWeek(week, opts) {
    _waSelectedWeek = week;
    if (!weekPills) return;
    weekPills.querySelectorAll('.tab-btn').forEach(p => { p.classList.remove('active'); p.setAttribute('aria-selected', 'false'); });
    const pill = weekPills.querySelector(`.tab-btn[data-value="${week}"]`);
    if (pill) {
      pill.classList.add('active');
      pill.setAttribute('aria-selected', 'true');
      /* Only scroll the pill into its horizontal strip on user interaction.
         Browsers still scroll the document vertically when the pill is
         below the fold even with block:'nearest', so the initial auto-
         select skips it to keep the user at the top of the page. */
      if (!opts || opts.scrollPill !== false) {
        const strip = weekPills;
        const stripRect = strip.getBoundingClientRect();
        const pillRect = pill.getBoundingClientRect();
        /* Horizontal-only scroll inside the pill strip, never page-level */
        if (pillRect.left < stripRect.left || pillRect.right > stripRect.right) {
          strip.scrollBy({
            left: pillRect.left - stripRect.left - (stripRect.width - pillRect.width) / 2,
            behavior: 'smooth',
          });
        }
      }
    }
    renderWeekDetail(week);
  }

  function renderWeekDetail(week) {
    if (!weekDetail) return;
    const actRow = (_cfg.activityData || []).find(r => r.week === week) || {};
    const trendRow = (_cfg.trends || []).find(r => r.week_number === week) || {};
    const commits = actRow.commits ?? 0;
    const mrs = actRow.merge_requests ?? 0;
    const pipes = actRow.pipelines ?? 0;
    const issues = actRow.issues ?? 0;
    const reviews = actRow.reviews ?? 0;
    const totalAct = commits + mrs + pipes + issues + reviews;
    const hasTrend = trendRow.avg_score != null;

    /* Exam period (skuskove obdobie): weeks beyond the teaching-week count
       carry the same EXAM PERIOD styling as the top stat card. */
    const examStart = parseInt(_cfg.examPeriodStart, 10) || 0;
    const isExam = examStart > 0 && week > examStart;
    const examChip = isExam
      ? GP.badgeHtml(t('Exam Period') + ' \u00b7 ' + t('Week') + ' ' + (week - examStart), 'warning')
      : '';

    weekDetail.classList.remove('d-none');

    /* No data - differentiate past / current / future and "before tracking
       started" so users understand WHY the week is empty. We never auto-
       trigger sync here - that's done from the course page sync button. */
    if (totalAct === 0 && !hasTrend) {
      const cw = parseInt(_cfg.currentWeek, 10) || 0;

      /* Detect when tracking actually started: earliest week that has any
         activity or compliance trend. Weeks before that = the project was
         imported later, so empty is expected and not a problem. */
      const allDataWeeks = [
        ...((_cfg.activityData || []).map(r => r.week)),
        ...((_cfg.trends || []).map(r => r.week_number)),
      ].filter(w => Number.isFinite(w));
      const firstTrackedWeek = allDataWeeks.length ? Math.min(...allDataWeeks) : null;

      let chipKey = 'No data yet';
      let chipVariant = 'muted';
      let bodyMsg = '';

      if (cw && week > cw) {
        chipKey = 'Future week';
        bodyMsg = t('This week has not started yet.');
      } else if (firstTrackedWeek && week < firstTrackedWeek) {
        chipKey = 'Before tracking started';
        bodyMsg = t('No data - tracking for this course started in week') +
                  ' ' + firstTrackedWeek + '.';
      } else if (cw && week === cw) {
        chipKey = 'Awaiting sync';
        chipVariant = 'info';
        bodyMsg = t('This week just started. Student activity is synced from GitLab via webhooks (real-time) or periodic sync. If data is missing, run a manual sync from the course page.');
      } else {
        bodyMsg = t('No student activity recorded for this week. If you expected data, check team configuration or run a manual sync from the course page.');
      }

      _renderEmptyWeek(
        `<h4 class="wa-detail-title">${t('Week')} ${week}</h4>` +
          examChip +
          GP.badgeHtml(t(chipKey), chipVariant),
        bodyMsg
      );
      return;
    }

    /* Hide any leftover empty placeholder when data exists */
    const stalePlaceholder = weekDetail.querySelector('.wa-empty-placeholder');
    if (stalePlaceholder) stalePlaceholder.classList.add('d-none');

    const body = weekDetail.querySelector('.wa-detail-body');
    if (body) body.classList.remove('d-none');

    /* Header */
    if (waDetailHead) {
      const scoreVariant = !hasTrend ? '' : trendRow.avg_score >= greenPct ? 'success'
        : (trendRow.avg_score >= yellowPct ? 'warning' : 'danger');
      waDetailHead.innerHTML =
        `<h4 class="wa-detail-title">${t('Week')} ${week}</h4>` +
        examChip +
        `<div class="wa-head-metrics">` +
          GP.badgeHtml(t('Activity') + ': ' + totalAct, 'gray') +
          (hasTrend ? GP.badgeHtml(t('Compliance') + ': ' + trendRow.avg_score.toFixed(1) + '%', scoreVariant) : '') +
          (hasTrend ? GP.badgeHtml(String(trendRow.improved_count ?? 0), 'success', { icon: 'trending-up' }) +
                      GP.badgeHtml(String(trendRow.declined_count ?? 0), 'danger', { icon: 'trending-down' }) : '') +
        `</div>`;
    }

    /* -- Bar chart: Activity breakdown -- */
    const barCanvas = document.getElementById('waBarChart');
    if (barCanvas && typeof Chart !== 'undefined') {
      if (_waBarChart) { _waBarChart.destroy(); _waBarChart = null; }

      if (totalAct === 0) {
        // No activity - show empty state instead of empty chart
        const wrap = barCanvas.closest('.wa-chart-wrap');
        if (wrap) {
          wrap.classList.add('wa-chart-wrap--empty');
          barCanvas.style.display = 'none';
          let emptyEl = wrap.querySelector('.wa-empty-msg');
          if (!emptyEl) {
            emptyEl = document.createElement('div');
            emptyEl.className = 'wa-empty-msg';
            wrap.appendChild(emptyEl);
          }
          emptyEl.innerHTML = GP.emptyStateHtml(hasTrend
            ? t('No GitLab events tracked this week')
            : t('No activity recorded this week'), 'chart-bar-sm');
        }
      } else {
        // Restore canvas if previously hidden
        const wrap = barCanvas.closest('.wa-chart-wrap');
        if (wrap) {
          wrap.classList.remove('wa-chart-wrap--empty');
          barCanvas.style.display = '';
          const emptyEl = wrap.querySelector('.wa-empty-msg');
          if (emptyEl) emptyEl.remove();
        }

      const labels = [
        t('Commits'),
        t('MRs'),
        t('Pipelines'),
        t('Issues'),
        t('Reviews'),
      ];
      const values = [commits, mrs, pipes, issues, reviews];
      /* The same categorical palette the Teacher's Checklist and the legend
         dots use (tokens.css --chart-cat-*): commits = quality, MRs, CI,
         issues, reviews. */
      const _c = (GP.chartTheme && GP.chartTheme.colors) || {};
      const colors = [_c.catQuality || '#ec4899', _c.catMr || '#428fdc', _c.catCi || '#0094b6', _c.catIssue || '#9475db', _c.catReview || '#d99530'];
      const _alpha = (GP.chartTheme && GP.chartTheme.alpha) || function (x) { return x; };

      // The first draw waits until the chart is on screen (GP.drawOnEntry).
      GP.drawOnEntry(barCanvas, function () {
        if (barCanvas.style.display === 'none') return;
        if (_waBarChart) { _waBarChart.destroy(); _waBarChart = null; }
        _waBarChart = new Chart(barCanvas.getContext('2d'), {
          type: 'bar',
          data: {
            labels,
            datasets: [{
              data: values,
              backgroundColor: colors.map(c => _alpha(c, 0.8)),
              borderColor: colors,
              borderWidth: 2,
              borderRadius: 6,
              borderSkipped: false,
              barPercentage: 0.65,
              categoryPercentage: 0.8,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: GP.barsEntrance(barCanvas),
            plugins: {
              legend: { display: false },
              tooltip: {
                // Theme-aware surface comes from Chart.defaults (GP.chartTheme);
                // a hardcoded dark box was dark-on-dark text on the light theme.
                titleFont: { size: 13, weight: '600' },
                bodyFont: { size: 12 },
                padding: 10,
                cornerRadius: 8,
                displayColors: true,
                boxWidth: 10,
                boxHeight: 10,
                boxPadding: 4,
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                // Neutral grid fallback that reads on BOTH themes if chartColors
                // has not resolved yet (white-6% vanished on the light card).
                grid: { color: chartColors.grid || 'rgba(128,128,128,0.15)' },
                ticks: { precision: 0, font: { size: 12 } },
              },
              x: {
                grid: { display: false },
                ticks: { font: { size: 12, weight: '500' }, color: chartColors.text || '#999' },
              },
            },
          },
        });
      });
      }
    }

    /* -- Doughnut chart: Compliance ring -- */
    const ringCanvas = document.getElementById('waRingChart');
    if (ringCanvas && typeof Chart !== 'undefined') {
      if (_waRingChart) { _waRingChart.destroy(); _waRingChart = null; }

      if (hasTrend) {
        const score = trendRow.avg_score;
        // The arc reads its colour from the same tokens the rest of the app
        // uses; `#22c55e/#f59e0b/#ef4444` were Tailwind's, not GitLab's, and
        // the amber one also ended up as the centre LABEL, at 2.15:1.
        const state = score >= greenPct ? 'green' : (score >= yellowPct ? 'amber' : 'red');
        const css = getComputedStyle(document.documentElement);
        const ringColor = css.getPropertyValue(
          state === 'green' ? '--gl-green-500' : state === 'amber' ? '--gl-orange-500' : '--gl-red-500',
        ).trim();
        if (waRingCenter) {
          waRingCenter.classList.remove('wa-ring--green', 'wa-ring--amber', 'wa-ring--red');
          waRingCenter.classList.add(`wa-ring--${state}`);
          waRingCenter.innerHTML =
            `<span class="wa-ring-value">${score.toFixed(1)}%</span>` +
            `<span class="wa-ring-label">${t('Compliance')}</span>`;
        }
        // The first draw waits until the chart is on screen (GP.drawOnEntry).
        GP.drawOnEntry(ringCanvas, function () {
          if (ringCanvas.style.display === 'none') return;
          if (_waRingChart) { _waRingChart.destroy(); _waRingChart = null; }
          _waRingChart = new Chart(ringCanvas.getContext('2d'), {
            type: 'doughnut',
            data: {
              labels: [t('Compliance'), t('Remaining')],
              datasets: [{
                data: [score, 100 - score],
                // The "remaining" track has to read on BOTH themes: white-at-6%
                // vanished on the light card. Same neutral as the empty-state ring.
                backgroundColor: [ringColor + 'dd', 'rgba(148,163,184,0.25)'],
                borderWidth: 0,
                cutout: '78%',
              }],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              animation: GP.ringEntrance(ringCanvas),
              plugins: {
                legend: { display: false },
                tooltip: {
                  enabled: true,
                  // Anchor the tooltip above the hovered arc (and the centre
                  // score label) instead of overlapping/sitting under it.
                  position: 'nearest',
                  yAlign: 'bottom',
                  displayColors: false,
                  callbacks: {
                    label: (ctx) => `${ctx.label}: ${Number(ctx.parsed).toFixed(1)}%`,
                  },
                },
              },
            },
          });
        });
      } else {
        if (waRingCenter) {
          waRingCenter.classList.remove('wa-ring--green', 'wa-ring--amber', 'wa-ring--red');
          waRingCenter.innerHTML =
            `<span class="wa-ring-value">\u2014</span>` +
            `<span class="wa-ring-label">${t('Compliance')}</span>`;
        }
        // No compliance data - draw a visible placeholder ring (matches the
        // activity pipeline doughnut's empty state; a near-transparent ring
        // read as "the donut disappeared" on the dark background).
        // Through the same entry draw as the scored ring, so the later of
        // the two calls is the one drawn.
        GP.drawOnEntry(ringCanvas, function () {
          if (_waRingChart) { _waRingChart.destroy(); _waRingChart = null; }
          _waRingChart = new Chart(ringCanvas.getContext('2d'), {
            type: 'doughnut',
            data: {
              labels: [t('No compliance data')],
              datasets: [{
                data: [1],
                backgroundColor: ['rgba(148,163,184,0.25)'],
                borderWidth: 0,
                cutout: '78%',
              }],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              events: [],
              animation: false,
              plugins: { legend: { display: false }, tooltip: { enabled: false } },
            },
          });
        });
      }
    }

    /* -- Side stats -- */
    if (waSideStats) {
      if (hasTrend) {
        waSideStats.innerHTML =
          `<div class="wa-stat"><span class="wa-stat-val">${trendRow.students_count ?? 0}</span><span class="wa-stat-lbl">${t('Active')}</span></div>` +
          `<div class="wa-stat wa-stat--green"><span class="wa-stat-val">${trendRow.improved_count ?? 0}</span><span class="wa-stat-lbl">${t('Improved')}</span></div>` +
          `<div class="wa-stat wa-stat--red"><span class="wa-stat-val">${trendRow.declined_count ?? 0}</span><span class="wa-stat-lbl">${t('Declined')}</span></div>`;
      } else {
        waSideStats.innerHTML =
          `<p class="muted text-xs text-center">${t('No compliance data')}</p>`;
      }
    }
  }

