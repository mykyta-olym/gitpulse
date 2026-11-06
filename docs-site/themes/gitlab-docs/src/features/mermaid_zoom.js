/**
 * Zoom and pan for Mermaid diagrams: an inline viewer plus a fullscreen overlay.
 *
 * We enhance on the `mermaid:rendered` event (dispatched by baseof.html once
 * `mermaid.run()` resolves).
 */
import { i18n } from "../../../../locales/i18n";

// The GitLab UI sprite sits next to the Vite bundle; derive its URL from the
// running module so it stays correct under path-prefixed builds/review apps.
const ICON_SPRITE = import.meta.url.replace(
  /\/vite\/[^/]*$/,
  "/gitlab_ui/svgs-latest/icons.svg",
);

const MIN_SCALE = 0.5;
const MAX_SCALE = 8;
const ZOOM_FACTOR = 1.2;
const PAN_STEP = 40;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

const iconMarkup = (name) =>
  `<svg class="gl-icon s16" aria-hidden="true"><use href="${ICON_SPRITE}#${name}"></use></svg>`;

const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const midpoint = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });

/** Pan/zoom transforms for a target within a viewport (mouse, wheel, touch). */
class PanZoom {
  constructor(viewport, target, { wheelNeedsModifier = false } = {}) {
    this.viewport = viewport;
    this.target = target;
    this.wheelNeedsModifier = wheelNeedsModifier;

    this.scale = 1;
    this.x = 0;
    this.y = 0;

    // Active pointers keyed by id, so we can tell a drag from a pinch.
    this.pointers = new Map();
    this.pinchDistance = 0;
    this.pinchCenter = { x: 0, y: 0 };

    this.target.style.transformOrigin = "0 0";

    this.handlers = {
      wheel: this.onWheel.bind(this),
      down: this.onPointerDown.bind(this),
      move: this.onPointerMove.bind(this),
      up: this.onPointerUp.bind(this),
    };
    viewport.addEventListener("wheel", this.handlers.wheel, { passive: false });
    viewport.addEventListener("pointerdown", this.handlers.down);
    viewport.addEventListener("pointermove", this.handlers.move);
    viewport.addEventListener("pointerup", this.handlers.up);
    viewport.addEventListener("pointercancel", this.handlers.up);

    this.apply();
  }

  apply() {
    this.target.style.transform = `translate(${this.x}px, ${this.y}px) scale(${this.scale})`;
  }

  reset() {
    this.scale = 1;
    this.x = 0;
    this.y = 0;
    this.apply();
  }

  localPoint(clientX, clientY) {
    const rect = this.viewport.getBoundingClientRect();
    return { x: clientX - rect.left, y: clientY - rect.top };
  }

  // Zoom by a factor while keeping the given viewport-relative point fixed.
  zoomToPoint(factor, px, py) {
    const newScale = clamp(this.scale * factor, MIN_SCALE, MAX_SCALE);
    const ratio = newScale / this.scale;
    this.x = px - (px - this.x) * ratio;
    this.y = py - (py - this.y) * ratio;
    this.scale = newScale;
    this.apply();
  }

  zoomBy(factor) {
    const rect = this.viewport.getBoundingClientRect();
    this.zoomToPoint(factor, rect.width / 2, rect.height / 2);
  }

  panBy(dx, dy) {
    this.x += dx;
    this.y += dy;
    this.apply();
  }

  fitToViewport() {
    this.reset();
    const vp = this.viewport.getBoundingClientRect();
    const box = this.target.getBoundingClientRect();
    if (!box.width || !box.height) return;
    this.scale = clamp(
      Math.min(vp.width / box.width, vp.height / box.height, 1),
      MIN_SCALE,
      MAX_SCALE,
    );
    this.x = (vp.width - box.width * this.scale) / 2;
    this.y = (vp.height - box.height * this.scale) / 2;
    this.apply();
  }

  onWheel(e) {
    // In the inline viewer, only zoom with a modifier so the page still scrolls.
    if (this.wheelNeedsModifier && !(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    const point = this.localPoint(e.clientX, e.clientY);
    const factor = e.deltaY < 0 ? ZOOM_FACTOR : 1 / ZOOM_FACTOR;
    this.zoomToPoint(factor, point.x, point.y);
  }

  onPointerDown(e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    this.viewport.setPointerCapture(e.pointerId);
    this.pointers.set(e.pointerId, this.localPoint(e.clientX, e.clientY));
    this.viewport.classList.add("is-grabbing");
    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      this.pinchDistance = distance(a, b);
      this.pinchCenter = midpoint(a, b);
    }
  }

  onPointerMove(e) {
    if (!this.pointers.has(e.pointerId)) return;
    const previous = this.pointers.get(e.pointerId);
    const current = this.localPoint(e.clientX, e.clientY);
    this.pointers.set(e.pointerId, current);

    if (this.pointers.size === 1) {
      this.panBy(current.x - previous.x, current.y - previous.y);
      return;
    }

    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      const dist = distance(a, b);
      const center = midpoint(a, b);
      if (this.pinchDistance > 0) {
        this.zoomToPoint(dist / this.pinchDistance, center.x, center.y);
      }
      this.panBy(center.x - this.pinchCenter.x, center.y - this.pinchCenter.y);
      this.pinchDistance = dist;
      this.pinchCenter = center;
    }
  }

  onPointerUp(e) {
    if (!this.pointers.has(e.pointerId)) return;
    this.pointers.delete(e.pointerId);
    try {
      this.viewport.releasePointerCapture(e.pointerId);
    } catch {
      // Pointer may already be released.
    }
    if (this.pointers.size < 2) this.pinchDistance = 0;
    if (this.pointers.size === 0) {
      this.viewport.classList.remove("is-grabbing");
    }
  }

  destroy() {
    const { wheel, down, move, up } = this.handlers;
    this.viewport.removeEventListener("wheel", wheel);
    this.viewport.removeEventListener("pointerdown", down);
    this.viewport.removeEventListener("pointermove", move);
    this.viewport.removeEventListener("pointerup", up);
    this.viewport.removeEventListener("pointercancel", up);
  }
}

const buildToolbar = (controller, { onFullscreen, onClose } = {}) => {
  const toolbar = document.createElement("div");
  toolbar.className = "mermaid-zoom__toolbar";

  const addButton = (icon, labelKey, onClick) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mermaid-zoom__btn";
    button.innerHTML = iconMarkup(icon);
    const label = i18n.t(`mermaidZoom.${labelKey}`);
    button.setAttribute("aria-label", label);
    button.title = label;
    button.addEventListener("click", () => onClick());
    toolbar.appendChild(button);
  };

  addButton("search-minus", "zoomOut", () =>
    controller.zoomBy(1 / ZOOM_FACTOR),
  );
  addButton("redo", "reset", () => controller.reset());
  addButton("search-plus", "zoomIn", () => controller.zoomBy(ZOOM_FACTOR));
  if (onFullscreen) addButton("maximize", "fullscreen", onFullscreen);
  if (onClose) addButton("close", "close", onClose);

  return toolbar;
};

const attachKeyboard = (element, controller) => {
  element.addEventListener("keydown", (e) => {
    switch (e.key) {
      case "+":
      case "=":
        controller.zoomBy(ZOOM_FACTOR);
        break;
      case "-":
      case "_":
        controller.zoomBy(1 / ZOOM_FACTOR);
        break;
      case "0":
        controller.reset();
        break;
      case "ArrowUp":
        controller.panBy(0, PAN_STEP);
        break;
      case "ArrowDown":
        controller.panBy(0, -PAN_STEP);
        break;
      case "ArrowLeft":
        controller.panBy(PAN_STEP, 0);
        break;
      case "ArrowRight":
        controller.panBy(-PAN_STEP, 0);
        break;
      default:
        return;
    }
    e.preventDefault();
  });
};

// A single overlay element is created lazily and reused for every diagram.
let overlay = null;
let overlayController = null;
let previouslyFocused = null;

const overlayIsOpen = () => overlay?.classList.contains("is-open");

const closeOverlay = () => {
  if (!overlayIsOpen()) return;
  overlay.classList.remove("is-open");
  overlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("mermaid-zoom-overlay-open");

  overlayController?.destroy();
  overlayController = null;
  overlay.querySelector(".mermaid-zoom-overlay__canvas").replaceChildren();
  overlay.querySelector(".mermaid-zoom__toolbar")?.remove();

  if (previouslyFocused) {
    previouslyFocused.focus();
    previouslyFocused = null;
  }
};

// Trap focus on the toolbar buttons and close on Escape (like the lightbox).
const onOverlayKeydown = (e) => {
  if (!overlayIsOpen()) return;

  if (e.key === "Escape") {
    e.preventDefault();
    closeOverlay();
    return;
  }

  if (e.key === "Tab") {
    const buttons = [...overlay.querySelectorAll("button")];
    if (!buttons.length) return;
    const first = buttons[0];
    const last = buttons[buttons.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
};

const createOverlay = () => {
  overlay = document.createElement("div");
  overlay.className = "mermaid-zoom-overlay";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-label", i18n.t("mermaidZoom.overlayLabel"));
  overlay.setAttribute("aria-hidden", "true");

  const canvas = document.createElement("div");
  canvas.className = "mermaid-zoom-overlay__canvas";
  canvas.tabIndex = -1;

  overlay.appendChild(canvas);
  document.body.appendChild(overlay);

  document.addEventListener("keydown", onOverlayKeydown);

  return overlay;
};

const openOverlay = (sourceSvg) => {
  if (!overlay || !overlay.isConnected) createOverlay();

  const canvas = overlay.querySelector(".mermaid-zoom-overlay__canvas");
  const clone = sourceSvg.cloneNode(true);
  canvas.replaceChildren(clone);

  overlayController = new PanZoom(canvas, clone, { wheelNeedsModifier: false });
  attachKeyboard(canvas, overlayController);
  overlay.appendChild(
    buildToolbar(overlayController, { onClose: closeOverlay }),
  );

  previouslyFocused = document.activeElement;
  overlay.classList.add("is-open");
  overlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("mermaid-zoom-overlay-open");
  canvas.focus();

  // Fit once the browser has laid out the cloned SVG.
  requestAnimationFrame(() => overlayController?.fitToViewport());
};

// Enhance the diagram's <pre> in place; CSS already gives it the viewer box,
// so this only adds interactivity and the toolbar (no layout shift).
const enhanceDiagram = (diagram) => {
  if (diagram.dataset.zoomEnhanced) return;
  const svg = diagram.querySelector("svg");
  if (!svg) return;
  diagram.dataset.zoomEnhanced = "true";

  diagram.classList.add("mermaid-zoom");
  diagram.setAttribute("role", "application");
  diagram.setAttribute("aria-label", i18n.t("mermaidZoom.regionLabel"));
  if (!diagram.hasAttribute("tabindex")) diagram.tabIndex = 0;

  const controller = new PanZoom(diagram, svg, { wheelNeedsModifier: true });
  attachKeyboard(diagram, controller);

  const toolbar = buildToolbar(controller, {
    onFullscreen: () => openOverlay(svg),
  });
  // The toolbar sits inside the viewer, so don't let its presses start a pan.
  toolbar.addEventListener("pointerdown", (e) => e.stopPropagation());
  diagram.appendChild(toolbar);
};

// Enhance diagrams lazily as they approach the viewport.
let observer = null;

const getObserver = () => {
  if (observer) return observer;
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        enhanceDiagram(entry.target);
      });
    },
    { rootMargin: "300px 0px" },
  );
  return observer;
};

const observeDiagrams = () => {
  const diagrams = document.querySelectorAll(
    "pre.mermaid[data-processed='true']",
  );
  if (!("IntersectionObserver" in window)) {
    diagrams.forEach((diagram) => enhanceDiagram(diagram));
    return;
  }
  const obs = getObserver();
  diagrams.forEach((diagram) => {
    if (!diagram.dataset.zoomEnhanced) obs.observe(diagram);
  });
};

/** Enhance the page's Mermaid diagrams; a no-op when there are none. */
export const activateMermaidZoom = () => {
  document.addEventListener("mermaid:rendered", observeDiagrams);
  observeDiagrams();
};
