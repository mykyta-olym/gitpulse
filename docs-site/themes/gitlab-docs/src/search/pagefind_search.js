import BaseSearchForm from "../components/search/search_form.vue";
import { PagefindService } from "../services/pagefind_service";
import { createVueInstance } from "../create_vue_instance";

document.addEventListener("DOMContentLoaded", async () => {
  // Create and initialize the pagefind search service
  const pagefindServiceInstance = new PagefindService();
  await pagefindServiceInstance.loadPagefindModule();

  const pagefindSearchService = {
    async getResults(query) {
      return (await pagefindServiceInstance.getSearchResults(query)) || [];
    },
  };

  // Support rendering multiple search forms (i.e. Landing page will have two searches - mobile header and search section)
  const searchFormElements = document.querySelectorAll(
    ".js-pagefind-search-form",
  );

  searchFormElements.forEach((searchForm) => {
    createVueInstance(searchForm, BaseSearchForm, {
      searchService: pagefindSearchService,
    });
  });
});
