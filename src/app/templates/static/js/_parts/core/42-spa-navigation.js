/* -- SPA navigation + content reconciliation ---------------------
   GitLab-style instant navigation. We intercept internal <a> clicks and swap ONLY
   the main content region (#main-content) via htmx.ajax - the sidebar, top bar,
   job bar, banners and toasts stay mounted, so navigation has NO layout flash and
   their state / SSE is never disrupted, and the <head> (all CSS/JS) is never
   re-parsed. (hx-boost's declarative auto-wiring would not reliably attach to our
   server-rendered links, so we drive it ourselves.)

   Because only #main-content is swapped, the afterSwap handler reconciles the
   chrome that lives outside it, from the full-page response: <title>, the
   breadcrumb, the sidebar active item, the #gp-modals block, the scroll position,
   and the per-page {% block extra_scripts %} init bundles (js/pages/<page>.js -
   they live in <head> and must define Alpine x-data before Alpine boots, so a
   content swap never re-runs them; each is re-run-safe: activePageCleanup first,
   registers its own cleanup last). Content-script bundles join the same ordered
   queue; libraries already loaded in the shell are reused. */
/* Retire the outgoing page: run the teardown it published as
   GP.activePageCleanup, once, and forget it. The navigation calls it before a
   swap, and every page bundle on entry (a bundle also runs on a full load,
   with no swap before it). It used to be called and kept, so the next bundle
   ran the old page's teardown a second time. */
GP.runPageCleanup = function () {
  const cleanup = GP.activePageCleanup;
  GP.activePageCleanup = null;
  if (typeof cleanup !== 'function') return;
  try { cleanup(); } catch (e) { console.error('Error during activePageCleanup:', e); }
};

(function _spaNavAndHeadMerge() {
  if (!document.body) return;

  function _isPageBundle(url) { return /\/js\/pages\/[^/]+\.js(\?|$)/.test(url || ''); }
  /* Scripts that must execute again on EVERY arrival, not just the first. A
     content script is skipped once it is present in <head>, which is right for a
     library and wrong for anything that writes into the swapped DOM: on the
     second return the markup is fresh and empty and nothing fills it. That is
     what blanked the date under the dashboard greeting from the second visit on.
     Opted in per script with `data-rerun`, so a library never re-executes. */
  function _mustRerun(el) {
    return !!(el && el.hasAttribute && el.hasAttribute('data-rerun'));
  }
  function _nonce() {
    const s = document.querySelector('script[nonce]');
    return s ? (s.nonce || s.getAttribute('nonce') || '') : '';
  }

  /* Bumped on every navigation swap so a slow page's late script-load callback
     cannot init Alpine over content a newer navigation already replaced. */
  let _navGeneration = 0;

  document.body.addEventListener('htmx:beforeSwap', function (evt) {
    const d = evt.detail || {};
    const target = d.target;
    if (d.shouldSwap && d.xhr?.status < 400 && target?.id === 'main-content'
        && target.classList.contains('is-navigating')) {
      // Retire the outgoing page only once its replacement can actually swap.
      // A failed request must leave its modals, handlers and dirty state intact.
      if (!target.classList.contains('is-refining')) GP.motion.coverPage(target);
      target.setAttribute('x-ignore', '');
      try { GP.dropPageModals(); } catch (_) {}
      GP.runPageCleanup();
      try { GP.clearJobReload(); } catch (_) {}
      try { GP.clearAllDirtyReasons(); } catch (_) {}
      try { GP.abortInflight(); } catch (_) {}
    }
  });

  function _scriptSrc(script) {
    return script.getAttribute('src') || script.dataset.gpScriptSrc || '';
  }

  /* Fetch together, execute in dependency order under this document's CSP nonce.
     Abort the read on timeout: removing an external <script> does not prevent
     its late execution over a replacement page. No partial init on load failure. */
  async function _loadScriptsSeq(list, nonce, done) {
    if (!list || !list.length) { done(); return; }
    const controller = new AbortController();
    const deadline = setTimeout(function () { controller.abort(); }, 10000);
    const generation = _navGeneration;
    try {
      const sources = await Promise.all(list.map(async function (src) {
        const response = await fetch(src, { signal: controller.signal, credentials: 'same-origin' });
        if (!response.ok || !/\b(?:java|ecma)script\b/i.test(response.headers.get('Content-Type') || '')) {
          throw new Error('Script load failed');
        }
        return response.text();
      }));
      if (controller.signal.aborted || generation !== _navGeneration) return;
      sources.forEach(function (source, index) {
        const script = document.createElement('script');
        script.dataset.gpScriptSrc = list[index];
        if (nonce) script.setAttribute('nonce', nonce);
        script.textContent = source + '\n//# sourceURL=' + list[index];
        document.head.appendChild(script);
      });
      done(false);
    } catch (_) {
      controller.abort();
      done(true);
    } finally {
      clearTimeout(deadline);
    }
  }

  /* After each navigation swap (target = #main-content), reconcile everything
     that lives OUTSIDE the swapped content region from the full-page response:
     <title>, breadcrumb, sidebar active item, modals block, scroll position, and
     the per-page <head> init bundles. Swapping only the content (not <body>) keeps
     the sidebar / top bar / job bar / banners / toasts mounted, so there is no
     layout flash and their state / SSE is never disrupted. */
  document.body.addEventListener('htmx:afterSwap', function (evt) {
    const d = evt.detail || {};
    const tgt = d.target;
    if (!tgt || tgt.id !== 'main-content') return;   /* only OUR navigation swaps */
    if (!d.xhr || !d.xhr.responseText) return;
    const html = d.xhr.responseText;
    if (html.indexOf('<head') === -1) return;
    let doc;
    try { doc = new DOMParser().parseFromString(html, 'text/html'); }
    catch (_) { return; }
    if (!doc) return;

    /* <title> */
    if (doc.title) document.title = doc.title;

    /* Breadcrumb bar (lives in #glPage, outside #main-content). */
    const nb = doc.querySelector('.gl-content-breadcrumb-nav');
    const cb = document.querySelector('.gl-content-breadcrumb-nav');
    if (nb && cb) cb.innerHTML = nb.innerHTML;

    /* Page-level status strips the incoming page rendered into
       #globalBannerSlot, which also lives outside #main-content. The outgoing
       page's strips are dropped by the handler at the bottom of this file. */
    if (GP._adoptIncomingBanners) GP._adoptIncomingBanners(doc);

    /* Sidebar active item (the sidebar is never swapped). */
    const respActive = doc.querySelector('.gl-sidebar-item.active');
    const activeHref = respActive ? respActive.getAttribute('href') : null;
    Array.prototype.forEach.call(document.querySelectorAll('.gl-sidebar-item'), function (el) {
      if (activeHref && el.getAttribute('href') === activeHref) el.classList.add('active');
      else el.classList.remove('active');
    });

    // Both page roots wait for their factories; outgoing dialogs retire in beforeSwap.
    const nm = doc.querySelector('#gp-modals');
    const cm = document.getElementById('gp-modals');
    if (cm) cm.setAttribute('x-ignore', '');
    if (nm && cm && cm.innerHTML !== nm.innerHTML) cm.innerHTML = nm.innerHTML;

    /* A fresh page starts scrolled to the top (the content area is the scroller). */
    const pc = document.querySelector('.gl-page-content');
    if (pc) pc.scrollTop = 0;

    /* Refresh the page-scoped <meta> tags. base.html renders them only when the
       page has a course (course-id, semester-start, semester-end) and they live in
       the <head>, which a content-only swap never touches - so after navigating
       into a course page they still held the PREVIOUS page's values, or were
       missing entirely. That is what silently dropped the semester week column
       from every date picker opened after an in-app navigation (initFlatpickr
       resolves its week anchor from meta[name=semester-start]). Drop ours, take
       the incoming page's. */
    if (doc.head) {
      ['course-id', 'semester-start', 'semester-end'].forEach(function (name) {
        const sel = 'meta[name="' + name + '"]';
        const cur = document.head.querySelector(sel);
        if (cur) cur.remove();
        const next = doc.head.querySelector(sel);
        if (!next) return;
        const m = document.createElement('meta');
        m.setAttribute('name', name);
        m.setAttribute('content', next.getAttribute('content') || '');
        document.head.appendChild(m);
      });
    }
    /* Refresh per-page inline JSON config (gp-page-config etc.) that lives in the
       <head> ({% block extra_scripts %}) - it is NOT inside the swapped
       #main-content, so a re-run page bundle would otherwise read the PREVIOUS
       page's (or a missing) config and silently misbehave (e.g. _isAdmin=false ->
       edit-user modal never opens). The global configs (gp-base-config /
       gp-i18n-config) live in <body>, so the <head> holds only page-specific
       configs: drop them all, then add the incoming page's. */
    if (doc.head) {
      const _cfgNonce = _nonce();
      Array.prototype.forEach.call(document.head.querySelectorAll('script[type="application/json"][id]'), function (s) { s.remove(); });
      Array.prototype.forEach.call(doc.head.querySelectorAll('script[type="application/json"][id]'), function (cfg) {
        const s = document.createElement('script');
        s.type = 'application/json';
        s.id = cfg.id;
        if (_cfgNonce) s.setAttribute('nonce', _cfgNonce);
        s.textContent = cfg.textContent;
        document.head.appendChild(s);
      });
    }

    /* Page bundles always re-run after a swap. Shared helpers load only once.
       Collect head and content scripts in dependency order; register the page's
       factories before Alpine initialises its x-data. */
    const _pnonce = _nonce();
    const _pageScripts = [];
    const _headHasSrc = function (src) {
      const els = document.head.querySelectorAll('script[src], script[data-gp-script-src]');
      for (let i = 0; i < els.length; i++) { if (_scriptSrc(els[i]) === src) return true; }
      return false;
    };
    if (doc.head) {
      /* Drop stale page-init bundles so they re-run cleanly. */
      Array.prototype.forEach.call(document.head.querySelectorAll('script[src], script[data-gp-script-src]'), function (s) {
        if (_isPageBundle(_scriptSrc(s))) s.remove();
      });
      Array.prototype.forEach.call(doc.head.querySelectorAll('script[src]'), function (el) {
        const src = el.getAttribute('src');
        if (!src) return;
        if (!_isPageBundle(src) && _headHasSrc(src)) return;   /* a shared script, already loaded */
        _pageScripts.push(src);
      });
    }
    /* Content-script bundles live in the swapped #main-content; pull them OUT so
       htmx cannot also run them, and queue them after the head scripts, in order.
       A shared per-page helper (js/config-import.js) placed before the bundle that
       needs it keeps its relative order; a global already in <head> is skipped. */
    const _cmc = document.getElementById('main-content');
    if (_cmc) {
      Array.prototype.forEach.call(_cmc.querySelectorAll('script[src]'), function (el) {
        const src = el.getAttribute('src');
        if (el.parentNode) el.parentNode.removeChild(el);   /* stop htmx re-running it */
        if (!src) return;
        if (!_isPageBundle(src) && !_mustRerun(el) && _headHasSrc(src)) return;   /* already loaded globally */
        if (_mustRerun(el)) {
          /* Drop the stale copy so the browser executes it again rather than
             serving the already-run one. */
          Array.prototype.forEach.call(document.head.querySelectorAll('script[src], script[data-gp-script-src]'), function (h) {
            if (_scriptSrc(h) === src) h.remove();
          });
        }
        _pageScripts.push(src);
      });
    }

    /* The outgoing cover stays visible until page scripts and Alpine finish.
       Fade that cover away over the ready page, without hiding the new frame. */

    /* Init Alpine once every page script has executed. #main-content kept its
       x-ignore across the swap (set in beforeSwap) so Alpine did NOT init - and
       throw "Undefined variable" on - the not-yet-registered components; the CSP
       build resolves x-data from its Alpine.data() registry, so we register the
       page's factories, clear x-ignore, then init both roots and their dialogs. The generation
       guard drops this callback if a newer navigation already replaced the
       content while these scripts were still loading. */
    const _navGen = ++_navGeneration;
    /* Keep the incoming layout measurable but hidden until scripts and Alpine
       finish. Failed script reads present a retryable error. In-place filters
       keep their controls visible while only the rows are marked as refining. */
    const _gated = !tgt.classList.contains('is-refining');
    const _arrive = function () {
      if (_navGen === _navGeneration) tgt.classList.remove('is-arriving');
      if (_navGen === _navGeneration) GP.motion.uncoverPage(tgt);
      if (_navGen === _navGeneration) window.dispatchEvent(new CustomEvent('gp:page-ready'));
    };
    // Set either way: a swap that overtook a gated one must not inherit its mark.
    tgt.classList.toggle('is-arriving', _gated);
    _loadScriptsSeq(_pageScripts, _pnonce, function (failed) {
      if (_navGen !== _navGeneration) return;
      if (failed) {
        tgt.innerHTML = GP.errorStateHtml(GP.t('Failed to load'), GP.t('Reload page'));
        tgt.removeAttribute('x-ignore');
        if (cm) { cm.replaceChildren(); cm.removeAttribute('x-ignore'); }
        GP.bindRetry(tgt, function () { window.location.reload(); });
        _arrive();
        return;
      }
      GP.registerPageAlpineData();
      const roots = [tgt, cm].filter(Boolean);
      roots.forEach(function (root) { root.removeAttribute('x-ignore'); });
      // Let Alpine's observer release x-ignore before mounting or teleporting.
      requestAnimationFrame(function () {
        if (_navGen !== _navGeneration) return;
        const modals = roots.flatMap(function (root) { return _teleportNestedModals(root); });
        modals.forEach(function (modal) { initTippy(modal); });
        roots.concat(modals).forEach(function (root) {
          initDatePickers(root);
          if (window.Alpine) window.Alpine.initTree(root);
        });
        _arrive();
      });
    });
  });

  /* -- Same-document link navigation ---------------------------- */

  /* Share the URL policy between native links and programmatic navigation. */
  function _spaUrl(href) {
    const raw = String(href || '');
    if (!raw || raw.charAt(0) === '#') return null;
    if (/^(javascript:|mailto:|tel:|blob:|data:)/i.test(raw)) return null;
    let url;
    try { url = new URL(raw, window.location.href); } catch (_) { return null; }
    if (url.origin !== window.location.origin) return null;
    /* Full navigation for endpoints that set cookies / redirect server-side or
       serve a non-HTML document - a SPA swap of those would break auth/i18n. */
    if (/^\/(static|docs|grafana|prometheus|jaeger|alertmanager)(\/|$)/.test(url.pathname)
        || /^\/health(\/|$)/.test(url.pathname)
        || /\/dashboard\/(language|logout|login)\b/.test(url.pathname)
        || /\/api\//.test(url.pathname)
        || /\/oauth\b/.test(url.pathname)) return null;
    /* Same path+query (e.g. a pure #hash change) - let the browser handle it. */
    if (url.pathname === window.location.pathname
        && url.search === window.location.search) return null;
    return url.href;
  }

  function _boostTarget(a, evt) {
    if (!a || !a.href) return null;
    if (evt.defaultPrevented || evt.button !== 0 || evt.metaKey || evt.ctrlKey
        || evt.shiftKey || evt.altKey) return null;
    if (a.target && a.target !== '' && a.target !== '_self') return null;
    if (a.hasAttribute('download') || a.hasAttribute('data-no-boost')
        || a.hasAttribute('data-no-transition')) return null;
    if (a.hasAttribute('hx-get') || a.hasAttribute('hx-post')
        || a.hasAttribute('hx-put') || a.hasAttribute('hx-delete')) return null;
    /* `a.href` is the resolved absolute form; the attribute is what the author
       wrote, which is what the scheme tests above want to see. */
    return _spaUrl(a.getAttribute('href') || '');
  }

  /* -- Navigation feedback -------------------------------------------------
     Three things, and nothing that covers the page or moves it:

       * the top progress bar, from the first millisecond (above);
       * the control the reader CLICKED, when it leads with an icon: that icon
         becomes the app's own spinner, in its own box. A sidebar item, a tab, a
         menu row, a button - the mark lands where the reader's eye already is
         and the control does not change size by a pixel;
       * a `progress` cursor over the content region, which is the signal every
         browser and every desktop app uses for exactly this, and the only one
         that works for a click on something with no icon to speak of.

     Four page-level shapes were tried before this and every one was reported:
     blanking the content for a centred mark; a toast beside the page; a
     full-screen veil with a second copy of the brand mark in a 92px ring (it
     covered the page it reported on, ignored the reader's accent, moved its own
     mark 13px when the slow note appeared, and stood still under
     `prefers-reduced-motion`); and a "Loading..." pill at the top of the content
     - which was visible, but was one more thing on the screen saying what the
     progress bar was already saying.

     The mark is placed by ONE rule, and only where that rule holds: the icon has
     to be the control's FIRST child and sit in its leading quarter. Searching
     the control for any icon at all is what put a spinner in the top-right
     corner of a stat card, over that card's own category icon - the "it is just
     chaotically placed, not where it should be" report. A card, a table row or a
     bare text link gets no mark at all now: the bar and the cursor say it, and
     nothing lands somewhere arbitrary. */

  let _busyEl = null;
  let _tinted = null;

  function _markBusy(el) {
    if (_tinted) {
      _tinted.classList.remove('is-nav-busy-tint');
      _tinted = null;
    }
    if (_busyEl && _busyEl !== el) {
      _busyEl.classList.remove('is-nav-busy');
      _busyEl.removeAttribute('aria-busy');
      const old = _busyEl.querySelector('.nav-busy-spinner');
      if (old && old.parentNode) old.parentNode.removeChild(old);
      const hidden = _busyEl.querySelector('.is-nav-busy-icon');
      if (hidden) hidden.classList.remove('is-nav-busy-icon');
    }
    _busyEl = el || null;
    if (!el) return;
    el.classList.add('is-nav-busy');
    el.setAttribute('aria-busy', 'true');
    if (el.querySelector('.nav-busy-spinner')) return;
    /* The app's own mark, at its smallest size, and aria-hidden - the busy
       state is already announced by `aria-busy` on the control itself. */
    const mark = GP.renderSpinnerHtml('xs');
    const holder = document.createElement('span');
    holder.className = 'nav-busy-spinner';
    holder.setAttribute('aria-hidden', 'true');
    holder.innerHTML = mark;
    /* It takes the ICON's place when the control has one - a 16px mark in a
       16px box, so the control's own layout is untouched and the label is never
       covered. A sidebar item, a tab and a card link all lead with an icon. The
       position is measured rather than guessed: only the element knows where its
       icon sits inside its padding. Without one - a bare text link - the mark
       goes to the trailing edge, which is the only free space it has. */
    const icon = _leadingIcon(el);
    if (!icon) {
      /* No icon slot to stand a mark in - a table row, a cell link, a card. The
         control says it is busy by TINTING instead: the same accent wash the row
         highlight uses, held for as long as the fetch runs. Background only, so
         nothing moves, and it works for every control the mark cannot sit on -
         which is most of what a reader clicks in a table.
         A row is tinted through its cells (they paint their own opaque
         backgrounds - see motion.js), so the whole row lights up rather than a
         single cell. */
      _tinted = el.closest('tr') || el;
      _tinted.classList.add('is-nav-busy-tint');
      return;
    }
    icon.classList.add('is-nav-busy-icon');
    /* Measured with getBoundingClientRect, NOT offsetLeft/offsetTop: those are
       HTMLElement properties and every icon here is an <svg>, where they are
       `undefined` - so `undefined + 'px'` was an invalid value the browser
       dropped, and the mark landed at the control's padding origin by luck.
       clientLeft/clientTop take the control's own border off, because an
       absolute offset is measured from its padding box. */
    const box = icon.getBoundingClientRect();
    const host = el.getBoundingClientRect();
    holder.style.left = (box.left - host.left - el.clientLeft) + 'px';
    holder.style.top = (box.top - host.top - el.clientTop) + 'px';
    holder.style.width = box.width + 'px';
    holder.style.height = box.height + 'px';
    el.appendChild(holder);
  }

  /* The control's own leading icon, or null. Both halves of the test matter:
     FIRST CHILD, so a category icon in a card's header - which is a
     `querySelector('svg')` hit but not a leading icon - is never taken; and
     inside the LEADING QUARTER, because a control can start with an icon that
     its own layout has pushed to the right (a flex row with the icon last in
     source order). Anything else means this control has no icon slot, and the
     mark stays off it rather than being put somewhere arbitrary. */
  function _leadingIcon(el) {
    const first = el.firstElementChild;
    if (!first) return null;
    const tag = first.tagName ? first.tagName.toLowerCase() : '';
    const isIcon = tag === 'svg' || tag === 'img' ||
      (first.classList && first.classList.contains('icon'));
    if (!isIcon) return null;
    const box = first.getBoundingClientRect();
    const host = el.getBoundingClientRect();
    if (!box.width || !host.width) return null;
    if (box.left - host.left > host.width * 0.25) return null;
    return first;
  }

  /* Scroll to the fragment the destination URL asks for (#danger-zone from the
     archived banner, #my-courses from the sidebar). A content-only swap never
     triggers the browser's own fragment scroll, so without this every in-app
     anchor link silently landed at the top of the page. The target can arrive
     with a lazily-loaded fragment, so retry briefly while that destination is
     still current. A missing anchor must not move a later page. */
  let _hashTimer = 0;
  function _applyHash(hash) {
    clearTimeout(_hashTimer);
    _hashTimer = 0;
    const pc = document.querySelector('.gl-page-content');
    if (!hash || hash === '#') { if (pc) pc.scrollTop = 0; return; }
    const href = window.location.href;
    let tries = 0;
    const _try = function () {
      _hashTimer = 0;
      if (window.location.href !== href) return;
      const el = _targetFromHash(hash);
      if (el) { GP.scrollWithinPageContent(el, { block: 'start', behavior: 'auto' }); return; }
      if (++tries < 3) _hashTimer = setTimeout(_try, 400);
    };
    _try();
  }

  let _navigating = false;
  /* The newest destination requested while a navigation is still in flight. It
     used to be dropped on the floor (`if (_navigating) return`), so clicking a
     second link before the first page arrived left the reader on the FIRST one -
     with no sign their click had registered. */
  let _queuedNav = null;
  /* Where the reader currently is. Only needed to put the address bar back when
     they cancel a Back that would have discarded unsaved work: by the time
     popstate fires the browser has already moved location.href on. */
  let _lastHref = window.location.href;
  /* Filters and sorters replace the current address without a page swap.
     Remember those writes too, so a later Back can distinguish a fragment
     from a query change and can restore the exact URL when leaving is vetoed. */
  ['pushState', 'replaceState'].forEach(function (method) {
    const update = window.history[method];
    window.history[method] = function () {
      const result = update.apply(this, arguments);
      if (!_navigating) _lastHref = window.location.href;
      return result;
    };
  });
  window.addEventListener('gp:hashnavigate', function () {
    clearTimeout(_hashTimer);
  });

  /* An internal navigation is a content swap, so `beforeunload` - the whole
     unsaved-work guard - never fires: `_navigate` below drops every dirty
     reason and the edits go with them. Clicking a sidebar link with a half-
     filled settings form threw the form away without a word.
     GitLab's settings pages are ordinary page loads, so the browser prompt
     covers them there; here the equivalent has to be asked for explicitly,
     through the app's ONE confirmation component. */
  function _confirmDiscard() {
    if (!GP.hasUnsavedState()) {
      return Promise.resolve(true);
    }
    return GP.confirmDialog({
      title: GP.t('Leave this page?'),
      message: GP.t('Changes you made may not be saved.'),
      confirmText: GP.t('Leave page'),
      variant: 'danger',
    });
  }

  function _navigate(href, push, origin) {
    if (_navigating) { _queuedNav = { href: href, push: push, origin: origin }; return; }
    _navigating = true;
    _confirmDiscard().then(function (ok) {
      if (!ok) {
        _navigating = false;
        /* A click made while the dialog was up would otherwise fire on the NEXT
           navigation and send the reader somewhere they never asked to go. */
        _queuedNav = null;
        /* A cancelled Back has already changed the address bar; put it back so
           it still names the page the reader is looking at. */
        if (push === false && window.location.href !== _lastHref) {
          try { window.history.pushState({ spa: 1 }, '', _lastHref); } catch (_) {}
        }
        return;
      }
      _navigateNow(href, push, origin);
    });
  }

  /* A selector that finds the focused control again in the incoming copy of
     the page: its id, or - for the period box and its menu, which have none - the box. */
  function _focusKeyOf(el, mc) {
    if (!el || el === document.body || !mc.contains(el)) return '';
    if (el.id && window.CSS && typeof CSS.escape === 'function') return '#' + CSS.escape(el.id);
    /* The toggle or the item just picked in its menu: the box is what stays. */
    if (el.closest('[data-period-selector]')) return '[data-period-selector] [data-dropdown-toggle]';
    return '';
  }

  function _navigateNow(href, push, origin) {
    clearTimeout(_hashTimer);
    const generation = _navGeneration;
    const finishProgress = GP.beginTopProgress();
    /* Swap ONLY the main content region (#main-content) - the sidebar, top bar,
       job bar, banners and toasts stay mounted, so navigation has no layout flash
       and their state / SSE is never disrupted. `select` extracts #main-content
       from the full-page response. htmx.ajax fires beforeRequest / afterRequest,
       which the top-progress bar already tracks. */
    const mc = document.getElementById('main-content');
    /* Close any open modal before navigating away. Backdrops are moved
       to <body> (out of forms), so they live OUTSIDE #main-content and the swap
       would otherwise leave them floating open over the new page. */
    // _confirmDiscard already approved leaving. Do not ask each form again.
    try { GP.closeAllModals({ force: true }); } catch (_) {}
    document.querySelectorAll('.flatpickr-input').forEach(function (input) {
      if (input._flatpickr?.isOpen) input._flatpickr.close();
    });
    /* Loading feedback: see the three layered signals above. The OUTGOING page
       stays on screen throughout - GitLab never blanks the page it is leaving,
       however long the next one takes, and neither does this. `is-navigating`
       only makes it inert and steps it back a little; the reader can still read
       the page they are on while the next one is fetched. */
    /* A navigation that STAYS on this page - a filter, the period, a sort, a
       page of the same list: only the query changes. Its controls are not
       stale, they already show what was picked, so they are not stepped back
       with the rest; only the rows are (`is-refining`, logo.css). Dimming the
       whole page made the filter just chosen fade out and come back when the
       page landed - "the selected filter blinks while it loads". */
    let inPlace = false;
    try { inPlace = new URL(href, window.location.href).pathname === window.location.pathname; } catch (_) {}
    if (mc) {
      mc.classList.toggle('is-refining', inPlace);
      mc.classList.add('is-navigating');
    }
    /* ...and the control the reader was on keeps the focus. The swap replaces
       it with its twin and focus fell to <body>: the period box lost its ring
       as the page landed, and a keyboard reader was sent back to the top of
       the page after every filter. */
    const refocus = inPlace && mc ? _focusKeyOf(document.activeElement, mc) : '';
    const previousInert = mc?.inert;
    const previousBusy = mc?.getAttribute('aria-busy');
    if (mc) {
      mc.inert = true;
      mc.setAttribute('aria-busy', 'true');
    }
    _markBusy(origin || null);
    const _clear = function () {
      finishProgress();
      if (_navGeneration === generation) {
        GP.motion.uncoverPage(mc, true);
        // Back/Forward already moved the address bar; the DOM did not move.
        if (push === false && window.location.href !== _lastHref) {
          try { window.history.pushState({ spa: 1 }, '', _lastHref); } catch (_) {}
        }
      }
      _markBusy(null);
      if (mc) mc.classList.remove('is-navigating');
      if (mc) mc.classList.remove('is-refining');
      if (mc) {
        mc.inert = previousInert;
        if (previousBusy === null) mc.removeAttribute('aria-busy');
        else mc.setAttribute('aria-busy', previousBusy);
      }
      _navigating = false;
      /* Honour a click made while this one was still in flight. */
      const q = _queuedNav;
      _queuedNav = null;
      if (q && q.href !== _lastHref) _navigate(q.href, q.push, q.origin);
    };
    /* select the CHILDREN of the response's #main-content, not the element
       itself: `swap:innerHTML` inserts the selection's outerHTML, so selecting
       #main-content would nest a SECOND <main id="main-content"> inside the
       existing one (duplicate id + doubled .main-container padding, which shifted
       the content on every navigation). Selecting `> *` swaps the inner content
       straight in - one #main-content, no double padding. The outer element keeps
       its x-ignore (set in beforeSwap) so Alpine stays suspended until afterSwap
       registers the page's factories. */
    let ready;
    const arrival = new Promise(resolve => { ready = resolve; });
    const onReady = function () {
      if (_navGeneration > generation) ready();
    };
    window.addEventListener('gp:page-ready', onReady);
    window.htmx.ajax('GET', href, { target: '#main-content', select: '#main-content > *', swap: 'innerHTML' })
      .then(function () {
        // HTMX resolves its promise even for HTTP errors that do not swap.
        if (_navGeneration === generation) return;
        if (push !== false) {
          try { window.history.pushState({ spa: 1 }, '', href); } catch (_) {}
        }
        _lastHref = new URL(href, window.location.href).href;
        return arrival.then(function () {
          let hash = '';
          try { hash = new URL(href, window.location.href).hash; } catch (_) {}
          _applyHash(hash);
        });
      })
      // HTTP/network failures already use the shared HTMX error toast.
      .finally(function () {
        window.removeEventListener('gp:page-ready', onReady);
        _clear();
        if (refocus && !_navigating) {
          mc.querySelector(refocus)?.focus({ preventScroll: true });
        }
      }).catch(function () { /* Shared HTMX handlers report the failure. */ });
  }

  /* -- Warm a course tab before it is clicked --------------------------
     The analytics fragment is expensive to build (aggregates over snapshots,
     commits, MRs and pipelines), which is why it is cached server-side. The
     cache key carries the deploy SHA, so every release makes it cold again and
     the next reader pays the full computation - the "analytics takes ages"
     report. Hovering the tab is a reliable signal that the click is coming, so
     the fetch starts ~200ms early and the server cache is warm (and the
     browser has the bytes) by the time it lands.

     Deliberately narrow: only the course sub-tabs, which are pure reads. Some
     dashboard GETs in this app trigger opportunistic background work, and a
     prefetch must never set anything in motion the reader did not ask for. */
  const _prefetched = Object.create(null);
  let _prefetchTimer = 0;
  const _TAB_RE = /^\/dashboard\/courses\/[0-9a-f-]{36}\/(activity|analytics|teachers|settings)$/;

  function _warm(href) {
    let path;
    try { path = new URL(href, window.location.href).pathname; } catch (_) { return; }
    if (!_TAB_RE.test(path) || _prefetched[path]) return;
    _prefetched[path] = 1;
    try {
      fetch(path, {
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { 'X-Gp-Prefetch': '1' },
        priority: 'low',
      }).catch(function () { delete _prefetched[path]; });
    } catch (_) { delete _prefetched[path]; }
  }

  document.addEventListener('mouseover', function (evt) {
    const a = evt.target && evt.target.closest ? evt.target.closest('a.tab-btn[href]') : null;
    if (!a) return;
    if (_prefetchTimer) clearTimeout(_prefetchTimer);
    _prefetchTimer = setTimeout(function () { _warm(a.getAttribute('href')); }, 200);
  }, true);
  document.addEventListener('mouseout', function () {
    if (_prefetchTimer) { clearTimeout(_prefetchTimer); _prefetchTimer = 0; }
  }, true);

  /* CAPTURE phase: some sidebar / menu components stopPropagation on their own
     link clicks during the target/bubble phase, which would starve a bubble-phase
     document listener. Capturing on document runs top-down BEFORE any such
     stopPropagation, so navigation is intercepted reliably. */
  document.addEventListener('click', function (evt) {
    if (!window.htmx) return;
    const a = evt.target.closest && evt.target.closest('a[href]');
    if (!a) return;
    const href = _boostTarget(a, evt);
    if (!href) return;
    evt.preventDefault();
    /* The anchor goes with the navigation: it is the control that turns while
       the fetch is in flight. */
    _navigate(href, true, a);
  }, true);

  /* Back links and the search palette use the same URL policy and feedback.
     Return false for destinations that require a full document load. */
  GP.navigateTo = function (href, origin) {
    if (!window.htmx) return false;
    const url = _spaUrl(href);
    if (!url) return false;
    _navigate(url, true, origin || null);
    return true;
  };

  window.addEventListener('popstate', function () {
    if (!window.htmx) return;
    const previous = new URL(_lastHref);
    if (!_navigating && previous.pathname === window.location.pathname
        && previous.search === window.location.search) {
      _lastHref = window.location.href;
      _applyHash(window.location.hash);
      return;
    }
    _navigate(window.location.href, false);
  });

  /* Seed history so the first Back restores the entry page via popstate. */
  try { window.history.replaceState({ spa: 1 }, '', window.location.href); } catch (_) {}
})();
