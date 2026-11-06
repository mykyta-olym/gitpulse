// CSS & JS used on every page
// vite will pull out the CSS into a separate file that we can load in the <head>
// imported on baseOf layout

import "./css/main.css";

import { i18n } from "../../../locales/i18n";
import { createVueInstance } from "./create_vue_instance";

import AppearanceToggle from "./components/appearance_toggle.vue";
import LanguageSelector from "./components/language_selector.vue";
import { activateKeyboardShortcuts } from "./features/keyboard_shortcuts";
import { activateLightbox } from "./features/lightbox";
import { activateMermaidZoom } from "./features/mermaid_zoom";
import { expandCollapse } from "./features/collapse";
import { trackPageHistory } from "./search/history";
import "./utils/appearance_manager";

document.addEventListener("DOMContentLoaded", async () => {
  i18n.locale = document.documentElement.lang;

  activateKeyboardShortcuts();
  activateLightbox();
  activateMermaidZoom();
  expandCollapse();
  trackPageHistory();

  // Appearance toggle
  const appearanceToggleContainer = document.querySelector(
    '[data-vue-app="appearance-toggle"]',
  );
  createVueInstance(appearanceToggleContainer, AppearanceToggle);

  // Language Selector
  //
  // Removing the versions menu next to this took the language selector with it,
  // which is why the theme's own control never appeared and a hand-written link
  // stood in for it. The versions menu stays gone - one version here - but this
  // is theirs, and it lists the same page in the other language.
  const languageContainer = document.querySelector(
    '[data-vue-app="language-selector"]',
  );

  if (window.languageData) {
    createVueInstance(languageContainer, LanguageSelector, {
      languages: window.languageData.languages,
      currentLang: window.languageData.currentLang,
    });
  }

  // Versions menu
});
