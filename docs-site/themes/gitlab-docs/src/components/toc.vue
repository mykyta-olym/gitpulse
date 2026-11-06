<script>
import { getTocOffset, getHeaderHeight } from "../utils/dom";

const ROOT_MARGIN_DEFAULT = "-100px 0px -65% 0px"; // heading should not become active until it's within the top third of the viewport
const THRESHOLD = [0, 0.5, 1];
const SCROLL_TIMEOUT = 150;

export default {
  name: "TOC",
  props: {
    contentSelector: {
      type: String,
      default: ".docs-content",
      required: false,
      validator: (value) => typeof value === "string" && value.length > 0,
    },
    headingSelector: {
      type: String,
      default: "h2, h3, h4",
      required: false,
      validator: (value) =>
        typeof value === "string" && value.trim().length > 0,
    },
    ignoreSelector: {
      type: String,
      default: "h3.archive-item, .no_toc",
      required: false,
      validator: (value) =>
        typeof value === "string" && value.trim().length > 0,
    },
    scrollBehavior: {
      type: String,
      default: "smooth",
      required: false,
      validator: (value) => ["smooth", "instant"].includes(value),
    },
  },
  data() {
    return {
      activeHeading: null,
      headings: [],
      isUserScrolling: false,
      prefersReducedMotion: false,
      headerHeight: 0,
      userScrollTimeout: null,
      observer: null,
      headerResizeObserver: null,
      headingElements: [],
      scrollableContainer: null,
      scrollListeners: [],
      rafId: null,
      pendingSync: false,
    };
  },
  computed: {
    getScrollBehavior() {
      return this.prefersReducedMotion ? "instant" : this.scrollBehavior;
    },
  },
  watch: {
    activeHeading(newHeadingId) {
      if (newHeadingId) {
        this.$nextTick(() => this.scrollToActiveItem(newHeadingId));
      }
    },
  },
  mounted() {
    this.prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    this.updateHeaderHeight();
    this.setupResizeObserver();
    this.setupUserScrollDetection();
    window.addEventListener("hashchange", this.syncFromUrlHash);

    // Whenever any scrolling stops (user-initiated or programmatic), we want to sync the TOC
    if ("onscrollend" in window) {
      window.addEventListener("scrollend", this.handleScrollEnd);
    }

    this.$nextTick(() => {
      this.initializeTOC();
      this.scrollableContainer = this.getScrollableAncestor(this.$refs.toc);
      this.syncFromUrlHash();
    });
  },
  beforeUnmount() {
    this.observer?.disconnect();
    this.headerResizeObserver?.disconnect();
    this.cleanupUserScrollDetection();
    window.removeEventListener("hashchange", this.syncFromUrlHash);
    if ("onscrollend" in window) {
      window.removeEventListener("scrollend", this.handleScrollEnd);
    }
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
    }
  },
  methods: {
    // User scroll detection
    setupUserScrollDetection() {
      // Debounced scroll handler - only sets flags, actual sync happens in scheduled sync
      const handleScrollEvent = () => {
        this.isUserScrolling = true;
        this.pendingSync = true;
        this.setScrollTimeout();
        this.scheduleSync();
      };

      this.scrollListeners = [
        {
          event: "wheel",
          handler: handleScrollEvent,
          options: { passive: true },
        },
        {
          event: "touchmove",
          handler: handleScrollEvent,
          options: { passive: true },
        },
        {
          event: "touchend",
          handler: () => {
            this.setScrollTimeout();
          },
          options: { passive: true },
        },
        { event: "keydown", handler: this.handleKeyScroll },
      ];
      this.scrollListeners.forEach(({ event, handler, options }) => {
        window.addEventListener(event, handler, options);
      });
    },
    cleanupUserScrollDetection() {
      clearTimeout(this.userScrollTimeout);
      this.scrollListeners?.forEach(({ event, handler, options }) => {
        window.removeEventListener(event, handler, options);
      });
    },
    setScrollTimeout() {
      clearTimeout(this.userScrollTimeout);
      this.userScrollTimeout = setTimeout(() => {
        this.isUserScrolling = false;
        this.pendingSync = true;
        this.scheduleSync();
      }, SCROLL_TIMEOUT);
    },
    handleUserScrollStart() {
      this.isUserScrolling = true;
      this.pendingSync = true;
      this.setScrollTimeout();
      this.scheduleSync();
    },
    handleScrollEnd() {
      this.isUserScrolling = false;
      this.pendingSync = true;
      this.scheduleSync();
    },
    scheduleSync() {
      if (this.rafId) return; // Already scheduled
      this.rafId = requestAnimationFrame(() => {
        if (this.pendingSync) {
          this.pendingSync = false;
          this.syncActiveHeading();
        }
        this.rafId = null;
      });
    },
    syncActiveHeading() {
      const targetZone =
        this.headerHeight + (window.innerHeight - this.headerHeight) * 0.33; // Top third of main content

      // Find the heading closest to (but above) the target zone
      let activeId = null;
      for (const heading of this.headingElements) {
        const rect = heading.getBoundingClientRect();
        if (rect.top <= targetZone) {
          activeId = heading.id;
        } else {
          break; // Headings are in DOM order, so we can stop here
        }
      }

      // If no heading is above the target zone, default to the first heading if we're near the top of the page
      if (
        !activeId &&
        window.scrollY < window.innerHeight &&
        this.headingElements.length > 0
      ) {
        activeId = this.headingElements[0].id;
      }

      if (activeId && activeId !== this.activeHeading) {
        this.activeHeading = activeId;
      }
    },
    syncFromUrlHash() {
      const hash = window.location.hash.slice(1);

      if (hash && this.headingElements.some((el) => el.id === hash)) {
        this.activeHeading = hash;

        // Wait for DOM updates
        requestAnimationFrame(() => {
          this.scrollToActiveItem(hash);
        });
      }
    },
    handleKeyScroll(e) {
      const scrollKeys = [
        "ArrowDown",
        "ArrowUp",
        "PageDown",
        "PageUp",
        "Space",
        "Home",
        "End",
      ];
      if (scrollKeys.includes(e.code)) {
        this.isUserScrolling = true;
        this.pendingSync = true;
        this.setScrollTimeout();
        this.scheduleSync();
      }
    },
    // TOC initialization
    initializeTOC() {
      const contentElement = document.querySelector(this.contentSelector);
      if (!contentElement) {
        console.warn(`Content selector "${this.contentSelector}" not found.`);
        return;
      }
      const allHeadings = Array.from(
        contentElement.querySelectorAll(this.headingSelector),
      );
      this.headingElements = this.filterHeadingElements(allHeadings);
      this.headings = this.headingElements.map((el) => ({
        id: el.id,
        level: parseInt(el.tagName.charAt(1), 10),
        text: el.textContent.trim(),
      }));
      this.setupIntersectionObserver();
    },
    shouldExcludeElement(element, selector) {
      if (selector.includes(" ")) {
        const [parentSelector, childSelector] = selector.split(" ");
        return (
          element.matches(childSelector) && element.closest(parentSelector)
        );
      }
      return element.matches(selector);
    },
    filterHeadingElements(elements) {
      if (!this.ignoreSelector) return elements;

      const selectors = this.ignoreSelector
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      return elements.filter((el) =>
        selectors.every((selector) => {
          try {
            return !this.shouldExcludeElement(el, selector);
          } catch {
            return true;
          }
        }),
      );
    },
    // Intersection Observer
    setupIntersectionObserver() {
      this.observer = new IntersectionObserver(
        (entries) => {
          if (!this.isUserScrolling) return;

          const visibleEntries = entries.filter((e) => e.isIntersecting);
          if (visibleEntries.length > 0) {
            const mostVisible = this.getMostVisibleEntry(visibleEntries);
            if (mostVisible.target.id !== this.activeHeading) {
              this.activeHeading = mostVisible.target.id;
            }
          }
        },
        {
          root: null,
          rootMargin: ROOT_MARGIN_DEFAULT,
          threshold: THRESHOLD,
        },
      );

      this.headingElements.forEach((h) => this.observer.observe(h));
    },
    getMostVisibleEntry(entries) {
      return entries.reduce((prev, current) => {
        if (current.intersectionRatio > prev.intersectionRatio) return current;
        if (current.intersectionRatio === prev.intersectionRatio) {
          return current.boundingClientRect.top < prev.boundingClientRect.top
            ? current
            : prev;
        }
        return prev;
      });
    },
    // Scrolling management

    // Gets the scrollable ancestor of the TOC element, which is outside of this component
    getScrollableAncestor(element) {
      let parent = element?.parentElement;

      while (parent) {
        const style = getComputedStyle(parent);
        if (style.overflowY === "auto" || style.overflowY === "scroll") {
          return parent;
        }
        parent = parent.parentElement;
      }

      return null;
    },
    scrollToActiveItem(headingId) {
      const tocItem = this.$refs[`toc-item-${headingId}`]?.[0];
      if (!tocItem || !this.scrollableContainer) return;

      if (
        this.scrollableContainer.scrollHeight <=
        this.scrollableContainer.clientHeight
      )
        return;

      const rect = tocItem.getBoundingClientRect();
      const containerRect = this.scrollableContainer.getBoundingClientRect();

      const topBoundary = Math.max(this.headerHeight, containerRect.top);
      const isOutOfView =
        rect.bottom > containerRect.bottom || rect.top < topBoundary;

      if (isOutOfView) {
        tocItem.scrollIntoView({
          behavior: this.getScrollBehavior,
          block: "nearest",
        });
      }
    },
    handleTocClick(headingId) {
      const element = document.getElementById(headingId);
      if (!element) return;

      this.activeHeading = headingId;

      const offsetPosition =
        element.getBoundingClientRect().top +
        window.pageYOffset -
        getTocOffset();

      if (window.location.hash !== `#${headingId}`) {
        window.history.pushState(null, "", `#${headingId}`);
      }

      window.scrollTo({
        top: offsetPosition,
        behavior: this.getScrollBehavior,
      });
    },
    updateHeaderHeight() {
      this.headerHeight = getHeaderHeight();
    },
    // to handle dynamic header height changes
    setupResizeObserver() {
      const headerElement = document.querySelector(".header-wrapper");
      let resizeTimeout = null;
      if (window.ResizeObserver) {
        this.headerResizeObserver = new ResizeObserver(() => {
          // Debounce resize updates to avoid excessive recalculations
          clearTimeout(resizeTimeout);
          resizeTimeout = setTimeout(() => {
            this.updateHeaderHeight();
          }, 100);
        });
        if (headerElement && this.headerResizeObserver) {
          this.headerResizeObserver.observe(headerElement);
        }
      }
    },
  },
};
</script>

<template>
  <nav ref="toc" class="toc" :aria-label="$t('toc.tableOfContents')">
    <ul ref="tocList" class="toc-list gl-list-none">
      <li
        v-for="heading in headings"
        :key="heading.id"
        :ref="`toc-item-${heading.id}`"
        :class="[
          'toc-item',
          `toc-level-${heading.level}`,
          { 'toc-active': activeHeading === heading.id },
        ]"
      >
        <a
          :href="`#${heading.id}`"
          class="toc-link gl-text-gray-800"
          :aria-current="activeHeading === heading.id ? 'location' : null"
          @click.prevent="handleTocClick(heading.id)"
        >
          {{ heading.text }}
        </a>
      </li>
    </ul>
  </nav>
</template>
