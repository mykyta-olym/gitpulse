  /* ==========================================
   *  Danger Zone - Archive / Activate / Clone / Delete
   * ========================================== */

  const _ca = GP.courseActions || {};

  document.getElementById('btnArchiveCourse')?.addEventListener('click', function () {
    _ca.archive(this.dataset.courseId, this, {
      skipBeforeunload: true,
      onSuccess: () => { window.location.href = '/dashboard/'; },
    });
  });

  document.getElementById('btnActivateCourse')?.addEventListener('click', function () {
    _ca.activate(this.dataset.courseId, this, {
      skipBeforeunload: true,
      onSuccess: () => { reloadKeepScroll(); },
    });
  });

  document.getElementById('btnTransferCourse')?.addEventListener('click', function () { openModal('transferCourseModal'); });

  /* The team picker only makes sense for the "selected" carry mode. */
  document.querySelectorAll('input[name="transferCarryMode"]').forEach(function (radio) {
    radio.addEventListener('change', function () {
      document.getElementById('transferTeamPicker')?.classList.toggle('d-none', this.value !== 'selected');
    });
  });

  document.getElementById('btnSubmitTransfer')?.addEventListener('click', async function () {
    const courseId = document.getElementById('btnTransferCourse')?.dataset.courseId;
    const academicYear = document.getElementById('transferAcademicYear')?.value?.trim();
    const semester = document.getElementById('transferSemester')?.value;
    if (!academicYear) { showToast(t('Academic year is required'), 'warning'); return; }
    const carryMode = document.querySelector('input[name="transferCarryMode"]:checked')?.value || 'all';
    const teamIds = carryMode === 'selected'
      ? Array.from(document.querySelectorAll('.transfer-team-checkbox:checked')).map((c) => c.value)
      : [];
    if (carryMode === 'selected' && !teamIds.length) {
      showToast(t('Select at least one group to carry over'), 'warning');
      return;
    }
    const btn = this;
    try {
      await _lock(`transferCourse:${courseId}`, async () => {
        setButtonLoading(btn, true);
        const result = await apiCall('/api/v1/courses/' + courseId + '/transfer', 'POST', {
          academic_year: academicYear,
          semester: semester,
          carry_mode: carryMode,
          team_ids: teamIds,
          webhook_mode: document.getElementById('transferWebhookMode')?.value || 'move',
          archive_source: !!document.getElementById('transferArchiveSource')?.checked,
          enqueue_sync: !!document.getElementById('transferEnqueueSync')?.checked,
          // The new course's dates as the dialog shows them; empty = let the
          // server move this course's own dates to the new term.
          semester_start_date: document.getElementById('transferStart')?.value || null,
          semester_end_date: document.getElementById('transferEnd')?.value || null,
        }, { maxRetries: 0, timeoutMs: 60000 });
        clearModalDirty('transferCourseModal');
        /* Fresh webhook secrets are shown ONCE - surface them before leaving. */
        const secrets = (result && result.webhook_secrets) || [];
        if (secrets.length) {
          const box = document.getElementById('transferResult');
          if (box) {
            box.classList.remove('d-none');
            box.innerHTML = '<p class="form-label">' + t('New webhook secrets (shown once - update them in GitLab):') + '</p>'
              + secrets.map((s) => '<p><strong>' + GP.escapeHtml(s.name) + ':</strong> <code>' + GP.escapeHtml(s.secret) + '</code></p>').join('')
              + '<button type="button" class="btn btn-primary w-100pct mt-2" id="btnTransferGo">' + t('Open the new course') + '</button>';
            document.getElementById('btnTransferGo')?.addEventListener('click', function () {
              if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
              window.location.href = '/dashboard/courses/' + result.id;
            });
          }
          flashToast(t('Course transferred - copy the new webhook secrets before leaving'), 'warning');
          return; /* stay in the modal so the secrets can be copied */
        }
        flashToast(t('Course transferred successfully'), 'success');
        closeModal('transferCourseModal');
        if (typeof GP !== 'undefined' && GP.skipBeforeunload) GP.skipBeforeunload();
        if (result && result.id) window.location.href = '/dashboard/courses/' + result.id;
      });
    } catch (err) {
      if (err.code !== 'LOCKED') showToast(err.message || t('Failed to transfer course'), 'danger');
    } finally {
      setButtonLoading(btn, false);
    }
  });

  document.getElementById('btnDeleteCoursePermanent')?.addEventListener('click', function () {
    if (!_isAdmin) { showToast(t('Only administrators can permanently delete courses'), 'warning'); return; }
    _ca.deletePermanent(this.dataset.courseId, this.dataset.courseCode || this.dataset.courseId, this, {
      skipBeforeunload: true,
      onSuccess: () => { window.location.href = '/dashboard/'; },
    });
  });

