/* Support ticket detail: shared request states and live thread updates. */

;(function () {
  'use strict';

  const GP = window.GP;
  GP.runPageCleanup();

  const { t } = GP;

  let activeInstance = null;

  /* status -> [label, badge variant, icon]: `status_badge_detail` in
     components/support_badges.html, which renders the badge first. */
  const STATUS_BADGES = {
    open: ['Open', 'success', 'git-pull-request'],
    in_progress: ['In Progress', 'info', 'clock'],
    resolved: ['Resolved', 'primary', 'check-circle'],
    closed: ['Closed', 'gray', 'git-merge'],
  };

  function ticketDetailManager() {
    const owner = document.getElementById('gh-ticket-cfg');
    const cfg = JSON.parse(owner.textContent);
    const ticketId = cfg.ticketId;
    const staffUsers = cfg.staffUsers || [];
    const currentFields = { ...cfg.currentFields };

    let disposed = false;
    let stream = null;
    const current = () => !disposed && owner.isConnected;
    const dirtyKey = 'support-reply:' + ticketId;
    const seenComments = new Set(Array.from(document.querySelectorAll('[data-comment-id]'), el => el.dataset.commentId));

    return {
      replyTab: 'write',
      liveState: 'connecting',
      _visibilityHandler: null,
      _healthHandler: null,
      assigneeSearch: '',
      assigneeDropdown: false,

      get liveLabel() {
        return t({ connecting: 'Connecting...', live: 'Live updates active',
          reconnecting: 'Reconnecting...', paused: 'Live updates paused',
          unavailable: 'Live updates unavailable' }[this.liveState]);
      },

      get filteredStaff() {
        const q = (this.assigneeSearch || '').toLowerCase();
        if (!q) return staffUsers;
        return staffUsers.filter(function(u) {
          return (u.username || '').toLowerCase().indexOf(q) !== -1 ||
                 (u.name || '').toLowerCase().indexOf(q) !== -1;
        });
      },

      init: function() {
        activeInstance = this;

        // Render markdown for server-rendered content (no Alpine expressions needed)
        document.querySelectorAll('.gh-md-render').forEach(function(el) {
          el.innerHTML = renderMarkdown(el.textContent);
          el.classList.remove('gh-md-render');
        });

        const self = this;
        this._visibilityHandler = function() { self.resumeLive(); };
        document.addEventListener('visibilitychange', this._visibilityHandler);

        this._healthHandler = function() { self.resumeLive(); };
        document.addEventListener('gp-health-change', this._healthHandler);
        window.addEventListener('online', this._healthHandler);
        window.addEventListener('offline', this._healthHandler);
        this.resumeLive();
        this.trackReply();
      },

      destroy: function() {
        if (disposed) return;
        disposed = true;
        GP.clearDirtyReason(dirtyKey);
        if (this._visibilityHandler) {
          document.removeEventListener('visibilitychange', this._visibilityHandler);
        }
        if (this._healthHandler) {
          document.removeEventListener('gp-health-change', this._healthHandler);
          window.removeEventListener('online', this._healthHandler);
          window.removeEventListener('offline', this._healthHandler);
        }
        stream?.close();
      },

      trackReply() {
        if (document.getElementById('reply_content')?.value) GP.addDirtyReason(dirtyKey);
        else GP.clearDirtyReason(dirtyKey);
      },

      resumeLive: function() {
        if (!current()) return;
        if (document.visibilityState === 'hidden' || !navigator.onLine || GP.health.isDown) {
          stream?.close();
          this.liveState = 'paused';
          return;
        }
        if (stream?.active) return;
        stream?.close();
        const self = this;
        this.liveState = 'connecting';
        function read(event) {
          let data;
          try { data = JSON.parse(event.data); } catch (_) { return null; }
          return current() && data && String(data.ticket_id) === String(ticketId) ? data : null;
        }
        stream = GP.sse({
          url: '/api/v1/support/tickets/' + ticketId + '/stream',
          events: {
            connected() { if (current()) self.liveState = 'live'; },
            comment(event) {
              const data = read(event);
              if (!data) return;
              self._injectComment(data.comment);
              if (data.updated_at) self._updateTimeline(data.updated_at);
            },
            update(event) {
              const data = read(event);
              if (!data || !data.fields || typeof data.fields !== 'object') return;
              self._applyFieldUpdates(data.fields);
              if (data.updated_at) self._updateTimeline(data.updated_at);
            },
          },
          onFailure() { if (current()) self.liveState = 'reconnecting'; },
          onGiveUp() { if (current()) self.liveState = 'unavailable'; },
          onBlocked() { if (current()) self.liveState = 'unavailable'; },
        });
      },

      _injectComment: function(comment) {
        if (!current() || !comment?.id || typeof comment.content !== 'string') return;
        const cid = String(comment.id);
        if (seenComments.has(cid)) return;

        const thread = document.querySelector('.gh-ticket-thread');
        const replyEntry = thread ? thread.querySelector('.gh-thread-reply') : null;
        if (!thread || !replyEntry) return;

        /* The server's own comment, cloned from #ghCommentTemplate (the same
           macro the page was rendered with) and filled in. */
        const tpl = document.getElementById('ghCommentTemplate');
        if (!tpl) return;
        const isStaff = !!comment.author && comment.author !== 'Submitter';
        const isInternal = !!comment.is_internal;
        const entryDiv = tpl.content.firstElementChild.cloneNode(true);
        entryDiv.dataset.commentId = cid;
        entryDiv.classList.toggle('gh-thread-internal', isInternal);
        entryDiv.querySelector('.gh-thread-bubble').classList.toggle('gh-thread-bubble--internal', isInternal);
        entryDiv.querySelector('.gh-thread-avatar-col').innerHTML =
          GP.avatarHtml(comment.author_avatar_url, comment.author || '?', 32);
        const author = entryDiv.querySelector('.gh-thread-author');
        author.textContent = comment.author || t('Unknown');
        if (comment.author_role) {
          author.insertAdjacentHTML('afterend', comment.author_is_bot
            ? GP.badgeHtml(t('Bot'), 'muted', { size: 'sm' })
            : GP.roleBadgeHtml(comment.author_role));
        }
        entryDiv.querySelector('.gh-thread-time').innerHTML = GP.timeHtml(comment.created_at, '', '');
        const header = entryDiv.querySelector('.gh-thread-header');
        if (isInternal) header.insertAdjacentHTML('beforeend', GP.badgeHtml(t('Internal'), 'warning'));
        else if (isStaff) header.insertAdjacentHTML('beforeend', GP.badgeHtml(t('GitPulse Support'), 'info', { class: 'gh-thread-role' }));
        entryDiv.querySelector('.gh-thread-text').innerHTML = renderMarkdown(comment.content || '');

        // Insert right before the reply form (chronological order - newest at bottom)
        thread.insertBefore(entryDiv, replyEntry);
        seenComments.add(cid);
        window.localizeTimes(entryDiv);

        // Update comment count in header if visible
        const countEl = document.querySelector('.gh-comment-count');
        if (countEl) {
          const n = parseInt(countEl.textContent || '0', 10) + 1;
          countEl.textContent = n;
        }

        if (comment.updated_at) this._updateTimeline(comment.updated_at);
      },

      /* Update the timestamp field in the shared Details card. */
      _updateTimeline: function(isoStr) {
        if (!isoStr) return;
        let el = document.getElementById('ghLastUpdated');
        if (!el) {
          // The page's own timestamp field, from #ghTimelineTemplate.
          const timeline = document.getElementById('ghTicketTimeline');
          const tpl = document.getElementById('ghTimelineTemplate');
          if (!timeline || !tpl) return;
          timeline.appendChild(tpl.content.firstElementChild.cloneNode(true));
          el = document.getElementById('ghLastUpdated');
        }
        el.innerHTML = GP.timeHtml(isoStr);
        window.localizeTimes(el);
      },

      _touchLastUpdated: function() {
        this._updateTimeline(new Date().toISOString());
      },

      _applyFieldUpdates: function(fields) {
        Object.assign(currentFields, fields);
        if (fields.status) {
          // The status badge, as `status_badge_detail` (support_badges.html) draws it.
          const holder = document.getElementById('ghStatusBadge');
          if (holder) {
            const b = STATUS_BADGES[fields.status] || STATUS_BADGES.open;
            holder.innerHTML = GP.badgeHtml(t(b[0]), b[1], { icon: b[2] });
          }
          // Update sidebar component select (hidden input)
          const statusInput = document.querySelector('.gh-sidebar-select input[name="status"]');
          if (statusInput) statusInput.value = fields.status;

          this._syncReplyButtons();
        }
        if (fields.priority) {
          const prInput = document.querySelector('.gh-sidebar-select input[name="priority"]');
          if (prInput) prInput.value = fields.priority;
        }
        if (fields.category) {
          const catInput = document.querySelector('.gh-sidebar-select input[name="category"]');
          if (catInput) catInput.value = fields.category;
        }
        if (fields.assigned_to !== undefined) {
          // Assignee is now a search component - reload to refresh
          const assigneeEl = document.querySelector('.gh-assignee-current .gl-avatar-labeled-label');
          if (assigneeEl) assigneeEl.textContent = fields.assigned_to || '';
        }

        // Update "Last updated" sidebar timestamp
        this._touchLastUpdated();
      },

      _syncReplyButtons() {
        if (!current()) return;
        const replyBtns = document.querySelector('.gh-reply-buttons');
        if (!replyBtns || replyBtns.closest('form').getAttribute('aria-busy') === 'true') return;
        const closed = String(['resolved', 'closed'].includes(currentFields.status));
        if (replyBtns.dataset.closed === closed) return;
        const tpl = document.getElementById(closed === 'true' ? 'ghReplyButtonsReopen' : 'ghReplyButtonsOpen');
        replyBtns.replaceChildren(tpl.content.cloneNode(true));
        replyBtns.dataset.closed = closed;
      },

      async addComment(event) {
        const form = event.target;
        const ta = form.querySelector('[name="content"]');
        const content = ta?.value?.trim();
        if (!content) return;
        const isInternal = form.querySelector('[name="is_internal"]')?.checked || false;
        const action = event.submitter?.value || 'comment';
        const submitBtn = event.submitter || form.querySelector('button[type="submit"]');
        await GP.refreshRegion({
          button: submitBtn, region: form, successMessage: t('Comment added'),
          errorMessage: t('Failed to add comment'),
          load: async () => {
            const comment = await GP.apiCall('/api/v1/support/tickets/' + ticketId + '/comments', 'POST', {
              content: content,
              is_internal: isInternal
            });
            if (current()) {
              this._injectComment({ ...comment, author_avatar_url: cfg.authorAvatar, author_role: cfg.authorRole });
              ta.value = '';
              this.replyTab = 'write';
              this.trackReply();
              const intCheck = form.querySelector('[name="is_internal"]');
              if (intCheck) intCheck.checked = false;
            }
            if (action === 'close' || action === 'reopen') {
              const fields = { status: action === 'close' ? 'closed' : 'open' };
              try {
                await GP.apiCall('/api/v1/support/tickets/' + ticketId, 'PUT', fields);
              } catch (err) {
                throw new Error(t('Comment added, but the ticket status could not be updated.') + ' ' + err.message);
              }
              if (current()) this._applyFieldUpdates(fields);
            }
            return current();
          },
        });
      },

      updateSelectedField(event) {
        const input = event.target;
        if (input.matches('.gh-sidebar-select input[type="hidden"]') &&
            ['status', 'priority', 'category'].includes(input.name)) {
          this.updateField(input.name, input.value);
        }
      },

      async updateField(field, value) {
        if (!current() || currentFields[field] === value) return;
        if (field === 'assigned_to' && GP.hasUnsavedState()) {
          const discard = await GP.confirmDialog({
            title: t('Unsaved changes'),
            message: t('Changing the assignee reloads this page. Discard your unsent reply?'),
            confirmText: t('Discard changes'), variant: 'danger',
          });
          if (!discard || !current()) return;
        }
        const payload = {};
        payload[field] = value || null;
        const input = document.querySelector('.gh-sidebar-select input[name="' + field + '"]');
        const saved = await GP.refreshRegion({
          region: document.querySelector('.gh-ticket-sidebar .card-body'),
          successMessage: t('Ticket updated'), errorMessage: t('Failed to update'),
          load: async () => {
            try {
              await GP.apiCall('/api/v1/support/tickets/' + ticketId, 'PUT', payload);
            } catch (err) {
              if (current() && input) input.value = currentFields[field];
              throw err;
            }
            if (!current()) return false;
            this._applyFieldUpdates(payload);
          },
        });
        // Render assignment-dependent permissions after preserving the success message.
        if (saved && current() && field === 'assigned_to') GP.reloadKeepScroll();
      },

      /** CSP-safe combined helper: assign + reset search + close dropdown
       *  (Alpine CSP parser disallows multi-statement @click expressions). */
      pickAssignee(user) {
        this.assigneeSearch = '';
        this.assigneeDropdown = false;
        this.updateField('assigned_to', user.username);
      }
    };
  }

  window.ticketDetailManager = ticketDetailManager;

  const onBeforeSwap = (evt) => {
    const target = evt.detail.target;
    if (target && (target.querySelector('#gh-ticket-cfg') || target.id === 'gh-ticket-cfg')) {
      GP.supportTicketDetailCleanup();
    }
  };

  document.addEventListener('htmx:beforeSwap', onBeforeSwap);

  GP.supportTicketDetailCleanup = function () {
    if (activeInstance) {
      try { activeInstance.destroy(); } catch (_) {}
      activeInstance = null;
    }
    document.removeEventListener('htmx:beforeSwap', onBeforeSwap);
  };
  GP.activePageCleanup = GP.supportTicketDetailCleanup;

})();
