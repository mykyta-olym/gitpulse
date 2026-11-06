/* THE dropdown controller - every dropdown in the app, on every page.
 *
 * There used to be two: this one for [data-dropdown], and a second class-based
 * handler in the core UI helpers for .gl-dropdown. They had to know about each
 * other to avoid desyncing `.open` (documented at length in the code they
 * replaced), which is exactly the sort of duplicate this codebase does not keep.
 * Both conventions are now roots here, so no markup had to change.
 *
 * Alpine-managed dropdowns are still someone else's: Alpine owns `.open` through
 * :class, and a second writer would fight it.
 */
(function initDropdowns(global) {
  'use strict';

  const ROOT_SELECTOR = '[data-dropdown], .gl-dropdown';
  const OPEN_ROOT_SELECTOR = '[data-dropdown].open, .gl-dropdown.open';
  const TOGGLE_SELECTOR = '[data-dropdown-toggle], .gl-dropdown-toggle';
  const MENU_SELECTOR = '[data-dropdown-menu], .gl-dropdown-menu';
  const ITEM_SELECTOR = '.gl-dropdown-item';

  function isAlpineManaged(root) {
    return !!(root && (
      root.hasAttribute('x-data')
      || (root.parentElement && root.parentElement.closest('[x-data]'))
    ));
  }

  function parts(root) {
    if (!root) return {};
    return {
      toggle: root.querySelector(TOGGLE_SELECTOR),
      /* When the menu is portaled to <body> it is no longer a descendant of the
         root, so `root.querySelector` cannot find it - and setOpen(false) then
         bailed on `if (!menu) return` BEFORE it could un-portal, leaving the
         "Per page" menu open on the page forever. The portal keeps a back-
         reference; prefer it. */
      menu: root._portalMenu || root.querySelector(MENU_SELECTOR),
    };
  }

  function isOpen(root) {
    return Boolean(root && root.classList.contains('open'));
  }

  function ownerOf(node) {
    const root = node.closest(ROOT_SELECTOR);
    if (root) return root;
    const portal = node.closest('[data-gl-portal]');
    return portal && Array.from(document.querySelectorAll(ROOT_SELECTOR))
      .find(candidate => candidate._portalMenu === portal);
  }

  function setOpen(root, open, options) {
    if (!root || isAlpineManaged(root)) return;
    const { toggle, menu } = parts(root);
    if (!toggle || !menu) return;

    if (open) {
      closeAll(root);
    }

    /* WAI-ARIA fix: when CLOSING, move focus out of the menu BEFORE hiding it.
       Without this the browser blocks aria-hidden because a focused descendant
       (e.g. a .gl-dropdown-item with :focus or a link that was just clicked)
       would be hidden from assistive technology, producing the console warning:
       "Blocked aria-hidden on an element because its descendant retained focus." */
    if (!open && menu.contains(document.activeElement)) {
      try { toggle.focus({ preventScroll: true }); } catch (_) {}
      if (menu.contains(document.activeElement) && document.activeElement.blur) {
        document.activeElement.blur();
      }
    }

    root.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-hidden', String(!open));
    if ('inert' in menu) {
      menu.inert = !open;
    }

    if (open) {
      root.dataset.dropdownOpen = '1';
      /* Portaling, as an option of THIS controller rather than a second one.
         A menu inside `overflow: hidden` has to move to <body> to be seen; the
         pagination page-size menu did that with its own toggle handler, so two
         controllers answered the same click. Marking the root is enough now. */
      if (root.hasAttribute('data-dropdown-portal')) portalMenu(root, menu, toggle);
      if (options && options.owner) root.dataset.dropdownOwner = options.owner;
      /* Decide up/down HERE, at the one moment the panel opens. This used to be
         a MutationObserver on the whole body watching `style` and `class` - so
         every GSAP tween (which writes inline style every frame) and every state
         class anywhere in the app delivered a mutation record, all to answer a
         question that only matters when a dropdown opens. */
      if (window.GP && typeof GP.positionDropdownMenu === 'function') {
        GP.positionDropdownMenu(menu);
      }
    } else {
      if (root.hasAttribute('data-dropdown-portal')) unportalMenu(root);
      delete root.dataset.dropdownOpen;
      delete root.dataset.dropdownOwner;
      delete root._keyboardFocusItem;
    }
  }

  /* ------------------------------------------------------------------
     Portaled menus - THE implementation, for every dropdown that has to escape
     an `overflow: hidden` ancestor.

     The paginator's page-size menu used to carry its own copy of all of this
     (move to <body>, measure the toggle, pin with position: fixed, pick up or
     down, undo on close). Two implementations of one behaviour, and only one of
     them learned that a fixed menu has to CLOSE when its anchor scrolls away -
     which is why that one hung in the middle of the table after a scroll.
     ------------------------------------------------------------------ */

  const PORTAL_GAP = 4;

  /** Move `menu` to <body> and pin it to `toggle`. Idempotent. */
  function portalMenu(root, menu, toggle) {
    if (!root || !menu || !toggle || root._portalMenu) return;

    root._portalMenu = menu;
    root._portalHome = menu.parentElement;
    menu.setAttribute('data-gl-portal', '');
    document.body.appendChild(menu);

    /* Measure it where it will be drawn, but invisibly: `min-width: 100%` on a
       fixed element resolves against the VIEWPORT, so the menu has to be given
       the toggle's width before its height means anything. */
    Object.assign(menu.style, {
      position: 'fixed',
      visibility: 'hidden',
      opacity: '0',
      display: 'block',
      maxWidth: '200px',
      left: 'auto', right: 'auto', top: 'auto', bottom: 'auto',
    });
    positionMenu(menu, toggle);
    Object.assign(menu.style, {
      zIndex: '9999', opacity: '1', visibility: 'visible', transform: 'translateY(0)',
    });

    /* This app scrolls inside `.gl-page-content`, not the window, so a menu
       pinned to fixed coordinates parts company with its toggle the moment the
       reader scrolls. It used to CLOSE on any scroll, which turned a nudge of
       the wheel into a dismissed menu. It follows instead, the way GitLab's
       does, and only closes once the toggle has actually left the viewport -
       past that point there is nothing left to point at.

       One rect read on one element, coalesced into a single frame, and only
       while a menu is open: not the multi-element read/write loop the earlier
       reflow work was about. Capture phase - the scroll happens on an ancestor
       container and does not bubble. */
    let frame = 0;
    root._portalReflow = function () {
      if (frame) return;
      frame = requestAnimationFrame(function () {
        frame = 0;
        if (!root._portalMenu) return;
        const r = toggle.getBoundingClientRect();
        const gone = r.bottom < 0 || r.top > window.innerHeight
          || r.right < 0 || r.left > window.innerWidth;
        if (gone) { unportalMenu(root); setOpen(root, false); return; }
        positionMenu(menu, toggle);
      });
    };
    root._portalDismiss = function () {
      if (frame) { cancelAnimationFrame(frame); frame = 0; }
    };
    window.addEventListener('scroll', root._portalReflow, { capture: true, passive: true });
    window.addEventListener('resize', root._portalReflow, { passive: true });
  }

  /** Pin `menu` under (or over) `toggle` in viewport coordinates. */
  function positionMenu(menu, toggle) {
    const rect = toggle.getBoundingClientRect();
    menu.style.minWidth = rect.width + 'px';
    const menuH = menu.offsetHeight;
    const spaceBelow = window.innerHeight - rect.bottom;
    const openUp = spaceBelow < menuH + PORTAL_GAP && rect.top > menuH + PORTAL_GAP;
    /* Right-anchored to the toggle, but never past the left edge of the
       screen: a toggle near the left of a phone pushed its menu off it. */
    const EDGE = 8;
    const menuW = menu.offsetWidth;
    const maxRight = Math.max(EDGE, window.innerWidth - EDGE - menuW);
    const menuRight = Math.max(EDGE, Math.min(window.innerWidth - rect.right, maxRight));
    Object.assign(menu.style, openUp
      ? { right: menuRight + 'px', top: 'auto', bottom: (window.innerHeight - rect.top + PORTAL_GAP) + 'px' }
      : { right: menuRight + 'px', bottom: 'auto', top: (rect.bottom + PORTAL_GAP) + 'px' });
  }

  /** Put the menu back where it came from and drop everything portalling added. */
  function unportalMenu(root) {
    if (!root) return;
    if (root._portalReflow) {
      window.removeEventListener('scroll', root._portalReflow, { capture: true });
      window.removeEventListener('resize', root._portalReflow);
      root._portalReflow = null;
    }
    /* Drop a frame that is already queued, or it repositions - or closes - a
       menu that has just been put back. */
    if (root._portalDismiss) { root._portalDismiss(); root._portalDismiss = null; }
    const menu = root._portalMenu;
    if (!menu) return;
    menu.removeAttribute('style');
    menu.removeAttribute('data-gl-portal');
    (root._portalHome || root).appendChild(menu);
    root._portalMenu = null;
    root._portalHome = null;
  }

  function closeAll(exceptRoot) {
    document.querySelectorAll(OPEN_ROOT_SELECTOR).forEach(function (root) {
      if (root === exceptRoot) return;
      // A tour owns the profile menu while the appearance/mode step is active;
      // a stray document click (e.g. on the Driver.js overlay) must NOT close
      // it - only the tour's own GP.dropdown.close() does. Otherwise the
      // highlighted theme switcher vanishes mid-step.
      if (root.dataset.dropdownOwner === 'tour') return;
      setOpen(root, false);
    });
  }

  function toggle(root) {
    setOpen(root, !isOpen(root));
  }

  function initRoot(root) {
    if (!root || root.dataset.dropdownReady === '1' || isAlpineManaged(root)) return;
    const { toggle: toggleButton, menu } = parts(root);
    if (!toggleButton || !menu) return;

    root.dataset.dropdownReady = '1';
    // Always materialise CLOSED on first init. Never trust a stale `.open`
    // class that may have survived a cached/bfcache-restored document or an
    // older markup revision served by the Service Worker - that was the
    // source of the "profile menu opens by itself on load" report.
    root.classList.remove('open');
    delete root.dataset.dropdownOpen;
    delete root.dataset.dropdownOwner;
    // Move focus out before hiding, same reason as in setOpen().
    if (menu.contains(document.activeElement)) {
      try { toggleButton.focus({ preventScroll: true }); } catch (_) {}
      if (menu.contains(document.activeElement) && document.activeElement.blur) {
        document.activeElement.blur();
      }
    }
    toggleButton.setAttribute('aria-expanded', 'false');
    menu.setAttribute('aria-hidden', 'true');
    if ('inert' in menu) menu.inert = true;
  }

  function initAll(scope) {
    const container = scope || document;
    if (container.matches && container.matches(ROOT_SELECTOR)) initRoot(container);
    container.querySelectorAll(ROOT_SELECTOR).forEach(initRoot);
  }

  document.addEventListener('click', function (event) {
    const toggleButton = event.target.closest(TOGGLE_SELECTOR);
    if (toggleButton) {
      const root = toggleButton.closest(ROOT_SELECTOR);
      if (root && !isAlpineManaged(root)) {
        event.preventDefault();
        toggle(root);
      } else if (root) {
        /* An Alpine dropdown opens itself, but the menus THIS controller owns
           still have to close: returning here left the period selector open
           under the status filter the moment the status filter was clicked -
           two menus standing on top of each other. Alpine ones close
           themselves (@click.outside). */
        document.querySelectorAll(OPEN_ROOT_SELECTOR).forEach(function (other) {
          if (other !== root && !isAlpineManaged(other) && other.dataset.dropdownOwner !== 'tour') {
            setOpen(other, false);
          }
        });
      }
      return;
    }

    /* Choosing an item closes the menu it came from. */
    const item = event.target.closest(ITEM_SELECTOR);
    if (item) {
      const owner = ownerOf(item);
      if (owner) setOpen(owner, false);
      return;
    }

    /* A menu portaled to <body> (to escape overflow:hidden) is still INSIDE its
       dropdown as far as the user is concerned - never treat a click there as an
       outside click. */
    if (event.target.closest('[data-gl-portal]')) return;

    const root = event.target.closest(ROOT_SELECTOR);
    if (!root) {
      if (document.documentElement.classList.contains('theme-transitioning')) {
        return;
      }
      closeAll();
      return;
    }

    if (
      root.classList.contains('open')
      && event.target.closest('[data-dropdown-close]')
      && !event.target.closest('[data-dropdown-keep-open]')
    ) {
      setOpen(root, false);
    }
  });

  /* ------------------------------------------------------------------
     Alpine-managed selects inside a scroll box.

     Alpine owns `.open` on these (the Course role select in the Teachers
     table, the role select in its toolbar), so the toggle is left to it - but
     a menu drawn inside `.table-responsive` (overflow: auto) is clipped by it
     all the same: the last row's menu showed as a sliver under the toggle.
     They get the same portal as any other menu. There is no hook into
     Alpine's state, so the root's class is read AFTER the click has been
     handled: Alpine applies `:class` from a microtask, hence the timeout. A
     click anywhere re-syncs every portaled root, which is how an outside
     click or a pick (both of which Alpine answers by dropping `.open`) put the
     menu back.
     ------------------------------------------------------------------ */
  const CLIP_SCOPE = '.table-responsive, .table-scrollable, [data-dropdown-portal-scope]';
  const _alpinePortaled = new Set();

  function syncAlpinePortal(root) {
    if (!root || !root.isConnected) { _alpinePortaled.delete(root); return; }
    const { toggle: toggleButton, menu } = parts(root);
    if (!toggleButton || !menu) return;
    if (root.classList.contains('open')) {
      if (!root._portalMenu && root.closest(CLIP_SCOPE)) {
        portalMenu(root, menu, toggleButton);
        _alpinePortaled.add(root);
      }
    } else if (root._portalMenu) {
      unportalMenu(root);
      _alpinePortaled.delete(root);
    }
  }

  document.addEventListener('click', function (event) {
    const toggleButton = event.target.closest(TOGGLE_SELECTOR);
    const root = toggleButton && toggleButton.closest(ROOT_SELECTOR);
    const pending = new Set(_alpinePortaled);
    if (root && isAlpineManaged(root)) pending.add(root);
    if (!pending.size) return;
    setTimeout(function () { pending.forEach(syncAlpinePortal); }, 0);
  });

  document.addEventListener('keydown', function (event) {
    const root = ownerOf(event.target)
      || (event.key === 'Escape' && document.querySelector(OPEN_ROOT_SELECTOR));
    if (!root || isAlpineManaged(root)) return;
    const { toggle: toggleButton, menu } = parts(root);
    if (!toggleButton || !menu) return;
    const wasOpen = isOpen(root);
    if (event.key === 'Escape' || event.key === 'Tab') {
      if (!wasOpen) return;
      if (menu.contains(document.activeElement)) toggleButton.focus({ preventScroll: true });
      setOpen(root, false);
      if (event.key === 'Escape') {
        toggleButton.focus({ preventScroll: true });
        event.preventDefault();
        event.stopPropagation(); // dismiss the list before its parent dialog
      }
      return;
    }
    if (toggleButton.disabled || event.target.closest('input, textarea, select, [contenteditable]')) return;
    const arrows = event.key === 'ArrowDown' || event.key === 'ArrowUp';
    if (!arrows && !(wasOpen && (event.key === 'Home' || event.key === 'End'))) return;
    event.preventDefault();
    setOpen(root, true);
    const items = Array.from(menu.querySelectorAll(ITEM_SELECTOR)).filter(item =>
      !item.matches(':disabled, [aria-disabled="true"], .disabled') && item.getClientRects().length);
    if (!items.length) return;
    let index = items.indexOf(root._keyboardFocusItem || document.activeElement);
    if (!wasOpen) index = items.findIndex(item => item.matches('.active, [aria-selected="true"]')
      || item.parentElement.getAttribute('aria-selected') === 'true');
    else if (event.key === 'Home') index = 0;
    else if (event.key === 'End') index = items.length - 1;
    else index = (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
    if (index < 0) index = event.key === 'ArrowUp' ? items.length - 1 : 0;
    const item = items[index];
    const previousFocus = document.activeElement;
    root._keyboardFocusItem = item;
    // Reparenting can leave inherited visibility hidden until rendering catches
    // up. Wait for visibility, unless a new key, dismissal or focus move wins.
    function focusItem() {
      if (!isOpen(root) || !item.isConnected || root._keyboardFocusItem !== item
          || document.activeElement !== previousFocus) return;
      if (getComputedStyle(item).visibility === 'hidden') {
        requestAnimationFrame(focusItem);
        return;
      }
      item.focus({ preventScroll: true });
      delete root._keyboardFocusItem;
    }
    focusItem();
    item.scrollIntoView({ block: 'nearest' });
  }, true);

  document.addEventListener('DOMContentLoaded', function () {
    initAll(document);
  });
  document.addEventListener('htmx:afterSwap', function (event) {
    initAll(event.target);
  });
  /* A portaled menu lives on <body>; when its page is swapped out, put it
     back (or drop it) rather than leaving it floating over the next page. */
  document.addEventListener('htmx:beforeSwap', function () {
    _alpinePortaled.forEach(function (root) { unportalMenu(root); });
    _alpinePortaled.clear();
  });
  global.addEventListener('pagehide', function () {
    closeAll();
  });

  global.GP = global.GP || {};
  global.GP.dropdown = Object.freeze({
    close: function (root) { setOpen(root, false); },
    closeAll: closeAll,
    init: initAll,
    isOpen: isOpen,
    open: function (root, options) { setOpen(root, true, options); },
    toggle: toggle,
    /* For a menu that has to escape an `overflow: hidden` ancestor. THE
       implementation - see the note above portalMenu. */
    portal: portalMenu,
    unportal: unportalMenu,
  });
})(window);
