/**
 * One preference store for the documentation, and one rule for whose choice wins.
 *
 * The application and the documentation are two sites on one domain, and both
 * let a reader pick a language and a theme. Without a rule between them the
 * later page load silently overrides the earlier choice, which is what made
 * switching to English on the site land on Slovak documentation.
 *
 * The rule, in order:
 *
 *   1. a choice made HERE, in the documentation      - wins, always
 *   2. otherwise the choice made in the application  - inherited
 *   3. otherwise the site default
 *
 * A choice made in the documentation is explicit: the reader was looking at
 * these pages when they made it. A value inherited from the application is a
 * default that happens to be available, so it must never overwrite an explicit
 * one.
 *
 * The application publishes its choices as ordinary cookies on the shared
 * domain - `gp_lang` and `gitpulse_color_mode` - so this reads them without an
 * extra request.
 */
(() => {
  const DOCS_LANG = "gitpulse-docs-lang";
  const DOCS_THEME = "gitlab-docs-theme"; // the theme's own key, kept as-is
  const APP_LANG_COOKIE = "gp_lang";
  const APP_THEME_COOKIE = "gitpulse_color_mode";

  const cookie = (name) => {
    const hit = document.cookie.split("; ").find((c) => c.startsWith(name + "="));
    return hit ? decodeURIComponent(hit.slice(name.length + 1)) : null;
  };

  const store = {
    get: (k) => {
      try {
        return localStorage.getItem(k);
      } catch {
        return null;
      }
    },
    set: (k, v) => {
      try {
        localStorage.setItem(k, v);
      } catch {
        /* private mode - the page still works, the choice just does not persist */
      }
    },
  };

  /* -- Language ----------------------------------------------------------- */

  const pageLang = document.documentElement.lang; // "sk" or "en"

  // Landing on a documentation URL is NOT a choice. Recording the page's own
  // language on every load (as this used to) set DOCS_LANG on the very first
  // visit, so the "inherit the application's language" rule below could never
  // fire - switching the language on the site never reached the docs. Only the
  // language selector records a choice now (language_selector.vue), so an
  // absent DOCS_LANG genuinely means "the reader has not chosen here".
  const chosen = store.get(DOCS_LANG);
  const fromApp = (cookie(APP_LANG_COOKIE) || "").slice(0, 2).toLowerCase();

  // Only inherit when the reader has never chosen here, and only when the
  // application's language differs from the page they are on. Redirecting
  // someone who just used the selector would undo their click.
  if (!chosen && fromApp && pageLang && fromApp !== pageLang && (fromApp === "sk" || fromApp === "en")) {
    const path = window.location.pathname;
    const target =
      fromApp === "en"
        ? path.replace(/^\/docs\//, "/docs/en/")
        : path.replace(/^\/docs\/en\//, "/docs/");
    if (target !== path) {
      window.location.replace(target + window.location.search + window.location.hash);
      return;
    }
  }

  /* -- Theme -------------------------------------------------------------- */

  // Same rule. The theme's own control (appearance_manager.js) writes DOCS_THEME
  // only when the reader toggles here, so its presence means an explicit choice.
  // When it is absent, follow the application's theme - but do NOT persist it:
  // persisting made the FIRST inherited value stick, so a later change of theme
  // on the site never reached the docs. Apply it for this load (the class, and
  // window.__initialTheme which appearance_manager reads first), and re-inherit
  // on the next load.
  if (!store.get(DOCS_THEME)) {
    const appTheme = cookie(APP_THEME_COOKIE);
    if (appTheme === "dark" || appTheme === "light") {
      window.__initialTheme = appTheme;
      document.documentElement.classList.remove("gl-dark", "gl-light");
      document.documentElement.classList.add(appTheme === "dark" ? "gl-dark" : "gl-light");
    }
  }
})();
