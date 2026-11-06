export const docsBaseURL = () =>
  document
    .querySelector('meta[name="gitlab_docs_base_url"]')
    ?.getAttribute("content");
