// Interactive behaviour for the `code-editable` shortcode.
//
// The shortcode renders `<PLACEHOLDER>` tokens as `.editable-var` spans inside a
// `.editable-codeblock-wrapper`. This module turns those spans into inline,
// editable fields:
//   - a reader clicks a placeholder and types their own value
//   - values persist for the browsing session (sessionStorage, scoped per page)
//   - placeholders sharing a name on the same page stay in sync
//
// Copy is handled elsewhere (codeblock_copy_button.vue) by reading the code block's
// live `textContent` at click time, so the reader's edits are what gets copied.

const STORAGE_PREFIX = "gl-docs-editable-code";

// Scope stored values per page so the same placeholder name on unrelated pages
// does not collide. Query string and hash are ignored.
function storageKey(name) {
  return `${STORAGE_PREFIX}:${window.location.pathname}:${name}`;
}

function readStored(name) {
  try {
    return window.sessionStorage.getItem(storageKey(name));
  } catch {
    return null;
  }
}

function writeStored(name, value) {
  try {
    window.sessionStorage.setItem(storageKey(name), value);
  } catch {
    // Storage can be unavailable (private mode, quota). Editing still works for
    // the current view; it just won't persist or sync across blocks.
  }
}

// Mirror a value onto every placeholder with the same name on the page.
function syncByName(name, value) {
  document
    .querySelectorAll(`.editable-var[data-var="${CSS.escape(name)}"]`)
    .forEach((el) => {
      if (el.textContent !== value) {
        el.textContent = value;
      }
    });
}

function selectContents(el) {
  const range = document.createRange();
  range.selectNodeContents(el);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
}

// Insert plain text at the caret, replacing any selection, via the
// Selection/Range API (the modern replacement for document.execCommand).
function insertTextAtCaret(text) {
  const selection = window.getSelection();
  if (!selection.rangeCount) return;
  const range = selection.getRangeAt(0);
  range.deleteContents();
  const node = document.createTextNode(text);
  range.insertNode(node);
  // Move the caret to the end of the inserted text.
  range.setStartAfter(node);
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
}

// Persist an edited value and mirror it to same-named placeholders.
function commit(el, name) {
  const value = el.textContent;
  writeStored(name, value);
  syncByName(name, value);
}

function initVar(el) {
  const name = el.dataset.var;
  if (!name) return;

  // Hydrate from a previously entered value.
  const stored = readStored(name);
  if (stored) {
    el.textContent = stored;
  }

  el.setAttribute("contenteditable", "true");
  el.setAttribute("spellcheck", "false");
  el.setAttribute("role", "textbox");
  el.setAttribute("tabindex", "0");
  el.setAttribute("aria-label", `Editable value: ${name}`);

  // Select the whole placeholder on focus so the first keystroke replaces it.
  el.addEventListener("focus", () => selectContents(el));

  el.addEventListener("input", () => commit(el, name));

  // Keep placeholders single-line: Enter confirms instead of inserting a break.
  el.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      el.blur();
    }
  });

  // Paste as plain, single-line text.
  el.addEventListener("paste", (event) => {
    event.preventDefault();
    const text = (event.clipboardData || window.clipboardData)
      .getData("text")
      .replace(/\s+/g, " ")
      .trim();
    insertTextAtCaret(text);
    commit(el, name);
  });
}

export function initEditableCodeblocks() {
  document
    .querySelectorAll(".editable-codeblock-wrapper .editable-var")
    .forEach(initVar);
}
