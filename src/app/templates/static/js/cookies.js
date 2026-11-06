/**
 * Cookie Utility - GitLab js-cookie Pattern
 *
 * Implements the same API as GitLab's cookie wrapper:
 *   import Cookies from '~/lib/utils/cookies';
 *   Cookies.set(name, value, { expires, sameSite, secure });
 *   Cookies.get(name);
 *   Cookies.remove(name);
 *
 * GitLab source: app/assets/javascripts/lib/utils/cookies.js
 * Based on: https://github.com/js-cookie/js-cookie (RFC 6265)
 *
 * Zero dependencies. Works on all pages (login, error, dashboard).
 */
(function (global) {
  'use strict';

  let initial = {};
  try { initial = JSON.parse(document.documentElement.dataset.preferenceCookies || '{}'); }
  catch (_) { /* standalone pages may have no server preferences */ }

  function getInitial(name) {
    try { return initial[name] ? decode(initial[name]) : undefined; }
    catch (_) { return undefined; }
  }

  /* -- RFC 6265 helpers -- */
  function encode(name) {
    return encodeURIComponent(name)
      .replace(/%(2[346B]|5E|60|7C)/g, decodeURIComponent);
  }
  function encodeValue(value) {
    return encodeURIComponent(value)
      .replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g, decodeURIComponent);
  }
  function decode(s) {
    return s.replace(/(%[\dA-F]{2})+/gi, decodeURIComponent);
  }

  function init(defaultAttributes) {
    async function setAsync(name, value, attributes) {
      const attrs = Object.assign({}, defaultAttributes, attributes);
      if (global.cookieStore) {
        const options = { name: encode(name), value: encodeValue(String(value)),
          path: attrs.path, sameSite: String(attrs.sameSite || 'Lax').toLowerCase() };
        if (attrs.domain) options.domain = attrs.domain;
        if (typeof attrs.expires === 'number') options.expires = Date.now() + attrs.expires * 864e5;
        else if (attrs.expires) options.expires = attrs.expires.getTime();
        try {
          await global.cookieStore.set(options);
          return;
        } catch (_) { /* older or restricted browsers use the standard fallback */ }
      }
      set(name, value, attributes);
    }
    /**
     * Set a cookie.
     * @param {string} name
     * @param {string} value
     * @param {Object} [attributes] - { expires, path, domain, secure, sameSite }
     */
    function set(name, value, attributes) {
      attributes = Object.assign({}, defaultAttributes, attributes);

      if (typeof attributes.expires === 'number') {
        attributes.expires = new Date(Date.now() + attributes.expires * 864e5);
      }
      if (attributes.expires) {
        attributes.expires = attributes.expires.toUTCString();
      }

      let stringifiedAttributes = '';
      for (const key in attributes) {
        if (!attributes[key] && attributes[key] !== 0) continue;
        stringifiedAttributes += '; ' + key;
        if (attributes[key] === true) continue;
        // Semicolons in value need no special handling per RFC 6265
        stringifiedAttributes += '=' + String(attributes[key]).split(';')[0];
      }

      document.cookie = encode(name) + '=' + encodeValue(String(value)) + stringifiedAttributes;
    }

    /**
     * Get a cookie by name, or get all cookies as an object.
     * @param {string} [name]
     * @returns {string|Object|undefined}
     */
    function get(name) {
      const cookies = document.cookie ? document.cookie.split('; ') : [];
      const jar = {};
      for (let i = 0; i < cookies.length; i++) {
        const parts = cookies[i].split('=');
        const foundName = decode(parts[0]);
        const foundValue = parts.slice(1).join('=');
        try {
          const decodedValue = decode(foundValue);
          jar[foundName] = decodedValue;
          if (name === foundName) {
            return decodedValue;
          }
        } catch (e) {
          // ignore malformed cookies
        }
      }
      return name === undefined ? jar : undefined;
    }

    /**
     * Remove a cookie.
     * @param {string} name
     * @param {Object} [attributes]
     */
    function remove(name, attributes) {
      set(name, '', Object.assign({}, attributes, { expires: -1 }));
    }

    return {
      set: set,
      setAsync: setAsync,
      getInitial: getInitial,
      get: get,
      remove: remove,
      withAttributes: function (attrs) {
        return init(Object.assign({}, defaultAttributes, attrs));
      }
    };
  }

  // GitLab default: path '/', SameSite 'Lax'
  const Cookies = init({ path: '/', sameSite: 'Lax' });

  // Expose globally (like GitLab's window.Cookies)
  global.Cookies = Cookies;

})(typeof window !== 'undefined' ? window : this);
