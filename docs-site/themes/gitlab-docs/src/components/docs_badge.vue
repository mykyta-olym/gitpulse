<script>
import { GlBadge, GlTooltipDirective } from "@gitlab/ui";

export default {
  components: {
    GlBadge,
  },
  directives: {
    GlTooltip: GlTooltipDirective,
  },
  props: {
    badgeData: {
      type: Object,
      required: true,
    },
  },
};
</script>

<template>
  <span :class="`docs-badges-wrapper gl-ml-2`">
    <gl-badge
      :key="badgeData.text"
      v-gl-tooltip.top
      :variant="'warning'"
      :title="badgeData.hoverText"
      class="gl-mr-2 gl-align-middle"
      :size="'md'"
    >
      <component :is="'span'" class="docs-badge gl-text-sm gl-capitalize">
        {{ badgeData.text }}
      </component>
    </gl-badge>
  </span>
</template>
