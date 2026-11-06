/**
 * Shared markdown rendering and insertion helpers.
 * Used by support-form.js and support-ticket-detail.js.
 *
 * Provides:
 *   renderMarkdown(text) - lightweight Markdown -> HTML converter
 *   mdInsert(ta, before, after) - insert formatting around selection
 */

/* exported renderMarkdown, mdInsert */

;(function () {
'use strict';
const GP = window.GP;

function renderMarkdown(text) {
  if (!text) return '';
  /* 1. Fenced code blocks - protect from further parsing */
  const codeBlocks = [];
  let s = text.replace(/```([\s\S]*?)```/g, function(_m, code) {
    codeBlocks.push('<pre><code>' + GP.escapeHtml(code) + '</code></pre>');
    return '\x00CB' + (codeBlocks.length - 1) + '\x00';
  });
  /* 2. Inline code - protect from further parsing */
  const inlineCode = [];
  s = s.replace(/`([^`]+)`/g, function(_m, code) {
    inlineCode.push('<code>' + GP.escapeHtml(code) + '</code>');
    return '\x00IC' + (inlineCode.length - 1) + '\x00';
  });
  /* 3. Block-level elements (before HTML escaping, so > works for blockquotes) */
  s = s.replace(/^### (.+)$/gm, '\x00H3$1\x00H3E')
    .replace(/^## (.+)$/gm, '\x00H2$1\x00H2E')
    .replace(/^# (.+)$/gm, '\x00H1$1\x00H1E')
    .replace(/^> (.+)$/gm, '\x00BQ$1\x00BQE');
  /* 4. HTML-escape remaining text */
  s = GP.escapeHtml(s);
  /* 5. Restore block elements */
  s = s.replace(/\x00H3(.+?)\x00H3E/g, '<h3>$1</h3>')
    .replace(/\x00H2(.+?)\x00H2E/g, '<h2>$1</h2>')
    .replace(/\x00H1(.+?)\x00H1E/g, '<h1>$1</h1>')
    .replace(/\x00BQ(.+?)\x00BQE/g, '<blockquote>$1</blockquote>');
  /* 6. Inline formatting */
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>');
  /* 7. Lists */
  s = s.replace(/^- (.+)$/gm, '<li>$1</li>');
  /* 8a. Images ![alt](url) -> inline <img> preview. MUST run before links: the
     link regex below would otherwise match the [alt](url) part and turn an image
     into a plain link (the "attachment shows as 123!file.png instead of a
     thumbnail" bug). The thumbnail links to the full image (opens in a new tab).*/
  s = s.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, function(_m, alt, url) {
    const clean = url.replace(/[\t\n\r]/g, '');
    if (/^(javascript|data|vbscript):/i.test(clean)) return alt;
    const safe = encodeURI(decodeURI(url));
    return '<a href="' + safe + '" target="_blank" rel="noopener noreferrer" class="gh-md-img-link">'
      + '<img src="' + safe + '" alt="' + alt + '" class="gh-md-img" loading="lazy"></a>';
  });
  /* 8b. Links - allow any URL except javascript:/data:/vbscript: */
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(_m, label, url) {
    if (/^(javascript|data|vbscript):/i.test(url.replace(/[\t\n\r]/g, ''))) return label;
    return '<a href="' + encodeURI(decodeURI(url)) + '" target="_blank" rel="noopener noreferrer">' + label + '</a>';
  });
  s = s.replace(/((?:<li>.+<\/li>\n?)+)/g, '<ul>$1</ul>');
  /* 9. Restore code placeholders */
  s = s.replace(/\x00CB(\d+)\x00/g, function(_m, i) { return codeBlocks[parseInt(i, 10)]; });
  s = s.replace(/\x00IC(\d+)\x00/g, function(_m, i) { return inlineCode[parseInt(i, 10)]; });
  s = s.replace(/\n/g, '<br>');
  return s;
}

function mdInsert(taOrId, before, after) {
  const ta = typeof taOrId === 'string' ? document.getElementById(taOrId) : taOrId;
  if (!ta) return;
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  const selected = ta.value.substring(start, end) || 'text';
  // Block-level markers (heading '### ', quote '> ', list '- '/'1. ') only work
  // at the start of a line - Markdown renders them literally otherwise. If we're
  // inserting one mid-line, break to a new line first (like GitHub/GitLab do),
  // so clicking Heading after existing text produces a real heading, not
  // "text### text" on one line.
  const isBlock = /^(#{1,6}|>|\d+\.|[-*])\s$/.test(before);
  const prefix = isBlock && start > 0 && ta.value[start - 1] !== '\n' ? '\n' : '';
  const replacement = prefix + before + selected + (after || '');
  ta.setRangeText(replacement, start, end, 'select');
  ta.focus();
  ta.dispatchEvent(new Event('input', { bubbles: true }));
}

GP.renderMarkdownPreview = function (editor) {
  const rendered = renderMarkdown(editor.querySelector('.gh-md-textarea').value);
  editor.querySelector('.gh-md-preview').innerHTML = rendered.trim()
    ? rendered
    : '<p class="gh-md-preview-empty">' + GP.escapeHtml(GP.t('Nothing to preview.')) + '</p>';
};

function initMarkdownAttachmentSupport(root) {
  (root || document).querySelectorAll('.gh-md-editor').forEach(editor => {
    const button = editor.querySelector('[data-md-upload]');
    if (!button || editor._gpAttachmentInit) return;
    editor._gpAttachmentInit = true;
    const ta = editor.querySelector('.gh-md-textarea');
    const input = editor.querySelector('.gl-file-upload-input');
    const region = ta.form || editor;

    input.addEventListener('change', () => {
      uploadFiles(input.files);
      input.value = '';
    });
    ta.addEventListener('paste', event => {
      const files = event.clipboardData?.files;
      if (files?.length) { event.preventDefault(); uploadFiles(files); }
    });
    ta.addEventListener('dragover', event => {
      if (!event.dataTransfer?.types.includes('Files')) return;
      event.preventDefault();
      ta.classList.add('dragover');
    });
    ta.addEventListener('dragleave', () => ta.classList.remove('dragover'));
    ta.addEventListener('drop', event => {
      ta.classList.remove('dragover');
      const files = event.dataTransfer?.files;
      if (files?.length) { event.preventDefault(); uploadFiles(files); }
    });

    async function uploadFiles(files) {
      const batch = Array.from(files);
      if (!batch.length || !ta.isConnected || region.inert) return;
      if (batch.some(file => file.size > 50 * 1024 * 1024)) {
        GP.showToast(GP.t('File is too large. Max 50 MB'), 'warning');
        return;
      }
      let start = ta.selectionStart, end = ta.selectionEnd;
      const dirtyKey = 'markdown_upload:' + ta.id;
      const saved = await GP.refreshRegion({
        button, region, errorMessage: GP.t('Failed to upload attachment.'),
        load: async options => {
          GP.addDirtyReason(dirtyKey);
          try {
            for (const [index, file] of batch.entries()) {
              const data = new FormData();
              data.append('file', file);
              const uploaded = await GP.apiCall('/api/v1/support/upload', 'POST', data, { ...options, key: dirtyKey });
              if (!ta.isConnected) return false;
              const image = /\.(jpe?g|png|gif|webp|svg)$/i.test(file.name) ? '!' : '';
              const link = (index ? '\n' : '') + image + '[' + file.name + '](' + uploaded.url + ')';
              ta.setRangeText(link, start, end, 'end');
              start = end = ta.selectionEnd;
              ta.dispatchEvent(new Event('gp:user-edit', { bubbles: true }));
              ta.dispatchEvent(new Event('input', { bubbles: true }));
              if (editor.querySelector('.gh-md-preview').checkVisibility()) GP.renderMarkdownPreview(editor);
            }
          } finally {
            if (ta.isConnected) GP.clearDirtyReason(dirtyKey);
          }
        }
      });
      if (ta.isConnected && document.activeElement === document.body) (saved ? ta : input).focus();
    }
  });
}

// Page scripts and Alpine magics share these helpers across full and SPA visits.
window.renderMarkdown = renderMarkdown;
window.mdInsert = mdInsert;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => initMarkdownAttachmentSupport(document));
} else {
  initMarkdownAttachmentSupport(document);
}

document.body.addEventListener('htmx:afterSwap', (event) => {
  initMarkdownAttachmentSupport(event.target || document);
});
})();
