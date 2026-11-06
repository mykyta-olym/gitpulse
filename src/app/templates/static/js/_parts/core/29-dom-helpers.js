/* Responsive tables: copy each column header into td[data-label] so the CSS can
   turn every row into a labelled "card" on narrow screens (the pattern used by
   GitLab / Stripe / Linear) instead of a tiny horizontal scroll. System-wide,
   on first paint AND every HTMX swap; opt a dense table out with .table-no-cards.
   Idempotent: only fills cells that don't already carry a label. */
function initResponsiveTableLabels(root) {
  const scope = root && root.querySelectorAll ? root : document;
  scope.querySelectorAll('table.data-table:not(.table-no-cards)').forEach((table) => {
    const heads = table.querySelectorAll(':scope > thead > tr > th');
    if (!heads.length) return;
    const labels = Array.prototype.map.call(heads, (th) =>
      (th.textContent || '').trim().replace(/\s+/g, ' ')
    );
    table.querySelectorAll(':scope > tbody > tr').forEach((tr) => {
      let col = 0;
      Array.prototype.forEach.call(tr.children, (cell) => {
        if (cell.tagName !== 'TD') {
          col += cell.colSpan || 1;
          return;
        }
        if (!cell.hasAttribute('data-label') && (cell.colSpan || 1) === 1 && labels[col]) {
          cell.setAttribute('data-label', labels[col]);
        }
        col += cell.colSpan || 1;
      });
    });
  });
}
window.GP.initResponsiveTableLabels = initResponsiveTableLabels;

/* Declarative dynamic styling: templates and page scripts provide data-* values,
   while this single helper owns the CSS variable writes. */
function _asPercent(raw) {
  if (raw == null || raw === '') {
    return null;
  }
  const n = parseFloat(String(raw).replace('%', ''));
  if (!Number.isFinite(n)) {
    return null;
  }
  return Math.max(0, Math.min(100, n)) + '%';
}

function _asCssToken(raw) {
  if (raw == null || raw === '') {
    return null;
  }
  const value = String(raw).trim();
  if (!value || /[;{}]/.test(value)) {
    return null;
  }
  if (!/^[a-zA-Z0-9_\-().,%+\s/*]+$/.test(value)) {
    return null;
  }
  return value;
}

function _asFlexKeyword(raw) {
  const value = String(raw || '').trim();
  const allowed = new Set([
    'start', 'end', 'center', 'stretch', 'baseline',
    'flex-start', 'flex-end', 'space-between', 'space-around', 'space-evenly',
  ]);
  if (value === 'between') return 'space-between';
  if (value === 'around') return 'space-around';
  if (value === 'evenly') return 'space-evenly';
  return allowed.has(value) ? value : null;
}

function _applyCssVar(el, dataName, cssName, parser) {
  if (!el || !el.dataset || !(dataName in el.dataset)) {
    return;
  }
  const value = parser(el.dataset[dataName]);
  if (value == null) {
    el.style.removeProperty(cssName);
    return;
  }
  el.style.setProperty(cssName, value);
}

function applyDataDrivenStyles(root) {
  const scope = root && root.querySelectorAll ? root : document;
  const selector = [
    '[data-progress]',
    '[data-grid-gap]',
    '[data-flex-justify]',
    '[data-flex-align]',
    '[data-flex-gap]',
    '[data-split-width]',
  ].join(', ');
  const elements = [];
  if (scope.matches && scope.matches(selector)) {
    elements.push(scope);
  }
  scope.querySelectorAll(selector).forEach((el) => elements.push(el));
  elements.forEach((el) => {
    _applyCssVar(el, 'progress', '--progress', _asPercent);
    _applyCssVar(el, 'gridGap', '--grid-gap', _asCssToken);
    _applyCssVar(el, 'flexJustify', '--flex-justify', _asFlexKeyword);
    _applyCssVar(el, 'flexAlign', '--flex-align', _asFlexKeyword);
    _applyCssVar(el, 'flexGap', '--flex-gap', _asCssToken);
    _applyCssVar(el, 'splitWidth', '--split-width', _asCssToken);
  });
}

let _dataDrivenStyleObserver = null;
function initDataDrivenStyles(root) {
  applyDataDrivenStyles(root || document);
  if (_dataDrivenStyleObserver || !document.body || typeof MutationObserver !== 'function') {
    return;
  }
  _dataDrivenStyleObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes') {
        applyDataDrivenStyles(mutation.target);
        return;
      }
      mutation.addedNodes.forEach((node) => {
        if (node && node.nodeType === 1) {
          applyDataDrivenStyles(node);
        }
      });
    });
  });
  _dataDrivenStyleObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: [
      'data-progress',
      'data-grid-gap',
      'data-flex-justify',
      'data-flex-align',
      'data-flex-gap',
      'data-split-width',
    ],
  });
}

window.GP.applyDataDrivenStyles = applyDataDrivenStyles;
window.GP.initDataDrivenStyles = initDataDrivenStyles;
