/**
 * Builds GitLab issue URLs for documentation feedback from docs.gitlab.com.
 *
 * Uses issuable_template=Documentation together with a prefilled issue[description]
 * so page context appears above the template guidance. Quick actions at the end of
 * the description must stay in sync with gitlab-org/gitlab's Documentation issue
 * template: .gitlab/issue_templates/Documentation.md
 */

const ISSUE_BASE_URL = "https://gitlab.com/gitlab-org/gitlab/-/issues/new";
const ISSUABLE_TEMPLATE = "Documentation";

// Keep in sync with gitlab-org/gitlab/.gitlab/issue_templates/Documentation.md
const ISSUE_QUICK_ACTIONS = `/label ~"documentation"
/label ~"docs-only"
/label ~"Technical Writing"
/label ~"type::maintenance" ~"maintenance::refactor"
/milestone %Backlog`;

/**
 * Strip review-app, version, and language prefixes from a pathname.
 * Mirrors themes/gitlab-docs/layouts/_partials/functions/clean-path.html.
 *
 * @param {string} pathname
 * @returns {string}
 */
export function buildIssueTitle(pathname) {
  let path = pathname.replace(/^\/+|\/+$/g, "");

  path = path
    .replace(/^(?:upstream-)?review-mr-[^/]+\//, "")
    .replace(/^\d+\.\d+\//, "")
    .replace(/^[a-z]{2}-[a-z]{2}\//, "");

  return path ? `Docs feedback: ${path}` : "Docs feedback";
}

function formatHighlightedText(selectedText) {
  const quotedText = selectedText.split("\n").join("\n> ");

  return `**Highlighted text:**

> ${quotedText}

`;
}

/**
 * @param {{ pageUrl: string, sourceUrl: string, selectedText: string }} context
 * @returns {string}
 */
function buildIssueDescription({ pageUrl, sourceUrl, selectedText }) {
  const highlightedSection = selectedText
    ? formatHighlightedText(selectedText)
    : "";

  return `<!-- Reported from the docs.gitlab.com "Create an issue" menu. Context added automatically: -->

**Reported from documentation:**

- **Page URL:** ${pageUrl}
- **Source file:** ${sourceUrl || "Unavailable"}

${highlightedSection}## Problem to solve

<!-- Describe what is wrong, missing, or unclear. -->

## Proposal

<!-- Optional: how could we fix it? -->

${ISSUE_QUICK_ACTIONS}
`;
}

/**
 * @param {{ pageUrl: string, sourceUrl?: string, selectedText?: string, title: string }} options
 * @returns {string}
 */
export function buildDocumentationIssueUrl({
  pageUrl,
  sourceUrl = "",
  selectedText = "",
  title,
}) {
  const description = buildIssueDescription({
    pageUrl,
    sourceUrl,
    selectedText,
  });

  const params = new URLSearchParams({
    issuable_template: ISSUABLE_TEMPLATE,
    "issue[title]": title,
    "issue[description]": description,
  });

  return `${ISSUE_BASE_URL}?${params.toString()}`;
}
