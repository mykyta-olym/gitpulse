<script>
import { GlButton, GlFormSelect } from "@gitlab/ui";
import { languages, defaultLocale } from "../../../../locales/index";
import MenuItem from "./sidebar_menu_item.vue";

// Mobile breakpoint (px)
const NAV_BREAKPOINT = 992;

export default {
  components: {
    GlButton,
    GlFormSelect,
    MenuItem,
  },
  props: {
    baseUrl: {
      type: String,
      required: true,
    },
    pageMetadata: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      menuItems: [],
      isCollapsed: false,
      isOverlayOpen: false,
      menuDataCache: {},
      currentMenuData: null,
      currentNormalizedPath: null,
      selectedTopic: "",
      topicMenu: [],
      // Use set to avoid duplicate URLs (some release notes nav items are shared URLs)
      duplicateUrls: new Set(),
    };
  },
  computed: {
    currentLocale() {
      return this.$i18n?.locale || defaultLocale;
    },
  },
  watch: {
    currentLocale: {
      immediate: true,
      async handler(newLocale) {
        await this.loadMenuDataForLocale(newLocale);
      },
    },
    currentMenuData: {
      immediate: true,
      handler() {
        if (this.currentMenuData) {
          const { menu } = this.processMenuData(this.currentMenuData);
          this.menuItems = Object.freeze(menu);
          if (!this.selectedTopic) {
            this.selectedTopic = this.menuItems[0].title;
          }
        }
      },
    },
  },
  mounted() {
    window.addEventListener("resize", this.handleResize);
    window.addEventListener("open-sidebar", this.toggleOverlay);
    this.selectedTopic = this.pageMetadata.trail[0]?.title || "";
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.handleResize);
    window.removeEventListener("open-sidebar", this.toggleOverlay);
  },
  methods: {
    async loadMenuDataForLocale(locale) {
      // Fall back to the site's default language, not a language this site
      // does not publish - that used to load another language's nav tree.
      const targetLocale = Object.keys(languages).includes(locale)
        ? locale
        : defaultLocale;

      // Check cache first
      if (this.menuDataCache[targetLocale]) {
        this.currentMenuData = this.menuDataCache[targetLocale];
        return;
      }

      // Load and cache the data
      try {
        // eslint-disable-next-line import/no-dynamic-require
        const module = await import(
          `../../../../data/${targetLocale}/navigation.yaml`
        );
        const menuData = module.default || module;

        // Cache it
        this.menuDataCache[targetLocale] = menuData;
        this.currentMenuData = menuData;
      } catch (error) {
        console.error(
          `Failed to load menu data for locale ${targetLocale}:`,
          error,
        );

        // Fall back to the default language if we failed to load another one
        if (targetLocale !== defaultLocale) {
          await this.loadMenuDataForLocale(defaultLocale);
        }
      }
    },
    toggleCollapse(action) {
      const container = document.querySelector(".template-single");
      if (action === "open" || action === "close") {
        this.isCollapsed = action === "close";
      } else {
        this.isCollapsed = !this.isCollapsed;
      }

      container.classList.toggle(
        "template-single-sidebar-collapsed",
        this.isCollapsed,
      );
    },
    toggleOverlay(action) {
      const actionValue = action.detail || action;
      this.isOverlayOpen = actionValue === "open";
      if (this.isOverlayOpen) {
        this.toggleCollapse("open");
      }
    },
    handleResize() {
      // Close the overlay if we've resized the window larger than the mobile breakpoint
      if (this.isOverlayOpen && window.innerWidth >= NAV_BREAKPOINT) {
        this.toggleOverlay("close");
      }
    },

    isActiveItem(item) {
      const { trail } = this.pageMetadata;
      // No active path if no trail is found
      if (!trail || trail.length === 0) return false;

      const activeItem = trail[trail.length - 1];
      const normalizedItemPath = this.buildPrefixedUrl(item.url).replace(
        this.baseUrl,
        "",
      );

      // The URL must always match the active page.
      if (normalizedItemPath !== activeItem.path) return false;

      // For patch releases, there will be repeated notes which means duplicate URLs.
      // So we cannot simply compare URL paths anymore as they won't be unique.
      // Instead, check if link carries  a `?nav=<title>` marker (set in processMenuItems),
      // so the copy that was navigated from is the one that highlights.
      if (this.duplicateUrls.has(item.url)) {
        const navParam = new URLSearchParams(window.location.search).get("nav");
        const targetTitle = navParam ?? activeItem.title;
        return item.title === targetTitle;
      }

      return true;
    },

    // Main entry point for processing menu data
    processMenuData(currMenu) {
      this.duplicateUrls = this.findDuplicateUrls(currMenu);
      const processedMenu = this.processMenuItems(currMenu);
      this.setInitialMenu(processedMenu);
      return { menu: processedMenu, isActiveTrail: false };
    },

    // Find URLs that appear more than once across the whole nav tree
    findDuplicateUrls(items, counts = new Map(), duplicates = new Set()) {
      for (const item of items) {
        if (item.url) {
          const count = (counts.get(item.url) || 0) + 1;
          counts.set(item.url, count);
          if (count > 1) {
            duplicates.add(item.url);
          }
        }
        if (Array.isArray(item.submenu)) {
          this.findDuplicateUrls(item.submenu, counts, duplicates);
        }
      }
      return duplicates;
    },

    // Recursively process menu items and their submenus
    processMenuItems(items, parentTrail = []) {
      return items.map((item) => {
        let prefixedUrl = this.buildPrefixedUrl(item.url);
        // Cross-listed links share a URL, so tag each with its nav title to
        // keep them distinct and let the clicked copy highlight after load.
        if (this.duplicateUrls.has(item.url)) {
          prefixedUrl += `?nav=${encodeURIComponent(item.title)}`;
        }
        const currentTrail = [
          ...parentTrail,
          { text: item.title, href: prefixedUrl },
        ];

        const isActive = this.isActiveItem(item);

        // Process submenu if it exists
        let processedSubmenu = item.submenu;
        let hasActiveInSubmenu = false;

        if (Array.isArray(item.submenu)) {
          processedSubmenu = this.processMenuItems(item.submenu, currentTrail);
          hasActiveInSubmenu = this.hasActiveTrail(processedSubmenu);
        }

        return {
          ...item,
          prefixedUrl,
          isActive,
          submenu: processedSubmenu,
          isActiveTrail: isActive || hasActiveInSubmenu,
        };
      });
    },
    // Build the prefixed URL for a menu item based on locale and base URL
    buildPrefixedUrl(url) {
      if (url.toLowerCase().startsWith("http")) {
        return url;
      }

      // Only a NON-default language carries a prefix: the default language owns
      // the un-prefixed URLs. Comparing against one hardcoded language prefixed
      // Slovak links that need no prefix and doubled the English one.
      const { locale } = this.$i18n || {};
      const localePrefix = locale && locale !== defaultLocale ? `${locale}/` : "";

      return `${this.baseUrl}${localePrefix}${url}`;
    },
    // Check if any item in the menu tree has an active trail
    hasActiveTrail(menuItems) {
      return menuItems.some((item) => item.isActiveTrail);
    },

    setInitialMenu(menu) {
      const topicMenu = menu.filter(
        (item) => item.title === this.selectedTopic,
      );
      this.topicMenu = topicMenu[0]?.submenu || [];
    },

    handleTopicChange(eventOrValue) {
      // get selected topic from event or metadata
      let selectedTopic;
      if (eventOrValue?.target) {
        selectedTopic = eventOrValue?.target?.value;
      } else {
        selectedTopic = eventOrValue;
      }
      this.selectedTopic = selectedTopic;

      // Get menu for selected topic
      const topicMenu = this.menuItems.filter(
        (item) => item.title === selectedTopic,
      );
      if (topicMenu.length > 0) {
        this.topicMenu = topicMenu[0]?.submenu || [];
        // If no submenu for the selected topic, redirect to topic url
        if (
          !topicMenu[0].submenu &&
          window.location.pathname !== topicMenu[0]?.prefixedUrl
        ) {
          window.location = topicMenu[0]?.prefixedUrl;
        }
      } else {
        this.topicMenu = [];
      }
    },
  },
};
</script>

<template>
  <div class="gl-pt-6">
    <transition name="fade">
      <div
        v-if="isOverlayOpen"
        class="lg:gl-hidden gl-block gl-z-2 modal-backdrop"
        aria-hidden="true"
        @click="toggleOverlay('close')"
      ></div>
    </transition>
    <aside
      class="global-nav-wrapper"
      :class="{
        'sidebar-collapsed': isCollapsed,
        'sidebar-overlay-open !gl-block': isOverlayOpen,
      }"
      :aria-label="$t('navBar.mainNavigation')"
    >
      <div class="global-nav">
        <div class="gl-flex gl-gap-4 gl-p-4 lg:gl-hidden">
          <gl-button
            :aria-label="$t('navBar.toggleSidebar')"
            category="tertiary"
            class="sidebar-toggle"
            data-testid="sidebar-toggle-btn-inner"
            icon="sidebar"
            role="button"
            size="small"
            @click="toggleOverlay('close')"
          />
          <label for="topics" class="gl-sr-only">{{
            $t("navBar.selectATopic")
          }}</label>
          <gl-form-select
            id="topics"
            v-model="selectedTopic"
            name="topics"
            class="topics"
            @change="handleTopicChange"
          >
            <option
              v-for="item in menuItems"
              :key="item.title"
              :value="item.title"
            >
              {{ item.title }}
            </option>
          </gl-form-select>
        </div>

        <nav aria-label="Main">
          <menu-item
            v-for="(item, index) in topicMenu"
            :key="index"
            :item="item"
            :level="1"
          />
        </nav>
      </div>
    </aside>
  </div>
</template>
