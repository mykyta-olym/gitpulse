/* ============================================
   Chart.js shared semantic theme.
   Usage: const { colors } = GP.chartTheme;
   ============================================ */
(function () {
  'use strict';
  const colors = {
    green:   '',
    greenBg: 'rgba(45,161,96,0.15)',
    yellow:  '',
    yellowBg:'rgba(193,125,16,0.15)',
    red:     '',
    redBg:   'rgba(236,89,65,0.15)',
    blue:    '',
    brand:   '',
    /* categorical: one per check category, per mode (tokens.css) */
    catIssue: '', catMr: '', catReview: '', catCi: '', catQuality: '', catCustom: '',
    blueBg:  'rgba(66,143,220,0.2)',
    orange:  '',
    orangeBg:'rgba(217,149,48,0.15)',
    purple:  '',
    teal:    '',
    grid:    '',
    text:    '',
    surface: '',
    tooltipBg:     '',
    tooltipText:   '',
    tooltipBorder: '',
  };

  function resolveToken(name, fallback) {
    const probe = document.createElement('span');
    probe.style.color = 'var(' + name + ')';
    probe.style.position = 'absolute';
    probe.style.visibility = 'hidden';
    probe.style.pointerEvents = 'none';
    (document.body || document.documentElement).appendChild(probe);
    const resolved = getComputedStyle(probe).color;
    probe.remove();
    return alpha(resolved || fallback, 1);
  }

  function readColors() {
    Object.assign(colors, {
      /* semantic, per mode (tokens.css --chart-*) */
      green: resolveToken('--chart-success', '#2da160'),
      yellow: resolveToken('--chart-warning', '#d99530'),
      red: resolveToken('--chart-danger', '#f57f6c'),
      blue: resolveToken('--gl-blue-400', '#428fdc'),
      /* The theme's own colour for the brand series (Score Trend, Skill
         Profile, live intelligence) - the accent under an accent theme. */
      brand: resolveToken('--chart-brand', '#428fdc'),
      catIssue:   resolveToken('--chart-cat-issue', '#9475db'),
      catMr:      resolveToken('--chart-cat-mr', '#428fdc'),
      catReview:  resolveToken('--chart-cat-review', '#d99530'),
      catCi:      resolveToken('--chart-cat-ci', '#0094b6'),
      catQuality: resolveToken('--chart-cat-quality', '#ec4899'),
      catCustom:  resolveToken('--chart-cat-custom', '#a855f7'),
      orange: resolveToken('--gl-orange-300', '#d99530'),
      purple: resolveToken('--gl-purple-500', '#7b58cf'),
      teal: resolveToken('--gl-teal-500', '#0094b6'),
      grid: resolveToken('--chart-grid', '#dcdcde'),
      text: resolveToken('--gl-text-color-subtle', '#626168'),
      surface: resolveToken('--gl-background-color-strong', '#ececef'),
      /* The ground a chart is drawn on - the ring around a data point and the
         gap between doughnut segments are cut from this, in either mode. */
      background: resolveToken('--gl-background-color-default', '#ffffff'),
      tooltipBg: resolveToken('--gl-background-color-overlap', '#ffffff'),
      tooltipText: resolveToken('--gl-text-color-default', '#28272d'),
      tooltipBorder: resolveToken('--gl-border-color-default', '#dcdcde'),
    });
  }

  function applyDefaults() {
    if (typeof Chart === 'undefined') return;
    Chart.defaults.color = colors.text;
    Chart.defaults.borderColor = colors.grid;
    Chart.defaults.font.family = getComputedStyle(document.documentElement)
      .getPropertyValue('--font-family').trim();
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.tooltip.backgroundColor = colors.tooltipBg;
    Chart.defaults.plugins.tooltip.titleColor = colors.tooltipText;
    Chart.defaults.plugins.tooltip.bodyColor = colors.tooltipText;
    Chart.defaults.plugins.tooltip.borderColor = colors.tooltipBorder;
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.padding = 10;
  }

  function updateExistingCharts(before) {
    if (typeof Chart === 'undefined' || !Chart.instances) return;
    Object.values(Chart.instances).forEach(function (chart) {
      /* The brand series follows the theme too: a dataset drawn in the
         previous brand colour is redrawn in the new one (the score trend, the
         skill profile), so a mode or accent switch does not leave the line in
         the colour of the theme that is gone. */
      if (before && before.brand && colors.brand && before.brand !== colors.brand) {
        const same = function (a, b) { return alpha(a, 1) === alpha(b, 1); };
        (chart.data && chart.data.datasets || []).forEach(function (ds) {
          if (typeof ds.borderColor === 'string' && same(ds.borderColor, before.brand)) ds.borderColor = colors.brand;
          if (typeof ds.backgroundColor === 'string') {
            const old = rgba(ds.backgroundColor);
            const brand = rgba(before.brand);
            if (old && brand && old.slice(0, 3).join() === brand.slice(0, 3).join()) ds.backgroundColor = alpha(colors.brand, old[3] / 255);
          }
          if (typeof ds.pointBackgroundColor === 'string' && same(ds.pointBackgroundColor, before.brand)) ds.pointBackgroundColor = colors.brand;
        });
      }
      const options = chart.options || {};
      options.color = colors.text;
      Object.values(options.scales || {}).forEach(function (scale) {
        if (scale.ticks) scale.ticks.color = colors.text;
        if (scale.grid) scale.grid.color = colors.grid;
        if (scale.border) scale.border.color = colors.grid;
      });
      const plugins = options.plugins || {};
      if (plugins.legend && plugins.legend.labels) {
        plugins.legend.labels.color = colors.text;
      }
      if (plugins.tooltip) {
        plugins.tooltip.backgroundColor = colors.tooltipBg;
        plugins.tooltip.titleColor = colors.tooltipText;
        plugins.tooltip.bodyColor = colors.tooltipText;
        plugins.tooltip.borderColor = colors.tooltipBorder;
      }
      chart.update('none');
    });
  }

  function refresh() {
    const before = Object.assign({}, colors);
    readColors();
    applyDefaults();
    updateExistingCharts(before);
  }

  /* Let the browser parse CSS colors, including color(srgb ...) and oklch().
     Appending a HEX suffix to a computed CSS color is never valid. */
  let colorContext;
  function rgba(color) {
    if (colorContext === undefined) {
      const canvas = document.createElement('canvas');
      canvas.width = canvas.height = 1;
      colorContext = canvas.getContext('2d', { willReadFrequently: true });
    }
    if (!colorContext) return null;
    colorContext.clearRect(0, 0, 1, 1);
    colorContext.fillStyle = 'transparent';
    colorContext.fillStyle = color;
    colorContext.fillRect(0, 0, 1, 1);
    return colorContext.getImageData(0, 0, 1, 1).data;
  }
  function alpha(color, a) {
    const channels = rgba(color);
    if (!channels) return color;
    return 'rgba(' + channels[0] + ', ' + channels[1] + ', ' + channels[2] + ', ' + (channels[3] / 255 * Math.max(0, Math.min(1, a))) + ')';
  }

  readColors();
  applyDefaults();
  GP.chartTheme = { colors: colors, refresh: refresh, alpha: alpha, token: resolveToken };
  window.addEventListener('gp:themechange', refresh);
  /* Chart.js is a per-page script that loads AFTER this bundle, so the
     applyDefaults() above ran against no Chart at all: every chart drew its
     ticks in Chart.js's own #666, its labels in Helvetica and its tooltips in
     the library's black box until the reader toggled the theme. Deferred
     scripts have all run by DOMContentLoaded; the charts themselves are
     created later (on scroll), so this is early enough. */
  document.addEventListener('DOMContentLoaded', refresh);
})();
