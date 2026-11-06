/* Global UI i18n (phrase catalog + DOM translation). */
(function initI18n() {
  window.GP = window.GP || {};
  const GP = window.GP;

  const ATTRIBUTES = ['placeholder', 'title', 'aria-label', 'data-tooltip', 'data-tippy-content'];
  const NUMBER_RE = /\b\d+(?:[.,]\d+)?\b/g;

  function normalizeLocale(value) {
    if (!value) {
      return null;
    }
    const raw = String(value).trim().toLowerCase();
    if (!raw) {
      return null;
    }
    const base = raw.split('-')[0].split('_')[0];
    return base || null;
  }

  function normalizeText(value) {
    return String(value || '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function tokenizeNumbers(value) {
    const captured = [];
    const tokenized = String(value || '').replace(NUMBER_RE, function (match) {
      const idx = captured.length;
      captured.push(match);
      return '__N' + idx + '__';
    });
    return { tokenized: tokenized, values: captured };
  }

  function restoreNumbers(value, numbers) {
    let output = String(value || '');
    for (let i = 0; i < numbers.length; i += 1) {
      output = output.replaceAll('__N' + i + '__', numbers[i]);
    }
    return output;
  }

  function parseConfig() {
    /* The catalogue arrives as a separate content-hashed file which sets this
       global, not as part of the island - inlined it was ~90% of a compressed
       page and could not be cached, having no URL of its own. The island still
       carries an older inline `catalog` on pages served before this change (a
       cached shell, a stale service-worker entry), so that is still read as a
       fallback rather than leaving the reader untranslated. */
    const shipped = (typeof window !== 'undefined' && window.__GP_I18N_CATALOG__) || null;
    const fallback = {
      locale: 'sk',
      default_locale: 'sk',
      source_locale: 'en',
      catalog: shipped && typeof shipped === 'object' ? shipped : {},
    };
    const node = document.getElementById('gp-i18n-config');
    if (!node || !node.textContent) {
      return fallback;
    }

    try {
      const parsed = JSON.parse(node.textContent);
      if (!parsed || typeof parsed !== 'object') {
        return fallback;
      }
      return {
        locale: parsed.locale || fallback.locale,
        default_locale: parsed.default_locale || fallback.default_locale,
        source_locale: parsed.source_locale || fallback.source_locale,
        catalog:
          shipped && typeof shipped === 'object'
            ? shipped
            : parsed.catalog && typeof parsed.catalog === 'object'
              ? parsed.catalog
              : {},
      };
    } catch (_) {
      return fallback;
    }
  }

  const config = parseConfig();
  const locale = normalizeLocale(config.locale) || 'sk';
  const defaultLocale = normalizeLocale(config.default_locale) || 'sk';
  const sourceLocale = normalizeLocale(config.source_locale) || 'en';
  const rawCatalog = config.catalog || {};

  const catalog = {};
  const patternCatalog = {};
  Object.keys(rawCatalog).forEach(function (key) {
    const normalizedKey = normalizeText(key);
    const normalizedValue = normalizeText(rawCatalog[key]);
    if (!normalizedKey || !normalizedValue) {
      return;
    }
    catalog[normalizedKey] = normalizedValue;
    const keyTokens = tokenizeNumbers(normalizedKey);
    if (keyTokens.values.length > 0) {
      const valueTokens = tokenizeNumbers(normalizedValue);
      patternCatalog[keyTokens.tokenized] = valueTokens.tokenized;
    }
  });

  function applyParams(text, params) {
    if (!params || typeof params !== 'object') {
      return text;
    }
    let rendered = String(text || '');
    Object.keys(params).forEach(function (name) {
      rendered = rendered.replaceAll('{' + name + '}', String(params[name]));
    });
    return rendered;
  }

  function translate(text, params) {
    const original = String(text == null ? '' : text);
    const normalized = normalizeText(original);
    if (!normalized) {
      return original;
    }

    let translated = normalized;
    if (locale !== sourceLocale) {
      translated = catalog[normalized];
      if (typeof translated !== 'string') {
        const keyTokens = tokenizeNumbers(normalized);
        const pattern = patternCatalog[keyTokens.tokenized];
        if (typeof pattern === 'string') {
          translated = restoreNumbers(pattern, keyTokens.values);
        } else {
          translated = normalized;
        }
      }
    }

    translated = applyParams(translated, params);
    if (original === normalized) {
      return translated;
    }
    return original.replace(normalized, translated);
  }

  function shouldTranslateText(text) {
    const value = normalizeText(text);
    if (!value) {
      return false;
    }
    if (!/[A-Za-z]/.test(value)) {
      return false;
    }
    return true;
  }

  function translateTextNode(node) {
    if (!node || node.nodeType !== Node.TEXT_NODE) {
      return;
    }
    const parent = node.parentElement;
    if (!parent) {
      return;
    }
    const tag = parent.tagName;
    if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'TEXTAREA') {
      return;
    }
    /* The HTML `translate="no"` attribute, honoured the way browsers'
       own translation does: a language's name in the language switcher is
       written in that language ("English", "Slovenčina") so a reader who
       cannot read the current one can still find their own - and the
       catalogue was turning it into "Angličtina". */
    if (parent.closest('[translate="no"]')) {
      return;
    }
    const original = node.nodeValue || '';
    if (!shouldTranslateText(original)) {
      return;
    }
    const translated = translate(original);
    if (translated !== original) {
      node.nodeValue = translated;
    }
  }

  function translateElementAttributes(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) {
      return;
    }
    if (el.closest('[translate="no"]')) {
      return;
    }

    for (let i = 0; i < ATTRIBUTES.length; i += 1) {
      const attr = ATTRIBUTES[i];
      if (!el.hasAttribute(attr)) {
        continue;
      }
      const current = el.getAttribute(attr);
      if (!current || !shouldTranslateText(current)) {
        continue;
      }
      const translated = translate(current);
      if (translated !== current) {
        el.setAttribute(attr, translated);
      }
    }

    // Translate explicit button labels declared via value attributes.
    if (
      el.tagName === 'INPUT' &&
      (el.type === 'submit' || el.type === 'button' || el.type === 'reset') &&
      el.hasAttribute('value')
    ) {
      const val = el.getAttribute('value') || '';
      if (shouldTranslateText(val)) {
        const translatedValue = translate(val);
        if (translatedValue !== val) {
          el.setAttribute('value', translatedValue);
        }
      }
    }
  }

  function translateTree(root) {
    if (!root) {
      return;
    }
    if (root.nodeType === Node.TEXT_NODE) {
      translateTextNode(root);
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) {
      return;
    }

    const element = root.nodeType === Node.ELEMENT_NODE ? root : document.documentElement;
    translateElementAttributes(element);

    if (element.querySelectorAll) {
      element.querySelectorAll('*').forEach(translateElementAttributes);
    }

    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null);
    let node = walker.nextNode();
    while (node) {
      translateTextNode(node);
      node = walker.nextNode();
    }
  }

  function translateDocument() {
    document.documentElement.setAttribute('lang', locale);
    if (document.title) {
      document.title = translate(document.title);
    }
    if (locale === sourceLocale && Object.keys(catalog).length === 0) {
      return;
    }
    translateTree(document.body || document.documentElement);
  }

  let observer = null;
  function startObserver() {
    if (observer || !(window.MutationObserver && document.body)) {
      return;
    }
    observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (mutation.type === 'characterData') {
          translateTextNode(mutation.target);
          return;
        }
        if (mutation.type === 'attributes') {
          translateElementAttributes(mutation.target);
          return;
        }
        mutation.addedNodes.forEach(function (node) {
          translateTree(node);
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ATTRIBUTES,
    });
  }

  GP.i18n = {
    locale: locale,
    defaultLocale: defaultLocale,
    sourceLocale: sourceLocale,
    catalog: catalog,
    t: translate,
    translate: translate,
    translateTree: translateTree,
    translateDocument: translateDocument,
  };
  GP.translate = translate;

  /* Clean up observer on HTMX page swap to prevent leaks */
  document.addEventListener('htmx:beforeSwap', function () {
    if (observer) { observer.disconnect(); observer = null; }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      translateDocument();
      startObserver();
    });
  } else {
    translateDocument();
    startObserver();
  }
})();
