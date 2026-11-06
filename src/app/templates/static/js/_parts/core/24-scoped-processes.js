/* ============================================
   Scoped Background Processes
   ============================================ */
function jobAffectsScope(detail, target = {}) {
  const key = String(detail?.jobType || '');
  const meta = { ...(window._globalJobs?.[key]?.meta || {}), ...(detail?.meta || {}) };
  const keyed = key.match(/^[^:]+:(course|team|project):(.+)$/);
  // Older analysis jobs carry their scope in the existing polling URL.
  const legacy = String(meta.pollUrl || '').match(
    /^\/dashboard\/(projects|teams)\/([^/?#]+)\/llm-analysis-status(?:[?#]|$)/,
  );
  const kind = keyed?.[1] || (legacy ? (legacy[1] === 'projects' ? 'project' : 'team') : '')
    || (meta.jobKind === 'course_sync' ? 'course' : '')
    || (meta.projectId ? 'project' : meta.teamId ? 'team' : meta.courseId ? 'course' : '');
  const ids = { courseId: meta.courseId, teamId: meta.teamId, projectId: meta.projectId };
  const scopedId = (keyed || legacy)?.[2];
  if (scopedId && ids[kind + 'Id'] && String(ids[kind + 'Id']) !== scopedId) return false;
  if (scopedId) ids[kind + 'Id'] = scopedId;
  const same = (left, right) => !!left && !!right && String(left) === String(right);
  if (!kind) return same(key, target.courseId); // Legacy course-sync key.
  // A sibling project can conflict with a process lock without changing this
  // project's data. Refresh follows the actual job scope, not lock conflicts.
  if (kind === 'project' && target.projectId) return same(ids.projectId, target.projectId);
  if (kind !== 'course' && target.teamId) return same(ids.teamId, target.teamId);
  return same(ids.courseId, target.courseId);
}
GP.jobAffectsScope = jobAffectsScope;

async function runScopedChecksProcess(options = {}) {
  const opts = options || {};
  const translate = GP.t;
  const jobKey = opts.jobKey || 'run_checks';
  const endpoint = opts.endpoint;
  const statusUrl = opts.statusUrl || null;
  const button = typeof opts.button === 'string'
    ? document.querySelector(opts.button)
    : opts.button;
  const lockKey = opts.lockKey || jobKey;
  const gridSelector = opts.gridSelector || '#runChecksGrid';
  const boxes = document.querySelectorAll(`${gridSelector} input[name="check_codes"]:checked`);
  const checkCodes = Array.from(boxes).map((cb) => cb.value).filter(Boolean);
  if (!endpoint) {
    return null;
  }
  if (!checkCodes.length) {
    showToast(
      translate('Please select at least one check to run, or use Select all.'),
      'warning',
    );
    return null;
  }
  if (
    typeof GP.guardProcessAction === 'function'
    && opts.guardScopes
    && !GP.guardProcessAction(['sync', 'run_checks'], { scope: opts.guardScopes })
  ) {
    return null;
  }

  const label = opts.label || opts.scopeLabel || translate('selection');
  const checksLabel = checkCodes.join(', ');
  const runningMessage = opts.runningMessage
    || translate('Running checks for %s: %s...').replace('%s', label).replace('%s', checksLabel);
  const connectingMessage = opts.connectingMessage
    || translate('Queueing checks for %s...').replace('%s', label);
  const queuedMessage = opts.queuedMessage
    || translate('Compliance checks queued for %s. Watch progress in the top bar.').replace('%s', label);
  /* No local indicator by default. `#btnRunChecks` sits in the modal that is
     closed right below, and while the modal was still fading out the bar's
     pre-scan saw the button as "visible", deferred the job to it and never
     showed the bar at all - a run on an empty course ended with a toast and
     nothing at the top. */
  const meta = {
    localIndicatorSelector: opts.localIndicatorSelector || null,
    courseId: String(opts.courseId || ''),
    teamId: String(opts.teamId || ''),
    projectId: String(opts.projectId || ''),
    jobKind: 'run_checks',
    ...(opts.meta || {}),
  };

  const unlockOnComplete = (ev) => {
    const detail = ev.detail || {};
    if (detail.jobType !== jobKey) {
      return;
    }
    window.removeEventListener('gp:job-complete', unlockOnComplete);

    if (button && typeof setButtonLoading === 'function') {
      setButtonLoading(button, false);
    }
    if (typeof opts.onComplete === 'function') {
      opts.onComplete(detail);
    }
  };

  const failNow = (message) => {
    const msg = message || translate('Checks failed');
    if (typeof failGlobalJob === 'function') {
      failGlobalJob(jobKey, msg);
    } else if (!finishGlobalJobOrToast(jobKey, msg, 'error', { type: 'danger' })) {
      showToast(msg, 'danger');
    }
    window.removeEventListener('gp:job-complete', unlockOnComplete);

    if (button && typeof setButtonLoading === 'function') {
      setButtonLoading(button, false);
      flashButton(button, 'error');
      // Anti-spam cooldown on failure, consistent with the Sync buttons - so
      // EVERY Run Checks button (course / team / project all go through here)
      // discourages hammering a failing endpoint instead of the timer only
      // living on some buttons.
      if (typeof GP.applyCooldown === 'function') {
        GP.applyCooldown(button);
      }
    }
    if (typeof opts.onError === 'function') {
      opts.onError(msg);
    }
  };

  const run = async () => {
    if (button && typeof setButtonLoading === 'function') {
      setButtonLoading(button, true);
    }
    // These values are now the run parameters, not an abandoned draft.
    GP.clearModalDirty(opts.modalId || 'runChecksModal');
    if (typeof closeModal === 'function') {
      closeModal(opts.modalId || 'runChecksModal');
    } else if (typeof forceCloseModal === 'function') {
      forceCloseModal(opts.modalId || 'runChecksModal');
    }
    if (typeof connectGlobalJob === 'function') {
      connectGlobalJob(jobKey, connectingMessage, meta);
    } else if (typeof showGlobalJob === 'function') {
      showGlobalJob(connectingMessage, jobKey, meta);
    }

    try {
      const result = await GP.apiCall(endpoint, 'POST', { check_codes: checkCodes });
      const status = String(result?.status || '').toLowerCase();
      const failedCount = Number(result?.failed || 0);
      const enqueuedCount = Number(result?.enqueued || 0);
      const msg = result?.message || queuedMessage;

      if (status === 'failed' || status === 'cancelled') {
        failNow(msg);
        return result;
      }

      if (result?.job_id) {
        /* The SSE stream is the primary channel and polling is the fallback, so
           the same poll is started from two places: when the stream errors, and
           when the browser has no stream support at all. Both spelled the whole
           call out, three message callbacks included - one definition, started
           from either. */
        const pollJobStatus = () => startGenericStatusPolling(
          jobKey,
          `/api/v1/jobs/${result.job_id}`,
          {
            messageRunning: (data) => data?.result_summary || data?.message || runningMessage,
            messageDone: (data) => (
              data?.result_summary || data?.message || translate('Checks completed!')
            ),
            messageFailed: (data) => (
              data?.error_message || data?.message || translate('Checks failed')
            ),
          },
        );
        window.addEventListener('gp:job-complete', unlockOnComplete);

        if (typeof showGlobalJob === 'function') {
          showGlobalJob(runningMessage, jobKey, { ...meta, jobId: result.job_id });
        } else if (typeof setGlobalJobMeta === 'function') {
          setGlobalJobMeta(jobKey, { ...meta, jobId: result.job_id });
        }
        showToast(msg, failedCount > 0 ? 'warning' : 'info');
        if (typeof streamJobProgress === 'function') {
          streamJobProgress(result.job_id, {
            onUpdate(data) {
              const message = data?.result_summary || data?.message || runningMessage;
              if (typeof updateGlobalJobProgress === 'function' && data?.progress != null) {
                updateGlobalJobProgress(jobKey, data.progress, message);
              } else if (typeof updateGlobalJob === 'function') {
                updateGlobalJob(message, jobKey);
              }
            },
            onComplete(data) {
              const finalStatus = String(data?.status || '').toLowerCase();
              if (finalStatus === 'failed' || finalStatus === 'cancelled') {
                const errorMessage = data?.error_message || data?.message || translate('Checks failed');
                if (typeof completeGlobalJob === 'function') {
                  completeGlobalJob(jobKey, errorMessage, 'error');
                }
                return;
              }
              if (typeof completeGlobalJob === 'function') {
                completeGlobalJob(
                  jobKey,
                  data?.result_summary || data?.message || translate('Checks completed!'),
                  'done',
                );
              }
            },
            onError() {
              if (typeof startGenericStatusPolling === 'function') {
                pollJobStatus();
              } else {
                failNow(translate('Check status unknown'));
              }
            },
          });
        } else if (typeof startGenericStatusPolling === 'function') {
          pollJobStatus();
        }
        return result;
      }

      if (statusUrl && enqueuedCount > 0) {
        window.addEventListener('gp:job-complete', unlockOnComplete);

        if (typeof showGlobalJob === 'function') {
          showGlobalJob(runningMessage, jobKey, { ...meta, pollUrl: statusUrl });
        }
        if (typeof startGenericStatusPolling === 'function') {
          startGenericStatusPolling(jobKey, statusUrl, {
            messageRunning(data) {
              if (typeof updateGlobalJobProgress === 'function' && data?.progress != null) {
                updateGlobalJobProgress(jobKey, data.progress, data?.result_summary || runningMessage);
              }
              return data?.result_summary || data?.message || runningMessage;
            },
            messageDone(data) {
              return data?.result_summary || data?.message || msg;
            },
            messageFailed(data) {
              return data?.error_message || data?.message || msg;
            },
          });
        }
        showToast(msg, failedCount > 0 ? 'warning' : 'info');
        return result;
      }

      // An empty launch has no job to wait for.
      const terminalStatus = failedCount > 0 ? 'error' : 'done';
      if (typeof completeGlobalJob === 'function') {
        completeGlobalJob(jobKey, msg, terminalStatus);
      } else {
        finishGlobalJobOrToast(jobKey, msg, terminalStatus, {
          type: terminalStatus === 'error' ? 'danger' : 'success',
        });
      }
      window.removeEventListener('gp:job-complete', unlockOnComplete);

      if (button && typeof setButtonLoading === 'function') {
        setButtonLoading(button, false);
      }
      if (terminalStatus === 'done' && typeof opts.onComplete === 'function') {
        opts.onComplete({ jobType: jobKey, status: 'done', message: msg });
      }
      return result;
    } catch (err) {
      if (err?.code !== 'LOCKED') {
        failNow(err?.message || translate('Checks failed'));
      }
      return null;
    }
  };

  return GP.withUiLock(lockKey, run);
}

GP.runScopedChecksProcess = runScopedChecksProcess;
window.runScopedChecksProcess = runScopedChecksProcess;

/* Single source of truth for a failed-sync message so course / group / project
   syncs all report the SAME thing - most importantly the 401 expired-token case,
   which used to read as the detailed banner on the course page but a bare "Sync
   failed" on the group/project pages. */
function syncErrorMessage(err) {
  const translate = GP.t;
  if (err && err.status === 401) {
    return translate('The GitLab API token is invalid or expired (401). Sync, import and other GitLab actions are blocked until the token is updated.');
  }
  const msg = err && err.message ? String(err.message) : '';
  return msg || translate('Sync failed');
}
GP.syncErrorMessage = syncErrorMessage;
