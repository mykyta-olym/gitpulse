<script>
import {
  GlDisclosureDropdown,
  GlDisclosureDropdownGroup,
  GlDisclosureDropdownItem,
} from "@gitlab/ui";
import {
  buildDocumentationIssueUrl,
  buildIssueTitle,
} from "../utils/documentation_issue_url";

export default {
  components: {
    GlDisclosureDropdown,
    GlDisclosureDropdownGroup,
    GlDisclosureDropdownItem,
  },
  data() {
    return {
      actions: [],
      pageSource: "",
    };
  },
  created() {
    this.pageSource =
      document.querySelector('meta[name="gitlab_docs_page_source"]')?.content ||
      "";
    const webIdeLink = document.querySelector(
      'meta[name="gitlab_docs_web_ide_link"]',
    )?.content;

    if (this.pageSource) {
      this.actions.push({
        text: this.$t("feedback.viewSource"),
        secondaryText: this.$t("feedback.viewSourceHelp"),
        href: this.pageSource,
      });
    }

    if (webIdeLink) {
      this.actions.push({
        text: this.$t("feedback.openWebIDE"),
        secondaryText: this.$t("feedback.openWebIDEhelp"),
        href: webIdeLink,
      });
    }

    this.actions.push({
      text: this.$t("feedback.suggestUpdates"),
      secondaryText: this.$t("feedback.suggestUpdatesHelp"),
      action: this.openDocumentationIssue,
    });
  },
  methods: {
    openDocumentationIssue() {
      const url = buildDocumentationIssueUrl({
        pageUrl: window.location.href,
        sourceUrl: this.pageSource,
        selectedText: window.getSelection()?.toString().trim() || "",
        title: buildIssueTitle(window.location.pathname),
      });

      window.location.assign(url);
    },
  },
};
</script>

<template>
  <gl-disclosure-dropdown
    :toggle-text="$t('feedback.editPage')"
    data-testid="edit-menu"
    icon="pencil"
    block
  >
    <gl-disclosure-dropdown-group>
      <gl-disclosure-dropdown-item
        v-for="(action, index) in actions"
        :key="index"
        :item="action"
        :data-testid="`${index}-menu-item`"
      >
        <template #list-item>
          <div class="gl-flex gl-flex-col">
            <span class="gl-flex gl-items-center gl-justify-between">
              <span data-testid="action-primary-text" class="gl-font-bold">{{
                action.text
              }}</span>
            </span>
            <span
              v-if="action.secondaryText"
              data-testid="action-secondary-text"
              class="gl-text-sm gl-text-secondary gl-mt-1"
            >
              {{ action.secondaryText }}
            </span>
          </div>
        </template>
      </gl-disclosure-dropdown-item>
    </gl-disclosure-dropdown-group>
  </gl-disclosure-dropdown>
</template>
