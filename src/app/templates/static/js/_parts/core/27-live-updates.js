/* ============================================
   Live update announcements
   ============================================ */
/* Pages refreshed themselves silently whenever the backend pushed a change, so
   numbers moved under the reader with no explanation of why. Say what arrived.

   This lives in core because EVERY page holds the dashboard stream (the sidebar
   owns it for badges; the dashboard page takes that same connection over), so
   both callers share one implementation and only one of them is ever connected.

   Bursts are the normal case - one student pushing produces several events in
   seconds, a re-synced project produces many - so notices are coalesced into a
   single message reporting how many changes it covers, rather than one toast
   per event. */
const _LIVE_UPDATE_LABELS = {
  webhook_merge_request: 'merge requests',
  webhook_issue: 'issues',
  webhook_note: 'comments',
  webhook_pipeline: 'pipelines',
  webhook_push: 'pushes',
  webhook_member: 'members',
  webhook_tag_push: 'tags',
};

let _liveUpdateKinds = [];
let _liveUpdateCount = 0;

const _flushLiveUpdate = debounce(function () {
  const count = _liveUpdateCount;
  const kinds = _liveUpdateKinds.slice();
  _liveUpdateCount = 0;
  _liveUpdateKinds = [];
  if (!count) return;
  const toast = window.showToast || GP.showToast;
  if (typeof toast !== 'function') return;
  const tr = (s) => GP.t(s);

  const named = kinds.map((k) => _LIVE_UPDATE_LABELS[k]).filter(Boolean).map(tr);
  const unique = named.filter((v, i) => named.indexOf(v) === i);
  const what = unique.length ? unique.join(', ') : tr('activity');
  const msg =
    count === 1
      ? tr('Live update: {what}').replace('{what}', what)
      : tr('Live update: {what} ({n} changes)')
          .replace('{what}', what)
          .replace('{n}', String(count));
  toast(msg, 'info');
}, 2500);

function announceLiveUpdate(ev) {
  _liveUpdateCount += 1;
  try {
    const kind = JSON.parse((ev && ev.data) || '{}').event;
    if (kind && _liveUpdateKinds.indexOf(kind) === -1) _liveUpdateKinds.push(kind);
  } catch (_) {
    /* a payload we cannot read still counts as a change */
  }
  _flushLiveUpdate();
}

if (typeof window.GP === 'object') {
  window.GP.announceLiveUpdate = announceLiveUpdate;
}

// Expose on GP namespace
if (typeof window.GP === 'object') {
  window.GP.initTippy = initTippy;
  window.GP.bindTippy = initTippy;
  window.GP.initCardInfoTips = initCardInfoTips;
}
