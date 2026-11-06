<script>
import { getSearchParamsFromURL } from "../../search/utils";

export default {
  props: {
    pagefindService: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      error: false,
    };
  },
  async mounted() {
    try {
      const { qParam } = getSearchParamsFromURL();

      const pagefind = await this.pagefindService.getInstance();

      if (qParam?.trim()) {
        pagefind.triggerSearch(qParam);
      }
    } catch (error) {
      this.error = true;
      console.error("Error initializing PageFind search: ", error);
    }
  },
  methods: {
    handleInput(event) {
      // Prevent the default behavior of the PageFind UI
      event.preventDefault();
      // Logic to set the query param to new search
      const searchQuery = event.target.value;
      const url = new window.URL(document.location);
      url.searchParams.set("q", searchQuery);
      window.history.replaceState({}, "", url);
    },
  },
};
</script>

<template>
  <div class="pagefind-search gl-mb-9">
    <h1 class="gl-my-6" data-testid="version-header">
      {{ $t("pagefindSearchResults.searchDocs") }}
    </h1>
    <div id="search-container" type="text" @input="handleInput"></div>
    <p v-if="error" class="gl-py-5" data-testid="pagefind-error">
      {{ $t("pagefindSearchResults.errorFetchingMsg") }}
    </p>
  </div>
</template>
