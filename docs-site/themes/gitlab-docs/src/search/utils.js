export const MAX_RESULTS = 7;

export const isBaseUrl = (path) => {
  return path === "/docs/" || path === "/docs/en/";
};

/**
 * Check URL parameters for search parameters.
 *
 * We support "q" for the query string as it's a search standard,
 * and also "query" as it has been long-documented in the
 * GitLab handbook as a Docs search parameter.
 *
 * See https://about.gitlab.com/handbook/tools-and-tips/searching/
 *
 * @returns
 *  An object containing query parameters.
 */
export const getSearchParamsFromURL = () => {
  const searchParams = new URLSearchParams(window.location.search);
  return {
    qParam: searchParams.get("q") || searchParams.get("query") || "",
  };
};
