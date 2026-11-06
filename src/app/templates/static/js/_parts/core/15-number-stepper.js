/* ============================================
   Number stepper (components/forms.html `number_stepper`)

   ONE delegated handler drives every stepper on the page, so a control cloned
   into a modal at runtime behaves exactly like a server-rendered one. This
   replaces the previous Alpine `glNumberInput` factory: Alpine never
   initialises nodes injected by page JS, so the check editor hand-rolled its
   own stepper markup plus a second document-level click handler - and since
   both handlers matched `.number-btn-minus`, a single click on a macro-rendered
   stepper stepped the value twice (Alpine's `step`, then the duplicate's -1).
   ============================================ */
const _STEPPER_SEL = '[data-number-input]';

function _stepperNum(raw, fallback) {
  if (raw === '' || raw === null || raw === undefined) return fallback;
  const n = Number(raw);
  return isFinite(n) ? n : fallback;
}

/** Snap a value into the field's min/max and to the step's decimal precision. */
function _stepperClamp(input, raw) {
  const min = _stepperNum(input.min, null);
  const max = _stepperNum(input.max, null);
  const step = _stepperNum(input.step, 1) || 1;
  const decimals = (String(step).split('.')[1] || '').length;
  let v = Number(raw);
  if (!isFinite(v)) v = min !== null ? min : 0;
  if (min !== null && v < min) v = min;
  if (max !== null && v > max) v = max;
  return Number(v.toFixed(decimals));
}

/** Current numeric value, falling back to the placeholder (= the default a
 *  check parameter row shows when the teacher has not overridden it). */
function _stepperValue(input) {
  const raw = input.value === '' ? input.placeholder : input.value;
  return _stepperClamp(input, raw);
}

/** Reflect the min/max limits on the -/+ buttons of one stepper. */
function syncNumberStepper(wrap) {
  const input = wrap.querySelector('.gl-number-input-field');
  if (!input) return;
  const min = _stepperNum(input.min, null);
  const max = _stepperNum(input.max, null);
  const cur = _stepperValue(input);
  const minus = wrap.querySelector('[data-number-step="-1"]');
  const plus = wrap.querySelector('[data-number-step="1"]');
  if (minus) minus.disabled = input.disabled || (min !== null && cur <= min);
  if (plus) plus.disabled = input.disabled || (max !== null && cur >= max);
}

/** Sync every stepper inside `root` (call after injecting markup). */
function syncNumberSteppers(root) {
  (root || document).querySelectorAll(_STEPPER_SEL).forEach(syncNumberStepper);
}

document.addEventListener('click', function _handleStepperClick(event) {
  const target = event.target instanceof Element ? event.target : null;
  const btn = target ? target.closest('[data-number-step]') : null;
  if (!btn) return;
  const wrap = btn.closest(_STEPPER_SEL);
  const input = wrap ? wrap.querySelector('.gl-number-input-field') : null;
  if (!input || input.disabled) return;
  event.preventDefault();
  const step = _stepperNum(input.step, 1) || 1;
  const dir = Number(btn.dataset.numberStep) < 0 ? -1 : 1;
  input.value = _stepperClamp(input, _stepperValue(input) + dir * step);
  syncNumberStepper(wrap);
  // Notify listeners (save guards, weight totals, dirty tracking).
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
});

/* Typing is free-form; snap back into range only when the field is left, so a
   manually typed 99 in a 0-1 weight cannot be submitted. */
document.addEventListener('input', function _handleStepperInput(event) {
  const el = event.target;
  if (el instanceof Element && el.classList.contains('gl-number-input-field')) {
    const wrap = el.closest(_STEPPER_SEL);
    if (wrap) syncNumberStepper(wrap);
  }
});
document.addEventListener('blur', function _handleStepperBlur(event) {
  const el = event.target;
  if (!(el instanceof Element) || !el.classList.contains('gl-number-input-field')) return;
  // An empty optional field stays empty - that is how a check parameter says
  // "use the default", and clamping it would write the default in as an override.
  if (el.value !== '') el.value = _stepperClamp(el, el.value);
  const wrap = el.closest(_STEPPER_SEL);
  if (wrap) syncNumberStepper(wrap);
}, true);

GP.syncNumberStepper = syncNumberStepper;
GP.syncNumberSteppers = syncNumberSteppers;
document.addEventListener('DOMContentLoaded', function () { syncNumberSteppers(document); });

/**
 * Build a stepper by CLONING the page's `#tplNumberStepper` - a single
 * `number_stepper()` render parked in a <template>. Cloning rather than
 * re-emitting the markup in JS keeps one definition of the control.
 *
 * @returns {HTMLElement|null} null when the page did not render the template.
 */
function createNumberStepper(opts) {
  const o = opts || {};
  const tpl = document.getElementById('tplNumberStepper');
  const proto = tpl && tpl.content ? tpl.content.querySelector('[data-number-input]') : null;
  if (!proto) return null;
  const wrap = proto.cloneNode(true);
  const input = wrap.querySelector('.gl-number-input-field');
  if (input) {
    const attrs = { id: o.id, name: o.name, min: o.min, max: o.max, step: o.step, placeholder: o.placeholder };
    Object.keys(attrs).forEach(function (k) {
      if (attrs[k] === undefined || attrs[k] === null || attrs[k] === '') input.removeAttribute(k);
      else input.setAttribute(k, String(attrs[k]));
    });
    input.value = o.value === undefined || o.value === null ? '' : String(o.value);
    if (o.className) input.classList.add.apply(input.classList, String(o.className).split(/\s+/).filter(Boolean));
    Object.keys(o.dataset || {}).forEach(function (k) { input.dataset[k] = o.dataset[k]; });
  }
  syncNumberStepper(wrap);
  return wrap;
}

/**
 * One settings row: label (+ hint) on the left, control on the right.
 *
 * Shared so the several "parameter with a default" lists in the app stop
 * hand-rolling their own flex row. The hint carries the default value; it used
 * to be a separate span pushed to the far edge with `margin-left:auto`, which
 * stranded "default: false" across the modal from the control it described.
 *
 * `wide` stacks the control under the label and lets it fill the row, for
 * free-text values (a regex, a comma-separated list) that are unreadable
 * squeezed into the narrow right-hand column a toggle or stepper needs.
 *
 * @param {{label: string, hint?: string, controlId?: string, control?: Node,
 *          wide?: boolean}} opts
 * @returns {HTMLElement}
 */
function createSettingRow(opts) {
  const o = opts || {};
  const row = document.createElement('div');
  row.className = o.wide ? 'gl-setting-row gl-setting-row--wide' : 'gl-setting-row';

  const text = document.createElement('div');
  text.className = 'gl-setting-row-text';
  const label = document.createElement('label');
  label.className = 'gl-setting-row-label';
  label.textContent = o.label || '';
  if (o.controlId) label.htmlFor = o.controlId;
  text.appendChild(label);
  if (o.hint) {
    const hint = document.createElement('p');
    hint.className = 'gl-setting-row-hint';
    hint.textContent = o.hint;
    text.appendChild(hint);
  }

  const control = document.createElement('div');
  control.className = 'gl-setting-row-control';
  if (o.control) control.appendChild(o.control);

  row.appendChild(text);
  row.appendChild(control);
  return row;
}

GP.createNumberStepper = createNumberStepper;
GP.createSettingRow = createSettingRow;
