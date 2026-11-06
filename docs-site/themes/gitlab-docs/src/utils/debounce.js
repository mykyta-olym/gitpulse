/**
 * delays the processing of the callback until after wait
 * @param {function} callback
 * @param {number} wait
 * @returns {function}
 */
export function debounce(callback, wait) {
  let timeoutId = null;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => {
      callback(...args);
    }, wait);
  };
}
