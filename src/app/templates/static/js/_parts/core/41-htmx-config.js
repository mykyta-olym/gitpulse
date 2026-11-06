/* -- HTMX global config --
   Default timeout = 0 (no timeout) means a stuck request hangs forever
   and the user is left staring at a loader until they manually refresh.
   Cap at 90s so slow / dead-ended requests fire htmx:timeout (handled by
   the lazy-content auto-retry below) and the user sees an actionable
   error state instead of an indefinite spinner. */
(function _htmxConfigInit() {
  function _apply() {
    if (window.htmx && htmx.config) {
      htmx.config.timeout = 90000;
      /* The SPA afterSwap handler below owns every <script> in the swapped
         content: it pulls the page bundles out of #main-content and loads them
         in order itself. htmx's own script pass runs AFTER that, at settle, on
         the same top-level nodes - and re-inserting a script whose parent is
         already gone threw "Cannot read properties of null (reading
         'insertBefore')" on every navigation to a page that ships its bundle
         inside the content. htmx has nothing left to execute; tell it so. */
      htmx.config.allowScriptTags = false;
      /* No attribute settling. After a swap htmx gives every element whose id
         also existed on the page before its OLD class and style for ~20ms and
         only then the new ones - so CSS transitions can run from old to new.
         Nothing here uses that (motion is GSAP's), and what it did instead:
         a selected tab, filter or period box wore its old "not selected" class
         first and a transition brought the highlight back - "the selected
         filter blinks while the page loads" - and a row the table filter hid
         right after the swap was shown again when the settle put back the
         class the server sent. */
      htmx.config.attributesToSettle = [];
    }
  }
  _apply();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _apply, { once: true });
  }
})();
