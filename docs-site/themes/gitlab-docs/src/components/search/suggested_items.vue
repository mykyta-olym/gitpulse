<script>
import { GlLink } from "@gitlab/ui";
import { i18n } from "../../../../../locales/i18n";
import { getCookie } from "../../utils/cookies";
import { docsBaseURL } from "../../utils/environment";

export default {
  components: {
    GlLink,
  },
  emits: ["pageHistoryInit"],
  data() {
    return {
      recentlyViewedTxt: i18n.t("searchSuggestedItems.recentlyViewed"),
      popularTxt: i18n.t("searchSuggestedItems.popular"),
      pageHistory: [],
      popularItems: [
        {
          title: i18n.t("searchSuggestedItems.cicdYAMLSyntaxReference"),
          path: `${docsBaseURL()}ci/yaml/`,
        },
      ],
    };
  },
  created() {
    this.pageHistory = JSON.parse(getCookie("pageHistory")) || [];
    this.pageHistory.shift(); // Drop the current page

    // Pass the list lengths to the parent component for keyboard nav,
    this.$emit(
      "pageHistoryInit",
      this.pageHistory.length + this.popularItems.length,
    );
  },
  methods: {
    /**
     * Calculate the keyboard nav index for "Popular" items.
     * Because "Recently viewed" can contain a variable number of items,
     * this needs to be derived from the length of that list.
     */
    kbdNavIndex(index) {
      return this.pageHistory.length + index;
    },
  },
};
</script>

<template>
  <div class="gl-py-3 gl-mt-3">
    <template v-if="pageHistory.length">
      <div class="gl-font-bold gl-text-left gl-pl-6">
        {{ recentlyViewedTxt }}
      </div>
      <ul class="gl-pl-0 gl-mb-3 gl-pt-3">
        <li
          v-for="(page, index) in pageHistory"
          :key="page.path"
          class="gl-list-none"
        >
          <gl-link
            :href="page.path"
            :data-link-index="index"
            data-result-type="history"
            class="gl-text-gray-700 gl-py-3 gl-px-6 gl-block gl-text-left"
          >
            {{ page.title }}
          </gl-link>
        </li>
      </ul>
    </template>
    <div class="gl-font-bold gl-text-left gl-pl-6">{{ popularTxt }}</div>
    <ul class="gl-pl-0 gl-mb-3 gl-pt-3">
      <li
        v-for="(page, index) in popularItems"
        :key="page.path"
        class="gl-list-none"
      >
        <gl-link
          :href="page.path"
          :data-link-index="kbdNavIndex(index)"
          data-result-type="popular"
          class="gl-text-gray-700 gl-py-3 gl-px-6 gl-block gl-text-left"
        >
          {{ page.title }}
        </gl-link>
      </li>
    </ul>
  </div>
</template>
