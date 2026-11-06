import { setCookie, getCookie } from "../utils/cookies";
import { cleanTitle } from "../utils/dom";
import { isBaseUrl, getSearchParamsFromURL } from "./utils";

/**
 * Store recent page views in a cookie.
 */

// Number of links to include in history
export const RECENT_HISTORY_ITEMS = 4;

// Writes page URLs to a cookie
export const trackPageHistory = () => {
  let pageHistory = [];
  const currentPath = window.location.pathname;
  const currentHash = window.location.hash;
  const cookieValue = getCookie("pageHistory");

  if (cookieValue) {
    try {
      pageHistory = JSON.parse(cookieValue);
      if (!Array.isArray(pageHistory)) {
        pageHistory = [];
      }

      // Filter out any base URLs that might already be in history
      pageHistory = pageHistory.filter((item) => !isBaseUrl(item.path));
    } catch {
      pageHistory = [];
    }
  }

  // Check if search page
  const isSearchPage = currentPath.includes("/search/");

  let path = currentPath;
  let title = cleanTitle(document.title);

  if (isSearchPage) {
    const searchQuery = getSearchParamsFromURL().qParam;
    path = currentPath + window.location.search;
    title = searchQuery ? `Search: ${searchQuery}` : "Search";
    // Check if any search item already exists in history
    const existingSearchIndex = pageHistory.findIndex((item) =>
      item.path.includes("/search/"),
    );
    if (existingSearchIndex > -1) {
      pageHistory.splice(existingSearchIndex, 1);
    }
  } else {
    // If link has an anchor, then get the heading from that element
    if (currentHash) {
      path = currentPath + currentHash;
      try {
        const heading = document.querySelector(
          CSS.escape(currentHash.slice(1))
            ? `#${CSS.escape(currentHash.slice(1))}`
            : currentHash,
        );
        if (heading && heading.textContent) {
          const headingText = heading.textContent.trim();
          title = headingText;
        }
      } catch (error) {
        console.warn(`Failed to get heading for hash ${currentHash}: ${error}`);
      }
    }
    // Remove current page URL if it already exist
    const index = pageHistory.findIndex((item) => item.path === path);
    if (index > -1) {
      pageHistory.splice(index, 1);
    }
  }

  // Add the current page URL to the beginning of the history array
  pageHistory.unshift({
    path,
    title,
  });

  // Keep only the designated amount of pages in history
  if (pageHistory.length > RECENT_HISTORY_ITEMS) {
    pageHistory = pageHistory.slice(0, RECENT_HISTORY_ITEMS);
  }

  // Set a cookie with the history string
  try {
    const updatedCookieValue = JSON.stringify(pageHistory);
    setCookie("pageHistory", updatedCookieValue, 365);
  } catch {
    // Skip updating if data can't be stringified
  }
};
