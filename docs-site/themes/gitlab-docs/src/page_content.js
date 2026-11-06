// JS and CSS for the page-content layout
import "./css/page-content.css";

import { i18n } from "../../../locales/i18n";
import BackToTopButton from "./components/back_to_top_button.vue";
import BreadcrumbNav from "./components/breadcrumb_nav.vue";
import CodeblockCopyButton from "./components/codeblock_copy_button.vue";
import CopyForLLM from "./components/copy_for_llm.vue";
import DocsBadges from "./components/docs_badge.vue";
import EditMenu from "./components/edit_menu.vue";
import GlossaryTooltip from "./components/glossary_tooltip.vue";
import OpenSidebar from "./components/open_sidebar.vue";
import SidebarMenu from "./components/sidebar_menu.vue";
import TabbedContent from "./components/tabbed_content.vue";
import TOC from "./components/toc.vue";

import { addHeaderPermalinks } from "./utils/header_permalinks";
import { assembleBreadcrumbs } from "./utils/breadcrumbs";
import { createVueInstance } from "./create_vue_instance";
import { docsBaseURL } from "./utils/environment";
import { initEditableCodeblocks } from "./utils/editable_code";
import { getNextUntil, initializeBannerScrollOffset } from "./utils/dom";
import { initializeStickyTableHeaders } from "./utils/tables/sticky_headers";

document.addEventListener("DOMContentLoaded", async () => {
  addHeaderPermalinks();
  initializeStickyTableHeaders();

  // Breadcrumb navigation
  const breadcrumbContainer = document.querySelector(
    '[data-vue-app="breadcrumb-nav"]',
  );
  createVueInstance(breadcrumbContainer, BreadcrumbNav, {
    items: assembleBreadcrumbs(i18n.locale),
  });

  // Sidebar menu (global navigation)
  const menuContainer = document.querySelector('[data-vue-app="sidebar-menu"]');
  createVueInstance(menuContainer, SidebarMenu, {
    baseUrl: docsBaseURL(),
    pageMetadata: window.pageMetadata,
  });

  const sidebarToggleContainer = document.querySelector(
    '[data-vue-app="open-sidebar"]',
  );
  createVueInstance(sidebarToggleContainer, OpenSidebar);

  // Right sidebar TOC
  const tocContainer = document.querySelector('[data-vue-app="toc"]');
  createVueInstance(tocContainer, TOC, {
    baseUrl: docsBaseURL(),
    pageMetadata: window.pageMetadata,
  });

  // Copy for LLM options
  const copyForLLMContainer = document.querySelector(
    '[data-vue-app="copy-for-llm"]',
  );
  if (copyForLLMContainer) {
    createVueInstance(copyForLLMContainer, CopyForLLM);
  }

  // Tabs
  const tabsetSelector = '[data-vue-app="docs-tabs"]';
  document.querySelectorAll(tabsetSelector).forEach((tabset) => {
    const tabTitles = [];
    const tabContents = [];

    tabset.querySelectorAll(".tab-title").forEach((tab) => {
      tabTitles.push(tab.innerText);
      tabContents.push(getNextUntil(tab, ".tab-title"));
    });

    createVueInstance(tabset, TabbedContent, {
      tabTitles,
      tabContents,
      responsive: false,
    });
  });

  // Clipboard copy for codeblocks. Run after tabs so copy buttons are mounted on the rendered tab DOM.
  // Editable code blocks are handled separately below (their copy reads live edits).
  document
    .querySelectorAll(".codeblock-wrapper:not(.editable-codeblock-wrapper)")
    .forEach((codeblock) => {
      const toolbarElement = codeblock.querySelector(
        '[data-vue-app="codeblock-toolbar"]',
      );
      createVueInstance(toolbarElement, CodeblockCopyButton, {
        codeContent: codeblock.querySelector("pre").textContent,
        codeLanguage: toolbarElement.getAttribute("data-code-language") || "",
      });
    });

  // Editable code blocks (code-editable shortcode): make <placeholder> tokens
  // editable, then mount a copy button that reads the live (edited) content.
  initEditableCodeblocks();
  document
    .querySelectorAll(".editable-codeblock-wrapper")
    .forEach((codeblock) => {
      const toolbarElement = codeblock.querySelector(
        '[data-vue-app="editable-codeblock-toolbar"]',
      );
      const pre = codeblock.querySelector("pre");
      createVueInstance(toolbarElement, CodeblockCopyButton, {
        getCodeContent: () => pre.textContent,
        codeLanguage: toolbarElement.getAttribute("data-code-language") || "",
      });
    });

  // Contribute/Solutions badge for h1 headers
  const badgeSpan = document.querySelector('[data-component="docs-badges"]');
  if (badgeSpan) {
    const badge = badgeSpan.querySelector("span");
    const badgeData = {
      text: badge.getAttribute("data-value"),
      hoverText: badge.getAttribute("data-hover-text"),
    };
    createVueInstance(badge, DocsBadges, {
      badgeData,
    });
  }

  // Edit menu
  const editMenuContainer = document.querySelector(
    '[data-vue-app="edit-menu"]',
  );
  createVueInstance(editMenuContainer, EditMenu);

  // Back to top button
  const backToTopButtonContainer = document.querySelector(
    '[data-vue-app="back-to-top-button"]',
  );
  createVueInstance(backToTopButtonContainer, BackToTopButton);

  // Glossary tooltips
  document
    .querySelectorAll('[data-vue-app="glossary-tooltip"]')
    .forEach((el) => {
      const props = {
        term: el.dataset.term,
        termId: el.dataset.id,
        definition: el.dataset.def,
        glossary: el.dataset.glossary,
      };
      createVueInstance(el, GlossaryTooltip, props);
    });

  // Since banners are uncommon, we lazy-load them to avoid unnecessary imports on every page load.
  async function createBanner(selector, bannerType, config) {
    const container = document.querySelector(selector);
    if (container) {
      const { default: DocsBanner } =
        await import("./components/docs_banner.vue");
      createVueInstance(container, DocsBanner, {
        bannerType,
        text: container?.innerHTML,
        ...config,
      });
    }
  }

  // Survey banner
  const bannerContainer = document.querySelector(
    '[data-vue-app="survey-banner"]',
  );
  if (bannerContainer) {
    await createBanner('[data-vue-app="survey-banner"]', "survey", {
      variant: "info",
    });
  }
  // l10n banner
  const l10nBannerContainer = document.querySelector(
    '[data-vue-app="l10n-banner"]',
  );
  if (l10nBannerContainer) {
    await createBanner('[data-vue-app="l10n-banner"]', "l10n", {
      variant: "info",
      dismissible: true,
    });
  }

  // Initialize banner scroll offset after Vue components render
  const banners = document.querySelectorAll(
    ".l10n-sticky-banner",
  );

  if (banners.length > 0) {
    initializeBannerScrollOffset();
  }
});
