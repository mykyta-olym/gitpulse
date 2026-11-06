/* ============================================================
 * Tab switcher - CSP-proof, no Alpine.
 * ------------------------------------------------------------
 * The dashboard's Quick-access panel drove its tabs with inline Alpine
 * (``:class="qaTab === 'groups' && '..'"``, ``@click="qaTab = 'groups'"``,
 * ``<template x-if>``). The production @alpinejs/csp build evaluates none of
 * those, so the tabs never switched AND the x-if panels never rendered - the
 * panel showed nothing at all.
 *
 * Markup contract (declarative, survives HTMX swaps via delegation):
 *   <div data-tabs [data-tabs-active-class="my--active"]>
 *     <button data-tab="groups">...</button>
 *     <div data-tab-panel="groups">...</div>
 *   </div>
 * The panel whose name matches the clicked tab is shown; the rest get
 * ``hidden``. Defaults to the first tab when none is pre-marked.
 * ============================================================ */
function _tabsActiveClass(container) {
  return container.getAttribute('data-tabs-active-class') || 'active';
}

function _activateTab(container, name) {
  if (!container) return;
  const activeClass = _tabsActiveClass(container);
  container.querySelectorAll('[data-tab]').forEach(function (b) {
    if (b.closest('[data-tabs]') !== container) return;
    const on = b.getAttribute('data-tab') === name;
    b.classList.toggle(activeClass, on);
    b.setAttribute('aria-selected', on ? 'true' : 'false');
    b.setAttribute('tabindex', on ? '0' : '-1');
    /* The underline TRAVELS from the old tab to the new one, which is what
       makes a strip read as one control instead of a row of buttons - and it
       is where the eye is while the panel underneath swaps. */
    if (on) GP.motion.inkTo(b);
  });
  /* The panel swaps at once, as GlTabs does (`:no-fade="true"`). The incoming
     panel used to fade up from opacity 0, so whatever the two panels share
     vanished and came back on every switch - Quick access's empty-state
     illustration, drawn in the same place in both, blinked. The travelling
     underline above is the switch's motion. */
  container.querySelectorAll('[data-tab-panel]').forEach(function (p) {
    if (p.closest('[data-tabs]') !== container) return;
    p.hidden = p.getAttribute('data-tab-panel') !== name;
  });
}

/** Initialise every [data-tabs] group inside `root` (idempotent). */
function initTabs(root) {
  const scope = root && root.querySelectorAll ? root : document;
  scope.querySelectorAll('[data-tabs]').forEach(function (container) {
    const buttons = Array.prototype.filter.call(
      container.querySelectorAll('[data-tab]'),
      function (b) { return b.closest('[data-tabs]') === container; }
    );
    if (!buttons.length) return;
    /* Wire ARIA: each tab button's aria-controls points at "tab-panel-<name>"
       (set in the tabs macro), but the caller's panels only carry
       data-tab-panel, so that reference dangled. Give every panel the matching
       id + a tabpanel role so the control resolves for assistive tech. */
    container.querySelectorAll('[data-tab-panel]').forEach(function (p) {
      if (p.closest('[data-tabs]') !== container) return;
      if (!p.id) p.id = 'tab-panel-' + p.getAttribute('data-tab-panel');
      if (!p.getAttribute('role')) p.setAttribute('role', 'tabpanel');
    });
    const preselected = buttons.find(function (b) {
      return b.getAttribute('aria-selected') === 'true';
    });
    _activateTab(container, (preselected || buttons[0]).getAttribute('data-tab'));
  });
}
GP.initTabs = initTabs;

document.addEventListener('click', function (e) {
  const btn = e.target.closest && e.target.closest('[data-tab]');
  if (!btn) return;
  const container = btn.closest('[data-tabs]');
  if (!container) return;
  e.preventDefault();
  _activateTab(container, btn.getAttribute('data-tab'));
});

/* Arrow-key roving focus, per the WAI-ARIA tablist pattern. */
document.addEventListener('keydown', function (e) {
  if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
  const btn = e.target.closest && e.target.closest('[data-tab]');
  if (!btn) return;
  const container = btn.closest('[data-tabs]');
  if (!container) return;
  const buttons = Array.prototype.filter.call(
    container.querySelectorAll('[data-tab]'),
    function (b) { return b.closest('[data-tabs]') === container; }
  );
  const i = buttons.indexOf(btn);
  if (i < 0) return;
  const next = buttons[(i + (e.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length];
  e.preventDefault();
  _activateTab(container, next.getAttribute('data-tab'));
  next.focus();
});

document.addEventListener('DOMContentLoaded', function () { initTabs(document); });
document.body.addEventListener('htmx:afterSwap', function (evt) {
  initTabs(evt.detail && evt.detail.target ? evt.detail.target : document);
});

/* ============================================================
 * "Show more / show less" disclosure - CSP-proof, no Alpine.
 * ------------------------------------------------------------
 * The dashboard activity feed hid overflow items with
 * ``x-show="limit >= N"`` and expanded them with ``x-click="limit = total"``.
 * The CSP build evaluates neither, so the extra rows stayed hidden behind
 * x-cloak and the button did nothing.
 *
 * Markup contract:
 *   <div data-show-more>
 *     <div class="...--extra">          (hidden by CSS until expanded)
 *     <button data-show-more-toggle="expand">
 *     <button data-show-more-toggle="collapse">
 * Toggling adds/removes ``is-expanded`` on the container; CSS does the rest.
 * ============================================================ */
document.addEventListener('click', function (e) {
  const btn = e.target.closest && e.target.closest('[data-show-more-toggle]');
  if (!btn) return;
  const box = btn.closest('[data-show-more]');
  if (!box) return;
  e.preventDefault();
  box.classList.toggle('is-expanded', btn.getAttribute('data-show-more-toggle') !== 'collapse');
});

/* ============================================================
 * Single-choice button group (rating / scale / NPS) - CSP-proof.
 * ------------------------------------------------------------
 * Support-form rating pickers bound the selection with
 * ``x-data="{ selectedVal: '' }"`` + ``@click="selectedVal = '3'"`` +
 * ``:class="selectedVal === '3' ? .. : .."``. The CSP build evaluates none of
 * them, so the buttons never highlighted AND the hidden input stayed empty -
 * a required rating could not be answered at all.
 *
 * Markup contract:
 *   <div data-choice-group [data-choice-active-class] [data-choice-inactive-class]>
 *     <input type="hidden" name="q1" data-choice-input>
 *     <button data-choice-value="3">3</button>
 * ============================================================ */
document.addEventListener('click', function (e) {
  const btn = e.target.closest && e.target.closest('[data-choice-value]');
  if (!btn) return;
  const group = btn.closest('[data-choice-group]');
  if (!group) return;
  e.preventDefault();
  const onClass = group.getAttribute('data-choice-active-class') || 'btn-confirm';
  const offClass = group.getAttribute('data-choice-inactive-class') || 'btn-secondary';
  const input = group.querySelector('[data-choice-input]');
  if (input) {
    input.value = btn.getAttribute('data-choice-value') || '';
    /* Let form-dirty guards and validation see the change. */
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  group.querySelectorAll('[data-choice-value]').forEach(function (b) {
    if (b.closest('[data-choice-group]') !== group) return;
    const on = b === btn;
    if (onClass) b.classList.toggle(onClass, on);
    if (offClass) b.classList.toggle(offClass, !on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
});
