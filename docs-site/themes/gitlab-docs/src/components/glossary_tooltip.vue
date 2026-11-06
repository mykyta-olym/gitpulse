<script>
import { GlTooltip } from "@gitlab/ui";

export default {
  name: "GlossaryTooltip",
  components: {
    GlTooltip,
  },
  props: {
    term: {
      type: String,
      required: true,
    },
    termId: {
      type: String,
      required: true,
    },
    definition: {
      type: String,
      required: true,
    },
    glossary: {
      type: String,
      required: false,
      default: null,
    },
  },
};
</script>
<template>
  <span class="glossary-term">
    <a
      v-if="glossary"
      :id="termId"
      :href="`${glossary}#${termId}`"
      class="gl-decoration-dotted"
      >{{ term }}</a
    >
    <span
      v-else
      :id="termId"
      class="gl-underline gl-decoration-dotted gl-decoration-blue-700 gl-underline-offset-4 gl-decoration-1"
      >{{ term }}</span
    >
    <gl-tooltip
      :id="`tooltip-${termId}`"
      :target="termId"
      triggers="hover focus"
      placement="top"
    >
      {{ definition }}
    </gl-tooltip>
  </span>
</template>
