import { i18n } from "../../../../locales/i18n";

/**
 * Convert PlantUML markup to images
 *
 * Custom implementation based on https://plantuml.com/text-encoding
 *
 * Customizations:
 * - Use GitLab's PlantUML server
 * - Return images in PNG format
 * - Adds a link around the image
 */

/**
 * Deflation compression with browser APIs.
 *
 * 1. We first create a blob containing the plant uml as the content
 * 2. We pipe the blobs content through deflate (without headers) with CompressionStream
 * 3. We convert the returned bytes in a given chunk to its respective ASCII character representation with `String.fromCharCode`
 *
 * @see https://developer.mozilla.org/en-us/docs/Web/API/CompressionStream
 * @param {string} puml
 * @returns {Promise<string>}
 */
async function deflateCustom(puml) {
  try {
    const compressedStream = new Blob([puml], { type: "text/plain" })
      .stream()
      .pipeThrough(new CompressionStream("deflate-raw"));

    // In support of all browsers (including mobile support).
    // Cannot iterate ReadableStream asynchronously (Browser incompatibility: https://caniuse.com/mdn-api_readablestream_--asynciterator).
    const reader = compressedStream.getReader();

    let deflated = "";

    /* eslint-disable no-await-in-loop */
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      // Convert each byte in current chunk into its character representation.
      deflated += Array.from(value, (byte) => String.fromCharCode(byte)).join(
        "",
      );
    }

    return deflated;
  } catch (error) {
    console.error("Compression failed:", error);
    throw error;
  }
}

const BASE_64 =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
const BASE_PLANT_UML =
  "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_";

/**
 * Convert base64 to plant uml's encoding
 *
 * Plant UML uses a custom base64-like encoding. However, the characters map differently, for example
 * what's A in base64 is 0 in the encoding.
 *
 * We can simply replace the characters
 *
 * @see https://plantuml.com/text-encoding
 * @param string
 * @returns {string}
 */
function convertBase64ToPlantUML(string) {
  const base64 = window.btoa(string);
  let res = "";
  for (const letter of base64) {
    res += BASE_PLANT_UML[BASE_64.indexOf(letter)];
  }
  return res;
}

// Render a warning banner for image render issues
async function renderErrorBanner(element, parent) {
  const textDiv = document.createElement("div");
  textDiv.textContent = `${i18n.t("plantuml.errorRenderMsg")}`;
  const iconDiv = document.createElement("div");
  iconDiv.classList.add("docs-error-icon");
  textDiv.appendChild(iconDiv);
  textDiv.classList.add("docs-error-box");
  parent.replaceChild(textDiv, element);
}

const plantUmlElements = document.querySelectorAll(".language-plantuml");
plantUmlElements.forEach(async (element) => {
  const parent = element.parentNode;
  try {
    const s = decodeURIComponent(encodeURIComponent(element.textContent));
    const imgElement = document.createElement("img");
    const imgData = convertBase64ToPlantUML(await deflateCustom(s));

    const imgSrc = `https://plantuml.gitlab-static.net/png/${imgData}`;
    imgElement.setAttribute("src", imgSrc);

    // Image load failed
    imgElement.onerror = function onError() {
      imgElement.style.display = "none";
      renderErrorBanner(element, parent);
      imgElement.onerror = null;
    };

    // Image load successful
    imgElement.onload = function onLoad() {
      const linkElement = document.createElement("a");
      linkElement.setAttribute("href", imgSrc);
      linkElement.setAttribute("class", "plantuml");
      linkElement.setAttribute("target", "_blank");

      // Wrap the image element inside the link element
      linkElement.appendChild(imgElement);
      parent.replaceChild(linkElement, element);
    };
    // eslint-disable-next-line no-unused-vars
  } catch (e) {
    // Catch decode URI error
    renderErrorBanner(element, parent);
  }
});
