import DOMPurify from "dompurify";
/**
 * Misc utilities for handling DOM elements
 */

// Store observer reference for cleanup
let bannerResizeObserver = null;

/**
 * Get HTML between two elements.
 *
 * @param {Element} el
 * @param {String} selector
 * @returns {String} HTML between the two given elements
 */
export const getNextUntil = (el, selector) => {
  const siblings = [];
  let next = el.nextElementSibling;

  while (next) {
    if (selector && next.matches(selector)) break;
    siblings.push(next.outerHTML);
    next = next.nextElementSibling;
  }

  return siblings.join("");
};

/**
 * Remove formatting (including escape characters) and boilerplate text from a page title
 *
 * We use this when we want to reference the title of a page,
 * without any extra formatting.
 */
export const cleanTitle = (htmlTitle) => {
  // Decode HTML title
  const textarea = document.createElement("textarea");
  textarea.innerHTML = htmlTitle;
  const decodedTitle = textarea.value;

  const formattedTitle = decodedTitle
    .replace(/\s*\|.*$/, "")
    .replaceAll("`", "")
    .trim();

  // Sanitize the properly decoded HTML
  const secureTitle = DOMPurify.sanitize(formattedTitle, {
    ALLOWED_TAGS: ["code", "em", "strong", "b", "i"],
    ALLOWED_ATTR: [],
  });

  return secureTitle;
};

/**
 * Gets the height of the sticky header
 * @param {string} unit - "px" or "rem"
 * @returns {number} Height of the header in the specified units
 */
export const getHeaderHeight = (unit = "px") => {
  const header = document.querySelector(".header-wrapper");
  const pxValue = header?.offsetHeight || 0;
  return unit === "px" ? pxValue : pxValue / 16; // 16px = 1 rem
};

export const getTocOffset = () => {
  let offset = 0;
  offset += getHeaderHeight("px") + 16; // 16px for margin
  const stickyBanner = document.querySelector(".l10n-sticky-banner");
  if (stickyBanner) {
    offset += stickyBanner.offsetHeight + 16; // 16px for margin
  }
  return offset;
};

/**
 * Updates banner scroll offset and handles anchor positioning
 * Ensures anchor links scroll to correct position accounting for all banners
 */
export const updateBannerScrollOffset = () => {
  const offset = getTocOffset();
  document.documentElement.style.setProperty(
    "--banner-scroll-offset",
    `${offset}px`,
  );

  // Re-scroll to anchor if present (fixes language switching with anchors)
  const { hash } = window.location;
  if (hash) {
    const target = document.querySelector(hash);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
};

/**
 * Clean up banner scroll offset observers
 */
export const cleanupBannerScrollOffset = () => {
  if (bannerResizeObserver) {
    bannerResizeObserver.disconnect();
    bannerResizeObserver = null;
  }
};

/**
 * Initializes banner scroll offset with proper timing and observers
 * Handles both initial setup and dynamic updates
 */
export const initializeBannerScrollOffset = () => {
  // Check if banners exist before running any banner-related code
  const banners = document.querySelectorAll(
    ".l10n-sticky-banner",
  );

  if (banners.length === 0) {
    return; // Exit early if no banners exist
  }

  // Update immediately
  updateBannerScrollOffset();

  // Set up ResizeObserver for dynamic updates
  bannerResizeObserver = new ResizeObserver(updateBannerScrollOffset);
  banners.forEach((banner) => bannerResizeObserver.observe(banner));

  // Clean up observer on page unload to prevent memory leaks
  window.addEventListener("beforeunload", cleanupBannerScrollOffset, {
    once: true,
  });
};
