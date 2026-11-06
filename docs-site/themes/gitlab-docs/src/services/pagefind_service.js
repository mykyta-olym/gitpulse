/* global PagefindUI:readonly */
import { MAX_RESULTS } from "../search/utils";

export class PagefindService {
  constructor() {
    this.pagefindModule = null;
    this.initPromise = null;
    this.pagefindPaths = null;
    this.indexDir = null;
  }

  /**
   * The index directory for a role.
   *
   * One index over the whole site was a hole through the role gate: the gate
   * refuses `/docs/operatori/`, but the index built from those pages carries
   * their text, and a signed-out visitor searching for a word from them got it
   * back. There is one index per tier now, and this picks the deepest the
   * reader may open. The SERVER still decides - `pagefind-staff/` and
   * `pagefind-admin/` are gated exactly like the sections they index, so naming
   * one you may not read returns the refusal page, not results.
   */
  static INDEX_FOR_ROLE = {
    admin: "pagefind-admin",
    teacher: "pagefind-staff",
  };

  /**
   * Ask the application which role this reader has. Cached; fails safe.
   * @returns {Promise<string>} - the index directory name
   */
  async resolveIndexDir() {
    if (this.indexDir) return this.indexDir;
    this.indexDir = "pagefind";
    try {
      const res = await fetch("/internal/docs-role", {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (res.ok) {
        const { role } = await res.json();
        this.indexDir = PagefindService.INDEX_FOR_ROLE[role] || "pagefind";
      }
    } catch {
      /* unreachable endpoint means the public index, which everyone may read */
    }
    return this.indexDir;
  }

  /**
   * Get the paths for pagefind resources
   * @returns {Promise<Object>} - Paths for pagefind resources
   *   @property {string} baseUrl - The base URL for the current site version
   *   @property {string} bundlePath - The directory path containing Pagefind resources
   *   @property {string} pagefindJS - The full path to the Pagefind JavaScript file
   */
  async getPagefindPaths() {
    if (this.pagefindPaths) {
      return this.pagefindPaths;
    }

    // Upstream serves one index per release at /17.9/pagefind/; this site
    // has a single version, so the index is at one fixed path per tier.
    const baseUrl = "/docs";
    const dir = await this.resolveIndexDir();

    this.pagefindPaths = {
      baseUrl,
      bundlePath: `${baseUrl}/${dir}/`,
      pagefindJS: `${baseUrl}/${dir}/pagefind.js`,
    };

    return this.pagefindPaths;
  }

  /**
   * Load pagefind.js module
   * @returns {Promise} - loaded pagefind module
   */
  async loadPagefindModule() {
    // Only import if pagefind module is not defined.
    if (!this.pagefindModule) {
      // Get pagefind.js file path.
      const { pagefindJS } = await this.getPagefindPaths();

      // eslint-disable-next-line import/no-dynamic-require
      this.pagefindModule = await import(`${pagefindJS}`);
    }
    return this.pagefindModule;
  }

  /**
   * Initialize PagefindUI instance
   */
  async getInstance() {
    if (this.initPromise) return this.initPromise;

    this.initPromise = this.createPagefindUI();
    return this.initPromise;
  }

  async createPagefindUI() {
    const { baseUrl, bundlePath } = await this.getPagefindPaths();

    // Ensure PagefindUI is available
    if (typeof PagefindUI === "undefined") {
      throw new Error("PagefindUI is not available");
    }

    const pagefindUI = new PagefindUI({
      element: "#search-container",
      baseUrl,
      bundlePath,
      showImages: false,
      showEmptyFilters: false,
      resetStyles: false,
      debounceTimeoutMs: 500,
      ranking: {
        pageLength: 0, // Disable page length ranking by setting it to 0
      },
    });

    return pagefindUI;
  }

  /**
   * Retrieve and process search results
   * @returns {Array} - array of search result objects
   */
  async getSearchResults(query) {
    if (!query?.trim()) return [];

    const pagefind = await this.loadPagefindModule();
    const search = await pagefind.search(query);
    const topResults = await Promise.all(
      search.results.slice(0, MAX_RESULTS).map(async (r) => {
        const data = await r.data();
        return { ...data, breadcrumbs: data.meta?.breadcrumbs };
      }),
    );

    return topResults;
  }
}
