/* eslint-disable class-methods-use-this, no-unused-vars, no-underscore-dangle */

/**
 * Handles switching between light/dark modes and fixed/fluid layouts
 * Theme preference hierarchy: stored theme → system preference → default theme
 * Layout preference hierarchy: stored layout → default layout
 */

const THEME_STORAGE_KEY = "gitlab-docs-theme";
const LAYOUT_STORAGE_KEY = "gitlab-docs-layout";

const THEMES = {
  LIGHT: "light",
  DARK: "dark",
  AUTO: "auto",
};
const LAYOUTS = {
  FIXED: "fixed",
  FLUID: "fluid",
};

class AppearanceManager {
  constructor() {
    this.htmlElement = document.documentElement;
    this.defaultSettings = {
      theme: THEMES.LIGHT,
      layout: LAYOUTS.FIXED,
    };

    // Use pre-determined settings from the FOUC prevention script in the <head> if available
    this.currentSettings = {
      theme: window.__initialTheme || this.determineInitialValue("theme"),
      layout: window.__initialLayout || this.determineInitialValue("layout"),
    };

    this.currentTheme = this.is_auto ? THEMES.AUTO : this.currentSettings.theme;
    this.currentLayout = this.currentSettings.layout;
    this.is_auto = false;

    this.init();
  }

  /**
   * Determine initial value for theme or layout
   * returns {string} - The initial theme or layout
   */
  determineInitialValue(type) {
    const storedValue = this.getStoredPreference(
      type === "theme" ? THEME_STORAGE_KEY : LAYOUT_STORAGE_KEY,
    );

    if (type === "theme" && storedValue === THEMES.AUTO) {
      this.is_auto = true;
      return this.getSystemPreference();
    }

    if (
      storedValue &&
      (type === "theme"
        ? Object.values(THEMES)
        : Object.values(LAYOUTS)
      ).includes(storedValue)
    ) {
      return storedValue;
    }

    // Then check system preference
    if (type === "theme") {
      const systemPreference = this.getSystemPreference();
      if (systemPreference) {
        return systemPreference;
      }
    }

    return this.defaultSettings[type];
  }

  /**
   * Get system theme preference
   */
  getSystemPreference() {
    try {
      return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? THEMES.DARK
        : THEMES.LIGHT;
    } catch (e) {
      return null;
    }
  }

  /**
   * Initialize appearance manager
   */
  init() {
    this.applyPreference({ type: "theme", value: this.currentSettings.theme });
    this.applyPreference({
      type: "layout",
      value: this.currentSettings.layout,
    });
  }

  /**
   * Get stored theme or layout preference from localStorage
   */
  getStoredPreference(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  /**
   * Store theme or layout preference in localStorage
   */
  setStoredPreference(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {
      // localStorage not available, continue without persistence
    }
  }

  /**
   * Apply theme to the document
   */
  applyPreference({ type, value }) {
    this.currentSettings[type] = value;

    if (type === "theme") {
      let effectiveValue = value;

      if (value === THEMES.AUTO) {
        const systemPreference = this.getSystemPreference();
        if (systemPreference) {
          effectiveValue = systemPreference;
        }
      }

      this.htmlElement.classList.remove("gl-dark", "gl-light");
      this.htmlElement.classList.add(
        effectiveValue === THEMES.DARK ? "gl-dark" : "gl-light",
      );
      this.updateSyntaxHighlighting(effectiveValue);
    } else if (type === "layout") {
      this.htmlElement.classList.remove("fixed", "fluid");
      this.htmlElement.classList.add(
        value === LAYOUTS.FLUID ? "fluid" : "fixed",
      );
    }

    const key = type === "theme" ? THEME_STORAGE_KEY : LAYOUT_STORAGE_KEY;

    // Store preference
    this.setStoredPreference(key, value);

    // Dispatch custom event for other components
    this.dispatchChangeEvent({ type, value });
  }

  /**
   * Update syntax highlighting stylesheets
   */
  updateSyntaxHighlighting(theme) {
    const darkStylesheet = document.getElementById("syntax-dark-theme");
    const lightStylesheet = document.getElementById("syntax-light-theme");

    if (darkStylesheet && lightStylesheet) {
      if (theme === THEMES.DARK) {
        darkStylesheet.disabled = false;
        lightStylesheet.disabled = true;
      } else {
        darkStylesheet.disabled = true;
        lightStylesheet.disabled = false;
      }
    }
  }

  /**
   * Dispatch change event
   */
  dispatchChangeEvent({ type, value }) {
    const eventType = `${type}change`;
    const event = new CustomEvent(eventType, {
      detail: { value },
    });
    document.dispatchEvent(event);
  }

  /**
   * Set preference (public API)
   */
  setPreference({ type, value }) {
    if (type === "theme" && Object.values(THEMES).includes(value)) {
      this.applyPreference({ type: "theme", value });
    } else if (type === "layout" && Object.values(LAYOUTS).includes(value)) {
      this.applyPreference({ type: "layout", value });
    }
  }

  /**
   * Toggle between light and dark themes
   */
  toggleTheme() {
    if (this.currentSettings.theme === THEMES.AUTO) {
      this.setPreference({ type: "theme", value: THEMES.AUTO });
    } else {
      const newTheme =
        this.currentSettings.theme === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK;
      this.setPreference({ type: "theme", value: newTheme });
    }
  }

  toggleLayout() {
    const newLayout =
      this.currentSettings.layout === LAYOUTS.FLUID
        ? LAYOUTS.FIXED
        : LAYOUTS.FLUID;
    this.setPreference({ type: "layout", value: newLayout });
  }

  /**
   * Get current preference for a specific type
   */
  getPreference(type) {
    if (this.currentSettings[type]) {
      return this.currentSettings[type];
    }
    return null;
  }
}

// Create global appearance manager instance
let appearanceManager;

/**
 * Reset appearance manager (for testing)
 */
export const resetAppearanceManager = () => {
  appearanceManager = null;
};

/**
 * Initialize appearance manager
 */
export const initAppearanceManager = () => {
  if (!appearanceManager) {
    appearanceManager = new AppearanceManager();
  }
  return appearanceManager;
};

/**
 * Get appearance manager instance
 */
export const getAppearanceManager = () => {
  return appearanceManager || initAppearanceManager();
};

/**
 * Public API functions
 */
export const setPreference = ({ type, value }) =>
  getAppearanceManager().setPreference({ type, value });
export const toggleTheme = () => getAppearanceManager().toggleTheme();
export const toggleLayout = () => getAppearanceManager().toggleLayout();
export const getPreference = (type) =>
  getAppearanceManager().getPreference(type);

// Auto-initialize when DOM is ready (only if not already initialized)
document.addEventListener("DOMContentLoaded", () => {
  if (!appearanceManager) {
    initAppearanceManager();
  }
});
