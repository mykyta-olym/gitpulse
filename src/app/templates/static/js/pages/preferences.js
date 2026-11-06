/* Preferences page.
 *
 * The form posts its controls as JSON to the endpoint declared in the page
 * config. Every control is a server-rendered input from the shared form
 * macros, so there is no client-side model of the settings to drift out of
 * step with what the server stored.
 *
 * The colour mode is deliberately NOT handled here: theme-bootstrap.js already
 * owns [data-theme-value], applies the mode and persists it on its own. The
 * switcher in the Mode section is that same component.
 *
 * Reuses the app's existing contracts rather than re-implementing them:
 *   GP.apiCall          - CSRF, timeout, retry policy
 *   GP.setButtonLoading - the shared spinner-in-place button state
 *   GP.flashToast       - exactly one toast, success XOR failure
 */
(function () {
  'use strict';

  /* Every page bundle re-runs on each SPA navigation into its page, so it first
     retires the previous page's listeners and then registers its own teardown.
     This one used to skip both halves: its `htmx:afterSwap` listener was added
     again on every visit and never removed, so after N visits N copies of it
     called init() on every swap in the app. */
  const GP = window.GP || {};
  GP.runPageCleanup();

  function pageConfig() {
    const el = document.getElementById('gp-page-config');
    if (!el) return {};
    try {
      return JSON.parse(el.textContent) || {};
    } catch (_) {
      return {};
    }
  }

  const { t, flashToast: toast, setButtonLoading: loading } = GP;

  /* Read the form into the shape the endpoint validates. An unchecked checkbox
     must post `false` rather than be omitted, or "turn it off and save" would
     silently keep the old value. */
  function readForm(form) {
    const out = {};
    const inputs = form.querySelectorAll('input[name], select[name]');
    for (let i = 0; i < inputs.length; i++) {
      const el = inputs[i];
      if (!el.name || el.disabled) continue;
      if (el.type === 'checkbox') {
        out[el.name] = el.checked;
      } else if (el.type === 'radio') {
        if (el.checked) out[el.name] = el.value;
      } else {
        out[el.name] = el.value;
      }
    }
    return out;
  }

  /* base.html renders these preferences onto <html> so CSS can key off them
     before first paint - and nothing ever updated them again. Saving posted
     the values, said "Preferences saved" and left the document exactly as it
     was, so accent, syntax scheme, layout width, page size, first day of week,
     time format, relative times and keyboard shortcuts all appeared to do
     nothing until the next full page load. An SPA navigation does not help:
     it swaps #main-content and never re-renders <html>.

     Mode is the one exception and is deliberately not here - theme-bootstrap.js
     owns [data-theme-value] and already applies it on click.

     Kept next to the base.html block it mirrors; pinned by
     tests/unit/test_preferences_apply_on_save.py. */
  const ROOT_VALUES = [
    ['accent_theme', 'data-accent', 'default'],
    ['syntax_theme', 'data-syntax-theme', 'dark'],
    ['layout_width', 'data-layout-width', 'fixed'],
    ['time_format', 'data-time-format', 'system'],
    ['first_day_of_week', 'data-first-day', 'system'],
    ['default_page_size', 'data-page-size', '50'],
    ['default_period', 'data-period-default', 'remembered'],
  ];
  /* Marker attributes: present only when the preference holds the value that
     base.html tests for - two of the three are the NEGATIVE of the checkbox. */
  const ROOT_FLAGS = [
    ['sidebar_collapsed', 'data-sidebar-collapsed', true],
    ['use_relative_times', 'data-absolute-times', false],
    ['keyboard_shortcuts_enabled', 'data-no-shortcuts', false],
  ];

  /* What the account currently holds. A live preview has to be undoable: an
     SPA navigation swaps #main-content and never re-renders <html>, so an
     accent the reader tried and did not save would follow them onto every
     other page for the rest of the session. */
  let _savedValues = null;

  function applySaved(values) {
    const root = document.documentElement;
    ROOT_VALUES.forEach(function (spec) {
      if (!(spec[0] in values)) return;
      root.setAttribute(spec[1], values[spec[0]] || spec[2]);
    });
    ROOT_FLAGS.forEach(function (spec) {
      if (!(spec[0] in values)) return;
      if (values[spec[0]] === spec[2]) root.setAttribute(spec[1], '1');
      else root.removeAttribute(spec[1]);
    });
    [
      ['diff_color_removed', '--gl-diff-color-removed'],
      ['diff_color_added', '--gl-diff-color-added'],
    ].forEach(function (pair) {
      if (!(pair[0] in values)) return;
      const value = (values[pair[0]] || '').trim();
      if (/^#[0-9a-fA-F]{6}$/.test(value)) root.style.setProperty(pair[1], value);
      else root.style.removeProperty(pair[1]);
    });
    /* Times are formatted once and flagged, so the two clock preferences need
       the already-rendered stamps re-read - the <time> element keeps its ISO
       source in `datetime`, which is what makes re-running safe. */
    if (typeof window.localizeTimes === 'function') {
      document.querySelectorAll('time[data-localized]').forEach(function (el) {
        delete el.dataset.localized;
      });
      window.localizeTimes();
    }
  }

  function applyValues(form, values) {
    Object.keys(values).forEach(function (name) {
      const value = values[name];
      const els = form.querySelectorAll('[name="' + name + '"]');
      for (let i = 0; i < els.length; i++) {
        const el = els[i];
        if (el.type === 'checkbox') {
          el.checked = value === true || value === 'true';
        } else if (el.type === 'radio') {
          el.checked = el.value === String(value);
        } else {
          el.value = value == null ? '' : String(value);
        }
        /* The custom select (glFormSelect) mirrors a hidden input and only
           re-renders its label on a native change event. */
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  }

  function init() {
    const form = document.querySelector('[data-preferences-form]');
    if (!form || form.dataset.preferencesBound === '1') return;
    form.dataset.preferencesBound = '1';

    const cfg = pageConfig();
    const endpoint = cfg.preferencesEndpoint || '/dashboard/api/preferences';
    /* Language is the one preference the client cannot apply: every string on
       the page was translated server-side. Saving sets the gp_lang cookie
       (api/dashboard/preferences.py) but nothing re-rendered, so the page
       stayed in the old language until the reader happened to reload. Snapshot
       what was rendered so a save can tell whether the language actually
       changed - the field's "" (system default) has no client-side equivalent
       to compare against. */
    let languageAtLoad = (function () {
      const el = form.querySelector('[name="preferred_language"]');
      return el ? el.value : null;
    })();
    const defaults = cfg.defaults || {};

    /* The SAME save contract the course-settings page uses: the button starts
       disabled, arms only once the form differs from its snapshot, and
       registers a dirty reason so navigating away warns about unsaved changes.
       Hand-rolling an always-enabled submit here would have been a second way
       to save a form, and would silently drop edits on navigation. */
    window.GP.initSaveGuard('#preferencesForm', '#preferencesSave', {
      dirtyKey: 'preferences_form',
    });

    /* Apply on SELECT, not on save. GitLab's preferences page repaints the
       moment you pick an accent or a scheme; ours waited for Save, so
       choosing a theme looked like it did nothing - the reported "half the
       settings do not work". The dirty guard still owns PERSISTENCE: Save
       stays the thing that writes, and leaving with unsaved changes still
       asks. */
    _savedValues = readForm(form);
    form.addEventListener('change', function () {
      applySaved(readForm(form));
    });

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      const button = document.getElementById('preferencesSave');
      if (!button) return;

      try {
        await GP.withUiLock('preferencesSave', async function () {
          loading(button, true);

          const payload = readForm(form);
          await window.GP.apiCall(endpoint, 'POST', payload, { maxRetries: 0 });

          if (!form.isConnected) return;

          toast(t('Preferences saved'), 'success');
          window.GP.setButtonDone(button);
          /* Make the saved choice visible NOW rather than at the next full
             page load - see applySaved. */
          const saved = payload;
          applySaved(readForm(form));
          _savedValues = saved;
          // Acknowledge the submitted values before considering a language
          // reload. Any later edits keep their warning and defer that reload.
          window.GP.resetSaveGuard('#preferencesForm', form);
          if (!GP.hasDirtyReason?.('preferences_form')
              && languageAtLoad !== null && saved.preferred_language !== languageAtLoad) {
            languageAtLoad = saved.preferred_language;
            /* Same two writes the language switcher makes, so other open tabs
               follow through locale-sync.js's storage listener, then the
               scroll-preserving reload it uses. */
            try {
              if (saved.preferred_language) {
                window.localStorage.setItem('gp_lang', saved.preferred_language);
              } else {
                window.localStorage.removeItem('gp_lang');
              }
            } catch (_) { /* private mode - the cookie still carries it */ }
            if (typeof window.reloadKeepScroll === 'function') window.reloadKeepScroll();
            else window.location.reload();
          }
        });
      } catch (err) {
        if (!form.isConnected) return;
        if (err && err.code === 'LOCKED') return;
        /* Name the field the server refused: a bare "could not save" on a
           page of this many controls tells the reader nothing actionable. */
        const fields = err && err.data && err.data.fields;
        const detail =
          Array.isArray(fields) && fields.length ? ': ' + fields.join(', ') : '';
        toast((err && err.message) || (t('Could not save preferences') + detail), 'danger');
      } finally {
        loading(button, false);
      }
    });

    /* Diff colour swatches fill the matching input and repaint the preview.
       Delegated from the form so the handler survives an SPA re-render without
       re-binding each button. */
    form.addEventListener('click', function (event) {
      const swatch = event.target.closest('[data-diff-swatch]');
      if (!swatch) return;
      event.preventDefault();
      const input = form.querySelector('[name="' + swatch.dataset.diffSwatch + '"]');
      if (!input) return;
      input.value = swatch.dataset.color;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });

    /* Live preview. The preview rows are the real .dn-code-* component, so
       setting the same two custom properties the student page reads shows
       exactly what the diff will look like - no separate preview styling to
       drift. An invalid half-typed hex is ignored rather than cleared, so the
       preview does not flicker while you type. */
    function repaintPreview() {
      /* BOTH panes: the removed and added tables each carry .gl-diff-preview,
         so painting `querySelector`'s single hit left the added pane showing
         the default colour no matter what was typed into its field. */
      const panes = form.querySelectorAll('.gl-diff-preview');
      if (!panes.length) return;
      [
        ['diff_color_removed', '--gl-diff-color-removed'],
        ['diff_color_added', '--gl-diff-color-added'],
      ].forEach(function (pair) {
        const input = form.querySelector('[name="' + pair[0] + '"]');
        if (!input) return;
        const value = (input.value || '').trim();
        for (let i = 0; i < panes.length; i++) {
          if (/^#[0-9a-fA-F]{6}$/.test(value)) {
            panes[i].style.setProperty(pair[1], value);
          } else if (value === '') {
            panes[i].style.removeProperty(pair[1]);
          }
        }
        /* Keep the native picker's swatch in step with a hex typed into the
           field or a suggested swatch clicked, so the palette always opens on
           the current colour. */
        const picker = form.querySelector('[data-diff-picker="' + pair[0] + '"]');
        if (picker && /^#[0-9a-fA-F]{6}$/.test(value)) picker.value = value;
      });
    }

    form.addEventListener('input', function (event) {
      /* The native colour picker carries no form name (it must not post - the
         hex field is the source of truth); mirror its value into that field and
         let the field's own input event drive the preview and the dirty guard. */
      const picker = event.target && event.target.closest && event.target.closest('[data-diff-picker]');
      if (picker) {
        const pinput = form.querySelector('[name="' + picker.dataset.diffPicker + '"]');
        if (pinput) {
          pinput.value = picker.value;
          pinput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        return;
      }
      if (event.target && /^diff_color_/.test(event.target.name || '')) repaintPreview();
    });
    repaintPreview();

    const reset = document.getElementById('preferencesReset');
    if (reset) {
      reset.addEventListener('click', function () {
        applyValues(form, defaults);
        repaintPreview();
        /* applyValues dispatches `change`, which the guard listens for, so the
           Save button arms itself - restoring is a proposal, not a save. */
        /* Not saved yet on purpose - restoring is a big change, so it stays a
           visible proposal the reader confirms with Save. */
        toast(t('Defaults restored - save to apply'), 'info');
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* SPA navigation swaps #main-content without a fresh document, so the page
     re-binds when it is navigated into. `dataset.preferencesBound` keeps that
     idempotent. */
  document.addEventListener('htmx:afterSwap', init);

  GP.preferencesCleanup = function () {
    document.removeEventListener('DOMContentLoaded', init);
    document.removeEventListener('htmx:afterSwap', init);
    /* Put the document back to what the account actually holds. Without this a
       previewed-but-unsaved accent, scheme or layout width would survive the
       content swap and misrepresent the saved settings everywhere else. */
    if (_savedValues) {
      try { applySaved(_savedValues); } catch (_) { /* page already gone */ }
    }
  };
  GP.activePageCleanup = GP.preferencesCleanup;
})();
