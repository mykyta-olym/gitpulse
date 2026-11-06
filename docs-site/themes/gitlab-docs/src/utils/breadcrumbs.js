import { defaultLocale } from "../../../../locales/index";
import { docsBaseURL } from "./environment";

const TRUNCATE_LENGTH = 24;

const truncateText = (text, maxLength = TRUNCATE_LENGTH) => {
  return text.length > maxLength ? `${text.substring(0, maxLength)}…` : text;
};

export const assembleBreadcrumbs = (currentLang) => {
  // Get the active trail from the pageMetadata object, with fallback
  const trail = window.pageMetadata?.trail || [];
  const breadcrumbs = trail.map((crumb, index, array) => ({
    href: docsBaseURL() + crumb.path,
    // Truncate all breadcrumbs, except the last one
    text: index === array.length - 1 ? crumb.title : truncateText(crumb.title),
  }));

  // Build homepage URL with language prefix if not English
  const homePath =
    currentLang === defaultLocale
      ? docsBaseURL()
      : `${docsBaseURL()}${currentLang}/`;

  return [{ text: "GitPulse Docs", href: homePath }, ...breadcrumbs];
};
