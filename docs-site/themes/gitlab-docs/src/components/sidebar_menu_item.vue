<script>
import { GlButton, GlAnimatedChevronRightDownIcon } from "@gitlab/ui";

export default {
  name: "MenuItem",
  components: {
    GlButton,
    GlAnimatedChevronRightDownIcon,
  },
  props: {
    item: {
      type: Object,
      required: true,
    },
    level: {
      type: Number,
      default: 1,
      required: false,
    },
  },
  data() {
    return {
      isOpen: this.item.isActiveTrail,
      isMounted: false,
    };
  },
  computed: {
    activeClasses() {
      return [
        this.item.isActiveTrail && "sidebar-link-active-trail",
        this.item.isActive && "sidebar-link-active-item",
      ]
        .filter(Boolean)
        .join(" ");
    },
    shouldAnimate() {
      return this.isMounted && this.item.submenu;
    },
    transitionComponent() {
      return this.shouldAnimate ? "transition" : "div";
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.isMounted = true;
    });

    if (this.item.isActive) {
      this.$refs.activeItem.scrollIntoView({
        behavior: "instant",
        block: "center",
      });

      // Reset viewport scroll - flexbox layout causes scrollIntoView to affect main content
      if (window.location.hash) {
        const hash = window.location.hash.substring(1);
        const element = document.getElementById(hash);
        if (element) {
          element.scrollIntoView({ behavior: "instant" });
        }
      } else {
        window.scrollTo({ top: 0 });
      }
    }
  },
  methods: {
    toggleOpen() {
      this.isOpen = !this.isOpen;
    },
  },
};
</script>
<template>
  <div>
    <div class="menu-link-wrapper-outer">
      <div
        :class="`menu-link-wrapper-inner gl-flex gl-items-center gl-rounded-base ${activeClasses}`"
      >
        <a
          :ref="item.isActiveTrail ? 'activeItem' : null"
          :href="item.prefixedUrl"
          class="menu-link gl-grow gl-py-2 gl-px-4 gl-text-default gl-no-underline hover:gl-no-underline"
        >
          {{ item.title }}
        </a>
        <gl-button
          v-if="item.submenu"
          :aria-label="isOpen ? 'Collapse' : 'Expand'"
          category="tertiary"
          class="submenu-toggle btn-icon gl-mr-2"
          size="small"
          @click="toggleOpen"
        >
          <gl-animated-chevron-right-down-icon :is-on="isOpen" />
        </gl-button>
      </div>
    </div>
    <component :is="transitionComponent" name="submenu">
      <div v-if="item.submenu && isOpen" class="submenu">
        <menu-item
          v-for="(child, childIndex) in item.submenu"
          :key="childIndex"
          :item="child"
          :level="level + 1"
        />
      </div>
    </component>
  </div>
</template>
