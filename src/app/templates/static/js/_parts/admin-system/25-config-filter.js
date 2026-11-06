  /* -- Configuration table: the pills that used to be tabs --
     Feature flags, the LLM settings and the runtime environment are one table
     of parameter / value / environment variable. These pills narrow it to one
     group; "All" is the view the three tabs could not offer. */
  (function initConfigGroupFilter() {
    const group = document.querySelector('.config-group-filter');
    const table = document.getElementById('systemConfigTable');
    if (!group || !table || group._bound) return;
    group._bound = true;
    const rows = Array.from(table.querySelectorAll('tbody > tr'));
    new FilterPills('.config-group-filter', 'data-value', function (value) {
      let shown = 0;
      rows.forEach(function (row) {
        const hide = value !== 'all' && row.dataset.group !== value;
        row.classList.toggle('d-none', hide);
        if (!hide) shown += 1;
      });
      // This one toggles rows directly rather than going through a paginator,
      // so it says "nothing matches" itself.
      if (GP.tableFilteredToNothing) {
        GP.tableFilteredToNothing(table.querySelector('tbody'), shown, rows.length);
      }
      writeCount(shown, rows.length);
    });
    // No paginator here, so this table writes its own header count - the same
    // sentence every other table's paginator writes into the same component.
    function writeCount(shown, total) {
      const slot = document.getElementById('configCount');
      if (!slot) return;
      slot.textContent = shown === total
        ? `${t('Showing')} ${total}`
        : `${t('Showing')} ${shown} ${t('of')} ${total}`;
    }
    writeCount(rows.length, rows.length);
  })();
