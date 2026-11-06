  /* The Analytics "Sync" button was removed: it fired a full GitLab sync, a
     course-level action that already lives on the course page and on Activity,
     offered from a page that only reads data. Its handler went with it - 178
     lines that could never run again - and so did the tour step that pointed at
     `#btnRefreshAnalytics`, which would have targeted a missing element and
     stalled the course tour. */
