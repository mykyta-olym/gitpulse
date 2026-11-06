/* Reveal of freshly-swapped lazy content: ONE quiet fade of the whole region.
   The old behavior staggered the top-level blocks in sequence and cascaded
   collection items one-by-one ("Framer-Motion feel") - deliberately removed:
   sequenced entrances on a data product read as showy noise, not information
   (GitLab/Linear: loaded content simply fades in as a unit). Honors
   prefers-reduced-motion by skipping straight to visible. */
function _revealSwapped(target) {
  if (!target || !target.classList) return;
  // Reveal each lazy region only ONCE (the loading -> content swap). Live
  // refreshes / polling re-swap the same region's innerHTML, and re-running the
  // fade there is exactly the "blink after everything appeared / activate twice"
  // the user sees - even though the stagger was already removed. The flag lives
  // on the persisting container, so a genuine page navigation (fresh container)
  // still fades once.
  if (target.dataset && target.dataset.gpRevealed === '1') return;
  if (target.dataset) target.dataset.gpRevealed = '1';
  /* GP.motion honours reduced motion itself, so the manual media query and the
     self-removing `animationend` listener are gone with the class. */
  GP.motion.panelIn(target);
}

/* When a fragment re-fetch (a manual refresh / SSE reload into .gl-tab-content)
   fails, htmx's beforeSwap handler already blocks the swap and a toast is shown,
   so the existing server-rendered content stays put - we never wipe a region
   to a "failed, retry" card over real content. */

document.body.addEventListener('htmx:afterSwap', (evt) => {
  /* Reveal real content as it replaces a loading state (the lazy-content
     shells): one quiet fade of the whole region - see _revealSwapped. */
  const _swapTarget = evt.detail && evt.detail.target;
  if (_swapTarget && _swapTarget.classList && _swapTarget.classList.contains('gl-tab-content')) {
    _revealSwapped(_swapTarget);
  }
  /* SCOPED to what actually arrived. Every one of these used to re-walk the
     WHOLE document on every swap - and a swap is not rare: each lazy region and
     each SPA navigation fires one. On a data-heavy page that is what Chrome
     reports as `'load' handler took 1027ms`: tippy re-scanning every
     `[data-tippy-content]` on the page, flatpickr re-checking every date input,
     and the label/style passes walking every table again to find nothing new.
     The swapped subtree is the only place new nodes can be. */
  const _swapped = (evt.detail && evt.detail.target) || document;
  // A page navigation refreshes course metadata in its reconciliation handler.
  // Initialise its calendars there, after the incoming semester is available.
  const _pageSwap = _swapped.id === 'main-content' && _swapped.classList.contains('is-navigating');
  initTippy(_swapped);
  /* Upgrade any date inputs that arrived in the swapped-in fragment. */
  if (!_pageSwap) initDatePickers(_swapped);
  /* Label any tables that arrived in the swapped-in fragment for card mode. */
  initResponsiveTableLabels(_swapped);
  /* Apply CSS variables from data-* values in swapped-in fragments. */
  initDataDrivenStyles(_swapped);
  /* Update responsive header actions layout in swapped-in fragments. */
  /* Re-initialise member filters (must run before paginators read rows) */
  if (GP.initMemberFilters) GP.initMemberFilters(evt.detail.target);
  /* Re-initialise sortable tables injected via HTMX lazy loading */
  if (window.SortableTable) SortableTable.init();
  /* Teleport modals loaded via HTMX to <body> so position:fixed is not
     broken by CSS contain:layout on .gl-page / .gl-page-content. */
  /* Modals move to <body>, i.e. OUT of the swapped subtree, so they are
     initialised after the teleport rather than by the scoped pass above. */
  const _teleported = _teleportNestedModals(_swapped);
  if (_teleported && _teleported.length) {
    _teleported.forEach(function (m) { initTippy(m); if (!_pageSwap) initDatePickers(m); });
  }
  GP.initJsonDrops(_swapped);
  /* Staggered entrance for HTMX-loaded content REMOVED: it made lazy
     cards (Contributors, Repository Stats, Protected Branches) pop in
     one-by-one and re-animate on every live refresh, which read as a
     blink / "activate twice". Swapped-in content now appears instantly. */
});
