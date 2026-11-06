<script>
import { GlAlert, GlSafeHtmlDirective as SafeHtml } from "@gitlab/ui";
import { nextTick } from "vue";
import { getCookie, setCookie } from "../utils/cookies";
import { updateBannerScrollOffset } from "../utils/dom";

export default {
  directives: {
    SafeHtml,
  },
  components: {
    GlAlert,
  },
  props: {
    bannerType: {
      type: String,
      required: true,
      validator: (value) => ["survey", "l10n"].includes(value),
    },
    text: {
      type: String,
      required: true,
    },
    variant: {
      type: String,
      required: true,
    },
    dismissible: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      showBanner: true,
    };
  },
  computed: {
    renderBanner() {
      if (this.bannerType === "survey") {
        return this.showBanner;
      }

      return this.showBanner || !this.dismissible;
    },
    bannerAlertStyle() {
      const styles = {
        survey: "gl-mb-5",
        l10n: "gl-my-5",
      };
      return styles[this.bannerType];
    },
    bannerTextStyle() {
      const styles = {
        survey: "gl-leading-24",
      };
      return styles[this.bannerType];
    },
  },
  created() {
    this.showBanner = getCookie("HideDocsBanner") !== "1";
  },
  methods: {
    dismissAlert() {
      this.showBanner = false;
      setCookie("HideDocsBanner", 1, 30);
      // Update scroll offset after banner is dismissed
      nextTick(() => {
        updateBannerScrollOffset();
      });
    },
  },
};
</script>

<template>
  <gl-alert
    v-if="renderBanner"
    :variant="variant"
    :dismissible="dismissible"
    :class="['gl-docs', bannerAlertStyle]"
    @dismiss="dismissAlert()"
  >
    <div
      v-safe-html="text"
      :class="['gl-layout-w-limited', 'gl-m-auto', bannerTextStyle]"
    ></div>
  </gl-alert>
</template>
