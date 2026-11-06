/* JSON drop editor (components/forms.html `json_drop`).

   The editor itself is the drop target: a dropped or browsed file is read as
   text INTO the textarea, so there is a single source of truth for what gets
   submitted. The previous arrangement - a dashed upload box stacked on a
   separate textarea - kept two, and each cleared the other.

   Idempotent per wrapper; safe to call again after an htmx swap. */
GP.initJsonDrop = function (wrapper) {
  if (!wrapper || wrapper._gpJsonDropInit) return;
  const editor = wrapper.querySelector('.gl-json-drop-input');
  const fileInput = wrapper.querySelector('.gl-file-upload-input');
  if (!editor || !fileInput) return;
  wrapper._gpJsonDropInit = true;

  const surface = wrapper.querySelector('.gl-json-drop-surface');
  const chip = wrapper.querySelector('.gl-json-drop-file');
  const chipName = wrapper.querySelector('.gl-json-drop-filename');
  const clearBtn = wrapper.querySelector('.gl-json-drop-clear');
  const maxBytes = (parseFloat(wrapper.dataset.maxSize) || 10) * 1024 * 1024;
  const { t } = GP;
  let activeReader = null;

  function cancelRead() {
    if (activeReader) activeReader.abort();
    activeReader = null;
  }

  function showChip(name) {
    if (chipName) chipName.textContent = name;
    if (chip) chip.hidden = !name;
  }

  /* Drag state is reference-counted: dragenter/dragleave also fire for
     descendants (the textarea), so a plain toggle drops the highlight the
     moment the pointer crosses onto a child. */
  let dragDepth = 0;
  function setDragging(on) {
    wrapper.classList.toggle('is-dragging', on);
  }

  function loadFile(file) {
    cancelRead();
    if (!file) return;
    if (file.size > maxBytes) {
      GP.showToast(t('File is too large (max') + ' ' + Math.round(maxBytes / 1048576) + ' MB)', 'warning');
      return;
    }
    const reader = new FileReader();
    activeReader = reader;
    reader.onload = function (ev) {
      if (activeReader !== reader || !editor.isConnected) return;
      activeReader = null;
      const modal = wrapper.closest('.modal-backdrop');
      if (modal && (!modal.classList.contains('active') || modal.classList.contains('closing'))) return;
      editor.value = String(ev.target.result || '');
      showChip(file.name);
      editor.dispatchEvent(new Event('gp:user-edit', { bubbles: true }));
      // Let the page's existing validation/preview run - it already listens
      // for edits to this field, so file and paste share one code path.
      editor.dispatchEvent(new Event('input', { bubbles: true }));
      editor.dispatchEvent(new Event('change', { bubbles: true }));
    };
    reader.onerror = function () {
      if (activeReader !== reader || !editor.isConnected) return;
      activeReader = null;
      GP.showToast(t('Could not read that file'), 'warning');
    };
    reader.readAsText(file);
  }

  wrapper.resetJsonDrop = function () {
    cancelRead();
    editor.value = '';
    fileInput.value = '';
    showChip('');
    dragDepth = 0;
    setDragging(false);
  };

  /* "Upload file" is a <label for> the input: the browser opens the picker on
     its own, nothing here relays a click. */
  fileInput.addEventListener('change', function () {
    loadFile(this.files && this.files[0]);
    // Reset so re-picking the same filename fires `change` again.
    this.value = '';
  });

  clearBtn?.addEventListener('click', function () {
    wrapper.resetJsonDrop();
    editor.dispatchEvent(new Event('input', { bubbles: true }));
    editor.dispatchEvent(new Event('change', { bubbles: true }));
    editor.focus();
  });

  // Typing by hand means the content is no longer "that file".
  editor.addEventListener('input', function (ev) {
    if (ev.isTrusted) { cancelRead(); showChip(''); }
  });

  ['dragenter', 'dragover'].forEach(function (evt) {
    surface?.addEventListener(evt, function (ev) {
      if (!ev.dataTransfer || Array.prototype.indexOf.call(ev.dataTransfer.types || [], 'Files') === -1) return;
      ev.preventDefault();
      if (evt === 'dragenter') dragDepth++;
      setDragging(true);
    });
  });
  surface?.addEventListener('dragleave', function () {
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) setDragging(false);
  });
  surface?.addEventListener('drop', function (ev) {
    const files = ev.dataTransfer && ev.dataTransfer.files;
    if (!files || !files.length) return;
    ev.preventDefault();
    dragDepth = 0;
    setDragging(false);
    loadFile(files[0]);
  });
};

GP.initJsonDrops = function (root) {
  (root || document).querySelectorAll('[data-json-drop]').forEach(function (el) { GP.initJsonDrop(el); });
};
document.addEventListener('DOMContentLoaded', function () { GP.initJsonDrops(document); });
