/* ============================================
   Auto-hide scrollbar on touch / mobile / tablet
   Toggles .is-scrolling class on scrollable containers
   so CSS can reveal the scrollbar thumb and fade it out.
   ============================================ */
(function _initAutoHideScrollbar() {
  const IDLE_MS = 1200;
  const MQ = window.matchMedia('(max-width: 1024px), (hover: none)');
  if (!MQ.matches) return;

  const targets = document.querySelectorAll('.gl-page-content, .gl-home-main, .gl-sidebar-body');
  targets.forEach(el => {
    let timer = null;
    el.addEventListener('scroll', () => {
      if (!el.classList.contains('is-scrolling')) {
        el.classList.add('is-scrolling');
      }
      clearTimeout(timer);
      timer = setTimeout(() => el.classList.remove('is-scrolling'), IDLE_MS);
    }, { passive: true });
  });
})();
