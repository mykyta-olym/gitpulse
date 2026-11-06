<script>
import { GlButton } from "@gitlab/ui";

export default {
  name: "BackToTopButton",
  components: {
    GlButton,
  },
  data() {
    return {
      observer: null,
      prefersReducedMotion: false,
    };
  },
  mounted() {
    this.setupIntersectionObserver();
    this.prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
  },
  beforeUnmount() {
    if (this.observer) {
      this.observer.disconnect();
    }
  },
  methods: {
    backToTop() {
      window.scrollTo({
        top: 0,
        behavior: this.prefersReducedMotion ? "instant" : "smooth",
      });
    },
    setupIntersectionObserver() {
      const options = {
        root: null, // Use the viewport as the root
        rootMargin: "0px",
        threshold: 0,
      };

      this.observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          this.$el.classList.toggle("gl-hidden", entry.isIntersecting);
        });
      }, options);
      const target = document.querySelector("#skipTarget");
      this.observer.observe(target);
    },
  },
};
</script>

<template>
  <gl-button
    :aria-label="$t('backToTopButton.label')"
    icon="chevron-lg-up"
    class="back-to-top-button gl-shadow-sm gl-hidden gl-fixed gl-bottom-5 gl-right-5 gl-z-40"
    category="default"
    role="button"
    size="small"
    :tooltip="$t('backToTopButton.label')"
    @click="backToTop()"
  />
</template>
