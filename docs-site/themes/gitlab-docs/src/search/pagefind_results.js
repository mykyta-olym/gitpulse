import Vue from "vue";
import { i18n } from "../../../../locales/i18n";
import PageFindSearchResults from "../components/search/pagefind_results.vue";
import { PagefindService } from "../services/pagefind_service";

document.addEventListener("DOMContentLoaded", () => {
  // Search results page (/search)
  const pagefindService = new PagefindService();

  (() =>
    new Vue({
      i18n,
      el: ".js-pagefind-search-results",
      components: { PageFindSearchResults },
      render(createElement) {
        return createElement(PageFindSearchResults, {
          props: {
            pagefindService,
          },
        });
      },
    }))();
});
