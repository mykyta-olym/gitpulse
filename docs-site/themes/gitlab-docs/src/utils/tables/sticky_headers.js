const MOBILE_BREAKPOINT = 991;
const STICKY_OFFSET_ADJUSTMENT = -1; // Prevents overlap with header border
const BANNER_SELECTORS = ".l10n-sticky-banner";

// Cache for CSS variable values to avoid recalculation on every scroll
let offsetCache = {
  headerHeight: null,
  lastViewportWidth: null,
};

const toPixels = (value) => {
  if (!value) return 0;

  const normalized = value.trim();
  if (normalized.endsWith("px")) return Number.parseFloat(normalized) || 0;
  if (normalized.endsWith("rem")) {
    const rootFontSize = parseFloat(
      getComputedStyle(document.documentElement).fontSize,
    );
    return (Number.parseFloat(normalized) || 0) * rootFontSize;
  }
  return Number.parseFloat(normalized) || 0;
};

const hasBannersWithHeight = () => {
  return Array.from(document.querySelectorAll(BANNER_SELECTORS)).some(
    (banner) => banner.offsetHeight > 0,
  );
};

const invalidateOffsetCache = () => {
  offsetCache = {
    headerHeight: null,
    lastViewportWidth: null,
  };
};

const calculateActualOffset = () => {
  let offset = 0;

  // Add header height
  const header = document.querySelector(".header-wrapper");
  if (header) {
    offset += header.offsetHeight;
  }

  // Add banner heights
  const banners = document.querySelectorAll(BANNER_SELECTORS);
  banners.forEach((banner) => {
    if (banner.offsetHeight > 0) {
      offset += banner.offsetHeight;
    }
  });

  return offset + STICKY_OFFSET_ADJUSTMENT;
};

const getStickyTopOffset = () => {
  const currentViewportWidth = window.innerWidth;

  // Invalidate cache if viewport width changed (mobile/desktop breakpoint)
  if (offsetCache.lastViewportWidth !== currentViewportWidth) {
    invalidateOffsetCache();
    offsetCache.lastViewportWidth = currentViewportWidth;
  }

  // Return cached value if available
  if (offsetCache.headerHeight !== null) {
    return offsetCache.headerHeight;
  }

  // Calculate offset by measuring actual elements (header + banners)
  const actualOffset = calculateActualOffset();

  // If we found actual elements, use that
  if (actualOffset > STICKY_OFFSET_ADJUSTMENT) {
    offsetCache.headerHeight = actualOffset;
    return actualOffset;
  }

  // Fall back to CSS variable if no actual elements found
  const rootStyle = getComputedStyle(document.documentElement);
  const bannerOffset = rootStyle
    .getPropertyValue("--banner-scroll-offset")
    .trim();

  if (bannerOffset && hasBannersWithHeight()) {
    const offsetValue = toPixels(bannerOffset);
    if (offsetValue > 0) {
      offsetCache.headerHeight = offsetValue;
      return offsetValue;
    }
  }

  // Final fallback to header height CSS variable
  const headerVar =
    currentViewportWidth <= MOBILE_BREAKPOINT
      ? "--header-height"
      : "--header-height-lg";

  const headerHeight =
    toPixels(rootStyle.getPropertyValue(headerVar)) + STICKY_OFFSET_ADJUSTMENT;
  offsetCache.headerHeight = headerHeight;
  return headerHeight;
};

const syncHeaderWidths = (instance) => {
  const sourceCells = instance.header.querySelectorAll("th");
  const cloneCells = instance.cloneHeader.querySelectorAll("th");

  instance.cloneTable.style.width = `${instance.table.offsetWidth}px`;

  sourceCells.forEach((cell, index) => {
    const cloneCell = cloneCells[index];
    if (!cloneCell) return;
    cloneCell.style.width = `${cell.getBoundingClientRect().width}px`;
  });
};

const updateCloneState = (instance) => {
  const stickyTop = getStickyTopOffset();
  const tableRect = instance.table.getBoundingClientRect();
  const containerRect = instance.container.getBoundingClientRect();
  const headerHeight = instance.header.getBoundingClientRect().height;

  const shouldShow =
    tableRect.top <= stickyTop && tableRect.bottom - headerHeight > stickyTop;

  if (!shouldShow) {
    instance.cloneWrapper.classList.remove("is-visible");
    return;
  }

  instance.cloneWrapper.classList.add("is-visible");
  instance.cloneWrapper.style.top = `${stickyTop}px`;
  instance.cloneWrapper.style.left = `${containerRect.left}px`;
  instance.cloneWrapper.style.width = `${containerRect.width}px`;
  instance.cloneTable.style.transform = `translateX(${-instance.container.scrollLeft}px)`;
};

const createStickyHeaderClone = (tableContainer) => {
  const table = tableContainer.querySelector(".docs-table");
  const header = table?.querySelector("thead");
  if (!table || !header) return null;

  const cloneWrapper = document.createElement("div");
  cloneWrapper.className = "table-sticky-clone";
  cloneWrapper.setAttribute("aria-hidden", "true");

  const cloneTable = document.createElement("table");
  cloneTable.className = table.className;

  const cloneHeader = header.cloneNode(true);
  cloneTable.append(cloneHeader);
  cloneWrapper.append(cloneTable);
  document.body.append(cloneWrapper);

  // Delegate clicks to original links to preserve JS handlers attached to them
  const originalLinks = header.querySelectorAll("a");
  const clonedLinks = cloneHeader.querySelectorAll("a");
  clonedLinks.forEach((clonedLink, index) => {
    clonedLink.addEventListener("click", (e) => {
      const originalLink = originalLinks[index];
      if (!originalLink) return;

      const mouseEvent = new MouseEvent("click", {
        bubbles: true,
        cancelable: true,
        view: window,
        ctrlKey: e.ctrlKey,
        shiftKey: e.shiftKey,
        altKey: e.altKey,
        metaKey: e.metaKey,
      });

      originalLink.dispatchEvent(mouseEvent);
    });
  });

  const instance = {
    container: tableContainer,
    table,
    header,
    cloneWrapper,
    cloneTable,
    cloneHeader,
  };

  const refresh = () => {
    syncHeaderWidths(instance);
    updateCloneState(instance);
  };

  tableContainer.addEventListener("scroll", refresh, {
    passive: true,
  });

  const resizeObserver = new ResizeObserver(refresh);
  resizeObserver.observe(tableContainer);
  resizeObserver.observe(table);

  instance.refresh = refresh;
  instance.destroy = () => {
    tableContainer.removeEventListener("scroll", refresh);
    resizeObserver.disconnect();
    cloneWrapper.remove();
  };

  return instance;
};

export const resetOffsetCache = () => {
  offsetCache = {
    headerHeight: null,
    lastViewportWidth: null,
  };
};

export const initializeStickyTableHeaders = (
  selector = ".table-container:not(.condensed)",
) => {
  const containers = Array.from(document.querySelectorAll(selector));
  if (containers.length === 0) return;

  const instances = containers
    .map((container) => createStickyHeaderClone(container))
    .filter(Boolean);

  if (instances.length === 0) return;

  const refreshAll = () => {
    instances.forEach((instance) => instance.refresh());
  };

  // Debounce resize events to avoid excessive recalculations
  let resizeTimeout;
  const debouncedRefresh = () => {
    clearTimeout(resizeTimeout);
    invalidateOffsetCache();
    resizeTimeout = setTimeout(refreshAll, 150);
  };

  // Listen for CSS variable changes to invalidate cache
  const mutationObserver = new MutationObserver(() => {
    invalidateOffsetCache();
  });

  window.addEventListener("scroll", refreshAll, { passive: true });
  window.addEventListener("resize", debouncedRefresh);
  mutationObserver.observe(document.documentElement, { attributes: true });

  window.addEventListener(
    "pagehide",
    () => {
      clearTimeout(resizeTimeout);
      window.removeEventListener("scroll", refreshAll);
      window.removeEventListener("resize", debouncedRefresh);
      mutationObserver.disconnect();
      instances.forEach((instance) => instance.destroy());
    },
    { once: true },
  );

  refreshAll();
};
