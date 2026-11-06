/* ------------------------------------------------------------------
 *  run-checks-modal.js - behavior for the shared Run Compliance Checks
 *  modal (`partials/_run_checks_modal.html`).
 *
 *  Uses event delegation on `document` so it works regardless of when
 *  the modal markup is inserted (initial render, HTMX lazy swap, or a
 *  later partial refresh). No per-instance init handshake required.
 *
 *  Selectors:
 *    [data-rcm-grid]                    - container, holds `data-defaults`
 *    [data-rcm-search]                  - filter input
 *    [data-rcm-action="select-all"]     - select all visible
 *    [data-rcm-action="deselect-all"]   - deselect all visible
 *    [data-rcm-action="reset-defaults"] - set selection to course defaults
 *    [data-rcm-empty]                   - "no matches" placeholder
 *    [data-rcm-count="selected|total"]  - footer counter targets
 *    .rcm-cb                            - check checkbox
 *    .rcm-item                          - check row (label)
 *    .rcm-group                         - category group wrapper
 * ------------------------------------------------------------------ */
(() => {
  'use strict';

  const tx = (key, fallback) => {
    try {
      return window?.t?.(key) || fallback;
    } catch {
      return fallback;
    }
  };

  const getRoot = (el) => el?.closest?.('.rcm') ?? null;
  const getGrid = (root) => root?.querySelector('[data-rcm-grid]') ?? null;
  const checkboxes = (grid) => (grid ? [...grid.querySelectorAll('.rcm-cb')] : []);
  const items = (grid) => (grid ? [...grid.querySelectorAll('.rcm-item')] : []);
  const defaultsFor = (grid) =>
    (grid.getAttribute('data-defaults') ?? '')
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

  const refresh = (root) => {
    const grid = getGrid(root);
    if (!grid) return;

    for (const g of grid.querySelectorAll('.rcm-group')) {
      let sel = 0;
      let tot = 0;
      for (const cb of g.querySelectorAll('.rcm-cb')) {
        const item = cb.closest('.rcm-item');
        if (item?.classList.contains('is-hidden')) continue;
        tot += 1;
        if (cb.checked) sel += 1;
      }
      const out = g.querySelector('[data-role="count"]');
      if (out) out.textContent = tot ? `${sel}/${tot}` : '';
      g.classList.toggle('is-empty', !tot);
    }

    // Filtering only changes visibility; the request includes every selection.
    const cbs = checkboxes(grid);
    const selectedCount = cbs.filter((cb) => cb.checked).length;

    const countSelected = root.querySelector('[data-rcm-count="selected"]');
    const countTotal = root.querySelector('[data-rcm-count="total"]');
    if (countSelected) countSelected.textContent = String(selectedCount);
    if (countTotal) countTotal.textContent = String(cbs.length);

    const runBtn = root.querySelector('#btnRunChecks');
    if (runBtn) {
      const locked = runBtn.dataset.processLocked === '1'
        || runBtn.dataset.archivedLocked === '1'
        || runBtn.dataset.cooldownActive === '1'
        || runBtn.classList.contains('loading');
      runBtn.disabled = locked || selectedCount === 0;
      runBtn.classList.toggle('is-disabled', locked || selectedCount === 0);
    }
  };

  const applyFilter = (root, q) => {
    const grid = getGrid(root);
    if (!grid) return;
    const needle = (q ?? '').trim().toLowerCase();
    let any = false;
    for (const el of items(grid)) {
      const hay = `${el.dataset.code ?? ''} ${el.dataset.name ?? ''} ${el.dataset.category ?? ''}`.toLowerCase();
      const hit = !needle || hay.includes(needle);
      el.classList.toggle('is-hidden', !hit);
      if (hit) any = true;
    }
    root.querySelector('[data-rcm-empty]')?.classList.toggle('d-none', any);
    refresh(root);
  };

  const selectAllVisible = (root, checked) => {
    const grid = getGrid(root);
    if (!grid) return;
    for (const el of items(grid)) {
      if (el.classList.contains('is-hidden')) continue;
      const cb = el.querySelector('.rcm-cb');
      if (cb) cb.checked = checked;
    }
    refresh(root);
  };

  const applyDefaults = (root) => {
    const grid = getGrid(root);
    if (!grid) return;
    const defaults = defaultsFor(grid);
    const cbs = checkboxes(grid);
    if (defaults.length === 0) {
      for (const cb of cbs) cb.checked = true;
      window.showToast(
        tx(
          'No course defaults configured. Showing all checks instead.',
          'No course defaults configured. Showing all checks instead.',
        ),
        'info',
      );
    } else {
      const set = new Set(defaults);
      for (const cb of cbs) cb.checked = set.has(cb.value);
      window.showToast(
        tx('Selection reset to course defaults.', 'Selection reset to course defaults.'),
        'success',
      );
    }
    refresh(root);
  };

  const ensurePreseeded = (root) => {
    const grid = getGrid(root);
    if (!grid || grid.dataset.rcmSeeded === '1') return;
    grid.dataset.rcmSeeded = '1';
    const defaults = defaultsFor(grid);
    const cbs = checkboxes(grid);
    if (defaults.length > 0) {
      const set = new Set(defaults);
      for (const cb of cbs) cb.checked = set.has(cb.value);
    } else {
      for (const cb of cbs) cb.checked = true;
    }
    refresh(root);
  };

  // -- Delegated listeners (attached once on document) --
  document.addEventListener('click', (e) => {
    const btn = e.target.closest?.('[data-rcm-action]');
    if (!btn) return;
    const root = getRoot(btn);
    if (!root) return;
    switch (btn.getAttribute('data-rcm-action')) {
      case 'select-all':
        selectAllVisible(root, true);
        break;
      case 'deselect-all':
        selectAllVisible(root, false);
        break;
      case 'reset-defaults':
        applyDefaults(root);
        break;
      // 'run' is handled by page-specific handlers (team-detail / project-detail)
      default:
        break;
    }
  });

  document.addEventListener('input', (e) => {
    const input = e.target.closest?.('[data-rcm-search]');
    if (!input) return;
    const root = getRoot(input);
    if (root) applyFilter(root, input.value);
  });

  document.addEventListener('change', (e) => {
    if (!e.target?.classList?.contains('rcm-cb')) return;
    const root = getRoot(e.target);
    if (root) refresh(root);
  });

  const seedAll = (scope) => {
    const root = scope?.querySelectorAll ? scope : document;
    root.querySelectorAll('.rcm').forEach(ensurePreseeded);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => seedAll());
  } else {
    seedAll();
  }

  document.addEventListener('htmx:afterSwap', (e) => seedAll(e.target ?? document));

  // When the modal-open helper fires its custom event we re-seed (no-op if already done).
  document.addEventListener('gp:modal-open', (e) => {
    if (e.detail?.id !== 'runChecksModal') return;
    const root = document.getElementById('runChecksModal')?.querySelector('.rcm');
    if (root) {
      ensurePreseeded(root);
      const search = root.querySelector('[data-rcm-search]');
      if (search) search.value = '';
      applyFilter(root, '');
    }
  });

  // -- dirty-state guard --
  // Warn before discarding a hand-tuned selection. Compares the current
  // checkbox state against the opening snapshot, after initial seeding.
  const armDirtyGuard = () => {
    if (window.GP?.enableFormDirtyGuard) {
      window.GP.enableFormDirtyGuard('runChecksModal');
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', armDirtyGuard);
  } else {
    armDirtyGuard();
  }
  window.GP = window.GP ?? {};
  window.GP.runChecksModal = { refresh, applyFilter, seedAll };
})();
