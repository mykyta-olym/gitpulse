/**
 * GitPulse - Reusable Frontend Components
 *
 * Backward compatible with existing global constructors/functions.
 */
;(function() {
'use strict';

const GP = window.GP || (window.GP = {});

/* ============================================
   ClientPaginator
   ============================================ */
class ClientPaginator {
  constructor(opts = {}) {
    this.tbody = document.querySelector(opts.tbodySelector || '');
    this.controls = document.querySelector(opts.controlsSelector || '');
    this._storageKey = opts.storageKey || opts.id || (this.tbody ? (this.tbody.closest('table')?.id || '') : '') || null;
    if (this._storageKey && !this._storageKey.includes('/')) {
      const p = (window.location && window.location.pathname) ? window.location.pathname : '';
      this._storageKey = p + '#' + this._storageKey;
    }
    /* Preferences > Behavior > "Rows per page" is the ACCOUNT default; a choice
       already made on THIS table still wins, because it is the more specific
       answer and the reader made it last. Without the account value a new
       device silently fell back to 50 however the reader had it set. */
    const saved = this._storageKey ? localStorage.getItem('gp_ps_' + this._storageKey) : null;
    const accountDefault = document.documentElement.getAttribute('data-page-size');
    this.pageSize = saved
      ? (saved === 'all' ? 'all' : (parseInt(saved, 10) || 50))
      : (accountDefault === 'all'
          ? 'all'
          : (parseInt(accountDefault, 10) || opts.pageSize || 50));
    if (this.pageSize !== 'all' && this.pageSize !== 25 && this.pageSize !== 50 && this.pageSize !== 100) {
      this.pageSize = 50;
    }
    this.pageSizes = [25, 50, 100];
    this.showPerPage = opts.showPerPage !== false;
    this.currentPage = 1;
    this._getVisibleRows = typeof opts.getVisibleRows === 'function' ? opts.getVisibleRows : null;
    this._itemSelector = opts.itemSelector || null;
    this._scrollOnChange = opts.scrollOnChange === true;
    this._allRows = [];
    this._filteredRows = [];
    this._id = opts.id || '';
    this._controlsBound = false;
    this._isInitialRender = true;
    this._suppressAnimation = false;

    /* Server-side pagination: skip client row management, call onFetch instead */
    this._serverSide = typeof opts.onFetch === 'function';
    this._onFetch = opts.onFetch || null;
    this._serverTotal = 0;

    if (!this._serverSide) {
      this._readRows();
      }
    this._bindControls();

    // Register on container for SortableTable integration
    if (this.tbody) this.tbody._clientPaginator = this;
  }

  register(id) {
    this._id = id;
    if (!this._storageKey && id) {
      const p = (window.location && window.location.pathname) ? window.location.pathname : '';
      this._storageKey = p + '#' + id;
    }
    if (!window._paginators) window._paginators = {};
    if (id) window._paginators[id] = this;
    if (this.tbody) {
      this.tbody._clientPaginator = this;
      const table = this.tbody.closest('table');
      if (table) table._clientPaginator = this;
    }
    return this;
  }

  _readRows() {
    if (!this.tbody) {
      this._allRows = [];
      this._filteredRows = [];
      return;
    }

    if (this._itemSelector) {
      this._allRows = Array.from(this.tbody.querySelectorAll(this._itemSelector));
    } else {
      this._allRows = Array.from(
        this.tbody.querySelectorAll('tr[data-search], tr:not(.table-empty-row)')
      ).filter((row) => !row.classList.contains('table-empty-row'));
    }

    this._filteredRows = [...this._allRows];
  }

  _bindControls() {
    if (!this.controls || this._controlsBound) {
      return;
    }

    this.controls.addEventListener('click', (event) => {
      const button = event.target.closest('[data-page]');
      if (!button || button.disabled) {
        return;
      }
      // Commit pending search inside the click, so rendering cannot remove
      // the pressed control between pointerdown and pointerup. Relative
      // arrows refer to the freshly filtered page; numbered pages stay exact.
      const filter = this._tableFilter;
      if (filter?._pendingSearch && filter._isCurrent()) filter.apply();
      const page = button.classList.contains('pagination-next') ? this.currentPage + 1
        : button.classList.contains('pagination-prev') ? this.currentPage - 1
        : Number(button.dataset.page);
      if (!Number.isNaN(page)) {
        this.goToPage(page);
      }
    });

    /* Opening and closing the page-size menu is GP.dropdown's job - the same
       controller every other dropdown uses. What stood here was a second one:
       it caught the toggle click, called stopPropagation() so the shared
       controller never saw it, and re-implemented open/close to add portaling.
       The shared controller portals on request now, so this is gone. */

    this._controlsBound = true;
  }

  setFilteredRows(rows) {
    this._filteredRows = Array.isArray(rows) ? rows : [];
    this.currentPage = 1;
    this._suppressAnimation = true;
    this.render();
    this._suppressAnimation = false;
    // Filtered down to nothing is a state, not an empty page. Here rather than
    // in each caller, because every filtered table comes through this one.
    if (GP.tableFilteredToNothing) {
      GP.tableFilteredToNothing(this.tbody, this._filteredRows.length, this._allRows.length);
    }
  }

  resync() {
    this._readRows();
    this._suppressAnimation = true;
    this.render();
    this._suppressAnimation = false;
    return this;
  }

  /** Re-read row order from DOM (after sort) but preserve active filter. */
  resyncOrder() {
    const prevFiltered = new Set(this._filteredRows);
    const hadFilter = prevFiltered.size < this._allRows.length;
    this._readRows();
    if (hadFilter) {
      this._filteredRows = this._allRows.filter(r => prevFiltered.has(r));
    }
    this._suppressAnimation = true;
    this.render();
    this._suppressAnimation = false;
    return this;
  }

  get allRows() {
    return this._allRows;
  }

  get filteredRows() {
    if (this._getVisibleRows) {
      const rows = this._getVisibleRows();
      return Array.isArray(rows) ? rows : [];
    }
    return this._filteredRows;
  }

  get totalPages() {
    if (this.pageSize === 'all') {
      return 1;
    }
    const total = this._serverSide ? this._serverTotal : this.filteredRows.length;
    return Math.max(1, Math.ceil(total / this.pageSize));
  }

  /** Server-side mode: update total count and re-render controls only. */
  setServerTotal(total) {
    this._serverTotal = total;
    if (this.currentPage > this.totalPages) this.currentPage = this.totalPages || 1;
    const ps = this.pageSize === 'all' ? total : this.pageSize;
    const startIndex = (this.currentPage - 1) * ps;
    const endIndex = Math.min(total, startIndex + ps);
    this._renderControls(total, startIndex, endIndex);
  }

  goToPage(page, scroll) {
    const numeric = Number(page);
    const target = Number.isFinite(numeric) ? numeric : 1;
    this.currentPage = Math.min(Math.max(target, 1), this.totalPages);
    if (this._serverSide) {
      this._onFetch(this.currentPage, this.pageSize);
      return;
    }
    this.render();
    this._suppressAnimation = false;
    if ((scroll || this._scrollOnChange) && this.tbody) {
      GP.scrollWithinPageContent?.(this.tbody, { block: 'start' });
    }
  }

  changePageSize(size) {
    if (String(size) === 'all') {
      this.pageSize = 'all';
    } else {
      const parsed = parseInt(size, 10);
      this.pageSize = Number.isNaN(parsed) ? this.pageSize : parsed;
    }
    this.currentPage = 1;
    if (this._storageKey) {
      try { localStorage.setItem('gp_ps_' + this._storageKey, String(this.pageSize)); } catch (_) {}
    }
    if (this._serverSide) {
      this._onFetch(this.currentPage, this.pageSize);
      return;
    }
    this._suppressAnimation = true;
    this.render();
    this._suppressAnimation = false;
  }

  render() {
    const rows = this.filteredRows;
    const totalRows = rows.length;

    if (this.currentPage > this.totalPages) {
      this.currentPage = this.totalPages;
    }

    const startIndex = this.pageSize === 'all' ? 0 : (this.currentPage - 1) * this.pageSize;
    const endIndex = this.pageSize === 'all'
      ? totalRows
      : Math.min(totalRows, startIndex + this.pageSize);

    // Lock container height during transitions to prevent scrollbar flash.
    const wrapper = (!this._isInitialRender && this.tbody) ? this.tbody.closest('.table-responsive') : null;
    if (wrapper) wrapper.style.minHeight = wrapper.offsetHeight + 'px';

    this._isInitialRender = false;

    const table = this.tbody ? this.tbody.closest('table') : null;
    if (table) table.classList.add('paginator-ready');

    this._allRows.forEach((row) => {
      row.classList.add('d-none');
    });

    for (let index = startIndex; index < endIndex; index += 1) {
      if (rows[index]) {
        rows[index].classList.remove('d-none');
      }
    }

    this._renderControls(totalRows, startIndex, endIndex);

    // Restripe visible rows for correct zebra colouring
    if (typeof restripeTable === 'function' && this.tbody) {
      restripeTable(this.tbody);
    }

    // Release height lock after browser paints the new state
    if (wrapper) {
      requestAnimationFrame(() => { wrapper.style.minHeight = ''; });
    }
  }

  /** Write "Showing X of Y" or "Showing X-Y of Z" into this table's card header slot. */
  _writeHeaderCount(start, end, totalRows) {
    if (this.controls) {
      // When pagination controls exist, the count is displayed exclusively in the bottom bar;
      // keep the header slot empty to avoid duplicate count labels.
      const card = (this.tbody || this.controls)?.closest('.card');
      const slot = card && card.querySelector('.card-header .table-count');
      if (slot) slot.textContent = '';
      return false;
    }
    const card = (this.tbody || this.controls)?.closest('.card');
    const slot = card && card.querySelector('.card-header .table-count');
    if (!slot) return false;
    const { t } = GP;
    if (!totalRows) {
      slot.textContent = '';
      return true;
    }
    const countText = (start === 1 && end === totalRows)
      ? `${totalRows}`
      : `${start}-${end}`;
    slot.textContent = `${t('Showing')} ${countText} ${t('of')} ${totalRows}`;
    return true;
  }

  /* The bar is born empty (pagination_controls()) - every table it sits
     under has its rows in the page from the first byte, so there is nothing
     to wait on: paint at once. */
  _renderControls(totalRows, startIndex, endIndex) {
    if (!this.controls) {
      return;
    }
    this._paintControls(totalRows, startIndex, endIndex);
  }

  _paintControls(totalRows, startIndex, endIndex) {
    const previousSizeMenu = this.controls.querySelector('.gl-page-size-dropdown');
    const restoreSizeFocus = previousSizeMenu?.contains(document.activeElement)
      || previousSizeMenu?._portalMenu?.contains(document.activeElement);
    if (previousSizeMenu) GP.dropdown?.close(previousSizeMenu);

    const totalPages = this.totalPages;
    const start = totalRows > 0 ? startIndex + 1 : 0;
    const end = totalRows > 0 ? endIndex : 0;

    const perPageHtml = this.showPerPage
      ? `<div class="gl-pagination-size">${this._buildPageSizeDropdown()}</div>`
      : '';

    // Build numbered page buttons using component pagination classes
    const pageButtonsHtml = totalRows === 0 ? '' : this._buildPageButtons(totalPages);

    const prevDisabled = this.currentPage === 1 || totalRows === 0;
    const nextDisabled = this.currentPage >= totalPages || totalRows === 0;

    this._writeHeaderCount(start, end, totalRows);

    const infoText = totalRows > 0
      ? `${GP.t('Showing')} <strong>${start}</strong>-<strong>${end}</strong> ${GP.t('of')} <strong>${totalRows}</strong>`
      : `${GP.t('Showing')} <strong>0</strong>-<strong>0</strong> ${GP.t('of')} <strong>0</strong>`;

    this.controls.innerHTML =
      `<span class="gl-pagination-info">${infoText}</span>` +
      '<nav class="pagination" aria-label="Pagination">' +
        `<button class="btn btn-secondary btn-icon-only pagination-btn pagination-prev${prevDisabled ? ' disabled' : ''}" data-tippy-content="${GP.t('Previous page')}" data-disabled-reason="${GP.t('You are on the first page.')}" data-page="${this.currentPage - 1}" ${prevDisabled ? 'disabled' : ''} aria-label="${GP.t('Previous page')}">` +
          GP.iconSvg('chevron-lg-left', 'sm') +
        '</button>' +
        `<div class="pagination-pages">${pageButtonsHtml}</div>` +
        `<button class="btn btn-secondary btn-icon-only pagination-btn pagination-next${nextDisabled ? ' disabled' : ''}" data-tippy-content="${GP.t('Next page')}" data-disabled-reason="${GP.t('You are on the last page.')}" data-page="${this.currentPage + 1}" ${nextDisabled ? 'disabled' : ''} aria-label="${GP.t('Next page')}">` +
          GP.iconSvg('chevron-lg-right', 'sm') +
        '</button>' +
      '</nav>' +
      perPageHtml;

    const sizeMenu = this.controls.querySelector('.gl-page-size-dropdown .gl-dropdown-menu');
    if (sizeMenu) sizeMenu._clientPaginator = this;

    /* The controller initialises dropdowns on DOMContentLoaded and after an
       htmx swap. This markup arrives by innerHTML, after both, so it has to be
       introduced explicitly. */
    GP.dropdown.init(this.controls);
    if (restoreSizeFocus) {
      this.controls.querySelector('.gl-page-size-dropdown .gl-dropdown-toggle')?.focus();
    }

    /* When pageSize === 'all', hide the nav buttons but keep
       the info text and per-page dropdown visible so the user
       can switch back to a numeric page size. Keep arrows visible (disabled)
       when there is 1 page or 0 rows for UI consistency. */
    const hideNav = this.pageSize === 'all';
    const nav = this.controls.querySelector('nav.pagination');
    if (nav) nav.classList.toggle('d-none', hideNav);

    /* Never hide controls on empty state: keep "Showing 0-0 of 0" and per-page dropdown visible */
    this.controls.classList.remove('d-none');
  }

  _buildPageButtons(totalPages) {
    if (totalPages <= 7) {
      // Show all pages
      return Array.from({ length: totalPages }, (_, i) => i + 1)
        .map(p => this._pageBtn(p)).join('');
    }
    // Ellipsis logic: always show first, last, and window around current
    const pages = [];
    const current = this.currentPage;
    pages.push(1);
    if (current > 3) pages.push('...');
    const rangeStart = Math.max(2, current - 1);
    const rangeEnd = Math.min(totalPages - 1, current + 1);
    for (let p = rangeStart; p <= rangeEnd; p++) pages.push(p);
    if (current < totalPages - 2) pages.push('...');
    pages.push(totalPages);
    return pages.map(p => {
      if (p === '...') return '<span class="pagination-ellipsis">...</span>';
      return this._pageBtn(p);
    }).join('');
  }

  _pageBtn(page) {
    const active = page === this.currentPage ? ' pagination-current' : '';
    const aria = page === this.currentPage ? ' aria-current="page"' : '';
    return `<button class="pagination-page${active}" data-page="${page}"${aria}>${page}</button>`;
  }

  _buildPageSizeDropdown() {
    /* Choices strictly match Preferences > Rows per page: [25, 50, 100, 'all']
       "не більше ні меньше" - identical options across all tables in the app. */
    const options = [25, 50, 100, 'all'];
    const _getLabel = (val) => {
      if (val === 'all') {
        return GP.t('Show all');
      }
      const perPage = GP.t('per page');
      return `${val} ${perPage}`;
    };
    const currentLabel = _getLabel(this.pageSize);
    const checkSvg = GP.icons.get('check', 16, 'icon icon-sm gl-dropdown-item-check');
    const optionsHtml = options
      .map((value) => {
        const active = String(this.pageSize) === String(value) ? ' active' : '';
        const ariaSel = active ? ' aria-selected="true"' : '';
        const label = _getLabel(value);
        return `<li role="option"${ariaSel}><button type="button" class="gl-dropdown-item${active}" data-size="${value}">${checkSvg}<span class="gl-dropdown-item-content"><span class="gl-dropdown-item-title">${label}</span></span></button></li>`;
      })
      .join('');
    return (
      '<div class="gl-dropdown gl-page-size-dropdown" data-dropdown-portal>' +
        '<button type="button" class="gl-dropdown-toggle" aria-haspopup="listbox">' +
          `<span>${currentLabel}</span>` +
          // The registry's chevron, not a copy of it scaled to a 12-unit grid.
          GP.icons.get('chevron-down', 12, 'gl-dropdown-chevron') +
        '</button>' +
        `<ul class="gl-dropdown-menu" role="listbox">${optionsHtml}</ul>` +
      '</div>'
    );
  }

  /* Opening and closing a portaled menu is GP.dropdown.portal / .unportal -
     THE implementation, shared with every other dropdown that has to escape an
     `overflow: hidden` ancestor. What stood here was a second copy of it: ~60
     lines that moved the menu to <body>, measured the toggle, pinned the menu
     with `position: fixed`, chose up or down, and undid all of it on close. The
     copy is what carried the bug - a fixed menu pinned once, in an app whose
     content scrolls inside `.gl-page-content`, hangs in the middle of the table
     the moment the reader scrolls. */
}

/* One delegated handler for all page-size menus, including portaled ones.
   Per-instance document listeners also changed other tables and retained
   paginators after SPA navigation. The menu keeps its own owner when portaled. */
document.addEventListener('click', function (event) {
  const opt = event.target.closest('.gl-dropdown-item[data-size]');
  if (!opt) return;
  const paginator = opt.closest('.gl-dropdown-menu')?._clientPaginator;
  if (!paginator?.controls?.isConnected) return;
  const root = paginator.controls.querySelector('.gl-page-size-dropdown');
  // Close before rendering, or its portaled menu outlives the replaced controls.
  if (root) GP.dropdown?.close(root);
  paginator.changePageSize(opt.dataset.size);
});

/* ============================================
   TableFilter
   ============================================ */
class TableFilter {
  constructor(opts = {}) {
    this.input = document.querySelector(opts.inputSelector || '');
    this.tbody = document.querySelector(opts.tbodySelector || '');
    this.countEl = opts.countSelector ? document.querySelector(opts.countSelector) : null;
    this.dropdownFilters = opts.dropdownFilters || {};
    this.paginator = opts.paginator || null;
    if (this.paginator) this.paginator._tableFilter = this;
    this._rowFilter = typeof opts.rowFilter === 'function' ? opts.rowFilter : null;
    this._urlParams = typeof opts.urlParams === 'function' ? opts.urlParams : null;
    this._allRows = [];
    this._activeFilters = {};
    this._pendingSearch = false;
    this._debouncedApply = (window.GP?.debounce || function(fn, ms) { let t; return function() { clearTimeout(t); t = setTimeout(fn, ms); }; })(() => {
      if (!this._pendingSearch || !this._isCurrent()) return;
      // A held pagination control must survive until click. If the press is
      // canceled, the next tick applies the filter after :active is released.
      if (this.paginator?.controls?.querySelector('[data-page]:active')) this._debouncedApply();
      else this.apply();
    }, opts.debounceMs || 100);

    this._readRows();
    this._bindEvents();
    /* A dropdown pre-set from the address (?status=archived - a link that
       arrives filtered) filters on load too, not only a search. */
    const _preset = Object.values(this._activeFilters).some((v) => v && v !== 'all');
    if ((this.input && this.input.value) || _preset) {
      this.apply();
    }
  }

  _readRows() {
    if (!this.tbody) {
      this._allRows = [];
      return;
    }
    this._allRows = Array.from(this.tbody.querySelectorAll('tr[data-search]'));
  }

  _isCurrent() {
    // Detached inputs and the still-visible outgoing page must not change
    // the destination URL, whether a timer or a final change event fires.
    return this.input?.isConnected && this.tbody?.isConnected
      && !this.tbody.closest('#main-content.is-navigating');
  }

  _bindEvents() {
    if (this.input) {
      try {
        const p = new URLSearchParams(window.location.search);
        const urlQ = p.get('q');
        if (urlQ && !this.input.value) {
          this.input.value = urlQ;
        }
      } catch (_) {}

      this.input.addEventListener('input', () => {
        this._pendingSearch = true;
        this._debouncedApply();
      });
      // Commit the URL before Refresh reads it, without replacing a control
      // under the pointer. Rendering stays debounced or belongs to pagination.
      this.input.addEventListener('change', () => {
        if (this._pendingSearch && this._isCurrent()) this._syncUrl();
      });
    }

    Object.entries(this.dropdownFilters).forEach(([name, cfg]) => {
      const dropdown = document.querySelector(cfg.selector);
      if (!dropdown) {
        return;
      }
      this._activeFilters[name] = dropdown.value || 'all';
      dropdown.addEventListener('change', () => {
        this._activeFilters[name] = dropdown.value || 'all';
        /* Into the address, as the search is (?q=): a reload, a shared link
           and the period selector - which rebuilds its links from the live
           address - all keep the filter. The page renders the dropdown from
           the same parameter. */
        try {
          const url = new URL(window.location.href);
          if (dropdown.value && dropdown.value !== 'all') url.searchParams.set(name, dropdown.value);
          else url.searchParams.delete(name);
          window.history.replaceState(window.history.state, '', url.toString());
        } catch (_) { /* no history API */ }
        this.apply();
      });
    });
  }

  resync() {
    this._readRows();
    this.apply();
    return this;
  }

  _rowMatchesSearch(row, query) {
    if (!query) {
      return true;
    }
    const haystack = (row.dataset.search || row.textContent || '').toLowerCase();
    return haystack.includes(query);
  }

  _rowMatchesDropdowns(row) {
    return Object.entries(this.dropdownFilters).every(([name, cfg]) => {
      const expected = this._activeFilters[name] || 'all';
      if (!expected || expected === 'all') {
        return true;
      }
      const attr = cfg.attribute || `data-${name}`;
      return row.getAttribute(attr) === expected;
    });
  }

  _syncUrl() {
    const rawQuery = (this.input?.value || '').trim();
    try {
      const url = new URL(window.location.href);
      if (rawQuery) {
        url.searchParams.set('q', rawQuery);
      } else {
        url.searchParams.delete('q');
      }
      if (this._urlParams) {
        Object.entries(this._urlParams()).forEach(([name, value]) => {
          if (value && value !== 'all') url.searchParams.set(name, value);
          else url.searchParams.delete(name);
        });
      }
      window.history.replaceState(window.history.state, '', url.toString());
    } catch (_) {}
    return rawQuery;
  }

  apply() {
    if (!this.tbody?.isConnected) return [];
    // An explicit filter application consumes its outstanding typing update.
    this._pendingSearch = false;
    const query = this._syncUrl().toLowerCase();

    const filtered = this._allRows.filter((row) => {
      return this._rowMatchesSearch(row, query) && this._rowMatchesDropdowns(row)
        && (!this._rowFilter || this._rowFilter(row));
    });

    if (this.paginator && typeof this.paginator.setFilteredRows === 'function') {
      this.paginator.setFilteredRows(filtered);
    } else {
      this._allRows.forEach((row) => {
        row.classList.add('d-none');
      });
      filtered.forEach((row) => {
        row.classList.remove('d-none');
      });
    }

    if (this.countEl) {
      this.countEl.textContent = String(filtered.length);
    }

    // Show/hide empty state message when filter yields no results
    this._updateEmptyState(filtered.length, this._allRows.length);

    return filtered;
  }

  _updateEmptyState(visibleCount, totalCount) {
    GP.tableFilteredToNothing(this.tbody, visibleCount, totalCount);
  }
}

/* ============================================
   Filtered to nothing
   ============================================ */
/**
 * Say so when a filter hides every row of a table.
 *
 * `TableFilter` grew this for itself, so a table filtered through anything else
 * - ClientPaginator, or a switch that toggles rows directly - showed a header
 * row over blank space and a count that read "Showing 0 of 1". Same markup as a
 * server-rendered empty table, so the two states look like one thing.
 *
 * @param {HTMLElement} tbody   the tbody being filtered
 * @param {number} visibleCount rows the filter left
 * @param {number} totalCount   rows there are
 */
GP.tableFilteredToNothing = function (tbody, visibleCount, totalCount) {
  if (!tbody) return;
  const table = tbody.closest('table');
  const container = (table && table.parentElement) || tbody.parentElement;
  if (!container) return;
  const card = container.closest('.card-body') || container.parentElement;
  const pagination = card ? card.querySelector('.pagination-controls') : null;
  let emptyEl = container.querySelector('.table-filter-empty');

  if (visibleCount === 0 && totalCount > 0) {
    if (!emptyEl) {
      /* THE empty state - GP.emptyStateHtml, the box every empty table shows. */
      container.insertAdjacentHTML('beforeend', GP.emptyStateHtml(GP.t('No results match your filter'), 'search-sm'));
      emptyEl = container.lastElementChild;
      emptyEl.classList.add('table-filter-empty');
      emptyEl.setAttribute('role', 'status');
      emptyEl.setAttribute('aria-live', 'polite');
    }
    emptyEl.classList.remove('d-none');
    if (table) table.classList.add('d-none');
    if (pagination) pagination.classList.remove('d-none');
  } else {
    if (emptyEl) emptyEl.classList.add('d-none');
    if (table) table.classList.remove('d-none');
    if (pagination) pagination.classList.remove('d-none');
  }
};

/* ============================================
   FilterPills
   ============================================ */
class FilterPills {
  constructor(containerSelector, attribute, onFilter) {
    this.container = document.querySelector(containerSelector || '');
    this.attribute = attribute || 'data-value';
    this.onFilter = typeof onFilter === 'function' ? onFilter : null;
    this.activeValue = 'all';

    // The control is drawn as a tab strip (the shape the course sub-navigation
    // uses), because picking one of several views of one table is switching,
    // not filtering.
    this.itemSelector = '.tab-btn';
    if (this.container) {
      const initial = this.container.querySelector('.tab-btn.active');
      if (initial) {
        this.activeValue =
          initial.dataset.value ||
          initial.dataset.role ||
          initial.getAttribute(this.attribute) ||
          'all';
      }
      this._setActiveState(initial);
      this.container.addEventListener('click', (event) => {
        const pill = event.target.closest(this.itemSelector);
        if (!pill || !this.container.contains(pill)) {
          return;
        }
        this._setActiveState(pill);
        this.activeValue =
          pill.dataset.value ||
          pill.dataset.role ||
          pill.getAttribute(this.attribute) ||
          'all';

        if (this.onFilter) {
          this.onFilter(this.activeValue);
        }
      });
    }
  }

  _setActiveState(activePill) {
    this.container.querySelectorAll(this.itemSelector).forEach((node) => {
      const isActive = node === activePill;
      node.classList.toggle('active', isActive);
      // A tab announces itself with aria-selected, a toggle button with
      // aria-pressed. Setting the wrong one leaves a screen reader saying
      // "not pressed" about a tab that is plainly the selected one.
      if (node.getAttribute('role') === 'tab') {
        node.setAttribute('aria-selected', String(isActive));
      } else {
        node.setAttribute('aria-pressed', String(isActive));
      }
    });
  }

  setActive(value) {
    if (!this.container) return;
    const target = Array.from(this.container.querySelectorAll(this.itemSelector)).find(
      (node) =>
        (node.dataset.value || node.dataset.role || node.getAttribute(this.attribute)) === value
    );
    if (target) {
      this._setActiveState(target);
      this.activeValue = value;
    }
  }
}

/* ============================================
   PollingController
   ============================================ */
class PollingController {
  constructor(urlOrFn, opts = {}) {
    this._urlOrFn = urlOrFn;
    this._interval = opts.interval || 3000;
    this._activeInterval = opts.activeInterval || null;
    this._idleInterval = opts.idleInterval || null;
    this._maxErrors = opts.maxErrors || 10;
    this._onUpdate = opts.onUpdate || null;
    this._onComplete = opts.onComplete || null;
    this._onError = opts.onError || null;
    this._isComplete = opts.isComplete || null;
    this._isActive = opts.isActive || null;
    this._pauseWhenHidden = opts.pauseWhenHidden !== false;
    this._errorCount = 0;
    this._timerId = null;
    this._stopped = true;
    this._inFlight = false;
  }

  start() {
    if (!this._stopped) {
      console.warn('PollingController.start() called while already running - ignoring.');
      return this;
    }

    this._stopped = false;
    this._errorCount = 0;
    this._schedule(0);
    return this;
  }

  stop() {
    this._stopped = true;
    this._inFlight = false;
    if (this._timerId) {
      clearTimeout(this._timerId);
      this._timerId = null;
    }
    return this;
  }

  isRunning() {
    return !this._stopped;
  }

  setInterval(ms) {
    const numeric = Number(ms);
    if (!Number.isFinite(numeric) || numeric <= 0) {
      return;
    }
    this._interval = numeric;
  }

  _schedule(delayMs) {
    if (this._stopped) {
      return;
    }
    if (this._timerId) {
      clearTimeout(this._timerId);
    }
    this._timerId = setTimeout(() => this._tick(), Math.max(0, delayMs));
  }

  async _fetchData() {
    if (typeof this._urlOrFn === 'function') {
      return this._urlOrFn();
    }

    // Delegate to apiCall for consistent CSRF, timeout, and error semantics
    return window.GP.apiCall(this._urlOrFn, 'GET', null, { maxRetries: 0 });
  }

  async _tick() {
    if (this._stopped || this._inFlight) {
      return;
    }

    if (this._pauseWhenHidden && document.hidden) {
      this._schedule(this._interval);
      return;
    }

    this._inFlight = true;

    try {
      const data = await this._fetchData();
      this._errorCount = 0;

      if (this._onUpdate) {
        this._onUpdate(data);
      }

      if (this._activeInterval && this._idleInterval && this._isActive) {
        const active = this._isActive(data);
        this._interval = active ? this._activeInterval : this._idleInterval;
      }

      if (this._isComplete && this._isComplete(data)) {
        this.stop();
        if (this._onComplete) {
          this._onComplete(data);
        }
        return;
      }
    } catch (error) {
      this._errorCount += 1;
      if (this._onError) {
        this._onError(error, this._errorCount);
      }
      if (this._errorCount >= this._maxErrors) {
        this.stop();
        return;
      }
    } finally {
      this._inFlight = false;
    }

    this._schedule(this._interval);
  }
}

/* ============================================
   submitModalForm
   ============================================ */
// A reopened dialog starts a new interaction, even while its previous write
// is pending. Retire only feedback owned by this form-submit component.
document.addEventListener('gp:modal-open', function (event) {
  const modal = event.detail?.modal;
  if (!modal) return;
  modal.querySelectorAll('[data-modal-submit]').forEach(function (btn) {
    btn._gpModalSubmission?.releaseFields();
    delete btn._gpModalSubmission;
    GP.clearButtonOutcome(btn);
    GP.clearButtonLoadingChrome(btn);
    setButtonLoading(btn, false);
  });
});

async function submitModalForm(event, opts = {}) {
  if (event?.preventDefault) {
    event.preventDefault();
  }

  const form = event?.target?.closest ? event.target.closest('form') : event?.target;
  if (!form) {
    throw new Error('Form element not found');
  }

  const submitBtn = opts.btnSelector
    ? document.querySelector(opts.btnSelector)
    : form.querySelector('button[type="submit"]');
  const modal = opts.modalId ? document.getElementById(opts.modalId) : null;
  const version = modal?._gpOpenVersion;
  const current = () => form.isConnected && (!modal || (
    document.getElementById(opts.modalId) === modal && modal._gpOpenVersion === version
    && modal.classList.contains('active') && !modal.classList.contains('closing')
  ));

  const defaultLock = `form:${form.id || opts.url || 'unknown'}${modal ? ':' + version : ''}`;
  const lockKey = opts.lockKey || form.dataset.lockKey || defaultLock;

  return GP.withUiLock(lockKey, async () => {
    const fields = [];
    const submission = { releaseFields() {
      fields.splice(0).forEach(field => {
        if (field.dataset.archivedLocked !== '1' && field.dataset.processLocked !== '1') {
          field.disabled = false;
        }
      });
    } };
    if (submitBtn) {
      if (modal) submitBtn.dataset.modalSubmit = '1';
      submitBtn._gpModalSubmission = submission;
      setButtonLoading(submitBtn, true);
    }

    try {
      const body = typeof opts.getData === 'function'
        ? opts.getData(form)
        : _formDataToJSON(form);

      // Capture the payload before disabling fields (FormData skips disabled
      // controls). Keep it stable while waiting, with Cancel and Close available.
      form.querySelectorAll('input, select, textarea, .gl-form-dropdown button').forEach(field => {
        if (!field.disabled) {
          fields.push(field);
          field.disabled = true;
        }
      });

      const result = await apiCall(
        opts.url,
        opts.method || 'POST',
        body,
        {
          timeoutMs: opts.timeoutMs || 20000,
          maxRetries: typeof opts.maxRetries === 'number' ? opts.maxRetries : 1,
          allowRetryUnsafe: opts.allowRetryUnsafe === true,
        }
      );
      // The server write may finish after closing, reopening, or navigating.
      // Its old callback must not read or replace the next interaction's form.
      if (!current()) return result;

      const successType = opts.successType || 'success';
      const successMsg = opts.successMsg || GP.t('Saved!');

      flashToast(successMsg, successType);

      if (opts.modalId) {
        clearModalDirty(opts.modalId);
        closeModal(opts.modalId);
      }

      if (typeof opts.onSuccess === 'function') {
        opts.onSuccess(result, form);
      }

      if (opts.reload !== false) {
        reloadKeepScroll();
      }

      return result;
    } catch (error) {
      if (!current() || error?.superseded) return null;
      if (error && error.code === 'LOCKED') {
        return null;
      }
      if (error && error.status === 409) {
        const conflictMsg = error.message || '';
        if (conflictMsg && !conflictMsg.includes('modified by another')) {
          showToast(conflictMsg, 'warning');
        } else {
          showToast(
            GP.t('This record was modified by another user. Please reload the page and try again.'),
            'warning'
          );
        }
      } else {
        showToast(error.message || GP.t('An error occurred'), 'danger');
      }
      if (typeof opts.onError === 'function') {
        opts.onError(error, form);
      }
      return null;
    } finally {
      submission.releaseFields();
      if (submitBtn && submitBtn._gpModalSubmission === submission) {
        delete submitBtn._gpModalSubmission;
        setButtonLoading(submitBtn, false);
      }
    }
  });
}

function _formDataToJSON(form) {
  const formData = new FormData(form);
  const data = {};
  const keys = Array.from(new Set(Array.from(formData.keys())));
  const escapeCss = (value) => {
    if (window.CSS && typeof window.CSS.escape === 'function') {
      return window.CSS.escape(value);
    }
    return String(value).replace(/([^\w-])/g, '\\$1');
  };

  keys.forEach((key) => {
    if (key === 'csrf_token') {
      return;
    }

    const values = formData.getAll(key);
    const fields = form.querySelectorAll(`[name="${escapeCss(key)}"]`);

    if (fields.length === 1 && fields[0].type === 'checkbox') {
      data[key] = fields[0].checked;
      return;
    }

    if (fields.length > 1 && Array.from(fields).every((field) => field.type === 'checkbox')) {
      data[key] = Array.from(fields)
        .filter((field) => field.checked)
        .map((field) => field.value || true);
      return;
    }

    if (values.length > 1) {
      data[key] = values;
      return;
    }

    data[key] = values[0];
  });

  return data;
}



/* ============================================
   Dangerous Action Confirmation
   ============================================ */
/* The app's canonical "are you sure?" for a destructive action.
 *
 * Runs on the shared, themed dialog (GP.confirmDialog) instead of the browser's
 * `window.confirm` / `window.prompt`: those cannot be themed, ignore dark mode,
 * carry no danger accent and read like the page broke - and they sat beside the
 * app's own modals doing the same job.
 *
 * The signature is unchanged. Callers pass an `onConfirm` CALLBACK, so going
 * from a blocking dialog to a promise ripples nowhere: the callback simply runs
 * later. What DID change is the return value - it is now a Promise, so a caller
 * that used the boolean synchronously must await it. The one such caller (the
 * object form below) is handled explicitly.
 *
 * Two confirmations collapse into one: the browser could only ask a yes/no
 * question, so a permanent delete needed a second dialog to feel safe. The real
 * dialog states the consequence once and gates the button on typing the name -
 * the safeguard the second click only pretended to be.
 */
async function confirmDangerousAction(entityName, onConfirm, opts = {}) {
  /* No local `window.confirm` fallback: GP.confirmDialog carries one itself
     (core/19-confirm-dialog.js), so a second copy here was one more place a raw, unthemed
     browser dialog could reach a user. */
  if (entityName && typeof entityName === 'object' && typeof onConfirm !== 'function') {
    const dialog = entityName;
    return GP.confirmDialog({
      title: dialog.title || GP.t('Are you sure?'),
      message: dialog.message || dialog.confirmText || GP.t('Are you sure you want to continue?'),
      confirmText: dialog.okText || GP.t('Confirm'),
      variant: dialog.variant || 'danger',
    });
  }

  const label = entityName || GP.t('this item');
  // Parameterised keys, not interpolated template literals: a string built with
  // the label already inside it can never match a catalog entry, so these
  // dialogs stayed English no matter the UI language. GP.t substitutes {name}.
  const primaryMessage = opts.confirmText
    || GP.t('Are you sure you want to delete {label}?\n\nThis action cannot be undone.', { label });
  const expected = opts.requireTyping ? String(opts.expectedValue || label) : '';

  const ok = await GP.confirmDialog({
    title: opts.title || GP.t('Are you sure?'),
    message: primaryMessage,
    confirmText: opts.okText || GP.t('Confirm'),
    variant: 'danger',
    requireTyping: !opts.singleConfirm && !!opts.requireTyping,
    expectedValue: expected,
    typingPrompt: opts.typingPrompt,
  });
  if (!ok) return false;

  if (typeof onConfirm === 'function') {
    return onConfirm();
  }
  return true;
}




/* ============================================
   Auto-init data components
   ============================================ */
function _autoInitComponents(root = document) {
  root.querySelectorAll('[data-paginator]').forEach((el) => {
    const id = el.dataset.paginator;
    if (!id) {
      return;
    }

    if (window._paginators && window._paginators[id]) {
      const existing = window._paginators[id];
      // If the cached paginator's elements are detached from DOM, clean it up so we can recreate it
      const tbodyOk = !existing.tbody || document.body.contains(existing.tbody);
      const controlsOk = !existing.controls || document.body.contains(existing.controls);
      if (tbodyOk && controlsOk) {
        return;
      }
      delete window._paginators[id];
    }

    const paginator = new ClientPaginator({
      id,
      tbodySelector: el.dataset.tbody || `#${id} tbody`,
      controlsSelector: el.dataset.controls || `#${id}PaginationControls`,
      pageSize: parseInt(el.dataset.pageSize, 10) || 50,
      showPerPage: el.dataset.showPerPage !== 'false',
      // Persist per-page selection across reloads.  Scope by pathname so
      // the same table id on different pages gets its own preference.
      storageKey: el.dataset.storageKey || (location.pathname + '#' + id),
    }).register(id);

    paginator.render();
  });

  root.querySelectorAll('input[data-filter]').forEach((input) => {
    if (input.dataset.filterInitialized === '1') {
      return;
    }

    const tableId = input.dataset.filter;
    const paginator = window._paginators && window._paginators[tableId];

    // Read dropdown filters from data-filter-dropdowns attribute if present
    // Format: 'status:#statusFilter@data-status,priority:#priorityFilter@data-priority'
    const dropdownFilters = {};
    const dropdownsAttr = input.dataset.filterDropdowns;
    if (dropdownsAttr) {
      dropdownsAttr.split(',').forEach(item => {
        const [name, rest] = item.split(':');
        if (name && rest) {
          const [selector, attr] = rest.split('@');
          if (selector && attr) {
            dropdownFilters[name] = { selector, attribute: attr };
          }
        }
      });
    }

    // Store instance for potential external reuse/debugging.
    input._tableFilter = new TableFilter({
      inputSelector: `input[data-filter="${tableId}"]`,
      tbodySelector: `#${tableId} tbody`,
      countSelector: input.dataset.filterCount || null,
      dropdownFilters,
      paginator,
    });

    input.dataset.filterInitialized = '1';
  });
}

GP.initDataComponents = _autoInitComponents;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => _autoInitComponents(document));
} else {
  _autoInitComponents(document);
}

document.body.addEventListener('htmx:afterSwap', (event) => {
  _autoInitComponents(event.target || document);
});

/* ============================================
   Exports
   ============================================ */

/* ============================================
   Course Lifecycle Actions (archive / activate / delete)
   ============================================ */
const COURSE_LIFECYCLE_LOCKS = ['sync', 'import', 'run_checks'];

function courseProcessScope(courseId) {
  const id = String(courseId || '').trim();
  return id ? `course:${id}` : '';
}

function guardCourseLifecycle(courseId) {
  if (!courseId || typeof GP.guardProcessAction !== 'function') return true;
  return GP.guardProcessAction(COURSE_LIFECYCLE_LOCKS, { scope: courseProcessScope(courseId) });
}

/* One lifecycle action for a course: confirm, lock, call, toast, unlock.
 * Archive, activate and permanent-delete each wrote these eighteen lines out -
 * same UI lock, same `err.code === 'LOCKED'` swallow, same badge refresh, same
 * finally-unlock - so a fix to one had to be remembered twice more.
 */
/* The course's term, from the control that asked or the row / card it sits
 * in (`data-course-period`); failing that, from any element of that course on
 * the page - a card's menu can be rendered outside the card. "Archive ZSI?"
 * names every year's ZSI; the dialog has to name the one this is.
 */
function _coursePeriodOf(courseId, btn) {
  let host = btn && btn.closest ? btn.closest('[data-course-period]') : null;
  if (!host && courseId && window.CSS && typeof CSS.escape === 'function') {
    host = document.querySelector('[data-course-period][data-course-id="' + CSS.escape(String(courseId)) + '"]');
  }
  return host ? host.getAttribute('data-course-period') || '' : '';
}

function courseLifecycle(courseId, btn, opts, spec) {
  const { onSuccess, onError, skipBeforeunload, confirmText } = opts || {};
  if (!guardCourseLifecycle(courseId)) return;
  const period = _coursePeriodOf(courseId, btn);
  const question = confirmText || spec.confirm;
  confirmDangerousAction(spec.subject, async () => {
    try {
      await GP.withUiLock(`${spec.lock}:${courseId}`, async () => {
        if (btn) setButtonLoading(btn, true);
        await GP.apiCall(spec.url, spec.method || 'POST');
        if (typeof GP.refreshSidebarBadges === 'function') GP.refreshSidebarBadges();
        GP.flashToast?.(spec.done, 'success');
        if (skipBeforeunload && GP.skipBeforeunload) GP.skipBeforeunload();
        if (onSuccess) onSuccess();
      });
    } catch (err) {
      if (err.code === 'LOCKED') return;
      if (onError && onError(err) === true) return;
      GP.showToast?.(err.message || spec.failed, 'danger');
    } finally {
      if (btn) setButtonLoading(btn, false);
    }
  }, {
    confirmText: period ? question + '\n\n' + GP.t('Period') + ': ' + period : question,
    ...spec.dialog,
  });
}

const courseActions = {
  archive(courseId, btn, opts) {
    courseLifecycle(courseId, btn, opts, {
      subject: GP.t('archive this course'),
      lock: 'archiveCourse',
      url: `/api/v1/courses/${courseId}/archive`,
      done: GP.t('Course archived'),
      failed: GP.t('Failed to archive course'),
      confirm: GP.t('Archive this course? All running processes (sync, import) will be cancelled.'),
      dialog: { singleConfirm: true },
    });
  },
  activate(courseId, btn, opts) {
    courseLifecycle(courseId, btn, opts, {
      subject: GP.t('re-activate this course'),
      lock: 'activateCourse',
      url: `/api/v1/courses/${courseId}/activate`,
      done: GP.t('Course activated'),
      failed: GP.t('Failed to activate course'),
      confirm: GP.t('Re-activate this course?'),
      dialog: { singleConfirm: true },
    });
  },
  deletePermanent(courseId, courseCode, btn, opts) {
    courseLifecycle(courseId, btn, opts, {
      subject: courseCode,
      lock: 'deleteCourse',
      method: 'DELETE',
      url: `/api/v1/courses/${courseId}/permanent`,
      done: GP.t('Course permanently deleted'),
      failed: GP.t('Failed to delete course'),
      confirm: `${GP.t('Permanently delete course')} ${courseCode}? `
        + GP.t('This will delete ALL groups, students, and data. This cannot be undone!'),
      dialog: {
        requireTyping: true,
        typingPrompt: `${GP.t('Type')} "${courseCode}" ${GP.t('to confirm deletion:')}`,
        expectedValue: courseCode,
      },
    });
  },
};

/* ============================================
   Module exports
   ============================================ */
GP.ClientPaginator = ClientPaginator;
GP.courseActions = courseActions;
GP.TableFilter = TableFilter;
GP.FilterPills = FilterPills;
GP.PollingController = PollingController;
GP.submitModalForm = submitModalForm;
GP.confirmDangerousAction = confirmDangerousAction;

window.ClientPaginator = ClientPaginator;
window.TableFilter = TableFilter;
window.FilterPills = FilterPills;
window.PollingController = PollingController;
window.submitModalForm = submitModalForm;
window.confirmDangerousAction = confirmDangerousAction;

})();
