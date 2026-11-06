/* ============================================
   Cross-platform blob download
   ============================================
   iOS Safari and most mobile WebViews silently ignore the ``download``
   attribute on an anchor pointing at a ``blob:`` URL - the click does
   nothing, leaving the user stuck on the page with no feedback. Every
   export button on the site (PDF report, roster CSV, checks-config /
   full-config / student-detail JSON exports) used the same
   broken anchor pattern.

   This helper centralizes the download flow:
     - On desktop: standard hidden ``<a download>`` click (preserves the
       suggested filename).
     - On mobile: open the blob in a new tab so the OS PDF/text viewer
       handles it; fall back to same-tab navigation if popups are
       blocked.
     - The blob URL is revoked after a delay so mobile viewers have time
       to load it before the URL becomes invalid.

   Usage:
       GP.downloadBlob(blob, 'report.pdf');
*/
function _downloadBlob(blob, filename) {
  if (!blob) return;
  const url = URL.createObjectURL(blob);
  const isMobile = /iphone|ipad|ipod|android/i.test(navigator.userAgent || '');
  try {
    if (isMobile) {
      const win = window.open(url, '_blank');
      if (!win) {
        // Popup blocked - fall back so the user still gets the file.
        window.location.href = url;
      }
    } else {
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'download';
      a.rel = 'noopener';
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
  } finally {
    // Long revoke delay: mobile PDF viewers may still be fetching the
    // blob asynchronously after window.open returns.
    setTimeout(function () { URL.revokeObjectURL(url); }, 60000);
  }
}

GP.downloadBlob = _downloadBlob;
window.downloadBlob = _downloadBlob;
