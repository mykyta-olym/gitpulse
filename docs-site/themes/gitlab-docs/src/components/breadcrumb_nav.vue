<script>
import { GlBreadcrumb } from "@gitlab/ui";

export default {
  components: {
    GlBreadcrumb,
  },
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
};
</script>

<template>
  <gl-breadcrumb :items="items" class="gl-overflow-hidden gl-py-3" />
</template>
