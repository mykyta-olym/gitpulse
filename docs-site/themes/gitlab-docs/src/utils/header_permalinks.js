/**
 * Adds a clickable permalink to each content heading
 */
export const addHeaderPermalinks = () => {
  document
    .querySelectorAll(".docs-content h2, h3, h4, h5, h6")
    .forEach((heading) => {
      const { id } = heading;
      if (!id) return;

      // Check if anchor already exists
      if (heading.querySelector(".anchor")) return;

      const anchor = document.createElement("a");
      anchor.href = `#${id}`;
      anchor.title = "Permalink";
      anchor.classList.add("anchor");

      heading.appendChild(anchor);
    });
};

/**
 * Transforms a string into a URL-friendly slug.
 *
 * This can be used to add IDs to Javascript-created headings,
 * which can then be permalinked by addHeaderPermalinks.
 */
export const slugify = (str) => {
  return str
    .replace(/<[^>]*>/g, "") // Remove HTML tags
    .toLowerCase()
    .replace(/[^\w\s-]/g, "") // Remove special chars
    .replace(/\s+/g, "-") // Replace spaces with hyphens
    .replace(/-+/g, "-") // Replace multiple hyphens with single
    .trim()
    .replace(/^-+|-+$/g, ""); // Trim leading/trailing hyphens
};
