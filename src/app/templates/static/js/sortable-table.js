/**
 * SortableTable - Universal client-side table sorting component.
 *
 * Auto-initializes on any <table data-sortable>.
 * Each sortable column needs: <th class="sortable-header" data-sort-key="field">
 * Optional: data-sort-type on <th>: "string" (default), "number", "date"
 * Optional: data-sort-value on <td> for custom sort values
 * Optional: data-sort-default="asc|desc" on <th> to set initial sort
 *
 * Works with ClientPaginator - after sorting, calls paginator.resync().
 *
 * API:
 *   SortableTable.init()                 - re-scan and init all [data-sortable] tables
 *   SortableTable.initTable(tableEl)     - init a single table
 *   new SortableTable(tableEl)           - manual constructor
 *   instance.sort(key, dir)              - programmatic sort
 *   instance.refresh()                   - re-read rows (after dynamic content change)
 */
;(function () {
  'use strict';

  /* -- Registry of initialized tables -- */
  const _instances = new WeakMap();

  /* -- Persisted state (per pathname + table id) --
     We only persist sort selections for tables that have an id, so we can
     reliably target the same table on the next visit.  Tables without an
     id render their default sort each time (unchanged legacy behaviour). */
  const STORAGE_KEY_PREFIX = 'gp_table_sort_v1:';

  /** Build a stable identifier for a table even when it has no `id`.
   *  Falls back to a hash of header column keys + class list + index
   *  among sibling [data-sortable] tables, so the same table on the
   *  same URL gets the same key on every reload. */
  function _syntheticId(table) {
    const ths = Array.from(table.querySelectorAll('thead th[data-sort-key]'))
      .map((th) => th.getAttribute('data-sort-key'))
      .join(',');
    const classes = (table.className || '').trim().split(/\s+/).sort().join('.');
    const all = Array.from(document.querySelectorAll('table[data-sortable]'));
    const idx = all.indexOf(table);
    return 'auto-' + idx + ':' + classes + ':' + ths;
  }

  function _storageKey(table) {
    if (!table) return null;
    const ident = table.id || _syntheticId(table);
    if (!ident) return null;
    return STORAGE_KEY_PREFIX + location.pathname + '#' + ident;
  }

  function _loadSortState(table) {
    // 1. URL search params take precedence (enables bookmarking, sharing, and consistent reload)
    try {
      const params = new URLSearchParams(window.location.search);
      const urlSort = params.get('sort');
      const urlDir = params.get('dir');
      if (urlSort && (urlDir === 'asc' || urlDir === 'desc')) {
        const th = table.querySelector('th[data-sort-key="' + urlSort + '"]');
        if (th) {
          return { key: urlSort, dir: urlDir };
        }
      }
    } catch (_) { /* ignore */ }

    // 2. Fall back to localStorage per page & table
    const key = _storageKey(table);
    if (!key) return null;
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (parsed && parsed.key && (parsed.dir === 'asc' || parsed.dir === 'desc')) {
        return parsed;
      }
    } catch (_) { /* ignore */ }
    return null;
  }

  function _saveSortState(table, sortKey, sortDir) {
    const key = _storageKey(table);
    if (!key || !sortKey) return;
    try {
      localStorage.setItem(key, JSON.stringify({ key: sortKey, dir: sortDir }));
    } catch (_) { /* ignore */ }
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('sort', sortKey);
      url.searchParams.set('dir', sortDir);
      window.history.replaceState(null, '', url.toString());
    } catch (_) { /* ignore */ }
  }

  /* -- Comparators by type -- */
  function compareString(a, b) {
    if (a == null && b == null) return 0;
    if (a == null) return 1;
    if (b == null) return -1;
    return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
  }

  function compareNumber(a, b) {
    const na = parseFloat(a), nb = parseFloat(b);
    if (isNaN(na) && isNaN(nb)) return 0;
    if (isNaN(na)) return 1;
    if (isNaN(nb)) return -1;
    return na - nb;
  }

  function compareDate(a, b) {
    const da = a ? new Date(a).getTime() : NaN;
    const db = b ? new Date(b).getTime() : NaN;
    if (isNaN(da) && isNaN(db)) return 0;
    if (isNaN(da)) return 1;
    if (isNaN(db)) return -1;
    return da - db;
  }

  const COMPARATORS = {
    string: compareString,
    number: compareNumber,
    date:   compareDate
  };

  /* -- SortableTable constructor -- */
  function SortableTable(table) {
    if (!(table instanceof HTMLTableElement)) return;
    if (_instances.has(table)) return _instances.get(table);

    this.table = table;
    this.sortKey = null;
    this.sortDir = null;
    this._headers = [];
    this._colIndex = {};

    this._setup();
    _instances.set(table, this);
  }

  SortableTable.prototype._setup = function () {
    const self = this;
    const ths = this.table.querySelectorAll('th.sortable-header[data-sort-key]');
    const allThs = this.table.querySelectorAll('thead th');

    // Build column index map: data-sort-key -> column index
    this._headers = [];
    this._colIndex = {};
    const thArray = Array.from(allThs);

    for (let i = 0; i < thArray.length; i++) {
      const key = thArray[i].getAttribute('data-sort-key');
      if (key) {
        this._colIndex[key] = i;
      }
    }

    // Ensure each sortable header has the sort-arrow and bind click
    for (const th of ths) {
      this._headers.push(th);
      this._ensureSortArrow(th);

      let touchStartX = 0;
      let touchStartY = 0;
      let isSwiping = false;

      th.addEventListener('touchstart', (e) => {
        if (e.touches && e.touches.length > 0) {
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
          isSwiping = false;
        }
      }, { passive: true });

      th.addEventListener('touchmove', (e) => {
        if (e.touches && e.touches.length > 0) {
          const dx = Math.abs(e.touches[0].clientX - touchStartX);
          const dy = Math.abs(e.touches[0].clientY - touchStartY);
          if (dx > 8 || dy > 8) {
            isSwiping = true;
          }
        }
      }, { passive: true });

      th.addEventListener('touchcancel', () => {
        isSwiping = false;
      }, { passive: true });

      th.addEventListener('click', (e) => {
        if (isSwiping) {
          isSwiping = false;
          return;
        }
        e.preventDefault();
        const key = th.getAttribute('data-sort-key');
        const switching = self.sortKey !== key;
        if (!switching) {
          self.sortDir = self.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          self.sortKey = key;
          // Default to descending for number/date columns (users expect
          // highest/newest first) and ascending for text columns.
          const type = th.getAttribute('data-sort-type') || 'string';
          self.sortDir = (type === 'number' || type === 'date') ? 'desc' : 'asc';
        }

        /* One click, one visible result.
           Switching to a new column very often produces the order already on
           screen - sorting courses by name lands them in the same sequence as
           by code - so the rows sat still and only the arrow moved. That reads
           as "the first click just focused it and I have to click again". When
           the new column's default direction changes nothing, flip it, so the
           first click always does something you can see. Only on a column
           SWITCH: an explicit second click on the same header must still be
           free to return the table to the order it had. */
        const orderBefore = switching ? self._rowOrder() : null;
        self._doSort();
        if (switching && self._rowOrder() === orderBefore) {
          self.sortDir = self.sortDir === 'asc' ? 'desc' : 'asc';
          self._doSort();
        }

        self._updateUI();
        self._syncPaginator();
        _saveSortState(self.table, self.sortKey, self.sortDir);
      });
    }

    // Apply default sort if specified
    this._applyDefaultSort();
  };

  SortableTable.prototype._ensureSortArrow = function (th) {
    // If this header already has a .sort-arrow, skip
    if (th.querySelector('.sort-arrow')) return;

    // Wrap content in .sort-link if not already
    let sortLink = th.querySelector('.sort-link');
    if (!sortLink) {
      sortLink = document.createElement('span');
      sortLink.className = 'sort-link';
      // Move all existing children into sortLink
      while (th.firstChild) {
        sortLink.appendChild(th.firstChild);
      }
      th.appendChild(sortLink);
    }

    // Add the sort arrow slot - tables.css draws GlTable's ↑ / ↓ in it
    const arrow = document.createElement('span');
    arrow.className = 'sort-arrow';
    arrow.setAttribute('data-sort-arrow', th.getAttribute('data-sort-key'));
    arrow.setAttribute('aria-hidden', 'true');
    sortLink.appendChild(arrow);
  };

  SortableTable.prototype._applyDefaultSort = function () {
    // Saved user sort selection (per pathname + table id) wins over the
    // template-defined default - it represents the user's most recent
    // intent and would otherwise be silently re-overridden on every load.
    const saved = _loadSortState(this.table);
    if (saved) {
      const th = this.table.querySelector('th[data-sort-key="' + saved.key + '"]');
      if (th) {
        this.sortKey = saved.key;
        this.sortDir = saved.dir;
        this._doSort();
        this._updateUI();
        // ClientPaginator may attach AFTER SortableTable.init runs (page
        // scripts typically wire it on DOMContentLoaded too). If already attached,
        // sync immediately to prevent row flash; otherwise defer.
        const tbody = this.table.tBodies[0];
        if (tbody && tbody._clientPaginator) {
          this._syncPaginator();
        } else {
          const self = this;
          setTimeout(function () { self._syncPaginator(); }, 0);
        }
        return;
      }
    }

    // Find a header with data-sort-default or class 'sorted'
    for (const th of this._headers) {
      const def = th.getAttribute('data-sort-default');
      if (def) {
        this.sortKey = th.getAttribute('data-sort-key');
        this.sortDir = def === 'desc' ? 'desc' : 'asc';
        this._doSort();
        this._updateUI();
        const tbody = this.table.tBodies[0];
        if (tbody && tbody._clientPaginator) {
          this._syncPaginator();
        }
        return;
      }
      if (th.classList.contains('sorted')) {
        this.sortKey = th.getAttribute('data-sort-key');
        const arrow = th.querySelector('.sort-arrow');
        this.sortDir = arrow && arrow.classList.contains('desc') ? 'desc' : 'asc';
        this._doSort();
        this._updateUI();
        const tbody = this.table.tBodies[0];
        if (tbody && tbody._clientPaginator) {
          this._syncPaginator();
        }
        return;
      }
    }
  };

  SortableTable.prototype._getRows = function () {
    const tbody = this.table.tBodies[0];
    if (!tbody) return [];
    return Array.from(tbody.rows).filter(function (row) {
      return !row.classList.contains('table-empty-row') &&
             !row.classList.contains('tree-row-child') &&
             row.cells.length > 1;
    });
  };

  SortableTable.prototype._getCellValue = function (row, key) {
    const colIdx = this._colIndex[key];
    if (colIdx === undefined || colIdx >= row.cells.length) return '';
    const cell = row.cells[colIdx];

    // data-sort-value takes priority
    const sv = cell.getAttribute('data-sort-value');
    if (sv !== null) return sv;

    // Extract text content, ignoring icons/badges decorators
    return (cell.textContent || '').trim();
  };

  /**
   * Collect "row groups": each data row + any companion rows that follow it
   * (teaching-notes, error banners, etc. - rows with cells.length <= 1).
   */
  SortableTable.prototype._getRowGroups = function () {
    const tbody = this.table.tBodies[0];
    if (!tbody) return [];
    const all = Array.from(tbody.rows);
    const groups = [];
    let current = null;

    for (let i = 0; i < all.length; i++) {
      const row = all[i];
      const isData = !row.classList.contains('table-empty-row') &&
                     !row.classList.contains('tree-row-child') &&
                     row.cells.length > 1;
      if (isData) {
        current = { primary: row, companions: [] };
        groups.push(current);
      } else if (current && !row.classList.contains('table-empty-row')) {
        current.companions.push(row);
      }
      /* orphan companion rows before the first data row are ignored */
    }
    return groups;
  };

  SortableTable.prototype._doSort = function () {
    const self = this;
    const groups = this._getRowGroups();
    if (!groups.length || !this.sortKey) return;

    const key = this.sortKey;
    const th = this.table.querySelector('th[data-sort-key="' + key + '"]');
    const sortType = (th && th.getAttribute('data-sort-type')) || 'string';
    const cmp = COMPARATORS[sortType] || COMPARATORS.string;
    const dir = this.sortDir === 'desc' ? -1 : 1;

    groups.sort(function (a, b) {
      const va = self._getCellValue(a.primary, key);
      const vb = self._getCellValue(b.primary, key);

      // Always push empty/null/dash values to end regardless of direction
      const sa = va == null ? '' : String(va).trim();
      const sb = vb == null ? '' : String(vb).trim();
      let aEmpty = sa === '' || sa === '\u2014';
      let bEmpty = sb === '' || sb === '\u2014';
      if (sortType === 'number') {
        aEmpty = aEmpty || isNaN(parseFloat(sa));
        bEmpty = bEmpty || isNaN(parseFloat(sb));
      }
      if (aEmpty && bEmpty) return 0;
      if (aEmpty) return 1;
      if (bEmpty) return -1;

      return cmp(va, vb) * dir;
    });

    // Snapshot the wrapper's scroll position so re-appending rows does
    // not visually shift the table when a horizontal scrollbar is active.
    const wrapper = this.table.closest('.table-responsive');
    const savedScrollLeft = wrapper ? wrapper.scrollLeft : 0;
    const savedScrollTop = wrapper ? wrapper.scrollTop : 0;

    // Re-append sorted row groups (data row + companions) to tbody
    const tbody = this.table.tBodies[0];
    /* Already in this order - the server rendered the default sort, or the
       reader clicked the column they were already sorted by. Moving 574
       rows through a fragment to put them back where they are cost 115ms
       of the Users page's load (profiled) and re-laid the table out for
       nothing. Compare the order first; only a change touches the DOM. */
    let inOrder = true;
    let cursor = tbody.firstElementChild;
    for (let i = 0; i < groups.length && inOrder; i++) {
      if (cursor !== groups[i].primary) { inOrder = false; break; }
      cursor = cursor.nextElementSibling;
      for (let j = 0; j < groups[i].companions.length; j++) {
        if (cursor !== groups[i].companions[j]) { inOrder = false; break; }
        cursor = cursor.nextElementSibling;
      }
    }
    if (inOrder) return;
    const fragment = document.createDocumentFragment();
    for (let i = 0; i < groups.length; i++) {
      fragment.appendChild(groups[i].primary);
      for (let j = 0; j < groups[i].companions.length; j++) {
        fragment.appendChild(groups[i].companions[j]);
      }
    }
    tbody.appendChild(fragment);

    if (wrapper) {
      wrapper.scrollLeft = savedScrollLeft;
      wrapper.scrollTop = savedScrollTop;
    }

    // Restripe visible rows for correct zebra colouring
    if (typeof restripeTable === 'function') {
      restripeTable(tbody);
    }
  };

  SortableTable.prototype._updateUI = function () {
    for (const th of this._headers) {
      const key = th.getAttribute('data-sort-key');
      const arrow = th.querySelector('.sort-arrow');

      if (key === this.sortKey) {
        th.classList.add('sorted');
        if (arrow) {
          arrow.classList.remove('asc', 'desc');
          arrow.classList.add(this.sortDir);
        }
      } else {
        th.classList.remove('sorted');
        if (arrow) {
          arrow.classList.remove('asc', 'desc');
        }
      }
    }
  };

  SortableTable.prototype._syncPaginator = function () {
    const tbody = this.table.tBodies[0];
    if (!tbody) return;

    // Dispatch event for custom listeners
    const evt = new CustomEvent('sortable-table:sorted', {
      bubbles: true,
      detail: { key: this.sortKey, dir: this.sortDir }
    });
    this.table.dispatchEvent(evt);

    // Auto-resync ClientPaginator if registered on tbody
    // Use resyncOrder (preserves active filter) when available, else resync.
    if (tbody._clientPaginator) {
      if (typeof tbody._clientPaginator.resyncOrder === 'function') {
        tbody._clientPaginator.resyncOrder();
      } else if (typeof tbody._clientPaginator.resync === 'function') {
        tbody._clientPaginator.resync();
      }
      tbody._clientPaginator.goToPage(1);
    }
  };

  /* -- Public API -- */
  SortableTable.prototype.sort = function (key, dir) {
    this.sortKey = key;
    this.sortDir = dir || 'asc';
    this._doSort();
    this._updateUI();
    this._syncPaginator();
  };

  /* A cheap fingerprint of the current row order, used to tell whether a sort
     actually moved anything. Row identity is enough - the cells never change. */
  SortableTable.prototype._rowOrder = function () {
    const tbody = this.table.querySelector('tbody');
    if (!tbody) return '';
    return Array.prototype.map
      .call(tbody.rows, (r) => r.rowIndex + ':' + (r.textContent || '').slice(0, 40))
      .join('|');
  };

  SortableTable.prototype.refresh = function () {
    this._doSort();
    this._updateUI();
  };

  /* -- Static methods -- */
  SortableTable.init = function () {
    const tables = document.querySelectorAll('table[data-sortable]');
    for (const table of tables) {
      new SortableTable(table);
    }
  };

  SortableTable.initTable = function (tableEl) {
    if (tableEl) return new SortableTable(tableEl);
  };

  SortableTable.getInstance = function (tableEl) {
    return _instances.get(tableEl) || null;
  };

  /* -- Expose globally -- */
  window.SortableTable = SortableTable;
  if (window.GP) window.GP.SortableTable = SortableTable;

  /* -- Auto-init on DOMContentLoaded -- */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', SortableTable.init);
  } else {
    SortableTable.init();
  }
})();