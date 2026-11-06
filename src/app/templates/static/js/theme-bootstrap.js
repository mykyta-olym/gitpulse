/**
 * Color mode bootstrap and controller.
 *
 * This file is intentionally loaded synchronously before CSS so the resolved
 * mode is applied before first paint. It also owns the shared light/dark/system
 * preference contract for dashboard, login, and standalone error pages.
 */
(function initColorMode(global) {
  "use strict";

  const STORAGE_KEY = "gitpulse-color-mode";
  const COOKIE_KEY = "gitpulse_color_mode";
  const MODES = new Set(["light", "dark", "system"]);
  const media = global.matchMedia("(prefers-color-scheme: dark)");
  const root = document.documentElement;

  // A programmatic reload (version mismatch, settings save - GP.reloadKeepScroll)
  // sets this flag. Handled here, synchronously before first paint, so the page
  // comes back IN PLACE: suppress the entrance animation and turn off the
  // browser's own scroll restoration, leaving the saved-scroll restore to drop
  // us exactly where we were - instead of a flash, a translate-in, then a jump.
  try {
    if (sessionStorage.getItem("_gp_silent_reload")) {
      root.classList.add("gp-no-enter");
      if ("scrollRestoration" in history) history.scrollRestoration = "manual";
    }
  } catch (_) { /* storage unavailable */ }

  /* The first-frame gate (tokens.css hides <body> while data-gp-gate is set
     and data-gp-ready is not). Lifted in a requestAnimationFrame queued from
     DOMContentLoaded: the callback runs in the rendering step AFTER every
     DOMContentLoaded listener - Alpine's start, the table painters, the mode
     switcher sync below - and before that frame is painted, so the first
     visible frame is the finished page. Registered here, in the one script
     that runs before anything paints. The timeout is the safety net for a
     deferred script that never arrives: a late page beats no page. */
  if (root.hasAttribute("data-gp-gate")) {
    const unveil = function () { root.setAttribute("data-gp-ready", ""); };
    document.addEventListener("DOMContentLoaded", function () {
      global.requestAnimationFrame(unveil);
    }, { once: true });
    global.setTimeout(unveil, 3000);
  }

  const persistUrl = root.dataset.themePersistUrl || "";
  let persistSequence = 0;
  // Set when readPreference() keeps a local explicit choice over a server
  // "system" default; the account is reconciled once the DOM (CSRF meta) is up.
  let reconcileToServer = null;
  let preference = readPreference();
  let activeTransitions = 0;

  function readLocalPreference() {
    try {
      const stored = global.localStorage.getItem(STORAGE_KEY);
      if (MODES.has(stored)) return stored;
    } catch (_) {
      // Continue with the cookie fallback.
    }
    let cookiePreference = "";
    try {
      cookiePreference = JSON.parse(root.dataset.preferenceCookies || "{}")[COOKIE_KEY] || "";
    } catch (_) { /* missing preferences use the system mode */ }
    return MODES.has(cookiePreference) ? cookiePreference : null;
  }

  function readPreference() {
    const serverPreference = root.dataset.themePreference;
    const local = readLocalPreference();
    // The account (server) value is authoritative for an EXPLICIT choice, so a
    // light/dark set on another device syncs here. But when the server is only
    // the ambiguous "system" DEFAULT while THIS browser holds an explicit
    // light/dark, trust the local choice: the account was never overridden (or
    // an earlier persist POST failed). Following the OS in that case is exactly
    // what made an explicit dark flip to light on its own after a reload. Keep
    // the local choice and reconcile the account below.
    if (MODES.has(serverPreference)) {
      if (serverPreference === "system" && local && local !== "system") {
        reconcileToServer = local;
        return local;
      }
      return serverPreference;
    }
    return local || "system";
  }

  function persistForBrowser(mode) {
    try {
      global.localStorage.setItem(STORAGE_KEY, mode);
    } catch (_) {
      // Storage can be unavailable in private or embedded browsing contexts.
    }
    global.Cookies.setAsync(COOKIE_KEY, mode, { expires: 365 }).catch(() => {});
  }

  function resolvedMode(mode) {
    return mode === "system" ? (media.matches ? "dark" : "light") : mode;
  }

  function updateThemeColor(mode) {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = mode === "dark" ? "#18171d" : "#ffffff";
  }

  function syncControls() {
    document.querySelectorAll("[data-theme-value]").forEach(function (control) {
      const selected = control.dataset.themeValue === preference;
      control.classList.toggle("is-selected", selected);
      control.setAttribute("aria-pressed", selected ? "true" : "false");
    });
  }

  function persistOnServer(mode) {
    if (!persistUrl) return;
    const sequence = ++persistSequence;
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";

    global.fetch(persistUrl, {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf,
      },
      body: JSON.stringify({ preference: mode }),
    }).catch(function () {
      if (sequence !== persistSequence) return;
      // The local preference remains usable offline. A later selection or
      // page load will reconcile it with the account preference.
    });
  }

  function apply(mode, options) {
    const settings = options || {};
    preference = MODES.has(mode) ? mode : "system";
    const resolved = resolvedMode(preference);

    // Auth pages (login / logout) pin themselves to a FIXED light card surface
    // via data-color-scheme-lock. Honour that lock for BOTH the browser canvas
    // (color-scheme) AND the design tokens (data-theme). Otherwise a visitor
    // whose saved preference is dark keeps data-theme="dark" here, so the white
    // card is correct but every token-driven component painted on top of it -
    // the language dropdown menu, the flash alerts, toasts, the selected-item
    // checkmark - renders dark on white. Pages with no lock follow the resolved
    // preference unchanged.
    const schemeLock = root.dataset.colorSchemeLock;
    const scheme = schemeLock === "light" || schemeLock === "dark" ? schemeLock : resolved;

    // Flip the theme INSTANTLY: suppress every element's colour transition for
    // the duration of the swap, otherwise thousands of elements animate their
    // background/colour at once and the switch janks hard on mobile GPUs.
    const changing = root.dataset.theme !== scheme;
    if (changing) root.classList.add("theme-no-transition");

    root.dataset.theme = scheme;
    root.dataset.themePreference = preference;
    root.style.colorScheme = scheme;
    updateThemeColor(scheme);

    if (settings.persist) {
      persistForBrowser(preference);
      persistOnServer(preference);
    }

    syncControls();
    global.dispatchEvent(new CustomEvent("gp:themechange", {
      detail: { preference: preference, resolved: resolved },
    }));

    if (changing) {
      // Force the un-transitioned paint, then re-enable transitions next frame.
      void root.offsetHeight;
      global.requestAnimationFrame(function () {
        root.classList.remove("theme-no-transition");
      });
    }
  }

  function setPreference(mode, trigger) {
    if (!MODES.has(mode) || mode === preference) return;

    const reduceMotion = global.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // The smooth full-page reveal plays on desktop. The dropdown that holds the
    // control now stays open (the outside-click handler no longer closes a
    // dropdown on an inside click), and the ::view-transition overlay is
    // pointer-events:none, so the reveal no longer "eats" clicks. Only MOBILE is
    // skipped: there the full-width profile dropdown is captured in the snapshot
    // and the circular reveal visibly tears, so the theme is applied instantly.
    const isMobile = global.matchMedia("(max-width: 768px)").matches;
    const canTransition = typeof document.startViewTransition === "function"
      && !reduceMotion && !isMobile;

    if (!canTransition) {
      apply(mode, { persist: true });
      return;
    }

    const rect = trigger && trigger.getBoundingClientRect
      ? trigger.getBoundingClientRect()
      : { left: global.innerWidth / 2, top: global.innerHeight / 2, width: 0, height: 0 };
    root.style.setProperty("--theme-transition-x", (rect.left + rect.width / 2) + "px");
    root.style.setProperty("--theme-transition-y", (rect.top + rect.height / 2) + "px");
    root.classList.add("theme-transitioning");
    activeTransitions++;

    const transition = document.startViewTransition(function () {
      apply(mode, { persist: true });
    });
    transition.finished
      .catch(function () { /* A superseded view transition is harmless. */ })
      .finally(function () {
        activeTransitions--;
        if (activeTransitions <= 0) {
          activeTransitions = 0;
          root.classList.remove("theme-transitioning");
        }
      });
  }

  document.addEventListener("click", function (event) {
    const trigger = event.target.closest("[data-theme-value]");
    if (!trigger) return;
    event.preventDefault();
    setPreference(trigger.dataset.themeValue, trigger);
  });

  if (typeof media.addEventListener === "function") {
    media.addEventListener("change", function () {
      if (preference === "system") apply("system");
    });
  } else if (typeof media.addListener === "function") {
    media.addListener(function () {
      if (preference === "system") apply("system");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    syncControls();
    // Self-heal a local explicit choice the account never recorded (server was
    // "system"), so the next load's server value matches and the theme stops
    // flipping. Deferred to here because the CSRF meta the POST needs is only
    // guaranteed present after the head is parsed. Also write it to localStorage
    // in case the value came from the cookie fallback.
    if (reconcileToServer) {
      persistForBrowser(reconcileToServer);
      persistOnServer(reconcileToServer);
      reconcileToServer = null;
    }
  }, { once: true });

  /* The SPA swaps #main-content without a new document, so DOMContentLoaded
     never fires again - and every [data-theme-value] control is SERVER-rendered
     with aria-pressed="false". Reaching Preferences by navigation therefore left
     the whole Mode switcher looking unselected, whatever the mode actually was.
     Re-sync after each swap; syncControls() is idempotent. */
  document.addEventListener("htmx:afterSwap", syncControls);

  global.addEventListener("storage", function (event) {
    if (event.key === STORAGE_KEY) apply(readPreference());
  });

  apply(preference);
})(window);
