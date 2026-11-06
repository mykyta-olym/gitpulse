<script>
import {
  GlCollapsibleListbox,
  GlTooltipDirective as GlTooltip,
} from "@gitlab/ui";
import { getAppearanceManager } from "../utils/appearance_manager";

export default {
  name: "AppearanceToggle",
  components: { GlCollapsibleListbox },
  directives: { GlTooltip },
  data() {
    return {
      currentTheme: "light",
      currentLayout: "fixed",
    };
  },
  computed: {
    formattedItems() {
      return [
        {
          name: this.$t("themeToggle.theme"),
          options: [
            { value: "light", text: this.$t("themeToggle.light") },
            { value: "dark", text: this.$t("themeToggle.dark") },
            { value: "auto", text: this.$t("themeToggle.auto") },
          ],
        },
        {
          name: this.$t("layoutToggle.layout"),
          options: [
            { value: "fixed", text: this.$t("layoutToggle.fixed") },
            { value: "fluid", text: this.$t("layoutToggle.fluid") },
          ],
        },
      ];
    },
    selectedItems() {
      return [this.currentTheme, this.currentLayout];
    },
  },
  mounted() {
    this.appearanceManager = getAppearanceManager();
    this.updateAppearanceState();
    document.addEventListener("themechange", this.updateAppearanceState);
    document.addEventListener("layoutchange", this.updateAppearanceState);
  },
  beforeUnmount() {
    document.removeEventListener("themechange", this.updateAppearanceState);
    document.removeEventListener("layoutchange", this.updateAppearanceState);
  },
  methods: {
    updateAppearanceState() {
      this.currentTheme = this.appearanceManager.getPreference("theme");
      this.currentLayout = this.appearanceManager.getPreference("layout");
    },
    getValueType(value) {
      if (["light", "dark", "auto"].includes(value)) return "theme";
      if (["fixed", "fluid"].includes(value)) return "layout";
      return null;
    },
    onAppearanceChange(values) {
      let theme = this.currentTheme;
      let layout = this.currentLayout;
      if (Array.isArray(values)) {
        values.forEach((v) => {
          const type = this.getValueType(v);
          if (type === "theme") theme = v;
          if (type === "layout") layout = v;
        });
      } else {
        const type = this.getValueType(values);
        if (type === "theme") theme = values;
        if (type === "layout") layout = values;
      }
      if (theme !== this.currentTheme) {
        this.appearanceManager.setPreference({ type: "theme", value: theme });
      }
      if (layout !== this.currentLayout) {
        this.appearanceManager.setPreference({ type: "layout", value: layout });
      }
    },
  },
};
</script>
<template>
  <gl-collapsible-listbox
    v-gl-tooltip.hover
    class="appearance-toggle gl-flex gl-mt-3 lg:gl-my-0"
    icon="appearance"
    :selected="selectedItems"
    :items="formattedItems"
    :multiple="true"
    placement="bottom-start"
    :title="$t('themeToggle.tooltip')"
    :toggle-text="$t('themeToggle.tooltip')"
    text-sr-only
    @select="onAppearanceChange"
  />
</template>
