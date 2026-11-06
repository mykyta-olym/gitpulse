/* ============================================
   Dropdown menus: placement and the hover guard
   ============================================ */
function positionDropdownMenu(menu) {
  /* Skip if menu has an explicit direction class set by the developer */
  if (menu.dataset.directionLocked) return;
  const container = menu.closest('.gl-dropdown');
  if (!container) return;

  // Place the panel before its first interactive frame.
  /* Start every pass from the menu's own CSS anchoring: a clamp left over
     from the previous open was measured against a different layout. */
  if (menu.dataset.clampedX) {
    menu.style.left = '';
    menu.style.right = '';
    delete menu.dataset.clampedX;
  }
  const rect = menu.getBoundingClientRect();
  const toggleEl = container.querySelector('.gl-dropdown-toggle, .gl-top-bar-action, .gl-top-bar-avatar-btn, .gl-sidebar-bottom-item, .btn');
  const toggleRect = toggleEl ? toggleEl.getBoundingClientRect() : container.getBoundingClientRect();
  const viewH = window.innerHeight;
  const menuH = rect.height;
  const spaceBelow = viewH - toggleRect.bottom;
  const spaceAbove = toggleRect.top;

  const needsUp = spaceBelow < menuH + 8 && spaceAbove > menuH + 8;
  const hasUp = menu.classList.contains('gl-dropdown-up');
  if (needsUp && !hasUp) {
    menu.classList.add('gl-dropdown-up');
  } else if (!needsUp && hasUp) {
    menu.classList.remove('gl-dropdown-up');
  }

  /* Left / right, the way the block above does up / down. A menu is anchored
     to ONE edge of its toggle by CSS - usually the right - and nothing asked
     whether the other side fits. On a phone a toggle that sits at the left
     of the screen opened its menu 34-51px past the left edge, cut off and
     half unreadable. Shift it back inside with left/right, not transform:
     the open animation owns `transform`, and an inline one would kill it.
     Up/down only moves the menu vertically, so `rect` is still true for x. */
  const EDGE = 8;
  const viewW = window.innerWidth;
  /* The screen is not the only edge: an ancestor that clips its overflow -
     the page's scroll area, a scrolling table - cuts a menu off just the
     same. A right-anchored menu on a toggle at the LEFT of the Dashboard's
     course bar opened inside the screen but under the sidebar's edge of
     the content area, its first letters shaved off. The box it has to fit
     is the screen narrowed by every such ancestor. */
  let minX = EDGE;
  let maxX = viewW - EDGE;
  for (let el = container.parentElement; el && el !== document.body; el = el.parentElement) {
    if (getComputedStyle(el).overflowX === 'visible') continue;
    const box = el.getBoundingClientRect();
    minX = Math.max(minX, box.left + EDGE);
    maxX = Math.min(maxX, box.right - EDGE);
  }
  /* Out on one side: first flip to the toggle's OTHER edge - a menu that
     starts where its toggle starts reads as belonging to it - and only when
     that does not fit either, press it against the edge of the box. */
  let targetLeft = null;
  if (rect.width >= maxX - minX) {
    targetLeft = minX;
  } else if (rect.left < minX) {
    targetLeft = toggleRect.left >= minX && toggleRect.left + rect.width <= maxX ? toggleRect.left : minX;
  } else if (rect.right > maxX) {
    const flipped = toggleRect.right - rect.width;
    targetLeft = flipped >= minX && toggleRect.right <= maxX ? flipped : maxX - rect.width;
  }
  /* A portaled menu is placed - and re-placed on every scroll - by
     dropdowns.js positionMenu, which clamps it itself. Setting `left` here
     as well would pin both edges once that rewrites `right`. */
  if (menu.hasAttribute('data-gl-portal')) targetLeft = null;
  if (targetLeft !== null) {
    /* `left` is relative to the offset parent - the dropdown for an absolute
       menu, the viewport for a portaled (fixed) one. */
    const parent = menu.offsetParent;
    const parentLeft = parent ? parent.getBoundingClientRect().left : 0;
    menu.style.right = 'auto';
    menu.style.left = Math.round(targetLeft - parentLeft) + 'px';
    menu.dataset.clampedX = '1';
  }
}
GP.positionDropdownMenu = positionDropdownMenu;

/* A menu opens UNDER the pointer, so whichever row happens to land beneath the
   cursor lights up as if the reader had chosen it - "at opening it highlights an
   option by itself". Hover is only meaningful once the pointer has actually
   moved, so suppress it from the click that opens the menu until then. */
document.addEventListener('click', function _armDropdownHoverGuard(event) {
  if (!event.target.closest('.gl-dropdown-toggle, [data-dropdown-toggle]')) return;
  document.documentElement.classList.add('gp-no-hover');
}, true);
document.addEventListener('pointermove', function _releaseDropdownHoverGuard() {
  document.documentElement.classList.remove('gp-no-hover');
}, { passive: true });
