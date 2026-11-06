/**
 * Image lightbox
 *
 * Content images are wrapped in `<a class="js-lightbox">` by the image render
 * hook (themes/gitlab-docs/layouts/_markup/render-image.html). Instead of
 * following that link to open the image in a new tab, this feature intercepts
 * the click and displays the image in an in-page overlay.
 *
 * The overlay is a single, lazily-created element reused for every image. It is
 * accessible: it traps focus while open, closes on Escape or backdrop click,
 * and restores focus to the triggering link when closed.
 */
import { i18n } from "../../../../locales/i18n";

// The element that had focus before the lightbox opened, so we can restore it.
let previouslyFocused = null;
let overlay = null;

const isOpen = () => overlay?.classList.contains("is-open");

/**
 * Move focus back to the element that opened the lightbox and close the overlay.
 */
const close = () => {
  if (!overlay || !isOpen()) return;

  overlay.classList.remove("is-open");
  overlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("lightbox-open");

  // Clear the image so it isn't announced by screen readers while hidden.
  overlay.querySelector(".lightbox-image").removeAttribute("src");
  overlay.querySelector(".lightbox-image").removeAttribute("alt");

  if (previouslyFocused) {
    previouslyFocused.focus();
    previouslyFocused = null;
  }
};

/**
 * Keep keyboard focus inside the overlay while it is open and close on Escape.
 */
const handleKeydown = (e) => {
  if (!isOpen()) return;

  if (e.key === "Escape") {
    e.preventDefault();
    close();
    return;
  }

  // Only the close button is focusable, so Tab should never leave the overlay.
  if (e.key === "Tab") {
    e.preventDefault();
    overlay.querySelector(".lightbox-close").focus();
  }
};

/**
 * Build the reusable overlay element and wire up its dismissal handlers.
 */
const createOverlay = () => {
  overlay = document.createElement("div");
  overlay.className = "lightbox-overlay";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-label", i18n.t("lightbox.label"));
  overlay.setAttribute("aria-hidden", "true");

  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.className = "lightbox-close";
  closeButton.setAttribute("aria-label", i18n.t("lightbox.close"));
  closeButton.textContent = "×"; // × multiplication sign

  const image = document.createElement("img");
  image.className = "lightbox-image";

  overlay.append(closeButton, image);
  document.body.appendChild(overlay);

  // Clicking the backdrop (but not the image) closes the lightbox.
  overlay.addEventListener("click", (e) => {
    if (e.target === image) return;
    close();
  });

  document.addEventListener("keydown", handleKeydown);

  return overlay;
};

/**
 * Display the given image source and alt text in the overlay.
 */
const open = (src, alt) => {
  if (!overlay || !overlay.isConnected) createOverlay();

  const image = overlay.querySelector(".lightbox-image");
  image.src = src;
  image.alt = alt || "";

  previouslyFocused = document.activeElement;
  overlay.classList.add("is-open");
  overlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("lightbox-open");
  overlay.querySelector(".lightbox-close").focus();
};

/**
 * Attach lightbox behavior to every content image link on the page.
 */
export const activateLightbox = () => {
  const triggers = document.querySelectorAll("a.js-lightbox");

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      // Respect modifier clicks (open in new tab/window) and the no-JS fallback.
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;

      const img = trigger.querySelector("img");
      if (!img) return;

      e.preventDefault();
      open(trigger.getAttribute("href"), img.getAttribute("alt"));
    });
  });
};
