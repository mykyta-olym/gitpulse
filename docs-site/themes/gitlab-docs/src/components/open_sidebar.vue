<script>
import { GlButton } from "@gitlab/ui";

export default {
  components: {
    GlButton,
  },
  methods: {
    toggleOverlay() {
      const event = new CustomEvent("open-sidebar", { detail: "open" });
      window.dispatchEvent(event);
    },
  },
};
</script>
<template>
  <div class="open-sidebar gl-text-sm gl-min-w-9 lg:gl-hidden">
    <gl-button
      :aria-label="$t('navBar.toggleSidebar')"
      category="tertiary"
      class="sidebar-toggle-outer"
      data-testid="sidebar-toggle-btn-outer"
      icon="sidebar"
      size="small"
      @click="toggleOverlay()"
    />
    <span class="gl-text-subtle gl-px-2">&nbsp;/&nbsp;</span>
  </div>
</template>
