/* ============================================
   Shared background-job message formatting
   ============================================
   Single source of truth for turning the English `result_summary` /
   `error_message` strings that workers store on a BackgroundJob (and the
   raw `job_type` codes) into friendly, translated text. Both the global
   job bar (completion toasts + the live progress row) and the Admin -> System
   job table render the same wording instead of one showing the pretty
   "notes" form and the other leaking the raw English summary. */
const _JOB_TYPE_LABELS = __GP_JOB_LABELS__;

/** Friendly, translated label for a raw background-job `job_type` code. */
function _jobTypeLabel(jt) {
  if (!jt) return jt;
  if (_JOB_TYPE_LABELS[jt]) return _translateUiText(_JOB_TYPE_LABELS[jt]) || _JOB_TYPE_LABELS[jt];
  // Strip scheduled:/manual: prefix, replace underscores, sentence-case.
  const bare = String(jt).split(':').pop().replace(/_/g, ' ').trim();
  if (!bare) return jt;
  const pretty = bare.charAt(0).toUpperCase() + bare.slice(1);
  return _translateUiText(pretty) || pretty;
}

/** Translate a worker-stored job result/error message (English) to UI text. */
function _formatJobMessage(msg) {
  if (!msg) return msg;
  const t = _translateUiText;
  // Static messages - translate via t()
  const direct = t(msg);
  if (direct !== msg) return direct;
  // Dynamic: "Synced N issues, N MRs, N MR notes, N issue notes, N pipelines"
  const syncMatch = msg.match(/^Synced (\d+) issues?, (\d+) MRs?, (\d+) MR notes?, (\d+) issue notes?, (\d+) pipelines?$/);
  if (syncMatch) {
    return t('Synced') + ' ' + syncMatch[1] + ' ' + t('issues') + ', ' +
      syncMatch[2] + ' ' + t('MRs') + ', ' + syncMatch[3] + ' ' + t('MR notes') + ', ' +
      syncMatch[4] + ' ' + t('issue notes') + ', ' + syncMatch[5] + ' ' + t('pipelines');
  }
  // Dynamic: "Enriched N names, N emails"
  const enrichMatch = msg.match(/^Enriched (\d+) names?, (\d+) emails?$/);
  if (enrichMatch) {
    return t('Enriched') + ' ' + enrichMatch[1] + ' ' + t('names') + ', ' + enrichMatch[2] + ' ' + t('emails');
  }
  // Dynamic: "Updated: field1, field2"
  const updateMatch = msg.match(/^Updated: (.+)$/);
  if (updateMatch) {
    return t('Updated') + ': ' + updateMatch[1];
  }
  return msg;
}

GP.formatJobMessage = _formatJobMessage;
GP.jobTypeLabel = _jobTypeLabel;
