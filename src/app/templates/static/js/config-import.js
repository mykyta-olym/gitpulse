/* -- Shared Config Import module --
 *
 * Provides parseConfig, showPreview, and initConfigImport to both
 * the dashboard (Import Course from JSON) and course-settings
 * (Import Full Course Configuration) modals.
 *
 * Usage:
 *   GP.ConfigImport.init({ ... options ... });
 */
;(function () {
  'use strict';

  const GP = window.GP || {};
  const _t = GP.t || function (s) { return s; };
  const _esc = GP.escapeHtml || function (s) { return String(s != null ? s : ''); };

  // -- Parse & validate JSON config --
  function parseConfig(text, showErrors) {
    const showToast = GP.showToast;
    try {
      const config = JSON.parse(text);
      if (!config || typeof config !== 'object' || Array.isArray(config)) {
        if (showErrors) showToast(_t('Invalid config: expected a JSON object'), 'warning');
        return null;
      }
      if (!config.$schema) {
        config.$schema = 'gitpulse/full-config/v2';
      }

      const warnings = [];
      const _VALID_CATEGORIES = ['issue', 'mr', 'review', 'ci', 'commit', 'custom'];
      const _VALID_RULE_TYPES = ['count', 'field_check', 'ratio', 'word_count', 'avg_word_count'];

      // -- Course metadata validations --
      const c = config.course;
      if (c) {
        if (c.code && String(c.code).length > 20) {
          warnings.push(_t('course.code exceeds 20 characters'));
        }
        if (c.name && String(c.name).length > 200) {
          warnings.push(_t('course.name exceeds 200 characters'));
        }
        if (c.academic_year) {
          if (String(c.academic_year).length > 10) {
            warnings.push(_t('course.academic_year exceeds 10 characters'));
          }
          if (String(c.academic_year).indexOf('/') === -1) {
            warnings.push(_t('course.academic_year must contain "/" (e.g. 2025/2026)'));
          }
        }
        if (c.semester && c.semester !== 'winter' && c.semester !== 'summer') {
          warnings.push(_t('course.semester must be "winter" or "summer"'));
        }
        if (c.description && String(c.description).length > 2000) {
          warnings.push(_t('course.description exceeds 2000 characters'));
        }
        if (c.teacher_usernames && Array.isArray(c.teacher_usernames)) {
          warnings.push(_t('Config includes teacher_usernames') + ' (' + c.teacher_usernames.length + ') - ' + _t('memberships will be synced on import'));
        }
      }

      // -- Settings validations --
      const s = config.settings;
      if (s) {
        if (typeof s.green_threshold === 'number') {
          if (s.green_threshold < 0 || s.green_threshold > 1) {
            warnings.push(_t('green_threshold must be between 0.0 and 1.0'));
          }
        }
        if (typeof s.yellow_threshold === 'number') {
          if (s.yellow_threshold < 0 || s.yellow_threshold > 1) {
            warnings.push(_t('yellow_threshold must be between 0.0 and 1.0'));
          }
        }
        if (typeof s.green_threshold === 'number' && typeof s.yellow_threshold === 'number') {
          if (s.green_threshold <= s.yellow_threshold) {
            warnings.push(_t('green_threshold must be > yellow_threshold'));
          }
        }
        if (s.semester_start_date && !/^\d{4}-\d{2}-\d{2}$/.test(s.semester_start_date)) {
          warnings.push(_t('semester_start_date: expected YYYY-MM-DD'));
        }
        if (s.semester_end_date && !/^\d{4}-\d{2}-\d{2}$/.test(s.semester_end_date)) {
          warnings.push(_t('semester_end_date: expected YYYY-MM-DD'));
        }
        if (s.mr_creation_deadline && !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?/.test(s.mr_creation_deadline)) {
          warnings.push(_t('mr_creation_deadline: expected ISO 8601 datetime'));
        }
        if (s.merge_deadline && !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?/.test(s.merge_deadline)) {
          warnings.push(_t('merge_deadline: expected ISO 8601 datetime'));
        }
        if (s.branch_pattern) {
          try { new RegExp(s.branch_pattern); } catch (e) {
            warnings.push(_t('branch_pattern: invalid regex') + ' - ' + e.message);
          }
          if (String(s.branch_pattern).length > 200) {
            warnings.push(_t('branch_pattern exceeds 200 characters'));
          }
        }
        if (s.gitlab_group_path && String(s.gitlab_group_path).length > 300) {
          warnings.push(_t('gitlab_group_path exceeds 300 characters'));
        }
        ['min_reviews_per_mr', 'min_review_word_count', 'min_distinct_mrs_reviewed'].forEach(function (k) {
          if (typeof s[k] === 'number' && (s[k] < 1 || s[k] > 100)) {
            warnings.push(k + ': ' + _t('must be between 1 and 100'));
          }
        });
        if (s.mr_template_required_sections && Array.isArray(s.mr_template_required_sections) && s.mr_template_required_sections.length > 100) {
          warnings.push(_t('mr_template_required_sections: exceeds 100 entries'));
        }
        if (s.test_file_patterns && Array.isArray(s.test_file_patterns) && s.test_file_patterns.length > 100) {
          warnings.push(_t('test_file_patterns: exceeds 100 entries'));
        }
        if (s.llm_course_type && ['default', 'zsi', 'devops'].indexOf(s.llm_course_type) === -1) {
          warnings.push(_t('llm_course_type must be "default", "zsi", or "devops"'));
        }
        if (s.llm_resource_urls && Array.isArray(s.llm_resource_urls)) {
          s.llm_resource_urls.forEach(function (u, i) {
            if (u.url && !/^https?:\/\//.test(u.url)) {
              warnings.push('llm_resource_urls[' + i + ']: ' + _t('URL must start with http:// or https://'));
            }
            if (u.url && String(u.url).length > 500) {
              warnings.push('llm_resource_urls[' + i + ']: ' + _t('URL exceeds 500 characters'));
            }
          });
        }
      }

      // -- Builtin checks validations --
      const allCheckCodes = {};
      if (config.builtin_checks) {
        if (config.builtin_checks.length > 20) {
          warnings.push(_t('builtin_checks: exceeds maximum of 20 entries'));
        }
        config.builtin_checks.forEach(function (ch) {
          if (ch.check_code) {
            if (!/^R/.test(ch.check_code)) {
              warnings.push(ch.check_code + ': ' + _t('builtin check_code must start with R'));
            }
            allCheckCodes[ch.check_code] = true;
          }
          if (typeof ch.weight === 'number' && (ch.weight < 0 || ch.weight > 1)) {
            warnings.push((ch.check_code || '?') + ': ' + _t('weight must be between 0.0 and 1.0'));
          }
          if (ch.category && _VALID_CATEGORIES.indexOf(ch.category) === -1) {
            warnings.push((ch.check_code || '?') + ': ' + _t('invalid category') + ' "' + ch.category + '"');
          }
        });
      }

      // -- Weight sum (the score divides by it, so only zero is a problem) --
      let tw = 0;
      (config.builtin_checks || []).forEach(function (ch) { if (ch.is_active) tw += ch.weight || 0; });
      (config.custom_checks || []).forEach(function (ch) { if (ch.is_active) tw += ch.weight || 0; });
      if ((config.builtin_checks || config.custom_checks) && tw <= 0) {
        warnings.push(_t('The active checks have no weight, so no score can be computed.'));
      }

      // -- Custom check validations --
      const seenCodes = {};
      if (config.custom_checks) {
        if (config.custom_checks.length > 50) {
          warnings.push(_t('custom_checks: exceeds maximum of 50 entries'));
        }
        config.custom_checks.forEach(function (ch) {
          if (!ch.check_code || !ch.name) {
            warnings.push(_t('Custom check missing code or name'));
          }
          if (ch.check_code && !/^C\d+$/.test(ch.check_code)) {
            warnings.push(ch.check_code + ': ' + _t('must start with C followed by digits'));
          }
          if (ch.check_code && seenCodes[ch.check_code]) {
            warnings.push(_t('Duplicate custom check code') + ': ' + ch.check_code);
          }
          if (ch.check_code) {
            seenCodes[ch.check_code] = true;
            allCheckCodes[ch.check_code] = true;
          }
          if (typeof ch.weight === 'number' && (ch.weight < 0 || ch.weight > 1)) {
            warnings.push((ch.check_code || '?') + ': ' + _t('weight must be between 0.0 and 1.0'));
          }
          if (ch.category && _VALID_CATEGORIES.indexOf(ch.category) === -1) {
            warnings.push((ch.check_code || '?') + ': ' + _t('invalid category') + ' "' + ch.category + '"');
          }
          if (ch.name && String(ch.name).length > 200) {
            warnings.push((ch.check_code || '?') + ': ' + _t('name exceeds 200 characters'));
          }
          // Evaluation rule validation
          if (ch.evaluation_rule && typeof ch.evaluation_rule === 'object') {
            const rule = ch.evaluation_rule;
            if (rule.type && _VALID_RULE_TYPES.indexOf(rule.type) === -1) {
              warnings.push((ch.check_code || '?') + ': ' + _t('invalid evaluation_rule type') + ' "' + rule.type + '"');
            }
            if (rule.type === 'count' && (!rule.entity || !rule.operator || rule.threshold == null)) {
              warnings.push((ch.check_code || '?') + ': ' + _t('count rule requires entity, operator, threshold'));
            }
            if (rule.type === 'field_check' && (!rule.entity || !rule.field || rule.expected == null)) {
              warnings.push((ch.check_code || '?') + ': ' + _t('field_check rule requires entity, field, expected'));
            }
            if (rule.type === 'ratio' && (!rule.entity || !rule.numerator_filter || !rule.denominator_filter)) {
              warnings.push((ch.check_code || '?') + ': ' + _t('ratio rule requires entity, numerator_filter, denominator_filter'));
            }
          }
        });
      }

      // -- Weekly deadline validations --
      const seenWeeks = {};
      if (config.weekly_deadlines) {
        if (config.weekly_deadlines.length > 52) {
          warnings.push(_t('weekly_deadlines: exceeds maximum of 52 entries'));
        }
        config.weekly_deadlines.forEach(function (wd, i) {
          if (!wd.week || typeof wd.week !== 'number') {
            warnings.push('weekly_deadlines[' + i + ']: ' + _t('missing or invalid week'));
          } else {
            if (wd.week < 1 || wd.week > 52) {
              warnings.push('weekly_deadlines[' + i + ']: ' + _t('week must be between 1 and 52'));
            }
            if (seenWeeks[wd.week]) {
              warnings.push('weekly_deadlines: ' + _t('duplicate week') + ' ' + wd.week);
            }
            seenWeeks[wd.week] = true;
          }
          if (wd.label && String(wd.label).length > 100) {
            warnings.push('weekly_deadlines[' + i + ']: ' + _t('label exceeds 100 characters'));
          }
          if (wd.expected_checks && Array.isArray(wd.expected_checks)) {
            if (wd.expected_checks.length > 30) {
              warnings.push('weekly_deadlines[' + i + ']: ' + _t('exceeds 30 expected_checks'));
            }
            // Cross-reference: check codes in expected_checks must exist
            wd.expected_checks.forEach(function (code) {
              if (Object.keys(allCheckCodes).length > 0 && !allCheckCodes[code]) {
                warnings.push('weekly_deadlines week ' + wd.week + ': ' + _t('unknown check') + ' "' + code + '"');
              }
            });
          }
          if (wd.mr_deadline && !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?/.test(wd.mr_deadline)) {
            warnings.push('weekly_deadlines[' + i + ']: ' + _t('mr_deadline: expected ISO 8601 datetime'));
          }
          if (wd.merge_deadline && !/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?/.test(wd.merge_deadline)) {
            warnings.push('weekly_deadlines[' + i + ']: ' + _t('merge_deadline: expected ISO 8601 datetime'));
          }
        });
      }

      // -- Cross-reference: enabled_checks in settings --
      if (s && s.enabled_checks && Array.isArray(s.enabled_checks) && Object.keys(allCheckCodes).length > 0) {
        s.enabled_checks.forEach(function (code) {
          if (!allCheckCodes[code]) {
            warnings.push('settings.enabled_checks: ' + _t('unknown check') + ' "' + code + '"');
          }
        });
      }

      config._clientWarnings = warnings;
      if (warnings.length > 0 && showErrors) {
        showToast(warnings.length + ' ' + _t('validation warnings found'), 'warning');
      }
      return config;
    } catch (e) {
      if (showErrors) GP.showToast(_t('Invalid JSON') + ': ' + e.message, 'danger');
      return null;
    }
  }

  // -- Build preview HTML --
  function showPreview(config, opts) {
    const preview = document.getElementById(opts.previewId);
    const summary = document.getElementById(opts.summaryId);
    const sections = document.getElementById(opts.sectionsId);
    const applyBtn = document.getElementById(opts.applyBtnId);
    if (!preview || !summary) return;

    const cm = config.course || config.source_course || {};
    const source = config.source_course || {};
    const exported = config.exported_at ? GP.timeHtml(config.exported_at) : '';
    const disabledFeatures = opts.disabledFeatures || {};

    // -- Summary --
    let html = '<ul class="prop-list">';
    if (cm.code) {
      html += '<li><strong>' + _t('Course') + ':</strong> ' + _esc(cm.code || '') + ' - ' + _esc(cm.name || '') + '</li>';
      /* The stored value is "winter" / "summer"; the reader gets the word. A
         missing semester is shown as the one the course would actually get -
         Course.semester defaults to winter - rather than as nothing. */
      html += '<li><strong>' + _t('Academic Year') + ':</strong> ' + _esc(GP.periodLabel(cm.academic_year || '', cm.semester || 'winter')) + '</li>';
    }
    if (exported) html += '<li><strong>' + _t('Exported') + ':</strong> ' + _esc(exported) + '</li>';
    if (source.code && source.code !== cm.code) html += '<li><strong>' + _t('Source') + ':</strong> ' + _esc(source.code) + (source.academic_year ? ' (' + _esc(GP.periodLabel(source.academic_year, source.semester || 'winter')) + ')' : '') + '</li>';
    html += '</ul>';
    summary.innerHTML = html;

    // -- Sections breakdown --
    let sHtml = '<div class="full-config-sections">';
    const sectionDefs = [
      { key: 'course', icon: 'book', label: _t('Course Metadata') },
      { key: 'settings', icon: 'settings', label: _t('Settings') },
      { key: 'builtin_checks', icon: 'shield', label: _t('Built-in Checks') },
      { key: 'custom_checks', icon: 'plus-circle', label: _t('Custom Checks') },
      { key: 'weekly_deadlines', icon: 'calendar', label: _t('Weekly Deadlines') },
      { key: 'assistant', icon: 'bot', label: _t('Classroom Assistant'), featureKey: 'classroom_assistant' },
    ];
    let includedCount = 0;
    sectionDefs.forEach(function (sec) {
      const present = config[sec.key] != null;
      const disabled = sec.featureKey && disabledFeatures[sec.featureKey];
      if (present && !disabled) includedCount++;
      let detail = '';
      const subItems = [];
      if (present) {
        if (sec.key === 'builtin_checks') {
          const bc = config.builtin_checks;
          const activeB = bc.filter(function (c) { return c.is_active; }).length;
          detail = bc.length + ' ' + _t('checks') + ' (' + activeB + ' ' + _t('active') + ')';
        } else if (sec.key === 'custom_checks') {
          const cc = config.custom_checks;
          const activeC = cc.filter(function (c) { return c.is_active; }).length;
          detail = cc.length + ' ' + _t('checks') + ' (' + activeC + ' ' + _t('active') + ')';
        } else if (sec.key === 'weekly_deadlines') {
          detail = (Array.isArray(config.weekly_deadlines) ? config.weekly_deadlines.length : 0) + ' ' + _t('weeks');
        } else if (sec.key === 'assistant') {
          // Tool settings only: a configuration file never carries the bot or its token.
          const as = config.assistant || {};
          const on = [];
          if (as.push_review_enabled) on.push(_t('Push review'));
          if (as.conflict_enabled) on.push(_t('Merge conflict'));
          if (as.mr_review_enabled) on.push(_t('Issues and merge requests'));
          detail = on.length ? on.join(', ') : _t('no tool on');
        } else if (sec.key === 'settings') {
          const st = config.settings || {};
          const fieldCount = Object.keys(st).length;
          detail = fieldCount + ' ' + _t('fields');
          // Detailed sub-items for settings
          if (st.branch_pattern) subItems.push(_t('Branch pattern') + ': ' + _esc(st.branch_pattern));
          if (st.gitlab_group_path) subItems.push(_t('GitLab group') + ': ' + _esc(st.gitlab_group_path));
          if (typeof st.green_threshold === 'number' || typeof st.yellow_threshold === 'number') {
            subItems.push(_t('Thresholds') + ': ' + _t('Green') + ' ≥ ' + (st.green_threshold != null ? st.green_threshold : '-') + ', ' + _t('Yellow') + ' ≥ ' + (st.yellow_threshold != null ? st.yellow_threshold : '-'));
          }
          if (typeof st.min_reviews_per_mr === 'number') subItems.push(_t('Min reviews per MR') + ': ' + st.min_reviews_per_mr);
          if (typeof st.min_review_word_count === 'number') subItems.push(_t('Min review word count') + ': ' + st.min_review_word_count);
          if (typeof st.min_distinct_mrs_reviewed === 'number') subItems.push(_t('Min distinct MRs reviewed') + ': ' + st.min_distinct_mrs_reviewed);
          if (st.semester_start_date) subItems.push(_t('Semester start') + ': ' + _esc(st.semester_start_date));
          if (st.semester_end_date) subItems.push(_t('Semester end') + ': ' + _esc(st.semester_end_date));
          if (st.skip_auto_archive === true) subItems.push(_t('Skip auto-archive') + ': ' + _t('yes'));
          if (st.mr_creation_deadline) subItems.push(_t('MR creation deadline') + ': ' + _esc(st.mr_creation_deadline));
          if (st.merge_deadline) subItems.push(_t('Merge deadline') + ': ' + _esc(st.merge_deadline));
          if (st.mr_template_required_sections && st.mr_template_required_sections.length) subItems.push(_t('MR template sections') + ': ' + st.mr_template_required_sections.length);
          if (st.test_file_patterns && st.test_file_patterns.length) subItems.push(_t('Test file patterns') + ': ' + st.test_file_patterns.length);
          if (st.enabled_checks && st.enabled_checks.length) subItems.push(_t('Enabled checks') + ': ' + st.enabled_checks.join(', '));
          // LLM sub-items inside settings
          const hasLlm = st.llm_course_type || (st.llm_resource_urls && st.llm_resource_urls.length) || st.llm_custom_prompt;
          if (hasLlm) {
            let llmLabel = _t('LLM') + ': ';
            const llmParts = [];
            if (st.llm_course_type) llmParts.push(_t('type') + ' = ' + _esc(st.llm_course_type));
            if (st.llm_resource_urls && st.llm_resource_urls.length) llmParts.push(st.llm_resource_urls.length + ' ' + _t('resource URLs'));
            if (st.llm_custom_prompt) llmParts.push(_t('custom prompt'));
            llmLabel += llmParts.join(', ');
            if (disabledFeatures.llm_suggestions) {
              llmLabel += ' ' + GP.iconSvg('slash', 'xs') + ' ' + _t('LLM feature disabled globally');
            }
            subItems.push(llmLabel);
          } else if (disabledFeatures.llm_suggestions) {
            subItems.push(_t('LLM') + ': ' + GP.iconSvg('slash', 'xs') + ' ' + _t('feature disabled globally'));
          }
        } else if (sec.key === 'course') {
          const crs = config.course;
          detail = _esc(crs.code || '') + ' - ' + _esc(crs.name || '');
          if (crs.description) subItems.push(_t('Description') + ': ' + _esc(crs.description.length > 80 ? crs.description.substring(0, 80) + '...' : crs.description));
          if (crs.teacher_usernames && crs.teacher_usernames.length) subItems.push(_t('Teachers') + ': ' + crs.teacher_usernames.map(_esc).join(', '));
          if (typeof crs.is_active === 'boolean') subItems.push(_t('Active') + ': ' + (crs.is_active ? _t('Yes') : _t('No')));
        }
      }

      sHtml += '<div class="full-config-section-item ' + (present && !disabled ? 'included' : 'skipped') + '">';
      sHtml += '<span class="full-config-section-status">' + GP.iconSvg(present && !disabled ? 'check' : disabled ? 'slash' : 'minus', 'sm') + '</span>';
      sHtml += '<strong>' + _esc(sec.label) + '</strong>';
      if (disabled && present) sHtml += ' <span class="text-warning">(' + _t('feature disabled - will be skipped') + ')</span>';
      else if (detail) sHtml += ' <span class="muted">(' + detail + ')</span>';
      if (subItems.length > 0) {
        sHtml += '<ul class="config-preview-details">';
        subItems.forEach(function (item) { sHtml += '<li>' + item + '</li>'; });
        sHtml += '</ul>';
      }
      sHtml += '</div>';
    });
    sHtml += '</div>';
    sHtml += '<p class="muted mt-2">' + includedCount + ' / ' + sectionDefs.length + ' ' + _t('sections will be applied') + '</p>';

    // -- Weight sum --
    if (config.builtin_checks || config.custom_checks) {
      let tw = 0;
      (config.builtin_checks || []).forEach(function (c) { if (c.is_active) tw += c.weight || 0; });
      (config.custom_checks || []).forEach(function (c) { if (c.is_active) tw += c.weight || 0; });
      sHtml += '<p class="' + (Math.abs(tw - 1.0) < 0.05 ? 'text-success' : 'text-warning') + '"><strong>' + _t('Total check weight') + ':</strong> ' + tw.toFixed(2) + '</p>';
    }

    // -- Warnings --
    const cw = config._clientWarnings || [];
    if (cw.length > 0) {
      sHtml += '<div class="full-config-warnings mt-3">';
      sHtml += '<h4 class="ce-panel-title text-warning">' + _t('Warnings') + ' (' + cw.length + ')</h4>';
      sHtml += '<ul class="prop-list">';
      cw.forEach(function (w) { sHtml += '<li class="text-warning">' + _esc(w) + '</li>'; });
      sHtml += '</ul></div>';
    }

    if (sections) sections.innerHTML = sHtml;
    preview.classList.remove('d-none');
    if (applyBtn) applyBtn.disabled = false;
  }

  // -- Initialize config import for a modal --
  //
  // opts:
  //   modalId        - modal element ID (e.g. 'importConfigCourseModal')
  //   previewId      - preview container ID
  //   summaryId      - summary div ID
  //   sectionsId     - sections div ID
  //   applyBtnId     - apply button ID
  //   cancelBtnId    - optional cancel button ID (for explicit cancel handler)
  //   openBtnId      - optional open button ID
  //   canOpen        - optional page permission check for the open button
  //   pasteInputId   - JSON editor <textarea> ID (typing, pasting AND uploads
  //                    all arrive here - see the `json_drop` component)
  //   parse          - optional config parser (e.g. the check-config schema)
  //   renderPreview  - optional preview renderer
  //   disabledFeatures - object of disabled feature flags
  //   requireCourseCode    - if true, require course.code (dashboard mode)
  //   requireAcademicYear  - if true, require course.academic_year (dashboard mode)
  //   onApply        - async function(config, btn) - performs the API call and post-success handling
  //
  function initConfigImport(opts) {
    const modal = document.getElementById(opts.modalId);
    const editor = document.getElementById(opts.pasteInputId);
    const preview = document.getElementById(opts.previewId);
    const applyBtn = document.getElementById(opts.applyBtnId);
    if (modal?._gpConfigImport) return modal._gpConfigImport;
    let _config = null;
    let _sourceText = '';
    let _pasteTimer = null;
    let destroyed = false;

    function _invalidate() {
      clearTimeout(_pasteTimer);
      _pasteTimer = null;
      _config = null;
      _sourceText = '';
      if (preview) preview.classList.add('d-none');
      if (applyBtn) applyBtn.disabled = true;
    }

    function _reset() {
      _invalidate();
      const drop = editor?.closest('[data-json-drop]');
      if (drop?.resetJsonDrop) drop.resetJsonDrop();
      else if (editor) editor.value = '';
      if (modal && document.getElementById(opts.modalId) === modal) GP.clearModalDirty(opts.modalId);
    }

    function _tryParse(text, showErrors) {
      const config = (opts.parse || parseConfig)(text, showErrors);
      if (!config) return null;

      // Additional required-field checks for dashboard (create) mode
      const cm = config.course || config.source_course || {};
      if (opts.requireCourseCode && !cm.code) {
        if (showErrors) GP.showToast(_t('Missing course.code in configuration'), 'warning');
        return null;
      }
      if (opts.requireAcademicYear && !cm.academic_year) {
        if (showErrors) GP.showToast(_t('Missing course.academic_year in configuration'), 'warning');
        return null;
      }
      return config;
    }

    function _onConfig(config, text) {
      _config = config;
      _sourceText = text;
      (opts.renderPreview || showPreview)(config, opts);
      GP.refreshProcessActionGuards(document.getElementById(opts.modalId) || document);
    }

    function _open() {
      if (opts.canOpen && !opts.canOpen()) return;
      window.openModal(opts.modalId);
    }

    function _close() {
      // Cancel, X, Escape and backdrop all use the same draft guard.
      window.closeModal(opts.modalId);
    }
    const openBtn = document.getElementById(opts.openBtnId);
    const cancelBtn = document.getElementById(opts.cancelBtnId);
    openBtn?.addEventListener('click', _open);
    cancelBtn?.addEventListener('click', _close);
    GP.enableFormDirtyGuard(opts.modalId, { settle: false });

    /* File upload needs no branch of its own: the shared `json_drop` component
       reads a dropped or browsed file into the JSON editor and fires an input
       event, so uploads flow through the paste handler below. That also
       retires the pair of mutually-clearing inputs this modal used to carry. */

    // -- Editor handler (debounced 400ms; covers typing, pasting and uploads) --
    function _onEdit() {
      const text = editor.value.trim();
      // An edited preview is stale immediately, even before parsing finishes.
      _invalidate();
      if (!text) return;
      _pasteTimer = setTimeout(function () {
        _pasteTimer = null;
        if (!modal?.isConnected || !modal.classList.contains('active')
            || modal.classList.contains('closing') || editor.value.trim() !== text) return;
        const config = _tryParse(text, true);
        if (config) _onConfig(config, text);
      }, 400);
    }
    editor?.addEventListener('input', _onEdit);

    // -- Apply button --
    async function _apply() {
      if (editor && editor.value.trim() !== _sourceText) { _onEdit(); return; }
      if (!_config) { GP.showToast(_t('No configuration loaded'), 'warning'); return; }
      if (typeof opts.onApply === 'function') {
        // Catch here so a failing apply shows a toast instead of an unhandled
        // promise rejection in the console.
        try {
          await opts.onApply(_config, this);
        } catch (err) {
          GP.showToast(_t('Import failed') + ': ' + (err && err.message ? err.message : err), 'danger');
        }
      }
    }
    applyBtn?.addEventListener('click', _apply);

    function _onClosing(event) {
      if (event.detail?.modal === modal) _reset();
    }
    document.addEventListener('gp:modal-closing', _onClosing);

    // Return handle so page code can access/clear the config
    const handle = {
      reset: _reset,
      destroy: function () {
        if (destroyed) return;
        destroyed = true;
        _reset();
        editor?.removeEventListener('input', _onEdit);
        openBtn?.removeEventListener('click', _open);
        cancelBtn?.removeEventListener('click', _close);
        applyBtn?.removeEventListener('click', _apply);
        document.removeEventListener('gp:modal-closing', _onClosing);
        if (modal) delete modal._gpConfigImport;
      },
    };
    if (modal) modal._gpConfigImport = handle;
    return handle;
  }

  // -- Expose on GP namespace --
  GP.ConfigImport = {
    parse: parseConfig,
    showPreview: showPreview,
    init: initConfigImport,
  };
  window.GP = GP;
})();
