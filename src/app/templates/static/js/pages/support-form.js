/* Support form page logic - GitHub-style ticket submission with markdown editor */
/* renderMarkdown and mdInsert are loaded from /static/js/markdown-helpers.js */

/* -- Alpine component for the form markdown editor -- */
function supportFormEditor() {
  return {
    mdTab: 'write',
    subjectText: ''
  };
}

/* -- Form submission -- */
(function initSupportFormPage() {
  const GP = window.GP;
  GP.runPageCleanup();
  const { apiCall, t } = GP;
  const form = document.getElementById('supportForm');
  const successBox = document.getElementById('successMessage');

  if (!form || !successBox) return;
  const page = form.closest('.gh-form-page');
  let disposed = false;
  const current = () => !disposed && form.isConnected;

  const META_FIELDS = new Set(['context_type', 'course_id', 'form_id', 'title', 'priority']);

  function parseFormData() {
    const formData = new FormData(form);
    const result = {};
    const responses = {};
    formData.forEach((value, key) => {
      if (META_FIELDS.has(key)) {
        if (key === 'course_id') {
          if (value && value !== '0' && value.trim() !== '') result[key] = value;
        } else {
          result[key] = value;
        }
        return;
      }
      responses[key] = value;
    });
    result.responses = responses;
    return result;
  }

  async function submit(event) {
    event.preventDefault();
    if (!current() || form.hidden) return;
    const submitButton = form.querySelector('button[type="submit"]');
    const saved = await GP.refreshRegion({
      button: submitButton, region: form,
      errorMessage: t('An error occurred. Please try again.'),
      load: async options => {
        try {
          await apiCall(form.action, 'POST', parseFormData(), options);
          return current();
        } catch (error) {
          if (current()) throw error;
          return false;
        }
      },
    });
    if (!saved || !current()) return;
    GP.clearDirtyReason('support_form');
    GP.motion.resize(page, function () {
      form.hidden = true;
      successBox.hidden = false;
    });
    successBox.focus();
  }

  // Custom controls emit synthetic value events after a real user interaction.
  let userEdited = false;
  const stopTracking = GP.trackFormUserEdits(form, () => { userEdited = true; });
  function trackEdit(event) {
    if (event.target.closest('[data-dirty-ignore]')) return;
    if (current() && !form.hidden && (event.isTrusted || userEdited)) GP.addDirtyReason('support_form');
  }
  form.addEventListener('submit', submit);
  form.addEventListener('input', trackEdit);
  form.addEventListener('change', trackEdit);
  GP.activePageCleanup = function () {
    disposed = true;
    stopTracking();
    GP.clearDirtyReason('support_form');
    form.removeEventListener('submit', submit);
    form.removeEventListener('input', trackEdit);
    form.removeEventListener('change', trackEdit);
  };
})();
