/* Course Assistant page.

   The page is server-rendered; what is this page's own are its four actions -
   connect the bot, disconnect it, save the tools, prepare the exercise - and
   keeping the activity card current. Connect, disconnect and save post their
   form, ask for the outcome as JSON, and the page then comes back from the
   server as it now is, as on the Teachers page. Prepare exercise is a
   background job like a sync: the top bar follows it, and when it ends the
   page shows the result. The three forms name their handler in
   `data-submit-action`, so the core's submit dispatch runs it and its form
   interception leaves them alone - one request per submit.

   The activity card is redrawn from the server (GET .../assistant/activity)
   by its Refresh button, at the end of an exercise run and whenever the
   course's live stream says the bot did something. The table is worked by the
   shared components: ClientPaginator, TableFilter (the search) and FilterPills
   (the tool tabs), with sortable-table.js on the headers. */

// Wrapped in an IIFE like every other page script: a top-level `const GP` here
// collides with the one core.bundle.js declares and aborts the whole file.
(function initCourseAssistantPage() {
  'use strict';
  const GP = window.GP || {};
  GP.runPageCleanup();

  const { t } = GP;
  const EXERCISE_JOB = 'assistant_exercise';

  /* What the server's refusal codes mean to the reader. */
  const REFUSALS = {
    empty: t('Paste the token first.'),
    read_token: t("That is GitPulse's read-only token. The assistant needs a token of its own."),
    invalid: t('GitLab did not accept this token.'),
    scope: t('The token needs the api scope.'),
    unreachable: t('GitLab could not be reached. Try again in a moment.'),
    not_connected: t('Connect the bot account first.'),
    token_unusable: t('The bot token does not work. Connect a new one first.'),
    already_running: t('The exercise is being prepared right now.'),
    tool_off: t('Turn on Issues and merge requests and save first.'),
    no_projects: t('Choose at least one project.'),
    queue_unavailable: t('The background queue is unavailable. Try again in a moment.'),
  };

  const TOOLS_FORM = '#assistantToolsForm';
  const pageOwner = document.querySelector('.tabs-nav[data-course-id]');
  const courseId = pageOwner?.dataset.courseId || '';
  const activityCard = document.getElementById('assistantActivityCard');
  let reloadTimer = 0;
  let activityRequest = 0;

  /** Post a form; resolve with the response and its JSON body. */
  function send(form, button) {
    if (button) GP.setButtonLoading(button, true);
    return fetch(form.action, {
      method: 'POST', body: new FormData(form), credentials: 'same-origin', headers: { Accept: 'application/json' },
    })
      .then(function (resp) {
        return resp.json().catch(function () { return {}; }).then(function (data) {
          return { ok: resp.ok && data.ok === true, data: data };
        });
      })
      .catch(function () { return { ok: false, data: {} }; })
      .finally(function () { if (button) GP.setButtonLoading(button, false); });
  }

  function refusal(data) {
    return REFUSALS[data.error] || t('Could not save the change. Try again.');
  }

  /* As Settings' Save does: the toast is raised here, so the button that was
     clicked reports "Done" in place, and the page comes back a moment later -
     the reload carries the toast over. Raising it only for the next page and
     reloading at once left the button without its third state. */
  function done(message, form) {
    if (!pageOwner?.isConnected || (form && !form.isConnected)) return;
    GP.showToast(message, 'success');
    scheduleReload(800, form || pageOwner);
  }

  function scheduleReload(delay, owner = pageOwner) {
    clearTimeout(reloadTimer);
    reloadTimer = setTimeout(function () {
      if (!pageOwner?.isConnected || !owner?.isConnected) return;
      if (GP.hasUnsavedState()) { refreshActivityQuietly(); return; }
      GP.reloadKeepScroll();
    }, delay);
  }

  /* -- The activity card, redrawn from the server --
     Only the card's BODY is swapped. The header - and the Refresh button in
     it - stays the same element, so the button goes through the states every
     Refresh does (working, "Done", back), as on Job History; swapping the
     whole card replaced the working button with a fresh idle one at once. */
  function swapActivityCard(html, card) {
    const next = new DOMParser().parseFromString(html, 'text/html')
      .querySelector('#assistantActivityCard > .card-body');
    const current = card.querySelector(':scope > .card-body');
    if (!next || !current) throw new Error(t('Could not load the assistant activity.'));
    current.replaceChildren(...next.childNodes);
    GP.initTippy(current);
    GP.scanAvatars(current);
    GP.initTableScroll(current);
    const table = current.querySelector('table[data-sortable]');
    if (table && window.SortableTable) window.SortableTable.initTable(table);
    initTable();
  }

  async function loadActivity(options) {
    const card = activityCard;
    if (!card?.isConnected || !card.dataset.refreshUrl) return false;
    const request = ++activityRequest;
    const query = window.location.search;
    const tbody = card.querySelector('#assistantActivityTable tbody');
    GP.tableLoading(tbody, 7);
    try {
      const html = await GP.apiCall(card.dataset.refreshUrl + query, 'GET', null, {
        timeoutMs: 10000, maxRetries: 0, ...options,
        key: 'assistant-activity:' + courseId, responseType: 'text', headers: { Accept: 'text/html' },
      });
      if (!card.isConnected || request !== activityRequest) return false;
      if (query !== window.location.search || card.querySelector('.card-body')?.contains(document.activeElement)) {
        refreshActivityQuietly();
        return false;
      }
      swapActivityCard(html, card);
    } finally {
      if (!tbody?.isConnected || request === activityRequest) GP.tableLoaded(tbody);
    }
  }

  /* A redraw nobody asked for (the live stream) waits while the reader is in
     the card - typing a search, on a tab - and stays silent either way. */
  let liveTimer = 0;
  function refreshActivityQuietly() {
    clearTimeout(liveTimer);
    liveTimer = setTimeout(function () {
      if (!activityCard?.isConnected) return;
      if (activityCard.querySelector('.card-body')?.contains(document.activeElement)) { refreshActivityQuietly(); return; }
      loadActivity().catch(function () { /* the next event or Refresh tries again */ });
    }, 1500);
  }

  /* -- The forms' actions (their `data-submit-action`) -- */
  function connectAssistantBot(event) {
    const form = event.target;
    send(form, document.getElementById('btnConnectSubmit')).then(function (out) {
      if (!out.ok) { GP.showToast(refusal(out.data), 'danger'); return; }
      done(t('Bot connected as') + ' @' + (out.data.bot_username || ''));
    });
  }

  function saveAssistantTools(event) {
    const form = event.target;
    const button = document.getElementById('btnSaveAssistantTools');
    form.querySelectorAll('.input-error').forEach(function (el) { el.classList.remove('input-error'); });
    send(form, button).then(function (out) {
      if (!form.isConnected) return;
      if (out.ok) {
        GP.resetSaveGuard(TOOLS_FORM, form);
        done(t('Assistant settings saved'), form);
        return;
      }
      (out.data.fields || []).forEach(function (name) {
        const field = form.querySelector('[name="' + name + '"]');
        if (field) field.classList.add('input-error');
      });
      GP.showToast(out.data.fields ? t('Some values are not valid - check the highlighted fields.') : refusal(out.data), 'danger');
      GP.recheckSaveGuardFor(button);
    });
  }

  /* Prepare exercise: queued as a BackgroundJob, followed by the top bar like
     a sync. When it ends the page comes back with the result - unless the
     reader has unsaved tool settings, which a reload would throw away; then
     only the activity card is redrawn and the bar's toast says the rest. */
  function prepareAssistantExercise(event) {
    const button = document.getElementById('btnPrepareSubmit');
    send(event.target, button).then(function (out) {
      if (!out.ok) { GP.showToast(refusal(out.data), 'danger'); return; }
      if (typeof closeModal === 'function') closeModal('assistantExerciseModal');
      const prepare = document.getElementById('btnPrepareExercise');
      if (prepare) prepare.disabled = true;
      const meta = { courseId: String(courseId), jobKind: EXERCISE_JOB, jobId: out.data.job_id };
      if (!out.data.job_id || typeof showGlobalJob !== 'function' || typeof startGenericStatusPolling !== 'function') {
        done(t('Preparing the exercise - the issues appear under Activity in a moment.'));
        return;
      }
      showGlobalJob(t('Preparing the exercise...'), EXERCISE_JOB, meta);
      startGenericStatusPolling(EXERCISE_JOB, '/api/v1/jobs/' + out.data.job_id, {
        messageRunning: function () { return t('Preparing the exercise...'); },
        messageDone: function (data) { return t((data && data.result_summary) || 'Exercise prepared'); },
        messageFailed: function (data) {
          return t((data && (data.error_message || data.message)) || 'Preparing the exercise failed. Try again.');
        },
      });
    });
  }

  function onJobComplete(ev) {
    const d = (ev && ev.detail) || {};
    if (d.jobType !== EXERCISE_JOB) return;
    if (d.meta?.courseId && String(d.meta.courseId) !== courseId) return;
    if (GP.hasUnsavedState()) {
      loadActivity().catch(function () { /* Refresh is there */ });
      return;
    }
    scheduleReload(1200);
  }

  function onClick(event) {
    if (event.target.closest('#btnRefreshAssistantActivity')) {
      GP.refreshRegion({
        button: event.target.closest('#btnRefreshAssistantActivity'),
        load: loadActivity,
        successMessage: t('Assistant activity reloaded'),
        errorMessage: t('Could not load the assistant activity.'),
      });
      return;
    }
    if (!event.target.closest('#btnDisconnectBot')) return;
    const form = document.getElementById('assistantDisconnectForm');
    if (!form) return;
    GP.confirmDialog({
      title: t('Disconnect the bot?'),
      message: t('Every tool stops until a token is connected again. What the assistant already did in GitLab stays.'),
      confirmText: t('Disconnect'),
      variant: 'danger',
    }).then(function (ok) {
      if (!ok) return;
      send(form, null).then(function (out) {
        if (!out.ok) { GP.showToast(refusal(out.data), 'danger'); return; }
        done(t('Bot disconnected'));
      });
    });
  }

  /* -- The activity table: the shared components, with this table's tool tabs -- */
  function initTable() {
    const tbody = document.querySelector('#assistantActivityTable tbody');
    if (!tbody || tbody._clientPaginator) return;
    const paginator = new ClientPaginator({
      tbodySelector: '#assistantActivityTable tbody',
      controlsSelector: '#paginationControls',
      storageKey: 'course-assistant',
      showPerPage: true,
    }).register('assistantActivityTable');
    const tabs = new FilterPills('.assistant-tool-filter', 'data-value', function () {
      filter.apply();
    });
    const filter = new TableFilter({
      inputSelector: '#assistantSearch',
      tbodySelector: '#assistantActivityTable tbody',
      paginator: paginator,
      urlParams: () => ({ tool: tabs.activeValue }),
      rowFilter: row => tabs.activeValue === 'all' || row.dataset.tool === tabs.activeValue,
    });
    filter.apply();
  }

  const toolsForm = document.querySelector(TOOLS_FORM);
  // An archived course's fields are disabled; there is nothing to guard.
  if (toolsForm && !toolsForm.querySelector(':disabled[name="conflict_file_path"]')) {
    GP.initSaveGuard(TOOLS_FORM, '#btnSaveAssistantTools', { dirtyKey: 'assistant_tools' });
  }

  // What the page says about its own state when it opens (the webhook), as
  // the Events page does: once - still on screen from the page before, it is
  // not raised again.
  let cfg = {};
  try {
    const el = document.getElementById('gp-page-config');
    if (el) cfg = JSON.parse(el.textContent);
  } catch (_) { /* no config, no warning */ }
  const warning = cfg.startupWarning;
  if (warning && warning.message) {
    GP.showToast(warning.message, 'warning', Number(warning.durationMs || 12000), { once: true });
  }

  /* The course's live stream: the bot acted (a webhook ran a tool) or an
     exercise run ended - the activity card catches up. A reconnect after a
     drop catches up too; the first connect trusts the server render. */
  let stream = null;
  if (courseId && document.getElementById('assistantActivityCard')) {
    let connectedOnce = false;
    stream = GP.sse({
      url: '/api/v1/courses/' + encodeURIComponent(courseId) + '/stream',
      events: {
        connected: function () {
          if (!connectedOnce) { connectedOnce = true; return; }
          refreshActivityQuietly();
        },
        update: function (e) {
          let d = null;
          try { d = JSON.parse(e.data); } catch (_) { return; }
          if (d && d.event === 'assistant_activity') refreshActivityQuietly();
        },
      },
    });
  }

  window.connectAssistantBot = connectAssistantBot;
  window.saveAssistantTools = saveAssistantTools;
  window.prepareAssistantExercise = prepareAssistantExercise;
  document.addEventListener('click', onClick);
  window.addEventListener('gp:job-complete', onJobComplete);
  GP.activePageCleanup = function () {
    document.removeEventListener('click', onClick);
    window.removeEventListener('gp:job-complete', onJobComplete);
    clearTimeout(liveTimer);
    clearTimeout(reloadTimer);
    if (stream) stream.close();
  };
  initTable();
})();
