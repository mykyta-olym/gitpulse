<script>
import {
  GlSearchBoxByType,
  GlLink,
  GlSafeHtmlDirective as SafeHtml,
  GlTooltipDirective as GlTooltip,
} from "@gitlab/ui";
import { directive as clickOutside } from "v-click-outside";
import { docsBaseURL } from "../../utils/environment";
import { debounce } from "../../utils/debounce";
import { MAX_RESULTS } from "../../search/utils";
import SuggestedItems from "./suggested_items.vue";

export default {
  components: {
    GlSearchBoxByType,
    GlLink,
    SuggestedItems,
  },
  directives: {
    clickOutside,
    SafeHtml,
    GlTooltip,
  },
  props: {
    searchService: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      activeLink: -1,
      historyItems: 0,
      isLoading: false,
      moreResultsPath: "",
      results: [],
      showTooltip: true,
      searchQuery: "",
      showModal: false,
      showResultPanel: false,
      submitted: false,
    };
  },
  computed: {
    hasMoreResults() {
      return this.results.length >= MAX_RESULTS;
    },
    hasNoResults() {
      return (
        !this.results.length && this.submitted && this.searchQuery.trim() !== ""
      );
    },
    showSuggested() {
      return !this.searchQuery;
    },
    getResultsWidth() {
      const searchInput = this.$refs.searchForm;
      return `width: ${searchInput ? searchInput.clientWidth : 0}px`;
    },
  },
  watch: {
    searchQuery() {
      this.results = [];
      this.showResultPanel = false;
      this.showTooltip = this.searchQuery.length === 0;
      this.submitted = false;
      this.moreResultsPath = `${docsBaseURL()}search/?q=${encodeURI(this.searchQuery)}`;
      this.debouncedGetResults();
    },
  },
  async created() {
    this.debouncedGetResults = debounce(this.getResults, 500);
  },
  methods: {
    async getResults() {
      if (this.isElasticSearch && this.missingKeys.length > 0) {
        this.showResultPanel = true;
        return;
      }

      this.isLoading = true;
      this.showResultPanel = false;

      try {
        this.results = await this.searchService.getResults(this.searchQuery);
        this.submitted = true;
        this.showResultPanel = true;
      } catch (error) {
        console.error("Error getting results:", error);
      } finally {
        this.isLoading = false;
      }
    },
    showAllResults() {
      // Sends the user to the advanced search page if they hit Enter.
      if (this.searchQuery) {
        window.location.href = this.moreResultsPath;
      }
    },
    keyboardNav(e) {
      const isArrowUp = e.key === "ArrowUp";
      const isArrowDown = e.key === "ArrowDown";
      const searchBox = document.querySelector("input[type=search]");

      if (isArrowUp || isArrowDown) {
        const activeIndex = this.activeLink + (isArrowUp ? -1 : 1);

        // If we're at the top or bottom of the list, go back to the search box.
        const listLength = this.searchQuery
          ? this.results.length
          : this.historyItems - 1;
        if (activeIndex < 0 || activeIndex > listLength) {
          this.activeLink = -1;
          searchBox.focus();
          // Reset the value after focus so that the cursor is at the end of the text.
          searchBox.value = this.searchQuery;
          return;
        }
        // Otherwise, select the previous or next link.
        this.setActiveResult(
          document.querySelector(`[data-link-index="${activeIndex}"]`),
        );
      }
    },
    setActiveResult(result) {
      if (result) {
        result.focus();
        this.activeLink = Number(result.dataset.linkIndex);
      }
    },
    deactivate() {
      this.showResultPanel = false;
      this.showModal = false;
      this.activeLink = -1;
      this.showTooltip = this.searchQuery.length === 0;
    },
    getTitle(result) {
      return result.meta.title;
    },
    getUrl(result) {
      return result.url;
    },
  },
};
</script>

<template>
  <div class="search-container">
    <div
      v-click-outside="() => deactivate()"
      class="search-form-wrapper gl-text-base"
      @keydown.arrow-down.prevent="keyboardNav"
      @keydown.arrow-up.prevent="keyboardNav"
      @keydown.escape="deactivate()"
      @keydown.tab="deactivate()"
    >
      <form ref="searchForm" class="gl-relative">
        <gl-search-box-by-type
          v-model="searchQuery"
          role="searchbox"
          :is-loading="isLoading"
          :placeholder="$t('searchForm.searchGitLabDocs')"
          autocomplete="off"
          :aria-label="$t('searchForm.search')"
          @focus="
            showResultPanel = true;
            showModal = true;
          "
          @keydown.enter.prevent="showAllResults()"
        />
        <kbd
          v-show="showTooltip && !isLoading"
          v-gl-tooltip.bottom.hover.html
          class="gl-absolute gl-z-1"
          :title="
            $t('searchForm.tooltipTxt', ['<br><kbd>/</kbd>', '<kbd>s</kbd>'])
          "
          >/</kbd
        >
      </form>
      <div
        v-if="showResultPanel"
        class="search-results gl-absolute gl-z-4 gl-bg-white gl-px-2 gl-shadow"
        :style="getResultsWidth"
        data-ga-section="search dropdown"
      >
        <ul
          v-if="results.length"
          data-testid="search-results"
          class="gl-pl-0 gl-mb-0 gl-py-3"
        >
          <li
            v-for="(result, index) in results"
            :key="result.id"
            class="gl-list-none"
          >
            <gl-link
              data-result-type="dropdown"
              :data-search-query="searchQuery"
              :data-link-index="index"
              class="gl-text-gray-700 gl-py-4 gl-px-6 gl-block gl-text-left"
              :href="getUrl(result)"
            >
              <span v-safe-html="getTitle(result)" class="gl-block"></span>
              <span
                v-if="result.breadcrumbs"
                v-safe-html="result.breadcrumbs"
                class="gl-text-xs gl-block gl-text-gray-400"
              ></span>
            </gl-link>
          </li>
          <li v-if="hasMoreResults" class="gl-list-none gl-mb-1">
            <gl-link
              :data-link-index="results.length"
              data-testid="more-results"
              :href="moreResultsPath"
              class="gl-text-gray-700 gl-pt-3 gl-pb-3 gl-px-6 gl-block gl-text-left"
            >
              {{ $t("searchForm.seeAllResults") }}
            </gl-link>
          </li>
        </ul>
        <p
          v-if="hasNoResults"
          data-testid="no-results"
          class="gl-text-left gl-py-3 gl-pl-6"
        >
          {{ $t("searchForm.noResultsFound") }}
        </p>
        <suggested-items
          v-if="showSuggested"
          @page-history-init="(items) => (historyItems = items)"
        />
      </div>
    </div>
    <transition name="fade">
      <div
        v-if="showModal"
        class="gl-hidden lg:gl-block gl-z-3 modal-backdrop"
      ></div>
    </transition>
  </div>
</template>
