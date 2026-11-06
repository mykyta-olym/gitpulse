/* Alpine component registration and shared bindings. */
/* Register the per-page component factories that page bundles expose on window.*.
   Re-callable: under SPA navigation a page's bundle runs AFTER alpine:init has
   already fired once, so its factory (teacherInvite, llmResourceUrls, ...) is not
   in Alpine's registry yet - the SPA nav handler calls this again after loading the
   new page's bundle, then re-inits the swapped subtree. Registering the CSP build's
   Alpine.data name is what makes `x-data="teacherInvite()"` resolve (it looks up
   the registry, NOT window.*). */
GP.registerPageAlpineData = function () {
  if (!window.Alpine || typeof window.Alpine.data !== 'function') return;
  ['glFormSelect', 'teacherInvite', 'ticketDetailManager', 'supportFormEditor', 'llmResourceUrls'].forEach(function (name) {
    if (typeof window[name] === 'function') {
      try { window.Alpine.data(name, window[name]); } catch (_) { /* noop */ }
    }
  });
};
document.addEventListener('alpine:init', function () {
  if (!window.Alpine) return;

  /* -- Per-page component factories (also re-registered after each SPA nav) -- */
  GP.registerPageAlpineData();

  /* -- Auto-dismiss alert (replaces inline arrow + setTimeout that the
     CSP build cannot evaluate). Used by components/alerts.html. -- */
  window.Alpine.data('autoDismissAlert', function (timeoutMs) {
    return {
      show: true,
      /* The close button used ``@click="show = false"`` - an assignment the
         CSP build cannot evaluate, so the x never dismissed. Exposed as a
         method instead. */
      dismiss: function () { this.show = false; },
      init: function () {
        /* Pass 0 for "stays until dismissed" (non-success alerts); omitting
           the argument keeps the historical 5 s auto-dismiss. */
        const ms = timeoutMs === undefined ? 5000 : Number(timeoutMs);
        if (!isFinite(ms) || ms <= 0) return;
        const self = this;
        setTimeout(function () { self.show = false; }, ms);
      }
    };
  });

  /* -- Collapsible disclosure (content sections, cards, AI-settings prompt).
     These all used ``x-data="{ open: true }"`` + ``@click="open = !open"`` +
     ``x-text="open ? '▼' : '▶'"``. The CSP build evaluates none of those, so
     every collapsible section/card in the app was frozen. Exposed as a
     factory with a no-argument ``toggle`` (the one @click form the CSP parser
     accepts) and a class getter that drives an ANIMATED chevron in CSS
     instead of swapping a text glyph. -- */
  window.Alpine.data('glCollapse', function (initialOpen) {
    return {
      open: initialOpen === undefined ? true : !!initialOpen,
      toggle: function () { this.open = !this.open; },
      /* Bound to the chevron via :class - CSS rotates it 90deg. */
      get chevronClass() { return this.open ? 'is-open' : ''; },
      /* aria-expanded needs the string form. */
      get expanded() { return this.open ? 'true' : 'false'; }
    };
  });

  // Resolve page helpers at invocation: SPA navigation loads them after Alpine init.
  window.Alpine.magic('mdInsert', function () {
    return function (textarea, before, after) { window.mdInsert(textarea, before, after); };
  });

  /* ``$roleBadge(role)`` - the role badge's variant and word
     (GP.roleBadgeParts) for a badge Alpine draws: the CSP build refuses
     x-html, so the caller binds `:class` and `x-text` from these. */
  window.Alpine.magic('roleBadge', function () {
    return function (role) { return GP.roleBadgeParts(role); };
  });

  /* ``$identicon(key)`` - the avatar's identicon class for a key
     (GP.identicon), for the avatars Alpine draws (avatar_alpine). */
  window.Alpine.magic('identicon', function () {
    return function (key) { return 'gl-avatar-identicon-bg' + GP.identicon(key); };
  });

  // Reveal an invalid textarea synchronously, before native validation focuses it.
  window.Alpine.magic('mdShowWrite', function (el) {
    return function (tabVar) {
      window.Alpine.$data(el)[tabVar] = 'write';
      el.style.removeProperty('display');
    };
  });

  // Alpine CSP forbids x-html; render inside the editor that owns the tab.
  window.Alpine.magic('mdShowPreview', function (el) {
    return function (tabVar) {
      GP.renderMarkdownPreview(el.closest('.gh-md-editor'));
      window.Alpine.$data(el)[tabVar] = 'preview';
    };
  });
});

function _autoInitModalDirtyGuards(root) {
  // Forms opt in here or call enableFormDirtyGuard(id) during page init.
  const container = root || document;
  container.querySelectorAll('.modal-backdrop[data-dirty-check]').forEach((el) => {
    if (el.id && (el.querySelector('form') || el.querySelector('input, select, textarea'))) {
      enableFormDirtyGuard(el.id);
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => _autoInitModalDirtyGuards(document));
} else {
  _autoInitModalDirtyGuards(document);
}

document.body.addEventListener('htmx:afterSwap', (event) => {
  _autoInitModalDirtyGuards(event.target || document);
});
