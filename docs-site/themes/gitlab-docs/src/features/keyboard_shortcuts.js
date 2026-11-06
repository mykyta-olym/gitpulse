/**
 * Keyboard shortcuts configuration
 */
const SHORTCUTS = {
  search: {
    keys: ["/", "s"],
    action: () => {
      const input = document.querySelector(
        "[data-search-kbd] .gl-search-box-by-type-input, [data-search-kbd] .gl-search-box-by-click-input",
      );
      if (input) {
        input.focus();
      }
    },
  },
  ideEdit: {
    keys: ["."],
    action: () => {
      const link = document
        .querySelector('meta[name="gitlab_docs_web_ide_link"]')
        ?.getAttribute("content");

      if (link) {
        window.open(link, "_blank", "noopener,noreferrer");
      }
    },
  },
};

/**
 * Check if event should be ignored
 */
const shouldIgnoreEvent = (e) => {
  // Ignore if modifier keys are pressed
  if (e.ctrlKey || e.metaKey) return true;

  // Ignore if focus is on form elements
  if (/^(?:input|textarea|select|button)$/i.test(e.target.tagName)) return true;

  // Ignore if focus is on an editable element (e.g. editable code placeholders)
  if (e.target.isContentEditable) return true;

  return false;
};

/**
 * Handle keyboard shortcuts
 */
const handleKeyboardShortcut = (e) => {
  if (shouldIgnoreEvent(e)) return;

  for (const shortcut of Object.values(SHORTCUTS)) {
    if (shortcut.keys.includes(e.key)) {
      e.preventDefault();
      shortcut.action();
      break; // Stop after first match
    }
  }
};

/**
 * Activate keyboard shortcuts
 */
export const activateKeyboardShortcuts = () => {
  document.addEventListener("keydown", handleKeyboardShortcut);
};
