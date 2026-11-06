/**
 * Pre-paint greeting correction: runs synchronously before the browser
 * paints so the viewer's *local* time-of-day word replaces the server (UTC)
 * fallback with no visible flash.
 */
(function () {
  'use strict';
  const h1 = document.querySelector('.gl-home-title[data-greeting]');
  const w = h1 && h1.querySelector('[data-greeting-word]');
  if (w) {
    const hr = new Date().getHours();
    const key = (hr >= 5 && hr < 12) ? 'morning' : (hr >= 12 && hr < 18) ? 'afternoon' : 'evening';
    const word = h1.getAttribute('data-greeting-' + key);
    if (word && w.textContent !== word) w.textContent = word;
  }
  const dateSpan = document.querySelector('[data-greeting-date]');
  if (dateSpan) {
    const locale = document.documentElement.getAttribute('data-locale') || 'sk';
    let dateStr = new Date().toLocaleDateString(locale === 'sk' ? 'sk-SK' : 'en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    if (dateStr) {
      dateStr = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
    }
    dateSpan.textContent = dateStr;
  }
})();
